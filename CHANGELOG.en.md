# CHANGELOG

[English](CHANGELOG.en.md) | [简体中文](CHANGELOG.md)

## Unreleased

### Added

- Complete English counterparts for user guides, the capability catalog, version and upgrade information, advanced usage references, and contributor documents, with language switches between Chinese and English.

### Changed

- English reading paths link to the corresponding English bodies and section anchors. Protocol-required structural labels remain literal, and the original languages of historical records and internal Agent contracts are identified explicitly.
- Skill installation and export include English usage references. Versioned zips also include the English changelog linked from the packaged English installation guide.

---

## v1.12.1 — 2026-11-09

### Changed

- Clarify verification responsibilities: Auto Fix selects verification scope by actual impact; project policy defines concrete commands and mandatory gates; Context's AGENTS template retains only brief defaults. Skip refreshing a file when the preview shows that human rules would be lost.
- Clarify that fixing and committing do not automatically authorize building deployment packages, publishing, or deploying, avoiding calls to release-packaging entry points merely to execute embedded tests.

### Fixed

- Auto Fix no longer maps strict or shared-infrastructure classification directly to repository-wide regression. Expansion to the whole repository requires an explicit requirement or evidence of insufficient coverage. Every profile may reuse valid verification, and additional or repeated commands stop once coverage is sufficient.
- Align Planning, Commands, and Runtime automatic-execution handoff requirements and provide a task-declaration reference. New HARNESS files use status-bearing command tables; candidate commands do not automatically qualify for execution, and existing manually confirmed sections remain unchanged.

---

## v1.12.0 — 2026-10-23

### Added

- Docs adds initial full inventory, incremental updates, and repeatable full reconciliation, recording baseline and coverage, preserving capability IDs, and defining handling for pending, removed, and incomplete items.
- Auto Fix adds `DocumentationCheck`, bound to the current change fingerprint. Before successful completion or commit, verify the basis for documentation updates or no-update decisions. Older successful runs without this check lose stale completion claims and require revalidation.

### Changed

- Organize the capability template and this repository's catalog by use case, using plain language for purpose, scope, limitations, and entry points, with engineering IDs and verification evidence expandable on demand. Retain the original 35 capability IDs and add the capability-inventory workflow item; count the current development version and release scope separately.
- Planning execution packets declare capability-documentation impact, necessary write scope, and acceptance methods before readiness, and record the outcome before completion. Milestones affecting product support require full catalog reconciliation before closure.

---

## v1.11.8 — 2026-09-16

### Changed

- Versioned zips distribute ready-to-use `skills/`, retaining required runtime scripts, templates, references, standalone installation instructions, VERSION, and CHANGELOG. Source, source installers, and repository maintenance documents are supplied through the matching source archive rather than duplicated in the Skill package; extract and copy the Skill directories to install.
- Chinese and English READMEs distinguish source-and-script installation from copying a dist package, adding host directories, individual-Skill dependencies, and upgrade instructions. Release-package regression verifies complete resources, version consistency, and runtime entry points independent of the source checkout.

---

## v1.11.7 — 2026-09-16

### Added

- Add regression tests for Context file safety and evidence integrity, Audit repair revalidation, and Auto Fix verification invalidation and commit recovery.

### Changed

- Upgrade Auto Fix state to SchemaVersion 3, separating content fingerprints from staging state and persisting verification dependency bindings and authorized commit receipts. Old states revoke prior completion claims and require verification and review again; already-committed old runs without reliable receipts must have their commits checked before a new run is established.
- Git Workflow uses generic TaskChangedFiles and task baselines to check commit ownership. Context and Git Workflow reuse the existing doc/ or docs/ root.
- Commands retains unconfirmed gaps per record; mobile projects run available tests according to specific device requirements; Audit reads LESSONS.md only on explicit user request.

### Fixed

