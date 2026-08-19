# dev-harness VNext 优化与 Codebase Audit 设计方案

> 状态：已在 dev-harness v1.8.0 实施，现作为设计依据与取舍记录保留。
>
> 当前范围与封板标准以 [`V1_V2_BOUNDARIES.md`](V1_V2_BOUNDARIES.md) 为唯一事实源；未来候选以 [`V2_BACKLOG.md`](V2_BACKLOG.md) 为唯一事实源；使用与维护入口见 [`docs/README.md`](README.md)。本文的 Stage、执行指令和未来时态保留为实施期历史，不再构成活动任务或授权。
>
> 历史用途：交给编码 Agent，在当前 dev-harness 仓库中实施优化。本文描述目标设计与实施约束，不要求机械照搬具体文件名或代码结构；当设计与可靠实现冲突时，以兼容性和经过测试的当前实现为准。

## 0. 实施结果与文档所有权

v1.8.0 已落地本文的稳定设计结论：以 Consistency / Evidence / Continuity 为目标的逻辑 Project Contract、五命令 HARNESS 接口、显式 FACT / POLICY / LESSON Retro、按需 references、可恢复且 fail-closed 的 Codebase Audit，以及安装与测试覆盖。

为避免同一状态在多处漂移，本文只解释“为什么这样设计”：

- 当前已包含/不包含的能力、封板标准：`V1_V2_BOUNDARIES.md`；
- 超出当前边界的候选与启动条件：`V2_BACKLOG.md`；
- 用户入口与能力概览：根 `README.md` 与 `docs/README_EN.md`；
- 精确 CLI、模板和行为：对应 Skill、runtime 与 tests；
- 版本变化：根 `CHANGELOG.md`。

本文与 V1/V2 规划没有功能冲突。名称上的关系是：本文的 “VNext” 已作为 v1.8.0 纳入 V1 范围，而 V2 仍表示需要真实项目试点后才可能启动的深化方向。

---

## 1. 改造目标

本次改造不是把 `dev-harness` 做成“大而全的 AI 软件工程 Skill 集合”，也不是给 AI 补充它已经具备的编程、架构、Review、安全、性能、测试等通用能力。

`dev-harness` 的核心定位应收敛为：

> **为不同开发者、不同 AI Agent、不同会话和不同项目阶段提供一致的项目工程契约、可验证证据，以及可恢复、可持续维护的任务状态。**

三个核心关键词：

1. **Consistency（一致性）**：同一项目换开发者、换 Codex / Claude / Gemini 后，项目上下文、规划格式、文档组织、验证命令和 Git 流程仍保持一致。
2. **Evidence（证据）**：关键结论不能只依赖 AI 声明，必须能绑定真实仓库、命令、diff、测试、调用链或快照。
3. **Continuity（连续性）**：长任务、上下文压缩、会话切换或项目演进后，仍可依据项目产物和 Git 私有状态恢复工作，而不是依赖聊天记忆。

同时支持：

- 新项目：用于初始化并统一项目工程契约。
- 老项目 / 大型存量项目：用于识别真实现状、兼容历史规范、渐进式治理和长任务扫描。

---

## 2. 明确“不做什么”

本项目不要发展成类似“AI 能力百科”的 Skill 集合。

除非未来有非常明确的 Harness 级需求，否则不要新增以下类型 Skill：

- frontend-engineering
- backend-engineering
- database-design
- api-design
- security-review
- performance-review
- generic-code-review
- TDD 教程
- C++ / Python / React / ArkTS 编程方法
- CI/CD 教程
- observability 教程
- UI/UX 设计方法

这些能力现代 Coding Agent 本身已经可以完成。

新增 Skill 必须优先满足至少一类价值：

- 统一团队 / 项目规范；
- 需要固定产物格式；
- 需要跨会话持久状态；
- 需要 Snapshot / drift / diff 等确定性约束；
- 需要证据绑定；
- 需要明确授权边界；
- 需要阻止 AI 在证据不足时声明完成；
- 老项目、大仓库中特别容易因上下文限制失控。

---

## 3. Project Contract：作为逻辑核心，不新增单一大文件

建议在 README / 设计文档中明确引入 **Project Contract** 概念，但不要为了这个概念再创建一个 `PROJECT_CONTRACT.md`。

