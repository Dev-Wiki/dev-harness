# dev-harness

**让 AI 修 bug 更稳、更快、可追溯** — 一套给 AI 编码助手的流程约束，不是测试框架，不是自动修 bug 的 CLI。

---

## 解决了什么问题？

你用 Cursor / Claude Code 修过 bug 的话，大概率经历过：

> AI 改了代码 → 编译没过 → 重新改 → 编译过了但没修对 → 再来一轮 → 3 轮后放弃了，"还是我自己看吧"

**问题不在 AI 能力不够，在于缺乏流程约束。** AI 不会主动确认复现条件、不会检查调用链、不会跑分层验证——它直接跳到"写代码"这一步，然后反复打转。

dev-harness 给 AI 加了一套**固定的排查流程**：

```
复现确认 → 可证伪根因 → 回归 RED → 最小修复 → GREEN → 审查 → 最终验证
```

每一步都有明确的停止条件和交付物，AI 必须在当前步完成验证后才能进入下一步。**本质上是把"资深工程师修 bug 的 SOP"交给了 AI。**

---

## 30 秒看懂

安装后，在 AI 助手里直接说人话：

```
# 初始化一个新仓库（让 AI 理解你的项目结构）
扫描这个仓库并生成上下文文件

# 开发一段时间后刷新自动识别区块和规范索引
刷新这个仓库的项目上下文

# 只分析，不改代码
分析这个 bug：登录后点击设置崩溃，使用 analyze 模式

# 修 bug，但不提交
自动修这个 bug：登录后点击设置崩溃，使用 fix 模式

# AI 会按流程走：
#   1. 固定工作区快照 → 2. 确认复现 → 3. 用探测证伪根因
#   → 4. 回归先失败 → 5. 最小修复 → 6. 回归通过
#   → 7. 按当前 diff 审查并最终验证

# 提交代码（自动检查分支命名、拦截调试残留）
帮我提交当前修改

# 复盘（记录这次 AI 犯了什么错，下次自动规避）
总结这次对话的问题
```

AI 会在每一步输出进度和证据，而不是闷头改完告诉你"修好了"。

---

## 安装

支持 **Cursor、Codex CLI、OpenCode、Antigravity**。

**macOS / Linux：**

```bash
./install.sh --ide cursor       # 安装到 Cursor
./install.sh --ide codex        # 安装到 Codex CLI
./install.sh --ide opencode     # 安装到 OpenCode
./install.sh --ide antigravity  # 安装到 Antigravity
```

**Windows：**

```powershell
.\install.bat --ide cursor
.\install.bat --ide codex
.\install.bat --ide opencode
.\install.bat --ide antigravity
```

**其他用法：**

```bash
./install.sh --target /custom/path    # 安装到自定义目录
./install.sh --export dist            # 导出便携包 dev-harness-vX.Y.Z.zip
./install.sh --ide cursor --skill dev-harness-context   # 只装一个 skill
```

---

## Skills 一览（6 个可发现 skill）

| Skill | 干什么用 |
|-------|---------|
| `dev-harness-context` | 初始化上下文文件，并安全刷新自动识别区块与项目规范索引 |
| `dev-harness-planning` | 根据需求文档、原型或参考格式生成 `docs/plan/Dashboard.md` 和 `TaskDetails.md` |
| `dev-harness-commands` | 把 project 里散落的构建/测试脚本统一成 `build / quick / bugfix / full` 四个语义入口 |
| `dev-harness-git-workflow` | 优先遵循项目 Git 规范；缺失时确认并初始化提交、tag、changelog 和发布约定 |
| `dev-harness-auto-fix` | 可选择 analyze / fix / commit / unattended；用运行时约束复现、可证伪根因、RED/GREEN、diff 绑定审查与精确提交 |
| `dev-harness-retro` | 任务复盘，把 AI 这次犯的错记录到 LESSONS.md，下次自动规避 |

> 每个 skill 的模板、references 和脚本跟随该 skill 自己安装，保持资源自包含。

> 复现 / 定位 / 回归 / 验证四阶段已内联为 auto-fix 的参考文件 `references/bugfix-flow/*.md`，不再作为独立 skill 安装。

### Auto-fix 的 dirty worktree 策略

