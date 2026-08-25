import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DocsSkillContractTests(unittest.TestCase):
    def test_docs_skill_declares_root_resolution_and_ssot_boundaries(self) -> None:
        skill = (ROOT / "dev-harness-docs" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("name: dev-harness-docs", skill)
        self.assertIn("If only `doc/` exists, use `doc/`", skill)
        self.assertIn("If only `docs/` exists, use `docs/`", skill)
        self.assertIn("Never rename an established root or create a second root", skill)
        self.assertIn(
            "Designate exactly one authoritative maintenance document for each changing fact",
            skill,
        )
        self.assertIn("Create `nav/` only when", skill)
        self.assertIn('rg --files "$DOCS_ROOT"', skill)

    def test_docs_skill_assets_have_no_unresolved_scaffold_todos(self) -> None:
        files = [
            ROOT / "dev-harness-docs" / "SKILL.md",
            ROOT / "dev-harness-docs" / "references" / "information-architecture.md",
            ROOT / "dev-harness-docs" / "assets" / "capabilities.template.md",
            ROOT / "dev-harness-docs" / "assets" / "docs-index.template.md",
            ROOT / "dev-harness-docs" / "assets" / "documentation-rules.template.md",
            ROOT / "dev-harness-docs" / "assets" / "nav.template.md",
        ]

        for path in files:
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("[TODO:", content, path.name)

    def test_capability_catalog_is_conditional_countable_and_evidence_backed(self) -> None:
        skill = (ROOT / "dev-harness-docs" / "SKILL.md").read_text(encoding="utf-8")
        reference = (
            ROOT / "dev-harness-docs" / "references" / "information-architecture.md"
        ).read_text(encoding="utf-8")
        template = (
            ROOT / "dev-harness-docs" / "assets" / "capabilities.template.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Treat it as a conditional product-scope SSOT", skill)
        self.assertIn("Reuse an equivalent SSOT regardless of filename", skill)
        self.assertIn("<docs-root>/product/CAPABILITIES.md", skill)
        self.assertIn("<docs-root>/CAPABILITIES.md", skill)
        self.assertIn("Never infer product support from route", skill)
        self.assertIn("Planning owns future work and task status", skill)
        self.assertIn("CHANGELOG owns released deltas", skill)
        self.assertIn(
            "为每个用户或集成方能够操作并确认的可独立验证功能项分配一个稳定 ID",
            reference,
        )
        self.assertIn("“待确认（Pending confirmation）”中的项目不计入", reference)
        for column in (
            "ID",
            "功能分类",
            "功能说明",
            "支持状态",
            "适用范围",
            "版本归属",
            "验证方式",
            "证据",
            "详情",
        ):
            self.assertIn(column, template)
        for status in ("已支持", "部分支持", "试验性", "已弃用"):
            self.assertIn(status, template)
        self.assertIn("## 待确认", template)
        self.assertIn("当前开发版本与最新发布版本分别统计", template)
        self.assertIn(
            "“支持状态”“适用范围”“版本归属”和“验证方式”必须分别记录",
            template,
        )

    def test_capability_catalog_uses_natural_zh_cn_terms(self) -> None:
        paths = (
            ROOT / "dev-harness-docs" / "SKILL.md",
            ROOT
            / "dev-harness-docs"
            / "references"
            / "information-architecture.md",
            ROOT / "dev-harness-docs" / "assets" / "capabilities.template.md",
            ROOT
            / "dev-harness-docs"
            / "assets"
            / "documentation-rules.template.md",
        )
        source = "\n".join(path.read_text(encoding="utf-8") for path in paths)

        for translated_term in (
            "当前产品可观察能力",
            "可观察能力",
            "叶子能力",
            "能力域",
            "交付基线",
            "验证等级",
            "当前仓库",
            "唯一可写清单",
            "已有等价 Owner",
        ):
            self.assertNotIn(translated_term, source)

        source_lower = source.lower()
        for translation_trigger in (
            "current observable capabilities",
            "observable capability",
            "leaf capability",
            "capability domain",
            "delivery baseline",
            "verification level",
            "current repository",
            "writable owner",
            "equivalent owner",
        ):
            self.assertNotIn(translation_trigger, source_lower)

        for natural_term in (
            "产品功能清单",
            "当前已支持功能",
            "可独立验证的功能项",
            "功能分类",
            "功能说明",
            "支持状态",
            "适用范围",
            "版本归属",
            "验证方式",
            "当前开发版本",
            "权威维护文档",
            "已有同类功能说明文档",
        ):
            self.assertIn(natural_term, source)

        self.assertIn("中文仓库使用自然中文", source)
        self.assertIn("英文仓库可改用自然英文", source)
        self.assertIn("“可观测性”只用于日志、指标和链路追踪", source)

    def test_docs_refresh_owns_codebase_audit_discoverability(self) -> None:
        skill = (ROOT / "dev-harness-docs" / "SKILL.md").read_text(encoding="utf-8")
        reference = (
            ROOT / "dev-harness-docs" / "references" / "information-architecture.md"
        ).read_text(encoding="utf-8")

        self.assertIn("## Publish Codebase Audit Navigation", skill)
        self.assertIn("<docs-root>/audit/Report.md", skill)
        self.assertIn("Make the update idempotent", skill)
        self.assertIn("root `README.md` shortcut is optional", skill)
        self.assertIn("Audit initializes its snapshot", skill)
        self.assertIn("文档治理只负责", reference)

    def test_docs_output_language_defaults_to_natural_simplified_chinese(self) -> None:
        skill = (ROOT / "dev-harness-docs" / "SKILL.md").read_text(encoding="utf-8")
        docs_index = (
            ROOT / "dev-harness-docs" / "assets" / "docs-index.template.md"
        ).read_text(encoding="utf-8")
        nav = (
            ROOT / "dev-harness-docs" / "assets" / "nav.template.md"
        ).read_text(encoding="utf-8")

        self.assertIn("If the user explicitly requests English", skill)
        self.assertIn("use Simplified Chinese", skill)
        self.assertIn("follow its primary language", skill)
        self.assertIn("Translate by meaning, not word by word", skill)
        self.assertIn("internal English enum", skill)
        self.assertIn("# {项目名称}文档中心", docs_index)
        self.assertIn("## 阅读路径", docs_index)
        self.assertIn("# 阅读路径：{路径名称}", nav)
        self.assertNotIn("## Reader routes", docs_index)
        self.assertNotIn("## Task routing", nav)

    def test_planning_uses_resolved_docs_root(self) -> None:
        skill = (ROOT / "planning" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("<docs-root>/plan/Dashboard.md", skill)
        self.assertIn("<docs-root>/plan/TaskDetails.md", skill)
        self.assertIn("If only `doc/` exists, use `doc/`", skill)
        self.assertIn("If both exist and ownership is ambiguous", skill)
        self.assertNotIn("Default output paths:\n\n- `docs/plan/Dashboard.md`", skill)


if __name__ == "__main__":
    unittest.main()