- Auto Fix binds new verification to current content and rechecks completion gates at final-verify, report, and commit, rejecting stale verification, failed reviews, and failed checks. Stage transitions, older passes, or skipped statuses cannot clear known failures. Objective skips must record blocker evidence, alternative checks, and remaining risk, allowing at most DONE_WITH_CONCERNS.
- Auto Fix supports staging identical content, recovery after a valid commit, and interruption recovery before the commit receipt is written. It checks content using Git's effective permission bits; explicit permission-bit changes invalidate prior review.
- Audit resolved Findings must reference real historical confirmation, retain the original finding basis, and supply a new snapshot and passing repair verification. Rendering and completion recheck these conditions; later drift revokes the resolution.
- Context fingerprints cover packages/ workspaces, hidden project configuration, and complete file contents, rejecting evidence references outside snapshot coverage. Explicit Unknown, low-confidence values, and empty lists are no longer filled as facts by offline Profiles.
- Context refresh rechecks the previewed file content and identity before writing, refusing to overwrite user changes made during confirmation.
- Planning snapshots include content and index fingerprints of existing dirty files. Reopened tasks use independent closure numbers on subsequent archival, and verification examples no longer hide earlier failures.

### Security

- Context initialization and refresh reject nonregular output files such as symlinks. Missing files are created exclusively, preventing out-of-scope writes through dangling symlinks and overwrites caused by creation races.

---

## v1.11.6 — 2026-09-08

### Fixed

- Audit call chains require evidence for every call, dispatch, or data transfer, listing prerequisites such as initialization separately so lifecycle ordering is not misrepresented as a continuous call chain.
- Cross-module reconciliation checks unknown entry points and call relationships. When no upper-level caller of a public interface is found, state the verification boundary rather than inferring automatic business invocation or rejecting an interface defect already proved under valid calling conditions.

---

## v1.11.5 — 2026-09-07

### Added

- Codebase Audit adds `batch`, `validate-outputs`, and `render-output`, supporting batch evidence registration, path validation, and compact audit-document generation through UTF-8 JSON files or stdin.

### Changed

- New Audit runs prefer batch persistence of Task, Finding, and document metadata, automatically generating navigation and snapshot references to reduce repetitive handwritten patches. Older individual commands and handwritten artifacts remain compatible.
- Audit state commands support summary responses and reuse Git identity checks within one workspace validation, reducing repeated process calls and context overhead. Cross-module reconciliation remains mandatory.

### Fixed

- Before a structured Audit run completes, check that documents for the current Revision were generated and not externally modified. The generator protects existing handwritten artifacts and supports per-file atomic replacement and retries after interruption.

---

## v1.11.4 — 2026-09-07

### Changed

- Release zips now include usage and maintenance documents from repository `docs/`, excluding internal `docs/audit/` work artifacts.

### Fixed

- Export builds in a temporary directory first and replaces atomically, retaining the previous usable bundle on build failure.
- Non-interactive Context `refresh` without `--force` is preview-only and no longer creates missing files early. Truncated repository evidence prevents reuse of potentially stale semantic analysis.
- Codebase Audit permits the current run to update existing audit output and invalidates earlier cross-module reconciliation when tasks or Findings change.
- Auto Fix revalidates workspace differences after `final-verify` before report or commit, rejecting stale verification evidence.

---

## v1.11.3 — 2026-09-04

### Changed

- `dev-harness-planning` adds the `🟢 待执行` (ready) state and packet-completeness gate, producing model-independent plans usable by fresh conversations or external execution workflows without owning task pickup or execution orchestration.
- Planning task templates add authoritative context, code and test entry points, invariants, confirmed decisions, and stop conditions so a new conversation can execute one task without inheriting the planning chat history.

---

## v1.11.2 — 2026-08-31

### Added

- `dev-harness-auto-fix` adds `fast / standard / strict` verification profiles independent of authorization mode, two risk assessments, structured verification plans, and a SchemaVersion 2 state contract.

### Changed

- Auto Fix invalidates evidence by actual impact on production code, tests, documentation, and shared infrastructure. It allows verification reuse derived from proven obligations and uses a final hash check instead of repeating expensive commands when the diff is unchanged.
- Independent review becomes risk-based. Self-review fallback is allowed only when review infrastructure is unavailable; a failed review cannot be overwritten.

