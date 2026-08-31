import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "auto-fix" / "runtime.py"


def load_runtime():
    spec = importlib.util.spec_from_file_location("dev_harness_auto_fix_runtime", RUNTIME_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load auto-fix runtime")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GitRepoCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Test User")
        self.git("config", "user.email", "test@example.com")
        self.write("app.py", "print('base')\n")
        self.write("notes.md", "base notes\n")
        self.git("add", "app.py", "notes.md")
        self.git("commit", "-m", "initial")
        self.runtime = load_runtime()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def write(self, relative: str, content: str) -> None:
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


class WorkspaceSnapshotTests(GitRepoCase):
    def test_allows_new_conversation_change_with_preexisting_dirty_file(self) -> None:
        self.write("notes.md", "user draft\n")
        snapshot = self.runtime.create_snapshot(self.repo)

        self.write("app.py", "print('fixed')\n")
        result = self.runtime.validate_workspace(snapshot, ["app.py"])

        self.assertEqual(result.changed_files, ("app.py",))
        self.assertEqual(snapshot["preexisting_changes"], ["notes.md"])

    def test_rejects_touching_a_preexisting_dirty_file(self) -> None:
        self.write("notes.md", "user draft\n")
        snapshot = self.runtime.create_snapshot(self.repo)
        self.write("notes.md", "agent overwrote user draft\n")

        with self.assertRaisesRegex(self.runtime.WorkspaceDrift, "pre-existing change"):
            self.runtime.validate_workspace(snapshot, [])

    def test_rejects_undeclared_new_change(self) -> None:
        snapshot = self.runtime.create_snapshot(self.repo)
        self.write("app.py", "print('undeclared')\n")

        with self.assertRaisesRegex(self.runtime.WorkspaceDrift, "undeclared"):
            self.runtime.validate_workspace(snapshot, [])

    def test_rejects_declaring_preexisting_change_as_auto_fix_file(self) -> None:
        self.write("notes.md", "user draft\n")
        snapshot = self.runtime.create_snapshot(self.repo)

        with self.assertRaisesRegex(self.runtime.WorkspaceDrift, "already dirty"):
            self.runtime.validate_workspace(snapshot, ["notes.md"])

    def test_diff_hash_tracks_tracked_untracked_and_deleted_content(self) -> None:
        snapshot = self.runtime.create_snapshot(self.repo)
        self.write("app.py", "print('one')\n")
        first = self.runtime.compute_diff_hash(snapshot, ["app.py"])
        self.write("app.py", "print('two')\n")
        second = self.runtime.compute_diff_hash(snapshot, ["app.py"])
        self.assertNotEqual(first, second)

        self.write("new.txt", "one\n")
        untracked_one = self.runtime.compute_diff_hash(snapshot, ["app.py", "new.txt"])
        self.write("new.txt", "two\n")
        untracked_two = self.runtime.compute_diff_hash(snapshot, ["app.py", "new.txt"])
        self.assertNotEqual(untracked_one, untracked_two)

        (self.repo / "app.py").unlink()
        deleted = self.runtime.compute_diff_hash(snapshot, ["app.py", "new.txt"])
        self.assertNotEqual(untracked_two, deleted)

    def test_hidden_file_name_is_preserved(self) -> None:
        snapshot = self.runtime.create_snapshot(self.repo)
        self.write(".env", "SAFE_TEST_VALUE=1\n")

        result = self.runtime.validate_workspace(snapshot, [".env"])

        self.assertEqual(result.changed_files, (".env",))


