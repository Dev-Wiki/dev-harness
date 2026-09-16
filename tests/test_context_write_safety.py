import codecs
import io
import stat
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from context.cli import main


class ContextWriteSafetyTests(unittest.TestCase):
    def run_cli(self, *args: str) -> int:
        with redirect_stdout(io.StringIO()):
            return main(list(args))

    def seed_refresh(self, repo: Path) -> Path:
        self.assertEqual(self.run_cli("scan", str(repo)), 0)
        readme = repo / "README.md"
        readme.write_text(readme.read_text() + "\n## Team notes\noriginal\n", encoding="utf-8")
        (repo / "main.py").write_text("print('hello')\n", encoding="utf-8")
        return readme

    def test_scan_and_refresh_reject_symlink_outputs_before_writing(self) -> None:
        for command in ("scan", "refresh"):
            for dangling in (False, True):
                for external in (False, True):
                    with self.subTest(command=command, dangling=dangling, external=external):
                        with tempfile.TemporaryDirectory() as tmp:
                            root = Path(tmp)
                            repo = root / "repo"
                            repo.mkdir()
                            self.assertEqual(self.run_cli("scan", str(repo)), 0)
                            content = (repo / "HARNESS.md").read_bytes()
                            for name in ("README.md", "AGENTS.md", "ARCHITECTURE.md", "HARNESS.md"):
                                (repo / name).unlink()
                            target = (root if external else repo) / "target.md"
                            if not dangling:
                                target.write_bytes(content)
                            link = repo / "HARNESS.md"
                            link.symlink_to(target)

                            result = self.run_cli(command, str(repo), "--force")

                            self.assertEqual(result, 1)
                            self.assertTrue(link.is_symlink())
                            self.assertEqual(target.exists(), not dangling)
                            if not dangling:
                                self.assertEqual(target.read_bytes(), content)
                            self.assertFalse((repo / "README.md").exists())

    def test_refresh_preserves_edits_made_during_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = self.seed_refresh(repo)
            expected = readme.read_text().replace("original", "edited during preview")

            def approve(name: str) -> str:
                self.assertEqual(name, "README.md")
                readme.write_text(expected, encoding="utf-8")
                return "yes"

            with patch("context.cli.sys.stdin.isatty", return_value=True), patch(
                "context.cli.prompt_overwrite_action", side_effect=approve
            ):
                result = self.run_cli("refresh", str(repo))

            self.assertEqual(result, 1)
            self.assertEqual(readme.read_text(), expected)

    def test_refresh_rejects_replacement_with_identical_bytes_or_changed_mode(self) -> None:
        for change in ("replace", "chmod"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                readme = self.seed_refresh(repo)
                before = readme.read_bytes()
                readme.chmod(0o640)

                def approve(name: str) -> str:
                    if change == "replace":
                        replacement = repo / "replacement.md"
                        replacement.write_bytes(before)
                        replacement.chmod(0o640)
                        replacement.replace(readme)
                    else:
                        readme.chmod(0o600)
                    return "yes"

                with patch("context.cli.sys.stdin.isatty", return_value=True), patch(
                    "context.cli.prompt_overwrite_action", side_effect=approve
                ):
                    result = self.run_cli("refresh", str(repo))

                self.assertEqual(result, 1)
                self.assertEqual(readme.read_bytes(), before)
                self.assertEqual(stat.S_IMODE(readme.stat().st_mode), 0o640 if change == "replace" else 0o600)

    def test_refresh_rejects_symlink_inserted_during_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            readme = self.seed_refresh(repo)
            outside = root / "outside.md"
            outside.write_bytes(readme.read_bytes())
            before = outside.read_bytes()

            def approve(name: str) -> str:
                readme.unlink()
                readme.symlink_to(outside)
                return "yes"

            with patch("context.cli.sys.stdin.isatty", return_value=True), patch(
                "context.cli.prompt_overwrite_action", side_effect=approve
            ):
                result = self.run_cli("refresh", str(repo))

            self.assertEqual(result, 1)
            self.assertTrue(readme.is_symlink())
            self.assertEqual(outside.read_bytes(), before)

    def test_refresh_missing_file_creation_does_not_clobber_new_file_or_symlink(self) -> None:
        for symlink in (False, True):
            with self.subTest(symlink=symlink), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo = root / "repo"
                repo.mkdir()
                target = repo / "HARNESS.md"
                outside = root / "outside.md"

                class ConcurrentCreation(io.StringIO):
                    def write(self, text: str) -> int:
                        if text == "已创建：README.md":
                            if symlink:
                                target.symlink_to(outside)
                            else:
                                target.write_bytes(b"concurrent user file\n")
                        return super().write(text)

                with redirect_stdout(ConcurrentCreation()):
                    result = main(["refresh", str(repo), "--force"])

                self.assertEqual(result, 1)
                self.assertFalse(outside.exists())
                if symlink:
                    self.assertTrue(target.is_symlink())
                else:
                    self.assertEqual(target.read_bytes(), b"concurrent user file\n")

    def test_refresh_checks_again_after_preparing_temporary_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = self.seed_refresh(repo)
            expected = readme.read_text().replace("original", "edited while preparing write")

            def edit_before_replace(descriptor: int) -> None:
                readme.write_text(expected, encoding="utf-8")

            with patch("context.managed.os.fsync", side_effect=edit_before_replace):
                result = self.run_cli("refresh", str(repo), "--force")

            self.assertEqual(result, 1)
            self.assertEqual(readme.read_text(), expected)
            self.assertEqual(list(repo.glob(".README.md.*")), [])

    def test_refresh_write_error_leaves_original_and_cleans_temporary_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = self.seed_refresh(repo)
            before = readme.read_bytes()

            with patch("context.managed.os.fsync", side_effect=OSError("write failed")):
                result = self.run_cli("refresh", str(repo), "--force")

            self.assertEqual(result, 1)
            self.assertEqual(readme.read_bytes(), before)
            self.assertEqual(list(repo.glob(".README.md.*")), [])

    def test_refresh_preserves_utf16_bom_crlf_final_newline_and_mode(self) -> None:
        for encoding, bom in (("utf-16-le", codecs.BOM_UTF16_LE), ("utf-16-be", codecs.BOM_UTF16_BE)):
            with self.subTest(encoding=encoding), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                readme = self.seed_refresh(repo)
                text = readme.read_text().rstrip("\n")
                readme.write_bytes(bom + text.replace("\n", "\r\n").encode(encoding))
                readme.chmod(0o640)

                self.assertEqual(self.run_cli("refresh", str(repo), "--force"), 0)

                raw = readme.read_bytes()
                self.assertTrue(raw.startswith(bom))
                decoded = raw[len(bom) :].decode(encoding)
                self.assertIn("Python", decoded)
                self.assertIn("## Team notes\r\noriginal", decoded)
                self.assertNotIn("\n", decoded.replace("\r\n", ""))
                self.assertFalse(decoded.endswith("\r\n"))
                self.assertEqual(stat.S_IMODE(readme.stat().st_mode), 0o640)


if __name__ == "__main__":
    unittest.main()
