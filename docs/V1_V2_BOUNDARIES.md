# V1 / VNext 与 V2 边界

> 文档角色：本文件是当前已支持功能范围、非目标和封板标准的唯一事实源。
> [`dev-harness VNext 优化与 Codebase Audit 设计方案`](dev-harness%20VNext%20%E4%BC%98%E5%8C%96%E4%B8%8E%20Codebase%20Audit%20%E8%AE%BE%E8%AE%A1%E6%96%B9%E6%A1%88.md) 记录 v1.8.0 的设计依据；[`V2_BACKLOG.md`](V2_BACKLOG.md) 只记录未来候选，不覆盖本文件。

## 版本命名

设计方案中的 **VNext** 指从既有 V1 向 v1.8.0 Project Contract 与 Codebase Audit 功能的兼容演进，仍属于本文件定义的 V1 范围；v1.9.0 在同一边界内补充 Capability Catalog 与 Audit 文档入口可达性，v1.9.1 进一步统一中文术语和模板表达，均不改变 V2 边界。VNext 不是 V2 的别名。当前实现与后续排期分别以本文件和 `V2_BACKLOG.md` 为准，设计记录中的实施阶段不作为活动任务清单。

## V1 定位

`dev-harness` V1 / VNext 的目标是：让已有项目具备一致的 Project Contract、可执行验证接口，以及 Bugfix 和大型代码库审计的完整证据链。

适用项目：

- WPF 客户端
- Harmony 手机 / PC App
- Win32 应用
- WPF + NativeBridge + Win32 / C++ SDK 这类混合项目
- Qt 客户端（当前仍支持接入，但不作为本轮优先增强目标）
- Go、Flutter、Node.js 项目（按各自高风险边界门控）

V1 解决的问题：

- AI 第一次进入仓库时，不知道项目怎么读
- AI 不知道 build / test / quick / bugfix / full 应该跑什么
- AI 不知道哪些目录和文件是高风险区域
- AI 在 NativeBridge / Win32 / C++ SDK 上容易盲改
- Bugfix 没有固定的复现、定位、回归、验证基线
- AI 容易把已有工作区修改混入本轮修复或提交
- “已验证”和“已审查”没有绑定到最终代码 diff
- 大型代码库无法在一次会话中完整载入上下文，跨会话扫描进度、证据和 Finding 容易丢失

## V1 已包含

### 1. 项目上下文初始化

- 生成 `README.md`
- 生成 `AGENTS.md`
- 生成 `ARCHITECTURE.md`
- 生成 `HARNESS.md`

### 1.1 文档与规划组织

- 复用项目已有 `doc/` 或 `docs/` 根目录，不创建第二套文档树
- 建立文档中心入口、渐进式导航、SSOT、文档归属和归档规则
- 当前功能信息分散、支持范围有角色/平台/版本差异或无法可靠统计时，按需建立 Capability Catalog；已有同类功能说明文档时复用
- Capability Catalog 分别记录支持状态、适用范围、交付版本和验证方式，只统计有稳定 ID 与证据、可独立验证的功能项
- 在同一文档根目录生成 `plan/Dashboard.md` 与 `plan/TaskDetails.md`
- 在同一文档根目录维护 `audit/` 的任务、结果、Finding Registry 与报告
- 不内建从代码生成全量 Diataxis 文档或基于分支 diff 的全仓文档陈旧检测

### 2. 客户端项目接入支持

- 优先识别 `WPF / Harmony / Win32 / Unknown`
- 识别 `WPF + NativeBridge` 混合项目的基础特征
- 对 `Qt` 保留基础识别与安全回退
- 提取高风险目录与禁改区域
- 提取调用链候选、架构边界规则、禁止操作清单、探索建议

### 3. NativeBridge 风险识别与明确标注

- 识别 `*.vcxproj`
- 识别 `DllImport`
- 识别 `MarshalAs`
- 识别 callback / observer
- 识别 Win32 API 使用痕迹
- 输出“自动识别候选”
- 输出“需人工确认”

### 4. 命令语义层

- `harness:build`
- `harness:test`
- `harness:quick`
- `harness:bugfix`
- `harness:full`

### 5. Bugfix Flow 与可执行契约

