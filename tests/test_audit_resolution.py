import copy

import test_codebase_audit_runtime as audit_tests


class AuditResolutionTests(audit_tests.GitRepoCase):
    def prepare_reverification(self):
        original = self.init_store("before-fix")
        finding = self.confirmed_finding(original.load()["AuditSnapshot"])
        original.upsert_finding(finding, "ctx-1")
        self.write("app.py", "print('fixed owner lifetime')\n")
        with self.assertRaises(self.runtime.WorkspaceDrift):
            original.verify_workspace("ctx-1")
        current = self.init_store("after-fix")
        current.upsert_finding(
            {"id": "AUD-001", "status": "stale", "source_run_id": "before-fix"},
            "ctx-1",
        )
        return original, current

    def resolution(self, store):
        return {
            "id": "AUD-001",
            "status": "resolved",
            "resolution": {
                "snapshot": store.load()["AuditSnapshot"]["snapshot_fingerprint"],
                "change_summary": "Owner cleanup now cancels the callback before release.",
                "verification_status": "passed",
                "evidence_paths_lines": [
                    {"path": "app.py", "lines": "1", "observation": "fixed lifetime"},
                    {"command": "python app.py", "observation": "fixed owner lifetime; exit 0"},
                ],
            },
        }

    def test_cannot_create_resolved_without_a_registered_problem(self):
        store = self.init_store()
        before = store.path.read_bytes()
        with self.assertRaises(self.runtime.FindingValidationError):
            store.upsert_finding({"id": "AUD-001", "status": "resolved"}, "ctx-1")
        self.assertEqual(store.path.read_bytes(), before)

    def test_confirmed_problem_cannot_be_resolved_in_the_same_snapshot(self):
        store = self.init_store()
        store.upsert_finding(self.confirmed_finding(store.load()["AuditSnapshot"]), "ctx-1")
        for patch in ({"id": "AUD-001", "status": "resolved"}, self.resolution(store)):
            with self.subTest(patch=patch), self.assertRaises(self.runtime.FindingValidationError):
                store.upsert_finding(patch, "ctx-1")
        self.assertEqual(store.load()["Findings"]["AUD-001"]["status"], "confirmed")

    def test_import_requires_a_real_previously_confirmed_finding(self):
        original = self.init_store("before-fix")
        original.upsert_finding({"id": "AUD-001", "status": "candidate"}, "ctx-1")
        self.write("app.py", "print('different')\n")
        current = self.init_store("after-fix")
        for source in ("missing-run", "before-fix", "../before-fix", "after-fix"):
            with self.subTest(source=source), self.assertRaises(self.runtime.FindingValidationError):
                current.upsert_finding(
                    {"id": "AUD-001", "status": "stale", "source_run_id": source}, "ctx-1"
                )
        self.assertEqual(current.load()["Findings"], {})

    def test_history_fields_cannot_forge_a_confirmation(self):
        store = self.init_store()
        forged = {"id": "AUD-001", "status": "stale", "previous_status": "confirmed",
                  "claim": "unverified", "evidence_paths_lines": ["not evidence"],
                  "snapshot": store.load()["AuditSnapshot"]["snapshot_fingerprint"]}
        with self.assertRaises(self.runtime.FindingValidationError):
            store.upsert_finding(forged, "ctx-1")
        self.assertEqual(store.load()["Findings"], {})

    def test_staling_cannot_replace_a_previously_confirmed_claim(self):
        store = self.init_store()
        store.upsert_finding(self.confirmed_finding(store.load()["AuditSnapshot"]), "ctx-1")
        with self.assertRaises(self.runtime.FindingValidationError):
            store.upsert_finding({"id": "AUD-001", "status": "stale", "claim": "unverified replacement"}, "ctx-1")
        store.upsert_finding({"id": "AUD-001", "status": "stale"}, "ctx-1")
        with self.assertRaises(self.runtime.FindingValidationError):
            store.upsert_finding({"id": "AUD-001", "evidence_paths_lines": ["unverified"]}, "ctx-1")

    def test_reopening_as_candidate_clears_confirmation_provenance(self):
        original = self.init_store("before-fix")
        original.upsert_finding(self.confirmed_finding(original.load()["AuditSnapshot"]), "ctx-1")
        original.upsert_finding({"id": "AUD-001", "status": "stale"}, "ctx-1")
        original.upsert_finding({"id": "AUD-001", "status": "candidate", "claim": "different unverified claim"}, "ctx-1")
        original.upsert_finding({"id": "AUD-001", "status": "stale"}, "ctx-1")
        self.assertNotIn("previous_status", original.load()["Findings"]["AUD-001"])
        self.write("app.py", "print('different')\n")
        current = self.init_store("after-fix")
        with self.assertRaises(self.runtime.FindingValidationError):
            current.upsert_finding({"id": "AUD-001", "status": "stale", "source_run_id": "before-fix"}, "ctx-1")

    def test_resolution_cannot_erase_original_confirmation_evidence(self):
        _, current = self.prepare_reverification()
        for field in ("evidence_paths_lines", "counter_evidence_checked", "relevant_call_chain_data_flow"):
            patch = {**self.resolution(current), field: []}
            with self.subTest(field=field), self.assertRaises(self.runtime.FindingValidationError):
                current.upsert_finding(patch, "ctx-1")
        self.assertEqual(current.load()["Findings"]["AUD-001"]["status"], "stale")

    def test_import_preserves_original_claim_and_snapshot(self):
        original, current = self.prepare_reverification()
        imported = current.load()["Findings"]["AUD-001"]
        historical = original.load()["Findings"]["AUD-001"]
        self.assertEqual(imported["claim"], historical["claim"])
        self.assertEqual(imported["snapshot"], historical["snapshot"])
        self.assertEqual(imported["previous_status"], "confirmed")
        with self.assertRaises(self.runtime.FindingValidationError):
            current.upsert_finding({"id": "AUD-001", "source_run_id": "other"}, "ctx-1")

    def test_resolution_requires_current_snapshot_and_valid_new_evidence(self):
        _, current = self.prepare_reverification()
        valid = self.resolution(current)
        invalid = [
            {"id": "AUD-001", "status": "resolved"},
            {**valid, "resolution": {**valid["resolution"], "evidence_paths_lines": []}},
            {**valid, "resolution": {**valid["resolution"], "snapshot": "old-snapshot"}},
            {**valid, "resolution": {**valid["resolution"], "change_summary": ""}},
            {**valid, "resolution": {**valid["resolution"], "verification_status": "failed"}},
            {**valid, "resolution": {**valid["resolution"], "verification_status": "skipped"}},
            {**valid, "resolution": {**valid["resolution"], "evidence_paths_lines": [
                {"path": "missing.py", "lines": "1"}]}},
        ]
        for patch in invalid:
            before = current.path.read_bytes()
            with self.subTest(patch=patch), self.assertRaises(self.runtime.FindingValidationError):
                current.upsert_finding(patch, "ctx-1")
            self.assertEqual(current.path.read_bytes(), before)

    def test_reverified_resolution_renders_completes_and_stales_on_later_changes(self):
        original, current = self.prepare_reverification()
        previous = copy.deepcopy(original.load())
        current.upsert_finding(self.resolution(current), "ctx-1")
        current.batch(audit_tests.BatchAndRenderingTests.document_batch(self), "ctx-1")
        current.checkpoint_cross_module("completed", "ctx-1", {"reviewed_tasks": ["A01"]})
        current.render_output("ctx-1")
        current.complete("ctx-1")
        current.render_output("ctx-1")
        report = (self.repo / "docs/audit/Findings.md").read_text()
        self.assertIn("已解决", report)
        self.assertIn("before-fix", report)
        self.assertIn("fixed owner lifetime; exit 0", report)
        self.assertEqual(original.load(), previous)
        self.write("app.py", "print('changed again')\n")
        with self.assertRaises(self.runtime.WorkspaceDrift):
            current.verify_workspace("ctx-1")
        finding = current.load()["Findings"]["AUD-001"]
        self.assertEqual(finding["status"], "stale")
        self.assertEqual(finding["previous_status"], "resolved")
