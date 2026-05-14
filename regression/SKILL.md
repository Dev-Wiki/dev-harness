---
name: dev-harness-regression
description: Use when you need to turn a bug or high-risk path into durable regression coverage with clear ownership, sample sources, and execution layers
---

# dev-harness-regression

负责把一次性 bugfix 沉淀成可长期复用的回归 harness。



## Preamble — 读取项目约束

```bash
_LESSONS="$(git rev-parse --show-toplevel 2>/dev/null)/LESSONS.md"
if [ -f "$_LESSONS" ]; then
  echo "=== LESSONS（项目历史 AI 犯错规则，视为硬约束）==="
  cat "$_LESSONS"
  echo "==="
fi
```

## 适用场景

- 已确认问题路径，需要补回归测试
- 项目已有测试，但缺少 bugfix 专用层
- 需要给 quick / bugfix / full 三层验证建立落点
- 需要固化失败样本、fixture、mock 或输入数据
- 客户端项目里需要区分逻辑层回归、资源回归、原生桥接回归和打包回归

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
- **ReuseStrategy**：后续相似 bug 如何复用
- **ClientRiskBoundary**：哪些回归可以自动做，哪些必须人工复核

## 顺序化步骤

1. 判断问题更适合单测、集成、端到端还是命令级验证
2. 选择最便宜且足够证明修复有效的那一层
3. 固化最小样本和断言
4. 规划 quick / bugfix / full 的分层归属
5. 记录后续可复用方式
6. 对客户端项目，说明是否需要把 UI、资源、原生层、打包层分开回归

## 停止条件

- 无法判断现有项目测试落点
- 无法拿到可复用样本
- 只能写笼统“补测试”，无法明确断言
- 预期行为本身未定义
- 无法给出 quick / bugfix / full 任一层的真实落点

出现上述情况时，必须停下补测试策略输入。

## 交接边界

- 向 `dev-harness-verify` 交付分层验证命令的输入
- 不负责最终运行验证
- 不负责根因分析
- 对客户端高风险区域，必须明确“自动验证”与“人工复核”的分界
