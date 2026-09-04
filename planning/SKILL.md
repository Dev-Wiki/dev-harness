---
name: dev-harness-planning
description: Create or refresh bounded project, release, or milestone plans under an existing doc/ or docs/ root, using one authoritative active Dashboard, task-scoped execution packets with readiness gates, completed-task archives, and drift checks.
---

# dev-harness-planning

Maintain reusable project plans without forcing an AI agent to load the full task history.

## When to Use

Use this skill when asked to:

- create or refresh `<docs-root>/plan/Dashboard.md`
- create or refresh task-scoped detail files under `<docs-root>/plan/tasks/`
- merge duplicate Dashboard / TaskDetails active indexes into one authoritative Dashboard
- turn requirements, PRDs, prototypes, screenshots, or rough notes into a project, release, or milestone backlog
- split an oversized planning document or archive completed planning work
- reuse another project's planning format without copying its business content

Do not use this for ordinary one-file edits, bug fixing, code review, task execution, or command mapping.

## Required Inputs and Read Scope

Resolve the existing project-owned `doc/` or `docs/` root, then inspect requirements such as `<docs-root>/spec.md`, `<docs-root>/prd/`, or `<docs-root>/product/`; prototypes; local planning conventions; and existing plan indexes. If the user names another project's plan, reuse its structure only, not its business content.

Inventory before reading detail bodies:

```bash
PLAN_ROOT="<resolved-docs-root>/plan"
test ! -d "$PLAN_ROOT" || rg --files "$PLAN_ROOT"
for plan_file in "$PLAN_ROOT/Dashboard.md" "$PLAN_ROOT/TaskDetails.md"; do
  test ! -f "$plan_file" || wc -l -c "$plan_file"
done
test ! -d "$PLAN_ROOT" || rg -n '^#{2,4} .*Task|^\|.*(📋|🟢|🚧|✅)' "$PLAN_ROOT"
```

Missing files are acceptable during initialization. Do not fail the whole inventory because one file does not exist.

Read `Dashboard.md` as the sole active index, then read only the current or affected task files. Do not read `TaskDetails.md` as a second active source; when present after migration, it is either a legacy monolith that still needs migration or a compatibility redirect to Dashboard. Search archive indexes by Task ID before opening archived detail. Do not load every completed task body merely to select, start, or refresh one active task. A legacy monolith migration is the exception: read [references/legacy-migration.md](references/legacy-migration.md) and process every source task body in bounded sections so the migration is lossless without loading the whole history at once.

If a source is missing, record the gap instead of inventing product details, protocols, APIs, credentials, devices, or compliance requirements.

## Output Contract

### 输出语言

- 用户明确要求英文或其他语言时，按用户要求输出；否则，中文项目以及未指定语言的新建文档默认使用简体中文。
- 更新既有文档时跟随文档的主体语言，不借机翻译无关的历史内容。
- 标题、表格字段、任务名称、范围、验收标准、验证结果、迁移台账和最终报告应使用中国人习惯的自然中文，避免逐字翻译形成生硬表达。
- 文件路径、命令、代码符号、API、协议名、产品名、必要缩写、任务编号和项目内部枚举保持原样；首次面向读者出现且可能引起歧义时，用中文简要解释。
- 内部状态或分类值必须保真；面向读者展示时，优先先给出中文含义，再保留必要的原值。

Resolve `<docs-root>` before writing:

1. Honor a documentation root explicitly named by the user.
2. Prefer the root containing an existing documentation index, governance file, or active plan.
3. If only `doc/` exists, use `doc/`; if only `docs/` exists, use `docs/`.
4. If both exist and ownership is ambiguous, stop and report the conflict instead of creating another plan tree.
5. If neither exists, default to `docs/`.

Use the same root selected by `dev-harness-docs`. Never rename an established root or create a competing `doc/` or `docs/` tree.

Default planning layout:

```text
<docs-root>/plan/
├── Dashboard.md
├── tasks/
│   └── <Task-ID>.md
└── archive/
    └── <milestone>/
        ├── README.md
        └── <Task-ID>.md
```

