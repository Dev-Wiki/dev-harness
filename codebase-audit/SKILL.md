---
name: dev-harness-codebase-audit
description: Use when a user-owned or explicitly authorized repository needs a systematic engineering-quality, correctness, and cross-module consistency audit across modules or sessions, with canonical Context as input, durable audit state, verified findings, drift detection, and mandatory cross-module reconciliation; not for penetration testing or offensive security workflows
---

# dev-harness-codebase-audit

对无法在一次会话中完整载入上下文的存量代码库做渐进式审计。让 AI 负责语义理解，让 `runtime.py` 负责快照、状态、漂移和写入边界；不要把本 Skill 变成语言规则库或静态分析器。

## Scope

本 Skill 面向用户拥有或已获准审计的代码仓库，执行工程质量、行为正确性和跨模块一致性审计。主要关注：

- correctness defects 与 configuration defects；
- lifecycle / state inconsistencies；
- cross-module contract violations 与 error propagation；
- concurrency / resource-management issues；
- destructive-operation correctness；
- build/runtime inconsistencies；
- maintainability / technical debt；
- testing / verification gaps；
- documentation/code drift。

本 Skill 不是 penetration testing 或 offensive security workflow。除非用户显式切换到独立的专门安全工作流，否则不得验证漏洞可利用性、构造 exploit / payload / 攻击 PoC、尝试认证或访问控制绕过、执行 privilege escalation、提取 credential / secret、对第三方目标执行安全测试、进行 weaponization，或把普通工程缺陷主动升级描述为 security vulnerability。即使用户另行授权专门安全工作，也不得把该授权默认为本 Audit 的范围扩展。

运行时验证只围绕项目声明行为的正确性，优先使用本地、确定性、最小复现。允许在 `/tmp` 或临时目录验证项目自身 CLI/API、错误输入、边界输入、循环配置、状态变化、错误传播，以及 destructive operation 是否符合项目声明语义；默认不得面向第三方目标或执行上述专门安全测试活动。

## 输出语言

- 把 `output_language` 作为 Audit 运行级文档约定，取值为 `zh-CN` 或 `en`。它不是 `AuditSnapshot` 或 Evidence fingerprint 的组成部分，语言变化本身不得让 Finding 变为 `stale`。
- 只有用户显式要求“全英文”“English only”或等价表达时才使用 `en`；其他情况默认 `zh-CN`。不得因为源码、Context、README 或技术栈主要使用英文而自动切换。
- 在 `Dashboard.md` 记录本轮输出语言；恢复运行时沿用已记录值。旧产物未记录语言时，按本规则选择并在下一检查点前统一当前 Audit 文档。用户显式要求中途切换时，也必须统一更新所有当前 Audit 文档，不得只翻译单个 Report。
- `zh-CN` 产物的标题、表头、说明、摘要和状态显示使用自然中文；保留 Finding/Task ID、P0–P3、内部状态枚举、路径、代码符号、CLI 参数、命令、SHA/fingerprint、原始日志和必要通用技术名。首次说明状态机时给出中文显示名与内部枚举的映射，之后正文优先使用中文。
- `en` 产物把模板中的自然语言完整转换为英文，不残留中文模板说明；必须原样引用的非英文源码或日志可保留，并附英文观察摘要。

内部状态值保持稳定，中文产物按下表显示：

| 内部状态 | 中文显示 |
|---|---|
| `candidate` | 候选项 |
| `needs-verification` | 待验证 |
| `confirmed` | 已确认 |
| `rejected` | 已排除 |
| `stale` | 已失效 |
| `resolved` | 已解决 |

Task 与运行状态同样只翻译显示层：`pending` 为“待开始”、`in-progress` 为“进行中”、`blocked` 为“受阻”、`completed` 为“已完成”；runtime 与 Git 私有状态仍保存原枚举。

## 硬边界

