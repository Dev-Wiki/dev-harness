import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from install import install_bundle_to_root


class InstallBundleTests(unittest.TestCase):
    def test_installed_context_templates_are_skill_local(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_root = root / "bundle"

            install_bundle_to_root(bundle_root, ["dev-harness-context"])
            skill_root = bundle_root / "skills" / "dev-harness-context"

            self.assertTrue((skill_root / "templates" / "README.template.md").exists())
            self.assertTrue((skill_root / "templates" / "AGENTS.template.md").exists())
            self.assertFalse((skill_root / "templates" / "context").exists())

    def test_installed_planning_skill_includes_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_root = root / "bundle"

            install_bundle_to_root(bundle_root, ["dev-harness-planning"])
            skill_root = bundle_root / "skills" / "dev-harness-planning"

            self.assertTrue((skill_root / "SKILL.md").exists())
            self.assertTrue((skill_root / "templates" / "Dashboard.template.md").exists())
            self.assertTrue((skill_root / "templates" / "TaskDetails.template.md").exists())

    def test_installed_git_workflow_includes_default_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_root = root / "bundle"

            install_bundle_to_root(bundle_root, ["dev-harness-git-workflow"])
            skill_root = bundle_root / "skills" / "dev-harness-git-workflow"

            self.assertTrue((skill_root / "templates" / "GIT_WORKFLOW.template.md").exists())
            self.assertTrue((skill_root / "templates" / "CHANGELOG.template.md").exists())

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


if __name__ == "__main__":
    unittest.main()
