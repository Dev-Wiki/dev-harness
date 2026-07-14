# 阶段：调用链与可观测性收敛 (triage)

从「可复现问题」收敛到「可验证的根因候选与证据链」。由 `dev-harness-auto-fix` 在 Step 3 内联调用，**不是独立 skill**。

## 输入要求

输入必须来自 **repro 阶段** 或等价结构化结果，至少包含：

- 现象
- 最小复现步骤
- 环境信息

## 输出契约

输出必须至少包含：

- **EntryPoint**：入口函数、接口、事件或任务
- **CallChain**：关键调用链
- **Signals**：现有日志、错误码、trace、指标
- **RootCauseCandidates**：可证伪根因候选列表；每项必须包含下列字段
  - **Claim**：可被否定的根因陈述
  - **Prediction**：Claim 为真时可观察到的结果
  - **Probe**：验证 Prediction 的最小只读探测
  - **Observation**：实际观察及证据位置
  - **Status**：`unverified` / `confirmed` / `rejected`
- **MissingObservability**：缺失的日志、断言、埋点或上下文
- **ClientRiskLayer**：UI、资源、原生层、打包层或 Unknown

## 顺序化步骤

1. 找到入口位置
2. 追踪关键分支与状态变化
3. 为每个 Claim 写 Prediction 和 Probe，先运行最便宜且区分度最高的探测
4. 原样摘要 Observation，并据此把 Status 更新为 confirmed 或 rejected
5. 给出最小可执行的补强建议
6. 对客户端项目，单独标记是否触及高风险层，必要时要求人工确认后再改

## 停止条件

- 入口不明确
- 调用链只有猜测，没有证据
- 关键状态不可见且无法补观测
- 无法区分业务错误和系统错误
- 连续三个候选被拒绝，且没有新的可执行 Probe
- 涉及原生桥接、签名、资源打包或 UI 启动链，但没有足够证据区分具体层级

满足任一条件时，不得直接进入修复设计。

## 交接边界

- 向修复设计（auto-fix Step 4）交付高风险路径和案例落点
- 可建议补日志或断言，但不直接定义最终验证命令
- 不声称根因已确认，除非有明确证据支撑
- 对客户端高风险层只做证据收敛，不得跳过人工确认直接下结论
