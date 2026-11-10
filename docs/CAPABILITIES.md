# dev-harness 产品功能清单

[简体中文](CAPABILITIES.md) | [English](CAPABILITIES.en.md)

dev-harness 帮助团队统一项目规则、安排开发任务、验证交付结果，并在项目变化后维护文档。你可以先按目标查找功能，再展开对应的技术证据。

本文件是当前已支持功能的权威维护文档，覆盖本仓库的 8 个工程助手（Skill）及安装分发。[Runtime](https://github.com/Dev-Wiki/dev-harness-runtime) 的自动执行、恢复和平台能力由其仓库维护，不计入本清单。未来候选见 [V2 Backlog](V2_BACKLOG.md)，版本边界见 [范围说明](V1_V2_BOUNDARIES.md)，版本变化见 [CHANGELOG](../CHANGELOG.md)。

## 快速查找

| 我想做什么 | 查看功能 |
|---|---|
| 安装或分享给同事 | [安装与分发](#安装与分发) |
| 让助手了解项目 | [了解和接入项目](#项目上下文) |
| 找到、更新和盘点项目文档 | [维护文档与功能清单](#文档治理) |
| 把需求拆成可交接的任务 | [安排开发任务](#项目规划) |
| 明确应该运行哪些构建与测试 | [构建与测试](#验证命令) |
| 按项目规则提交与整理发布说明 | [提交与发布](#git-工作流) |
| 定位和修复一个已知问题 | [问题分析与修复](#auto-fix) |
| 系统检查现有项目的工程问题 | [现有项目检查](#codebase-audit) |
| 整理任务经验 | [任务复盘](#显式复盘) |

## 怎么开始使用

安装后，在支持这些 Skill 的编码助手中直接描述目标。例如：

- 首次盘点：“根据当前实现，全量盘点已经支持的功能，生成普通用户能读懂的功能清单。”
- 增量同步：“核对这次功能或 fix 对功能清单的影响，完成必要更新后再收口。”
- 全量复核：“重新全量核对已有功能清单，保留功能 ID，列出变化、待确认项和未覆盖范围。”

现有项目已有同类功能说明时会沿用；功能是否支持，以当前实现和验证证据为依据。

## 汇总

仓库 [VERSION](../VERSION) 为 `v1.12.1`，本版明确验证范围与项目门禁的职责分工，并对齐 Runtime 自动执行交接要求，功能数量不变。下表分别统计当前开发版本与本次发布范围，版本内容见 [CHANGELOG](../CHANGELOG.md#v1121--2026-11-09)，发行状态以 [GitHub Releases](https://github.com/Dev-Wiki/dev-harness/releases) 为准。

| 版本范围 | 已支持 | 部分支持 | 试验性 | 已弃用 |
|---|---:|---:|---:|---:|
| 当前开发版本（v1.12.1） | 36 | 0 | 0 | 0 |
| 本次发布范围（v1.12.1） | 36 | 0 | 0 | 0 |

待确认和已移除项不计入已支持数量。分类、任务、页面和测试数量不作为功能数量。

## 当前已支持功能

### 安装与分发

<a id="ins-001"></a>

#### 安装需要的工程助手

选择安装全部或部分工程助手，让不同编码工具使用同一套项目规则。

- **支持状态**：已支持
- **适用范围**：使用 Cursor、Codex、OpenCode 或 Antigravity 的团队
- **使用入口**：[安装说明](../README.md#安装)
- **使用限制**：安装脚本需要 Python 3；各编码工具的安装目录不同。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`INS-001`
- **版本记录**：已发布：v1.10.0
- **工程条件**：Python 3；POSIX / Windows wrapper
- **验证方式**：自动化测试 + 代码证据
- **证据**：[tests/test_install.py](../tests/test_install.py)；[install.py](../install.py)；[install.bat](../install.bat)
- **技术详情**：安装全部或指定 Skill，支持 Cursor、Codex、OpenCode、Antigravity、交互选择和自定义目标，并展开 Skill 依赖；详细规则见 [安装说明](../README.md#安装)。

</details>

<a id="ins-002"></a>

#### 打包并离线分发工程助手

把工程助手及所需资源打成便携包，供同事解压复制安装。

- **支持状态**：已支持
- **适用范围**：需要离线安装、统一分发或维护发布包的团队
- **使用入口**：[安装说明](../README.md#安装)
- **使用限制**：便携包提供工程助手及运行资源；源码和仓库维护文档由源码归档提供。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`INS-002`
- **版本记录**：已发布：v1.10.0；修正：v1.11.4；Skill 专用发布包：v1.11.8
- **工程条件**：维护者发布与离线分发
- **验证方式**：自动化测试 + 代码证据
- **证据**：[tests/test_install.py](../tests/test_install.py)；[install.py](../install.py)；[release.py](../release.py)
- **技术详情**：原子导出便携 `bundle/`，失败时保留旧产物；版本 zip 包含可直接使用的 Skill 及其运行资源、中英文专用安装说明、VERSION 和 CHANGELOG，解压后复制安装；详细规则见 [安装与发布入口](../README.md#安装)。

</details>

<a id="项目上下文"></a>

### 了解和接入项目

<a id="ctx-001"></a>

#### 收集项目的真实结构与入口

读取仓库中的文件与工程配置，为理解项目提供可核对的材料。

- **支持状态**：已支持
- **适用范围**：需要接入新项目或重新了解现有项目的开发团队
- **使用入口**：[客户端项目接入](CLIENT_PROJECT_ONBOARDING.md)
- **使用限制**：不收集依赖和缓存目录；材料不完整时会明确提示，不能据此确认完整项目情况。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`CTX-001`
- **版本记录**：已发布：v1.10.0；修正：v1.11.7
- **工程条件**：可读取的本地仓库，不限内置 Profile；仍排除依赖与缓存目录
- **验证方式**：自动化测试 + 契约证据
- **证据**：[tests/test_context_cli.py](../tests/test_context_cli.py)；[tests/test_context_evidence_integrity.py](../tests/test_context_evidence_integrity.py)；[context/SKILL.md](../context/SKILL.md)
- **技术详情**：`evidence` 输出通用仓库清单、分析字段契约、截断状态和完整文件内容指纹，覆盖 workspace 源码与隐藏工程配置；详细规则见 [Context 契约](../context/SKILL.md)。

</details>

<a id="ctx-002"></a>

#### 补齐首次接入所需的项目说明

为尚未准备好的项目补建项目简介、架构、助手规则和验证说明。

- **支持状态**：已支持
- **适用范围**：首次接入工程助手的项目
- **使用入口**：[客户端项目接入](CLIENT_PROJECT_ONBOARDING.md)
- **使用限制**：已有同名文件会保留；更新已有内容应使用刷新功能。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`CTX-002`
- **版本记录**：已发布：v1.10.0；修正：v1.11.7
- **工程条件**：首次初始化项目
- **验证方式**：自动化测试 + 代码证据
- **证据**：[tests/test_context_cli.py](../tests/test_context_cli.py)；[tests/test_context_write_safety.py](../tests/test_context_write_safety.py)；[tests/test_install.py](../tests/test_install.py)
- **技术详情**：`scan` 以独占创建方式补齐缺失的 README、AGENTS、ARCHITECTURE、HARNESS，拒绝链接目标并保留已有同名文件；默认 AGENTS 包含按影响范围验证、全仓回归须有依据和复用有效证据的约束。新 HARNESS 的人工区使用命令表，状态初始为 `missing`，候选不会自动获得执行资格。格式与旧人工区保留回归见 [交接测试](../tests/test_runtime_handoff.py)；详细规则见 [Context 契约](../context/SKILL.md)。

</details>

<a id="ctx-003"></a>

#### 更新已有项目说明

项目变化后更新约定的自动识别章节，保留人工维护的内容。

- **支持状态**：已支持
- **适用范围**：已经初始化项目说明的仓库
- **使用入口**：[客户端项目接入](CLIENT_PROJECT_ONBOARDING.md)
- **使用限制**：只更新约定章节；结构冲突或文件在预览后被改动时停止写入。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`CTX-003`
- **版本记录**：已发布：v1.10.0；修正：v1.11.4、v1.11.7
- **工程条件**：固定标题结构有效的已初始化项目
- **验证方式**：自动化测试
- **证据**：[tests/test_context_cli.py](../tests/test_context_cli.py)；[tests/test_managed_context.py](../tests/test_managed_context.py)；[tests/test_context_write_safety.py](../tests/test_context_write_safety.py)
- **技术详情**：`refresh` 只更新固定 Markdown 章节，保留这些章节之外的人工内容、编码、换行和权限；固定章节按模板整段替换，Agent 预览发现人工规则将丢失时先跳过该文件的刷新，不能依赖 Writer 自动合并。结构异常或预览后目标变化时拒绝写入；非交互且未使用 `--force` 时仅预览；详细规则见 [Context 契约](../context/SKILL.md)。

</details>

<a id="ctx-004"></a>

#### 根据证据理解项目

结合真实仓库材料，识别项目语言、框架、模块职责和入口，并保留判断依据。

- **支持状态**：已支持
- **适用范围**：需要由编码助手理解项目的团队
- **使用入口**：[客户端项目接入](CLIENT_PROJECT_ONBOARDING.md)
- **使用限制**：材料缺失或判断不确定时保留未知项；不把框架惯例自动写成事实。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`CTX-004`
- **版本记录**：已发布：v1.10.0；修正：v1.11.4、v1.11.7
- **工程条件**：通用仓库与未知框架；离线 Profile 回退与 AI 主路径分离
- **验证方式**：自动化测试 + 契约证据
- **证据**：[tests/test_context_cli.py](../tests/test_context_cli.py)；[tests/test_semantic_analysis.py](../tests/test_semantic_analysis.py)；[tests/test_context_evidence_integrity.py](../tests/test_context_evidence_integrity.py)
- **技术详情**：接受绑定置信度和快照指纹的 AI 语义分析，引用必须纳入指纹覆盖；拒绝漂移或截断证据，明确 Unknown、低置信度和空值不会被 Profile 回填为事实；详细规则见 [Context 契约](../context/SKILL.md)。

</details>

<a id="文档治理"></a>

### 维护文档与功能清单

<a id="doc-001"></a>

#### 检查文档是否容易找到、相互一致

找出文档入口缺失、链接损坏、重复维护和找不到归属的内容。

- **支持状态**：已支持
- **适用范围**：已有文档或准备建立文档体系的项目
- **使用入口**：[文档整理规则](../dev-harness-docs/SKILL.md)
- **使用限制**：检查阶段只读；整理或修正文档需要对应的更新请求。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`DOC-001`
- **版本记录**：已发布：v1.10.0
- **工程条件**：已有或待建立文档体系的仓库
- **验证方式**：契约测试
- **证据**：[tests/test_docs_contract.py](../tests/test_docs_contract.py)；[dev-harness-docs/SKILL.md](../dev-harness-docs/SKILL.md)
- **技术详情**：只读审计重复所有权、孤儿文档、导航和链接问题；详细规则见 [Docs 契约](../dev-harness-docs/SKILL.md)。

</details>

<a id="doc-002"></a>

#### 建立项目文档入口

建立最小文档中心与必要维护规则，让团队知道资料放在哪里。

- **支持状态**：已支持
- **适用范围**：还没有完整文档入口的项目
- **使用入口**：[文档整理规则](../dev-harness-docs/SKILL.md)
- **使用限制**：沿用项目已有的文档目录，不另外建一套相同用途的目录。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`DOC-002`
- **版本记录**：已发布：v1.10.0
- **工程条件**：尚无完整文档中心的仓库
- **验证方式**：契约测试 + 资源安装测试
- **证据**：[tests/test_docs_contract.py](../tests/test_docs_contract.py)；[tests/test_install.py](../tests/test_install.py)
- **技术详情**：初始化最小文档中心和必要维护规则，同时解析并复用唯一 `doc/` 或 `docs/` 根；详细规则见 [Docs 契约](../dev-harness-docs/SKILL.md)。

</details>

<a id="doc-003"></a>

#### 整理和更新文档导航

整理索引、阅读路径和权威文档入口，让读者找到当前有效说明。

- **支持状态**：已支持
- **适用范围**：需要整理现有文档体系的项目
- **使用入口**：[文档整理规则](../dev-harness-docs/SKILL.md)
- **使用限制**：只维护入口与归属；详细内容仍由各自的权威文档维护。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`DOC-003`
- **版本记录**：已发布：v1.10.0
- **工程条件**：既有文档体系；Audit 导航受 Snapshot 漂移边界约束
- **验证方式**：契约测试
- **证据**：[tests/test_docs_contract.py](../tests/test_docs_contract.py)；[dev-harness-docs/SKILL.md](../dev-harness-docs/SKILL.md)
- **技术详情**：组织或刷新索引、导航、SSOT、放置规则和 Audit `Report.md` 入口，不复制深层正文；详细规则见 [Docs 契约](../dev-harness-docs/SKILL.md)。

</details>

<a id="doc-004"></a>

#### 归档过时或已完成的文档

保留有用历史，同时把读者引导到当前有效文档。

- **支持状态**：已支持
- **适用范围**：存在过时、被替代或已完成文档的项目
- **使用入口**：[文档整理规则](../dev-harness-docs/SKILL.md)
- **使用限制**：移动前核对路径和链接影响；不会默认删除历史正文。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`DOC-004`
- **版本记录**：已发布：v1.10.0
- **工程条件**：非活跃、已完成或被替代的文档
- **验证方式**：契约证据
- **证据**：[dev-harness-docs/SKILL.md](../dev-harness-docs/SKILL.md)
- **技术详情**：在确认精确 move map 与链接影响后，归档已完成或被替代文档并维护当前权威入口；详细规则见 [Docs 契约](../dev-harness-docs/SKILL.md)。

</details>

<a id="doc-005"></a>

#### 在交付后同步功能与项目事实

每次功能或修复验证通过后，核对相关文档，补上变化并说明处理结果。

- **支持状态**：已支持
- **适用范围**：需要持续维护已有功能说明和工程文档的团队
- **使用入口**：[功能清单维护](../dev-harness-docs/references/capability-maintenance.md)
- **使用限制**：只记录有当前实现或验证依据的事实；完成检查自 v1.12.0 起纳入交付要求。
- **版本归属**：v1.10.0 起支持；v1.12.0 增强

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`DOC-005`
- **版本记录**：已发布：v1.10.0；本轮增强：v1.12.0
- **工程条件**：代码或验证变化后的事实同步
- **验证方式**：契约证据
- **证据**：[dev-harness-docs/SKILL.md](../dev-harness-docs/SKILL.md)
- **技术详情**：把代码、配置或成功验证证明的可复用事实按最小计划同步到既有 SSOT，未验证项进入“待确认”；每次交付前记录已更新、无需更新或不适用的处理结果及依据；详细规则见 [Docs 契约](../dev-harness-docs/SKILL.md)。

</details>

<a id="doc-006"></a>

#### 维护普通用户也能阅读的功能目录

把当前功能、适用范围、限制和使用入口集中说明，技术证据可按需展开。

- **支持状态**：已支持
- **适用范围**：功能分散、支持条件复杂或需要可靠盘点的项目
- **使用入口**：[功能清单维护](../dev-harness-docs/references/capability-maintenance.md)
- **使用限制**：复用已有同类文档；支持状态与是否发布分别说明，不从任务数量推算功能数量。
- **版本归属**：v1.10.0 起支持；v1.12.0 增强

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`DOC-006`
- **版本记录**：已发布：v1.10.0；本轮增强：v1.12.0
- **工程条件**：当前功能分散、有适用差异或无法可靠统计的项目
- **验证方式**：契约测试
- **证据**：[tests/test_docs_contract.py](../tests/test_docs_contract.py)；[dev-harness-docs/SKILL.md](../dev-harness-docs/SKILL.md)
- **技术详情**：条件性建立或维护 Capability Catalog，以稳定 ID 分离支持状态、适用范围、版本归属、验证方式和证据；用户说明和工程证据绑定在同一功能项，技术信息按需展开；详细规则见 [Docs 契约](../dev-harness-docs/SKILL.md)。

</details>

<a id="doc-007"></a>

#### 首次盘点并反复核对已支持功能

从真实实现建立功能清单，并在项目演进后反复全量核对，补上遗漏、更新限制和保留待确认项。

- **支持状态**：已支持
- **适用范围**：需要建立或重新全量核对功能目录的项目
- **使用入口**：[功能清单维护](../dev-harness-docs/references/capability-maintenance.md)
- **使用限制**：由编码助手按证据执行；不是独立扫描命令。覆盖不足时明确未完成，不能保证自动发现所有未知功能。
- **版本归属**：v1.12.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`DOC-007`
- **版本记录**：首次支持：v1.12.0
- **验证方式**：契约证据 + 正向场景演练
- **证据**：[dev-harness-docs/references/capability-maintenance.md](../dev-harness-docs/references/capability-maintenance.md)；[dev-harness-docs/assets/capabilities.template.md](../dev-harness-docs/assets/capabilities.template.md)
- **技术详情**：在 Agent 工作流中首次全量盘点、逐次增量同步并反复全量复核；记录基线和覆盖范围，核对所有既有 ID，保留待确认或已移除依据；详细规则见 [功能清单维护](../dev-harness-docs/references/capability-maintenance.md)。

</details>

<a id="项目规划"></a>

### 安排开发任务

<a id="pln-001"></a>

#### 把需求整理成开发看板

把需求、原型或产品说明拆成看板与独立任务，方便分工和交接。

- **支持状态**：已支持
- **适用范围**：按项目、版本或里程碑安排开发的团队
- **使用入口**：[开发任务工作流](WORKFLOW.md#4-新功能交付工作流)
- **使用限制**：规划负责整理任务，自动执行需要另外安装 Runtime。
- **版本归属**：v1.11.1 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`PLN-001`
- **版本记录**：已发布：v1.11.1
- **工程条件**：项目、版本或里程碑级规划
- **验证方式**：契约测试 + 资源安装测试
- **证据**：[tests/test_docs_contract.py](../tests/test_docs_contract.py)；[tests/test_install.py](../tests/test_install.py)
- **技术详情**：从需求、PRD、原型或参考格式生成同一文档根下唯一活跃 Dashboard 和单任务详情；详细规则见 [Planning 契约](../planning/SKILL.md)。

</details>

<a id="pln-002"></a>

#### 更新计划并保留已有进度

需求变化时按任务编号合并计划，保留仍有效的任务身份与完成依据。

- **支持状态**：已支持
- **适用范围**：需要长期更新开发计划的项目
- **使用入口**：[开发任务工作流](WORKFLOW.md#4-新功能交付工作流)
- **使用限制**：发现其他人修改了计划或已有工作内容时，需要先重新对齐。
- **版本归属**：v1.11.1 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`PLN-002`
- **版本记录**：已发布：v1.11.1；修正：v1.11.7
- **工程条件**：已有计划，包括单体 TaskDetails 迁移
- **验证方式**：契约测试 + 场景验证
- **证据**：[tests/test_planning_contract.py](../tests/test_planning_contract.py)；[planning/SKILL.md](../planning/SKILL.md)
- **技术详情**：刷新计划时按 Task ID 合并，保留有效 ID、本地约定和有证据的完成状态；临时快照核对已有 dirty 内容与暂存状态，检查块同时拒绝重复字段和读取错误；详细规则见 [Planning 契约](../planning/SKILL.md)。

</details>

<a id="pln-003"></a>

#### 归档完成任务并支持重新打开

让看板保持简洁，同时保留每次任务关闭的验收记录；重开后仍能追踪前次结果。

- **支持状态**：已支持
- **适用范围**：长期演进或任务较多的项目
- **使用入口**：[开发任务工作流](WORKFLOW.md#4-新功能交付工作流)
- **使用限制**：任务进度只在看板维护；重新关闭会保留前次归档，不覆盖历史。
- **版本归属**：v1.11.1 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`PLN-003`
- **版本记录**：已发布：v1.11.1；修正：v1.11.7
- **工程条件**：长期演进或大型计划
- **验证方式**：契约测试 + 模板安装测试 + 场景验证
- **证据**：[tests/test_planning_contract.py](../tests/test_planning_contract.py)；[tests/test_install.py](../tests/test_install.py)；[planning/SKILL.md](../planning/SKILL.md)；[planning/templates/ArchiveIndex.template.md](../planning/templates/ArchiveIndex.template.md)
- **技术详情**：活跃任务按 Task ID 分片，跨任务可变字段只在 Dashboard 维护；完成任务进入里程碑归档，重开后再次完成使用下一未占用 closure 编号并保留旧快照；详细规则见 [Planning 契约](../planning/SKILL.md)。

</details>

<a id="pln-004"></a>

#### 准备可交接的任务说明

明确每项任务的目标、范围、验收和停止条件，使新对话也能继续执行。

- **支持状态**：已支持
- **适用范围**：规划与开发由不同人员或不同会话承担的团队
- **使用入口**：[开发任务工作流](WORKFLOW.md#4-新功能交付工作流)
- **使用限制**：材料不齐时保持规划中；交给 Runtime 自动执行还需准备其支持的计划格式、命令表与冻结声明，必要文档修改和检查纳入任务范围。普通人工计划无需 Runtime 声明。
- **版本归属**：v1.11.3 起支持；v1.12.0 增强

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`PLN-004`
- **版本记录**：已发布：v1.11.3；本轮增强：v1.12.0
- **工程条件**：规划与执行分属不同对话或外部工作流的项目
- **验证方式**：契约测试 + 模板安装测试
- **证据**：[tests/test_planning_contract.py](../tests/test_planning_contract.py)；[tests/test_install.py](../tests/test_install.py)；[planning/templates/Task.template.md](../planning/templates/Task.template.md)
- **技术详情**：用 `规划中` 与 `待执行` 区分任务包完整性，并在单任务执行包中固定权威需求、代码与测试入口、不变量、已确认决策和停止条件；就绪前声明功能文档影响与授权路径，验收包含文档检查。自动执行的命令、范围、验收覆盖和归档输入按 [Runtime 交接](../planning/references/runtime-handoff.md) 准备，格式样例由 [交接测试](../tests/test_runtime_handoff.py) 检查；详细规则见 [Planning 契约](../planning/SKILL.md)。

</details>

<a id="验证命令"></a>

### 构建与测试

<a id="cmd-001"></a>

#### 统一项目的构建与测试入口

把项目已有命令整理成一致的构建、测试、快速检查、缺陷验证和完整验证入口。

- **支持状态**：已支持
- **适用范围**：已有真实构建或验证工具的项目
- **使用入口**：[构建与验证指南](HARNESS_GUIDE.md)
- **使用限制**：不替换原工具链；未确认的命令保留缺口，需要设备的验证单独说明。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`CMD-001`
- **版本记录**：已发布：v1.10.0；修正：v1.11.7
- **工程条件**：已存在真实构建或验证入口的项目；无独立构建可记为 N/A
- **验证方式**：契约测试 + 契约证据
- **证据**：[tests/test_vnext_contract.py](../tests/test_vnext_contract.py)；[commands/SKILL.md](../commands/SKILL.md)
- **技术详情**：把仓库真实命令映射为稳定的 `build / test / quick / bugfix / full` 语义入口，支持 Platform / Variant 多记录；单条命令缺口不阻止其他已确认记录写入 HARNESS 人工确认区。新维护的人工区采用带状态的表格，旧列表交接 Runtime 前按证据迁移，并核对唯一用途与 literal argv 限制；详细规则见 [Commands 契约](../commands/SKILL.md)。

</details>

<a id="git-工作流"></a>

### 提交与发布

<a id="git-001"></a>

#### 遵循项目自己的提交与发布规则

先识别项目已有规则，缺少规则时再提出适合项目的方案。

- **支持状态**：已支持
- **适用范围**：使用 Git 的项目
- **使用入口**：[交付与提交工作流](WORKFLOW.md#46-同步事实状态并提交)
- **使用限制**：新建规则需要确认；确认规则本身不会授予提交或发布权限。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`GIT-001`
- **版本记录**：已发布：v1.10.0；修正：v1.11.7
- **工程条件**：Git 仓库；根或规范归属冲突时需人工选择，初始化不等于授权 Git 写操作
- **验证方式**：契约测试 + Context 发现测试
- **证据**：[tests/test_git_workflow_contract.py](../tests/test_git_workflow_contract.py)；[tests/test_contract_discovery.py](../tests/test_contract_discovery.py)；[git-workflow/SKILL.md](../git-workflow/SKILL.md)
- **技术详情**：优先发现并遵循仓库自有 Git / commit / tag / release / changelog 规范，复用权威 doc/ 或 docs/ 根；缺失时提出候选，显式确认后初始化默认规范；详细规则见 [Git Workflow 契约](../git-workflow/SKILL.md)。

</details>

<a id="git-002"></a>

#### 精确提交本次任务的修改

核对文件归属和暂存内容，帮助提交当前任务，保留其他已有修改。

- **支持状态**：已支持
- **适用范围**：已明确授权提交的开发任务
- **使用入口**：[交付与提交工作流](WORKFLOW.md#46-同步事实状态并提交)
- **使用限制**：需要单独的提交授权；遇到内容归属冲突或敏感文件时停止处理。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`GIT-002`
- **版本记录**：已发布：v1.10.0；修正：v1.11.7
- **工程条件**：用户明确授权 commit 的工作流；通用任务无需创建 Auto Fix Run
- **验证方式**：契约测试 + 契约证据
- **证据**：[tests/test_auto_fix_contract.py](../tests/test_auto_fix_contract.py)；[git-workflow/SKILL.md](../git-workflow/SKILL.md)
- **技术详情**：按本轮授权文件和补丁精确暂存、提交，核对已有修改的内容归属与暂存状态，并检测敏感文件、调试残留和无关变更；详细规则见 [Git Workflow 契约](../git-workflow/SKILL.md)。

</details>

<a id="git-003"></a>

#### 根据版本记录整理发布说明

从对应版本的变更日志生成标签说明和发布说明，保持格式一致。

- **支持状态**：已支持
- **适用范围**：已授权创建标签或整理发布说明的团队
- **使用入口**：[交付与提交工作流](WORKFLOW.md#46-同步事实状态并提交)
- **使用限制**：由编码助手按规则生成；对应版本记录缺失时停止，不根据提交标题编造发布内容。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`GIT-003`
- **版本记录**：已发布：v1.10.0
- **工程条件**：用户明确授权 tag / release message 的仓库
- **验证方式**：契约测试
- **证据**：[tests/test_git_workflow_contract.py](../tests/test_git_workflow_contract.py)；[git-workflow/SKILL.md](../git-workflow/SKILL.md)；[git-workflow/references/default-contract.md](../git-workflow/references/default-contract.md)
- **技术详情**：从匹配版本 CHANGELOG 生成 annotated tag annotation 和 release notes，按约定顺序省略空分类，缺失版本时停止；详细规则见 [Git Workflow 契约](../git-workflow/SKILL.md)。

</details>

<a id="auto-fix"></a>

### 问题分析与修复

<a id="fix-001"></a>

#### 只分析问题，保留项目原样

复现问题、检查原因与反证，输出调查结论和仍缺少的证据。

- **支持状态**：已支持
- **适用范围**：希望先了解问题原因的使用者
- **使用入口**：[问题分析与修复指南](BUGFIX_GUIDE.md)
- **使用限制**：只读分析模式不会进入代码修复或提交阶段。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`FIX-001`
- **版本记录**：已发布：v1.10.0
- **工程条件**：只分析、不修改的 Bug 调查
- **验证方式**：运行时测试 + 契约测试
- **证据**：[tests/test_auto_fix_runtime.py](../tests/test_auto_fix_runtime.py)；[tests/test_auto_fix_contract.py](../tests/test_auto_fix_contract.py)
- **技术详情**：`analyze` 模式执行只读复现、探测、可证伪根因分析和报告，运行时阻止进入写阶段；详细规则见 [Auto Fix 契约](../auto-fix/SKILL.md)。

</details>

<a id="fix-002"></a>

#### 修复已知问题并验证结果

围绕已确认原因修复问题，核对修复前后结果、功能文档和最终改动。

- **支持状态**：已支持
- **适用范围**：有明确问题、可以复现并有项目验证入口的仓库
- **使用入口**：[问题分析与修复指南](BUGFIX_GUIDE.md)
- **使用限制**：验证缺口必须说明；完成前须核对功能文档。
- **版本归属**：v1.10.0 起支持；v1.12.0 增强

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`FIX-002`
- **版本记录**：已发布：v1.10.0；修正：v1.11.7；本轮增强：v1.12.0
- **工程条件**：可建立复现与项目验证入口的 Bug；客观验证缺口须记录替代验证与风险
- **验证方式**：运行时测试 + 契约测试
- **证据**：[tests/test_auto_fix_runtime.py](../tests/test_auto_fix_runtime.py)；[tests/test_auto_fix_lifecycle.py](../tests/test_auto_fix_lifecycle.py)；[tests/test_auto_fix_contract.py](../tests/test_auto_fix_contract.py)；[tests/test_auto_fix_documentation.py](../tests/test_auto_fix_documentation.py)
- **技术详情**：`fix` 模式要求 confirmed 假设、RED/GREEN、当前依赖证据、diff-bound review 和 final verify；同阶段更新与重复 report 也重新执行门禁，客观 skip 最多为 DONE_WITH_CONCERNS；DocumentationCheck 绑定当前 diff，final-verify、成功 report 和 commit 重查；详细规则见 [Auto Fix 契约](../auto-fix/SKILL.md)。

</details>

<a id="fix-003"></a>

#### 在授权后提交修复结果

验收通过后精确提交本次修复，并保留可恢复的提交记录。

- **支持状态**：已支持
- **适用范围**：明确授权自动提交的修复任务
- **使用入口**：[问题分析与修复指南](BUGFIX_GUIDE.md)
- **使用限制**：默认修复模式不提交；推送、PR 和发布仍分别需要授权。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`FIX-003`
- **版本记录**：已发布：v1.10.0；修正：v1.11.7
- **工程条件**：明确授权提交的 Auto Fix Run；支持 Git 文本转换和 core.filemode 语义
- **验证方式**：运行时测试 + 契约测试
- **证据**：[tests/test_auto_fix_runtime.py](../tests/test_auto_fix_runtime.py)；[tests/test_auto_fix_lifecycle.py](../tests/test_auto_fix_lifecycle.py)；[auto-fix/SKILL.md](../auto-fix/SKILL.md)
- **技术详情**：`commit` / `unattended` 精确核对暂存内容与提交 tree，记录可恢复的提交回执；`fix` / `analyze` 禁止提交，push / PR / release 仍需独立授权；详细规则见 [Auto Fix 契约](../auto-fix/SKILL.md)。

</details>

<a id="fix-004"></a>

#### 中断后恢复修复工作

保存修复阶段与证据，在新会话继续时重新核对项目和工作区。

- **支持状态**：已支持
- **适用范围**：需要跨会话完成的较长修复任务
- **使用入口**：[问题分析与修复指南](BUGFIX_GUIDE.md)
- **使用限制**：项目在外部发生变化时先停止对齐；过期完成结论不能直接沿用。
- **版本归属**：v1.10.0 起支持；v1.12.0 增强

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`FIX-004`
- **版本记录**：已发布：v1.10.0；修正：v1.11.4、v1.11.7；本轮增强：v1.12.0
- **工程条件**：Git 仓库中的长流程修复；旧运行已提交时须核对后建立新运行
- **验证方式**：运行时测试
- **证据**：[tests/test_auto_fix_runtime.py](../tests/test_auto_fix_runtime.py)；[tests/test_auto_fix_lifecycle.py](../tests/test_auto_fix_lifecycle.py)；[auto-fix/runtime.py](../auto-fix/runtime.py)
- **技术详情**：WorkspaceSnapshot 与 Git 私有原子状态支持漂移检查和断点恢复；Schema 3 分离内容与暂存指纹，旧状态撤销过期完成证据并要求重验；详细规则见 [Auto Fix 契约](../auto-fix/SKILL.md)。

</details>

<a id="fix-005"></a>

#### 按问题风险安排必要验证

按影响范围安排验证，并复用仍然有效的结果，减少无依据的重复执行。

- **支持状态**：已支持
- **适用范围**：不同规模和风险的缺陷修复
- **使用入口**：[问题分析与修复指南](BUGFIX_GUIDE.md)
- **使用限制**：风险不明时采用更严格验证；已有失败不能用跳过或旧记录掩盖。
- **版本归属**：v1.11.2 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`FIX-005`
- **版本记录**：已发布：v1.11.2；修正：v1.11.7
- **工程条件**：fast / standard / strict 修复；风险不明时 fail-safe，保留客观验证缺口
- **验证方式**：运行时测试 + 契约测试
- **证据**：[tests/test_auto_fix_runtime.py](../tests/test_auto_fix_runtime.py)；[tests/test_auto_fix_lifecycle.py](../tests/test_auto_fix_lifecycle.py)；[tests/test_auto_fix_contract.py](../tests/test_auto_fix_contract.py)；[auto-fix/SKILL.md](../auto-fix/SKILL.md)
- **技术详情**：授权 Mode 与验证档位正交；技能要求按实际影响选择验证范围，strict 或共享基础设施分类不单独触发全仓回归，全仓须记录明确要求或较小范围不足的证据。运行时按依赖使证据失效或复用，文档变化仍要求重审；已知失败只能由同命令/检查的新通过证据清除，状态写入权限失败快速终止；详细规则见 [Auto Fix 契约](../auto-fix/SKILL.md)。

</details>

<a id="codebase-audit"></a>

### 系统检查现有项目

<a id="aud-001"></a>

#### 中断后恢复项目检查

保存项目检查的范围、阶段和问题记录，支持后续会话继续。

- **支持状态**：已支持
- **适用范围**：已获准检查的本地 Git 项目
- **使用入口**：[项目检查工作流](WORKFLOW.md#5-代码库审计与修复工作流)
- **使用限制**：项目和上下文变化后需要重新核对，不能把旧结论当成当前事实。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`AUD-001`
- **版本记录**：已发布：v1.10.0
- **工程条件**：用户拥有或明确授权的 Git 仓库，已有唯一 docs root 与 Canonical Context
- **验证方式**：运行时测试
- **证据**：[tests/test_codebase_audit_runtime.py](../tests/test_codebase_audit_runtime.py)
- **技术详情**：初始化 Git 私有 AuditSnapshot，并通过 checkpoint、status、resume 跨会话恢复任务和 Finding 状态；详细规则见 [Audit 契约](../codebase-audit/SKILL.md)。

</details>

<a id="aud-002"></a>

#### 按实际模块检查现有项目

根据项目真实边界分阶段检查，并生成任务结果、问题清单和总报告。

- **支持状态**：已支持
- **适用范围**：较大或跨模块的现有项目
- **使用入口**：[项目检查工作流](WORKFLOW.md#5-代码库审计与修复工作流)
- **使用限制**：侧重工程质量和行为正确性；这项能力不用于维护产品功能清单。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`AUD-002`
- **版本记录**：已发布：v1.10.0
- **工程条件**：大型或跨模块存量仓库；工程质量审计，不含 offensive security
- **验证方式**：契约测试
- **证据**：[tests/test_vnext_contract.py](../tests/test_vnext_contract.py)；[codebase-audit/SKILL.md](../codebase-audit/SKILL.md)
- **技术详情**：基于 Context 动态分区并逐任务生成 Dashboard、Task、Result、Findings 和 Report；详细规则见 [Audit 契约](../codebase-audit/SKILL.md)。

</details>

<a id="aud-003"></a>

#### 跟踪问题的确认与修复验证

记录问题是候选、已确认、已排除、已失效还是已解决，并保留证据。

- **支持状态**：已支持
- **适用范围**：使用项目检查问题清单的团队
- **使用入口**：[项目检查工作流](WORKFLOW.md#5-代码库审计与修复工作流)
- **使用限制**：标为已解决前需要真实原问题和修复后的新验证；代码再次变化后结论可能失效。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`AUD-003`
- **版本记录**：已发布：v1.10.0；修正：v1.11.6、v1.11.7
- **工程条件**：Audit Finding Registry；保留原确认依据，后续漂移使 resolved 再次 stale
- **验证方式**：运行时测试 + 契约证据
- **证据**：[tests/test_codebase_audit_runtime.py](../tests/test_codebase_audit_runtime.py)；[tests/test_audit_resolution.py](../tests/test_audit_resolution.py)；[codebase-audit/references/finding-contract.md](../codebase-audit/references/finding-contract.md)
- **技术详情**：Finding 支持候选、确认、拒绝、过期与解决状态；confirmed 绑定完整证据和 Snapshot，resolved 必须从真实历史确认问题导入，并绑定修复后新快照及通过的验证；详细规则见 [Finding 契约](../codebase-audit/references/finding-contract.md)。

</details>

<a id="aud-004"></a>

#### 在检查结束前核对模块之间的关系

集中检查跨模块调用、数据流、重复问题和相互矛盾的结论。

- **支持状态**：已支持
- **适用范围**：所有项目检查任务，包括小项目或没有发现问题的情况
- **使用入口**：[项目检查工作流](WORKFLOW.md#5-代码库审计与修复工作流)
- **使用限制**：必须保留关系和反证依据，不能仅凭模块初始化先后推断调用关系。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`AUD-004`
- **版本记录**：已发布：v1.10.0；修正：v1.11.4、v1.11.6
- **工程条件**：所有 Audit Run，包括小项目或零 Finding
- **验证方式**：运行时测试 + 契约测试 + 契约证据
- **证据**：[tests/test_codebase_audit_runtime.py](../tests/test_codebase_audit_runtime.py)；[tests/test_vnext_contract.py](../tests/test_vnext_contract.py)；[codebase-audit/references/cross-module-review.md](../codebase-audit/references/cross-module-review.md)
- **技术详情**：完成前强制 Cross-module Reconciliation，执行 checkpoint、去重、矛盾处理和完整调用链复核，检查生命周期关系误写与未经验证的入口；task 或 Finding 变化后旧复核自动失效；详细规则见 [跨模块复核](../codebase-audit/references/cross-module-review.md)。

</details>

<a id="aud-005"></a>

#### 防止项目变化后沿用过期检查结论

在关键阶段核对版本与工作区变化，保护检查范围和证据有效性。

- **支持状态**：已支持
- **适用范围**：正在执行或恢复的项目检查
- **使用入口**：[项目检查工作流](WORKFLOW.md#5-代码库审计与修复工作流)
- **使用限制**：只能写检查文档与私有运行状态；发现未纳入基线的变化时停止确认新事实。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`AUD-005`
- **版本记录**：已发布：v1.10.0；修正：v1.11.4
- **工程条件**：活跃或恢复中的 Audit Run
- **验证方式**：运行时测试
- **证据**：[tests/test_codebase_audit_runtime.py](../tests/test_codebase_audit_runtime.py)；[codebase-audit/runtime.py](../codebase-audit/runtime.py)
- **技术详情**：HEAD、分支、已有业务 dirty 内容、Context 或业务源码漂移时 fail closed，允许当前运行更新既有审计输出，并限制输出到 `<docs-root>/audit/**`；详细规则见 [Audit 契约](../codebase-audit/SKILL.md)。

</details>

<a id="aud-006"></a>

#### 选择中文或英文检查报告

默认用自然中文整理报告，也可按明确要求输出全英文。

- **支持状态**：已支持
- **适用范围**：需要不同文档语言的项目检查
- **使用入口**：[项目检查工作流](WORKFLOW.md#5-代码库审计与修复工作流)
- **使用限制**：语言变化只影响展示，不改变问题证据和运行状态。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`AUD-006`
- **版本记录**：已发布：v1.10.0
- **工程条件**：Audit 文档输出
- **验证方式**：契约测试
- **证据**：[tests/test_vnext_contract.py](../tests/test_vnext_contract.py)；[codebase-audit/SKILL.md](../codebase-audit/SKILL.md)
- **技术详情**：默认生成自然中文审计产物，显式要求时生成全英文；显示语言不改变内部状态和 Evidence fingerprint；详细规则见 [Audit 契约](../codebase-audit/SKILL.md)。

</details>

<a id="aud-007"></a>

#### 核对检查报告的文档入口

确认总报告是否能从项目文档中心找到，缺入口时给出具体交接动作。

- **支持状态**：已支持
- **适用范围**：已经确定项目文档根的检查任务
- **使用入口**：[项目检查工作流](WORKFLOW.md#5-代码库审计与修复工作流)
- **使用限制**：检查流程不会越界修改文档中心；入口更新由文档维护流程处理。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`AUD-007`
- **版本记录**：已发布：v1.10.0
- **工程条件**：已解析 docs root 的 Audit Run
- **验证方式**：契约测试
- **证据**：[tests/test_vnext_contract.py](../tests/test_vnext_contract.py)；[tests/test_docs_contract.py](../tests/test_docs_contract.py)
- **技术详情**：检查稳定入口 `audit/Report.md` 的文档可发现性，记录 `linked` 或 `docs-refresh-required`，缺入口时生成精确 Docs handoff；详细规则见 [Audit 契约](../codebase-audit/SKILL.md)。

</details>

<a id="aud-008"></a>

#### 批量保存检查证据

把任务结果、问题和文档信息批量保存，减少长任务反复录入。

- **支持状态**：已支持
- **适用范围**：问题和证据较多的项目检查
- **使用入口**：[项目检查工作流](WORKFLOW.md#5-代码库审计与修复工作流)
- **使用限制**：批量保存仍受范围和证据检查约束，不会替代问题核实。
- **版本归属**：v1.11.5 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`AUD-008`
- **版本记录**：已发布：v1.11.5
- **工程条件**：结构化审计与长线程；保留漂移和跨模块门禁
- **验证方式**：运行时回归测试
- **证据**：[tests/test_codebase_audit_runtime.py](../tests/test_codebase_audit_runtime.py)；[codebase-audit/runtime.py](../codebase-audit/runtime.py)
- **技术详情**：原子 batch 登记 Task/Finding/document、批量输出校验与摘要返回；同次工作区校验复用 Git 身份检查；详细规则见 [批量接口](../codebase-audit/references/runtime-interface.md)。

</details>

<a id="aud-009"></a>

#### 从持久化证据生成检查报告

根据已保存的检查结果生成互相链接的报告，保留原问题与修复验证依据。

- **支持状态**：已支持
- **适用范围**：使用结构化结果的项目检查
- **使用入口**：[项目检查工作流](WORKFLOW.md#5-代码库审计与修复工作流)
- **使用限制**：已存在的手写或外部修改内容会受到保护，需要先核对再更新。
- **版本归属**：v1.11.5 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`AUD-009`
- **版本记录**：已发布：v1.11.5；修正：v1.11.7
- **工程条件**：新审计；旧手写产物保留兼容流程
- **验证方式**：渲染/中断恢复/安装包实测
- **证据**：[tests/test_codebase_audit_runtime.py](../tests/test_codebase_audit_runtime.py)；[tests/test_audit_resolution.py](../tests/test_audit_resolution.py)；[codebase-audit/render.py](../codebase-audit/render.py)
- **技术详情**：从持久化证据生成紧凑 Markdown，分别展示原问题与修复后验证快照；保护手写/外部修改的输出，完成前核对当前 Revision 渲染凭据及解决证据；详细规则见 [写入与完成](../codebase-audit/references/runtime-interface.md#写入与完成)。

</details>

<a id="显式复盘"></a>

### 任务复盘

<a id="ret-001"></a>

#### 按明确要求整理任务复盘

把复盘内容整理为事实、政策、经验和待纳入正式文档的候选结论。

- **支持状态**：已支持
- **适用范围**：明确提出复盘或总结并沉淀的团队
- **使用入口**：[复盘使用规则](../retro/SKILL.md)
- **使用限制**：不会默认在每个任务后启动复盘，也不会把未验证经验自动升级为项目规则。
- **版本归属**：v1.10.0 起支持

<details>
<summary>技术信息与验证证据</summary>

- **功能 ID**：`RET-001`
- **版本记录**：已发布：v1.10.0
- **工程条件**：明确的 retro、复盘、总结并沉淀请求
- **验证方式**：契约测试 + 安装测试
- **证据**：[tests/test_vnext_contract.py](../tests/test_vnext_contract.py)；[tests/test_install.py](../tests/test_install.py)
- **技术详情**：只在用户显式要求时复盘，把条目分类为 FACT / POLICY / LESSON，以稳定 `Rnnn` ID 去重并维护 Promotion Candidates；详细规则见 [Retro 契约](../retro/SKILL.md)。

</details>

## 待确认

以下两项尚无足够实现或验证证据，不计入已支持数量。

### 一次修复原生编排多个仓库

单个 Auto Fix 运行原生管理多个仓库的分支、快照和提交，尚未找到对应实现与自动化验证。原声明保留为线索，不承诺当前支持。

<details>
<summary>待确认依据</summary>

- **候选 ID**：`CAND-001`
- **线索**：旧版使用指南中的多仓库声明。
- **缺口**：仓库集合、跨仓库快照及提交边界的实现与验证。

</details>

### 自动抓取远端问题内容

在没有宿主连接工具或用户输入的情况下，直接抓取 GitHub / GitLab Issue，尚未找到固定客户端或集成验证。

<details>
<summary>待确认依据</summary>

- **候选 ID**：`CAND-002`
- **线索**：[Auto Fix 输入说明](../auto-fix/SKILL.md)。
- **缺口**：固定连接能力、运行实现或集成验证。

</details>

## 已移除

无。查找不到旧证据时先核对迁移或改名，不能据此直接认定功能已移除。

## 最近一次全量盘点

<details>
<summary>维护信息与覆盖范围</summary>

- **盘点环节**：全量复核。
- **盘点日期**：2026-10-23。
- **基线**：`v1.12.0` 发布源树；由 `main` / `82d39d7db45473a661b1352a8ada767f86d44149` 加入本次 Docs、Planning 与 Auto Fix 文档维护增强和版本更新。核对对象为此版本源码及安装包资源，不包含独立 Runtime 的平台状态。
- **覆盖结论**：全量盘点完成；以下九类范围及所有既有功能 ID 已核对。
- **排除范围**：独立 Runtime 仓库的任务执行与平台支持，原因是由该产品自行维护。

| 功能范围 | 检查入口与证据 | 核对结果 |
|---|---|---|
| 安装与分发 | [安装器](../install.py)、[发布打包](../release.py)、[安装验证](../tests/test_install.py) | 已检查 |
| 项目上下文 | [Context 契约](../context/SKILL.md)、[证据收集](../context/evidence.py)、[写入保护](../tests/test_context_write_safety.py) | 已检查 |
| 文档治理与功能盘点 | [Docs 契约](../dev-harness-docs/SKILL.md)、[功能清单维护](../dev-harness-docs/references/capability-maintenance.md) | 已检查 |
| 开发规划与任务交接 | [Planning 契约](../planning/SKILL.md)、[任务模板](../planning/templates/Task.template.md) | 已检查 |
| 验证命令 | [Commands 契约](../commands/SKILL.md)、[跨 Skill 验证](../tests/test_vnext_contract.py) | 已检查 |
| Git 提交与发布说明 | [Git 契约](../git-workflow/SKILL.md)、[默认规则](../git-workflow/references/default-contract.md) | 已检查 |
| 问题修复 | [Auto Fix 契约](../auto-fix/SKILL.md)、[文档门禁验证](../tests/test_auto_fix_documentation.py) | 已检查 |
| 项目检查 | [Audit 契约](../codebase-audit/SKILL.md)、[运行时验证](../tests/test_codebase_audit_runtime.py) | 已检查 |
| 显式复盘 | [Retro 契约](../retro/SKILL.md)、[跨 Skill 验证](../tests/test_vnext_contract.py) | 已检查 |

- **本轮变化**：保留原 35 个功能 ID；新增 `DOC-007`；更新 `DOC-005`、`DOC-006`、`PLN-004`、`FIX-002`、`FIX-004` 的本轮变化说明；保留两个待确认 ID。原证据路径重新核对，改用文件链接和稳定规则入口，去除易漂移的行号。
- **验证范围**：实现与契约逐类核对；本轮完整回归 259 项通过。独立临时项目完成首次盘点、增量同步、两次连续全量复核及读取范围受限的演练：旧 ID 保留、重复复核无新增或重新编号、覆盖不足不覆盖上一轮完整记录。新增门禁和安装包资源由本轮测试验证；历史目标环境验证不冒充本轮实测。验证方式见 [测试说明](TESTING.md)。
- **未决项**：`CAND-001`、`CAND-002` 缺少实现或集成证据。

</details>

## 维护规则

- [功能清单维护流程](../dev-harness-docs/references/capability-maintenance.md) 定义首次盘点、交付后的增量同步与可重复的全量复核。
- 每个独立功能只分配一个稳定 ID；名称、分类、适用条件和证据变化保留原 ID，移除时保留依据。
- 普通用户说明与技术证据属于同一个功能项；不另建一份需要人工同步的功能目录。
- 每次功能或 fix 完成前记录文档检查结果及依据；任务进度不能作为支持证据。
- 全量复核核对全部声明范围和所有已有 ID；未完成时明确范围缺口。只保留最近一次完整盘点摘要，历史由 Git 保存。
- 每次功能状态或版本变化后重新计算汇总；未来工作写入规划，已发布变化写入 CHANGELOG，证据不足的功能留在待确认。
