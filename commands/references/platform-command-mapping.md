# 平台命令映射指南

仅在仓库证据已经识别出相关平台后读取本指南。以下内容只是映射启发，不是命令存在或可执行的证据。

## 桌面端与原生项目

- WPF：`build` / `quick` 优先映射到项目级 `dotnet build`，`test` 使用已有的 `dotnet test` 或 `vstest` 入口，`full` 使用解决方案级构建。
- Win32：`build` / `quick` 优先映射到项目级 MSBuild，`test` 使用已有的 `ctest` 或 `vstest`，`full` 使用解决方案级 MSBuild。打包、签名和安装程序归入 `package/release-only`，不能占用本地验证入口。
- Qt：优先使用仓库已有的 CMake preset 或构建入口；只有测试图确实存在时才使用 `ctest`。保留项目配置的 Qt Kit 和生成器。

## 移动端与设备依赖场景

- Harmony：按 product 和 buildMode 映射本地 Hvigor 模块级或项目级命令。设备测试标记为 `device-required`；打包脚本不能占用本地 `full`。
- Android/iOS：明确记录设备或模拟器、宿主操作系统、签名和构建变体要求。依赖设备的流程不得标记为可自动执行。
- Flutter：Dart 单元测试和组件测试可按证据映射为自动执行；`integration_test` 与原生桥接验证通常应标记为 `device-required`。

## 服务端与工具链

- Go：使用仓库已有的 `go build` / `go test` 入口，并保留包作用域。
- Node.js / TypeScript：使用真实存在的包管理器脚本和 workspace 作用域；生命周期脚本与安装脚本属于前置条件，不是验证证据。
- Python 服务：使用仓库已有的 pytest、tox 或 nox 入口。依赖安装命令不是构建命令；没有独立构建步骤的项目可使用 `N/A`。

## 平台 / 构建变体记录

同一语义命令存在多种实现时，应分别记录，不要把互不兼容的命令拼在一起：

```text
Purpose: build
Command: <repository-backed command>
WorkingDirectory: <repo-relative path>
Platform: PC | Phone | Windows | Linux | ...
Variant: Debug | Release | product name | ...
Preconditions: <toolchain or dependency>
DeviceRequirement: none | device-required | manual-only
Shell / Environment: <only when required>
Evidence: <path or successful run>
Status: candidate | confirmed | missing
```

简单仓库可继续使用旧版单值字段 `BuildCommand` / `TestCommand` / `QuickCommand` / `BugfixCommand` / `FullCommand`。这些字段名和枚举是内部契约，不翻译；面向读者的说明使用自然中文。
