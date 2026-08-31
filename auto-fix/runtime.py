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
SCHEMA_VERSION = 2
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
    if version not in {1, SCHEMA_VERSION}:
        raise StateTransitionError(f"unsupported state SchemaVersion: {version}")
    migrated["SchemaVersion"] = SCHEMA_VERSION
    migrated.setdefault("ValidationProfile", "strict")
    migrated.setdefault("ProfileAssessment", _default_profile_assessment())
    migrated.setdefault("VerificationPlan", [])
    migrated.setdefault("ReviewMode", None)
    migrated.setdefault("ReviewOutcome", None)
    migrated.setdefault("RepeatExecutions", [])
    migrated.setdefault("ChangeImpacts", [])
    migrated.setdefault("ChangedFileImpacts", {})
    migrated.setdefault("FinalDiffHash", None)
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
        if item.get("check") not in CHECK_NAMES:
            raise StateTransitionError("VerificationPlan check is invalid")
        depends_on = item.get("depends_on")
        if (
            not isinstance(depends_on, list)
            or not depends_on
            or not set(depends_on) <= CHANGE_IMPACTS
        ):
            raise StateTransitionError("VerificationPlan depends_on contains an invalid impact")
        proves = item.get("proves")
        if not isinstance(proves, list) or not proves:
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
            validate_workspace(
                existing["WorkspaceSnapshot"], existing.get("ChangedFiles", [])
            )
            if raw != existing:
                store._write(existing)
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
            self._validate_transition(state, stage)
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
            state["Commits"].append(commit)
        if issue_comment_marker is not None:
            state["IssueCommentMarker"] = issue_comment_marker
        if completion_status is not None:
            if completion_status not in COMPLETION_STATUSES:
                raise StateTransitionError(f"invalid completion status: {completion_status}")
            state["CompletionStatus"] = completion_status
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
            if impacts != {"documentation"}:
                state["VerificationEvidence"] = {}
                if "shared-infrastructure" in impacts:
                    state["VerificationPlan"] = []
                else:
                    retained: list[dict[str, Any]] = []
                    for item in state.get("VerificationPlan", []):
                        dependencies = set(item.get("depends_on", CHANGE_IMPACTS))
                        if not dependencies.intersection(impacts):
                            retained.append(item)
                    state["VerificationPlan"] = retained
            state["ReviewDiffHash"] = None
            state["ReviewMode"] = None
            state["ReviewOutcome"] = None
            state["FinalDiffHash"] = None
        if stage == "final-verify":
            state["FinalDiffHash"] = state["ReviewDiffHash"]
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
            assessment = state.get("ProfileAssessment")
            if not isinstance(assessment, dict) or assessment.get("initial") is None:
                raise StateTransitionError("initial ProfileAssessment is required before regress-red")
            _validate_profile_assessment(assessment, state["ValidationProfile"])
        if current == "regress-red" and target == "implement" and not state["RegressionRedEvidence"]:
            raise StateTransitionError("regression RED evidence is required before implement")
        if current == "verify" and target == "review":
            if not state.get("VerificationEvidence"):
                raise StateTransitionError("VerificationEvidence is required before review")
            assessment = state.get("ProfileAssessment", {}).get("final")
            if assessment is None:
                raise StateTransitionError("final ProfileAssessment is required before review")
            _validate_profile_assessment(
                state["ProfileAssessment"], state["ValidationProfile"]
            )
            if not assessment.get("required_checks"):
                raise StateTransitionError("final ProfileAssessment requires at least one check")
            _validate_verification_plan(state.get("VerificationPlan", []))
            missing_checks = set(assessment.get("required_checks", [])) - _covered_checks(
                state.get("VerificationPlan", [])
            )
            if missing_checks:
                raise StateTransitionError(
                    "required verification checks are not covered: "
                    + ", ".join(sorted(missing_checks))
                )
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
            if state.get("ReviewOutcome") not in {"pass", "pass_with_concerns"}:
                raise StateTransitionError(
                    "final-verify requires a passing ReviewOutcome; unavailable is not a pass"
                )
            if state.get("ReviewMode") not in REVIEW_MODES:
                raise StateTransitionError("final-verify requires ReviewMode")
            assessment = state.get("ProfileAssessment", {}).get("final")
            if assessment is None:
                raise StateTransitionError("final ProfileAssessment is required before final-verify")
            _validate_profile_assessment(
                state["ProfileAssessment"], state["ValidationProfile"]
            )
            if not assessment.get("required_checks"):
                raise StateTransitionError("final ProfileAssessment requires at least one check")
            required_checks = set(assessment.get("required_checks", []))
            _validate_verification_plan(state.get("VerificationPlan", []))
            missing_checks = required_checks - _covered_checks(state.get("VerificationPlan", []))
            if missing_checks:
                raise StateTransitionError(
                    "required verification checks are not covered: "
                    + ", ".join(sorted(missing_checks))
                )
        if current == "final-verify" and target in {"report", "commit"}:
            if not state.get("FinalDiffHash") or state["FinalDiffHash"] != state.get("ReviewDiffHash"):
                raise StateTransitionError("FinalDiffHash must match ReviewDiffHash")


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
            if args.command == "verify-workspace":
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
