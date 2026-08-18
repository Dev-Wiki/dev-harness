# Audit Result {Axx} — `{Behavior Domain}`

> **职责**：本文件保存 [对应 Task](../tasks/{Axx}-{slug}.md) 的局部覆盖、Evidence、candidate、反证和缺口。它不是最终报告；稳定 Finding 维护在 [Findings.md](../Findings.md)。

## Navigation

- [Dashboard](../Dashboard.md)
- [Audit Task](../tasks/{Axx}-{slug}.md)
- [Finding Registry](../Findings.md)
- [Current Report](../Report.md)

## Snapshot

| Field | Value |
|---|---|
| Audit Run / Task | `{run-id}` / `{Axx}` |
| Base SHA / Branch | `{sha}` / `{branch}` |
| Context Fingerprint | `{fingerprint}` |
| Dirty Fingerprint | `{fingerprint/clean}` |
| Drift Status | `{valid/WorkspaceDrift/STALE}` |
| Result Status | `{running/blocked/stale/completed}` |

## Coverage Executed

- **Entry points followed**: `{symbols/paths}`
- **Call chains / data flows**: `{chains examined}`
- **Boundaries examined**: `{boundary sides}`
- **Excluded or unread scope**: `{scope and reason}`

## Evidence

| Evidence ID | Path / Command / Artifact | Observation | Supports / Contradicts | Snapshot |
|---|---|---|---|---|
| `{E-Axx-01}` | `{path:line or command}` | `{observed behavior}` | `{candidate/claim ID}` | `{sha/fingerprint}` |

## Candidate Outcomes

| Local ID | Status | Claim | Evidence | Counter-evidence | Registry Mapping |
|---|---|---|---|---|---|
| `{Axx-C01}` | `{candidate/needs-verification/confirmed/rejected/stale}` | `{falsifiable claim}` | `{Evidence IDs}` | `{checks/results}` | `{AUD-nnn/pending}` |

> Task-local `confirmed` 表示局部验证门禁已通过；只有完成全局 cross-module reconciliation 后才可作为 Report 中的当前 confirmed Finding。

## Counter-evidence and Alternatives

- `{guard, cleanup, alternate implementation, platform branch, exception path, or test inspected}`

## Evidence Gaps / Blockers

- `{missing caller, unavailable runtime, device, command, permission, or ambiguous Context}`

## Cross-module Inputs

| Boundary / Claim | Related Task | Question to Reconcile | Evidence Link |
|---|---|---|---|
| `{boundary}` | `{Ayy}` | `{duplication/contradiction/end-to-end question}` | `{section/Evidence ID}` |

## Checkpoint

- **Last durable stage**: `{stage}`
- **Next action**: `{next evidence step or reconciliation}`
- **Snapshot validation**: `{command/result summary}`
