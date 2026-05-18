---
name: dev-harness-triage
description: Use when you need to trace the entry point, narrow the call chain, and assess whether current logs and signals are sufficient for root-cause analysis
---

# dev-harness-triage

负责从“可复现问题”收敛到“可验证的根因候选与证据链”。



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

- 已知如何复现，但不知道问题卡在哪
- 调用链长、模块多、上下文装载成本高
- 需要判断当前日志、错误码、埋点是否足够
- 需要找出最值得补的可观测性缺口
- 客户端项目里需要判断问题位于 UI 逻辑、资源加载、原生桥接还是打包配置

## 输入要求

输入必须来自 `dev-harness-repro` 或等价结构化结果，至少包含：

- 现象
- 最小复现步骤
- 环境信息

## 输出契约

输出必须至少包含：

- **EntryPoint**：入口函数、接口、事件或任务
- **CallChain**：关键调用链
- **Signals**：现有日志、错误码、trace、指标
- **RootCauseCandidates**：根因候选列表
- **MissingObservability**：缺失的日志、断言、埋点或上下文
- **ClientRiskLayer**：UI、资源、原生层、打包层或 Unknown

## 顺序化步骤

1. 找到入口位置
2. 追踪关键分支与状态变化
3. 记录能证明问题发生的位置与证据
4. 判断日志/错误码是否足以继续收敛
5. 给出最小可执行的补强建议
6. 对客户端项目，单独标记是否触及高风险层，必要时要求人工确认后再改

## 停止条件

- 入口不明确
- 调用链只有猜测，没有证据
- 关键状态不可见且无法补观测
- 无法区分业务错误和系统错误
- 涉及原生桥接、签名、资源打包或 UI 启动链，但没有足够证据区分具体层级

满足任一条件时，不得直接进入修复设计。

## 交接边界

- 向 `dev-harness-regression` 交付高风险路径和案例落点
- 可建议补日志或断言，但不直接定义最终验证命令
- 不声称根因已确认，除非有明确证据支撑
- 对客户端高风险层只做证据收敛，不得跳过人工确认直接下结论