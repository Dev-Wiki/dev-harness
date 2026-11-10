# V1 / VNext and V2 boundaries

[English](V1_V2_BOUNDARIES.en.md) | [简体中文](V1_V2_BOUNDARIES.md)

> Document role: this file is the sole source of truth for V1 / VNext and V2 version boundaries, non-goals, and completion criteria.
> See [`CAPABILITIES.md`](CAPABILITIES.en.md) for currently supported capabilities, applicability, version placement, and verification evidence. The [VNext improvements and Codebase Audit design](dev-harness%20VNext%20%E4%BC%98%E5%8C%96%E4%B8%8E%20Codebase%20Audit%20%E8%AE%BE%E8%AE%A1%E6%96%B9%E6%A1%88.md) records the v1.8.0 design rationale; [`V2_BACKLOG.md`](V2_BACKLOG.en.md) records future candidates only.

## Version naming

**VNext** in the design record means the compatible evolution from the existing V1 to the v1.8.0 Project Contract and Codebase Audit capabilities; it remains within the V1 scope defined here. Within the same boundary, v1.9.0 added Capability Catalogs and Audit document discoverability; v1.9.1 unified Chinese terminology and template wording; v1.10.0 clarified Engineering Audit responsibilities, output-language conventions, minimum behavioral verification, and the Finding identity gate; v1.11.0 added bounded planning packets, legacy monolithic-plan migration, and a natural-Chinese output contract across all skills; v1.11.1 made Dashboard the sole active planning entry and added a planning drift gate; v1.11.2 added risk-tiered Auto Fix verification, structured evidence reuse, and fail-fast state writes; v1.11.3 added Planning readiness gates and individual execution packets that can be handed to another conversation; v1.11.4 hardened installation/export, Context previews and truncated evidence, Audit reconciliation invalidation, and the Auto Fix final-diff gate, and completed offline release documentation. None of these changes alters the V2 boundary. VNext is not another name for V2. Current capabilities, version boundaries, and future candidates are owned respectively by `CAPABILITIES.md`, this file, and `V2_BACKLOG.md`; implementation stages in design records are not an active task list.

## V1 positioning

v1.12.0 completes initial full capability inventory, incremental updates, and repeatable full reconciliation; presents capabilities in the order ordinary users need them; and adds documentation checks to Planning and Auto Fix closure. These changes remain within existing project contracts and documentation maintenance, without changing the V1 / VNext and V2 boundaries.

v1.11.8 makes the versioned zip a collection of skills that can be installed by copying their folders. Source code and maintenance documents are supplied through the matching source archive. Both installation methods remain available, with no change to Skill capabilities or the V1 / VNext boundary.

v1.11.5 improves Audit batch state updates and compact document generation within the same boundary, and requires structured runs to verify the persisted receipt for the current Revision before completion. It does not expand audit authorization or introduce execution orchestration.

The goal of `dev-harness` V1 / VNext is to give existing projects a consistent Project Contract, executable verification interfaces, and complete evidence chains for bug fixes and large-codebase audits.

Applicable projects:

- WPF clients
- Harmony phone / PC apps
- Win32 applications
- Mixed projects such as WPF + NativeBridge + Win32 / C++ SDK
- Qt clients, which remain supported for onboarding but are not a priority enhancement target in this iteration
- Go, Flutter, and Node.js projects, gated by their respective high-risk boundaries

Problems V1 addresses:

- An AI entering a repository for the first time does not know how to read it.
- The AI does not know which commands implement build / test / quick / bugfix / full.
- The AI does not know which directories and files are high-risk.
- The AI may make blind changes around NativeBridge / Win32 / C++ SDK boundaries.
- Bug fixes lack stable reproduction, diagnosis, regression, and verification baselines.
- The AI may mix existing workspace changes into the current fix or commit.
- “Verified” and “reviewed” claims are not bound to the final code diff.
- A large codebase cannot fit into one conversation; scan progress, evidence, and Findings are easily lost across sessions.

