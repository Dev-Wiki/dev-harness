import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "codebase-audit" / "runtime.py"


def load_runtime():
    spec = importlib.util.spec_from_file_location(
        "dev_harness_codebase_audit_runtime", RUNTIME_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load codebase-audit runtime")
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
        self.write("docs/README.md", "# Project docs\n")
        self.git("add", "app.py", "notes.md", "docs/README.md")
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

    def init_store(self, run_id: str = "audit-1", context: str = "ctx-1"):
        return self.runtime.AuditStateStore.initialize(
            self.repo, run_id, context, ["whole-repository"], "docs"
        )

    def confirmed_finding(self, snapshot: dict) -> dict:
        return {
            "id": "AUD-001",
            "status": "confirmed",
            "severity": "P1",
            "category": "lifecycle",
            "summary": "Callback may outlive its owner",
            "evidence_paths_lines": [
                {"path": "app.py", "lines": "1", "observation": "test evidence"}
            ],
            "relevant_call_chain_data_flow": "entry -> callback -> owner",
            "claim": "The callback can access an expired owner.",
            "counter_evidence_checked": ["No cancellation path exists."],
            "risk_impact": "A production request can fail.",
            "confidence": "high",
            "suggested_next_action": "Reproduce under the owner shutdown path.",
            "snapshot": snapshot["snapshot_fingerprint"],
        }


class AuditSnapshotTests(GitRepoCase):
    def test_initializes_run_in_git_private_state(self) -> None:
        store = self.init_store()
        state = store.load()

        self.assertTrue(store.path.is_file())
        self.assertTrue(store.path.is_relative_to(self.repo / ".git"))
        self.assertEqual(state["RunId"], "audit-1")
        self.assertEqual(state["Status"], "ACTIVE")
        self.assertFalse(state["NeedsReverification"])
        self.assertEqual(state["Tasks"], {})
        self.assertNotIn("dev-harness", self.git("status", "--short"))

    def test_snapshot_records_head_branch_dirty_fingerprints_context_scope_and_output(self) -> None:
        self.write("notes.md", "user draft\n")
        snapshot = self.runtime.create_audit_snapshot(
            self.repo, "context-fp", ["core", "platform-boundary"], "docs"
        )

        self.assertEqual(snapshot["base_sha"], self.git("rev-parse", "HEAD"))
        self.assertEqual(snapshot["branch"], "main")
        self.assertEqual(snapshot["preexisting_dirty_files"], ["notes.md"])
        self.assertEqual(len(snapshot["preexisting_fingerprints"]["notes.md"]), 64)
        self.assertEqual(snapshot["context_fingerprint"], "context-fp")
        self.assertEqual(snapshot["scope"], ["core", "platform-boundary"])
        self.assertEqual(snapshot["docs_root"], "docs")
        self.assertEqual(snapshot["audit_output_root"], "docs/audit")
        self.assertEqual(len(snapshot["snapshot_fingerprint"]), 64)

    def test_audit_docs_output_is_not_business_drift(self) -> None:
        store = self.init_store()
        self.write("docs/audit/Findings.md", "# Findings\n")

        validation = store.verify_workspace("ctx-1")

        self.assertEqual(validation.business_dirty_files, ())
        self.assertEqual(validation.audit_output_files, ("docs/audit/Findings.md",))
        self.assertEqual(store.load()["Status"], "ACTIVE")

    def test_preexisting_dirty_audit_output_is_preserved(self) -> None:
        self.write("docs/audit/Findings.md", "user draft\n")
        store = self.init_store()
        self.write("docs/audit/Findings.md", "agent overwrite\n")

        with self.assertRaisesRegex(self.runtime.WorkspaceDrift, "pre-existing dirty"):
            store.verify_workspace("ctx-1")

    def test_business_source_change_fails_closed_and_marks_run_stale(self) -> None:
        store = self.init_store()
        self.write("app.py", "print('changed during audit')\n")

        with self.assertRaisesRegex(self.runtime.WorkspaceDrift, "business/source"):
            store.verify_workspace("ctx-1")

        state = store.load()
        self.assertEqual(state["Status"], "STALE")
        self.assertTrue(state["NeedsReverification"])
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "STALE"):
            store.checkpoint_task("A01", "in-progress", "ctx-1")

    def test_preexisting_dirty_content_head_and_branch_are_all_guarded(self) -> None:
        self.write("notes.md", "draft one\n")
        dirty_store = self.init_store("dirty-run")
        self.write("notes.md", "draft two\n")
        with self.assertRaisesRegex(self.runtime.WorkspaceDrift, "pre-existing dirty"):
            dirty_store.verify_workspace("ctx-1")

        self.git("restore", "notes.md")
        head_store = self.init_store("head-run")
        self.write("later.txt", "next commit\n")
        self.git("add", "later.txt")
        self.git("commit", "-m", "later")
        with self.assertRaisesRegex(self.runtime.WorkspaceDrift, "HEAD drifted"):
            head_store.verify_workspace("ctx-1")

        branch_store = self.init_store("branch-run")
        self.git("switch", "-c", "topic")
        with self.assertRaisesRegex(self.runtime.WorkspaceDrift, "branch drifted"):
            branch_store.verify_workspace("ctx-1")


