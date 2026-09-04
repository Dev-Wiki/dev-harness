# dev-harness HARNESS 使用指南

本文只说明如何维护和使用业务仓库中的 `HARNESS.md` 验证契约，适用于 Cursor、Codex CLI、OpenCode 和 Antigravity。安装及首次接入见[项目概览](../README.md#安装)和[客户端项目接入](CLIENT_PROJECT_ONBOARDING.md)，跨 Skill 阶段顺序见[端到端工作流](WORKFLOW.md)。

各项目的具体命令和执行环境以仓库根目录 `HARNESS.md` 为唯一事实源；行为、安全和修改边界以 `AGENTS.md` 为准。

---

## 一、前置条件

- 已安装 `dev-harness` Skills。
- 业务仓库根目录已有 `AGENTS.md` 和 `HARNESS.md`；缺失时先用 `dev-harness-context` 初始化。
- `HARNESS.md` 中的命令必须来自真实脚本、构建配置或成功执行证据，不能根据技术栈经验编造。

需要补齐命令时，在业务仓库中调用：

```text
使用 dev-harness-commands 帮我定义 build / test / quick / bugfix / full 命令
```

## 二、五类验证入口

`harness:build`、`harness:test`、`harness:quick`、`harness:bugfix` 和 `harness:full` 是稳定语义，不要求项目改写原有工具链或统一脚本名称。

| 入口 | 证明范围 |
|---|---|
| `build` | 当前目标或构建图能够完成编译、生成或等价构建 |
| `test` | 仓库已有的自动化测试入口能够运行 |
| `quick` | 为高频迭代提供最短、可信的相关反馈 |
| `bugfix` | 验证某个已知问题的复现或专项回归路径 |
| `full` | 执行项目已确认的完整本地构建与测试边界 |

打包、签名和发布链应标记为 `package/release-only` 或 CI-only，不能冒充本地 `full`。多平台、设备或构建变体应分别记录，并通过 Platform / Variant 唯一选择；设备依赖同时写入 `DeviceRequirement`。

`dev-harness-context` 只维护自动识别的候选命令，`dev-harness-commands` 只维护人工确认区。候选命令不能直接作为成功验证证据；确认入口仍为 `Unknown` 或 `Missing` 时必须停止并补齐。

---

## 三、HARNESS.md 项目构建与验证契约

`HARNESS.md` 是项目构建、验证和执行环境的唯一事实源，记录真实可执行命令、运行条件和验证边界。

AI Agent 在执行构建、测试或验证命令前必须先读取该文件，不得根据 README、CI 配置或生态经验猜测、替换或覆盖其中的命令。行为、安全和修改边界以 `AGENTS.md` 为准；具体命令和执行环境以 `HARNESS.md` 为准。

### 必须包含的区域

```markdown
## 自动识别构建命令候选
- **build**: `<自动识别候选或 Unknown>`
- **test**: `<自动识别候选、device-required 或 Unknown>`
- **quick**: `<自动识别候选或 Unknown>`
- **bugfix**: `<自动识别候选或 Unknown>`
- **full**: `<自动识别候选或 Unknown>`

## 已确认命令（人工维护）
- **build**: `<真实构建命令或 Unknown>`
- **test**: `<真实测试命令、device-required 或 Unknown>`
- **quick**: `<真实快速验证命令或 Unknown>`
- **bugfix**: `<真实问题专项验证命令或 Unknown>`
- **full**: `<真实完整验证命令或 Unknown>`
```

自动识别结果只作为候选；`dev-harness-context` 按该固定标题刷新候选章节，`dev-harness-commands` 只能更新“已确认命令（人工维护）”，不得写入或覆盖候选章节。执行时以已确认命令为准；仍为 `Unknown` 时必须停止并补齐，不能直接执行候选。

### 推荐包含的字段

- `CanRunBuildHere`：当前环境是否可以运行构建（用于 WSL 等跨平台场景）
- `RecommendedTerminal`：推荐的终端环境
- `高风险目录`：AI 不得自动修改的区域
- `禁止操作`：明确禁止的操作清单

---

## 四、常见问题

**Q: HARNESS.md 命令显示 Unknown/Missing**

先用 `dev-harness-commands` 根据仓库证据补齐命令映射，再继续开发或验证。

**Q: 同一入口在不同平台或 Variant 下使用不同命令**

为每种 Platform / Variant 建立独立命令记录，不要把互不兼容的命令拼成一条；设备要求和终端环境分别记录。

**Q: 发布包构建能否作为 full**

不能。`full` 只表示项目确认的完整本地验证边界；打包、签名、安装器制作和发布属于独立的 release-only 流程。

---

## 五、参考文档

| 文档 | 说明 |
|------|------|
| [项目概览](../README.md) | 安装、宿主支持和 Skill 入口 |
| [客户端项目接入](CLIENT_PROJECT_ONBOARDING.md) | 新项目初始化与最小契约 |
| [端到端工作流](WORKFLOW.md) | 新功能交付、审计与修复的阶段顺序 |
| [测试说明](TESTING.md) | 分层测试策略与验证证据要求 |
| [Bugfix 指南](BUGFIX_GUIDE.md) | Bug 描述、复现和专项回归格式 |
| [Commands 契约](../commands/SKILL.md) | 命令记录字段、停止条件和所有权边界 |