- `Dashboard.md` is the only active planning authority: milestone status, work order, Task ID, priority, status, dependency, blocker, shared verification baseline, coverage, recent completions, and links. It must not repeat task implementation detail.
- `tasks/<Task-ID>.md` is the authoritative execution packet for one active task: background, goal, scope, authoritative sources, code and test entry points, invariants, expected files, suggested steps, acceptance, verification evidence, confirmed decisions, and task-specific stop conditions. It must not duplicate mutable cross-task fields such as status, priority, dependency, work order, or blocker.
- `archive/<milestone>/README.md` indexes completed tasks for one closed or active milestone. Archived task files preserve useful final rationale and evidence without remaining in the active read path.
- An existing `TaskDetails.md` may remain only as a short compatibility redirect to `Dashboard.md`. It must not contain task rows, status, priority, dependency, work order, blockers, validation baselines, or task bodies.

This ownership prevents read drift: mutable cross-task state has one source, task execution detail has one source, and closed work has one immutable source. Do not copy a field merely to make a file self-contained; link to its authority instead.

Use the bundled templates:

- `templates/Dashboard.template.md`
- `templates/Task.template.md`
- `templates/ArchiveIndex.template.md`
- `templates/TaskDetails.template.md` only when an existing inbound link requires a compatibility redirect

Honor an existing equivalent partitioned convention instead of renaming it to match these defaults.

## Workflow

1. Resolve `<docs-root>` and inventory the existing plan without loading all historical detail.
2. Read requirements, prototypes, Dashboard, and only affected task files. If a previous run selected a task, revalidate its planning snapshot before trusting that selection.
3. Extract the product goal, actors, workflows, constraints, integration points, and acceptance criteria.
4. Split work into prerequisite, P0 core, P1 supporting, and P2 future tasks using stable project-local IDs.
5. For a new plan, generate one `Dashboard.md` entry file and one `tasks/<Task-ID>.md` file per active task from the bundled templates. Do not generate `TaskDetails.md`.
6. For an existing partitioned plan, merge by Task ID: preserve existing task IDs, unchanged local labels, priorities, links, and evidence-backed completed states; update only Dashboard and affected task files. Move mutable cross-task fields out of task files instead of keeping synchronized copies.
7. An untouched legacy monolithic `TaskDetails.md` may retain its existing anchors temporarily while it remains below every default guardrail: 1,000 lines, 100 KB, and 20 task bodies. Before the next refresh that would change overlapping active state, before any content write after a guardrail is exceeded, or whenever the user requests splitting or archival, read and follow [references/legacy-migration.md](references/legacy-migration.md). A stricter project-owned limit wins.
8. Build a move map before migration or archival. Move each complete task body to its own stable path, update repository-wide inbound links and every relative link inside the moved body, and avoid copying the same body into both active and archived locations.
9. In a partitioned plan, check every active Dashboard row links to one authoritative active task file and every archived summary links to one archived task snapshot. Do not preserve a second mutable active index after migration.
10. If repository-owned links still target the non-anchor `TaskDetails.md`, either rewrite them to Dashboard or keep the compatibility redirect. Never keep duplicate active rows for compatibility.
11. Report reused, added, moved, archived, status-changed, and drifted Task IDs plus verification evidence.

## Planning Snapshot and Drift Gate

Before selecting or resuming an active task, record an ephemeral planning snapshot; do not write it into project documents:

```bash
git rev-parse HEAD
sha256sum "$PLAN_ROOT/Dashboard.md" "$PLAN_ROOT/tasks/<Task-ID>.md"
git status --short
```

The snapshot binds `HEAD`, Dashboard hash, selected Task ID and path, task-file hash, and pre-existing worktree changes. Before trusting a previous selection, changing planning state, archiving, or reporting completion, recompute it.

- If HEAD, Dashboard, selected task path, or pre-existing content changed outside the current work, stop and reload Dashboard before continuing.
- If the selected task is no longer active, its link changed, or another file now claims the same active Task ID, stop and reconcile ownership.
- Changes made by the current work are expected only inside its declared file set. An undeclared Dashboard or task-file change is drift, not a reason to overwrite the newer state.
- Apply a lifecycle transition as one reviewed change: update final task evidence, move the task to its archive, update Dashboard, update inbound links, then validate the whole set. Do not leave intermediate duplicate authorities.

