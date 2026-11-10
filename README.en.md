# dev-harness

[English](README.en.md) | [简体中文](README.md)

**A project engineering contract layer for AI coding assistants.** dev-harness connects project context, documentation, planning, verification commands, and Git policy, with durable evidence workflows for feature delivery, bug fixes, and codebase audits.

It is built around three goals:

- **Consistency:** project rules remain stable across assistants and sessions.
- **Evidence:** completion claims are backed by code, diffs, tests, or runtime evidence.
- **Continuity:** long tasks can resume from project documents and private Git state.

## How it works

dev-harness connects the project's existing authoritative sources instead of putting every fact into one central configuration:

```text
Project Contract
├── Context: README / ARCHITECTURE / AGENTS
├── Verification: HARNESS.md
├── Documentation: the existing doc/ or docs/ root
├── Current Capabilities: Capability Catalog or an existing equivalent
├── Planning: one active Dashboard + tasks/ packets + milestone archives
├── Git Policy: the project's own Git / release / changelog conventions
├── Retrospective: LESSONS.md
└── Codebase Audit: <docs-root>/audit/ + private Git state
```

Once the Project Contract is ready, choose one of two main paths:

```text
Feature delivery
Requirements and acceptance → Planning packets → Development
→ Tests and acceptance → Update documentation and status → Commit

Codebase audit and repair
Audit → Confirmed Findings → Route by category → Auto Fix / Planning / Docs
      → Full verification → QA → Final review
```

See the [end-to-end workflow](docs/WORKFLOW.en.md) for the complete stages, evidence requirements, and authorization boundaries.

## Quick start

