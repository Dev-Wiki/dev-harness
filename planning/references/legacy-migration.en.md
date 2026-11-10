# Migrating legacy monolithic plans

[English](legacy-migration.en.md) | [简体中文](legacy-migration.md)

Read this reference when an existing `TaskDetails.md` duplicates active state with the Dashboard, exceeds Planning capacity guardrails, or the user requests task splitting or historical archiving.

Migration must preserve every task body and every meaningful link. Its goal is a shorter active reading path without discarding history through summaries.

## 1. Preflight inventory and mapping

Before editing, inventory the monolith by headings. Build a migration ledger covering the entire source file: one row for each task body, plus separate rows for non-task ranges such as the preface, grouping explanations, shared verification baselines, and maintenance rules.

| Field | Required confirmation |
|---|---|
| Task ID | Preserve existing stable IDs. Stop migration if IDs are duplicated or missing. |
| Source range | A task ends before the next heading of equal or higher level, or at EOF. Register non-task ranges separately so every line has an owner. |
| Original state | Preserve project-local values until evidence establishes their meaning. |
| Completion evidence | Record a state explicitly supplied by the user, or implementation and verification evidence. |
| Milestone | Use explicit source metadata only; do not infer it from task order or names. |
| Completion date | Use explicit dates only. |
| Destination | Select one unique active or archive path for the body. |
| Outgoing links | Inventory relative links and same-file anchors in the body. |
| Incoming links | Search the whole repository for links to the source file or task anchors. |

Assign every non-task range:

- Current milestone goals, scope, or coverage summary → `Dashboard.md`.
- Active work order, shared dependencies, verification baseline, or maintenance rules → `Dashboard.md`.
- Final evidence or historical summaries for an entire milestone → its archive directory's `README.md`.
- A topic body with its own lifecycle → the project's topic document, linked from an appropriate index.

Do not absorb a following higher-level shared section into the preceding task. Prefaces, meaningful separators, and global sections must survive even without task IDs.

Search all repository-owned Markdown and rule files, not only `plan/`:

```bash
rg -n 'TaskDetails\.md(?:#[A-Za-z0-9._~!$&()*+,;=:@%/-]+)?' . \
  --glob '*.md' --glob '*.mdc' --glob '!vendor/**' --glob '!node_modules/**'
```

Before moving files, report ledger totals, complete source coverage, ambiguities, proposed paths, and incoming-link impact. Stop if task boundaries, duplicate IDs, content ownership, or completion states cannot be determined safely, and preserve the entire source.

Also record a temporary planning snapshot: current `HEAD`, Dashboard hash, `TaskDetails.md` hash, and preexisting worktree state for migration paths. Recheck it before applying. If source files, Dashboard, or incoming links changed outside this migration, stop and rebuild the ledger rather than overwrite newer content.

## 2. Deterministic classification

- Archive a task only when completion meets the project's evidence requirements or the user explicitly confirms completion.
- Ambiguous states such as implemented, partially complete, or awaiting deployment acceptance remain active unless the project explicitly defines them as completed.
- A task eligible for archiving without an explicit milestone goes to `archive/legacy-import-YYYY-MM-DD/`. Explain that this is a migration collection directory, not an inferred product milestone.
- Order recently-completed summaries only by explicit completion dates. Undated tasks do not enter the Dashboard's latest five; link their archive index instead.
- Move planning, in-progress, blocked, ambiguous, and future tasks into `tasks/<Task-ID>.md`.
- Move tasks with sufficient completion evidence directly into `archive/<milestone>/<Task-ID>.md`, without first passing through `tasks/`.

## 3. Stage before applying

Treat a broad migration as a transaction over the exact paths in its move map:

1. Record pre-migration hashes or byte-for-byte snapshots for every potentially changed file, preserving unrelated existing worktree changes.
2. Generate the complete destination tree and proposed modified files in a temporary staging directory outside the live documentation tree. Resolve relative links according to each file's final path.
3. Validate source coverage, task-ID ownership, destination counts, rewritten incoming links, and relative-link targets against the staging tree together with unchanged repository files.
4. Apply the verified move map to live directories only after every staged postcondition passes.
5. Repeat the same postconditions in live directories. If application or final validation fails, restore only mapped paths from snapshots and delete only files newly created by this migration. Before reporting failure, confirm that plan and incoming-link files match pre-migration hashes.

Do not use a broad Git reset or checkout for rollback or overwrite unrelated user changes.

## 4. Lossless chunked migration

Process the monolith in chunks, but process each task and non-task ledger record exactly once:

1. Copy the complete source task body to its destination, including final rationale and evidence.
2. Normalize only outer task headings or metadata required by `Task.template.md`; do not rewrite product content just to fit a template. Remove mutable state, priority, dependency, order, or blocker fields from active task files only after their complete original values are in the Dashboard. Archive snapshots retain final closure metadata.
3. Rewrite same-file task anchors to the new task or archive paths.
4. Recalculate every relative link in migrated bodies from the destination directory, including links to `Dashboard.md`, `topics/`, `projects/`, requirements, product documents, images, and sibling archives.
5. Update all repository-owned incoming links found in preflight, preserving meaningful link text and anchors.
6. Place each non-task range in its mapped current index, archive index, or independent topic document.
7. Add active tasks, work order, and cross-task mutable fields to `Dashboard.md`; add completed tasks to the selected milestone archive index.
8. Replace the monolith with a compatibility redirect pointing only to the Dashboard after every ledger record has a verified staged destination. The file may also be removed once neither repository nor external readers need the old path.

Do not retain duplicate bodies in the monolith and destination files. Git history preserves the pre-migration text.

## 5. Reopen a task

An archived task file is an immutable closure snapshot. When reopening:

1. Keep `archive/<milestone>/<Task-ID>.md` and its archive-index entry unchanged; an additional link to the reopened task is permitted.
2. Create `tasks/<Task-ID>.md` as the sole active authority, linking the previous closure snapshot.
3. Record why the task reopened, its new scope, and current acceptance criteria.
4. While open, maintain active state and the task-file link only in the Dashboard. Do not add task-level links to the compatibility `TaskDetails.md`.
5. On another closure in the same milestone, retain `<Task-ID>.md` as the first snapshot and use the next unoccupied `<Task-ID>.closure-<N>.md`, starting at 2. Never overwrite an existing target. Record the closure count in the archive index, link the new snapshot to its predecessor, and point the recently-completed summary to this closure.

## 6. Postconditions

Before deleting the monolithic body or announcing success, confirm every item:

- The source task count equals active task files plus newly created archive snapshots.
- Every task and non-task source range appears at exactly one destination, without omission or duplication.
- Each active Task ID has exactly one active authoritative file.
- The Dashboard is the sole active planning entry point and remains bounded.
- If retained, `TaskDetails.md` contains only a Dashboard compatibility redirect, with no task rows, states, priorities, dependencies, work order, blockers, or verification baseline.
- Every archive-index target exists.
- Repository-owned incoming links no longer point to removed `TaskDetails.md` anchors.
- Every changed Markdown relative link resolves to an existing file and valid anchor.
- Ambiguous states, missing dates, and legacy-import collection-directory assignments are reported explicitly.
- `git diff --summary --find-renames` agrees with the final move map.
- Final `HEAD`, Dashboard, task paths, and worktree changes match the migration snapshot and declared change set. Any undeclared drift has stopped work and been reconciled.

Failed staging validation must not modify live planning. Failed live application restores the mapped paths and rechecks pre-migration hashes. Report the blocking ledger records and leave no partially migrated state.
