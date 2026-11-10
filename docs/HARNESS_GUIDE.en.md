# dev-harness HARNESS guide

[English](HARNESS_GUIDE.en.md) | [简体中文](HARNESS_GUIDE.md)

This guide explains how to maintain and use a product repository's `HARNESS.md` verification contract with Cursor, Codex CLI, OpenCode, and Antigravity. For installation and first onboarding, see the [project overview](../README.en.md#install) and [client project onboarding](CLIENT_PROJECT_ONBOARDING.en.md). See the [end-to-end workflow](WORKFLOW.en.md) for stage order across Skills.

Each project's root `HARNESS.md` is the sole source of truth for concrete commands and execution environments. `AGENTS.md` defines behavior, safety, and modification boundaries.

---

## 1. Prerequisites

- The `dev-harness` Skills are installed.
- The product repository has root `AGENTS.md` and `HARNESS.md` files. Initialize missing files with `dev-harness-context` first.
- Commands in `HARNESS.md` must come from actual scripts, build configuration, or successful execution evidence. Do not invent them from technology-stack conventions.

To fill command gaps, invoke this in the product repository:

```text
Use dev-harness-commands to define build / test / quick / bugfix / full commands for this project.
```

## 2. Five verification entry points

`harness:build`, `harness:test`, `harness:quick`, `harness:bugfix`, and `harness:full` are stable semantics. They do not require projects to rewrite existing toolchains or standardize script names.

| Entry | What it establishes |
|---|---|
| `build` | The current target or build graph can compile, generate, or perform an equivalent build |
| `test` | The repository's existing automated test entry point can run |
| `quick` | The shortest trustworthy relevant feedback for frequent iteration |
| `bugfix` | A known issue's reproduction or targeted regression path |
| `full` | The project's confirmed complete local build and test boundary |

Mark packaging, signing, and release chains as `package/release-only` or CI-only; they cannot stand in for local `full`. Record platforms, devices, and build variants separately and select uniquely through Platform / Variant. Record device dependencies in `DeviceRequirement` as well.

`dev-harness-context` maintains only automatically detected candidate commands; `dev-harness-commands` maintains only the human-confirmed area. Candidates are not successful verification evidence. If a confirmed entry remains `Unknown` or `Missing`, stop and complete the contract.

---

## 3. HARNESS.md project build and verification contract

`HARNESS.md` is the sole source of truth for project build, verification, and execution environments. It records real executable commands, operating conditions, and verification boundaries.

An AI Agent must read it before running build, test, or verification commands. It must not guess, substitute, or overwrite its commands based on README, CI configuration, or ecosystem habits. `AGENTS.md` owns behavior, safety, and modification boundaries; `HARNESS.md` owns concrete commands and environments.

### Required areas

The Chinese headings and table labels below are structural contract literals. Preserve them for current Context refresh and Runtime parsing; the surrounding guide is translated for readers.

```markdown
## 自动识别构建命令候选
- **build**: `<自动识别候选或 Unknown>`
- **test**: `<自动识别候选、device-required 或 Unknown>`
- **quick**: `<自动识别候选或 Unknown>`
- **bugfix**: `<自动识别候选或 Unknown>`
- **full**: `<自动识别候选或 Unknown>`

## 已确认命令（人工维护）

| 用途 | 命令 | 状态 |
|---|---|---|
| build | `Unknown` | missing |
| test | `Unknown` | missing |
| quick | `Unknown` | missing |
| bugfix | `Unknown` | missing |
| full | `Unknown` | missing |
```

Automatically detected results remain candidates. `dev-harness-context` refreshes the candidate section by its fixed heading; `dev-harness-commands` may update only `已确认命令（人工维护）` (human-confirmed commands), without writing to or overwriting the candidate section. Execution uses confirmed commands. If they remain `Unknown`, stop and fill the gap instead of directly executing candidates.

### Handoff to Runtime automatic execution

Set a command to `confirmed` only when actual entry points and evidence establish it. A command cell contains exactly one inline code span. Put prerequisites, device requirements, and evidence in extra columns or outside the table. `Unknown`, `Missing`, `N/A`, and `candidate` entries are not automatically executable.

Older lists and fields such as BuildCommand remain usable in manual workflows and are preserved by Context refresh. Before Runtime migration, Commands organizes an evidence-backed human-confirmed table; old headings and detected candidates do not constitute bulk confirmation. Current Runtime requires one command per purpose, a repository-root verification working directory, and at least one confirmed test / quick / bugfix / full entry. It does not select duplicate purposes using extra platform columns.

Automatic execution uses literal argv. It does not interpret `source`, environment assignments, pipes, redirections, `&&`, or shell expansion. If a virtual environment is required, first confirm the Adapter's toolchain, dependencies, and controlled verification environment support it. Rewriting a command grants no new mount or read permissions. Automatic tasks also require a [Runtime handoff declaration](../planning/references/runtime-handoff.en.md); normal manual plans do not.

### Recommended fields

- `CanRunBuildHere`: whether the current environment can build, including cross-platform cases such as WSL.
- `RecommendedTerminal`: the recommended terminal environment.
- `高风险目录` (high-risk directories): areas AI must not modify automatically.
- `禁止操作` (prohibited operations): explicit prohibited actions.

---

## 4. Frequently asked questions

**HARNESS.md commands show Unknown/Missing**

Use `dev-harness-commands` to fill the mapping from repository evidence before continuing development or verification.

**One entry uses different commands on different platforms or Variants**

Create a separate record for each Platform / Variant instead of joining incompatible commands into one. Record device requirements and terminal environments separately.

**Can release-package generation count as full?**

No. `full` means the project's confirmed complete local verification boundary. Packaging, signing, installer creation, and release belong to separate release-only workflows.

---

## 5. References

| Document | Purpose |
|---|---|
| [Project overview](../README.en.md) | Installation, host support, and Skill entry points |
| [Client project onboarding](CLIENT_PROJECT_ONBOARDING.en.md) | Initial setup and minimum contracts |
| [End-to-end workflow](WORKFLOW.en.md) | Feature delivery, audit, and repair stage order |
| [Testing](TESTING.en.md) | Layered verification and evidence requirements |
| [Bugfix guide](BUGFIX_GUIDE.en.md) | Bug descriptions, reproduction, and targeted regression formats |
| [Commands contract](../commands/SKILL.md) | Command-record fields, stop conditions, and ownership boundaries |