After [installing the skills](#install), open your project in your AI assistant and describe the task:

```text
# Onboard a repository
Scan this repository and generate project context. Identify the real verification commands and existing Git policy.

# Prepare feature delivery
Create one active Planning Dashboard and individual task packets from the requirements. Implement, verify, and archive each task.

# Organize documentation
Organize this project's existing documentation root and sources of truth. Sync only facts backed by implementation or successful verification.

# Audit a codebase
Initialize a codebase audit from the project Context and execute it in stages along module boundaries.

# Fix a known bug
Auto fix this bug in fix mode: opening Settings after login crashes.

# Request a retrospective explicitly
retro: summarize this task and organize candidates for promotion into the formal project contracts.
```

Commit, push, PR, tag, release, and deployment actions each require explicit authorization.

English prompts do not automatically select English for every generated document. See [language coverage](#language-coverage) before translating project contracts or Planning packets.

## Install

Supports **Cursor, Codex CLI, OpenCode, and Antigravity**.

### From source

Clone this repository or extract its source archive, then open the project root containing `install.py`. Python 3 is required.

macOS / Linux:

```bash
./install.sh --ide codex
```

Windows:

```powershell
.\install.bat --ide codex
```

Replace `codex` with `cursor`, `opencode`, or `antigravity` for another host. The installer builds the skills and resolves dependencies when installing an individual skill.

```bash
./install.sh --ide codex --skill dev-harness-context
./install.sh --target /custom/path
./install.sh --export dist
```

`--target` selects the installation root; the skills are placed under its `skills/` directory. `--export dist` creates `dist/bundle/`. Without flags, the installer shows a menu in an interactive terminal and defaults to Cursor in a non-interactive environment.

Maintainers generate the versioned zip with `python release.py`; this does not publish a release.

### From a Skill release package

Download `dev-harness-vX.Y.Z.zip` from the [releases](https://github.com/Dev-Wiki/dev-harness/releases), extract it, and copy the `dev-harness-*` folders inside `skills/` into your host's skills directory:

| Host | Skills directory |
|---|---|
| Cursor | `~/.cursor/skills/` |
| Codex | `~/.codex/skills/` |
| OpenCode | `~/.config/opencode/skills/`; on Windows with APPDATA set, `%APPDATA%/opencode/skills/` |
| Antigravity | `~/.gemini/antigravity/skills/` |

`~` means your home directory. Create the destination if needed, or use your host's configured skills directory. For Codex, the resulting path should be `~/.codex/skills/dev-harness-context/SKILL.md`, with no extra `skills/` level.

Copying all eight skills is recommended. If copying individual skills, include these dependencies:

- `dev-harness-codebase-audit` requires `dev-harness-context`.
- `dev-harness-auto-fix` requires `dev-harness-git-workflow`.

For upgrades, preserve your custom changes before replacing the corresponding skill folders, keep unrelated skills, and reload the host's skill list.

Keep each skill's runtime scripts, templates, and references together. Context, Auto Fix, and Codebase Audit require Python 3 at runtime; Git workspace operations require Git. New release packages include standalone installation instructions in `README.md` and `README.en.md`. Earlier packages may have Chinese instructions only; these copy-install steps also apply to them. Source code and maintenance documentation are provided by the corresponding source archive.

v1.12.1 clarifies that Auto Fix selects verification based on actual impact; strict validation does not automatically trigger a repository-wide regression. Projects define concrete commands and mandatory gates, while the Context template keeps brief defaults. This release also aligns Planning, Commands, and Runtime on command tables and task-declaration handoffs.

v1.12.0 adds initial full capability inventory, incremental updates, and repeatable full reconciliation, and makes the capability catalog easier for users and PMs to read. Planning tasks include documentation-impact acceptance; Auto Fix requires a valid capability-documentation check before successful completion or commit.

Release packages continue to provide skills that can be installed by copying their folders. After an upgrade, older write-mode runs that lack the documentation check but already have a successful outcome or final receipt lose their previous completion claim and require revalidation. See the [changelog](CHANGELOG.en.md) and [Bugfix guide](docs/BUGFIX_GUIDE.en.md) for migration boundaries.

## Skills (8 discoverable skills)

### Project Contract / Governance

| Skill | Purpose |
|---|---|
| `dev-harness-context` | Initialize or refresh project context and the contract index. |
| `dev-harness-docs` | Organize the documentation root, navigation, sources of truth, Capability Catalog, archives, and verified facts. |
| `dev-harness-planning` | Maintain one authoritative active Dashboard, task packets with readiness gates for handoff, milestone archives, and planning drift checks. |
| `dev-harness-commands` | Map real project commands to `build / test / quick / bugfix / full`. |
| `dev-harness-git-workflow` | Discover or initialize project-owned Git, commit, tag, changelog, and release conventions. |
| `dev-harness-retro` | Produce FACT / POLICY / LESSON retrospective candidates only when explicitly requested. |

### Evidence-driven Long-running Workflows

| Skill | Purpose |
|---|---|
| `dev-harness-auto-fix` | Repair known bugs with reproduction, root-cause hypotheses, RED/GREEN, and diff-bound evidence, with verification selected by the `fast / standard / strict` risk profile. |
| `dev-harness-codebase-audit` | Audit large codebases in stages, persist evidence in batches, generate compact documents, and reconcile cross-module findings. |

Each skill carries its own templates, references, and scripts. This repository provides the engineering contracts and Skills Bundle; [dev-harness-runtime](https://github.com/Dev-Wiki/dev-harness-runtime/blob/main/README.en.md) executes Planning Tasks, handling task selection, Worker dispatch, independent acceptance, authorization, state, and recovery. See the [Runtime integration boundary](docs/WORKFLOW.en.md#6-runtime-integration-boundary) for usage and the [Runtime installation guide](https://github.com/Dev-Wiki/dev-harness-runtime/blob/main/README.en.md#install-the-codex-plugin) (English) for installation.

Installing this Skills Bundle does not install `dhr` or enable a host Executor. Consult the [Runtime platform matrix](https://github.com/Dev-Wiki/dev-harness-runtime/blob/main/docs/PLATFORM_MATRIX.en.md) for platform evidence. The complete Audit / Finding / Auto Fix / QA workflow remains a composition of skills rather than a built-in Runtime pipeline.

## Sources of truth

| Changing fact | Authoritative owner |
|---|---|
| Project context and managed sections in root documents | Context |
| Confirmed verification commands | `HARNESS.md` |
| Documentation root, navigation, sources of truth, and global archive governance | Docs; Planning owns task lifecycle and archive content within `plan/` |
| Currently supported capabilities | Capability Catalog or an existing equivalent |
| Active task state and implementation details | State only in `<docs-root>/plan/Dashboard.md`; implementation details in `tasks/` |
| Git, tags, releases, and changelog | Project Git policy and `CHANGELOG.md` |
| Audit Findings and evidence | `<docs-root>/audit/` and the corresponding private Git state |

Plans do not establish current support, and commit history does not replace the capability catalog. Other documents should link to the authoritative source instead of copying its state.

## Documentation

- [Documentation index](docs/README.en.md): routes for use, maintenance, scope, and design records, with translation status.
- [End-to-end workflow](docs/WORKFLOW.en.md): recommended stages for feature delivery and codebase audit / repair.
- [Capability catalog](docs/CAPABILITIES.en.md): currently supported capabilities and their verification evidence.
- [Client project onboarding](docs/CLIENT_PROJECT_ONBOARDING.en.md): initialize the project contracts.
- [Testing](docs/TESTING.en.md): verification entry points and evidence requirements for this repository.
- [Git workflow](docs/GIT_WORKFLOW.en.md): commit and release rules for this repository.
- [Version boundaries](docs/V1_V2_BOUNDARIES.en.md) and [V2 backlog](docs/V2_BACKLOG.en.md): current commitments and future candidates.

## Design boundaries

dev-harness does not aim to cover the entire SDLC or accumulate generic development tutorials. It does not replace the project's toolchain, UI automation platform, observability platform, or release system. It keeps context, planning, verification, documentation, Git boundaries, and long-term evidence consistent across assistants.

## Language coverage

The READMEs, user guides, capability catalog, version and upgrade information, advanced references, and contributor documents have corresponding Chinese and English bodies; start from the [English documentation index](docs/README.en.md). Historical design records, original verification evidence, and internal Agent execution contracts retain their original language and are identified explicitly. Linked specialist documents remain authoritative for detailed behavior.

Several skills accept explicit requests for English reports. Codebase Audit has a bilingual renderer with `output_language` set to `zh-CN` or `en`. End-to-end English project contracts and Runtime Planning are not yet supported: Context generation and refresh, as well as Runtime's Planning and acceptance checks, still depend on fixed Chinese headings or labels. Preserve those structural labels when preparing tasks for Runtime.

To request English audit artifacts explicitly:

```text
Initialize a codebase audit from the project Context. Write all audit artifacts in English only.
```

## Local verification

The [repository verification contract](HARNESS.en.md) owns commands and verification boundaries. From this repository's root, with Python 3 and Git installed:

```bash
python3 -m unittest discover -s tests -v
git diff --check
```

## License

MIT
