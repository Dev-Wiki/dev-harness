import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NaturalChineseContractTests(unittest.TestCase):
    def test_all_skills_define_a_natural_chinese_default(self) -> None:
        expected = {
            "commands/SKILL.md": ("默认使用简体中文", "自然中文"),
            "context/SKILL.md": ("默认使用简体中文", "自然中文"),
            "dev-harness-docs/SKILL.md": ("Simplified Chinese", "natural Chinese"),
            "planning/SKILL.md": ("默认使用简体中文", "自然中文"),
            "git-workflow/SKILL.md": ("默认使用简体中文", "自然中文"),
            "auto-fix/SKILL.md": ("默认使用简体中文", "自然中文"),
            "codebase-audit/SKILL.md": ("默认使用简体中文（`zh-CN`）", "自然中文"),
            "retro/SKILL.md": ("默认使用简体中文", "自然中文"),
        }
        self.assertEqual(len(expected), 8)
        for relative, phrases in expected.items():
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(skill=relative):
                for phrase in phrases:
                    self.assertIn(phrase, text)

    def test_planning_templates_use_chinese_reader_labels(self) -> None:
        task = (ROOT / "planning/templates/Task.template.md").read_text(encoding="utf-8")
        compatibility_redirect = (ROOT / "planning/templates/TaskDetails.template.md").read_text(encoding="utf-8")
        archive = (ROOT / "planning/templates/ArchiveIndex.template.md").read_text(encoding="utf-8")

        self.assertTrue(task.startswith("# 任务 {任务编号}：{任务名称}"))
        for old_label in ("Create:", "Modify:", "Test:"):
            self.assertNotIn(old_label, task)
        self.assertIn("活跃任务入口已合并", compatibility_redirect)
        self.assertIn("[Dashboard.md](Dashboard.md)", compatibility_redirect)
        self.assertIn("| 任务编号 |", archive)

    def test_git_default_keeps_conventional_type_and_uses_chinese_description(self) -> None:
        skill = (ROOT / "git-workflow/SKILL.md").read_text(encoding="utf-8")
        contract = (ROOT / "git-workflow/references/default-contract.md").read_text(encoding="utf-8")
        for text in (skill, contract):
            self.assertIn("<type>(<scope>): <中文描述>", text)
            self.assertIn("用户明确要求英文", text)


if __name__ == "__main__":
    unittest.main()