Project Contract 是现有多个项目文件与 Skill 产物共同组成的逻辑契约：

```text
Project Contract
│
├── Context
│   ├── README.md managed sections
│   ├── ARCHITECTURE.md managed sections
│   └── AGENTS.md lightweight index / constraints
│
├── Verification Interface
│   └── HARNESS.md
│
├── Documentation Governance
│   └── existing doc/ or docs/
│
├── Planning Contract
│   └── <docs-root>/plan/
│
├── Git Policy
│   └── project-owned Git / release / changelog docs
│
├── Retrospective Knowledge
│   └── LESSONS.md + promoted facts/policies
│
└── Codebase Audit
    └── <docs-root>/audit/
```

目标是让每个 Skill 有明确的**所有权边界**，避免多个 Skill 同时维护同一段事实。

---

## 4. 现有 Skill 的目标定位

现有 Skill 不应因为 AI 本身会做相关操作而删除。它们的价值不是“教 AI 做”，而是“规定当前项目应该怎么做、产物长什么样”。

### 4.1 `dev-harness-context`

定位：**Canonical Project Context / 项目事实统一格式**。

职责：

- 从真实仓库识别语言、框架、模块、入口、架构边界、平台、Native 边界、关键风险点和验证候选；
- 输出固定、跨 Agent 稳定的项目上下文结构；
- 使用 Evidence Collector → AI Semantic Analyzer → Deterministic Validator / Writer；
- 所有强事实绑定证据和扫描快照；
- 项目演进后支持 refresh，而不是重新生成一套不同风格的文档；
- `AGENTS.md` 保持轻量索引，不把所有详细规则复制进去。

优化要求：

1. 保留现有 evidence / fingerprint / validator / safe writer 能力。
2. 不把 Context 变成 Code Audit：Context 负责描述“项目是什么、边界在哪里”，不负责系统性寻找所有 bug/技术债。
3. 将过长的平台说明、专业风险提示尽量移到按需读取的 `references/`，减小 `SKILL.md` 固定上下文占用。
4. Profile 用于增强识别和风险提示，不作为技术栈白名单。
5. Context 输出必须足够让新的 Codebase Audit 动态决定审计范围。

### 4.2 `dev-harness-commands`

定位：**Project Verification Interface / 项目验证接口**。

它不是“命令教程”，而是把项目真实存在的构建、测试、验证方式统一映射为稳定接口，供所有 AI 使用。

保留：

- `build`
- `test`
- `quick`
- `bugfix`
- `full`

现有“Context 维护自动识别候选、Commands 维护人工确认命令”的边界应保留。

优化要求：

1. 支持多平台 / 多设备 / 多构建 Variant，而不是假设每类命令只有一个值。例如 Harmony PC / Phone、Debug / Release 可以有不同实际命令。
2. 每个确认命令建议明确：
   - Purpose
   - Command
   - WorkingDirectory
   - Platform / Variant
   - Preconditions
   - DeviceRequirement
   - Shell / Environment（确有需要时）
   - Evidence
   - Status（candidate / confirmed / missing）
3. 保持简单项目仍可只使用单一 `BuildCommand` 等简化形式，避免为了复杂项目让所有项目都复杂化。
4. 把 Windows Shell、平台映射等大段说明拆入 references，SKILL 只保留决策流程。
5. `HARNESS.md` 应成为普通功能开发完成后也能使用的标准验证入口，而不仅仅服务于 auto-fix。
6. 在 AGENTS / Context 模板中明确：Agent 完成功能修改前，应优先使用 HARNESS 已确认命令验证，不得自行猜测生态默认命令。

### 4.3 `dev-harness-git-workflow`

定位：**Project Git Policy / 仓库 Git 流程契约**。

必须保留。

原因：AI 会 Git 操作，但不知道不同公司 / 项目的分支、PR、tag、release、changelog、hotfix 和提交授权规则。

优化要求：

1. 继续坚持“项目已有规范 > 本 Skill 默认值”。
2. 历史 Git 行为只能作为候选证据，不能自动升级为规范。
3. commit / tag / push / PR / release / deploy 分离授权。
4. 与 WorkspaceSnapshot / changed-files 精确范围保持兼容。
5. 默认 Git 契约和大量示例可下沉到 references/templates，主 SKILL 重点保留发现 → 确认 → 执行 → 停止条件。
6. 不扩展成 Git 教程或 GitHub/GitLab 全功能助手。

