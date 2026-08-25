from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from context.cli import generate_context_files


ROOT = Path(__file__).resolve().parents[1]


class CommandsContextNaturalChineseTests(unittest.TestCase):
    def test_skills_define_chinese_default_without_translating_internal_contract(self) -> None:
        commands = (ROOT / "commands" / "SKILL.md").read_text(encoding="utf-8")
        context = (ROOT / "context" / "SKILL.md").read_text(encoding="utf-8")

        for content in (commands, context):
            self.assertIn("用户明确要求英文", content)
            self.assertIn("默认使用简体中文", content)
            self.assertIn("沿用其主体语言", content)
            self.assertIn("不做", content)

        for internal_field in ("Purpose", "Command", "WorkingDirectory", "Evidence", "Status"):
            self.assertIn(internal_field, commands)

    def test_context_fallback_generates_natural_chinese_and_keeps_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
            (repo / "main.py").write_text(
                "from fastapi import FastAPI\napp = FastAPI()\n",
                encoding="utf-8",
            )
            (repo / "tests").mkdir()

            generated = generate_context_files(repo)

        self.assertIn("根据仓库证据识别为 FastAPI 项目。", generated["README.md"])
        self.assertIn("FastAPI 服务", generated["ARCHITECTURE.md"])
        self.assertIn("工作目录）：仓库根目录", generated["HARNESS.md"])
        self.assertIn("`python -m pytest -q`", generated["HARNESS.md"])
        self.assertNotIn("Automatically detected", "\n".join(generated.values()))


if __name__ == "__main__":
    unittest.main()
