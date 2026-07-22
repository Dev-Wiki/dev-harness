# CHANGELOG

## Unreleased

---

## v1.5.1 — 2026-07-22

### Context 文档去噪与语义校验

- README 使用真实项目名作为一级标题，过滤运行时目录和无依据的通用目录占位描述，并支持语义分析提供真实 `core_modules` 职责。
- AGENTS/HARNESS 不再写入内部证据审计字段、无意义的 `- Unknown` 列表、绝对工作目录或与项目无关的 SDK/C++ 模板术语。
- Python 依赖安装与构建语义分离；无独立编译或打包步骤时 build 明确为 `N/A`。
- 证据引用新增行号范围校验；带强约束词的结论要求精确行证据，安装命令不得声明为 build 命令。
- 补充 Python 应用启动、数据库初始化、并发锁/重试、外部调用和服务安装入口的高风险识别。

---

## v1.5.0 — 2026-07-16

### 通用 AI 语义识别

- 新增框架无关的 `evidence` 命令，输出仓库清单、分析字段契约、截断状态和快照指纹。
- 新增 AI Semantic Analysis JSON 协议；未知语言或框架无需先增加硬编码 profile 即可生成项目类型、架构、调用链、风险边界和命令候选。
- 所有非 `Unknown` 结论必须携带仓库内证据路径与 high/medium/low 置信度，并在 AGENTS/HARNESS 中保留证据台账。
- 低置信度结论自动转入人工确认；无证据命令、仓库外路径、未知字段和过期快照在写入前拒绝。
- 内置 WPF、Qt、Harmony、Win32、FastAPI 等 profile 调整为兼容回退和专业风险增强，不再作为项目识别白名单。
- 安装包新增 `evidence.py` 与 `semantic.py` 运行时，并覆盖安装后 evidence/analysis 调用。

---

## v1.4.0 — 2026-07-16

### Context 安全刷新与 FastAPI 支持

- 新增 `refresh` 固定 Markdown 章节刷新，不注入管理标记，并保留其他用户章节、编码、换行和文件权限。
- `scan` 改为只创建缺失文件，即使传入 `--force` 也不会覆盖已有上下文文档。
- 新增项目自有 Git、代码、发布和 changelog 规范索引，并对冲突引用给出人工确认项。
- 新增 FastAPI 项目识别，基于依赖和源码证据发现 ASGI 入口、router/service/core 调用链及高风险边界。
- 自动生成 FastAPI 的 Python 编译检查、uvicorn 运行命令和 pytest quick/bugfix/full 候选。

### 构建与验证契约

- 将 `HARNESS.md` 明确为构建、验证和执行环境的唯一事实源。
- 安装包新增 Git workflow 默认模板与 Context 固定章节刷新运行时。

### Auto-fix 可执行契约

- 新增 `auto-fix/runtime.py`，提供 WorkspaceSnapshot、工作区归属校验、稳定 diff hash、Git 私有状态文件和阶段状态机。
- 新增 analyze / fix / commit / unattended 四种授权模式；fix 不再隐式提交，Issue 回写、push、PR、发布仍需独立授权。
- dirty worktree 允许保留：快照时已有修改归用户所有；本轮只允许修改和精确暂存 AutoFixChangedFiles，检测到已有修改漂移或未声明变更即停止。
- 根因判断改为 Claim / Prediction / Probe / Observation / Status 可证伪结构；连续假设失败时返回 NEEDS_CONTEXT/BLOCKED。
- 回归测试成为写模式默认门禁，要求修复前 RED、修复后 GREEN；客观无法自动化时显式降级为 DONE_WITH_CONCERNS。
- review 与最终验证绑定 diff hash；实现变化会清空旧 Review/Verify 证据。
- 安装包现包含 auto-fix runtime，并新增运行时、契约及安装产物测试。

---

## v1.3.0 — 2026-07-10

### 新增规划阶段 skill 模板

- 新增 `dev-harness-planning`，用于在进入实现前生成任务看板与任务详情。
- 新增 `planning/templates/Dashboard.template.md` 与 `planning/templates/TaskDetails.template.md`，随安装包一起导出。
- 调整 `install.py`，确保 planning skill 与其模板能被安装和打包。
- 将 context 相关模板迁移到 `context/templates/`，安装后保持 skill-local 目录结构。
- 更新 README / 英文文档 / 模板说明，并补充安装测试覆盖 planning 模板。

---

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

---

## v1.1.0 — 2026-05-18

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
