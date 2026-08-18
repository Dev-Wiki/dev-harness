# dev-harness

**AI 编码助手的项目工程约束层** — 统一项目上下文、文档、规划、验证命令和 Git 流程，并为 Bug 修复与大型代码库审计提供可持久化、可验证的工作流。

---

## 为什么需要 dev-harness？

模型可以理解、设计、编码和 Review，但同一项目换开发者、换 Agent 或跨会话后，项目事实、命令、计划格式和完成证据很容易漂移。dev-harness 聚焦三件事：

- **Consistency（一致性）**：项目契约不随开发者或 Agent 改变；
- **Evidence（证据）**：关键结论绑定仓库、命令、diff、测试、调用链或快照；
- **Continuity（连续性）**：长任务、上下文压缩和会话切换后可从项目产物与 Git 私有状态恢复。

这些能力共同组成逻辑上的 **Project Contract**，不额外复制成一个中心配置文件：

```text
Project Contract
├── Context: README / ARCHITECTURE / AGENTS
├── Verification Interface: HARNESS.md
├── Documentation Governance: 现有 doc/ 或 docs/
├── Planning Contract: <docs-root>/plan/
├── Git Policy: 项目自己的 Git / release / changelog 文档
├── Retrospective Knowledge: LESSONS.md 与提升候选
└── Codebase Audit: <docs-root>/audit/ + Git 私有状态
```

Auto Fix 仍是最成熟的证据工作流：`复现 → 可证伪根因 → RED → 最小修复 → GREEN → 审查 → 最终验证`。Codebase Audit 则解决大型存量仓库无法一次装入上下文时，如何分阶段扫描未知问题并持久化证据。

---

## 30 秒看懂

安装后，在 AI 助手里直接说人话：

```
# 初始化一个新仓库（让 AI 理解你的项目结构）
扫描这个仓库并生成上下文文件

# 开发一段时间后刷新自动识别区块和规范索引
刷新这个仓库的项目上下文

# 整理项目文档（保留已有 doc/ 或 docs/ 根目录）
审计并整理这个仓库的文档结构、导航和 SSOT

# 更新文档（只写入代码/验证已证明的事实）
按本次改动同步仓库文档中的命令、路径和事实

# 审计大型存量代码库（只输出审计文档，不修改业务代码）
基于项目 Context 初始化 codebase audit，并按模块边界分阶段执行

# 只分析，不改代码
分析这个 bug：登录后点击设置崩溃，使用 analyze 模式

# 修 bug，但不提交
自动修这个 bug：登录后点击设置崩溃，使用 fix 模式

# AI 会按流程走：
#   1. 固定工作区快照 → 2. 确认复现 → 3. 用探测证伪根因
#   → 4. 回归先失败 → 5. 最小修复 → 6. 回归通过
#   → 7. 按当前 diff 审查并最终验证

# 提交代码（自动检查分支命名、拦截调试残留）
帮我提交当前修改

# 显式复盘（分类为 FACT / POLICY / LESSON，稳定结论再提升）
retro：总结这次任务并沉淀 promotion candidates
```

AI 会在每一步输出进度和证据，而不是闷头改完告诉你"修好了"。

---

## 安装

支持 **Cursor、Codex CLI、OpenCode、Antigravity**。

**macOS / Linux：**

```bash
./install.sh --ide cursor       # 安装到 Cursor
./install.sh --ide codex        # 安装到 Codex CLI
./install.sh --ide opencode     # 安装到 OpenCode
./install.sh --ide antigravity  # 安装到 Antigravity
```

**Windows：**

```powershell
.\install.bat --ide cursor
.\install.bat --ide codex
.\install.bat --ide opencode
.\install.bat --ide antigravity
```

**其他用法：**

```bash
./install.sh --target /custom/path    # 安装到自定义目录
./install.sh --export dist            # 导出便携目录 dist/bundle/
./install.sh --ide cursor --skill dev-harness-context   # 只装一个 skill
```

版本 zip 由维护者运行 `python release.py` 生成。

---

## Skills 一览（8 个可发现 Skill）

### Project Contract / Governance

| Skill | 干什么用 |
|-------|---------|
| `dev-harness-context` | 初始化上下文文件，并安全刷新自动识别区块与项目规范索引 |
| `dev-harness-docs` | 识别现有 `doc/` 或 `docs/` 根目录，整理索引、渐进式导航、SSOT、归档和链接，并把已验证事实同步进现有文档 |
| `dev-harness-planning` | 根据需求文档、原型或参考格式，在现有文档根目录生成 `plan/Dashboard.md` 和 `TaskDetails.md` |
| `dev-harness-commands` | 把项目中的真实命令统一映射为 `build / test / quick / bugfix / full` 五个语义入口 |
| `dev-harness-git-workflow` | 优先遵循项目 Git 规范；缺失时确认并初始化提交、tag、changelog 和发布约定 |
| `dev-harness-retro` | 仅在用户显式触发时复盘，分类 FACT / POLICY / LESSON，并输出契约提升候选 |

