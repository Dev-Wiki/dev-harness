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

    # 打包成 zip（直接从 bundle_dir 内部开始，解压后根目录就是 skills/）
    # 同时把 CHANGELOG.md 放在 zip 根目录
    print(f"正在生成 {zip_name} ...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(bundle_dir.rglob("*")):
            if file.is_file():
                zf.write(file, file.relative_to(bundle_dir))
        changelog = SCRIPT_DIR / "CHANGELOG.md"
        if changelog.exists():
            zf.write(changelog, "CHANGELOG.md")

    size_kb = zip_path.stat().st_size // 1024
    print(f"\n[ok] {zip_name} ({size_kb} KB)")
    print(f"     路径：{zip_path}")
    print()
    print("同事安装方式：")
    print(f"  1. 解压 {zip_name}")
    print("  2. 进入解压目录，运行：")
    print("       python install.py --ide cursor")
    print("     或根据使用的 AI 工具选择：codex / opencode / antigravity")


if __name__ == "__main__":
    main()
