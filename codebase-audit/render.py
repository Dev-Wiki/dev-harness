"""Compact Markdown views of audit state; no code analysis or inferred conclusions."""

import json
import re


def render_documents(state):
    document = state.get("Document", {})
    english = document.get("output_language", "zh-CN") == "en"

    def tr(zh, en):
        return en if english else zh

    labels = {
        "ACTIVE": "进行中", "COMPLETED": "已完成", "STALE": "已失效",
        "pending": "待开始", "in-progress": "进行中", "completed": "已完成",
        "blocked": "受阻", "candidate": "候选项", "needs-verification": "待验证",
        "confirmed": "已确认", "rejected": "已排除", "stale": "已失效", "resolved": "已解决",
    }

    def status(value):
        return value if english else labels.get(value, value)

    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    def prose(value):
        if isinstance(value, list):
            lines = []
            for item in value:
                rendered = prose(item)
                if isinstance(item, (list, dict)):
                    lines.append("-\n" + "\n".join("  " + line for line in rendered.splitlines()))
                else:
                    lines.append("- " + rendered.replace("\n", "\n  "))
            return "\n".join(lines)
        if isinstance(value, dict):
            lines = []
            for key, item in value.items():
                rendered = prose(item)
                if isinstance(item, (list, dict)) or "\n" in rendered:
                    lines.append(f"- {key}:\n" + "\n".join("  " + line for line in rendered.splitlines()))
                else:
                    lines.append(f"- {key}: {rendered}")
            return "\n".join(lines)
        return str(value)

    def section(zh, en, value):
        return f"\n## {tr(zh, en)}\n\n{prose(value)}\n"

    def table(headers, rows):
        return "\n".join(["| " + " | ".join(headers) + " |",
                          "| " + " | ".join("---" for _ in headers) + " |"] +
                         ["| " + " | ".join(cell(v) for v in row) + " |" for row in rows]) + "\n"

    def require(mapping, fields, where):
        if not isinstance(mapping, dict):
            raise ValueError(f"{where} must be an object")
        missing = [key for key in fields if not mapping.get(key)]
        if missing:
            raise ValueError(f"{where} requires: {', '.join(missing)}")

    require(document, ("context", "discoverability"), "document")
    discovery = document["discoverability"]
    require(discovery, ("hub", "status"), "document.discoverability")
    if discovery["status"] not in {"linked", "docs-refresh-required"}:
        raise ValueError("discoverability.status must be linked or docs-refresh-required")
    if discovery["status"] == "docs-refresh-required":
        require(discovery, ("handoff",), "document.discoverability")

    snapshot = state["AuditSnapshot"]
    tasks = state["Tasks"]
    findings = state["Findings"]
    review = state["CrossModuleReview"]
    finished = state["Status"] == "COMPLETED"
    if finished or review.get("Status") == "completed":
        require(document, ("summary",), "document")
    if finished and review.get("Status") != "completed":
        raise ValueError("completed report requires cross-module reconciliation")

    def nav(nested=False):
        prefix = "../" if nested else ""
        return "\n## " + tr("导航", "Navigation") + "\n\n" + " · ".join(
            f"[{tr(zh, en)}]({prefix}{path})" for zh, en, path in (
                ("看板", "Dashboard", "Dashboard.md"),
                ("问题登记表", "Findings", "Findings.md"),
                ("报告", "Report", "Report.md"))) + "\n"

    def snapshot_ref(nested=False):
        prefix = "../" if nested else ""
        return section("审计快照（Snapshot）", "Snapshot",
                       f"`{state['RunId']}` / `{snapshot['snapshot_fingerprint']}`\n\n"
                       f"[{tr('完整快照', 'Full snapshot')}]({prefix}Dashboard.md#snapshot)")

    discovery_text = table(
        [tr("文档中心", "Documentation hub"), tr("固定入口", "Audit entry"),
         tr("状态", "Status"), tr("交接", "Handoff")],
        [[discovery["hub"], snapshot["audit_output_root"] + "/Report.md",
          discovery["status"], discovery.get("handoff", tr("无", "None"))]])
    task_rows = []
    documents = {}
    task_fields = [("scope", "范围", "Scope"), ("basis", "分区依据", "Context basis"),
                   ("entry_points", "入口", "Entry points"), ("boundaries", "重要边界", "Boundaries"),
                   ("exclusions", "排除项", "Exclusions"), ("strategy", "证据策略（Evidence）", "Evidence strategy"),
                   ("dependencies", "依赖", "Dependencies")]
    result_fields = [("coverage", "实际覆盖", "Coverage"), ("evidence", "证据（Evidence）", "Evidence"),
                     ("candidates", "候选项与登记表映射", "Candidates and registry mapping"),
                     ("counter_evidence", "已检查反证", "Counter-evidence checked"),
                     ("gaps", "证据缺口", "Evidence gaps"),
                     ("cross_module", "跨模块复核输入", "Cross-module inputs")]
    for task_id, task in sorted(tasks.items()):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", task_id):
            raise ValueError("unsafe task ID for document rendering")
        checkpoint = task.get("checkpoint", {})
        require(checkpoint, ("title", "scope", "basis", "entry_points", "boundaries", "exclusions", "strategy"), task_id)
        result = checkpoint.get("result", {})
        if task["status"] in {"completed", "blocked"}:
            require(result, tuple(key for key, _, _ in result_fields), task_id + ".result")
        task_path, result_path = f"tasks/{task_id}.md", f"results/{task_id}.md"
        title = checkpoint["title"]
        task_rows.append([f"[{task_id} — {title}]({task_path})", status(task["status"]),
                          f"[{tr('结果', 'Result')}]({result_path})"])
        task_text = f"# {tr('审计任务', 'Audit task')} {task_id} — {title}\n" + nav(True) + snapshot_ref(True)
        task_text += f"\n{status(task['status'])} · [{tr('对应结果', 'Result')}](../{result_path})\n"
        for key, zh, en in task_fields:
            if key in checkpoint:
                task_text += section(zh, en, checkpoint[key])
        result_text = f"# {tr('审计结果', 'Audit result')} {task_id} — {title}\n" + nav(True) + snapshot_ref(True)
        result_text += f"\n{status(task['status'])} · [{tr('对应任务', 'Task')}](../{task_path})\n"
        for key, zh, en in result_fields:
            result_text += section(zh, en, result.get(key, tr("尚未记录", "Not recorded yet")))
        documents[task_path] = task_text
        documents[result_path] = result_text

    task_table = table([tr("任务", "Task"), tr("状态", "Status"), tr("结果", "Result")], task_rows)
    counts = {value: 0 for value in ("candidate", "needs-verification", "confirmed", "rejected", "stale", "resolved")}
    for finding in findings.values():
        value = finding["status"]
        counts[value] = counts.get(value, 0) + 1
    count_table = table([tr("问题状态", "Finding status"), tr("数量", "Count")],
                        [[status(key), value] for key, value in sorted(counts.items())])
    count_table += "\n" + table([tr("已确认问题级别", "Confirmed severity"), tr("数量", "Count")],
        [[severity, sum(f.get("status") == "confirmed" and f.get("severity") == severity for f in findings.values())]
         for severity in ("P0", "P1", "P2", "P3")])
    dashboard = f"# {tr('审计看板', 'Audit dashboard')}\n" + nav()
    dashboard += '\n<a id="snapshot"></a>\n'
    dashboard += section("审计快照（Snapshot）", "Snapshot", table(
        [tr("字段", "Field"), tr("值", "Value")],
        [["RunId", state["RunId"]], ["Status", status(state["Status"])], ["Revision", state["Revision"]],
         ["HEAD / branch", snapshot["base_sha"] + " / " + snapshot["branch"]],
         ["Context", snapshot["context_fingerprint"]], ["Snapshot", snapshot["snapshot_fingerprint"]],
         [tr("既有修改指纹", "Preexisting fingerprints"), json.dumps(snapshot["preexisting_fingerprints"], ensure_ascii=False)],
         [tr("范围", "Scope"), "; ".join(snapshot["scope"])], ["output_language", "en" if english else "zh-CN"]]))
    dashboard += section("任务状态", "Tasks", task_table) + section("问题计数", "Finding counts", count_table)
    dashboard += section("当前焦点与阻塞", "Focus and blockers",
                         status(state["Status"]) if finished else document.get("focus", status(state["Status"])))
    dashboard += section("文档可发现性", "Documentation Discoverability", discovery_text)
    dashboard += section("证据（Evidence）", "Evidence", document["context"])

    registry = f"# {tr('问题登记表', 'Finding registry')}\n" + nav() + snapshot_ref()
    registry += section("问题契约", "Finding contract", tr(
        "问题正文与 Evidence 仅维护于本登记表。confirmed 需当前快照、调用链、影响和反证；发布前必须完成跨模块复核。",
        "This registry owns finding details and Evidence. Confirmation requires current snapshot, flow, impact and counter-evidence; publication requires cross-module reconciliation."))
    registry_rows = []
    finding_sections = ""
    # Render every persisted field, including identity decisions and historical evidence.
    finding_labels = {"claim": ("主张", "Claim"), "evidence_paths_lines": ("证据（Evidence）", "Evidence"),
                      "relevant_call_chain_data_flow": ("调用链与数据流", "Call chain and data flow"),
                      "counter_evidence_checked": ("已检查反证", "Counter-evidence checked"),
                      "risk_impact": ("风险与影响", "Risk and impact"),
                      "suggested_next_action": ("建议后续动作", "Suggested next action"),
                      "status": ("状态", "Status"), "severity": ("严重度", "Severity"),
                      "category": ("分类", "Category"), "confidence": ("置信度", "Confidence"),
                      "snapshot": ("审计快照", "Snapshot"), "source_task": ("来源任务", "Source task"),
                      "aliases": ("别名", "Aliases"), "root_cause": ("根因", "Root cause"),
                      "owner": ("职责归属", "Owner"), "fix_boundary": ("修复边界", "Fix boundary"),
                      "identity": ("同一性证据", "Identity evidence"),
                      "source_run_id": ("原审计运行", "Original audit run"),
                      "resolution": ("修复后验证", "Repair verification")}
    for finding_id, finding in sorted(findings.items()):
        registry_rows.append([f"[{finding_id}](#{finding_id.lower()})", finding.get("severity", "—"),
                              status(finding["status"]), finding.get("summary", "—")])
        finding_sections += f'\n<a id="{finding_id.lower()}"></a>\n\n## {finding_id} — {finding.get("summary", "")}\n'
        for key, value in finding.items():
            if key in {"id", "summary"}:
                continue
            title = tr(*finding_labels[key]) if key in finding_labels else key
            if key == "source_task" and isinstance(value, str) and value in tasks:
                value = f"[{value}](results/{value}.md)"
            finding_sections += f"\n### {title}\n\n{prose(status(value) if key == 'status' else value)}\n"
    registry += "\n" + table(["ID", tr("严重度", "Severity"), tr("状态", "Status"), tr("摘要", "Summary")], registry_rows)
    registry += finding_sections

    report = f"# {tr('审计报告', 'Audit report')}\n" + nav() + snapshot_ref()
    report += section("运行状态", "Run status", status(state["Status"]))
    if not finished:
        report += "\n" + tr("审计尚未完成，局部 confirmed 不代表已发布的当前结论。", "Audit is unfinished; local confirmed findings are not published conclusions.") + "\n"
    report += section("摘要与覆盖限制", "Summary and coverage limits", document.get("summary", tr("尚未记录", "Not recorded yet")))
    report += section("任务覆盖", "Task coverage", task_table)
    report += section("问题计数", "Finding counts", count_table)
    report += section("问题索引", "Finding index", [
        f"[{fid}](Findings.md#{fid.lower()}) — {status(f['status'])} / {f.get('severity', '—')} / {f.get('summary', '')}"
        for fid, f in sorted(findings.items())] or tr("无已登记问题；不构成无缺陷保证。", "No registered findings; this is not a defect-free guarantee."))
    report += section("跨模块复核", "Cross-module reconciliation", {
        "Status": status(review["Status"]), "Evidence": review.get("Evidence", tr("尚未记录", "Not recorded yet"))})
    report += section("文档可发现性", "Documentation Discoverability", discovery_text)
    documents.update({"Dashboard.md": dashboard, "Findings.md": registry, "Report.md": report})
    return {path: content.rstrip() + "\n" for path, content in documents.items()}