### Evidence-driven Long-running Workflows

| Skill | 干什么用 |
|-------|---------|
| `dev-harness-auto-fix` | 可选择 analyze / fix / commit / unattended；用运行时约束复现、可证伪根因、RED/GREEN、diff 绑定审查与精确提交 |
| `dev-harness-codebase-audit` | 基于 Canonical Context 动态分区大型代码库，跨会话持久化任务、证据与 Finding，并在仓库漂移时 fail-closed |

> 每个 skill 的模板、references 和脚本跟随该 skill 自己安装，保持资源自包含。

> 复现 / 定位 / 回归 / 验证四阶段已内联为 auto-fix 的参考文件 `references/bugfix-flow/*.md`，不再作为独立 skill 安装。

### Auto-fix 的 dirty worktree 策略

开始任务时，auto-fix 会把已有修改记录进 `WorkspaceSnapshot`。这些修改可以原样保留，不要求 stash 或清空；AI 只维护本轮对话产生的 `AutoFixChangedFiles`。

- 已有脏文件不被修改、暂存或提交。
- 如果目标文件在任务开始时已经脏，流程停止，让用户决定如何合并语义。
- commit 模式只逐文件暂存本轮集合；暂存区含其他内容时报告冲突，不替用户取消暂存。
- HEAD、分支、已有修改或未声明文件发生漂移时停止，避免把别的工作误算成本轮结果。

`auto-fix/runtime.py` 只负责快照、状态机和 diff 证据，不是替代 AI Agent 的一键修复器。

### Codebase Audit 的边界

Codebase Audit 面向“仓库中还有哪些未知问题”，先按 subsystem、runtime/platform boundary、shared core、native bridge、数据与外部集成动态分区，再沿调用链和数据流渐进读取。它不内置巨型语言 checklist，也不修改源码。

- 审计状态位于 `.git/dev-harness/codebase-audit/<run-id>/state.json`；
- 版本化产物位于已有 `<docs-root>/audit/`，包含 Dashboard、稳定 Finding Registry、任务、结果和总报告；
- Confirmed Finding 必须有代码或运行证据、反证检查与 Snapshot；
- HEAD、分支、Context 或业务源码漂移后，旧证据会被标记 stale；
- 缺陷交给 Auto Fix，架构/技术债交给 Planning，验证命令或治理缺口交给对应 owner。

---

## 通用项目识别与增强 Profile

`dev-harness-context` 默认由 AI 基于仓库证据识别语言、框架、架构和验证入口，不要求先为新技术栈增加扫描器分支。确定性代码负责证据收集、结论校验，并按固定 Markdown 标题安全更新章节，不向文档注入管理标记。

当前内置以下增强 Profile，用于离线规则回退和专业风险补充：

| 类型 | 覆盖 |
|------|------|
| **WPF** | C# + 可选 C++/CLI native bridge |
| **Harmony** | ArkTS / HarmonyOS |
| **Win32** | C++ / MSBuild |
| **Qt** | Windows + Linux，含 Shared C++ Core 检测 |
| **Go** | 后端服务，识别 CGO 边界与核心并发逻辑 |
| **Flutter** | 跨端客户端，识别 Platform Channels 与原生代码边界 |
| **Node.js** | 前端工具链与插件（识别跨 Workspace 与生命周期钩子） |
| **FastAPI** | Python 后端服务，识别 ASGI 入口、router/service 调用链与 pytest 验证命令 |

其他项目类型通过 `evidence → AI semantic analysis → validator → safe writer` 主路径识别。只有证据不足的单项标记为 `Unknown`；低置信度结论进入“需人工确认”。

```bash
dev-harness-context evidence /path/to/repo
dev-harness-context scan /path/to/repo --analysis /tmp/context-analysis.json
dev-harness-context refresh /path/to/repo --analysis /tmp/context-analysis.json
```

每个 AI 结论都必须引用仓库内证据并绑定扫描快照指纹；无证据命令、越界路径、无效行号或仓库漂移会在写入前被拒绝。证据明细保留在分析 JSON 中，不复制到 AGENTS/HARNESS；README 的核心模块优先采用 AI 基于源码给出的真实职责。

