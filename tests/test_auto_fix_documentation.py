"""Completion requires an explicit documentation decision for the current content."""

import copy
import json
import subprocess
import sys

import test_auto_fix_runtime as fixtures


class AutoFixDocumentationTests(fixtures.GitRepoCase):
    assessment = staticmethod(fixtures.StateStoreTests.assessment)
    plan_item = staticmethod(fixtures.StateStoreTests.plan_item)

    def ready(self, catalog_path=None, *, mode="fix"):
        if catalog_path:
            self.write(catalog_path, "# Current functions\n\nCAP-001: Existing output behavior.\n")
            self.git("add", catalog_path)
            self.git("commit", "-m", "fixture catalog")
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "documentation", mode, "fast")
        fixtures.StateStoreTests.prepare_review(self, store, documentation=False)
        return store

    def record(self, store, *, result="not-applicable", path=None, ids=None):
        check = self.documentation_check(store, result=result, catalog_path=path, capability_ids=ids)
        if result == "no-impact":
            check["reason"] = "Checked CAP-001; this fix restores its existing promised output."
        elif result == "updated":
            check["reason"] = "Updated CAP-001 limits and verification evidence to match the fix."
        store.checkpoint("review", documentation_check=check)
        return check

    def revise_catalog(self, store, path):
        plan = copy.deepcopy(store.load()["VerificationPlan"])
        self.write(path, "# Current functions\n\nCAP-001: Updated output behavior and evidence.\n")
        store.checkpoint("implement", changed_files=["app.py", path],
                         changed_file_impacts={"app.py": "production", path: "documentation"})
        store.checkpoint("verify", profile_assessment=self.assessment("fast", ["BugfixCheck"]))
        state = store.load()
        store.checkpoint("review", review_mode="self", review_outcome="pass",
                         review_diff_hash=self.runtime.compute_diff_hash(state["WorkspaceSnapshot"], state["ChangedFiles"]))
        self.assertEqual(store.load()["VerificationPlan"], plan)

    def test_missing_documentation_check_blocks_final_success(self):
        store = self.ready()
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "DocumentationCheck"):
            store.checkpoint("final-verify")
        self.assertIsNone(store.load()["FinalDiffHash"])

    def test_existing_catalog_cannot_be_reported_not_applicable(self):
        for index, path in enumerate(self.runtime.DEFAULT_CATALOG_PATHS):
            with self.subTest(path=path):
                self.write(path, "# Functions\n")
                store = self.runtime.AutoFixStateStore.initialize(self.repo, f"catalog-{index}", "fix")
                with self.assertRaisesRegex(self.runtime.StateTransitionError, "catalog exists") as raised:
                    store.checkpoint("context", documentation_check=self.documentation_check(store))
                self.assertIn(path, str(raised.exception))
                (self.repo / path).unlink()

    def test_documentation_directory_without_catalog_is_not_applicable(self):
        (self.repo / "docs").mkdir()
        store = self.ready()
        self.record(store)
        store.checkpoint("final-verify")
        self.assertEqual(store.checkpoint("report", completion_status="DONE")["CompletionStatus"], "DONE")

    def test_no_impact_can_complete_without_changing_catalog(self):
        path = "docs/product-functions.md"
        store = self.ready(path)
        check = self.record(store, result="no-impact", path=path, ids=["CAP-001"])
        self.assertNotIn(path, store.load()["ChangedFiles"])
        store.checkpoint("final-verify")
        self.assertEqual(store.checkpoint("report", completion_status="DONE")["DocumentationCheck"], check)

    def test_updated_catalog_preserves_execution_evidence_and_can_complete(self):
        path = "docs/CAPABILITIES.md"
        store = self.ready(path)
        self.revise_catalog(store, path)
        self.record(store, result="updated", path=path, ids=["CAP-001"])
        store.checkpoint("final-verify")
        self.assertEqual(store.checkpoint("report", completion_status="DONE")["DocumentationCheck"]["result"], "updated")

    def test_updated_requires_actual_catalog_change_and_known_ids(self):
        path = "docs/CAPABILITIES.md"
        store = self.ready(path)
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "changed catalog"):
            self.record(store, result="updated", path=path, ids=["CAP-001"])
        self.revise_catalog(store, path)
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "capability_ids"):
            self.record(store, result="updated", path=path)
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "absent"):
            self.record(store, result="updated", path=path, ids=["CAP-999"])

    def test_invalid_record_shape_and_reason_do_not_persist(self):
        store = self.ready()
        original = store.path.read_bytes()
        valid = self.documentation_check(store)
        for patch in ({"reason": "  "}, {"result": "unchecked"}, {"result": []},
                      {"capability_ids": ["CAP-001", "CAP-001"]},
                      {"catalog_path": "docs/CAPABILITIES.md"}, {"diff_hash": "prior-diff"}):
            with self.subTest(patch=patch):
                with self.assertRaisesRegex(self.runtime.StateTransitionError, "DocumentationCheck"):
                    store.checkpoint("review", documentation_check={**valid, **patch})
                self.assertEqual(store.path.read_bytes(), original)

    def test_missing_deleted_directory_or_escaping_catalog_is_rejected(self):
        store = self.ready()
        (self.repo / "docs").mkdir()
        for path in ("docs/missing.md", "docs", "../outside.md", str(self.repo / "app.py"), "C:\\catalog.md"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(self.runtime.StateTransitionError, "DocumentationCheck"):
                    self.record(store, result="no-impact", path=path)

    def test_symlink_file_and_parent_cannot_be_catalog_paths(self):
        self.write("docs/functions.md", "CAP-001\n")
        try:
            (self.repo / "catalog.md").symlink_to("docs/functions.md")
            (self.repo / "linked-docs").symlink_to("docs", target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlinks are unavailable: {exc}")
        self.git("add", "docs/functions.md", "catalog.md", "linked-docs")
        self.git("commit", "-m", "fixture symlink paths")
        store = self.ready()
        for path in ("catalog.md", "linked-docs/functions.md"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(self.runtime.StateTransitionError, "symlink"):
                    self.record(store, result="no-impact", path=path)

    def test_deleting_catalog_cannot_bypass_documentation_check(self):
        path = "docs/CAPABILITIES.md"
        store = self.ready(path)
        (self.repo / path).unlink()
        store.checkpoint("implement", changed_files=["app.py", path],
                         changed_file_impacts={"app.py": "production", path: "documentation"})
        store.checkpoint("verify", profile_assessment=self.assessment("fast", ["BugfixCheck"]))
        for result, catalog in (("no-impact", path), ("updated", path), ("not-applicable", None)):
            with self.subTest(result=result):
                check = self.documentation_check(store, result=result, catalog_path=catalog,
                                                 capability_ids=["CAP-001"] if result == "updated" else [])
                with self.assertRaisesRegex(self.runtime.StateTransitionError, "DocumentationCheck"):
                    store.checkpoint("verify", documentation_check=check)
        (self.repo / path).mkdir()
        with self.assertRaisesRegex(self.runtime.WorkspaceDrift, "unsupported changed file type"):
            store.checkpoint("verify", documentation_check=self.documentation_check(store))

    def test_implementation_revokes_documentation_decision_and_stale_check_is_rejected(self):
        path = "docs/CAPABILITIES.md"
        store = self.ready(path)
        old = self.record(store, result="no-impact", path=path, ids=["CAP-001"])
        self.revise_catalog(store, path)
        self.assertIsNone(store.load()["DocumentationCheck"])
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "DocumentationCheck.*stale"):
            store.checkpoint("review", documentation_check=old)
        state = store.load()
        state["DocumentationCheck"] = old
        store._write(state)
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "DocumentationCheck.*stale"):
            store.checkpoint("final-verify")

    def test_report_and_commit_recheck_documentation_gate(self):
        store = self.ready(mode="commit")
        self.record(store)
        store.checkpoint("final-verify")
        state = store.load()
        state["DocumentationCheck"] = None
        store._write(state)
        for stage, options in (("report", {"completion_status": "DONE"}), ("commit", {})):
            with self.subTest(stage=stage):
                with self.assertRaisesRegex(self.runtime.StateTransitionError, "DocumentationCheck"):
                    store.checkpoint(stage, **options)

    def test_legacy_success_revokes_completion_but_preserves_bound_tests_and_mode(self):
        store = self.ready()
        self.record(store)
        store.checkpoint("final-verify")
        state = store.checkpoint("report", completion_status="DONE")
        del state["DocumentationCheck"]
        store.path.write_text(json.dumps(state), encoding="utf-8")
        resumed = self.runtime.AutoFixStateStore.initialize(self.repo, "documentation", "fix", "fast")
        migrated = resumed.load()
        self.assertIsNone(migrated["CompletionStatus"])
        self.assertIsNone(migrated["FinalDiffHash"])
        self.assertEqual(migrated["Stage"], "verify")
        self.assertEqual(migrated["Mode"], state["Mode"])
        self.assertEqual(migrated["VerificationBindings"], state["VerificationBindings"])
        resumed.checkpoint("review")
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "DocumentationCheck"):
            resumed.checkpoint("final-verify")
        self.record(resumed)
        resumed.checkpoint("final-verify")
        resumed.checkpoint("report", completion_status="DONE")

    def test_legacy_final_receipts_before_report_require_documentation_revalidation(self):
        store = self.ready(mode="commit")
        self.record(store)
        finalized = copy.deepcopy(store.checkpoint("final-verify"))
        self.git("add", "app.py")
        committing = store.checkpoint("commit")
        for original in (finalized, committing):
            with self.subTest(stage=original["Stage"]):
                legacy = copy.deepcopy(original)
                del legacy["DocumentationCheck"]
                store.path.write_text(json.dumps(legacy), encoding="utf-8")
                resumed = self.runtime.AutoFixStateStore.initialize(self.repo, "documentation", "commit", "fast")
                migrated = resumed.load()
                self.assertEqual(migrated["Stage"], "verify")
                self.assertIsNone(migrated["CompletionStatus"])
                self.assertIsNone(migrated["FinalDiffHash"])
                self.assertEqual(migrated["FinalFileFingerprints"], {})
                self.assertEqual(migrated["FinalGitEntries"], {})
                self.assertEqual(migrated["Mode"], original["Mode"])
                self.assertEqual(migrated["ValidationProfile"], original["ValidationProfile"])
                self.assertEqual(migrated["VerificationBindings"], original["VerificationBindings"])
                self.assertEqual(migrated["VerificationPlan"], original["VerificationPlan"])
                resumed.checkpoint("review")
                with self.assertRaisesRegex(self.runtime.StateTransitionError, "DocumentationCheck"):
                    resumed.checkpoint("final-verify")

    def test_blocked_report_does_not_require_documentation_check(self):
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "blocked", "fix")
        self.assertEqual(store.checkpoint("report", completion_status="BLOCKED")["CompletionStatus"], "BLOCKED")

    def test_analyze_completion_and_legacy_recovery_do_not_require_documentation_check(self):
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "analysis", "analyze")
        store.checkpoint("context")
        store.checkpoint("reproduce")
        store.checkpoint("hypothesize", hypotheses=[{"Status": "confirmed"}])
        state = store.checkpoint("report", completion_status="DONE")
        del state["DocumentationCheck"]
        store.path.write_text(json.dumps(state), encoding="utf-8")
        resumed = self.runtime.AutoFixStateStore.initialize(self.repo, "analysis", "analyze")
        self.assertEqual(resumed.load()["CompletionStatus"], "DONE")
        self.assertEqual(resumed.load()["Stage"], "report")

    def test_cli_records_current_documentation_decision(self):
        store = self.ready()
        check = self.documentation_check(store)
        command = [sys.executable, str(fixtures.RUNTIME_PATH), "checkpoint", "--state", str(store.path),
                   "--stage", "review", "--documentation-check-json", json.dumps(check)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["DocumentationCheck"], check)
        store.checkpoint("final-verify")
        store.checkpoint("report", completion_status="DONE")
