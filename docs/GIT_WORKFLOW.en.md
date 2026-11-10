# Git workflow policy

[English](GIT_WORKFLOW.en.md) | [简体中文](GIT_WORKFLOW.md)

This file is the dev-harness repository's own contract for Git, commits, tags, changelogs, and release messages. Other projects should follow their existing repository policy first; this file is not a company-wide policy imposed on target projects.

## 1. Branch mode

This repository uses the confirmed `single-branch` mode: development and commits may take place directly on the current default branch; automatic feature-branch creation is not required.

For another project without a policy, `dev-harness-git-workflow` asks the user to confirm one mode:

- `single-branch`: work directly on the default branch according to project policy.
- `feature-branch`: use the `feat/`, `fix/`, `docs/`, `refactor/`, `test/`, `perf/`, or `chore/` prefixes.

An existing repository branch policy always takes precedence.

## 2. Commit conventions

Use Conventional Commits:

```text
<type>(<scope>): <description>
```

`scope` is optional. Default types:

- `feat`
- `fix`
- `docs`
- `style`
- `refactor`
- `perf`
- `test`
- `build`
- `ci`
- `chore`
- `revert`

The description should explain the specific purpose of the change. Unless the user explicitly requests English, use natural Chinese by default, for example `feat(planning): 拆分活跃任务并归档历史计划` (split active tasks and archive historical plans). Avoid vague descriptions such as “fix bug” or “update code.”

Before committing, inspect the entire workspace and index. If content is already staged, commit only the staged files. Stop and ask the user when potential secrets, `.env` files, unexpected large files, unrelated changes, or temporary debugging output are found.

## 3. Tag conventions

- Use SemVer annotated tags: `vMAJOR.MINOR.PATCH`.
- Prereleases may use `vMAJOR.MINOR.PATCH-PRERELEASE`.
- Do not create, move, or overwrite tags without an explicit tag or release request.

## 4. Changelog conventions

The default changelog is the root `CHANGELOG.md`. Context's `scan` and `refresh` detect the path only; they do not create the file.

Organize version content in this fixed order:

1. `Breaking Changes`
2. `Added`
3. `Changed`
4. `Deprecated`
5. `Fixed`
6. `Removed`
7. `Security`

Use `Removed` for removals. Omit empty categories when finalizing a version.

## 5. Tag annotations and release notes

Generate both the annotated tag message and release notes from the matching version in `CHANGELOG.md`:

```text
Release vMAJOR.MINOR.PATCH

<Nonempty categories and their entries only>
```

Keep the category order from section 4 and omit empty categories. If the matching version is absent, stop and request completion or confirmation; do not invent release notes from commit subjects without confirmation.

## 6. Debugging residue and sensitive files

Before committing, scan added diff lines, particularly for:

- `Console.WriteLine`
- `Debug.Log`
- Bare `print(`
- `.env`, keys, credentials, and unexpected large files

A match is not necessarily an error, but it must be confirmed as intentional before committing.

## 7. Policy initialization

When the target repository has no Git policy, `dev-harness-git-workflow` first reads at most 100 historical commits, branches, tags, and contribution files. It presents candidates and obtains explicit confirmation before creating `docs/GIT_WORKFLOW.md` from the Skill template.

Create `CHANGELOG.md` only when the user confirms initialization or begins the first release. After creating or selecting the policy, run:

```bash
dev-harness-context refresh <repo-path>
```

This refreshes only the AGENTS policy-path index; detailed rules are not copied into AGENTS.
