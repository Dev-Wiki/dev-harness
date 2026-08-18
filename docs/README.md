# dev-harness 文档中心

本目录是 dev-harness 唯一的项目文档根。根 [`README.md`](../README.md) 提供产品入口；本页按读者任务导航，不复制专题文档的详细事实。

## 使用 dev-harness

1. [客户端项目接入](CLIENT_PROJECT_ONBOARDING.md)：在真实项目中安装、初始化 Context 并确认契约。
2. [HARNESS 使用指南](HARNESS_GUIDE.md)：维护和消费 build / test / quick / bugfix / full 验证接口。
3. [Bugfix 指南](BUGFIX_GUIDE.md)：使用证据驱动的已知问题分析与修复流程。
4. [English README](README_EN.md)：英文项目概览与安装入口。

## 维护与验证

- [测试说明](TESTING.md)：运行测试、理解覆盖范围并检查安装/发布产物。
- [Git 工作流](GIT_WORKFLOW.md)：本仓库的分支、提交、tag、changelog 和发布消息契约。

## 当前范围、设计与未来规划

| 文档 | 唯一职责 | 状态 |
|------|----------|------|
| [V1 / VNext 与 V2 边界](V1_V2_BOUNDARIES.md) | 当前能力、明确非目标、V1 封板标准 | 当前范围 SSOT |
| [VNext 优化与 Codebase Audit 设计方案](dev-harness%20VNext%20%E4%BC%98%E5%8C%96%E4%B8%8E%20Codebase%20Audit%20%E8%AE%BE%E8%AE%A1%E6%96%B9%E6%A1%88.md) | v1.8.0 的设计依据、取舍和实施期约束 | 已实施的设计记录 |
| [V2 Backlog](V2_BACKLOG.md) | 超出当前边界的候选能力与启动条件 | 候选池，不是承诺 Roadmap |

三类文档分别回答“现在承诺什么”“为什么这样设计”“以后可能做什么”。变动状态只在对应 Owner 中维护，其他入口仅链接。

## 文档维护边界

- 根 README 只保留概览和入口，不复制深层设计。
- 当前行为以代码、测试、对应 Skill/reference 和已经验证的命令为准。
- 已完成的实施计划不继续作为活动文档维护；历史由 Git 保存。
- Codebase Audit 在目标项目中拥有 `<docs-root>/audit/` 内容，Docs 只治理导航、链接和归档。
- Planning 在目标项目中拥有 `<docs-root>/plan/` 内容，Docs 不复制任务状态。
