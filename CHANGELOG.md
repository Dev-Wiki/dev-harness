# CHANGELOG

## v1.2.0 — 2026-06-01

### 扩展多语言项目支持与安全拦截

**新增：**
- **Go 后端项目**：支持上下文分析与验证闭环，并增加 CGO 边界与核心并发逻辑（Goroutines 泄露）的自动拦截。
- **Flutter 跨端客户端**：支持项目结构分析、框架约束加载，并强化 Platform Channels 与原生代码边界的修改确认。
- **Node.js 前端工具链与插件**：支持包含 `plugin.json` 插件类的分析，加入跨 Workspace 依赖覆盖与生命周期钩子篡改的拦截网。
- **Retro 经验沉淀**：新增 L001 通用防越界规则，阻止 AI 错误修改全局安装目录下的产物。

**调整：**
- 移除了 `dev-harness-auto-fix` 中原有的“仅限 Qt/Harmony”硬阻断，现根据读取到的语言标识动态挂载风险拦截规则。
- 补充并更新了 `commands` 脚本中 Go 和 Node.js 对应的自动化测试指令及门控状态。
- 更新了 README 项目支持矩阵。

---## v1.1.0 — 2026-05-18

### 内联 bugfix 四阶段并删除 pilot（skill 数 10 → 5）

**破坏性变更**：移除独立 skill `dev-harness-repro`、`dev-harness-triage`、`dev-harness-regression`、`dev-harness-verify` 以及 `dev-harness-pilot`。

- 流程细则迁至仓库 `internal/bugfix-flow/*.md`，安装时复制到 `dev-harness-auto-fix` 的 `references/bugfix-flow/`。
- auto-fix 在执行到对应步骤时**按需读取**参考文件，不再作为宿主可发现的独立 skill。
- pilot 的三条分支（初始化→context，修 bug→auto-fix）本身冗余，一并移除。
- 可安装 skill 数由 10 降为 **5**（commands / context / git-workflow / auto-fix / retro）。

**升级**：重新运行 `./install.sh --ide cursor`（或等价命令）。可手动删除旧目录 `skills/dev-harness-repro` 等以免残留。

---

## v1.0.1 — 2026-05-18

### 上下文工程优化（基于 context-engineering 分析）

**① 防止 Context Flooding**
所有 skill preamble 由全量 `cat LESSONS.md` 改为 Python 过滤 Top 10 高频规则（按触发次数倒序），无 Python 环境时 fallback 到 `cat`。防止 LESSONS.md 增长后挤占 AI 上下文窗口。

**② Inline Planning Pattern（auto-fix）**
`dev-harness-auto-fix` Step 0.7 新增执行计划输出，列明 8 步链路、项目画像、可用状态和审查模式，供用户在进入 Step 1 前确认方向。

**③ Trust Level 标注**
`AGENTS.template.md` 新增 §1b「文件信任等级」，三级区分：✅ 可信源码 / ⚠️ 需核实配置与外部文档 / ❌ 不可信用户内容，防止 prompt injection。

---

## v1.0.0 — 2026-05-14

首个正式版本发布。

### Skills

- `dev-harness-pilot` — 入口 skill，根据目标路由到对应 skill
- `dev-harness-context` — 扫描仓库，生成 `README.md`、`ARCHITECTURE.md`、`HARNESS.md`、`AGENTS.md`
- `dev-harness-commands` — 统一 `build / quick / bugfix / full` 命令入口
- `dev-harness-repro` — 复现条件收敛
- `dev-harness-triage` — 调用链追踪与根因定位
- `dev-harness-regression` — 回归覆盖与测试锚点定义
- `dev-harness-verify` — 分层验证命令与完成证据
- `dev-harness-git-workflow` — 分支命名校验、commit message 生成、调试残留拦截（Conventional Commits 规范）
- `dev-harness-auto-fix` — 全流程自动修复：bug 描述 / issue URL → 根因 → 修复 → 审查 → 提交
- `dev-harness-retro` — 任务复盘，提取 AI 犯错规则写入 `LESSONS.md`

### 扫描器

- `context/cli.py`：项目类型检测使用通配模式和动态命名空间推断，不依赖特定项目名称
- `platform_profiles.py`：Harmony 打包脚本检测使用 `buildScript/*_package.py` glob
- 当前优先支持栈：WPF、Harmony、Win32、Qt（含 Shared C++ Core）

### 工程基础

- `VERSION` 文件作为版本单一事实源
- `install.py` 安装/导出时自动向每个 SKILL.md frontmatter 注入 `bundle_version`
- `release.py` / `release.bat` / `release.sh`：一键打包 `dev-harness-vX.Y.Z.zip`
- 支持平台：Cursor、Codex CLI、OpenCode、Antigravity
- 测试：14 个 unittest，覆盖扫描器核心路径

### 文档

- `docs/HARNESS_GUIDE.md`：通用使用指南
- `docs/GIT_WORKFLOW.md`：Conventional Commits 分支与提交规范参考