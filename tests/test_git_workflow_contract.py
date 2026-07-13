import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_CATEGORIES = (
    "Breaking Changes",
    "Added",
    "Changed",
    "Deprecated",
    "Fixed",
    "Removed",
    "Security",
)


class GitWorkflowContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_templates_use_confirmed_release_categories_in_order(self) -> None:
        for relative in (
            "git-workflow/templates/GIT_WORKFLOW.template.md",
            "git-workflow/templates/CHANGELOG.template.md",
        ):
            with self.subTest(relative=relative):
                content = self.read(relative)
                positions = [content.index(category) for category in RELEASE_CATEGORIES]
                self.assertEqual(positions, sorted(positions))
                self.assertNotIn("Deleted", content)

    def test_skill_prioritizes_project_rules_and_requires_confirmation(self) -> None:
        skill = self.read("git-workflow/SKILL.md")

        self.assertIn("仓库已有规范优先", skill)
        self.assertIn("显式确认", skill)
        self.assertIn("git log -100", skill)
        self.assertIn("dev-harness-context refresh", skill)
        self.assertIn("不得覆盖", skill)

    def test_defaults_support_single_and_feature_branch_modes(self) -> None:
        template = self.read("git-workflow/templates/GIT_WORKFLOW.template.md")

        self.assertIn("single-branch", template)
        self.assertIn("feature-branch", template)
        self.assertIn("由项目确认", template)

    def test_tag_and_release_messages_omit_empty_categories(self) -> None:
        surfaces = self.read("git-workflow/SKILL.md") + self.read("docs/GIT_WORKFLOW.md")

        self.assertIn("vMAJOR.MINOR.PATCH", surfaces)
        self.assertIn("annotated tag", surfaces)
        self.assertIn("省略空分类", surfaces)
        self.assertIn("CHANGELOG.md", surfaces)

    def test_open_source_contract_has_no_company_branch_baselines(self) -> None:
        relative_paths = (
            "context/templates/AGENTS.template.md",
            "git-workflow/SKILL.md",
            "docs/GIT_WORKFLOW.md",
        )
        forbidden = (
            "公司" + " Git 门禁",
            "master_" + "5.2",
            "release_" + "pub",
            "pri" + "vate_6.0",
        )
        for relative in relative_paths:
            content = self.read(relative)
            for marker in forbidden:
                self.assertNotIn(marker, content, f"{marker} leaked into {relative}")
        self.assertFalse((ROOT / "tests" / "test_branch_rules.py").exists())


if __name__ == "__main__":
    unittest.main()
