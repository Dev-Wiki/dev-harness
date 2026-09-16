import json
import os
import tempfile
import unittest
from pathlib import Path

from context.cli import generate_context_files
from context.evidence import collect_repository_evidence
from context.semantic import SemanticAnalysisError, load_semantic_analysis


class ContextEvidenceIntegrityTests(unittest.TestCase):
    def analysis(self, parent, repo, claims=None, lists=None):
        path = parent / "analysis.json"
        path.write_text(json.dumps({
            "schema_version": 1,
            "evidence_fingerprint": collect_repository_evidence(repo)["evidence_fingerprint"],
            "claims": claims or {},
            "lists": lists or {},
        }), encoding="utf-8")
        return path

    def test_workspace_sources_and_ci_changes_are_in_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            repo = parent / "repo"
            (repo / "packages/app").mkdir(parents=True)
            (repo / "packages/app/index.ts").write_text("export const version = 1;\n")
            (repo / ".github/workflows").mkdir(parents=True)
            ci = repo / ".github/workflows/ci.yml"
            ci.write_text("run: npm test\n")
            evidence = collect_repository_evidence(repo)
            self.assertIn("packages/app/index.ts", evidence["source_candidates"])
            self.assertIn(".github/workflows/ci.yml", evidence["important_files"])
            path = self.analysis(parent, repo, {"test_command": {
                "value": "npm test", "confidence": "high", "evidence": [".github/workflows/ci.yml:1"],
            }})
            ci.write_text("run: npm run integration\n")
            with self.assertRaisesRegex(SemanticAnalysisError, "fingerprint changed"):
                load_semantic_analysis(path, repo)

    def test_excluded_dependency_and_cache_evidence_is_rejected(self):
        for directory in ("node_modules", ".venv", ".git"):
            with self.subTest(directory=directory), tempfile.TemporaryDirectory() as tmp:
                parent = Path(tmp)
                repo = parent / "repo"
                (repo / directory).mkdir(parents=True)
                (repo / directory / "entry.py").write_text("print('dependency')\n")
                (repo / "app.py").write_text("print('application')\n")
                self.assertEqual(collect_repository_evidence(repo)["file_count"], 1)
                path = self.analysis(parent, repo, {"core_entry": {
                    "value": "entry", "confidence": "high", "evidence": [f"{directory}/entry.py:1"],
                }})
                with self.assertRaisesRegex(SemanticAnalysisError, "not covered by.*snapshot"):
                    load_semantic_analysis(path, repo)

    def test_directory_evidence_requires_an_included_descendant(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            repo = parent / "repo"
            (repo / "src").mkdir(parents=True)
            (repo / "src/main.py").write_text("pass\n")
            (repo / "empty").mkdir()
            path = self.analysis(parent, repo, {"core_entry": {
                "value": "source tree", "confidence": "high", "evidence": ["src"],
            }})
            self.assertEqual(load_semantic_analysis(path, repo).claims["core_entry"], "source tree")
            path = self.analysis(parent, repo, {"core_entry": {
                "value": "empty tree", "confidence": "high", "evidence": ["empty"],
            }})
            with self.assertRaisesRegex(SemanticAnalysisError, "not covered by.*snapshot"):
                load_semantic_analysis(path, repo)

    def test_fingerprint_covers_file_content_after_first_chunk(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            path = repo / "large.py"
            path.write_bytes(b"#" * 65536 + b"a\n")
            before = collect_repository_evidence(repo)["evidence_fingerprint"]
            previous = path.stat()
            path.write_bytes(b"#" * 65536 + b"b\n")
            os.utime(path, ns=(previous.st_atime_ns, previous.st_mtime_ns))
            self.assertNotEqual(before, collect_repository_evidence(repo)["evidence_fingerprint"])

    def test_unknown_empty_and_low_confidence_do_not_restore_profile_facts(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            repo = parent / "repo"
            repo.mkdir()
            (repo / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")
            (repo / "tests").mkdir()
            (repo / "tests/test_main.py").write_text("import unittest\n")
            path = self.analysis(parent, repo, {
                "test_command": {"value": "Unknown", "confidence": "high", "evidence": []},
                "style_rules": {"value": "Unknown", "confidence": "high", "evidence": []},
                "architecture_rules": {"value": "Possible routing layer", "confidence": "low", "evidence": ["main.py:1"]},
                "high_risk_files": {"value": "Unknown", "confidence": "high", "evidence": []},
            }, {"module_interfaces": [], "core_modules": []})
            analysis = load_semantic_analysis(path, repo)
            self.assertEqual(analysis.claim("style_rules", "fallback"), "Unknown")
            self.assertEqual(analysis.claim("architecture_rules", "fallback"), "Unknown")
            self.assertEqual(analysis.claim("logging_rules", "fallback"), "fallback")
            self.assertEqual(analysis.items("core_modules", ["fallback"]), [])
            documents = generate_context_files(repo, analysis)
            self.assertIn("- **test**: `Unknown`", documents["HARNESS.md"])
            self.assertIn("## 2. 命名与风格约束\n\nUnknown", documents["AGENTS.md"])
            self.assertIn("## 3. 架构边界规则\n\nUnknown", documents["AGENTS.md"])
            self.assertIn("## 5. 高风险文件标注\n\nUnknown", documents["AGENTS.md"])
            self.assertNotIn("通过 FastAPI include_router 注册路由", documents["ARCHITECTURE.md"])
            self.assertIn("Possible routing layer", documents["AGENTS.md"])

    def test_missing_analysis_fields_do_not_enable_offline_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            repo = parent / "repo"
            repo.mkdir()
            (repo / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")
            path = self.analysis(parent, repo)
            documents = generate_context_files(repo, load_semantic_analysis(path, repo))
            self.assertIn("## 2. 命名与风格约束\n\nUnknown", documents["AGENTS.md"])
            self.assertNotIn("通过 FastAPI include_router 注册路由", documents["ARCHITECTURE.md"])
            offline = generate_context_files(repo)
            self.assertIn("通过 FastAPI include_router 注册路由", offline["ARCHITECTURE.md"])


if __name__ == "__main__":
    unittest.main()
