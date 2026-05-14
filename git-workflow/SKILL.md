---
name: dev-harness-git-workflow
description: Use when you need to enforce branch naming rules, commit message format, and debug artifact checks before committing code
---

# dev-harness-git-workflow

通用 Git 工作流门禁。负责在提交前校验分支命名、生成规范提交信息，并拦截调试残留代码。

完整规范见 `docs/GIT_WORKFLOW.md`。



## Preamble — 读取项目约束

```bash
_LESSONS="$(git rev-parse --show-toplevel 2>/dev/null)/LESSONS.md"
if [ -f "$_LESSONS" ]; then
  echo "=== LESSONS（项目历史 AI 犯错规则，视为硬约束）==="
  cat "$_LESSONS"
  echo "==="
fi
```

## 适用场景

- 用户准备提交代码，需要生成符合规范的 commit message
- 需要校验当前分支名是否符合命名规范
- 需要在提交前拦截 `Console.WriteLine` / `Debug.Log` / `print` 等调试残留
- CI 流水线需要机器可读的门禁输出

## 输入要求

至少需要以下输入：

- 当前分支名（通过 `git branch --show-current` 获取，或用户提供）
- 当前未提交的 diff（通过 `git diff` / `git diff --cached` 获取）
- 用户通过 `/commit` 参数提供的上下文（可选）
- `skip_branch_create` 标记（由上游 auto-fix 传入时为 `true`；单独调用时默认为 `false`）
- 用户原始输入（用于检测是否包含"在当前分支提交"、"不创建新分支"等意图）

若无法获取分支名，标记为 `unknown` 并跳过分支校验（不拦截）。

## 输出契约

输出必须至少包含：

- **BranchCheck**：通过 / 失败 + 原因
- **DebugCheck**：通过 / 失败 + 残留位置
- **CommitTitle**：生成的完整首行提交说明（格式见下）
- **CommitResult**：`git commit` 执行结果（commit SHA 或失败原因）
- **MachineBlock**：`---OUTPUT---` 块，见下方示例

## 顺序化步骤

### Step 1: 获取当前状态与分支创建门禁

```
1.1 获取当前分支名和未提交的 diff：
    - `git branch --show-current` → 分支名
    - `git diff` → 工作区变更
    - `git diff --cached` → 暂存区变更

1.2 分支创建门禁（若 skip_branch_create=true → 跳过整节，直接进入 1.3）：
    1.2.1 检查用户原始输入是否明确包含：
        - "在当前分支提交" / "不创建新分支" / "直接提交"
        → 是 → skip_branch_create=true，跳过 1.2.2~1.2.4
    1.2.2 判断当前分支是否为主干分支（master / main / HEAD detached）：
        → 是主干分支 → must_create=true
        → 否 → 检查分支名是否符合 Step 2 中的任一命名规范
            → 符合 → 已是工作分支，不创建
            → 不符合 → must_create=true
    1.2.3 must_create=true 时生成分支名（遵循 Conventional 风格）：
        - bugfix → `fix/<描述>`（描述取 Symptom 关键词，小写中划线，≤ 40 字符）
        - 新功能 → `feat/<描述>`
        - 重构/维护 → `chore/<描述>` 或 `refactor/<描述>`
        - 无上下文 → 询问用户工作类型，再生成对应分支名
    1.2.4 执行分支创建：
        - `git checkout -b <分支名>` → 成功进入 1.3
        - 分支已存在 → `git checkout <分支名>` → 进入 1.3
        - 其他失败 → STOP，输出失败原因

1.3 最终确认当前分支名：`git branch --show-current`
```

### Step 2: 分支命名校验

**字符合集**：仅小写字母 `a-z`、数字 `0-9`、中划线 `-`、斜杠 `/`。

**合法格式**（任一匹配即通过）：

