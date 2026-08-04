---
name: dev-harness-docs
description: Use when a project needs its documentation structure initialized, organized, audited, refreshed, indexed, archived, or its verified facts updated, including doc/docs root detection, progressive navigation, SSOT boundaries, document placement rules, link validation, and fact-sync discipline
---

# dev-harness-docs

Organize project documentation without inventing a second documentation root or duplicating facts. Preserve project-owned conventions and separate documentation structure from documentation content generation.

## Boundaries

Keep these responsibilities separate:

- Let `dev-harness-context` own root `README.md`, `AGENTS.md`, `ARCHITECTURE.md`, and `HARNESS.md` managed sections.
- Let `dev-harness-planning` own the active `plan/Dashboard.md` and `plan/TaskDetails.md` content.
- Let `dev-harness-git-workflow` own release, CHANGELOG, tag, and commit conventions.
- Let `dev-harness-retro` own `LESSONS.md` maintenance.
- Own the documentation root, index, navigation, placement, SSOT, discoverability, and archive rules here.
- Own the verified-fact update discipline: only facts proven by code, configuration, or successful validation may be written; task logs, commit summaries, one-off paths, failed attempts, and personal preferences never enter project documentation.
- Do not generate a full tutorial, API reference, or feature explanation unless the user explicitly requests content authoring. Organize and route those documents instead.

## Select the Operation

Infer the operation from the request:

- **Audit**: inspect structure, duplicate ownership, orphaned documents, and broken navigation; do not edit files.
- **Initialize**: create the minimum index and documentation rules for a repository without an established documentation system.
- **Organize**: propose and, when authorized, apply a safer information architecture to existing documents.
- **Refresh**: update indexes, navigation, placement rules, and archive links after documents change.
- **Update**: after code or validation changes, sink only verified, reusable project facts into existing documents; produce a minimal add/correct/delete plan with evidence, preserve human-owned prose and structure, and leave unverified items as `待确认` instead of facts.
- **Archive**: move completed or superseded documents only after confirming the exact move map and link impact.

Treat review, explanation, and audit requests as read-only. Treat initialize, organize, refresh, update, and archive requests as authorization to edit only the documentation files in scope. Update requires validation evidence for every fact written. Ask before broad file moves, deletions, or replacing an established documentation convention.

## Resolve the Documentation Root

Resolve one documentation root before creating files:

1. Honor a path explicitly named by the user.
2. Prefer the root containing an existing documentation index, governance file, or active plan.
3. If only `doc/` exists, use `doc/`.
4. If only `docs/` exists, use `docs/`.
5. If both exist, determine whether one is generated, vendor-owned, historical, or narrowly scoped. Stop and report ambiguity if both appear project-owned.
6. If neither exists, default to `docs/`.

Never rename an established root or create a second root merely to match a template. Record the resolved value as `<docs-root>` and use it consistently, including `<docs-root>/plan`.

## Read Evidence Progressively

Read repository instructions before proposing changes:

1. Read `LESSONS.md`, `AGENTS.md`, root `README.md`, and `ARCHITECTURE.md` when present.
2. Inventory Markdown and documentation-framework files with `rg --files`; exclude generated, dependency, cache, build, and vendor directories.
3. Read the current documentation index and navigation files first.
4. Read representative or directly affected documents next. Do not recursively load a large documentation tree into context.
5. Read [references/information-architecture.md](references/information-architecture.md) when creating navigation, defining SSOT ownership, planning moves, or updating verified facts.

Base every classification on a document's actual audience and purpose. Do not classify by filename alone.

## Design the Structure

Create only directories justified by existing or requested content. Use these common destinations as options, not a mandatory skeleton:

- `product/` for requirements, manuals, roadmaps, and product boundaries
- `arch/` for architecture and design rationale
- `plan/` for active planning indexes, topics, projects, and archives
- `how-to/` for task-oriented procedures
- `reference/` for factual APIs, configuration, schemas, and command references
- `integration/` for third-party platform documentation
- `standards/` for project-owned engineering or interaction rules
- `deployment/` for deployment, operations, backup, and delivery procedures
- `troubleshooting/` for reproducible solved problems
- `archive/` only for material that is no longer actively maintained

Create `<docs-root>/README.md` as the default documentation hub. Use [assets/docs-index.template.md](assets/docs-index.template.md) as a starting point, but adapt its sections to the repository.

Create `<docs-root>/DOCUMENTATION.md` for placement, SSOT, navigation, and archive rules when the project needs a durable maintenance contract. Use [assets/documentation-rules.template.md](assets/documentation-rules.template.md).