class StateStoreTests(GitRepoCase):
    @staticmethod
    def assessment(profile: str, required_checks: list[str] | None = None) -> dict:
        return {
            "initial": {
                "profile": profile,
                "reasons": ["test assessment"],
                "risk_flags": [],
            },
            "final": {
                "profile": profile,
                "reasons": ["test assessment"],
                "risk_flags": [],
                "required_checks": required_checks or [],
            },
            "upgraded": False,
        }

    @staticmethod
    def plan_item(
        item_id: str,
        *,
        command: str = "python -m unittest focused",
        obligation: str = "focused-green",
        check: str = "BugfixCheck",
        depends_on: list[str] | None = None,
        diff_hash: str = "test-diff-hash",
        repeat_reason: str | None = None,
    ) -> dict:
        item = {
            "id": item_id,
            "command": command,
            "status": "passed",
            "check": check,
            "proves": [{"obligation": obligation, "evidence": f"logs/{item_id}.txt"}],
            "subsumes": {},
            "depends_on": depends_on or ["production", "test"],
            "diff_hash": diff_hash,
        }
        if repeat_reason is not None:
            item["repeat_reason"] = repeat_reason
        return item

    def test_new_state_uses_schema_v2_and_explicit_profile(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(
            self.repo, "run-profile", "fix", validation_profile="fast"
        )

        state = store.load()
        self.assertEqual(state["SchemaVersion"], 2)
        self.assertEqual(state["ValidationProfile"], "fast")
        self.assertEqual(state["VerificationPlan"], [])
        self.assertIsNone(state["FinalDiffHash"])

    def test_unattended_cannot_start_below_standard(self) -> None:
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "unattended"):
            self.runtime.AutoFixStateStore.initialize(
                self.repo, "run-unattended-fast", "unattended", validation_profile="fast"
            )

    def test_legacy_state_migrates_to_strict(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "run-legacy", "fix")
        legacy = store.load()
        for key in (
            "SchemaVersion",
            "ValidationProfile",
            "ProfileAssessment",
            "VerificationPlan",
            "ReviewMode",
            "ReviewOutcome",
            "RepeatExecutions",
            "FinalDiffHash",
        ):
            legacy.pop(key, None)
        store.path.write_text(json.dumps(legacy), encoding="utf-8")

        resumed = self.runtime.AutoFixStateStore.initialize(self.repo, "run-legacy", "fix")

        self.assertEqual(resumed.load()["SchemaVersion"], 2)
        self.assertEqual(resumed.load()["ValidationProfile"], "strict")

    def test_profile_can_upgrade_but_not_downgrade(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(
            self.repo, "run-upgrade", "fix", validation_profile="fast"
        )
        store.checkpoint("context", validation_profile="standard")
        self.assertEqual(store.load()["ValidationProfile"], "standard")

        with self.assertRaisesRegex(self.runtime.StateTransitionError, "downgrade"):
            store.checkpoint("context", validation_profile="fast")

    def test_initial_assessment_must_match_active_profile(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(
            self.repo, "run-assessment-profile", "fix", validation_profile="fast"
        )
        assessment = {
            "initial": {
                "profile": "standard",
                "reasons": ["mismatched assessment"],
                "risk_flags": [],
            },
            "final": None,
            "upgraded": False,
        }

        with self.assertRaisesRegex(self.runtime.StateTransitionError, "active"):
            store.checkpoint("context", profile_assessment=assessment)

    def test_verification_plan_derives_subsumption_from_proved_obligations(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "run-plan", "fix")
        item = self.plan_item("device")
        item["subsumes"] = {"QuickCheck": ["focused-green"]}
        store.checkpoint("context", verification_plan=[item])

        invalid = self.plan_item("invalid")
        invalid["subsumes"] = {"QuickCheck": ["missing-obligation"]}
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "subsumes"):
            store.checkpoint("context", verification_plan=[invalid])

    def test_duplicate_command_requires_repeat_reason(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "run-repeat", "fix")
        first = self.plan_item("first")
        duplicate = self.plan_item("duplicate")
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "repeat_reason"):
            store.checkpoint("context", verification_plan=[first, duplicate])

        duplicate["repeat_reason"] = "environment-recovery"
        store.checkpoint("context", verification_plan=[first, duplicate])

    def test_test_only_change_preserves_unaffected_build_evidence(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "run-impact-test", "fix")
        state = store.load()
        build = self.plan_item(
            "build", obligation="compiled", check="QuickCheck", depends_on=["production"]
        )
        focused = self.plan_item("focused", depends_on=["production", "test"])
        state.update(
            {
                "Stage": "review",
                "VerificationPlan": [build, focused],
                "VerificationEvidence": {"result": "passed"},
                "ReviewDiffHash": "old-review",
                "FinalDiffHash": "old-final",
            }
        )
        store._write(state)

        updated = store.checkpoint(
            "implement", changed_files=["app.py"], change_impacts=["test"]
        )

        self.assertEqual([item["id"] for item in updated["VerificationPlan"]], ["build"])
        self.assertEqual(updated["VerificationEvidence"], {})
        self.assertIsNone(updated["ReviewDiffHash"])
        self.assertIsNone(updated["FinalDiffHash"])

    def test_fast_profile_upgrades_when_production_scope_exceeds_two_files(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(
            self.repo, "run-production-scope", "fix", validation_profile="fast"
        )
        state = store.load()
        state["Stage"] = "regress-red"
        state["RegressionRedEvidence"] = {"observed_failure": "signature"}
        state["ProfileAssessment"] = {
            "initial": {
                "profile": "fast",
                "reasons": ["planned two-file change"],
                "risk_flags": [],
            },
            "final": None,
            "upgraded": False,
        }
        store._write(state)
        files = ["one.py", "two.py", "three.py"]

        updated = store.checkpoint(
            "implement",
            changed_files=files,
            changed_file_impacts={path: "production" for path in files},
        )

        self.assertEqual(updated["ValidationProfile"], "standard")
        self.assertTrue(updated["ProfileAssessment"]["upgraded"])

    def test_shared_infrastructure_change_forces_strict_and_clears_plan(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(
            self.repo, "run-shared", "fix", validation_profile="fast"
        )
        state = store.load()
        state.update(
            {
                "Stage": "regress-red",
                "RegressionRedEvidence": {"observed_failure": "signature"},
                "VerificationPlan": [self.plan_item("build", depends_on=["production"])],
                "ProfileAssessment": {
                    "initial": {
                        "profile": "fast",
                        "reasons": ["initially local"],
                        "risk_flags": [],
                    },
                    "final": None,
                    "upgraded": False,
                },
            }
        )
        store._write(state)

        updated = store.checkpoint(
            "implement",
            changed_files=["build.py"],
            changed_file_impacts={"build.py": "shared-infrastructure"},
        )

        self.assertEqual(updated["ValidationProfile"], "strict")
        self.assertEqual(updated["VerificationPlan"], [])

    def test_hard_risk_assessment_requires_strict(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(
            self.repo, "run-hard-risk", "fix", validation_profile="fast"
        )
        assessment = self.assessment("fast")
        assessment["initial"]["risk_flags"] = ["security"]

        with self.assertRaisesRegex(self.runtime.StateTransitionError, "hard risk"):
            store.checkpoint("context", profile_assessment=assessment)

    def test_documentation_change_keeps_execution_evidence(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "run-impact-docs", "fix")
        state = store.load()
        plan = [self.plan_item("focused")]
        state.update(
            {
                "Stage": "review",
                "VerificationPlan": plan,
                "VerificationEvidence": {"result": "passed"},
                "ReviewDiffHash": "old-review",
                "FinalDiffHash": "old-final",
            }
        )
        store._write(state)

        updated = store.checkpoint(
            "implement", changed_files=["notes.md"], change_impacts=["documentation"]
        )

        self.assertEqual(updated["VerificationPlan"], plan)
        self.assertEqual(updated["VerificationEvidence"], {"result": "passed"})
        self.assertIsNone(updated["ReviewDiffHash"])
        self.assertIsNone(updated["FinalDiffHash"])

    def test_state_write_permission_error_has_stable_code(self) -> None:
        with mock.patch.object(Path, "mkdir", side_effect=PermissionError("denied")):
            with self.assertRaises(self.runtime.StateWriteError) as raised:
                self.runtime.AutoFixStateStore.initialize(
                    self.repo, "run-write-denied", "fix"
                )

        self.assertEqual(raised.exception.code, "state_write_denied")

    def test_failed_independent_review_cannot_be_overridden_by_self_review(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "run-review-fail", "fix")
        state = store.load()
        state.update(
            {
                "Stage": "review",
                "ReviewMode": "independent",
                "ReviewOutcome": "fail",
            }
        )
        store._write(state)

        with self.assertRaisesRegex(self.runtime.StateTransitionError, "cannot be overridden"):
            store.checkpoint("review", review_mode="self", review_outcome="pass")

    def test_unavailable_independent_review_can_fall_back_to_self_review(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(
            self.repo, "run-review-unavailable", "fix"
        )
        state = store.load()
        state.update(
            {
                "Stage": "review",
                "ReviewMode": "independent",
                "ReviewOutcome": "unavailable",
            }
        )
        store._write(state)

        updated = store.checkpoint("review", review_mode="self", review_outcome="pass")

        self.assertEqual(updated["ReviewMode"], "self")
        self.assertEqual(updated["ReviewOutcome"], "pass")

    def test_final_verify_rejects_uncovered_required_check(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(
            self.repo, "run-required-check", "fix", validation_profile="fast"
        )
        self.write("app.py", "print('fixed')\n")
        state = store.load()
        current_hash = self.runtime.compute_diff_hash(
            state["WorkspaceSnapshot"], ["app.py"]
        )
        state.update(
            {
                "Stage": "review",
                "ChangedFiles": ["app.py"],
                "VerificationEvidence": {"result": "passed"},
                "VerificationPlan": [self.plan_item("focused", diff_hash=current_hash)],
                "ProfileAssessment": self.assessment("fast", ["QuickCheck"]),
                "ReviewMode": "self",
                "ReviewOutcome": "pass",
                "ReviewDiffHash": current_hash,
            }
        )
        store._write(state)

        with self.assertRaisesRegex(self.runtime.StateTransitionError, "not covered"):
            store.checkpoint("final-verify")

    def test_cli_checkpoint_persists_state(self) -> None:
        initialized = subprocess.run(
            [
                sys.executable,
                str(RUNTIME_PATH),
                "init",
                "--repo",
                str(self.repo),
                "--run-id",
                "run-cli",
                "--mode",
                "analyze",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        state_path = json.loads(initialized.stdout)["state_path"]

        checkpointed = subprocess.run(
            [
                sys.executable,
                str(RUNTIME_PATH),
                "checkpoint",
                "--state",
                state_path,
                "--stage",
                "context",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertEqual(json.loads(checkpointed.stdout)["Stage"], "context")

    def test_state_is_stored_under_git_private_path(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "run-1", "fix")

        self.assertTrue(store.path.is_file())
        self.assertTrue(store.path.is_relative_to(self.repo / ".git"))
        self.assertNotIn("dev-harness", self.git("status", "--short"))
        self.assertIn("dev-harness", str(store.path))
        self.assertEqual(store.load()["Mode"], "fix")

    def test_analyze_mode_cannot_enter_write_stages(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "run-analyze", "analyze")
        store.checkpoint("context")
        store.checkpoint("reproduce")
        store.checkpoint(
            "hypothesize",
            hypotheses=[{"Status": "confirmed", "Claim": "broken branch"}],
        )

        with self.assertRaisesRegex(self.runtime.StateTransitionError, "analyze"):
            store.checkpoint("regress-red")
        store.checkpoint("report", completion_status="DONE")

    def test_implement_requires_confirmed_hypothesis_and_red_evidence(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "run-fix", "fix")
        store.checkpoint("context")
        store.checkpoint("reproduce")
        store.checkpoint("hypothesize", hypotheses=[{"Status": "unverified"}])

        with self.assertRaisesRegex(self.runtime.StateTransitionError, "confirmed"):
            store.checkpoint("regress-red")

        store.checkpoint("hypothesize", hypotheses=[{"Status": "confirmed"}])
        store.checkpoint(
            "hypothesize",
            profile_assessment={
                "initial": {
                    "profile": "strict",
                    "reasons": ["legacy strict test"],
                    "risk_flags": [],
                },
                "final": None,
                "upgraded": False,
            },
        )
        store.checkpoint("regress-red", regression_red={"observed_failure": "signature"})
        store.checkpoint("implement", changed_files=["app.py"])
        self.assertEqual(store.load()["Stage"], "implement")

    def test_code_change_invalidates_old_review_and_verification(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "run-invalidate", "fix")
        state = store.load()
        state["Stage"] = "review"
        state["VerificationEvidence"] = {"quick": "passed"}
        state["ReviewDiffHash"] = "old-hash"
        store._write(state)

        store.checkpoint("implement", changed_files=["app.py"])
        updated = store.load()
        self.assertEqual(updated["VerificationEvidence"], {})
        self.assertIsNone(updated["ReviewDiffHash"])

    def test_final_verify_rejects_diff_not_seen_by_review(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "run-review-drift", "fix")
        self.write("app.py", "print('fixed')\n")
        state = store.load()
        state["Stage"] = "review"
        state["ChangedFiles"] = ["app.py"]
        state["ReviewDiffHash"] = "stale-review-hash"
        store._write(state)

        with self.assertRaisesRegex(self.runtime.StateTransitionError, "ReviewDiffHash"):
            store.checkpoint("final-verify")

    def test_final_verify_accepts_current_reviewed_diff(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "run-review-current", "fix")
        self.write("app.py", "print('fixed')\n")
        state = store.load()
        current_hash = self.runtime.compute_diff_hash(
            state["WorkspaceSnapshot"], ["app.py"]
        )
        state["Stage"] = "review"
        state["ChangedFiles"] = ["app.py"]
        state["VerificationEvidence"] = {"result": "passed"}
        state["VerificationPlan"] = [self.plan_item("focused", diff_hash=current_hash)]
        state["ProfileAssessment"] = self.assessment("strict", ["BugfixCheck"])
        state["ReviewMode"] = "self"
        state["ReviewOutcome"] = "pass"
        state["ReviewDiffHash"] = current_hash
        store._write(state)

        store.checkpoint("final-verify")

        self.assertEqual(store.load()["Stage"], "final-verify")
        self.assertEqual(store.load()["FinalDiffHash"], current_hash)

    def test_fix_mode_cannot_enter_commit(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "run-no-commit", "fix")
        state = store.load()
        state["Stage"] = "final-verify"
        state["CompletionStatus"] = "DONE"
        store._write(state)

        with self.assertRaisesRegex(self.runtime.StateTransitionError, "commit"):
            store.checkpoint("commit")

    def test_state_file_remains_valid_json_after_checkpoint(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "run-json", "commit")
        store.checkpoint("context")
        parsed = json.loads(store.path.read_text(encoding="utf-8"))
        self.assertEqual(parsed["Stage"], "context")

    def test_initialize_same_run_resumes_existing_state(self) -> None:
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "run-resume", "fix")
        store.checkpoint("context")

        resumed = self.runtime.AutoFixStateStore.initialize(self.repo, "run-resume", "fix")

        self.assertEqual(resumed.load()["Stage"], "context")


if __name__ == "__main__":
    unittest.main()
