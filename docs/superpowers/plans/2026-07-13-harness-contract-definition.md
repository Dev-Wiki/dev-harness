# HARNESS Contract Definition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define `HARNESS.md` as the project build and verification contract and force generated `AGENTS.md` files to route build, test, and verification work through it.

**Architecture:** Keep the existing Markdown-template generation architecture and all current fields. Add contract language to the two built-in templates, protect it with a generated-output regression test, and align the user guide with the current six-skill product surface.

**Tech Stack:** Python 3 standard library, `unittest`, Markdown templates.

## Global Constraints

- `HARNESS.md` is the sole source of truth for command mappings and execution environment.
- `AGENTS.md` remains authoritative for behavior, safety, and modification boundaries.
- Do not change command detection, CLI arguments, template field names, README files, or installation behavior.
- Preserve repository file encodings.
- This repository uses single-branch development; implement directly on the current branch without creating a Git worktree.

---

### Task 1: Generated contract and mandatory navigation

**Files:**
- Modify: `tests/test_context_cli.py`
- Modify: `context/templates/AGENTS.template.md`
- Modify: `context/templates/HARNESS.template.md`

**Interfaces:**
- Consumes: `context.cli.main(["scan", repo_path])` and the existing template renderer.
- Produces: generated `AGENTS.md` and `HARNESS.md` containing stable contract language.

- [ ] **Step 1: Write the failing generated-output test**

Add this test after `test_scan_writes_missing_files` in `ContextCliTests`:

```python
def test_scan_links_agents_to_harness_contract(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = Path(tmp) / "demo-repo"
        repo_root.mkdir()
        (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")

        exit_code = main(["scan", str(repo_root)])

        self.assertEqual(exit_code, 0)
        agents_content = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
        harness_content = (repo_root / "HARNESS.md").read_text(encoding="utf-8")
        self.assertIn("构建与验证契约（AI 必读）", agents_content)
        self.assertIn("执行构建、测试或验证命令前，必须读取项目根目录的 `HARNESS.md`", agents_content)
        self.assertIn("不得猜测、替换或覆盖", agents_content)
        self.assertIn("`Unknown` 或 `Missing`", agents_content)
        self.assertIn("# HARNESS — 项目构建与验证契约", harness_content)
        self.assertIn("构建、验证和执行环境的唯一事实源", harness_content)
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
python -m unittest tests.test_context_cli.ContextCliTests.test_scan_links_agents_to_harness_contract -v
```

Expected: FAIL because the generated files do not yet contain `构建与验证契约（AI 必读）`.

- [ ] **Step 3: Add the mandatory AGENTS navigation**

Insert this section between the project line and the current `## 0. 项目犯错记录` section in `context/templates/AGENTS.template.md`:

```markdown
## 构建与验证契约（AI 必读）

执行构建、测试或验证命令前，必须读取项目根目录的 `HARNESS.md`。

- `HARNESS.md` 是构建、快速验证、Bugfix 验证、完整验证及执行环境的唯一事实源。
- 不得猜测、替换或覆盖 `HARNESS.md` 中的命令；README、CI 配置和生态惯例只能用于核实，不能替代契约。
- 若 `HARNESS.md` 缺失、不可读，或命令标记为 `Unknown` 或 `Missing`，必须停止猜测并提示补齐契约。
- 行为、安全和修改边界以 `AGENTS.md` 为准；具体命令和执行环境以 `HARNESS.md` 为准。
```

- [ ] **Step 4: Add the formal HARNESS definition**

Replace the heading at the start of `context/templates/HARNESS.template.md` with:

```markdown
# HARNESS — 项目构建与验证契约

本文件是项目构建、验证和执行环境的唯一事实源。
它定义可执行命令、运行条件和验证边界，不替代 `AGENTS.md` 中的行为、安全与修改约束。
```

- [ ] **Step 5: Run the focused test and verify GREEN**

Run:

```bash
python -m unittest tests.test_context_cli.ContextCliTests.test_scan_links_agents_to_harness_contract -v
```

Expected: PASS with one test run.

- [ ] **Step 6: Commit the generated contract change**

```bash
git add tests/test_context_cli.py context/templates/AGENTS.template.md context/templates/HARNESS.template.md
git commit -m "feat: define harness build verification contract"
```

### Task 2: Align the user guide with the current product

**Files:**
- Modify: `docs/HARNESS_GUIDE.md`

**Interfaces:**
- Consumes: the contract language introduced in Task 1 and the six current skills listed in `README.md`.
- Produces: a user guide that describes the same source-of-truth boundary and no longer instructs users to invoke removed standalone skills.

- [ ] **Step 1: Update the guide introduction and contract definition**

Change the introduction to call `HARNESS.md` the “项目构建与验证契约”. In section three, state exactly:

```markdown
`HARNESS.md` 是项目构建、验证和执行环境的唯一事实源，记录真实可执行命令、运行条件和验证边界。

AI Agent 在执行构建、测试或验证命令前必须先读取该文件，不得根据 README、CI 配置或生态经验猜测、替换或覆盖其中的命令。行为、安全和修改边界以 `AGENTS.md` 为准；具体命令和执行环境以 `HARNESS.md` 为准。
```

- [ ] **Step 2: Replace references to removed standalone workflow skills**

Replace the `dev-harness-repro`, `dev-harness-triage`, `dev-harness-verify`, and `dev-harness-regression` manual instructions with a current table containing:

```markdown
| Skill | 用途 |
|-------|------|
| `dev-harness-context` | 扫描仓库并生成项目上下文与契约文件 |
| `dev-harness-commands` | 补齐 build / quick / bugfix / full 的真实命令映射 |
| `dev-harness-auto-fix` | 执行内置的复现、定位、修复、审查与验证流程 |
| `dev-harness-git-workflow` | 校验分支与提交信息并拦截调试残留 |
| `dev-harness-retro` | 复盘并更新 `LESSONS.md` |
```

Explain that reproduction, triage, regression, and verification are internal stages of `dev-harness-auto-fix`, not independently installed skills.

- [ ] **Step 3: Check Markdown and stale references**

Run:

```bash
rg -n "dev-harness-(repro|triage|regression|verify)" docs/HARNESS_GUIDE.md
git -c core.whitespace=cr-at-eol diff --check
```

Expected: `rg` finds only the explanatory sentence saying these are internal stages, and `git diff --check` exits successfully without whitespace errors.

- [ ] **Step 4: Commit the guide alignment**

```bash
git add docs/HARNESS_GUIDE.md
git commit -m "docs: align harness guide with current workflow"
```

### Task 3: Full regression verification

**Files:**
- Verify: `tests/`
- Verify: all files changed in Tasks 1 and 2

**Interfaces:**
- Consumes: completed template, test, and guide changes.
- Produces: fresh evidence that context generation and packaging tests still pass.

- [ ] **Step 1: Run the complete test suite**

Run:

```bash
python -m unittest discover -s tests -v
```

Expected: exit code 0 with all discovered tests passing.

- [ ] **Step 2: Validate generated content and repository diff**

Run:

```bash
git -c core.whitespace=cr-at-eol diff --check HEAD~2..HEAD
git status --short
```

Expected: no whitespace errors; status contains no uncommitted implementation files.

- [ ] **Step 3: Review requirements against the design**

Confirm all four requirements:

1. `HARNESS.md` has the formal “项目构建与验证契约” definition.
2. Generated `AGENTS.md` mandates reading it before build, test, or verification commands.
3. Missing or unknown contracts prohibit guessed commands.
4. `docs/HARNESS_GUIDE.md` matches the current workflow and source-of-truth boundary.
