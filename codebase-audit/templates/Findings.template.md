# Codebase Audit Findings

> **职责**：本文件是稳定 Finding Registry。同一根因更新原 ID；详细任务覆盖见 [Task Results](results/)，总体摘要见 [Report.md](Report.md)，运行状态见 [Dashboard.md](Dashboard.md)。

## Navigation

- [Dashboard](Dashboard.md)
- [Current Report](Report.md)
- [Audit Tasks](tasks/)
- [Task Results](results/)

## Snapshot

| Field | Value |
|---|---|
| Audit Run | `{run-id}` |
| Base SHA / Branch | `{sha}` / `{branch}` |
| Context Fingerprint | `{fingerprint}` |
| Registry Last Verified | `{checkpoint}` |
| Drift Status | `{valid/STALE}` |

## Registry

| ID | Severity | Status | Summary | Source Tasks | Last Verified Snapshot |
|---|---|---|---|---|---|
| [AUD-001](#aud-001--summary) | `{P0/P1/P2/P3}` | `{candidate/needs-verification/confirmed/rejected/stale/resolved}` | `{summary}` | `{result links}` | `{sha/fingerprint}` |

## Evidence

- 每个 Finding 在自己的 `Finding Evidence` 小节维护 `path:line`、命令/artifact、反证和 Result 链接。
- Evidence 必须绑定该 Finding 的 Snapshot；Dashboard 和 Report 只链接，不复制详细证据。
- 无代码或运行 Evidence 的条目不得标 `confirmed`。

## Findings

### AUD-001 — `{Summary}`

- **Status**: `{candidate/needs-verification/confirmed/rejected/stale/resolved}`
- **Severity**: `{P0/P1/P2/P3}`
- **Category**: `{free category}`
- **Confidence**: `{high/medium/low}`
- **Source Tasks**: `{task/result links and aliases}`

#### Claim

`{Falsifiable mechanism: condition → behavior → failure}`

#### Risk / Impact

`{Reachability, affected users/platforms/data, and consequence}`

#### Call Chain / Data Flow

`{entry → caller/producer → boundary → callee/consumer → sink}`

#### Counter-evidence Checked

- `{guard, cleanup path, alternate implementation, platform branch, exception path, or test checked}`

#### Snapshot

- **Run / Base SHA / Branch**: `{run-id}` / `{sha}` / `{branch}`
- **Context / Dirty Fingerprint**: `{context fingerprint}` / `{dirty fingerprint}`
- **Last verified**: `{checkpoint}`

#### Finding Evidence

- `{path:line — behavior observed}`
- `{command/artifact — result and exit status}`
- `{linked Task Result section}`

#### Suggested Next Action

- **Handoff**: `{dev-harness-auto-fix/dev-harness-planning/dev-harness-docs/dev-harness-commands/dev-harness-git-workflow/manual verification}`
- **Acceptance direction**: `{what future verification must prove}`

---

> `confirmed` 必须有当前 Snapshot、代码或运行 Evidence、反证检查和完成的 cross-module reconciliation。漂移后移入 `stale`，不得继续作为当前事实。
