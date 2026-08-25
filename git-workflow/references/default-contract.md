# 可确认的默认 Git 契约

仅当仓库缺少相应主题的权威规范，并且用户已经明确接受默认值时，才使用本参考。

## 分支和提交

- 分支模式由项目在`single-branch`和`feature-branch`中确认；模式或请求动作不需要分支时，不要提前创建分支。
- 默认提交格式采用 Conventional Commits：`<type>(<scope>): <中文描述>`，`scope`可省略。用户明确要求英文时使用自然英文描述。
- 仓库自己的分支、提交格式和语言规范始终高于这些默认值。

## tag 和发布说明

- 默认使用`vMAJOR.MINOR.PATCH`格式的 annotated tag；预发布版本可追加`-PRERELEASE`。
- tag 注释和发布说明必须来自`CHANGELOG.md`中的对应版本。
- 非空分类依次为：重大变更（`Breaking Changes`）、新增（`Added`）、变更（`Changed`）、弃用（`Deprecated`）、修复（`Fixed`）、移除（`Removed`）、安全（`Security`）。
- 缺少对应的变更日志版本时停止；未经确认，不得根据 commit subject 编造发布事实。

## 精确的变更文件所有权

调用方提供`WorkspaceSnapshot`和其负责的变更文件集合时，只使用`git add -- <file>`暂存这些路径。出现暂存范围冲突、敏感文件、被截断的 diff 或快照漂移时停止。提交授权不包含 push、PR、tag、release 或 deploy 授权。
