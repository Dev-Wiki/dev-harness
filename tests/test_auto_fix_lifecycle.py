"""Public-API regressions for evidence freshness and authorized commit recovery."""

import copy
import json
import os
import shlex
import subprocess
import sys

import test_auto_fix_runtime as fixtures


class AutoFixLifecycleTests(fixtures.GitRepoCase):
    def checked_run(self):
        return subprocess.run(
            [sys.executable, "-c", "import subprocess, sys; r = subprocess.run([sys.executable, 'app.py'], capture_output=True, text=True); assert r.returncode == 0 and r.stdout == 'fixed\\n', r"],
            cwd=self.repo, capture_output=True, text=True,
        )

    def ready(self, mode="fix", *, explicit_dependencies=False):
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "lifecycle", mode, "fast")
        self.assessment = {
            "initial": {"profile": "fast", "reasons": ["one-file fix"], "risk_flags": []},
            "final": None, "upgraded": False,
        }
        store.checkpoint("context")
        store.checkpoint("reproduce")
        store.checkpoint("hypothesize", hypotheses=[{
            "Claim": "app prints the wrong value", "Prediction": "output is base",
            "Probe": "python app.py", "Observation": "base", "Status": "confirmed",
        }], profile_assessment=copy.deepcopy(self.assessment))
        red = self.checked_run()
        self.assertNotEqual(red.returncode, 0)
        store.checkpoint("regress-red", regression_red={
            "command": "check app output", "exit_code": red.returncode,
            "FailureSignature": "output is not fixed", "output": red.stderr,
        })
        self.write("app.py", "print('fixed')\n")
        store.checkpoint("implement", changed_files=["app.py"],
                         changed_file_impacts={"app.py": "production"})
        green = self.checked_run()
        self.assertEqual(green.returncode, 0, green.stderr)
        diff_hash = self.runtime.compute_diff_hash(store.load()["WorkspaceSnapshot"], ["app.py"])
        plan = [{"id": "focused", "command": "check app output", "status": "passed",
                 "check": "BugfixCheck", "diff_hash": diff_hash,
                 "depends_on": ["production", "test"],
                 "proves": [{"obligation": "expected output", "evidence": "actual exit 0"}]}]
        if explicit_dependencies:
            plan[0]["depends_on_files"] = ["app.py"]
        self.assessment["final"] = {**self.assessment["initial"], "required_checks": ["BugfixCheck"]}
        store.checkpoint("verify", verification={"exit_code": 0}, verification_plan=plan,
                         profile_assessment=copy.deepcopy(self.assessment))
        return store

    def reviewed(self, store):
        state = store.load()
        diff_hash = self.runtime.compute_diff_hash(state["WorkspaceSnapshot"], state["ChangedFiles"])
        store.checkpoint("review", review_mode="self", review_outcome="pass", review_diff_hash=diff_hash)
        return diff_hash

    def finalized(self, store):
        self.reviewed(store)
        return store.checkpoint("final-verify")

    def test_old_green_cannot_certify_modified_production_code(self):
        store = self.ready()
        self.write("app.py", "raise RuntimeError('regression')\n")
        self.assertNotEqual(self.checked_run().returncode, 0)
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "stale|fresh|depend"):
            self.reviewed(store)

    def test_false_hash_cannot_register_passed_verification(self):
        store = self.ready()
        plan = store.load()["VerificationPlan"]
        plan[0]["diff_hash"] = "a-prior-unverified-hash"
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "hash|fresh"):
            store.checkpoint("verify", verification_plan=plan)

    def test_failed_final_check_cannot_finish_done(self):
        store = self.ready()
        self.finalized(store)
        plan = store.load()["VerificationPlan"]
        plan[0]["status"] = "failed"
        store.checkpoint("final-verify", verification={"exit_code": 1}, verification_plan=plan)
        self.assertIsNone(store.load()["FinalDiffHash"])
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "failed|covered|FinalDiffHash"):
            store.checkpoint("report", completion_status="DONE")

    def test_updated_failed_review_cannot_finish_done(self):
        store = self.ready()
        self.finalized(store)
        store.checkpoint("final-verify", review_outcome="fail")
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "ReviewOutcome|review|FinalDiffHash"):
            store.checkpoint("report", completion_status="DONE")

    def test_completion_validates_new_values_in_same_checkpoint(self):
        store = self.ready()
        self.finalized(store)
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "ReviewOutcome|review"):
            store.checkpoint("report", completion_status="DONE", review_outcome="fail")
        self.assertEqual(store.load()["Stage"], "final-verify")

    def test_done_cannot_be_written_before_report(self):
        store = self.runtime.AutoFixStateStore.initialize(self.repo, "early", "fix", "fast")
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "report|completion"):
            store.checkpoint("context", completion_status="DONE")

    def test_repeated_report_does_not_bypass_freshness(self):
        store = self.ready()
        self.finalized(store)
        store.checkpoint("report", completion_status="DONE")
        self.write("app.py", "raise RuntimeError('after report')\n")
        with self.assertRaises((self.runtime.StateTransitionError, self.runtime.WorkspaceDrift)):
            store.checkpoint("report", completion_status="DONE")

    def test_documentation_change_reuses_bound_execution(self):
        store = self.ready()
        original = copy.deepcopy(store.load()["VerificationPlan"])
        self.reviewed(store)
        self.write("notes.md", "clarify behavior\n")
        store.checkpoint("implement", changed_files=["app.py", "notes.md"],
                         changed_file_impacts={"app.py": "production", "notes.md": "documentation"})
        store.checkpoint("verify", profile_assessment=copy.deepcopy(self.assessment))
        self.finalized(store)
        state = store.checkpoint("report", completion_status="DONE")
        self.assertEqual(state["VerificationPlan"], original)
        self.assertNotEqual(original[0]["diff_hash"], state["FinalDiffHash"])

    def test_explicit_dependency_scope_reuses_unrelated_test_change(self):
        store = self.ready(explicit_dependencies=True)
        original = copy.deepcopy(store.load()["VerificationPlan"])
        self.reviewed(store)
        self.write("unrelated_test.py", "assert 2 + 2 == 4\n")
        store.checkpoint("implement", changed_files=["app.py", "unrelated_test.py"],
                         changed_file_impacts={"app.py": "production", "unrelated_test.py": "test"})
        store.checkpoint("verify", profile_assessment=copy.deepcopy(self.assessment))
        self.finalized(store)
        self.assertEqual(store.checkpoint("report", completion_status="DONE")["VerificationPlan"], original)

    def test_implicit_test_dependencies_invalidate_new_test_change(self):
        store = self.ready()
        self.reviewed(store)
        self.write("new_test.py", "assert False\n")
        store.checkpoint("implement", changed_files=["app.py", "new_test.py"],
                         changed_file_impacts={"app.py": "production", "new_test.py": "test"})
        store.checkpoint("verify", profile_assessment=copy.deepcopy(self.assessment))
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "covered|VerificationEvidence|fresh|stale"):
            self.reviewed(store)

    def test_legacy_unbound_evidence_cannot_be_used_to_complete(self):
        store = self.ready()
        state = store.load()
        state.pop("VerificationBindings", None)
        state["SchemaVersion"] = 2
        store.path.write_text(json.dumps(state), encoding="utf-8")
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "bound|binding|fresh|stale|VerificationEvidence|covered"):
            self.reviewed(store)

    def test_staging_preserves_reviewed_content_hash(self):
        store = self.ready("commit")
        state = self.finalized(store)
        self.git("add", "app.py")
        current_hash = self.runtime.compute_diff_hash(state["WorkspaceSnapshot"], ["app.py"])
        self.assertEqual(current_hash, state["FinalDiffHash"])
        store.checkpoint("commit")

    def test_legacy_completed_state_revokes_done_and_returns_to_verification(self):
        store = self.ready()
        self.finalized(store)
        state = store.checkpoint("report", completion_status="DONE")
        state["SchemaVersion"] = 2
        store.path.write_text(json.dumps(state), encoding="utf-8")
        resumed = self.runtime.AutoFixStateStore.initialize(self.repo, "lifecycle", "fix", "fast")
        self.assertEqual(resumed.load()["Stage"], "verify")
        self.assertIsNone(resumed.load()["CompletionStatus"])
        self.assertTrue(resumed.load()["EvidenceRevalidationRequired"])
        with self.assertRaises(self.runtime.StateTransitionError):
            resumed.checkpoint("report", completion_status="DONE")

    def test_legacy_commit_cannot_invent_a_recovery_receipt(self):
        store = self.ready("commit")
        self.finalized(store)
        self.git("add", "app.py")
        store.checkpoint("commit")
        self.git("commit", "-m", "fix output")
        store.checkpoint("commit", commit=self.git("rev-parse", "HEAD"))
        state = store.checkpoint("report", completion_status="DONE")
        state["SchemaVersion"] = 2
        store.path.write_text(json.dumps(state), encoding="utf-8")
        with self.assertRaisesRegex(self.runtime.StateTransitionError, "legacy|new run"):
            self.runtime.AutoFixStateStore.initialize(self.repo, "lifecycle", "commit", "fast")
        self.assertIsNone(store.load()["CompletionStatus"])
        self.assertIsNone(store.load()["CommitReceipt"])

    def test_recorded_authorized_commit_can_resume_and_report(self):
        store = self.ready("commit")
        self.finalized(store)
        self.git("add", "app.py")
        store.checkpoint("commit")
        self.git("commit", "-m", "fix output")
        sha = self.git("rev-parse", "HEAD")
        store.checkpoint("commit", commit=sha)
        resumed = self.runtime.AutoFixStateStore.initialize(self.repo, "lifecycle", "commit", "fast")
        self.assertEqual(resumed.checkpoint("report", completion_status="DONE")["Commits"], [sha])

    def test_commit_interrupted_before_receipt_can_resume(self):
        store = self.ready("commit")
        self.finalized(store)
        self.git("add", "app.py")
        store.checkpoint("commit")
        self.git("commit", "-m", "fix output")
        resumed = self.runtime.AutoFixStateStore.initialize(self.repo, "lifecycle", "commit", "fast")
        self.assertEqual(resumed.load()["Commits"], [self.git("rev-parse", "HEAD")])
        resumed.checkpoint("report", completion_status="DONE")

    def test_commit_with_extra_file_is_rejected(self):
        store = self.ready("commit")
        self.finalized(store)
        self.git("add", "app.py")
        store.checkpoint("commit")
        self.write("notes.md", "unrelated\n")
        self.git("add", "app.py", "notes.md")
        self.git("commit", "-m", "mixed changes")
        with self.assertRaises((self.runtime.StateTransitionError, self.runtime.WorkspaceDrift)):
            store.checkpoint("commit", commit=self.git("rev-parse", "HEAD"))

    def test_commit_with_unreviewed_content_is_rejected(self):
        store = self.ready("commit")
        self.finalized(store)
        self.git("add", "app.py")
        store.checkpoint("commit")
        self.write("app.py", "print('unreviewed')\n")
        self.git("add", "app.py")
        self.git("commit", "-m", "wrong tree")
        with self.assertRaises((self.runtime.StateTransitionError, self.runtime.WorkspaceDrift)):
            self.runtime.AutoFixStateStore.initialize(self.repo, "lifecycle", "commit", "fast")

    def test_additional_commit_does_not_count_as_authorized_recovery(self):
        store = self.ready("commit")
        self.finalized(store)
        self.git("add", "app.py")
        store.checkpoint("commit")
        self.git("commit", "-m", "fix output")
        self.git("commit", "--allow-empty", "-m", "unrelated commit")
        with self.assertRaises((self.runtime.StateTransitionError, self.runtime.WorkspaceDrift)):
            self.runtime.AutoFixStateStore.initialize(self.repo, "lifecycle", "commit", "fast")

    def test_commit_rejects_partial_or_unrelated_staging_before_git_commit(self):
        store = self.ready("commit")
        self.finalized(store)
        self.git("add", "app.py")
        self.write("notes.md", "unrelated draft\n")
        self.git("add", "notes.md")
        with self.assertRaisesRegex(self.runtime.WorkspaceDrift, "undeclared|staged_scope_conflict"):
            store.checkpoint("commit")
        self.assertEqual(self.git("rev-parse", "HEAD"), store.load()["BaseSha"])

    def test_commit_rejects_staged_bytes_different_from_reviewed_worktree(self):
        store = self.ready("commit")
        self.write("app.py", "print('old staged value')\n")
        self.git("add", "app.py")
        self.write("app.py", "print('fixed')\n")
        self.finalized(store)
        with self.assertRaisesRegex(self.runtime.WorkspaceDrift, "staged content"):
            store.checkpoint("commit")

    def test_authorized_commit_supports_git_text_normalization_and_cli(self):
        self.write(".gitattributes", "app.py text eol=lf\n")
        self.git("add", ".gitattributes")
        self.git("commit", "-m", "fixture text normalization")
        store = self.ready("commit")
        self.reviewed(store)
        self.write("app.py", "print('fixed')\r\n")
        store.checkpoint("implement", changed_files=["app.py"], changed_file_impacts={"app.py": "production"})
        plan = [{"id": "normalized", "command": "check app output", "status": "passed",
                 "check": "BugfixCheck", "depends_on": ["production"],
                 "proves": [{"obligation": "expected output", "evidence": "actual exit 0"}],
                 "diff_hash": self.runtime.compute_diff_hash(store.load()["WorkspaceSnapshot"], ["app.py"])}]
        self.assertEqual(self.checked_run().returncode, 0)
        store.checkpoint("verify", verification={"exit_code": 0}, verification_plan=plan,
                         profile_assessment=copy.deepcopy(self.assessment))
        state = self.finalized(store)
        self.git("add", "app.py")
        store.checkpoint("commit")
        self.git("commit", "-m", "normalized fix")
        store.checkpoint("commit", commit=self.git("rev-parse", "HEAD"))
        result = subprocess.run([sys.executable, str(fixtures.RUNTIME_PATH), "diff-hash", "--state", str(store.path),
                                 "--changed-file", "app.py"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), state["FinalDiffHash"])
        self.runtime.AutoFixStateStore.initialize(self.repo, "lifecycle", "commit", "fast")
        store.checkpoint("report", completion_status="DONE")

    def strict_device_skip(self, store):
        assessment = copy.deepcopy(self.assessment)
        assessment['final'] = {'profile': 'strict', 'reasons': ['device integration boundary'],
                               'risk_flags': [], 'required_checks': ['BugfixCheck', 'FullCheck']}
        assessment['upgraded'] = True
        plan = copy.deepcopy(store.load()['VerificationPlan'])
        plan.append({'id': 'device-full', 'command': 'device integration tests', 'status': 'skipped',
                     'check': 'FullCheck', 'diff_hash': plan[0]['diff_hash'], 'depends_on': ['production'],
                     'skip_reason': 'device-required', 'skip_evidence': 'device enumeration returned no device',
                     'alternative_verification': 'focused output test passed locally',
                     'remaining_risk': 'native device integration remains unverified',
                     'proves': []})
        return assessment, plan

    def test_filemode_false_preserves_the_git_mode_when_filesystem_differs(self):
        self.git('config', 'core.filemode', 'false')
        (self.repo / 'app.py').chmod(0o755)
        self.assertEqual(self.git('status', '--short'), '')
        store = self.ready('commit')
        self.finalized(store)
        self.git('add', 'app.py')
        self.assertEqual(self.git('ls-files', '--stage', 'app.py').split()[0], '100644')
        store.checkpoint('commit')
        self.git('commit', '-m', 'fix with ignored executable bit')
        store.checkpoint('commit', commit=self.git('rev-parse', 'HEAD'))
        resumed = self.runtime.AutoFixStateStore.initialize(self.repo, 'lifecycle', 'commit', 'fast')
        resumed.checkpoint('report', completion_status='DONE')

    def test_filemode_false_explicit_index_mode_change_invalidates_review(self):
        self.git('config', 'core.filemode', 'false')
        (self.repo / 'app.py').chmod(0o755)
        store = self.ready('commit')
        reviewed_hash = self.reviewed(store)
        self.git('add', 'app.py')
        self.assertEqual(self.runtime.compute_diff_hash(store.load()['WorkspaceSnapshot'], ['app.py']), reviewed_hash)
        self.git('update-index', '--chmod=+x', 'app.py')
        with self.assertRaisesRegex(self.runtime.StateTransitionError, 'ReviewDiffHash|stale'):
            store.checkpoint('final-verify')

    def test_objective_full_skip_can_complete_only_with_concerns(self):
        store = self.ready()
        assessment, plan = self.strict_device_skip(store)
        store.checkpoint('verify', validation_profile='strict', profile_assessment=assessment,
                         verification_plan=plan)
        self.finalized(store)
        with self.assertRaisesRegex(self.runtime.StateTransitionError, 'DONE_WITH_CONCERNS|skip|gap'):
            store.checkpoint('report', completion_status='DONE')
        state = store.checkpoint('report', completion_status='DONE_WITH_CONCERNS')
        self.assertEqual(state['VerificationPlan'][-1]['status'], 'skipped')
        self.assertNotIn('FullCheck', self.runtime._covered_checks(state['VerificationPlan']))

    def test_skip_requires_objective_reason_evidence_alternative_and_risk(self):
        store = self.ready()
        assessment, plan = self.strict_device_skip(store)
        for field in ('skip_reason', 'skip_evidence', 'alternative_verification', 'remaining_risk'):
            with self.subTest(field=field):
                invalid = copy.deepcopy(plan)
                del invalid[-1][field]
                with self.assertRaisesRegex(self.runtime.StateTransitionError, 'skip|risk|alternative'):
                    store.checkpoint('verify', validation_profile='strict', profile_assessment=assessment,
                                     verification_plan=invalid)
        invalid = copy.deepcopy(plan)
        invalid[-1]['skip_reason'] = 'user-requested'
        with self.assertRaisesRegex(self.runtime.StateTransitionError, 'skip'):
            store.checkpoint('verify', validation_profile='strict', profile_assessment=assessment,
                             verification_plan=invalid)

    def test_failed_execution_cannot_be_erased_by_an_objective_skip(self):
        store = self.ready()
        assessment, plan = self.strict_device_skip(store)
        failed = copy.deepcopy(plan)
        failed[-1]['status'] = 'failed'
        failed[-1]['proves'] = [{'obligation': 'device integration outcome',
                                'evidence': 'recorded assertion failure, exit 1'}]
        store.checkpoint('verify', validation_profile='strict', profile_assessment=assessment,
                         verification_plan=failed)
        store.checkpoint('verify', verification_plan=plan)
        with self.assertRaisesRegex(self.runtime.StateTransitionError, 'failed'):
            self.reviewed(store)

    def test_noop_implement_cannot_erase_failure_before_skip(self):
        store = self.ready()
        assessment, skipped = self.strict_device_skip(store)
        failed = copy.deepcopy(skipped)
        failed[-1]['status'] = 'failed'
        failed[-1]['proves'] = [{'obligation': 'device behavior', 'evidence': 'observed assertion failure'}]
        store.checkpoint('verify', validation_profile='strict', profile_assessment=assessment,
                         verification_plan=failed)
        content = (self.repo / 'app.py').read_bytes()
        failures = store.load()['VerificationFailures']
        store.checkpoint('implement', changed_files=['app.py'], changed_file_impacts={'app.py': 'production'})
        self.assertEqual((self.repo / 'app.py').read_bytes(), content)
        self.assertEqual(store.load()['VerificationFailures'], failures)
        store.checkpoint('verify', profile_assessment=assessment, verification_plan=skipped)
        with self.assertRaisesRegex(self.runtime.StateTransitionError, 'failed'):
            self.finalized(store)

    def test_fresh_passing_rerun_clears_failure_after_implement(self):
        store = self.ready()
        assessment, plan = self.strict_device_skip(store)
        command = [sys.executable, '-c', "import os; assert os.environ['AUTO_FIX_FIXTURE_DEVICE_READY'] == 'yes'"]
        failed_run = subprocess.run(command, capture_output=True, text=True,
                                    env={**os.environ, 'AUTO_FIX_FIXTURE_DEVICE_READY': 'no'})
        self.assertNotEqual(failed_run.returncode, 0)
        plan[-1].update(command=shlex.join(command), status='failed',
                        proves=[{'obligation': 'device readiness', 'evidence': failed_run.stderr}])
        store.checkpoint('verify', validation_profile='strict', profile_assessment=assessment,
                         verification_plan=plan)
        store.checkpoint('implement', changed_files=['app.py'], changed_file_impacts={'app.py': 'production'})
        passed_run = subprocess.run(command, capture_output=True, text=True,
                                    env={**os.environ, 'AUTO_FIX_FIXTURE_DEVICE_READY': 'yes'})
        self.assertEqual(passed_run.returncode, 0, passed_run.stderr)
        for field in ('skip_reason', 'skip_evidence', 'alternative_verification', 'remaining_risk'):
            plan[-1].pop(field)
        plan[-1].update(status='passed', repeat_reason='environment-recovery',
                        proves=[{'obligation': 'device readiness', 'evidence': 'actual rerun exit 0'}])
        store.checkpoint('verify', profile_assessment=assessment, verification_plan=plan)
        self.assertEqual(store.load()['VerificationFailures'], [])
        self.finalized(store)
        store.checkpoint('report', completion_status='DONE')

    def test_old_passing_evidence_cannot_clear_a_later_failure(self):
        store = self.ready()
        assessment, passed = self.strict_device_skip(store)
        passed[-1].update(status='passed', proves=[{'obligation': 'device behavior', 'evidence': 'earlier pass'}])
        store.checkpoint('verify', validation_profile='strict', profile_assessment=assessment,
                         verification_plan=passed)
        failed = copy.deepcopy(passed[-1])
        failed.update(id='device-retry', status='failed', repeat_reason='user-requested',
                      proves=[{'obligation': 'device behavior', 'evidence': 'later assertion failure'}])
        store.checkpoint('verify', verification_plan=passed + [failed])
        store.checkpoint('verify', verification_plan=passed)
        with self.assertRaisesRegex(self.runtime.StateTransitionError, 'failed'):
            self.finalized(store)

    def test_regression_skip_cannot_replace_red_and_keep_done(self):
        store = self.ready()
        self.finalized(store)
        skip = {'RegressionSkipReason': 'device-required', 'skip_evidence': 'device enumeration found none',
                'alternative_verification': 'focused output test passed locally',
                'remaining_risk': 'original device failure not reproduced'}
        with self.assertRaisesRegex(self.runtime.StateTransitionError, 'DONE_WITH_CONCERNS|skip|gap'):
            store.checkpoint('report', regression_red=skip, completion_status='DONE')
        state = store.checkpoint('report', regression_red=skip, completion_status='DONE_WITH_CONCERNS')
        self.assertEqual(state['RegressionRedEvidence']['RegressionSkipReason'], 'device-required')

    def test_regression_skip_cannot_omit_observation_or_use_user_preference(self):
        store = self.ready()
        self.finalized(store)
        for skip in (
            {'RegressionSkipReason': 'device-required', 'alternative_verification': 'local test',
             'remaining_risk': 'device not checked'},
            {'RegressionSkipReason': 'user-requested', 'skip_evidence': 'user says do not run',
             'alternative_verification': 'local test', 'remaining_risk': 'device not checked'},
        ):
            with self.subTest(skip=skip):
                with self.assertRaisesRegex(self.runtime.StateTransitionError, 'skip'):
                    store.checkpoint('report', regression_red=skip, completion_status='DONE_WITH_CONCERNS')
