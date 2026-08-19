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
        self.assertIn("Assign each changing fact exactly one writable owner", skill)
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
        self.assertIn("stable ID for each leaf capability", reference)
        self.assertIn("exclude `Pending confirmation / 待确认` rows", reference)
        for column in (
            "ID",
            "Capability domain",
            "Observable capability",
            "Product status",
            "Availability scope",
            "Delivery baseline",
            "Verification level",
            "Evidence",
            "Details",
        ):
            self.assertIn(column, template)
        for status in ("Supported", "Partial", "Experimental", "Deprecated"):
            self.assertIn(status, template)
        self.assertIn("Pending confirmation / 待确认", template)

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
        self.assertIn("Documentation governance owns only the stable link", reference)

    def test_planning_uses_resolved_docs_root(self) -> None:
        skill = (ROOT / "planning" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("<docs-root>/plan/Dashboard.md", skill)
        self.assertIn("<docs-root>/plan/TaskDetails.md", skill)
        self.assertIn("If only `doc/` exists, use `doc/`", skill)
        self.assertIn("If both exist and ownership is ambiguous", skill)
        self.assertNotIn("Default output paths:\n\n- `docs/plan/Dashboard.md`", skill)


if __name__ == "__main__":
    unittest.main()
