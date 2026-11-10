# Capability catalog maintenance

[English](capability-maintenance.en.md) | [简体中文](capability-maintenance.md)

Use this workflow for the first inventory of implemented capabilities, incremental synchronization after each delivery, and repeatable full reconciliation. It checks current support rather than code quality and does not infer capability support from completed Dashboard tasks.

## Choose a stage

| User goal | Stage | Scope |
|---|---|---|
| No catalog exists and the user wants to know what is supported | Initial full inventory | The current product's full capability scope |
| A feature, fix, or support condition changes | Incremental synchronization | The current change and affected existing capability items |
| An existing catalog needs a full rescan, gap check, or periodic reconciliation | Full reconciliation | The full capability scope and every existing catalog ID |

Reuse an equivalent existing catalog. Questions about support are read-only; write documents only when the user explicitly requests inventory, synchronization, or reconciliation.

## One catalog, two reading layers

Reader-facing prose serves ordinary users and PMs: capability name, what it enables, support status, applicability, limitations, available versions, and usage entry points. Categorize by real use case. Category navigation links to capability records without repeating changing support states.

Keep stable IDs, verification methods, code or test evidence, and engineering constraints in an expandable area of the same item. If the renderer cannot collapse content, use a technical-details subsection within that item. Do not create another PM catalog requiring manual synchronization. Respect the existing language and valid format instead of rewriting the document merely to fit a template.

## Initial full inventory

1. Confirm one documentation root and catalog path. Read current Context, documentation entry points, existing capability descriptions, and actual implementation entry points. Plans, CHANGELOG, menus, and test names are investigation clues only.
2. Establish the baseline with branch, HEAD, and existing uncommitted changes affecting product support. Per-file fingerprints and process logs stay in temporary workspace or existing verification records; the catalog keeps only a brief explanation and evidence links. Reconcile out-of-scope drift before using old evidence to confirm a new version.
3. Enumerate product scope through user tasks, roles, platforms, integrations, and operating modes before checking individual areas. Identify exclusions and reasons. If the user requests the whole project but only part is checked, the outcome must remain incomplete.
4. Confirm independent behavior along actual entry points, implementation, and applicable tests or runtime verification. Rejected, disabled, and unconnected paths are not supported capabilities. Record code evidence, contract evidence, automated tests, actual execution, and target-environment validation separately; unexecuted checks must not be described as passing in this run.
5. Assign stable IDs to confirmed capabilities. Candidates lacking evidence retain pending IDs and gaps, excluded from supported totals. Count an independent capability once; applicability and implementation details do not create additional counts.
6. Write capability records and the latest full-inventory coverage record, establish documentation-hub navigation, and calculate current-development and latest-release counts separately.

## Incremental synchronization

Follow this order: implementation and verification pass → check documentation impact and complete necessary updates → record the outcome → complete and archive the task. Update only facts established by this change's evidence.

| Change | Catalog handling |
|---|---|
| New independent capability | Check for duplicates, then assign a new ID; distinguish development from released support |
| Changed support, behavior, or limitations | Update the existing ID's description, state, version, and evidence |
| Fix restoring a promised behavior | Check the existing description and evidence, normally reuse the ID; explain why no body update is needed when applicable |
| Internal refactoring, test changes, etc. | Check external behavior and evidence references; commit type alone does not establish no impact |

The completion record keeps only the catalog path, relevant IDs, outcome, basis, and verification entry points. Outcomes are:

- Updated (`updated`): necessary catalog changes are complete; evidence and totals have been checked.
- No update required (`no-impact`): the existing catalog was checked, with an explanation of why support facts and evidence stay valid. A bare no-impact claim is not a basis.
- Not applicable (`not-applicable`): the project has no catalog or equivalent capability documentation requiring maintenance, with the assessment basis. This cannot bypass an existing catalog.

If the check has not run, evidence is insufficient, or necessary changes lie outside authorization, record the gap and stop successful closure. Planning includes documentation paths and check requirements in scope, acceptance, and verification before task readiness. Runtime follows frozen scope and cannot expand its authority. Return old tasks missing these requirements to planning first. Record outcomes in task verification evidence or completion-acceptance results, without creating another capability-state table in the Dashboard. Auto Fix `DocumentationCheck` also binds to the final change fingerprint and must be rechecked after later changes.

These packet requirements apply only to existing Planning / Runtime execution tasks. For a direct documentation-inventory or incremental-sync request without a packet, explain the handling basis in this result or an existing verification record; do not require a new planning task solely for that purpose.

## Repeatable full reconciliation

1. Preserve existing IDs, support records, and the catalog snapshot from before this run. Reestablish the baseline and product scope. Investigate both implementation scope and the existing catalog rather than reviewing only old rows and missing new modules.
2. For each scope, record actual inspection entry points, evidence, and a checked / pending / blocked result. Revalidate the baseline when resuming; unchanged scope can reuse valid evidence, while changed scope requires fresh verification.
3. Every existing ID gets an outcome: unchanged, updated, pending confirmation, deprecated, or removed. Add IDs for new behavior only after deduplication. Names, categories, and applicability changes do not automatically create capabilities.
4. Before declaring an old capability missing, check moved entry points, renaming, switches, and replacement implementations. If removal cannot be established, mark it pending confirmation and retain the ID and prior basis. Mark removed only when current implementation or explicit removal facts prove loss of support, keeping a short ID record.
5. Summarize added, changed, pending, deprecated, and removed IDs. An unchanged rerun must not create duplicates, renumber items, or change version placement merely because the scan date changed.
6. Record full inventory complete only after all declared scope is checked, every old ID has an outcome, pending items are listed, counts and links are checked, and the baseline has not drifted. Blocked or unchecked scope preserves the previous latest complete inventory and makes this run explicitly incomplete. An individual candidate lacking evidence may remain pending, excluded from supported counts.

The catalog maintains only the latest complete inventory's baseline, coverage, and brief outcome. Git or existing verification records preserve history. Temporary progress belongs in existing work records or temporary files, without a second capability authority or another full copy per scan. Completion means reconciliation against declared scope; it does not guarantee discovery of every unknown capability.

## Completion checks

- Full inventory has baseline and coverage evidence; every existing ID has an outcome and new items are deduplicated.
- Incremental synchronization has an explicit result, basis, and necessary updates; task acceptance or the Auto Fix completion gate includes the check.
- Reader-facing prose explains purpose, support, limitations, and entry points; engineering verification stays within the same item.
- Pending and removed items are excluded from supported totals; deprecated items are counted separately. Development and release counts remain separate, and a Git tag alone does not establish release.
- Reference real files, stable sections, or test methods instead of maintaining fragile fixed line numbers. Tests not executed are not marked as passed in this run.

These rules govern Agent capability-inventory work. They do not promise automatic discovery of every product capability through static code analysis.
