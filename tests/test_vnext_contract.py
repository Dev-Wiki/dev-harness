import unittest
from pathlib import Path

from context.evidence import analysis_contract


ROOT = Path(__file__).resolve().parents[1]


class RetroVNextContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_retro_is_explicit_and_has_three_non_interchangeable_types(self) -> None:
        skill = self.read("retro/SKILL.md")
        frontmatter = skill.split("---", 2)[1]

        self.assertIn("仅在用户明确要求", frontmatter)
        for category in ("FACT", "POLICY", "LESSON"):
            self.assertIn(f"`{category}`", skill)
        self.assertIn("一次 AI 失误不是 `FACT`", skill)
        self.assertIn("历史提交习惯不是 `POLICY`", skill)
        self.assertIn("`LESSON` 不自动成为永久约束", skill)
        self.assertIn("Promotion Candidates", skill)
        self.assertIn("不得在一次 Retro 中静默修改多个 Skill", skill)

    def test_lessons_are_not_unconditionally_injected_or_loaded(self) -> None:
        install = self.read("install.py")
        agents_template = self.read("context/templates/AGENTS.template.md")

        self.assertNotIn("_inject_lessons_into_agents", install)
        self.assertNotIn("_ensure_lessons_md", install)
        self.assertIn("不是默认硬约束", agents_template)
        for relative in (
            "context/SKILL.md",
            "commands/SKILL.md",
            "git-workflow/SKILL.md",
            "dev-harness-docs/SKILL.md",
        ):
            self.assertNotIn("_LESSONS=", self.read(relative), relative)


class ProjectContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_readme_defines_project_contract_and_two_skill_groups(self) -> None:
        readme = self.read("README.md")

        for principle in ("Consistency", "Evidence", "Continuity"):
            self.assertIn(principle, readme)
        self.assertIn("Project Contract / Governance", readme)
        self.assertIn("Evidence-driven Long-running Workflows", readme)
        self.assertIn("dev-harness-codebase-audit", readme)
        self.assertIn("8 个可发现 Skill", readme)
        self.assertIn("不以覆盖完整 SDLC", readme)

    def test_harness_exposes_five_commands_and_variant_record_shape(self) -> None:
        harness = self.read("context/templates/HARNESS.template.md")
        commands = self.read("commands/SKILL.md")

        for purpose in ("build", "test", "quick", "bugfix", "full"):
            self.assertIn(f"**{purpose}**", harness)
            self.assertIn(f"harness:{purpose}", commands)
        for field in (
            "Purpose",
            "WorkingDirectory",
            "Platform / Variant",
            "Preconditions",
            "DeviceRequirement",
            "Shell / Environment",
            "Evidence",
            "Status",
        ):
            self.assertIn(field, commands)
        self.assertIn("test_command", analysis_contract()["claims"])

    def test_cross_skill_audit_ownership_and_handoffs_are_explicit(self) -> None:
        audit = self.read("codebase-audit/SKILL.md")
        docs = self.read("dev-harness-docs/SKILL.md")
        auto_fix = self.read("auto-fix/SKILL.md")
        planning = self.read("planning/SKILL.md")

        self.assertIn("<docs-root>/audit/**", audit)
        self.assertIn("Cross-module Reconciliation", audit)
        self.assertIn("dynamic partition", audit)
        self.assertIn("`dev-harness-auto-fix`", audit)
        self.assertIn("`dev-harness-planning`", audit)
        self.assertIn("own content under `<docs-root>/audit/`", docs)
        self.assertIn("Documentation Discoverability", audit)
        self.assertIn("`linked`", audit)
        self.assertIn("`docs-refresh-required`", audit)
        self.assertIn("Audit 自己不得越界写入", audit)
        self.assertIn("## Publish Codebase Audit Navigation", docs)
        self.assertIn("`AUD-*` Finding", auto_fix)
        self.assertIn("Codebase Audit finding", planning)

        dashboard = self.read("codebase-audit/templates/Dashboard.template.md")
        report = self.read("codebase-audit/templates/Report.template.md")
        for template in (dashboard, report):
            self.assertIn("Documentation Discoverability", template)
            self.assertIn("Stable Audit Entry", template)
            self.assertIn("docs-refresh-required", template)

    def test_planning_refresh_preserves_ids_and_requires_completion_evidence(self) -> None:
        planning = self.read("planning/SKILL.md")

        self.assertIn("preserve existing task IDs", planning)
        self.assertIn("Never mark a task completed from AI inference alone", planning)
        self.assertIn("do not add it to the roadmap until the user accepts", planning)


if __name__ == "__main__":
    unittest.main()
