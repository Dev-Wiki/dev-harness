# dev-harness

**AI 编码助手的项目工程约束层**：统一项目上下文、文档、规划、验证命令和 Git 流程，并为新功能交付、Bug 修复与大型代码库审计提供可持久化、可验证的工作流。

dev-harness 关注三个跨 Agent、跨会话都需要稳定的问题：

- **Consistency（一致性）**：项目契约不随开发者或 Agent 改变；
- **Evidence（证据）**：完成结论绑定代码、命令、diff、测试或运行证据；
- **Continuity（连续性）**：长任务可以从项目文档和 Git 私有状态恢复。

## 工作方式

dev-harness 不创建一个包办所有信息的中心配置，而是连接项目已有的权威来源：

```text
Project Contract
├── Context：README / ARCHITECTURE / AGENTS
├── Verification：HARNESS.md
├── Documentation：现有 doc/ 或 docs/
├── Current Capabilities：Capability Catalog 或已有同类文档
├── Planning：唯一活跃 Dashboard + tasks/ 分片 + milestone archive
├── Git Policy：项目自己的 Git / release / changelog 规范
├── Retrospective：LESSONS.md
└── Codebase Audit：<docs-root>/audit/ + Git 私有状态
```

准备好 Project Contract 后，根据任务选择两条主路径之一：

```text
新功能交付
需求与验收 → 看板拆分 → 开发 → 测试与验收 → 更新文档和状态 → 提交

代码库审计与修复
Audit → Confirmed Findings → 分类路由 → Auto Fix / Planning / Docs
      → 完整验证 → QA → 最终复核
```

完整的阶段、证据和授权边界见 [端到端工作流](docs/WORKFLOW.md)。

## 30 秒开始

安装后，在 AI 助手中直接描述目标：

```text
# 首次接入
扫描这个仓库并生成项目上下文，再确认验证命令和 Git 规范

# 新功能交付
根据需求生成唯一活跃 Dashboard 和单任务文件，逐项开发、验证并归档

# 整理或同步文档
整理文档结构和 SSOT，只同步代码或成功验证已经证明的事实

# 审计大型存量代码库
基于项目 Context 初始化 codebase audit，并按模块边界分阶段执行

# 修复已知问题
自动修这个 bug：登录后点击设置崩溃，使用 fix 模式

# 显式复盘
retro：总结这次任务，并整理可纳入正式规范的候选结论
```

需要 commit、push、PR、tag、release 或 deploy 时必须分别明确授权。

## 安装

支持 **Cursor、Codex CLI、OpenCode、Antigravity**。

### 方式一：源码＋脚本安装

克隆仓库或下载并解压对应版本的源码归档，进入包含 `install.py` 的项目根目录。安装脚本需要 Python 3。

macOS / Linux：

```bash
./install.sh --ide codex
```

Windows：

```powershell
.\install.bat --ide codex
```

将 `codex` 替换为 `cursor`、`opencode` 或 `antigravity` 即可安装到其他宿主。脚本会构建 Skill 并安装到对应目录；只安装一个 Skill 时会自动补齐依赖。也支持自定义目标或导出便携包：

```bash
./install.sh --ide codex --skill dev-harness-context
./install.sh --target /custom/path
./install.sh --export dist
```

维护者使用 `python release.py` 生成版本 zip。

### 方式二：dist 包直接复制安装

取得 `dist/dev-harness-vX.Y.Z.zip`，或下载发布附件中的同名 Skill 包，解压后将 `skills/` 下的 `dev-harness-*` 文件夹复制到对应目录：

| 工具 | Skill 目录 |
|---|---|
| Cursor | `~/.cursor/skills/` |
| Codex | `~/.codex/skills/` |
| OpenCode | `~/.config/opencode/skills/`；Windows 设置了 APPDATA 时用 `%APPDATA%/opencode/skills/` |
| Antigravity | `~/.gemini/antigravity/skills/` |

`~` 表示用户主目录。目标目录不存在时先创建；使用自定义配置时复制到实际配置的 Skill 目录。以 Codex 为例，复制后的路径应为 `~/.codex/skills/dev-harness-context/SKILL.md`，不要多套一层 `skills/`。

