#!/usr/bin/env python3
"""Deterministic state and workspace guardrails for Codebase Audit V1.

This runtime deliberately does not inspect source code or generate audit prose.  It
only owns the durable run state, snapshot validation, finding contract, and the
boundary within which an agent may write audit documents.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path, PureWindowsPath
from typing import Any, Mapping, NamedTuple, Sequence


SCHEMA_VERSION = 1
RUN_STATUSES = {"ACTIVE", "COMPLETED", "STALE"}
TASK_STATUSES = {
    "pending",
    "in-progress",
    "needs-verification",
    "completed",
    "blocked",
    "stale",
}
FINDING_STATUSES = {
    "candidate",
    "needs-verification",
    "confirmed",
    "rejected",
    "stale",
    "resolved",
}
SEVERITIES = {"P0", "P1", "P2", "P3"}
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
TASK_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
FINDING_ID_PATTERN = re.compile(r"^AUD-[0-9]{3,}$")


class AuditRuntimeError(RuntimeError):
    """Base class for deterministic audit contract failures."""


class WorkspaceDrift(AuditRuntimeError):
    """Raised when code, Git identity, or canonical context has drifted."""


class StateTransitionError(AuditRuntimeError):
    """Raised when a stale run is mutated or a checkpoint is invalid."""


class OutputPathError(AuditRuntimeError):
    """Raised when an audit output path is outside the allowed audit root."""


class FindingValidationError(AuditRuntimeError):
    """Raised when a finding does not satisfy the finding contract."""


class WorkspaceValidation(NamedTuple):
    business_dirty_files: tuple[str, ...]
    audit_output_files: tuple[str, ...]
    snapshot_fingerprint: str


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
    value = _git(repo, "rev-parse", "--show-toplevel").decode().strip()
    return Path(value).resolve()


def _nul_paths(raw: bytes) -> set[str]:
    return {
        item.decode("utf-8", errors="surrogateescape")
        for item in raw.split(b"\0")
        if item
    }


def _changed_paths(repo: Path) -> set[str]:
    return (
        _nul_paths(_git(repo, "diff", "--name-only", "-z"))
        | _nul_paths(_git(repo, "diff", "--cached", "--name-only", "-z"))
        | _nul_paths(_git(repo, "ls-files", "--others", "--exclude-standard", "-z"))
    )


def _normalize_repo_path(raw: str) -> str:
    if not isinstance(raw, str) or not raw.strip() or "\0" in raw:
        raise WorkspaceDrift(f"invalid repository path: {raw!r}")
    path = Path(raw)
    if path.is_absolute() or PureWindowsPath(raw).is_absolute() or ".." in path.parts:
        raise WorkspaceDrift(f"invalid repository path: {raw!r}")
    value = path.as_posix()
    if value in {"", "."}:
        raise WorkspaceDrift(f"invalid repository path: {raw!r}")
    return value


def _file_fingerprint(repo: Path, relative: str) -> str:
    """Fingerprint index/worktree state, including untracked and deleted files."""

    relative = _normalize_repo_path(relative)
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


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def resolve_docs_root(repo: str | Path, docs_root: str | Path | None = None) -> Path:
    """Resolve one already-existing top-level ``doc/`` or ``docs/`` directory."""

    root = _git_root(Path(repo).resolve())
    if docs_root is None:
        candidates = [root / name for name in ("docs", "doc") if (root / name).is_dir()]
        if not candidates:
            raise OutputPathError("repository has no existing doc/ or docs/ root")
        if len(candidates) > 1:
            raise OutputPathError(
                "repository has both doc/ and docs/; select the canonical root explicitly"
            )
        selected = candidates[0]
    else:
        raw = os.fspath(docs_root)
        path = Path(raw)
        if (
            path.is_absolute()
            or PureWindowsPath(raw).is_absolute()
            or ".." in path.parts
            or path.as_posix() not in {"doc", "docs"}
        ):
            raise OutputPathError("docs_root must be the existing top-level doc or docs directory")
        selected = root / path
        if not selected.is_dir():
            raise OutputPathError(f"selected docs root does not exist: {path.as_posix()}")

    resolved = selected.resolve()
    if not _is_within(resolved, root):
        raise OutputPathError("docs root escapes the repository through a symlink")
    return selected


def _normalize_scope(scope: str | Sequence[str]) -> list[str]:
    values = [scope] if isinstance(scope, str) else list(scope)
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("audit scope entries must be non-empty strings")
        stripped = value.strip()
        if stripped not in normalized:
            normalized.append(stripped)
    if not normalized:
        raise ValueError("audit scope must contain at least one entry")
    return normalized


def _snapshot_fingerprint_payload(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "base_sha": snapshot["base_sha"],
        "branch": snapshot["branch"],
        "preexisting_dirty_files": snapshot["preexisting_dirty_files"],
        "preexisting_fingerprints": snapshot["preexisting_fingerprints"],
        "context_fingerprint": snapshot["context_fingerprint"],
        "scope": snapshot["scope"],
        "docs_root": snapshot["docs_root"],
        "audit_output_root": snapshot["audit_output_root"],
    }


def compute_snapshot_fingerprint(snapshot: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        _snapshot_fingerprint_payload(snapshot),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8", errors="surrogateescape")
    return hashlib.sha256(b"dev-harness-codebase-audit-v1\0" + encoded).hexdigest()


def create_audit_snapshot(
    repo: str | Path,
    context_fingerprint: str,
    scope: str | Sequence[str],
    docs_root: str | Path | None = None,
) -> dict[str, Any]:
    """Create the immutable evidence boundary for one audit run."""

    if not isinstance(context_fingerprint, str) or not context_fingerprint.strip():
        raise ValueError("context_fingerprint must be a non-empty string")
    root = _git_root(Path(repo).resolve())
    canonical_docs_root = resolve_docs_root(root, docs_root)
    dirty = sorted(_changed_paths(root))
    relative_docs_root = canonical_docs_root.relative_to(root).as_posix()
    snapshot: dict[str, Any] = {
        "version": SCHEMA_VERSION,
        "repo_root": str(root),
        "base_sha": _git(root, "rev-parse", "HEAD").decode().strip(),
        "branch": _git(root, "rev-parse", "--abbrev-ref", "HEAD").decode().strip(),
        "preexisting_dirty_files": dirty,
        # Compatibility with the existing Auto Fix snapshot vocabulary.
        "preexisting_changes": dirty,
        "preexisting_fingerprints": {
            path: _file_fingerprint(root, path) for path in dirty
        },
        "context_fingerprint": context_fingerprint.strip(),
        "scope": _normalize_scope(scope),
        "docs_root": relative_docs_root,
        "audit_output_root": f"{relative_docs_root}/audit",
    }
    snapshot["snapshot_fingerprint"] = compute_snapshot_fingerprint(snapshot)
    return snapshot


# A concise public alias for callers that already use Auto Fix's create_snapshot API.
create_snapshot = create_audit_snapshot


def _assert_snapshot_identity(snapshot: Mapping[str, Any]) -> Path:
    root = _git_root(Path(snapshot["repo_root"]))
    head = _git(root, "rev-parse", "HEAD").decode().strip()
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD").decode().strip()
    if head != snapshot["base_sha"]:
        raise WorkspaceDrift("HEAD drifted since AuditSnapshot")
    if branch != snapshot["branch"]:
        raise WorkspaceDrift("branch drifted since AuditSnapshot")
    if compute_snapshot_fingerprint(snapshot) != snapshot.get("snapshot_fingerprint"):
        raise WorkspaceDrift("AuditSnapshot fingerprint is invalid")
    return root


def _is_audit_output(relative: str, snapshot: Mapping[str, Any]) -> bool:
    path = Path(_normalize_repo_path(relative))
    audit_root = Path(snapshot["audit_output_root"])
    return path == audit_root or audit_root in path.parents


def validate_output_path(snapshot: Mapping[str, Any], output_path: str | Path) -> Path:
    """Validate a path relative to ``<docs-root>/audit`` and return its full path."""

    raw = os.fspath(output_path)
    if not raw.strip() or "\0" in raw:
        raise OutputPathError("audit output path must be non-empty")
    relative = Path(raw)
    if (
        relative.is_absolute()
        or PureWindowsPath(raw).is_absolute()
        or ".." in relative.parts
        or relative.as_posix() in {"", "."}
    ):
        raise OutputPathError("audit output path must be relative and may not contain '..'")

    root = _assert_snapshot_identity(snapshot)
    docs_root = root / snapshot["docs_root"]
    audit_root = root / snapshot["audit_output_root"]
    candidate = audit_root / relative
    resolved_root = root.resolve()
    resolved_docs = docs_root.resolve()
    resolved_audit = audit_root.resolve()
    resolved_candidate = candidate.resolve()
    if not _is_within(resolved_docs, resolved_root):
        raise OutputPathError("docs root escapes the repository through a symlink")
    if not _is_within(resolved_audit, resolved_docs):
        raise OutputPathError("audit root escapes the docs root through a symlink")
    if not _is_within(resolved_candidate, resolved_audit):
        raise OutputPathError("audit output path escapes the audit root through a symlink")
    return candidate


def validate_workspace(
    snapshot: Mapping[str, Any], current_context_fingerprint: str | None = None
) -> WorkspaceValidation:
    """Fail closed on all drift except files inside this run's audit docs root."""

    root = _assert_snapshot_identity(snapshot)
    if (
        current_context_fingerprint is not None
        and current_context_fingerprint != snapshot["context_fingerprint"]
    ):
        raise WorkspaceDrift("canonical Context fingerprint changed since AuditSnapshot")

    preexisting = set(snapshot["preexisting_dirty_files"])
    current = _changed_paths(root)
    for path in sorted(preexisting):
        expected = snapshot["preexisting_fingerprints"].get(path)
        if expected is None or _file_fingerprint(root, path) != expected:
            raise WorkspaceDrift(f"pre-existing dirty content drifted: {path}")
        if path not in current:
            raise WorkspaceDrift(f"pre-existing dirty file disappeared: {path}")

    preexisting_business = {path for path in preexisting if not _is_audit_output(path, snapshot)}
    current_business = {path for path in current if not _is_audit_output(path, snapshot)}
    added = current_business - preexisting_business
    removed = preexisting_business - current_business
    if added:
        raise WorkspaceDrift(
            "business/source workspace drift detected: " + ", ".join(sorted(added))
        )
    if removed:
        raise WorkspaceDrift(
            "pre-existing dirty files disappeared: " + ", ".join(sorted(removed))
        )

    audit_outputs = sorted(current - current_business)
    for relative in audit_outputs:
        within_audit = Path(relative).relative_to(Path(snapshot["audit_output_root"]))
        try:
            validate_output_path(snapshot, within_audit)
        except OutputPathError as error:
            raise WorkspaceDrift(str(error)) from error

    return WorkspaceValidation(
        tuple(sorted(current_business)),
        tuple(audit_outputs),
        str(snapshot["snapshot_fingerprint"]),
    )