### 4.4 `dev-harness-planning`

定位：**Project Planning Contract / 项目级规划格式协议**。

必须保留，但要避免用于每一个临时编码小任务。

它解决的问题不是“AI 不会计划”，而是：

- 不同 AI 拆整个项目时粒度和格式不同；
- 不同开发者生成不同风格的规划文件；
- 项目长期演进时任务 ID、状态和链接不稳定。

优化要求：

1. 主要用于项目级、版本级、里程碑级规划，不要因为普通单文件修改自动触发。
2. 保持 `Dashboard.md` + `TaskDetails.md` 固定双层模型。
3. 保持 existing `doc/` / `docs/` 根目录优先。
4. 支持 refresh / merge：已有 Task ID 和已完成状态尽量稳定，不要每次重新生成导致 Git diff 巨大。
5. 已完成任务不能仅凭 AI 推测改成完成；应基于实现 / 验证证据或用户明确状态。
6. 允许项目已有状态/优先级约定覆盖默认模板；没有约定时使用 dev-harness 默认模板，保证跨 AI 一致。
7. Audit 发现的架构/技术债问题可以“建议转 Planning”，但不得自动污染项目 Roadmap。

### 4.5 `dev-harness-docs`

定位：**Documentation Governance / 项目文档治理**。

必须保留。

它不是教 AI 写 README 或 API 文档，而是统一：

- doc/docs 根目录；
- 文档索引；
- SSOT；
- 文档放置位置；
- 归档；
- 链接；
- 已验证事实同步规则。

现有“不要创建第二套文档根目录”和“区分结构治理与内容生成”方向正确，应继续保持。

优化要求：

1. 新增 Codebase Audit 后，`<docs-root>/audit/` 属于 Audit Skill 的内容所有权；Docs 只负责它在文档体系中的导航、归档和链接治理。
2. Docs 自己现有的 `Audit` 操作表示“文档结构审计”，不要与新的代码库审计混为一谈。
3. 因此新的代码扫描 Skill 不建议叫简单的 `dev-harness-audit`。

### 4.6 `dev-harness-auto-fix`

定位：**Evidence-driven Known Problem Workflow / 已知问题的证据驱动修复流程**。

这是 dev-harness 最典型的 Harness 能力，应保持为核心。

保留：

- WorkspaceSnapshot；
- dirty worktree 边界；
- analyze / fix / commit / unattended 授权；
- reproduce；
- falsifiable hypothesis；
- RED / GREEN；
- diff-bound review；
- final verify；
- state.json；
- drift protection。

优化要求：

1. 不要扩展为通用 Coding Skill。
2. 支持把 Codebase Audit 的 Confirmed Finding 作为输入，例如用户说“修复 AUD-017”。
3. Finding 只是调查输入，不能绕过 auto-fix 自己的快照、根因确认、RED/GREEN 和验证门。
4. 如果 Finding 已因仓库变化 stale，必须重新验证证据。
5. 架构重构类 Finding 不适合 auto-fix 时，应建议转 Planning，而不是强行套 bugfix 流程。

### 4.7 `dev-harness-retro`

定位调整为：**Explicit Project Retrospective / 开发者显式触发的项目复盘**。

不要删除，但需要重点改造。

当前风险是把 AI 一次偶发错误自动固化成永久硬规则，随着模型升级会产生历史包袱和上下文膨胀。

要求：

1. **不得在每次任务完成后自动调用 Retro。** 只有用户明确说“retro / 复盘 / 总结并沉淀”等才执行。
2. Retro 结果至少分成三类：

   - `FACT`：可以被仓库、配置、测试或可靠证据证明的项目客观事实；
   - `POLICY`：开发者 / 团队明确决定的项目规范；
   - `LESSON`：本次任务得到的经验、AI 行为问题、暂时性注意事项。

3. 三类内容不能互相冒充：

   - 一次 AI 失误不是 FACT；
   - Git 历史惯例不是 POLICY，除非开发者确认；
   - LESSON 默认不是永久硬约束。

