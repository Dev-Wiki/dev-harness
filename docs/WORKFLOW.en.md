# dev-harness end-to-end workflow

[English](WORKFLOW.en.md) | [简体中文](WORKFLOW.md)

> This document explains how the existing eight Skills work together to deliver new features or audit a codebase. Each Skill's exact behavior, authorization, and state remain governed by its `SKILL.md` and runtime.
>
> The [capability catalog](CAPABILITIES.en.md) is authoritative for currently supported capabilities; see [V1 / VNext and V2 boundaries](V1_V2_BOUNDARIES.en.md) for version scope and non-goals. Automatic Planning Task execution is provided by [`dev-harness-runtime`](https://github.com/Dev-Wiki/dev-harness-runtime/blob/main/README.en.md). This document describes its collaboration boundary with the Skills Bundle; the Runtime repository owns platform capabilities and task progress.

## 1. Shared principles

1. The outer workflow defines stage order and handoffs without duplicating a Skill's internal state machine.
2. Requirements, task state, current capabilities, Findings, verification evidence, and commit boundaries each have their own source of truth.
3. Finishing the code does not complete the task. Mark it `✅ 已完成` only after acceptance and verification pass.
4. Commit, push, PR, tag, release, and deploy each require separate authorization.
5. QA is optional. Checks that cannot run must be identified as remaining manual verification items and must not be reported as passed.

## 2. Choose an entry point

Prepare the Project Contract first, then choose a workflow based on the input:

```text
                         Project Contract
                                 │
                  ┌──────────────┴──────────────┐
                  ▼                             ▼
       Known requirements / features    Unknown risks / existing codebase
                  │                             │
                  ▼                             ▼
              Planning                   Codebase Audit
                  │                             │
                  ▼                             ▼
     Develop → Test → Accept → Commit   Findings → Route → Reconcile
```

- For explicit requirements, prototypes, or acceptance goals, use [feature delivery](#4-feature-delivery-workflow).
- To systematically discover unknown engineering defects, use [codebase audit and repair](#5-codebase-audit-and-repair-workflow).
- A known bug with a clear boundary can go directly to `dev-harness-auto-fix` without an Audit first.

## 3. Shared prerequisite: prepare the Project Contract

For a project's first onboarding, use these skills as needed:

- [`dev-harness-context`](../context/SKILL.md): initialize or refresh project context.
- [`dev-harness-docs`](../dev-harness-docs/SKILL.md): confirm the documentation root, navigation, and sources of truth. Planning maintains task archive content within `plan/` itself.
- [`dev-harness-commands`](../commands/SKILL.md): map real commands to stable semantic entry points.
- [`dev-harness-git-workflow`](../git-workflow/SKILL.md): identify the project's Git, commit, and release conventions.

Before writing, confirm at least:

- Project goals, change scope, high-risk areas, and prohibited actions.
- Requirement sources and directly verifiable acceptance criteria.
- Confirmed `build / test / quick / bugfix / full` commands.
- The authoritative locations for documentation, current capabilities, active planning, Git policy, and released changes.
- The current branch, HEAD, worktree, and index state.

If real commands or evidence are missing, retain `Unknown`, `Missing`, or a blocked state. Do not invent entry points from familiarity with the technology stack.

## 4. Feature delivery workflow

### 4.1 Overview

```text
Requirements and acceptance criteria
→ Split the plan into a Dashboard and individual task packets
→ Executor selects an unblocked task and marks it 🚧 开发中
→ Develop
→ Targeted tests + task acceptance
→ Required harness:full / QA
→ Check and update capability documentation; record the check result
→ Mark ✅ 已完成 and archive
→ Commit the exact task changes
→ Next task or milestone closure
```

A normal development Agent implements the feature. dev-harness does not add a feature-development Skill to replace general coding ability. Planning manages work boundaries, Commands provides verification entry points, Docs manages verified facts, and Git Workflow manages commit boundaries.

### 4.2 Clarify requirements and acceptance criteria

Before splitting work, confirm the requirement sources, target users, first-release scope, non-goals, dependencies, and executable acceptance criteria. Unknown protocols, SDKs, credentials, devices, or compliance requirements must be recorded as blockers or prerequisite research instead of being filled in by inference.

Requirements documents own what must be delivered. They do not own development task state or prove that a capability is already supported.

### 4.3 Split the Dashboard and task details

Use [`dev-harness-planning`](../planning/SKILL.md) within the project's existing documentation root to maintain:

- `<docs-root>/plan/Dashboard.md`: the sole active planning entry point, containing the current milestone, work order, task IDs, priorities, states, dependencies, blockers, shared verification baseline, coverage, and detail links.
- `<docs-root>/plan/tasks/<Task-ID>.md`: the execution layer. Each active task separately records its background, goals, authoritative context, code and test entry points, invariants, affected files, suggested steps, acceptance, decisions, stop conditions, and verification evidence.
- `<docs-root>/plan/archive/<milestone>/`: final task summaries and evidence entry points for completed work, excluded from the default reading scope of normal development.

After migration, an existing `TaskDetails.md` may remain only as a compatibility redirect to the Dashboard. It must not continue storing task rows or mutable state.

Splitting rules:

1. List prerequisite research and blockers first, then split P0 core work, P1 supporting work, and P2 future work.
2. Every active task in the Dashboard must link to exactly one `tasks/<Task-ID>.md`.
3. Each task should be independently implementable, verifiable, and committable. Record cross-task dependencies explicitly.
4. Use stable states: `📋 规划中`, `🟢 待执行`, `🚧 开发中`, `✅ 已完成`, and `📋 远期`. Only a complete execution packet may enter `🟢 待执行`.
5. Never infer completion from planning or conversation without implementation and verification evidence.
6. Before the packet is ready, identify the existing capability catalog, relevant IDs or prospective behavior, documentation requirements, and acceptance method. Include necessary documentation changes in affected files and execution scope beforehand. If no catalog applies, record the basis; do not defer the check until Worker execution and then expand authorization.

### 4.4 Pick up and develop one task

Planning generates and maintains a handoff-ready work order, `🟢 待执行` state, and task execution packets. It does not choose the execution method, claim tasks, or orchestrate development. A user can explicitly name a Task ID in a new conversation. Automatic pickup, recovery, or concurrency control belongs to a separate execution Skill, Agent workflow, or external orchestrator, using the Dashboard's current order, dependencies, and blockers without creating a second order from priority.

After resolving one unique Task ID, the executor changes its state only in the Dashboard from `🟢 待执行` to `🚧 开发中`, then loads its task file, the necessary context it names, and actually relevant code. Do not read all active or completed task bodies. Record a temporary planning snapshot before claiming or resuming a task. If the Dashboard, task path, or `HEAD` later changes outside the current work, reread and reconcile before proceeding with the old selection.

Development follows the project's `AGENTS.md`, architecture constraints, and existing code style. If implementation reveals a requirement gap, return to the requirements or current task file to clarify it. Do not silently add scope to the task. Known defects can go to Auto Fix; larger architecture changes should return to Planning for a new breakdown.

### 4.5 Test and accept

Task risk and the project's `HARNESS.md` determine verification scope. The recommended order is:

```text
harness:quick / relevant build
→ Targeted harness:test or task-specific tests
→ Acceptance criteria in the current task file
→ harness:full when required
→ QA / Dogfood when executable
```

- `quick` provides fast feedback and cannot replace task acceptance.
- Targeted tests should cover the feature's normal, exceptional, and key boundary paths.
- Run `full` when requested by the user, required by a project gate applicable to this task, or justified by an evidenced coverage gap. High risk, shared infrastructure, or committing alone does not trigger repository-wide regression. Select verification along actual impact, and do not label an arbitrary local command as full. See the [verification rules](../internal/bugfix-flow/verify.md#验证范围与全仓回归).
- Device or UI acceptance that the environment cannot execute must remain an explicit manual item.

Any failure returns to the current task for repair and revalidation. Do not overwrite failure evidence with an older successful result.

### 4.6 Sync facts and state, then commit

After verification passes, close the task in this order:

1. Inspect the current diff, task acceptance results, and fresh validation evidence.
2. Use Docs to incrementally reconcile the current capability catalog and other affected authoritative documents. Record the catalog path, relevant capability IDs, verification evidence, and the specific basis for updated / no update required / not applicable. Successful closure requires necessary updates to be complete. A fix restoring an existing promise normally keeps its ID; plans must not be written as supported capabilities.
3. Record final verification commands or result references in the task file, move it into `archive/<milestone>/`, remove it from the Dashboard's active area, and add a bounded recently-completed summary.
4. Use Git Workflow to stage only the current task's files, inspect sensitive content, debug residue, and unrelated changes, then commit.
5. Run push, PR, tag, release, or deploy only with separate authorization for each.

Prefer one commit per independently verifiable task. A commit failure does not change verification facts, but the uncommitted state must be reported; do not continue claiming that delivery closure is complete.

### 4.7 Continue or close the milestone

After committing, the executor rereads the Dashboard, selects the next unblocked task according to the user's instruction or independent execution workflow, and repeats the development loop. Once every planned task in a milestone is complete, run fresh `harness:full` and available QA, summarize the milestone, and close its archive with:

- Completed, remaining, and blocked tasks.
- Acceptance and full verification evidence.
- Actual commit SHAs and any push / PR results produced under separate authorization.
- Updated current-capability or other authoritative documents.
- Remaining risks and manual verification items.

Before closing a milestone that changes product support, use Docs to reconcile capabilities across the full declared scope. The archive links to that reconciliation evidence only. For a milestone without product-support changes, record the reason reconciliation is unnecessary.

### 4.8 Three capability-maintenance stages

| Stage | When | Output |
|---|---|---|
| Initial full inventory | No authority for current capabilities exists | A catalog and coverage baseline based on implementation and evidence |
| Incremental synchronization | After each feature, fix, or support-condition change | Updated existing items or new items, with the check result recorded before task completion |
| Full reconciliation | Explicitly requested rescan, or before closing a milestone that affects product support | Recheck the full scope and all existing IDs; fill gaps, correct errors, and refresh evidence |

All three stages share one catalog. Reader-facing prose explains purpose, support, limitations, and usage; technical evidence is expanded under the corresponding item. Full reconciliation is repeatable and keeps IDs for unchanged items. Identify unchecked scope explicitly; a partial review must not be called a full reconciliation. See [capability maintenance](../dev-harness-docs/references/capability-maintenance.en.md) for coverage, recovery, deduplication, and completion rules.

## 5. Codebase audit and repair workflow

### 5.1 Audit and Finding routing

[`dev-harness-codebase-audit`](../codebase-audit/SKILL.md) applies to user-owned or explicitly authorized repositories:

```text
Dynamic partitioning → Staged scan → Candidate → Verification
→ Confirmed / Rejected → Cross-module Reconciliation → Report
```

Audit discovers, verifies, and routes issues without changing product source, tests, or configuration. Only confirmed Findings in the authoritative Finding Registry proceed to downstream handling.

New runs should use `batch` to persist task results, Findings, and document metadata together, then `render-output` to generate compact documents instead of repeatedly hand-writing identical navigation and snapshots. After cross-module reconciliation, close in this order: generate current documents → check content and links → complete → refresh the completed display. Older handwritten artifacts remain compatible. See the [Audit batch interface](../codebase-audit/references/runtime-interface.en.md) for inputs and full gates.

| Finding type | Downstream owner |
|---|---|
| defect / crash / lifecycle bug | `dev-harness-auto-fix` |
| architecture / refactor / tech debt | `dev-harness-planning`, entering the Roadmap after user acceptance |
| docs drift | `dev-harness-docs` |
| verification gap | `dev-harness-commands` |
| Git / release / changelog gap | `dev-harness-git-workflow` |

### 5.2 Handle defects individually

Send confirmed defects to [`dev-harness-auto-fix`](../auto-fix/SKILL.md):

```text
preflight → context → reproduce → hypothesize → profile assessment → RED
→ minimal fix → GREEN → capability-documentation check → review → final verify → optional commit
```

Prefer a separate Auto Fix Run for each confirmed defect so it can be verified, reviewed, reverted, and evidenced independently. The outer workflow must not commit changes already committed by Auto Fix. After `fix` mode, a Git Workflow commit needs separate authorization.

Known bugs entering Auto Fix directly also require the documentation check, without first running a code-quality audit. `DocumentationCheck` binds to the current change fingerprint; a missing or stale check blocks successful completion and commit at runtime. See [Auto Fix capability-documentation checks](../auto-fix/SKILL.md#61-功能文档检查).

Authorization `Mode` and verification `ValidationProfile` are independent. Use `fast` for small low-risk changes and `standard` for medium risk. Security, ABI, concurrency, persistence, permissions, signing, shared infrastructure, cross-repository production dependencies, or uncertain risk require `strict`. Assess the profile once after confirming the boundary and again after the final diff stabilizes; automatic changes may only raise it. Reuse evidence according to actual proof obligations. In `fast / standard`, final verification does not rerun expensive commands if the post-review diff hash is unchanged and obligations are covered.

`BLOCKED` or `NEEDS_CONTEXT` stops processing and must not be silently skipped. Each owner maintains its Docs, Commands, Planning, or Git Workflow handoff; detailed downstream state is not copied into the Audit report.

### 5.3 Combined verification, QA, and final reconciliation

After all planned code changes are complete, run the confirmed `harness:full`. A single Auto Fix GREEN proves only the target repair; fresh `full` establishes that the combined changes still satisfy the project's complete verification requirements.

After full verification, run QA / Dogfood as the environment permits. New QA issues normally enter Auto Fix as known bugs. Codebase Audit creates formal Findings only when long-term tracking and cross-module reconciliation are needed; other workflows must not invent `AUD-*` IDs.

Code changes invalidate some evidence in the original Audit Snapshot. For long-running governance, create a fresh Audit Snapshot in the final worktree and let Codebase Audit reclassify the original Findings as `resolved / remaining / stale`. Only Codebase Audit updates Finding state.

The final report contains at least the original Audit Run, Finding outcomes, Auto Fix state, actual commit SHAs, fresh `harness:full`, QA and manual items, final reconciliation results, and remaining blockers.

## 6. Runtime integration boundary

`dev-harness` provides engineering contracts for Context, Planning, Commands, Git Workflow, and Docs, plus evidence workflows for Auto Fix and Codebase Audit. Use the separate [`dev-harness-runtime`](https://github.com/Dev-Wiki/dev-harness-runtime/blob/main/README.en.md) for automatic execution of planned tasks; it consumes these contracts through a locked protocol source.

Before handoff, follow the [Runtime handoff guide](../planning/references/runtime-handoff.en.md) to check confirmed command tables, Dashboard unblocked values, independent task sections, and the frozen `dhr-runtime` declaration. Normal manual planning is not subject to these automatic-dispatch format restrictions. Refresh old plans within bounds first; never fabricate or relax configuration in a Run that has already started.

Prepare project context, HARNESS, Git policy, and an executable Planning Task first. Then use Runtime's `run` entry to start a named task, the next ready Task, or all ready Tasks. Core handles eligibility, snapshots, authorization, Worker dispatch, independent acceptance, and Run state. Worker closes the current task according to the upstream Planning contract. `status` reads persistent state; `resume` revalidates boundaries before resuming the same Run. No commit is the default; per-task commits require explicit authorization.

The Skills Bundle installer installs only this repository's eight skills. Install the Runtime plugin and `dhr` entry separately using the [Runtime usage instructions](https://github.com/Dev-Wiki/dev-harness-runtime/blob/main/README.en.md#usage). Generating installation artifacts and automatically executing on a host are separate capabilities; the [Runtime platform matrix](https://github.com/Dev-Wiki/dev-harness-runtime/blob/main/docs/PLATFORM_MATRIX.en.md) defines actual support.

Runtime's execution unit is a Planning Task. The Audit → Finding routing → Auto Fix → QA → final reconciliation flow in section 5 still follows each Skill's responsibilities; it is not a built-in complete Runtime pipeline. When using Skills alone, the user or Agent owns stage transitions, downstream Run references, and the final summary.
