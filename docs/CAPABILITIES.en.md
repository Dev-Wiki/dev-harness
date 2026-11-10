# dev-harness capability catalog

[English](CAPABILITIES.en.md) | [简体中文](CAPABILITIES.md)

dev-harness helps teams keep project rules consistent, arrange development tasks, verify deliveries, and maintain documentation as projects change. Find a capability by goal, then expand its technical evidence when needed.

This file is the authoritative maintenance document for currently supported capabilities, covering this repository's eight engineering assistants (Skills) and installation/distribution. [Runtime](https://github.com/Dev-Wiki/dev-harness-runtime/blob/main/README.en.md) owns its automatic execution, recovery, and platform capabilities; they are not counted here. See [V2 Backlog](V2_BACKLOG.en.md) for future candidates, [Scope](V1_V2_BOUNDARIES.en.md) for version boundaries, and [CHANGELOG](../CHANGELOG.en.md) for version changes.

## Quick lookup

| I want to | See |
|---|---|
| Install or share with colleagues | [Installation and distribution](#installation-and-distribution) |
| Help the assistant understand the project | [Understand and onboard projects](#项目上下文) |
| Find, update, and inventory project documents | [Maintain documentation and capability catalogs](#文档治理) |
| Split requirements into tasks that can be handed off | [Arrange development tasks](#项目规划) |
| Establish which builds and tests to run | [Build and test](#验证命令) |
| Commit and prepare release notes under project policy | [Commit and release](#git-工作流) |
| Diagnose and repair a known bug | [Bug analysis and repair](#auto-fix) |
| Systematically audit engineering problems in an existing project | [Audit existing projects](#codebase-audit) |
| Organize lessons from a task | [Task retrospectives](#显式复盘) |

## Get started

After installation, describe the goal directly in a coding assistant that supports these Skills. For example:

- Initial inventory: “Inventory all capabilities supported by the current implementation and generate a catalog ordinary users can understand.”
- Incremental update: “Check how this feature or fix affects the capability catalog and complete necessary updates before closure.”
- Full reconciliation: “Reconcile the entire existing capability catalog again, preserving capability IDs and listing changes, pending items, and uncovered scope.”

An existing equivalent capability document is reused. Current implementation and verification evidence determine whether a capability is supported.

## Summary

Repository [VERSION](../VERSION) is `v1.12.1`. This version clarifies ownership of verification scope and project gates, and aligns Runtime automatic-execution handoff requirements; the capability count is unchanged. The table separates the current development version from this release scope. See [CHANGELOG](../CHANGELOG.en.md#v1121--2026-11-09) for version content and [GitHub Releases](https://github.com/Dev-Wiki/dev-harness/releases) for release status.

| Version scope | Supported | Partially supported | Experimental | Deprecated |
|---|---:|---:|---:|---:|
| Current development version (v1.12.1) | 36 | 0 | 0 | 0 |
| This release scope (v1.12.1) | 36 | 0 | 0 | 0 |

Pending and removed items are excluded from supported totals. Categories, tasks, pages, and tests are not counted as capabilities.

## Currently supported capabilities

### Installation and distribution

<a id="ins-001"></a>

#### Install the engineering assistants you need

Install all or selected engineering assistants so different coding tools can use the same project rules.

- **Support status**: Supported
- **Applicability**: Teams using Cursor, Codex, OpenCode, or Antigravity
- **Usage**: [Installation](../README.en.md#install)
- **Limitations**: The installer requires Python 3; each coding tool uses a different installation directory.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `INS-001`
- **Version record**: released: v1.10.0
- **Engineering conditions**: Python 3; POSIX / Windows wrappers
- **Verification method**: automated tests + code evidence
- **Evidence**: [tests/test_install.py](../tests/test_install.py); [install.py](../install.py); [install.bat](../install.bat)
- **Technical details**: Install all or selected skills, with Cursor, Codex, OpenCode, Antigravity, interactive selection, custom targets, and Skill dependency expansion; see [Installation](../README.en.md#install) for the detailed rules.

</details>

<a id="ins-002"></a>

#### Package and distribute engineering assistants offline

Create a portable package containing the assistants and required resources so colleagues can extract and copy them to install.

- **Support status**: Supported
- **Applicability**: Teams needing offline installation, centralized distribution, or release-package maintenance
- **Usage**: [Installation](../README.en.md#install)
- **Limitations**: The portable package contains engineering assistants and runtime resources; source code and repository maintenance documents are supplied in the source archive.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `INS-002`
- **Version record**: released: v1.10.0; corrected: v1.11.4; Skill-specific release package: v1.11.8
- **Engineering conditions**: Maintainer releases and offline distribution
- **Verification method**: automated tests + code evidence
- **Evidence**: [tests/test_install.py](../tests/test_install.py); [install.py](../install.py); [release.py](../release.py)
- **Technical details**: Export a portable `bundle/` atomically, preserving previous artifacts on failure. The versioned zip contains ready-to-use skills, their runtime resources, standalone Chinese and English installation instructions, VERSION, and CHANGELOG; extract and copy to install. See [Installation and release entry points](../README.en.md#install).

</details>

<a id="项目上下文"></a>

### Understand and onboard projects

<a id="ctx-001"></a>

#### Collect the real project structure and entry points

Read repository files and project configuration to collect verifiable material for understanding the project.

- **Support status**: Supported
- **Applicability**: Development teams onboarding a new project or revisiting an existing one
- **Usage**: [Client project onboarding](CLIENT_PROJECT_ONBOARDING.en.md)
- **Limitations**: Dependency and cache directories are excluded. Incomplete material is reported explicitly and cannot establish a complete project picture.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `CTX-001`
- **Version record**: released: v1.10.0; corrected: v1.11.7
- **Engineering conditions**: A readable local repository, not limited to built-in Profiles; dependency and cache directories remain excluded
- **Verification method**: automated tests + contract evidence
- **Evidence**: [tests/test_context_cli.py](../tests/test_context_cli.py); [tests/test_context_evidence_integrity.py](../tests/test_context_evidence_integrity.py); [context/SKILL.md](../context/SKILL.md)
- **Technical details**: `evidence` emits a generic repository inventory, analysis-field contract, truncation status, and fingerprints of complete file contents, covering workspace source and hidden project configuration; see the [Context contract](../context/SKILL.md).

</details>

<a id="ctx-002"></a>

#### Create the project documents needed for initial onboarding

Create the project overview, architecture, assistant rules, and verification documentation when the project is not yet prepared.

- **Support status**: Supported
- **Applicability**: Projects adopting the engineering assistants for the first time
- **Usage**: [Client project onboarding](CLIENT_PROJECT_ONBOARDING.en.md)
- **Limitations**: Existing files with the same names are preserved; use refresh to update existing content.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `CTX-002`
- **Version record**: released: v1.10.0; corrected: v1.11.7
- **Engineering conditions**: Initial project initialization
- **Verification method**: automated tests + code evidence
- **Evidence**: [tests/test_context_cli.py](../tests/test_context_cli.py); [tests/test_context_write_safety.py](../tests/test_context_write_safety.py); [tests/test_install.py](../tests/test_install.py)
- **Technical details**: `scan` exclusively creates missing README, AGENTS, ARCHITECTURE, and HARNESS files, rejects link targets, and preserves existing files of the same names. Default AGENTS rules require impact-based verification, justification for repository-wide regression, and reuse of valid evidence. The manual section of a new HARNESS uses a command table with initial `missing` status; candidates do not automatically become executable. See [handoff tests](../tests/test_runtime_handoff.py) for format and preservation of old manual sections, and the [Context contract](../context/SKILL.md) for detailed rules.

</details>

<a id="ctx-003"></a>

#### Update existing project documentation

Refresh agreed automatically detected sections after project changes while preserving manually maintained content.

- **Support status**: Supported
- **Applicability**: Repositories with initialized project documentation
- **Usage**: [Client project onboarding](CLIENT_PROJECT_ONBOARDING.en.md)
- **Limitations**: Only agreed sections are updated. Structural conflicts or changes to a file after preview prevent writing.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `CTX-003`
- **Version record**: released: v1.10.0; corrected: v1.11.4, v1.11.7
- **Engineering conditions**: Initialized projects with valid fixed-heading structure
- **Verification method**: automated tests
- **Evidence**: [tests/test_context_cli.py](../tests/test_context_cli.py); [tests/test_managed_context.py](../tests/test_managed_context.py); [tests/test_context_write_safety.py](../tests/test_context_write_safety.py)
- **Technical details**: `refresh` updates only fixed Markdown sections, preserving human content outside them, encoding, line endings, and permissions. Fixed sections are replaced as complete template blocks. If the Agent preview shows human rules would be lost, skip refreshing that file rather than relying on the Writer to merge them. Invalid structure or target changes after preview reject the write. Non-interactive runs without `--force` only preview. See the [Context contract](../context/SKILL.md).

</details>

<a id="ctx-004"></a>

#### Understand the project from evidence

Use real repository material to identify languages, frameworks, module responsibilities, and entry points, retaining the basis for each judgment.

- **Support status**: Supported
- **Applicability**: Teams asking a coding assistant to understand their project
- **Usage**: [Client project onboarding](CLIENT_PROJECT_ONBOARDING.en.md)
- **Limitations**: Keep unknowns when material is missing or judgments are uncertain; framework conventions are not automatically recorded as facts.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `CTX-004`
- **Version record**: released: v1.10.0; corrected: v1.11.4, v1.11.7
- **Engineering conditions**: Generic repositories and unknown frameworks; offline Profile fallback is separate from the main AI path
- **Verification method**: automated tests + contract evidence
- **Evidence**: [tests/test_context_cli.py](../tests/test_context_cli.py); [tests/test_semantic_analysis.py](../tests/test_semantic_analysis.py); [tests/test_context_evidence_integrity.py](../tests/test_context_evidence_integrity.py)
- **Technical details**: Accept AI semantic analysis bound to confidence and a snapshot fingerprint; citations must be covered by the fingerprint. Reject drifted or truncated evidence. Explicit Unknown, low-confidence, and empty values are not backfilled as facts by Profiles. See the [Context contract](../context/SKILL.md).

</details>

<a id="文档治理"></a>

### Maintain documentation and capability catalogs

<a id="doc-001"></a>

#### Check document discoverability and consistency

Find missing documentation entry points, broken links, duplicated maintenance, and content with unclear ownership.

- **Support status**: Supported
- **Applicability**: Projects with existing documents or preparing to establish documentation
- **Usage**: [Documentation organization rules](../dev-harness-docs/SKILL.md)
- **Limitations**: The checking phase is read-only; organizing or correcting documents requires the corresponding update request.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `DOC-001`
- **Version record**: released: v1.10.0
- **Engineering conditions**: Repositories with existing or planned documentation systems
- **Verification method**: contract tests
- **Evidence**: [tests/test_docs_contract.py](../tests/test_docs_contract.py); [dev-harness-docs/SKILL.md](../dev-harness-docs/SKILL.md)
- **Technical details**: Read-only audit of duplicate ownership, orphaned documents, navigation, and link problems; see the [Docs contract](../dev-harness-docs/SKILL.md).

</details>

<a id="doc-002"></a>

#### Establish a project documentation entry point

Create a minimal documentation hub and necessary maintenance rules so the team knows where material belongs.

- **Support status**: Supported
- **Applicability**: Projects without a complete documentation entry point
- **Usage**: [Documentation organization rules](../dev-harness-docs/SKILL.md)
- **Limitations**: Use the existing project documentation directory rather than creating another directory for the same purpose.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `DOC-002`
- **Version record**: released: v1.10.0
- **Engineering conditions**: Repositories without a complete documentation hub
- **Verification method**: contract tests + resource installation tests
- **Evidence**: [tests/test_docs_contract.py](../tests/test_docs_contract.py); [tests/test_install.py](../tests/test_install.py)
- **Technical details**: Initialize a minimal documentation hub and necessary maintenance rules while resolving and reusing the single `doc/` or `docs/` root; see the [Docs contract](../dev-harness-docs/SKILL.md).

</details>

<a id="doc-003"></a>

#### Organize and refresh documentation navigation

Organize indexes, reading routes, and authoritative document entry points so readers can find current instructions.

- **Support status**: Supported
- **Applicability**: Projects needing to organize existing documentation
- **Usage**: [Documentation organization rules](../dev-harness-docs/SKILL.md)
- **Limitations**: Maintain entry points and ownership only; each authoritative document continues to own its detailed content.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `DOC-003`
- **Version record**: released: v1.10.0
- **Engineering conditions**: Existing documentation systems; Audit navigation is constrained by Snapshot drift boundaries
- **Verification method**: contract tests
- **Evidence**: [tests/test_docs_contract.py](../tests/test_docs_contract.py); [dev-harness-docs/SKILL.md](../dev-harness-docs/SKILL.md)
- **Technical details**: Organize or refresh indexes, navigation, sources of truth, placement rules, and the Audit `Report.md` entry without copying detailed bodies; see the [Docs contract](../dev-harness-docs/SKILL.md).

</details>

<a id="doc-004"></a>

#### Archive obsolete or completed documents

Preserve useful history while directing readers to currently valid documents.

- **Support status**: Supported
- **Applicability**: Projects with obsolete, superseded, or completed documents
- **Usage**: [Documentation organization rules](../dev-harness-docs/SKILL.md)
- **Limitations**: Check exact paths and link impact before moving; historical bodies are not deleted by default.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `DOC-004`
- **Version record**: released: v1.10.0
- **Engineering conditions**: Inactive, completed, or superseded documents
- **Verification method**: contract evidence
- **Evidence**: [dev-harness-docs/SKILL.md](../dev-harness-docs/SKILL.md)
- **Technical details**: After confirming the exact move map and link impact, archive completed or superseded documents and maintain the current authoritative entry; see the [Docs contract](../dev-harness-docs/SKILL.md).

</details>

<a id="doc-005"></a>

#### Sync capabilities and project facts after delivery

After a feature or fix passes verification, check the related documentation, update changed facts, and record the outcome.

- **Support status**: Supported
- **Applicability**: Teams continuously maintaining capability descriptions and engineering documents
- **Usage**: [Capability maintenance](../dev-harness-docs/references/capability-maintenance.en.md)
- **Limitations**: Record only facts supported by current implementation or verification; completion checks became delivery requirements in v1.12.0.
- **Version placement**: v1.10.0 onward; v1.12.0 enhanced

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `DOC-005`
- **Version record**: released: v1.10.0; enhanced in this iteration: v1.12.0
- **Engineering conditions**: Fact synchronization after code or verification changes
- **Verification method**: contract evidence
- **Evidence**: [dev-harness-docs/SKILL.md](../dev-harness-docs/SKILL.md)
- **Technical details**: Sync reusable facts proved by code, configuration, or successful verification into existing sources of truth using a minimal plan; leave unverified items pending confirmation. Before each delivery, record an updated, no-update, or not-applicable outcome and its basis. See the [Docs contract](../dev-harness-docs/SKILL.md).

</details>

<a id="doc-006"></a>

#### Maintain a capability catalog ordinary users can read

Collect current capabilities, applicability, limitations, and usage entry points, with technical evidence available on demand.

- **Support status**: Supported
- **Applicability**: Projects with scattered capabilities, complex support conditions, or a need for reliable inventory
- **Usage**: [Capability maintenance](../dev-harness-docs/references/capability-maintenance.en.md)
- **Limitations**: Reuse an existing equivalent document. Explain support status separately from release status; do not derive capability counts from task counts.
- **Version placement**: v1.10.0 onward; v1.12.0 enhanced

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `DOC-006`
- **Version record**: released: v1.10.0; enhanced in this iteration: v1.12.0
- **Engineering conditions**: Projects where current capabilities are scattered, vary in applicability, or cannot be counted reliably
- **Verification method**: contract tests
- **Evidence**: [tests/test_docs_contract.py](../tests/test_docs_contract.py); [dev-harness-docs/SKILL.md](../dev-harness-docs/SKILL.md)
- **Technical details**: Conditionally establish or maintain a Capability Catalog with stable IDs and separate support status, applicability, version placement, verification method, and evidence. Bind user descriptions and engineering evidence to the same capability item, with technical information expandable on demand. See the [Docs contract](../dev-harness-docs/SKILL.md).

</details>

<a id="doc-007"></a>

#### Inventory supported capabilities and reconcile them repeatedly

Build a capability catalog from actual implementation, then repeat full reconciliation as the project evolves to add omissions, update limitations, and retain pending items.

- **Support status**: Supported
- **Applicability**: Projects establishing or fully reconciling a capability catalog
- **Usage**: [Capability maintenance](../dev-harness-docs/references/capability-maintenance.en.md)
- **Limitations**: The coding assistant follows evidence; this is not a standalone scanning command. Insufficient coverage is explicitly incomplete, and automatic discovery of every unknown capability is not guaranteed.
- **Version placement**: v1.12.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `DOC-007`
- **Version record**: first supported: v1.12.0
- **Verification method**: contract evidence + positive-scenario rehearsal
- **Evidence**: [dev-harness-docs/references/capability-maintenance.md](../dev-harness-docs/references/capability-maintenance.en.md); [dev-harness-docs/assets/capabilities.template.md](../dev-harness-docs/assets/capabilities.template.md)
- **Technical details**: Perform initial full inventory, incremental updates, and repeated full reconciliation in the Agent workflow. Record baseline and coverage, reconcile every existing ID, and retain evidence for pending or removed items. See [Capability maintenance](../dev-harness-docs/references/capability-maintenance.en.md).

</details>

<a id="项目规划"></a>

### Arrange development tasks

<a id="pln-001"></a>

#### Turn requirements into a development Dashboard

Split requirements, prototypes, or product descriptions into a Dashboard and individual tasks for assignment and handoff.

- **Support status**: Supported
- **Applicability**: Teams organizing development by project, release, or milestone
- **Usage**: [Feature-delivery workflow](WORKFLOW.en.md#4-feature-delivery-workflow)
- **Limitations**: Planning organizes tasks; automatic execution requires a separately installed Runtime.
- **Version placement**: v1.11.1 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `PLN-001`
- **Version record**: released: v1.11.1
- **Engineering conditions**: Project-, release-, or milestone-level planning
- **Verification method**: contract tests + resource installation tests
- **Evidence**: [tests/test_docs_contract.py](../tests/test_docs_contract.py); [tests/test_install.py](../tests/test_install.py)
- **Technical details**: Generate one authoritative active Dashboard and individual task details under the same documentation root from requirements, PRDs, prototypes, or reference formats; see the [Planning contract](../planning/SKILL.md).

</details>

<a id="pln-002"></a>

#### Update plans while retaining valid progress

Merge changing requirements by task ID, preserving valid task identities and completion evidence.

- **Support status**: Supported
- **Applicability**: Projects maintaining development plans over time
- **Usage**: [Feature-delivery workflow](WORKFLOW.en.md#4-feature-delivery-workflow)
- **Limitations**: If others have changed the plan or existing work, reconcile those changes before continuing.
- **Version placement**: v1.11.1 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `PLN-002`
- **Version record**: released: v1.11.1; corrected: v1.11.7
- **Engineering conditions**: Existing plans, including monolithic TaskDetails migration
- **Verification method**: contract tests + scenario verification
- **Evidence**: [tests/test_planning_contract.py](../tests/test_planning_contract.py); [planning/SKILL.md](../planning/SKILL.md)
- **Technical details**: Merge refreshed plans by Task ID, preserving valid IDs, local conventions, and evidence-backed completion states. Temporary snapshots check existing dirty content and staging state; check blocks reject duplicate fields as well as read errors. See the [Planning contract](../planning/SKILL.md).

</details>

<a id="pln-003"></a>

#### Archive completed tasks and support reopening

Keep the Dashboard compact while retaining acceptance records for every closure and links to earlier results after reopening.

- **Support status**: Supported
- **Applicability**: Projects with long-term evolution or many tasks
- **Usage**: [Feature-delivery workflow](WORKFLOW.en.md#4-feature-delivery-workflow)
- **Limitations**: Task progress is maintained only on the Dashboard. Closing a reopened task preserves the previous archive rather than overwriting history.
- **Version placement**: v1.11.1 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `PLN-003`
- **Version record**: released: v1.11.1; corrected: v1.11.7
- **Engineering conditions**: Long-running or large plans
- **Verification method**: contract tests + template installation tests + scenario verification
- **Evidence**: [tests/test_planning_contract.py](../tests/test_planning_contract.py); [tests/test_install.py](../tests/test_install.py); [planning/SKILL.md](../planning/SKILL.md); [planning/templates/ArchiveIndex.template.md](../planning/templates/ArchiveIndex.template.md)
- **Technical details**: Shard active tasks by Task ID and maintain cross-task mutable fields only in Dashboard. Completed tasks enter milestone archives; completing a reopened task uses the next unoccupied closure number and preserves older snapshots. See the [Planning contract](../planning/SKILL.md).

</details>

<a id="pln-004"></a>

#### Prepare task instructions that can be handed off

Define each task's goal, scope, acceptance, and stop conditions so a fresh conversation can execute it.

- **Support status**: Supported
- **Applicability**: Teams where planning and development are handled by different people or sessions
- **Usage**: [Feature-delivery workflow](WORKFLOW.en.md#4-feature-delivery-workflow)
- **Limitations**: Keep incomplete packets in planning. Runtime automatic execution also requires its supported plan format, command table, and frozen declaration; include necessary documentation changes and checks in task scope. Ordinary manual plans do not require a Runtime declaration.
- **Version placement**: v1.11.3 onward; v1.12.0 enhanced

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `PLN-004`
- **Version record**: released: v1.11.3; enhanced in this iteration: v1.12.0
- **Engineering conditions**: Projects with planning and execution in different conversations or external workflows
- **Verification method**: contract tests + template installation tests
- **Evidence**: [tests/test_planning_contract.py](../tests/test_planning_contract.py); [tests/test_install.py](../tests/test_install.py); [planning/templates/Task.template.md](../planning/templates/Task.template.md)
- **Technical details**: Use `规划中` (planning) and `待执行` (ready) to distinguish packet completeness. Individual execution packets fix authoritative requirements, code/test entry points, invariants, confirmed decisions, and stop conditions. Declare capability-documentation impact and authorized paths before readiness; acceptance includes the documentation check. Prepare execution commands, scope, acceptance coverage, and archive inputs according to [Runtime handoff](../planning/references/runtime-handoff.en.md); [handoff tests](../tests/test_runtime_handoff.py) check the format examples. See the [Planning contract](../planning/SKILL.md).

</details>

<a id="验证命令"></a>

### Build and test

<a id="cmd-001"></a>

#### Standardize project build and test entry points

Organize existing project commands into consistent build, test, quick-check, bug-verification, and full-verification entry points.

- **Support status**: Supported
- **Applicability**: Projects with real build or verification tools
- **Usage**: [Build and verification guide](HARNESS_GUIDE.en.md)
- **Limitations**: Do not replace the existing toolchain. Retain gaps for unconfirmed commands and describe device-dependent verification separately.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `CMD-001`
- **Version record**: released: v1.10.0; corrected: v1.11.7
- **Engineering conditions**: Projects with existing real build or verification entry points; no separate build may be recorded as N/A
- **Verification method**: contract tests + contract evidence
- **Evidence**: [tests/test_vnext_contract.py](../tests/test_vnext_contract.py); [commands/SKILL.md](../commands/SKILL.md)
- **Technical details**: Map actual repository commands to stable `build / test / quick / bugfix / full` semantics, supporting multiple Platform / Variant records. A gap in one command does not prevent other confirmed records from entering the manual HARNESS section. Newly maintained manual sections use a status-bearing table; migrate old lists from evidence before Runtime handoff, checking unique purposes and literal argv limits. See the [Commands contract](../commands/SKILL.md).

</details>

<a id="git-工作流"></a>

### Commit and release

<a id="git-001"></a>

#### Follow the project's own commit and release rules

Identify existing project policy first; propose a suitable policy only when one is missing.

- **Support status**: Supported
- **Applicability**: Projects using Git
- **Usage**: [Delivery and commit workflow](WORKFLOW.en.md#46-sync-facts-and-state-then-commit)
- **Limitations**: New policy requires confirmation; confirming policy itself does not authorize commits or releases.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `GIT-001`
- **Version record**: released: v1.10.0; corrected: v1.11.7
- **Engineering conditions**: Git repositories; root or policy-ownership conflicts require human selection, and initialization does not authorize Git writes
- **Verification method**: contract tests + Context discovery tests
- **Evidence**: [tests/test_git_workflow_contract.py](../tests/test_git_workflow_contract.py); [tests/test_contract_discovery.py](../tests/test_contract_discovery.py); [git-workflow/SKILL.md](../git-workflow/SKILL.md)
- **Technical details**: Prefer discovering and following repository-owned Git / commit / tag / release / changelog policy, reusing the authoritative doc/ or docs/ root. Propose candidates when absent and initialize defaults after explicit confirmation. See the [Git Workflow contract](../git-workflow/SKILL.md).

</details>

<a id="git-002"></a>

#### Commit exactly the current task's changes

Check file ownership and staged content to commit the current task while preserving other existing changes.

- **Support status**: Supported
- **Applicability**: Development tasks with explicit commit authorization
- **Usage**: [Delivery and commit workflow](WORKFLOW.en.md#46-sync-facts-and-state-then-commit)
- **Limitations**: Separate commit authorization is required; stop on content-ownership conflicts or sensitive files.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `GIT-002`
- **Version record**: released: v1.10.0; corrected: v1.11.7
- **Engineering conditions**: Workflows with explicit user commit authorization; ordinary tasks need not create an Auto Fix Run
- **Verification method**: contract tests + contract evidence
- **Evidence**: [tests/test_auto_fix_contract.py](../tests/test_auto_fix_contract.py); [git-workflow/SKILL.md](../git-workflow/SKILL.md)
- **Technical details**: Stage and commit exactly the authorized files and patches from this task, checking ownership and staging of existing changes and detecting sensitive files, debugging residue, and unrelated changes. See the [Git Workflow contract](../git-workflow/SKILL.md).

</details>

<a id="git-003"></a>

#### Prepare release notes from version records

Generate tag annotations and release notes from the matching changelog version, keeping the format consistent.

- **Support status**: Supported
- **Applicability**: Teams authorized to create tags or prepare release notes
- **Usage**: [Delivery and commit workflow](WORKFLOW.en.md#46-sync-facts-and-state-then-commit)
- **Limitations**: The coding assistant follows the rules. Stop when the matching version record is missing; do not invent release content from commit titles.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `GIT-003`
- **Version record**: released: v1.10.0
- **Engineering conditions**: Repositories with explicit user authorization for tag / release messages
- **Verification method**: contract tests
- **Evidence**: [tests/test_git_workflow_contract.py](../tests/test_git_workflow_contract.py); [git-workflow/SKILL.md](../git-workflow/SKILL.md); [git-workflow/references/default-contract.md](../git-workflow/references/default-contract.en.md)
- **Technical details**: Generate annotated tag annotations and release notes from the matching CHANGELOG version, omitting empty categories in the agreed order; stop when the version is missing. See the [Git Workflow contract](../git-workflow/SKILL.md).

</details>

<a id="auto-fix"></a>

### Bug analysis and repair

<a id="fix-001"></a>

#### Analyze a bug without changing the project

Reproduce the problem, inspect causes and counter-evidence, and report conclusions and remaining evidence gaps.

- **Support status**: Supported
- **Applicability**: Users who want to understand the cause before making changes
- **Usage**: [Bug analysis and repair guide](BUGFIX_GUIDE.en.md)
- **Limitations**: Read-only analysis mode does not enter code-repair or commit stages.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `FIX-001`
- **Version record**: released: v1.10.0
- **Engineering conditions**: Read-only Bug investigation
- **Verification method**: runtime tests + contract tests
- **Evidence**: [tests/test_auto_fix_runtime.py](../tests/test_auto_fix_runtime.py); [tests/test_auto_fix_contract.py](../tests/test_auto_fix_contract.py)
- **Technical details**: `analyze` mode performs read-only reproduction, probes, falsifiable root-cause analysis, and reporting; the runtime prevents entry to write stages. See the [Auto Fix contract](../auto-fix/SKILL.md).

</details>

<a id="fix-002"></a>

#### Fix a known bug and verify the result

Repair the confirmed cause and check before/after results, capability documentation, and the final changes.

- **Support status**: Supported
- **Applicability**: Repositories with a clear reproducible problem and project verification entry points
- **Usage**: [Bug analysis and repair guide](BUGFIX_GUIDE.en.md)
- **Limitations**: Explain verification gaps and check capability documentation before completion.
- **Version placement**: v1.10.0 onward; v1.12.0 enhanced

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `FIX-002`
- **Version record**: released: v1.10.0; corrected: v1.11.7; enhanced in this iteration: v1.12.0
- **Engineering conditions**: Bugs for which reproduction and project verification can be established; objective verification gaps require alternative checks and risk records
- **Verification method**: runtime tests + contract tests
- **Evidence**: [tests/test_auto_fix_runtime.py](../tests/test_auto_fix_runtime.py); [tests/test_auto_fix_lifecycle.py](../tests/test_auto_fix_lifecycle.py); [tests/test_auto_fix_contract.py](../tests/test_auto_fix_contract.py); [tests/test_auto_fix_documentation.py](../tests/test_auto_fix_documentation.py)
- **Technical details**: `fix` mode requires a confirmed hypothesis, RED/GREEN, current dependency evidence, diff-bound review, and final verify. Same-stage updates and repeated reports also rerun the gates; objective skips allow at most DONE_WITH_CONCERNS. DocumentationCheck binds the current diff and is rechecked at final-verify, successful report, and commit. See the [Auto Fix contract](../auto-fix/SKILL.md).

</details>

<a id="fix-003"></a>

#### Commit a repair after authorization

After acceptance passes, commit exactly this repair and retain a recoverable commit record.

- **Support status**: Supported
- **Applicability**: Repair tasks with explicit automatic-commit authorization
- **Usage**: [Bug analysis and repair guide](BUGFIX_GUIDE.en.md)
- **Limitations**: Default fix mode does not commit; push, PR, and release still require separate authorization.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `FIX-003`
- **Version record**: released: v1.10.0; corrected: v1.11.7
- **Engineering conditions**: Auto Fix Runs explicitly authorized to commit; Git text conversion and core.filemode semantics are supported
- **Verification method**: runtime tests + contract tests
- **Evidence**: [tests/test_auto_fix_runtime.py](../tests/test_auto_fix_runtime.py); [tests/test_auto_fix_lifecycle.py](../tests/test_auto_fix_lifecycle.py); [auto-fix/SKILL.md](../auto-fix/SKILL.md)
- **Technical details**: `commit` / `unattended` check staged content and the commit tree exactly and record a recoverable commit receipt. `fix` / `analyze` forbid commits; push / PR / release still require independent authorization. See the [Auto Fix contract](../auto-fix/SKILL.md).

</details>

<a id="fix-004"></a>

#### Resume repair work after interruption

Persist the repair stage and evidence, then recheck the project and workspace when continuing in a new session.

- **Support status**: Supported
- **Applicability**: Longer repair tasks spanning sessions
- **Usage**: [Bug analysis and repair guide](BUGFIX_GUIDE.en.md)
- **Limitations**: Stop and reconcile external project changes first; stale completion claims cannot be reused directly.
- **Version placement**: v1.10.0 onward; v1.12.0 enhanced

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `FIX-004`
- **Version record**: released: v1.10.0; corrected: v1.11.4, v1.11.7; enhanced in this iteration: v1.12.0
- **Engineering conditions**: Long-running repairs in Git repositories; verify already-committed older runs before creating a new run
- **Verification method**: runtime tests
- **Evidence**: [tests/test_auto_fix_runtime.py](../tests/test_auto_fix_runtime.py); [tests/test_auto_fix_lifecycle.py](../tests/test_auto_fix_lifecycle.py); [auto-fix/runtime.py](../auto-fix/runtime.py)
- **Technical details**: WorkspaceSnapshot and atomic private Git state support drift checks and checkpoint recovery. Schema 3 separates content and staging fingerprints; older states revoke stale completion evidence and require revalidation. See the [Auto Fix contract](../auto-fix/SKILL.md).

</details>

<a id="fix-005"></a>

#### Select necessary verification by bug risk

Arrange verification by impact scope and reuse valid results to reduce unjustified repeated execution.

- **Support status**: Supported
- **Applicability**: Bug fixes of varying size and risk
- **Usage**: [Bug analysis and repair guide](BUGFIX_GUIDE.en.md)
- **Limitations**: Use stricter verification when risk is unclear; known failures cannot be hidden by skipping or old records.
- **Version placement**: v1.11.2 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `FIX-005`
- **Version record**: released: v1.11.2; corrected: v1.11.7
- **Engineering conditions**: fast / standard / strict fixes; fail safely for unclear risk and retain objective verification gaps
- **Verification method**: runtime tests + contract tests
- **Evidence**: [tests/test_auto_fix_runtime.py](../tests/test_auto_fix_runtime.py); [tests/test_auto_fix_lifecycle.py](../tests/test_auto_fix_lifecycle.py); [tests/test_auto_fix_contract.py](../tests/test_auto_fix_contract.py); [auto-fix/SKILL.md](../auto-fix/SKILL.md)
- **Technical details**: Authorization Mode and validation profile are independent. The Skill selects verification scope by actual impact; strict or shared-infrastructure classification alone does not trigger repository-wide regression. Full regression requires an explicit requirement or evidence that smaller coverage is insufficient. The runtime invalidates or reuses evidence by dependencies, and documentation changes still require re-review. Known failures can only be cleared by new passing evidence for the same command/check; permission failures during state writes fail fast. See the [Auto Fix contract](../auto-fix/SKILL.md).

</details>

<a id="codebase-audit"></a>

### Systematically audit existing projects

<a id="aud-001"></a>

#### Resume a project audit after interruption

Persist the audit scope, stage, and problem records so later sessions can continue.

- **Support status**: Supported
- **Applicability**: Local Git projects authorized for audit
- **Usage**: [Project-audit workflow](WORKFLOW.en.md#5-codebase-audit-and-repair-workflow)
- **Limitations**: Recheck after project or Context changes; old conclusions cannot be treated as current facts.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `AUD-001`
- **Version record**: released: v1.10.0
- **Engineering conditions**: User-owned or explicitly authorized Git repositories with one documentation root and Canonical Context
- **Verification method**: runtime tests
- **Evidence**: [tests/test_codebase_audit_runtime.py](../tests/test_codebase_audit_runtime.py)
- **Technical details**: Initialize a private Git AuditSnapshot and recover Task and Finding state across sessions through checkpoint, status, and resume. See the [Audit contract](../codebase-audit/SKILL.md).

</details>

<a id="aud-002"></a>

#### Audit an existing project by its actual modules

Audit in stages along actual project boundaries and generate task results, a finding list, and an overall report.

- **Support status**: Supported
- **Applicability**: Large or cross-module existing projects
- **Usage**: [Project-audit workflow](WORKFLOW.en.md#5-codebase-audit-and-repair-workflow)
- **Limitations**: Focus on engineering quality and behavioral correctness; this capability does not maintain a product capability catalog.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `AUD-002`
- **Version record**: released: v1.10.0
- **Engineering conditions**: Large or cross-module existing repositories; engineering quality auditing excludes offensive security
- **Verification method**: contract tests
- **Evidence**: [tests/test_vnext_contract.py](../tests/test_vnext_contract.py); [codebase-audit/SKILL.md](../codebase-audit/SKILL.md)
- **Technical details**: Dynamically partition from Context and generate Dashboard, Task, Result, Findings, and Report per task. See the [Audit contract](../codebase-audit/SKILL.md).

</details>

<a id="aud-003"></a>

#### Track finding confirmation and repair verification

Record whether findings are candidates, confirmed, rejected, stale, or resolved, retaining their evidence.

- **Support status**: Supported
- **Applicability**: Teams using project-audit finding lists
- **Usage**: [Project-audit workflow](WORKFLOW.en.md#5-codebase-audit-and-repair-workflow)
- **Limitations**: Resolution requires a real original finding and new post-fix verification; further code changes may invalidate the conclusion.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `AUD-003`
- **Version record**: released: v1.10.0; corrected: v1.11.6, v1.11.7
- **Engineering conditions**: Audit Finding Registry; retain the original confirmation basis, and subsequent drift makes resolved findings stale again
- **Verification method**: runtime tests + contract evidence
- **Evidence**: [tests/test_codebase_audit_runtime.py](../tests/test_codebase_audit_runtime.py); [tests/test_audit_resolution.py](../tests/test_audit_resolution.py); [codebase-audit/references/finding-contract.md](../codebase-audit/references/finding-contract.en.md)
- **Technical details**: Findings support candidate, confirmed, rejected, stale, and resolved states. Confirmed findings bind complete evidence and Snapshot; resolved findings must be imported from real historical confirmation and bound to a new post-fix snapshot and passing verification. See the [Finding contract](../codebase-audit/references/finding-contract.en.md).

</details>

<a id="aud-004"></a>

#### Reconcile relationships among modules before audit completion

Review cross-module calls, data flows, duplicate findings, and contradictory conclusions together.

- **Support status**: Supported
- **Applicability**: All project audits, including small projects and audits with no findings
- **Usage**: [Project-audit workflow](WORKFLOW.en.md#5-codebase-audit-and-repair-workflow)
- **Limitations**: Retain relationship and counter-evidence; module initialization order alone cannot establish a call relationship.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `AUD-004`
- **Version record**: released: v1.10.0; corrected: v1.11.4, v1.11.6
- **Engineering conditions**: All Audit Runs, including small projects or zero Findings
- **Verification method**: runtime tests + contract tests + contract evidence
- **Evidence**: [tests/test_codebase_audit_runtime.py](../tests/test_codebase_audit_runtime.py); [tests/test_vnext_contract.py](../tests/test_vnext_contract.py); [codebase-audit/references/cross-module-review.md](../codebase-audit/references/cross-module-review.en.md)
- **Technical details**: Require Cross-module Reconciliation before completion: checkpoint, deduplicate, handle contradictions, and review complete call chains, checking lifecycle relationships misrepresented as calls and unverified entry points. Changes to tasks or Findings automatically invalidate earlier reconciliation. See [Cross-module reconciliation](../codebase-audit/references/cross-module-review.en.md).

</details>

<a id="aud-005"></a>

#### Prevent reuse of stale audit conclusions after project changes

Check version and workspace changes at key stages to protect audit scope and evidence validity.

- **Support status**: Supported
- **Applicability**: Active or resumed project audits
- **Usage**: [Project-audit workflow](WORKFLOW.en.md#5-codebase-audit-and-repair-workflow)
- **Limitations**: Only audit documents and private runtime state may be written; stop confirming new facts when changes outside the baseline are found.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `AUD-005`
- **Version record**: released: v1.10.0; corrected: v1.11.4
- **Engineering conditions**: Active or resumed Audit Runs
- **Verification method**: runtime tests
- **Evidence**: [tests/test_codebase_audit_runtime.py](../tests/test_codebase_audit_runtime.py); [codebase-audit/runtime.py](../codebase-audit/runtime.py)
- **Technical details**: Fail closed on drift in HEAD, branch, existing dirty product content, Context, or product source. Allow the current run to update existing audit output, with output restricted to `<docs-root>/audit/**`. See the [Audit contract](../codebase-audit/SKILL.md).

</details>

<a id="aud-006"></a>

#### Choose Chinese or English audit reports

Prepare reports in natural Chinese by default, or in English only when explicitly requested.

- **Support status**: Supported
- **Applicability**: Project audits needing different document languages
- **Usage**: [Project-audit workflow](WORKFLOW.en.md#5-codebase-audit-and-repair-workflow)
- **Limitations**: Language changes affect presentation only, not finding evidence or run state.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `AUD-006`
- **Version record**: released: v1.10.0
- **Engineering conditions**: Audit document output
- **Verification method**: contract tests
- **Evidence**: [tests/test_vnext_contract.py](../tests/test_vnext_contract.py); [codebase-audit/SKILL.md](../codebase-audit/SKILL.md)
- **Technical details**: Generate natural-Chinese audit artifacts by default and English-only artifacts on explicit request. Display language does not change internal state or the Evidence fingerprint. See the [Audit contract](../codebase-audit/SKILL.md).

</details>

<a id="aud-007"></a>

#### Check the documentation entry for an audit report

Confirm that the overall report is reachable from the project documentation hub and provide an exact handoff when the entry is missing.

- **Support status**: Supported
- **Applicability**: Audits with a resolved project documentation root
- **Usage**: [Project-audit workflow](WORKFLOW.en.md#5-codebase-audit-and-repair-workflow)
- **Limitations**: The audit workflow does not modify the documentation hub outside its scope; the documentation-maintenance workflow owns entry updates.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `AUD-007`
- **Version record**: released: v1.10.0
- **Engineering conditions**: Audit Runs with a resolved documentation root
- **Verification method**: contract tests
- **Evidence**: [tests/test_vnext_contract.py](../tests/test_vnext_contract.py); [tests/test_docs_contract.py](../tests/test_docs_contract.py)
- **Technical details**: Check discoverability of the stable `audit/Report.md` entry, record `linked` or `docs-refresh-required`, and generate an exact Docs handoff when missing. See the [Audit contract](../codebase-audit/SKILL.md).

</details>

<a id="aud-008"></a>

#### Persist audit evidence in batches

Persist task results, findings, and document metadata in batches to reduce repetitive entry during long tasks.

- **Support status**: Supported
- **Applicability**: Project audits with many findings and evidence records
- **Usage**: [Project-audit workflow](WORKFLOW.en.md#5-codebase-audit-and-repair-workflow)
- **Limitations**: Batch persistence remains subject to scope and evidence validation; it does not replace verification of findings.
- **Version placement**: v1.11.5 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `AUD-008`
- **Version record**: released: v1.11.5
- **Engineering conditions**: Structured audits and long threads; drift and cross-module gates remain enforced
- **Verification method**: runtime regression tests
- **Evidence**: [tests/test_codebase_audit_runtime.py](../tests/test_codebase_audit_runtime.py); [codebase-audit/runtime.py](../codebase-audit/runtime.py)
- **Technical details**: Atomic batch registration of Task/Finding/document, batch output validation, and summary return. Reuse Git identity checks within the same workspace validation. See the [Batch interface](../codebase-audit/references/runtime-interface.en.md).

</details>

<a id="aud-009"></a>

#### Generate audit reports from persisted evidence

Generate interlinked reports from saved audit results while retaining the original findings and repair-verification basis.

- **Support status**: Supported
- **Applicability**: Project audits using structured results
- **Usage**: [Project-audit workflow](WORKFLOW.en.md#5-codebase-audit-and-repair-workflow)
- **Limitations**: Existing handwritten or externally modified content is protected and must be reconciled before updating.
- **Version placement**: v1.11.5 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `AUD-009`
- **Version record**: released: v1.11.5; corrected: v1.11.7
- **Engineering conditions**: New audits; older handwritten artifacts retain a compatible workflow
- **Verification method**: rendering / interruption recovery / installation-package validation
- **Evidence**: [tests/test_codebase_audit_runtime.py](../tests/test_codebase_audit_runtime.py); [tests/test_audit_resolution.py](../tests/test_audit_resolution.py); [codebase-audit/render.py](../codebase-audit/render.py)
- **Technical details**: Generate compact Markdown from persisted evidence, showing original-finding and post-fix verification snapshots separately. Protect handwritten/externally modified output; check the current Revision rendering receipt and resolution evidence before completion. See [Writing and completion](../codebase-audit/references/runtime-interface.en.md#writing-and-completion).

</details>

<a id="显式复盘"></a>

### Task retrospectives

<a id="ret-001"></a>

#### Prepare a retrospective on explicit request

Organize retrospective material into facts, policies, lessons, and candidates for promotion into formal documents.

- **Support status**: Supported
- **Applicability**: Teams explicitly requesting a retrospective or durable task summary
- **Usage**: [Retrospective usage rules](../retro/SKILL.md)
- **Limitations**: Retrospectives do not start after every task by default, and unverified lessons are not automatically promoted into project rules.
- **Version placement**: v1.10.0 onward

<details>
<summary>Technical information and verification evidence</summary>

- **Capability ID**: `RET-001`
- **Version record**: released: v1.10.0
- **Engineering conditions**: Explicit retro, retrospective, or durable-summary requests
- **Verification method**: contract tests + installation tests
- **Evidence**: [tests/test_vnext_contract.py](../tests/test_vnext_contract.py); [tests/test_install.py](../tests/test_install.py)
- **Technical details**: Run retrospectives only on explicit user request, classify entries as FACT / POLICY / LESSON, deduplicate with stable `Rnnn` IDs, and maintain Promotion Candidates. See the [Retro contract](../retro/SKILL.md).

</details>


## Pending confirmation

The following two items lack sufficient implementation or verification evidence and are not counted as supported.

### Native orchestration of multiple repositories in one repair

No corresponding implementation and automated verification have been found for a single Auto Fix run natively managing branches, snapshots, and commits across multiple repositories. The old claim remains a lead, not a commitment of current support.

<details>
<summary>Basis for pending confirmation</summary>

- **Candidate ID**: `CAND-001`
- **Lead**: the multi-repository claim in an older usage guide.
- **Gap**: implementation and verification for the repository set, cross-repository snapshots, and commit boundaries.

</details>

### Fetch remote issue content automatically

No fixed client or integration verification has been found for fetching GitHub / GitLab Issues directly without host connector tools or user input.

<details>
<summary>Basis for pending confirmation</summary>

- **Candidate ID**: `CAND-002`
- **Lead**: [Auto Fix input documentation](../auto-fix/SKILL.md).
- **Gap**: a fixed connector capability, runtime implementation, or integration verification.

</details>

## Removed

None. Check migration or renaming when old evidence cannot be found; absence alone does not establish removal.

## Most recent full inventory

<details>
<summary>Maintenance information and coverage</summary>

- **Inventory stage**: full reconciliation.
- **Inventory date**: 2026-10-23.
- **Baseline**: the `v1.12.0` release source tree, starting from `main` / `82d39d7db45473a661b1352a8ada767f86d44149` plus the current Docs, Planning, and Auto Fix documentation-maintenance enhancements and version update. The review covers this version's source and installation-package resources, excluding the separate Runtime's platform state.
- **Coverage conclusion**: full inventory complete; all nine scopes below and all existing capability IDs have been reconciled.
- **Excluded scope**: task execution and platform support in the separate Runtime repository, because that product maintains them itself.

| Capability scope | Review entry points and evidence | Result |
|---|---|---|
| Installation and distribution | [Installer](../install.py), [Release packaging](../release.py), [Installation verification](../tests/test_install.py) | Checked |
| Project context | [Context contract](../context/SKILL.md), [Evidence collection](../context/evidence.py), [Write protection](../tests/test_context_write_safety.py) | Checked |
| Documentation governance and capability inventory | [Docs contract](../dev-harness-docs/SKILL.md), [Capability maintenance](../dev-harness-docs/references/capability-maintenance.en.md) | Checked |
| Development planning and task handoff | [Planning contract](../planning/SKILL.md), [Task template](../planning/templates/Task.template.md) | Checked |
| Verification commands | [Commands contract](../commands/SKILL.md), [Cross-Skill verification](../tests/test_vnext_contract.py) | Checked |
| Git commits and release notes | [Git contract](../git-workflow/SKILL.md), [Default rules](../git-workflow/references/default-contract.en.md) | Checked |
| Bug repair | [Auto Fix contract](../auto-fix/SKILL.md), [Documentation-gate verification](../tests/test_auto_fix_documentation.py) | Checked |
| Project audit | [Audit contract](../codebase-audit/SKILL.md), [Runtime verification](../tests/test_codebase_audit_runtime.py) | Checked |
| Explicit retrospectives | [Retro contract](../retro/SKILL.md), [Cross-Skill verification](../tests/test_vnext_contract.py) | Checked |

- **Changes in this iteration**: retain the original 35 capability IDs; add `DOC-007`; update the change descriptions for `DOC-005`, `DOC-006`, `PLN-004`, `FIX-002`, and `FIX-004`; retain both pending IDs. Recheck original evidence paths, use file links and stable rule entry points, and remove fragile line numbers.
- **Verification scope**: reconcile implementation and contracts by category; all 259 full-regression tests passed in this iteration. An independent temporary project exercised initial inventory, incremental update, two consecutive full reconciliations, and restricted-read coverage: old IDs remain stable, repeated reconciliation creates no extra items or renumbering, and insufficient coverage does not replace the last complete record. New gates and installation resources were verified by this iteration's tests; historical target-environment verification is not represented as a fresh test. See [Testing](TESTING.en.md) for verification methods.
- **Open items**: `CAND-001` and `CAND-002` lack implementation or integration evidence.

</details>

## Maintenance rules

- [Capability maintenance](../dev-harness-docs/references/capability-maintenance.en.md) defines initial inventory, post-delivery incremental updates, and repeatable full reconciliation.
- Assign one stable ID per independent capability. Preserve it across changes to name, category, applicability, and evidence, and retain the basis for removal.
- User descriptions and technical evidence belong to the same capability item; do not create a separate catalog requiring manual synchronization.
- Before each feature or fix is completed, record the documentation-check outcome and basis. Task progress is not support evidence.
- Full reconciliation covers the entire declared scope and every existing ID. State coverage gaps when incomplete. Keep only the most recent complete inventory summary; Git preserves history.
- Recalculate the summary after capability-status or version changes. Put future work in planning, released changes in CHANGELOG, and insufficiently evidenced capabilities under pending confirmation.
