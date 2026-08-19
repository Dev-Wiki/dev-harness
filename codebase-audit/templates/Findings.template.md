# 代码库审计问题登记表（Finding Registry）

> **职责**：本文件是稳定 Finding Registry。只有通过 identity gate、证明根因与修复边界一致后才更新原 ID；详细任务覆盖见 [任务结果](results/)，总体摘要见 [Report.md](Report.md)，运行状态见 [Dashboard.md](Dashboard.md)。

## 导航

- [审计看板](Dashboard.md)
- [当前报告](Report.md)
- [审计任务](tasks/)
- [任务结果](results/)

## 审计快照（Snapshot）

| 字段 | 值 |
|---|---|
| 审计运行 ID | `{run-id}` |
| 基线 SHA / 分支 | `{sha}` / `{branch}` |
| Context 指纹 | `{fingerprint}` |
| 登记表最近验证位置 | `{checkpoint}` |
| 漂移状态 | `{有效/已失效}` |

## 状态说明

| 内部状态 | 中文显示 | 含义 |
|---|---|---|
| `candidate` | 候选项 | 尚未通过验证门禁 |
| `needs-verification` | 待验证 | 缺少关键链路、反证或运行证据 |
| `confirmed` | 已确认 | 当前 Snapshot 下证据闭合 |
| `rejected` | 已排除 | Evidence 否定 Claim 或已有有效保护 |
| `stale` | 已失效 | Snapshot/Context 漂移，旧 Evidence 不再代表当前事实 |
| `resolved` | 已解决 | 外部修复后已在新 Snapshot 下重新验证 |

## 问题登记表（Finding Registry）

| ID | 严重度（Severity） | 状态 | 摘要 | 来源任务 | 最近验证的 Snapshot |
|---|---|---|---|---|---|
| [AUD-001](#aud-001--summary) | `{P0/P1/P2/P3}` | `{候选项/待验证/已确认/已排除/已失效/已解决}` | `{摘要}` | `{Result 链接}` | `{sha/fingerprint}` |

## 证据（Evidence）

- 每个 Finding 在自己的“问题证据（Finding Evidence）”小节维护 `path:line`、命令/产物、反证和 Result 链接。
- Evidence 必须绑定该 Finding 的 Snapshot；Dashboard 和 Report 只链接，不复制详细证据。
- 无代码或运行 Evidence 的条目不得标 `confirmed`。

## Finding 详情

### AUD-001 — `{摘要}`

- **状态**：`{候选项/待验证/已确认/已排除/已失效/已解决}`
- **严重度（Severity）**：`{P0/P1/P2/P3}`
- **分类**：`{自由分类}`
- **置信度（Confidence）**：`{高/中/低}`
- **来源任务**：`{Task/Result 链接及别名}`

#### 主张（Claim）

`{可证伪机制：触发条件 → 行为 → 错误结果}`

#### 风险 / 影响（Risk / Impact）

`{触发条件、受影响执行路径、可观察影响、影响对象及后果}`

#### 调用链 / 数据流（Call Chain / Data Flow）

`{entry → caller/producer → boundary → callee/consumer → output/side effect}`

#### 已检查的反证（Counter-evidence）

- `{已检查的前置条件、清理路径、替代实现、平台分支、异常路径或测试}`

#### 根因与修复边界判断

- **根因**：`{被 Evidence 支持的直接根因}`
- **职责归属（Owner / responsibility boundary）**：`{职责归属}`
- **修复边界**：`{预期需要改动或验证的行为边界}`
- **同一性结论（Identity decision）**：`{保持独立/与哪些 alias 合并，以及四项条件的证据}`

#### 审计快照（Snapshot）

- **运行 ID / 基线 SHA / 分支**：`{run-id}` / `{sha}` / `{branch}`
- **Context / 审计前工作区指纹**：`{context fingerprint}` / `{dirty fingerprint}`
- **最近验证位置**：`{checkpoint}`

#### 问题证据（Finding Evidence）

- `{path:line — 观察到的行为}`
- `{命令/artifact — 结果与退出状态}`
- `{关联 Task Result 章节}`

#### 建议后续动作（Suggested Next Action）

- **建议交接**：`{dev-harness-auto-fix/dev-harness-planning/dev-harness-docs/dev-harness-commands/dev-harness-git-workflow/人工验证}`
- **验收方向**：`{后续验证必须证明什么}`

---

> “已确认（`confirmed`）”必须有当前 Snapshot、代码或运行 Evidence、反证检查和已完成的跨模块复核。漂移后移入“已失效（`stale`）”，不得继续作为当前事实。
