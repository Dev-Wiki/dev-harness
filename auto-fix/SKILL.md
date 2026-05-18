---
name: dev-harness-auto-fix
description: 从 bug 描述/issue URL 到 git commit 的全自动 bugfix 闭环。当用户提供 bug 描述、GitHub/GitLab issue URL 或说"自动修这个 bug"、"auto fix"时使用。前置条件：项目已有 HARNESS.md 定义 build/quick 命令。
---

# dev-harness-auto-fix

从 bug 描述或 issue URL 到 git commit 的全自动修复流水线。

## 前置条件

| 依赖 | 级别 | 缺失时行为 |
|------|------|-----------|
| HARNESS.md（含 build/quick/bugfix/full 命令） | ✅ 强必需 | 停止，要求先执行 dev-harness-commands |
| 内置 bugfix-flow 参考（`references/bugfix-flow/*.md`） | ✅ 强必需 | 随本 skill 安装；缺失则停止并重装 bundle |
| dev-harness-git-workflow | ✅ 强必需 | 停止 |
| 子 Agent / 任务委派能力（Subagent / Task） | ❌ 可选 | 降级为本轮自检，并在完成报告中标记需提交后手动切换模型审查 |
| ARCHITECTURE.md / AGENTS.md | ❌ 推荐 | 告警后降级为 grep 全仓搜索调用链 |

## 适用场景

- 用户说"修这个 bug"并提供 bug 描述或 issue 链接
- 用户说"auto fix"、"自动修复"
- CI 流水线触发自动 bugfix

## 当前优先链路

当前阶段优先打通 **Qt Client (Windows/Linux) -> Shared C++ Core** 链路。

- **Qt**：优先支持 Qt UI / Controller / wrapper 到共享 C++ 底层库的定位、风险分级和验证闭环。Windows 和 Linux 两端共享同一 C++ 代码架构，仅编译命令和打包脚本不同，视为同一优先链路。
- **Harmony**：已具备 auto-fix 基础能力，本阶段不扩张，保持现有 hvigor 验证路径
- **WPF**：维护态，仅严重问题进入修复；复用 Windows Client -> Shared C++ Core 的底层风险规则
- **Android**：暂缓，不进入本阶段 MVP

> ⚠️ **HARD STOP**: 不得为了"多平台通吃"同时扩张 Qt / Harmony / Android / WPF。Qt Linux 属于已有 Qt 优先链路的平台扩展（同一代码架构），不违反此约束。

## 输入要求

至少提供以下之一：

- **GitHub / GitLab issue URL**（自动 fetch 标题 + body）
- **Bug 标题 + 描述 + 复现步骤**（手动输入）

若两者都没有，必须停止并要求用户提供。

## 内联 bugfix 阶段（非独立 skill）

复现 / 定位 / 验证已内联；参考文件位于本 skill 安装目录 `references/bugfix-flow/`。**按需读取**：进入对应 Step 再读，勿预读。

| Step | 参考文件 |
|------|----------|
| 2 repro | `references/bugfix-flow/repro.md` |
| 3 triage | `references/bugfix-flow/triage.md` |
| 6 verify | `references/bugfix-flow/verify.md` |

影响面大或用户要求补回归时，可选读取 `references/bugfix-flow/regression.md`（Step 4 与 Step 6 之间）。

## 顺序化步骤

> ⚠️ **每一步必须完整执行后才能进入下一步，不得跳步。**

### Step 0: 环境就绪检查

