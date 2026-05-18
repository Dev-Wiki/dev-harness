---



## Preamble — 读取项目约束

```bash
_LESSONS="$(git rev-parse --show-toplevel 2>/dev/null)/LESSONS.md"
if [ -f "$_LESSONS" ]; then
  echo "=== LESSONS — 项目 AI 犯错约束（Top 10 高频，完整规则见 LESSONS.md）==="
  _py=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
  if [ -n "$_py" ]; then
    "$_py" - "$_LESSONS" <<'PYEOF'
import sys, re
path = sys.argv[1]
text = open(path, encoding='utf-8').read()
m = re.search(r'## \u6d3b\u8dc3\u89c4\u5219[^\n]*\n((?:.*\n)*?)(?=## |\Z)', text)
rows = [l for l in (m.group(1).splitlines() if m else []) if l.startswith('| L')]
def cnt(r):
    try: return int(r.split('|')[5].strip())
    except: return 0
top = sorted(rows, key=cnt, reverse=True)[:10]
if top:
    print('| ID | \u89c4\u5219 | \u7c7b\u578b | \u89e6\u53d1\u6b21\u6570 | \u6700\u8fd1\u89e6\u53d1 |')
    print('|----|------|------|---------|---------|')
    for r in top: print(r)
    if len(rows) > 10: print(f'...\uff08\u5171 {len(rows)} \u6761\u6d3b\u8dc3\u89c4\u5219\uff09')
else:
    print('(\u6682\u65e0\u6d3b\u8dc3\u89c4\u5219)')
PYEOF
  else
    cat "$_LESSONS"
  fi
  echo "==="
fi
```

## name: dev-harness-pilot
description: MUST USE when the user wants to onboard an existing client project into AI engineering, improve bugfix efficiency, or standardize AI-assisted debugging workflows

# dev-harness-pilot

面向 AI 辅助开发场景的客户端 harness 工程化编排 skill。

## Host dependency

本 skill 依赖宿主平台已经安装以下 superpowers skills：

- `systematic-debugging`
- `verification-before-completion`

如果宿主缺少上述能力，`dev-harness-pilot` 只能执行降级版串行检查；若缺少最基本的读取、搜索、执行命令能力，必须停止并要求用户补齐环境。

## 触发条件

- 用户要求初始化 AI 项目上下文文件
- 用户要求给现有客户端项目做 AI 工程化准入
- 用户要求提升 AI 修 Bug 效率
- 用户要求给项目补 harness、回归测试、bugfix 流程
- 用户要求标准化复现、定位、验证步骤
- 用户提供 ONES bug 链接要求自动修复 → 快速通道：直接加载 `dev-harness-auto-fix`

典型输入：

- “帮这个项目做 harness 工程化”
- “让这个客户端项目先具备 AI 可接入能力”
- “初始化这个仓库的 README / AGENTS / ARCHITECTURE”
- “补齐 bugfix harness”
- “让 AI 修 bug 更快更稳”
- “增加回归测试和验证闭环”
- “自动修这个 bug https://github.com/owner/repo/issues/123”

## 工作流

收到目标后，按以下顺序执行：

0. **自动修复快速通道**：如果用户提供了 ONES bug 链接或明确要求“自动修 bug”，直接加载 `dev-harness-auto-fix`，跳过工程化步骤
1. **上下文初始化分流**：如果目标是做项目准入或生成上下文文件，优先加载 `dev-harness-context`
2. **命令约定分流**：如果仓库缺少统一的 build / quick / bugfix / full 入口，加载 `dev-harness-commands`
3. **问题与目标收敛**：如果目标是 bugfix harness 工程化，明确要提高的是哪个链路，输出影响面和成功标准
4. **加载 `dev-harness-repro`**：收敛最小复现条件、环境约束和复现证据
5. **加载 `dev-harness-triage`**：确认调用链、日志、错误码、根因候选
6. **加载 `dev-harness-regression`**：为高风险路径定义回归测试落点与样例固化方式
7. **加载 `dev-harness-verify`**：定义验证命令分层、通过标准和完成证据
8. **加载 `dev-harness-git-workflow`**：提交前执行分支命名校验、commit message 生成和调试残留拦截

> ⚠️ **每一步必须完整执行后才能进入下一步，不得跳步。**

## 依赖契约

