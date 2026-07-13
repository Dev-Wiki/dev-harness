# Open-Source Git Workflow Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace company-coupled Git rules with repository-owned contract discovery, safe fallback templates, and a lightweight AGENTS index for Git, code-style, release, and changelog documents.

**Architecture:** Add a focused `context/contracts.py` discovery module and feed its immutable `ContractIndex` into AGENTS rendering. Keep Git Workflow agent-driven rather than adding a CLI: its SKILL reads existing repository standards first and uses packaged Markdown templates only after user confirmation.

**Tech Stack:** Python 3 standard library, `dataclasses`, `pathlib`, `unittest`, Markdown skill/templates.

## Global Constraints

- Work directly on the current branch; do not create a Git worktree or development branch.
- Use TDD for each behavior change and commit each completed task separately.
- Repository-owned standards always outrank dev-harness defaults.
- Context only discovers and indexes standards; it never creates Git, code-style, release, or changelog policy files.
- Existing standard documents are never overwritten.
- Default policy creation requires explicit user confirmation.
- `CHANGELOG.md` is created only after confirmed changelog initialization or when starting the first release flow.
- Use `Removed`, never `Deleted`, in the default release categories.
- Omit empty categories from generated tag annotations and release notes.
- Do not encode company names, product baselines, private branch patterns, or mandatory branch creation into the open-source defaults.

---

### Task 1: Discover repository-owned contracts and render the AGENTS index

**Files:**
- Create: `context/contracts.py`
- Modify: `context/cli.py`
- Modify: `context/templates/AGENTS.template.md`
- Modify: `install.py`
- Create: `tests/test_contract_discovery.py`
- Modify: `tests/test_context_cli.py`

**Interfaces:**
- Produces: `ContractIndex(build, git_workflow, code_style, release, changelog)` and `discover_contract_index(repo_root: Path) -> ContractIndex`.
- Consumes: valid repository-relative references already present in the managed `agents.contract-index` block, followed by deterministic filename candidates.

- [ ] **Step 1: Write failing discovery and refresh tests**

Create tests that assert:

```python
def test_prefers_valid_existing_agents_reference_over_default_candidate() -> None:
    # company/GIT_RULES.md is referenced by AGENTS and docs/GIT_WORKFLOW.md also exists.
    # discover_contract_index returns company/GIT_RULES.md.

def test_rejects_contract_symlink_outside_repository() -> None:
    # docs/GIT_WORKFLOW.md points outside repo; result is Unknown.

def test_scan_indexes_known_contract_documents() -> None:
    # docs/GIT_WORKFLOW.md, docs/CODE_STYLE.md, docs/RELEASE.md, CHANGELOG.md exist.
    # Generated AGENTS contains all four repository-relative paths plus HARNESS.md.

def test_refresh_updates_only_contract_index_after_document_is_added() -> None:
    # scan first, add docs/GIT_WORKFLOW.md, refresh --force.
    # Index changes from Unknown to path and user text outside markers remains.
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
python -m unittest tests.test_contract_discovery \
  tests.test_context_cli.ContextCliTests.test_scan_indexes_known_contract_documents \
  tests.test_context_cli.ContextCliTests.test_refresh_updates_only_contract_index_after_document_is_added -v
```

Expected: import failure for `context.contracts` and static `Unknown` index values.

- [ ] **Step 3: Implement deterministic safe discovery**

Create `context/contracts.py` with:

```python
@dataclass(frozen=True)
class ContractIndex:
    build: str
    git_workflow: str
    code_style: str
    release: str
    changelog: str

def discover_contract_index(repo_root: Path) -> ContractIndex:
    # Parse current managed index references when AGENTS.md is valid UTF text.
    # Accept only existing regular files whose resolved path stays under repo_root.
    # Fall back through the exact priority lists in the approved design.
    # Return repository-relative POSIX paths or "Unknown".
```

The build entry is always `HARNESS.md`, because Context creates it in the same initialization set. Add `contracts.py` to `CONTEXT_RUNTIME_FILES`.

- [ ] **Step 4: Render the five-entry managed index and remove company policy**

Change the template to use:

```markdown
- 构建与验证：`{构建规范路径}`
- Git 工作流：{Git规范路径或 Unknown}
- 代码规范：{代码规范路径或 Unknown}
- 发布规范：{发布规范路径或 Unknown}
- 变更日志：{变更日志路径或 Unknown}
```

