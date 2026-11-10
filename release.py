#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打包 dev-harness 发布版本，生成 dev-harness-vX.Y.Z.zip。"""

from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VERSION_FILE = SCRIPT_DIR / "VERSION"
DIST_DIR = SCRIPT_DIR / "dist"


def _release_readme(version: str) -> str:
    return f"""# dev-harness v{version}

[简体中文](README.md) | [English](README.en.md)

本包包含可直接使用的 Skill，每个 `skills/dev-harness-*` 目录均包含所需的
说明、运行脚本、模板和参考资料。源码及维护文档见对应版本的源码归档。

## 安装

解压后，将 `skills/` 下的 `dev-harness-*` 文件夹复制到所用工具的 Skill 目录：

| 工具 | Skill 目录 |
|---|---|
| Cursor | `~/.cursor/skills/` |
| Codex | `~/.codex/skills/` |
| OpenCode | `~/.config/opencode/skills/`；Windows 设置了 APPDATA 时用 `%APPDATA%/opencode/skills/` |
| Antigravity | `~/.gemini/antigravity/skills/` |

`~` 表示用户主目录。目标目录不存在时先创建，也可使用宿主配置的自定义 Skill 目录。
最终目录应为 `<Skill 目录>/dev-harness-context/SKILL.md`，不要再嵌套一层 `skills/`。
升级时替换对应的 `dev-harness-*` 文件夹，保留自己修改过的内容和其他 Skill。
完成后重新加载宿主的 Skill 列表。

建议复制全部 Skill。单独安装 `dev-harness-codebase-audit` 时，需同时复制
`dev-harness-context`；单独安装 `dev-harness-auto-fix` 时，需同时复制
`dev-harness-git-workflow`。

## 使用

在 AI 工具中按名称调用 Skill，具体流程见各目录的 `SKILL.md`。
Context、Auto Fix 和 Codebase Audit 的运行脚本需要 Python 3，Git 工作区操作需要 Git。
Python 脚本是 Skill 的运行资源，请与模板和参考资料一并保留。

版本信息见 `VERSION`，版本变化见 `CHANGELOG.md` 或 `CHANGELOG.en.md`。
"""


def _release_readme_en(version: str) -> str:
    return f"""# dev-harness v{version}

[English](README.en.md) | [简体中文](README.md)

This package contains ready-to-use skills. Each `skills/dev-harness-*` directory
includes its instructions, runtime scripts, templates, and references. Source code
and maintenance documentation are available in the corresponding source archive.

## Install

Extract this archive, then copy the `dev-harness-*` folders inside `skills/` into
your host's skills directory:

| Host | Skills directory |
|---|---|
| Cursor | `~/.cursor/skills/` |
| Codex | `~/.codex/skills/` |
| OpenCode | `~/.config/opencode/skills/`; on Windows with APPDATA set, `%APPDATA%/opencode/skills/` |
| Antigravity | `~/.gemini/antigravity/skills/` |

`~` means your home directory. Create the destination if needed, or use your host's
configured skills directory. The resulting path should look like
`<skills-directory>/dev-harness-context/SKILL.md`, without an extra `skills/` level.
For upgrades, preserve custom changes before replacing the corresponding skill
folders, keep unrelated skills, and reload the host's skill list.

Copying all eight skills is recommended. If copying individual skills, include
`dev-harness-context` with `dev-harness-codebase-audit`, and include
`dev-harness-git-workflow` with `dev-harness-auto-fix`.

## Use

Invoke the installed skills by name in your AI assistant. For example:

```text
Use dev-harness-context to scan this repository and generate project context.
Use dev-harness-auto-fix in fix mode for this bug: <description>. Write the report in English.
Use dev-harness-codebase-audit to audit this repository. Write all audit artifacts in English only.
```

See each skill's `SKILL.md` for its contract. Context, Auto Fix, and Codebase Audit
require Python 3 at runtime; Git workspace operations require Git. Keep the runtime
scripts, templates, and references with their skill folders.

English report requests do not enable fully English project contracts. Context
generation and refresh, and Runtime Planning and acceptance, still depend on fixed
Chinese headings or labels. Preserve those structural labels for Runtime tasks.
The Runtime plugin is installed separately from this Skills Bundle.

See [VERSION](VERSION) for the package version and [CHANGELOG.en.md](CHANGELOG.en.md)
for released changes. English usage references are included with their skills.
"""


def main() -> None:
    if not VERSION_FILE.exists():
        print("ERROR: VERSION 文件不存在", file=sys.stderr)
        sys.exit(1)

    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    zip_name = f"dev-harness-v{version}.zip"
    bundle_dir = DIST_DIR / "bundle"
    zip_path = DIST_DIR / zip_name

    # 清理上次产物
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    if zip_path.exists():
        zip_path.unlink()

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # 调用 install.py 导出 bundle
    print(f"正在导出 dev-harness v{version} ...")
    import install as _install
    _install.export_bundle(DIST_DIR)

    # 只分发构建好的 Skill 和发布说明，源码由对应版本的源码归档提供。
    print(f"正在生成 {zip_name} ...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(bundle_dir.rglob("*")):
            if file.is_file():
                zf.write(file, file.relative_to(bundle_dir))
        zf.writestr("README.md", _release_readme(version))
        zf.writestr("README.en.md", _release_readme_en(version))
        zf.writestr("VERSION", version + "\n")
        changelog = SCRIPT_DIR / "CHANGELOG.md"
        if changelog.exists():
            zf.write(changelog, "CHANGELOG.md")
        english_changelog = SCRIPT_DIR / "CHANGELOG.en.md"
        if english_changelog.exists():
            zf.write(english_changelog, "CHANGELOG.en.md")

    size_kb = zip_path.stat().st_size // 1024
    print(f"\n[ok] {zip_name} ({size_kb} KB)")
    print(f"     路径：{zip_path}")
    print()
    print("同事安装方式：")
    print(f"  1. 解压 {zip_name}")
    print("  2. 将 skills/ 下的 dev-harness-* 文件夹复制到宿主的 Skill 目录")
    print("     各工具的目标目录及单 Skill 依赖见包内 README.md")


if __name__ == "__main__":
    main()
