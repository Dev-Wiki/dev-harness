---
name: dev-harness-planning
description: Use when a project needs reusable planning documents, backlog boards, task breakdowns, or Dashboard.md and TaskDetails.md generated under its existing doc/ or docs/ root from requirements, prototypes, existing docs, or reference formats
---

# dev-harness-planning

Generate reusable project planning docs from real requirements and prototypes.

## When to Use

Use this skill when asked to:

- create or refresh `<docs-root>/plan/Dashboard.md`
- create or refresh `<docs-root>/plan/TaskDetails.md`
- turn requirements, PRDs, prototypes, screenshots, or rough notes into a backlog board and execution plan
- reuse another project's planning format without copying its business content

Do not use this for ordinary one-file edits, bug fixing, code review, or command mapping. It is a project-, release-, or milestone-level planning contract.

## Required Inputs

Read the available project evidence before writing:

- Documentation root: resolve the existing project-owned `doc/` or `docs/` root before selecting output paths.
- Requirements: `<docs-root>/spec.md`, `<docs-root>/prd/*`, `<docs-root>/product/*`, or user-provided files.
- Prototypes: HTML, images, mockups, flows, or screenshots.
- Existing planning docs: if present, preserve local terminology and status conventions.
- Reference format: if the user names another project's board/plan docs, read those files and copy the structure only.

If a source is missing, state the gap in the generated plan instead of inventing details.

## Output Contract

Resolve `<docs-root>` before writing:

1. Honor a documentation root explicitly named by the user.
2. Prefer the root containing an existing documentation index, governance file, or active plan.
3. If only `doc/` exists, use `doc/`; if only `docs/` exists, use `docs/`.
4. If both exist and ownership is ambiguous, stop and report the conflict instead of creating another plan tree.
5. If neither exists, default to `docs/`.

Use the same root selected by `dev-harness-docs` when that skill has already established one. Never rename `doc/` to `docs/` or create both roots merely to match this skill's default.

Output paths:

- `<docs-root>/plan/Dashboard.md`
- `<docs-root>/plan/TaskDetails.md`

Use the bundled templates:

- `templates/Dashboard.template.md`
- `templates/TaskDetails.template.md`

Dashboard is the index layer. It contains status, priority, coverage, links, gaps, and acceptance scope. It must not repeat implementation detail.

TaskDetails is the execution layer. It contains task background, goals, files, steps, validation, risks, and maintenance rules.

## Workflow

1. Resolve `<docs-root>` without creating a competing `doc/` or `docs/` tree.
2. Read requirements and prototypes.
3. Read existing or referenced planning docs.
4. Extract product goal, actors, workflows, hardware/software constraints, integration points, and acceptance criteria.
5. Split work into one prerequisite task, P0 core tasks, P1 supporting tasks, and P2 future tasks.
6. If the plan does not exist, generate Dashboard and TaskDetails from the bundled templates.
7. If the plan exists, build a merge map keyed by existing Task ID: preserve unchanged rows, links, local labels and completed states; add or update only evidence-backed tasks. Do not regenerate either file from the template.
8. Check every Dashboard task links to a TaskDetails heading.
9. Search generated files for placeholder words: `TBD`, `TODO`, `FIXME`, `待补`, `占位`.
10. Report the resolved documentation root, source files read, files created or updated, and verification evidence.

## Planning Rules

- Prefer task IDs that reflect phase and scope, such as `V0`, `K1`, `K2`, `S1`, or project-local conventions.
- Use priority labels consistently: `🔴 P0`, `🟡 P1`, `🟢 P2`.
- Use status labels consistently: `📋 规划中`, `🚧 开发中`, `✅ 已完成`, `📋 远期`.
- Keep Dashboard concise and link-heavy.
- Keep TaskDetails concrete enough for an engineer or AI agent to start work without rereading all source docs.
- Mark unknown protocols, APIs, SDKs, credentials, devices, and compliance requirements as blockers or risks.
- Never copy another project's business-specific backlog items into the current project.
- On refresh, preserve existing task IDs, links, project-local statuses, priorities, and user-confirmed completed states whenever their underlying work is unchanged.
- Never mark a task completed from AI inference alone; require implementation and verification evidence or an explicit user status.
- A Codebase Audit finding may be proposed as planning input, but do not add it to the roadmap until the user accepts the scope and priority.
- Keep refresh diffs minimal: report reused IDs, added IDs, changed statuses and unresolved conflicts before writing.

## Verification

Before claiming completion, run:

```bash
DOCS_ROOT="<resolved-docs-root>"
test -f "$DOCS_ROOT/plan/Dashboard.md"
test -f "$DOCS_ROOT/plan/TaskDetails.md"
rg -n "TBD|TODO|FIXME|待补|占位" "$DOCS_ROOT/plan"
```

`rg` should exit 1 with no matches for the placeholder scan.
