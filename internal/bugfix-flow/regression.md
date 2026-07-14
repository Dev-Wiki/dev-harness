# 阶段：回归测试与样本固化 (regression)

把一次性 bugfix 沉淀成可长期复用的回归 harness。它是写模式的默认门禁，**不是独立 skill**。

## 输入要求

至少需要以下信息：

- 问题现象与预期
- 关键调用链或高风险路径
- 当前项目已有的测试层级或验证方式

## 输出契约

输出必须至少包含：

- **TestLayer**：建议放在哪一层验证
- **CaseLocation**：建议放在哪个目录或模块
- **SampleSource**：样本、fixture、mock、日志回放或输入数据来源
- **AssertionFocus**：必须验证的核心断言
- **FailureSignature**：回归失败与目标 bug 一致的判定签名
- **RegressionRedEvidence**：回归在修复前失败的命令、退出码和关键输出
- **RegressionGreenEvidence**：同一回归在修复后通过的命令、退出码和关键输出
- **RegressionSkipReason**：只能是 `device-required` / `ui-only` / `environment-unavailable` / `no-test-seam`
- **ReuseStrategy**：后续相似 bug 如何复用
- **ClientRiskBoundary**：哪些回归可以自动做，哪些必须人工复核

## 顺序化步骤

1. 判断问题更适合单测、集成、端到端还是命令级验证
2. 选择最便宜且足够证明修复有效的那一层
3. 固化最小样本和断言，先运行并证明修复前失败，保存 RegressionRedEvidence
4. 修复后运行同一用例并证明修复后通过，保存 RegressionGreenEvidence
5. 记录后续可复用方式
6. 对客户端项目，说明是否需要把 UI、资源、原生层、打包层分开回归

## 停止条件

- 无法判断现有项目测试落点
- 无法拿到可复用样本
- 只能写笼统「补测试」，无法明确断言
- 预期行为本身未定义
- 无法给出 quick / bugfix / full 任一层的真实落点

出现上述情况时，必须停下补测试策略输入。

若仅因允许的 RegressionSkipReason 无法自动化，不得伪造 RED/GREEN；记录替代验证和剩余风险，最终状态最多为 `DONE_WITH_CONCERNS`。

## 交接边界

- 向 **verify 阶段** 交付分层验证命令的输入
- 不负责最终运行验证
- 不负责根因分析
- 对客户端高风险区域，必须明确「自动验证」与「人工复核」的分界
