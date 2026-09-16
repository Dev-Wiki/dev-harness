# 代码库审计流程

本文件定义长任务的阶段、checkpoint 和 fail-closed 门禁。语义判断由 AI 完成；快照、状态和路径边界由 `runtime.py` 执行。

## 运行不变量

- Context 是前置 canonical input，不是本阶段的输出。
- 受版本控制的写入集合恒为 `<docs-root>/audit/**`。
- 私有执行状态恒位于 Git 返回的 `.git/dev-harness/codebase-audit/<run-id>/` 实际路径。
- 任一旧 Evidence 只有在 Snapshot 仍有效时才能支撑当前结论。
- 任何 Task 的局部结论都必须进入全局 reconciliation。
- 固定开发者入口为 `<docs-root>/audit/Report.md`；Audit 只读检查外部导航，Docs 负责维护文档中心链接。
- 本轮 `output_language` 由用户显式要求或默认值 `zh-CN` 决定，记录在 Dashboard 并在跨会话恢复时保持一致；它不属于 Evidence Snapshot。

## 阶段 0 — 前置检查 / 恢复运行

1. 读取仓库级 `AGENTS.md`、`README.md`、`ARCHITECTURE.md`、`HARNESS.md` 和规范索引（存在时）。只有用户明确要求参考复盘历史时才读取 `LESSONS.md`；其中 LESSON 不自动成为审计标准或项目硬约束。
2. 解析唯一 `<docs-root>`；禁止为 Audit 创建第二个文档根。
3. 确定 `output_language`：显式全英文请求使用 `en`；刷新既有文档时跟随主体语言；其他新建且未指定语言的情况使用 `zh-CN`。恢复时优先读取 Dashboard 已记录值。
4. 只读检查 `<docs-root>/README.md` 或一个既有 route index 是否链接 `audit/Report.md`。把结果记录为 `linked` 或 `docs-refresh-required`；这不是代码 Finding，不分配 `AUD-*`。
5. 若同一用户授权同时包含 Docs Refresh，在所有只读 preflight 检查通过后、Audit Snapshot 建立前，由 `dev-harness-docs` 幂等添加固定入口。若只授权 Audit，不修改 hub，继续运行并持久化精确 handoff。
6. 读取 `runtime.py --help` 和 [runtime-interface.md](runtime-interface.md)。新运行用 `init --summary`，优先通过 `batch` 更新任务/问题、`render-output` 生成文档；不要硬编码未确认参数或手改 state.json。
7. 新运行把 output_language、discoverability、Context 来源和 Task 计划写入同一个批次，再渲染进行中产物。恢复先读 `status --summary` 与当前 Task/Result，按需补充相关 Finding；重新计算 Context 指纹后 `resume --summary`。
8. `render-output` 已校验它生成的全部路径；无需先逐项验证。手写产物用 `validate-outputs` 一次校验整组 audit-relative 路径，拒绝越界、符号链接逃逸和业务文件目标。

若 Context 缺失、明显过期、被截断或无法绑定 fingerprint，返回 `ContextRequired`，建议运行 `dev-harness-context` 后重新开始。不要边审计边发明新的仓库模型。

## 阶段 1 — 建立审计快照

建立并持久化 `AuditSnapshot`：

| 字段 | 含义 |
|---|---|
| 运行 ID | 本轮稳定标识 |
| 基线 SHA / 分支 | 代码基线 |
| 审计前工作区指纹 | 开始前用户修改的路径、内容与暂存状态 |
| Context 指纹 | 本轮实际使用的权威 Context 内容指纹 |
| 审计范围 | 包含项、排除项和用户限制 |
| 输出路径 | 已校验的审计文档路径 |

完整执行状态只写 Git 私有目录。结构化模式从状态自动生成 Dashboard 的 Snapshot 全表，Task/Result/Findings/Report 只保留快照 ID 和引用；禁止逐份重复手写。后续门禁由状态操作内置校验或独立 `verify-workspace` 判断 Snapshot 是否仍有效。

## 阶段 2 — 动态分区

读取 [partitioning.md](partitioning.md)，从 Context 事实生成 Task。任务围绕 subsystem、调用链、数据流、所有权或边界，而不是“每 N 个文件”或固定技术栈规则。

1. 将 Task 计划及索引信息放入同一个 `batch`，不凑任务数。
2. 用 `render-output` 生成 `tasks/Axx.md` 与其他紧凑产物；既有手写 `tasks/Axx-*.md` 按需读取模板增量维护，不整套删除重建。
3. 记录每个 Task 的 Context 来源、入口、边界、排除项、证据策略、依赖和状态。面向读者的名称和问题按 `output_language` 表达，不直接复制 Context 中缺少行为说明的风险标签。
4. checkpoint partition plan；恢复后复用未漂移的 Task，不为凑数量重新切片。

## 阶段 3 — 渐进执行审计任务

每个 Task 使用以下漏斗：

```text
Context / 仓库地图
  → 符号与文本搜索
  → 入口
  → 调用方 / 被调用方
  → 职责归属 / 生命周期 / 边界
  → 聚焦代码证据或本地行为证据
```

执行规则：

1. 开始 Task 前重新计算 Context 指纹，用批次将 Task 标为 in-progress 并校验 drift，记录当前 focus。已有内置校验时不紧邻重复 verify-workspace。
2. 沿行为链读取最少必要文件，记录实际覆盖和未覆盖范围。
3. 每个可疑现象独立保留为 task-local candidate；不要因为命名、风格、一次搜索、同一模块或同一机制就直接确认或合并问题。
4. 在 checkpoint.result 记录 Evidence、反证、缺口、candidate 映射和跨模块输入，由 renderer 生成对应结果；旧手写文件继续按模板维护。
5. 局部调查完成即将 Task/result 和相关 Finding 放入一个原子批次。中断后从最后一个有效 checkpoint 恢复，不从聊天记忆猜测进度，也不等最终答复之后才补记录。

