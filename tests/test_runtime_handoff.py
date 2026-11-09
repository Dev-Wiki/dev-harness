import codecs
import json
import re
import tempfile
import unittest
from pathlib import Path

from context.cli import generate_context_files, main


ROOT = Path(__file__).resolve().parents[1]


class RuntimeHandoffTests(unittest.TestCase):
    def test_new_harness_uses_table_without_confirming_detected_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            (repo / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
            (repo / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n", encoding="utf-8")
            (repo / "tests").mkdir()
            harness = generate_context_files(repo)["HARNESS.md"]

        confirmed = harness.split("## 已确认命令（人工维护）\n", 1)[1].split("\n## ", 1)[0]
        rows = [line.split("|")[1:-1] for line in confirmed.splitlines() if line.startswith("|")]
        self.assertGreaterEqual(len(rows), 7)
        self.assertEqual([value.strip() for value in rows[0]], ["用途", "命令", "状态"])
        commands = [[value.strip() for value in row] for row in rows[2:]]
        self.assertEqual([row[0] for row in commands], ["build", "test", "quick", "bugfix", "full"])
        self.assertTrue(all(row[1:] == ["`Unknown`", "missing"] for row in commands))
        self.assertIn("`python -m pytest -q`", harness.split("## 已确认命令", 1)[0])

    def test_refresh_preserves_legacy_manual_section_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            (repo / "package.json").write_text('{"name":"fixture"}', encoding="utf-8")
            self.assertEqual(main(["scan", str(repo)]), 0)
            path = repo / "HARNESS.md"
            original = path.read_text(encoding="utf-8")
            prefix, manual = original.split("## 已确认命令（人工维护）\n", 1)
            _, suffix = manual.split("\n## 高风险目录", 1)
            legacy = "\n- **test**: `team-test`\n\n团队说明：必须保留。\n"
            path.write_bytes(codecs.BOM_UTF8 + (prefix + "## 已确认命令（人工维护）\n" + legacy
                                              + "\n## 高风险目录" + suffix).replace("\n", "\r\n").encode("utf-8"))
            path.chmod(0o640)
            (repo / "CMakeLists.txt").write_text("project(Fixture)\n", encoding="utf-8")

            self.assertEqual(main(["refresh", str(repo), "--force"]), 0)

            after = path.read_bytes()
            self.assertTrue(after.startswith(codecs.BOM_UTF8))
            self.assertIn(legacy.replace("\n", "\r\n").encode("utf-8"), after)
            self.assertNotIn(b"\n", after.replace(b"\r\n", b""))
            self.assertEqual(path.stat().st_mode & 0o777, 0o640)

    def test_opt_in_runtime_example_binds_scope_commands_and_criteria(self) -> None:
        reference = (ROOT / "planning/references/runtime-handoff.md").read_text(encoding="utf-8")
        task = reference.split("### docs/plan/tasks/A.md\n", 1)[1].split("\n````\n", 1)[0]
        config = json.loads(re.search(r"```dhr-runtime\n(.*?)\n```", task, re.DOTALL).group(1))
        impacts = task.split("## 影响文件\n", 1)[1].split("\n## ", 1)[0]
        self.assertEqual(config["schemaVersion"], 1)
        self.assertEqual(config["scope"]["files"], re.findall(r"`([^`]+)`", impacts))
        self.assertEqual(config["scope"]["directories"], [])
        self.assertEqual(config["scope"]["archivePath"], "docs/plan/archive/M1/A.md")
        acceptance = task.split("## 验收标准\n", 1)[1].split("\n## ", 1)[0]
        count = len(re.findall(r"^- \[ \] ", acceptance, re.MULTILINE))
        covered = {number for command in config["verification"]["commands"] for number in command["criteria"]}
        self.assertEqual(covered, set(range(1, count + 1)))
        self.assertEqual(config["verification"]["sources"], ["scripts/check.mjs"])
        self.assertEqual(config["verification"]["manual"], [])
        self.assertIn("`node scripts/check.mjs`", task)
        self.assertIn("| test | `node scripts/check.mjs` | confirmed |", reference)
        self.assertIn("### scripts/check.mjs\n", reference)

    def test_runtime_handoff_is_conditional_and_discoverable(self) -> None:
        skill = (ROOT / "planning/SKILL.md").read_text(encoding="utf-8")
        template = (ROOT / "planning/templates/Task.template.md").read_text(encoding="utf-8")
        self.assertIn("references/runtime-handoff.md", skill)
        self.assertIn("Runtime", template)
        self.assertNotIn("```dhr-runtime", template)


if __name__ == "__main__":
    unittest.main()