4. `LESSONS.md` 建议改为复盘历史 / 经验库，不再宣称其中每条都是必须自动加载的硬规则。
5. 不要让所有 Skill 每次启动都无条件读取完整 LESSONS 或 Top N 历史错误。真正稳定的 FACT / POLICY 应被“提升（promote）”到对应的 Canonical Contract：

   - 项目事实 → Context 管理的上下文；
   - 构建验证政策 → HARNESS / Commands；
   - Git 政策 → Git Workflow；
   - 文档政策 → Docs；
   - 规划政策 → Planning。

6. Promotion 应需要明确证据；POLICY 写入正式规范前需要用户确认。
7. Retro 可以输出 Promotion Candidates，但不要静默修改多个 Skill 的正式规范。

---

## 5. 新增 Skill：`dev-harness-codebase-audit`

### 5.1 命名

推荐：

```text
dev-harness-codebase-audit
```

目录：

```text
codebase-audit/
```

不建议简单叫 `dev-harness-audit`，原因：

- `dev-harness-docs` 已存在文档结构的 Audit 操作；
- “audit” 可能表示 security audit、docs audit、PR audit；
- `codebase-audit` 更准确表达“对整个存量代码库进行系统扫描”。

### 5.2 核心定位

Codebase Audit **不是教 AI 应该检查什么**。

它解决的是：

> **大型代码库无法在一次会话中完整载入上下文时，如何让 AI 可靠地分阶段扫描未知问题，并持久保存进度、证据、Finding 和跨模块结论。**

它与 Auto Fix 的边界：

```text
Known Problem
    ↓
auto-fix

Unknown Problems in a Codebase
    ↓
codebase-audit
```

### 5.3 不要在 Audit 中硬编码巨型 Checklist

禁止把下列内容做成几百条固定检查项：

- C++ 所有最佳实践；
- ArkTS 所有最佳实践；
- FastAPI 所有最佳实践；
- security 全量 checklist；
- performance 全量 checklist；
- frontend / database / API 全量 checklist。

Audit 应首先读取 Context，根据真实项目动态生成 Audit Domains。

例如 Context 识别出：

```text
Platforms: PC + Phone
Languages: ArkTS + C++
Boundaries: ArkUI -> ArkTS Adapter -> NAPI -> C++ SDK
Build: Hvigor + CMake
```

AI 应据此自行决定重点关注 PC/Phone 边界、UI 生命周期、状态、Native Bridge、线程、所有权和构建 Variant，而不是依赖 Skill 内预写 200 条 Harmony 规则。

### 5.4 V1 工作流

建议流程：

```text
preflight
  ↓
load / validate canonical context
  ↓
snapshot
  ↓
partition audit domains
  ↓
generate task docs
  ↓
progressive task execution
  ↓
verify / deduplicate findings
  ↓
cross-module reconciliation
  ↓
final report
```

#### Phase 0 — Preflight

读取：

- `AGENTS.md`
- `ARCHITECTURE.md`
- `HARNESS.md`
- Context 的最新证据 / fingerprint（按当前实现可用方式）
- 项目已有规范索引
- `<docs-root>`

如果 Context 缺失或明显过期：

- 不要自己生成另一套 Repository Context；
- 使用 / 建议运行 `dev-harness-context` 更新 Canonical Context；
- Context 是 Audit 的前置输入。

#### Phase 1 — Snapshot

建立 `AuditSnapshot`。

至少包含：

- base SHA；
- branch；
- preexisting dirty files + content fingerprint；
- Context fingerprint；
- audit scope；
- audit output paths。

状态写入 Git 私有目录，例如：

```text
.git/dev-harness/codebase-audit/<run-id>/state.json
```

不要把执行状态写进受版本控制的业务目录。

Audit 允许写入自己的审计文档，但禁止修改业务源码、测试、配置和构建文件。

如果审计期间源代码、HEAD、分支或 preexisting dirty 内容发生漂移，旧 Evidence 必须视为可能失效。V1 可以采用 fail-closed 策略：标记 `WorkspaceDrift` / `STALE` 并停止继续生成“已确认”结论。

#### Phase 2 — Dynamic Partition

基于 Context 动态生成审计任务，不按文件数量机械切片。

优先按：

- subsystem；
- module；
- runtime boundary；
- platform boundary；
- shared core；
- native / bridge boundary；
- data / persistence boundary；
- external integration；
- build / packaging boundary。