### Fixed

- Auto Fix reports stable state-write errors by `mkdir / create / fsync / replace` stage. Permission denial immediately returns `state_write_denied`; temporary-file name collisions permit only bounded retries.

---

## v1.11.1 — 2026-08-25

### Changed

- `dev-harness-planning` makes Dashboard the sole active planning entry. Task files maintain execution details only; migrated `TaskDetails.md` remains a compatibility redirect, avoiding AI reading drift from multiple mutable state copies.
- Add temporary planning snapshots and drift gates when claiming, resuming, migrating, and closing tasks, checking `HEAD`, Dashboard, task paths, content hashes, and existing workspace changes before continuing.

---

## v1.11.0 — 2026-08-25

### Added

- `dev-harness-planning` adds active-task packets at `tasks/<Task-ID>.md` and completed-task archive templates under `archive/<milestone>/`, allowing AI to load only current task details.
- Add an on-demand migration reference for large legacy monolithic `TaskDetails.md`, covering task-scope ledgers, status fallback, missing milestones, repository-wide incoming links, and relative-link checks after moves.

### Changed

- Planning's `TaskDetails.md` becomes the active-task entry. If a monolithic detail file exceeds 1,000 lines, 100 KB, or 20 task bodies, perform compatible migration before appending more.
- Completed tasks leave the active index after final acceptance evidence is recorded. Dashboard retains at most five recent-completion summaries, while Git history continues to record editing history.
- All eight skills gain consistent output-language contracts: without a user-specified language, Chinese projects and new documents default to natural Simplified Chinese; refresh follows an existing document's primary language.
- Reader-facing headings, tables, verification conclusions, final reports, commit descriptions, and release copy prefer expressions natural to Chinese development teams. Paths, commands, APIs, protocols, necessary abbreviations, and internal enums remain stable.

---

## v1.10.0 — 2026-08-20

### Added

- `dev-harness-codebase-audit` adds an explicit Engineering Audit Scope: user-owned or explicitly authorized repositories, focused on engineering quality, behavioral correctness, and cross-module consistency, with a clear separation from penetration testing / offensive security workflows.
- Codebase Audit adds a run-level `output_language` convention: natural-Chinese audit documents by default, English documents only on an explicit English-only request. Internal state enums stay stable; Chinese is a presentation layer.

### Changed

- Codebase Audit runtime verification is explicitly limited to local, deterministic, minimal reproductions, verifying trigger conditions, state changes, error propagation, and actual high-impact outcomes against declared project behavior.
- Finding merging gains an identity gate: Candidates remain separate by default and merge only when root cause, ownership, repair boundary, and the effect of one fix all agree. Cross-module Reconciliation still performs end-to-end review, contradiction handling, and Severity / Confidence reordering.
- Audit references, templates, and examples use engineering-quality semantics and natural Chinese while retaining Audit Snapshot, Finding Registry, Evidence / Counter-evidence, state machines, workspace drift, fail-closed behavior, and audit-only boundaries that prohibit product-source changes.

---

## v1.9.1 — 2026-08-19

### Changed

- Capability Catalog, documentation governance, Context, Planning, Audit, Retro, and Bugfix templates adopt natural Chinese, avoiding awkward word-by-word translations of concepts such as `observable capability`, `leaf capability`, `owner`, and `promote`.
- Newly generated Context documents use headings meaning code-style examples, core business flow, build/start troubleshooting, and the general process for adding features, while recognizing and migrating older headings compatibly.

### Fixed

- `dev-harness-docs` adds Chinese terminology constraints and anti-literal-translation tests, reserving “observability” for logs, metrics, and traces rather than product capabilities.

---

## v1.9.0 — 2026-08-19

### Added

- `dev-harness-docs` adds a conditional Capability Catalog contract and self-contained template: reuse an existing scope source of truth; if absent, select a location according to the existing product-document directory, separating product status, applicability, delivery baseline, verification level, and evidence.

