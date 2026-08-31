import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AutoFixContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auto_fix = (ROOT / "auto-fix" / "SKILL.md").read_text(encoding="utf-8")
        cls.git_workflow = (ROOT / "git-workflow" / "SKILL.md").read_text(encoding="utf-8")
        cls.repro = (ROOT / "internal" / "bugfix-flow" / "repro.md").read_text(
            encoding="utf-8"
        )
        cls.triage = (ROOT / "internal" / "bugfix-flow" / "triage.md").read_text(
            encoding="utf-8"
        )
        cls.regression = (ROOT / "internal" / "bugfix-flow" / "regression.md").read_text(
            encoding="utf-8"
        )
        cls.verify = (ROOT / "internal" / "bugfix-flow" / "verify.md").read_text(
            encoding="utf-8"
        )

    def test_declares_four_authorization_modes(self) -> None:
        for mode in ("analyze", "fix", "commit", "unattended"):
            self.assertIn(f"`{mode}`", self.auto_fix)
        self.assertIn("fix 模式不得提交", self.auto_fix)
        self.assertIn("Issue 回写仍需单独授权", self.auto_fix)

    def test_analyze_reports_before_regression_write_stage(self) -> None:
        analyze_flow = self.auto_fix.index("analyze 路径")
        report = self.auto_fix.index("report", analyze_flow)
        regression = self.auto_fix.index("regress-red")
        self.assertLess(report, regression)
        self.assertIn("analyze 模式到此结束", self.auto_fix)

    def test_workspace_snapshot_preserves_preexisting_dirty_files(self) -> None:
        for token in (
            "WorkspaceSnapshot",
            "preexisting_changes",
            "AutoFixChangedFiles",
            "runtime.py snapshot",
            "runtime.py verify-workspace",
        ):
            self.assertIn(token, self.auto_fix)
        self.assertIn("已有修改允许保留", self.auto_fix)
        self.assertIn("目标文件在快照时已有修改", self.auto_fix)

    def test_root_cause_is_falsifiable(self) -> None:
        for token in ("Claim", "Prediction", "Probe", "Observation", "Status"):
            self.assertIn(token, self.auto_fix)
            self.assertIn(token, self.triage)
        self.assertIn("confirmed", self.auto_fix)
        self.assertIn("连续 3 个假设", self.auto_fix)
        self.assertNotIn("置信度均低（< 50%）", self.auto_fix)

    def test_regression_red_green_is_default_gate(self) -> None:
        for token in (
            "FailureSignature",
            "RegressionRedEvidence",
            "RegressionGreenEvidence",
            "RegressionSkipReason",
            "DONE_WITH_CONCERNS",
        ):
            self.assertIn(token, self.auto_fix + self.regression)
        self.assertIn("修复前失败", self.regression)
        self.assertIn("修复后通过", self.regression)

    def test_issue_content_is_untrusted_and_redacted(self) -> None:
        for token in ("不可信输入", "不得执行", "脱敏"):
            self.assertIn(token, self.auto_fix)
            self.assertIn(token, self.repro)
        self.assertIn("GitHub", self.auto_fix)
        self.assertIn("GitLab", self.auto_fix)
        self.assertNotIn("ONES", self.auto_fix)

    def test_review_and_verification_are_diff_bound(self) -> None:
        self.assertIn("ReviewDiffHash", self.auto_fix)
        self.assertIn("ReviewDiffHash 与 FinalDiffHash 失效", self.auto_fix)
        self.assertIn("FreshVerificationEvidence", self.verify)
        self.assertIn("最终 diff hash 与 ReviewDiffHash 不一致", self.verify)

    def test_validation_profiles_are_orthogonal_and_fail_safe(self) -> None:
        for token in (
            "ValidationProfile",
            "fast",
            "standard",
            "strict",
            "SchemaVersion",
            "ProfileAssessment",
            "VerificationPlan",
            "FinalDiffHash",
        ):
            self.assertIn(token, self.auto_fix)
        self.assertIn("旧状态", self.auto_fix)
        self.assertIn("默认 `strict`", self.auto_fix)
        self.assertIn("只允许自动升级", self.auto_fix)
        self.assertIn("最低为 `standard`", self.auto_fix)

    def test_fast_and_standard_final_verify_reuse_unchanged_evidence(self) -> None:
        self.assertIn("不重复执行耗时命令", self.auto_fix)
        self.assertIn("ReviewDiffHash", self.auto_fix)
        self.assertIn("FinalDiffHash", self.auto_fix)
        self.assertIn("subsumes", self.verify)
        self.assertIn("RepeatReason", self.verify)
        self.assertIn("禁止无理由重复", self.verify)

    def test_invalidation_is_impact_aware(self) -> None:
        for token in ("production", "test", "documentation", "shared-infrastructure"):
            self.assertIn(token, self.auto_fix)
        self.assertIn("文档变化", self.auto_fix)
        self.assertIn("共享基础设施", self.auto_fix)

    def test_completion_status_is_explicit(self) -> None:
        for status in ("DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"):
            self.assertIn(status, self.auto_fix)

    def test_git_workflow_stages_only_conversation_files(self) -> None:
        for token in ("WorkspaceSnapshot", "AutoFixChangedFiles", "git add -- <file>"):
            self.assertIn(token, self.git_workflow)
        self.assertNotIn("git add -A", self.git_workflow)
        self.assertIn("staged_scope_conflict", self.git_workflow)

    def test_preserves_public_platform_risk_boundaries(self) -> None:
        for token in ("Qt", "WPF", "Go", "Flutter", "Node.js", "Harmony"):
            self.assertIn(token, self.auto_fix)


if __name__ == "__main__":
    unittest.main()
