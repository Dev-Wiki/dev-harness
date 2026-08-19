# Codebase Audit Workflow

本文件定义长任务的阶段、checkpoint 和 fail-closed 门禁。语义判断由 AI 完成；快照、状态和路径边界由 `runtime.py` 执行。

## 运行不变量

- Context 是前置 canonical input，不是本阶段的输出。
- 受版本控制的写入集合恒为 `<docs-root>/audit/**`。
- 私有执行状态恒位于 Git 返回的 `.git/dev-harness/codebase-audit/<run-id>/` 实际路径。
- 任一旧 Evidence 只有在 Snapshot 仍有效时才能支撑当前结论。
- 任何 Task 的局部结论都必须进入全局 reconciliation。
- 固定开发者入口为 `<docs-root>/audit/Report.md`；Audit 只读检查外部导航，Docs 负责维护文档中心链接。
- 本轮 `output_language` 由用户显式要求或默认值 `zh-CN` 决定，记录在 Dashboard 并在跨会话恢复时保持一致；它不属于 Evidence Snapshot。

## Phase 0 — Preflight / Resume

1. 读取仓库级 `AGENTS.md`、`README.md`、`ARCHITECTURE.md`、`HARNESS.md`、`LESSONS.md` 和规范索引（存在时）。
2. 解析唯一 `<docs-root>`；禁止为 Audit 创建第二个文档根。
3. 确定 `output_language`：只有显式全英文请求使用 `en`，否则使用 `zh-CN`。恢复时读取 Dashboard 已记录值；不得根据仓库主要语言自行切换。
4. 只读检查 `<docs-root>/README.md` 或一个既有 route index 是否链接 `audit/Report.md`。把结果记录为 `linked` 或 `docs-refresh-required`；这不是代码 Finding，不分配 `AUD-*`。
5. 若同一用户授权同时包含 Docs Refresh，在所有只读 preflight 检查通过后、Audit Snapshot 建立前，由 `dev-harness-docs` 幂等添加固定入口。若只授权 Audit，不修改 hub，继续运行并持久化精确 handoff。
6. 读取 `runtime.py --help` 并按实际接口使用语义操作：`init` 建立运行，`resume` / `status` 恢复或查看状态，`verify-workspace` 校验快照，`checkpoint` 持久化阶段，`upsert-finding` 维护 Finding，`validate-output` 校验输出边界与契约。不要硬编码未确认参数，也不要手工编辑 `state.json`。
7. 新运行按 `output_language` 创建模板产物并把选择写入 Dashboard；恢复运行先读取 state、Dashboard、Task 和 Result，再校验工作区与文档语言一致性。
8. 用 `validate-output` 检查输出路径：拒绝绝对越界、`..` 路径外移、符号链接指向审计根外部、文档中心和任何业务文件目标。

若 Context 缺失、明显过期、被截断或无法绑定 fingerprint，返回 `ContextRequired`，建议运行 `dev-harness-context` 后重新开始。不要边审计边发明新的仓库模型。

## Phase 1 — Snapshot

建立并持久化 `AuditSnapshot`：

| 字段 | 含义 |
|---|---|
| Run ID | 本轮稳定标识 |
| Base SHA / Branch | 代码基线 |
| Preexisting dirty fingerprint | 开始前用户修改的路径、内容与暂存状态 |
| Context fingerprint | 本轮实际使用的 canonical Context 内容指纹 |
| Scope | include、exclude 和用户限制 |
| Output paths | 已校验的 audit 文档路径 |

把 Snapshot 摘要写入 Dashboard、Task、Result、Findings 和 Report；完整执行状态只写 Git 私有目录。后续门禁通过 `verify-workspace` 判断 Snapshot 是否仍有效。

## Phase 2 — Dynamic Partition

读取 [partitioning.md](partitioning.md)，从 Context 事实生成 Task。任务围绕 subsystem、调用链、数据流、所有权或边界，而不是“每 N 个文件”或固定技术栈规则。

1. 创建或刷新 `Dashboard.md` 的 Task 索引。
2. 从 `AuditTask.template.md` 创建 `tasks/Axx-*.md`。
3. 记录每个 Task 的 Context 来源、入口、边界、排除项、证据策略、依赖和状态。面向读者的名称和问题按 `output_language` 表达，不直接复制 Context 中缺少行为说明的风险标签。
4. checkpoint partition plan；恢复后复用未漂移的 Task，不为凑数量重新切片。

## Phase 3 — Progressive Task Execution

每个 Task 使用以下漏斗：

```text
Context / repository map
  → symbol and text search
  → entry point
  → caller / callee
  → owner / lifecycle / boundary
  → focused code or local behavior evidence
```

执行规则：

1. 开始 Task 前校验 drift，并把 Dashboard 的 Current Focus 指向该 Task。
2. 沿行为链读取最少必要文件，记录实际覆盖和未覆盖范围。
3. 每个可疑现象独立保留为 task-local candidate；不要因为命名、风格、一次搜索、同一模块或同一机制就直接确认或合并问题。
4. 从 `AuditResult.template.md` 创建对应 `results/Axx-*.md`，记录 Evidence、反证、缺口和需要其他 Task 回答的问题。
5. 原子 checkpoint Task 状态。中断后从最后一个有效 checkpoint 恢复，不从聊天记忆猜测进度。

