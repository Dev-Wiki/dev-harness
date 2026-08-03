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
            ROOT / "dev-harness-docs" / "assets" / "docs-index.template.md",
            ROOT / "dev-harness-docs" / "assets" / "documentation-rules.template.md",
            ROOT / "dev-harness-docs" / "assets" / "nav.template.md",
        ]

        for path in files:
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("[TODO:", content, path.name)

    def test_planning_uses_resolved_docs_root(self) -> None:
        skill = (ROOT / "planning" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("<docs-root>/plan/Dashboard.md", skill)
        self.assertIn("<docs-root>/plan/TaskDetails.md", skill)
        self.assertIn("If only `doc/` exists, use `doc/`", skill)
        self.assertIn("If both exist and ownership is ambiguous", skill)
        self.assertNotIn("Default output paths:\n\n- `docs/plan/Dashboard.md`", skill)


if __name__ == "__main__":
    unittest.main()