Automatic Planning Task execution is provided by the separate [`dev-harness-runtime`](https://github.com/Dev-Wiki/dev-harness-runtime/blob/main/README.en.md). See the [workflow](WORKFLOW.en.md#6-runtime-integration-boundary) for integration. This preserves this repository's Skills Bundle role; Runtime capabilities already implemented there are not recorded as V2 capabilities of this repository.

## Included in the V1 boundary

The following describes V1 responsibilities rather than a capability count. See [`CAPABILITIES.md`](CAPABILITIES.en.md) for independently verifiable current capability items and evidence.

### 1. Project context initialization

- Generate `README.md`.
- Generate `AGENTS.md`.
- Generate `ARCHITECTURE.md`.
- Generate `HARNESS.md`.

### 1.1 Documentation and planning organization

- Reuse the project's existing `doc/` or `docs/` root without creating a second documentation tree.
- Establish a documentation hub, progressive navigation, sources of truth, document ownership, and archive rules.
- Establish a Capability Catalog when current capability facts are scattered, support differs by role/platform/version, or capabilities cannot be counted reliably; reuse an existing equivalent capability document.
- Record support status, applicability, delivery version, and verification method separately in the Capability Catalog; count only independently verifiable items with stable IDs and evidence.
- Generate the sole active entry `plan/Dashboard.md`, individual task details under `tasks/`, and milestone archives under the same documentation root; retain an existing `TaskDetails.md` only as a compatibility redirect after migration.
- Maintain Audit tasks, results, the Finding Registry, and reports under `audit/` in the same documentation root.
- Do not include full Diataxis documentation generation from code or repository-wide documentation staleness detection based on branch diffs.

### 2. Client-project onboarding support

- Prioritize recognition of `WPF / Harmony / Win32 / Unknown`.
- Recognize basic characteristics of mixed `WPF + NativeBridge` projects.
- Retain basic recognition and safe fallback for `Qt`.
- Extract high-risk directories and areas that must not be changed.
- Extract candidate call chains, architecture boundary rules, forbidden operations, and exploration suggestions.

### 3. NativeBridge risk recognition and explicit labeling

- Recognize `*.vcxproj`.
- Recognize `DllImport`.
- Recognize `MarshalAs`.
- Recognize callback / observer usage.
- Recognize traces of Win32 API usage.
- Output automatically detected candidates.
- Output items requiring human confirmation.

### 4. Command semantics layer

- `harness:build`
- `harness:test`
- `harness:quick`
- `harness:bugfix`
- `harness:full`

### 5. Bugfix Flow and executable contracts

- `dev-harness-auto-fix` includes references for the four stages repro / triage / regression / verify.
- Four explicit authorization modes: analyze / fix / commit / unattended.
- Falsifiable hypotheses: Claim / Prediction / Probe / Observation / Status.
- Regression tests default to RED before the fix and GREEN after it.
- Review and final verification are bound to the diff hash.
- Completion states: DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT.

`auto-fix/runtime.py` makes the following boundaries executable and testable:

- WorkspaceSnapshot records HEAD, branch, and fingerprints of existing modifications at task start.
- An existing dirty worktree may remain, but the Agent must not touch those changes.
- AutoFixChangedFiles contains only changes produced in the current conversation.
- State is stored in a private Git directory and supports stage recovery after process interruption.
- Illegal stage transitions, undeclared changes, drift in existing modifications, and unauthorized commits are rejected.

It also includes risk boundaries for client projects:

- UI layer
- Resource layer
- Native bridge layer
- Packaging layer

### 6. Codebase Audit V1

- Audit user-owned or explicitly authorized repositories for engineering quality, behavioral correctness, and cross-module consistency; this is not penetration testing or an offensive security workflow.
- Dynamically derive subsystem / runtime / platform / native / data audit partitions from Canonical Context rather than shipping a giant language checklist.
- Bind AuditSnapshot to HEAD, branch, existing dirty fingerprints, Context fingerprint, scope, and output root.
- Store state at `.git/dev-harness/codebase-audit/<run-id>/state.json`, supporting cross-session resume/status/task checkpoints.
- New structured runs support atomic batch updates, batch path validation, and summary output. `render-output` generates documents from existing evidence, and completion verifies that the current Revision has been persisted. The renderer does not analyze code or infer conclusions; older manually written runs remain compatible (v1.11.5).
- Permit writes only under the existing `<docs-root>/audit/**`; fail closed on source, Context, or workspace drift, and mark old confirmed Findings stale.
- Use internal Finding states candidate / needs-verification / confirmed / rejected / stale / resolved, bound to Evidence and Snapshot. Documents display natural Chinese by default and switch only when the user explicitly requests English-only output.
- Keep candidates separate by default; merge only when root cause, ownership, repair boundary, and the effect of a single fix all match.
- Verify runtime behavior against the project's declared behavior, preferring local, deterministic, minimal reproductions.
- Require Cross-module Reconciliation before completion: check Finding identity, resolve contradictions, review end-to-end paths, and reorder Severity / Confidence. Audit does not fix source, create PRs, or automatically add items to a Roadmap.
- Use `<docs-root>/audit/Report.md` as the stable entry. If the documentation hub lacks a link, record `docs-refresh-required`; Docs adds the entry before AuditSnapshot creation, and Audit does not modify the hub outside its scope.

## Explicit V1 non-goals

- UI automation
- Screenshot-driven verification
- Log / metric / Trace platform integration
- A multi-worktree parallel scheduler; worktree-specific private Git state paths are already supported
- An automatic PR / multi-Agent review scheduler
- Automatic native-layer repair
- Full documentation-content generation and pre-release documentation-coverage audits
- Automatic proof of ABI / marshaling correctness
- Deep semantic verification of Win32 handles / threads / message loops

## V2 candidate directions

### 1. Runtime Harness orchestration

- Add independent per-task run directories over the existing auto-fix state contract.
- Launch worktrees.
- Probe runtime status.
- Clean up runtime environments automatically.

### 2. Observability Harness

- Standardize log entry points.
- Provide metric / Trace query entry points.
- Provide a local observation layer readable by AI.

### 3. UI Harness

- Launch applications.
- Capture screenshots.
- Perform basic automated UI checks.
- Run smoke verification.

### 4. Deeper NativeBridge support

- Extract more detailed `Service -> Interface -> Bridge -> Native` call chains automatically.
- Score high-risk files.
- Classify marshaling / callback / thread / handle risks more precisely.
- Persist human-confirmation results and write them back to the corresponding documents.

### 5. Agent Loop Automation

- Automatic review
- Automatic feedback-and-fix loops
- Documentation staleness detection
- Tech-debt / doc-gardening tasks

## Completion criteria

V1 can be considered complete when:

1. It can generate the four context files.
2. It can expose the `build / test / quick / bugfix / full` semantics layer.
3. It explicitly identifies high-risk areas and forbidden-change boundaries.
4. For NativeBridge projects, it outputs automatically detected candidates and items requiring human confirmation.
5. It does not fabricate completion when commands or evidence are missing.
6. The current fix does not accidentally alter, stage, or commit pre-existing dirty-worktree changes.
7. Completion evidence matches the final diff; code changes invalidate old evidence.
8. Existing `doc/` or `docs/` roots are reused, and documentation organization and planning do not create competing roots.
9. The active Planning entry does not accumulate completed task bodies indefinitely; individual task details load on demand and move to milestone archives after completion.
10. Complex or scattered current capabilities have one verifiable, countable authoritative document; simple projects and projects with an equivalent capability document are not forced to split it.
11. Codebase Audit can recover across sessions and does not keep publishing old confirmed conclusions after product source or Context drifts.
12. The Codebase Audit Report is reachable from the documentation hub, or an explicit pending Docs Refresh handoff is recorded.
