# Auto-fix 通用化加固 Implementation Plan

> **For agentic workers:** Execute inline in the current workspace. Do not use subagents, do not commit, and preserve all pre-existing worktree changes. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立通用、可执行、可测试的 auto-fix 授权、证据、dirty worktree 和精确提交契约。

**Architecture:** Markdown Skill 负责语义路由；`auto-fix/runtime.py` 使用 Python 标准库提供确定性的快照、diff hash、状态和门禁；安装器把运行时和四个 bugfix-flow references 一起分发。

**Tech Stack:** Python 3 标准库、unittest、Markdown Skills、现有 `install.py`。

## Global Constraints

- 保留现有 Qt、WPF、Go、Flutter、Node.js、Harmony 风险边界。
- Issue Provider 保持 GitHub/GitLab/用户描述通用，不引入 ONES。
- Dirty worktree 允许存在，但本轮不得修改或暂存快照前已有变更。
- `analyze` 必须只读，并在 hypothesize 后进入 report。
- 不新增第三方依赖。
- 不提交、不 push、不创建 PR。

---

### Task 1: Auto-fix 契约和安装 RED

**Files:**
- Create: `tests/test_auto_fix_contract.py`
- Modify: `tests/test_install.py`

**Interfaces:**
- Consumes: `auto-fix/SKILL.md`、`git-workflow/SKILL.md`、四个 bugfix-flow references。
- Produces: 授权、顺序、RED/GREEN、精确暂存和安装内容的回归契约。

- [ ] 写入期望新契约的字符串和顺序断言。
- [ ] 增加安装产物包含 `runtime.py` 与四个 references 的断言。
- [ ] 运行 `python -B -m unittest tests.test_auto_fix_contract tests.test_install -v`，确认旧实现因缺少新能力失败。

### Task 2: Runtime 行为 RED/GREEN

**Files:**
- Create: `tests/test_auto_fix_runtime.py`
- Create: `auto-fix/runtime.py`

**Interfaces:**
- Produces: `create_snapshot(repo)`、`validate_workspace(snapshot, changed_files)`、`compute_diff_hash(...)`、`AutoFixStateStore` 和 CLI。

- [ ] 先写临时 Git 仓库测试：已有 dirty 文件保持不变时允许本轮新增修改。
- [ ] 写既有 dirty 文件被触碰时拒绝的测试。
- [ ] 写未声明新增变更和 HEAD/分支漂移拒绝测试。
- [ ] 写 tracked、untracked、删除内容改变 diff hash 的测试。
- [ ] 写状态文件位于 Git 私有目录且原子恢复的测试。
- [ ] 写 analyze/fix/commit 阶段授权和根因/RED/Review hash 门禁测试。
- [ ] 运行测试确认因 `auto-fix.runtime` 缺失而失败。
- [ ] 实现最小运行时并逐轮运行到通过。

### Task 3: 安装运行时

**Files:**
- Modify: `install.py`
- Test: `tests/test_install.py`

**Interfaces:**
- Consumes: `auto-fix/runtime.py`。
- Produces: `<bundle>/skills/dev-harness-auto-fix/runtime.py`。

- [ ] 增加源文件校验。
- [ ] 在 auto-fix builder 中复制运行时。
- [ ] 运行安装测试确认产物完整。

### Task 4: 迁移 Auto-fix 状态机

**Files:**
- Rewrite: `auto-fix/SKILL.md`
- Modify: `internal/bugfix-flow/repro.md`
- Modify: `internal/bugfix-flow/triage.md`
- Rewrite: `internal/bugfix-flow/regression.md`
- Modify: `internal/bugfix-flow/verify.md`

**Interfaces:**
- Consumes: runtime CLI、HARNESS、AGENTS、LESSONS 和 Git workflow。
- Produces: analyze/fix/commit/unattended 通用状态机。

- [ ] 定义授权模式、不可信输入和完成状态。
- [ ] 使用 runtime 初始化快照和状态。
- [ ] 把根因候选改为可证伪假设。
- [ ] 把 Regression RED 提升为默认实现前门禁。
- [ ] 把 Review 放到分层验证之后，并增加 final-verify。
- [ ] 保留所有现有平台风险门禁。
- [ ] 运行契约测试。

### Task 5: 精确暂存契约

**Files:**
- Modify: `git-workflow/SKILL.md`
- Test: `tests/test_auto_fix_contract.py`

**Interfaces:**
- Consumes: `WorkspaceSnapshot`、`AutoFixChangedFiles`、`Mode`。
- Produces: 逐文件暂存和冲突停止条件。

- [ ] 明确已有 staged 文件不自动提交。
- [ ] 要求 runtime 校验允许集合。
- [ ] 逐文件 `git add -- <file>`，禁止全仓暂存。
- [ ] 暂存结果与允许集合不一致时停止。

### Task 6: 文档和完整验证

**Files:**
- Modify: `README.md`
- Modify: `docs/V1_V2_BOUNDARIES.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Produces: 对外可发现的授权和证据流说明。

- [ ] 更新 README 的 auto-fix 说明和示例。
- [ ] 更新 V1/V2 已落地边界。
- [ ] 在 CHANGELOG 未发布区记录变更，不发布新版本。
- [ ] 运行 `python -B -m unittest discover -s tests -v`。
- [ ] 运行 `git diff --check`。
- [ ] 检查 `git status --short`，确认教程选题文档仍未被本次改动吸收。
