---
name: dev-harness-commands
description: Use when you need to standardize build, test, quick, bugfix, and full verification entry points for an existing client project without rewriting its toolchain
---

# dev-harness-commands

负责把已有客户端项目里的构建、测试和验证入口收敛成统一的 harness 命令约定。

## 适用场景

- 项目已经能构建或测试，但入口分散
- AI 不知道该跑哪个命令验证改动
- 同一个项目里存在多套脚本、多个构建方式或多平台命令
- 需要把项目映射成稳定的 `build / test / quick / bugfix / full` 五类入口

## 输入要求

至少需要以下输入：

- 目标仓库根目录
- 真实存在的构建文件、脚本文件或命令入口
- 当前项目的最小验证方式

若项目没有任何可执行命令，必须明确报缺，不得伪造命令。

## 按需平台指导

- 多平台、设备和 Variant 的映射格式见 [references/platform-command-mapping.md](references/platform-command-mapping.md)。
- Windows shell、原生工具链和控制台编码问题见 [references/windows-shell.md](references/windows-shell.md)。

这些 reference 只提供识别与记录方法，不能代替仓库证据。未加载相关平台时不要读取。

## 输出契约

除非用户明确要求英文，否则新建且未指定语言的文档默认使用简体中文；更新既有文档时沿用其主体语言。标题、表格、说明、验证结论和最终报告应使用中国开发团队常用的自然中文，不做生硬逐字翻译。路径、命令、代码符号、API、协议、产品名、必要缩写和以下内部字段或枚举保持原样；首次出现且容易误解时，可补充简短中文解释。此规则只约束本次新建或更新的内容，不借机翻译无关正文。

简单项目可以继续使用单值字段；多平台、多设备或多 Variant 项目使用命令记录列表。同一个语义入口允许有多条已确认记录，但必须能由 Platform / Variant 唯一选择。

每条命令记录至少包含：

- **用途（Purpose）**：`build / test / quick / bugfix / full`
- **命令（Command）**：真实可执行入口，缺失时为 `Missing`，不适用时为 `N/A`
- **工作目录（WorkingDirectory）**：仓库相对工作目录
- **平台 / 构建变体（Platform / Variant）**：适用平台和构建 Variant；简单项目可省略
- **前置条件（Preconditions）**：工具链、依赖、凭据等前置条件
- **设备要求（DeviceRequirement）**：`none / device-required / manual-only`
- **终端 / 环境（Shell / Environment）**：仅在确有要求时记录
- **证据（Evidence）**：真实文件、配置或成功执行证据
- **状态（Status）**：`candidate / confirmed / missing`

兼容的单值字段仍为 **BuildCommand**、**TestCommand**、**QuickCommand**、**BugfixCommand** 和 **FullCommand**；同时报告 **MissingCommands**。

## 统一命名约定

`harness:build`、`harness:test`、`harness:quick`、`harness:bugfix`、`harness:full` 是稳定语义层，不要求项目重写工具链或采用统一脚本语法。平台标签不能替代 `DeviceRequirement`，打包、签名和发布链不能冒充本地 `full`。

## 顺序化步骤

1. 扫描真实构建入口、测试入口和本地脚本
2. 判断哪些命令可以安全映射为 `build / test / quick / bugfix / full`
3. 把映射结果写入 `HARNESS.md` 的 `## 已确认命令（人工维护）`；不得写入 `harness.detected-commands` 托管候选块
4. 报告缺失项和不可自动推断项
5. 若命令不存在，只能标记 `Unknown`（未知）或 `Missing`（缺失），不得编造

## 停止条件

- 仓库中没有任何可识别构建入口
- 现有命令需要私有环境但无法验证
- 无法判断 quick 与 full 的职责边界
- 输出证据被截断

满足任一条件时，必须停止并说明缺失项。

## 交接边界

- 可作为 `dev-harness-context` 生成 `HARNESS.md` 后的补强能力
- 只维护人工确认命令；不得覆盖 Context 在托管块中生成的自动识别候选
- 为 auto-fix 内联 verify 阶段提供 build / test / quick / bugfix / full 的命令基础
- Codebase Audit 发现验证命令缺口时可路由到本 Skill，但 Audit 不得自行猜测或确认命令
- 不负责 UI 自动化
- 不负责直接改写项目 CI
