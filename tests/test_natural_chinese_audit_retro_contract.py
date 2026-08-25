import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NaturalChineseAuditRetroContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_owned_skills_define_language_selection_and_refresh_behavior(self) -> None:
        for relative in (
            "auto-fix/SKILL.md",
            "codebase-audit/SKILL.md",
            "retro/SKILL.md",
        ):
            content = self.read(relative)
            self.assertIn("## 输出语言", content, relative)
            self.assertIn("用户明确要求", content, relative)
            self.assertIn("主体语言", content, relative)
            self.assertIn("简体中文", content, relative)
            self.assertIn("顺带", content, relative)

    def test_internal_values_keep_stable_names_but_gain_chinese_display_names(self) -> None:
        auto_fix = self.read("auto-fix/SKILL.md")
        for display, internal in (
            ("已完成", "DONE"),
            ("已完成但有留存风险", "DONE_WITH_CONCERNS"),
            ("受阻", "BLOCKED"),
            ("缺少关键信息", "NEEDS_CONTEXT"),
        ):
            self.assertIn(f"{display}（`{internal}`）", auto_fix)

        retro = self.read("retro/SKILL.md")
        for category in ("FACT", "POLICY", "LESSON"):
            self.assertIn(f"`{category}`", retro)
        self.assertIn("待纳入正式规范的候选结论", retro)

    def test_default_audit_templates_use_chinese_reader_facing_headings(self) -> None:
        template_names = (
            "AuditTask.template.md",
            "AuditResult.template.md",
            "Dashboard.template.md",
            "Findings.template.md",
            "Report.template.md",
        )
        forbidden_headings = (
            "# Finding Contract",
            "## Finding 详情",
            "## Required Result",
            "## Promotion Candidates",
            "## Evidence Quality",
        )
        for name in template_names:
            content = self.read(f"codebase-audit/templates/{name}")
            self.assertIn("## 导航", content, name)
            for heading in forbidden_headings:
                self.assertNotIn(heading, content, name)


if __name__ == "__main__":
    unittest.main()