开始任务时，auto-fix 会把已有修改记录进 `WorkspaceSnapshot`。这些修改可以原样保留，不要求 stash 或清空；AI 只维护本轮对话产生的 `AutoFixChangedFiles`。

- 已有脏文件不被修改、暂存或提交。
- 如果目标文件在任务开始时已经脏，流程停止，让用户决定如何合并语义。
- commit 模式只逐文件暂存本轮集合；暂存区含其他内容时报告冲突，不替用户取消暂存。
- HEAD、分支、已有修改或未声明文件发生漂移时停止，避免把别的工作误算成本轮结果。

`auto-fix/runtime.py` 只负责快照、状态机和 diff 证据，不是替代 AI Agent 的一键修复器。

---

## 通用项目识别与增强 Profile

`dev-harness-context` 默认由 AI 基于仓库证据识别语言、框架、架构和验证入口，不要求先为新技术栈增加扫描器分支。确定性代码负责证据收集、结论校验，并按固定 Markdown 标题安全更新章节，不向文档注入管理标记。

当前内置以下增强 Profile，用于离线规则回退和专业风险补充：

| 类型 | 覆盖 |
|------|------|
| **WPF** | C# + 可选 C++/CLI native bridge |
| **Harmony** | ArkTS / HarmonyOS |
| **Win32** | C++ / MSBuild |
| **Qt** | Windows + Linux，含 Shared C++ Core 检测 |
| **Go** | 后端服务，识别 CGO 边界与核心并发逻辑 |
| **Flutter** | 跨端客户端，识别 Platform Channels 与原生代码边界 |
| **Node.js** | 前端工具链与插件（识别跨 Workspace 与生命周期钩子） |
| **FastAPI** | Python 后端服务，识别 ASGI 入口、router/service 调用链与 pytest 验证命令 |

其他项目类型通过 `evidence → AI semantic analysis → validator → safe writer` 主路径识别。只有证据不足的单项标记为 `Unknown`；低置信度结论进入“需人工确认”。

```bash
dev-harness-context evidence /path/to/repo
dev-harness-context scan /path/to/repo --analysis /tmp/context-analysis.json
dev-harness-context refresh /path/to/repo --analysis /tmp/context-analysis.json
```

每个 AI 结论都必须引用仓库内证据并绑定扫描快照指纹；无证据命令、越界路径、无效行号或仓库漂移会在写入前被拒绝。证据明细保留在分析 JSON 中，不复制到 AGENTS/HARNESS；README 的核心模块优先采用 AI 基于源码给出的真实职责。

安装、构建、运行和验证命令按真实语义区分。依赖安装不会冒充 build；Python 服务没有独立编译或打包步骤时，build 明确标记为 `N/A`。

### 项目规范如何组织

`AGENTS.md` 保持为轻量索引：构建与验证指向 `HARNESS.md`，Git、代码风格、发布和 changelog 指向各自的专业文档。详细规则不全部塞入 AGENTS。

- `dev-harness-context` 只识别这些文档并在 `refresh` 时更新索引，不自动创建 Git、代码或发布规范，也不自动创建 `CHANGELOG.md`。
- `dev-harness-git-workflow` 先读取项目或团队已有规范；没有规范时才分析历史、展示候选，并在用户确认后初始化默认规范。
- 代码规范文档只做识别，不根据 lint/formatter 配置自动生成。
- `CHANGELOG.md` 在用户确认初始化或开始首次发布时创建；默认发布分类为 Breaking Changes、Added、Changed、Deprecated、Fixed、Removed、Security，空分类不进入 tag message 或 release notes。

---

## 设计边界

**dev-harness 做了什么：**
- 给 AI 一套可执行的排查 SOP，每一步有证据、有停止条件
- 用 Git 私有状态、工作区快照和 diff hash 把关键边界变成可测试契约
- 让 bugfix 过程可追溯、可验证、可复盘
- 跨平台、跨 IDE，纯 skills bundle，不需要改你的项目工具链

**dev-harness 不做什么：**
- 不提供 UI 自动化测试
- 不做截图驱动验证
- 不搭建日志/指标/Trace 平台
- 不是一键修 bug 的黑盒工具

详见 [V1/V2 边界文档](docs/V1_V2_BOUNDARIES.md)。

---

## License

MIT
