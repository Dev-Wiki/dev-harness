# 问题登记契约

Finding 在本流程中指“审计问题”。它是可追踪、可证伪并绑定仓库快照的工程缺陷主张，不是代码气味清单或泛化建议。

## 状态机

```text
candidate → needs-verification → confirmed
         ↘ rejected
confirmed → stale → confirmed | rejected | resolved
confirmed → resolved
```

- `candidate`（候选项）：局部证据显示值得调查，尚未通过验证门禁。
- `needs-verification`（待验证）：Claim 清晰，但缺少关键链路、反证检查或运行证据。
- `confirmed`（已确认）：当前 Snapshot 下有代码或运行证据，反证已检查，影响机制成立。
- `rejected`（已排除）：证据否定 Claim、已有保护或实际语义不同。
- `stale`（已失效）：Snapshot/Context 漂移，旧证据不再代表当前事实。
- `resolved`（已解决）：修复后在新 Snapshot 下重新验证不再成立；Audit 本身不执行修复。

不得从搜索命中直接跳到 `confirmed`。Task-local candidate 可使用 `Axx-Cnn`；进入全局 Registry 时分配稳定 `AUD-nnn`。只有通过 Finding identity gate 后，才能为已证明同一根因的现象保留最早 ID 并记录别名；门禁未完成时保持独立。

## 必备字段

每个 Registry Finding 包含：

| 字段 | 要求 |
|---|---|
| ID / 状态 | 稳定 `AUD-nnn` 与状态机中的状态 |
| 严重度 | P0/P1/P2/P3；按影响和紧迫度，不按置信度 |
| 分类 | 自由分类，不受技术栈枚举限制 |
| 摘要 | 一句话描述可观察问题 |
| 主张 | 可被反证的机制陈述 |
| 证据 | 仓库内 `path:line`、运行输出或可复查产物 |
| 调用链 / 数据流 | 相关入口、边界、职责归属和生命周期 |
| 已检查反证 | 搜过什么反例、保护、旁路和其他实现 |
| 风险 / 影响 | 触发条件、影响对象和后果 |
| 置信度 | 高/中/低，并说明证据缺口 |
| 建议后续动作 | 验证或交接，不自动执行 |
| 审计快照 | 运行 ID、基线 SHA、Context 指纹、最近验证位置 |
| 来源任务 | 任务/结果链接及去重别名 |

`confirmed` 不允许低置信度。Severity 高不代表证据充分；影响很大但证据不足仍是 `needs-verification`。

## 验证门禁

按顺序验证 candidate：

1. **Claim**：说明哪个行为在什么条件下为何错误。
2. **Chain**：追踪 caller/callee、read/write、producer/consumer、owner/borrower 或 lifecycle。
3. **Positive Evidence**：给出支持机制的代码或运行证据及精确位置。
4. **Counter-evidence**：检查保护条件、清理路径、替代实现、平台分支、异常路径和测试。
5. **Impact**：证明影响可达，而非只存在理论可能。
6. **Freshness**：验证 Snapshot 与 Context 未漂移。
7. **Reconciliation**：检查其他 Task 是否重复、冲突、补充或改变 severity。

缺少代码或运行证据不得 confirmed；无法完成关键步骤时保持 `needs-verification`。静态搜索不到引用不能单独证明 dead code，单处没有保护也不能证明完整调用链没有保护。

## 证据质量

优先使用可复查的最小证据：

- `path:line` 加相关符号和行为摘要；
- caller → boundary → callee 的链路；
- input/state → transformation → sink 的数据流；
- 可重复命令、测试或日志的摘要与退出状态；
- 反证搜索范围和结果；
- Evidence 采集时的 Snapshot fingerprint。

不要复制大段源码或只写“经检查”。生成代码、依赖目录、缓存和不稳定临时日志不能作为唯一证据。Evidence 含非公开配置值、个人数据或机器私有路径时先脱敏。

## 去重规则

用根因与修复边界去重，而不是用模块归属、机制名称或错误表象。Candidate 先独立保留，只有证据同时证明以下四点后才能合并：

1. 根因一致；
2. owner / responsibility boundary 一致；
3. 修复边界基本一致；
4. 一个修复可以合理同时解决多个现象。

任一点尚未证明就保持独立 Finding，并把待确认关系带入 Cross-module Reconciliation。位于同一模块、同一函数、同一配置解析器或同一宽泛机制，不足以证明 Finding identity。

具体规则：

- 同一 owner/lifecycle 错误导致多个平台症状：一个 Finding，列出多影响面。
- 不同根因恰好产生同一错误消息：保留多个 Finding。
- 新证据扩大影响：更新原 ID 的 Scope/Evidence/Severity。
- 结论冲突：降为 `needs-verification`，直到 cross-module review 解决。

例如，“缺失 base 后仍返回 partial workspace”与“循环 base 导致无限递归”应先作为两个 Candidate。只有跨模块复核证明二者根因、职责归属、修复边界和单一修复效果均一致时，才合并为同一 `AUD-nnn`。

## 失效与解决

发现 HEAD、branch、dirty fingerprint、Context 或 scope 漂移时，将受影响 Finding 标 `stale` 并保留旧 Snapshot；不得原样复制到当前报告的 confirmed 区。外部修复完成后，只有在新 Snapshot 下重跑相关验证和 reconciliation 才能标 `resolved`。

## 交接内容

交接只提供：Finding ID、Claim、Snapshot、Evidence、影响、已检查反证、验证缺口、建议验收口径和目标 Skill。不要借 handoff 自动修代码、生成计划、改文档、补命令、commit 或创建 PR。