class DurableStateTests(GitRepoCase):
    def test_task_checkpoint_can_resume_in_a_new_store_instance(self) -> None:
        store = self.init_store()
        store.checkpoint_task(
            "A01",
            "in-progress",
            "ctx-1",
            {"current_focus": "native boundary", "evidence": ["app.py:1"]},
        )

        resumed = self.runtime.AuditStateStore.resume(self.repo, "audit-1", "ctx-1")
        task = resumed.load()["Tasks"]["A01"]

        self.assertEqual(task["status"], "in-progress")
        self.assertEqual(task["checkpoint"]["current_focus"], "native boundary")
        self.assertEqual(task["revision"], 1)

    def test_context_change_stales_run_and_confirmed_findings_then_blocks_checkpoint(self) -> None:
        store = self.init_store()
        finding = self.confirmed_finding(store.load()["AuditSnapshot"])
        store.upsert_finding(finding, "ctx-1")

        with self.assertRaisesRegex(self.runtime.WorkspaceDrift, "Context fingerprint"):
            self.runtime.AuditStateStore.resume(self.repo, "audit-1", "ctx-2")

        state = store.load()
        self.assertEqual(state["Status"], "STALE")
        self.assertTrue(state["NeedsReverification"])
        self.assertEqual(state["Findings"]["AUD-001"]["status"], "stale")
        self.assertEqual(
            state["Findings"]["AUD-001"]["previous_status"], "confirmed"
        )
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "STALE"):
            store.checkpoint_task("A02", "pending", "ctx-1")

    def test_status_and_cli_resume_need_only_persisted_state_not_chat(self) -> None:
        store = self.init_store("resume-cli")
        store.checkpoint_task("A01", "completed", "ctx-1", {"result": "recorded"})

        resumed = subprocess.run(
            [
                sys.executable,
                str(RUNTIME_PATH),
                "resume",
                "--repo",
                str(self.repo),
                "--run-id",
                "resume-cli",
                "--context-fingerprint",
                "ctx-1",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        status = subprocess.run(
            [
                sys.executable,
                str(RUNTIME_PATH),
                "status",
                "--repo",
                str(self.repo),
                "--run-id",
                "resume-cli",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertEqual(json.loads(resumed.stdout)["state"]["Tasks"]["A01"]["status"], "completed")
        payload = json.loads(status.stdout)
        self.assertEqual(payload["TaskCounts"], {"completed": 1})
        self.assertEqual(payload["State"]["Tasks"]["A01"]["checkpoint"]["result"], "recorded")

    def test_state_remains_valid_json_after_repeated_atomic_checkpoints(self) -> None:
        store = self.init_store()
        store.checkpoint_task("A01", "pending", "ctx-1")
        store.checkpoint_task("A01", "in-progress", "ctx-1", {"cursor": "symbol-x"})

        parsed = json.loads(store.path.read_text(encoding="utf-8"))

        self.assertEqual(parsed["Tasks"]["A01"]["revision"], 2)
        self.assertEqual(parsed["Revision"], 2)

    def test_completion_requires_tasks_and_cross_module_reconciliation(self) -> None:
        store = self.init_store()
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "task checkpoints"):
            store.complete("ctx-1")

        store.checkpoint_task("A01", "completed", "ctx-1", {"result": "recorded"})
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "cross-module"):
            store.complete("ctx-1")
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "requires"):
            store.checkpoint_cross_module("completed", "ctx-1")

        store.checkpoint_cross_module(
            "completed",
            "ctx-1",
            {"deduplicated": True, "contradictions": "none", "full_chain": "checked"},
        )
        state = store.complete("ctx-1")

        self.assertEqual(state["Status"], "COMPLETED")
        self.assertEqual(
            state["CompletedSnapshot"], state["AuditSnapshot"]["snapshot_fingerprint"]
        )
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "STALE"):
            store.checkpoint_task("A02", "pending", "ctx-1")


