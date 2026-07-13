import tempfile
import unittest
from pathlib import Path

from context.contracts import discover_contract_index


class ContractDiscoveryTests(unittest.TestCase):
    def test_prefers_valid_existing_agents_reference_over_default_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "company").mkdir()
            (repo_root / "docs").mkdir()
            (repo_root / "company" / "GIT_RULES.md").write_text("# Team Git\n", encoding="utf-8")
            (repo_root / "docs" / "GIT_WORKFLOW.md").write_text("# Default Git\n", encoding="utf-8")
            (repo_root / "AGENTS.md").write_text(
                "<!-- dev-harness:managed:start id=agents.contract-index version=1 -->\n"
                "## 项目规范索引\n\n"
                "- Git 工作流：`company/GIT_RULES.md`\n"
                "<!-- dev-harness:managed:end id=agents.contract-index -->\n",
                encoding="utf-8",
            )

            contracts = discover_contract_index(repo_root)

            self.assertEqual(contracts.git_workflow, "company/GIT_RULES.md")

    def test_rejects_contract_symlink_outside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            repo_root = Path(tmp)
            (repo_root / "docs").mkdir()
            outside_file = Path(outside) / "GIT_WORKFLOW.md"
            outside_file.write_text("# External\n", encoding="utf-8")
            (repo_root / "docs" / "GIT_WORKFLOW.md").symlink_to(outside_file)

            contracts = discover_contract_index(repo_root)

            self.assertEqual(contracts.git_workflow, "Unknown")

    def test_uses_deterministic_specialist_document_priorities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "docs").mkdir()
            for relative in (
                "docs/GIT_WORKFLOW.md",
                "docs/CODE_STYLE.md",
                "docs/RELEASE.md",
                "CHANGELOG.md",
            ):
                (repo_root / relative).write_text(f"# {relative}\n", encoding="utf-8")

            contracts = discover_contract_index(repo_root)

            self.assertEqual(contracts.build, "HARNESS.md")
            self.assertEqual(contracts.git_workflow, "docs/GIT_WORKFLOW.md")
            self.assertEqual(contracts.code_style, "docs/CODE_STYLE.md")
            self.assertEqual(contracts.release, "docs/RELEASE.md")
            self.assertEqual(contracts.changelog, "CHANGELOG.md")


if __name__ == "__main__":
    unittest.main()
