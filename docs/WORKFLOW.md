# dev-harness 端到端工作流

> 本文说明现有八个 Skills 如何组合完成新功能交付或代码库审计；各 Skill 的精确行为、授权和状态仍以对应 `SKILL.md` 与 runtime 为准。
>
> 当前已支持功能以 [产品功能清单](CAPABILITIES.md) 为权威文档，版本边界与非目标见 [V1 / VNext 与 V2 边界](V1_V2_BOUNDARIES.md)。跨 Skill 自动编排属于独立的 [`dev-harness-dsh`](https://github.com/Dev-Wiki/dev-harness-dsh) 项目，不在本文维护其需求或任务状态。

## 1. 共同原则

1. 外层流程只负责阶段顺序和 handoff，不复制 Skill 内部状态机。
2. 需求、任务状态、当前功能、Finding、验证证据和提交边界分别由其 SSOT 维护。
3. “代码写完”不等于任务完成；只有验收与验证通过后才能标记 `✅ 已完成`。
4. commit、push、PR、tag、release 和 deploy 是彼此独立的授权。
5. QA 是可选工作流阶段；无法执行的部分必须明确列为人工验证项，不能写成已通过。

## 2. 选择入口

先准备 Project Contract，再根据输入选择工作流：

```text
                         Project Contract
                                 │
                  ┌──────────────┴──────────────┐
                  ▼                             ▼
           已知需求 / 新功能              未知问题 / 存量治理
                  │                             │
                  ▼                             ▼
              Planning                   Codebase Audit
                  │                             │
                  ▼                             ▼
        开发 → 测试 → 验收 → 提交       Findings → 分类处理 → 复核
```

- 有明确需求、原型或验收目标时，进入[新功能交付](#4-新功能交付工作流)。
- 需要系统发现未知工程问题时，进入[代码库审计与修复](#5-代码库审计与修复工作流)。
- 已知且边界明确的 Bug 可以直接使用 `dev-harness-auto-fix`，不必先运行 Audit。

## 3. 共享前置：准备 Project Contract

第一次接入项目时按需使用：

- [`dev-harness-context`](../context/SKILL.md)：初始化或刷新项目上下文；
- [`dev-harness-docs`](../dev-harness-docs/SKILL.md)：确认文档根、导航和 SSOT；Planning 自己维护 `plan/` 内的任务归档内容；
- [`dev-harness-commands`](../commands/SKILL.md)：把真实命令映射为稳定语义入口；
- [`dev-harness-git-workflow`](../git-workflow/SKILL.md)：识别项目 Git、提交和发布规范。

开始写入前至少应确认：

- 项目目标、修改范围、高风险区域和禁止事项；
- 需求来源与可直接验证的验收标准；
- `build / test / quick / bugfix / full` 的已确认命令；
- 文档、当前功能、活动计划、Git 规范和发布变化的权威维护位置；
- 当前分支、HEAD、工作区和暂存区状态。

缺少真实命令或证据时保持 `Unknown`、`Missing` 或阻塞，不得根据技术栈经验编造入口。

## 4. 新功能交付工作流

### 4.1 总览

```text
需求与验收标准
→ 看板拆分（Dashboard + 单任务文件）
→ 选择一个无阻塞任务并标记 🚧 开发中
→ 开发
→ 定向测试 + 任务验收
→ 必要的 harness:full / QA
→ 更新事实文档 + 标记 ✅ 已完成
→ 精确提交
→ 下一任务或里程碑收口
```

普通开发 Agent 负责实现功能；dev-harness 不额外提供一个替代通用编码能力的“功能开发 Skill”。Planning 管理工作边界，Commands 提供验证入口，Docs 管理已验证事实，Git Workflow 管理提交边界。

### 4.2 明确需求与验收标准

开始拆分前确认需求来源、目标用户、首版边界、非目标、依赖和可执行的验收标准。协议、SDK、凭据、设备、合规要求等未知项应登记为阻塞或前置调研，不能靠推断补齐。

需求文档维护“要交付什么”；它不维护开发中的任务状态，也不证明功能已经支持。

### 4.3 拆分看板与任务详情

使用 [`dev-harness-planning`](../planning/SKILL.md) 在项目已有文档根目录维护：

- `<docs-root>/plan/Dashboard.md`：唯一活跃计划入口，保存当前里程碑、工作顺序、任务 ID、优先级、状态、依赖、阻塞、共享验证基线、覆盖范围和详情链接；
- `<docs-root>/plan/tasks/<Task-ID>.md`：执行层，每个活跃任务独立保存背景、目标、影响文件、步骤、验收、风险和验证证据；
- `<docs-root>/plan/archive/<milestone>/`：完成任务的最终摘要与证据入口，不进入普通开发的默认读取范围。

既有 `TaskDetails.md` 完成迁移后只可作为指向 Dashboard 的兼容跳转，不能继续保存任务行或可变状态。

拆分规则：

1. 先列前置调研和阻塞，再拆 P0 核心、P1 支撑和 P2 远期任务。
2. Dashboard 中的每个活跃任务必须链接到唯一的 `tasks/<Task-ID>.md`。
3. 每项任务应能独立实现、验证和提交；跨任务依赖必须显式记录。
4. 使用稳定状态：`📋 规划中`、`🚧 开发中`、`✅ 已完成`、`📋 远期`。
5. 未经实现和验证证据，不得从计划或聊天推断任务已经完成。

### 4.4 领取并开发一个任务

按依赖和优先级选择一个无阻塞任务，只在 Dashboard 将状态改为 `🚧 开发中`，然后加载对应任务文件及其必要上下文；任务文件不复制状态、优先级、依赖、执行顺序或阻塞，不读取全部已完成任务正文。领取或恢复任务前记录临时规划快照，后续若 Dashboard、任务路径或 `HEAD` 出现本次工作之外的变化，先重新读取并核对，不能沿用旧选择。

开发过程遵循项目 `AGENTS.md`、架构约束和现有代码风格。实现中发现需求缺口时先回到需求或当前任务文件澄清；不要把新增范围静默塞进当前任务。已知缺陷可交给 Auto Fix，较大的架构调整应回到 Planning 重新拆分。

### 4.5 测试与验收

验证范围由任务风险和项目 `HARNESS.md` 决定，推荐顺序为：

```text
harness:quick / 相关 build
→ 定向 harness:test 或任务专属测试
→ 当前任务文件的验收标准
→ 必要时 harness:full
→ 可执行时 QA / Dogfood
```

- `quick` 负责快速反馈，不能替代任务验收。
- 定向测试应覆盖本次功能的正常、异常和关键边界路径。
- `full` 用于高风险任务、共享基础设施变更、提交/合并门禁或里程碑收口；不得用任意局部命令冒充。
- 环境无法执行的设备或 UI 验收必须列为剩余人工项。

任何失败都回到当前任务修复并重新验证；失败证据不能用旧的成功结果覆盖。

### 4.6 同步事实、状态并提交

验证通过后按以下顺序收口：

1. 检查当前 diff、任务验收结果和 fresh validation evidence。
2. 使用 Docs 将代码或成功验证已经证明、且未来会重复使用的事实同步到现有权威文档；计划内容不得直接写入当前功能清单。
3. 在任务文件记录最终验证入口或结果引用，把任务文件迁入 `archive/<milestone>/`，同时从 Dashboard 活跃区移除并写入有界的最近完成摘要。
4. 使用 Git Workflow 精确暂存当前任务文件，检查敏感内容、调试残留和无关变更后提交。
5. push、PR、tag、release 和 deploy 仅在分别获得授权后执行。

推荐一个可独立验证的任务对应一个提交。提交失败不改变验证事实，但必须报告未提交状态，不能继续声称交付闭环已经完成。

### 4.7 下一任务与里程碑收口

提交后重新读取 Dashboard，选择下一个无阻塞任务并重复开发闭环。一个里程碑的计划内任务全部完成后，再执行 fresh `harness:full` 和可用的 QA，汇总并收口里程碑归档：

- 已完成、剩余和阻塞任务；
- 验收与完整验证证据；
- 实际提交 SHA，以及另行授权后产生的 push / PR 结果；
- 已更新的当前功能或其他权威文档；
- 剩余风险和人工验证项。

## 5. 代码库审计与修复工作流

### 5.1 Audit 与 Finding 路由

[`dev-harness-codebase-audit`](../codebase-audit/SKILL.md) 面向用户拥有或明确授权的代码库：

```text
动态分区 → 分阶段扫描 → Candidate → Verification
→ Confirmed / Rejected → Cross-module Reconciliation → Report
```

Audit 发现、验证和路由问题，但不修改业务源码、测试或配置。只有权威 Finding Registry 中的 confirmed Finding 才进入后续处理。

| Finding 类型 | 后续 Owner |
|---|---|
| defect / crash / lifecycle bug | `dev-harness-auto-fix` |
| architecture / refactor / tech debt | `dev-harness-planning`，经用户接受后进入 Roadmap |
| docs drift | `dev-harness-docs` |
| verification gap | `dev-harness-commands` |
| Git / release / changelog gap | `dev-harness-git-workflow` |

### 5.2 逐项处理 Defect

confirmed defect 交给 [`dev-harness-auto-fix`](../auto-fix/SKILL.md)：

```text
preflight → context → reproduce → hypothesize → RED
→ minimal fix → GREEN → review → final verify → optional commit
```

推荐每个 confirmed defect 使用独立 Auto Fix Run，以便单独验证、审查、回滚和保存证据。Auto Fix 已提交的修改不得由外层流程重复提交；`fix` 模式结束后则需要另行授权 Git Workflow 提交。

`BLOCKED` 或 `NEEDS_CONTEXT` 必须停止处理，不能静默跳过。Docs、Commands、Planning 和 Git Workflow handoff 由各自 Owner 维护，详细状态不复制回 Audit 报告。

### 5.3 整体验证、QA 与最终复核

所有计划内代码修改完成后执行已确认的 `harness:full`。单个 Auto Fix 的 GREEN 只证明目标问题得到修复，fresh `full` 才证明多个修改组合后仍满足项目完整验证要求。

完整验证后可按环境执行 QA / Dogfood。QA 发现的新问题默认作为已知 Bug 进入 Auto Fix；只有需要长期登记和跨模块复核时，才由 Codebase Audit 创建正式 Finding，其他流程不得伪造 `AUD-*` ID。

代码变化会使原 Audit Snapshot 的部分证据失效。长期治理流程应在最终工作区创建 fresh Audit Snapshot，并由 Codebase Audit 将原 Findings 复核为 `resolved / remaining / stale`。Finding 状态只能由 Codebase Audit 更新。

最终报告至少包含：原 Audit Run、Finding 处理结果、Auto Fix 状态、实际提交 SHA、fresh `harness:full`、QA 与人工项、最终复核结果和剩余阻塞。

## 6. 手工编排边界

完全使用 Skills 时，用户或 Agent 仍需维护当前路径、任务或 Finding、下游 Run 引用、失败重试、授权和最终汇总。独立的 [`dev-harness-dsh`](https://github.com/Dev-Wiki/dev-harness-dsh) 项目规划自动化这些外层编排；`dev-harness` 继续保持跨 Agent 的纯 Skills Bundle。
