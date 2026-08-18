#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Install or export the dev-harness skills bundle from source directories."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

VERSION = (SCRIPT_DIR / "VERSION").read_text(encoding="utf-8").strip()

COMMANDS_SKILL_SOURCE = SCRIPT_DIR / "commands" / "SKILL.md"
COMMANDS_REFERENCE_DIR = SCRIPT_DIR / "commands" / "references"
COMMANDS_REFERENCE_FILES = ("platform-command-mapping.md", "windows-shell.md")
CONTEXT_SOURCE_DIR = SCRIPT_DIR / "context"
CONTEXT_SKILL_SOURCE = SCRIPT_DIR / "context" / "SKILL.md"
CONTEXT_REFERENCE_DIR = CONTEXT_SOURCE_DIR / "references"
CONTEXT_REFERENCE_FILES = ("platform-enhancements.md",)
PLANNING_SOURCE_DIR = SCRIPT_DIR / "planning"
PLANNING_SKILL_SOURCE = SCRIPT_DIR / "planning" / "SKILL.md"
DOCS_SOURCE_DIR = SCRIPT_DIR / "dev-harness-docs"
DOCS_SKILL_SOURCE = DOCS_SOURCE_DIR / "SKILL.md"
INTERNAL_BUGFIX_FLOW_DIR = SCRIPT_DIR / "internal" / "bugfix-flow"
INTERNAL_BUGFIX_FLOW_FILES = ("repro.md", "triage.md", "regression.md", "verify.md")
GIT_WORKFLOW_SKILL_SOURCE = SCRIPT_DIR / "git-workflow" / "SKILL.md"
GIT_WORKFLOW_TEMPLATE_DIR = SCRIPT_DIR / "git-workflow" / "templates"
GIT_WORKFLOW_TEMPLATE_FILES = (
    "GIT_WORKFLOW.template.md",
    "CHANGELOG.template.md",
)
GIT_WORKFLOW_REFERENCE_DIR = SCRIPT_DIR / "git-workflow" / "references"
GIT_WORKFLOW_REFERENCE_FILES = ("default-contract.md",)
AUTO_FIX_SKILL_SOURCE = SCRIPT_DIR / "auto-fix" / "SKILL.md"
AUTO_FIX_RUNTIME_SOURCE = SCRIPT_DIR / "auto-fix" / "runtime.py"
RETRO_SKILL_SOURCE = SCRIPT_DIR / "retro" / "SKILL.md"
CODEBASE_AUDIT_SOURCE_DIR = SCRIPT_DIR / "codebase-audit"
CODEBASE_AUDIT_SKILL_SOURCE = CODEBASE_AUDIT_SOURCE_DIR / "SKILL.md"
CODEBASE_AUDIT_RUNTIME_SOURCE = CODEBASE_AUDIT_SOURCE_DIR / "runtime.py"
CODEBASE_AUDIT_REFERENCE_DIR = CODEBASE_AUDIT_SOURCE_DIR / "references"
CODEBASE_AUDIT_REFERENCE_FILES = (
    "workflow.md",
    "partitioning.md",
    "finding-contract.md",
    "cross-module-review.md",
)
CODEBASE_AUDIT_TEMPLATE_DIR = CODEBASE_AUDIT_SOURCE_DIR / "templates"
CODEBASE_AUDIT_TEMPLATE_FILES = (
    "Dashboard.template.md",
    "Findings.template.md",
    "AuditTask.template.md",
    "AuditResult.template.md",
    "Report.template.md",
)
CONTEXT_RUNTIME_FILES = [
    "SKILL.md",
    "__init__.py",
    "cli.py",
    "contracts.py",
    "evidence.py",
    "managed.py",
    "platform_profiles.py",
    "repo_walk.py",
    "semantic.py",
]
CONTEXT_TEMPLATE_DIR = CONTEXT_SOURCE_DIR / "templates"
CONTEXT_TEMPLATE_FILES = [
    "README.template.md",
    "AGENTS.template.md",
    "ARCHITECTURE.template.md",
    "HARNESS.template.md",
]
PLANNING_TEMPLATE_DIR = PLANNING_SOURCE_DIR / "templates"
PLANNING_TEMPLATE_FILES = [
    "Dashboard.template.md",
    "TaskDetails.template.md",
]
DOCS_REFERENCE_DIR = DOCS_SOURCE_DIR / "references"
DOCS_REFERENCE_FILES = ["information-architecture.md"]
DOCS_ASSET_DIR = DOCS_SOURCE_DIR / "assets"
DOCS_ASSET_FILES = [
    "docs-index.template.md",
    "documentation-rules.template.md",
    "nav.template.md",
]
DOCS_AGENT_DIR = DOCS_SOURCE_DIR / "agents"
DOCS_AGENT_FILES = ["openai.yaml"]