```
0.0 读取项目级犯错约束（Top 10 高频规则）：
    _LESSONS="$(git rev-parse --show-toplevel 2>/dev/null)/LESSONS.md"
    → 文件存在 → 按触发次数倒序加载前 10 条活跃规则，视为本次修复的硬约束
               （防止 context flooding；完整规则见 LESSONS.md）
    → 文件不存在 → 跳过，不报错
0.1 检查 HARNESS.md 是否存在且含 build/quick 命令
    → 缺失 → STOP，提示先执行 dev-harness-commands
0.2 检查 ARCHITECTURE.md / AGENTS.md 是否存在
    → 缺失 → 告警：triage 将降级为 grep 全仓搜索，可能较慢
0.3 确认本 skill 目录下 `references/bugfix-flow/{repro,triage,verify}.md` 存在；检查 dev-harness-git-workflow 是否可加载
0.4 检查当前 Agent 环境是否提供任务委派能力（Subagent / Task）：
    → 可用 → review_delegation_available=true
    → 不可用 → review_delegation_available=false，跳过子 Agent / B 模型审查，后续使用本轮自检并标记 ManualReviewRequired=true
0.5 读取 HARNESS.md / AGENTS.md 中的项目画像：
    - 若为 Qt Client (Windows/Linux) + Shared C++ Core → 进入 Qt 优先链路
    - 若为 Harmony → 走既有 Harmony auto-fix 流程
    - 若为 WPF / Win32 → 标记 maintenance-only，触及底层 C++ 时强制人工确认
0.7 输出执行计划（Inline Plan），供用户确认方向后再进入 Step 1：

    ─────────────────────────────────────────
    PLAN — dev-harness-auto-fix
    ─────────────────────────────────────────
    1. 拉取 Bug 上下文（GitHub/GitLab issue URL 或用户描述）
    2. 复现收敛 → 产出 ReproCommand
    3. 根因定位 → 产出 RootCauseCandidate
    4. 生成修复代码 diff
    5. 子 Agent 审查（或本轮自检）
    6. 验证闭环（QuickCheck → TestCheck → BugfixCheck）
    7. 分支创建 + git commit
    8. 完成报告
    链路：<项目画像，如 Qt/Linux 或 Harmony>
    可用状态：<issue URL 是否可用>
    审查委派：<available/降级为自检>
    ─────────────────────────────────────────
    → 如有调整请现在告知，否则直接进入 Step 1。
```

> ⚠️ **HARD STOP**: HARNESS.md 不存在或无 build/quick 命令，不得继续。

### Step 1: 拉取 Bug 上下文

```
1.1 若用户提供了 GitHub / GitLab issue URL：
    1.1.1 fetch issue 页面，提取：标题、body、labels、评论（取前 5 条）
    1.1.2 从内容中识别：现象、复现步骤、环境信息、附带日志
    1.1.3 记录 issue_url 和 issue_title 供后续提交使用
1.2 若用户直接描述 bug：
    1.2.1 按 BUGFIX_GUIDE.md 格式引导用户提供：
          - 标题（一句话）
          - 现象（报错/异常行为/日志）
          - 预期行为
          - 复现步骤
          - 环境信息（版本/系统）
    1.2.2 将用户输入结构化保存为本地 bug 记录
1.3 提取 bug 关键字段：
    - Symptom / Expected / Preconditions / ReproSteps
```

> ⚠️ **HARD STOP**: 无 bug 描述、无现象、无复现步骤 → 停止，提示用户补充信息。

### Step 2: 复现收敛 — repro 阶段

```
2.1 读取本 skill 目录 `references/bugfix-flow/repro.md` 并严格执行（勿预读 triage/verify）
2.2 输入：Step 1 提取的 Symptom + 附件日志
2.3 输出必须包含：
    - 最小复现步骤（ReproSteps）
    - 可执行复现命令（ReproCommand）
    - 还缺什么信息（EvidenceGap）
```

> ⚠️ **HARD STOP**: 无法产出 ReproCommand 或最小复现步骤 → 停止，提示用户补充复现细节。

### Step 3: 根因定位 — triage 阶段

```
3.1 读取 `references/bugfix-flow/triage.md` 并严格执行
3.2 输入：Step 2 的 ReproSteps + 附件日志 + 项目代码
3.3 ARCHITECTURE.md 可用 → 按架构文档追踪调用链
    否则 → grep 全仓搜索关键函数/异常名
3.4 输出必须包含：
    - EntryPoint（入口位置）
    - CallChain（关键调用链）
    - RootCauseCandidates（根因候选，按置信度排序）
    - MissingObservability（缺失的日志/埋点）
    - ClientRiskLayer（QtUI / QtAdapter / SharedCppCore / CppAbiBoundary / Packaging / Unknown）
```

> ⚠️ **HARD STOP**: RootCauseCandidates 为空 → 插入补充日志 → 回到 Step 2 重跑复现。不得在无根因证据时生成修复代码。

**决策门**：多个根因候选时，取最高置信度一个。若置信度均低（< 50%），停止并请求人工确认。

### Step 4: 生成修复代码

```
4.1 基于 RootCauseCandidate + CallChain 确定修改范围
4.2 检查修改范围是否触及高风险区域：
    - 参考 HARNESS.md 中的禁改区域和高风险目录
    - Qt 项目额外检查：Qt signal/slot 跨线程调用、Qt wrapper、Shared C++ Core、导出头文件
    - WPF / Win32 维护态项目额外检查：DllImport / MarshalAs / callback / Win32 API
    - C++/CLI / P/Invoke / ABI / 内核级代码
4.3 若触及高风险区域 → STOP，展示风险分析，要求人工确认后再改
4.4 若为安全区域 → 生成 diff：
    - 遵循项目现有代码风格（从 AGENTS.md / CONVENTIONS.md 获取）
    - 最小改动原则：只修根因，不顺手重构
    - 包含 Null Check 和异常处理
```