### Changed

- Codebase Audit includes document discoverability in Dashboard, Report, and completion criteria while retaining the `<docs-root>/audit/**` write boundary. Missing documentation-hub entries are explicitly handed to Docs Refresh; root README shortcuts remain optional.

---

## v1.8.1 — 2026-08-19

### Fixed

- Align the OpenAI display name of `dev-harness-docs` with its actual Skill name and lock this metadata through installation-artifact tests, preventing it from appearing separately as `Dev Harness Docs`.

---

## v1.8.0 — 2026-08-18

### Added

- Add `dev-harness-codebase-audit`: dynamically partition large codebases from Canonical Context, persist AuditSnapshot, tasks, and Findings in private Git state, and restrict versioned artifacts to the existing `<docs-root>/audit/` directory.
- Codebase Audit runtime adds workspace/context drift checks, output-path validation, symlink-escape prevention, Finding state and confirmed-evidence validation, and init/resume/status/task/finding/cross-module/complete CLI entries.
- Installation, individual-Skill installation, export, and release archives include Audit runtime, references, and templates.
- Add the `docs/README.md` documentation hub and link the VNext design as the v1.8.0 design rationale.

### Changed

- Refocus the top-level role on a Project Contract driven by Consistency / Evidence / Continuity rather than only Bugfix, without expanding into a generic AI Skills encyclopedia.
- Retro becomes explicitly triggered only, using FACT / POLICY / LESSON and Promotion Candidates. The installer and other skills no longer inject or read `LESSONS.md` hard rules unconditionally.
- Add `test` to HARNESS verification interfaces and support both simple single-value commands and multiple Platform / Variant command records.
- Move platform/default explanations in Context, Commands, and Git Workflow into on-demand references. Planning refresh explicitly preserves Task IDs and evidence-backed completion states.
- Clarify that the V1 / VNext boundary document owns current scope and V2 Backlog owns future candidates; design records no longer serve as active task lists.

### Removed

- Remove `docs/superpowers` implementation plans and design drafts already superseded by current code, tests, and specialist documents. Git history continues to preserve historical decisions.

---

## v1.7.0 — 2026-08-04

### Added

- `dev-harness-docs` adds `Update`: sync only reusable facts proved by code, configuration, or successful verification into existing documents. Produce a minimal update plan, preserve human sections and formatting, and keep unverified items pending without depending on external documentation packages.
- Add verified-fact update discipline to the information-architecture reference. External packages such as gstack are explicitly optional heavyweight channels for full content generation and release audits; routine fact synchronization defaults to the built-in Update operation.

---

## v1.6.0 — 2026-08-03

### Added

- Add `dev-harness-docs`, reusing the project's existing `doc/` or `docs/` root and providing documentation indexes, progressive navigation, sources of truth, archives, and link-verification workflows.
- Include documentation-hub, maintenance-rule, and navigation templates, plus information-architecture and safe-migration references; installation and release packages remain Skill-self-contained.

### Changed

- `dev-harness-planning` resolves the project documentation root before generating `plan/Dashboard.md` and `plan/TaskDetails.md`, avoiding a second documentation tree.

---

## v1.5.1 — 2026-07-22

### Context document cleanup and semantic validation

- README uses the actual project name as its H1, filtering runtime directories and unsupported generic placeholder-directory descriptions, and accepts real `core_modules` responsibilities from semantic analysis.
- AGENTS/HARNESS no longer include internal evidence-audit fields, meaningless `- Unknown` lists, absolute working directories, or SDK/C++ template terminology unrelated to the project.
- Separate Python dependency installation from build semantics; mark build explicitly `N/A` when there is no independent compilation or packaging step.
- Add evidence-reference line-range validation. Conclusions using strong constraints require precise line evidence, and installation commands cannot be declared as build commands.
- Add high-risk detection for Python application startup, database initialization, concurrency locks/retries, external calls, and service-installation entry points.

