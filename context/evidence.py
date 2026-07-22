"""Framework-agnostic repository evidence collection for AI semantic analysis."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from context.repo_walk import iter_walk_files

SCHEMA_VERSION = 1
MAX_FILES = 4000
IMPORTANT_NAMES = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "Pipfile",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "Makefile",
    "CMakeLists.txt",
    "Dockerfile",
    "docker-compose.yml",
    "compose.yml",
    "main.py",
    "app.py",
    "Program.cs",
    "App.xaml",
    "pubspec.yaml",
    "plugin.json",
}
SOURCE_SUFFIXES = {
    ".py",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".cs",
    ".cpp",
    ".cc",
    ".c",
    ".h",
    ".hpp",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".dart",
    ".swift",
}


def _relative(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _fingerprint(files: list[Path], repo_root: Path) -> str:
    digest = hashlib.sha256()
    for path in files:
        stat = path.stat()
        digest.update(_relative(path, repo_root).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(stat.st_size).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(stat.st_mtime_ns).encode("ascii"))
        digest.update(b"\0")
        with path.open("rb") as stream:
            digest.update(stream.read(65536))
        digest.update(b"\0")
    return digest.hexdigest()


def analysis_contract() -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "claim_shape": {
            "value": "non-empty string or Unknown",
            "confidence": "high | medium | low",
            "evidence": ["repository/relative/path:optional-line"],
        },
        "claims": [
            "project_type",
            "project_summary",
            "language_framework",
            "architecture_pattern",
            "core_entry",
            "core_flow",
            "dependency_graph",
            "version_marker",
            "install_command",
            "build_command",
            "run_command",
            "quick_command",
            "bugfix_command",
            "full_command",
            "style_rules",
            "architecture_rules",
            "forbidden_operations",
            "high_risk_files",
            "feature_paths",
            "code_safety_rules",
            "multi_version_notes",
            "logging_rules",
            "exploration_suggestions",
        ],
        "lists": [
            "core_modules",
            "module_interfaces",
            "key_module_markers",
            "high_risk_directories",
            "auto_detected_candidates",
            "manual_review_items",
        ],
        "rules": [
            "Every non-Unknown value requires at least one repository-local evidence reference.",
            "Evidence line references must exist and stay within the referenced file.",
            "Low-confidence claims are not rendered as facts and become manual-review items.",
            "Command claims without evidence are rejected.",
            "Installation-only commands are invalid build commands; use N/A when the project has no build step.",
            "Normative claims using all/must/forbidden/only language require exact line evidence and counterexample search.",
            "evidence_fingerprint must match the current repository snapshot.",
        ],
    }


def collect_repository_evidence(repo_root: Path) -> dict[str, object]:
    root = repo_root.resolve()
    all_files: list[Path] = []
    rejected_external_symlinks: list[str] = []
    for path in iter_walk_files(root):
        if not path.is_file():
            continue
        try:
            path.resolve().relative_to(root)
        except ValueError:
            rejected_external_symlinks.append(_relative(path, root))
            continue
        all_files.append(path)
    all_files.sort(key=lambda path: _relative(path, root))
    truncated = len(all_files) > MAX_FILES
    files = all_files[:MAX_FILES]
    suffix_counts = Counter(path.suffix.lower() or "<none>" for path in files)
    top_level = sorted(
        path.name
        for path in root.iterdir()
        if not path.name.startswith(".")
    )
    important = [
        _relative(path, root)
        for path in files
        if path.name in IMPORTANT_NAMES
        or path.name.startswith("requirements")
        or path.suffix.lower() in {".sln", ".csproj", ".vcxproj", ".gradle"}
    ]
    source_candidates = [
        _relative(path, root)
        for path in files
        if path.suffix.lower() in SOURCE_SUFFIXES
        and (
            path.name.lower().startswith(("main", "app", "index", "program", "server"))
            or len(path.relative_to(root).parts) <= 2
        )
    ][:200]
    fingerprint = _fingerprint(files, root)
    return {
        "schema_version": SCHEMA_VERSION,
        "repository": root.name,
        "evidence_fingerprint": fingerprint,
        "truncated": truncated,
        "file_count": len(all_files),
        "top_level_entries": top_level[:300],
        "suffix_counts": dict(sorted(suffix_counts.items())),
        "important_files": important[:300],
        "source_candidates": source_candidates,
        "rejected_external_symlinks": sorted(rejected_external_symlinks),
        "analysis_contract": analysis_contract(),
        "analysis_template": {
            "schema_version": SCHEMA_VERSION,
            "evidence_fingerprint": fingerprint,
            "claims": {},
            "lists": {},
        },
    }


def evidence_json(repo_root: Path) -> str:
    return json.dumps(collect_repository_evidence(repo_root), ensure_ascii=False, indent=2, sort_keys=True)