需要运行证据时，优先在 `/tmp` 或临时目录构造最小、可回收的本地复现，调用项目自身 CLI/API，检查错误输入、边界输入、循环配置、实际状态变化和错误传播。验证目标是项目声明行为的正确性；不得超出 `SKILL.md` Scope 定义的工程验证边界。

## 阶段 4 — 问题验证

读取 [finding-contract.md](finding-contract.md)。对每个 candidate：

1. 为每个 candidate 分别写出可证伪 Claim、影响机制、触发条件和预期观察。
2. 跟踪相关 caller/callee、数据流、owner 和 lifecycle。
3. 搜索旁路、反例、保护条件、其他实现和运行/测试证据。
4. 证据充分时进入 `confirmed`，被否定时进入 `rejected`，仍缺关键证据时进入 `needs-verification`。
5. 通过 `upsert-finding` 维护稳定 `AUD-nnn`；只有 identity gate 已证明根因、owner、修复边界和单一修复效果一致时才复用 ID。证据不足时保留独立 Finding，不按模块或表象强行聚类，也不绕过状态转换。

局部验证通过只代表“可进入 reconciliation”。报告前仍可能被合并、降级、改为 stale 或重新排序。

同快照下已执行的测试可支撑多个 Finding，不按每个候选重复跑全套；仅变化、失败或新 Evidence gap 才补查。批次登记仍逐项验证契约，不能通过批量确认跳过反证。

## 阶段 5 — 跨模块复核

读取并完整执行 [cross-module-review.md](cross-module-review.md)。至少：

```text
任务内问题
    ↓
边界台账
    ↓
问题同一性复核
    ↓
矛盾处理
    ↓
端到端链路追踪
    ↓
重新评定严重度和置信度
    ↓
最终报告
```

- 根据 identity gate 合并已证明属于同一 Finding 的现象，并保持其他 candidate 独立；
- 解决 Task 间矛盾；
- 贯通边界两端的调用链、数据流、生命周期和所有权；
- 检查 shared core 对所有 caller/platform 的影响；
- 重新评估 severity 和 confidence；
- 明确未闭合的 Evidence gap。

即使没有 confirmed Finding，也要记录覆盖矩阵、矛盾检查和“未发现可确认跨模块问题”的证据，不得省略阶段。

已闭合的局部链路引用权威 Evidence，只对接缝、矛盾、遗漏或变化补查。不要把全局复核执行成重复全量审计。所有 Task/Finding/document 更新后再登记复核；之后改变输入会使旧复核失效。

## 阶段 6 — 最终报告

新结构化运行使用 `render-output → 检查内容/互链 → complete --summary → render-output`。首次渲染当前 Revision 的证据与进行中状态，complete 校验其产物未被改动，第二次只刷新已完成显示；无需重复阅读全套文档或再逐路径启动 Python。最后渲染失败必须说明文档未收口，不得口头宣称已完成。以下细则同时适用于旧手写兼容流程。

1. 再次校验 Snapshot；发现 drift 时停止并执行 stale 处理。
2. 更新 `Findings.md`，让每个状态和 Evidence 指向唯一权威条目。
3. 更新 `Dashboard.md` 的计数、状态、阻塞和 Last Verified Snapshot。
4. 由 `render-output` 生成 Report；旧手写模式才读取 Report.template.md。按本轮 output_language 汇总当前 confirmed P0–P3、cross-module Findings、needs-verification 和 handoff。内部状态枚举保持稳定。
5. 在 Dashboard 与 Report 中同步 Documentation Discoverability：文档中心、固定入口、`linked/docs-refresh-required` 状态、维护方和具体动作。缺入口时不得声称 Audit 已能从项目文档中心找到。
6. renderer 内置路径校验或手写模式的 `validate-outputs` 通过，并检查文档互链、Task/Result 一一对应、Finding ID 唯一、所有确认项含 Snapshot/Evidence。
7. checkpoint completion。不要在 Audit 内执行 handoff 的修改、计划创建、文档中心更新、commit 或 PR。

## 文档可发现性

Audit 与 Docs 的职责分离如下：

- Audit 写入并维护 `<docs-root>/audit/**`，固定入口是 `audit/Report.md`。
- Docs 幂等维护 `<docs-root>/README.md` 或一个既有 route index 中的简短入口，不复制 Finding、计数或结论。
- 根 README 快捷链接可选；已能到达文档中心时不要求重复添加。
- 新 Audit 与 Docs Refresh 同时授权时，顺序必须是 `read-only Audit preflight → Docs Refresh → AuditSnapshot/init → Audit execution`。
- Audit 已有活跃 Snapshot 时不得修改 hub；记录 handoff，避免把导航更新伪装成审计输出或触发未声明 drift。

## 工作区漂移

在 resume、每个 Task、任何状态变为 `confirmed`、reconciliation 和 report 前校验。以下任一变化均使相关证据 fail closed：

- HEAD 或分支变化；
- preexisting dirty 文件内容或暂存状态变化；
- 出现未被运行纳入的受审源码变化；
- Context fingerprint 变化；
- audit scope 或输出路径变化。

处理方式：记录 `WorkspaceDrift` Evidence，将受影响结果/Finding 标 `STALE`/`stale`，停止发布当前结论。只有新 Snapshot 下重新执行必要 Task 和验证后才能清除 stale。

## 完成检查清单

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
