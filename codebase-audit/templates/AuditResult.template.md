# 审计结果 {Axx} — `{行为域}`

> **职责**：本文件记录 [对应任务](../tasks/{Axx}-{slug}.md) 的检查范围、证据（Evidence）、候选项（Candidate）、反证和缺口。它不是最终报告；稳定 Finding 维护在 [Findings.md](../Findings.md)。

## 导航

- [审计看板](../Dashboard.md)
- [审计任务](../tasks/{Axx}-{slug}.md)
- [问题登记表（Finding Registry）](../Findings.md)
- [当前报告](../Report.md)

## 审计快照（Snapshot）

| 字段 | 值 |
|---|---|
| 审计运行 ID / 任务 | `{run-id}` / `{Axx}` |
| 基线 SHA / 分支 | `{sha}` / `{branch}` |
| Context 指纹 | `{fingerprint}` |
| 审计前工作区指纹 | `{fingerprint/clean}` |
| 漂移状态 | `{有效/检测到 WorkspaceDrift/已失效}` |
| 结果状态 | `{进行中/受阻/已失效/已完成}` |

## 实际覆盖

- **已追踪入口**：`{symbols/paths}`
- **调用链 / 数据流**：`{已检查链路}`
- **已检查边界**：`{边界两侧}`
- **排除或未读取范围**：`{范围及原因}`

## 证据（Evidence）

| 证据 ID | 路径 / 命令 / 产物 | 观察结果 | 支持 / 反驳 | Snapshot |
|---|---|---|---|---|
| `{E-Axx-01}` | `{path:line 或命令}` | `{观察到的行为}` | `{candidate/claim ID}` | `{sha/fingerprint}` |

## 候选项（Candidate）验证结果

| 本地 ID | 状态 | 主张（Claim） | 证据（Evidence） | 反证（Counter-evidence） | 同一性 / 修复边界判断（Identity） | 登记表映射 |
|---|---|---|---|---|---|---|
| `{Axx-C01}` | `{候选项/待验证/已确认/已排除/已失效}` | `{可证伪主张}` | `{Evidence IDs}` | `{检查及结果}` | `{根因、owner、修复边界；保持独立或待复核}` | `{AUD-nnn/待分配}` |

> “任务内已确认（`confirmed`）”只表示本任务范围内的验证要求已满足；只有完成全局跨模块复核（Cross-module Reconciliation）后，才能作为 Report 中当前有效的已确认 Finding。位于同一模块或机制不足以合并 Candidate。

## 反证与替代实现

- `{已检查的前置条件、清理路径、替代实现、平台分支、异常路径或测试}`

## 证据缺口与阻塞项

- `{缺失 caller、不可用运行环境、设备、命令、执行条件或存在歧义的 Context}`

## 跨模块复核输入

| 边界 / 主张（Claim） | 相关任务 | 待复核问题 | Evidence 链接 |
|---|---|---|---|
| `{boundary}` | `{Ayy}` | `{identity/矛盾/端到端问题}` | `{section/Evidence ID}` |

### 复核结论

- **Finding 同一性**：`{合并/保持独立/待验证，以及四项 identity 条件的证据}`
- **矛盾处理**：`{已解决结论/待验证缺口}`
- **严重度 / 置信度变化**：`{变化及原因/无}`

## 检查点

- **最近持久化阶段**：`{stage}`
- **下一动作**：`{下一证据步骤或复核动作}`
- **Snapshot 校验**：`{命令/结果摘要}`
