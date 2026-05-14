"""Pruned repository file walking for context scanning (avoids bin/obj/packages, etc.)."""

from __future__ import annotations

import fnmatch
import os
from collections.abc import Iterator
from itertools import islice
from pathlib import Path

# Directory names we never descend into (build outputs, tooling caches, deps).
SKIP_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        ".idea",
        ".vscode",
        ".cursor",
        ".pytest_cache",
        "__pycache__",
        "node_modules",
        "dist",
        "build",
        "coverage",
        "bin",
        "obj",
        "packages",
        "PackageCache",
        ".vs",
        "TestResults",
        "ipch",
        "publish",
        "_ReSharper.Caches",
    }
)


def _skip_dir(name: str) -> bool:
    if name in SKIP_DIR_NAMES:
        return True
    if name.startswith("."):
        return True
    return False


def iter_walk_files(repo_root: Path) -> Iterator[Path]:
    """Yield files under repo_root, skipping heavy/irrelevant directories."""
    root = repo_root.resolve()
    if not root.is_dir():
        return
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        dirnames[:] = [d for d in dirnames if not _skip_dir(d)]
        base = Path(dirpath)
        for fname in filenames:
            yield base / fname


def iter_matching_files(repo_root: Path, *patterns: str) -> Iterator[Path]:
    for path in iter_walk_files(repo_root):
        name = path.name
        if any(fnmatch.fnmatch(name, p) for p in patterns):
            yield path


def first_matching_file(repo_root: Path, *patterns: str) -> Path | None:
    """Lexicographically first path (by posix rel path) matching any basename pattern."""
    best: tuple[str, Path] | None = None
    for path in iter_matching_files(repo_root, *patterns):
        rel = path.relative_to(repo_root.resolve()).as_posix()
        if best is None or rel < best[0]:
            best = (rel, path)
    return best[1] if best else None


def find_all_matching_files(repo_root: Path, *patterns: str) -> list[Path]:
    """All files whose name matches any pattern; stable globally sorted by rel path."""
    root = repo_root.resolve()
    matches: list[Path] = []
    seen: set[str] = set()
    for path in iter_walk_files(root):
        name = path.name
        if not any(fnmatch.fnmatch(name, p) for p in patterns):
            continue
        rel = path.relative_to(root).as_posix()
        if rel in seen:
            continue
        seen.add(rel)
        matches.append(path)
    matches.sort(key=lambda p: p.relative_to(root).as_posix())
    return matches


def repo_has_suffix(repo_root: Path, suffix: str) -> bool:
    suf = suffix.lower()
    for path in iter_walk_files(repo_root):
        if path.suffix.lower() == suf:
            return True
    return False


def repo_has_any_suffix(repo_root: Path, suffixes: tuple[str, ...]) -> bool:
    targets = {s.lower() for s in suffixes}
    for path in iter_walk_files(repo_root):
        if path.suffix.lower() in targets:
            return True
    return False


def repo_contains_pattern(repo_root: Path, pattern: str) -> bool:
    for _ in iter_matching_files(repo_root, pattern):
        return True
    return False


def repo_contains_vcxproj(repo_root: Path) -> bool:
    return repo_contains_pattern(repo_root, "*.vcxproj")


def sample_matching_files(repo_root: Path, limit: int, *patterns: str) -> list[Path]:
    return list(islice(iter_matching_files(repo_root, *patterns), limit))
