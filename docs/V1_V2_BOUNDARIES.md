# V1_V2_BOUNDARIES

## V1 定位

`dev-harness` V1 的目标是：让已有项目具备最基本、可执行的 AI 工程化接入与 bugfix 证据闭环。

适用项目：

- WPF 客户端
- Harmony 手机 / PC App
- Win32 应用
- WPF + NativeBridge + Win32 / C++ SDK 这类混合项目
- Qt 客户端（当前保留接入能力，但不作为本轮优先增强目标）
- Go、Flutter、Node.js 项目（按各自高风险边界门控）

V1 解决的问题：

- AI 第一次进入仓库时，不知道项目怎么读
- AI 不知道 build / quick / bugfix / full 应该跑什么
- AI 不知道哪些目录和文件是高风险区域
- AI 在 NativeBridge / Win32 / C++ SDK 上容易盲改
- Bugfix 没有固定的复现、定位、回归、验证基线
- AI 容易把已有工作区修改混入本轮修复或提交
- “已验证”和“已审查”没有绑定到最终代码 diff

## V1 已包含

### 1. 项目上下文初始化

- 生成 `README.md`
- 生成 `AGENTS.md`
- 生成 `ARCHITECTURE.md`
- 生成 `HARNESS.md`

### 2. 客户端项目准入能力

- 优先识别 `WPF / Harmony / Win32 / Unknown`
- 识别 `WPF + NativeBridge` 混合项目的基础特征
- 对 `Qt` 保留基础识别与安全回退
- 提取高风险目录与禁改区域
- 提取调用链候选、架构边界规则、禁止操作清单、探索建议

### 3. NativeBridge 风险显式化

- 识别 `*.vcxproj`
- 识别 `DllImport`
- 识别 `MarshalAs`
- 识别 callback / observer
- 识别 Win32 API 使用痕迹
- 输出“自动识别候选”
- 输出“需人工确认”

### 4. 命令语义层

- `harness:build`
- `harness:quick`
- `harness:bugfix`
- `harness:full`

### 5. Bugfix Flow 与可执行契约

- `dev-harness-auto-fix` 内联 repro / triage / regression / verify 四阶段参考
- analyze / fix / commit / unattended 四种显式授权模式
- 可证伪假设（Claim / Prediction / Probe / Observation / Status）
- 回归测试默认要求修复前 RED、修复后 GREEN
- review 与最终验证绑定 diff hash
- DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT 完成状态

`auto-fix/runtime.py` 把以下边界变为可执行、可测试行为：

- WorkspaceSnapshot 保存任务开始时的 HEAD、分支和已有修改指纹
- 已有 dirty worktree 可以保留，但 Agent 不得触碰
- AutoFixChangedFiles 只包含本轮对话产生的变更
- 状态保存在 Git 私有目录，支持进程中断后的阶段恢复
- 非法阶段跳转、未声明变更、已有修改漂移和提交越权会被拒绝

并已补上客户端项目的风险边界：

- UI 层
- 资源层
- 原生桥接层
- 打包层

## V1 明确不做

- UI 自动化
- 截图驱动验证
- 日志 / 指标 / Trace 平台接入
- 多 worktree 并行调度器（单个 worktree 的 Git 私有状态路径已支持）
- 自动 PR / 多 Agent review 调度器
- Native 层自动修复
- ABI / marshaling 正确性自动证明
- Win32 句柄 / 线程 / 消息循环的深语义验证

## V2 候选方向

### 1. Runtime Harness 编排

- 在现有 auto-fix 状态契约上增加每任务独立运行目录
- worktree 启动
- 运行状态探针
- 自动清理运行环境

### 2. Observability Harness

- 日志入口标准化
- 指标 / Trace 查询入口
- AI 可读的本地观测层

### 3. UI Harness

- 应用启动
- 截图
- 基础 UI 自动检查
- smoke 验证

### 4. NativeBridge 深化

- 自动抽取更细的 `Service -> Interface -> Bridge -> Native` 调用链
- 高风险文件评分
- 更细的 marshaling / callback / thread / handle 风险分类
- 人工确认结果持久化回写

### 5. Agent Loop Automation

- 自动 review
- 自动反馈修复循环
- 文档陈旧检测
- tech debt / doc gardening 任务

## 封板标准

满足以下条件即可视为 V1 封板：

1. 能生成 4 个上下文文件
2. 能输出 `build / quick / bugfix / full` 语义层
3. 能显式标出高风险区域与禁改边界
4. 对 NativeBridge 项目能输出“自动识别候选 / 需人工确认”
5. 不会在缺少命令或证据时伪造完成
6. 已有 dirty worktree 不会被本轮修复误改、误暂存或误提交
7. 完成证据与最终 diff 一致，代码变化会使旧证据失效