SKILL_SOURCES = {
    "dev-harness-commands": COMMANDS_SKILL_SOURCE,
    "dev-harness-context": CONTEXT_SKILL_SOURCE,
    "dev-harness-docs": DOCS_SKILL_SOURCE,
    "dev-harness-planning": PLANNING_SKILL_SOURCE,
    "dev-harness-git-workflow": GIT_WORKFLOW_SKILL_SOURCE,
    "dev-harness-auto-fix": AUTO_FIX_SKILL_SOURCE,
    "dev-harness-retro": RETRO_SKILL_SOURCE,
    "dev-harness-codebase-audit": CODEBASE_AUDIT_SKILL_SOURCE,
}

SKILL_DEPENDENCIES = {
    "dev-harness-commands": (),
    "dev-harness-context": (),
    "dev-harness-docs": (),
    "dev-harness-planning": (),
    "dev-harness-git-workflow": (),
    "dev-harness-auto-fix": (
        "dev-harness-git-workflow",
    ),
    "dev-harness-retro": (),
    "dev-harness-codebase-audit": (
        "dev-harness-context",
    ),
}


def validate_sources() -> None:
    for skill_name, source in SKILL_SOURCES.items():
        if not source.exists():
            raise FileNotFoundError(f"Missing {skill_name} source: {source}")
    for file_name in INTERNAL_BUGFIX_FLOW_FILES:
        source = INTERNAL_BUGFIX_FLOW_DIR / file_name
        if not source.exists():
            raise FileNotFoundError(f"Missing internal bugfix-flow source: {source}")
    if not AUTO_FIX_RUNTIME_SOURCE.exists():
        raise FileNotFoundError(f"Missing dev-harness-auto-fix runtime: {AUTO_FIX_RUNTIME_SOURCE}")
    for file_name in CONTEXT_RUNTIME_FILES:
        source = CONTEXT_SOURCE_DIR / file_name
        if not source.exists():
            raise FileNotFoundError(f"Missing dev-harness-context runtime source: {source}")
    for file_name in CONTEXT_TEMPLATE_FILES:
        source = CONTEXT_TEMPLATE_DIR / file_name
        if not source.exists():
            raise FileNotFoundError(f"Missing dev-harness-context template source: {source}")
    for file_name in PLANNING_TEMPLATE_FILES:
        source = PLANNING_TEMPLATE_DIR / file_name
        if not source.exists():
            raise FileNotFoundError(f"Missing dev-harness-planning template source: {source}")
    for file_name in DOCS_REFERENCE_FILES:
        source = DOCS_REFERENCE_DIR / file_name
        if not source.exists():
            raise FileNotFoundError(f"Missing dev-harness-docs reference source: {source}")
    for file_name in DOCS_ASSET_FILES:
        source = DOCS_ASSET_DIR / file_name
        if not source.exists():
            raise FileNotFoundError(f"Missing dev-harness-docs asset source: {source}")
    for file_name in DOCS_AGENT_FILES:
        source = DOCS_AGENT_DIR / file_name
        if not source.exists():
            raise FileNotFoundError(f"Missing dev-harness-docs agent metadata source: {source}")
    for file_name in GIT_WORKFLOW_TEMPLATE_FILES:
        source = GIT_WORKFLOW_TEMPLATE_DIR / file_name
        if not source.exists():
            raise FileNotFoundError(f"Missing dev-harness-git-workflow template source: {source}")
    for directory, file_names, label in (
        (COMMANDS_REFERENCE_DIR, COMMANDS_REFERENCE_FILES, "dev-harness-commands reference"),
        (CONTEXT_REFERENCE_DIR, CONTEXT_REFERENCE_FILES, "dev-harness-context reference"),
        (GIT_WORKFLOW_REFERENCE_DIR, GIT_WORKFLOW_REFERENCE_FILES, "dev-harness-git-workflow reference"),
        (CODEBASE_AUDIT_REFERENCE_DIR, CODEBASE_AUDIT_REFERENCE_FILES, "dev-harness-codebase-audit reference"),
        (CODEBASE_AUDIT_TEMPLATE_DIR, CODEBASE_AUDIT_TEMPLATE_FILES, "dev-harness-codebase-audit template"),
    ):
        for file_name in file_names:
            source = directory / file_name
            if not source.exists():
                raise FileNotFoundError(f"Missing {label} source: {source}")
    if not CODEBASE_AUDIT_RUNTIME_SOURCE.exists():
        raise FileNotFoundError(f"Missing dev-harness-codebase-audit runtime: {CODEBASE_AUDIT_RUNTIME_SOURCE}")


