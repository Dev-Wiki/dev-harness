# Cross-module reconciliation

[English](cross-module-review.en.md) | [简体中文](cross-module-review.md)

This is a mandatory global stage in every audit. Task results are local evidence and cannot simply be concatenated into a final report.

Final convergence must pass through the complete sequence:

```text
Task-local issues
    ↓
Boundary ledger
    ↓
Finding identity review
    ↓
Contradiction resolution
    ↓
End-to-end chain tracing
    ↓
Reassess severity and confidence
    ↓
Final report
```

## Inputs

- The currently valid `AuditSnapshot`.
- All Tasks and Results, including blocked Tasks, Tasks without Findings, and stale Tasks.
- Candidate, needs-verification, confirmed, and rejected entries in the Findings Registry.
- Subsystem, boundary, shared-core, platform, and integration relationships in Context.

Run drift validation before starting. If it fails, stop reconciliation and mark affected conclusions `stale`.

## 1. Build a boundary ledger

For every important seam, record both ends and evidence:

| Boundary | Producer / caller / owner | Consumer / callee / borrower | Tasks | Evidence | State |
|---|---|---|---|---|---|
| `{boundary}` | `{side-a}` | `{side-b}` | `{Axx, Ayy}` | `{result links}` | `{covered/gap}` |

Cover at least the runtime, platform, shared-core, data/persistence, external-integration, and build/package boundaries present in Context. Do not invent inapplicable dimensions.

## 2. Review Finding identity

Assess candidate identity individually before grouping by root cause, owner, and repair boundary. Merge only when evidence proves the same root cause, the same owner / responsibility boundary, substantially the same repair boundary, and one repair that can reasonably resolve the observations together:

- Merge multi-module symptoms of one root cause, retaining the earliest stable Finding ID.
- Preserve source Tasks, aliases, affected platforms, and every Evidence link.
- Keep separate Findings when symptoms match but mechanisms differ.
- Keep separate Findings when they share a module or broad mechanism but any identity condition remains unproven.
- Reject or return for verification candidates that merely repeat best practices without a concrete mechanism.

## 3. Resolve contradictions

List conflicts explicitly instead of choosing the more confident Task:

| Claim | Supporting evidence | Counter-evidence | Missing verification | Outcome |
|---|---|---|---|---|
| `{claim}` | `{link}` | `{link}` | `{reproduction or behavior evidence}` | `{resolved/needs-verification}` |

Check conditional compilation, platform variants, startup / cleanup order, exceptional paths, concurrency timing, and other implementations. Conflicts not resolved by evidence must be downgraded to `needs-verification`.

## 4. Trace end-to-end behavior

Connect the complete chain for potentially cross-layer Findings, for example:

```text
entry/UI lifecycle → state/manager → wrapper/adapter
                   → FFI/native/service → worker/callback/storage
```

Also inspect:

- configuration → runtime.
- state → mutation.
- precondition → side effect.
- module → module.
- input/state → transformation → output/side effect.
- Whether calls are reachable and returns / errors propagate correctly.
- Whether lifecycle ordering is incorrectly presented as a call relationship, or the chain crosses unverified entry points. Follow the [Finding contract's Chain requirements](finding-contract.en.md#verification-gates) to distinguish prerequisites from actual calls.
- The owner's creation, sharing, cancellation, and destruction order.
- Types, units, null values, and consistency on both sides of data boundaries.
- Context changes across callbacks, threads, and transactions.
- Shared-core changes affecting every caller / platform.
- Whether the build/package variant actually includes the audited implementation.

Inspecting just one layer does not complete this stage.

## 5. Reassess and apply gates

For every merged Finding, reassess:

- Whether Severity reflects actually reachable impact rather than local code appearance.
- Whether cross-module evidence strengthens or weakens Confidence.
- Whether Snapshot / Evidence remains current.
- Whether Suggested Next Action points to the correct owner Skill.
- Whether any caller, platform, or lifecycle remains uncovered.

Only Findings with complete evidence and no unresolved contradictions remain in the current `confirmed` set. Mark other entries `needs-verification`, `rejected`, or `stale`.

## Required results

Record in Report and the relevant Results:

- The boundary coverage ledger or its authoritative link.
- Merged / aliased Finding IDs and evidence for all four identity conditions.
- Related Candidates kept separate and the reasons they were not merged.
- Contradictions and their resolutions.
- Newly discovered cross-module Findings.
- Severity / confidence changes.
- Uncovered boundaries and Evidence gaps.
- The Snapshot used for reconciliation.

Even with no Finding, record which boundaries were reviewed, which Task Results were compared, and why no confirmable conclusion was found. Audit cannot complete without this record.
