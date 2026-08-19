# CLIENT_PROJECT_ONBOARDING

用于把一个从未做过 AI 工程化的客户端项目接入 `dev-harness`。

## 1. 接入目标

V1 目标不是自动化一切，而是先让 AI 具备最基本的工程操作能力：

- 知道项目是什么类型
- 知道从哪里开始读代码
- 知道如何构建
- 知道如何做 quick / bugfix / full 验证
- 知道哪些区域不能随便改

## 2. 最小接入产物

接入后，仓库中至少应存在以下上下文文件：

- `README.md`
- `AGENTS.md`
- `ARCHITECTURE.md`
- `HARNESS.md`

如果这些文件缺失，可先通过 `dev-harness-context` 初始化。

`AGENTS.md` 只保留轻量的“项目规范索引”。以下专业文档按项目需要存在，不要求全部创建：

- Git 工作流：项目已有规范，或确认后由 `dev-harness-git-workflow` 初始化的 `docs/GIT_WORKFLOW.md`
- 代码规范：项目已有的 `docs/CODE_STYLE.md`、`CODE_STYLE.md` 或 contribution 文档；Context 只识别，不自动生成
- 发布规范：`docs/RELEASE.md`，也可以继续放在 `docs/GIT_WORKFLOW.md`
- 变更日志：`CHANGELOG.md`；仅在确认初始化或开始首次发布时创建

新增或移动这些文档后运行 `dev-harness-context refresh <repo-path>`，只更新 AGENTS 托管索引，不覆盖人工内容。

项目存在较多深度文档时，使用 `dev-harness-docs` 复用已有 `doc/` 或 `docs/` 根目录，建立文档中心入口、按读者任务组织的渐进式导航、SSOT 与归档规则。当前功能信息分散、不同角色/平台/版本支持范围不一致或无法可靠统计时，按需建立 Capability Catalog；已有同类功能说明文档时直接复用。项目较小时保持单层索引即可，不强制创建空目录、`nav/` 或功能清单目录。

Codebase Audit 的固定入口是 `<docs-root>/audit/Report.md`。Audit 只维护 `audit/` 内的证据；若文档中心尚未链接该入口，由 Docs Refresh 幂等补一条导航，根 README 快捷链接可选。

常用触发方式：

```text
# 功能范围已经零散在多个文档时
盘点这个仓库当前已支持的功能，必要时建立或刷新 Capability Catalog

# 开始大型代码库审计，并保证结果能从文档中心找到
基于项目 Context 初始化 codebase audit；若文档中心缺少 audit/Report.md 入口，先刷新文档导航
```

## 3. 首次接入检查

对客户端项目，至少补齐以下信息：

- **项目类型**：WPF / Harmony / Win32 / Qt / Unknown
- **主构建入口**
- **快速验证入口**
- **Bugfix 验证入口**
- **完整验证入口**
- **日志输出位置**
- **高风险目录**
- **禁止 AI 直接修改的区域**

## 4. 客户端项目特别关注点

### WPF

- `*.xaml` 与 `App.xaml` 往往影响 UI 资源合并与启动行为
- `*.csproj` 影响引用、打包和构建方式
- 本地 `full` 优先表示 solution 级全量 `dotnet build`，而不是安装包或发布打包
- 若没有测试，至少要固定一个最小构建和 smoke 验证命令

### Win32 应用

- `*.vcxproj`、`*.sln`、`*.rc` 往往决定构建链、资源打包和入口形态
- 含 `WinMain`、窗口消息循环、资源脚本时，应单独标记高风险
- 本地 `full` 优先表示 solution 级 `msbuild` 全量编译，不应把本地打包或安装器制作混进 `full`
- 若只是识别到 `Win32 API` 痕迹但命令入口不清晰，`HARNESS.md` 中应保持 `Unknown`，不得伪造

### Qt

- `CMakeLists.txt` / `*.pro` 决定构建拓扑
- `*.ui` 可能与生成代码联动
- 对资源文件和平台桥接层要单独标高风险

### Harmony

- `hvigor` 构建链和 `*.json5` 配置文件通常是关键入口
- 若仓库存在 `buildScript/app_build.sh` 与 `buildScript/*_package.py`，应把本地 `hvigorw assembleHap ...` / `hvigorw assembleApp ...` 与完整定制打包链分开记录
- 本地 `full` 应优先表示全量编译或全模块构建；Jenkins 打包链属于 `package/release-only`，不应直接占用 `HARNESS.md` 中的 `full`
- 模块定义、签名、打包配置默认属于高风险区域
- 若本地验证依赖设备或模拟器，必须在 `HARNESS.md` 写明

## 5. AI 可改动边界

至少给出以下分类：

- **可直接修改**：普通业务代码、非关键逻辑层
- **需人工确认后修改**：UI 资源、打包配置、原生桥接、签名相关
- **禁止直接修改**：生成目录、第三方依赖、私有构建产物

## 6. 完成定义

一个客户端项目完成 V1 接入，至少满足：

1. AI 能读到完整上下文文件
2. AI 能找到构建入口
3. AI 能找到 quick / bugfix / full 至少其中 2 个验证入口；缺失的明确写 `Unknown`
4. AI 知道高风险目录和禁改区域
5. 没有命令时，系统会报告缺失，而不是伪造完成
6. Git、代码、发布和 changelog 规范若存在，AGENTS 索引能指向其权威文档；不存在时明确为 `Unknown`
