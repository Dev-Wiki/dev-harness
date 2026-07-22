---
name: dev-harness-context
description: Use when you need to initialize or safely refresh AI project context by scanning a real repository and maintaining managed sections in README.md, ARCHITECTURE.md, HARNESS.md, and AGENTS.md
---

# dev-harness-context

负责扫描真实仓库结构，由 AI 基于证据识别语言、框架、架构和验证入口，初始化面向开发者、AI Agent 和架构分析的项目上下文文件，并在后续开发中安全刷新自动识别区块。

增强版重点不是生成“简介型 AGENTS”，而是生成一份**约束型 AGENTS.md**，尽量把调用链、架构边界、高风险文件、禁止操作和探索建议沉淀出来。

## 工作模型

Context 采用三层职责，不以硬编码 profile 作为项目识别白名单：

1. **确定性 Evidence Collector**：只收集目录、文件类型、配置、入口候选和仓库快照指纹，不下架构结论。
2. **AI Semantic Analyzer**：阅读真实代码，输出带证据路径和置信度的结构化分析。
3. **Deterministic Validator / Writer**：验证证据没有越界、命令有来源、仓库快照未漂移，再按固定 Markdown 标题安全更新章节。

内置 profile 是无 AI 调用时的兼容回退，以及高风险领域的增强规则，不决定项目“能否被识别”。当前增强 profile 包括：

- `Qt Client (Windows/Linux) -> Shared C++ Core`
- `WPF`
- `Harmony`
- `Win32` 应用
- `WPF + NativeBridge` 这类维护态混合项目
- **`Go` 后端服务**
- **`Flutter` 跨端客户端**
- **`Node.js / TypeScript` 前端工具链与 SDK**
- **`Node.js` 插件类项目 (含 `plugin.json`)**
- **`Python / FastAPI` 后端服务**

对 Qt / WPF / Win32 这类依赖共享 C++ 底层的高风险项目，还应额外输出：

- Qt UI / Controller / wrapper 到 Shared C++ Core 的调用链候选
- Shared C++ Core、导出头文件、CMake 构建入口等自动识别候选
- `DllImport` / `MarshalAs` / callback / observer / Win32 API 等自动识别候选
- “需人工确认”的边界项，例如 ABI、线程模型、句柄生命周期、Qt signal/slot 跨线程调用、可信验证命令

对 Go 后端服务，还应额外输出：

- 核心分层设计（如 `cmd`, `internal`, `pkg`）
- 关键模块依赖流向及防循环依赖约束

对 Flutter 客户端，还应额外输出：

- 状态管理方案和平台通道（Platform Channels）调用链
- 原生目录（`android`, `ios` 等）中包含的特定平台实现与边界

对 Node.js 插件与工具链，还应额外输出：

- 工作空间（Workspace）包间依赖及入口点
- `plugin.json` 约定的生命周期及扩展点隔离要求

对 FastAPI 后端服务，还应额外输出：

- ASGI 应用入口、router 注册和 service/core 调用链候选
- 依赖安装、pytest 验证与 uvicorn 运行命令候选；无独立编译或打包步骤时 build 明确为 `N/A`
- 路由契约、认证配置、数据库迁移和敏感日志边界

遇到未列出的语言或框架时，**不得因为 profile 缺失而停止**。只要仓库证据充分，AI 应按同一语义分析协议识别；不能确认的单项才标记 `Unknown`。



## Preamble — 读取项目约束

```bash
_LESSONS="$(git rev-parse --show-toplevel 2>/dev/null)/LESSONS.md"
if [ -f "$_LESSONS" ]; then
  echo "=== LESSONS — 项目 AI 犯错约束（Top 10 高频，完整规则见 LESSONS.md）==="
  _py=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
  if [ -n "$_py" ]; then
    "$_py" - "$_LESSONS" <<'PYEOF'
import sys, re
path = sys.argv[1]
text = open(path, encoding='utf-8').read()
m = re.search(r'## \u6d3b\u8dc3\u89c4\u5219[^\n]*\n((?:.*\n)*?)(?=## |\Z)', text)
rows = [l for l in (m.group(1).splitlines() if m else []) if l.startswith('| L')]
def cnt(r):
    try: return int(r.split('|')[5].strip())
    except: return 0
top = sorted(rows, key=cnt, reverse=True)[:10]
if top:
    print('| ID | \u89c4\u5219 | \u7c7b\u578b | \u89e6\u53d1\u6b21\u6570 | \u6700\u8fd1\u89e6\u53d1 |')
    print('|----|------|------|---------|---------|')
    for r in top: print(r)
    if len(rows) > 10: print(f'...\uff08\u5171 {len(rows)} \u6761\u6d3b\u8dc3\u89c4\u5219\uff09')
else:
    print('(\u6682\u65e0\u6d3b\u8dc3\u89c4\u5219)')
PYEOF
  else
    cat "$_LESSONS"
  fi
  echo "==="
fi
```