1. `feat/<描述>` — 新功能
2. `fix/<描述>` — bug 修复
3. `chore/<描述>` — 构建/工具/维护
4. `docs/<描述>` — 文档
5. `refactor/<描述>` — 重构
6. `test/<描述>` — 测试
7. `perf/<描述>` — 性能优化
8. `release/<版本>` — 发布分支
9. `main` / `master` — 主干（只读，不在上面直接提交）

均不匹配 → 警告但不强制拦截（允许团队自定义分支名），`branch_check=warn`。

### Step 3: 调试残留检查

扫描 diff 中的新增行（`+` 开头），检查是否包含：

- `Console.WriteLine`
- `Debug.Log`
- 裸 `print(` （Python 临时调试输出；不含 `file=` 的日志输出可警告确认）

检出 → 拦截，`fail_reason=debug_print`。

### Step 4: 生成提交信息

生成格式（Conventional Commits）：

```
<type>(<scope>): <描述>
```

- **type**：从 `feat` / `fix` / `docs` / `style` / `refactor` / `perf` / `test` / `chore` 中选择，根据分支名和 diff 内容推断。
- **scope**（可选）：从分支名或项目名推断模块名。
- **描述**：根据 diff 内容生成，说明改动的具体目的，不能写"bug fix"、"问题修复"等笼统描述。
- **长度**：整行 commit title 建议 > 20 字符，< 72 字符。

### Step 5: 输出机器可读块与执行提交

**直接执行以下命令完成提交**（无需用户二次确认，用户调用本 skill 即表示意图提交）：

1. 运行 `git status --porcelain` 确认有变更
2. 若暂存区为空（`git diff --cached` 无输出），先执行 `git add -A` 暂存所有变更
   - 若暂存区已有内容，仅提交已暂存的内容，不追加 `git add`
3. 执行 `git commit -m "<完整 commit_title>"`
4. 记录 commit SHA：`git rev-parse HEAD`
5. 在回复中展示提交结果

> ⚠️ **`git add -A` 安全提示**：执行前应检查是否有不应提交的文件（如 `.env`、密钥、大文件）。若 diff 中疑似存在敏感文件，先警告用户确认。

## 停止条件

- 无法获取当前分支名且用户未提供
- 分支创建失败（`git checkout -b` 异常，非"已存在"情况）
- diff 被截断无法完整扫描
- 调试残留检出后用户拒绝移除
- 规范文档 `docs/GIT_WORKFLOW.md` 不可用（可选，仅供参考）

满足任一条件时，不得继续生成 commit title 或输出 `status=pass`。

## 交接边界

- 与 `dev-harness-verify` 衔接：验证通过后进入 git-workflow 门禁
- 默认执行 `git commit`（用户调用即表示意图提交），但可通过环境变量 `HARNESS_COMMIT_DRY_RUN=1` 跳过实际提交
- 不负责 push、PR 创建或 CI 触发
- 不依赖宿主项目构建系统，可独立运行
- 提交完成后输出 `commit_sha`，供流水线上游追溯

## 使用示例

用户输入：`帮我提交代码` 或 `提交当前修改`

输出：
```text
✅ 分支检查通过（fix/token-refresh-retry）
✅ 无调试残留

📝 提交信息：
fix(auth): 修复登录页 token 过期后未自动刷新，补充 refresh_token 重试逻辑

📦 执行 git commit...
[fix/token-refresh-retry a1b2c3d] fix(auth): 修复登录页 token 过期后未自动刷新，补充 refresh_token 重试逻辑
 3 files changed, 42 insertions(+), 8 deletions(-)

🔖 commit_sha: a1b2c3d4e5f6789012345678901234567890abcde

---OUTPUT---
format=conventional-commits/v1
status=pass
branch=fix/token-refresh-retry
commit_title=fix(auth): 修复登录页 token 过期后未自动刷新，补充 refresh_token 重试逻辑
commit_sha=a1b2c3d4e5f6789012345678901234567890abcde
---END---
```
