# dev-harness documentation

[English](README.en.md) | [简体中文](README.md)

This directory is dev-harness's only project documentation root. The root [README](../README.en.md) introduces the project; this index organizes documents by reader task without duplicating specialist details. Linked specialist documents are currently **Chinese**; the English overview and index are identified below.

## Use dev-harness

1. [End-to-end workflow](WORKFLOW.md): start from the shared Project Contract and follow feature delivery or the codebase audit / repair loop.
2. [Client project onboarding](CLIENT_PROJECT_ONBOARDING.md): install the skills, initialize Context, and confirm the contracts in a real project.
3. [HARNESS guide](HARNESS_GUIDE.md): maintain and use the build / test / quick / bugfix / full verification interfaces.
4. [Bugfix guide](BUGFIX_GUIDE.md): analyze and repair known bugs through evidence-driven workflows.
5. [English README](../README.en.md) and [English documentation index](README.en.md): project overview, quick start, and guide navigation with language status.
6. [Runtime integration boundary](WORKFLOW.md#6-runtime-协作边界): prepare the engineering contracts, then use [dev-harness-runtime](https://github.com/Dev-Wiki/dev-harness-runtime/blob/main/README.en.md) (English overview) to execute Planning Tasks automatically.
7. [Audit batch interface](../codebase-audit/references/runtime-interface.md): structured evidence inputs, compact document generation, and completion gates.

## Maintain and verify

- [Testing](TESTING.md) and the [repository verification contract](../HARNESS.md): run checks, understand coverage, and verify installation / release artifacts.
- [Git workflow](GIT_WORKFLOW.md): this repository's branch, commit, tag, changelog, and release-message contract.
- [Capability maintenance](../dev-harness-docs/references/capability-maintenance.md): initial full inventory, incremental updates, and repeatable full reconciliation.
- [Changelog](../CHANGELOG.md): changes in released versions.

## Current scope, design, and future planning

| Document | Sole responsibility | Status |
|---|---|---|
| [Capability catalog](CAPABILITIES.md) | Capabilities by use case, support, limitations, and entry points; technical evidence available on demand | Authority for current capabilities |
| [V1 / VNext and V2 boundaries](V1_V2_BOUNDARIES.md) | Version boundaries, explicit non-goals, and V1 completion criteria | Authority for version scope |
| [VNext improvements and Codebase Audit design](dev-harness%20VNext%20%E4%BC%98%E5%8C%96%E4%B8%8E%20Codebase%20Audit%20%E8%AE%BE%E8%AE%A1%E6%96%B9%E6%A1%88.md) | v1.8.0 design rationale, tradeoffs, and implementation-stage constraints | Implemented design record |
| [V2 backlog](V2_BACKLOG.md) | Candidates beyond current scope and the conditions for starting them | Candidate pool, without a roadmap commitment |

These documents answer what is supported now, the current version's boundaries, why it was designed this way, and what might come next. Each document owns its changing facts; other entry points only link to it.

## Documentation maintenance boundaries

- Root READMEs contain an overview and entry points rather than deep design details.
- Keep Chinese and English READMEs aligned section by section. Do not omit workflows, examples, commands, version notes, or documentation routes from one language. When either version changes, check and update its counterpart.
- When installation, Skill scope, or Runtime integration changes, update the affected English overview and navigation in the same change. Mark untranslated guides explicitly. The old `README_EN.md` entry is a compatibility redirect only.
- Current behavior is established by code, tests, the relevant Skill / reference, and verified commands.
- Completed implementation plans are no longer maintained as active documents; Git preserves their history.
- Codebase Audit owns `<docs-root>/audit/` content in target projects; Docs only manages navigation, links, and archiving.
- Planning owns `<docs-root>/plan/` content and task lifecycle archives in target projects; Docs governs placement, navigation, and links without copying or rewriting task state.
