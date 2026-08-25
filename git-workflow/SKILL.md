---
name: dev-harness-git-workflow
description: Use when you need to discover, initialize, or follow a repository-owned Git workflow, or explicitly commit, tag, and prepare release messages safely
---

# dev-harness-git-workflow

负责识别并遵循目标仓库自己的 Git、提交、tag 和发布规范。**仓库已有规范优先**；本 skill 的模板只在项目没有规范且用户显式确认后使用。

## 输出语言

- 仓库已有提交、CHANGELOG、tag 注释或发布说明规范时，始终优先遵循仓库规范。
- 用户明确要求英文时使用自然英文。否则，中文项目及语言未指定的新项目默认使用简体中文；更新现有文档时沿用其主体语言和既有术语。
- 中文输出中的标题、表格、提交说明、tag 注释、发布说明、验证结果和最终报告使用自然中文。路径、命令、代码符号、API、协议、产品名、必要缩写、Conventional Commits 的`type`以及内部枚举值保持原样。
- 内部英文枚举或字段必须面向读者展示时，首次用“中文含义（原值）”说明，后续正文优先使用中文含义。按语义表达，不逐字硬译，也不顺便翻译本次没有修改的历史内容。
- 项目没有提交语言规范且用户已确认默认契约时，默认提交格式为`<type>(<scope>): <中文描述>`；`scope`可省略。用户明确要求英文时，描述改用自然英文。

## 适用场景

- 识别项目已有的分支、提交、tag、changelog 和发布规范
- 没有规范时，根据历史提出候选并初始化 `docs/GIT_WORKFLOW.md`
- 新项目需要确认 GitHub 友好的默认工作流
- 用户明确要求提交、创建 tag 或生成 release notes
- 提交前检查调试残留、敏感文件和无关变更

初始化或审计本身不表示授权执行 commit、tag、push、release 或创建分支。只有用户明确请求对应动作时才允许产生相应 Git 变更。

## 第一步：读取项目规范索引

1. 读取仓库根目录 `AGENTS.md`，通过其中的项目规范索引定位权威文档。
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
- Conventional Commits：`<type>(<scope>): <中文描述>`；用户明确要求英文时使用英文描述
- annotated tag：`vMAJOR.MINOR.PATCH`，预发布可用 `vMAJOR.MINOR.PATCH-PRERELEASE`
- 发布规范默认写在 `docs/GIT_WORKFLOW.md`，也可由用户拆分到 `docs/RELEASE.md`
- `CHANGELOG.md` 仅在用户确认初始化或开始首次发布时创建

## 第三步：确认和初始化

在写入任何规范前，必须向用户展示完整候选并获得**显式确认**。

确认后：

1. 仅当目标文件不存在时，从 `templates/GIT_WORKFLOW.template.md` 初始化 `docs/GIT_WORKFLOW.md`。
2. 把用户确认的分支模式和项目选择写入模板占位处。
3. 按“输出语言”规则调整模板文案；英文项目不得机械保留中文占位说明。
4. 只有用户同时确认 changelog 初始化或正在开始首次发布时，才从 `templates/CHANGELOG.template.md` 创建 `CHANGELOG.md`。
5. 任何现有规范或 changelog 均不得覆盖。
6. 完成后运行或建议运行：

```bash
dev-harness-context refresh <repo-path>
```

Context 只刷新 AGENTS 托管索引，不复制规范正文。

## 默认 Git 契约

完整默认值只在项目缺少相应规范且用户已经确认时按需读取 [references/default-contract.md](references/default-contract.md)。核心兼容值为 `single-branch` / `feature-branch`、Conventional Commits、annotated tag `vMAJOR.MINOR.PATCH`，release notes 按既定顺序省略空分类。

### 精确提交边界

用户明确要求提交时：

1. 读取完整 `git status --short`、工作区 diff 和暂存区 diff；若调用方提供 `WorkspaceSnapshot`，先确认 HEAD、分支和已有修改指纹未漂移。
2. 提交范围必须来自本轮明确维护的 `AutoFixChangedFiles`，而不是笼统的当前 diff。已有暂存内容不属于该集合时，报告 `staged_scope_conflict` 并停止，不得混入或擅自取消用户暂存。
3. 对集合内每个文件逐个执行 `git add -- <file>`；删除文件也使用同一精确形式。禁止使用全量暂存命令。
4. 暂存后重新比较 staged 文件集合与 AutoFixChangedFiles；不相等即报告 `staged_scope_conflict` 并停止。
5. 检查候选文件，发现 `.env`、密钥、凭据、大文件或明显无关变更时停止并确认。
6. 扫描新增行中的临时调试输出，如 `Console.WriteLine`、`Debug.Log`、裸 `print(`；疑似残留时停止并确认。
7. 按项目规范生成 commit message；只有项目没有该主题且用户已确认默认契约时才使用上述 Conventional Commits。

Tag annotation 与 release notes 必须来自 `CHANGELOG.md` 的匹配版本；缺失时停止，不得从 commit subject 编造发布事实。

## 输出

审计或初始化输出：

- 规范来源（`WorkflowSource`）：已有规范路径 / 已确认默认值（`confirmed-default`）/ 缺失（`missing`）
- 分支模式（`BranchMode`）：项目规则 / 推断候选（`inferred-candidate`）/ 未知（`unknown`）
- 提交规则（`CommitRule`）：项目规则 / 推断候选（`inferred-candidate`）/ 未知（`unknown`）
- tag 规则（`TagRule`）：项目规则 / 推断候选（`inferred-candidate`）/ 未知（`unknown`）
- 发布规则（`ReleaseRule`）：项目规则 / 推断候选（`inferred-candidate`）/ 未知（`unknown`）
- 变更日志（`Changelog`）：路径 / 尚未初始化（`not-initialized`）
- 下一步（`NextAction`）：刷新（`refresh`）/ 确认（`confirm`）/ 无（`none`）

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
- Codebase Audit 发现 Git / release policy gap 时可建议使用本 Skill；审计 Finding 不是执行 commit、tag、push 或 release 的授权
- 不默认 push、创建 PR、发布 GitHub Release、部署或触发 CI
- 项目或公司自己的规范文档始终高于本 skill 默认模板
