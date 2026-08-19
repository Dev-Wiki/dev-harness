from __future__ import annotations

import codecs
import os
import re
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path


START_RE = re.compile(
    r"^<!-- dev-harness:managed:start id=(?P<id>[a-z0-9][a-z0-9._-]*) version=(?P<version>\d+) -->$"
)
END_RE = re.compile(r"^<!-- dev-harness:managed:end id=(?P<id>[a-z0-9][a-z0-9._-]*) -->$")
MARKER_PREFIX = "<!-- dev-harness:managed:"
SUPPORTED_BLOCK_VERSION = 1


class ManagedDocumentError(ValueError):
    pass


@dataclass(frozen=True)
class DocumentFormat:
    encoding: str
    bom: bytes
    newline: str
    final_newline: bool


@dataclass(frozen=True)
class ManagedBlock:
    block_id: str
    version: int
    start: int
    body_start: int
    body_end: int
    end: int
    body: str


@dataclass(frozen=True)
class SectionSpec:
    section_id: str
    level: int
    title: str
    legacy_titles: tuple[str, ...] = ()


@dataclass(frozen=True)
class MarkdownSection:
    section_id: str
    level: int
    title: str
    start: int
    body_start: int
    end: int
    body: str


SECTION_SPECS: dict[str, tuple[SectionSpec, ...]] = {
    "README.md": (
        SectionSpec("readme.languages", 2, "编程语言"),
        SectionSpec("readme.build-systems", 2, "构建系统"),
        SectionSpec("readme.core-modules", 2, "核心模块"),
        SectionSpec("readme.usage", 2, "使用说明"),
    ),
    "AGENTS.md": (
        SectionSpec("agents.contract-index", 2, "项目规范索引"),
        SectionSpec("agents.build-contract", 2, "构建与验证契约（AI 必读）"),
        SectionSpec("agents.context", 2, "1. 项目上下文速查"),
        SectionSpec("agents.trust", 2, "1b. 文件信任等级"),
        SectionSpec("agents.style", 2, "2. 命名与风格约束"),
        SectionSpec("agents.architecture", 2, "3. 架构边界规则"),
        SectionSpec("agents.forbidden", 2, "4. 禁止操作清单"),
        SectionSpec("agents.high-risk", 2, "5. 高风险文件标注"),
        SectionSpec(
            "agents.feature-path",
            2,
            "6. 新增功能的一般流程",
            ("6. 新增功能标准路径",),
        ),
        SectionSpec("agents.safety", 2, "7. 代码安全规范"),
        SectionSpec("agents.versions", 2, "8. 多版本/多定制注意事项"),
        SectionSpec("agents.logging", 2, "9. 日志规范"),
        SectionSpec("agents.exploration", 2, "10. 提问与探索建议"),
        SectionSpec("agents.candidates", 2, "11. 自动识别候选"),
        SectionSpec("agents.manual-review", 2, "12. 需人工确认"),
        SectionSpec(
            "agents.style-anchors",
            2,
            "13. 代码风格示例（仓库抽样）",
            ("13. 代码风格锚点（仓库抽样）",),
        ),
    ),
    "ARCHITECTURE.md": (
        SectionSpec("architecture.dependencies", 2, "模块依赖关系图"),
        SectionSpec("architecture.flow", 2, "核心业务流程", ("核心功能流",)),
        SectionSpec("architecture.pattern", 2, "架构模式"),
        SectionSpec("architecture.interfaces", 2, "模块接口与通信方式"),
        SectionSpec("architecture.modules", 2, "关键模块标记"),
    ),
    "HARNESS.md": (
        SectionSpec("harness.project-type", 2, "项目类型"),
        SectionSpec(
            "harness.bootstrap",
            2,
            "编译与启动问题排查",
            ("编译启动诊断",),
        ),
        SectionSpec("harness.commands", 2, "自动识别构建命令候选"),
        SectionSpec("harness.high-risk", 2, "高风险目录"),
        SectionSpec("harness.restricted", 2, "禁改区域"),
        SectionSpec("harness.candidates", 2, "自动识别候选"),
        SectionSpec("harness.manual-review", 2, "需人工确认"),
    ),
}


