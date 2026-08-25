---
name: dev-harness-planning
description: Create or refresh bounded project, release, or milestone plans under an existing doc/ or docs/ root, using a concise dashboard, an active-task index, task-scoped detail files, and completed-task archives.
---

# dev-harness-planning

Maintain reusable project plans without forcing an AI agent to load the full task history.

## When to Use

Use this skill when asked to:

- create or refresh `<docs-root>/plan/Dashboard.md`
- create or refresh `<docs-root>/plan/TaskDetails.md` or task-scoped detail files
- turn requirements, PRDs, prototypes, screenshots, or rough notes into a project, release, or milestone backlog
- split an oversized planning document or archive completed planning work
- reuse another project's planning format without copying its business content

Do not use this for ordinary one-file edits, bug fixing, code review, or command mapping.

## Required Inputs and Read Scope

Resolve the existing project-owned `doc/` or `docs/` root, then inspect requirements such as `<docs-root>/spec.md`, `<docs-root>/prd/`, or `<docs-root>/product/`; prototypes; local planning conventions; and existing plan indexes. If the user names another project's plan, reuse its structure only, not its business content.

Inventory before reading detail bodies:

```bash
PLAN_ROOT="<resolved-docs-root>/plan"
test ! -d "$PLAN_ROOT" || rg --files "$PLAN_ROOT"
for plan_file in "$PLAN_ROOT/Dashboard.md" "$PLAN_ROOT/TaskDetails.md"; do
  test ! -f "$plan_file" || wc -l -c "$plan_file"
done
test ! -d "$PLAN_ROOT" || rg -n '^#{2,4} .*Task|^\|.*(📋|🚧|✅)' "$PLAN_ROOT"
```

Missing files are acceptable during initialization. Do not fail the whole inventory because one file does not exist.

Read `Dashboard.md`, the active index in `TaskDetails.md`, and only the current or affected task files. Search archive indexes by Task ID before opening archived detail. Do not load every completed task body merely to select, start, or refresh one active task. A legacy monolith migration is the exception: read [references/legacy-migration.md](references/legacy-migration.md) and process every source task body in bounded sections so the migration is lossless without loading the whole history at once.

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
├── TaskDetails.md
├── tasks/
│   └── <Task-ID>.md
└── archive/
    └── <milestone>/
        ├── README.md
        └── <Task-ID>.md
```

- `Dashboard.md` is the current-state index: milestone status, priority, coverage, blockers, acceptance scope, and links. It must not repeat task implementation detail.
- `TaskDetails.md` is a compact active-task gateway: work order, dependencies, shared verification baseline, and links to active task files. It must not contain full task bodies or an append-only execution log.
- `tasks/<Task-ID>.md` is the authoritative execution packet for one active task: background, goal, scope, files, steps, acceptance, verification evidence, and risks.
- `archive/<milestone>/README.md` indexes completed tasks for one closed or active milestone. Archived task files preserve useful final rationale and evidence without remaining in the active read path.

Use the bundled templates:

- `templates/Dashboard.template.md`
- `templates/TaskDetails.template.md`
- `templates/Task.template.md`
- `templates/ArchiveIndex.template.md`

Honor an existing equivalent partitioned convention instead of renaming it to match these defaults.

## Workflow

1. Resolve `<docs-root>` and inventory the existing plan without loading all historical detail.
2. Read requirements, prototypes, the current indexes, and only affected task files.
3. Extract the product goal, actors, workflows, constraints, integration points, and acceptance criteria.
4. Split work into prerequisite, P0 core, P1 supporting, and P2 future tasks using stable project-local IDs.
5. For a new plan, generate the two entry files and one `tasks/<Task-ID>.md` file per active task from the bundled templates.
6. For an existing partitioned plan, merge by Task ID: preserve existing task IDs, unchanged local labels, priorities, links, and evidence-backed completed states; update only affected indexes and task files.
7. A legacy monolithic `TaskDetails.md` may retain its existing anchor links while it remains below every default guardrail: 1,000 lines, 100 KB, and 20 task bodies. Before any content write after a guardrail is exceeded, or whenever the user requests splitting or archival, read and follow [references/legacy-migration.md](references/legacy-migration.md). A stricter project-owned limit wins.
8. Build a move map before migration or archival. Move each complete task body to its own stable path, update repository-wide inbound links and every relative link inside the moved body, and avoid copying the same body into both active and archived locations.
9. In a partitioned plan, check every active Dashboard row and `TaskDetails.md` entry links to one authoritative active task file. Check every archived summary links to one archived task snapshot. A below-threshold legacy monolith may continue linking to its existing `TaskDetails.md` anchors.
10. Report reused, added, moved, archived, and status-changed Task IDs plus verification evidence.

## Task Lifecycle

- `📋 规划中`, `🚧 开发中`, and `📋 远期` tasks stay in `tasks/` and the active indexes.
- Never mark a task completed from AI inference alone. Require implementation and verification evidence or an explicit user status.
- When a task becomes `✅ 已完成`, first record its final acceptance result and durable evidence links, then move its detail file to `archive/<milestone>/` in the same planning refresh. Do not treat an ambiguous local state such as “implemented, pending acceptance” as completed without the project's explicit status semantics.
- Remove the completed task from active work order and full-detail indexes. Dashboard may keep at most five recent completed summaries; older completions belong only in the milestone archive index.
- When all milestone tasks are closed, retain only a milestone summary and archive link in the active entry files.
- Git history carries editing chronology. Do not accumulate repeated progress notes, command transcripts, or superseded implementation drafts in the final task body.
- If a completed task becomes active again, keep its immutable closure snapshot in the milestone archive and create `tasks/<Task-ID>.md` as the sole active authority. Link the active file to the prior closure and record why it reopened.

These rules bound the active read path; the archive can still grow when the project chooses to retain historical evidence.

## Planning Rules

- Prefer phase-and-scope IDs such as `V0`, `K1`, `K2`, or the project-local convention.
- Default priorities are `🔴 P0`, `🟡 P1`, and `🟢 P2`; default statuses are `📋 规划中`, `🚧 开发中`, `✅ 已完成`, and `📋 远期`.
- Keep one task independently implementable, verifiable, and linkable. Split a task file that itself becomes a broad multi-feature plan.
- Reference authoritative requirements, code, test output, commits, or audit results instead of duplicating their full contents.
- Preserve user-confirmed completed states during migration and refresh.
- A Codebase Audit finding may be proposed as planning input, but do not add it to the roadmap until the user accepts its scope and priority.
- Keep refresh diffs minimal and preserve local terminology when it does not violate the active/archive ownership boundary.

## Verification

Before claiming completion, adapt and run:

```bash
PLAN_ROOT="<resolved-docs-root>/plan"
test -f "$PLAN_ROOT/Dashboard.md"
test -f "$PLAN_ROOT/TaskDetails.md"
active_plan_paths=("$PLAN_ROOT/Dashboard.md" "$PLAN_ROOT/TaskDetails.md")
test ! -d "$PLAN_ROOT/tasks" || active_plan_paths+=("$PLAN_ROOT/tasks")
rg -n 'TBD|TODO|FIXME|待补|占位' "${active_plan_paths[@]}"
wc -l -c "$PLAN_ROOT/Dashboard.md" "$PLAN_ROOT/TaskDetails.md"
```

The placeholder scan should exit 1; report intentional registers instead of rewriting them. For a migrated plan, also search the repository for obsolete `TaskDetails.md#...` inbound links and verify all changed relative links. Confirm that each Task ID has at most one active authoritative detail file; immutable archived closure snapshots are history, not active authorities.
