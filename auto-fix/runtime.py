#!/usr/bin/env python3
"""Deterministic runtime for the dev-harness auto-fix contract."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path
from typing import Any, NamedTuple, Sequence


MODES = {"analyze", "fix", "commit", "unattended"}
COMPLETION_STATUSES = {"DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"}
SCHEMA_VERSION = 3
VALIDATION_PROFILES = {"fast", "standard", "strict"}
PROFILE_RANK = {"fast": 0, "standard": 1, "strict": 2}
REVIEW_MODES = {"self", "independent"}
REVIEW_OUTCOMES = {"pass", "pass_with_concerns", "fail", "unavailable"}
REPEAT_REASONS = {
    "environment-recovery",
    "wrong-failure-signature",
    "device-reset",
    "user-requested",
    "evidence-expired",
    "diff-changed",
}
CHANGE_IMPACTS = {"production", "test", "documentation", "shared-infrastructure"}
CHECK_NAMES = {"QuickCheck", "TestCheck", "BugfixCheck", "FullCheck"}
OBJECTIVE_SKIP_REASONS = {"device-required", "ui-only", "environment-unavailable", "no-test-seam"}
HARD_RISK_FLAGS = {
    "abi",
    "concurrency",
    "cross-repository",
    "permissions",
    "persistence",
    "security",
    "shared-infrastructure",
    "signing",
}
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


class WorkspaceDrift(RuntimeError):
    """Raised when the workspace no longer matches its ownership snapshot."""


class StateTransitionError(RuntimeError):
    """Raised when an auto-fix stage transition violates the contract."""


class StateWriteError(RuntimeError):
    """Raised with a stable code when private runtime state cannot be persisted."""

    def __init__(self, code: str, operation: str, message: str):
        self.code = code
        self.operation = operation
        super().__init__(f"{code}: {operation}: {message}")


class WorkspaceValidation(NamedTuple):
    changed_files: tuple[str, ...]
    diff_hash: str


def _default_profile_assessment() -> dict[str, Any]:
    return {"initial": None, "final": None, "upgraded": False}


def _migrate_state(state: dict[str, Any]) -> dict[str, Any]:
    """Upgrade legacy run state conservatively without weakening its validation."""
    migrated = dict(state)
    version = migrated.get("SchemaVersion", 1)
    if version not in {1, 2, SCHEMA_VERSION}:
        raise StateTransitionError(f"unsupported state SchemaVersion: {version}")
    migrated["SchemaVersion"] = SCHEMA_VERSION
    migrated.setdefault("ValidationProfile", "strict")
    if "SchemaVersion" not in state:
        migrated["ValidationProfile"] = "strict"
    migrated.setdefault("ProfileAssessment", _default_profile_assessment())
    migrated.setdefault("VerificationPlan", [])
    migrated.setdefault("ReviewMode", None)
    migrated.setdefault("ReviewOutcome", None)
    migrated.setdefault("RepeatExecutions", [])
    migrated.setdefault("ChangeImpacts", [])
    migrated.setdefault("ChangedFileImpacts", {})
    migrated.setdefault("FinalDiffHash", None)
    migrated.setdefault("VerificationBindings", {})
    migrated.setdefault("VerificationFailures", [])
    migrated.setdefault("FinalFileFingerprints", {})
    migrated.setdefault("FinalGitEntries", {})
    migrated.setdefault("CommitReceipt", None)
    if version < 3:
        # Old hashes include index placement, and old executions have no dependency
        # receipt. Preserve their history without manufacturing current evidence.
        migrated["ReviewDiffHash"] = None
        migrated["FinalDiffHash"] = None
        migrated["VerificationBindings"] = {}
        migrated["FinalFileFingerprints"] = {}
        migrated["FinalGitEntries"] = {}
        migrated["CommitReceipt"] = None
        if migrated.get("Mode") != "analyze":
            migrated["EvidenceRevalidationRequired"] = True
            if migrated.get("CompletionStatus") in {"DONE", "DONE_WITH_CONCERNS"}:
                migrated["CompletionStatus"] = None
            if migrated.get("Stage") in {"review", "final-verify", "commit"} or (
                migrated.get("Stage") == "report" and migrated.get("CompletionStatus") is None
            ):
                migrated["Stage"] = "verify"
    return migrated


def _validate_profile(profile: str, mode: str) -> None:
    if profile not in VALIDATION_PROFILES:
        raise StateTransitionError(f"unsupported ValidationProfile: {profile}")
    if mode == "unattended" and PROFILE_RANK[profile] < PROFILE_RANK["standard"]:
        raise StateTransitionError("unattended mode requires ValidationProfile standard or strict")


def _validate_profile_assessment(value: dict[str, Any], profile: str) -> None:
    if not isinstance(value, dict):
        raise StateTransitionError("ProfileAssessment must be an object")
    initial = value.get("initial")
    final = value.get("final")
    for label, assessment in (("initial", initial), ("final", final)):
        if assessment is None:
            continue
        if not isinstance(assessment, dict):
            raise StateTransitionError(f"ProfileAssessment.{label} must be an object")
        assessed_profile = assessment.get("profile")
        if assessed_profile not in VALIDATION_PROFILES:
            raise StateTransitionError(f"ProfileAssessment.{label}.profile is invalid")
        for field in ("reasons", "risk_flags"):
            items = assessment.get(field)
            if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
                raise StateTransitionError(f"ProfileAssessment.{label}.{field} must be a string array")
        required_checks = assessment.get("required_checks", [])
        if not isinstance(required_checks, list) or not set(required_checks) <= CHECK_NAMES:
            raise StateTransitionError(
                f"ProfileAssessment.{label}.required_checks contains an unsupported check"
            )
        if set(assessment["risk_flags"]).intersection(HARD_RISK_FLAGS) and assessed_profile != "strict":
            raise StateTransitionError(
                f"ProfileAssessment.{label} contains a hard risk and must use strict"
            )
    active = final or initial
    if active is not None and active["profile"] != profile:
        raise StateTransitionError("active ProfileAssessment must match ValidationProfile")
    if initial is not None and final is not None:
        upgraded = PROFILE_RANK[final["profile"]] > PROFILE_RANK[initial["profile"]]
        if PROFILE_RANK[final["profile"]] < PROFILE_RANK[initial["profile"]]:
            raise StateTransitionError("ProfileAssessment cannot downgrade")
        if bool(value.get("upgraded")) != upgraded:
            raise StateTransitionError("ProfileAssessment.upgraded does not match assessed profiles")


def _validate_skip_record(record: dict[str, Any], reason: Any) -> None:
    if not isinstance(reason, str) or reason not in OBJECTIVE_SKIP_REASONS:
        raise StateTransitionError("skip requires an allowed objective skip_reason")
    for field in ("skip_evidence", "alternative_verification", "remaining_risk"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            raise StateTransitionError(f"objective skip requires {field}")


def _regression_skip_reason(evidence: dict[str, Any]) -> str | None:
    if "RegressionSkipReason" not in evidence and "skip_reason" not in evidence:
        return None
    reason = evidence.get("RegressionSkipReason", evidence.get("skip_reason"))
    if "skip_reason" in evidence and evidence["skip_reason"] != reason:
        raise StateTransitionError("conflicting regression skip reasons")
    _validate_skip_record(evidence, reason)
    return reason


def _validate_verification_plan(plan: list[dict[str, Any]]) -> None:
    if not isinstance(plan, list):
        raise StateTransitionError("VerificationPlan must be an array")
    ids: set[str] = set()
    executions: set[tuple[str, str]] = set()
    for item in plan:
        if not isinstance(item, dict):
            raise StateTransitionError("VerificationPlan entries must be objects")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id or item_id in ids:
            raise StateTransitionError("VerificationPlan ids must be unique non-empty strings")
        ids.add(item_id)
        command = item.get("command")
        diff_hash = item.get("diff_hash")
        if not isinstance(command, str) or not command or not isinstance(diff_hash, str) or not diff_hash:
            raise StateTransitionError("VerificationPlan command and diff_hash are required")
        if item.get("status") not in {"passed", "failed", "skipped"}:
            raise StateTransitionError("VerificationPlan status is invalid")
        if item["status"] == "skipped":
            _validate_skip_record(item, item.get("skip_reason"))
            if item.get("subsumes"):
                raise StateTransitionError("skipped verification cannot subsume passed checks")
        if item.get("check") not in CHECK_NAMES:
            raise StateTransitionError("VerificationPlan check is invalid")
        depends_on = item.get("depends_on")
        if (
            not isinstance(depends_on, list)
            or not depends_on
            or not set(depends_on) <= CHANGE_IMPACTS
        ):
            raise StateTransitionError("VerificationPlan depends_on contains an invalid impact")
        if "depends_on_files" in item:
            files = item["depends_on_files"]
            if not isinstance(files, list) or not files or not all(isinstance(p, str) for p in files):
                raise StateTransitionError("VerificationPlan depends_on_files must be a non-empty path array")
            _normalize_paths(files)
        proves = item.get("proves", [] if item["status"] == "skipped" else None)
        if not isinstance(proves, list) or (not proves and item["status"] != "skipped"):
            raise StateTransitionError("VerificationPlan proves must contain evidence-backed obligations")
        obligations: set[str] = set()
        for proof in proves:
            if not isinstance(proof, dict):
                raise StateTransitionError("VerificationPlan proof must be an object")
            obligation = proof.get("obligation")
            evidence = proof.get("evidence")
            if not isinstance(obligation, str) or not obligation or not isinstance(evidence, str) or not evidence:
                raise StateTransitionError("VerificationPlan proof requires obligation and evidence")
            obligations.add(obligation)
        subsumes = item.get("subsumes", {})
        if not isinstance(subsumes, dict) or not set(subsumes) <= CHECK_NAMES:
            raise StateTransitionError("VerificationPlan subsumes must map supported checks")
        for check, references in subsumes.items():
            if (
                not isinstance(references, list)
                or not references
                or not all(isinstance(reference, str) for reference in references)
                or not set(references) <= obligations
            ):
                raise StateTransitionError(
                    f"VerificationPlan subsumes {check} must reference proved obligations"
                )
        repeat_reason = item.get("repeat_reason")
        execution = (command, diff_hash)
        if execution in executions and repeat_reason not in REPEAT_REASONS:
            raise StateTransitionError(
                "repeated command for the same diff requires an allowed repeat_reason"
            )
        if repeat_reason is not None and repeat_reason not in REPEAT_REASONS:
            raise StateTransitionError("VerificationPlan repeat_reason is invalid")
        executions.add(execution)


def _covered_checks(plan: list[dict[str, Any]]) -> set[str]:
    covered: set[str] = set()
    for item in plan:
        if item.get("status") != "passed":
            continue
        covered.add(item["check"])
        covered.update(item.get("subsumes", {}))
    return covered


def _git(repo: Path, *args: str, input_data: bytes | None = None) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
        input=input_data,
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
        _nul_paths(_git(repo, "diff", "--name-only", "--no-renames", "-z"))
        | _nul_paths(_git(repo, "diff", "--cached", "--name-only", "--no-renames", "-z"))
        | _nul_paths(_git(repo, "ls-files", "--others", "--exclude-standard", "-z"))
    )


def _normalize_paths(paths: Sequence[str]) -> tuple[str, ...]:
    normalized: set[str] = set()
    for raw in paths:
        path = Path(raw)
        if path.is_absolute() or ".." in path.parts or not raw.strip():
            raise WorkspaceDrift(f"invalid changed file path: {raw!r}")
        value = path.as_posix()
        if value in {"", "."}:
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
    return _content_diff_hash(snapshot, _content_fingerprints(root, changed_files))


def _content_fingerprint(relative: str, mode: str, content: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(relative.encode("utf-8", errors="surrogateescape"))
    digest.update(b"\0" + mode.encode() + b"\0" + content)
    return digest.hexdigest()


def _trusts_filemode(root: Path) -> bool:
    return _git(root, "config", "--type=bool", "--default=true", "--get", "core.filemode").strip() == b"true"


def _regular_file_mode(root: Path, relative: str, path: Path, trust_filemode: bool) -> str:
    if trust_filemode:
        return "100755" if path.stat().st_mode & 0o100 else "100644"
    # Git preserves the index mode when filesystem executable bits are unreliable.
    # Explicit update-index --chmod changes this effective mode and must invalidate
    # the review, while ordinary git add of the same content keeps it stable.
    indexed = _git(root, "ls-files", "--stage", "-z", "--", relative)
    if indexed:
        records = indexed.rstrip(b"\0").split(b"\0")
        if len(records) != 1:
            raise WorkspaceDrift(f"unmerged index entry: {relative}")
        metadata, name = records[0].split(b"\t", 1)
        index_mode, _, stage = metadata.decode().split()
        if stage != "0" or name.decode(errors="surrogateescape") != relative:
            raise WorkspaceDrift(f"invalid index entry: {relative}")
        if index_mode in {"100644", "100755"}:
            return index_mode
    return "100644"


def _content_fingerprints(root: Path, paths: Sequence[str]) -> dict[str, str]:
    """Content identity excludes index placement; ownership still uses Git diffs."""
    fingerprints = {}
    trust_filemode = _trusts_filemode(root)
    for relative in _normalize_paths(paths):
        path = root / relative
        if path.is_symlink():
            mode, content = "120000", os.fsencode(os.readlink(path))
        elif path.is_file():
            mode = _regular_file_mode(root, relative, path, trust_filemode)
            content = path.read_bytes()
        elif not path.exists():
            mode, content = "missing", b""
        else:
            raise WorkspaceDrift(f"unsupported changed file type: {relative}")
        fingerprints[relative] = _content_fingerprint(relative, mode, content)
    return fingerprints


def _content_diff_hash(snapshot: dict[str, Any], fingerprints: dict[str, str]) -> str:
    digest = hashlib.sha256()
    digest.update(f"dev-harness-diff-v2\0{snapshot['base_sha']}\0".encode())
    for path, fingerprint in sorted(fingerprints.items()):
        digest.update(path.encode("utf-8", errors="surrogateescape"))
        digest.update(b"\0")
        digest.update(fingerprint.encode())
        digest.update(b"\0")
    return digest.hexdigest()


def _dependency_fingerprints(state: dict[str, Any], item: dict[str, Any]) -> dict[str, str]:
    classifications = state.get("ChangedFileImpacts", {})
    fallback = set(state.get("ChangeImpacts") or ["shared-infrastructure"])
    paths = set(item.get("depends_on_files", []))
    for path in state.get("ChangedFiles", []):
        impacts = {classifications[path]} if path in classifications else fallback
        if "shared-infrastructure" in impacts or (
            "depends_on_files" not in item and impacts.intersection(item["depends_on"])
        ):
            paths.add(path)
    return _content_fingerprints(Path(state["WorkspaceSnapshot"]["repo_root"]), sorted(paths))


def _execution_digest(item: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(item, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _binding_is_fresh(state: dict[str, Any], item: dict[str, Any]) -> bool:
    binding = state.get("VerificationBindings", {}).get(item["id"], {})
    return (
        binding.get("execution") == _execution_digest(item)
        and binding.get("dependencies") == _dependency_fingerprints(state, item)
    )


def _bind_verification_plan(state: dict[str, Any]) -> None:
    current_hash = _content_diff_hash(state["WorkspaceSnapshot"], _content_fingerprints(
        Path(state["WorkspaceSnapshot"]["repo_root"]), state.get("ChangedFiles", [])))
    bindings = {}
    fresh_pass_ids = set()
    for item in state["VerificationPlan"]:
        if item["status"] not in {"passed", "skipped"}:
            continue
        if _binding_is_fresh(state, item):
            bindings[item["id"]] = state["VerificationBindings"][item["id"]]
        elif item["diff_hash"] == current_hash:
            bindings[item["id"]] = {
                "execution": _execution_digest(item),
                "dependencies": _dependency_fingerprints(state, item),
            }
            if item["status"] == "passed":
                fresh_pass_ids.add(item["id"])
        else:
            raise StateTransitionError("verification evidence is stale or unbound; record a fresh execution with the current diff hash")
    state["VerificationBindings"] = bindings
    # A skip cannot erase an observed failure, even if a later checkpoint replaces
    # the plan array. Only a fresh passing execution can clear it; reusing a pass
    # observed before the failure or entering implement does not establish recovery.
    failures = {tuple(key) for key in state.get("VerificationFailures", [])}
    for item in state["VerificationPlan"]:
        key = (item["command"], item["check"])
        if item["status"] == "failed":
            failures.add(key)
        elif item["status"] == "passed" and item["id"] in fresh_pass_ids:
            failures.discard(key)
    state["VerificationFailures"] = [list(key) for key in sorted(failures)]


def _expected_git_entries(root: Path, paths: Sequence[str]) -> dict[str, dict[str, str]]:
    """The reviewed bytes as Git will store them, including configured text filters."""
    entries = {}
    trust_filemode = _trusts_filemode(root)
    for relative in _normalize_paths(paths):
        path = root / relative
        if path.is_symlink():
            mode = "120000"
            object_id = _git(root, "hash-object", "--stdin", input_data=os.fsencode(os.readlink(path))).decode().strip()
        elif path.is_file():
            mode = _regular_file_mode(root, relative, path, trust_filemode)
            object_id = _git(root, "hash-object", f"--path={relative}", "--stdin", input_data=path.read_bytes()).decode().strip()
        elif not path.exists():
            mode, object_id = "missing", ""
        else:
            raise WorkspaceDrift(f"unsupported changed file type: {relative}")
        entries[relative] = {"mode": mode, "object": object_id}
    return entries


def _validate_staged_content(state: dict[str, Any]) -> None:
    root = Path(state["WorkspaceSnapshot"]["repo_root"])
    staged = sorted(_nul_paths(_git(root, "diff", "--cached", "--name-only", "--no-renames", "-z")))
    if staged != list(_normalize_paths(state["ChangedFiles"])):
        raise WorkspaceDrift("staged_scope_conflict: stage exactly AutoFixChangedFiles before checkpoint commit")
    entries = {}
    for relative in staged:
        raw = _git(root, "ls-files", "--stage", "-z", "--", relative)
        if not raw:
            mode, object_id = "missing", ""
        else:
            records = raw.rstrip(b"\0").split(b"\0")
            if len(records) != 1:
                raise WorkspaceDrift(f"unmerged index entry: {relative}")
            metadata, name = records[0].split(b"\t", 1)
            mode, object_id, stage = metadata.decode().split()
            if stage != "0" or name.decode(errors="surrogateescape") != relative:
                raise WorkspaceDrift(f"invalid index entry: {relative}")
        entries[relative] = {"mode": mode, "object": object_id}
    if entries != state.get("FinalGitEntries"):
        raise WorkspaceDrift("staged content does not match the final reviewed tree")


def _commit_receipt(state: dict[str, Any], sha: str) -> dict[str, Any]:
    """Accept exactly the reviewed one-parent commit, never arbitrary HEAD drift."""
    snapshot = state["WorkspaceSnapshot"]
    root = _git_root(Path(snapshot["repo_root"]))
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", sha):
        raise StateTransitionError("commit must be a full Git object ID")
    if state["Mode"] not in {"commit", "unattended"} or not state.get("FinalDiffHash"):
        raise StateTransitionError("commit requires authorization and final verification")
    if _git(root, "rev-parse", "HEAD").decode().strip() != sha:
        raise WorkspaceDrift("recorded commit must be the current HEAD")
    if _git(root, "rev-parse", "--abbrev-ref", "HEAD").decode().strip() != snapshot["branch"]:
        raise WorkspaceDrift("branch drifted since WorkspaceSnapshot")
    parents = _git(root, "rev-list", "--parents", "-n", "1", sha).decode().split()
    if parents != [sha, snapshot["base_sha"]]:
        raise WorkspaceDrift("authorized commit must have the snapshot HEAD as its single parent")
    paths = sorted(_nul_paths(_git(root, "diff-tree", "--no-commit-id", "--name-only", "--no-renames", "-r", "-z", snapshot["base_sha"], sha)))
    if paths != list(_normalize_paths(state["ChangedFiles"])):
        raise WorkspaceDrift("committed paths do not exactly match AutoFixChangedFiles")
    entries = {}
    for relative in paths:
        entry = _git(root, "ls-tree", "-z", sha, "--", relative)
        if not entry:
            mode, object_id = "missing", ""
        else:
            metadata, name = entry.rstrip(b"\0").split(b"\t", 1)
            mode, kind, object_id = metadata.decode().split()
            if kind != "blob" or name.decode(errors="surrogateescape") != relative:
                raise WorkspaceDrift(f"unsupported committed file type: {relative}")
        entries[relative] = {"mode": mode, "object": object_id}
    if entries != state.get("FinalGitEntries") or _content_diff_hash(snapshot, state.get("FinalFileFingerprints", {})) != state["FinalDiffHash"]:
        raise WorkspaceDrift("committed tree does not match the final reviewed content")
    return {"sha": sha, "parent": snapshot["base_sha"],
            "tree": _git(root, "rev-parse", f"{sha}^{{tree}}").decode().strip(),
            "changed_files": paths, "diff_hash": state["FinalDiffHash"]}


def _validate_state_workspace(state: dict[str, Any]) -> WorkspaceValidation:
    receipt = state.get("CommitReceipt")
    if not receipt:
        return validate_workspace(state["WorkspaceSnapshot"], state.get("ChangedFiles", []))
    if _commit_receipt(state, receipt["sha"]) != receipt or state["Commits"] != [receipt["sha"]]:
        raise WorkspaceDrift("authorized commit receipt is inconsistent")
    effective = {**state["WorkspaceSnapshot"], "base_sha": receipt["sha"]}
    validate_workspace(effective, [])
    fingerprints = _content_fingerprints(Path(effective["repo_root"]), state["ChangedFiles"])
    if fingerprints != state["FinalFileFingerprints"]:
        raise WorkspaceDrift("workspace content differs from the authorized commit")
    return WorkspaceValidation(tuple(state["ChangedFiles"]), _content_diff_hash(state["WorkspaceSnapshot"], fingerprints))


class AutoFixStateStore:
    def __init__(self, repo: Path, path: Path):
        self.repo = repo
        self.path = path

    @classmethod
    def initialize(
        cls,
        repo: str | Path,
        run_id: str,
        mode: str,
        validation_profile: str = "strict",
    ) -> "AutoFixStateStore":
        if mode not in MODES:
            raise ValueError(f"unsupported mode: {mode}")
        _validate_profile(validation_profile, mode)
        if not RUN_ID_PATTERN.fullmatch(run_id):
            raise ValueError("run_id may contain only letters, digits, dot, underscore, and dash")
        root = _git_root(Path(repo).resolve())
        relative = _git(root, "rev-parse", "--git-path", f"dev-harness/auto-fix/{run_id}/state.json").decode().strip()
        path = Path(relative)
        if not path.is_absolute():
            path = root / path
        store = cls(root, path.resolve())
        if store.path.exists():
            raw = json.loads(store.path.read_text(encoding="utf-8"))
            existing = _migrate_state(raw)
            if existing.get("RunId") != run_id or existing.get("Mode") != mode:
                raise StateTransitionError("existing run state does not match run_id and mode")
            _validate_profile(existing["ValidationProfile"], mode)
            if raw != existing:
                store._write(existing)
            head = _git(root, "rev-parse", "HEAD").decode().strip()
            if existing.get("EvidenceRevalidationRequired") and head != existing["WorkspaceSnapshot"]["base_sha"]:
                raise StateTransitionError("legacy evidence cannot authenticate a changed HEAD; review the committed changes and start a new run")
            if (existing["Stage"] == "commit" and not existing.get("CommitReceipt")
                    and head != existing["WorkspaceSnapshot"]["base_sha"]):
                # The process may have stopped after Git committed but before the
                # receipt checkpoint. The same exact-tree gate applies on recovery.
                store.checkpoint("commit", commit=head)
            else:
                _validate_state_workspace(existing)
            return store
        snapshot = create_snapshot(root)
        store._write(
            {
                "RunId": run_id,
                "SchemaVersion": SCHEMA_VERSION,
                "Mode": mode,
                "ValidationProfile": validation_profile,
                "ProfileAssessment": _default_profile_assessment(),
                "BaseSha": snapshot["base_sha"],
                "Stage": "preflight",
                "WorkspaceSnapshot": snapshot,
                "Hypotheses": [],
                "RegressionRedEvidence": {},
                "ChangedFiles": [],
                "VerificationEvidence": {},
                "VerificationPlan": [],
                "ReviewDiffHash": None,
                "ReviewMode": None,
                "ReviewOutcome": None,
                "RepeatExecutions": [],
                "ChangeImpacts": [],
                "ChangedFileImpacts": {},
                "FinalDiffHash": None,
                "Commits": [],
                "IssueCommentMarker": None,
                "CompletionStatus": None,
            }
        )
        return store

    def load(self) -> dict[str, Any]:
        return _migrate_state(json.loads(self.path.read_text(encoding="utf-8")))

    def _write(self, state: dict[str, Any]) -> None:
        state = _migrate_state(state)
        temporary: Path | None = None
        operation = "mkdir"
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            operation = "create"
            for _ in range(3):
                candidate = self.path.with_name(
                    f".{self.path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp"
                )
                try:
                    with candidate.open("x", encoding="utf-8") as handle:
                        temporary = candidate
                        handle.write(payload)
                        handle.flush()
                        operation = "fsync"
                        os.fsync(handle.fileno())
                    break
                except FileExistsError:
                    continue
            else:
                raise StateWriteError(
                    "state_write_collision", "create", "temporary state name collided 3 times"
                )
            operation = "replace"
            os.replace(temporary, self.path)
            temporary = None
        except StateWriteError:
            raise
        except OSError as exc:
            code = (
                "state_write_denied"
                if isinstance(exc, PermissionError)
                or exc.errno in {errno.EACCES, errno.EPERM, errno.EROFS}
                else "state_write_failed"
            )
            raise StateWriteError(code, operation, str(exc)) from exc
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass

    def checkpoint(
        self,
        stage: str,
        *,
        hypotheses: list[dict[str, Any]] | None = None,
        regression_red: dict[str, Any] | None = None,
        changed_files: Sequence[str] | None = None,
        verification: dict[str, Any] | None = None,
        validation_profile: str | None = None,
        profile_assessment: dict[str, Any] | None = None,
        verification_plan: list[dict[str, Any]] | None = None,
        review_mode: str | None = None,
        review_outcome: str | None = None,
        repeat_execution: dict[str, Any] | None = None,
        change_impacts: Sequence[str] | None = None,
        changed_file_impacts: dict[str, str] | None = None,
        review_diff_hash: str | None = None,
        commit: str | None = None,
        issue_comment_marker: str | None = None,
        completion_status: str | None = None,
    ) -> dict[str, Any]:
        state = self.load()
        current = state["Stage"]
        mode = state["Mode"]
        if stage != current:
            self._validate_transition(state, stage, completion_status)
        if changed_files is not None and stage != "implement":
            normalized_changes = list(_normalize_paths(changed_files))
            if normalized_changes != state.get("ChangedFiles", []):
                raise StateTransitionError("ChangedFiles may only change in implement")
        if (change_impacts is not None or changed_file_impacts is not None) and stage != "implement":
            raise StateTransitionError("change impacts may only be recorded in implement")
        if validation_profile is not None:
            _validate_profile(validation_profile, mode)
            current_profile = state["ValidationProfile"]
            if PROFILE_RANK[validation_profile] < PROFILE_RANK[current_profile]:
                raise StateTransitionError(
                    f"ValidationProfile downgrade is not allowed: {current_profile} -> {validation_profile}"
                )
            if PROFILE_RANK[validation_profile] > PROFILE_RANK[current_profile]:
                assessment = dict(state.get("ProfileAssessment") or _default_profile_assessment())
                assessment["upgraded"] = True
                state["ProfileAssessment"] = assessment
            state["ValidationProfile"] = validation_profile
        if profile_assessment is not None:
            _validate_profile_assessment(profile_assessment, state["ValidationProfile"])
            state["ProfileAssessment"] = profile_assessment
        if hypotheses is not None:
            state["Hypotheses"] = hypotheses
        if regression_red is not None:
            state["RegressionRedEvidence"] = regression_red
        if changed_files is not None:
            state["ChangedFiles"] = list(_normalize_paths(changed_files))
        if verification is not None:
            state["VerificationEvidence"] = verification
        if verification_plan is not None:
            _validate_verification_plan(verification_plan)
            state["VerificationPlan"] = verification_plan
        if review_mode is not None:
            if review_mode not in REVIEW_MODES:
                raise StateTransitionError(f"invalid ReviewMode: {review_mode}")
            state["ReviewMode"] = review_mode
        if review_outcome is not None:
            if review_outcome not in REVIEW_OUTCOMES:
                raise StateTransitionError(f"invalid ReviewOutcome: {review_outcome}")
            if state.get("ReviewOutcome") == "fail" and review_outcome != "fail":
                raise StateTransitionError(
                    "a failed review cannot be overridden in place; return to implement"
                )
            state["ReviewOutcome"] = review_outcome
        if repeat_execution is not None:
            reason = repeat_execution.get("reason") if isinstance(repeat_execution, dict) else None
            if reason not in REPEAT_REASONS:
                raise StateTransitionError("RepeatExecution requires an allowed reason")
            state["RepeatExecutions"].append(repeat_execution)
        if review_diff_hash is not None:
            state["ReviewDiffHash"] = review_diff_hash
        if commit is not None:
            if mode not in {"commit", "unattended"}:
                raise StateTransitionError(f"{mode} mode cannot record a commit")
            if stage != "commit":
                raise StateTransitionError("commit receipt may only be recorded in commit")
            receipt = _commit_receipt(state, commit)
            if state["Commits"] and state["Commits"] != [commit]:
                raise StateTransitionError("run already records a different commit")
            state["Commits"] = [commit]
            state["CommitReceipt"] = receipt
        if issue_comment_marker is not None:
            state["IssueCommentMarker"] = issue_comment_marker
        if completion_status is not None:
            if completion_status not in COMPLETION_STATUSES:
                raise StateTransitionError(f"invalid completion status: {completion_status}")
            state["CompletionStatus"] = completion_status
        if state.get("CompletionStatus") in {"DONE", "DONE_WITH_CONCERNS"} and stage != "report":
            raise StateTransitionError("successful completion may only be recorded in report")
        if stage == "implement":
            if changed_file_impacts is not None:
                if not isinstance(changed_file_impacts, dict):
                    raise StateTransitionError("changed_file_impacts must be an object")
                normalized_impact_paths = _normalize_paths(list(changed_file_impacts))
                if set(normalized_impact_paths) != set(state["ChangedFiles"]):
                    raise StateTransitionError(
                        "changed_file_impacts must classify every ChangedFiles path exactly once"
                    )
                if not all(impact in CHANGE_IMPACTS for impact in changed_file_impacts.values()):
                    raise StateTransitionError("changed_file_impacts contains an unsupported impact")
                state["ChangedFileImpacts"] = {
                    path: changed_file_impacts[path] for path in normalized_impact_paths
                }
                impacts = set(changed_file_impacts.values())
            else:
                impacts = set(change_impacts or ["shared-infrastructure"])
                state["ChangedFileImpacts"] = {}
            if not impacts <= CHANGE_IMPACTS:
                raise StateTransitionError("change_impacts contains an unsupported impact")
            if "shared-infrastructure" in impacts:
                state["ValidationProfile"] = "strict"
            elif (
                state["ValidationProfile"] == "fast"
                and sum(
                    impact == "production"
                    for impact in state["ChangedFileImpacts"].values()
                )
                > 2
            ):
                state["ValidationProfile"] = "standard"
            state["ChangeImpacts"] = sorted(impacts)
            assessment = dict(state.get("ProfileAssessment") or _default_profile_assessment())
            initial = assessment.get("initial")
            assessment["final"] = None
            assessment["upgraded"] = bool(
                initial
                and PROFILE_RANK[state["ValidationProfile"]]
                > PROFILE_RANK[initial["profile"]]
            )
            state["ProfileAssessment"] = assessment
            # Classification describes all task files, not just the last edit.
            # Retain only executions whose actual dependency contents still match.
            retained = [item for item in state.get("VerificationPlan", [])
                        if item["status"] in {"passed", "skipped"} and _binding_is_fresh(state, item)]
            state["VerificationPlan"] = retained
            state["VerificationBindings"] = {
                item["id"]: state["VerificationBindings"][item["id"]] for item in retained}
            if not retained:
                state["VerificationEvidence"] = {}
            state["ReviewDiffHash"] = None
            state["ReviewMode"] = None
            state["ReviewOutcome"] = None
            state["FinalDiffHash"] = None
            state["FinalFileFingerprints"] = {}
            state["FinalGitEntries"] = {}
        if verification_plan is not None:
            _validate_state_workspace(state)
            _bind_verification_plan(state)
        if stage == "final-verify":
            state["FinalDiffHash"] = None
            state["FinalFileFingerprints"] = {}
            state["FinalGitEntries"] = {}
        state["Stage"] = stage
        self._validate_stage(state)
        self._write(state)
        return state

    @staticmethod
    def _validate_transition(
        state: dict[str, Any], target: str, completion_status: str | None = None
    ) -> None:
        current = state["Stage"]
        mode = state["Mode"]
        if mode == "analyze" and target not in {"context", "reproduce", "hypothesize", "report"}:
            raise StateTransitionError(f"analyze mode cannot enter {target}")
        if target == "commit" and mode not in {"commit", "unattended"}:
            raise StateTransitionError(f"{mode} mode cannot enter commit")
        if target == "report" and completion_status in {"BLOCKED", "NEEDS_CONTEXT"}:
            return
        allowed = {
            "preflight": {"context"},
            "context": {"reproduce"},
            "reproduce": {"hypothesize"},
            "hypothesize": {"report"} if mode == "analyze" else {"regress-red"},
            "regress-red": {"implement"},
            "implement": {"verify"},
            "verify": {"implement", "review"},
            "review": {"implement", "final-verify"},
            "final-verify": {"implement", "report", "commit"},
            "commit": {"report"},
            "report": set(),
        }
        if target not in allowed.get(current, set()):
            raise StateTransitionError(f"invalid stage transition: {current} -> {target}")

    @staticmethod
    def _require_root_evidence(state: dict[str, Any], *, red: bool = True) -> None:
        if not any(item.get("Status") == "confirmed" for item in state["Hypotheses"]):
            raise StateTransitionError("a confirmed hypothesis is required before regress-red")
        assessment = state.get("ProfileAssessment")
        if not isinstance(assessment, dict) or assessment.get("initial") is None:
            raise StateTransitionError("initial ProfileAssessment is required before regress-red")
        if red and not state["RegressionRedEvidence"]:
            raise StateTransitionError("regression RED evidence is required before implement")
        if red:
            evidence = state["RegressionRedEvidence"]
            if not isinstance(evidence, dict):
                raise StateTransitionError("regression RED evidence must be an object")
            if _regression_skip_reason(evidence) and state.get("CompletionStatus") == "DONE":
                raise StateTransitionError("regression skip requires DONE_WITH_CONCERNS")

    @staticmethod
    def _verification_failed(state: dict[str, Any]) -> bool:
        if state.get("VerificationFailures"):
            return True
        evidence = state.get("VerificationEvidence", {})
        if (evidence.get("result") in {"fail", "failed"}
                or evidence.get("status") in {"fail", "failed"}
                or (isinstance(evidence.get("exit_code"), int) and evidence["exit_code"] != 0)):
            return True
        failures = set()
        for item in state.get("VerificationPlan", []):
            key = (item["command"], item["check"])
            if item["status"] == "failed":
                failures.add(key)
            elif item["status"] == "passed":
                failures.discard(key)
        return bool(failures)

    @staticmethod
    def _require_verification(state: dict[str, Any]) -> None:
        if not state.get("VerificationEvidence"):
            raise StateTransitionError("VerificationEvidence is required before review")
        if AutoFixStateStore._verification_failed(state):
            raise StateTransitionError("failed verification cannot certify completion")
        assessment = state.get("ProfileAssessment", {}).get("final")
        if assessment is None:
            raise StateTransitionError("final ProfileAssessment is required before review")
        _validate_profile_assessment(state["ProfileAssessment"], state["ValidationProfile"])
        if not assessment.get("required_checks"):
            raise StateTransitionError("final ProfileAssessment requires at least one check")
        plan = state.get("VerificationPlan", [])
        _validate_verification_plan(plan)
        latest = {(item["command"], item["check"]): item for item in plan}
        for item in latest.values():
            if item["status"] in {"passed", "skipped"} and not _binding_is_fresh(state, item):
                raise StateTransitionError("verification dependencies are stale or evidence has no runtime binding")
        skipped = {item["check"] for item in latest.values() if item["status"] == "skipped"}
        missing = set(assessment["required_checks"]) - _covered_checks(list(latest.values())) - skipped
        if missing:
            raise StateTransitionError("required verification checks are not covered: " + ", ".join(sorted(missing)))
        if skipped and state.get("CompletionStatus") == "DONE":
            raise StateTransitionError("objective verification skips require DONE_WITH_CONCERNS")

    @staticmethod
    def _require_review(state: dict[str, Any], validation: WorkspaceValidation) -> None:
        if not state.get("ReviewDiffHash"):
            raise StateTransitionError("ReviewDiffHash is required before final-verify")
        if validation.diff_hash != state["ReviewDiffHash"]:
            raise StateTransitionError("current diff does not match ReviewDiffHash; review evidence is stale")
        if state.get("ReviewOutcome") not in {"pass", "pass_with_concerns"}:
            raise StateTransitionError("final-verify requires a passing ReviewOutcome; unavailable is not a pass")
        if state.get("ReviewMode") not in REVIEW_MODES:
            raise StateTransitionError("final-verify requires ReviewMode")

    @staticmethod
    def _validate_stage(state: dict[str, Any]) -> None:
        """Check the merged checkpoint, including repeated and terminal updates."""
        stage = state["Stage"]
        terminal = state.get("CompletionStatus") in {"DONE", "DONE_WITH_CONCERNS"}
        if state["Mode"] == "analyze":
            if stage not in {"preflight", "context", "reproduce", "hypothesize", "report"}:
                raise StateTransitionError(f"analyze mode cannot enter {stage}")
            if stage == "report":
                _validate_state_workspace(state)
            return
        if stage == "report" and not terminal:
            if state.get("CompletionStatus") not in {"BLOCKED", "NEEDS_CONTEXT"}:
                raise StateTransitionError("report requires an explicit completion status")
            return
        if stage in {"regress-red", "implement", "verify", "review", "final-verify", "commit", "report"}:
            AutoFixStateStore._require_root_evidence(state, red=stage != "regress-red")
        if stage == "regress-red":
            _validate_profile_assessment(state["ProfileAssessment"], state["ValidationProfile"])
        if stage not in {"review", "final-verify", "commit", "report"}:
            return
        validation = _validate_state_workspace(state)
        if stage == "review":
            AutoFixStateStore._require_verification(state)
            return
        if stage == "final-verify" and (
            state.get("ReviewOutcome") in {"fail", "unavailable"}
            or AutoFixStateStore._verification_failed(state)
        ):
            # Negative observations must be durable. They revoke final evidence;
            # report/DONE still applies the complete success gate below.
            return
        AutoFixStateStore._require_review(state, validation)
        AutoFixStateStore._require_verification(state)
        if stage == "final-verify":
            state["FinalDiffHash"] = validation.diff_hash
            state["FinalFileFingerprints"] = _content_fingerprints(
                Path(state["WorkspaceSnapshot"]["repo_root"]), state["ChangedFiles"])
            state["FinalGitEntries"] = _expected_git_entries(
                Path(state["WorkspaceSnapshot"]["repo_root"]), state["ChangedFiles"])
            state["EvidenceRevalidationRequired"] = False
        elif not state.get("FinalDiffHash") or state["FinalDiffHash"] != validation.diff_hash:
            raise StateTransitionError("current diff does not match FinalDiffHash; final verification evidence is stale")
        if stage == "commit" and state["Mode"] not in {"commit", "unattended"}:
            raise StateTransitionError(f"{state['Mode']} mode cannot enter commit")
        if stage == "commit" and not state.get("CommitReceipt"):
            _validate_staged_content(state)


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
    init_parser.add_argument(
        "--validation-profile", choices=sorted(VALIDATION_PROFILES), default="strict"
    )
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
    checkpoint_parser.add_argument("--validation-profile", choices=sorted(VALIDATION_PROFILES))
    checkpoint_parser.add_argument("--profile-assessment-json")
    checkpoint_parser.add_argument("--verification-plan-json")
    checkpoint_parser.add_argument("--review-mode", choices=sorted(REVIEW_MODES))
    checkpoint_parser.add_argument("--review-outcome", choices=sorted(REVIEW_OUTCOMES))
    checkpoint_parser.add_argument("--repeat-execution-json")
    checkpoint_parser.add_argument(
        "--change-impact", action="append", choices=sorted(CHANGE_IMPACTS)
    )
    checkpoint_parser.add_argument("--changed-file-impacts-json")
    checkpoint_parser.add_argument("--review-diff-hash")
    checkpoint_parser.add_argument("--commit")
    checkpoint_parser.add_argument("--issue-comment-marker")
    checkpoint_parser.add_argument("--completion-status", choices=sorted(COMPLETION_STATUSES))
    args = parser.parse_args(argv)

    try:
        if args.command == "snapshot":
            _print_json(create_snapshot(args.repo))
        elif args.command == "init":
            store = AutoFixStateStore.initialize(
                args.repo, args.run_id, args.mode, args.validation_profile
            )
            _print_json({"state_path": str(store.path), "state": store.load()})
        elif args.command in {"verify-workspace", "diff-hash"}:
            state = _migrate_state(json.loads(args.state.read_text(encoding="utf-8")))
            snapshot = state["WorkspaceSnapshot"]
            if state.get("CommitReceipt"):
                if args.changed_file and list(_normalize_paths(args.changed_file)) != state["ChangedFiles"]:
                    raise WorkspaceDrift("changed files do not match the authorized commit receipt")
                result = _validate_state_workspace(state)
                if args.command == "verify-workspace":
                    _print_json({"changed_files": result.changed_files, "diff_hash": result.diff_hash})
                else:
                    print(result.diff_hash)
            elif args.command == "verify-workspace":
                result = validate_workspace(snapshot, args.changed_file)
                _print_json({"changed_files": result.changed_files, "diff_hash": result.diff_hash})
            else:
                print(compute_diff_hash(snapshot, args.changed_file))
        else:
            state = _migrate_state(json.loads(args.state.read_text(encoding="utf-8")))
            store = AutoFixStateStore(
                Path(state["WorkspaceSnapshot"]["repo_root"]), args.state.resolve()
            )
            options: dict[str, Any] = {}
            for argument, key in (
                (args.hypotheses_json, "hypotheses"),
                (args.regression_red_json, "regression_red"),
                (args.verification_json, "verification"),
                (args.profile_assessment_json, "profile_assessment"),
                (args.verification_plan_json, "verification_plan"),
                (args.repeat_execution_json, "repeat_execution"),
                (args.changed_file_impacts_json, "changed_file_impacts"),
            ):
                if argument is not None:
                    options[key] = json.loads(argument)
            if args.changed_file is not None:
                options["changed_files"] = args.changed_file
            if args.change_impact is not None:
                options["change_impacts"] = args.change_impact
            for argument, key in (
                (args.validation_profile, "validation_profile"),
                (args.review_mode, "review_mode"),
                (args.review_outcome, "review_outcome"),
                (args.review_diff_hash, "review_diff_hash"),
                (args.commit, "commit"),
                (args.issue_comment_marker, "issue_comment_marker"),
                (args.completion_status, "completion_status"),
            ):
                if argument is not None:
                    options[key] = argument
            _print_json(store.checkpoint(args.stage, **options))
    except StateWriteError as exc:
        print(
            json.dumps(
                {"error": exc.code, "operation": exc.operation, "message": str(exc)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
