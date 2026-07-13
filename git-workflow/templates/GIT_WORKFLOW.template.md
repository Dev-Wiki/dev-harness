# Git Workflow Contract

This document is the repository-owned contract for branches, commits, tags, changelog entries, and release messages.

## Branch Mode

**Confirmed mode**: `{single-branch | feature-branch}` — 由项目确认后保留一个值。

- `single-branch`: development may continue directly on the configured default branch.
- `feature-branch`: use `feat/`, `fix/`, `docs/`, `refactor/`, `test/`, `perf/`, or `chore/` prefixes.

Do not create or switch branches unless required by the confirmed mode or explicitly requested by the user.

## Commit Convention

Use Conventional Commits:

```text
<type>(<scope>): <description>
```

`scope` is optional. Allowed default types:

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

Descriptions state the concrete purpose of the change. Repository-specific issue references may be added only when the project defines them.

## Tags

- Use SemVer annotated tags in `vMAJOR.MINOR.PATCH` form.
- Pre-releases may use `vMAJOR.MINOR.PATCH-PRERELEASE`.
- Do not create or replace a tag without an explicit release/tag request.

## Changelog

The default changelog is `CHANGELOG.md`. It is initialized only after explicit confirmation or when starting the first release.

Release categories use this order:

1. `Breaking Changes`
2. `Added`
3. `Changed`
4. `Deprecated`
5. `Fixed`
6. `Removed`
7. `Security`

`Removed` is the removal category. Finalized version entries omit empty categories.

## Tag Annotation and Release Notes

Generate both from the matching changelog version:

```text
Release vMAJOR.MINOR.PATCH

<non-empty categorized changelog entries>
```

Preserve the category order above and omit empty categories. If the matching changelog version is missing, stop and request confirmation before creating it; do not fabricate release content from commit subjects.

## Commit Safety

Before committing:

- inspect the complete working tree and staged diff;
- preserve an existing staged-file boundary;
- stop on suspected secrets, credentials, large accidental files, or unrelated changes;
- stop on temporary debug output such as `Console.WriteLine`, `Debug.Log`, or bare `print(` unless the project confirms it is intentional.
