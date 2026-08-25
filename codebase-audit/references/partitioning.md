# 基于 Context 的审计分区

目标是把超出单次上下文的代码库拆成可验证的行为域，同时保留跨边界关系。不要维护语言或框架 checklist。

## 从 Context 提取分区事实

只使用 canonical Context 中有证据的事实：

- subsystem / module 及职责；
- 运行入口、后台 worker、回调和生命周期；
- UI、adapter、FFI/native、service、data/persistence 等边界；
- platform / build variant / shared core；
- 外部系统、permission model boundary 或外部操作边界；
- 构建、打包和验证入口；
- Context 明示的高影响或待确认项。

每个分区理由必须引用 Context 路径或其中的仓库 evidence。Context 未确认的架构不能在 Task 中升级成事实。

## 分区步骤

1. **画边界图**：列出入口、模块、shared owners、数据存储、外部依赖和平台分叉。
2. **找行为链**：把同一调用链、数据流、所有权或生命周期组合为候选域。
3. **切在可验证边界**：让一个 Task 能回答具体的正确性或影响问题，并有明确 entry points 和 exclusions。
4. **保留接缝**：任何跨 Task 边界都登记 producer/consumer、caller/callee、owner/borrower 或 write/read 两端。
5. **控制规模**：大型仓库通常使用 4–10 个主 Task，小型仓库可更少；不要为了目标数量强拆或合并。
6. **检查覆盖**：每个 in-scope Context 事实至少映射到一个 Task；每条重要边界至少有一个主 Task 和一个 reconciliation 输入。

文件只能作为入口或 Evidence path，不能单独成为审计单位。按目录平均切分通常会丢失跨层问题。

## 优先级启发式

优先安排同时具备多个特征的域：

- 多 caller、多平台或 shared core；
- 生命周期、线程、ownership 或异步回调跨边界；
- 数据持久化、迁移、permission model 状态或外部副作用；
- Context 标为高影响、证据不足或契约不清；
- 缺少可执行验证入口。

这些只决定阅读顺序，不直接证明存在 Finding，也不预设 category 或 severity。

## 任务契约

每个 `tasks/Axx-*.md` 必须包含：

| 字段 | 要求 |
|---|---|
| 任务 ID / 状态 | 稳定 ID；状态可持久化到检查点 |
| 范围 | 行为域和范围内路径 |
| 分区依据 | 引用 Context 事实与证据 |
| 入口 | 最小起始位置 |
| 重要边界 | 接缝两端和相关任务 |
| 排除项 | 本任务明确不覆盖什么 |
| 证据策略 | 搜索 → 追踪链路 → 聚焦阅读 / 行为验证 |
| 依赖 | 前置任务、共享证据和待回答问题 |
| 审计快照 | 当前代码与 Context 基线 |

建议 ID `A01`、`A02`…；名称描述行为域，例如 `A03-session-lifecycle`，不要只写技术栈名。Task 标题和问题应描述实际工程行为，例如“工作区路径与操作边界”“执行前置检查与状态变化”，不要仅复制 Context 中缺少具体机制的风险标签。默认中文产物使用自然中文名称；仅在 `output_language=en` 时使用全英文自然语言。

## 覆盖检查

生成 Task 后检查：

- 是否存在无 owner 的 Context 模块或入口；
- 是否存在只扫描一端的 runtime/platform/data boundary；
- shared core 是否覆盖所有主要 caller；
- build variant、后台执行或异常路径是否被无意排除；
- 两个 Task 是否可能覆盖相关现象；在 identity gate 完成前仍保持各自 candidate 独立；
- 任一 Task 是否过大到必须批量加载无关文件。

覆盖有缺口时调整分区或明确 blocker。不要用增加一组通用 checklist 来填补缺口。