ATX_HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})[ \t]+(?P<title>.*?)[ \t]*#*[ \t]*$")
FENCE_RE = re.compile(r"^[ \t]{0,3}(?P<fence>`{3,}|~{3,})")


def _decode_with_bom(raw: bytes) -> tuple[str, str, bytes]:
    if raw.startswith(codecs.BOM_UTF8):
        bom = codecs.BOM_UTF8
        encoding = "utf-8"
    elif raw.startswith(codecs.BOM_UTF16_LE):
        bom = codecs.BOM_UTF16_LE
        encoding = "utf-16-le"
    elif raw.startswith(codecs.BOM_UTF16_BE):
        bom = codecs.BOM_UTF16_BE
        encoding = "utf-16-be"
    else:
        bom = b""
        encoding = "utf-8"

    try:
        text = raw[len(bom) :].decode(encoding, errors="strict")
    except UnicodeDecodeError as exc:
        raise ManagedDocumentError("unsupported or undecodable text encoding") from exc
    return text, encoding, bom


def decode_document(raw: bytes) -> tuple[str, DocumentFormat]:
    text, encoding, bom = _decode_with_bom(raw)
    has_crlf = "\r\n" in text
    without_crlf = text.replace("\r\n", "")
    if "\r" in without_crlf:
        raise ManagedDocumentError("unsupported standalone CR line endings")
    has_lf = "\n" in without_crlf
    if has_crlf and has_lf:
        raise ManagedDocumentError("mixed line endings")

    newline = "\r\n" if has_crlf else "\n"
    normalized = text.replace("\r\n", "\n")
    return normalized, DocumentFormat(
        encoding=encoding,
        bom=bom,
        newline=newline,
        final_newline=normalized.endswith("\n"),
    )


def encode_document(text: str, document_format: DocumentFormat) -> bytes:
    normalized = text.replace("\r\n", "\n")
    if "\r" in normalized:
        raise ManagedDocumentError("text must use normalized LF line endings")
    if normalized.endswith("\n") != document_format.final_newline:
        normalized = normalized.rstrip("\n")
        if document_format.final_newline:
            normalized += "\n"
    rendered = normalized.replace("\n", document_format.newline)
    return document_format.bom + rendered.encode(document_format.encoding, errors="strict")


def parse_managed_blocks(text: str) -> dict[str, ManagedBlock]:
    blocks: dict[str, ManagedBlock] = {}
    open_block: tuple[str, int, int, int] | None = None
    offset = 0
    fence_char: str | None = None
    fence_length = 0

    for line in text.splitlines(keepends=True):
        marker_text = line[:-1] if line.endswith("\n") else line
        fence_match = FENCE_RE.match(marker_text)
        if fence_match is not None:
            fence = fence_match.group("fence")
            if fence_char is None:
                fence_char = fence[0]
                fence_length = len(fence)
            elif fence[0] == fence_char and len(fence) >= fence_length:
                fence_char = None
                fence_length = 0
            offset += len(line)
            continue
        if fence_char is not None:
            offset += len(line)
            continue
        start_match = START_RE.fullmatch(marker_text)
        end_match = END_RE.fullmatch(marker_text)

        if marker_text.startswith(MARKER_PREFIX) and start_match is None and end_match is None:
            raise ManagedDocumentError(f"malformed managed marker: {marker_text}")

        if start_match is not None:
            if open_block is not None:
                raise ManagedDocumentError("nested managed blocks are not allowed")
            block_id = start_match.group("id")
            version = int(start_match.group("version"))
            if version != SUPPORTED_BLOCK_VERSION:
                raise ManagedDocumentError(f"unsupported managed block version: {version}")
            if block_id in blocks:
                raise ManagedDocumentError(f"duplicate managed block id: {block_id}")
            open_block = (block_id, version, offset, offset + len(line))
        elif end_match is not None:
            if open_block is None:
                raise ManagedDocumentError("managed block end marker has no start")
            block_id, version, start, body_start = open_block
            end_id = end_match.group("id")
            if end_id != block_id:
                raise ManagedDocumentError(f"managed block end id {end_id} does not match {block_id}")
            blocks[block_id] = ManagedBlock(
                block_id=block_id,
                version=version,
                start=start,
                body_start=body_start,
                body_end=offset,
                end=offset + len(line),
                body=text[body_start:offset],
            )
            open_block = None

        offset += len(line)

    if open_block is not None:
        raise ManagedDocumentError(f"unclosed managed block: {open_block[0]}")
    return blocks


