import json
import tempfile
import unittest
from pathlib import Path

from context.evidence import analysis_contract, collect_repository_evidence
from context.semantic import SemanticAnalysisError, load_semantic_analysis


class SemanticAnalysisTests(unittest.TestCase):
    def test_analysis_contract_exposes_document_noise_guards(self) -> None:
        contract = analysis_contract()

        self.assertIn("core_modules", contract["lists"])
        rules = "\n".join(contract["rules"])
        self.assertIn("line references", rules)
        self.assertIn("Installation-only commands", rules)
        self.assertIn("counterexample search", rules)

    def _write_analysis(
        self,
        root: Path,
        repo_root: Path,
        claims: dict,
        lists: dict | None = None,
    ) -> Path:
        evidence = collect_repository_evidence(repo_root)
        path = root / "analysis.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "evidence_fingerprint": evidence["evidence_fingerprint"],
                    "claims": claims,
                    "lists": lists or {},
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_low_confidence_claim_becomes_manual_review_instead_of_fact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_root = root / "repo"
            repo_root.mkdir()
            (repo_root / "entry.custom").write_text("boot\n", encoding="utf-8")
            analysis_path = self._write_analysis(
                root,
                repo_root,
                {
                    "project_type": {
                        "value": "MaybeFramework",
                        "confidence": "low",
                        "evidence": ["entry.custom:1"],
                    }
                },
            )

            analysis = load_semantic_analysis(analysis_path, repo_root)

            self.assertNotIn("project_type", analysis.claims)
            self.assertIn("MaybeFramework", "\n".join(analysis.manual_review_items))

    def test_repository_drift_invalidates_prior_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_root = root / "repo"
            repo_root.mkdir()
            entry = repo_root / "entry.custom"
            entry.write_text("boot\n", encoding="utf-8")
            analysis_path = self._write_analysis(
                root,
                repo_root,
                {
                    "project_type": {
                        "value": "CustomFramework",
                        "confidence": "high",
                        "evidence": ["entry.custom:1"],
                    }
                },
            )
            entry.write_text("boot changed\n", encoding="utf-8")

            with self.assertRaisesRegex(SemanticAnalysisError, "fingerprint changed"):
                load_semantic_analysis(analysis_path, repo_root)

    def test_evidence_reference_cannot_escape_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_root = root / "repo"
            repo_root.mkdir()
            (repo_root / "entry.custom").write_text("boot\n", encoding="utf-8")
            analysis_path = self._write_analysis(
                root,
                repo_root,
                {
                    "project_type": {
                        "value": "CustomFramework",
                        "confidence": "high",
                        "evidence": ["../outside.txt"],
                    }
                },
            )

            with self.assertRaisesRegex(SemanticAnalysisError, "stay inside"):
                load_semantic_analysis(analysis_path, repo_root)

    def test_out_of_range_evidence_line_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_root = root / "repo"
            repo_root.mkdir()
            (repo_root / "app.py").write_text("print('one line')\n", encoding="utf-8")
            analysis_path = self._write_analysis(
                root,
                repo_root,
                {
                    "core_entry": {
                        "value": "app.py",
                        "confidence": "high",
                        "evidence": ["app.py:99"],
                    }
                },
            )

            with self.assertRaisesRegex(SemanticAnalysisError, "line is out of range"):
                load_semantic_analysis(analysis_path, repo_root)

    def test_install_command_cannot_be_used_as_build_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_root = root / "repo"
            repo_root.mkdir()
            (repo_root / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
            install = "python -m pip install -r requirements.txt"
            analysis_path = self._write_analysis(
                root,
                repo_root,
                {
                    "install_command": {
                        "value": install,
                        "confidence": "high",
                        "evidence": ["requirements.txt:1"],
                    },
                    "build_command": {
                        "value": install,
                        "confidence": "high",
                        "evidence": ["requirements.txt:1"],
                    },
                },
            )

            with self.assertRaisesRegex(SemanticAnalysisError, "installation command cannot be used"):
                load_semantic_analysis(analysis_path, repo_root)

    def test_normative_claim_requires_exact_line_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_root = root / "repo"
            repo_root.mkdir()
            (repo_root / "db.py").write_text("def save():\n    pass\n", encoding="utf-8")
            analysis_path = self._write_analysis(
                root,
                repo_root,
                {
                    "architecture_rules": {
                        "value": "所有数据库写入必须使用 Session",
                        "confidence": "high",
                        "evidence": ["db.py"],
                    }
                },
            )

            with self.assertRaisesRegex(SemanticAnalysisError, "normative claims require exact line evidence"):
                load_semantic_analysis(analysis_path, repo_root)


if __name__ == "__main__":
    unittest.main()
