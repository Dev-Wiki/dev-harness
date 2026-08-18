# Confirmable default Git contract

Use this reference only when the repository has no authoritative rule for the topic and the user has explicitly accepted a default.

## Branches and commits

- Branch mode is either project-confirmed `single-branch` or `feature-branch`; never create a branch before the mode or requested action requires it.
- Default commit shape is Conventional Commits: `<type>(<scope>): <description>`, with optional scope.
- Repository-specific branch and commit rules always override these defaults.

## Tags and release notes

- Default tags are annotated `vMAJOR.MINOR.PATCH`; pre-releases may append `-PRERELEASE`.
- Build tag annotations and release notes from the matching `CHANGELOG.md` version.
- Emit non-empty categories in this order: Breaking Changes, Added, Changed, Deprecated, Fixed, Removed, Security.
- Stop when the matching changelog entry does not exist; never synthesize release facts from commit subjects without confirmation.

## Exact changed-file ownership

When a caller supplies a WorkspaceSnapshot and owned changed-file set, stage only those paths with `git add -- <file>`. Stop on staged scope conflicts, sensitive files, truncated diffs, or snapshot drift. Commit authorization never implies push, PR, tag, release, or deploy authorization.