需要运行证据时，优先在 `/tmp` 或临时目录构造最小、可回收的本地复现，调用项目自身 CLI/API，检查错误输入、边界输入、循环配置、实际状态变化和错误传播。验证目标是项目声明行为的正确性；不得超出 `SKILL.md` Scope 定义的工程验证边界。

## Phase 4 — Finding Verification

读取 [finding-contract.md](finding-contract.md)。对每个 candidate：

1. 为每个 candidate 分别写出可证伪 Claim、影响机制、触发条件和预期观察。
2. 跟踪相关 caller/callee、数据流、owner 和 lifecycle。
3. 搜索旁路、反例、保护条件、其他实现和运行/测试证据。
4. 证据充分时进入 `confirmed`，被否定时进入 `rejected`，仍缺关键证据时进入 `needs-verification`。
5. 通过 `upsert-finding` 维护稳定 `AUD-nnn`；只有 identity gate 已证明根因、owner、修复边界和单一修复效果一致时才复用 ID。证据不足时保留独立 Finding，不按模块或表象强行聚类，也不绕过状态转换。

局部验证通过只代表“可进入 reconciliation”。报告前仍可能被合并、降级、改为 stale 或重新排序。

## Phase 5 — Cross-module Reconciliation

读取并完整执行 [cross-module-review.md](cross-module-review.md)。至少：

```text
Task findings
    ↓
Boundary Ledger
    ↓
Finding identity reconciliation
    ↓
Contradiction resolution
    ↓
End-to-end trace
    ↓
Severity / Confidence re-ranking
    ↓
Final Report
```

- 根据 identity gate 合并已证明属于同一 Finding 的现象，并保持其他 candidate 独立；
- 解决 Task 间矛盾；
- 贯通边界两端的调用链、数据流、生命周期和所有权；
- 检查 shared core 对所有 caller/platform 的影响；
- 重新评估 severity 和 confidence；
- 明确未闭合的 Evidence gap。

即使没有 confirmed Finding，也要记录覆盖矩阵、矛盾检查和“未发现可确认跨模块问题”的证据，不得省略阶段。

## Phase 6 — Final Report

1. 再次校验 Snapshot；发现 drift 时停止并执行 stale 处理。
2. 更新 `Findings.md`，让每个状态和 Evidence 指向唯一权威条目。
3. 更新 `Dashboard.md` 的计数、状态、阻塞和 Last Verified Snapshot。
4. 从 `Report.template.md` 生成 `Report.md`：按本轮 `output_language` 汇总当前 confirmed P0–P3、cross-module Findings、needs-verification 和 handoff。中文模式使用中文状态显示，内部状态值和 runtime state 保持英文枚举。
5. 在 Dashboard 与 Report 中同步 Documentation Discoverability：文档中心、固定入口、`linked/docs-refresh-required` 状态、维护方和具体动作。缺入口时不得声称 Audit 已能从项目文档中心找到。
6. 使用 `validate-output` 并校验文档互链、Task/Result 一一对应、Finding ID 唯一、所有确认项含 Snapshot/Evidence。
7. checkpoint completion。不要在 Audit 内执行 handoff 的修改、计划创建、文档中心更新、commit 或 PR。

## Documentation Discoverability

Audit 与 Docs 的职责分离如下：

- Audit 写入并维护 `<docs-root>/audit/**`，固定入口是 `audit/Report.md`。
- Docs 幂等维护 `<docs-root>/README.md` 或一个既有 route index 中的简短入口，不复制 Finding、计数或结论。
- 根 README 快捷链接可选；已能到达文档中心时不要求重复添加。
- 新 Audit 与 Docs Refresh 同时授权时，顺序必须是 `read-only Audit preflight → Docs Refresh → AuditSnapshot/init → Audit execution`。
- Audit 已有活跃 Snapshot 时不得修改 hub；记录 handoff，避免把导航更新伪装成审计输出或触发未声明 drift。

## Workspace Drift

在 resume、每个 Task、任何状态变为 `confirmed`、reconciliation 和 report 前校验。以下任一变化均使相关证据 fail closed：

- HEAD 或分支变化；
- preexisting dirty 文件内容或暂存状态变化；
- 出现未被运行纳入的受审源码变化；
- Context fingerprint 变化；
- audit scope 或输出路径变化。

处理方式：记录 `WorkspaceDrift` Evidence，将受影响结果/Finding 标 `STALE`/`stale`，停止发布当前结论。只有新 Snapshot 下重新执行必要 Task 和验证后才能清除 stale。

## Completion Checklist

- [ ] 所有 Task 已完成、blocked 或 stale，且原因可追踪。
- [ ] 所有 Task 都有对应 Result。
- [ ] 所有 confirmed Finding 有当前 Snapshot 和 Evidence。
- [ ] 相同根因已去重，矛盾已解决或降为 needs-verification。
- [ ] Cross-module Reconciliation 已记录。
- [ ] 所有当前 Audit 文档使用同一 `output_language`，Dashboard 已记录该值，且不存在非必要的中英混排。
- [ ] 最终 drift 和路径边界校验通过。
- [ ] Dashboard、Findings、Report、Task、Result 互相可达。
- [ ] Documentation Discoverability 为 `linked`，或 Dashboard、Report 和最终回复都记录了精确 Docs Refresh handoff。
- [ ] 没有修改 `<docs-root>/audit/**` 与 Git 私有状态以外的文件。