Render known paths as backticked repository-relative paths and `Unknown` without backticks. Delete the entire `## 14. 公司 Git 门禁规范` section and renumber AI navigation knowledge to section 14. Call `discover_contract_index` once in `generate_context_files` and pass the result to `render_agents`.

- [ ] **Step 5: Run focused and complete Context tests**

Run:

```bash
python -m unittest tests.test_contract_discovery tests.test_context_cli tests.test_managed_context -v
```

Expected: all tests pass and Context refresh preserves user-owned text.

- [ ] **Step 6: Commit contract discovery**

```bash
git add context/contracts.py context/cli.py context/templates/AGENTS.template.md install.py tests/test_contract_discovery.py tests/test_context_cli.py
git commit -m "feat(context): index repository-owned contracts"
```

### Task 2: Replace company Git rules with confirmed open-source defaults

**Files:**
- Rewrite: `git-workflow/SKILL.md`
- Rewrite: `docs/GIT_WORKFLOW.md`
- Create: `git-workflow/templates/GIT_WORKFLOW.template.md`
- Create: `git-workflow/templates/CHANGELOG.template.md`
- Delete: `tests/test_branch_rules.py`
- Create: `tests/test_git_workflow_contract.py`

**Interfaces:**
- Consumes: repository standards discovered through AGENTS and conventional paths.
- Produces: agent workflow for `discover -> infer if absent -> present candidate -> confirm -> initialize/enforce`, plus reusable Git and changelog templates.

- [ ] **Step 1: Write failing open-source contract tests**

Add tests that read the skill, canonical documentation, and templates and assert:

```python
RELEASE_CATEGORIES = (
    "Breaking Changes", "Added", "Changed", "Deprecated",
    "Fixed", "Removed", "Security",
)

def test_templates_use_confirmed_release_categories_in_order() -> None:
    # Each category exists in order; "Deleted" is absent.

def test_skill_prioritizes_project_rules_and_requires_confirmation() -> None:
    # Existing standards outrank defaults; initialization says explicit confirmation.

def test_defaults_support_single_branch_and_feature_branch_modes() -> None:
    # Neither mode is silently mandatory.

def test_tag_and_release_messages_omit_empty_categories() -> None:
    # Skill specifies changelog-derived categorized messages and empty-category omission.

def test_open_source_contract_has_no_company_branch_baselines() -> None:
    # Former master_5.2/private_/dated release fixtures and company gate copy are absent.
```

- [ ] **Step 2: Run tests and verify RED**

```bash
python -m unittest tests.test_git_workflow_contract -v
```

Expected: missing templates and company-coupled AGENTS/branch fixtures fail the new contract.

- [ ] **Step 3: Create the default Git workflow template**

The template must contain:

- a user-selected `single-branch` or `feature-branch` mode;
- Conventional Commits types `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`;
- annotated `vMAJOR.MINOR.PATCH` SemVer tags;
- `CHANGELOG.md` as the default changelog;
- release sections in the seven-category order;
- tag annotation and release note generation from the matching changelog version;
- an explicit rule to omit empty categories.

- [ ] **Step 4: Create the changelog authoring template**

Use:

```markdown
# Changelog

## Unreleased

### Breaking Changes
### Added
### Changed
### Deprecated
### Fixed
### Removed
### Security
```

Explain that empty headings are authoring prompts and are removed from finalized version entries and release messages.

- [ ] **Step 5: Rewrite the skill and canonical documentation**

The skill must:

1. read AGENTS-referenced standards first;
2. inspect at most 100 commit subjects, branches, tags, contribution docs, and changelog only if no standard exists;
3. distinguish existing-history inference from new-repository defaults;
4. show candidates and obtain explicit confirmation before creating policy files;
5. initialize from packaged templates without overwriting existing files;
6. direct Context `refresh` after selection/creation;
7. keep commit/tag/release mutations behind explicit corresponding user requests;
8. preserve debug-artifact and sensitive-file commit checks without imposing company naming rules.

Rewrite `docs/GIT_WORKFLOW.md` as the repository's canonical example of the same open-source contract. Remove the executable company fixture test file.

- [ ] **Step 6: Run workflow contract tests and Context regressions**

```bash
python -m unittest tests.test_git_workflow_contract tests.test_context_cli -v
rg -n "master_5\.2|release_pub|private_|公司 Git 门禁" context git-workflow docs/GIT_WORKFLOW.md tests
```

