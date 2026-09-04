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
            "tasks/<Task-ID>.md",
            "archive/<milestone>/README.md",
        ):
            self.assertIn(path, skill)

        self.assertIn("Do not load every completed task body", skill)
        for guardrail in ("1,000 lines", "100 KB", "20 task bodies"):
            self.assertIn(guardrail, skill)
        self.assertIn("Do not preserve a second mutable active index", skill)
        self.assertIn("move its detail file to `archive/<milestone>/`", skill)
        self.assertIn("at most five recent completed summaries", skill)
        self.assertIn("These rules bound the active read path", skill)

    def test_dashboard_is_the_only_active_entry(self) -> None:
        dashboard = self.read("templates/Dashboard.template.md")
        compatibility_redirect = self.read("templates/TaskDetails.template.md")

        self.assertIn("唯一活跃计划入口", dashboard)
        self.assertIn("tasks/{任务编号}.md", dashboard)
        self.assertIsNone(re.search(r"TaskDetails\.md#[^)]+", dashboard), dashboard)
        self.assertIn("当前工作顺序", dashboard)
        self.assertIn("共享验证基线", dashboard)
        self.assertIn("依赖", dashboard)
        self.assertIn("下一步 / 阻塞", dashboard)

        self.assertIn("最多保留五项摘要", dashboard)
        self.assertIn("[{任务编号}]({任务详情路径})", dashboard)
        self.assertIn("不在本文件追加逐次命令输出", dashboard)

        self.assertIn("[Dashboard.md](Dashboard.md)", compatibility_redirect)
        for duplicated_content in ("tasks/{任务编号}.md", "📋 规划中", "## 共享验证基线", "## 当前工作顺序"):
            self.assertNotIn(duplicated_content, compatibility_redirect)

    def test_task_and_archive_templates_have_distinct_ownership(self) -> None:
        task = self.read("templates/Task.template.md")
        archive = self.read("templates/ArchiveIndex.template.md")

        for section in (
            "## 背景与目标",
            "## 执行上下文",
            "## 范围",
            "## 建议实施顺序",
            "## 验收标准",
            "## 验证证据",
            "## 已确认决策",
            "## 未知项与停止条件",
        ):
            self.assertIn(section, task)

        for field in ("权威需求", "代码入口", "相关测试", "必须保持的不变量"):
            self.assertIn(field, task)

        self.assertIn("编辑过程由 Git 历史承担", archive)
        self.assertIn("## 已归档任务", archive)
        self.assertNotIn("## 建议实施顺序", archive)

    def test_planning_produces_ready_packets_without_owning_execution(self) -> None:
        skill = self.read("SKILL.md")
        dashboard = self.read("templates/Dashboard.template.md")
        task = self.read("templates/Task.template.md")

        self.assertIn("🟢 待执行", skill)
        self.assertIn("execution packet is incomplete", skill)
        self.assertIn("complete enough for a fresh conversation", skill)
        self.assertIn("工作顺序是计划维护的权威顺序", dashboard)

        combined = "\n".join((skill, dashboard, task)).lower()
        self.assertIsNone(re.search(r"\b(?:gpt-[\w.-]+|sol|terra)\b", combined), combined)
        for execution_rule in ("selected_task", "automatic pickup", "atomic claim"):
            self.assertNotIn(execution_rule, combined)

    def test_generated_planning_text_defaults_to_natural_chinese(self) -> None:
        skill = self.read("SKILL.md")
        task = self.read("templates/Task.template.md")
        compatibility_redirect = self.read("templates/TaskDetails.template.md")
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
        self.assertIn("唯一权威来源", task)
        self.assertIn("活跃任务入口已合并", compatibility_redirect)
        self.assertIn("| 任务编号 |", archive)

    def test_mutable_state_has_one_authority_and_drift_gate(self) -> None:
        skill = self.read("SKILL.md")
        dashboard = self.read("templates/Dashboard.template.md")
        task = self.read("templates/Task.template.md")

        for field in ("status", "priority", "dependency", "work order", "blocker"):
            self.assertIn(field, skill)
        for command in ("git rev-parse HEAD", "sha256sum", "git status --short"):
            self.assertIn(command, skill)
        self.assertIn("Planning Snapshot and Drift Gate", skill)
        self.assertIn("Do not generate `TaskDetails.md`", skill)
        self.assertIn("唯一活跃计划入口", dashboard)
        self.assertIn("🟢 待执行", dashboard)

        for mutable_label in ("**优先级**", "**状态**", "**依赖**", "**阻塞**"):
            self.assertNotIn(mutable_label, task)
        self.assertIn("以 [Dashboard.md](../Dashboard.md) 为唯一权威来源", task)

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
        self.assertIn("Dashboard 是唯一活跃计划入口", migration)
        self.assertIn("只包含指向 Dashboard 的兼容跳转", migration)
        self.assertIn("临时规划快照", migration)


if __name__ == "__main__":
    unittest.main()