## 适用场景

- 新仓库第一次接入 AI 辅助开发
- 项目开发一段时间后，需要刷新自动识别的结构、命令候选和约束索引
- 需要补齐 `README.md`、`AGENTS.md`、`ARCHITECTURE.md`
- 需要让 AI 更快理解目录结构、语言、构建系统和模块关系
- 需要用固定模板产出可解析上下文文件

## 输入要求

至少需要以下输入：

- 目标仓库根目录
- 操作模式：首次初始化使用 `scan`，后续同步使用 `refresh`
- AI 语义分析文件：按 `evidence` 输出中的 `analysis_contract` 生成

## 输出契约

输出必须满足以下约束：

- 所有分析都基于真实代码、真实目录结构和真实配置文件
- 所有非 `Unknown` 的 AI 结论必须携带至少一个仓库内证据路径，可附行号（如 `src/main.py:42`）
- 包含“所有、必须、禁止、只能、不得”的强约束必须引用精确行号，并执行反证搜索
- 每个 AI 结论必须标记 `high`、`medium` 或 `low` 置信度；低置信度结论只能进入“需人工确认”，不得渲染成事实
- build / run / quick / bugfix / full 等命令没有仓库内证据时必须拒绝，不得用生态惯例猜测
- install、build、run、quick、bugfix、full 必须按真实语义区分；依赖安装不得冒充构建
- 证据明细保留在分析 JSON 中，不得把 `AI field[index] [confidence]` 等内部审计字段写入 AGENTS/HARNESS
- AI 分析必须绑定 `evidence_fingerprint`；仓库在分析后发生漂移时必须重新扫描，不得写入旧结论
- 无法确认的信息必须写成 `Unknown`
- 只按固定 Markdown 模板输出
- 产物仅限：
  - `README.md`
  - `AGENTS.md`
  - `ARCHITECTURE.md`
  - `HARNESS.md`
- **严禁修改任何文件的编码格式**（UTF-8 / UTF-8 BOM / UTF-16 / GBK / GB2312 / Latin-1 等）。若编码变更看似必要，必须先获得人工确认，不得绕过
- `scan` 只创建缺失文件，现有文件即使使用 `--force` 也不得覆盖
- `refresh` 只更新模板契约列出的固定 Markdown 章节，其他章节和标题之外文本归用户所有
- 生成文件不得注入 `dev-harness:managed` 或其他 HTML 注释标记
- `AGENTS.md` 的“项目规范索引”只记录专业文档路径，不复制 Git、代码、发布或 changelog 规则正文
- 识别已有 Git 工作流、代码规范、发布规范和 changelog 文档；Context 不负责创建这些专业文档
- 旧版合法 `dev-harness:managed` 标记在首次刷新时自动移除，标记正文保持不变
- 固定标题缺失、重复、层级变化、混合换行、未知编码或损坏旧标记必须停止写入并报告错误

## 顺序化步骤

1. 运行 `dev-harness-context evidence <repo-path>`，读取 JSON 证据清单和 `evidence_fingerprint`
2. 若 `truncated` 为 `true`，立即停止；不得在不完整仓库视图上生成上下文
3. AI 根据 `important_files`、`source_candidates` 和真实目录继续读取入口、依赖、测试、CI、构建脚本及关键模块
4. AI 生成符合 `analysis_contract` 的 JSON；非 `Unknown` Claim 必须包含 `value`、`confidence`、`evidence`，README 核心模块通过 `core_modules` 提供真实职责
5. 对每个强约束执行反证搜索；主动检查相同能力的其他实现、启动副作用、事务、旁路调用和异常路径，发现反例后收窄结论
6. 对高风险候选逐项分类，至少覆盖应用启动、数据库/schema、认证授权、外部调用、锁与重试、文件写入、子进程、服务安装和不可信输入输出
7. 生成四份文档的内存预览并检查命令分类、模块职责、绝对路径、动态测试数量、模板术语、重复内容和内部字段名
8. 将分析 JSON 写入工作区外的临时路径，不得把扫描中间产物提交到目标仓库
9. 首次初始化运行 `scan <repo-path> --analysis <analysis.json>`；后续同步运行 `refresh <repo-path> --analysis <analysis.json>`
10. Validator 负责证据路径与行号、快照指纹、字段白名单和命令来源校验；校验失败时停止，不得绕过
11. 无法确认的项保持 `Unknown`，不适用项写 `N/A`，空列表不得渲染成 `- Unknown`
12. 在 `AGENTS.md` 中优先输出约束信息：调用链、架构边界、高风险文件、禁改规则、探索建议和证据不足项
13. 内置 profile 只补充框架特有风险；新的语言或框架不要求先修改扫描器代码
14. 首次初始化只创建缺失文件；后续刷新先展示固定章节差异，再按确认结果原子写入

