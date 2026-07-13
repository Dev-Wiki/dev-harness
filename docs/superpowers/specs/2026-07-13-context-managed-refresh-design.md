# Context Managed Refresh 设计

## 目标

让 `dev-harness-context` 同时支持首次初始化和长期增量刷新。重新扫描仓库时，只更新工具管理的内容，保留团队手工维护的约束、命令、说明、文件编码、BOM 和换行格式。

本阶段只实现 Context 的刷新基础设施，不实现 Git Workflow 的规范发现与初始化。后续 Git Workflow 通过本阶段提供的规范索引更新能力接入。

## 命令语义

### `scan`

```bash
dev-harness-context scan <repo-path>
```

- 面向首次初始化。
- 缺失的 `README.md`、`AGENTS.md`、`ARCHITECTURE.md`、`HARNESS.md` 使用带 managed block 的新模板创建。
- 已有同名文件时不再整文件覆盖，提示用户改用 `refresh`。
- `scan --force` 不得覆盖已有同名文件，避免把初始化命令变成破坏性更新入口。

### `refresh`

```bash
dev-harness-context refresh <repo-path>
```

- 重新扫描仓库并生成最新候选内容。
- 只替换已有 managed block 的正文。
- managed block 之外的内容视为用户所有，逐字节保留。
- 默认展示分块 diff 并逐文件确认。
- 非交互环境只预览并返回状态码 `2`，不写入差异文件。
- `refresh --force` 只强制更新已存在的 managed block，不得整文件覆盖，也不得自动迁移无标记旧文件。

## Managed Block 格式

```markdown
<!-- dev-harness:managed:start id=agents.contract-index version=1 -->
## 项目规范索引

- 构建与验证：`HARNESS.md`
- Git 工作流：Unknown
<!-- dev-harness:managed:end id=agents.contract-index -->
```

约束：

- `id` 在单个文件内唯一且稳定。
- 起止标记必须成对，且禁止嵌套。
- `version` 用于未来迁移 block 结构，不表示项目版本。
- 标记之间由 dev-harness 管理；标记之外由用户管理。
- 发现重复 ID、缺失结束标记、嵌套标记或未知结构版本时停止该文件刷新，不猜测修复。

## 文件所有权划分

### `AGENTS.md`

工具管理：

- 项目规范索引；
- 项目上下文速查；
- 自动识别候选；
- 代码风格锚点。

用户管理：

- 项目人工约束；
- 架构决策；
- 禁止操作；
- 公司或团队规范正文；
- retro 沉淀的规则与知识。

`AGENTS.md` 只保存专项规范索引和必要的强制导航，不复制 Git、代码风格或发布规范全文。

### `HARNESS.md`

工具管理：

- 项目类型；
- 编译环境诊断；
- 自动识别的命令候选；
- 自动识别候选与待确认项。

用户管理：

- 已确认的 build / quick / bugfix / full 命令；
- 人工确认的运行环境；
- 项目特有高风险目录和禁改区域。

自动探测结果与已确认命令冲突时，只展示差异，不覆盖用户确认值。

### `README.md` 与 `ARCHITECTURE.md`

工具只管理可由仓库扫描稳定推导的摘要区块。人工说明、设计背景、决策原因和示例保持在 managed block 之外。

## 旧文件迁移

没有 managed marker 的文件视为 legacy 文件，默认不自动修改。

执行 `refresh` 时：

1. 按已知模板标题解析 legacy 文件；
2. 与最新扫描结果相同的已知章节可标记为安全迁移候选；
3. 内容不同的章节视为人工内容或冲突，不自动归入 managed block；
4. 展示逐章节迁移预览；
5. 只有交互式人工确认后才写入；
6. 冲突章节默认保留为用户所有；用户可以逐项选择采用新生成内容；
7. `--force` 不绕过 legacy 迁移确认。

迁移过程不得复制整份旧文件形成重复章节，也不得静默删除无法识别的内容。

## 编码与换行

写回文件前必须检测并保持：

- UTF-8、UTF-8 BOM、UTF-16 BOM 等可明确识别的编码；
- CRLF 或 LF；
- 文件末尾是否有换行。

编码无法可靠识别、文件包含混合换行或解码失败时，停止该文件更新并报告。不得回退为 UTF-8 重写，也不得用“多数换行”替换混合格式。

新创建文件继续使用 UTF-8 无 BOM 和 LF。

## 更新算法

对每个目标文件执行：

1. 读取原始字节并识别编码、BOM、换行和末尾换行；
2. 解析 managed block，验证 ID、配对、嵌套和版本；
3. 生成按 block ID 组织的新内容；
4. 仅比较并替换同 ID block 正文；
5. 保留标记之外的原始文本；
6. 使用原编码、BOM、换行和末尾换行重新编码；
7. 写入前展示 block 级 diff；
8. 通过临时文件和原子替换写回，避免中途失败损坏文件。

若新模板出现一个旧文件中不存在的 managed block，默认把它列为新增候选，交互确认后插入模板定义的位置。`--force` 可以插入缺失的已知 block，但仍不得修改用户内容。

## 错误与退出码

- `0`：成功，或没有差异；
- `1`：路径、编码、模板或 block 结构错误；
- `2`：存在待确认差异，但当前为非交互模式或用户全部跳过；
- `130`：用户选择 `quit`。

单个文件发生结构或编码错误时不得写入该文件。其他文件可以继续预览，但最终返回 `1` 并列出未更新文件。

## 向后兼容

- 保留现有 `y / n / all / none / quit` 交互选择。
- `refresh --force` 的含义收窄为“强制更新 managed block”。
- 不再允许任何命令整文件覆盖已有上下文文件。
- 仓库自定义模板必须包含合法 managed block；缺失时报告模板不支持 refresh，不静默退回整文件覆盖。

## 测试

至少覆盖：

1. `scan` 创建带 managed block 的四个文件；
2. 再次 `scan` 不覆盖已有文件；
3. `refresh` 更新 managed block 并保留块外人工内容；
4. `refresh --force` 不能覆盖块外内容；
5. 缺失、重复、嵌套 marker 被拒绝；
6. legacy 文件默认不修改并展示迁移预览；
7. legacy 冲突章节保留为用户内容；
8. UTF-8 BOM、UTF-16 BOM、CRLF、LF 和末尾换行保持不变；
9. 混合换行或未知编码停止更新；
10. 非交互刷新存在差异时返回 `2`；
11. 已确认 HARNESS 命令不会被新探测候选覆盖；
12. AGENTS 规范索引保持轻量，不包含专项规范全文。

## 实施约定

本仓库采用单分支开发，直接在当前分支实施，不创建 Git worktree。Context 子系统完成全部验证后单独提交，再开始 Git Workflow 子系统。
