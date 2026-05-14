---
name: dev-harness-commands
description: Use when you need to standardize build, test, quick, bugfix, and full verification entry points for an existing client project without rewriting its toolchain
---

# dev-harness-commands

负责把已有客户端项目里的构建、测试和验证入口收敛成统一的 harness 命令约定。



## Preamble — 读取项目约束

```bash
_LESSONS="$(git rev-parse --show-toplevel 2>/dev/null)/LESSONS.md"
if [ -f "$_LESSONS" ]; then
  echo "=== LESSONS（项目历史 AI 犯错规则，视为硬约束）==="
  cat "$_LESSONS"
  echo "==="
fi
```

## 适用场景

- 项目已经能构建或测试，但入口分散
- AI 不知道该跑哪个命令验证改动
- 同一个项目里存在多套脚本、多个构建方式或多平台命令
- 需要把项目映射成稳定的 `build / test / quick / bugfix / full` 五类入口

## 输入要求

至少需要以下输入：

- 目标仓库根目录
- 真实存在的构建文件、脚本文件或命令入口
- 当前项目的最小验证方式

若项目没有任何可执行命令，必须明确报缺，不得伪造命令。

## Windows 终端前置检查

在映射、书写或指导用户执行 **harness 相关本地 shell 命令** 前，若判定宿主为 **Windows**（例如用户信息含 `win32`、`Windows 10/11`，或工作区路径为 `X:\...` 等）：

1. **识别集成终端类型**：是否为主流 **cmd（命令提示符）** 或 **PowerShell**（含 Windows PowerShell 与 PowerShell 7+）。可依据 `user_info` 中的 Shell、Cursor/VS Code 默认终端配置或用户自述。
2. **若当前为 Git Bash、MSYS2、Cygwin、WSL、或与上述类似的类 Unix 环境（例如在 Windows 上 Shell 显示为 `bash` / `zsh`）**：必须先**明确提示用户**将 Cursor/VS Code 的**默认终端**改为 **命令提示符** 或 **PowerShell**，再执行或代跑构建/测试类命令；说明此类终端下易出现 Windows 路径与 POSIX 语义混用、引号/换行转义差异、子进程管道挂起或原生工具链不兼容，从而导致大量报错或**卡死**。
3. **执行策略**：在用户完成切换或明确声明「已在 cmd/PowerShell 中执行」之前，对长时间、高风险的验证命令应避免盲跑；可仅给出 **cmd/PowerShell 写法** 的命令供用户手动粘贴。若无法判断终端类型但用户报告命令异常或挂起，应优先追问终端类型并给出上述切换指引。
4. **中文环境控制台编码（简体 Windows）**：许多原生/旧式工具链的控制台输出按 **GBK**（代码页 **936**；与 **GB2312** 常见文本兼容）写入，而集成终端、PowerShell 或 `chcp 65001`（UTF-8）会话若与上述输出**编码不一致**，会出现**中文乱码**，并可能导致日志证据无法比对或误判失败。须提示用户：优先保证「工具输出编码 ↔ 当前控制台代码页 / 终端解码」一致；在 cmd 下可用 `chcp` 查看，需与 GBK 语义对齐时通常使用 **936**（`chcp 936`）；PowerShell 下注意 `[Console]::OutputEncoding`、管道与外部程序输出的编码是否与 **GBK** 一致；解读或粘贴 harness 日志证据时应声明当时的代码页/编码，避免在 UTF-8 假设下误判 GBK 输出。

> ⚠️ **HARD STOP（执行侧）**：在已判定为 Windows 且非 cmd/PowerShell 时，不得在未提示用户切换终端的情况下，代用户启动可能长时间阻塞的 harness 验证命令。

## 输出契约

输出必须至少包含：

- **BuildCommand**：标准构建入口
- **TestCommand**：自动化测试入口（平台可自动执行时映射；需设备/模拟器时标记 `device-required` 或 `manual-only`）
- **QuickCommand**：最快反馈入口
- **BugfixCommand**：本次问题专属验证入口
- **FullCommand**：完整验证入口
- **Evidence**：这些命令来自哪些真实文件或配置
- **MissingCommands**：缺少哪些命令仍需人工补齐

