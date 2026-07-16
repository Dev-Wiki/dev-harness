import json
import tempfile
import unittest
from pathlib import Path

from context.evidence import collect_repository_evidence
from context.semantic import SemanticAnalysisError, load_semantic_analysis


class SemanticAnalysisTests(unittest.TestCase):
    def _write_analysis(self, root: Path, repo_root: Path, claims: dict) -> Path:
        evidence = collect_repository_evidence(repo_root)
        path = root / "analysis.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "evidence_fingerprint": evidence["evidence_fingerprint"],
                    "claims": claims,
                    "lists": {},
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


if __name__ == "__main__":
    unittest.main()
