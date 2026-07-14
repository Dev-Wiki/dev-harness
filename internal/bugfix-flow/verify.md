# 阶段：验证闭环 (verify)

把「我觉得差不多了」收敛成「有证据证明通过」的完成闭环。由 `dev-harness-auto-fix` 在 Step 6 内联调用，**不是独立 skill**。

## 输入要求

至少需要以下输入：

- 已定义的回归测试落点（或本次 bugfix 的最小验证目标）
- 可执行命令或人工验证步骤
- 成功标准与失败标准

## 输出契约

输出必须至少包含：

- **QuickCheck**：最快反馈命令（构建/编译检查）
- **TestCheck**：自动化测试执行命令（平台门控，见下方规则）
- **BugfixCheck**：本次问题专属验证命令
- **FullCheck**：完整回归命令
- **PassCriteria**：通过标准
- **FailureReport**：失败时最少要记录的信息
- **FreshVerificationEvidence**：绑定当前 diff hash 的命令、时间、退出码和关键输出
- **TestSkipReason**：若 TestCheck 被跳过，必须记录跳过原因
- **ManualReviewBoundary**：UI、资源、原生层、打包层中哪些必须人工确认

### 测试执行平台门控

TestCheck 执行前必须判定平台是否可自动执行测试：

| 条件 | 行为 |
|------|------|
| Qt / WPF / WinForms / Win32 C++ 桌面项目 | 执行 TestCommand（`ctest` / `dotnet test` / `vstest.console.exe`） |
| Harmony / Android / iOS | 跳过 TestCheck，`TestSkipReason=device-required` |
| HARNESS.md 中 TestCommand 为 `device-required` 或不存在 | 跳过 TestCheck，记录原因 |

## 顺序化步骤

1. 为 quick / test / bugfix / full 四层分别定义命令
2. 标注每层要证明什么，不得重复堆命令
3. TestCheck 执行前必须过平台门控（桌面端自动执行，移动端跳过）
4. 指定失败时必须记录的输入、输出、日志、错误码
5. 记录 FreshVerificationEvidence（含 test 通过证据和当前 diff hash）
6. 只有满足证据门槛，才允许声称完成
7. 对客户端项目，若修改触及高风险层，必须额外注明人工复核点
8. 最终 diff hash 与 ReviewDiffHash 不一致时，旧审查与验证证据全部失效，必须重新 review 和 verify

## 停止条件

- 没有可执行命令
- 只有「应该通过」这类主观判断
- 没有失败证据记录标准
- quick / test / bugfix / full 没有职责区分
- TestCheck 被跳过但未记录 TestSkipReason
- 客户端项目缺少 quick / test / bugfix / full 的真实命令映射

出现任一条件时，必须停止并补充验证设计。

## 交接边界

- 为 `dev-harness-auto-fix` 提供最终完成证据（含测试通过证据）
- 不负责新增测试用例设计（仅执行已有测试套件）
- 若修改触及 UI、资源、原生层或打包层，必须把人工复核要求传回根流程
- TestCommand 来自 `dev-harness-commands` 的 `harness:test` 映射
