# CLIENT_PROJECT_ONBOARDING

[English](CLIENT_PROJECT_ONBOARDING.en.md) | [简体中文](CLIENT_PROJECT_ONBOARDING.md)

Use this guide to onboard a client project that has not previously used AI engineering workflows into `dev-harness`.

## 1. Onboarding goals

V1 first gives AI the essential ability to operate within the project's engineering constraints:

- Know the project type.
- Know where to start reading code.
- Know how to build it.
- Know how to run quick / bugfix / full verification.
- Know which areas cannot be changed freely.

## 2. Minimum onboarding artifacts

After onboarding, at least these context files should exist at the repository root:

- `README.md`
- `AGENTS.md`
- `ARCHITECTURE.md`
- `HARNESS.md`

If they are missing, initialize them with `dev-harness-context` first.

`AGENTS.md` retains only a lightweight project-contract index. The following specialist documents exist as needed; creating all of them is not mandatory:

- Git workflow: the project's existing policy, or `docs/GIT_WORKFLOW.md` initialized by `dev-harness-git-workflow` after confirmation.
- Code style: the project's existing `docs/CODE_STYLE.md`, `CODE_STYLE.md`, or contribution document. Context discovers it but does not generate it.
- Release policy: `docs/RELEASE.md`, or an existing section in `docs/GIT_WORKFLOW.md`.
- Changelog: `CHANGELOG.md`, created only after initialization is confirmed or the first release begins.

After adding or moving these documents, run `dev-harness-context refresh <repo-path>` to update only the managed AGENTS index without overwriting human-maintained content.

For projects with substantial documentation, use `dev-harness-docs` to reuse the existing `doc/` or `docs/` root, create a documentation hub, organize progressive navigation by reader task, and define sources of truth and archive rules. Establish a Capability Catalog when current capability facts are scattered, support varies by role / platform / version, or support cannot be counted reliably; reuse an equivalent capability document when one exists. Small projects can keep a single-level index without mandatory empty directories, `nav/`, or a separate catalog directory.

Maintain capabilities through initial full inventory → incremental updates after each delivery → periodic full reconciliation. Reader-facing prose serves users and PMs, with technical evidence expandable on demand. Repeated full reconciliation keeps existing feature IDs and records coverage. See [capability maintenance](../dev-harness-docs/references/capability-maintenance.en.md).

Codebase Audit applies to user-owned or explicitly authorized repositories and audits engineering quality, behavioral correctness, and cross-module consistency. It is not a penetration-testing or offensive-security workflow. Its stable entry point is `<docs-root>/audit/Report.md`. Audit maintains evidence only within `audit/`; if the hub lacks a link to the report, Docs Refresh adds one idempotently. A root README shortcut is optional.

Audit artifacts default to natural Chinese, preserving Finding / Task IDs, P0–P3, internal state enums, paths, code symbols, commands, and other necessary English identifiers. Request English-only documents explicitly when invoking it. Language affects presentation only and does not change Snapshot or Finding identity.

Common requests:

```text
# Current capability facts are scattered across documents
Inventory this repository's currently supported capabilities. Create or refresh a Capability Catalog when needed.

# Start a large codebase audit and make its results discoverable
Initialize a codebase audit from the project Context. If the documentation hub lacks an audit/Report.md link, refresh navigation first.

# Request English audit artifacts
Initialize a codebase audit from the project Context. Write all audit documents in English only.
```

## 3. First-onboarding checks

For a client project, identify at least:

- **Project type:** WPF / Harmony / Win32 / Qt / Unknown.
- **Primary build entry point.**
- **Quick verification entry point.**
- **Bugfix verification entry point.**
- **Full verification entry point.**
- **Log output locations.**
- **High-risk directories.**
- **Areas AI must not modify directly.**

## 4. Client-project concerns

### WPF

- `*.xaml` and `App.xaml` often affect UI resource merging and startup.
- `*.csproj` affects references, packaging, and build behavior.
- Local `full` normally means a full solution-level `dotnet build`, rather than producing an installer or release package.
- Without tests, establish at least a minimal build and smoke verification command.

### Win32 applications

- `*.vcxproj`, `*.sln`, and `*.rc` often determine the build chain, resource packaging, and entry-point structure.
- Mark `WinMain`, window message loops, and resource scripts as high risk where present.
- Local `full` normally means a complete solution-level `msbuild`; do not mix local packaging or installer generation into `full`.
- If only traces of `Win32 API` usage are identified and the command entry point is unclear, keep `Unknown` in `HARNESS.md` instead of inventing a command.

### Qt

- `CMakeLists.txt` / `*.pro` determine build topology.
- `*.ui` may interact with generated code.
- Mark resource files and platform bridge layers as high risk separately.

### Harmony

- The `hvigor` build chain and `*.json5` configuration are usually key entry points.
- If `buildScript/app_build.sh` and `buildScript/*_package.py` exist, record local `hvigorw assembleHap ...` / `hvigorw assembleApp ...` separately from the complete custom packaging chain.
- Local `full` should normally represent full compilation or an all-module build. Jenkins packaging belongs to `package/release-only` and should not directly occupy the `full` entry in `HARNESS.md`.
- Module definitions, signing, and packaging configuration are high risk by default.
- Record device or emulator requirements for local verification in `HARNESS.md`.

## 5. AI modification boundaries

Define at least these categories:

- **May modify directly:** ordinary product code and noncritical logic layers.
- **Requires human confirmation before changes:** UI resources, packaging configuration, native bridges, and signing-related areas.
- **Must not modify directly:** generated directories, third-party dependencies, and private build artifacts.

## 6. Definition of completion

A client project has completed V1 onboarding when at least:

1. AI can read the complete context files.
2. AI can find the build entry point.
3. AI can find at least two of quick / bugfix / full, with missing entries explicitly marked `Unknown`.
4. AI knows the high-risk and prohibited areas.
5. Missing commands are reported instead of producing fabricated completion claims.
6. Existing Git, code, release, and changelog policies are linked from the AGENTS index to their authoritative documents; absent policies are explicitly `Unknown`.
