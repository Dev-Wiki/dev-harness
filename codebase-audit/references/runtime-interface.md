# 批量执行与文档生成

`runtime.py --help` 是命令事实源；本页定义结构化输入，通常无需读取 runtime 源码。旧单项命令保留兼容；新运行优先用 `batch`、`validate-outputs`、`render-output`。它们不降低 Finding 验证、漂移或跨模块门禁。

## 命令与输入

以下命令使用项目已确认的 Python 入口，`<runtime>` 为本 Skill 的 runtime.py，`<fp>` 必须是当前重新计算的 Context 指纹。示意参数需替换为真实路径和值。

```text
python <runtime> init --repo <repo> --run-id <run> --context-fingerprint <fp> --scope <scope> --docs-root docs --summary
python <runtime> batch --repo <repo> --run-id <run> --context-fingerprint <fp> --input <batch.json>
python <runtime> render-output --repo <repo> --run-id <run> --context-fingerprint <fp>
python <runtime> status --repo <repo> --run-id <run> --summary
python <runtime> validate-outputs --repo <repo> --run-id <run> --input <paths.json>
```

- `batch` 输入包含 `tasks`、`findings`、`document` 中至少一个。数组非空、同类 ID 不重复；全部校验通过才写入一次 Revision。任一项无效时整批不落盘；漂移仍持久化 STALE。事务不包含长时间测试/源码读取，不跨 Task 开始时的门禁。
- 新命令默认返回摘要。旧 `init/resume/status/checkpoint/upsert-finding/checkpoint-cross-module/complete` 加 `--summary`，避免每次把整份 state 灌回模型。
- `--input` 接受 UTF-8 JSON 文件（兼容 BOM），或默认 `-` 从 stdin 读取。输入文件放 Git 私有运行目录或临时目录，用补丁工具写一次、按任务增量更新；不要把 JSON 多次嵌套到 PowerShell/JavaScript 命令字符串中。
- `validate-outputs` 输入为合法 JSON 数组，例如 `["Dashboard.md", "Report.md"]`，路径相对于 **audit 根**，不带 `docs/audit/` 前缀。一个进程校验整组，禁止每个路径起一个进程。`render-output` 已校验其全部输出，无需再逐个验证同一组路径。
- 两个状态批次之间发生代码、Context 或 HEAD 变化时重新核验；不要重复使用旧 `<fp>` 来冒充 Context 重算。
- 批次调用同步完成后读取摘要。工具返回 running 时等待其 completion；不能把 yield 视为成功。
- 同一运行保持单个状态写入方；batch 保证该批校验失败不部分发布，不提供多进程并发事务或状态锁。

## 数据约定

Task 的 `checkpoint` 保存计划、结果和恢复位置；每次更新按完整 checkpoint 替换。`document` 按顶层字段合并，`findings` 按 ID 合并。新建空白运行时先登记 document 和任务，再渲染简短进行中产物；无需提前填充结果模板。

以下是单任务数据形状示例。文字必须替换为真实观察，不可把示例当作审计证据。

```json
{
  "document": {
    "output_language": "zh-CN",
    "context": ["README.md、ARCHITECTURE.md、HARNESS.md 的实际来源与范围"],
    "discoverability": {
      "hub": "docs/README.md",
      "status": "docs-refresh-required",
      "handoff": "由 dev-harness-docs 在 docs/README.md 增加指向 audit/Report.md 的简短入口"
    },
    "focus": "A01 入口与错误传播",
    "summary": "检查范围、当前结论及未实测平台；不宣称未检查范围安全"
  },
  "tasks": [{
    "task_id": "A01",
    "status": "in-progress",
    "checkpoint": {
      "title": "入口与持久化",
      "scope": "本任务范围与待回答的行为问题",
      "basis": "Context 章节及证据",
      "entry_points": ["app.py:1"],
      "boundaries": ["入口 → 状态写入；两端及相关 Task"],
      "exclusions": "明确排除项及原因；无则明确写无",
      "strategy": "入口搜索、调用链、反证和必要行为验证",
      "dependencies": "无",
      "result": {
        "coverage": "实际检查的入口、链路和两端",
        "evidence": ["path:line 或 command + 实际观察"],
        "candidates": "本地 ID、主张、状态和 AUD ID；无候选也说明检查结论",
        "counter_evidence": "实际检查的旁路与保护条件",
        "gaps": "未覆盖范围或阻塞；无则明确写无",
        "cross_module": "边界两端、相关任务和待复核问题"
      }
    }
  }]
}
```

