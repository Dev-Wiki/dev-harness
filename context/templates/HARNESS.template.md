<!-- dev-harness:managed:start id=harness.contract version=1 -->
# HARNESS — 项目构建与验证契约

本文件是项目构建、验证和执行环境的唯一事实源。
它定义可执行命令、运行条件和验证边界，不替代 `AGENTS.md` 中的行为、安全与修改约束。
<!-- dev-harness:managed:end id=harness.contract -->

<!-- dev-harness:managed:start id=harness.detected-context version=1 -->
## 项目类型
{项目类型或 Unknown}

## 编译启动诊断
{编译启动诊断或 Unknown}
<!-- dev-harness:managed:end id=harness.detected-context -->

<!-- dev-harness:managed:start id=harness.detected-commands version=1 -->
## 自动识别构建命令候选

- **build**: `{命令或 Unknown}`
- **quick**: `{命令或 Unknown}`
- **bugfix**: `{命令或 Unknown}`
- **full**: `{命令或 Unknown}`
<!-- dev-harness:managed:end id=harness.detected-commands -->

## 已确认命令（人工维护）

- **build**: `Unknown`
- **quick**: `Unknown`
- **bugfix**: `Unknown`
- **full**: `Unknown`

<!-- dev-harness:managed:start id=harness.detected-boundaries version=1 -->
## 高风险目录
- {目录1: 风险说明}
- {目录2: 风险说明}
- ...

## 禁改区域
- {区域1: 原因}
- {区域2: 原因}
- ...

## 自动识别候选
- {候选1: 说明}
- {候选2: 说明}
- ...

## 需人工确认
- {确认项1: 原因}
- {确认项2: 原因}
- ...
<!-- dev-harness:managed:end id=harness.detected-boundaries -->
