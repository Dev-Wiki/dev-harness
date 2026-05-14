# CHANGELOG

## v1.0.0 — 2026-05-14

首个正式版本发布。

### Skills

- `dev-harness-pilot` — 入口 skill，根据目标路由到对应 skill
- `dev-harness-context` — 扫描仓库，生成 `README.md`、`ARCHITECTURE.md`、`HARNESS.md`、`AGENTS.md`
- `dev-harness-commands` — 统一 `build / quick / bugfix / full` 命令入口
- `dev-harness-repro` — 复现条件收敛
- `dev-harness-triage` — 调用链追踪与根因定位
- `dev-harness-regression` — 回归覆盖与测试锚点定义
- `dev-harness-verify` — 分层验证命令与完成证据
- `dev-harness-git-workflow` — 分支命名校验、commit message 生成、调试残留拦截（Conventional Commits 规范）
- `dev-harness-auto-fix` — 全流程自动修复：bug 描述 / issue URL → 根因 → 修复 → 审查 → 提交
- `dev-harness-retro` — 任务复盘，提取 AI 犯错规则写入 `LESSONS.md`

### 扫描器

- `context/cli.py`：项目类型检测使用通配模式和动态命名空间推断，不依赖特定项目名称
- `platform_profiles.py`：Harmony 打包脚本检测使用 `buildScript/*_package.py` glob
- 当前优先支持栈：WPF、Harmony、Win32、Qt（含 Shared C++ Core）

### 工程基础

- `VERSION` 文件作为版本单一事实源
- `install.py` 安装/导出时自动向每个 SKILL.md frontmatter 注入 `bundle_version`
- `release.py` / `release.bat` / `release.sh`：一键打包 `dev-harness-vX.Y.Z.zip`
- 支持平台：Cursor、Codex CLI、OpenCode、Antigravity
- 测试：14 个 unittest，覆盖扫描器核心路径

### 文档

- `docs/HARNESS_GUIDE.md`：通用使用指南
- `docs/GIT_WORKFLOW.md`：Conventional Commits 分支与提交规范参考
