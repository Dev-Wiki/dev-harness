# Finding registry contract

[English](finding-contract.en.md) | [简体中文](finding-contract.md)

A Finding is a traceable, falsifiable engineering-defect claim bound to a repository snapshot. It is not a code-smell list or generalized advice.

## State machine

```text
candidate → needs-verification → confirmed
         ↘ rejected
confirmed → stale → confirmed | rejected
New run imports historical confirmed / stale(previous_status=confirmed) → stale → resolved
```

- `candidate`: local evidence warrants investigation, but verification gates have not passed.
- `needs-verification`: a clear Claim still lacks a key chain, counter-evidence check, or runtime evidence.
- `confirmed`: code or runtime evidence under the current Snapshot supports the impact mechanism, with counter-evidence checked.
- `rejected`: evidence disproves the Claim, existing protection applies, or actual semantics differ.
- `stale`: Snapshot / Context drift means old evidence no longer represents current facts.
- `resolved`: post-repair revalidation under a new Snapshot establishes the issue no longer holds. Audit itself does not repair it.

A search hit cannot jump directly to `confirmed`. Task-local candidates may use `Axx-Cnn`; global Registry entry assigns stable `AUD-nnn` IDs. Only after the Finding identity gate proves a shared root cause may multiple observations retain the earliest ID and record aliases. Keep them separate until the gate is complete.

## Required fields

Every Registry Finding contains:

| Field | Requirement |
|---|---|
| ID / state | Stable `AUD-nnn` and a state from the state machine |
| Severity | P0/P1/P2/P3, based on impact and urgency rather than confidence |
| Category | Free-form classification, unrestricted by technology-stack enums |
| Summary | One sentence describing an observable issue |
| Claim | A mechanism statement that counter-evidence can falsify |
| Evidence | Repository-local `path:line`, runtime output, or reviewable artifacts |
| Call chain / data flow | Relevant entry points, boundaries, responsibilities, and lifecycle |
| Counter-evidence checked | Counterexamples, protections, alternate paths, and other implementations searched |
| Risk / impact | Trigger conditions, affected subjects, and consequences |
| Confidence | High / medium / low, with evidence gaps explained |
| Suggested next action | Verification or handoff, without automatic execution |
| Audit snapshot | Run ID, baseline SHA, Context fingerprint, and last verification location |
| Source task | Task / result links and deduplication aliases |

`confirmed` cannot have low confidence. High severity does not establish sufficient evidence; a large potential impact without proof remains `needs-verification`.

## Verification gates

Validate each candidate in order:

1. **Claim:** explain which behavior is wrong, under what conditions, and why.
2. **Chain:** trace caller/callee, read/write, producer/consumer, owner/borrower, or lifecycle. Every arrow requires corresponding call, dispatch, or data-transfer evidence and an explicit relationship type. List prerequisites such as object creation, initialization, and state preparation separately; do not join them with later possible calls into a continuous call chain. If tracing reaches a public interface without finding its higher-level caller, state the verified boundary and unknown entry point. Do not infer automatic product triggering, or reject a defect already established under valid calls merely because no upper caller was found.
3. **Positive Evidence:** provide code or runtime evidence for the mechanism at precise locations.
4. **Counter-evidence:** inspect guards, cleanup paths, alternative implementations, platform branches, exceptional paths, and tests.
5. **Impact:** establish reachable impact rather than theoretical possibility alone.
6. **Freshness:** verify Snapshot and Context have not drifted.
7. **Reconciliation:** check whether other Tasks duplicate, contradict, extend, or change severity.

Without code or runtime evidence, a candidate cannot be confirmed. Missing key steps leave it `needs-verification`. A static search finding no references does not alone establish dead code; one location lacking a guard does not establish an unguarded complete call chain.

## Evidence quality

Prefer minimal, reviewable evidence:

- `path:line` with relevant symbols and a behavioral summary.
- A caller → boundary → callee chain.
- An input/state → transformation → sink data flow.
- A reproducible command, test, or log summary with exit status.
- Counter-evidence search scope and results.
- The Snapshot fingerprint at collection time.

Do not copy large source excerpts or write only checked. Generated code, dependencies, caches, and unstable temporary logs cannot be the sole evidence. Redact nonpublic configuration values, personal data, and private machine paths before including them.

## Deduplication rules

Deduplicate by root cause and repair boundary rather than module, mechanism name, or error symptoms. Keep candidates separate until evidence establishes all four conditions:

1. The same root cause.
2. The same owner / responsibility boundary.
3. Substantially the same repair boundary.
4. One repair can reasonably resolve the observations together.

If any condition is unproven, retain separate Findings and carry their pending relationship into Cross-module Reconciliation. The same module, function, configuration parser, or broad mechanism does not establish Finding identity.

Specific rules:

- One owner / lifecycle error causing several platform symptoms: one Finding with multiple impact areas.
- Different root causes producing the same error message: separate Findings.
- New evidence expanding impact: update Scope / Evidence / Severity on the existing ID.
- Conflicting conclusions: downgrade to `needs-verification` until cross-module review resolves them.

For example, returning a partial workspace after a missing base and infinitely recursing through a cyclic base begin as separate Candidates. Merge them into one `AUD-nnn` only when cross-module review proves matching root cause, ownership, repair boundary, and single-repair effect.

## Staleness and resolution

On HEAD, branch, dirty fingerprint, Context, or scope drift, mark affected Findings `stale` and retain the old Snapshot. Do not copy them unchanged into the current report's confirmed section. After an external repair, use `resolved` only after relevant verification and reconciliation run again under a new Snapshot.

Register resolution evidence at runtime in this order:

1. Initialize a post-repair run. Import an actually registered confirmed Finding, or one made stale from confirmed, from the original run using `id/status=stale/source_run_id`. Do not directly create resolved or import a candidate as a confirmed issue.
2. Import preserves the original claim, evidence, and `snapshot`; `source_run_id` cannot be replaced. Read the original state without restoring its old worktree.
3. After revalidation, submit `status=resolved` and `resolution` containing the current new `snapshot`, repair `change_summary`, `verification_status=passed`, and nonempty `evidence_paths_lines`. Failed, skipped, or missing checks do not establish resolution.
4. The update invalidates previous cross-module review; publish only after a new review completes. Rendering and complete recheck resolution evidence. Later worktree drift also makes resolved stale, preserving `previous_status=resolved`.

The original Finding's `snapshot` is historical evidence; `resolution.snapshot` is post-repair verification. They must differ. If original Git-private state is unavailable, report a source-evidence gap rather than fabricate historical confirmation. See [runtime-interface.md](runtime-interface.en.md) for fields and examples.

Runtime records `previous_status` and `stale_reason`; normal Finding inputs must not set them. Resolution must not delete or alter original confirmation evidence; post-repair evidence goes only in `resolution`. Older reports remain overwrite-protected. Preserve and migrate them under project authorization before establishing the new snapshot, or continue the existing handwritten workflow. Do not delete old reports to make rendering pass.

## Handoff contents

A handoff contains only Finding ID, Claim, Snapshot, Evidence, impact, checked counter-evidence, verification gaps, suggested acceptance, and the target Skill. It does not automatically authorize code repair, planning, document changes, command configuration, commit, or PR creation.