---

## v1.5.0 — 2026-07-16

### Generic AI semantic recognition

- Add the framework-independent `evidence` command, emitting a repository inventory, analysis-field contract, truncation status, and snapshot fingerprint.
- Add the AI Semantic Analysis JSON protocol. New languages or frameworks can produce project type, architecture, call chains, risk boundaries, and command candidates without a new hard-coded Profile first.
- Every non-`Unknown` conclusion must cite repository-local evidence and high/medium/low confidence, with an evidence ledger retained in AGENTS/HARNESS.
- Low-confidence conclusions automatically go to human confirmation. Reject commands without evidence, paths outside the repository, unknown fields, and stale snapshots before writing.
- Built-in WPF, Qt, Harmony, Win32, FastAPI, and other Profiles become compatibility fallbacks and specialized risk enhancements rather than a recognition allowlist.
- Add `evidence.py` and `semantic.py` to installed runtime resources and cover post-install evidence/analysis calls.

---

## v1.4.0 — 2026-07-16

### Safe Context refresh and FastAPI support

- Add `refresh` for fixed Markdown sections without managed markers, preserving other user sections, encoding, line endings, and file permissions.
- Change `scan` to create missing files only, never overwriting existing context documents even with `--force`.
- Add a project-owned Git, code, release, and changelog policy index, with human-confirmation items for conflicting references.
- Add FastAPI recognition from dependency and source evidence, discovering ASGI entry points, router/service/core call chains, and high-risk boundaries.
- Generate FastAPI Python compile checks, uvicorn run commands, and pytest quick/bugfix/full candidates automatically.

### Build and verification contract

- Make `HARNESS.md` the sole source of truth for builds, verification, and execution environments.
- Add the default Git workflow template and fixed-section Context refresh runtime to the installation package.

### Executable Auto-fix contract

- Add `auto-fix/runtime.py`, providing WorkspaceSnapshot, workspace-ownership checks, stable diff hashes, private Git state files, and a stage state machine.
- Add analyze / fix / commit / unattended authorization modes. Fix no longer commits implicitly; Issue writeback, push, PR, and publishing still need independent authorization.
- Allow dirty worktrees: existing snapshot-time changes belong to the user. The current task may modify and stage only AutoFixChangedFiles; stop on drift in pre-existing changes or undeclared changes.
- Structure root-cause judgments as falsifiable Claim / Prediction / Probe / Observation / Status records. Repeated failed hypotheses return NEEDS_CONTEXT/BLOCKED.
- Make regression tests a default gate for write modes, requiring RED before and GREEN after the fix. Objective inability to automate explicitly downgrades the outcome to DONE_WITH_CONCERNS.
- Bind review and final verification to the diff hash; implementation changes clear old Review/Verify evidence.
- Include the auto-fix runtime in installation packages and add runtime, contract, and installation-artifact tests.

---

## v1.3.0 — 2026-07-10

### Add planning-stage Skill templates

- Add `dev-harness-planning` to generate task Dashboards and details before implementation.
- Add `planning/templates/Dashboard.template.md` and `planning/templates/TaskDetails.template.md`, exported with the installation package.
- Update `install.py` so the Planning Skill and its templates can be installed and packaged.
- Move Context templates to `context/templates/`, retaining Skill-local directory structure after installation.
- Update README, English documentation, and template descriptions, and extend installation-test coverage to Planning templates.

---

## v1.2.0 — 2026-06-01

### Expand multilingual-project support and safety gates

**Added:**
- **Go backend projects**: support context analysis and verification loops, with automatic gates for CGO boundaries and core concurrency logic such as Goroutine leaks.
- **Flutter cross-platform clients**: support project-structure analysis and framework constraints, strengthening confirmation for changes at Platform Channels and native-code boundaries.
- **Node.js frontend toolchains and plugins**: support plugin analysis including `plugin.json`, adding gates for cross-Workspace dependency overrides and lifecycle-hook tampering.
- **Retro knowledge capture**: add the generic L001 boundary rule, preventing AI from incorrectly modifying artifacts in globally installed directories.

