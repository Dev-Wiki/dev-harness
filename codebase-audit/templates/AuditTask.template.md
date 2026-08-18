# Audit Task {Axx} — `{Behavior Domain}`

> **职责**：本文件定义本轮要扫描什么，不保存最终 Finding 正文。执行证据写入 [对应 Result](../results/{Axx}-{slug}.md)，全局 Finding 写入 [Findings.md](../Findings.md)，运行状态写入 [Dashboard.md](../Dashboard.md)。

## Navigation

- [Dashboard](../Dashboard.md)
- [Finding Registry](../Findings.md)
- [Current Report](../Report.md)
- [Task Result](../results/{Axx}-{slug}.md)

## Snapshot

| Field | Value |
|---|---|
| Audit Run | `{run-id}` |
| Base SHA / Branch | `{sha}` / `{branch}` |
| Context Fingerprint | `{fingerprint}` |
| Dirty Fingerprint | `{fingerprint/clean}` |
| Task Status | `{pending/running/blocked/stale/completed}` |

## Scope

- **Behavior domain**: `{call chain, data flow, ownership, lifecycle, or boundary}`
- **In-scope paths**: `{entry paths; not a mechanical file slice}`
- **Audit questions**: `{specific falsifiable questions}`

## Why This Scope Exists

- `{Context fact and link/path that justifies the task}`

## Entry Points

- `{symbol/path:line and why it is an entry}`

## Important Boundaries

| Boundary | This Side | Other Side | Related Task |
|---|---|---|---|
| `{boundary}` | `{owner/caller/producer}` | `{borrower/callee/consumer}` | `{Ayy link}` |

## Exclusions

- `{explicitly excluded scope and owning task/reason}`

## Evidence

### Partition Evidence

- `{canonical Context path/section → repository evidence}`

### Evidence Strategy

1. `{search terms/symbol discovery}`
2. `{caller/callee or data-flow trace}`
3. `{owner/lifecycle/boundary checks}`
4. `{focused code read, command, or runtime probe}`

### Required Counter-evidence

- `{guards, cleanup, alternate implementations, platform variants, exception paths, or tests to inspect}`

## Dependencies / Related Tasks

- **Depends on**: `{task IDs/none}`
- **Provides to**: `{task IDs/cross-module review}`
- **Open questions**: `{questions another task must answer}`

## Completion Gate

- [ ] Planned scope and exclusions are accounted for.
- [ ] Result records actual coverage, Evidence and gaps.
- [ ] Candidates follow the Finding state contract.
- [ ] Boundary inputs are ready for cross-module reconciliation.
- [ ] Snapshot remains valid at checkpoint.
