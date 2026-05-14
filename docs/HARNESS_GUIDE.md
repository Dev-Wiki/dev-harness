# dev-harness 使用指南

面向 **Cursor** 环境，使用 **`dev-harness-*`** skills 时的通用操作说明。

业务仓库需已具备 **`AGENTS.md`**、**`HARNESS.md`**，且 **`harness:quick` / `harness:build` / `harness:bugfix` / `harness:full`** 映射为**真实可执行**命令（缺失时用 **`dev-harness-commands`** 补齐，禁止编造）。各项目具体命令以该仓库根目录 `HARNESS.md` 为唯一事实源。

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

这会生成/更新 `README.md`、`AGENTS.md`、`ARCHITECTURE.md`、`HARNESS.md`。

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

### 2.2 手动分步使用

| 步骤 | Skill | 说明 |
|------|-------|------|
| 1. 复现收敛 | `dev-harness-repro` | 收敛最小复现步骤和证据 |
| 2. 根因定位 | `dev-harness-triage` | 追踪调用链，定位根因 |
| 3. 验证 | `dev-harness-verify` | 运行 build / test / bugfix check |
| 4. 提交 | `dev-harness-git-workflow` | 校验分支命名，生成规范 commit |
| 5. 复盘 | `dev-harness-retro` | 提取 AI 犯错记录，更新 LESSONS.md |

**典型 Prompt（手动模式）**：

```
帮我定位这个 bug：<描述现象>
按 dev-harness-repro 收敛最小复现与证据（日志/截图/版本）。
按 dev-harness-triage 做根因定位；在我明确确认根因前不要改代码。
```

### 2.3 回归测试

影响面大时，追加：

```
按 dev-harness-regression 给出回归落点（自动化或手工检查表）。
```

---

## 三、HARNESS.md 规范

HARNESS.md 是 dev-harness 的核心契约文件，定义了项目的构建/测试命令映射。

### 必须包含的字段

```markdown
## 构建命令
- **build**: <真实构建命令>
- **quick**: <快速构建/编译检查命令>
- **bugfix**: <bugfix 验证命令>
- **full**: <完整构建+测试命令>
```

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
