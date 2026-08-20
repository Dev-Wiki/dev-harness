# dev-harness 端到端工作流

> 文档职责：说明现有八个 Skills 如何组合成一条完整工程工作流；各 Skill 的精确行为、授权和状态仍以对应 `SKILL.md` 与 runtime 为准。
>
> 当前已支持功能以 [产品功能清单](CAPABILITIES.md) 为权威文档，版本边界与非目标见 [V1 / VNext 与 V2 边界](V1_V2_BOUNDARIES.md)。跨 Skill 自动编排属于独立的 [`dev-harness-dsh`](https://github.com/Dev-Wiki/dev-harness-dsh) 项目，不在本文维护其需求或任务状态。

## 1. 目标与原则

不安装额外编排 Plugin 时，现有 Skills 也可以按以下顺序协作：

```text
准备 Project Contract
→ Codebase Audit
→ Finding 路由
→ 逐项 Auto Fix
→ 可选精确提交
→ harness:full
→ QA / Dogfood
→ QA Failure Loop
→ Final Audit Reconciliation
→ 最终报告
```

组合工作流遵守四条原则：

1. 外层流程只负责顺序和 handoff，不复制 Skill 内部状态机。
2. Finding、验证证据、提交边界和任务状态由各自 SSOT 维护。
3. commit、push、PR、tag、release 和 deploy 是彼此独立的授权。
4. QA 是可选工作流阶段，不是 dev-harness Core Skill；无法执行的部分必须明确交给人工验证。

## 2. 工作流总览

```text
Context / Docs / Commands / Git Policy
                    │
                    ▼
              Codebase Audit
                    │
                    ▼
             Confirmed Findings
                    │
                    ▼
               Finding Router
        ┌───────────┼───────────┬──────────────┐
        ▼           ▼           ▼              ▼
     Defect     Tech debt    Docs gap    Verification gap
        │           │           │              │
        ▼           ▼           ▼              ▼
    Auto Fix     Planning      Docs          Commands
        │
        ▼
 Reproduce → Hypothesis → RED → Minimal Fix → GREEN
        │
        ▼
 Review → Final Verify → Optional Commit
        │
        ▼
   Next Finding → harness:full → QA / Dogfood
                                      │
                              ┌───────┴───────┐
                              ▼               ▼
                         QA Failure          PASS
                              │               │
                              ▼               ▼
                          Auto Fix     Final Reconciliation
```

## 3. Step 1：准备 Project Contract

第一次接入项目时，按需使用：

- [`dev-harness-context`](../context/SKILL.md)：初始化或刷新项目上下文；
- [`dev-harness-docs`](../dev-harness-docs/SKILL.md)：确认文档根、导航和 SSOT；
- [`dev-harness-commands`](../commands/SKILL.md)：把真实命令映射为稳定语义入口；
- [`dev-harness-git-workflow`](../git-workflow/SKILL.md)：识别项目 Git、提交和发布规范。

项目至少应能可靠回答：

- 项目是什么、从哪里开始阅读；
- 哪些区域高风险或禁止直接修改；
- `build / test / quick / bugfix / full` 分别执行什么；
- 文档、当前功能、计划、Git 规范和发布变化由谁维护。

缺少真实命令或证据时保持 `Unknown`，不得根据技术栈经验编造入口。

## 4. Step 2：执行 Codebase Audit

[`dev-harness-codebase-audit`](../codebase-audit/SKILL.md) 面向用户拥有或明确授权的代码库，负责：

```text
动态分区
→ 分阶段扫描
→ Candidate
→ Verification
→ Confirmed / Rejected
→ Cross-module Reconciliation
→ Report
```

Audit 发现、验证和路由问题，但不修改业务源码、测试或配置。只有权威 Finding Registry 中的 confirmed Finding 才能进入后续处理。

| Finding 类型 | 后续 Owner |
|---|---|
| defect / crash / lifecycle bug | `dev-harness-auto-fix` |
| architecture / refactor / tech debt | `dev-harness-planning` |
| docs drift | `dev-harness-docs` |
| verification gap | `dev-harness-commands` |
| Git / release / changelog gap | `dev-harness-git-workflow` |

## 5. Step 3：逐项处理 Defect

confirmed defect 交给 [`dev-harness-auto-fix`](../auto-fix/SKILL.md)。写模式完整路径为：

```text
preflight
→ context
→ reproduce
→ hypothesize
→ regress-red
→ implement
→ verify / GREEN
→ review
→ final-verify
→ optional commit
→ report
```

RED、GREEN、ReviewDiffHash 和最终验证均由 Auto Fix 维护。外层工作流不得重新实现另一套红绿灯或根据聊天文本判断修复完成。

推荐每个 confirmed defect 使用一个独立 Auto Fix Run，以便单独验证、Review、回滚和保留清晰证据。架构重构和较大技术债不强行进入 Bugfix 写流程，应转 Planning。

## 6. Step 4：选择提交方式

### 方式 A：Auto Fix `commit` / `unattended`

用户已经明确授权提交时，由 Auto Fix 在最终验证后加载 Git Workflow，只精确提交本轮 `AutoFixChangedFiles`。

### 方式 B：Auto Fix `fix` 后单独提交

用户只授权修复时，Auto Fix 在工作区修复和验证后结束，不得提交。用户随后可以单独授权 Git Workflow 检查当前修改并提交。

两种方式不能叠加。Auto Fix 已产生提交后，外层流程不得再次为同一修改创建第二个提交。

无论采用哪种方式，以下动作都不随 commit 自动授权：

- push；
- 创建 PR；
- tag；
- release；
- deploy；
- Issue 回写。

## 7. Step 5：处理全部计划内 Finding

推荐顺序执行需要写代码的 Finding：

```text
AUD-001 → Auto Fix Run 001 → 可选 commit A
AUD-002 → Auto Fix Run 002 → 可选 commit B
AUD-003 → Auto Fix Run 003 → 可选 commit C
```

只有下游 Skill 报告允许继续的完成状态时，外层流程才能推进；`BLOCKED` 或 `NEEDS_CONTEXT` 必须停止并请求处理，不能静默跳过。

Docs、Commands、Planning 或 Git Workflow handoff 分别交给对应 Owner，不把详细状态复制回 Audit 报告或临时总表。

## 8. Step 6：整体 Full Verification

所有计划内代码修改完成后，执行项目 `HARNESS.md` 中已确认的：

```text
harness:full
```

单个 Auto Fix 的 GREEN 证明目标问题在当前变更下被修复；最终 `harness:full` 证明多个修改组合后仍满足项目完整验证要求。

外层流程不得重新猜测项目命令，也不得把任意局部命令成功冒充 `harness:full`。

## 9. Step 7：QA / Dogfood

完整验证通过后，可根据项目类型和当前环境执行真实使用场景：

- Web：浏览器、网络请求、Console、正常/异常/边界路径；
- CLI / Backend：真实命令或 API、错误输入、状态变化、重启和持久化；
- Android / Desktop / Device：当前环境已具备的设备、模拟器、ADB、UI 自动化或人工检查。

可以组合用户显式指定或当前环境已验证可用的外部 QA 能力，但 dev-harness Core 不依赖具体第三方工具。

环境无法完成真实 UI QA 时，应执行仍可自动验证的部分并列出剩余人工检查项；不得把“无法执行”描述为“QA PASS”。

## 10. Step 8：QA Failure Loop

QA 发现的新问题默认作为当前开发流程的 Bug Input：

```text
QA Finding
→ Auto Fix
→ RED
→ Minimal Fix
→ GREEN
→ Review / Final Verify
→ 可选 Commit
→ harness:full
→ QA Retry
```

只有需要长期登记和跨模块复核时，才重新交给 Codebase Audit 创建正式 Finding。普通 Agent 或外层流程不得自行伪造 `AUD-*` ID。

## 11. Step 9：Final Audit Reconciliation

代码、完整验证和 QA 完成后，原 Audit Snapshot 可能已因 HEAD、源码或 Context 变化而失效。长期治理流程应在最终工作区上创建 fresh Audit Snapshot，并由 Codebase Audit 复核原始 Findings：

```text
Fresh Audit Snapshot
→ Reverify original Findings
→ resolved / remaining / stale
```

Finding 状态始终由 Codebase Audit 更新。外层流程只能读取和汇总，不能直接修改 Registry。

## 12. 最终报告

最终报告至少列出：

- 原 Audit Run 和 Finding 处理结果；
- 每个 Auto Fix Run 的 CompletionStatus 与剩余风险；
- 是否实际产生提交及对应 SHA；
- `harness:full` 的 fresh evidence；
- QA 已执行场景、失败重试和剩余人工项；
- Final Reconciliation 的 resolved / remaining 结果；
- Overall 状态和阻塞。

报告应链接或引用权威证据，不复制下游完整正文。

## 13. 手工编排边界

完全使用 Skills 时，用户或 Agent 仍需维护：

- 当前阶段；
- 当前 Finding；
- 下游 Run 引用；
- 失败重试与恢复顺序；
- 运行级授权；
- 最终汇总。

这些外层编排问题由独立的 [`dev-harness-dsh`](https://github.com/Dev-Wiki/dev-harness-dsh) 项目规划解决；`dev-harness` 继续保持跨 Agent 的纯 Skill Bundle。
