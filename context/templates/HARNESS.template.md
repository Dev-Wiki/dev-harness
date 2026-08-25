# HARNESS — 项目构建与验证契约

本文件是项目构建、验证和执行环境的唯一事实源。
它定义可执行命令、运行条件和验证边界，不替代 `AGENTS.md` 中的行为、安全与修改约束。

## 项目类型
{项目类型或 Unknown}

## 编译与启动问题排查
{编译与启动问题排查结果或 Unknown}

## 自动识别构建命令候选

- **build**: `{命令或 Unknown}`
- **test**: `{命令或 Unknown}`
- **quick**: `{命令或 Unknown}`
- **bugfix**: `{命令或 Unknown}`
- **full**: `{命令或 Unknown}`

## 已确认命令（人工维护）

- **build**: `Unknown`
- **test**: `Unknown`
- **quick**: `Unknown`
- **bugfix**: `Unknown`
- **full**: `Unknown`

复杂项目可为同一用途（Purpose）维护多条已确认记录。每条记录使用以下内部字段：`Purpose / Command / WorkingDirectory / Platform / Variant / Preconditions / DeviceRequirement / Shell / Environment / Evidence / Status`。面向读者时依次理解为用途、命令、工作目录、平台、构建变体、前置条件、设备要求、终端、环境、证据和状态；简单项目继续使用上面的单值字段。

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
