# dev-harness 使用指南

面向 **Cursor** 环境，使用 **`dev-harness-*`** skills 时的通用操作说明。

业务仓库需已具备 **`AGENTS.md`** 和作为“项目构建与验证契约”的 **`HARNESS.md`**，且 **`harness:quick` / `harness:build` / `harness:bugfix` / `harness:full`** 映射为**真实可执行**命令（缺失时用 **`dev-harness-commands`** 补齐，禁止编造）。

各项目的具体命令和执行环境以仓库根目录 `HARNESS.md` 为唯一事实源；行为、安全和修改边界以 `AGENTS.md` 为准。

---

## 一、前置条件

| 组件 | 说明 |
|------|------|
| **Cursor IDE** | 已安装，建议使用最新版 |
| **dev-harness skills** | 已通过 `install.py` 安装到 `~/.cursor/skills/` |
| **业务仓库** | 根目录有 `HARNESS.md`（或先运行 `dev-harness-context` 生成） |

### 安装 dev-harness

```bash
# 克隆仓库
git clone https://github.com/your-org/dev-harness.git
cd dev-harness

# 安装到 Cursor skills 目录（运行后按提示选择安装位置）
python install.py
```

### 初始化业务仓库上下文

在业务仓库根目录，用 Cursor 打开并执行：

```
使用 dev-harness-context 扫描本仓库
```

首次执行使用 `scan`，只创建缺失的 `README.md`、`AGENTS.md`、`ARCHITECTURE.md`、`HARNESS.md`，不会覆盖现有文件。

项目开发一段时间后需要同步自动识别信息时，使用 `refresh`。它按模板约定的固定 Markdown 标题更新章节，不注入 HTML 管理标记，并保留其他人工章节以及原文件编码、换行和权限：

```bash
dev-harness-context refresh <repo-path>
```

非交互环境默认只预览差异；确认后可使用 `--force` 应用成功定位的章节。固定标题缺失、重复或层级变化时停止更新；旧版合法 managed 标记会在首次刷新时无损移除。

AGENTS 中只保留轻量的项目规范索引。Context 会识别已有 Git 工作流、代码规范、发布规范和 changelog 文档并刷新路径，但不会创建这些专业文档。Git/提交/tag/发布规范缺失时由 `dev-harness-git-workflow` 在用户确认后初始化；代码规范不自动生成；`CHANGELOG.md` 仅在确认初始化或首次发布时创建。

然后用 `dev-harness-commands` 补齐真实命令映射：

```
使用 dev-harness-commands 帮我定义 build / quick / bugfix / full 命令
```

---

## 二、核心工作流

### 2.1 Bug 修复流程（推荐）

使用 `dev-harness-auto-fix` 一键串联完整修复流水线：

```
# 方式 1：提供 issue URL
修这个 bug https://github.com/owner/repo/issues/123

# 方式 2：直接描述
自动修这个 bug：登录后点击设置按钮崩溃，复现步骤：1. 登录 2. 点设置

# 方式 3：触发 auto fix
auto fix
```

**流水线顺序**：Bug 上下文 → 复现收敛 → 根因定位 → 修复生成 → 审查 → 验证闭环 → 分支提交

### 2.2 配套 Skills

| Skill | 用途 |
|-------|------|
| `dev-harness-context` | 初始化上下文文件，并按固定 Markdown 标题安全刷新自动识别章节 |
| `dev-harness-commands` | 补齐 build / quick / bugfix / full 的真实命令映射 |
| `dev-harness-auto-fix` | 执行内置的复现、定位、修复、审查与验证流程 |
| `dev-harness-git-workflow` | 遵循项目已有 Git 规范；缺失时确认并初始化提交、tag、changelog 和发布约定 |
| `dev-harness-retro` | 复盘并更新 `LESSONS.md` |

复现（repro）、定位（triage）、回归（regression）和验证（verify）已内置为 `dev-harness-auto-fix` 的流程阶段，不再作为 `dev-harness-repro`、`dev-harness-triage`、`dev-harness-regression`、`dev-harness-verify` 独立安装或调用。

**典型 Prompt**：

```
使用 dev-harness-auto-fix 处理这个 bug：<描述现象>。
先收敛最小复现与证据（日志/截图/版本），确认根因后再修改代码。
```

### 2.3 回归测试

影响面大时，追加：

```
使用 dev-harness-auto-fix 时给出回归落点（自动化或手工检查表）。
```

---

## 三、HARNESS.md 项目构建与验证契约

`HARNESS.md` 是项目构建、验证和执行环境的唯一事实源，记录真实可执行命令、运行条件和验证边界。

AI Agent 在执行构建、测试或验证命令前必须先读取该文件，不得根据 README、CI 配置或生态经验猜测、替换或覆盖其中的命令。行为、安全和修改边界以 `AGENTS.md` 为准；具体命令和执行环境以 `HARNESS.md` 为准。

### 必须包含的区域

```markdown
## 自动识别构建命令候选
- **build**: `<自动识别候选或 Unknown>`
- **quick**: `<自动识别候选或 Unknown>`
- **bugfix**: `<自动识别候选或 Unknown>`
- **full**: `<自动识别候选或 Unknown>`

## 已确认命令（人工维护）
- **build**: `<真实构建命令或 Unknown>`
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

先用 `dev-harness-commands` 补齐命令映射，再继续修复。

**Q: 修复触及高风险区域被拦截**

dev-harness 对底层 native bridge、ABI、C++/CLI、Win32 API 等区域设置了强制确认门禁。需要人工确认后才能继续。

**Q: 没有 GitHub/GitLab issue，只有内部描述**

直接将 bug 标题 + 现象 + 复现步骤粘贴给 AI，auto-fix 支持手动输入模式。

**Q: 多仓库项目（如前端 + 后端）**

auto-fix 支持多仓库，完成报告会输出每个仓库的分支/commit 信息表格。

---

## 五、参考文档

| 文档 | 说明 |
|------|------|
| `README.md` | 项目概览和 skill 列表 |
| `docs/GIT_WORKFLOW.md` | Git 分支命名和提交信息规范 |
| `docs/BUGFIX_GUIDE.md` | Bug 描述格式指南 |
| `docs/CLIENT_PROJECT_ONBOARDING.md` | 新项目接入 dev-harness 指南 |
| `docs/TESTING.md` | 测试策略说明 |
