# Runtime automatic-execution handoff

[English](runtime-handoff.en.md) | [简体中文](runtime-handoff.md)

Use this reference only when the user chooses automatic execution with `dev-harness-runtime`. Planning prepares reviewable declarations; Runtime Core still owns task selection, frozen snapshots, authorization, execution, and acceptance. This documents the current `schemaVersion: 1` input format. If the installed version does not support it, report the mismatch instead of modifying Worker or skipping checks to force compatibility.

## Readiness conditions

- HARNESS has exactly one top-level second-level heading for human-confirmed commands, with a top-level table containing the literal `用途 / 命令 / 状态` columns. Use only repository-evidenced entries whose state is `confirmed`; Unknown, Missing, N/A, and candidates are ineligible. Context refresh does not migrate the human-confirmed area; Commands must organize older lists from evidence.
- Current Runtime selects a unique purpose and cannot resolve duplicate purposes through Platform / Variant columns. Verification commands run from the repository root and are parsed as literal argv, without shell `source`, assignments, redirection, pipes, `&&`, or expansion. If virtual environments, extra toolchains, or dependencies are needed, first check actual Adapter support and the controlled verification environment. A command table grants no additional mount or read permissions; rewriting a command does not establish environment availability.
- Keep the Dashboard's exact `## 当前工作顺序` and `## 活跃任务` headings, optionally preceded by a numeric prefix such as `1.`, and its six-column table headers. The work order is a top-level ordered list numbered consecutively from 1, with each item beginning with a task link to `tasks/<ID>.md` of the same ID. IDs begin with a letter, followed by letters, digits, dots, underscores, or hyphens, with at most 64 characters.
- In the active table, dependencies are exactly `无` (none), or Task IDs / links separated by the Chinese enumeration comma `、`. External conditions belong in the blocker column. Only exact `无` or `无；后续说明` means unblocked; arbitrary next-step prose does not make a task ready. Close completed tasks under the archive rules before removing them from the active table.
- Keep the template's independent second-level task headings, especially `范围`, `影响文件`, `验收标准`, `验证证据`, and `未知项与停止条件` (scope, affected files, acceptance criteria, verification evidence, and unknowns / stop conditions). Do not merge them into custom headings. Every affected-file list item contains exactly one repository-relative code path; directory paths end in `/`. Do not insert explanatory items without a path.
- Declarations cover only the task's confirmed scope. Verification items cover every acceptance checkbox, including capability-documentation checks. Do not associate a command with a criterion it cannot actually prove just to populate `criteria`. Preserve required manual checks honestly. The current Codex package has no trusted manual-acceptance channel, so such tasks cannot be automatically dispatched directly.

## Task declaration

Add exactly one `## Runtime 配置` heading to the task, containing exactly one `dhr-runtime` JSON block. Use only `schemaVersion / scope / verification`, without extra fields.

- `scope.files` and `scope.directories` match the affected-file list item by item. JSON directory entries have no trailing `/`. Include necessary capability-documentation changes in both the list and scope.
- `scope.archivePath` points to `plan/archive/<milestone>/<ID>.md` within the same documentation root. The milestone's `README.md` must already exist and the target archive must not. If an existing archive or a reopened task's closure path exceeds the installed version's support, reconcile the version and archive policy first; do not overwrite old evidence.
- `verification.sources` lists existing inputs the commands depend on but this task will not modify. Core automatically freezes HARNESS and the current task; do not repeat them or list candidate modified files as frozen inputs. Include direct scripts, package.json, lockfiles, test configuration, and indirect imports according to actual dependencies. An empty list is not a safe default.
- Each `verification.commands` item contains `id / purpose / criteria / writableArtifacts`. `purpose` matches HARNESS's unique confirmed purpose. The complete command must also appear as inline code in the task's `验证证据` section. `criteria` contains acceptance-checkbox indices starting at 1. `writableArtifacts` lists only existing artifact directories verification needs to write; it grants Worker no additional modification scope.
- Each `verification.manual` item contains `id / criteria / description`. Use an empty array only if no manual checks exist. At least one valid real command or manual item covers each acceptance criterion.

Afterward, use read-only `doctor --project <repo>` through the installed package's trusted entry point to inspect the project and plan, preserving actual diagnostics. Doctor is neither a capability probe nor passing verification evidence. Missing declarations, incompatible commands, or uncertain scope remain planning gaps; do not start a Run and then fill in frozen inputs.

## Minimal format example

This synthetic project checks parser handoff and accepts JavaScript syntax only. It does not replace real feature-task tests, capability-documentation checks, or a complete input inventory. Replace it with actual evidence from the target project instead of marking sample commands as confirmed for that project.

The following Markdown samples intentionally retain Chinese structural headings, table headers, statuses, and required literals so they remain compatible with the current parser.

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


The sample also needs a valid Git HEAD, `src/feature.mjs`, an existing `docs/plan/archive/M1/README.md`, an actual Git workflow contract such as `docs/GIT_WORKFLOW.md`, and a contract link to it in `AGENTS.md`. The default no-commit policy does not omit that frozen source. Freeze `scripts/check.mjs`, which this task cannot modify, as a verification input before letting Node parse the candidate module. The checker depends only on Node built-ins and has no other project inputs. Do not put candidate modified files directly in the command argv: Runtime requires existing file arguments to be frozen sources too, while a candidate file cannot also be declared an immutable source.