建议复制全部 8 个 Skill。单独安装时，`dev-harness-codebase-audit` 还需要 `dev-harness-context`，`dev-harness-auto-fix` 还需要 `dev-harness-git-workflow`。升级时替换对应的 Skill 文件夹，先保留自己的修改，并保留其他 Skill；完成后重新加载宿主的 Skill 列表。

此方式无需源码和安装脚本。包内的运行脚本、模板和参考资料需要完整保留；Context、Auto Fix 和 Codebase Audit 运行时仍需要 Python 3，Git 工作区操作需要 Git。包内 `README.md` 提供独立安装说明，源码和仓库维护文档由对应版本的源码归档提供。

v1.11.8 将发布包收敛为可直接使用的 Skill 集合，并明确以上两种安装方式。从 v1.11.7 之前的版本升级时，旧版 Auto Fix 状态仍需重新验证与审查；迁移限制见 [变更日志](CHANGELOG.md) 和 [Bugfix 指南](docs/BUGFIX_GUIDE.md)。

## Skills 一览（8 个可发现 Skill）

### Project Contract / Governance

| Skill | 职责 |
|---|---|
| `dev-harness-context` | 初始化或刷新项目上下文和规范索引 |
| `dev-harness-docs` | 整理文档根、导航、SSOT、Capability Catalog、归档和已验证事实 |
| `dev-harness-planning` | 生成单一权威 Dashboard、带就绪门禁的可交接任务执行包和里程碑归档，并检查计划漂移 |
| `dev-harness-commands` | 将真实命令映射为 `build / test / quick / bugfix / full` |
| `dev-harness-git-workflow` | 遵循或初始化 Git、提交、tag、changelog 和发布约定 |
| `dev-harness-retro` | 仅在显式触发时沉淀 FACT / POLICY / LESSON 候选结论 |

### Evidence-driven Long-running Workflows

| Skill | 职责 |
|---|---|
| `dev-harness-auto-fix` | 以复现、根因假设、RED/GREEN 和差异证据修复已知问题，并按 `fast / standard / strict` 风险档位裁剪验证 |
| `dev-harness-codebase-audit` | 分阶段审计大型代码库，批量持久化证据、生成紧凑文档并执行跨模块复核 |

每个 Skill 的模板、references 和脚本均自包含。跨 Skill 自动编排由独立的 [`dev-harness-dsh`](https://github.com/Dev-Wiki/dev-harness-dsh) 项目规划；本仓库保持纯 Skills Bundle。

## 权威边界

| 变化中的事实 | 权威维护位置 |
|---|---|
| 项目上下文与根文档托管区块 | Context |
| 已确认验证命令 | `HARNESS.md` |
| 文档根、导航、SSOT 与全局归档治理 | Docs；`plan/` 内任务生命周期与归档内容由 Planning 负责 |
| 当前已支持功能 | Capability Catalog 或已有同类文档 |
| 活动任务状态与实施细节 | 状态只在 `<docs-root>/plan/Dashboard.md`；实施细节在 `tasks/` |
| Git、tag、release 与 changelog | 项目 Git 规范与 `CHANGELOG.md` |
| Audit Finding 与证据 | `<docs-root>/audit/` 和对应 Git 私有状态 |

计划不代表当前已经支持，提交历史也不替代功能清单；其他文档应链接到权威来源，而不是复制状态。

## 文档入口

- [文档中心](docs/README.md)：按使用、维护、范围与设计记录组织文档。
- [端到端工作流](docs/WORKFLOW.md)：新功能交付与代码审计 / 修复的推荐顺序。
- [产品功能清单](docs/CAPABILITIES.md)：当前已支持功能及其验证证据。
- [客户端项目接入](docs/CLIENT_PROJECT_ONBOARDING.md)：初始化项目契约。
- [测试说明](docs/TESTING.md)：本仓库验证入口与证据要求。
- [Git 工作流](docs/GIT_WORKFLOW.md)：本仓库提交与发布规则。
- [版本边界](docs/V1_V2_BOUNDARIES.md) 与 [V2 Backlog](docs/V2_BACKLOG.md)：当前承诺和未来候选。

## 设计边界

dev-harness 不以覆盖完整 SDLC 或堆叠通用开发教程为目标，也不替代项目工具链、UI 自动化平台、可观测平台或发布系统。它负责让上下文、计划、验证、文档、Git 边界和长期证据在不同 Agent 之间保持一致。

## License

MIT
