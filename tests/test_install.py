import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from install import (
    PLANNING_REFERENCE_FILES,
    PLANNING_TEMPLATE_FILES,
    SKILL_SOURCES,
    install_bundle_to_root,
)
import release


class InstallBundleTests(unittest.TestCase):
    def test_full_install_contains_every_registered_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_root = Path(tmp) / "bundle"

            install_bundle_to_root(bundle_root)

            installed = {path.name for path in (bundle_root / "skills").iterdir() if path.is_dir()}
            self.assertEqual(installed, set(SKILL_SOURCES))

    def test_installer_does_not_create_or_inject_lessons_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_root = Path(tmp) / "bundle"
            bundle_root.mkdir()
            agents = bundle_root / "AGENTS.md"
            agents.write_text("# Existing agent rules\n", encoding="utf-8")

            install_bundle_to_root(bundle_root, ["dev-harness-retro"])

            self.assertEqual(agents.read_text(encoding="utf-8"), "# Existing agent rules\n")
            self.assertFalse((bundle_root / "LESSONS.md").exists())

    def test_installed_context_templates_are_skill_local(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_root = root / "bundle"

            install_bundle_to_root(bundle_root, ["dev-harness-context"])
            skill_root = bundle_root / "skills" / "dev-harness-context"

            self.assertTrue((skill_root / "templates" / "README.template.md").exists())
            self.assertTrue((skill_root / "templates" / "AGENTS.template.md").exists())
            self.assertFalse((skill_root / "templates" / "context").exists())
            self.assertTrue((skill_root / "references" / "platform-enhancements.md").exists())

    def test_installed_commands_includes_progressive_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_root = Path(tmp) / "bundle"

            install_bundle_to_root(bundle_root, ["dev-harness-commands"])
            skill_root = bundle_root / "skills" / "dev-harness-commands"

            self.assertTrue((skill_root / "references" / "platform-command-mapping.md").exists())
            self.assertTrue((skill_root / "references" / "windows-shell.md").exists())

    def test_installed_planning_skill_includes_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_root = root / "bundle"

            install_bundle_to_root(bundle_root, ["dev-harness-planning"])
            skill_root = bundle_root / "skills" / "dev-harness-planning"

            self.assertTrue((skill_root / "SKILL.md").exists())
            for template_name in PLANNING_TEMPLATE_FILES:
                self.assertTrue(
                    (skill_root / "templates" / template_name).exists(),
                    template_name,
                )
            for reference_name in PLANNING_REFERENCE_FILES:
                self.assertTrue(
                    (skill_root / "references" / reference_name).exists(),
                    reference_name,
                )

    def test_installed_docs_skill_is_self_contained(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_root = root / "bundle"

            install_bundle_to_root(bundle_root, ["dev-harness-docs"])
            skill_root = bundle_root / "skills" / "dev-harness-docs"

            self.assertTrue((skill_root / "SKILL.md").exists())
            self.assertTrue((skill_root / "references" / "information-architecture.md").exists())
            self.assertTrue((skill_root / "assets" / "capabilities.template.md").exists())
            self.assertTrue((skill_root / "assets" / "docs-index.template.md").exists())
            self.assertTrue((skill_root / "assets" / "documentation-rules.template.md").exists())
            self.assertTrue((skill_root / "assets" / "nav.template.md").exists())
            self.assertTrue((skill_root / "agents" / "openai.yaml").exists())
            agent_metadata = (skill_root / "agents" / "openai.yaml").read_text(encoding="utf-8")
            self.assertIn('display_name: "dev-harness-docs"', agent_metadata)

    def test_installed_git_workflow_includes_default_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_root = root / "bundle"

            install_bundle_to_root(bundle_root, ["dev-harness-git-workflow"])
            skill_root = bundle_root / "skills" / "dev-harness-git-workflow"

            self.assertTrue((skill_root / "templates" / "GIT_WORKFLOW.template.md").exists())
            self.assertTrue((skill_root / "templates" / "CHANGELOG.template.md").exists())
            self.assertTrue((skill_root / "references" / "default-contract.md").exists())

    def test_installed_codebase_audit_is_self_contained_and_brings_context_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_root = Path(tmp) / "bundle"

            install_bundle_to_root(bundle_root, ["dev-harness-codebase-audit"])
            skill_root = bundle_root / "skills" / "dev-harness-codebase-audit"

            self.assertTrue((bundle_root / "skills" / "dev-harness-context" / "SKILL.md").exists())
            self.assertTrue((skill_root / "SKILL.md").exists())
            self.assertTrue((skill_root / "runtime.py").exists())
            for file_name in (
                "workflow.md",
                "partitioning.md",
                "finding-contract.md",
                "cross-module-review.md",
            ):
                self.assertTrue((skill_root / "references" / file_name).exists(), file_name)
            for file_name in (
                "Dashboard.template.md",
                "Findings.template.md",
                "AuditTask.template.md",
                "AuditResult.template.md",
                "Report.template.md",
            ):
                self.assertTrue((skill_root / "templates" / file_name).exists(), file_name)

    def test_installed_auto_fix_includes_runtime_and_all_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_root = Path(tmp) / "bundle"

            install_bundle_to_root(bundle_root, ["dev-harness-auto-fix"])
            skill_root = bundle_root / "skills" / "dev-harness-auto-fix"
            refs = skill_root / "references" / "bugfix-flow"

            self.assertTrue((skill_root / "runtime.py").exists())
            for file_name in ("repro.md", "triage.md", "regression.md", "verify.md"):
                self.assertTrue((refs / file_name).exists(), file_name)

    def test_installed_context_launcher_can_scan_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_root = root / "bundle"
            repo_root = root / "demo-repo"
            repo_root.mkdir()
            (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")

            install_bundle_to_root(bundle_root, ["dev-harness-context"])
            launcher = bundle_root / "skills" / "dev-harness-context" / "dev-harness-context"

            result = subprocess.run(
                [sys.executable, str(launcher), "scan", str(repo_root)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((repo_root / "HARNESS.md").exists())

            evidence = subprocess.run(
                [sys.executable, str(launcher), "evidence", str(repo_root)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(evidence.returncode, 0, evidence.stderr)
            self.assertIn("evidence_fingerprint", evidence.stdout)
            self.assertTrue((bundle_root / "skills" / "dev-harness-context" / "lib" / "context" / "semantic.py").exists())

            evidence_payload = json.loads(evidence.stdout)
            analysis_path = root / "analysis.json"
            analysis_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "evidence_fingerprint": evidence_payload["evidence_fingerprint"],
                        "claims": {
                            "project_type": {
                                "value": "CustomFramework",
                                "confidence": "high",
                                "evidence": ["package.json"],
                            }
                        },
                        "lists": {},
                    }
                ),
                encoding="utf-8",
            )
            refresh = subprocess.run(
                [
                    sys.executable,
                    str(launcher),
                    "refresh",
                    str(repo_root),
                    "--analysis",
                    str(analysis_path),
                    "--force",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(refresh.returncode, 0, refresh.stderr)
            self.assertIn("CustomFramework", (repo_root / "HARNESS.md").read_text(encoding="utf-8"))

    def test_installed_context_launcher_can_refresh_managed_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_root = root / "bundle"
            repo_root = root / "demo-repo"
            repo_root.mkdir()
            (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")

            install_bundle_to_root(bundle_root, ["dev-harness-context"])
            skill_root = bundle_root / "skills" / "dev-harness-context"
            launcher = skill_root / "dev-harness-context"
            scan = subprocess.run(
                [sys.executable, str(launcher), "scan", str(repo_root)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(scan.returncode, 0, scan.stderr)
            agents_path = repo_root / "AGENTS.md"
            agents_path.write_text(
                agents_path.read_text(encoding="utf-8") + "\n团队自定义约束\n",
                encoding="utf-8",
            )
            (repo_root / "CMakeLists.txt").write_text("project(Demo)\n", encoding="utf-8")

            refresh = subprocess.run(
                [sys.executable, str(launcher), "refresh", str(repo_root), "--force"],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(refresh.returncode, 0, refresh.stderr)
            self.assertIn("团队自定义约束", agents_path.read_text(encoding="utf-8"))
            self.assertTrue((skill_root / "lib" / "context" / "managed.py").exists())

    def test_release_archive_is_self_contained_and_installable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dist_dir = root / "dist"
            extracted = root / "extracted"
            install_root = root / "installed"

            with patch.object(release, "DIST_DIR", dist_dir):
                release.main()

            archive = dist_dir / f"dev-harness-v{release.VERSION_FILE.read_text(encoding='utf-8').strip()}.zip"
            with zipfile.ZipFile(archive) as zf:
                names = set(zf.namelist())
                self.assertIn("install.py", names)
                self.assertIn("VERSION", names)
                self.assertIn("context/platform_profiles.py", names)
                self.assertIn("codebase-audit/runtime.py", names)
                self.assertIn("codebase-audit/references/finding-contract.md", names)
                self.assertIn("skills/dev-harness-codebase-audit/runtime.py", names)
                self.assertIn("dev-harness-docs/SKILL.md", names)
                self.assertIn("dev-harness-docs/assets/capabilities.template.md", names)
                self.assertIn("planning/templates/Task.template.md", names)
                self.assertIn("planning/templates/ArchiveIndex.template.md", names)
                self.assertIn("planning/references/legacy-migration.md", names)
                self.assertIn(
                    "skills/dev-harness-planning/templates/Task.template.md", names
                )
                self.assertIn(
                    "skills/dev-harness-planning/references/legacy-migration.md", names
                )
                self.assertIn(
                    "skills/dev-harness-docs/assets/capabilities.template.md", names
                )
                zf.extractall(extracted)

            result = subprocess.run(
                [
                    sys.executable,
                    str(extracted / "install.py"),
                    "--target",
                    str(install_root),
                    "--skill",
                    "dev-harness-context",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            installed_profile = install_root / "skills" / "dev-harness-context" / "lib" / "context" / "platform_profiles.py"
            self.assertIn("FastAPI", installed_profile.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
