# Batch execution and document generation

[English](runtime-interface.en.md) | [简体中文](runtime-interface.md)

`runtime.py --help` is the source of truth for commands. This page defines structured inputs, so reading runtime source is usually unnecessary. Older single-item commands remain compatible. Prefer `batch`, `validate-outputs`, and `render-output` for new runs; they do not weaken Finding validation, drift protection, or cross-module gates.

## Commands and inputs

Use the project's confirmed Python entry point for these commands. `<runtime>` is this Skill's runtime.py, and `<fp>` must be the freshly recomputed Context fingerprint. Replace illustrative arguments with actual paths and values.

```text
python <runtime> init --repo <repo> --run-id <run> --context-fingerprint <fp> --scope <scope> --docs-root docs --summary
python <runtime> batch --repo <repo> --run-id <run> --context-fingerprint <fp> --input <batch.json>
python <runtime> render-output --repo <repo> --run-id <run> --context-fingerprint <fp>
python <runtime> status --repo <repo> --run-id <run> --summary
python <runtime> validate-outputs --repo <repo> --run-id <run> --input <paths.json>
```

- A `batch` input includes at least one of `tasks`, `findings`, or `document`. Arrays are nonempty and IDs of the same kind are unique. One Revision is written only after the whole input validates. Any invalid item prevents the entire batch from persisting; drift still persists STALE. Transactions exclude long-running tests / source reads and do not span the gate at Task start.
- New commands return summaries by default. Add `--summary` to older `init/resume/status/checkpoint/upsert-finding/checkpoint-cross-module/complete` commands rather than returning the entire state to the model each time.
- `--input` accepts a UTF-8 JSON file, including BOM, or reads stdin with the default `-`. Put input files in Git-private run storage or a temporary directory; write once with a patch tool and update incrementally per task. Do not repeatedly nest JSON inside PowerShell / JavaScript command strings.
- `validate-outputs` accepts a valid JSON array such as `["Dashboard.md", "Report.md"]`. Paths are relative to the **audit root**, without a `docs/audit/` prefix. Validate the whole set in one process, never one process per path. `render-output` already validates every output it generates; do not validate that same set individually again.
- Revalidate when code, Context, or HEAD changes between state batches. Reusing an old `<fp>` is not Context recomputation.
- Read a batch summary after its synchronous call completes. If the tool returns running, wait for completion; a yield is not success.
- Keep a single state writer per run. Batch prevents partial publication when that batch fails validation; it does not provide multiprocess transactions or state locking.

## Data contract

A Task's `checkpoint` stores its plan, result, and recovery position. Each update replaces the entire checkpoint. `document` merges top-level fields, while `findings` merges by ID. For a new empty run, register document metadata and tasks first, then render compact in-progress artifacts; prefilled result templates are unnecessary.

The following illustrates one task's data shape. Replace prose with actual observations; an example is not audit evidence. This English example selects `output_language: "en"`; `zh-CN` selects Chinese headings and labels.

```json
{
  "document": {
    "output_language": "en",
    "context": ["Actual sources and scope in README.md, ARCHITECTURE.md, and HARNESS.md"],
    "discoverability": {
      "hub": "docs/README.md",
      "status": "docs-refresh-required",
      "handoff": "dev-harness-docs adds a concise audit/Report.md entry to docs/README.md"
    },
    "focus": "A01 entry points and error propagation",
    "summary": "Scope, current conclusions, and untested platforms; no safety claim for unchecked scope"
  },
  "tasks": [{
    "task_id": "A01",
    "status": "in-progress",
    "checkpoint": {
      "title": "Entry points and persistence",
      "scope": "Task scope and behavioral questions to answer",
      "basis": "Context sections and evidence",
      "entry_points": ["app.py:1"],
      "boundaries": ["Entry point → state write; both ends and related Tasks"],
      "exclusions": "Explicit exclusions and reasons; state none when absent",
      "strategy": "Entry-point search, call-chain tracing, counter-evidence, and necessary behavioral validation",
      "dependencies": "None",
      "result": {
        "coverage": "Actually checked entry points, chains, and both boundary ends",
        "evidence": ["path:line or command + actual observation"],
        "candidates": "Local IDs, claims, states, and AUD IDs; explain the result even without candidates",
        "counter_evidence": "Actually checked alternate paths and guards",
        "gaps": "Unchecked scope or blockers; state none when absent",
        "cross_module": "Both boundary ends, related tasks, and questions awaiting reconciliation"
      }
    }
  }]
}
```

