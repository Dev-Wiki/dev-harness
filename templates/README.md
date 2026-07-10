# templates

顶层 `templates/` 不再承载正式模板。

dev-harness 的资源约定是 **skill 自包含**：

- `context/templates/`：上下文初始化模板
- `planning/templates/`：计划看板与任务详情模板
- `auto-fix/references/`：自动修复流程参考资料

新增模板应放到所属 skill 目录下，只有确实跨多个 skill 共享且无法归属时，才考虑新增顶层资源。