大型项目建议 4～10 个主要任务；小项目允许更少。不要为了固定数量强行拆分。

每个任务包含：

- Task ID；
- Scope；
- Why this scope exists（来自 Context 的哪些事实）；
- Entry Points；
- Important Boundaries；
- Exclusions；
- Evidence Strategy；
- Dependencies / Related Tasks；
- Status。

#### Phase 3 — Progressive Execution

禁止：

```text
为了“扫描完整”连续读取大量无关大文件
```

推荐：

```text
Repository Map / Context
    ↓
symbol / text search
    ↓
entry point
    ↓
caller / callee
    ↓
owner / lifecycle / boundary
    ↓
按需读取代码
    ↓
evidence
```

核心原则：

> **文件不是审计单位；调用链、数据流、所有权和模块边界才是审计单位。**

AI 自己决定具体检查内容。Skill 只约束扫描过程和证据质量。

#### Phase 4 — Finding Verification

发现可疑点时不要直接写成 Confirmed Finding。

建议状态：

```text
candidate
needs-verification
confirmed
rejected
stale
resolved
```

Confirmed Finding 至少包含：

- ID，例如 `AUD-001`；
- Severity：P0 / P1 / P2 / P3；
- Category：自由分类，不限制为固定技术栈；
- Summary；
- Evidence Paths / Lines；
- Relevant Call Chain / Data Flow；
- Claim；
- Counter-evidence checked；
- Risk / Impact；
- Confidence；
- Suggested Next Action；
- Snapshot / fingerprint。

要求：

- 没有代码或运行证据，不得标 confirmed；
- 先检查反例 / 旁路 / 生命周期 / 其他实现后再确认；
- 静态搜索不到引用不能直接等于 dead code；
- 不确定就 `needs-verification`；
- 同一根因在多个 Task 出现时去重，不生成多个重复 Finding。

#### Phase 5 — Cross-module Reconciliation

这是 Audit 的强制阶段，不可省略。

目标：

- 合并重复 Finding；
- 处理不同任务之间相互矛盾的结论；
- 找到单模块看不出来的跨层问题；
- 检查共享模块变化对多平台 / 多调用方的影响；
- 重新排序真正的 P0 / P1 风险。

典型跨层链路：

```text
UI lifecycle
  ↓
state / manager
  ↓
wrapper / adapter
  ↓
NAPI / FFI
  ↓
native object
  ↓
worker / SDK callback
```

单独扫描任一层可能都正常，问题可能只存在于完整生命周期组合中。

#### Phase 6 — Final Report

最终报告以已经验证的 Findings 为中心，不重新生成一份脱离 Evidence 的长篇“最佳实践建议”。

---

## 6. Codebase Audit 文档产物

复用项目现有 `<docs-root>`，禁止创建第二套 `doc/` / `docs/`。

建议：

```text
<docs-root>/audit/
├── Dashboard.md
├── Findings.md
├── Report.md
├── tasks/
│   ├── A01-*.md
│   ├── A02-*.md
│   └── ...
└── results/
    ├── A01-*.md
    ├── A02-*.md
    └── ...
```

### `Dashboard.md`

只负责当前审计状态：

- Audit Run / Snapshot；
- 任务列表；
- Task Status；
- Finding 计数；
- Current Focus；
- Blockers；
- Last Verified Snapshot。

不要塞详细问题正文。

### `Findings.md`

作为稳定 Finding Registry。

要求：

- Finding ID 稳定；
- 同一问题更新原 ID，不重复创建；
- 状态可变化；
- 每个 Finding 有 Snapshot / Evidence；
- Repo 演进后可重新验证或标 stale；
- Git 历史本身承担历史版本追踪，不需要 V1 创建大量时间戳归档文件。

### `tasks/`

Task 是“当前这一轮该扫描什么”的外部记忆。

Task 文档应短、聚焦，不复制整个 SKILL 和 Context。

### `results/`

保存每个 Task 的阶段结果和局部证据，避免下一个 Session 必须重新扫描同一范围。

### `Report.md`

面向开发者的当前总体结果：

- Executive Summary；
- Architecture / scope summary；
- Confirmed P0/P1/P2/P3；
- Cross-module findings；
- Needs Verification；
- Recommended next actions。

---

