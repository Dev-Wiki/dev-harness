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

## 3. 首次准入检查

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

一个客户端项目完成 V1 准入，至少满足：

1. AI 能读到完整上下文文件
2. AI 能找到构建入口
3. AI 能找到 quick / bugfix / full 至少其中 2 个验证入口；缺失的明确写 `Unknown`
4. AI 知道高风险目录和禁改区域
5. 没有命令时，系统会报告缺失，而不是伪造完成
