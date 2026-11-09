# HARNESS — dev-harness 仓库验证契约

命令在仓库根目录执行，要求 Python 3 与 Git。验证入口来自 [测试说明](docs/TESTING.md)；本仓库的 Python 源码与 Skill 文档无需单独编译。

## 已确认命令（人工维护）

| 用途 | 命令 | 语义 | 状态 |
|---|---|---|---|
| test | `python3 -m unittest discover -s tests -v` | 完整 Python 回归，包含安装、导出及跨 Skill 契约 | confirmed |
| full | `python3 -m unittest discover -s tests -v` | 完整回归；发布前另行执行差异检查 | confirmed |
| quick | `git diff --check` | 检查新增差异的空白错误 | confirmed |
| bugfix | `python3 -m unittest discover -s tests -v` | 缺陷回归；专项调试可选取已有测试模块 | confirmed |

## 执行边界

- 测试在临时目录构建与安装合成 Skill，不授予修改真实宿主 Skill 目录的权限。
- 安装、导出与发布使用 `install.py`、`release.py`；发布与提交需单独授权。
- 不修改文件编码，不覆盖人工维护的已确认命令或用户已有修改。