A completed / blocked Task's result contains all six result fields above. Its plan also contains title/scope/basis/entry_points/boundaries/exclusions/strategy. Fill `document.summary` before completing reconciliation, explaining conclusions and coverage limits. Bodies may be strings, lists, or objects. AI owns body language; the renderer translates only fixed headings and states. Represent complex boundary evidence as objects / lists instead of repeating the same conclusion across documents.

Findings follow [finding-contract.md](finding-contract.en.md). Each `findings` item is an existing `upsert-finding` object containing `id/status/severity/category/summary/claim/evidence_paths_lines/relevant_call_chain_data_flow/counter_evidence_checked/risk_impact/confidence/suggested_next_action/snapshot`, plus `source_task`, aliases, root cause, owner, repair boundary, and identity evidence where available. `snapshot` uses the init Snapshot fingerprint. `evidence_paths_lines` uses `{"path":"app.py","lines":"1-3"}` or `{"command":"...","observation":"..."}`. Confirmed Findings keep every original gate. Resolved Findings require revalidated repair evidence rather than a renamed state.

A post-repair run imports the original issue first, then submits validation results, with actual verification performed between the two batches:

```json
{"findings":[{"id":"AUD-001","status":"stale","source_run_id":"original-run"}]}
```

```json
{"findings":[{"id":"AUD-001","status":"resolved","resolution":{
  "snapshot":"<current post-repair Snapshot fingerprint>",
  "change_summary":"<actual repair and basis>",
  "verification_status":"passed",
  "evidence_paths_lines":[{"command":"<actual verification command>","observation":"<post-repair observation and exit result>"}]
}}]}
```

`source_run_id` must resolve to a historical confirmation record for that same ID in an original run of this repository. Import preserves the original claim and snapshot. A nonexistent issue, old snapshot, failed check, or empty evidence cannot establish resolution. The original and post-repair snapshots are retained separately in Finding `snapshot` and `resolution.snapshot`.

## Writing and completion

1. Validate the worktree before each Task. Once results exist, submit the checkpoint and related Findings in the same batch. When the batch validates internally, do not immediately repeat an independent verify-workspace call. Save available evidence during work instead of reconstructing it after the final response.
2. After registering every result, perform semantic reconciliation under cross-module-review.md. Persist boundaries, contradictions, identity, complete chains, and gaps with `checkpoint-cross-module ... --review-status completed --evidence-json <JSON> --summary`. Later Task, Finding, or document changes invalidate that review.
3. `render-output` generates Dashboard, Findings, Report, `tasks/A01.md`, `results/A01.md`, and similar files from state. Only Dashboard contains the complete Snapshot table; other files reference it. Finding bodies appear only in Findings. Code owns the fixed UI; AI writes investigation results only.
4. After checking generated content, mutual links, and coverage, run `complete ... --summary`, then `render-output` once more to show completion. For runs with document metadata, complete checks that this Revision has been rendered and outputs are unchanged. State must not say complete while disk still holds an initialization skeleton.
5. If the final render fails, explicitly report incomplete documentation closure instead of completed artifacts. Rendering does not change Tasks, Findings, or CrossModuleReview and does not trigger another review.

Output is restricted to `<docs-root>/audit/**`. Byte-identical generated files are not rewritten. Each file is replaced atomically. Private `rendered.json` stores hashes and the rendered Revision so interruption can be retried. The output set is not a cross-file atomic transaction; failure yields no completion receipt for the current Revision.

The renderer refuses to overwrite differing handwritten documents, other runs' artifacts, or externally modified outputs from the current run. Read existing artifacts and maintain them incrementally under the established templates, or explicitly preserve and migrate them before enabling generation. Do not delete user audit documents to make rendering pass. An older resumed run without document metadata can continue its handwritten workflow; the old API does not force migration.
