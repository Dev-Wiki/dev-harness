# Git 工作流规范

本文件是 dev-harness 仓库自己的 Git、提交、tag、changelog 与发布消息契约。其他项目应优先使用其仓库内已有规范；本文件不是强加给目标项目的公司级规则。

## 1. 分支模式

本仓库确认使用 `single-branch`：允许在当前默认分支直接开发和提交，不要求自动创建功能分支。

其他项目没有规范时，`dev-harness-git-workflow` 会请用户在以下模式中确认一个：

- `single-branch`：按项目约定直接在默认分支工作。
- `feature-branch`：使用 `feat/`、`fix/`、`docs/`、`refactor/`、`test/`、`perf/`、`chore/` 前缀。

仓库已有分支规范时始终以仓库规范为准。

## 2. 提交规范

使用 Conventional Commits：

```text
<type>(<scope>): <description>
```

`scope` 可选。默认 type：

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

description 应说明改动的具体目的，不使用 “fix bug” 或 “update code” 等笼统描述。

提交前必须检查完整工作区和暂存区。已有暂存内容时仅提交已暂存文件；发现疑似密钥、`.env`、意外大文件、无关改动或临时调试输出时停止确认。

## 3. Tag 规范

- 使用 SemVer annotated tag：`vMAJOR.MINOR.PATCH`。
- 预发布版本可用 `vMAJOR.MINOR.PATCH-PRERELEASE`。
- 未收到明确 tag 或发布请求时不得创建、移动或覆盖 tag。

## 4. Changelog 规范

默认变更日志为根目录 `CHANGELOG.md`。Context 的 `scan` 和 `refresh` 只识别路径，不负责创建该文件。

版本内容按以下固定顺序组织：

1. `Breaking Changes`
2. `Added`
3. `Changed`
4. `Deprecated`
5. `Fixed`
6. `Removed`
7. `Security`

使用 `Removed` 表示移除。版本定稿时省略空分类。

## 5. Tag Annotation 与 Release Notes

annotated tag message 与 release notes 都从 `CHANGELOG.md` 中匹配的版本生成：

```text
Release vMAJOR.MINOR.PATCH

<只包含非空分类及条目>
```

分类保持第 4 节顺序，并省略空分类。如果对应版本不存在，必须停止并请求补齐或确认；不得未经确认从 commit subject 编造发布说明。

## 6. 调试残留与敏感文件

提交前扫描新增 diff，重点检查：

- `Console.WriteLine`
- `Debug.Log`
- 裸 `print(`
- `.env`、密钥、凭据和意外大文件

检出内容不一定都是错误，但必须先确认其为有意变更才能提交。

## 7. 规范初始化

目标仓库没有 Git 规范时，`dev-harness-git-workflow` 先读取至多 100 条历史提交、分支、tag 和 contribution 文件，展示候选并取得显式确认，然后才可从 skill 模板创建 `docs/GIT_WORKFLOW.md`。

`CHANGELOG.md` 只在用户确认初始化或开始第一次发布时创建。创建或选择规范后运行：

```bash
dev-harness-context refresh <repo-path>
```

这只更新 AGENTS 的规范路径索引，不把详细规则塞入 AGENTS。
