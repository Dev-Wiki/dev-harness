---
name: dev-harness-verify
description: Use when you need completion criteria, layered verification commands, and evidence rules before claiming a bugfix harness is ready
---

# dev-harness-verify

负责把“我觉得差不多了”收敛成“有证据证明通过”的完成闭环。



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

- 需要定义 quick / test / bugfix / full 分层命令
- 需要在提交前确认验证闭环
- 需要判断当前证据是否足以声称 harness 生效
- 客户端项目里需要明确哪些验证可自动执行，哪些必须人工确认
- 桌面端项目需要自动执行已有测试套件（无设备依赖）

## 输入要求

至少需要以下输入：

- 已定义的回归测试落点
- 可执行命令或人工验证步骤
- 成功标准与失败标准

## Windows 终端前置检查

与 `dev-harness-commands` 中 **「Windows 终端前置检查」** 一致（含 **简体中文 Windows 下 GBK/936 与工具输出编码对齐**，避免中文乱码）。在定义或执行 **QuickCheck / TestCheck / BugfixCheck / FullCheck**、以及收集 fresh verification evidence 所依赖的本地 shell 时，若为 Windows 且集成终端非 cmd/PowerShell，必须先提示用户切换终端后再跑验证，避免挂死或证据无效。

## 输出契约

输出必须至少包含：

- **QuickCheck**：最快反馈命令（构建/编译检查）
- **TestCheck**：自动化测试执行命令（平台门控，见下方规则）
- **BugfixCheck**：本次问题专属验证命令
- **FullCheck**：完整回归命令
- **PassCriteria**：通过标准
- **FailureReport**：失败时最少要记录的信息
- **TestSkipReason**：若 TestCheck 被跳过，必须记录跳过原因
- **ManualReviewBoundary**：UI、资源、原生层、打包层中哪些必须人工确认

### 测试执行平台门控

TestCheck 执行前必须判定平台是否可自动执行测试：

| 条件 | 行为 |
|------|------|
| Qt / WPF / WinForms / Win32 C++ 桌面项目 | 执行 TestCommand（`ctest` / `dotnet test` / `vstest.console.exe`） |
| Harmony / Android / iOS | 跳过 TestCheck，`TestSkipReason=device-required` |
| HARNESS.md 中 TestCommand 为 `device-required` 或不存在 | 跳过 TestCheck，记录原因 |
| 用户明确声明跳过测试 | 跳过 TestCheck，`TestSkipReason=user-requested` |

## 顺序化步骤

1. 为 quick / test / bugfix / full 四层分别定义命令
2. 标注每层要证明什么，不得重复堆命令
3. TestCheck 执行前必须过平台门控（桌面端自动执行，移动端跳过）
4. 指定失败时必须记录的输入、输出、日志、错误码
5. 要求 fresh verification evidence（含 test 通过的证据）
6. 只有满足证据门槛，才允许声称完成
7. 对客户端项目，若修改触及高风险层，必须额外注明人工复核点

## 停止条件

- 没有可执行命令
- 只有"应该通过"这类主观判断
- 没有失败证据记录标准
- quick / test / bugfix / full 没有职责区分
- TestCheck 被跳过但未记录 TestSkipReason
- 客户端项目缺少 quick / test / bugfix / full 的真实命令映射

出现任一条件时，必须停止并补充验证设计。

## 交接边界

- 为根 skill 提供最终完成证据（含测试通过证据）
- 不负责新增测试用例设计（仅执行已有测试套件）
- 不替代 `verification-before-completion`；若宿主有该 skill，必须在结束前显式调用
- 若修改触及 UI、资源、原生层或打包层，必须把人工复核要求传回根流程
- TestCommand 来自 `dev-harness-commands` 的 `harness:test` 映射