def remove_existing(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


IDE_ALIASES = ("cursor", "codex", "opencode", "antigravity")

IDE_LABELS: dict[str, str] = {
    "cursor": "Cursor",
    "codex": "Codex",
    "opencode": "OpenCode",
    "antigravity": "Google Antigravity (global ~/.gemini/antigravity/skills)",
}


@dataclass(frozen=True)
class ResolvedInstallTarget:
    """Exactly one of bundle_root or export_parent is set (except both None = user quit)."""

    bundle_root: Path | None = None
    export_parent: Path | None = None


def bundle_root_for_ide(ide: str) -> Path:
    """Resolve the host root directory for a known IDE / agent skills layout."""
    home = Path.home()
    if ide == "cursor":
        return home / ".cursor"
    if ide == "codex":
        return home / ".codex"
    if ide == "opencode":
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA")
            if appdata:
                return Path(appdata) / "opencode"
        return home / ".config" / "opencode"
    if ide == "antigravity":
        # Global skills per https://antigravity.google/docs/skills
        # Installs to <root>/skills/... → ~/.gemini/antigravity/skills/<skill-name>/
        return home / ".gemini" / "antigravity"
    raise ValueError(f"Unknown IDE: {ide}")


def _prompt_nonempty_path(prompt: str) -> Path:
    while True:
        raw = input(prompt).strip().strip('"').strip("'")
        if not raw:
            print("Path required.")
            continue
        return Path(raw).expanduser()


def run_interactive_menu() -> ResolvedInstallTarget | None:
    """TTY menu: list supported IDE targets and a few extra actions. None = user quit."""
    n_ide = len(IDE_ALIASES)
    opt_export = n_ide + 1
    opt_custom = n_ide + 2
    opt_ag_workspace = n_ide + 3

    print()
    print("dev-harness — choose where to install (each skill becomes <root>/skills/<name>/):")
    print()
    for i, ide in enumerate(IDE_ALIASES, start=1):
        root = bundle_root_for_ide(ide)
        label = IDE_LABELS[ide]
        print(f"  {i}) {label}")
        print(f"      → {root / 'skills'}")
    print(f"  {opt_export}) Export portable bundle only (creates <dir>/bundle/skills/...)")
    print(f"  {opt_custom}) Custom install root (same as --target; parent of skills/)")
    print(
        f"  {opt_ag_workspace}) Google Antigravity — workspace skills "
        f"(asks repo root → installs to <repo>/.agent/skills/; see https://antigravity.google/docs/skills )"
    )
    print("  0) Exit")
    print()

    while True:
        raw = input(f"Enter choice [0-{opt_ag_workspace}]: ").strip()
        if not raw:
            continue
        try:
            choice = int(raw)
        except ValueError:
            print("Enter a number.")
            continue
        if choice == 0:
            return None
        if 1 <= choice <= n_ide:
            ide = IDE_ALIASES[choice - 1]
            return ResolvedInstallTarget(bundle_root=bundle_root_for_ide(ide), export_parent=None)
        if choice == opt_export:
            parent = _prompt_nonempty_path("Export parent directory (e.g. dist or ./out): ")
            return ResolvedInstallTarget(bundle_root=None, export_parent=parent)
        if choice == opt_custom:
            root = _prompt_nonempty_path("Install root (directory that will contain skills/): ")
            return ResolvedInstallTarget(bundle_root=root, export_parent=None)
        if choice == opt_ag_workspace:
            repo = _prompt_nonempty_path("Repository root (workspace root, not .agent): ")
            return ResolvedInstallTarget(bundle_root=repo / ".agent", export_parent=None)
        print(f"Choose 0-{opt_ag_workspace}.")


def expand_skills(skills: list[str] | None) -> list[str]:
    requested = list(SKILL_DEPENDENCIES) if skills is None else list(skills)
    resolved: list[str] = []

    def add(skill_name: str) -> None:
        if skill_name not in SKILL_DEPENDENCIES:
            raise ValueError(f"Unknown skill: {skill_name}")
        if skill_name in resolved:
            return
        resolved.append(skill_name)
        for dependency in SKILL_DEPENDENCIES[skill_name]:
            add(dependency)

    for skill_name in requested:
        add(skill_name)

    return resolved


def _inject_version_into_skill(source: Path, destination: Path) -> None:
    """复制 SKILL.md 并在 frontmatter 中注入 bundle_version 字段。"""
    content = source.read_text(encoding="utf-8")
    if content.startswith("---"):
        # 找到 frontmatter 结束位置（第二个 ---）
        end = content.index("---", 3)
        frontmatter = content[3:end].rstrip("\n")
        rest = content[end + 3:]
        # 移除已有的 bundle_version 行（幂等）
        lines = [l for l in frontmatter.splitlines() if not l.startswith("bundle_version:")]
        lines.append(f"bundle_version: {VERSION}")
        new_content = "---\n" + "\n".join(lines) + "\n---" + rest
    else:
        new_content = content
    destination.write_text(new_content, encoding="utf-8")


def build_skill(skill_name: str, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    _inject_version_into_skill(SKILL_SOURCES[skill_name], destination / "SKILL.md")


def _copy_bugfix_flow_references(destination: Path) -> None:
    refs_dir = destination / "references" / "bugfix-flow"
    refs_dir.mkdir(parents=True, exist_ok=True)
    for file_name in INTERNAL_BUGFIX_FLOW_FILES:
        shutil.copy2(INTERNAL_BUGFIX_FLOW_DIR / file_name, refs_dir / file_name)


def build_dev_harness_auto_fix(_skill_name: str, destination: Path) -> None:
    build_skill("dev-harness-auto-fix", destination)
    shutil.copy2(AUTO_FIX_RUNTIME_SOURCE, destination / "runtime.py")
    _copy_bugfix_flow_references(destination)


def build_dev_harness_context(_skill_name: str, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    lib_dir = destination / "lib" / "context"
    lib_dir.mkdir(parents=True, exist_ok=True)
    templates_dir = destination / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    references_dir = destination / "references"
    references_dir.mkdir(parents=True, exist_ok=True)

    _inject_version_into_skill(CONTEXT_SOURCE_DIR / "SKILL.md", destination / "SKILL.md")

    launcher = destination / "dev-harness-context"
    launcher.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "from pathlib import Path\n\n"
        "SCRIPT_PATH = Path(__file__).resolve()\n"
        "sys.path.insert(0, str(SCRIPT_PATH.parent / \"lib\"))\n"
        "from context.cli import cli_main\n\n"
        "if __name__ == \"__main__\":\n"
        "    raise SystemExit(cli_main())\n",
        encoding="utf-8",
    )

    for file_name in CONTEXT_RUNTIME_FILES:
        if file_name == "SKILL.md":
            continue
        shutil.copy2(CONTEXT_SOURCE_DIR / file_name, lib_dir / file_name)

    for file_name in CONTEXT_TEMPLATE_FILES:
        shutil.copy2(CONTEXT_TEMPLATE_DIR / file_name, templates_dir / file_name)
    for file_name in CONTEXT_REFERENCE_FILES:
        shutil.copy2(CONTEXT_REFERENCE_DIR / file_name, references_dir / file_name)


def build_dev_harness_commands(_skill_name: str, destination: Path) -> None:
    build_skill("dev-harness-commands", destination)
    references_dir = destination / "references"
    references_dir.mkdir(parents=True, exist_ok=True)
    for file_name in COMMANDS_REFERENCE_FILES:
        shutil.copy2(COMMANDS_REFERENCE_DIR / file_name, references_dir / file_name)


def build_dev_harness_planning(_skill_name: str, destination: Path) -> None:
    build_skill("dev-harness-planning", destination)
    templates_dir = destination / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    for file_name in PLANNING_TEMPLATE_FILES:
        shutil.copy2(PLANNING_TEMPLATE_DIR / file_name, templates_dir / file_name)


def build_dev_harness_docs(_skill_name: str, destination: Path) -> None:
    build_skill("dev-harness-docs", destination)
    for directory_name, source_dir, file_names in (
        ("references", DOCS_REFERENCE_DIR, DOCS_REFERENCE_FILES),
        ("assets", DOCS_ASSET_DIR, DOCS_ASSET_FILES),
        ("agents", DOCS_AGENT_DIR, DOCS_AGENT_FILES),
    ):
        output_dir = destination / directory_name
        output_dir.mkdir(parents=True, exist_ok=True)
        for file_name in file_names:
            shutil.copy2(source_dir / file_name, output_dir / file_name)


def build_dev_harness_git_workflow(_skill_name: str, destination: Path) -> None:
    build_skill("dev-harness-git-workflow", destination)
    templates_dir = destination / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    for file_name in GIT_WORKFLOW_TEMPLATE_FILES:
        shutil.copy2(GIT_WORKFLOW_TEMPLATE_DIR / file_name, templates_dir / file_name)
    references_dir = destination / "references"
    references_dir.mkdir(parents=True, exist_ok=True)
    for file_name in GIT_WORKFLOW_REFERENCE_FILES:
        shutil.copy2(GIT_WORKFLOW_REFERENCE_DIR / file_name, references_dir / file_name)


def build_dev_harness_codebase_audit(_skill_name: str, destination: Path) -> None:
    build_skill("dev-harness-codebase-audit", destination)
    shutil.copy2(CODEBASE_AUDIT_RUNTIME_SOURCE, destination / "runtime.py")
    for directory_name, source_dir, file_names in (
        ("references", CODEBASE_AUDIT_REFERENCE_DIR, CODEBASE_AUDIT_REFERENCE_FILES),
        ("templates", CODEBASE_AUDIT_TEMPLATE_DIR, CODEBASE_AUDIT_TEMPLATE_FILES),
    ):
        output_dir = destination / directory_name
        output_dir.mkdir(parents=True, exist_ok=True)
        for file_name in file_names:
            shutil.copy2(source_dir / file_name, output_dir / file_name)


BUILDERS = {skill_name: build_skill for skill_name in SKILL_SOURCES}
BUILDERS["dev-harness-commands"] = build_dev_harness_commands
BUILDERS["dev-harness-auto-fix"] = build_dev_harness_auto_fix
BUILDERS["dev-harness-context"] = build_dev_harness_context
BUILDERS["dev-harness-docs"] = build_dev_harness_docs
BUILDERS["dev-harness-planning"] = build_dev_harness_planning
BUILDERS["dev-harness-git-workflow"] = build_dev_harness_git_workflow
BUILDERS["dev-harness-codebase-audit"] = build_dev_harness_codebase_audit


def install_bundle_to_root(bundle_root: Path, skills: list[str] | None = None) -> Path:
    validate_sources()

    selected_skills = expand_skills(skills)
    skills_dir = bundle_root / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    for skill_name in selected_skills:
        destination = skills_dir / skill_name
        remove_existing(destination)
        BUILDERS[skill_name](skill_name, destination)

    return bundle_root


def export_bundle(out_dir: Path, skills: list[str] | None = None) -> Path:
    bundle_root = out_dir / "bundle"
    remove_existing(bundle_root)
    return install_bundle_to_root(bundle_root, skills)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install or export the dev-harness skills bundle from source."
    )
    parser.add_argument("--target", type=Path, help="install the skills bundle into this root directory")
    parser.add_argument("--export", dest="export_dir", type=Path, help="export the skills bundle under this directory")
    parser.add_argument(
        "--ide",
        choices=list(IDE_ALIASES),
        help="install into this IDE/agent default root (cursor/codex/opencode/antigravity; see bundle_root_for_ide)",
    )
    parser.add_argument(
        "--skill",
        action="append",
        choices=list(SKILL_DEPENDENCIES),
        help="install only the named skill; may be repeated",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"dev-harness {VERSION}",
        help="show bundle version and exit",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    modes = sum(1 for x in (args.target, args.export_dir, args.ide) if x is not None)
    if modes > 1:
        parser.error("use at most one of --target, --export, --ide")

    if args.export_dir:
        target = export_bundle(args.export_dir, args.skill)
        print(f"[ok] Exported dev-harness v{VERSION} to {target}")
        return

    if args.target is not None:
        bundle_root = args.target
    elif args.ide is not None:
        bundle_root = bundle_root_for_ide(args.ide)
    elif sys.stdin.isatty():
        resolved = run_interactive_menu()
        if resolved is None:
            print("Cancelled.")
            return
        if resolved.export_parent is not None:
            target = export_bundle(resolved.export_parent, args.skill)
            print(f"[ok] Exported dev-harness v{VERSION} to {target}")
            return
        bundle_root = resolved.bundle_root
        assert bundle_root is not None
    else:
        bundle_root = bundle_root_for_ide("cursor")

    target = install_bundle_to_root(bundle_root, args.skill)
    print(f"[ok] Installed dev-harness v{VERSION} to {target}")


if __name__ == "__main__":
    main()
