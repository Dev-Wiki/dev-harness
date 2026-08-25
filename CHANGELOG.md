# CHANGELOG

## Unreleased

---

## v1.11.1 — 2026-08-25

### Changed

- `dev-harness-planning` 将 Dashboard 收敛为唯一活跃计划入口；任务文件只维护执行详情，既有 `TaskDetails.md` 迁移后仅保留兼容跳转，避免多份可变状态导致 AI 读取漂移。
- 领取、恢复、迁移和收口任务时增加临时规划快照与漂移门禁，核对 `HEAD`、Dashboard、任务路径、内容哈希和既有工作区变化后再继续。

---

## v1.11.0 — 2026-08-25

### Added

- `dev-harness-planning` 新增 `tasks/<Task-ID>.md` 活跃任务分片与 `archive/<milestone>/` 完成任务归档模板，使 AI 可以只加载当前任务详情。
- 大型旧版单体 `TaskDetails.md` 新增按需迁移参考，覆盖任务范围台账、状态回退、里程碑缺失、仓库级入站链接和移动后相对链接校验。

### Changed

- Planning 的 `TaskDetails.md` 收敛为活跃任务入口；单体详情超过 1,000 行、100 KB 或 20 个任务正文时，在继续追加前执行兼容迁移。
- 完成任务在记录最终验收证据后退出活跃索引；Dashboard 最多保留五项最近完成摘要，编辑过程继续由 Git 历史承担。
- 8 个 Skill 统一补充输出语言契约：用户未指定语言时，中文项目和新建文档默认使用自然简体中文；刷新既有文档时沿用主体语言。
- 面向读者的标题、表格、验证结论、最终报告、提交说明和发布文案优先采用中国开发团队常用表达；路径、命令、API、协议、必要缩写和内部枚举保持稳定。

---

## v1.10.0 — 2026-08-20

### Added

- `dev-harness-codebase-audit` 新增明确的 Engineering Audit Scope：面向用户拥有或明确授权的代码仓库，聚焦工程质量、行为正确性和跨模块一致性，并与 penetration testing / offensive security workflow 清晰分离。
- Codebase Audit 新增运行级 `output_language` 约定：默认生成自然中文审计文档，只有用户显式要求全英文时才生成英文文档；内部状态枚举保持稳定，中文仅作为显示层。

### Changed

- Codebase Audit 的运行时验证明确限定为本地、确定性、最小复现，围绕项目声明行为验证触发条件、状态变化、错误传播和高影响操作的实际结果。
- Finding 合并增加 identity gate：Candidate 默认独立保留，只有根因、职责归属、修复边界及单一修复效果均一致时才合并，并继续在 Cross-module Reconciliation 中完成端到端复核、矛盾处理和 Severity / Confidence 重排。
- Audit references、templates 与示例改用工程质量语义和自然中文表达，保留 Audit Snapshot、Finding Registry、Evidence / Counter-evidence、状态机、workspace drift、fail-closed 与只审计不修改业务源码等既有能力。

---

## v1.9.1 — 2026-08-19

### Changed

- Capability Catalog、文档治理、Context、Planning、Audit、Retro 与 Bugfix 模板统一采用自然中文表达，避免把 `observable capability`、`leaf capability`、`owner`、`promote` 等概念逐词翻译成生硬术语。
- Context 新生成文档使用“代码风格示例”“核心业务流程”“编译与启动问题排查”“新增功能的一般流程”等标题，并兼容识别和迁移旧标题。

### Fixed

- `dev-harness-docs` 增加中文术语约束和防直译测试，明确“可观测性”仅用于日志、指标和链路追踪，不用于描述产品功能。

---

## v1.9.0 — 2026-08-19

### Added

- `dev-harness-docs` 新增条件性 Capability Catalog 契约与自包含模板：复用已有范围 SSOT，缺失时按现有产品目录选择落点，并分离产品状态、适用范围、交付基线、验证级别和证据。

### Changed

- Codebase Audit 将文档可发现性纳入 Dashboard、Report 与完成口径；继续保持 `<docs-root>/audit/**` 写入边界，缺少文档中心入口时显式交给 Docs Refresh，根 README 快捷链接保持可选。

---

## v1.8.1 — 2026-08-19

### Fixed

- 将 `dev-harness-docs` 的 OpenAI 展示名与实际 Skill 名统一，并通过安装产物测试锁定该元数据，避免它单独显示为 `Dev Harness Docs`。

---

## v1.8.0 — 2026-08-18

### Added

- 新增 `dev-harness-codebase-audit`：基于 Canonical Context 动态分区大型代码库，使用 Git 私有状态持久化 AuditSnapshot、任务与 Finding，并将版本化产物限制在既有 `<docs-root>/audit/`。
- Codebase Audit runtime 新增 workspace/context drift、输出路径、防 symlink escape、Finding 状态与 confirmed evidence 校验，以及 init/resume/status/task/finding/cross-module/complete CLI。
- 安装、单 Skill 安装、export 与 release archive 纳入 Audit runtime、references 和 templates。
- 新增 `docs/README.md` 文档中心，并将 VNext 方案作为 v1.8.0 的设计依据纳入导航。

### Changed

- 顶层定位收敛为 Consistency / Evidence / Continuity 驱动的 Project Contract，不再只以 Bugfix 为叙事，也不扩展为通用 AI Skills 百科。
- Retro 改为仅显式触发，使用 FACT / POLICY / LESSON 与 Promotion Candidates；installer 和其他 Skill 不再无条件注入或读取 `LESSONS.md` 硬规则。
- HARNESS 验证接口补齐 `test`，并支持简单单值命令与多 Platform / Variant 命令记录。
- Context、Commands 与 Git Workflow 的平台/默认值说明下沉为按需 references；Planning refresh 明确保留 Task ID 和有证据的完成状态。
- 明确当前范围由 V1 / VNext 边界文档维护、未来候选由 V2 Backlog 维护，设计记录不再充当活动任务清单。

### Removed

- 移除已由当前代码、测试和专题文档承接的 `docs/superpowers` 实施计划与设计草案，历史决策继续由 Git 记录保留。

---

## v1.7.0 — 2026-08-04

### Added

- `dev-harness-docs` 新增 `Update` 操作：只把代码、配置或成功验证证明的可复用事实同步进现有文档；生成最小更新计划、保留人工章节与格式，未验证项进入待确认，不依赖外部文档包。
- 信息架构参考新增"已验证事实更新纪律"；gstack 等外部文档包明确为可选重量级通道（全量内容生成、发布审计），日常事实同步默认走内置 Update。

---

## v1.6.0 — 2026-08-03

### Added

- 新增 `dev-harness-docs`，复用项目已有 `doc/` 或 `docs/` 根目录，提供文档索引、渐进式导航、SSOT、归档与链接验证工作流。
- 内置文档中心、维护规则和导航模板，并附带信息架构与安全迁移参考；安装与发布包保持 skill 自包含。

### Changed

- `dev-harness-planning` 改为先解析项目文档根目录，再生成 `plan/Dashboard.md` 与 `plan/TaskDetails.md`，避免创建第二套文档树。

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
