import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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
        state["ReviewDiffHash"] = current_hash
        store._write(state)

        store.checkpoint("final-verify")

        self.assertEqual(store.load()["Stage"], "final-verify")

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
