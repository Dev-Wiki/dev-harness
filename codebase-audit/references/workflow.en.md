# Codebase audit workflow

[English](workflow.en.md) | [简体中文](workflow.md)

This document defines long-task stages, checkpoints, and fail-closed gates. AI makes semantic judgments; `runtime.py` enforces snapshots, state, and path boundaries.

## Run invariants

- Context is a prerequisite canonical input, not an output of this stage.
- Version-controlled writes are always restricted to `<docs-root>/audit/**`.
- Private execution state always lives at the actual Git-resolved `.git/dev-harness/codebase-audit/<run-id>/` path.
- Old Evidence supports current conclusions only while its Snapshot remains valid.
- Every Task-local conclusion enters global reconciliation.
- The stable developer entry point is `<docs-root>/audit/Report.md`. Audit checks external navigation read-only; Docs maintains the hub link.
- User instructions or the default `zh-CN` determine this run's `output_language`. Record it in Dashboard and preserve it across sessions. It is not part of the Evidence Snapshot.

## Stage 0 — Preflight / resume

1. Read repository-level `AGENTS.md`, `README.md`, `ARCHITECTURE.md`, `HARNESS.md`, and the contract index when present. Read `LESSONS.md` only if the user explicitly requests retrospective history; a LESSON does not automatically become an audit criterion or hard project constraint.
2. Resolve one `<docs-root>`. Never create a second documentation root for Audit.
3. Select `output_language`: use `en` for an explicit English-only request; follow an existing document's primary language when refreshing it; otherwise use `zh-CN` for new documents without a specified language. On resume, prefer the Dashboard's recorded value.
4. Check read-only whether `<docs-root>/README.md` or one existing route index links `audit/Report.md`. Record `linked` or `docs-refresh-required`. This is not a code Finding and receives no `AUD-*` ID.
5. If the same user authorization includes Docs Refresh, let `dev-harness-docs` add the fixed entry idempotently after all read-only preflight checks pass and before the Audit Snapshot is established. With Audit-only authorization, leave the hub unchanged, continue, and persist an exact handoff.
6. Read `runtime.py --help` and [runtime-interface.md](runtime-interface.en.md). Initialize new runs with `init --summary`; prefer `batch` for task / Finding updates and `render-output` for documents. Do not hard-code unconfirmed arguments or hand-edit state.json.
7. For a new run, put output_language, discoverability, Context sources, and the Task plan into one batch, then render in-progress artifacts. On resume, read `status --summary` and the current Task / Result, load relevant Findings as needed, recompute the Context fingerprint, then `resume --summary`.
8. `render-output` validates every generated path; no per-path prevalidation is needed. For handwritten artifacts, validate the whole set of audit-relative paths with `validate-outputs`, rejecting out-of-scope destinations, symlink escape, and product files.

If Context is missing, clearly stale, truncated, or cannot bind to a fingerprint, return `ContextRequired` and recommend running `dev-harness-context` before restarting. Do not invent a repository model while auditing.

## Stage 1 — Establish the audit snapshot

Create and persist `AuditSnapshot`:

| Field | Meaning |
|---|---|
| Run ID | Stable identifier for this run |
| Baseline SHA / branch | Code baseline |
| Pre-audit worktree fingerprint | Paths, contents, and index state of existing user changes |
| Context fingerprint | Fingerprint of the authoritative Context actually used |
| Audit scope | Includes, exclusions, and user restrictions |
| Output paths | Validated audit-document paths |

Complete execution state goes only into Git-private storage. Structured mode generates Dashboard's full Snapshot table from state; Task / Result / Findings / Report retain only snapshot IDs and references. Never hand-write duplicates. Subsequent gates validate Snapshot freshness within state operations or through independent `verify-workspace`.

## Stage 2 — Dynamic partitioning

Read [partitioning.md](partitioning.en.md) and derive Tasks from Context facts. Organize them around subsystems, call chains, data flows, ownership, or boundaries, not every N files or fixed technology-stack rules.

1. Put the Task plan and index metadata in one `batch`, without manufacturing task counts.
2. Use `render-output` to generate `tasks/Axx.md` and other compact artifacts. Read and incrementally maintain existing handwritten `tasks/Axx-*.md` under their templates instead of deleting and recreating the set.
3. Record each Task's Context source, entry points, boundaries, exclusions, evidence strategy, dependencies, and state. Reader-facing names and questions follow `output_language`; do not copy Context risk labels that lack behavioral explanation.
4. Checkpoint the partition plan. Reuse Tasks without drift after resuming instead of reslicing to meet a quota.

## Stage 3 — Progressive Task execution

Use this funnel for every Task:

```text
Context / repository map
  → Symbol and text search
  → Entry points
  → Callers / callees
  → Responsibility / lifecycle / boundaries
  → Focused code evidence or local behavioral evidence
```

Execution rules:

1. Before starting a Task, recompute the Context fingerprint; mark it in-progress and validate drift in a batch, recording current focus. Do not immediately duplicate a built-in check with verify-workspace.
2. Follow behavioral chains through the minimum necessary files, recording actual coverage and unchecked scope.
3. Preserve each suspicious observation as a separate task-local candidate. Naming, style, one search, the same module, or a shared mechanism does not establish confirmation or identity.
4. Record Evidence, counter-evidence, gaps, candidate mappings, and cross-module inputs in checkpoint.result; let the renderer generate results. Continue maintaining older handwritten files under their templates.
5. After local investigation, persist Task / result and related Findings in one atomic batch. Recover from the last valid checkpoint after interruption, without guessing progress from conversation or waiting until after the final response to record evidence.