## 7. Audit 与其他 Skill 的 Handoff

Codebase Audit 只发现和验证问题，不自动修改业务代码。

Finding 的后续处理建议：

```text
Confirmed defect / crash / lifecycle bug
    → dev-harness-auto-fix

Architecture / refactor / technical-debt work
    → dev-harness-planning

Documentation governance problem
    → dev-harness-docs

Git / release policy gap
    → dev-harness-git-workflow

Verification command gap
    → dev-harness-commands
```

这些是建议路由，不要在 Audit 内自动执行写操作。

---

## 8. 跨 Skill 所有权矩阵

实施时请检查当前仓库是否存在职责重叠或冲突，并按下表明确归属。

| 资源 / 事实 | Owner | 其他 Skill 行为 |
|---|---|---|
| Repository evidence / canonical context | Context | 只读使用 |
| README / ARCHITECTURE / AGENTS managed sections | Context | 不直接覆盖 |
| HARNESS 自动候选 | Context | Commands 可读取 |
| HARNESS 人工确认命令 | Commands | Auto-fix / 普通 Agent 使用 |
| docs root / index / SSOT / archive | Docs | Planning/Audit 复用 |
| `<docs-root>/plan/*` | Planning | Docs 只做导航治理 |
| Git / tag / release / changelog policy | Git Workflow | 其他 Skill 只读使用 |
| `.git/dev-harness/auto-fix/*` | Auto Fix | 私有状态 |
| `<docs-root>/audit/*` | Codebase Audit | Docs 只做导航/归档 |
| `.git/dev-harness/codebase-audit/*` | Codebase Audit | 私有状态 |
| LESSONS / retro candidates | Retro | 不自动升级为硬规则 |

不要创建一个新的中心配置文件复制以上所有内容。

---

## 9. 减少 Skill 上下文占用

当前多个 SKILL 包含较长平台说明和示例。优化时不要为了“文件短”删除有价值能力，但应使用 Progressive Disclosure：

```text
SKILL.md
  ├── 定位
  ├── 触发条件
  ├── 核心流程
  ├── 边界
  ├── 停止条件
  └── 按需 references
```

适合下沉到 references 的内容：

- Windows shell / 编码细节；
- Harmony / Qt / WPF / FastAPI 等平台增强说明；
- 默认 Git 约定长表；
- Finding 示例；
- Audit partitioning 指导；
- cross-module review 指导；
- 模板格式说明。

目标不是追求最短 SKILL，而是：

> **Agent 在不需要某个细节时，不应因此长期占用固定的上下文空间。**

---

## 10. 建议的 Codebase Audit Skill 目录

V1 推荐最小结构：

```text
codebase-audit/
├── SKILL.md
├── runtime.py
├── references/
│   ├── workflow.md
│   ├── partitioning.md
│   ├── finding-contract.md
│   └── cross-module-review.md
└── templates/
    ├── Dashboard.template.md
    ├── Findings.template.md
    ├── AuditTask.template.md
    ├── AuditResult.template.md
    └── Report.template.md
```

如果现有 repo 有更统一的 Python contract/runtime 组织方式，可以复用；不要为了这个目录图重复创建公共逻辑。

### V1 `runtime.py` 只负责确定性操作

建议仅负责：

- init run；
- AuditSnapshot；
- workspace drift 校验；
- task state checkpoint；
- finding ID / state 基础校验；
- output path 范围校验；
- resume/status。

**不要让 runtime.py 自己扫描代码、做 AST 审计、判断架构或自动生成 Finding。**

AI Agent 负责语义理解；Runtime 负责“不允许 AI 靠文字绕过的状态和边界”。

---

## 11. Audit V1 暂不实现

为防止范围膨胀，V1 明确不做：

- AST / Compiler 级静态分析引擎；
- 自建代码索引数据库；
- 向量数据库；
- 全语言规则库；
- security scanner；
- dependency vulnerability scanner；
- 自动性能 benchmark 平台；
- 自动修复；
- 自动 PR；
- 自动创建 Roadmap task；
- 多 Agent 调度框架；
- Web Dashboard；
- 后台 daemon；
- 云端状态同步。

Agent 自己已经有搜索、阅读、推理能力。V1 只解决长任务可靠性。

---

## 12. README / 项目定位调整

