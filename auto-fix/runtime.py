#!/usr/bin/env python3
"""Deterministic runtime for the dev-harness auto-fix contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, NamedTuple, Sequence


MODES = {"analyze", "fix", "commit", "unattended"}
COMPLETION_STATUSES = {"DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"}
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


class WorkspaceDrift(RuntimeError):
    """Raised when the workspace no longer matches its ownership snapshot."""


class StateTransitionError(RuntimeError):
    """Raised when an auto-fix stage transition violates the contract."""


class WorkspaceValidation(NamedTuple):
    changed_files: tuple[str, ...]
    diff_hash: str


def _git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise WorkspaceDrift(f"git {' '.join(args)} failed: {message}")
    return result.stdout


def _git_root(repo: Path) -> Path:
    return Path(_git(repo, "rev-parse", "--show-toplevel").decode().strip()).resolve()


def _nul_paths(raw: bytes) -> set[str]:
    return {item.decode("utf-8", errors="surrogateescape") for item in raw.split(b"\0") if item}


def _changed_paths(repo: Path) -> set[str]:
    return (
        _nul_paths(_git(repo, "diff", "--name-only", "-z"))
        | _nul_paths(_git(repo, "diff", "--cached", "--name-only", "-z"))
        | _nul_paths(_git(repo, "ls-files", "--others", "--exclude-standard", "-z"))
    )


def _normalize_paths(paths: Sequence[str]) -> tuple[str, ...]:
    normalized: set[str] = set()
    for raw in paths:
        path = Path(raw)
        if path.is_absolute() or ".." in path.parts or not raw.strip():
            raise WorkspaceDrift(f"invalid changed file path: {raw!r}")
        value = path.as_posix()
        if not value:
            raise WorkspaceDrift(f"invalid changed file path: {raw!r}")
        normalized.add(value)
    return tuple(sorted(normalized))


def _file_fingerprint(repo: Path, relative: str) -> str:
    digest = hashlib.sha256()
    digest.update(relative.encode("utf-8", errors="surrogateescape"))
    for args in (
        ("diff", "--binary", "--", relative),
        ("diff", "--cached", "--binary", "--", relative),
    ):
        digest.update(b"\0git\0")
        digest.update(_git(repo, *args))
    path = repo / relative
    if path.is_symlink():
        digest.update(b"\0symlink\0")
        digest.update(os.readlink(path).encode("utf-8", errors="surrogateescape"))
    elif path.is_file():
        stat = path.stat()
        digest.update(f"\0file\0{stat.st_mode & 0o777:o}\0".encode())
        digest.update(path.read_bytes())
    elif path.exists():
        digest.update(b"\0other\0")
    else:
        digest.update(b"\0missing\0")
    return digest.hexdigest()


def create_snapshot(repo: str | Path) -> dict[str, Any]:
    root = _git_root(Path(repo).resolve())
    preexisting = sorted(_changed_paths(root))
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD").decode().strip()
    return {
        "version": 1,
        "repo_root": str(root),
        "base_sha": _git(root, "rev-parse", "HEAD").decode().strip(),
        "branch": branch,
        "preexisting_changes": preexisting,
        "preexisting_fingerprints": {
            path: _file_fingerprint(root, path) for path in preexisting
        },
    }


def _assert_snapshot_identity(snapshot: dict[str, Any]) -> Path:
    root = _git_root(Path(snapshot["repo_root"]))
    head = _git(root, "rev-parse", "HEAD").decode().strip()
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD").decode().strip()
    if head != snapshot["base_sha"]:
        raise WorkspaceDrift("HEAD drifted since WorkspaceSnapshot")
    if branch != snapshot["branch"]:
        raise WorkspaceDrift("branch drifted since WorkspaceSnapshot")
    return root


def validate_workspace(
    snapshot: dict[str, Any], changed_files: Sequence[str]
) -> WorkspaceValidation:
    root = _assert_snapshot_identity(snapshot)
    declared = _normalize_paths(changed_files)
    preexisting = set(snapshot["preexisting_changes"])
    overlap = preexisting.intersection(declared)
    if overlap:
        raise WorkspaceDrift(
            "AutoFixChangedFiles contains a path that was already dirty: "
            + ", ".join(sorted(overlap))
        )

    for path, expected in snapshot["preexisting_fingerprints"].items():
        if _file_fingerprint(root, path) != expected:
            raise WorkspaceDrift(f"pre-existing change was modified: {path}")

    new_changes = _changed_paths(root) - preexisting
    undeclared = new_changes - set(declared)
    missing = set(declared) - new_changes
    if undeclared:
        raise WorkspaceDrift("undeclared workspace changes: " + ", ".join(sorted(undeclared)))
    if missing:
        raise WorkspaceDrift("declared files are not changed: " + ", ".join(sorted(missing)))
    return WorkspaceValidation(declared, compute_diff_hash(snapshot, declared))


def compute_diff_hash(snapshot: dict[str, Any], changed_files: Sequence[str]) -> str:
    root = _assert_snapshot_identity(snapshot)
    paths = _normalize_paths(changed_files)
    digest = hashlib.sha256()
    digest.update(f"dev-harness-diff-v1\0{snapshot['base_sha']}\0".encode())
    for path in paths:
        digest.update(path.encode("utf-8", errors="surrogateescape"))
        digest.update(b"\0")
        digest.update(_file_fingerprint(root, path).encode())
        digest.update(b"\0")
    return digest.hexdigest()


class AutoFixStateStore:
    def __init__(self, repo: Path, path: Path):
        self.repo = repo
        self.path = path

    @classmethod
    def initialize(cls, repo: str | Path, run_id: str, mode: str) -> "AutoFixStateStore":
        if mode not in MODES:
            raise ValueError(f"unsupported mode: {mode}")
        if not RUN_ID_PATTERN.fullmatch(run_id):
            raise ValueError("run_id may contain only letters, digits, dot, underscore, and dash")
        root = _git_root(Path(repo).resolve())
        relative = _git(root, "rev-parse", "--git-path", f"dev-harness/auto-fix/{run_id}/state.json").decode().strip()
        path = Path(relative)
        if not path.is_absolute():
            path = root / path
        store = cls(root, path.resolve())
        if store.path.exists():
            existing = store.load()
            if existing.get("RunId") != run_id or existing.get("Mode") != mode:
                raise StateTransitionError("existing run state does not match run_id and mode")
            validate_workspace(
                existing["WorkspaceSnapshot"], existing.get("ChangedFiles", [])
            )
            return store
        snapshot = create_snapshot(root)
        store._write(
            {
                "RunId": run_id,
                "Mode": mode,
                "BaseSha": snapshot["base_sha"],
                "Stage": "preflight",
                "WorkspaceSnapshot": snapshot,
                "Hypotheses": [],
                "RegressionRedEvidence": {},
                "ChangedFiles": [],
                "VerificationEvidence": {},
                "ReviewDiffHash": None,
                "Commits": [],
                "IssueCommentMarker": None,
                "CompletionStatus": None,
            }
        )
        return store

    def load(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, state: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(f".tmp-{os.getpid()}")
        temporary.write_text(
            json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.path)

    def checkpoint(
        self,
        stage: str,
        *,
        hypotheses: list[dict[str, Any]] | None = None,
        regression_red: dict[str, Any] | None = None,
        changed_files: Sequence[str] | None = None,
        verification: dict[str, Any] | None = None,
        review_diff_hash: str | None = None,
        commit: str | None = None,
        issue_comment_marker: str | None = None,
        completion_status: str | None = None,
    ) -> dict[str, Any]:
        state = self.load()
        current = state["Stage"]
        mode = state["Mode"]
        if stage != current:
            self._validate_transition(state, stage)
        if hypotheses is not None:
            state["Hypotheses"] = hypotheses
        if regression_red is not None:
            state["RegressionRedEvidence"] = regression_red
        if changed_files is not None:
            state["ChangedFiles"] = list(_normalize_paths(changed_files))
        if verification is not None:
            state["VerificationEvidence"] = verification
        if review_diff_hash is not None:
            state["ReviewDiffHash"] = review_diff_hash
        if commit is not None:
            if mode not in {"commit", "unattended"}:
                raise StateTransitionError(f"{mode} mode cannot record a commit")
            state["Commits"].append(commit)
        if issue_comment_marker is not None:
            state["IssueCommentMarker"] = issue_comment_marker
        if completion_status is not None:
            if completion_status not in COMPLETION_STATUSES:
                raise StateTransitionError(f"invalid completion status: {completion_status}")
            state["CompletionStatus"] = completion_status
        if stage == "implement":
            state["VerificationEvidence"] = {}
            state["ReviewDiffHash"] = None
        state["Stage"] = stage
        self._write(state)
        return state

    @staticmethod
    def _validate_transition(state: dict[str, Any], target: str) -> None:
        current = state["Stage"]
        mode = state["Mode"]
        if mode == "analyze" and target not in {"context", "reproduce", "hypothesize", "report"}:
            raise StateTransitionError(f"analyze mode cannot enter {target}")
        if target == "commit" and mode not in {"commit", "unattended"}:
            raise StateTransitionError(f"{mode} mode cannot enter commit")

        allowed = {
            "preflight": {"context"},
            "context": {"reproduce"},
            "reproduce": {"hypothesize"},
            "hypothesize": {"report"} if mode == "analyze" else {"regress-red"},
            "regress-red": {"implement"},
            "implement": {"verify"},
            "verify": {"implement", "review"},
            "review": {"implement", "final-verify"},
            "final-verify": {"report", "commit"},
            "commit": {"report"},
            "report": set(),
        }
        if target not in allowed.get(current, set()):
            raise StateTransitionError(f"invalid stage transition: {current} -> {target}")
        if current == "hypothesize" and target == "regress-red":
            confirmed = any(item.get("Status") == "confirmed" for item in state["Hypotheses"])
            if not confirmed:
                raise StateTransitionError("a confirmed hypothesis is required before regress-red")
        if current == "regress-red" and target == "implement" and not state["RegressionRedEvidence"]:
            raise StateTransitionError("regression RED evidence is required before implement")
        if current == "review" and target == "final-verify":
            reviewed_hash = state.get("ReviewDiffHash")
            if not reviewed_hash:
                raise StateTransitionError("ReviewDiffHash is required before final-verify")
            validation = validate_workspace(
                state["WorkspaceSnapshot"], state.get("ChangedFiles", [])
            )
            if validation.diff_hash != reviewed_hash:
                raise StateTransitionError(
                    "current diff does not match ReviewDiffHash; review evidence is stale"
                )


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    snapshot_parser = sub.add_parser("snapshot")
    snapshot_parser.add_argument("--repo", default=".")
    init_parser = sub.add_parser("init")
    init_parser.add_argument("--repo", default=".")
    init_parser.add_argument("--run-id", required=True)
    init_parser.add_argument("--mode", choices=sorted(MODES), required=True)
    verify_parser = sub.add_parser("verify-workspace")
    verify_parser.add_argument("--state", type=Path, required=True)
    verify_parser.add_argument("--changed-file", action="append", default=[])
    hash_parser = sub.add_parser("diff-hash")
    hash_parser.add_argument("--state", type=Path, required=True)
    hash_parser.add_argument("--changed-file", action="append", default=[])
    checkpoint_parser = sub.add_parser("checkpoint")
    checkpoint_parser.add_argument("--state", type=Path, required=True)
    checkpoint_parser.add_argument("--stage", required=True)
    checkpoint_parser.add_argument("--hypotheses-json")
    checkpoint_parser.add_argument("--regression-red-json")
    checkpoint_parser.add_argument("--changed-file", action="append")
    checkpoint_parser.add_argument("--verification-json")
    checkpoint_parser.add_argument("--review-diff-hash")
    checkpoint_parser.add_argument("--commit")
    checkpoint_parser.add_argument("--issue-comment-marker")
    checkpoint_parser.add_argument("--completion-status", choices=sorted(COMPLETION_STATUSES))
    args = parser.parse_args(argv)

    if args.command == "snapshot":
        _print_json(create_snapshot(args.repo))
    elif args.command == "init":
        store = AutoFixStateStore.initialize(args.repo, args.run_id, args.mode)
        _print_json({"state_path": str(store.path), "state": store.load()})
    elif args.command in {"verify-workspace", "diff-hash"}:
        state = json.loads(args.state.read_text(encoding="utf-8"))
        snapshot = state["WorkspaceSnapshot"]
        if args.command == "verify-workspace":
            result = validate_workspace(snapshot, args.changed_file)
            _print_json({"changed_files": result.changed_files, "diff_hash": result.diff_hash})
        else:
            print(compute_diff_hash(snapshot, args.changed_file))
    else:
        state = json.loads(args.state.read_text(encoding="utf-8"))
        store = AutoFixStateStore(Path(state["WorkspaceSnapshot"]["repo_root"]), args.state.resolve())
        options: dict[str, Any] = {}
        if args.hypotheses_json is not None:
            options["hypotheses"] = json.loads(args.hypotheses_json)
        if args.regression_red_json is not None:
            options["regression_red"] = json.loads(args.regression_red_json)
        if args.changed_file is not None:
            options["changed_files"] = args.changed_file
        if args.verification_json is not None:
            options["verification"] = json.loads(args.verification_json)
        for argument, key in (
            (args.review_diff_hash, "review_diff_hash"),
            (args.commit, "commit"),
            (args.issue_comment_marker, "issue_comment_marker"),
            (args.completion_status, "completion_status"),
        ):
            if argument is not None:
                options[key] = argument
        _print_json(store.checkpoint(args.stage, **options))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
