# Context 平台增强指南

Profile 只用于补强证据收集和风险提示，不能决定陌生技术栈是否可被理解。

通用仓库证据识别出可能的平台后，只读取与该平台相关的条目。

- 包含共享原生代码的 Qt / WPF / Win32：沿 UI 或控制器 → wrapper/interop → 共享 C++ 核心追踪调用链，并将 ABI、所有权、句柄、回调、消息循环、条件编译和线程边界列入人工确认项。
- Harmony：识别 ArkUI/ArkTS 入口、product/target 构建变体、NAPI/原生桥接、生命周期、打包、签名和设备要求。
- Go：识别 `cmd` 入口、`internal` / `pkg` 依赖、持久化、并发、CGO 和包循环依赖风险。
- Flutter：识别状态归属、Platform Channels、原生平台实现、生命周期和仅设备可执行的验证。
- Node.js / TypeScript：识别 workspace 依赖、包入口、插件清单、生命周期钩子和供应链脚本。
- FastAPI：识别 ASGI 入口、路由注册、service/core 调用链、依赖注入、认证、迁移、外部集成以及 pytest/uvicorn 证据。没有独立构建步骤时使用 `N/A`。

其他技术栈也沿用“证据收集器（Evidence Collector）→ AI 语义分析器（AI Semantic Analyzer）→ 确定性校验与写入器（Deterministic Validator / Writer）”路径。仅将证据不足的单项标记为 `Unknown`，不得因缺少 profile 而停止。