## Task Lifecycle

- `📋 规划中` means the execution packet is incomplete. `🟢 待执行` means the planning packet is complete enough to hand off after its Dashboard dependencies and blockers are checked. `🚧 开发中` means execution has started. `📋 远期` remains outside the current work order. These active tasks stay in `tasks/` and Dashboard.
- Move a task from `📋 规划中` to `🟢 待执行` only when its goal, scope, authoritative context, invariants, acceptance criteria, verification method, and unresolved planning questions are complete enough for a fresh conversation to act without access to planning chat history.
- Never mark a task completed from AI inference alone. Require implementation and verification evidence or an explicit user status.
- When a task becomes `✅ 已完成`, first record its final acceptance result and durable evidence links, then move its detail file to `archive/<milestone>/` in the same planning refresh. Do not treat an ambiguous local state such as “implemented, pending acceptance” as completed without the project's explicit status semantics.
- Remove the completed task from Dashboard's active work order and task table. Dashboard may keep at most five recent completed summaries; older completions belong only in the milestone archive index.
- When all milestone tasks are closed, retain only a milestone summary and archive link in Dashboard.
- Git history carries editing chronology. Do not accumulate repeated progress notes, command transcripts, or superseded implementation drafts in the final task body.
- If a completed task becomes active again, keep its immutable closure snapshot in the milestone archive and create `tasks/<Task-ID>.md` as the sole active execution authority. Link the active file to the prior closure, record why it reopened, and add its mutable state only to Dashboard.

These rules bound the active read path; the archive can still grow when the project chooses to retain historical evidence.

## Planning Rules

- Prefer phase-and-scope IDs such as `V0`, `K1`, `K2`, or the project-local convention.
- Default priorities are `🔴 P0`, `🟡 P1`, and `🟢 P2`; default statuses are `📋 规划中`, `🟢 待执行`, `🚧 开发中`, `✅ 已完成`, and `📋 远期`.
- Keep one task independently implementable, verifiable, and linkable. Split a task file that itself becomes a broad multi-feature plan.
- Keep status, priority, dependency, work order, and blockers only in Dashboard. Active task files must link back to Dashboard instead of copying those values.
- Reference authoritative requirements, code, test output, commits, or audit results instead of duplicating their full contents.
- Preserve user-confirmed completed states during migration and refresh.
- A Codebase Audit finding may be proposed as planning input, but do not add it to the roadmap until the user accepts its scope and priority.
- Keep refresh diffs minimal and preserve local terminology when it does not violate the active/archive ownership boundary.

## Verification

Before claiming completion, adapt and run:

```bash
PLAN_ROOT="<resolved-docs-root>/plan"
test -f "$PLAN_ROOT/Dashboard.md"
active_plan_paths=("$PLAN_ROOT/Dashboard.md")
test ! -d "$PLAN_ROOT/tasks" || active_plan_paths+=("$PLAN_ROOT/tasks")
rg -n 'TBD|TODO|FIXME|待补|占位' "${active_plan_paths[@]}"
wc -l -c "$PLAN_ROOT/Dashboard.md"
test ! -d "$PLAN_ROOT/tasks" || ! rg -n '^\*\*(状态|优先级|依赖|阻塞|执行顺序)\*\*[：:]' "$PLAN_ROOT/tasks"
test ! -f "$PLAN_ROOT/TaskDetails.md" || rg -n 'Dashboard\.md' "$PLAN_ROOT/TaskDetails.md"
```

The placeholder and duplicated-mutable-field scans should exit 1; report intentional registers instead of rewriting them. If `TaskDetails.md` exists as a compatibility redirect, verify it has no task rows, mutable state, validation baseline, or task body. For a migrated plan, also search the repository for obsolete `TaskDetails.md#...` inbound links and verify all changed relative links. Confirm that each active Task ID appears once in the active task table and has exactly one active task file, and that every `🟢 待执行` Task ID appears exactly once in current work order. Immutable archived closure snapshots are history, not active authorities. Recompute the planning snapshot before claiming completion.
