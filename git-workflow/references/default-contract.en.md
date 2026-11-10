# Confirmable default Git contract

[English](default-contract.en.md) | [简体中文](default-contract.md)

Use this reference only when the repository lacks an authoritative policy for the topic and the user has explicitly accepted the defaults.

## Branches and commits

- The project confirms `single-branch` or `feature-branch`. Do not create a branch in advance when the mode or requested action does not require it.
- Default commit format uses Conventional Commits: `<type>(<scope>): <中文描述>`, with optional `scope`. The description defaults to natural Chinese; use natural English when the user explicitly requests it.
- Repository-owned branch, commit-format, and language policies always take precedence over these defaults.

## Tags and release notes

- Use annotated `vMAJOR.MINOR.PATCH` tags by default; prereleases may append `-PRERELEASE`.
- Tag annotations and release notes must come from the matching version in `CHANGELOG.md`.
- Nonempty categories appear in this order: Breaking Changes, Added, Changed, Deprecated, Fixed, Removed, Security.
- Stop if the matching changelog version is missing. Do not invent release facts from commit subjects without confirmation.

## Exact changed-file ownership

When the caller provides a `WorkspaceSnapshot` and its owned changed-file set, stage only those paths with `git add -- <file>`. Stop on staged-scope conflicts, sensitive files, truncated diffs, or snapshot drift. Commit authorization does not authorize push, PR, tag, release, or deploy.
