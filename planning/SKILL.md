---
name: dev-harness-planning
description: Use when a project needs reusable planning documents, backlog boards, task breakdowns, or Dashboard.md and TaskDetails.md generated from requirements, prototypes, existing docs, or reference formats
---

# dev-harness-planning

Generate reusable project planning docs from real requirements and prototypes.

## When to Use

Use this skill when asked to:

- create or refresh `docs/plan/Dashboard.md`
- create or refresh `docs/plan/TaskDetails.md`
- turn requirements, PRDs, prototypes, screenshots, or rough notes into a backlog board and execution plan
- reuse another project's planning format without copying its business content

Do not use this for bug fixing, code review, or command mapping.

## Required Inputs

Read the available project evidence before writing:

- Requirements: `docs/spec.md`, `docs/prd/*`, `docs/product/*`, or user-provided files.
- Prototypes: HTML, images, mockups, flows, or screenshots.
- Existing planning docs: if present, preserve local terminology and status conventions.
- Reference format: if the user names another project's board/plan docs, read those files and copy the structure only.

If a source is missing, state the gap in the generated plan instead of inventing details.

## Output Contract

Default output paths:

- `docs/plan/Dashboard.md`
- `docs/plan/TaskDetails.md`

Use the bundled templates:

- `templates/Dashboard.template.md`
- `templates/TaskDetails.template.md`

Dashboard is the index layer. It contains status, priority, coverage, links, gaps, and acceptance scope. It must not repeat implementation detail.

TaskDetails is the execution layer. It contains task background, goals, files, steps, validation, risks, and maintenance rules.

## Workflow

1. Read requirements and prototypes.
2. Read existing or referenced planning docs.
3. Extract product goal, actors, workflows, hardware/software constraints, integration points, and acceptance criteria.
4. Split work into one prerequisite task, P0 core tasks, P1 supporting tasks, and P2 future tasks.
5. Generate Dashboard from `templates/Dashboard.template.md`.
6. Generate TaskDetails from `templates/TaskDetails.template.md`.
7. Check every Dashboard task links to a TaskDetails heading.
8. Search generated files for placeholder words: `TBD`, `TODO`, `FIXME`, `待补`, `占位`.
9. Report source files read, files created or updated, and verification evidence.

## Planning Rules

- Prefer task IDs that reflect phase and scope, such as `V0`, `K1`, `K2`, `S1`, or project-local conventions.
- Use priority labels consistently: `🔴 P0`, `🟡 P1`, `🟢 P2`.
- Use status labels consistently: `📋 规划中`, `🚧 开发中`, `✅ 已完成`, `📋 远期`.
- Keep Dashboard concise and link-heavy.
- Keep TaskDetails concrete enough for an engineer or AI agent to start work without rereading all source docs.
- Mark unknown protocols, APIs, SDKs, credentials, devices, and compliance requirements as blockers or risks.
- Never copy another project's business-specific backlog items into the current project.

## Verification

Before claiming completion, run:

```bash
test -f docs/plan/Dashboard.md
test -f docs/plan/TaskDetails.md
rg -n "TBD|TODO|FIXME|待补|占位" docs/plan
```

`rg` should exit 1 with no matches for the placeholder scan.