当前 README 的入口仍明显以“修 bug”作为主要叙事。Auto Fix 可以继续作为最成熟示例，但建议把顶层定位扩展为：

> dev-harness 是给 AI 编码助手的项目工程约束层：统一项目上下文、文档、规划、验证命令和 Git 流程，并为 Bug 修复与大型代码库审计提供可持久化、可验证的工作流。

建议 README 明确两类 Skill：

### Project Contract / Governance

- context
- commands
- git-workflow
- planning
- docs
- retro

### Evidence-driven Long-running Workflows

- auto-fix
- codebase-audit

这只是文档分类，不要求改变安装方式。

同时在设计边界加入：

> dev-harness 不以覆盖完整 SDLC 能力为目标；模型能够可靠自行完成的通用编程能力不重复做 Skill。

---

## 13. Installer / Export / Discovery 更新

新增 `dev-harness-codebase-audit` 后，必须检查所有 Skill 注册和打包入口，而不是只增加一个目录。

至少检查：

- `install.py`
- `install.sh`
- `install.bat`
- export / dist 逻辑
- `--skill` 单 Skill 安装
- README Skill 列表与数量
- release scripts
- tests 中的 Skill allowlist / expected bundle

不要假设具体实现文件，一切以当前 repo 为准。

---

## 14. 测试要求

本次优化不能只有 Markdown Skill 文本变更。

### 14.1 保持现有回归

先运行当前项目已有 tests，记录 baseline；改造后必须继续通过。

### 14.2 Codebase Audit Runtime

至少覆盖：

1. 初始化 Audit Run；
2. Snapshot 正确记录 HEAD / branch / dirty files；
3. Audit 自己的 docs 输出不被误判为业务源代码漂移；
4. 业务源码发生变化后 drift 检测失败；
5. task checkpoint 可恢复；
6. context fingerprint 改变后旧 run 被标记需要重新验证；
7. 输出路径无法逃逸 repo/docs root；
8. Finding 状态值非法时拒绝；
9. resume 不依赖聊天上下文；
10. Audit 模式不能修改业务源代码。

### 14.3 Skill Packaging

至少验证：

- 全量安装包含新 Skill；
- `--skill dev-harness-codebase-audit` 可单独安装；
- references/templates/runtime 跟随安装；
- export 包内容完整。

### 14.4 Retro

验证：

- description 明确仅显式触发；
- FACT / POLICY / LESSON 三类输出契约存在；
- LESSON 不会自动变成正式 Policy；
- 不再要求所有 Skill 无条件注入大量 LESSONS 历史。

---

## 15. 推荐实施阶段

不要一次大重构全部目录。

### Stage 1 — Baseline / Contract Review

- 阅读所有现有 Skill / templates / runtime / tests；
- 跑 baseline tests；
- 输出当前 ownership map；
- 找出职责重复和 LESSONS 自动注入位置。

### Stage 2 — Positioning & Cross-skill Contracts

- 更新 README 定位；
- 明确 Project Contract 是逻辑概念；
- 明确 Skill ownership / handoff；
- 不改变现有正确行为。

### Stage 3 — Retro 收敛

- 改为 explicit retrospective；
- 引入 FACT / POLICY / LESSON；
- 降低 LESSONS 自动硬约束和固定上下文成本；
- 保留历史兼容策略，避免粗暴删除现有用户数据。

### Stage 4 — Existing Skill Context Reduction

- 将大段平台 / shell / 默认示例渐进下沉 references；
- 保持 SKILL 行为契约不变；
- 优先处理 context / commands / git-workflow 中明显的固定上下文大块。

### Stage 5 — Codebase Audit V1

- 新建 Skill；
- 实现 runtime state；
- 实现模板；
- 实现 Context 前置和动态 partition；
- 实现 Findings Registry；
- 实现 cross-module reconciliation；
- 不实现自动修复。

### Stage 6 — Handoff

- auto-fix 支持读取 `AUD-*` Finding；
- planning/docs/commands/git-workflow 加入最小的 Audit handoff 说明；
- 不建立复杂自动 orchestration。

### Stage 7 — Tests / Installer / Docs

- 完成 runtime tests；
- install/export tests；
- README usage examples；
- CHANGELOG / VERSION 是否调整按项目现有 release policy 处理，不自行发布。

---

