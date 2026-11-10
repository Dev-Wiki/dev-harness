# BUGFIX_GUIDE

[English](BUGFIX_GUIDE.en.md) | [简体中文](BUGFIX_GUIDE.md)

Use this guide to standardize bugfix harness records and reduce the context AI and people must read to reproduce and diagnose an issue.

## 1. Bug description template

Record at least these fields for every bug:

- **Title:** one sentence describing the issue.
- **Observed behavior:** actual errors, unexpected behavior, logs, or screenshots.
- **Expected behavior:** what correct behavior looks like.
- **Impact:** affected interfaces, pages, modules, users, or environments.
- **First observed:** optional, but recommended.

## 2. Minimum reproduction information

Record the minimum necessary information without unrelated steps:

- **Environment:** versions, OS, devices, network, switches, and accounts.
- **Prerequisite data:** fixtures, seed data, and dependency-service state.
- **Steps:** the smallest ordered sequence that reproduces the issue.
- **Reproduction command:** prefer an executable command when possible.
- **Actual result:** error codes, logs, screenshots, and trace IDs.

## 3. Call-chain records

During diagnosis, preserve at least:

- **Entry point:** interface, event, job, button, timer, or consumer.
- **Key call chain:** only the principal path that causes the issue.
- **Key state:** inputs, outputs, branch conditions, and failure points.
- **Missing signals:** logs, assertions, or instrumentation that are still insufficient.

Use a stable structure:

```text
EntryPoint:
CallChain:
ObservedSignals:
MissingObservability:
RootCauseCandidates:
```

## 4. Regression-test planning

Every repair must answer at least these four questions:

1. Which layer best verifies this issue: `quick`, `bugfix`, or `full`?
2. Which directory or module should contain the test?
3. Where do samples or fixtures come from?
4. Which assertion actually proves the issue is fixed?

### Validation profiles

The authorization mode controls permission to edit and commit. The validation profile determines required evidence. Neither replaces the other:

- `fast`: one low-risk logic repair touching no more than two production files; minimal RED or existing failure evidence, targeted GREEN, necessary compilation, and one diff self-review.
- `standard`: multiple affected verification entry points or medium impact; complete affected `quick / test / bugfix` checks. If the final diff is unchanged, final verification checks only the worktree and diff hash.
- `strict`: security, ABI, concurrency, persistence, permissions, signing, shared infrastructure, cross-repository production dependencies, or uncertain risk; complete all applicable checks within the actual impact scope, with independent review and manual verification as needed.

Assess the profile after confirming the issue boundary and again once the final diff stabilizes. Automatic changes may only raise the profile. Tests, ordinary runners, and documentation do not count as production files; build scripts, generators, shared runners, and release configuration are shared infrastructure. Do not repeat the same command on the same diff without a reason.

Strict does not automatically trigger repository-wide regression. Start with targeted and affected-module checks. Expand to the whole repository only when the user or an applicable project contract explicitly requires it, or a smaller scope has an evidenced coverage gap, and record the reason. Every profile can reuse still-valid evidence. Repair or commit authorization does not authorize deployment-package builds, releases, or deployment. See the [verification rules](../internal/bugfix-flow/verify.md#验证范围与全仓回归).

### Evidence validity and verification gaps

Verification records must bind to the content and actual dependencies at execution time. Changes to code or related tests invalidate affected old evidence. Documentation or unrelated dependency changes may reuse valid execution evidence, but the current complete diff still requires review. Final completion gates check the root cause, RED, required verification, capability-documentation check, review, and final content; same-stage updates and repeated report commands are also subject to the gates.

If objective conditions prevent a required check, record the skip reason, actual blocking evidence, alternative verification, and remaining risk. The final state may be at most `DONE_WITH_CONCERNS`, never passed. An existing failure cannot be erased by entering implement, marking it skipped, or reusing a pass from before the failure. Only a fresh passing execution of the same command / check clears it. The [Auto Fix contract](../auto-fix/SKILL.md) defines fields, permitted reasons, and evidence-reuse rules.

### Capability-documentation check

After the repair passes verification, reconcile the existing capability catalog or equivalent documentation. Complete necessary updates, then record updated / no update required / not applicable and the specific basis. A fix restoring an existing promise normally retains its feature ID and does not increase the feature count. `DocumentationCheck` binds to the current change fingerprint; a missing or stale check blocks successful completion and commit. See [Auto Fix capability-documentation checks](../auto-fix/SKILL.md#61-功能文档检查) for fields and usage.

### Resuming older runs

Auto Fix Schema 3 separates content fingerprints from index state and stores verification dependencies and commit receipts. Migration clears old review and final fingerprints; write-mode runs lose old completion state and require fresh verification and review. Historical plans must not be treated as current passing evidence. Since v1.12.0, the new documentation gate still uses Schema 3. When an old write-mode run lacks a documentation check and already has a successful conclusion or final receipt, recovery returns it to verify to complete the check and reconfirm the final result while preserving still-valid execution evidence.

If an old run has already committed and HEAD differs from its old baseline, inspect the committed changes before starting a new run. Do not fabricate a commit receipt to bypass validation. The current format separately validates exact commits when Git has committed but interruption prevented receipt persistence. See the [Auto Fix state and commit contract](../auto-fix/SKILL.md) for the precise sequence.

## 5. Definition of completion

A bugfix harness has at least:

- Minimal reproduction inputs.
- Call-chain or root-cause evidence.
- An identified regression-test location or manual verification checklist.
- Executable verification commands.
- Minimum requirements for failure records.
- The validation profile, risk rationale, structured verification evidence, and final diff hash.
- The capability-documentation check result for the current change, affected capabilities, and specific basis.