- `dev-harness-auto-fix` 内联 repro / triage / regression / verify 四阶段参考
- analyze / fix / commit / unattended 四种显式授权模式
- 可证伪假设（Claim / Prediction / Probe / Observation / Status）
- 回归测试默认要求修复前 RED、修复后 GREEN
- review 与最终验证绑定 diff hash
- DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT 完成状态

`auto-fix/runtime.py` 把以下边界变为可执行、可测试行为：

- WorkspaceSnapshot 保存任务开始时的 HEAD、分支和已有修改指纹
- 已有 dirty worktree 可以保留，但 Agent 不得触碰
- AutoFixChangedFiles 只包含本轮对话产生的变更
- 状态保存在 Git 私有目录，支持进程中断后的阶段恢复
- 非法阶段跳转、未声明变更、已有修改漂移和提交越权会被拒绝

并已补上客户端项目的风险边界：

- UI 层
- 资源层
- 原生桥接层
- 打包层

### 6. Codebase Audit V1

- 基于 Canonical Context 动态生成 subsystem / runtime / platform / native / data 等审计分区，不内置巨型语言 checklist
- AuditSnapshot 绑定 HEAD、branch、既有 dirty fingerprints、Context fingerprint、scope 和输出根
- 状态保存在 `.git/dev-harness/codebase-audit/<run-id>/state.json`，支持跨会话 resume/status/task checkpoint
- 只允许写入既有 `<docs-root>/audit/**`；源码、Context 或工作区漂移时 fail-closed 并把旧 confirmed Finding 标 stale
- Finding 使用 candidate / needs-verification / confirmed / rejected / stale / resolved 状态并绑定 Evidence 与 Snapshot
- 完成前强制 Cross-module Reconciliation；Audit 不修复源码、不创建 PR、不自动污染 Roadmap
- 固定入口为 `<docs-root>/audit/Report.md`；缺少文档中心链接时记录 `docs-refresh-required`，由 Docs 在 Audit Snapshot 建立前补入口，Audit 不越界修改 hub

## V1 明确不做

- UI 自动化
- 截图驱动验证
- 日志 / 指标 / Trace 平台接入
- 多 worktree 并行调度器（单个 worktree 的 Git 私有状态路径已支持）
- 自动 PR / 多 Agent review 调度器
- Native 层自动修复
- 全量文档内容生成与发布前文档覆盖率审计
- ABI / marshaling 正确性自动证明
- Win32 句柄 / 线程 / 消息循环的深语义验证

## V2 候选方向

### 1. Runtime Harness 编排

- 在现有 auto-fix 状态契约上增加每任务独立运行目录
- worktree 启动
- 运行状态探针
- 自动清理运行环境

### 2. Observability Harness

- 日志入口标准化
- 指标 / Trace 查询入口
- AI 可读的本地观测层

### 3. UI Harness

- 应用启动
- 截图
- 基础 UI 自动检查
- smoke 验证

### 4. NativeBridge 深化

- 自动抽取更细的 `Service -> Interface -> Bridge -> Native` 调用链
- 高风险文件评分
- 更细的 marshaling / callback / thread / handle 风险分类
- 持久保存人工确认结果，并写回相应文档

### 5. Agent Loop Automation

- 自动 review
- 自动反馈修复循环
- 文档陈旧检测
- tech debt / doc gardening 任务

## 封板标准

满足以下条件即可视为 V1 封板：

1. 能生成 4 个上下文文件
2. 能输出 `build / test / quick / bugfix / full` 语义层
3. 能显式标出高风险区域与禁改边界
4. 对 NativeBridge 项目能输出“自动识别候选 / 需人工确认”
5. 不会在缺少命令或证据时伪造完成
6. 已有 dirty worktree 不会被本轮修复误改、误暂存或误提交
7. 完成证据与最终 diff 一致，代码变化会使旧证据失效
8. 已有 `doc/` 或 `docs/` 能被复用，文档整理和 planning 不会创建竞争根目录
9. 当前功能复杂或分散时有唯一、可验证、可统计的权威文档；简单项目和已有同类功能说明文档不被强制拆分
10. Codebase Audit 能跨会话恢复，且业务源码或 Context 漂移后不会继续发布旧 confirmed 结论
11. Codebase Audit 的 Report 已从文档中心可达，或明确记录待执行的 Docs Refresh handoff
