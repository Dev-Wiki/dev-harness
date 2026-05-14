# templates

当前目录只做占位，供后续增强版 harness 使用。

计划中的模板类型：

- 上下文初始化模板
- 客户端项目准入模板
- 测试命令约定模板
- CI 片段模板
- bugfix checklist 模板
- `templates/<stack>/` 形式的语言栈模板

当前版本已提供 `templates/context/` 下的固定上下文模板，并通过 `HARNESS.template.md` 承载客户端项目准入所需的最小运行规则；仍刻意不放任何语言栈专用模板，避免在没有明确约束时过度设计。
