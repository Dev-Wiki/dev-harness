# 代码库审计报告

> **职责**：本文件是当前有效 Snapshot 下的开发者总览，只汇总已验证 Findings、跨模块结论、未决证据和建议交接。权威 Finding 正文见 [Findings.md](Findings.md)，执行状态见 [Dashboard.md](Dashboard.md)。

## 导航

- [审计看板](Dashboard.md)
- [问题登记表（Finding Registry）](Findings.md)
- [审计任务](tasks/)
- [任务结果](results/)

## 文档可发现性

| 字段 | 值 |
|---|---|
| 文档中心 | `{docs-root}/README.md 或既有导航索引` |
| 固定审计入口 | `{docs-root}/audit/Report.md` |
| 状态 | `{已链接（linked）/需刷新文档（docs-refresh-required）}` |
| 负责方 / 动作 | `{dev-harness-docs / 无或增加一个简短入口}` |

> Audit 不修改文档中心。状态为 `docs-refresh-required` 时，本表就是精确的导航交接，不需要创建 `AUD-*` Finding。

## 审计快照（Snapshot）

| 字段 | 值 |
|---|---|
| 审计运行 ID | `{run-id}` |
| 基线 SHA / 分支 | `{sha}` / `{branch}` |
| Context 指纹 | `{fingerprint}` |
| 审计范围 | `{include/exclude summary}` |
| 最近漂移校验 | `{checkpoint/result}` |
| 跨模块复核（Cross-module Reconciliation） | `{已完成/已失效}` |

## 执行摘要

`{当前且有 Evidence 支撑的结论；不要写通用最佳实践长文。}`

- **任务**：`{已完成/受阻/已失效计数}`
- **已确认问题（Findings）**：`{P0/P1/P2/P3 计数}`
- **待验证项**：`{count}`
- **覆盖限制**：`{重要排除项或 Evidence 缺口}`

## 架构与范围摘要

`{基于 Context 简要说明 subsystem、运行时/平台边界、shared core 和 integration，并附链接。}`

## 已确认问题（Findings）

### P0

- [AUD-nnn — `{摘要}`](Findings.md#{finding-anchor}) — `{影响与 Evidence 链接}`

### P1

- `{Finding 链接或无}`

### P2

- `{Finding 链接或无}`

### P3

- `{Finding 链接或无}`

## 跨模块复核结论

- `{Finding 链接}：{端到端链路、受影响模块/平台及复核结论}`
- **已合并别名**：`{本地/全局 ID 或无；附四项同一性条件（identity）的证据}`
- **保持独立的相关 Candidate**：`{ID、未合并理由或无}`
- **已解决矛盾**：`{Claim → Evidence 支撑的结论或无}`
- **边界覆盖缺口**：`{缺口及 Result 链接或无}`

## 待验证项

- [AUD-nnn](Findings.md#{finding-anchor}) — `{缺失的最小复现/行为验证 Evidence，以及它为何阻止确认}`

## 已排除 / 已失效 / 已解决

- `{Finding 链接、状态、原因及相关 Snapshot}`

## 证据（Evidence）

- **Canonical Context**：`{链接及 Context 指纹}`
- **任务覆盖**：`{Task/Result 链接}`
- **Finding Registry**：[Findings.md](Findings.md)
- **跨模块复核**：`{Result/Report 章节链接}`
- **最终工作区校验**：`{命令/结果摘要}`

## 建议后续动作

| Finding / 缺口 | 建议交接 | 验收方向 | 审计动作 |
|---|---|---|---|
| `{AUD-nnn}` | `{dev-harness-auto-fix/planning/docs/commands/git-workflow/人工处理}` | `{后续需要的验证证据}` | `仅建议` |

> 本报告不授权自动修复、计划创建、文档修改、命令改写、commit、PR 或 release。