> ⚠️ **HARD STOP**: 触及 Shared C++ Core 导出头文件、ABI、marshal、句柄/内存所有权、Qt 跨线程 signal/slot、Win32 消息循环、Qt Linux 平台条件编译 (`Q_OS_LINUX`/`Q_OS_WIN`)、X11/Wayland 依赖 → 必须人工确认。不得盲改。

**Qt -> Shared C++ Core 修复策略**：

| 层级 | 行为 |
|------|------|
| Qt UI / Controller | 可自动修小范围空指针、状态判断、参数校验、调用顺序问题 |
| Qt wrapper / Adapter | 可自动修防御性检查和错误处理；涉及线程切换必须人工确认 |
| Shared C++ Core 内部实现 | 仅允许非 ABI 内部小修；必须说明影响面并跑 C++ 构建/测试 |
| `.h/.hpp` 导出头、回调签名、结构体、枚举、DLL 边界 | 强制停止，要求人工确认 |
| 平台条件编译 (`#ifdef Q_OS_LINUX` / `Q_OS_WIN`) | 涉及 Linux/Windows 分支逻辑修改时必须人工确认；不得删除或合并平台分支 |
| X11 / Wayland / D-Bus / `linuxdeployqt` 依赖 | Linux 显示服务、系统总线、打包依赖收集为高风险区，涉及必须人工确认 |
| 打包、签名、发布链 | 不进入 auto-fix，标记 release-only |

**修复安全网**：

| 条件 | 行为 |
|------|------|
| 改动 ≤ 2 文件 + 不含高风险区 | 自动应用 |
| 改动 > 2 文件或含高风险区 | 展示 diff，请求用户确认 |
| 触及 NativeBridge / Win32 / kernel | 强制停止，输出风险分析 |

### Step 5: Review — 子 Agent 审查优先，缺失时降级

```
5.1 若 review_delegation_available=true，优先使用任务委派能力启动独立审查子 Agent：
    - subagent_type：code-reviewer
    - readonly：true
    - run_in_background：false
5.2 若 review_delegation_available=false：
    - 跳过子 Agent 审查，由当前会话完成本轮自检
    - 设置 ManualReviewRequired=true
5.3 审查 prompt 必须包含：
    - Bug Symptom / Expected / ReproSteps
    - EntryPoint / CallChain / RootCauseCandidate / ClientRiskLayer
    - 本次 git diff 摘要及改动文件清单
    - HARNESS.md / AGENTS.md 中与本次改动相关的禁改区和验证命令
    - 明确要求：只审查，不修改代码，不提交，不运行破坏性命令
5.4 审查必须对照根因逐条检查 diff：
    ① 因果匹配：修复是否直接命中 RootCauseCandidate？
    ② 副作用：改动是否影响其他调用路径？
    ③ 安全合规：无硬编码密钥？输入校验是否完备？
    ④ 异常处理：Null Check 是否补全？边界条件是否覆盖？
    ⑤ 风格一致：命名/缩进/模式是否与周边代码一致？
    ⑥ 最小改动：是否夹杂无关重构或格式化？
5.5 审查输出格式：
    - Verdict：PASS / WARN / FAIL
    - Findings：按严重程度列出，每项含文件、问题、原因、建议
    - ManualReviewRequired：true / false
5.6 审查结果分级：
    - PASS → 进入 Step 6
    - WARN（1-2 个小问题）→ 就地修复 → 重新自检 → PASS 后进入 Step 6
    - FAIL → 回到 Step 4 重新生成修复，最多 2 轮
```

> ⚠️ **HARD STOP**: 审查输出为 FAIL 且 2 轮重试后仍不通过 → 停止，输出审查不通过报告。

### Step 6: 验证闭环 — verify 阶段

```
6.1 读取 `references/bugfix-flow/verify.md` 并严格执行
6.2 从 HARNESS.md 读取 quick / test / bugfix / full 命令
6.3 执行 QuickCheck（编译/构建）：
    → 通过 → 进入 6.4
    → 失败 → 分析失败原因 → 回到 Step 4（最多 3 轮）
6.4 执行 TestCheck（自动化测试，平台门控）：
    6.4.1 判定平台类型：
        - 桌面端（Qt / WPF / Win32）→ 进入 6.4.2
        - 移动端/设备端（Harmony / Android / iOS）→ TestSkipReason=device-required → 跳过，进入 6.5
        - HARNESS.md 无 TestCommand → TestSkipReason=no-test-command → 跳过，进入 6.5
    6.4.2 执行 TestCommand
    6.4.3 TestCheck 结果判定：
        → 所有测试通过 → 进入 6.5
        → 存在失败测试 → 确认是否与本次修改相关
            → 相关 → 回到 Step 4（最多 2 轮）
            → 不相关（预存失败）→ 记录已知失败列表，警告后进入 6.5
6.5 执行 BugfixCheck（本次问题专属验证）：
    → 通过 → 进入 Step 7
    → 失败 → 分析失败原因 → 回到 Step 4（最多 3 轮）
6.6 记录 FreshVerificationEvidence
```

