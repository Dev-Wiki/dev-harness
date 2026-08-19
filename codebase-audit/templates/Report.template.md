# Codebase Audit Report

> **职责**：本文件是当前有效 Snapshot 下的开发者总览，只汇总已验证 Findings、跨模块结论、未决证据和建议 handoff。权威 Finding 正文见 [Findings.md](Findings.md)，执行状态见 [Dashboard.md](Dashboard.md)。

## Navigation

- [Dashboard](Dashboard.md)
- [Finding Registry](Findings.md)
- [Audit Tasks](tasks/)
- [Task Results](results/)

## Documentation Discoverability

| Field | Value |
|---|---|
| Documentation Hub | `{docs-root}/README.md or route index` |
| Stable Audit Entry | `{docs-root}/audit/Report.md` |
| Status | `{linked/docs-refresh-required}` |
| Owner / Action | `{dev-harness-docs / none or add one concise hub link}` |

> Audit does not edit the documentation hub. When status is `docs-refresh-required`, this table is the exact navigation handoff and does not require an `AUD-*` Finding.

## Snapshot

| Field | Value |
|---|---|
| Audit Run | `{run-id}` |
| Base SHA / Branch | `{sha}` / `{branch}` |
| Context Fingerprint | `{fingerprint}` |
| Audit Scope | `{include/exclude summary}` |
| Last Drift Validation | `{checkpoint/result}` |
| Cross-module Reconciliation | `{completed/stale}` |

## Executive Summary

`{Current, evidence-backed outcome; do not write a generic best-practices essay.}`

- **Tasks**: `{completed/blocked/stale counts}`
- **Confirmed Findings**: `{P0/P1/P2/P3 counts}`
- **Needs Verification**: `{count}`
- **Coverage limits**: `{material exclusions or evidence gaps}`

## Architecture / Scope Summary

`{Concise Context-derived subsystem, runtime/platform boundary, shared core and integration summary with links.}`

## Confirmed Findings

### P0

- [AUD-nnn — `{summary}`](Findings.md#{finding-anchor}) — `{impact and Evidence link}`

### P1

- `{finding link or none}`

### P2

- `{finding link or none}`

### P3

- `{finding link or none}`

## Cross-module Findings

- `{Finding link}: {end-to-end chain, affected modules/platforms, reconciliation decision}`
- **Merged aliases**: `{local/global IDs or none}`
- **Contradictions resolved**: `{claim → evidence-backed decision or none}`
- **Boundary coverage gaps**: `{gap and Result link or none}`

## Needs Verification

- [AUD-nnn](Findings.md#{finding-anchor}) — `{missing probe/evidence and why it blocks confirmation}`

## Rejected / Stale / Resolved

- `{Finding link, state, reason, and relevant Snapshot}`

## Evidence

- **Canonical Context**: `{links and Context fingerprint}`
- **Task coverage**: `{Task/Result links}`
- **Finding Registry**: [Findings.md](Findings.md)
- **Cross-module reconciliation**: `{result/report section links}`
- **Final workspace validation**: `{command/result summary}`

## Recommended Next Actions

| Finding / Gap | Suggested Handoff | Acceptance Direction | Audit Action |
|---|---|---|---|
| `{AUD-nnn}` | `{dev-harness-auto-fix/planning/docs/commands/git-workflow/manual}` | `{future proof required}` | `recommend only` |

> 本报告不授权自动修复、计划创建、文档修改、命令改写、commit、PR 或 release。