- 把 `dev-harness-context` 维护的 Context 当作唯一 canonical repository input。只读使用 `README.md`、`AGENTS.md`、`ARCHITECTURE.md`、`HARNESS.md` 及其规范索引；不要另建 Repository Context。
- 只允许写入 `<docs-root>/audit/**` 和 Git 私有目录 `.git/dev-harness/codebase-audit/**`（worktree 中使用 Git 返回的实际私有路径）。
- 不得为了补导航而由 Audit 修改 `<docs-root>/README.md` 或根 `README.md`；文档中心入口归 `dev-harness-docs`，Audit 只检查并记录 discoverability 状态与精确 handoff。
- 不得修改业务源码、测试、配置、构建文件、Context 托管区或其他 Skill 的产物。
- 只发现、验证和路由问题；不得自动修复、commit、创建 PR、发布或创建 Roadmap/计划任务。
- 不得用固定语言、框架或“最佳实践”巨型 checklist 代替基于 Context 的动态分区。
- 必须运行 Cross-module Reconciliation；项目小、没有发现问题或所有任务看似独立都不是跳过理由。

## 按需读取

- 开始或恢复运行时，读取 [references/workflow.md](references/workflow.md)。
- 生成审计任务时，读取 [references/partitioning.md](references/partitioning.md)。
- 第一次记录 candidate 或改变 Finding 状态前，读取 [references/finding-contract.md](references/finding-contract.md)。
- 所有任务结束、生成最终报告前，读取 [references/cross-module-review.md](references/cross-module-review.md)。
- 创建产物时使用 `templates/` 中对应模板，不删除其职责、导航、`Snapshot`、`Evidence` 或 Finding Contract 章节；按本轮 `output_language` 转换所有面向读者的自然语言。

## Preflight

1. 确定仓库根、当前分支、HEAD、Git 私有目录和已有 dirty files。
2. 读取 canonical Context、项目规范索引与 `HARNESS.md`。Context 缺失、证据被截断、与仓库明显不符或无法得到可记录的 Context fingerprint 时，停止并交给 `dev-harness-context` 刷新；不得自行补一套上下文。
3. 解析唯一 `<docs-root>`：尊重用户指定的既有路径；否则复用已有索引、治理文件、活跃 `plan/` 或 `audit/` 所在根；仅有 `doc/` 或 `docs/` 时使用已有者。二者均为项目所有且归属不明，或二者皆不存在时停止并先交给文档治理流程建立 canonical root；Audit 不自行创建第二套文档体系。
4. 确定 `output_language`：显式全英文请求使用 `en`，否则使用 `zh-CN`；恢复运行时优先沿用 Dashboard 已记录值。
5. 只读检查 `<docs-root>/README.md` 或一个既有 route index 是否链接固定入口 `<docs-root>/audit/Report.md`，将状态记为 `linked` 或 `docs-refresh-required`。缺入口不是 `AUD-*` Finding。
6. 若用户同时授权 Docs Refresh，在 Audit 只读 preflight 已解析稳定路径后、`runtime.py init` 建立 Snapshot 前，由 `dev-harness-docs` 幂等补入口；Audit 自己不得越界写入。若只授权 Audit，继续运行但必须把精确 handoff 写入 Dashboard、Report 和最终回复。
7. 校验所有预期输出都位于 `<docs-root>/audit/**`，所有运行状态都位于 Git 私有目录。
8. 用 `runtime.py` 初始化或恢复运行并建立 `AuditSnapshot`。先读取 `python <skill-dir>/runtime.py --help`，再按实际接口使用 `init`、`resume` / `status`、`verify-workspace`、`checkpoint`、`upsert-finding`、`validate-output`、`checkpoint-cross-module` 和 `complete` 等语义操作；不硬编码未确认参数，不手工伪造或绕过状态校验。

`AuditSnapshot` 至少绑定 base SHA、branch、preexisting dirty files 及内容 fingerprint、Context fingerprint、audit scope 和 output paths。

## 核心流程

按顺序执行，详细门禁见 [references/workflow.md](references/workflow.md)：

```text
preflight → snapshot → dynamic partition → task execution
          → finding verification → cross-module reconciliation → report
```

1. 从 Context 的真实 subsystem、runtime/platform boundary、shared core、数据流、持久化、外部集成和构建边界生成任务。文件数量不是分区依据。
2. 按 `repository map → search → entry point → caller/callee → owner/lifecycle/boundary → evidence` 渐进读取；不要为“完整”批量加载无关文件。
3. 把任务和阶段结果持久化到审计文档，把运行 checkpoint 持久化到 Git 私有状态。恢复时先校验快照，再相信旧结果。
4. 每个可疑现象先独立进入 `candidate`，检查反证、旁路、生命周期和其他实现。不得因位于同一模块或机制就提前合并；证据不足时使用 `needs-verification`，不得提高措辞强度来替代验证。
5. 对必要 candidate 执行本地、确定性、最小行为验证，证明触发条件、实际状态变化、错误传播或可观察影响；不得把工程验证扩展为专门安全测试。
6. 对所有任务做 Finding identity reconciliation、矛盾处理、完整调用链/数据流审查和跨平台影响检查，之后才能发布当前 `confirmed` 结论。
7. 最终报告只汇总已验证 Findings、未决项和建议路由，不写脱离 Evidence 的长篇最佳实践建议。
8. 最终报告单独记录 Documentation Discoverability：文档中心、固定 Audit 入口、`linked/docs-refresh-required` 状态和精确 Docs handoff。