Expected: tests pass and `rg` returns no matches in the scoped open-source surfaces.

- [ ] **Step 7: Commit the open-source workflow contract**

```bash
git add git-workflow/SKILL.md git-workflow/templates docs/GIT_WORKFLOW.md tests/test_git_workflow_contract.py tests/test_branch_rules.py
git commit -m "feat(git-workflow): add repository-owned workflow defaults"
```

### Task 3: Package Git Workflow templates

**Files:**
- Modify: `install.py`
- Modify: `tests/test_install.py`

**Interfaces:**
- Produces: installed `dev-harness-git-workflow/templates/GIT_WORKFLOW.template.md` and `CHANGELOG.template.md`.
- Consumes: templates created in Task 2.

- [ ] **Step 1: Write the failing installation test**

```python
def test_installed_git_workflow_includes_default_templates(self) -> None:
    install_bundle_to_root(bundle_root, ["dev-harness-git-workflow"])
    skill_root = bundle_root / "skills" / "dev-harness-git-workflow"
    self.assertTrue((skill_root / "templates" / "GIT_WORKFLOW.template.md").exists())
    self.assertTrue((skill_root / "templates" / "CHANGELOG.template.md").exists())
```

- [ ] **Step 2: Run the test and verify RED**

```bash
python -m unittest tests.test_install.InstallBundleTests.test_installed_git_workflow_includes_default_templates -v
```

Expected: installed template paths do not exist.

- [ ] **Step 3: Add validation and a dedicated installer builder**

Add:

```python
GIT_WORKFLOW_TEMPLATE_FILES = (
    "GIT_WORKFLOW.template.md",
    "CHANGELOG.template.md",
)

def build_dev_harness_git_workflow(_skill_name: str, destination: Path) -> None:
    build_skill("dev-harness-git-workflow", destination)
    templates_dir = destination / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    for file_name in GIT_WORKFLOW_TEMPLATE_FILES:
        shutil.copy2(GIT_WORKFLOW_TEMPLATE_DIR / file_name, templates_dir / file_name)
```

Validate both sources and register the builder in `BUILDERS`.

- [ ] **Step 4: Run installer and complete tests**

```bash
python -m unittest tests.test_install -v
```

Expected: all installation tests pass.

- [ ] **Step 5: Commit template packaging**

```bash
git add install.py tests/test_install.py
git commit -m "feat(installer): package git workflow templates"
```

### Task 4: Document ownership and perform the final audit

**Files:**
- Modify: `context/SKILL.md`
- Modify: `docs/CLIENT_PROJECT_ONBOARDING.md`
- Modify: `docs/HARNESS_GUIDE.md`
- Modify: `README.md`

**Interfaces:**
- Documents: Context recognition-only behavior, Git Workflow initialization ownership, repeat-refresh flow, changelog lifecycle, and specialist-document indexing.

- [ ] **Step 1: Update user-facing workflow documentation**

Document these exact rules:

- AGENTS is a lightweight index, not a container for every standard;
- Context recognizes and refreshes paths but does not create specialist policy or changelog files;
- Git Workflow reads project/company standards first and initializes a confirmed fallback only when none exist;
- code-style documents are recognized but never auto-generated;
- `CHANGELOG.md` is optional until confirmed initialization or first release;
- release categories use `Removed` and omit empty categories;
- adding custom standards is completed by running Context `refresh`.

Preserve the existing CRLF style of `docs/HARNESS_GUIDE.md`.

- [ ] **Step 2: Run full verification**

```bash
python -m unittest discover -s tests -v
git -c core.whitespace=cr-at-eol diff --check
rg -n "master_5\.2|release_pub|private_|公司 Git 门禁" context git-workflow docs/GIT_WORKFLOW.md tests
git status --short
```

Expected: all tests pass, no whitespace errors, no company-coupled matches, and only Task 4 documentation is uncommitted.

- [ ] **Step 3: Commit documentation**

```bash
git add context/SKILL.md docs/CLIENT_PROJECT_ONBOARDING.md docs/HARNESS_GUIDE.md README.md
git commit -m "docs: explain project-owned workflow contracts"
```

- [ ] **Step 4: Perform the post-commit audit**

Re-run the full test suite, whitespace check, company-rule scan, and `git status --short`. Compare the implementation against every requirement in `docs/superpowers/specs/2026-07-13-open-source-git-workflow-design.md`; do not report completion unless the worktree is clean and every check passes.