## 固定模板要求

生成内容时按以下优先级选择模板：

1. 目标仓库覆盖模板（兼容旧项目，可选）：
   - `templates/context/README.template.md`
   - `templates/context/AGENTS.template.md`
   - `templates/context/ARCHITECTURE.template.md`
   - `templates/context/HARNESS.template.md`
2. 若目标仓库模板缺失或不完整，回退到 skill 自带模板（源码中位于 `context/templates/`，安装后位于 skill 根目录的 `templates/`）：
   - `templates/README.template.md`
   - `templates/AGENTS.template.md`
   - `templates/ARCHITECTURE.template.md`
   - `templates/HARNESS.template.md`

不得擅自扩展字段，不得输出模板之外的解释性文字。仓库覆盖模板必须保留对应文件的固定章节标题及层级；标题是刷新定位契约。

## CLI

安装后的最小运行入口为：

```bash
dev-harness-context evidence <repo-path>
dev-harness-context scan <repo-path>
dev-harness-context scan <repo-path> --analysis <analysis.json>
dev-harness-context refresh <repo-path>
dev-harness-context refresh <repo-path> --analysis <analysis.json>
```

默认行为：

- `evidence` 输出通用仓库证据、分析字段契约和快照指纹，不输出框架结论
- `scan` / `refresh` 传入 `--analysis` 时，优先使用经验证的 AI 语义分析；未传入时保留内置规则回退以兼容脚本和离线调用
- AI Agent 调用本 skill 时默认必须走 `evidence` + `--analysis` 主路径，不得仅凭规则回退的 `Unknown` 宣告无法识别项目
- `scan` 仅在上下文文件缺失时创建；已有同名文件保持原样，返回码 `2` 提示改用 `refresh`
- `scan --force` 为兼容旧调用保留，但仍不得覆盖现有文件
- `refresh` 按固定 Markdown 标题比较和更新章节，保持其他章节、原编码/BOM、CRLF/LF、末尾换行状态和文件权限
- 新增或调整项目自己的 Git、代码、发布、changelog 文档后，运行 `refresh` 更新 AGENTS 索引
- 代码规范只识别现有文档，不根据 formatter/linter 配置自动生成规则文档
- `CHANGELOG.md` 不由 Context 创建；它由用户确认后或首次发布流程通过 `dev-harness-git-workflow` 初始化
- 非交互 `refresh` 发现差异时只输出预览并返回 `2`；`refresh --force` 可直接应用成功定位的固定章节更新
- 交互刷新支持 `y` / `n` / `all` / `none` / `quit`；`quit` 返回 `130`
- 旧版合法 managed 标记会在刷新时无损移除；损坏标记直接报错，不猜测修复
- 不得暴露“兼容模式”之类的自定义术语；仓库模板缺失时应直接回退到 skill 自带模板继续生成，不再额外询问模板模式选择

## 停止条件

- 无法访问目标仓库
- 仓库结构扫描结果被截断
- 关键配置文件无法读取
- 文件缺少固定章节标题、同名标题重复或标题层级变化
- 文件包含混合换行、无法解码的编码、重复/嵌套/不闭合旧标记或未知旧标记版本
- 仓库模板缺失且 skill 自带模板也不可用
- AI 提议或尝试修改文件编码且用户未明确确认

满足任一条件时，必须停止并向用户报告阻塞原因。

## 交接边界

- 可作为 `dev-harness-auto-fix` 的前置上下文补充能力
- Git、提交、tag、发布与 changelog 规范的识别/初始化决策交给 `dev-harness-git-workflow`
- 不负责修 bug、补测试或定义验证命令
- 不得臆测架构模式、模块职责或接口关系
- 不得擅自转换文件编码；若检测到编码不一致，应标记到 AGENTS.md 第 4 节交由人工决策