## 统一命名约定

V1 统一按以下逻辑表达，不强制项目一定改成某种技术栈格式：

- `harness:build`
- `harness:test`
- `harness:quick`
- `harness:bugfix`
- `harness:full`

上面 5 个名字代表的是**稳定语义层**，不是要求所有仓库都必须使用相同脚本系统。它们可以映射到：

- WPF:
  - 本地 `build` / `quick` 优先映射到项目级 `dotnet build <project>.csproj`
  - 本地 `test` 优先映射到 `dotnet test <test-project>.csproj --no-build`（无设备依赖，可自动执行）
  - 本地 `full` 优先映射到 solution 级 `dotnet build <solution>.sln` 或等价全量依赖编译链
- Win32:
  - 本地 `build` / `quick` 优先映射到项目级 `msbuild <project>.vcxproj /p:Configuration=Debug`
  - 本地 `test` 优先映射到 `vstest.console.exe <test-dll>` 或 `ctest --output-on-failure`（无设备依赖，可自动执行）
  - 本地 `full` 优先映射到 solution 级 `msbuild <solution>.sln /m /p:Configuration=Debug`
  - 本地 `full` 默认不等于打包，安装包、签名或发布物应单独标记为 `package/release-only`
- Qt:
  - 本地 `build` / `quick` 优先映射到 `cmake --build <build-dir>` 或项目级构建
  - 本地 `test` 优先映射到 `ctest --output-on-failure`（桌面端无设备依赖，可自动执行）
  - 本地 `full` 优先映射到 `cmake --build + ctest` 全量链路
- Harmony:
  - 本地快速构建优先映射到 `hvigorw assembleHap --mode module -p product=default -p buildMode=release --no-daemon`
  - 本地 `test` → `device-required`（需连接鸿蒙设备/模拟器，不能自动执行）
  - 本地 `full` 优先映射到 `hvigorw assembleApp --mode project -p product=default -p buildMode=release --no-daemon` 或等价全量编译链
  - 若仓库存在 `buildScript/app_build.sh` + `buildScript/*_package.py`，应标记为 `package/release-only` 或 CI 打包链，不应占用本地 `full`
- Android:
  - 本地 `test` → `device-required`（需连接设备/模拟器，不能自动执行）
- 其他客户端项目：映射到真实存在的自定义脚本

### 测试命令平台门控规则

| 平台 | TestCommand 状态 | 说明 |
|------|-----------------|------|
| Qt (Windows/macOS/Linux 桌面) | ✅ 自动执行 | `ctest --output-on-failure`，无设备依赖 |
| WPF / WinForms | ✅ 自动执行 | `dotnet test` / `vstest.console.exe`，无设备依赖 |
| Win32 C++ | ✅ 自动执行 | `ctest` / `vstest.console.exe`，无设备依赖 |
| Harmony | ❌ device-required | 需鸿蒙设备或模拟器，跳过自动测试 |
| Android | ❌ device-required | 需 ADB 连接设备或模拟器，跳过自动测试 |
| iOS | ❌ device-required | 需 macOS + 设备/模拟器，跳过自动测试 |

## 顺序化步骤

1. 扫描真实构建入口、测试入口和本地脚本
2. 判断哪些命令可以安全映射为 `build / test / quick / bugfix / full`
3. 把映射结果写入 `HARNESS.md` 或等价上下文文件
4. 报告缺失项和不可自动推断项
5. 若命令不存在，只能标记 `Unknown` 或 `Missing`，不得编造

## 停止条件

- 仓库中没有任何可识别构建入口
- 现有命令需要私有环境但无法验证
- 无法判断 quick 与 full 的职责边界
- 输出证据被截断

满足任一条件时，必须停止并说明缺失项。

## 交接边界

- 可作为 `dev-harness-context` 生成 `HARNESS.md` 后的补强能力
- 向 `dev-harness-verify` 提供 build / test / quick / bugfix / full 的命令基础
- 不负责 UI 自动化
- 不负责直接改写项目 CI
