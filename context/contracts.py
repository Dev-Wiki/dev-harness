from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from context.managed import ManagedDocumentError, decode_document, parse_managed_blocks


@dataclass(frozen=True)
class ContractIndex:
    build: str
    git_workflow: str
    code_style: str
    release: str
    changelog: str
    manual_review: tuple[str, ...] = ()


LABEL_TO_FIELD = {
    "Git 工作流": "git_workflow",
    "代码规范": "code_style",
    "发布规范": "release",
    "变更日志": "changelog",
}

CANDIDATES = {
    "git_workflow": (
        "docs/GIT_WORKFLOW.md",
        ".github/CONTRIBUTING.md",
        "CONTRIBUTING.md",
        "GIT_WORKFLOW.md",
    ),
    "code_style": (
        "docs/CODE_STYLE.md",
        "CODE_STYLE.md",
        ".github/CONTRIBUTING.md",
        "CONTRIBUTING.md",
    ),
    "release": (
        "docs/RELEASE.md",
        "RELEASE.md",
        "docs/GIT_WORKFLOW.md",
        ".github/CONTRIBUTING.md",
        "CONTRIBUTING.md",
    ),
    "changelog": (
        "CHANGELOG.md",
        "docs/CHANGELOG.md",
        "HISTORY.md",
    ),
}

INDEX_ENTRY_RE = re.compile(r"^- (?P<label>Git 工作流|代码规范|发布规范|变更日志)：`(?P<path>[^`]+)`$")


def _valid_relative_file(repo_root: Path, relative: str) -> str | None:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    root = repo_root.resolve()
    try:
        resolved = (root / candidate).resolve(strict=True)
        resolved.relative_to(root)
    except (FileNotFoundError, OSError, ValueError):
        return None
    if not resolved.is_file():
        return None
    return resolved.relative_to(root).as_posix()


def _existing_index_references(repo_root: Path) -> tuple[dict[str, str], set[str]]:
    agents_path = repo_root / "AGENTS.md"
    if not agents_path.is_file():
        return {}, set()
    try:
        text, _ = decode_document(agents_path.read_bytes())
        block = parse_managed_blocks(text).get("agents.contract-index")
    except (OSError, ManagedDocumentError):
        return {}, set()
    if block is None:
        return {}, set()

    references: dict[str, str] = {}
    conflicts: set[str] = set()
    for line in block.body.splitlines():
        match = INDEX_ENTRY_RE.fullmatch(line)
        if match is None:
            continue
        field = LABEL_TO_FIELD[match.group("label")]
        valid = _valid_relative_file(repo_root, match.group("path"))
        if valid is None or field in conflicts:
            continue
        previous = references.get(field)
        if previous is not None and previous != valid:
            references.pop(field)
            conflicts.add(field)
        else:
            references[field] = valid
    return references, conflicts


def discover_contract_index(repo_root: Path) -> ContractIndex:
    existing, conflicts = _existing_index_references(repo_root)
    discovered: dict[str, str] = {}
    for field, candidates in CANDIDATES.items():
        if field in conflicts:
            discovered[field] = "Unknown"
            continue
        if field in existing:
            discovered[field] = existing[field]
            continue
        discovered[field] = next(
            (valid for relative in candidates if (valid := _valid_relative_file(repo_root, relative)) is not None),
            "Unknown",
        )
    field_labels = {field: label for label, field in LABEL_TO_FIELD.items()}
    manual_review = tuple(
        f"{field_labels[field]}存在多个有效规范引用，需人工选择权威文档"
        for field in CANDIDATES
        if field in conflicts
    )
    return ContractIndex(build="HARNESS.md", manual_review=manual_review, **discovered)
