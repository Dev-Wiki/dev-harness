# V2_BACKLOG

## 说明

本文件记录 `dev-harness` 在 V1 封板之后，下一阶段明确进入排期池的能力项。

原则：

- 只记录 **超出 V1 边界** 的事项
- 只记录 **值得做但不应继续塞进 V1** 的事项
- 默认按 **P0 / P1 / P2** 粗分优先级

## P0

### 1. NativeBridge 深化

- 自动抽取更细的 `Service -> Interface -> Bridge -> Native` 调用链
- 输出桥接函数、P/Invoke、callback、observer 的关联关系
- 区分 `C++/CLI`、`P/Invoke`、纯 Win32 DLL wrapper 三类桥接模式
- 对 `ABI / marshaling / thread / handle / callback` 风险做更细分类
- 支持把“人工确认结果”回写到 `AGENTS.md` / `HARNESS.md`

### 2. 高风险文件评分

- 不只列高风险候选，还给出优先级或风险等级
- 综合文件体积、引用度、入口属性、bridge 属性、状态机属性进行评分
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
