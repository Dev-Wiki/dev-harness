import json
import shutil
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
import install


class InstallBundleTests(unittest.TestCase):
    def test_failed_export_preserves_previous_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "out"
            previous = out_dir / "bundle" / "skills" / "previous" / "SKILL.md"
            previous.parent.mkdir(parents=True)
            previous.write_text("previous working artifact\n", encoding="utf-8")

            with patch.dict(
                install.SKILL_SOURCES,
                {"dev-harness-commands": root / "missing" / "SKILL.md"},
            ):
                with self.assertRaises(FileNotFoundError):
                    install.export_bundle(out_dir)

            self.assertEqual(
                previous.read_text(encoding="utf-8"), "previous working artifact\n"
            )

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
            compatibility_redirect = (
                skill_root / "templates" / "TaskDetails.template.md"
            ).read_text(encoding="utf-8")
            self.assertIn("[Dashboard.md](Dashboard.md)", compatibility_redirect)
            self.assertNotIn("tasks/{任务编号}.md", compatibility_redirect)

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

    def test_release_archive_contains_ready_to_use_skills_without_source_tree(self) -> None:
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
                self.assertEqual(
                    {name.split("/")[0] for name in names},
                    {"skills", "README.md", "VERSION", "CHANGELOG.md"},
                )
                exported_skills = {
                    path.relative_to(dist_dir / "bundle").as_posix(): path
                    for path in (dist_dir / "bundle" / "skills").rglob("*")
                    if path.is_file()
                }
                self.assertEqual(
                    {name for name in names if name.startswith("skills/")},
                    set(exported_skills),
                )
                for name, path in exported_skills.items():
                    self.assertEqual(zf.read(name), path.read_bytes(), name)
                self.assertIn("skills/dev-harness-codebase-audit/runtime.py", names)
                self.assertIn("skills/dev-harness-codebase-audit/render.py", names)
                self.assertIn("skills/dev-harness-auto-fix/runtime.py", names)
                self.assertIn(
                    "skills/dev-harness-planning/templates/Task.template.md", names
                )
                self.assertIn(
                    "skills/dev-harness-planning/references/legacy-migration.md", names
                )
                self.assertIn(
                    "skills/dev-harness-docs/assets/capabilities.template.md", names
                )
                version = zf.read("VERSION").decode().strip()
                self.assertIn(version, zf.read("README.md").decode())
                for skill in SKILL_SOURCES:
                    self.assertIn(
                        f"bundle_version: {version}",
                        zf.read(f"skills/{skill}/SKILL.md").decode(),
                    )
                zf.extractall(extracted)

            # Install by copying the delivered skills; run from an unrelated directory
            # in isolated Python mode so the checkout cannot supply missing modules.
            shutil.copytree(extracted / "skills", install_root / "skills")
            repo_root = root / "demo-repo"
            repo_root.mkdir()
            (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")
            launcher = install_root / "skills" / "dev-harness-context" / "dev-harness-context"
            result = subprocess.run(
                [sys.executable, "-I", str(launcher), "scan", str(repo_root)],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((repo_root / "HARNESS.md").exists())
            for skill in ("dev-harness-auto-fix", "dev-harness-codebase-audit"):
                with self.subTest(skill=skill):
                    runtime = install_root / "skills" / skill / "runtime.py"
                    result = subprocess.run(
                        [sys.executable, "-I", str(runtime), "--help"],
                        cwd=root,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