## 16. 验收标准

完成后必须满足：

### 项目定位

- README 不再暗示 dev-harness 只等于 bugfix；
- 同时明确不做“大而全 AI Skills Library”；
- Consistency / Evidence / Continuity 的方向清晰。

### 现有 Skill

- Context、Commands、Git Workflow、Planning、Docs 继续发挥统一规范的作用；
- Auto Fix 的严格证据链不弱化；
- Retro 变成开发者显式触发，不把单次 AI 失误自动固化成永久事实。

### Codebase Audit

- 能基于现有 Context 动态产生审计分区；
- 不依赖固定语言 Checklist 才能工作；
- 能在多个 Session 间恢复；
- 每个 Confirmed Finding 有证据和 Snapshot；
- 源代码漂移后不会继续把旧证据声明为当前事实；
- 有强制 Cross-module Review；
- 只允许修改审计文档和 Git 私有状态；
- 不自动修业务代码。

### Packaging

- 保持对 Codex / Cursor / OpenCode / Antigravity 现有安装方式的兼容；
- 新 Skill 可以全量和单独安装；
- 现有 tests + 新增 tests 全部通过。

---

## 17. 实施时的强约束

Codex 在执行本方案时必须遵守：

1. **先读当前实现，再改。** 不要根据本文假设 repo 结构。
2. **不要为了架构“更漂亮”重写已经工作的 runtime。**
3. **不要删除现有正确能力。** 本方案主要是职责收敛和新增 Audit。
4. **不要顺便格式化整个仓库。**
5. **不要自动升级依赖。**
6. **不要改变现有安装路径 / Skill 名称，除新增 `dev-harness-codebase-audit` 外。**
7. **不要把 audit 做成静态分析器。**
8. **不要把 Profile 做成技术栈白名单。**
9. **不要创建第二个 docs 根目录。**
10. **不要自动 commit / tag / push / release。**
11. 遇到本文与现有可靠实现冲突时，优先保持兼容，记录设计偏差。
12. 每个 Stage 完成后运行适用测试，不要等全部改完才一次性验证。

---

## 18. 可以直接给 Codex 的执行指令

将本文放到 dev-harness 仓库后，可直接给 Codex：

```text
阅读这份设计文档以及当前 dev-harness 仓库全部相关实现：

<本文路径>

目标是在不把项目做成大而全 AI Skill Library 的前提下，优化现有 Skill 的职责、跨 Skill 契约和上下文成本，并新增 dev-harness-codebase-audit。

要求：

1. 先扫描当前 README、所有 SKILL.md、templates/references、runtime、install/export/release 和 tests。
2. 先给出“当前实现 vs 设计文档”的 Gap Analysis 和准备修改的文件范围。
3. 然后按文档 Stage 顺序直接实施，不需要等待我逐阶段确认；遇到高风险或本文与现有实现冲突时选择最小兼容方案，并记录原因。
4. 不做无关重构，不升级依赖，不格式化整个仓库，不 commit/push/release。
5. 每阶段运行适用测试；完成后运行完整测试。
6. 最终报告：
   - 实际修改内容
   - 新增 Codebase Audit 架构
   - Retro 行为变化
   - 跨 Skill ownership / handoff
   - 新增/修改测试
   - 与本文有差异的地方及原因
   - 尚未实现、建议以后再做的事项
```

---

## 19. 最终设计判断

本次演进后，`dev-harness` 不应该通过 Skill 数量体现价值。

更合理的判断标准是：

```text
AI 本身负责：
理解、设计、编码、Review、推理、选择具体技术检查点

Dev Harness 负责：
统一格式
统一项目规范
证据绑定
工作区边界
授权边界
持久状态
长任务连续性
跨 Agent 一致性
```

因此，新增 Codebase Audit 的价值不在于“比模型更懂 C++ / Harmony / FastAPI”，而在于让模型面对大型、历史悠久、跨模块的代码库时，仍能可靠地：

```text
Context
  ↓
Partition
  ↓
Progressive Scan
  ↓
Persistent Evidence
  ↓
Confirmed Findings
  ↓
Cross-module Reconciliation
  ↓
Handoff
```

这应当成为 dev-harness 在大型存量项目方向上的核心能力之一，同时保持整个项目克制、可组合、不与通用 AI 能力重复。
