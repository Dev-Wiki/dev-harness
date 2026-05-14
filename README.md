# dev-harness

面向 AI 辅助开发的工程化 skills 包，平台无关，交付形式是一套可安装的 skills bundle。

不是测试框架，不是自动修 bug 的 CLI。它提供的是一套流程约束，用来降低复现、定位、回归和验证的成本——让 AI 修 bug 更稳、更快、更可追溯。

支持 Cursor、Codex CLI、OpenCode、Antigravity。

[English README →](docs/README_EN.md)

---

## Skills

| Skill | 说明 |
|-------|------|
| `dev-harness-pilot` | 入口 — 根据目标路由到对应 skill |
| `dev-harness-context` | 扫描仓库，生成 `README.md`、`ARCHITECTURE.md`、`HARNESS.md`、`AGENTS.md` |
| `dev-harness-commands` | 统一 `build / quick / bugfix / full` 命令入口 |
| `dev-harness-repro` | 复现条件收敛 |
| `dev-harness-triage` | 调用链追踪与根因定位 |
| `dev-harness-regression` | 回归覆盖与测试锚点定义 |
| `dev-harness-verify` | 分层验证命令与完成证据 |
| `dev-harness-git-workflow` | 分支命名校验、commit message 生成、调试残留拦截 |
| `dev-harness-auto-fix` | 全流程自动修复：bug 描述 / issue URL → 根因 → 修复 → 审查 → 提交 |
| `dev-harness-retro` | 任务复盘，提取 AI 犯错规则写入 `LESSONS.md` |

---

## 安装

**macOS / Linux：**

```bash
./install.sh --ide cursor       # 安装到 ~/.cursor
./install.sh --ide codex        # 安装到 ~/.codex
./install.sh --ide opencode     # 安装到 ~/.config/opencode
./install.sh --ide antigravity  # 安装到 ~/.gemini/antigravity
```

**Windows：**

```powershell
.\install.bat --ide cursor
.\install.bat --ide codex
.\install.bat --ide opencode
.\install.bat --ide antigravity
```

**自定义目录：**

```bash
./install.sh --target /path/to/target
```

**导出便携包：**

```bash
./install.sh --export dist
# 生成 dist/dev-harness-vX.Y.Z.zip
```

**只安装某个 skill**（依赖自动补齐）：

```bash
./install.sh --ide cursor --skill dev-harness-context
```

不带任何参数：TTY 环境下进入交互菜单；非交互环境（CI/管道）默认等价于 `--ide cursor`。

---

## 使用

安装后直接在 AI 助手里调用：

```
# 初始化仓库上下文
扫描这个仓库并生成上下文文件

# 修复 bug
自动修这个 bug：登录后点击设置崩溃，复现步骤：1. 登录 2. 点设置
自动修这个 bug https://github.com/owner/repo/issues/123

# 提交代码
帮我提交当前修改

# 任务复盘
总结这次对话的问题
```

**`dev-harness-context` 同时提供最小 CLI：**

```bash
dev-harness-context scan /path/to/repo
dev-harness-context scan /path/to/repo --force
```

行为约定：
- 缺少目标文件时直接写入
- 已有文件内容不同时先输出差异摘要，由用户决定是否覆盖
- `--force` 直接覆盖

---

## 扫描器支持栈

`dev-harness-context` 扫描项目类型并生成约束型 `AGENTS.md`，当前优先支持：

| 栈 | 说明 |
|----|------|
| **WPF** | C# + 可选 C++/CLI native bridge |
| **Harmony** | HarmonyOS / ArkTS |
| **Win32** | C++ / MSBuild |
| **Qt** | Windows + Linux，含 Shared C++ Core 检测 |

其他栈：安全检测 + `Unknown` 回退 + 人工确认提示。

生成的 `AGENTS.md` 包含：
- 调用链候选
- 架构边界规则
- 禁止操作清单
- 高风险文件标注
- 探索建议
- NativeBridge 自动识别候选

---

## 命令语义层

通过 `dev-harness-commands` 在 `HARNESS.md` 中定义四个稳定入口：

| 命令 | 含义 |
|------|------|
| `harness:build` | 完整编译/构建 |
| `harness:quick` | 快速编译检查 |
| `harness:bugfix` | bug 专项验证 |
| `harness:full` | 完整构建 + 全量测试 |

`full` 表示完整构建/依赖图验证，不等于打包。打包/签名/发布物应单独标记为 `package/release-only` 或 CI 打包链。

---

## 仓库结构

```
dev-harness/
├── SKILL.md                    # pilot skill
├── auto-fix/SKILL.md
├── commands/SKILL.md
├── context/
│   ├── SKILL.md
│   ├── cli.py                  # context CLI 入口
│   ├── platform_profiles.py    # 项目类型检测
│   └── repo_walk.py            # 文件遍历工具
├── git-workflow/SKILL.md
├── regression/SKILL.md
├── repro/SKILL.md
├── retro/SKILL.md
├── triage/SKILL.md
├── verify/SKILL.md
├── templates/context/          # AGENTS / HARNESS / README / ARCHITECTURE 模板
├── docs/                       # 使用指南和参考文档
├── tests/                      # unittest 测试套件
├── install.py                  # 跨平台安装/导出脚本
├── install.sh
├── install.bat
├── release.py                  # 构建发布包
└── VERSION
```

---

## V1 / V2 边界

V1 是已有项目的 AI 工程化接入层。目标：上下文初始化、命令语义层、bugfix 基线流程、NativeBridge 风险显式化。

V1 明确不包含：UI 自动化、截图驱动验证、日志/指标/Trace 平台化、多 worktree runtime、自动 PR/review loop、native 层自动修复。

详见 `docs/V1_V2_BOUNDARIES.md` 和 `docs/V2_BACKLOG.md`。

---

## License

MIT