- 根 skill 不直接绑定宿主的某个具体工具名，只声明必须具备的能力。
- 子 skill 优先消费结构化输入；如果上一步输出不完整，必须停下补数据，不得假设缺失信息。
- 若平台支持 subagent，可用于 review loop；否则必须在当前会话中做等效串行审查。

## Runtime capability notes

- If subagents are available, use them for review loops or cross-checks.
- Otherwise run an equivalent serial review before proceeding.
- If the current environment cannot execute verification commands, stop and ask the user to provide a runnable path.
- **Windows 终端**：宿主为 Windows 时，若集成终端不是 **cmd** 或 **PowerShell**（例如 `Shell: bash` 下的 Git Bash），在跑 harness 验证或长命令前必须先提示用户把默认终端改为命令提示符或 PowerShell，否则易出现路径/转义错误或进程卡死；**简体中文环境**下还需对齐控制台 **GBK（936）/ GB2312** 与工具输出，避免中文乱码误导结论；细则见 `dev-harness-commands` 与 `dev-harness-verify`。

---

### 1. 收敛问题与成功标准

如果用户目标是初始化项目上下文文件或做客户端项目准入：

- **加载 `dev-harness-context`**
- 严格基于真实仓库结构和代码生成 `README.md`、`AGENTS.md`、`ARCHITECTURE.md`、`HARNESS.md`
- 无法确认的信息统一标记为 `Unknown`
- 若仓库中已有同名文件且用户未授权覆盖，必须先停止并询问

> ⚠️ **HARD STOP**: 上下文初始化流程不得臆测模块职责、架构模式或依赖关系；证据不足时必须写 `Unknown`。

如果项目缺少统一命令入口：

- **加载 `dev-harness-commands`**
- 把真实存在的构建、快速验证、bugfix 验证、完整验证入口映射为稳定语义层
- 若仓库没有任何可执行命令，必须明确报告 `Missing` 或 `Unknown`

> ⚠️ **HARD STOP**: 不得编造 `build / quick / bugfix / full` 命令；命令不存在时必须停止并要求人工补齐。

如果用户目标是 bugfix harness 工程化，再继续下面的结构化收敛：

首先把用户目标整理成结构化输入：

- **当前痛点**：慢在复现、定位、测试、回归还是上下文装载
- **目标对象**：单仓库、单模块或跨模块链路
- **成功标准**：例如定位时间下降、回归 case 补齐、验证命令固定化
- **现有资产**：已有测试、日志、脚本、CI、文档

> ⚠️ **HARD STOP**: 如果连目标链路都未明确，不得直接进入复现或测试设计，必须先向用户确认范围。

---

### 2. 复现能力收敛

**加载 `dev-harness-repro`**：检查是否已经具备稳定复现条件。

需要得到的结构化结果：

- 最小复现步骤
- 依赖环境和输入数据
- 可执行命令或手动操作说明
- 缺失项和阻塞项

> ⚠️ **HARD STOP**: 若无法判断“如何稳定触发问题”，必须停止后续流程，先补复现条件。

---

### 3. 调用链与可观测性收敛

**加载 `dev-harness-triage`**：沿调用链定位问题入口、关键分支和失败证据。

输出至少包含：

- 入口位置
- 关键调用链
- 现有日志/错误码是否足够
- 根因候选与证据缺口

> ⚠️ **HARD STOP**: 若没有任何可验证证据支撑根因候选，不得直接设计修复或回归测试。

---

### 4. 回归测试与样例固化

**加载 `dev-harness-regression`**：把问题沉淀成长期可复用的回归 harness。

输出至少包含：

- 建议的测试层级（quick / bugfix / full）
- case 放置位置
- 样本来源
- 缺失 harness 的最小补齐路径

> ⚠️ **HARD STOP**: 不得只说“补测试”，必须明确补到哪一层、验证什么输入输出、如何复用。

---

### 5. 验证闭环

**加载 `dev-harness-verify`**：定义完成标准并执行最终验证。

必须明确：

- 哪些命令证明 quick 验证通过
- 哪些命令证明 bugfix 验证通过
- 哪些命令证明 full 回归通过
- 哪些证据允许声称“harness 已生效”

> ⚠️ **HARD STOP**: 没有 fresh verification evidence，不得声称流程建设完成。
