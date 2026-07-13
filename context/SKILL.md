---
name: dev-harness-context
description: Use when you need to initialize or safely refresh AI project context by scanning a real repository and maintaining managed sections in README.md, ARCHITECTURE.md, HARNESS.md, and AGENTS.md
---

# dev-harness-context

负责扫描真实仓库结构，初始化面向开发者、AI Agent 和架构分析的项目上下文文件，并在后续开发中安全刷新自动识别区块。

增强版重点不是生成“简介型 AGENTS”，而是生成一份**约束型 AGENTS.md**，尽量把调用链、架构边界、高风险文件、禁止操作和探索建议沉淀出来。

当前优先支持的项目形态为：

- `Qt Client (Windows/Linux) -> Shared C++ Core`
- `WPF`
- `Harmony`
- `Win32` 应用
- `WPF + NativeBridge` 这类维护态混合项目
- **`Go` 后端服务**
- **`Flutter` 跨端客户端**
- **`Node.js / TypeScript` 前端工具链与 SDK**
- **`Node.js` 插件类项目 (含 `plugin.json`)**

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

## 输出契约

输出必须满足以下约束：

- 所有分析都基于真实代码、真实目录结构和真实配置文件
- 无法确认的信息必须写成 `Unknown`
- 只按固定 Markdown 模板输出
- 产物仅限：
  - `README.md`
  - `AGENTS.md`
  - `ARCHITECTURE.md`
  - `HARNESS.md`
- **严禁修改任何文件的编码格式**（UTF-8 / UTF-8 BOM / UTF-16 / GBK / GB2312 / Latin-1 等）。若编码变更看似必要，必须先获得人工确认，不得绕过
- `scan` 只创建缺失文件，现有文件即使使用 `--force` 也不得覆盖
- `refresh` 只更新 `dev-harness:managed` 标记内的自动识别内容，标记外文本归用户所有
- 无标记旧文件只能在交互终端中保守迁移；`--force` 不得绕过迁移确认
- 混合换行、未知编码或损坏标记必须停止写入并报告错误

## 顺序化步骤

1. 扫描仓库目录结构
2. 识别编程语言、构建系统、入口文件和核心模块
3. 搜索关键类、接口、模块边界和依赖关系
4. 无法确认的项标记为 `Unknown`
5. 在 `AGENTS.md` 中优先输出约束信息：调用链、架构边界、高风险文件、禁改规则（含文件编码约束）、探索建议
5b. 从仓库抽样生成「代码风格锚点」：真实文件路径 + 首条结构性声明截断行，约束 AI 对齐既有写法
6. 对 Qt -> Shared C++ Core / NativeBridge 项目，补充“自动识别候选”和“需人工确认”区块
6b. 对 Go、Flutter、Node.js 插件等项目，补充其特有的框架约束、组件识别候选和需人工确认的边界项
7. 额外生成 `HARNESS.md`，记录项目类型、build/quick/bugfix/full 命令、高风险目录、禁改区域、自动识别候选和需人工确认项
8. 首次初始化只创建缺失文件；后续刷新先展示托管块差异，再按确认结果原子写入

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

不得擅自扩展字段，不得输出模板之外的解释性文字。

## CLI

安装后的最小运行入口为：

```bash
dev-harness-context scan <repo-path>
dev-harness-context refresh <repo-path>
```

默认行为：

- `scan` 仅在上下文文件缺失时创建；已有同名文件保持原样，返回码 `2` 提示改用 `refresh`
- `scan --force` 为兼容旧调用保留，但仍不得覆盖现有文件
- `refresh` 只比较和更新托管块，保持块外用户内容、原编码/BOM、CRLF/LF、末尾换行状态和文件权限
- 非交互 `refresh` 发现差异时只输出预览并返回 `2`；`refresh --force` 可直接应用有效托管块更新
- 交互刷新支持 `y` / `n` / `all` / `none` / `quit`；`quit` 返回 `130`
- 无标记旧文件必须交互确认迁移，`refresh --force` 会保留文件并返回 `2`
- 不得暴露“兼容模式”之类的自定义术语；仓库模板缺失时应直接回退到 skill 自带模板继续生成，不再额外询问模板模式选择

## 停止条件

- 无法访问目标仓库
- 仓库结构扫描结果被截断
- 关键配置文件无法读取
- 旧文件没有托管标记且当前会话不可交互
- 文件包含混合换行、无法解码的编码、重复/嵌套/不闭合标记或未知标记版本
- 仓库模板缺失且 skill 自带模板也不可用
- AI 提议或尝试修改文件编码且用户未明确确认

满足任一条件时，必须停止并向用户报告阻塞原因。

## 交接边界

- 可作为 `dev-harness-pilot` 的前置补充能力
- 不负责修 bug、补测试或定义验证命令
- 不得臆测架构模式、模块职责或接口关系
- 不得擅自转换文件编码；若检测到编码不一致，应标记到 AGENTS.md 第 4 节交由人工决策
