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

| 用途 | 命令 | 状态 |
|---|---|---|
| build | `Unknown` | missing |
| test | `Unknown` | missing |
| quick | `Unknown` | missing |
| bugfix | `Unknown` | missing |
| full | `Unknown` | missing |

本区由 Commands 根据仓库证据维护；Context 不自动确认候选，也不改写已有人工确认区。确认可执行入口后才将状态改为 `confirmed`；未知或缺失入口保持 `missing`，未完成验证的候选为 `candidate`。命令单元格仅包含一段行内代码，前置条件与证据放在独立列或表外说明。

多平台项目可增加工作目录、平台、构建变体、前置条件、设备要求、终端和证据列。交给 Runtime 自动执行前，每个用途须只有一条适用的 `confirmed` 记录，命令工作目录为仓库根，至少确认 test / quick / bugfix / full 中的一项。平台或设备条件尚未唯一确定时，不进入自动执行。

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
