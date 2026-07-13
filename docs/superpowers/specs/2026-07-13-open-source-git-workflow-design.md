# Open-Source Git Workflow and Project Contract Index Design

## Goal

Decouple `dev-harness-git-workflow` from company-specific branch rules and make it a reusable open-source workflow skill that:

1. follows repository-owned standards when they exist;
2. proposes, confirms, and initializes a small Git workflow contract only when standards are absent;
3. lets `dev-harness-context` keep a lightweight index of build, Git, code-style, release, and changelog contracts in `AGENTS.md`;
4. defines clear default commit, tag, changelog, and release-message behavior for new repositories.

## Ownership Boundaries

### `dev-harness-context`

Context discovers contract documents and writes only their paths into the managed `agents.contract-index` block. It does not create `CHANGELOG.md`, code-style rules, Git rules, or release rules. `scan` initializes missing context files; `refresh` updates the managed index after users add, rename, or remove contract documents.

The index has five entries:

- Build and verification
- Git workflow
- Code style
- Release
- Changelog

Discovery uses repository-relative paths and deterministic priority lists. Unknown items remain `Unknown`; Context must not infer prose rules into `AGENTS.md`.

### `dev-harness-git-workflow`

Git Workflow owns discovery, selection, initialization, and enforcement guidance for Git-related contracts. It does not own build commands, application code style, CI deployment, pushing, pull-request creation, or company policy.

It never replaces an existing project standard. If multiple candidates exist, it reports them and asks the user to select the authoritative document. After a document is selected or created, it directs the user or agent to run Context `refresh` so the managed AGENTS index is updated; it does not edit the managed block directly.

### Repository-owned standards

Project-specific and company-specific rules remain in the target repository. They may use any filename or structure. Once referenced by the AGENTS contract index, AI agents treat the referenced document as authoritative. Open-source dev-harness templates remain fallbacks, not higher-priority policy.

## Contract Discovery

Context recognizes these candidates in priority order.

### Git workflow

1. A current valid path already present in the AGENTS contract index
2. `docs/GIT_WORKFLOW.md`
3. `.github/CONTRIBUTING.md`
4. `CONTRIBUTING.md`
5. `GIT_WORKFLOW.md`

### Code style

1. A current valid path already present in the AGENTS contract index
2. `docs/CODE_STYLE.md`
3. `CODE_STYLE.md`
4. `.github/CONTRIBUTING.md`
5. `CONTRIBUTING.md`

Formatter and linter configuration files are evidence, not human-readable contract documents, so they are not placed in the AGENTS index.

### Release

1. A current valid path already present in the AGENTS contract index
2. `docs/RELEASE.md`
3. `RELEASE.md`
4. `docs/GIT_WORKFLOW.md`
5. `.github/CONTRIBUTING.md`
6. `CONTRIBUTING.md`

### Changelog

1. A current valid path already present in the AGENTS contract index
2. `CHANGELOG.md`
3. `docs/CHANGELOG.md`
4. `HISTORY.md`

Discovery is case-sensitive and only accepts existing regular files inside the repository. Symlinks that resolve outside the repository are rejected. When multiple same-priority user references conflict, Context outputs `Unknown` plus a manual-review candidate instead of choosing silently.

## Existing Repository Flow

When an authoritative Git workflow document exists, the skill reads and follows it. Missing topics are reported as gaps; open-source defaults are not silently merged into the project standard.

When no authoritative document exists, the skill inspects read-only evidence:

- default branch and active branches;
- up to 100 recent commit subjects;
- existing tags sorted by version and creation date;
- release/changelog files;
- contribution and pull-request templates;
- current single-branch or multi-branch practice.

It produces a candidate summary for branch mode, commit format, tag format, changelog location, and release categories. The candidate must be confirmed by the user before creating `docs/GIT_WORKFLOW.md`. History is evidence, not authority: ambiguous or inconsistent history produces the documented default plus an explicit warning.

## New Repository Defaults