When runtime evidence is needed, prefer a minimal, disposable local reproduction in `/tmp` or a temporary directory. Invoke the project's own CLI / API and inspect invalid inputs, boundary inputs, cyclic configuration, real state changes, and error propagation. Validate correctness of the project's declared behavior without exceeding the engineering-verification Scope in `SKILL.md`.

## Stage 4 — Finding verification

Read [finding-contract.md](finding-contract.en.md). For each candidate:

1. Write a separate falsifiable Claim, impact mechanism, trigger conditions, and expected observation.
2. Trace relevant caller / callee, data flow, owner, and lifecycle.
3. Search alternate paths, counterexamples, guards, other implementations, and runtime / test evidence.
4. Use `confirmed` when evidence suffices, `rejected` when disproven, and `needs-verification` while key evidence is missing.
5. Maintain stable `AUD-nnn` IDs through `upsert-finding`. Reuse an ID only when the identity gate proves matching root cause, owner, repair boundary, and one-fix effect. Otherwise keep separate Findings; do not cluster by module or symptoms or bypass state transitions.

Passing local verification means only eligibility for reconciliation. Before reporting, a Finding may still be merged, downgraded, marked stale, or reordered.

Tests already executed against the same snapshot may support multiple Findings. Do not rerun the whole suite for each candidate; investigate further only for changes, failures, or new Evidence gaps. Batch registration still validates every item and cannot skip counter-evidence through bulk confirmation.

## Stage 5 — Cross-module reconciliation

Read and fully execute [cross-module-review.md](cross-module-review.en.md). At minimum:

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

- Merge observations only when the identity gate establishes one Finding, keeping other candidates separate.
- Resolve contradictions between Tasks.
- Connect call chains, data flows, lifecycles, and ownership across both sides of boundaries.
- Check shared core effects on every caller / platform.
- Reassess severity and confidence.
- Explicitly identify unresolved Evidence gaps.

Even with no confirmed Finding, record the coverage matrix, contradiction checks, and evidence for no confirmable cross-module issue. Do not omit this stage.

Reference authoritative Evidence for closed local chains. Investigate only seams, contradictions, omissions, or changes further instead of repeating the entire audit. Register reconciliation after all Task / Finding / document updates; later input changes invalidate it.

## Stage 6 — Final report

New structured runs use `render-output → inspect content / mutual links → complete --summary → render-output`. The first render publishes the current Revision's evidence and in-progress state; complete verifies the artifacts are unchanged; the second render updates completed presentation only. Do not reread the entire document set or launch Python per path again. A failed final render requires an explicit incomplete-documentation report, not a verbal completion claim. The following also applies to older handwritten workflows.

1. Revalidate Snapshot. On drift, stop and apply stale handling.
2. Update `Findings.md` so every state and Evidence reference points to one authoritative record.
3. Update Dashboard counts, state, blockers, and Last Verified Snapshot.
4. Generate Report with `render-output`; read Report.template.md only for handwritten mode. Summarize current confirmed P0–P3, cross-module Findings, needs-verification, and handoffs in this run's output_language, preserving internal enums.
5. Keep Documentation Discoverability consistent in Dashboard and Report: hub, fixed entry point, `linked/docs-refresh-required` state, maintainer, and exact action. Without the link, do not claim Audit is discoverable from project documentation.
6. Pass renderer path validation or handwritten `validate-outputs`, and check mutual links, one Task per Result, unique Finding IDs, and Snapshot / Evidence for every confirmed item.
7. Checkpoint completion. Audit must not execute handed-off modifications, create plans, update the documentation hub, commit, or create PRs.

## Documentation discoverability

Audit and Docs divide responsibility as follows:

- Audit writes and maintains `<docs-root>/audit/**`, with fixed entry `audit/Report.md`.
- Docs idempotently maintains a concise link in `<docs-root>/README.md` or one existing route index, without copying Findings, totals, or conclusions.
- A root README shortcut is optional and need not be duplicated if the hub is reachable.
- When a new Audit and Docs Refresh are both authorized, order them as `read-only Audit preflight → Docs Refresh → AuditSnapshot/init → Audit execution`.
- With an active Audit Snapshot, do not change the hub. Record a handoff to avoid presenting navigation changes as audit output or causing undeclared drift.

## Worktree drift

Validate before resume, every Task, any transition to `confirmed`, reconciliation, and reporting. Any of these changes makes affected evidence fail closed:

- HEAD or branch changes.
- Changes to contents or index state of preexisting dirty files.
- Audited source changes not incorporated into the run.
- Context fingerprint changes.
- Changes to audit scope or output paths.

Record `WorkspaceDrift` Evidence, mark affected results / Findings `STALE` / `stale`, and stop publishing current conclusions. Clear stale only after necessary Tasks and verification run again under a new Snapshot.

## Completion checklist

- [ ] Every Task is completed, blocked, or stale with a traceable reason.
- [ ] Every Task has a corresponding Result.
- [ ] Every confirmed Finding has the current Snapshot and Evidence.
- [ ] Shared root causes are deduplicated; contradictions are resolved or downgraded to needs-verification.
- [ ] Cross-module Reconciliation is recorded.
- [ ] All current Audit documents share one `output_language`, recorded in Dashboard, without unnecessary mixed-language prose.
- [ ] Final drift and path-boundary checks pass.
- [ ] Dashboard, Findings, Report, Task, and Result are mutually reachable.
- [ ] Documentation Discoverability is `linked`, or Dashboard, Report, and the final response each record the exact Docs Refresh handoff.
- [ ] No files outside `<docs-root>/audit/**` and Git-private state were modified.
