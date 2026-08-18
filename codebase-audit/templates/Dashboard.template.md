# Codebase Audit Dashboard

> **职责**：本文件只维护当前 Audit 的快照、任务状态、Finding 计数、当前焦点和阻塞。问题正文维护在 [Findings.md](Findings.md)，总体结论维护在 [Report.md](Report.md)。

## Navigation

- [Finding Registry](Findings.md)
- [Current Report](Report.md)
- [Audit Tasks](tasks/)
- [Task Results](results/)

## Snapshot

| Field | Value |
|---|---|
| Audit Run | `{run-id}` |
| Status | `{initialized/running/blocked/stale/completed}` |
| Base SHA | `{sha}` |
| Branch | `{branch}` |
| Preexisting Dirty Fingerprint | `{fingerprint/clean}` |
| Context Fingerprint | `{fingerprint}` |
| Audit Scope | `{include/exclude summary}` |
| Output Root | `{docs-root}/audit` |
| Private State | `{git-private-state-path}` |

## Task Status

| Task | Scope | Status | Result | Dependencies | Last Checkpoint |
|---|---|---|---|---|---|
| [A01 — `{scope}`](tasks/A01-{slug}.md) | `{behavior domain}` | `{pending/running/blocked/stale/completed}` | [Result](results/A01-{slug}.md) | `{task IDs/none}` | `{snapshot/checkpoint}` |

## Finding Counts

| P0 | P1 | P2 | P3 | Needs Verification | Rejected | Stale | Resolved |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `{0}` | `{0}` | `{0}` | `{0}` | `{0}` | `{0}` | `{0}` | `{0}` |

## Current Focus

- **Task**: `{task link/none}`
- **Question**: `{current audit question}`
- **Next checkpoint**: `{next durable step}`

## Blockers

- `{blocker or none; link to task/result evidence}`

## Last Verified Snapshot

- **Verified at**: `{timestamp/checkpoint}`
- **Drift status**: `{valid/WorkspaceDrift/STALE}`
- **Cross-module reconciliation**: `{pending/completed/stale}`

## Evidence

- Canonical Context: `{README/AGENTS/ARCHITECTURE/HARNESS links}`
- Snapshot record: `{private state reference; do not copy private state into docs}`
- Last drift validation: `{command/result summary}`

> 任务范围和局部证据只写入对应 [Task](tasks/) / [Result](results/)；不要在本文件复制 Finding 详情。