For a repository without meaningful Git history, the proposed GitHub-friendly defaults are:

- Branch mode: ask the user to choose single-branch or feature-branch development. Single-branch mode allows direct work on the configured default branch; feature-branch mode uses `feat/`, `fix/`, `docs/`, `refactor/`, `test/`, `perf/`, and `chore/` prefixes.
- Commits: Conventional Commits using `type(scope): description`, with optional scope and types `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, and `revert`.
- Tags: annotated SemVer tags in `vMAJOR.MINOR.PATCH` form. Pre-releases may use `vMAJOR.MINOR.PATCH-PRERELEASE`.
- Release contract: stored in `docs/GIT_WORKFLOW.md` by default. Teams may split it into `docs/RELEASE.md`; Context then indexes the split document.
- Changelog: not created by Context initialization. `dev-harness-git-workflow` creates `CHANGELOG.md` only when the user confirms changelog initialization or starts the first release flow.

No default is written until the user confirms the candidate.

## Changelog and Release Message Contract

The default changelog uses an `Unreleased` section and version sections. Within each release, categories appear in this order:

1. `Breaking Changes`
2. `Added`
3. `Changed`
4. `Deprecated`
5. `Fixed`
6. `Removed`
7. `Security`

Empty categories are omitted from both `CHANGELOG.md` version sections and generated tag/release messages. `Removed` is the canonical removal category; `Deleted` is not used.

Tag annotations and release notes are generated from the matching changelog version. Both use `Release vMAJOR.MINOR.PATCH` as the heading, followed only by non-empty categories and their entries. If no changelog entry exists for the version, the skill stops and asks whether to create one; it must not fabricate changes from commit subjects without confirmation.

## Template and Packaging Design

The installed Git Workflow skill includes:

- `templates/GIT_WORKFLOW.template.md`: the confirmed fallback contract for branch mode, commits, tags, changelog, and releases;
- `templates/CHANGELOG.template.md`: an `Unreleased` skeleton containing the seven categories as authoring prompts.

The changelog template may show all categories while authoring. Release generation removes empty categories. The Git workflow template contains no company names, product baselines, private branch patterns, issue-system assumptions, or mandatory branch creation.

## AGENTS Index Rendering

The managed block remains intentionally small:

```markdown
## 项目规范索引

- 构建与验证：`HARNESS.md`
- Git 工作流：`docs/GIT_WORKFLOW.md` or `Unknown`
- 代码规范：`docs/CODE_STYLE.md` or `Unknown`
- 发布规范：`docs/RELEASE.md`, `docs/GIT_WORKFLOW.md`, or `Unknown`
- 变更日志：`CHANGELOG.md` or `Unknown`
```

Detailed rules stay in specialist documents. Existing user text elsewhere in AGENTS remains untouched by Context refresh.

## Error and Safety Behavior

- Missing standards are not errors; they produce `Unknown` index entries and an initialization offer.
- Existing documents are never overwritten by templates.
- Candidate initialization requires explicit confirmation because it creates project policy.
- Conflicting candidate documents are reported for human selection.
- Git-history inspection is read-only.
- Commit, tag, and release mutations occur only when the user explicitly invokes the corresponding action; initialization alone performs no Git mutation.
- Sensitive files, untracked secrets, and unrelated working-tree changes remain subject to existing commit safety checks.

## Testing

Automated tests verify:

- deterministic Context discovery and AGENTS index rendering;
- refresh updates only the managed index after documents are added;
- company-specific branch fixtures are removed from the open-source baseline;
- Git and changelog templates contain the confirmed defaults and `Removed`, not `Deleted`;
- installed Git Workflow bundles include both templates;
- full Context refresh and installation regression tests continue to pass.

## Non-goals

- A standalone Git workflow CLI
- Automatic conversion of an existing repository to Conventional Commits or SemVer
- Automatic code-style document generation
- Automatic changelog creation during Context scan/refresh
- Automatic tag, release, push, pull request, or deployment operations during initialization
- Encoding company policy into dev-harness