## 产物职责

使用同一 `<docs-root>/audit/`：

- `Dashboard.md`：仅维护运行快照、输出语言、任务状态、计数、当前焦点和阻塞；链接到其他产物，不放 Finding 正文。
- `Findings.md`：稳定 Finding Registry；通过 identity gate 后确认同一根因的项复用 ID，记录状态、Snapshot 和 Evidence。
- `tasks/Axx-*.md`：当前轮次要扫描什么，以及范围、边界、排除项、证据策略和依赖。
- `results/Axx-*.md`：对应 Task 的检查范围、candidate、反证、证据缺口和跨模块输入。
- `Report.md`：当前快照下的开发者总览，聚合 Findings 和 Cross-module 结论。

各文档必须互相链接。详细证据只维护在 Finding 或 Task Result 的权威位置，其他文档链接过去，不复制正文。历史由 Git 承担；V1 不创建按时间滚动的归档副本。

稳定外部入口是 `<docs-root>/audit/Report.md`。`<docs-root>/README.md` 或既有 route index 的入口由 Docs 维护；根 README 快捷链接可选。Audit 不得把缺失导航伪装成 Finding，也不得在活跃 Snapshot 中调用 Docs 修改 hub，否则会形成 workspace drift。

## Drift 与停止条件

在恢复运行、开始每个 Task、把 Finding 标为 `confirmed`、Cross-module Reconciliation 和生成报告前，运行 workspace drift 校验。

HEAD、分支、preexisting dirty 内容/暂存状态、Context fingerprint 或受审范围发生未纳入快照的变化时：

1. 立即停止产生新的当前事实；
2. 把受影响 Task/Result/Finding 标记为 `STALE` 或 `stale`，并记录 drift evidence；
3. 不得把旧 Evidence 继续表述为当前已确认事实；
4. 建立新快照并重新验证后才能恢复确认。

Context 不可用、docs root 冲突、输出越界、运行状态损坏、Evidence 无法绑定快照或 Cross-module 阶段未完成时同样 fail closed。

## Finding 与交接

Finding 必须遵循 `candidate → verification → confirmed/rejected`，并可在仓库演进后变为 `stale`，修复且重新验证后变为 `resolved`。`confirmed` 至少需要代码或运行证据、相关调用链/数据流、反证检查、风险、置信度和 Snapshot；静态搜索不到引用不等于 dead code。

只建议以下 handoff，不在本运行中执行后续变更：

| Finding 类型 | 建议交给 |
|---|---|
| 已确认 defect、crash、lifecycle bug | `dev-harness-auto-fix` |
| 架构、重构、技术债工作 | `dev-harness-planning` |
| 文档治理问题 | `dev-harness-docs` |
| 验证命令缺口 | `dev-harness-commands` |
| Git、发布或 changelog 规范缺口 | `dev-harness-git-workflow` |

交接只包含 Finding ID、当前 Snapshot、Evidence、影响、验收方向和建议 owner。授权审计不等于授权任何后续修改。

产物 discoverability 缺口是运行级 Docs handoff，不需要 Finding ID。它必须包含文档中心路径、稳定目标 `audit/Report.md`、当前状态和最小动作“增加一个简短入口”；不得复制 Audit 结论或扩大为文档重组。

## 完成口径

仅当所有计划内 Task 有结果或明确 blocker、所有发布的 confirmed Findings 绑定当前 Snapshot、重复和矛盾已收敛、Cross-module Reconciliation 已记录、最终 drift 校验通过，并且 Documentation Discoverability 已标记为 `linked` 或记录了精确 Docs Refresh handoff 时，才把运行标为完成。报告本次只写入哪些审计文档、状态路径、快照、Finding 计数、未决 Evidence gap、discoverability 状态和建议 handoff。
