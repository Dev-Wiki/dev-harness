# Git 工作流契约

本文件是仓库关于分支、提交、tag、变更日志和发布文案的权威规范。

## 分支模式

**已确认模式**：`{single-branch | feature-branch}`——由项目确认后只保留一个值。

- `single-branch`：可以直接在配置的默认分支上继续开发。
- `feature-branch`：使用`feat/`、`fix/`、`docs/`、`refactor/`、`test/`、`perf/`或`chore/`前缀。

除非已确认的模式要求或用户明确提出，否则不要创建或切换分支。

## 提交规范

使用 Conventional Commits：

```text
<type>(<scope>): <中文描述>
```

`scope`可省略。默认允许的`type`包括：

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

描述应准确说明变更目的，并使用自然中文；用户明确要求英文时使用自然英文。只有项目已经定义时，才添加项目特有的 issue 引用。

## tag

- 使用`vMAJOR.MINOR.PATCH`格式的 SemVer annotated tag。
- 预发布版本可以使用`vMAJOR.MINOR.PATCH-PRERELEASE`。
- 没有明确的发布或 tag 请求时，不创建或替换 tag。

## 变更日志

默认变更日志为`CHANGELOG.md`，仅在用户明确确认或开始首次发布时初始化。

发布分类按以下顺序排列；括号中为兼容工具可能使用的内部英文分类：

1. 重大变更（`Breaking Changes`）
2. 新增（`Added`）
3. 变更（`Changed`）
4. 弃用（`Deprecated`）
5. 修复（`Fixed`）
6. 移除（`Removed`）
7. 安全（`Security`）

删除内容归入“移除（`Removed`）”。定稿的版本记录省略空分类。

## tag 注释和发布说明

两者都根据变更日志中的对应版本生成：

```text
发布 vMAJOR.MINOR.PATCH

<按分类整理的非空变更日志内容>
```

保持上述分类顺序并省略空分类。缺少对应的变更日志版本时，先停止并请求确认；不得根据 commit subject 编造发布内容。

## 提交安全检查

提交前：

- 检查完整工作区和暂存区 diff；
- 保留已有的暂存文件边界；
- 发现疑似密钥、凭据、意外的大文件或无关变更时停止；
- 发现`Console.WriteLine`、`Debug.Log`或裸`print(`等临时调试输出时停止，除非项目确认需要保留。
