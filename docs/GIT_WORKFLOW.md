# Git 工作流规范

通用 Git 工作流规范，覆盖分支命名、提交信息格式和调试残留拦截。

由 `dev-harness-git-workflow` skill 执行，本文档作为参考。

---

## 1. 分支命名规范

### 1.1 字符合集

分支名只能由小写字母 `a-z`、数字 `0-9`、中划线 `-`、斜杠 `/` 组成。

### 1.2 合法格式

遵循 [Conventional Branches](https://www.conventionalcommits.org/) 风格：

| 格式 | 说明 | 示例 |
|------|------|------|
| `feat/<描述>` | 新功能 | `feat/user-login` |
| `fix/<描述>` | Bug 修复 | `fix/token-refresh-null` |
| `chore/<描述>` | 构建/工具/维护 | `chore/update-deps` |
| `docs/<描述>` | 文档 | `docs/api-readme` |
| `refactor/<描述>` | 重构 | `refactor/auth-service` |
| `test/<描述>` | 测试 | `test/login-unit` |
| `perf/<描述>` | 性能优化 | `perf/reduce-bundle-size` |
| `release/<版本>` | 发布分支 | `release/1.2.0` |
| `main` / `master` | 主干（不在上面直接提交）| — |

不符合以上格式时，`dev-harness-git-workflow` 会警告但不强制拦截。

---

## 2. 提交信息格式

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <描述>

[可选 body]

[可选 footer]
```

### 2.1 Type 列表

| Type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 仅文档变更 |
| `style` | 格式（不影响代码逻辑） |
| `refactor` | 重构（不是新功能也不是 bugfix） |
| `perf` | 性能优化 |
| `test` | 添加或修改测试 |
| `chore` | 构建过程或辅助工具变更 |

### 2.2 规则

- **type** 必填，从上表选择
- **scope** 可选，表示影响模块（如 `auth`、`api`、`ui`）
- **描述** 不能使用笼统词汇（"fix bug"、"update code"等）
- 整行 commit title 建议 < 72 字符

### 2.3 示例

```
feat(auth): 添加 OAuth2 登录支持

fix(api): 修复 token 过期后未自动刷新的问题

chore(deps): 升级 requests 到 2.31.0
```

---

## 3. 调试残留拦截

提交前扫描 diff 新增行，以下内容被视为调试残留，会被拦截：

- `Console.WriteLine`
- `Debug.Log`
- 裸 `print(`（不含 `file=` 参数的临时调试输出）

---

## 4. 机器可读输出块

`dev-harness-git-workflow` 在回复末尾追加固定格式输出块：

```
---OUTPUT---
format=conventional-commits/v1
status=<pass|fail>
branch=<分支名>
commit_title=<提交说明首行>
commit_sha=<40位SHA>
fail_reason=<debug_print|branch_invalid|other>（仅失败时）
---END---
```
