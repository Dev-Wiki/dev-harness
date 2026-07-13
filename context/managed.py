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

    for line in text.splitlines(keepends=True):
        marker_text = line[:-1] if line.endswith("\n") else line
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


def _block_text(text: str, block: ManagedBlock) -> str:
    return text[block.start : block.end]


def merge_managed_blocks(existing: str, generated: str) -> tuple[str, list[str]]:
    existing_blocks = parse_managed_blocks(existing)
    generated_blocks = parse_managed_blocks(generated)
    if not existing_blocks:
        raise ManagedDocumentError("legacy document has no managed blocks")
    if not generated_blocks:
        raise ManagedDocumentError("generated document has no managed blocks")

    merged = existing
    changed_ids: list[str] = []
    replacements: list[tuple[int, int, str, str]] = []
    for block_id, existing_block in existing_blocks.items():
        generated_block = generated_blocks.get(block_id)
        if generated_block is None:
            continue
        replacement = _block_text(generated, generated_block)
        current = _block_text(existing, existing_block)
        if current != replacement:
            replacements.append((existing_block.start, existing_block.end, replacement, block_id))

    for start, end, replacement, block_id in sorted(replacements, reverse=True):
        merged = merged[:start] + replacement + merged[end:]
        changed_ids.append(block_id)
    changed_ids.reverse()

    generated_order = list(generated_blocks)
    for block_id in generated_order:
        merged_blocks = parse_managed_blocks(merged)
        if block_id in merged_blocks:
            continue
        generated_block = generated_blocks[block_id]
        insertion = _block_text(generated, generated_block)
        following_ids = generated_order[generated_order.index(block_id) + 1 :]
        next_block = next((merged_blocks[item] for item in following_ids if item in merged_blocks), None)
        if next_block is not None:
            insert_at = next_block.start
            merged = merged[:insert_at] + insertion + merged[insert_at:]
        else:
            if merged and not merged.endswith("\n"):
                merged += "\n"
            merged += insertion
        changed_ids.append(block_id)

    return merged, changed_ids


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