完成/受阻 Task 的 result 必须含以上六个字段；计划还必须含 title/scope/basis/entry_points/boundaries/exclusions/strategy。复核完成前填好 document.summary，说明结论和覆盖限制。正文可为字符串、列表或对象；正文语言由 AI 保证，renderer 只翻译固定标题和状态。复杂边界证据可用对象/列表表达，不在各文档重复写同一结论。

Finding 沿用 [finding-contract.md](finding-contract.md)。`findings` 数组每项是现有 `upsert-finding` 对象：`id/status/severity/category/summary/claim/evidence_paths_lines/relevant_call_chain_data_flow/counter_evidence_checked/risk_impact/confidence/suggested_next_action/snapshot`，加 `source_task`、别名、根因、owner、修复边界与 identity 证据（有则记录）。`snapshot` 使用 init 的 Snapshot fingerprint，`evidence_paths_lines` 用 `{"path":"app.py","lines":"1-3"}` 或 `{"command":"...","observation":"..."}`。confirmed 保留全部原门禁；resolved 需重新验证修复证据，不能只改状态名。

修复后的新运行先导入原问题，再提交验证结果，两个批次之间执行实际验证：

```json
{"findings":[{"id":"AUD-001","status":"stale","source_run_id":"original-run"}]}
```

```json
{"findings":[{"id":"AUD-001","status":"resolved","resolution":{
  "snapshot":"<修复后当前 Snapshot fingerprint>",
  "change_summary":"<实际修复及依据>",
  "verification_status":"passed",
  "evidence_paths_lines":[{"command":"<实际验证命令>","observation":"<修复后观察与退出结果>"}]
}}]}
```

`source_run_id` 必须能读取本仓库原运行中同 ID 的历史确认记录。导入保留原主张与快照；不能用不存在的问题、旧快照、失败验证或空证据登记解决。原快照和修复后快照分别在 Finding 的 `snapshot` 与 `resolution.snapshot` 中保存。

## 写入与完成

1. 每个 Task 开始前校验工作区，结果形成后将 checkpoint 和相关 Finding 放在同一批提交；当批已内部校验时不再紧邻调用一次独立 verify-workspace。工作过程中及时保存已有证据，不积累到最终答复之后补记。
2. 所有结果登记完后，按 cross-module-review.md 做语义复核；用 `checkpoint-cross-module ... --review-status completed --evidence-json <JSON> --summary` 保存边界、矛盾、identity、完整链路和缺口。之后改任务、Finding 或 document 会使旧复核失效。
3. `render-output` 从状态生成 Dashboard、Findings、Report、`tasks/A01.md` 和 `results/A01.md` 等。Snapshot 全表只在 Dashboard，其他文件引用它；Finding 正文只生成在 Findings。固定 UI 由代码维护，AI 只写调查结果。
4. 检查生成结果、互链和覆盖后执行 `complete ... --summary`，再运行一次 `render-output` 将状态显示刷新为已完成。配置了 document 的运行，complete 会检查本 Revision 已渲染且输出未经修改；不能再出现 state 完成但磁盘仍是初始化骨架。
5. 最后一次渲染失败时明确报告文档未收口，不能称产物已完成。渲染本身不修改 Task、Finding 或 CrossModuleReview，不触发重复复核。

输出只能在 `<docs-root>/audit/**`，生成文件按字节未变则不写。每个文件原子替换，私有 `rendered.json` 保存 hash 与已渲染 Revision，可在中断后重试。整组文件不是跨文件原子事务；失败时不会获得当前 Revision 的完成凭据。

已有手写文档或其他运行产物与生成内容不同，renderer 拒绝覆盖；本轮生成文件被外部改动也拒绝覆盖。先读旧产物并按既有模板增量维护，或明确完成保留与迁移，再启用自动生成。不要删除用户旧审计文档来让渲染通过。恢复旧运行没有 document 时可继续原有手写流程，旧 API 不强制迁移。
