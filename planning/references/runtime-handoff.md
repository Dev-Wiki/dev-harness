# Runtime 自动执行交接

仅在用户选择 `dev-harness-runtime` 自动执行时使用。Planning 负责准备可审查的声明；任务选择、冻结快照、授权、执行与验收仍由 Runtime Core 负责。下面记录当前 `schemaVersion: 1` 的输入格式；安装版本不支持时报告差异，不通过修改 Worker 或跳过检查兼容。

## 就绪条件

- HARNESS 只有一个顶层“已确认命令”二级标题，命令采用带 `用途 / 命令 / 状态` 列的顶层表格。只使用有仓库证据、状态为 `confirmed` 的入口；Unknown、Missing、N/A 与候选均不获得执行资格。Context 刷新不会迁移人工确认区，旧列表需由 Commands 按证据整理。
- 当前 Runtime 只选择唯一用途，不能按 Platform / Variant 列消除重复用途。验证命令从仓库根运行，以 literal argv 解析，不执行 shell 的 `source`、赋值、重定向、管道、`&&` 或展开。需要虚拟环境、额外工具链或依赖时，先核对 Adapter 的实际支持与受控验证环境；命令表本身不授予额外挂载或读取权限，不能只改写命令就宣称环境可用。
- Dashboard 保留准确的 `## 当前工作顺序`、`## 活跃任务` 标题（可有 `1.` 数字前缀）及六列表头。当前工作顺序是从 1 连续编号、以任务链接开头的顶层有序列表；链接指向同 ID 的 `tasks/<ID>.md`。ID 以字母开头，后接字母、数字、点、下划线或连字符，最多 64 字符。
- 活跃表的依赖写精确 `无`，或用顿号分隔的 Task ID / 任务链接；外部条件放入阻塞列。只有精确 `无` 或 `无；后续说明` 表示无阻塞，不能把任意“下一步”说明当作 ready。已完成任务先按归档规则收口，不保留在活跃表。
- 任务保留模板中的独立二级标题，尤其是 `范围`、`影响文件`、`验收标准`、`验证证据`、`未知项与停止条件`；不合并成“范围与影响文件”等自定义标题。每条影响文件列表项包含且只包含一个仓库相对代码路径，目录以 `/` 结尾；不在该列表插入无路径说明项。
- 声明只能覆盖已确认的本任务范围；验证项逐一覆盖所有验收复选框，包括功能文档检查。某命令实际上不能证明某标准时，不能为了填满 `criteria` 把两者关联。必要人工项如实保留；当前 Codex 包没有可信人工验收通道，这类任务不能直接自动派发。

## 任务声明

在任务中增加唯一的 `## Runtime 配置`，内含唯一 `dhr-runtime` JSON 代码块。字段为 `schemaVersion / scope / verification`，不添加其他字段。

- `scope.files`、`scope.directories` 与“影响文件”列表逐项相等；JSON 目录不带尾部 `/`。必要功能文档修改也纳入该列表与范围。
- `scope.archivePath` 指向同一文档根的 `plan/archive/<milestone>/<ID>.md`；该里程碑的 `README.md` 必须已存在，目标归档尚不存在。已有同名归档或重开任务的关闭路径超出安装版本支持时，先对齐版本与归档策略，不能覆盖旧证据。
- `verification.sources` 列出命令依赖但本任务不会修改的既有输入。Core 自动冻结 HARNESS 与当前任务，不重复列入；也不把候选修改文件列为冻结输入。直接脚本、package.json、锁文件、测试配置及间接导入须按实际依赖补齐，不能把空列表当作默认安全设置。
- `verification.commands` 每项包含 `id / purpose / criteria / writableArtifacts`。`purpose` 对应 HARNESS 中唯一已确认用途，完整命令还须作为行内代码出现在任务“验证证据”里；`criteria` 为从 1 开始的验收复选框序号；`writableArtifacts` 仅列验证时需要写入的既有产物目录，不授予 Worker 额外修改范围。
- `verification.manual` 每项包含 `id / criteria / description`；没有人工项才使用空数组。每项验收至少被一个真实有效的命令或人工项覆盖。

完成后用安装包内受信入口的只读 `doctor --project <repo>` 检查项目与计划，保留实际诊断；doctor 不等于能力 probe 或验证通过。缺少声明、命令不兼容或范围无法确认时保留规划缺口，不启动 Run 后再补写冻结输入。

## 最小格式样例

这是用于解析器交接检查的合成项目，仅验收 JavaScript 语法；它不代替真实功能任务的测试、功能文档检查或完整输入清单。复用时用目标项目的真实证据替换，而非将示例命令标记为本项目已确认。

### HARNESS.md

```markdown
# HARNESS

## 已确认命令（人工维护）

| 用途 | 命令 | 状态 |
|---|---|---|
| test | `node scripts/check.mjs` | confirmed |
```

### docs/plan/Dashboard.md

```markdown
# 当前状态看板

## 当前工作顺序

1. [A — 检查模块语法](tasks/A.md)

## 活跃任务

| 任务 | 优先级 | 状态 | 依赖 | 下一步 / 阻塞 | 详情 |
|---|---|---|---|---|---|
| A — 检查模块语法 | 🔴 P0 | 🟢 待执行 | 无 | 无；检查模块语法 | [任务文件](tasks/A.md) |
```

### scripts/check.mjs

```javascript
import { spawnSync } from 'node:child_process';

const result = spawnSync(process.execPath, ['--check', 'src/feature.mjs'], { stdio: 'inherit' });
if (result.error) throw result.error;
process.exitCode = result.status ?? 1;
```

### docs/plan/tasks/A.md

````markdown
# 任务 A：检查模块语法

## 背景与目标

验证合成模块能通过 Node.js 语法检查。

## 执行上下文

- **权威需求**：本任务“背景与目标”。
- **代码入口**：`src/feature.mjs`
- **相关测试**：本任务“验证证据”。
- **必须保持的不变量**：不引入运行时副作用。

## 范围

仅修改合成模块。

## 影响文件

- `src/feature.mjs`

## 功能文档影响

不适用，本项目仅用于合成语法探测，没有对外功能支持声明。

## 验收标准

- [ ] 模块通过 Node.js 语法检查。

## 验证证据

| 验证项 | 命令 / 操作 | 结果 / 证据链接 |
|---|---|---|
| 模块语法 | `node scripts/check.mjs` | 待执行 |

## 未知项与停止条件

不扩大本任务范围；没有未决问题。

## Runtime 配置

```dhr-runtime
{
  "schemaVersion": 1,
  "scope": {
    "files": ["src/feature.mjs"],
    "directories": [],
    "archivePath": "docs/plan/archive/M1/A.md"
  },
  "verification": {
    "sources": ["scripts/check.mjs"],
    "commands": [
      {"id": "syntax", "purpose": "test", "criteria": [1], "writableArtifacts": []}
    ],
    "manual": []
  }
}
```
````

样例还需有效 Git HEAD、`src/feature.mjs`、已存在的 `docs/plan/archive/M1/README.md`，以及真实的 Git 工作流契约（如 `docs/GIT_WORKFLOW.md`）和在 `AGENTS.md` 中指向它的规范链接；默认不提交也不省略该冻结来源。不可由本任务修改的 `scripts/check.mjs` 先作为验证输入冻结，再让 Node 解析候选模块；检查器只依赖 Node 内置模块，没有其他项目输入。不要把候选修改文件直接放进命令 argv：Runtime 会要求现存文件参数也属于冻结来源，而候选文件不能同时声明为不可修改来源。