Create `nav/` only when the documentation has at least three stable reader or task routes and a single index has become difficult to scan. Use [assets/nav.template.md](assets/nav.template.md) for each justified route. Do not copy another project's route names blindly.

## Enforce SSOT

Assign each changing fact exactly one writable owner:

- Keep index documents concise: status summary, one-line description, and links.
- Keep topic documents authoritative for cross-task status and decisions.
- Keep implementation, requirement, or reference documents authoritative for their local detail.
- Link to an existing fact instead of restating it in another document.
- Mark superseded or completed documents clearly, link to the current authority, and stop maintaining their body.
- Preserve historical decisions in an archive when they remain useful for audit or rationale.

Do not claim that duplicated prose is synchronized merely because it currently matches.

## Update Verified Facts

After code or validation changes, update existing documents with verified facts only.

Admission gate — a fact qualifies only when it satisfies all of:

- proven by current code, configuration, or a successful validation;
- something future developers will repeatedly need;
- a clear owning document and stable scope.

Excluded by default: task logs, commit summaries, one-off paths, failed attempts, and personal preferences.

Workflow:

1. Read the current diff, design or review artifacts, and validation evidence.
2. Locate the existing SSOT owner (root README, AGENTS, ARCHITECTURE, HARNESS, module docs, or docs index); do not create a second authority to host a fact.
3. Produce a minimal update plan: for every add, correction, or deletion, name the fact and its evidence; no opportunistic full rewrites.
4. Preserve human-authored sections, encoding/BOM, heading levels, line endings, style, and framework metadata; keep the edit surgical.
5. Check links, commands, versions, examples, and duplicates; put unverified items into `待确认` instead of rendering them as facts.
6. Report modified files, how each fact was verified, and the remaining documentation gaps.

Do not re-implement owned boundaries: managed `README.md` / `AGENTS.md` / `ARCHITECTURE.md` / `HARNESS.md` sections are refreshed by `dev-harness-context`, and release / CHANGELOG facts belong to `dev-harness-git-workflow`.

## Apply Changes Safely

Before editing:

1. Capture `git status --short` and preserve unrelated user changes.
2. Produce an explicit proposed map for every create, move, rename, archive, and index update.
3. Identify incoming links to files that would move.
4. Stop for confirmation when the map contains broad moves, removals, generated documentation, or ambiguous ownership.

When editing:

1. Create the minimum missing structure; do not create empty category directories.
2. Update relative links affected by approved moves.
3. Add new documents to the nearest index and ensure the documentation hub reaches them.
4. Add only lightweight documentation links to root `README.md` or `AGENTS.md`; do not copy deep content there.
5. Preserve encoding, line endings, frontmatter, framework-specific metadata, and user-owned prose.
6. Keep existing `doc/` versus `docs/` naming and local language conventions.

## Coordinate with Planning

Resolve the same `<docs-root>` before invoking or following `dev-harness-planning`:

- Write the active dashboard to `<docs-root>/plan/Dashboard.md`.
- Write task details to `<docs-root>/plan/TaskDetails.md`.
- Keep Dashboard as the index layer and TaskDetails as the execution/topic layer.
- Archive completed implementation plans without copying their detailed status back into Dashboard.

## Verify

Run checks proportionate to the change:

```bash
DOCS_ROOT="<resolved-docs-root>"
git status --short
rg --files "$DOCS_ROOT"
rg -n 'TBD|TODO|FIXME|待补|占位' "$DOCS_ROOT"
```

Also verify:

- every new or moved document is reachable from `<docs-root>/README.md` or one justified navigation route;
- every relative Markdown link changed by the task resolves to an existing target or valid anchor;
- only one project-owned documentation root is active;
- index documents do not repeat detailed status or implementation notes;
- archived documents link to the current authority and are not presented as active;
- every fact written by an Update is backed by diff or validation evidence, never by speculation;
- commands and links written by an Update resolve to real targets;
- unverified claims appear only under a `待确认` heading, never as facts;
- no unrelated file was modified.

Treat intentional TODO registers as an explicit exception to the placeholder scan. Report the exception instead of silently deleting valid backlog content.

## Report

Report:

- operation and resolved documentation root;
- evidence and conventions read;
- files created, updated, moved, or left unchanged;
- SSOT and navigation decisions;
- validation commands and results;
- unresolved ambiguity, intentionally deferred moves, unverified items moved to `待确认`, or optional content-authoring gaps.
