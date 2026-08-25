# 跨模块复核

这是每次审计的强制全局阶段。任务结果是局部证据，不能直接拼接成最终报告。

最终收敛必须完整经过：

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

## 输入

- 当前有效 `AuditSnapshot`；
- 所有 Task 及 Result，包括 blocked、无 finding 和 stale 的任务；
- Findings Registry 中的 candidate、needs-verification、confirmed 和 rejected 项；
- Context 中的 subsystem、boundary、shared core、platform 和 integration 关系。

开始前运行漂移校验。失败时停止复核，将受影响结论标为 `stale`。

## 1. 建立边界台账

为每条重要接缝记录两端和证据：

| 边界 | 生产方 / 调用方 / 负责方 | 消费方 / 被调用方 / 借用方 | 任务 | 证据 | 状态 |
|---|---|---|---|---|---|
| `{boundary}` | `{side-a}` | `{side-b}` | `{Axx, Ayy}` | `{result links}` | `{covered/gap}` |

至少覆盖 Context 中存在的 runtime、platform、shared core、data/persistence、external integration 和 build/package 边界。不适用的轴无需硬造。

## 2. 复核问题同一性

先逐项判断 candidate identity，再按根因、owner 和修复边界聚类。只有证据同时证明根因一致、owner / responsibility boundary 一致、修复边界基本一致，并且一个修复可以合理同时解决多个现象时，才允许合并：

- 合并同一根因的多模块症状，保留最早稳定 Finding ID；
- 保留 source Task、alias、影响平台和所有 Evidence 链接；
- 若表象相同但机制不同，保留独立 Finding；
- 若位于同一模块或宽泛机制但任一 identity 条件未闭合，继续保留独立 Finding；
- 把只重复描述最佳实践而无具体机制的 candidate 拒绝或退回验证。

## 3. 处理矛盾

显式列出冲突，而不是选择更自信的 Task：

| 主张 | 支持证据 | 反驳证据 | 缺失的验证 | 结论 |
|---|---|---|---|---|
| `{claim}` | `{link}` | `{link}` | `{reproduction or behavior evidence}` | `{resolved/needs-verification}` |

检查条件编译、平台 variant、启动/清理顺序、异常路径、并发时序和其他实现。无法用证据解决的冲突必须降为 `needs-verification`。

## 4. 追踪端到端行为

对可能跨层的 Finding 贯通完整链路，例如：

```text
entry/UI lifecycle → state/manager → wrapper/adapter
                   → FFI/native/service → worker/callback/storage
```

同时检查：

- configuration → runtime；
- state → mutation；
- precondition → side effect；
- module → module；
- input/state → transformation → output/side effect；
- 调用是否可达，返回或错误是否被正确传播；
- owner 的创建、共享、取消和销毁顺序；
- 数据在边界两端的类型、单位、空值和一致性；
- callback/thread/transaction 的上下文变化；
- shared core 变更对所有 caller/platform 的影响；
- build/package variant 是否实际包含被审实现。

只检查链路中一层不能完成此阶段。

## 5. 重新评定并执行门禁

对合并后的每个 Finding 重新评估：

- Severity 是否反映实际可达影响，而不是局部代码外观；
- Confidence 是否被跨模块证据加强或削弱；
- Snapshot/Evidence 是否仍为当前；
- Suggested Next Action 是否指向正确 owner Skill；
- 是否还有未覆盖 caller、platform 或 lifecycle。

只有证据闭合且无未解决矛盾的项才能留在当前 `confirmed` 集合。其他项标 `needs-verification`、`rejected` 或 `stale`。

## 必备结果

在 Report 和相关 Result 中记录：

- Boundary coverage ledger 或其权威链接；
- merged/aliased Finding IDs，以及四项 identity 条件的证据；
- 保持独立的相关 Candidate 及未合并理由；
- contradictions 与决议；
- 新发现的跨模块 Finding；
- severity/confidence 变化；
- 未覆盖边界和 Evidence gaps；
- reconciliation 使用的 Snapshot。

即使无 Finding，也要记录审查了哪些边界、哪些 Task Result 相互核对以及为何没有可确认结论。没有这份记录不得完成 Audit。
