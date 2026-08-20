# V2_BACKLOG

> 文档角色：本文件是超出当前 V1 / VNext 边界的未来候选池，不是已承诺 Roadmap。
> 当前已支持功能以 [`CAPABILITIES.md`](CAPABILITIES.md) 为准；版本边界与封板标准以 [`V1_V2_BOUNDARIES.md`](V1_V2_BOUNDARIES.md) 为准；v1.8.0 的设计依据见 [`dev-harness VNext 优化与 Codebase Audit 设计方案`](dev-harness%20VNext%20%E4%BC%98%E5%8C%96%E4%B8%8E%20Codebase%20Audit%20%E8%AE%BE%E8%AE%A1%E6%96%B9%E6%A1%88.md)。

## 说明

本文件记录 `dev-harness` 在 V1 封板之后，下一阶段明确进入排期池的能力项。

原则：

- 只记录 **超出 V1 边界** 的事项
- 只记录 **值得做但不应继续塞进 V1** 的事项
- 默认按 **P0 / P1 / P2** 粗分优先级

## 与 VNext 设计方案的关系

VNext 方案中已经落地的 Project Contract、五命令语义、显式 Retro、渐进式 references 和 Codebase Audit V1 不再列入本 Backlog。本文件保留的是它们之上的深化能力，例如更强的 NativeBridge 分析、执行环境隔离、UI/Observability Harness 和自动化 Agent Loop。

其中“命令映射增强”是在当前 Platform / Variant 记录契约上增强自动选择与 preflight；“Runtime Harness”是面向任务执行环境的隔离编排，均不等同于已经交付的 Codebase Audit 状态运行时。

## P0

### 1. NativeBridge 深化

- 自动抽取更细的 `Service -> Interface -> Bridge -> Native` 调用链
- 输出桥接函数、P/Invoke、callback、observer 的关联关系
- 区分 `C++/CLI`、`P/Invoke`、纯 Win32 DLL wrapper 三类桥接模式
- 对 `ABI / marshaling / thread / handle / callback` 风险做更细分类
- 支持把“人工确认结果”回写到 `AGENTS.md` / `HARNESS.md`

### 2. 高风险文件评分

- 不只列高风险候选，还给出优先级或风险等级
- 综合文件体积、被引用次数、是否为入口、是否涉及 bridge 或状态机等因素进行评分
- 区分“禁止盲改”和“可改但需人工确认”

### 3. 命令映射增强

- 在现有 build / test / quick / bugfix / full 与 Platform / Variant 记录契约上，增加更强的自动选择和执行适配
- 支持从现有脚本、解决方案文件、hvigor、cmake 等真实配置中提取证据
- 对复杂设备矩阵和远端构建环境提供可验证的 preflight，而不是扩展为通用 CI/CD 助手

## P1

### 4. Runtime Harness

- 每个任务独立运行目录
- 基于 worktree 的隔离执行
- 启动 / 关闭 / 清理脚本
- 运行状态探针与健康检查

### 5. UI Harness

- 客户端应用启动能力
- 截图抓取
- 最小 smoke 验证
- 基础 UI 自动检查

### 6. Observability Harness

- 本地日志入口标准化
- 日志文件位置约定
- 指标 / Trace 查询入口
- AI 可直接读取的观测层

## P2

### 7. Agent Loop Automation

- 自动 review
- 自动反馈修复循环
- 自愈式修复失败命令
- 文档陈旧检测与 doc gardening

### 8. 项目类型模板扩展

- `templates/<stack>/`
- WPF 专项模板
- Qt 专项模板
- Harmony 专项模板

### 9. 更强的架构分析

- 模块依赖图增强
- 更准确的架构模式识别
- 更细的入口、状态机、回调分发中心识别

## 暂不进入 V2

以下事项当前不建议直接放入 V2 排期：

- 全自动修改 native SDK 核心实现
- 全自动证明 ABI / marshaling 正确性
- 无人工确认的底层 C++ / Win32 自动修复
- 一开始就做全平台通吃的“超级 runtime”

## V2 启动条件

满足以下条件后，再正式开启 V2：

1. V1 已在至少 2~3 个真实客户端项目试点
2. 已收集到真实问题，而不是凭想象补功能
3. 能明确区分哪些是高频痛点，哪些只是“看起来高级”