> ⚠️ **HARD STOP**: 3 轮修复重试后 QuickCheck 仍失败 → 停止，输出失败报告。

### Step 7: 分支创建与提交 — 加载 dev-harness-git-workflow

```
7.1 分支创建决策：
    7.1.1 检查用户原始输入是否包含"在当前分支提交"/"不创建新分支"/"直接提交"
        → 是 → skip_branch_create=true，直接进入 7.2
    7.1.2 获取当前分支名，判断是否为主干分支（master / main / HEAD detached）：
        → 是主干分支 → must_create=true
        → 否 → 检查是否符合命名规范 → 符合则跳过创建
    7.1.3 must_create=true 时生成分支名（遵循 Conventional 风格）：
        - Bugfix → `fix/<关键词>`，描述取 Symptom 关键词，小写中划线，≤ 40 字符
          示例：`fix/login-token-null-check`
        - Feature → `feat/<描述>`
    7.1.4 执行 `git checkout -b <分支名>`
7.2 加载 dev-harness-git-workflow（传入 skip_branch_create 标记）
7.3 执行完整门禁流程：
    - 分支命名校验
    - 调试残留检查
    - 生成规范 commit message（type(scope): 描述，可附 issue URL）
    - 执行 git commit
7.4 记录每个仓库的完整修改信息：
    - repo_name / branch_name / commit_sha / commit_title / mr_url
```

## 停止条件

- HARNESS.md 不存在或无 build/quick 命令
- 无 bug 描述或复现步骤
- 无法稳定复现
- RootCauseCandidates 为空且插入日志后仍无法定位
- Review FAIL 且 2 轮审查重试后仍不通过
- 修复触及高风险区域且用户未确认
- 3 轮修复重试后 QuickCheck 仍失败
- TestCheck 失败且确认与修改相关，2 轮修复后仍不通过

满足任一条件时，输出结构化失败报告，不强行提交。

## 交接边界

- 内联 repro → triage → verify 阶段，并消费 dev-harness-git-workflow
- 不负责架构级重构（超出 bugfix 范围的改动需人工决定）
- 不负责 UI 渲染/布局类问题（需截图驱动验证）
- 不负责 Shared C++ Core ABI / marshal / Win32 句柄管理的无确认自动修复
- 仅 diff 级别代码修复，不涉及 CI/CD 流水线变更

## 质量检验

- [ ] Step 0: HARNESS.md 可读取，quick 命令存在？
- [ ] Step 1: bug 上下文完整（标题/现象/复现步骤）？
- [ ] Step 2: 有可执行 ReproCommand？
- [ ] Step 3: RootCauseCandidates 有置信度 > 50% 的候选？
- [ ] Step 4: 修复未触及禁改区域？代码风格符合项目规范？
- [ ] Step 5: Review PASS（或已标记 ManualReviewRequired）？
- [ ] Step 6: QuickCheck 通过？TestCheck 通过/有合理跳过原因？BugfixCheck 通过？
- [ ] Step 7: 分支创建正确？commit 成功？无调试残留？每个仓库信息已记录？

## 完成后告知用户

```text
✅ auto-fix 完成

Bug:  <Symptom 一句话>
根因: <RootCause 一句话，附文件位置>
修复: <文件路径列表，每行一个，含改动摘要>
审查: <delegated-subagent / self-review> ✅（ManualReviewRequired=<true/false>）
测试: TestCheck ✅ / <TestSkipReason>（若有跳过）
验证: QuickCheck ✅ / BugfixCheck ✅

───────────────────────────────────────
📦 涉及仓库
───────────────────────────────────────

| 仓库 | 分支 | Commit | 提交说明 | MR |
|------|------|--------|----------|----|
| <repo_name> | <branch_name> | `<commit_sha 前8位>` | <commit_title> | <MR 链接 / 未创建> |

若创建了 MR，每行 MR 列填写可点击链接；若未创建则填"未创建"。
───────────────────────────────────────
```

**多仓库场景**：表格每行对应一个仓库，并在正文说明各仓库合并顺序建议。