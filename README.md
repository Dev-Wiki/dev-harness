# dev-harness

**让 AI 修 bug 更稳、更快、可追溯** — 一套给 AI 编码助手的流程约束，不是测试框架，不是自动修 bug 的 CLI。

---

## 解决了什么问题？

你用 Cursor / Claude Code 修过 bug 的话，大概率经历过：

> AI 改了代码 → 编译没过 → 重新改 → 编译过了但没修对 → 再来一轮 → 3 轮后放弃了，"还是我自己看吧"

**问题不在 AI 能力不够，在于缺乏流程约束。** AI 不会主动确认复现条件、不会检查调用链、不会跑分层验证——它直接跳到"写代码"这一步，然后反复打转。

dev-harness 给 AI 加了一套**固定的排查流程**：

```
复现确认 → 调用链定位 → 根因分析 → 生成修复 → 分层验证 → 规范提交
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

# 修 bug（提供 bug 描述或 GitHub issue 链接）
自动修这个 bug：登录后点击设置崩溃，复现步骤：1. 登录 2. 点设置

# AI 会按流程走：
#   1. 确认能复现 → 2. 追踪调用链 → 3. 定位根因
#   → 4. 生成修复 → 5. 跑验证命令 → 6. 提交代码

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
| `dev-harness-auto-fix` | 全流程自动修复：bug 描述 → 复现 → 定位 → 修复 → 验证 → 提交，内置 `references/bugfix-flow/` |
| `dev-harness-retro` | 任务复盘，把 AI 这次犯的错记录到 LESSONS.md，下次自动规避 |

> 每个 skill 的模板、references 和脚本跟随该 skill 自己安装，保持资源自包含。

> 复现 / 定位 / 回归 / 验证四阶段已内联为 auto-fix 的参考文件 `references/bugfix-flow/*.md`，不再作为独立 skill 安装。

---

## 支持的项目类型

`dev-harness-context` 能自动识别以下项目类型并生成对应的 AGENTS.md 约束：

| 类型 | 覆盖 |
|------|------|
| **WPF** | C# + 可选 C++/CLI native bridge |
| **Harmony** | ArkTS / HarmonyOS |
| **Win32** | C++ / MSBuild |
| **Qt** | Windows + Linux，含 Shared C++ Core 检测 |
| **Go** | 后端服务，识别 CGO 边界与核心并发逻辑 |
| **Flutter** | 跨端客户端，识别 Platform Channels 与原生代码边界 |
| **Node.js** | 前端工具链与插件（识别跨 Workspace 与生命周期钩子） |

其他项目类型会走安全回退路径，标记为 `Unknown` 并提示人工确认。

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
