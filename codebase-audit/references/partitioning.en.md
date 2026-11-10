# Context-based audit partitioning

[English](partitioning.en.md) | [简体中文](partitioning.md)

Divide a codebase that exceeds one context window into verifiable behavioral domains while preserving cross-boundary relationships. Do not maintain language- or framework-specific checklists.

## Extract partitioning facts from Context

Use only evidence-backed facts from canonical Context:

- Subsystems / modules and their responsibilities.
- Runtime entry points, background workers, callbacks, and lifecycles.
- Boundaries such as UI, adapters, FFI/native, services, and data/persistence.
- Platforms, build variants, and shared core.
- External systems, permission-model boundaries, or external-operation boundaries.
- Build, packaging, and verification entry points.
- High-impact or pending-confirmation items explicitly identified by Context.

Every partitioning rationale must cite a Context path or repository evidence within it. Architecture unconfirmed by Context must not become a fact inside a Task.

## Partitioning steps

1. **Map boundaries:** list entry points, modules, shared owners, data stores, external dependencies, and platform branches.
2. **Find behavioral chains:** group a shared call chain, data flow, ownership, or lifecycle into a candidate domain.
3. **Split at verifiable boundaries:** let one Task answer a concrete correctness or impact question, with clear entry points and exclusions.
4. **Preserve seams:** record producer/consumer, caller/callee, owner/borrower, or write/read endpoints for every cross-Task boundary.
5. **Control size:** large repositories usually use 4–10 main Tasks; small repositories may need fewer. Do not force splitting or merging to reach a target count.
6. **Check coverage:** map every in-scope Context fact to at least one Task. Every important boundary has at least one primary Task and one reconciliation input.

Files serve as entry points or Evidence paths, not as standalone audit units. Equal directory-based partitions commonly miss cross-layer issues.

## Priority heuristics

Prioritize domains combining several of these characteristics:

- Multiple callers, multiple platforms, or shared core.
- Lifecycles, threads, ownership, or asynchronous callbacks crossing boundaries.
- Data persistence, migration, permission-model state, or external side effects.
- High impact, insufficient evidence, or unclear contracts identified by Context.
- Missing executable verification entry points.

These heuristics determine reading order only. They do not establish a Finding or predetermine category or severity.

## Task contract

Every Task contains the following. Structured mode generates `tasks/Axx.md` from the checkpoint; older `tasks/Axx-*.md` files may continue to be maintained:

| Field | Requirement |
|---|---|
| Task ID / state | Stable ID and checkpoint-persistable state |
| Scope | Behavioral domain and in-scope paths |
| Partitioning basis | References to Context facts and evidence |
| Entry points | Minimum starting locations |
| Important boundaries | Both seam endpoints and related tasks |
| Exclusions | Explicitly uncovered scope |
| Evidence strategy | Search → trace chains → focused reading / behavioral validation |
| Dependencies | Prerequisite tasks, shared evidence, and unanswered questions |
| Audit snapshot | Current code and Context baseline |

Recommended IDs are `A01`, `A02`, and so on. Names describe behavioral domains, such as `A03-session-lifecycle`, rather than technology-stack names alone. Task titles and questions describe actual engineering behavior, such as workspace paths and operation boundaries or execution preflight and state changes, rather than copying Context risk labels without a concrete mechanism. Default Chinese artifacts use natural Chinese names; use English-only natural language only when `output_language=en`.

## Coverage checks

After generating Tasks, check:

- Whether any Context module or entry point has no owner.
- Whether any runtime/platform/data boundary is scanned from only one side.
- Whether shared core covers all principal callers.
- Whether build variants, background execution, or exceptional paths were unintentionally excluded.
- Whether two Tasks may cover related observations; keep their candidates separate until the identity gate completes.
- Whether any Task is so large that it requires loading unrelated files in bulk.

Adjust partitions or identify blockers when coverage has gaps. Adding generic checklists does not fill those gaps.