class OutputAndFindingContractTests(GitRepoCase):
    def test_output_path_rejects_absolute_parent_and_symlink_escape(self) -> None:
        store = self.init_store()
        with self.assertRaises(self.runtime.OutputPathError):
            store.validate_output("/tmp/report.md")
        with self.assertRaises(self.runtime.OutputPathError):
            store.validate_output("../Report.md")

        outside = self.repo.parent / f"{self.repo.name}-outside"
        outside.mkdir()
        (self.repo / "docs/audit").mkdir(parents=True)
        (self.repo / "docs/audit/escape").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(self.runtime.OutputPathError, "symlink"):
            store.validate_output("escape/Report.md")

        self.assertEqual(
            store.validate_output("tasks/A01-core.md"),
            self.repo / "docs/audit/tasks/A01-core.md",
        )

    def test_finding_rejects_unknown_status(self) -> None:
        store = self.init_store()

        with self.assertRaisesRegex(self.runtime.FindingValidationError, "invalid finding status"):
            store.upsert_finding(
                {"id": "AUD-001", "status": "probably-confirmed"}, "ctx-1"
            )

    def test_confirmed_finding_requires_complete_evidence_contract_and_snapshot(self) -> None:
        store = self.init_store()
        with self.assertRaisesRegex(
            self.runtime.FindingValidationError, "missing required evidence fields"
        ):
            store.upsert_finding(
                {"id": "AUD-001", "status": "confirmed", "severity": "P1"},
                "ctx-1",
            )

        finding = self.confirmed_finding(store.load()["AuditSnapshot"])
        finding["snapshot"] = "old-snapshot"
        with self.assertRaisesRegex(self.runtime.FindingValidationError, "snapshot"):
            store.upsert_finding(finding, "ctx-1")

        finding = self.confirmed_finding(store.load()["AuditSnapshot"])
        state = store.upsert_finding(finding, "ctx-1")
        self.assertEqual(state["Findings"]["AUD-001"]["status"], "confirmed")

    def test_confirmed_finding_validates_evidence_location_lines_and_confidence(self) -> None:
        store = self.init_store()
        snapshot = store.load()["AuditSnapshot"]

        finding = self.confirmed_finding(snapshot)
        finding["evidence_paths_lines"] = [{"path": "../outside.py", "lines": 1}]
        with self.assertRaisesRegex(self.runtime.FindingValidationError, "invalid repository path"):
            store.upsert_finding(finding, "ctx-1")

        finding = self.confirmed_finding(snapshot)
        finding["evidence_paths_lines"] = [{"path": "app.py", "lines": 99}]
        with self.assertRaisesRegex(self.runtime.FindingValidationError, "outside"):
            store.upsert_finding(finding, "ctx-1")

        finding = self.confirmed_finding(snapshot)
        finding["confidence"] = "low"
        with self.assertRaisesRegex(self.runtime.FindingValidationError, "high or medium"):
            store.upsert_finding(finding, "ctx-1")

    def test_all_documented_finding_states_are_accepted(self) -> None:
        snapshot = self.runtime.create_audit_snapshot(
            self.repo, "ctx-1", "whole-repository", "docs"
        )
        for index, status in enumerate(sorted(self.runtime.FINDING_STATUSES), start=1):
            finding = {"id": f"AUD-{index:03d}", "status": status}
            if status == "confirmed":
                finding = self.confirmed_finding(snapshot)
                finding["id"] = f"AUD-{index:03d}"
            canonical = self.runtime.validate_finding(finding, snapshot)
            self.assertEqual(canonical["status"], status)

    def test_runtime_operations_cannot_write_business_source(self) -> None:
        before = (self.repo / "app.py").read_bytes()
        store = self.init_store()
        store.checkpoint_task("A01", "pending", "ctx-1")
        store.upsert_finding({"id": "AUD-002", "status": "candidate"}, "ctx-1")
        output = store.validate_output("results/A01.md")

        self.assertEqual(output, self.repo / "docs/audit/results/A01.md")
        self.assertEqual((self.repo / "app.py").read_bytes(), before)
        self.assertFalse((self.repo / "docs/audit/results/A01.md").exists())
        changed = self.git("status", "--short")
        self.assertEqual(changed, "")

    def test_init_requires_an_existing_unambiguous_docs_root(self) -> None:
        (self.repo / "docs/README.md").unlink()
        (self.repo / "docs").rmdir()
        with self.assertRaisesRegex(self.runtime.OutputPathError, "no existing"):
            self.runtime.create_audit_snapshot(self.repo, "ctx", "all")

        (self.repo / "docs").mkdir()
        (self.repo / "doc").mkdir()
        with self.assertRaisesRegex(self.runtime.OutputPathError, "both doc/ and docs/"):
            self.runtime.create_audit_snapshot(self.repo, "ctx", "all")


if __name__ == "__main__":
    unittest.main()
