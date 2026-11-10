# dev-harness documentation

[English](README.en.md) | [简体中文](README.md)

Start with the [English project overview, installation, and quick start](../README.en.md). This index uses the existing `docs/` root and links to the documents that own each topic. **Chinese** means the linked document has not yet been translated; an English link label does not indicate an English guide.

## Use dev-harness

| Goal | Read | Language |
|---|---|---|
| Install the skills and try a first task | [Project overview and quick start](../README.en.md) | English |
| Connect an existing project | [Client project onboarding](CLIENT_PROJECT_ONBOARDING.md) | Chinese |
| Deliver a feature or audit and repair a codebase | [End-to-end workflow](WORKFLOW.md) | Chinese |
| Confirm build and verification commands | [HARNESS guide](HARNESS_GUIDE.md) | Chinese |
| Reproduce and fix a known bug | [Bugfix guide](BUGFIX_GUIDE.md) | Chinese |
| Check current support and limitations | [Capability catalog](CAPABILITIES.md) | Chinese |
| Execute prepared Planning Tasks | [Runtime installation and usage](https://github.com/Dev-Wiki/dev-harness-runtime/blob/main/README.en.md) | English |
| Understand the Skills Bundle / Runtime boundary | [Runtime integration](WORKFLOW.md#6-runtime-协作边界) | Chinese |
| Supply structured audit evidence | [Audit runtime interface](../codebase-audit/references/runtime-interface.md) | Chinese |

English documentation currently covers discovery, installation, and navigation. See [language coverage](../README.en.md#language-coverage) for report-language support and the Chinese structural labels still required by Context and Runtime Planning.

## Maintain and verify

| Goal | Read | Language |
|---|---|---|
| Run this repository's checks and understand their evidence | [Testing](TESTING.md) and [HARNESS](../HARNESS.md) | Chinese |
| Follow repository Git and release policy | [Git workflow](GIT_WORKFLOW.md) | Chinese |
| Inventory or reconcile current capabilities | [Capability maintenance](../dev-harness-docs/references/capability-maintenance.md) | Chinese |
| Review released changes | [Changelog](../CHANGELOG.md) | Chinese |

## Scope and design

- [V1 / VNext and V2 boundaries](V1_V2_BOUNDARIES.md) (Chinese): current scope and non-goals.
- [V2 backlog](V2_BACKLOG.md) (Chinese): future candidates, without a delivery commitment.
- [Chinese documentation index](README.md): also links to the implemented VNext design record.

## Documentation maintenance

The Chinese project overview and specialist documents remain the source for changing project facts. Update the affected English overview and navigation in the same change when installation, skill scope, or Runtime integration changes. Mark untranslated guides explicitly. Keep current capability facts in the catalog, task state in Planning, and release history in the changelog; indexes provide links rather than duplicate those records.
