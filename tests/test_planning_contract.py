import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANNING = ROOT / "planning"


class PlanningLifecycleContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (PLANNING / relative).read_text(encoding="utf-8")

    def test_skill_bounds_the_active_read_path_and_legacy_migration(self) -> None:
        skill = self.read("SKILL.md")

        for path in (
            "<docs-root>/plan/Dashboard.md",
            "<docs-root>/plan/TaskDetails.md",
            "tasks/<Task-ID>.md",
            "archive/<milestone>/README.md",
        ):
            self.assertIn(path, skill)

        self.assertIn("Do not load every completed task body", skill)
        for guardrail in ("1,000 lines", "100 KB", "20 task bodies"):
            self.assertIn(guardrail, skill)
        self.assertIn("A below-threshold legacy monolith may continue linking", skill)
        self.assertIn("move its detail file to `archive/<milestone>/`", skill)
        self.assertIn("at most five recent completed summaries", skill)
        self.assertIn("These rules bound the active read path", skill)

    def test_entry_templates_link_to_task_files_not_monolithic_anchors(self) -> None:
        dashboard = self.read("templates/Dashboard.template.md")
        task_index = self.read("templates/TaskDetails.template.md")

        for template in (dashboard, task_index):
            self.assertIn("tasks/{任务编号}.md", template)
            self.assertIsNone(
                re.search(r"TaskDetails\.md#[^)]+", template),
                template,
            )

        self.assertIn("最多保留五项摘要", dashboard)
        self.assertIn("[{任务编号}]({任务详情路径})", dashboard)
        self.assertIn("不在本文件追加逐次命令输出", task_index)

    def test_task_and_archive_templates_have_distinct_ownership(self) -> None:
        task = self.read("templates/Task.template.md")
        archive = self.read("templates/ArchiveIndex.template.md")

        for section in (
            "## 背景与目标",
            "## 范围",
            "## 实施步骤",
            "## 验收标准",
            "## 验证证据",
        ):
            self.assertIn(section, task)

        self.assertIn("编辑过程由 Git 历史承担", archive)
        self.assertIn("## 已归档任务", archive)
        self.assertNotIn("## 实施步骤", archive)

    def test_generated_planning_text_defaults_to_natural_chinese(self) -> None:
        skill = self.read("SKILL.md")
        task = self.read("templates/Task.template.md")
        task_index = self.read("templates/TaskDetails.template.md")
        archive = self.read("templates/ArchiveIndex.template.md")

        for rule in (
            "未指定语言的新建文档默认使用简体中文",
            "跟随文档的主体语言",
            "中国人习惯的自然中文",
            "文件路径、命令、代码符号、API、协议名、产品名、必要缩写",
        ):
            self.assertIn(rule, skill)

        self.assertTrue(task.startswith("# 任务 {任务编号}：{任务名称}"))
        self.assertIn("- 新建：`{路径}`", task)
        self.assertIn("| 任务编号 |", task_index)
        self.assertIn("负责人 / 解除条件", task_index)
        self.assertIn("| 任务编号 |", archive)

    def test_legacy_migration_contract_is_lossless_and_link_aware(self) -> None:
        migration = self.read("references/legacy-migration.md")

        for ledger_field in (
            "任务编号（Task ID）",
            "源区间",
            "原始状态",
            "完成证据",
            "里程碑",
            "完成日期",
            "出站链接",
            "入站链接",
        ):
            self.assertIn(ledger_field, migration)

        self.assertIn("archive/legacy-import-YYYY-MM-DD/", migration)
        self.assertIn("下一个同级或更高级标题", migration)
        self.assertIn("非任务区间也分别占一行", migration)
        self.assertIn("重新计算迁移正文中的每条相对链接", migration)
        self.assertIn("必须且只能处理一次", migration)
        self.assertIn("临时暂存目录", migration)
        self.assertIn("只从快照恢复移动映射涉及的路径", migration)
        self.assertIn("源任务数量等于活跃任务文件数", migration)
        self.assertIn("不得修改正式计划", migration)


if __name__ == "__main__":
    unittest.main()
