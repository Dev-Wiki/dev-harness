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
CONTEXT_SOURCE_DIR = SCRIPT_DIR / "context"
CONTEXT_SKILL_SOURCE = SCRIPT_DIR / "context" / "SKILL.md"
PLANNING_SOURCE_DIR = SCRIPT_DIR / "planning"
PLANNING_SKILL_SOURCE = SCRIPT_DIR / "planning" / "SKILL.md"
INTERNAL_BUGFIX_FLOW_DIR = SCRIPT_DIR / "internal" / "bugfix-flow"
INTERNAL_BUGFIX_FLOW_FILES = ("repro.md", "triage.md", "regression.md", "verify.md")
GIT_WORKFLOW_SKILL_SOURCE = SCRIPT_DIR / "git-workflow" / "SKILL.md"
AUTO_FIX_SKILL_SOURCE = SCRIPT_DIR / "auto-fix" / "SKILL.md"
RETRO_SKILL_SOURCE = SCRIPT_DIR / "retro" / "SKILL.md"
CONTEXT_RUNTIME_FILES = [
    "SKILL.md",
    "__init__.py",
    "cli.py",
    "platform_profiles.py",
    "repo_walk.py",
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

SKILL_SOURCES = {
    "dev-harness-commands": COMMANDS_SKILL_SOURCE,
    "dev-harness-context": CONTEXT_SKILL_SOURCE,
    "dev-harness-planning": PLANNING_SKILL_SOURCE,
    "dev-harness-git-workflow": GIT_WORKFLOW_SKILL_SOURCE,
    "dev-harness-auto-fix": AUTO_FIX_SKILL_SOURCE,
    "dev-harness-retro": RETRO_SKILL_SOURCE,
}

SKILL_DEPENDENCIES = {
    "dev-harness-commands": (),
    "dev-harness-context": (),
    "dev-harness-planning": (),
    "dev-harness-git-workflow": (),
    "dev-harness-auto-fix": (
        "dev-harness-git-workflow",
    ),
    "dev-harness-retro": (),
}


LESSONS_AGENTS_SNIPPET = """\

## 0. 项目犯错记录（AI 必读）

开始任何任务前，检查并读取项目根目录的 `LESSONS.md`（如果存在）。
文件中每条规则均有历史原因，视为硬约束，不得忽略或覆盖。
触发次数高的规则说明 AI 在此项目中容易重犯，优先关注。
"""

LESSONS_TEMPLATE = """\
# LESSONS — 项目级 AI 行为约束

> 由 dev-harness-retro 维护。开始任何任务前必须读此文件。
> 每条规则有历史原因，视为硬约束，不得忽略。
> 触发次数越高说明越容易重犯，优先关注。

## 活跃规则

| ID | 规则（一句话，AI 可直接执行） | 类型 | 触发次数 | 最近触发 |
|----|-------------------------------|------|---------|---------|

## 归档规则

> 超过 60 天未触发，自动移至此处。规则仍然有效，优先级低于活跃规则。

| ID | 规则 | 类型 | 触发次数 | 最近触发 | 归档日期 |
|----|------|------|---------|---------|---------|
"""


def _inject_lessons_into_agents(agents_path: Path) -> None:
    """若 AGENTS.md 存在且尚未包含 LESSONS.md 引用，在文件开头注入说明片段。"""
    if not agents_path.exists():
        return
    content = agents_path.read_text(encoding="utf-8")
    if "LESSONS.md" in content:
        return
    agents_path.write_text(LESSONS_AGENTS_SNIPPET + content, encoding="utf-8")


def _ensure_lessons_md(project_root: Path) -> None:
    """在项目根目录创建空 LESSONS.md（如果不存在）。"""
    lessons_path = project_root / "LESSONS.md"
    if not lessons_path.exists():
        lessons_path.write_text(LESSONS_TEMPLATE, encoding="utf-8")



def validate_sources() -> None:
    for skill_name, source in SKILL_SOURCES.items():
        if not source.exists():
            raise FileNotFoundError(f"Missing {skill_name} source: {source}")
    for file_name in INTERNAL_BUGFIX_FLOW_FILES:
        source = INTERNAL_BUGFIX_FLOW_DIR / file_name
        if not source.exists():
            raise FileNotFoundError(f"Missing internal bugfix-flow source: {source}")
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
    _copy_bugfix_flow_references(destination)


def build_dev_harness_context(_skill_name: str, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    lib_dir = destination / "lib" / "context"
    lib_dir.mkdir(parents=True, exist_ok=True)
    templates_dir = destination / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

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


def build_dev_harness_planning(_skill_name: str, destination: Path) -> None:
    build_skill("dev-harness-planning", destination)
    templates_dir = destination / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    for file_name in PLANNING_TEMPLATE_FILES:
        shutil.copy2(PLANNING_TEMPLATE_DIR / file_name, templates_dir / file_name)


BUILDERS = {skill_name: build_skill for skill_name in SKILL_SOURCES}
BUILDERS["dev-harness-auto-fix"] = build_dev_harness_auto_fix
BUILDERS["dev-harness-context"] = build_dev_harness_context
BUILDERS["dev-harness-planning"] = build_dev_harness_planning


def install_bundle_to_root(bundle_root: Path, skills: list[str] | None = None) -> Path:
    validate_sources()

    selected_skills = expand_skills(skills)
    skills_dir = bundle_root / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    for skill_name in selected_skills:
        destination = skills_dir / skill_name
        remove_existing(destination)
        BUILDERS[skill_name](skill_name, destination)

    # 在 skill 所在根目录（IDE bundle root 的上层项目根）尝试注入 LESSONS 支撑文件。
    # bundle_root 通常是 ~/.cursor 或 ~/.codex，不是客户端项目根；
    # 此处仅处理 export 模式下 bundle_root 是项目根（含 AGENTS.md）的情形。
    _inject_lessons_into_agents(bundle_root / "AGENTS.md")
    _ensure_lessons_md(bundle_root)

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
