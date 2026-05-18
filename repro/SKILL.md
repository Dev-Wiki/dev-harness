---
name: dev-harness-repro
description: Use when you need to extract reproducible steps, lock environment assumptions, and identify missing evidence before bugfix work starts
---

# dev-harness-repro

负责把“问题描述”收敛成“可重复执行的复现 harness 输入”。



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

- Bug 现象描述零散
- 有问题反馈但缺少稳定复现步骤
- 需要把手工复现转成脚本或固定命令
- 需要识别环境、数据、账号、设备等前置条件
- 客户端项目里需要区分 UI、资源、原生层、打包层的复现前置条件

## 输入要求

至少提供以下一项：

- Bug 描述
- 报错信息或日志片段
- 复现视频、截图、步骤
- 失败命令或失败请求

若输入不完整，必须先列缺失项，不得默认补全。

## 输出契约

输出必须结构化，至少包含：

- **Symptom**：实际现象
- **Expected**：预期行为
- **Preconditions**：环境、账号、数据、版本、开关
- **ReproSteps**：最小复现步骤
- **ReproCommand**：可执行命令；若无法命令化，明确说明原因
- **EvidenceGap**：还缺什么信息
- **RiskArea**：问题位于 UI、资源、原生层、打包层还是 Unknown

## Windows 终端前置检查

当 **ReproCommand** 需在 Windows 本机 shell 中执行或代跑时，遵守 `dev-harness-commands` 中的 **「Windows 终端前置检查」**（cmd/PowerShell 与 Git Bash 等差异，以及简体中文下 **GBK/936** 与输出编码一致），避免复现命令报错、卡死或中文乱码误判。

## 顺序化步骤

1. 提取现象、预期和影响面
2. 识别环境与前置条件
3. 收敛到最小复现步骤，剔除无关操作
4. 优先把步骤转成命令、脚本或固定输入
5. 标记仍无法稳定复现的原因
6. 对客户端项目，额外标记问题触发是否依赖 UI 交互、资源文件、平台桥接或打包产物

## 停止条件

- 没有最小复现步骤
- 无法判断必要环境
- 输入证据被截断
- 关键前置条件完全缺失
- 客户端项目缺少最基本的 quick / bugfix 入口，导致无法复现后验证

出现上述情况时必须停止，并明确告诉用户“先补复现，再继续”。

## 交接边界

- 向 `dev-harness-triage` 交付结构化复现结果
- 不负责根因分析
- 不负责设计回归测试
- 如果复现涉及设备、模拟器、签名、资源加载或打包差异，必须显式交给下游，不得省略