安装、构建、运行和验证命令按真实语义区分。依赖安装不会冒充 build；Python 服务没有独立编译或打包步骤时，build 明确标记为 `N/A`。

### 项目规范如何组织

`AGENTS.md` 保持为轻量索引：构建与验证指向 `HARNESS.md`，Git、代码风格、发布和 changelog 指向各自的专业文档。详细规则不全部塞入 AGENTS。

| 资源 / 事实 | 写入 Owner | 其他 Skill 的行为 |
|-------------|------------|-------------------|
| Canonical Context 与根文档固定章节 | Context | 只读消费，不复制另一套 Context |
| HARNESS 自动候选 / 人工确认命令 | Context / Commands | Auto Fix 和普通 Agent 只读执行已确认入口 |
| docs root、索引、SSOT、归档 | Docs | Planning / Audit 复用同一个 root |
| `<docs-root>/plan/*` | Planning | Docs 只做导航和归档治理 |
| Git / tag / release / changelog policy | Git Workflow | 其他 Skill 只读消费，动作分离授权 |
| `.git/dev-harness/auto-fix/*` | Auto Fix | Git 私有状态 |
| `<docs-root>/audit/*` 与对应 Git 私有状态 | Codebase Audit | Docs 只做导航；后续处理通过 handoff |
| `LESSONS.md` 与 Promotion Candidates | Retro | 不自动升级为正式 Fact / Policy |

- `dev-harness-context` 只识别这些文档并在 `refresh` 时更新索引，不自动创建 Git、代码或发布规范，也不自动创建 `CHANGELOG.md`。
- `dev-harness-docs` 维护项目已有 `doc/` 或 `docs/` 的信息架构、入口、SSOT 和归档规则，不改名或创建第二套文档根目录。
- `dev-harness-planning` 复用同一个文档根目录，将 Dashboard 作为索引层、TaskDetails 作为执行与专题层。
- `dev-harness-codebase-audit` 独占 `<docs-root>/audit/` 的审计内容；Docs 只负责导航、链接和归档治理。
- `dev-harness-git-workflow` 先读取项目或团队已有规范；没有规范时才分析历史、展示候选，并在用户确认后初始化默认规范。
- `dev-harness-retro` 只在显式触发时维护复盘历史；Lesson 默认不是硬规则，稳定 Fact/Policy 提升到对应 owner。
- 代码规范文档只做识别，不根据 lint/formatter 配置自动生成。
- `CHANGELOG.md` 在用户确认初始化或开始首次发布时创建；默认发布分类为 Breaking Changes、Added、Changed、Deprecated、Fixed、Removed、Security，空分类不进入 tag message 或 release notes。

---

## 文档导航

- [文档中心](docs/README.md)：按使用、维护、范围与设计记录组织全部项目文档。
- [V1 / VNext 与 V2 边界](docs/V1_V2_BOUNDARIES.md)：当前能力范围和封板标准的唯一事实源。
- [VNext 优化与 Codebase Audit 设计方案](docs/dev-harness%20VNext%20%E4%BC%98%E5%8C%96%E4%B8%8E%20Codebase%20Audit%20%E8%AE%BE%E8%AE%A1%E6%96%B9%E6%A1%88.md)：v1.8.0 的设计依据与取舍记录，不作为后续排期表。
- [V2 Backlog](docs/V2_BACKLOG.md)：超出当前边界的候选能力与启动条件。

设计记录解释“为什么这样设计”，边界文档说明“当前承诺什么”，Backlog 记录“未来可能做什么”；三者不重复维护状态。

---

## 设计边界

**dev-harness 做了什么：**
- 固定跨 Agent 的 Project Contract 格式、owner 和交接边界
- 用 Git 私有状态、工作区快照和 diff hash 把关键边界变成可测试契约
- 让 bugfix 与大型代码库审计可恢复、可追溯、可验证
- 让项目上下文、深度文档和计划共享清晰入口与 SSOT，避免重复文档根目录
- 跨平台、跨 IDE，纯 skills bundle，不需要改你的项目工具链

**dev-harness 不做什么：**
- 不以覆盖完整 SDLC 或堆叠通用 AI Skills 为目标
- 不重复提供 frontend/backend/database/security/performance 等模型已经具备的通用方法教程
- 不提供 UI 自动化测试
- 不做截图驱动验证
- 不搭建日志/指标/Trace 平台
- 不替代完整的 Diataxis 内容生成或发布前文档覆盖率审计工具
- 不是一键修 bug、静态分析或自动 PR 的黑盒工具

详见 [V1 / VNext 与 V2 边界文档](docs/V1_V2_BOUNDARIES.md)。

---

## License

MIT
