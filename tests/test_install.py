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


if __name__ == "__main__":
    unittest.main()
