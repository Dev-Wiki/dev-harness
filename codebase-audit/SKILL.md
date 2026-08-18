---
name: dev-harness-codebase-audit
description: Use when an existing repository needs a systematic, evidence-backed search for unknown codebase problems across modules or sessions, with canonical Context as input, durable audit state, verified findings, drift detection, and mandatory cross-module reconciliation
---

# dev-harness-codebase-audit

对无法一次装入上下文的存量代码库做渐进式审计。让 AI 负责语义理解，让 `runtime.py` 负责快照、状态、漂移和写入边界；不要把本 Skill 变成语言规则库或静态分析器。

## 硬边界

- 把 `dev-harness-context` 维护的 Context 当作唯一 canonical repository input。只读消费 `README.md`、`AGENTS.md`、`ARCHITECTURE.md`、`HARNESS.md` 及其规范索引；不要另建 Repository Context。
- 只允许写入 `<docs-root>/audit/**` 和 Git 私有目录 `.git/dev-harness/codebase-audit/**`（worktree 中使用 Git 返回的实际私有路径）。
- 不得修改业务源码、测试、配置、构建文件、Context 托管区或其他 Skill 的产物。
- 只发现、验证和路由问题；不得自动修复、commit、创建 PR、发布或创建 Roadmap/计划任务。
- 不得用固定语言、框架或“最佳实践”巨型 checklist 代替基于 Context 的动态分区。
- 必须运行 Cross-module Reconciliation；项目小、没有发现问题或所有任务看似独立都不是跳过理由。

## 按需读取

- 开始或恢复运行时，读取 [references/workflow.md](references/workflow.md)。
- 生成审计任务时，读取 [references/partitioning.md](references/partitioning.md)。
- 第一次记录 candidate 或改变 Finding 状态前，读取 [references/finding-contract.md](references/finding-contract.md)。
- 所有任务结束、生成最终报告前，读取 [references/cross-module-review.md](references/cross-module-review.md)。
- 创建产物时使用 `templates/` 中对应模板，不删除其职责、导航、`Snapshot` 或 `Evidence` 章节。

## Preflight

1. 确定仓库根、当前分支、HEAD、Git 私有目录和已有 dirty files。
2. 读取 canonical Context、项目规范索引与 `HARNESS.md`。Context 缺失、证据被截断、与仓库明显不符或无法得到可记录的 Context fingerprint 时，停止并交给 `dev-harness-context` 刷新；不得自行补一套上下文。
3. 解析唯一 `<docs-root>`：尊重用户指定的既有路径；否则复用已有索引、治理文件、活跃 `plan/` 或 `audit/` 所在根；仅有 `doc/` 或 `docs/` 时使用已有者。二者均为项目所有且归属不明，或二者皆不存在时停止并先交给文档治理流程建立 canonical root；Audit 不自行创建第二套文档体系。
4. 校验所有预期输出都位于 `<docs-root>/audit/**`，所有运行状态都位于 Git 私有目录。
5. 用 `runtime.py` 初始化或恢复运行并建立 `AuditSnapshot`。先读取 `python <skill-dir>/runtime.py --help`，再按实际接口使用 `init`、`resume` / `status`、`verify-workspace`、`checkpoint`、`upsert-finding`、`validate-output`、`checkpoint-cross-module` 和 `complete` 等语义操作；不硬编码未确认参数，不手工伪造或绕过状态校验。

`AuditSnapshot` 至少绑定 base SHA、branch、preexisting dirty files 及内容 fingerprint、Context fingerprint、audit scope 和 output paths。

## 核心流程

按顺序执行，详细门禁见 [references/workflow.md](references/workflow.md)：

```text
preflight → snapshot → dynamic partition → task execution
          → finding verification → cross-module reconciliation → report
```

1. 从 Context 的真实 subsystem、runtime/platform boundary、shared core、数据流、持久化、外部集成和构建边界生成任务。文件数量不是分区依据。
2. 按 `repository map → search → entry point → caller/callee → owner/lifecycle/boundary → evidence` 渐进读取；不要为“完整”批量加载无关文件。
3. 把任务和阶段结果持久化到审计文档，把运行 checkpoint 持久化到 Git 私有状态。恢复时先校验快照，再相信旧结果。
4. 可疑点先进入 `candidate`，检查反证、旁路、生命周期和其他实现。证据不足时使用 `needs-verification`，不得提高措辞强度来替代验证。
5. 对所有任务做去重、矛盾处理、完整调用链/数据流审查和跨平台影响检查，之后才能发布当前 `confirmed` 结论。
6. 最终报告只汇总已验证 Findings、未决项和建议路由，不写脱离 Evidence 的长篇最佳实践建议。

## 产物职责

使用同一 `<docs-root>/audit/`：

- `Dashboard.md`：仅维护运行快照、任务状态、计数、当前焦点和阻塞；链接到其他产物，不放 Finding 正文。
- `Findings.md`：稳定 Finding Registry；同一根因复用 ID，记录状态、Snapshot 和 Evidence。
- `tasks/Axx-*.md`：当前轮次要扫描什么，以及范围、边界、排除项、证据策略和依赖。
- `results/Axx-*.md`：对应 Task 的局部覆盖、candidate、反证、证据缺口和跨模块输入。
- `Report.md`：当前快照下的开发者总览，聚合 Findings 和 Cross-module 结论。

各文档必须互相链接。详细证据只维护在 Finding 或 Task Result 的权威位置，其他文档链接过去，不复制正文。历史由 Git 承担；V1 不创建按时间滚动的归档副本。

## Drift 与停止条件

在恢复运行、开始每个 Task、把 Finding 标为 `confirmed`、Cross-module Reconciliation 和生成报告前，运行 workspace drift 校验。

HEAD、分支、preexisting dirty 内容/暂存状态、Context fingerprint 或受审范围发生未纳入快照的变化时：

1. 立即停止产生新的当前事实；
2. 把受影响 Task/Result/Finding 标记为 `STALE` 或 `stale`，并记录 drift evidence；
3. 不得把旧 Evidence 继续表述为当前已确认事实；
4. 建立新快照并重新验证后才能恢复确认。

Context 不可用、docs root 冲突、输出越界、运行状态损坏、Evidence 无法绑定快照或 Cross-module 阶段未完成时同样 fail closed。

## Finding 与交接

Finding 必须遵循 `candidate → verification → confirmed/rejected`，并可在仓库演进后变为 `stale`，修复且重新验证后变为 `resolved`。`confirmed` 至少需要代码或运行证据、相关调用链/数据流、反证检查、风险、置信度和 Snapshot；静态搜索不到引用不等于 dead code。

只建议以下 handoff，不在本运行中自动调用写操作：

| Finding 类型 | 建议交给 |
|---|---|
| 已确认 defect、crash、lifecycle bug | `dev-harness-auto-fix` |
| 架构、重构、技术债工作 | `dev-harness-planning` |
| 文档治理问题 | `dev-harness-docs` |
| 验证命令缺口 | `dev-harness-commands` |
| Git、发布或 changelog 规范缺口 | `dev-harness-git-workflow` |

交接只包含 Finding ID、当前 Snapshot、Evidence、影响、验收方向和建议 owner。授权审计不等于授权任何后续修改。

## 完成口径

仅当所有计划内 Task 有结果或明确 blocker、所有发布的 confirmed Findings 绑定当前 Snapshot、重复和矛盾已收敛、Cross-module Reconciliation 已记录且最终 drift 校验通过时，才把运行标为完成。报告本次只写入哪些审计文档、状态路径、快照、Finding 计数、未决 Evidence gap 和建议 handoff。
