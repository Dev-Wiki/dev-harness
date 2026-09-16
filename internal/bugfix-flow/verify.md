# 阶段：验证结果确认 (verify)

把「我觉得差不多了」转化为「有证据证明通过」的客观结论。由 `dev-harness-auto-fix` 在 Step 6 内联调用，**不是独立 skill**。

## 输入要求

至少需要以下输入：

- 已确定的回归测试位置（或本次 bugfix 的最小验证目标）
- 可执行命令或人工验证步骤
- 成功标准与失败标准
- `ValidationProfile`、最终 `ProfileAssessment` 与变更影响分类

## 输出契约

输出必须至少包含：

- **QuickCheck**：最快反馈命令（构建/编译检查）
- **TestCheck**：自动化测试执行命令（平台门控，见下方规则）
- **BugfixCheck**：本次问题专属验证命令
- **FullCheck**：完整回归命令
- **PassCriteria**：通过标准
- **FailureReport**：失败时至少需要记录的信息
- **FreshVerificationEvidence**：绑定当前 diff hash 的命令、时间、退出码和关键输出
- **VerificationPlan**：结构化记录每次执行的 check、command、status、proves、subsumes、depends_on、diff_hash 和证据位置
- **RepeatReason**：同一 diff 重复相同命令时的枚举化理由
- **TestSkipReason**：若 TestCheck 被跳过，必须记录跳过原因
- **ManualReviewBoundary**：UI、资源、原生层、打包层中哪些必须人工确认

### 测试执行条件

TestCheck 执行前按 HARNESS 中具体命令的 DeviceRequirement 和实际环境判定，平台名称本身不构成跳过理由：

| 条件 | 行为 |
|------|------|
| 命令可本地执行且前置条件具备，包括移动项目的纯逻辑测试 | 执行已确认的 TestCommand |
| 命令依赖设备且设备或模拟器可用 | 执行设备测试 |
| 命令依赖设备且设备确实不可用 | 仅跳过该命令，记录 `TestSkipReason=device-required` 和剩余人工项 |
| 命令缺失或其他环境条件不足 | 记录具体缺口；当前档位要求该验证时不得声称通过，继续执行独立且可用的检查 |

### 结构化覆盖复用

`VerificationPlan` 的每一项至少包含：

```yaml
- id: focused-device-test
  check: BugfixCheck
  command: <实际命令>
  status: passed
  proves:
    - obligation: main-hap-build
      evidence: <日志或产物位置>
    - obligation: device-green
      evidence: <结果位置>
  subsumes:
    QuickCheck: [main-hap-build]
  depends_on: [production, test]
  diff_hash: <当前 hash>
```

`subsumes` 中的每个证明义务必须出现在同项 `proves`，且具有实际 evidence；不能因为命令名称相似就声称覆盖。最终风险评估通过 `required_checks` 声明本轮必须覆盖哪些 check。

## 顺序化步骤

1. 根据 ValidationProfile 和最终风险评估列出 required_checks；`fast` 只要求专项 GREEN 与必要编译，`standard` 补齐受影响的 quick/test/bugfix，`strict` 再增加必要 full/人工验证
2. 先运行专项 GREEN，把实际证明义务和证据写入 VerificationPlan
3. 从已通过项目的 proves 推导 subsumes，只执行尚未覆盖的 required_checks
4. TestCheck 执行前逐条核对设备与环境条件；移动平台同样执行可用的本地测试
5. 每个命令记录输入、输出、日志、错误码、环境、时间和当前 diff hash
6. 相同 command 与 diff_hash 禁止无理由重复；允许的 RepeatReason 为 `environment-recovery`、`wrong-failure-signature`、`device-reset`、`user-requested`、`evidence-expired`、`diff-changed`
7. `fast` 默认预算为一次有效 RED、一次 GREEN、一次未被 GREEN 覆盖的必要编译；预算外执行必须有 RepeatReason
8. review 后若 FinalDiffHash 等于 ReviewDiffHash，且档位为 fast/standard、required_checks 已覆盖，则只做工作区与 hash 终检，不重复执行耗时命令
9. `strict` 按最终评估执行必要 FullCheck；没有必要的 full 义务时不得为了流程形式堆命令
10. 最终 diff hash 与 ReviewDiffHash 不一致时，审查无效；按影响关系只清除受影响证据，再回到 verify/review

## 停止条件

- 没有可执行命令
- 只有「应该通过」这类主观判断
- 没有失败证据记录标准
- 当前 ValidationProfile 要求的 checks 没有职责区分或覆盖证据
- TestCheck 被跳过但未记录 TestSkipReason
- 客户端项目缺少当前 ValidationProfile 所需的真实命令映射；未使用的命令缺失不是停止条件
- `subsumes` 引用了未在同项 proves 中提供证据的义务
- 相同 diff 无 RepeatReason 重复执行相同命令

出现任一条件时，必须停止并补充验证设计。

## 交接边界

- 为 `dev-harness-auto-fix` 提供最终完成证据（含测试通过证据）
- 不负责新增测试用例设计（仅执行已有测试套件）
- 若修改触及 UI、资源、原生层或打包层，必须把人工复核要求传回根流程
- TestCommand 来自 `dev-harness-commands` 的 `harness:test` 映射
