# dev-harness

[English](README.en.md) | [简体中文](README.md)

**A project engineering contract layer for AI coding assistants.** dev-harness connects project context, documentation, planning, verification commands, and Git policy, with durable evidence workflows for feature delivery, bug fixes, and codebase audits.

It is built around three goals:

- **Consistency:** project rules remain stable across assistants and sessions.
- **Evidence:** completion claims are backed by code, diffs, tests, or runtime evidence.
- **Continuity:** long tasks can resume from project documents and private Git state.

The Skills Bundle supports Cursor, Codex CLI, OpenCode, and Antigravity. Automatic Planning Task execution is provided separately by [dev-harness-runtime](https://github.com/Dev-Wiki/dev-harness-runtime/blob/main/README.en.md).

## Quick start

After [installing the skills](#install), open your project in your AI assistant and describe the task:

```text
# Onboard a repository
Scan this repository and generate project context. Identify the real verification commands and existing Git policy.

# Prepare feature delivery
Create one active Planning Dashboard and bounded task packets with scope, acceptance criteria, and verification steps.

# Organize documentation
Organize this project's existing documentation root and sources of truth. Sync only facts backed by implementation or successful verification.

# Fix a known bug
Auto fix this bug in fix mode: opening Settings after login crashes. Write the report in English.

# Audit a codebase
Initialize a codebase audit from the canonical project context. If the documentation hub lacks an audit/Report.md link, refresh that navigation first. Write all audit artifacts in English only.

# Request a retrospective explicitly
retro: summarize this task and propose FACT, POLICY, and LESSON candidates in English.
```

Commit, push, PR, tag, release, and deployment actions each require explicit authorization.

English prompts do not automatically select English for every generated document. See [language coverage](#language-coverage) before translating project contracts or Planning packets.

## Install

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

## Skills

| Skill | Purpose |
|---|---|
| `dev-harness-context` | Initialize or refresh project context in README, ARCHITECTURE, AGENTS, and HARNESS. |
| `dev-harness-docs` | Organize the existing documentation root, navigation, sources of truth, capability catalog, and verified facts. |
| `dev-harness-planning` | Maintain one active Dashboard, bounded task packets, readiness checks, and milestone archives. |
| `dev-harness-commands` | Map real project commands to `build / test / quick / bugfix / full`. |
| `dev-harness-git-workflow` | Discover or initialize project-owned Git, commit, tag, changelog, and release conventions. |
| `dev-harness-retro` | Produce retrospective candidates only when explicitly requested. |
| `dev-harness-auto-fix` | Diagnose and repair known bugs with reproducible evidence and validation proportional to impact. |
| `dev-harness-codebase-audit` | Audit engineering quality, correctness, and cross-module consistency without changing product source. |

Each skill carries its own templates, references, and scripts. The [capability catalog](docs/CAPABILITIES.md) (Chinese) owns current support details; the [changelog](CHANGELOG.md) (Chinese) owns release history.

## Runtime integration

Install the [Runtime plugin](https://github.com/Dev-Wiki/dev-harness-runtime/blob/main/README.en.md#install-the-codex-plugin) separately to execute prepared Planning Tasks. It handles task selection, Worker dispatch, independent acceptance, authorization, state, and recovery.

Installing this Skills Bundle does not install `dhr` or enable a host Executor. Consult the [Runtime platform matrix](https://github.com/Dev-Wiki/dev-harness-runtime/blob/main/docs/PLATFORM_MATRIX.md) (Chinese) for platform evidence. The complete Audit / Finding / Auto Fix / QA workflow remains a composition of skills rather than a built-in Runtime pipeline.

## Language coverage

The project overview, installation instructions, quick start, and [documentation index](docs/README.en.md) are available in English. Specialist guides are marked by language in the index; most are currently Chinese. Their linked source documents remain authoritative for detailed behavior.

Several skills accept explicit requests for English reports. Codebase Audit has a bilingual renderer with `output_language` set to `zh-CN` or `en`. End-to-end English project contracts and Runtime Planning are not yet supported: Context generation and refresh, as well as Runtime's Planning and acceptance checks, still depend on fixed Chinese headings or labels. Preserve those structural labels when preparing tasks for Runtime.

## Documentation and development

- [English documentation index](docs/README.en.md): onboarding, workflow, verification, bug fixes, support, and maintenance routes, with translation status.
- [Chinese documentation index](docs/README.md).
- [Repository verification contract](HARNESS.md) (Chinese): authoritative commands and verification boundaries.
- [Git workflow](docs/GIT_WORKFLOW.md) (Chinese): contribution and release conventions.

From this repository's root, with Python 3 and Git installed:

```bash
python3 -m unittest discover -s tests -v
git diff --check
```

Maintainers generate the local versioned Skill zip with `python release.py`; this does not publish a release.

## License

MIT