_FINDING_ALIASES: dict[str, tuple[str, ...]] = {
    "id": ("id", "finding_id", "ID", "FindingId"),
    "status": ("status", "Status"),
    "severity": ("severity", "Severity"),
    "category": ("category", "Category"),
    "summary": ("summary", "Summary"),
    "evidence_paths_lines": (
        "evidence_paths_lines",
        "evidence",
        "Evidence",
        "EvidencePathsLines",
    ),
    "relevant_call_chain_data_flow": (
        "relevant_call_chain_data_flow",
        "relevant_flow",
        "call_chain",
        "data_flow",
        "RelevantCallChainOrDataFlow",
    ),
    "claim": ("claim", "Claim"),
    "counter_evidence_checked": (
        "counter_evidence_checked",
        "CounterEvidenceChecked",
    ),
    "risk_impact": ("risk_impact", "RiskImpact"),
    "confidence": ("confidence", "Confidence"),
    "suggested_next_action": (
        "suggested_next_action",
        "next_action",
        "SuggestedNextAction",
    ),
    "snapshot": ("snapshot", "Snapshot"),
}


def _has_content(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def _canonicalize_finding(finding: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(finding, Mapping):
        raise FindingValidationError("finding must be a JSON object")
    aliases = {alias for values in _FINDING_ALIASES.values() for alias in values}
    canonical = {key: value for key, value in finding.items() if key not in aliases}
    for target, names in _FINDING_ALIASES.items():
        present = [(name, finding[name]) for name in names if name in finding]
        if not present:
            continue
        first = present[0][1]
        if any(value != first for _, value in present[1:]):
            raise FindingValidationError(f"conflicting aliases for finding field: {target}")
        canonical[target] = first
    return canonical


def _validate_line_numbers(path: Path, raw_lines: Any) -> None:
    if isinstance(raw_lines, int):
        numbers = [raw_lines]
    elif isinstance(raw_lines, str):
        pieces = [piece.strip() for piece in raw_lines.split(",")]
        numbers = []
        for piece in pieces:
            if "-" in piece:
                start, end = piece.split("-", 1)
                if not start.isdigit() or not end.isdigit() or int(start) > int(end):
                    raise FindingValidationError(f"invalid evidence line range: {raw_lines}")
                numbers.extend((int(start), int(end)))
            elif piece.isdigit():
                numbers.append(int(piece))
            else:
                raise FindingValidationError(f"invalid evidence line: {raw_lines}")
    elif isinstance(raw_lines, list) and all(isinstance(item, int) for item in raw_lines):
        numbers = raw_lines
    else:
        raise FindingValidationError("evidence lines must be an integer, range string, or integer list")
    if not numbers or any(number < 1 for number in numbers):
        raise FindingValidationError("evidence lines must be positive")
    content = path.read_bytes()
    line_count = content.count(b"\n") + (1 if content and not content.endswith(b"\n") else 0)
    if any(number > line_count for number in numbers):
        raise FindingValidationError("evidence line is outside the referenced file")


def _validate_evidence_item(item: Any, snapshot: Mapping[str, Any]) -> None:
    root = Path(snapshot["repo_root"])
    if isinstance(item, str):
        match = re.fullmatch(r"(?P<path>.+?):(?P<line>[1-9][0-9]*)", item.strip())
        if match is None:
            raise FindingValidationError(
                "string evidence must use repository-relative path:line"
            )
        item = {"path": match.group("path"), "lines": match.group("line")}
    if not isinstance(item, Mapping):
        raise FindingValidationError("evidence items must be path or runtime evidence objects")

    if _has_content(item.get("path")):
        try:
            relative = _normalize_repo_path(str(item["path"]))
        except WorkspaceDrift as error:
            raise FindingValidationError(str(error)) from error
        target = (root / relative).resolve()
        if not _is_within(target, root) or not target.is_file():
            raise FindingValidationError(
                f"evidence path must reference a repository file: {relative}"
            )
        if not _has_content(item.get("lines")):
            raise FindingValidationError("code evidence requires exact lines")
        _validate_line_numbers(target, item["lines"])
        return

    if not (
        (_has_content(item.get("command")) or _has_content(item.get("artifact")))
        and _has_content(item.get("observation"))
    ):
        raise FindingValidationError(
            "runtime evidence requires command or artifact plus an observation"
        )


def validate_finding(
    finding: Mapping[str, Any], snapshot: Mapping[str, Any]
) -> dict[str, Any]:
    """Return a canonical finding after enforcing state and confirmed evidence."""

    canonical = _canonicalize_finding(finding)
    finding_id = canonical.get("id")
    if not isinstance(finding_id, str) or not FINDING_ID_PATTERN.fullmatch(finding_id):
        raise FindingValidationError("finding id must match AUD- followed by at least three digits")
    status = canonical.get("status")
    if status not in FINDING_STATUSES:
        raise FindingValidationError(
            "invalid finding status; expected one of: " + ", ".join(sorted(FINDING_STATUSES))
        )
    severity = canonical.get("severity")
    if severity is not None and severity not in SEVERITIES:
        raise FindingValidationError("severity must be one of P0, P1, P2, or P3")

    if status == "confirmed":
        required = (
            "severity",
            "category",
            "summary",
            "evidence_paths_lines",
            "relevant_call_chain_data_flow",
            "claim",
            "counter_evidence_checked",
            "risk_impact",
            "confidence",
            "suggested_next_action",
            "snapshot",
        )
        missing = [name for name in required if not _has_content(canonical.get(name))]
        if missing:
            raise FindingValidationError(
                "confirmed finding is missing required evidence fields: " + ", ".join(missing)
            )
        evidence = canonical["evidence_paths_lines"]
        if not isinstance(evidence, list) or not evidence:
            raise FindingValidationError(
                "confirmed finding evidence_paths_lines must be a non-empty list"
            )
        for item in evidence:
            _validate_evidence_item(item, snapshot)
        if canonical["confidence"] not in {"high", "medium"}:
            raise FindingValidationError(
                "confirmed finding confidence must be high or medium"
            )
        snapshot_reference = canonical["snapshot"]
        if isinstance(snapshot_reference, Mapping):
            snapshot_reference = snapshot_reference.get("snapshot_fingerprint")
        if snapshot_reference != snapshot["snapshot_fingerprint"]:
            raise FindingValidationError(
                "confirmed finding snapshot must match the current AuditSnapshot fingerprint"
            )
        canonical["snapshot"] = snapshot_reference
    return canonical


def _state_path(repo: Path, run_id: str) -> Path:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("run_id may contain only letters, digits, dot, underscore, and dash")
    relative = _git(
        repo,
        "rev-parse",
        "--git-path",
        f"dev-harness/codebase-audit/{run_id}/state.json",
    ).decode().strip()
    path = Path(relative)
    if not path.is_absolute():
        path = repo / path
    return path.resolve()


class AuditStateStore:
    """Atomic Git-private state for an audit that can resume in a new session."""

    def __init__(self, repo: Path, path: Path):
        self.repo = repo
        self.path = path

    @classmethod
    def initialize(
        cls,
        repo: str | Path,
        run_id: str,
        context_fingerprint: str,
        scope: str | Sequence[str],
        docs_root: str | Path | None = None,
    ) -> "AuditStateStore":
        root = _git_root(Path(repo).resolve())
        store = cls(root, _state_path(root, run_id))
        if store.path.exists():
            state = store.load()
            if state.get("RunId") != run_id:
                raise StateTransitionError("existing audit state does not match run_id")
            expected_scope = _normalize_scope(scope)
            snapshot = state["AuditSnapshot"]
            selected_docs = resolve_docs_root(root, docs_root).relative_to(root).as_posix()
            if snapshot["scope"] != expected_scope or snapshot["docs_root"] != selected_docs:
                raise StateTransitionError("existing audit state has a different scope or docs root")
            store.verify_workspace(context_fingerprint)
            return store

        snapshot = create_audit_snapshot(root, context_fingerprint, scope, docs_root)
        store._write(
            {
                "SchemaVersion": SCHEMA_VERSION,
                "RunId": run_id,
                "Status": "ACTIVE",
                "NeedsReverification": False,
                "StaleReasons": [],
                "AuditSnapshot": snapshot,
                "Tasks": {},
                "Findings": {},
                "CrossModuleReview": {"Status": "pending"},
                "Revision": 0,
            }
        )
        return store

    @classmethod
    def resume(
        cls,
        repo: str | Path,
        run_id: str,
        context_fingerprint: str,
    ) -> "AuditStateStore":
        root = _git_root(Path(repo).resolve())
        path = _state_path(root, run_id)
        if not path.is_file():
            raise StateTransitionError(f"audit run does not exist: {run_id}")
        store = cls(root, path)
        state = store.load()
        if state.get("RunId") != run_id:
            raise StateTransitionError("audit state RunId does not match its path")
        store.verify_workspace(context_fingerprint)
        return store

    @classmethod
    def open(cls, repo: str | Path, run_id: str) -> "AuditStateStore":
        """Open persisted state without claiming that its evidence is current."""

        root = _git_root(Path(repo).resolve())
        path = _state_path(root, run_id)
        if not path.is_file():
            raise StateTransitionError(f"audit run does not exist: {run_id}")
        return cls(root, path)

    def load(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, state: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix="state.tmp-", dir=self.path.parent
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(state, stream, ensure_ascii=False, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if temporary.exists():
                temporary.unlink()

    def _mark_stale(self, reason: str) -> dict[str, Any]:
        state = self.load()
        state["Status"] = "STALE"
        state["NeedsReverification"] = True
        reasons = state.setdefault("StaleReasons", [])
        if reason not in reasons:
            reasons.append(reason)
        for finding in state.get("Findings", {}).values():
            if finding.get("status") == "confirmed":
                finding["previous_status"] = "confirmed"
                finding["status"] = "stale"
                finding["stale_reason"] = reason
        state["Revision"] = int(state.get("Revision", 0)) + 1
        self._write(state)
        return state

    def verify_workspace(self, context_fingerprint: str) -> WorkspaceValidation:
        state = self.load()
        try:
            return validate_workspace(state["AuditSnapshot"], context_fingerprint)
        except WorkspaceDrift as error:
            self._mark_stale(str(error))
            raise

    def status(self, context_fingerprint: str | None = None) -> dict[str, Any]:
        validation_error: str | None = None
        if context_fingerprint is not None:
            try:
                self.verify_workspace(context_fingerprint)
            except WorkspaceDrift as error:
                validation_error = str(error)
        state = self.load()
        task_counts = Counter(
            task.get("status", "unknown") for task in state.get("Tasks", {}).values()
        )
        finding_counts = Counter(
            finding.get("status", "unknown")
            for finding in state.get("Findings", {}).values()
        )
        result: dict[str, Any] = {
            "RunId": state["RunId"],
            "Status": state["Status"],
            "NeedsReverification": state["NeedsReverification"],
            "Revision": state["Revision"],
            "TaskCounts": dict(sorted(task_counts.items())),
            "FindingCounts": dict(sorted(finding_counts.items())),
            "StatePath": str(self.path),
            "State": state,
        }
        if validation_error is not None:
            result["ValidationError"] = validation_error
        return result

    def _require_active(self, state: Mapping[str, Any]) -> None:
        if state.get("Status") != "ACTIVE" or state.get("NeedsReverification"):
            raise StateTransitionError(
                "audit run is STALE/NeedsReverification; start a new snapshot before checkpointing"
            )

    def checkpoint_task(
        self,
        task_id: str,
        status: str,
        context_fingerprint: str,
        checkpoint: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not TASK_ID_PATTERN.fullmatch(task_id):
            raise StateTransitionError("invalid task id")
        if status not in TASK_STATUSES:
            raise StateTransitionError(
                "invalid task status; expected one of: " + ", ".join(sorted(TASK_STATUSES))
            )
        state = self.load()
        self._require_active(state)
        self.verify_workspace(context_fingerprint)
        state = self.load()
        self._require_active(state)
        previous = state["Tasks"].get(task_id, {})
        state["Tasks"][task_id] = {
            "task_id": task_id,
            "status": status,
            "checkpoint": dict(checkpoint or {}),
            "revision": int(previous.get("revision", 0)) + 1,
        }
        state["Revision"] = int(state.get("Revision", 0)) + 1
        self._write(state)
        return state

    # Convenient API name matching the CLI command.
    checkpoint = checkpoint_task

    def checkpoint_cross_module(
        self,
        status: str,
        context_fingerprint: str,
        evidence: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if status not in {"pending", "in-progress", "completed", "blocked"}:
            raise StateTransitionError("invalid cross-module review status")
        if status == "completed" and not evidence:
            raise StateTransitionError(
                "completed cross-module review requires reconciliation evidence"
            )
        state = self.load()
        self._require_active(state)
        self.verify_workspace(context_fingerprint)
        state = self.load()
        state["CrossModuleReview"] = {
            "Status": status,
            "Evidence": dict(evidence or {}),
        }
        state["Revision"] = int(state.get("Revision", 0)) + 1
        self._write(state)
        return state

    def complete(self, context_fingerprint: str) -> dict[str, Any]:
        state = self.load()
        self._require_active(state)
        self.verify_workspace(context_fingerprint)
        state = self.load()
        tasks = state.get("Tasks", {})
        if not tasks:
            raise StateTransitionError("cannot complete an audit without task checkpoints")
        unfinished = sorted(
            task_id
            for task_id, task in tasks.items()
            if task.get("status") not in {"completed", "blocked"}
        )
        if unfinished:
            raise StateTransitionError(
                "cannot complete audit with unfinished tasks: " + ", ".join(unfinished)
            )
        review = state.get("CrossModuleReview", {})
        if review.get("Status") != "completed" or not review.get("Evidence"):
            raise StateTransitionError(
                "completed cross-module reconciliation is required before audit completion"
            )
        state["Status"] = "COMPLETED"
        state["CompletedSnapshot"] = state["AuditSnapshot"]["snapshot_fingerprint"]
        state["Revision"] = int(state.get("Revision", 0)) + 1
        self._write(state)
        return state

    def upsert_finding(
        self,
        finding: Mapping[str, Any],
        context_fingerprint: str,
    ) -> dict[str, Any]:
        state = self.load()
        self._require_active(state)
        self.verify_workspace(context_fingerprint)
        state = self.load()
        self._require_active(state)
        patch = _canonicalize_finding(finding)
        finding_id = patch.get("id")
        if not isinstance(finding_id, str):
            raise FindingValidationError("finding id is required")
        existing = state["Findings"].get(finding_id, {})
        merged = dict(existing)
        merged.update(patch)
        validated = validate_finding(merged, state["AuditSnapshot"])
        state["Findings"][finding_id] = validated
        state["Revision"] = int(state.get("Revision", 0)) + 1
        self._write(state)
        return state

    def validate_output(self, output_path: str | Path) -> Path:
        return validate_output_path(self.load()["AuditSnapshot"], output_path)


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _store_from_args(args: argparse.Namespace) -> AuditStateStore:
    return AuditStateStore.open(args.repo, args.run_id)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init", help="initialize or idempotently resume an audit run")
    init_parser.add_argument("--repo", default=".")
    init_parser.add_argument("--run-id", required=True)
    init_parser.add_argument("--context-fingerprint", required=True)
    init_parser.add_argument("--scope", action="append", required=True)
    init_parser.add_argument("--docs-root", choices=("doc", "docs"))

    for command, help_text in (
        ("resume", "resume a run after validating its snapshot"),
        ("verify-workspace", "validate Git, Context, and workspace identity"),
    ):
        command_parser = sub.add_parser(command, help=help_text)
        command_parser.add_argument("--repo", default=".")
        command_parser.add_argument("--run-id", required=True)
        command_parser.add_argument("--context-fingerprint", required=True)

    status_parser = sub.add_parser("status", help="show durable status without chat context")
    status_parser.add_argument("--repo", default=".")
    status_parser.add_argument("--run-id", required=True)
    status_parser.add_argument("--context-fingerprint")

    checkpoint_parser = sub.add_parser("checkpoint", help="persist one audit task checkpoint")
    checkpoint_parser.add_argument("--repo", default=".")
    checkpoint_parser.add_argument("--run-id", required=True)
    checkpoint_parser.add_argument("--context-fingerprint", required=True)
    checkpoint_parser.add_argument("--task-id", required=True)
    checkpoint_parser.add_argument("--task-status", choices=sorted(TASK_STATUSES), required=True)
    checkpoint_parser.add_argument("--checkpoint-json", default="{}")

    finding_parser = sub.add_parser("upsert-finding", help="validate and persist a finding")
    finding_parser.add_argument("--repo", default=".")
    finding_parser.add_argument("--run-id", required=True)
    finding_parser.add_argument("--context-fingerprint", required=True)
    finding_parser.add_argument("--finding-json", required=True)

    cross_module_parser = sub.add_parser(
        "checkpoint-cross-module",
        help="persist mandatory cross-module reconciliation evidence",
    )
    cross_module_parser.add_argument("--repo", default=".")
    cross_module_parser.add_argument("--run-id", required=True)
    cross_module_parser.add_argument("--context-fingerprint", required=True)
    cross_module_parser.add_argument(
        "--review-status",
        choices=("pending", "in-progress", "completed", "blocked"),
        required=True,
    )
    cross_module_parser.add_argument("--evidence-json", default="{}")

    complete_parser = sub.add_parser(
        "complete", help="complete a run after task and cross-module gates"
    )
    complete_parser.add_argument("--repo", default=".")
    complete_parser.add_argument("--run-id", required=True)
    complete_parser.add_argument("--context-fingerprint", required=True)

    output_parser = sub.add_parser("validate-output", help="validate an audit-relative output path")
    output_parser.add_argument("--repo", default=".")
    output_parser.add_argument("--run-id", required=True)
    output_parser.add_argument("--path", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            store = AuditStateStore.initialize(
                args.repo,
                args.run_id,
                args.context_fingerprint,
                args.scope,
                args.docs_root,
            )
            _print_json({"state_path": str(store.path), "state": store.load()})
        elif args.command == "resume":
            store = AuditStateStore.resume(
                args.repo, args.run_id, args.context_fingerprint
            )
            _print_json({"state_path": str(store.path), "state": store.load()})
        elif args.command == "status":
            _print_json(_store_from_args(args).status(args.context_fingerprint))
        elif args.command == "verify-workspace":
            result = _store_from_args(args).verify_workspace(args.context_fingerprint)
            _print_json(result._asdict())
        elif args.command == "checkpoint":
            checkpoint = json.loads(args.checkpoint_json)
            if not isinstance(checkpoint, dict):
                raise StateTransitionError("checkpoint JSON must be an object")
            state = _store_from_args(args).checkpoint_task(
                args.task_id,
                args.task_status,
                args.context_fingerprint,
                checkpoint,
            )
            _print_json(state)
        elif args.command == "upsert-finding":
            finding = json.loads(args.finding_json)
            state = _store_from_args(args).upsert_finding(
                finding, args.context_fingerprint
            )
            _print_json(state)
        elif args.command == "checkpoint-cross-module":
            evidence = json.loads(args.evidence_json)
            if not isinstance(evidence, dict):
                raise StateTransitionError("cross-module evidence JSON must be an object")
            state = _store_from_args(args).checkpoint_cross_module(
                args.review_status,
                args.context_fingerprint,
                evidence,
            )
            _print_json(state)
        elif args.command == "complete":
            state = _store_from_args(args).complete(args.context_fingerprint)
            _print_json(state)
        else:
            validated = _store_from_args(args).validate_output(args.path)
            _print_json({"path": str(validated)})
    except (AuditRuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
