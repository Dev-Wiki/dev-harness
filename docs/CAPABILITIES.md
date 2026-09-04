# dev-harness 产品功能清单

> 本文件是“当前已支持功能”的权威维护文档，只记录有代码、契约或自动化测试证据的可独立验证功能。版本边界、非目标和封板标准见 [V1 / VNext 与 V2 边界](V1_V2_BOUNDARIES.md)，未来候选见 [V2 Backlog](V2_BACKLOG.md)，发布变化见根目录 [`CHANGELOG.md`](../CHANGELOG.md)。

## 汇总

仓库 [`VERSION`](../VERSION)、[`CHANGELOG.md`](../CHANGELOG.md) 当前版本条目与最新 Git 标签均为 `v1.11.3`。每次修改清单后必须根据下表重新统计；“待确认”不计入总数。

| 版本范围 | 已支持 | 部分支持 | 试验性 | 已弃用 |
|---|---:|---:|---:|---:|
| 当前开发版本（v1.11.3） | 33 | 0 | 0 | 0 |
| 最新标签版本（v1.11.3） | 33 | 0 | 0 | 0 |

## 当前已支持功能

### 安装与分发

| ID | 功能说明 | 支持状态 | 适用范围 | 版本归属 | 验证方式 | 证据 | 详情 |
|---|---|---|---|---|---|---|---|
| INS-001 | 安装全部或指定 Skill，支持 Cursor、Codex、OpenCode、Antigravity、交互选择和自定义目标，并展开 Skill 依赖 | 已支持 | Python 3；POSIX / Windows wrapper | 已发布：v1.10.0 | 自动化测试 + 代码证据 | `tests/test_install.py:15-22,101-204`；`install.py:182-217,229-295,432-511`；`install.bat:1-32` | [安装说明](../README.md#安装) |
| INS-002 | 导出便携 `bundle/`，并生成包含源码、安装器、Skill 自包含资源和 CHANGELOG 的版本 zip | 已支持 | 维护者发布与离线分发 | 已发布：v1.10.0 | 自动化测试 + 代码证据 | `tests/test_install.py:242-284`；`install.py:447-504`；`release.py:45-82` | [安装与发布入口](../README.md#安装) |

### 项目上下文

| ID | 功能说明 | 支持状态 | 适用范围 | 版本归属 | 验证方式 | 证据 | 详情 |
|---|---|---|---|---|---|---|---|
| CTX-001 | `evidence` 输出通用仓库清单、分析字段契约、截断状态和快照指纹 | 已支持 | 可读取的本地仓库，不限内置 Profile | 已发布：v1.10.0 | 自动化测试 + 契约证据 | `tests/test_context_cli.py:750-764`；`context/SKILL.md:14-20,70-79,102-118` | [Context 契约](../context/SKILL.md) |
| CTX-002 | `scan` 只创建缺失的 README、AGENTS、ARCHITECTURE、HARNESS，不覆盖已有同名文件 | 已支持 | 首次初始化项目 | 已发布：v1.10.0 | 自动化测试 + 代码证据 | `tests/test_context_cli.py:175-225,453-482`；`tests/test_install.py:139-204` | [Context 契约](../context/SKILL.md) |
| CTX-003 | `refresh` 只更新固定 Markdown 章节，保留人工内容、编码、换行和权限，结构异常时 fail closed | 已支持 | 固定标题结构有效的已初始化项目 | 已发布：v1.10.0 | 自动化测试 | `tests/test_context_cli.py:291-451`；`tests/test_managed_context.py:21-150` | [Context 契约](../context/SKILL.md) |
| CTX-004 | 接受绑定仓库证据、置信度和 fingerprint 的 AI 语义分析，支持未知框架，并拒绝越界路径、无证据命令和漂移分析 | 已支持 | 通用仓库；内置 Profile 为增强与离线回退 | 已发布：v1.10.0 | 自动化测试 + 契约证据 | `tests/test_context_cli.py:609-748`；`tests/test_semantic_analysis.py:42-176` | [Context 契约](../context/SKILL.md) |

### 文档治理

| ID | 功能说明 | 支持状态 | 适用范围 | 版本归属 | 验证方式 | 证据 | 详情 |
|---|---|---|---|---|---|---|---|
| DOC-001 | 只读审计重复所有权、孤儿文档、导航和链接问题 | 已支持 | 已有或待建立文档体系的仓库 | 已发布：v1.10.0 | 契约测试 | `tests/test_docs_contract.py:9-21`；`dev-harness-docs/SKILL.md:23-59` | [Docs 契约](../dev-harness-docs/SKILL.md) |
| DOC-002 | 初始化最小文档中心和必要维护规则，同时解析并复用唯一 `doc/` 或 `docs/` 根 | 已支持 | 尚无完整文档中心的仓库 | 已发布：v1.10.0 | 契约测试 + 资源安装测试 | `tests/test_docs_contract.py:9-21`；`tests/test_install.py:71-87` | [Docs 契约](../dev-harness-docs/SKILL.md) |
| DOC-003 | 组织或刷新索引、导航、SSOT、放置规则和 Audit `Report.md` 入口，不复制深层正文 | 已支持 | 既有文档体系；Audit 导航受 Snapshot 漂移边界约束 | 已发布：v1.10.0 | 契约测试 | `tests/test_docs_contract.py:140-151`；`dev-harness-docs/SKILL.md:61-80,167-197` | [Docs 契约](../dev-harness-docs/SKILL.md) |
| DOC-004 | 在确认精确 move map 与链接影响后，归档已完成或被替代文档并维护当前权威入口 | 已支持 | 非活跃、已完成或被替代的文档 | 已发布：v1.10.0 | 契约证据 | `dev-harness-docs/SKILL.md:23-34,130-141,167-183,219-231` | [Docs 契约](../dev-harness-docs/SKILL.md) |
| DOC-005 | 把代码、配置或成功验证证明的可复用事实按最小计划同步到既有 SSOT，未验证项进入“待确认” | 已支持 | 代码或验证变化后的事实同步 | 已发布：v1.10.0 | 契约证据 | `dev-harness-docs/SKILL.md:143-165,208-231` | [Docs 契约](../dev-harness-docs/SKILL.md) |
| DOC-006 | 条件性建立或维护 Capability Catalog，以稳定 ID 分离支持状态、适用范围、版本归属、验证方式和证据 | 已支持 | 当前功能分散、有适用差异或无法可靠统计的项目 | 已发布：v1.10.0 | 契约测试 | `tests/test_docs_contract.py:37-138`；`dev-harness-docs/SKILL.md:82-128` | [Docs 契约](../dev-harness-docs/SKILL.md) |

### 项目规划

| ID | 功能说明 | 支持状态 | 适用范围 | 版本归属 | 验证方式 | 证据 | 详情 |
|---|---|---|---|---|---|---|---|
| PLN-001 | 从需求、PRD、原型或参考格式生成同一文档根下唯一活跃 Dashboard 和单任务详情 | 已支持 | 项目、版本或里程碑级规划 | 已发布：v1.11.1 | 契约测试 + 资源安装测试 | `tests/test_docs_contract.py`；`tests/test_install.py` | [Planning 契约](../planning/SKILL.md) |
| PLN-002 | 刷新计划时按 Task ID 合并，保留有效 ID、本地约定和有证据的完成状态，并通过临时快照识别读取漂移 | 已支持 | 已有计划，包括单体 TaskDetails 迁移 | 已发布：v1.11.1 | 契约测试 | `tests/test_planning_contract.py`；`planning/SKILL.md` | [Planning 契约](../planning/SKILL.md) |
| PLN-003 | 活跃任务按 Task ID 分片，跨任务可变字段只在 Dashboard 维护；完成任务进入里程碑归档并退出默认读取路径 | 已支持 | 长期演进或大型计划 | 已发布：v1.11.1 | 契约测试 + 模板安装测试 | `tests/test_planning_contract.py`；`tests/test_install.py` | [Planning 契约](../planning/SKILL.md) |
| PLN-004 | 用 `规划中` 与 `待执行` 区分任务包完整性，并在单任务执行包中固定权威需求、代码与测试入口、不变量、已确认决策和停止条件 | 已支持 | 规划与执行分属不同对话或外部工作流的项目 | 已发布：v1.11.3 | 契约测试 + 模板安装测试 | `tests/test_planning_contract.py`；`tests/test_install.py`；`planning/templates/Task.template.md` | [Planning 契约](../planning/SKILL.md) |

### 验证命令

| ID | 功能说明 | 支持状态 | 适用范围 | 版本归属 | 验证方式 | 证据 | 详情 |
|---|---|---|---|---|---|---|---|
| CMD-001 | 把仓库真实命令映射为稳定的 `build / test / quick / bugfix / full` 语义入口，支持 Platform / Variant 多记录并写入 HARNESS 人工确认区 | 已支持 | 已存在真实构建或验证入口的项目 | 已发布：v1.10.0 | 契约测试 | `tests/test_vnext_contract.py:58-76`；`commands/SKILL.md:34-62` | [Commands 契约](../commands/SKILL.md) |

### Git 工作流

| ID | 功能说明 | 支持状态 | 适用范围 | 版本归属 | 验证方式 | 证据 | 详情 |
|---|---|---|---|---|---|---|---|
| GIT-001 | 优先发现并遵循仓库自有 Git / commit / tag / release / changelog 规范；缺失时提出候选，显式确认后初始化默认规范 | 已支持 | Git 仓库；初始化不等于授权 Git 写操作 | 已发布：v1.10.0 | 契约测试 | `tests/test_git_workflow_contract.py:32-46`；`git-workflow/SKILL.md:20-87` | [Git Workflow 契约](../git-workflow/SKILL.md) |
| GIT-002 | 按本轮明确维护文件精确暂存和提交，检测 staged scope 冲突、敏感文件、调试残留和无关变更 | 已支持 | 用户明确授权 commit 的工作流 | 已发布：v1.10.0 | 契约测试 | `tests/test_auto_fix_contract.py:89-93`；`git-workflow/SKILL.md:89-100` | [Git Workflow 契约](../git-workflow/SKILL.md) |
| GIT-003 | 从匹配版本 CHANGELOG 生成 annotated tag annotation 和 release notes，按约定顺序省略空分类，缺失版本时停止 | 已支持 | 用户明确授权 tag / release message 的仓库 | 已发布：v1.10.0 | 契约测试 | `tests/test_git_workflow_contract.py:21-54`；`git-workflow/SKILL.md:101-125` | [Git Workflow 契约](../git-workflow/SKILL.md) |

### Auto Fix

| ID | 功能说明 | 支持状态 | 适用范围 | 版本归属 | 验证方式 | 证据 | 详情 |
|---|---|---|---|---|---|---|---|
| FIX-001 | `analyze` 模式执行只读复现、探测、可证伪根因分析和报告，运行时阻止进入写阶段 | 已支持 | 只分析、不修改的 Bug 调查 | 已发布：v1.10.0 | 运行时测试 + 契约测试 | `tests/test_auto_fix_runtime.py:161-172`；`tests/test_auto_fix_contract.py:26-37` | [Auto Fix 契约](../auto-fix/SKILL.md) |
| FIX-002 | `fix` 模式要求 confirmed 假设、修复前 RED、最小实现、修复后 GREEN、diff-bound review 和 final verify | 已支持 | 可建立复现与项目验证入口的 Bug | 已发布：v1.10.0 | 运行时测试 + 契约测试 | `tests/test_auto_fix_runtime.py:174-227`；`tests/test_auto_fix_contract.py:51-87` | [Auto Fix 契约](../auto-fix/SKILL.md) |
| FIX-003 | `commit` / `unattended` 可在授权范围内精确提交；`fix` / `analyze` 禁止提交，push / PR / release 仍需独立授权 | 已支持 | 明确授权提交的 Auto Fix Run | 已发布：v1.10.0 | 运行时测试 + 契约测试 | `tests/test_auto_fix_runtime.py:229-237`；`auto-fix/SKILL.md:10-21,133-135` | [Auto Fix 契约](../auto-fix/SKILL.md) |
| FIX-004 | WorkspaceSnapshot、Git 私有原子状态、断点恢复、变更集合和 diff hash 防止 dirty worktree、HEAD、分支及未声明文件漂移 | 已支持 | Git 仓库中的长流程修复 | 已发布：v1.10.0 | 运行时测试 | `tests/test_auto_fix_runtime.py:55-159,188-251`；`auto-fix/SKILL.md:42-71` | [Auto Fix 契约](../auto-fix/SKILL.md) |
| FIX-005 | 授权 Mode 与 `fast / standard / strict` 验证档位正交；按文件影响使证据失效、从证明义务复用验证、限制无理由重复，并对状态写入权限失败快速终止 | 已支持 | 已知问题的低、中、高风险修复；旧状态与风险不明场景 fail-safe | 已发布：v1.11.2 | 运行时测试 + 契约测试 | `tests/test_auto_fix_runtime.py`；`tests/test_auto_fix_contract.py`；`auto-fix/runtime.py`；`auto-fix/SKILL.md` | [Auto Fix 契约](../auto-fix/SKILL.md) |

### Codebase Audit

| ID | 功能说明 | 支持状态 | 适用范围 | 版本归属 | 验证方式 | 证据 | 详情 |
|---|---|---|---|---|---|---|---|
| AUD-001 | 初始化 Git 私有 AuditSnapshot，并通过 checkpoint、status、resume 跨会话恢复任务和 Finding 状态 | 已支持 | 用户拥有或明确授权的 Git 仓库，已有唯一 docs root 与 Canonical Context | 已发布：v1.10.0 | 运行时测试 | `tests/test_codebase_audit_runtime.py:83-109,164-236` | [Audit 契约](../codebase-audit/SKILL.md) |
| AUD-002 | 基于 Context 动态分区并逐任务生成 Dashboard、Task、Result、Findings 和 Report | 已支持 | 大型或跨模块存量仓库；工程质量审计，不含 offensive security | 已发布：v1.10.0 | 契约测试 | `tests/test_vnext_contract.py:78-127`；`codebase-audit/SKILL.md:10-26,80-108` | [Audit 契约](../codebase-audit/SKILL.md) |
| AUD-003 | Finding 支持 candidate、needs-verification、confirmed、rejected、stale、resolved，confirmed 必须绑定完整证据和当前 Snapshot | 已支持 | Audit Finding Registry | 已发布：v1.10.0 | 运行时测试 | `tests/test_codebase_audit_runtime.py:296-352` | [Finding 契约](../codebase-audit/references/finding-contract.md) |
| AUD-004 | 完成前强制 Cross-module Reconciliation，执行 checkpoint、去重、矛盾处理和完整调用链复核 | 已支持 | 所有 Audit Run，包括小项目或零 Finding | 已发布：v1.10.0 | 运行时测试 + 契约测试 | `tests/test_codebase_audit_runtime.py:248-271`；`tests/test_vnext_contract.py:129-152` | [跨模块复核](../codebase-audit/references/cross-module-review.md) |
| AUD-005 | HEAD、分支、已有 dirty 内容、Context 或业务源码漂移时 fail closed，并限制输出到 `<docs-root>/audit/**` | 已支持 | 活跃或恢复中的 Audit Run | 已发布：v1.10.0 | 运行时测试 | `tests/test_codebase_audit_runtime.py:121-196,275-294,354-376` | [Audit 契约](../codebase-audit/SKILL.md) |
| AUD-006 | 默认生成自然中文审计产物，显式要求时生成全英文；显示语言不改变内部状态和 Evidence fingerprint | 已支持 | Audit 文档输出 | 已发布：v1.10.0 | 契约测试 | `tests/test_vnext_contract.py:154-183`；`codebase-audit/SKILL.md:28-47` | [Audit 契约](../codebase-audit/SKILL.md) |
| AUD-007 | 检查稳定入口 `audit/Report.md` 的文档可发现性，记录 `linked` 或 `docs-refresh-required`，缺入口时生成精确 Docs handoff | 已支持 | 已解析 docs root 的 Audit Run | 已发布：v1.10.0 | 契约测试 | `tests/test_vnext_contract.py:78-104`；`tests/test_docs_contract.py:140-151` | [Audit 契约](../codebase-audit/SKILL.md) |

### 显式复盘

| ID | 功能说明 | 支持状态 | 适用范围 | 版本归属 | 验证方式 | 证据 | 详情 |
|---|---|---|---|---|---|---|---|
| RET-001 | 只在用户显式要求时复盘，把条目分类为 FACT / POLICY / LESSON，以稳定 `Rnnn` ID 去重并维护 Promotion Candidates | 已支持 | 明确的 retro、复盘、总结并沉淀请求 | 已发布：v1.10.0 | 契约测试 + 安装测试 | `tests/test_vnext_contract.py:14-40`；`tests/test_install.py:24-34` | [Retro 契约](../retro/SKILL.md) |

## 待确认

以下候选尚无足够实现或自动化测试证据，不计入已支持总数：

| ID | 功能分类 | 待确认功能 | 已知适用范围 | 缺少的证据 | 线索来源 |
|---|---|---|---|---|---|
| CAND-001 | Auto Fix | 单个 Auto Fix Run 原生编排多个 Git 仓库，并输出每仓库分支 / commit 结果 | 多仓库项目 | Skill、runtime 和自动化测试中的仓库集合、跨仓库快照及提交边界 | 旧版使用指南中的声明 |
| CAND-002 | Auto Fix | 不依赖宿主 Connector 或用户输入，直接抓取远端 GitHub / GitLab Issue | 远端 Issue 输入 | 固定 Connector、runtime 实现或集成测试 | `auto-fix/SKILL.md` 的输入说明 |

## 维护规则

- 每个可独立验证功能项只分配一个稳定 ID；功能分类、页面、接口、文件、模块和测试本身不单独计数。
- 平台、IDE、项目类型、角色和部署方式差异写入“适用范围”，不要重复登记同一功能。
- “支持状态”“适用范围”“版本归属”和“验证方式”分别维护，不能互相替代。
- 状态、范围、版本或证据变化时保留原 ID；新增行或删除已支持行后重新计算汇总。
- 本清单只链接详细契约，不复制 Skill、需求、架构、计划或 CHANGELOG 正文。
- 未来工作写入规划文档，已发布变化写入 CHANGELOG，证据不足的功能只留在“待确认”。
