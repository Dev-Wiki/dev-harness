# dev-harness 文档中心

[简体中文](README.md) | [English](README.en.md)

本目录是 dev-harness 唯一的项目文档根。根 [`README.md`](../README.md) 提供产品入口；本页按读者任务导航，不复制专题文档的详细事实。

用户指南、功能清单、版本边界、进阶使用参考和贡献者说明均提供对应英文正文。历史设计记录与 Agent 内部执行契约保留原文，并在英文导航中标明语言。

## 使用 dev-harness

1. [端到端工作流](WORKFLOW.md)：从共享 Project Contract 进入新功能交付或代码库审计 / 修复闭环。
2. [客户端项目接入](CLIENT_PROJECT_ONBOARDING.md)：在真实项目中安装、初始化 Context 并确认契约。
3. [HARNESS 使用指南](HARNESS_GUIDE.md)：维护和使用 build / test / quick / bugfix / full 验证接口。
4. [Bugfix 指南](BUGFIX_GUIDE.md)：使用证据驱动的已知问题分析与修复流程。
5. [English README](../README.en.md) 与 [English documentation index](README.en.md)：英文概览、快速开始及标注翻译状态的指南导航。
6. [Runtime 协作边界](WORKFLOW.md#6-runtime-协作边界)：准备工程契约后，交给 [dev-harness-runtime](https://github.com/Dev-Wiki/dev-harness-runtime) 自动执行 Planning Task。
7. [Audit 批量接口](../codebase-audit/references/runtime-interface.md)：结构化证据输入、紧凑文档生成与完成门禁。

## 维护与验证

- [测试说明](TESTING.md)与[仓库验证契约](../HARNESS.md)：运行测试、理解覆盖范围并检查安装/发布产物。
- [Git 工作流](GIT_WORKFLOW.md)：本仓库的分支、提交、tag、changelog 和发布消息契约。
- [功能清单维护](../dev-harness-docs/references/capability-maintenance.md)：首次全量盘点、日常增量同步和可重复的全量复核。
- [变更日志](../CHANGELOG.md)：已发布版本的变化。

## 当前范围、设计与未来规划

| 文档 | 唯一职责 | 状态 |
|------|----------|------|
| [产品功能清单](CAPABILITIES.md) | 按使用场景查看功能、支持程度、限制和入口；技术证据按需展开 | 当前功能权威文档 |
| [V1 / VNext 与 V2 边界](V1_V2_BOUNDARIES.md) | 版本边界、明确非目标、V1 封板标准 | 版本边界权威文档 |
| [VNext 优化与 Codebase Audit 设计方案](dev-harness%20VNext%20%E4%BC%98%E5%8C%96%E4%B8%8E%20Codebase%20Audit%20%E8%AE%BE%E8%AE%A1%E6%96%B9%E6%A1%88.md) | v1.8.0 的设计依据、取舍和实施期约束 | 已实施的设计记录 |
| [V2 Backlog](V2_BACKLOG.md) | 超出当前边界的候选功能与启动条件 | 候选池，不代表已承诺的路线图 |

四类文档分别回答“现在支持什么”“当前版本边界是什么”“为什么这样设计”“以后可能做什么”。变动状态只在相应文档中维护，其他入口仅提供链接。

## 进阶使用与配置

- [Runtime 自动执行交接](../planning/references/runtime-handoff.md)与[旧计划迁移](../planning/references/legacy-migration.md)：准备执行声明、迁移已有计划和归档。
- [功能清单维护](../dev-harness-docs/references/capability-maintenance.md)与[文档信息架构](../dev-harness-docs/references/information-architecture.md)：维护当前能力、文档归属与导航。
- [审计运行流程](../codebase-audit/references/workflow.md)、[问题登记契约](../codebase-audit/references/finding-contract.md)与[批量接口](../codebase-audit/references/runtime-interface.md)：执行审计、理解问题状态并保存证据。
- [平台命令映射](../commands/references/platform-command-mapping.md)与[Windows 终端说明](../commands/references/windows-shell.md)：确认不同平台的验证入口和执行环境。
- [默认 Git 契约](../git-workflow/references/default-contract.md)：理解可供项目确认的默认约定。

## 文档维护边界

- 根 README 只保留概览和入口，不复制深层设计。
- 中英文 README 按章节保持信息对应，工作流、示例、命令、版本说明与文档入口不能因语言版本删减；修改任一版本时同步核对另一版本。
- 用户文档沿用同目录 `文件名.en.md`，保留完整章节、示例、表格、限制与证据引用；英文阅读路径优先链接对应英文正文。中文来源与英文译文在同一变更中核对更新，不维护两套独立事实。
- 机器识别的标题、状态、字段、命令与路径按实际协议保留；英文说明解释原值，不能仅为翻译修改可执行示例的结构。
- 安装、Skill 范围或 Runtime 协作入口变化时，同步更新受影响的英文概览与导航；尚未翻译的指南明确标注语言。旧英文入口 `README_EN.md` 仅保留跳转。
- 当前行为以代码、测试、对应 Skill/reference 和已经验证的命令为准。
- 已完成的实施计划不继续作为活动文档维护；历史由 Git 保存。
- Codebase Audit 负责维护目标项目中的 `<docs-root>/audit/` 内容，Docs 只管理导航、链接和归档。
- Planning 负责维护目标项目中的 `<docs-root>/plan/` 内容及任务生命周期归档，Docs 只治理其放置、导航和链接，不复制或改写任务状态。
