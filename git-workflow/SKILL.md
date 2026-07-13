---
name: dev-harness-git-workflow
description: Use when you need to discover, initialize, or follow a repository-owned Git workflow, or explicitly commit, tag, and prepare release messages safely
---

# dev-harness-git-workflow

负责识别并遵循目标仓库自己的 Git、提交、tag 和发布规范。**仓库已有规范优先**；本 skill 的模板只在项目没有规范且用户显式确认后使用。

## 适用场景

- 识别项目已有的分支、提交、tag、changelog 和发布规范
- 没有规范时，根据历史提出候选并初始化 `docs/GIT_WORKFLOW.md`
- 新项目需要确认 GitHub 友好的默认工作流
- 用户明确要求提交、创建 tag 或生成 release notes
- 提交前检查调试残留、敏感文件和无关变更

初始化或审计本身不表示授权执行 commit、tag、push、release 或创建分支。只有用户明确请求对应动作时才允许产生相应 Git 变更。

## 第一步：读取项目规范索引

1. 读取仓库根目录 `AGENTS.md` 和 `LESSONS.md`（若存在）。
2. 优先读取 AGENTS“项目规范索引”中的 Git 工作流、发布规范和变更日志路径。
3. 索引缺失时，依次检查：
   - `docs/GIT_WORKFLOW.md`
   - `.github/CONTRIBUTING.md`
   - `CONTRIBUTING.md`
   - `GIT_WORKFLOW.md`
   - `docs/RELEASE.md` / `RELEASE.md`
   - `CHANGELOG.md` / `docs/CHANGELOG.md` / `HISTORY.md`
4. 找到项目规范后，以它为唯一事实源。缺少的主题作为 gap 报告，不得静默混入本 skill 默认值。
5. 多个文档冲突时，列出候选并请用户选择权威文档；不得自行覆盖或合并。

## 第二步：没有规范时生成候选

### 有开发历史的仓库

只读检查以下证据：

```bash
git branch --show-current
git branch -a
git log -100 --pretty=%s
git tag --list --sort=-version:refname
```

同时读取 contribution、pull request、release 和 changelog 文件。根据证据提出以下候选：

- 分支模式：`single-branch` 或 `feature-branch`
- commit 格式
- tag 格式
- release 规范位置
- changelog 位置与分类

历史只作为证据，不是规范。历史不一致时，展示观察结果和默认建议，等待用户选择。

### 没有有效历史的新仓库

提出以下 GitHub 友好默认值：

- 分支模式由用户在 `single-branch` 与 `feature-branch` 中选择
- Conventional Commits：`type(scope): description`
- annotated tag：`vMAJOR.MINOR.PATCH`，预发布可用 `vMAJOR.MINOR.PATCH-PRERELEASE`
- 发布规范默认写在 `docs/GIT_WORKFLOW.md`，也可由用户拆分到 `docs/RELEASE.md`
- `CHANGELOG.md` 仅在用户确认初始化或开始首次发布时创建

## 第三步：确认和初始化

在写入任何规范前，必须向用户展示完整候选并获得**显式确认**。

确认后：

1. 仅当目标文件不存在时，从 `templates/GIT_WORKFLOW.template.md` 初始化 `docs/GIT_WORKFLOW.md`。
2. 把用户确认的分支模式和项目选择写入模板占位处。
3. 只有用户同时确认 changelog 初始化或正在开始首次发布时，才从 `templates/CHANGELOG.template.md` 创建 `CHANGELOG.md`。
4. 任何现有规范或 changelog 均不得覆盖。
5. 完成后运行或建议运行：

```bash
dev-harness-context refresh <repo-path>
```

Context 只刷新 AGENTS 托管索引，不复制规范正文。

## 默认 Git 契约

### 分支模式

- `single-branch`：允许按项目约定直接在默认分支开发和提交，不自动创建工作分支。
- `feature-branch`：使用 `feat/`、`fix/`、`docs/`、`refactor/`、`test/`、`perf/`、`chore/` 等前缀。

不得在项目未确认模式时强制创建分支。仓库自定义命名规则始终优先。

### Commit

默认格式：

```text
<type>(<scope>): <description>
```

`scope` 可选。默认 type 为：`feat`、`fix`、`docs`、`style`、`refactor`、`perf`、`test`、`build`、`ci`、`chore`、`revert`。

用户明确要求提交时：

1. 读取完整 `git status --short`、工作区 diff 和暂存区 diff。
2. 若已有暂存内容，只提交已暂存内容；不要自动追加其他文件。
3. 若暂存区为空，提交前检查所有候选文件，发现 `.env`、密钥、凭据、大文件或明显无关变更时停止并确认。
4. 扫描新增行中的临时调试输出，如 `Console.WriteLine`、`Debug.Log`、裸 `print(`；疑似残留时停止并确认。
5. 按项目规范生成 commit message；只有项目没有该主题且用户已确认默认契约时才使用上述 Conventional Commits。

### Tag 和发布消息

- 默认使用 annotated tag：`vMAJOR.MINOR.PATCH`。
- tag annotation 与 release notes 都从 `CHANGELOG.md` 中匹配的版本生成。
- 标题为 `Release vMAJOR.MINOR.PATCH`，正文按以下固定顺序输出非空分类：
  1. `Breaking Changes`
  2. `Added`
  3. `Changed`
  4. `Deprecated`
  5. `Fixed`
  6. `Removed`
  7. `Security`
- 必须省略空分类，不使用 `Deleted`。
- 找不到对应版本的 changelog 条目时停止，询问是否创建；未经确认不得用 commit subject 编造发布内容。

## 输出

审计或初始化输出：

- `WorkflowSource`: 已有规范路径 / confirmed-default / missing
- `BranchMode`: 项目规则 / inferred-candidate / unknown
- `CommitRule`: 项目规则 / inferred-candidate / unknown
- `TagRule`: 项目规则 / inferred-candidate / unknown
- `ReleaseRule`: 项目规则 / inferred-candidate / unknown
- `Changelog`: 路径 / not-initialized
- `NextAction`: refresh / confirm / none

执行 commit、tag 或发布动作时，额外报告实际命令结果和完整 SHA/tag；失败时报告原因，不得输出虚假的成功状态。

## 停止条件

- AGENTS 引用多个相互冲突的规范且用户尚未选择
- 现有规范不可读或语义不足以执行请求的动作
- 初始化候选尚未得到显式确认
- 目标规范文件已经存在
- diff 被截断，或疑似包含敏感文件、调试残留、无关变更
- tag 对应的 changelog 版本不存在
- 用户没有明确授权相应 commit、tag、push 或 release 动作

## 交接边界

- Context 负责规范路径索引；本 skill 不直接编辑 `agents.contract-index` 托管块
- 不自动生成代码规范文档
- 不修改构建验证契约 `HARNESS.md`
- 不默认 push、创建 PR、发布 GitHub Release、部署或触发 CI
- 项目或公司自己的规范文档始终高于本 skill 默认模板