def strip_legacy_managed_markers(text: str) -> tuple[str, tuple[str, ...]]:
    """Remove valid legacy marker lines while preserving every byte of their bodies."""
    blocks = parse_managed_blocks(text)
    if not blocks:
        return text, ()
    cleaned = text
    for block in sorted(blocks.values(), key=lambda item: item.start, reverse=True):
        cleaned = cleaned[: block.body_end] + cleaned[block.end :]
        cleaned = cleaned[: block.start] + cleaned[block.body_start :]
    return cleaned, tuple(blocks)


def _headings(text: str) -> list[tuple[int, str, int, int]]:
    headings: list[tuple[int, str, int, int]] = []
    offset = 0
    fence_char: str | None = None
    fence_length = 0
    for line in text.splitlines(keepends=True):
        marker_text = line[:-1] if line.endswith("\n") else line
        fence_match = FENCE_RE.match(marker_text)
        if fence_match is not None:
            fence = fence_match.group("fence")
            if fence_char is None:
                fence_char = fence[0]
                fence_length = len(fence)
            elif fence[0] == fence_char and len(fence) >= fence_length:
                fence_char = None
                fence_length = 0
            offset += len(line)
            continue
        if fence_char is None:
            heading_match = ATX_HEADING_RE.fullmatch(marker_text)
            if heading_match is not None:
                headings.append(
                    (
                        len(heading_match.group("hashes")),
                        heading_match.group("title").rstrip(),
                        offset,
                        offset + len(line),
                    )
                )
        offset += len(line)
    return headings


def parse_markdown_sections(text: str, specs: tuple[SectionSpec, ...]) -> dict[str, MarkdownSection]:
    headings = _headings(text)
    sections: dict[str, MarkdownSection] = {}
    for spec in specs:
        accepted_titles = (spec.title, *spec.legacy_titles)
        matching = [item for item in headings if item[1] in accepted_titles]
        if not matching:
            raise ManagedDocumentError(f"missing fixed heading: {'#' * spec.level} {spec.title}")
        if len(matching) > 1:
            raise ManagedDocumentError(
                f"duplicate fixed heading or legacy alias: {spec.title}"
            )
        level, title, start, body_start = matching[0]
        if level != spec.level:
            raise ManagedDocumentError(
                f"fixed heading level changed: {spec.title} (expected {spec.level}, found {level})"
            )
        heading_index = headings.index(matching[0])
        end = len(text)
        for next_level, _, next_start, _ in headings[heading_index + 1 :]:
            if next_level <= level:
                end = next_start
                break
        sections[spec.section_id] = MarkdownSection(
            section_id=spec.section_id,
            level=level,
            title=title,
            start=start,
            body_start=body_start,
            end=end,
            body=text[body_start:end],
        )
    return sections


def merge_markdown_sections(
    existing: str,
    generated: str,
    specs: tuple[SectionSpec, ...],
) -> tuple[str, list[str], tuple[str, ...]]:
    existing, legacy_ids = strip_legacy_managed_markers(existing)
    generated, _ = strip_legacy_managed_markers(generated)
    existing_sections = parse_markdown_sections(existing, specs)
    generated_sections = parse_markdown_sections(generated, specs)
    replacements: list[tuple[int, int, str, str]] = []
    for spec in specs:
        current = existing_sections[spec.section_id]
        generated_section = generated_sections[spec.section_id]
        replacement = generated[generated_section.start : generated_section.end]
        original = existing[current.start : current.end]
        if original != replacement:
            replacements.append((current.start, current.end, replacement, spec.section_id))

    merged = existing
    changed_ids: list[str] = []
    for start, end, replacement, section_id in sorted(replacements, reverse=True):
        merged = merged[:start] + replacement + merged[end:]
        changed_ids.append(section_id)
    changed_ids.reverse()
    return merged, changed_ids, legacy_ids


def atomic_write_document(path: Path, text: str, document_format: DocumentFormat) -> None:
    encoded = encode_document(text, document_format)
    original_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
            temporary_path = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        temporary_path.chmod(original_mode)
        os.replace(temporary_path, path)
    except Exception:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
        raise