**Changed:**
- Remove the former Qt/Harmony-only hard block in `dev-harness-auto-fix`; risk gates now attach dynamically according to the language identifiers read.
- Add and update Go and Node.js automated test commands and gating states in `commands` scripts.
- Update the README project-support matrix.

---

## v1.1.0 — 2026-05-18

### Inline the four Bugfix stages and remove Pilot (Skill count 10 → 5)

**Breaking change**: remove the standalone `dev-harness-repro`, `dev-harness-triage`, `dev-harness-regression`, `dev-harness-verify`, and `dev-harness-pilot` skills.

- Move workflow details to repository `internal/bugfix-flow/*.md`, copied at installation to `references/bugfix-flow/` under `dev-harness-auto-fix`.
- Auto Fix reads references **on demand** at the corresponding steps; they are no longer separately discoverable host skills.
- Remove Pilot's three redundant routing branches (initialization → Context, bug fixing → Auto Fix).
- Reduce installable skills from 10 to **5**: commands / context / git-workflow / auto-fix / retro.

**Upgrade**: rerun `./install.sh --ide cursor` or an equivalent command. Old directories such as `skills/dev-harness-repro` may be removed manually to avoid leftovers.

---

## v1.0.1 — 2026-05-18

### Context engineering improvements (based on context-engineering analysis)

**① Prevent Context Flooding**
Replace full `cat LESSONS.md` in every Skill preamble with Python filtering of the ten most frequent rules, descending by trigger count, falling back to `cat` when Python is unavailable. This prevents a growing LESSONS.md from consuming the AI context window.

**② Inline Planning Pattern (Auto-fix)**
Add an execution-plan output at `dev-harness-auto-fix` Step 0.7, listing the eight-step chain, project profile, availability, and review mode so the user can confirm the direction before Step 1.

**③ Trust Level labels**
Add §1b, file trust levels, to `AGENTS.template.md`: ✅ trusted source, ⚠️ configuration/external documents requiring verification, and ❌ untrusted user content, preventing prompt injection.

---

## v1.0.0 — 2026-05-14

First official release.

### Skills

- `dev-harness-pilot` — entry Skill that routes a goal to the corresponding Skill
- `dev-harness-context` — scan repositories and generate `README.md`, `ARCHITECTURE.md`, `HARNESS.md`, and `AGENTS.md`
- `dev-harness-commands` — standardize `build / quick / bugfix / full` command entries
- `dev-harness-repro` — narrow reproduction conditions
- `dev-harness-triage` — trace call chains and locate root causes
- `dev-harness-regression` — define regression coverage and test anchors
- `dev-harness-verify` — layered verification commands and completion evidence
- `dev-harness-git-workflow` — validate branch names, generate commit messages, and detect debugging residue under Conventional Commits
- `dev-harness-auto-fix` — full automatic repair workflow: bug description / Issue URL → root cause → fix → review → commit
- `dev-harness-retro` — retrospective that extracts AI mistake rules into `LESSONS.md`

### Scanner

- `context/cli.py`: project-type detection uses wildcard patterns and dynamic namespace inference, not specific project names.
- `platform_profiles.py`: Harmony packaging-script detection uses the `buildScript/*_package.py` glob.
- Initial priority stacks: WPF, Harmony, Win32, and Qt, including Shared C++ Core.

### Engineering foundation

- `VERSION` is the single source of truth for the version.
- `install.py` injects `bundle_version` into every SKILL.md frontmatter during installation/export.
- `release.py` / `release.bat` / `release.sh`: one-command packaging of `dev-harness-vX.Y.Z.zip`.
- Supported platforms: Cursor, Codex CLI, OpenCode, and Antigravity.
- Tests: 14 unittest cases covering core scanner paths.

### Documentation

- `docs/HARNESS_GUIDE.md`: general usage guide.
- `docs/GIT_WORKFLOW.md`: reference for Conventional Commits branch and commit conventions.
