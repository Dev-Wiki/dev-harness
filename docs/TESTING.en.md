# TESTING

[English](TESTING.en.md) | [简体中文](TESTING.md)

This document defines layered verification for the bugfix harness. The goal is to make clear to AI and human readers what each command proves, rather than simply running more tests.

## Verification of the dev-harness repository itself

This repository uses Python's standard-library `unittest`. The full regression entry is:

```bash
python -m unittest discover -s tests -v
```

Also run `git diff --check` before release. Codebase Audit runtime, installation/export/release integrity, and VNext cross-Skill contracts are included in the full regression.

Key boundaries are covered by these tests:

- Skill release package: the archive contains only complete `skills/` resources and release documentation; resources match exported artifacts and Skill versions agree. Chinese and English installation instructions contain the current version, and language-switch and other document links resolve inside the package. After extracting and copying, Context scanning and the Auto Fix / Audit command entries execute in an isolated Python environment. See `tests/test_install.py`.
- Context evidence integrity: workspace source, hidden project configuration, and complete file contents are included in fingerprints; excluded directories cannot serve as AI evidence, and Unknown, low-confidence, or empty claims are not backfilled. See `tests/test_context_evidence_integrity.py`.
- Context write protection: human edits, file replacement, permission changes, or link changes after preview prevent overwriting; missing files are created exclusively, write errors retain the original, and encoding, line endings, and permissions are preserved. See `tests/test_context_write_safety.py`.
- Policy discovery: reuse the authoritative `doc/` or `docs/` root and preserve valid index priority; conflicting or out-of-scope links must be rejected or sent for human handling. See `tests/test_contract_discovery.py`.
- Auto Fix lifecycle: dependency changes invalidate evidence, documentation changes may reuse evidence appropriately, terminal states are rechecked, older states are reverified, staging and commit recovery are exact, Git text/permission semantics are respected, and objective skips or known failures cannot be hidden. See `tests/test_auto_fix_lifecycle.py`.
- Auto Fix capability-documentation gate: missing or stale checks, invented inapplicability, unchanged documents claimed as updated, and invalid catalog paths or IDs prevent successful closure. Valid updates, no-update decisions, and older-run revalidation are verified separately. See `tests/test_auto_fix_documentation.py`.
- Audit resolution evidence: import real previously confirmed problems, verify them on a new snapshot, retain the original confirmation basis, enforce rendering/completion gates, and invalidate again on subsequent drift. See `tests/test_audit_resolution.py`.

Planning documents and templates are checked by `tests/test_planning_contract.py` contract tests. When changing their maintenance workflow, also rehearse “complete → reopen → complete again” in a temporary repository according to the [Skill](../planning/SKILL.md), changes to same-named dirty files, and checker exit results for no duplicates, duplicates, and read errors. Text contract tests do not replace these behavioral checks.

Capability-maintenance behavioral verification uses an independent temporary project: perform an initial full inventory, apply actual capability and behavior changes followed by an incremental update, then run full reconciliation twice against the same implementation. Check stable old IDs, duplicate detection for new capabilities, correct counts, no promotion of unimplemented candidates, real evidence types, and complete coverage conclusions. Blocked coverage must not overwrite the last complete inventory record. This is an Agent workflow that inventories capabilities from implementation and evidence, not a static-code CLI that automatically recognizes every capability. See [Capability maintenance](../dev-harness-docs/references/capability-maintenance.en.md).

## 1. Layer naming conventions

Retain at least three verification layers:

- `test:quick`
  The fastest feedback layer, verifying the most important basic correctness of the current change.
- `test:bugfix`
  Verification specific to the current bug, covering the corresponding scenario.
- `test:full`
  Full regression, used when explicitly required or when smaller verification scopes cannot cover the risk.

For non-Node.js projects, map these to another command form, such as:

- `make test-quick`
- `pytest -m quick`
- `dotnet test --filter Quick`

Fixed responsibilities matter more than command names.

## 2. What each layer must prove

### `test:quick`

- The current change has not immediately broken a basic path.
- Feedback is as fast as practical.
- It supports frequent local iteration.

### `test:bugfix`

- Explicitly cover the input, state, or interaction involved in this bug.
- Assertions must target the bug directly rather than nearby behavior that looks similar.
- Keep the test after the fix.

### `test:full`

- Cover mainline regression risks.
- Run when explicitly requested by the user, required for the current task by the project contract, or when evidence shows smaller verification sets are insufficient; committing alone does not trigger full regression.
- Speed is not the primary requirement, but the boundary must be clear.

Default to focused checks and affected-module verification, determining scope along dependencies and interfaces. A `strict`, high-risk, or shared-infrastructure classification does not automatically mean repository-wide regression. Before running it, record the source of the requirement or the coverage gap, and why a smaller scope is insufficient. Stop expanding once coverage is sufficient, and reuse results whose dependency, environment, and validity requirements still hold. See [Verification details](../internal/bugfix-flow/verify.md#验证范围与全仓回归) for the complete decision rules.

## 3. Minimum failure output

For a failure at any layer, show at least:

- The executed command
- The failing case name
- Input sample or context identifier
- Expected result
- Actual result
- Error code, exception stack, log, or trace ID

## 4. Recommended implementation

When onboarding a project to the harness, prioritize:

1. Define a unified entry for each of quick / bugfix / full.
2. Allow bugfix cases to run independently.
3. Make failure output readable.
4. Document these commands in README or developer documentation.

## 5. Verification evidence requirements

Every claim that tests passed, a fix is complete, or the harness works must rest on evidence that remains valid for the current change:

- Execute new verification against current content. When reusing an earlier execution, check its dependency bindings and obtain new evidence for affected checks.
- Inspect the complete output.
- State the passing count or exit code.
- Re-review the entire current diff and reconcile the workspace with final content before completion.

Record unexecuted checks as verification gaps; do not count them as passes. Objective Auto Fix skips allow only `DONE_WITH_CONCERNS`; a known failure can be cleared only by a new passing result for that check. See the [Auto Fix contract](../auto-fix/SKILL.md) for evidence binding, reuse, and terminal-state rules.

Do not claim completion without evidence.
