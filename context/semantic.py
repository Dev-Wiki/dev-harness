"""Validation for AI-authored, evidence-backed repository semantic analysis."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from context.evidence import SCHEMA_VERSION, collect_repository_evidence

ALLOWED_CONFIDENCE = {"high", "medium", "low"}
ALLOWED_CLAIMS = {
    "project_type",
    "project_summary",
    "language_framework",
    "architecture_pattern",
    "core_entry",
    "core_flow",
    "dependency_graph",
    "version_marker",
    "install_command",
    "build_command",
    "run_command",
    "test_command",
    "quick_command",
    "bugfix_command",
    "full_command",
    "style_rules",
    "architecture_rules",
    "forbidden_operations",
    "high_risk_files",
    "feature_paths",
    "code_safety_rules",
    "multi_version_notes",
    "logging_rules",
    "exploration_suggestions",
}
ALLOWED_LISTS = {
    "core_modules",
    "module_interfaces",
    "key_module_markers",
    "high_risk_directories",
    "auto_detected_candidates",
    "manual_review_items",
}
COMMAND_CLAIMS = {
    "install_command",
    "build_command",
    "run_command",
    "test_command",
    "quick_command",
    "bugfix_command",
    "full_command",
}
LINE_REFERENCE = re.compile(r"^(?P<path>.+?)(?::(?P<line>[1-9][0-9]*))?$")
INSTALL_ONLY_COMMAND = re.compile(
    r"^(?:(?:py(?:\s+-\d+(?:\.\d+)?)?|python(?:\d+(?:\.\d+)?)?)\s+-m\s+)?pip\s+install\b"
    r"|^(?:npm|pnpm|yarn|ohpm)\s+install\b",
    re.IGNORECASE,
)
NORMATIVE_CLAIMS = {
    "architecture_rules",
    "forbidden_operations",
    "code_safety_rules",
}
NORMATIVE_TERMS = ("所有", "必须", "禁止", "只能", "不得")


class SemanticAnalysisError(ValueError):
    pass


@dataclass(frozen=True)
class SemanticAnalysis:
    claims: dict[str, str]
    lists: dict[str, list[str]]
    manual_review_items: list[str]
    evidence_items: list[str]

    def claim(self, name: str, fallback: str) -> str:
        return self.claims.get(name, fallback)

    def items(self, name: str, fallback: list[str]) -> list[str]:
        return self.lists.get(name, fallback)


def _validate_evidence_reference(repo_root: Path, reference: object, field: str) -> str:
    if not isinstance(reference, str) or not reference.strip():
        raise SemanticAnalysisError(f"{field}: evidence references must be non-empty strings")
    match = LINE_REFERENCE.fullmatch(reference.strip())
    if match is None:
        raise SemanticAnalysisError(f"{field}: invalid evidence reference: {reference}")
    relative = Path(match.group("path"))
    if relative.is_absolute() or ".." in relative.parts:
        raise SemanticAnalysisError(f"{field}: evidence must stay inside the repository: {reference}")
    target = (repo_root / relative).resolve()
    try:
        target.relative_to(repo_root)
    except ValueError as exc:
        raise SemanticAnalysisError(f"{field}: evidence escapes the repository: {reference}") from exc
    if not target.exists():
        raise SemanticAnalysisError(f"{field}: evidence path does not exist: {reference}")
    if match.group("line") and not target.is_file():
        raise SemanticAnalysisError(f"{field}: line evidence must reference a file: {reference}")
    if match.group("line"):
        line_number = int(match.group("line"))
        try:
            with target.open("rb") as stream:
                content = stream.read()
        except OSError as exc:
            raise SemanticAnalysisError(f"{field}: cannot read evidence file: {reference}") from exc
        line_count = content.count(b"\n")
        if content and not content.endswith(b"\n"):
            line_count += 1
        if line_number > line_count:
            raise SemanticAnalysisError(
                f"{field}: evidence line is out of range ({line_number} > {line_count}): {reference}"
            )
    return reference.strip()


def _validate_claim(repo_root: Path, field: str, raw: object) -> tuple[str, str, list[str]]:
    if not isinstance(raw, dict):
        raise SemanticAnalysisError(f"{field}: claim must be an object")
    unexpected = set(raw) - {"value", "confidence", "evidence"}
    if unexpected:
        raise SemanticAnalysisError(f"{field}: unsupported claim keys: {', '.join(sorted(unexpected))}")
    value = raw.get("value")
    confidence = raw.get("confidence")
    evidence = raw.get("evidence")
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise SemanticAnalysisError(f"{field}: value must be a non-empty string")
    value = value.strip()
    if len(value) > 8000:
        raise SemanticAnalysisError(f"{field}: value is too large")
    if confidence not in ALLOWED_CONFIDENCE:
        raise SemanticAnalysisError(f"{field}: confidence must be high, medium, or low")
    if not isinstance(evidence, list):
        raise SemanticAnalysisError(f"{field}: evidence must be a list")
    if value != "Unknown" and not evidence:
        kind = "command" if field in COMMAND_CLAIMS else "claim"
        raise SemanticAnalysisError(f"{field}: non-Unknown {kind} requires evidence")
    validated_evidence = [
        _validate_evidence_reference(repo_root, reference, field)
        for reference in evidence
    ]
    base_field = field.split("[", 1)[0]
    if (
        base_field == "build_command"
        and value not in {"Unknown", "N/A"}
        and INSTALL_ONLY_COMMAND.search(value)
    ):
        raise SemanticAnalysisError(
            "build_command: installation command cannot be used as build_command; use N/A when no build exists"
        )
    if (
        base_field in NORMATIVE_CLAIMS
        and any(term in value for term in NORMATIVE_TERMS)
        and value != "Unknown"
        and any(LINE_REFERENCE.fullmatch(item).group("line") is None for item in validated_evidence)
    ):
        raise SemanticAnalysisError(
            f"{field}: normative claims require exact line evidence and a counterexample search"
        )
    return value, confidence, validated_evidence


def load_semantic_analysis(path: Path, repo_root: Path) -> SemanticAnalysis:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SemanticAnalysisError(f"cannot read semantic analysis: {exc}") from exc
    if not isinstance(raw, dict):
        raise SemanticAnalysisError("semantic analysis root must be an object")
    unexpected = set(raw) - {"schema_version", "evidence_fingerprint", "claims", "lists"}
    if unexpected:
        raise SemanticAnalysisError(f"unsupported top-level keys: {', '.join(sorted(unexpected))}")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise SemanticAnalysisError(f"unsupported semantic analysis schema version: {raw.get('schema_version')}")
    current_evidence = collect_repository_evidence(repo_root)
    if raw.get("evidence_fingerprint") != current_evidence["evidence_fingerprint"]:
        raise SemanticAnalysisError("repository evidence fingerprint changed; collect evidence and analyze again")

    raw_claims = raw.get("claims", {})
    raw_lists = raw.get("lists", {})
    if not isinstance(raw_claims, dict) or not isinstance(raw_lists, dict):
        raise SemanticAnalysisError("claims and lists must be objects")
    unknown_claims = set(raw_claims) - ALLOWED_CLAIMS
    unknown_lists = set(raw_lists) - ALLOWED_LISTS
    if unknown_claims or unknown_lists:
        names = sorted(unknown_claims | unknown_lists)
        raise SemanticAnalysisError(f"unsupported semantic fields: {', '.join(names)}")

    claims: dict[str, str] = {}
    lists: dict[str, list[str]] = {}
    manual: list[str] = []
    evidence_items: list[str] = []
    for field, claim in raw_claims.items():
        value, confidence, evidence = _validate_claim(repo_root, field, claim)
        if confidence == "low" and value != "Unknown":
            manual.append(f"AI 分析 `{field}` 置信度较低（候选：{value}），需人工确认")
        elif value != "Unknown":
            claims[field] = value
            evidence_items.append(f"AI `{field}` [{confidence}] 证据：{', '.join(f'`{item}`' for item in evidence)}")

    for field, entries in raw_lists.items():
        if not isinstance(entries, list):
            raise SemanticAnalysisError(f"{field}: list field must be an array")
        accepted: list[str] = []
        for index, claim in enumerate(entries):
            value, confidence, evidence = _validate_claim(repo_root, f"{field}[{index}]", claim)
            if confidence == "low" and value != "Unknown":
                manual.append(f"AI 分析 `{field}` 置信度较低（候选：{value}），需人工确认")
            elif value != "Unknown":
                accepted.append(value)
                evidence_items.append(f"AI `{field}[{index}]` [{confidence}] 证据：{', '.join(f'`{item}`' for item in evidence)}")
        if accepted:
            lists[field] = accepted
    manual.extend(lists.get("manual_review_items", []))
    return SemanticAnalysis(
        claims=claims,
        lists=lists,
        manual_review_items=manual,
        evidence_items=evidence_items,
    )
