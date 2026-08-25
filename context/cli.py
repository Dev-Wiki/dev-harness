from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
from itertools import islice
from pathlib import Path

from context.contracts import ContractIndex, discover_contract_index
from context.evidence import collect_repository_evidence
from context.managed import (
    DocumentFormat,
    ManagedDocumentError,
    SECTION_SPECS,
    atomic_write_document,
    decode_document,
    merge_markdown_sections,
    parse_markdown_sections,
    strip_legacy_managed_markers,
)
from context.platform_profiles import (
    detect_high_risk_directories as profile_detect_high_risk_directories,
    detect_project_type as profile_detect_project_type,
    detect_validation_commands as profile_detect_validation_commands,
    get_harmony_build_command,
    get_win32_build_command,
    get_wpf_build_command,
    find_fastapi_entry,
    has_harmony_packaging_scripts,
)
from context.repo_walk import (
    find_all_matching_files,
    first_matching_file,
    iter_matching_files,
    iter_walk_files,
    repo_has_any_suffix,
    repo_has_suffix,
    SKIP_DIR_NAMES,
)
from context.semantic import SemanticAnalysis, SemanticAnalysisError, load_semantic_analysis

TARGET_FILES = ("README.md", "AGENTS.md", "ARCHITECTURE.md", "HARNESS.md")
TEMPLATE_FILES = (
    "README.template.md",
    "AGENTS.template.md",
    "ARCHITECTURE.template.md",
    "HARNESS.template.md",
)
RUNTIME_DIRECTORY_NAMES = {"data", "logs", "log", "tmp", "temp", "cache"}
GENERATED_DOCUMENT_ANTI_PATTERNS = (
    ("内部语义证据字段", re.compile(r"AI `[a-z_]+(?:\[\d+\])?` \[(?:high|medium|low)\]")),
    ("可能已过期的测试数量", re.compile(r"\b\d+\s+passed\b", re.IGNORECASE)),
    ("无具体含义的目录占位说明", re.compile(r"contains (?:project files|submodules or grouped resources)")),
    ("不适用于当前项目的 SDK 模板术语", re.compile(r"SDK 调用链")),
    ("无具体含义的 Unknown 列表项", re.compile(r"(?m)^- Unknown\s*$")),
)
LANGUAGE_BY_SUFFIX = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".c": "C",
    ".h": "C/C++ 头文件",
    ".hpp": "C/C++ 头文件",
    ".rb": "Ruby",
    ".php": "PHP",
    ".sh": "Shell",
}


def discover_template_dir(repo_root: Path | None = None) -> Path:
    if repo_root is not None:
        repo_template_dir = repo_root / "templates" / "context"
        required_templates = [repo_template_dir / file_name for file_name in TEMPLATE_FILES]
        if all(path.exists() for path in required_templates):
            return repo_template_dir

    current = Path(__file__).resolve()
    for parent in [current.parent, *current.parents]:
        for candidate in (parent / "templates", parent / "templates" / "context"):
            required_templates = [candidate / file_name for file_name in TEMPLATE_FILES]
            if all(path.exists() for path in required_templates):
                return candidate
    raise FileNotFoundError("找不到 Context 模板目录")


def read_template(name: str, repo_root: Path | None = None) -> str:
    template_path = discover_template_dir(repo_root) / name
    return template_path.read_text(encoding="utf-8")


def iter_repo_files(repo_root: Path):
    yield from iter_walk_files(repo_root)


def detect_languages(repo_root: Path) -> list[str]:
    languages = {LANGUAGE_BY_SUFFIX[path.suffix.lower()] for path in iter_repo_files(repo_root) if path.suffix.lower() in LANGUAGE_BY_SUFFIX}
    return sorted(languages)


def detect_build_systems(repo_root: Path) -> list[str]:
    build_systems: list[str] = []
    file_markers = [
        ("package.json", "npm / package.json"),
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "Yarn"),
        ("pyproject.toml", "pyproject.toml"),
        ("requirements.txt", "Python 依赖清单（requirements.txt，非构建系统）"),
        ("Cargo.toml", "Cargo"),
        ("go.mod", "Go Modules"),
        ("pom.xml", "Maven"),
        ("build.gradle", "Gradle"),
        ("build.gradle.kts", "Gradle"),
        ("CMakeLists.txt", "CMake"),
        ("Makefile", "Make"),
        ("*.sln", ".NET 解决方案"),
        ("*.csproj", ".NET 项目"),
    ]
    for pattern, label in file_markers:
        matches = list(repo_root.glob(pattern))
        if matches and label not in build_systems:
            build_systems.append(label)
    return build_systems


def describe_directory(directory: Path) -> str | None:
    known_roles = {
        "app": "应用源码与运行入口",
        "src": "项目源码",
        "tests": "自动化测试",
        "docs": "项目文档",
        "deploy": "部署与服务安装脚本",
        "scripts": "开发、运行和维护脚本",
        "skills": "Skill 定义与配套自动化脚本",
    }
    if directory.name in known_roles:
        return known_roles[directory.name]
    if (directory / "SKILL.md").exists():
        return "Skill 定义与配套资源"

    languages = detect_languages(directory)
    if languages:
        return f"{', '.join(languages)} 源码"

    child_files = [path for path in directory.iterdir() if path.is_file()]
    if child_files:
        return None

    child_dirs = [path for path in directory.iterdir() if path.is_dir()]
    if child_dirs:
        return None

    return None


def detect_core_modules(repo_root: Path) -> list[str]:
    modules: list[str] = []
    for child in sorted(repo_root.iterdir()):
        if not child.is_dir():
            continue
        if (
            child.name in SKIP_DIR_NAMES
            or child.name in RUNTIME_DIRECTORY_NAMES
            or child.name.startswith(".")
        ):
            continue
        description = describe_directory(child)
        if description:
            modules.append(f"{child.name}: {description}")
    return modules


def detect_project_name(repo_root: Path) -> str:
    package_json = repo_root / "package.json"
    if package_json.exists():
        try:
            package_data = json.loads(package_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return repo_root.name or "Unknown"
        package_name = package_data.get("name")
        if isinstance(package_name, str) and package_name.strip():
            return package_name.strip()
    return repo_root.name or "Unknown"


def repo_has_dotnet_solution(repo_root: Path) -> bool:
    if list(repo_root.glob("*.csproj")):
        return True
    for path in repo_root.glob("*.sln"):
        content = path.read_text(encoding="utf-8", errors="ignore")
        if ".csproj" in content:
            return True
    return False


def detect_usage_steps(repo_root: Path, project_type: str) -> tuple[str, str, str]:
    install_step = "Unknown"
    build_step = "Unknown"
    run_step = "Unknown"

    package_json = repo_root / "package.json"
    if package_json.exists():
        try:
            package_data = json.loads(package_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            package_data = {}
        scripts = package_data.get("scripts", {})
        if isinstance(scripts, dict):
            install_step = "npm install"
            if "build" in scripts:
                build_step = "npm run build"
            if "start" in scripts:
                run_step = "npm run start"
            elif "dev" in scripts:
                run_step = "npm run dev"

    if install_step == "Unknown":
        if (repo_root / "requirements.txt").exists():
            install_step = "python -m pip install -r requirements.txt"
        elif (repo_root / "pyproject.toml").exists():
            install_step = "python -m pip install -e ."

    if build_step == "Unknown":
        if (repo_root / "Makefile").exists():
            build_step = "make"
        elif (repo_root / "Cargo.toml").exists():
            build_step = "cargo build"
        elif (repo_root / "go.mod").exists():
            build_step = "go build ./..."
        elif project_type == "WPF":
            build_step = get_wpf_build_command(repo_root)
        elif project_type == "Win32":
            build_step = get_win32_build_command(repo_root)
        elif project_type == "Qt":
            from context.platform_profiles import get_qt_build_command

            build_step = get_qt_build_command(repo_root)
        elif has_harmony_packaging_scripts(repo_root):
            build_step = get_harmony_build_command(repo_root)
        elif (repo_root / "hvigorfile.ts").exists() or (repo_root / "hvigorfile.js").exists():
            build_step = get_harmony_build_command(repo_root)
        elif repo_has_dotnet_solution(repo_root):
            build_step = "dotnet build"
        elif (
            (repo_root / "requirements.txt").exists()
            and not (repo_root / "pyproject.toml").exists()
            and not (repo_root / "setup.py").exists()
            and not (repo_root / "setup.cfg").exists()
        ):
            build_step = "N/A（项目无独立编译或打包步骤）"

    if project_type == "FastAPI":
        entry = find_fastapi_entry(repo_root)
        if entry:
            module = relative_display(entry, repo_root).removesuffix(".py").replace("/", ".")
            run_step = f"python -m uvicorn {module}:app --reload"

    return install_step, build_step, run_step


def detect_project_type(repo_root: Path) -> str:
    return profile_detect_project_type(repo_root)


def detect_validation_commands(repo_root: Path, project_type: str, build_step: str) -> tuple[str, str, str]:
    return profile_detect_validation_commands(repo_root, project_type, build_step)


def detect_test_command(repo_root: Path, project_type: str, quick_step: str) -> str:
    """返回有证据支持的通用测试候选，不臆造工具链入口。"""
    if project_type == "FastAPI" and (repo_root / "tests").is_dir():
        return "python -m pytest -q"
    if project_type == "Qt" and (repo_root / "CMakeLists.txt").exists():
        return quick_step if quick_step.startswith("ctest ") else "Unknown"
    if project_type == "Harmony":
        return "device-required"
    return "Unknown"


def is_wsl_host() -> bool:
    if "WSL_DISTRO_NAME" in os.environ or "WSL_INTEROP" in os.environ:
        return True
    proc_version = Path("/proc/version")
    if not proc_version.exists():
        return False
    try:
        content = proc_version.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return False
    return "microsoft" in content or "wsl" in content


def detect_build_bootstrap(repo_root: Path, project_type: str, build_step: str) -> str:
    lines = [
        "- **WorkingDirectory**（工作目录）：仓库根目录",
    ]

    if project_type in {"WPF", "Win32"}:
        lines.append("- **RecommendedTerminal**（建议终端）：Windows PowerShell 7 或 cmd")
        if is_wsl_host():
            lines.append("- **CanRunBuildHere**（当前环境能否构建）：no")
            lines.append("- **Reason**（原因）：当前宿主是 WSL，Windows 客户端编译链容易受路径、SDK、MSBuild 发现和子进程语义影响")
        elif sys.platform == "win32":
            lines.append("- **CanRunBuildHere**（当前环境能否构建）：yes")
        else:
            lines.append("- **CanRunBuildHere**（当前环境能否构建）：unknown")
            lines.append("- **Reason**（原因）：当前宿主不是 Windows，需在 Windows PowerShell/cmd 中确认工具链")

        if project_type == "WPF":
            lines.append("- **Preflight**（执行前检查）：`dotnet --info`；若使用旧式 .NET Framework 项目，还需确认 Visual Studio Build Tools")
            if first_matching_file(repo_root, "global.json"):
                lines.append("- **Evidence**（证据）：`global.json` 会约束 .NET SDK 版本")
            if first_matching_file(repo_root, "NuGet.config", "packages.config"):
                lines.append("- **Preflight**（执行前检查）：先执行 NuGet restore 或确认私有源可访问")
        else:
            lines.append("- **Preflight**（执行前检查）：`where msbuild`；确认 Visual Studio Build Tools、Windows SDK、PlatformToolset、Configuration/Platform")
            if first_matching_file(repo_root, "*.vcxproj"):
                lines.append("- **Evidence**（证据）：检测到 `.vcxproj`，需要 Windows 原生 MSBuild 工具链")
    elif project_type == "Harmony":
        lines.append("- **RecommendedTerminal**（建议终端）：项目约定的本机 shell；Windows 下优先 PowerShell/cmd")
        lines.append("- **CanRunBuildHere**（当前环境能否构建）：unknown")
        lines.append("- **Preflight**（执行前检查）：`ohpm --version`；`hvigorw --version`；确认 DevEco / hvigor / ohpm 与签名配置")
    elif project_type == "Qt":
        lines.append("- **RecommendedTerminal**（建议终端）：已加载 Qt/CMake 工具链环境的终端")
        lines.append("- **CanRunBuildHere**（当前环境能否构建）：unknown")
        lines.append("- **Preflight**（执行前检查）：`cmake --version`；`ctest --version`；确认 Qt Kit、生成器和 build preset")
    elif project_type == "FastAPI":
        lines.append("- **RecommendedTerminal**（建议终端）：项目 Python 虚拟环境中的 shell")
        lines.append("- **CanRunBuildHere**（当前环境能否构建）：unknown")
        lines.append("- **Preflight**（执行前检查）：`python --version`；确认已安装运行依赖与测试依赖")
        if (repo_root / "requirements.txt").exists():
            lines.append("- **Evidence**（证据）：`requirements.txt` 定义运行依赖")
        if (repo_root / "requirements-dev.txt").exists():
            lines.append("- **Evidence**（证据）：`requirements-dev.txt` 定义测试或开发依赖")
    else:
        lines.append("- **RecommendedTerminal**（建议终端）：PowerShell（Windows）或项目兼容 shell")
        lines.append("- **CanRunBuildHere**（当前环境能否构建）：unknown")

    if build_step == "Unknown":
        lines.append("- **MissingCommands**（缺失命令）：build 命令缺失，不能启动编译")
    elif build_step.startswith("N/A"):
        lines.append("- **BuildCommand**（构建命令）：N/A")
        lines.append("- **Reason**（原因）：项目无独立编译或打包步骤")
    else:
        lines.append(f"- **BuildCommand**（构建命令）：`{build_step}`")
        lines.append("- **FailureEvidence**（失败证据）：记录完整命令、工作目录、终端类型、退出码、前 50 行和最后 100 行构建日志")
    return "\n".join(lines)


def detect_high_risk_directories(repo_root: Path, project_type: str) -> list[str]:
    return profile_detect_high_risk_directories(repo_root, project_type)


def detect_restricted_areas(repo_root: Path) -> list[str]:
    restricted: list[str] = []
    for candidate, description in [
        ("bin", "构建产物"),
        ("obj", "构建中间产物"),
        ("dist", "打包产物"),
        ("build", "构建输出目录"),
        ("node_modules", "已安装的第三方依赖"),
        (".git", "版本控制元数据"),
    ]:
        if (repo_root / candidate).exists():
            restricted.append(f"{candidate}: {description}")
    return restricted or ["Unknown"]


def relative_display(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def file_contains_any(path: Path, needles: list[str]) -> bool:
    content = path.read_text(encoding="utf-8", errors="ignore")
    return any(needle in content for needle in needles)


def detect_native_bridge_info(repo_root: Path) -> tuple[bool, list[str]]:
    vcx_paths = find_all_matching_files(repo_root, "*.vcxproj")
    if vcx_paths:
        return True, sorted({path.stem for path in vcx_paths})

    bridge_dirs = []
    for path in iter_walk_files(repo_root):
        if path.suffix.lower() != ".cpp":
            continue
        parent_name = path.parent.name.lower()
        if any(keyword in parent_name for keyword in ("sdk", "interop", "bridge", "native", "win")):
            bridge_dirs.append(path.parent.name)
    if bridge_dirs:
        return True, sorted(set(bridge_dirs))

    return False, []


def detect_shared_cpp_core_info(repo_root: Path) -> tuple[bool, list[str]]:
    markers: list[str] = []
    cmake_file = repo_root / "CMakeLists.txt"
    if cmake_file.exists():
        content = cmake_file.read_text(encoding="utf-8", errors="ignore")
        if "add_library" in content:
            markers.append("CMake add_library")

    native_dir_names = {"shared_cpp", "native", "core", "sdk", "lib"}
    for path in find_all_matching_files(repo_root, "*.h", "*.hpp"):
        rel = relative_display(path, repo_root)
        if any(part.lower() in native_dir_names for part in path.parts):
            markers.append(rel)

    deduped: list[str] = []
    seen: set[str] = set()
    for marker in markers:
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(marker)
    return bool(deduped), deduped


def detect_language_framework_summary(repo_root: Path, project_type: str, languages: list[str]) -> str:
    has_native_bridge, bridge_projects = detect_native_bridge_info(repo_root)
    has_shared_cpp_core, _ = detect_shared_cpp_core_info(repo_root)
    summary_parts: list[str] = []

    if project_type == "WPF":
        summary_parts.append("C# + WPF")
    elif project_type == "Qt":
        summary_parts.append("Qt 客户端")
        if has_shared_cpp_core:
            summary_parts.append("共享 C++ 核心")
    elif project_type == "Harmony":
        summary_parts.append("Harmony")
    elif project_type == "FastAPI":
        summary_parts.append("Python + FastAPI")
    elif languages:
        summary_parts.append(" + ".join(languages[:2]))
    else:
        summary_parts.append("Unknown")

    if project_type == "Qt" and has_shared_cpp_core:
        return " + ".join(summary_parts)

    if has_native_bridge:
        bridge_label = "、".join(f"`{name}`" for name in bridge_projects[:3]) if bridge_projects else "NativeBridge"
        summary_parts.append(f"部分 C++/CLI（{bridge_label} 项目）")

    return "，".join(summary_parts)


def detect_architecture_pattern(repo_root: Path, project_type: str) -> str:
    if project_type == "FastAPI":
        if (repo_root / "app" / "routers").is_dir():
            return "FastAPI 模块化服务"
        return "FastAPI 服务"
    if first_matching_file(repo_root, "*ViewModel.cs") or (repo_root / "ViewModel").exists():
        return "MVVM"
    return "Unknown"


def detect_core_entry(repo_root: Path) -> str:
    entry = find_fastapi_entry(repo_root) or first_matching_file(repo_root, "App.xaml.cs", "Program.cs", "main.cpp", "main.cc")
    return relative_display(entry, repo_root) if entry else "Unknown"


def detect_sdk_call_chain(repo_root: Path) -> str:
    project_type = detect_project_type(repo_root)
    has_shared_cpp_core, _ = detect_shared_cpp_core_info(repo_root)
    if project_type == "Qt" and has_shared_cpp_core:
        return "Qt UI -> Qt 控制器/服务 -> C++ 包装层 -> 共享 C++ 核心"
    if project_type == "FastAPI":
        entry = find_fastapi_entry(repo_root)
        parts = [relative_display(entry, repo_root) if entry else "ASGI 入口"]
        for candidate in ("app/routers", "app/services", "app/core"):
            if (repo_root / candidate).is_dir():
                parts.append(candidate)
        return " -> ".join(parts)

    service_dir = None
    service_file = first_matching_file(repo_root, "*Service.cs")
    if service_file:
        namespace_parts = service_file.parent.parts[-2:]
        service_dir = ".".join(namespace_parts) + ".*"

    interface_file = first_matching_file(repo_root, "I*Service.cs")
    interface_name = "Unknown"
    if interface_file:
        parent_parts = interface_file.parent.parts[-2:]
        interface_name = ".".join(parent_parts) + "." + interface_file.stem

    has_native_bridge, bridge_projects = detect_native_bridge_info(repo_root)
    bridge_name = bridge_projects[0] if bridge_projects else "Unknown"
    bridge_part = f"{bridge_name}（C++/CLI）" if has_native_bridge and bridge_name != "Unknown" else "Unknown"
    native_part = (
        "原生 C++ SDK"
        if has_native_bridge and repo_has_any_suffix(repo_root, (".cpp", ".h", ".hpp"))
        else "Unknown"
    )

    parts = [service_dir or "Unknown", interface_name, bridge_part, native_part]
    return " -> ".join(parts)


def detect_version_marker(repo_root: Path) -> str:
    version_file = first_matching_file(repo_root, "VersionUtil.cs", "*Version*.cs")
    if version_file:
        return f"`{relative_display(version_file, repo_root)}`"
    return "Unknown"


MAX_STYLE_ANCHOR_FILES = 5
MAX_STYLE_ANCHOR_LINE_LEN = 120
MAX_STYLE_ANCHOR_FILE_BYTES = 256_000


def _extract_cs_style_anchor_line(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("using "):
            continue
        if line.startswith(
            (
                "namespace ",
                "file ",
                "public ",
                "internal ",
                "protected ",
                "private ",
                "partial ",
                "class ",
                "interface ",
                "struct ",
                "record ",
                "enum ",
            )
        ):
            return line[:MAX_STYLE_ANCHOR_LINE_LEN]
    return None


def _extract_ts_style_anchor_line(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("//") or line.startswith("/*") or line.startswith("*"):
            continue
        if line.startswith("import "):
            continue
        if line.startswith(("export ", "class ", "interface ", "type ", "function ", "const ", "enum ")):
            return line[:MAX_STYLE_ANCHOR_LINE_LEN]
    return None


def _extract_py_style_anchor_line(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("from ", "import ")):
            continue
        if line.startswith(("class ", "def ", "async def ")):
            return line[:MAX_STYLE_ANCHOR_LINE_LEN]
    return None


def detect_style_anchors(repo_root: Path) -> str:
    """抽取真实文件路径和一行结构示例，帮助 Agent 对齐现有风格。"""
    anchors: list[tuple[str, str | None]] = []
    seen: set[str] = set()

    def add_path(path: Path) -> None:
        if path.stat().st_size > MAX_STYLE_ANCHOR_FILE_BYTES:
            return
        rel = relative_display(path, repo_root)
        if rel in seen:
            return
        seen.add(rel)
        suffix = path.suffix.lower()
        snippet: str | None = None
        if suffix == ".cs":
            snippet = _extract_cs_style_anchor_line(path)
        elif suffix in {".ts", ".tsx", ".js", ".jsx"}:
            snippet = _extract_ts_style_anchor_line(path)
        elif suffix == ".py":
            snippet = _extract_py_style_anchor_line(path)
        anchors.append((rel, snippet))

    if repo_has_suffix(repo_root, ".cs"):
        priority_patterns = [
            "*Service.cs",
            "*ViewModel.cs",
            "*Command.cs",
            "App.xaml.cs",
            "Program.cs",
            "*Callback*.cs",
        ]
        for pattern in priority_patterns:
            for path in find_all_matching_files(repo_root, pattern):
                try:
                    add_path(path)
                except OSError:
                    continue
                if len(anchors) >= MAX_STYLE_ANCHOR_FILES:
                    break
            if len(anchors) >= MAX_STYLE_ANCHOR_FILES:
                break
        if len(anchors) < MAX_STYLE_ANCHOR_FILES:
            for path in sorted(p for p in iter_walk_files(repo_root) if p.suffix.lower() == ".cs"):
                try:
                    add_path(path)
                except OSError:
                    continue
                if len(anchors) >= MAX_STYLE_ANCHOR_FILES:
                    break
    elif repo_has_suffix(repo_root, ".ts") or repo_has_suffix(repo_root, ".tsx"):
        for pattern in ("**/src/**/*.ts", "**/src/**/*.tsx"):
            for path in sorted(repo_root.glob(pattern)):
                try:
                    add_path(path)
                except OSError:
                    continue
                if len(anchors) >= MAX_STYLE_ANCHOR_FILES:
                    break
            if len(anchors) >= MAX_STYLE_ANCHOR_FILES:
                break
        if len(anchors) < MAX_STYLE_ANCHOR_FILES:
            for path in sorted(
                p for p in iter_walk_files(repo_root) if p.suffix.lower() in {".ts", ".tsx"}
            ):
                try:
                    add_path(path)
                except OSError:
                    continue
                if len(anchors) >= MAX_STYLE_ANCHOR_FILES:
                    break
    elif repo_has_suffix(repo_root, ".py"):
        for path in sorted(p for p in iter_walk_files(repo_root) if p.suffix.lower() == ".py"):
            try:
                add_path(path)
            except OSError:
                continue
            if len(anchors) >= MAX_STYLE_ANCHOR_FILES:
                break

    if not anchors:
        return "Unknown"

    lines: list[str] = [
        "以下路径由扫描器按优先级从仓库抽样。**新增或修改代码应优先对齐**这些文件的组织方式（命名空间/模块分层、import/using 顺序、注释粒度、async 习惯等），避免在同目录或同层引入另一种写法。",
    ]
    for rel, snippet in anchors:
        lines.append(f"- `{rel}`")
        if snippet:
            lines.append(f"  - 结构性首行（截断）：`{snippet}`")
    return "\n".join(lines)


def detect_style_rules(repo_root: Path) -> str:
    if detect_project_type(repo_root) == "FastAPI":
        rules = [
            "- **模块/函数/变量**: 对齐现有 Python 文件中的 snake_case 命名",
            "- **路由组织**: 路由保持在现有 `routers` 模块，通过 `include_router` 注册",
            "- **异步边界**: I/O 路径保持现有 `async` / `await` 风格",
            "- **严禁**: 未经明确授权，不重命名公开路由、请求字段或响应字段",
        ]
        return "\n".join(rules)

    if not repo_has_suffix(repo_root, ".cs"):
        return "Unknown"

    service_files = find_all_matching_files(repo_root, "*Service.cs")
    viewmodel_files = find_all_matching_files(repo_root, "*ViewModel.cs")
    xaml_files = find_all_matching_files(repo_root, "*.xaml")

    rules = [
        "- **类/方法/属性**: PascalCase",
        "- **字段/局部变量**: camelCase 或 Unknown",
        ("- **接口**: `I` 前缀（如 `" + first_matching_file(repo_root, "I*.cs").stem + "`）") if first_matching_file(repo_root, "I*.cs") else "- **接口**: Unknown",
        "- **ViewModel**: `ViewModel` 后缀" if viewmodel_files else "- **ViewModel**: Unknown",
        "- **Service**: `Service` 后缀" if service_files else "- **Service**: Unknown",
        "- **View（窗口）**: `.xaml` 与 `.xaml.cs` 成对维护" if xaml_files else "- **View（窗口）**: Unknown",
        "- **严禁**: 未经明确授权，不重命名既有公开类、方法、接口签名",
    ]
    return "\n".join(rules)


def detect_architecture_rules(repo_root: Path) -> str:
    rules: list[str] = []
    sdk_chain = detect_sdk_call_chain(repo_root)
    if sdk_chain != "Unknown -> Unknown -> Unknown -> Unknown":
        rules.append("```")
        rules.append(sdk_chain.replace(" -> ", "  ->  "))
        rules.append("```")

    if first_matching_file(repo_root, "*.xaml") and first_matching_file(repo_root, "*ViewModel.cs"):
        rules.append("- **View 层**不得直接调用 SDK bridge 或原生层")
        rules.append("- **ViewModel 层**应通过 Service 或 Locator 获取能力，不直接跨层 new 原生依赖")
    iface = first_matching_file(repo_root, "I*Service.cs")
    if iface:
        rules.append(f"- **Service 层**围绕接口层组织，不直接让 UI 依赖 `{iface.stem}` 之下的原生实现细节")
    if any(
        file_contains_any(path, ["DispatcherHelper", "Application.Current.Dispatcher"])
        for path in iter_matching_files(repo_root, "*.cs")
    ):
        rules.append("- **UI 线程安全**: 所有 UI 更新必须回到 Dispatcher / UI 线程")

    return "\n".join(rules) if rules else "Unknown"


def detect_forbidden_operations(repo_root: Path) -> str:
    items: list[str] = []
    project_type = detect_project_type(repo_root)
    if project_type == "FastAPI":
        entry = find_fastapi_entry(repo_root)
        if entry:
            items.append(f"- 未确认启动、middleware 和 router 注册顺序前，禁止重写 `{relative_display(entry, repo_root)}`")
        items.append("- 未验证兼容性前，禁止修改既有 HTTP 路径、请求/响应 schema 或认证依赖")
        items.append("- 未生成和审查迁移前，禁止直接修改生产数据库结构")
        return "\n".join(items)
    native_cpp = first_matching_file(repo_root, "*.cpp")
    if native_cpp:
        if project_type == "Qt":
            items.append(f"- 直接修改 `{relative_display(native_cpp, repo_root)}`: Qt 共享 C++ Core，需确认调用链和 ABI 影响面后再动")
        else:
            items.append(f"- 直接修改 `{relative_display(native_cpp, repo_root)}`: C++/CLI 或原生桥接层，需完整理解调用链后再动")
    interface_file = first_matching_file(repo_root, "I*Service.cs")
    if interface_file:
        items.append(f"- 修改 `{relative_display(interface_file, repo_root)}` 接口签名: 会破坏实现契约")
    if first_matching_file(repo_root, "*.xaml.cs"):
        items.append("- 在 `.xaml.cs` 中写业务逻辑: 业务逻辑应尽量下沉到 ViewModel / Service")
    if any(
        file_contains_any(path, ["Thread.Sleep"])
        for path in iter_matching_files(repo_root, "*.cs", "*.cpp")
    ):
        items.append("- 在 UI 线程使用 `Thread.Sleep`: 会阻塞界面或消息循环")
    if native_cpp or first_matching_file(repo_root, "*.vcxproj"):
        items.append("- 未确认线程模型、资源释放和 ABI 约束前，禁止直接改底层 native bridge")
    return "\n".join(items) if items else "Unknown"


def detect_high_risk_files(repo_root: Path) -> str:
    candidates: list[tuple[str, str]] = []
    if detect_project_type(repo_root) == "FastAPI":
        entry = find_fastapi_entry(repo_root)
        if entry:
            candidates.append((relative_display(entry, repo_root), "ASGI 应用入口、生命周期、中间件和路由注册点"))
        for path in islice(iter_matching_files(repo_root, "*.py"), 30):
            rel = relative_display(path, repo_root)
            if "/routers/" in f"/{rel}":
                candidates.append((rel, "HTTP 路由与外部 API 契约"))
            elif rel.endswith(("security.py", "database.py", "config.py", "settings.py")):
                candidates.append((rel, "安全、数据库或运行配置边界"))
            if len(candidates) >= 5:
                break
    risk_patterns = {
        "AppUICallback.cs": "SDK 回调分发与 UI 线程切换枢纽",
        "AppUIState.cs": "全局 UI 状态或状态机聚合点",
        "App.xaml.cs": "应用生命周期、启动与全局初始化",
        "VersionUtil.cs": "版本判断、多定制或功能分流逻辑",
    }
    for file_name, reason in risk_patterns.items():
        path = first_matching_file(repo_root, file_name)
        if path:
            candidates.append((relative_display(path, repo_root), reason))

    iface_cpp = first_matching_file(repo_root, "I*Service.cs")
    if iface_cpp:
        candidates.append((relative_display(iface_cpp, repo_root), "Service 契约边界，影响所有实现方"))
    native_bridge_cpp = first_matching_file(repo_root, "*.cpp")
    if native_bridge_cpp and detect_project_type(repo_root) != "Qt":
        candidates.append((relative_display(native_bridge_cpp, repo_root), "C++/CLI 与 native bridge 实现，可能涉及非托管内存"))

    for path in islice(iter_matching_files(repo_root, "*ServiceImpl.cs"), 2):
        candidates.append((relative_display(path, repo_root), "核心 Service 实现，通常承载主业务链路"))

    for path in islice(iter_matching_files(repo_root, "*.py"), 300):
        content = path.read_text(encoding="utf-8", errors="ignore")
        relative_path = relative_display(path, repo_root)
        if "tests" in Path(relative_path).parts:
            continue
        if (
            ("FastAPI(" in content or "create_app(" in content)
            and any(
                token in content
                for token in (
                    "create_all(",
                    "include_router(",
                    "upgrade_",
                    "ensure_search_index(",
                    "lifespan=",
                    "@app.on_event",
                )
            )
        ):
            candidates.append(
                (
                    relative_path,
                    "应用启动与装配入口，包含初始化副作用或路由注册",
                )
            )
        if (
            ("asyncio.Lock(" in content or "threading.Lock(" in content)
            and any(token in content for token in ("attempt", "retry", "sleep(", "qa_client", "httpx", "requests."))
        ):
            candidates.append(
                (
                    relative_path,
                    "包含并发锁、重试或外部调用，失败状态与持久化语义风险较高",
                )
            )
        if any(token in content for token in ("engine.begin(", "metadata.create_all(", "ALTER TABLE", "PRAGMA ")):
            candidates.append(
                (
                    relative_path,
                    "包含数据库初始化、schema 或 Engine 事务操作",
                )
            )

    install_service = first_matching_file(repo_root, "install_service.ps1", "install*.sh", "install*.bat")
    if install_service:
        candidates.append(
            (
                relative_display(install_service, repo_root),
                "服务安装或部署入口，可能涉及管理员权限与持久化目录",
            )
        )

    deduped: list[tuple[str, str]] = []
    seen_paths: set[str] = set()
    for path, reason in candidates:
        if path not in seen_paths:
            deduped.append((path, reason))
            seen_paths.add(path)

    if not deduped:
        return "Unknown"

    return "\n".join(f"- `{path}`: {reason}" for path, reason in deduped[:12])


def merge_high_risk_files(semantic_value: str, detected_value: str) -> str:
    if semantic_value == "Unknown":
        return detected_value
    if detected_value == "Unknown":
        return semantic_value
    merged = semantic_value.rstrip()
    for line in detected_value.splitlines():
        path_match = line.split("`", 2)
        if len(path_match) >= 3 and f"`{path_match[1]}`" in merged:
            continue
        merged += f"\n{line}"
    return merged


def detect_feature_paths(repo_root: Path) -> str:
    suggestions: list[str] = []
    if detect_project_type(repo_root) == "FastAPI":
        if (repo_root / "app" / "routers").is_dir():
            suggestions.append("1. 在 `app/routers/` 的既有边界内新增或扩展 HTTP 路由")
        if (repo_root / "app" / "services").is_dir():
            suggestions.append("2. 将业务逻辑放入 `app/services/`，避免堆积在路由处理函数")
        if (repo_root / "tests").is_dir():
            suggestions.append("3. 在 `tests/` 增加对应路由、服务或回归测试")
        return "\n".join(suggestions) if suggestions else "Unknown"
    if first_matching_file(repo_root, "*Service.cs"):
        suggestions.append("1. 在现有 Service 目录下扩展或新增 `XxxService.cs`")

    if first_matching_file(repo_root, "*ViewModel.cs"):
        suggestions.append("2. 在 `ViewModel/` 或对应子目录扩展 `XxxViewModel.cs`")
    if first_matching_file(repo_root, "*.xaml"):
        suggestions.append("3. 在对应 View 目录维护 `.xaml` + `.xaml.cs` 成对文件")
    if first_matching_file(repo_root, "I*Service.cs") or first_matching_file(repo_root, "*.vcxproj"):
        suggestions.append("4. 涉及 SDK 或桥接回调时，先确认接口层与 bridge 层边界再下钻")

    return "\n".join(suggestions) if suggestions else "Unknown"


def detect_code_safety_rules(repo_root: Path) -> str:
    if detect_project_type(repo_root) == "FastAPI":
        return "\n".join(
            [
                "- 输入边界: 外部参数通过 FastAPI/Pydantic schema 校验，不信任原始请求数据",
                "- 异步资源: 数据库连接、HTTP client 和文件句柄必须按生命周期显式释放",
                "- 认证与密钥: 不记录 token、cookie、密码、身份证号或完整请求体",
                "- 异常处理: 对外响应保持稳定，内部日志保留可定位上下文但不得泄露敏感数据",
            ]
        )
    if not repo_has_suffix(repo_root, ".cs") and not first_matching_file(repo_root, "*.vcxproj"):
        return "Unknown"
    rules = [
        "- Null 检查: Service/Factory 返回值默认按可空处理",
        "- IDisposable / 资源释放: 文件句柄、流、native 句柄必须显式释放",
        "- 异常处理: Service 层和 bridge 调用层必须带上下文捕获异常",
    ]
    if any(
        file_contains_any(path, ["DispatcherHelper", "Application.Current.Dispatcher"])
        for path in iter_matching_files(repo_root, "*.cs")
    ):
        rules.append("- UI 线程: ObservableCollection 和界面状态更新必须切回 Dispatcher")
    if first_matching_file(repo_root, "*.vcxproj"):
        rules.append("- Native bridge: 修改 C++/CLI 或 Win32 API 相关代码前必须确认线程、ABI 和资源生命周期")
    return "\n".join(rules)


def detect_multi_version_notes(repo_root: Path) -> str:
    version_file = first_matching_file(repo_root, "VersionUtil.cs", "*CustomService*.cs", "*ConfigService*.cs")
    if not version_file:
        return "Unknown"
    return f"- 版本/定制逻辑集中在 `{relative_display(version_file, repo_root)}` 或相邻配置服务中，修改前需验证不同品牌/版本路径"


def detect_logging_rules(repo_root: Path) -> str:
    if detect_project_type(repo_root) == "FastAPI" and any(
        file_contains_any(path, ["logging.getLogger", "import logging"])
        for path in iter_matching_files(repo_root, "*.py")
    ):
        return "\n".join(
            [
                "- 复用项目现有 Python logging 配置，不在业务模块重复初始化全局日志",
                "- 请求、启动和外部调用日志不得包含密钥、token、cookie 或完整个人信息",
            ]
        )
    if any(
        file_contains_any(path, ["ILog", "LogManager", "log.Debug", "log.Info"])
        for path in iter_matching_files(repo_root, "*.cs", "*.cpp")
    ):
        return "\n".join(
            [
                "- 类级别日志对象应保持单例化，避免散乱实例化",
                "- 关键流程打 `Info`，调试细节打 `Debug`，异常带上下文和异常对象",
            ]
        )
    return "Unknown"


def detect_exploration_suggestions(repo_root: Path) -> str:
    suggestions: list[str] = []
    if detect_project_type(repo_root) == "FastAPI":
        entry = find_fastapi_entry(repo_root)
        if entry:
            suggestions.append(f"1. 先读 `{relative_display(entry, repo_root)}`，确认 lifespan、middleware 和 router 注册顺序")
        if (repo_root / "app" / "routers").is_dir():
            suggestions.append("2. 从 `app/routers/` 的 HTTP 入口追到 service/core 层，再定位数据或外部集成边界")
        if (repo_root / "tests").is_dir():
            suggestions.append("3. 修改前在 `tests/` 查找同路由或同服务的现有回归覆盖")
        return "\n".join(suggestions)
    callback_file = first_matching_file(repo_root, "AppUICallback.cs", "*Callback*.cs")
    if callback_file:
        suggestions.append(f"1. 定位问题前，先读 `{relative_display(callback_file, repo_root)}`，理解事件来源和回调分发")
    service_file = first_matching_file(repo_root, "*CallService.cs", "*Service.cs")
    interface_file = first_matching_file(repo_root, "I*Service.cs")
    bridge_cpp = first_matching_file(repo_root, "*.cpp")
    if service_file and interface_file and bridge_cpp:
        suggestions.append(
            f"2. 追踪服务调用链：`{service_file.stem}` -> `{interface_file.stem}` -> `{bridge_cpp.parent.name}`"
        )
    if first_matching_file(repo_root, "*.xaml") and first_matching_file(repo_root, "*ViewModel.cs"):
        suggestions.append("3. UI 问题先看 `.xaml`，再看对应 `ViewModel.cs`，最后回到 `Service` 层")
    state_file = first_matching_file(repo_root, "*State*.cs")
    if state_file:
        suggestions.append(f"4. 崩溃或时序问题优先结合 `{relative_display(state_file, repo_root)}` 这类状态文件检查状态机")
    return "\n".join(suggestions) if suggestions else "Unknown"


def detect_nativebridge_signals(repo_root: Path) -> list[str]:
    signals: list[str] = []
    project_type = detect_project_type(repo_root)
    has_shared_cpp_core, shared_cpp_markers = detect_shared_cpp_core_info(repo_root)

    if project_type == "Qt" and has_shared_cpp_core:
        signals.append("Qt 客户端 -> 共享 C++ 核心：检测到 Qt UI 与共享 C++ 底层链路")
        for marker in shared_cpp_markers[:3]:
            signals.append(f"`{marker}`：共享 C++ 核心候选")
    elif project_type == "FastAPI":
        entry = find_fastapi_entry(repo_root)
        if entry:
            signals.append(f"`{relative_display(entry, repo_root)}`：FastAPI ASGI 应用入口")
        for candidate, label in (("app/routers", "路由层"), ("app/services", "服务层"), ("app/core", "核心基础设施层")):
            if (repo_root / candidate).is_dir():
                signals.append(f"`{candidate}`：FastAPI {label}候选")

    for path in islice(iter_matching_files(repo_root, "*.vcxproj"), 3):
        signals.append(f"`{relative_display(path, repo_root)}`：检测到原生工程或桥接工程")

    for path in islice(iter_matching_files(repo_root, "*.cs"), 30):
        content = path.read_text(encoding="utf-8", errors="ignore")
        relative_path = relative_display(path, repo_root)
        if "DllImport" in content:
            signals.append(f"`{relative_path}`：检测到 DllImport / PInvoke")
        if "MarshalAs" in content or "System.Runtime.InteropServices.Marshal" in content:
            signals.append(f"`{relative_path}`：检测到 MarshalAs / marshaling")
        if "delegate" in content and ("Callback" in content or "Observer" in content):
            signals.append(f"`{relative_path}`：检测到 callback / observer 定义")

    for path in islice(iter_matching_files(repo_root, "*.cpp", "*.h", "*.hpp"), 30):
        content = path.read_text(encoding="utf-8", errors="ignore")
        relative_path = relative_display(path, repo_root)
        if any(token in content for token in ("windows.h", "HWND", "HANDLE", "CreateWindow", "SendMessage", "GetMessage")):
            signals.append(f"`{relative_path}`：检测到 Win32 API 使用")

    deduped: list[str] = []
    seen: set[str] = set()
    for item in signals:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped or ["Unknown"]


def detect_manual_review_items(
    repo_root: Path,
    build_step: str,
    test_step: str,
    quick_step: str,
    bugfix_step: str,
    full_step: str,
) -> list[str]:
    items: list[str] = []
    project_type = detect_project_type(repo_root)
    has_shared_cpp_core, shared_cpp_markers = detect_shared_cpp_core_info(repo_root)

    if project_type == "Qt" and has_shared_cpp_core:
        header_markers = [marker for marker in shared_cpp_markers if marker.endswith((".h", ".hpp"))]
        if header_markers:
            items.append(f"`{header_markers[0]}`：C++ 导出头文件或 ABI 边界需人工确认")
        else:
            items.append("C++ 导出头文件或 ABI 边界需人工确认")
        items.append("Qt signal/slot 跨线程调用、回调生命周期和共享 C++ Core 影响面需人工确认")

    if first_matching_file(repo_root, "*.vcxproj") or any(
        "DllImport" in path.read_text(encoding="utf-8", errors="ignore")
        for path in islice(iter_matching_files(repo_root, "*.cs"), 30)
    ):
        items.append("Native bridge 的 ABI、线程模型、句柄生命周期和 marshaling 策略需人工确认")

    if any(
        "MarshalAs" in path.read_text(encoding="utf-8", errors="ignore")
        for path in islice(iter_matching_files(repo_root, "*.cs"), 30)
    ):
        items.append("P/Invoke 的参数对齐、字符串编码和返回值封送策略需人工确认")

    if any(
        "DispatcherHelper" in path.read_text(encoding="utf-8", errors="ignore")
        or "Application.Current.Dispatcher" in path.read_text(encoding="utf-8", errors="ignore")
        for path in islice(iter_matching_files(repo_root, "*.cs"), 30)
    ):
        items.append("UI 线程切换规则是否完整覆盖关键回调路径，需人工确认")

    if bugfix_step == "Unknown":
        items.append("`bugfix` 验证命令仍缺失，需人工补齐可信入口")

    if build_step == "Unknown" or test_step == "Unknown" or quick_step == "Unknown" or full_step == "Unknown":
        items.append("build / test / quick / full 命令映射不完整，需人工确认最终入口")

    high_risk_cpp = first_matching_file(repo_root, "*.cpp")
    if high_risk_cpp:
        items.append(f"`{relative_display(high_risk_cpp, repo_root)}` 是否允许 AI 直接修改，需人工确认")

    return items or ["Unknown"]


def detect_architecture_overview(core_modules: list[str]) -> str:
    if not core_modules:
        return "Unknown"
    module_names = ", ".join(item.split(":", 1)[0] for item in core_modules[:5])
    return f"仓库按顶层模块组织，主要包括：{module_names}。"


def detect_module_dependency_graph(core_modules: list[str]) -> str:
    if not core_modules:
        return "Unknown"
    return "Unknown"


def detect_module_interfaces(core_modules: list[str]) -> list[str]:
    if not core_modules:
        return ["Unknown"]
    return ["Unknown"]


def detect_key_module_markers(core_modules: list[str]) -> list[str]:
    if not core_modules:
        return ["Unknown"]
    return core_modules[: min(3, len(core_modules))]


def format_bullets(items: list[str]) -> str:
    meaningful = [item for item in items if item and item != "Unknown"]
    if not meaningful:
        return "- 暂无"
    return "\n".join(f"- {item}" for item in meaningful)


def validate_generated_documents(generated_files: dict[str, str]) -> None:
    for file_name, content in generated_files.items():
        for label, pattern in GENERATED_DOCUMENT_ANTI_PATTERNS:
            if pattern.search(content):
                raise ManagedDocumentError(f"{file_name}：生成文档包含{label}")


def render_readme(
    repo_root: Path,
    project_name: str,
    project_type: str,
    project_summary: str,
    languages: list[str],
    build_systems: list[str],
    core_modules: list[str],
    install_step: str,
    build_step: str,
    run_step: str,
) -> str:
    template = read_template("README.template.md", repo_root)
    return (
        template.replace("{项目名称或 Unknown}", project_name or "Unknown", 1)
        .replace("{项目简介或 Unknown}", project_summary, 1)
        .replace("{语言列表或 Unknown}", ", ".join(languages) if languages else "Unknown", 1)
        .replace("{构建系统或 Unknown}", ", ".join(build_systems) if build_systems else "Unknown", 1)
        .replace("- {模块1: 描述}\n- {模块2: 描述}\n- ...", format_bullets(core_modules), 1)
        .replace("{步骤或 Unknown}", install_step, 1)
        .replace("{步骤或 Unknown}", build_step, 1)
        .replace("{步骤或 Unknown}", run_step, 1)
    )


def render_agents(
    repo_root: Path,
    project_name: str,
    contract_index: ContractIndex,
    language_framework_summary: str,
    architecture_pattern: str,
    core_entry: str,
    sdk_call_chain: str,
    version_marker: str,
    style_rules: str,
    architecture_rules: str,
    forbidden_operations: str,
    high_risk_files: str,
    feature_paths: str,
    code_safety_rules: str,
    multi_version_notes: str,
    logging_rules: str,
    exploration_suggestions: str,
    auto_detected_candidates: str,
    manual_review_items: str,
    style_anchors: str,
) -> str:
    template = read_template("AGENTS.template.md", repo_root)
    contract_value = lambda value: f"`{value}`" if value != "Unknown" else "Unknown"
    return (
        template.replace("{项目名称或 Unknown}", project_name or "Unknown", 1)
        .replace("{构建规范路径}", contract_index.build, 1)
        .replace("{Git规范路径或 Unknown}", contract_value(contract_index.git_workflow), 1)
        .replace("{代码规范路径或 Unknown}", contract_value(contract_index.code_style), 1)
        .replace("{发布规范路径或 Unknown}", contract_value(contract_index.release), 1)
        .replace("{变更日志路径或 Unknown}", contract_value(contract_index.changelog), 1)
        .replace("{语言框架摘要或 Unknown}", language_framework_summary, 1)
        .replace("{架构模式或 Unknown}", architecture_pattern, 1)
        .replace("{核心入口或 Unknown}", core_entry, 1)
        .replace("{核心调用链或 Unknown}", sdk_call_chain, 1)
        .replace("- **SDK 调用链**: {SDK 调用链或 Unknown}", f"- **核心调用链**: {sdk_call_chain}", 1)
        .replace("{版本识别点或 Unknown}", version_marker, 1)
        .replace("{命名与风格约束或 Unknown}", style_rules, 1)
        .replace("{架构边界规则或 Unknown}", architecture_rules, 1)
        .replace("{禁止操作清单或 Unknown}", forbidden_operations, 1)
        .replace("{高风险文件标注或 Unknown}", high_risk_files, 1)
        .replace("{新增功能的一般流程或 Unknown}", feature_paths, 1)
        .replace("{新增功能标准路径或 Unknown}", feature_paths, 1)
        .replace("{代码安全规范或 Unknown}", code_safety_rules, 1)
        .replace("{多版本注意事项或 Unknown}", multi_version_notes, 1)
        .replace("{日志规范或 Unknown}", logging_rules, 1)
        .replace("{提问与探索建议或 Unknown}", exploration_suggestions, 1)
        .replace("{自动识别候选或 Unknown}", auto_detected_candidates, 1)
        .replace("{需人工确认或 Unknown}", manual_review_items, 1)
        .replace("{代码风格示例或 Unknown}", style_anchors, 1)
        .replace("{代码风格锚点或 Unknown}", style_anchors, 1)
    )


def render_architecture(
    repo_root: Path,
    dependency_graph: str,
    architecture_overview: str,
    core_flow: str,
    architecture_pattern: str,
    module_interfaces: list[str],
    key_module_markers: list[str],
) -> str:
    template = read_template("ARCHITECTURE.template.md", repo_root)
    return (
        template.replace("{文本表示的依赖关系，例如 ModuleA -> ModuleB -> ModuleC 或 Unknown}", dependency_graph, 1)
        .replace("{主要功能调用链或 Unknown}", core_flow, 1)
        .replace("{如 MVC、MVVM、微服务等，无法确定标记 Unknown}", architecture_pattern, 1)
        .replace("- {模块1 -> 模块2: 接口类型或 Unknown}\n- {模块2 -> 模块3: 接口类型或 Unknown}", format_bullets(module_interfaces), 1)
        .replace("- {模块1: 上游/下游/核心功能说明或 Unknown}\n- {模块2: 上游/下游/核心功能说明或 Unknown}", format_bullets(key_module_markers), 1)
    )


def render_harness(
    repo_root: Path,
    project_type: str,
    build_step: str,
    build_bootstrap: str,
    test_step: str,
    quick_step: str,
    bugfix_step: str,
    full_step: str,
    high_risk_directories: list[str],
    restricted_areas: list[str],
    auto_detected_candidates: list[str],
    manual_review_items: list[str],
) -> str:
    template = read_template("HARNESS.template.md", repo_root)
    return (
        template.replace("{项目类型或 Unknown}", project_type, 1)
        .replace("{命令或 Unknown}", build_step, 1)
        .replace("{编译与启动问题排查结果或 Unknown}", build_bootstrap, 1)
        .replace("{编译启动诊断或 Unknown}", build_bootstrap, 1)
        .replace("{命令或 Unknown}", test_step, 1)
        .replace("{命令或 Unknown}", quick_step, 1)
        .replace("{命令或 Unknown}", bugfix_step, 1)
        .replace("{命令或 Unknown}", full_step, 1)
        .replace("- {目录1: 风险说明}\n- {目录2: 风险说明}\n- ...", format_bullets(high_risk_directories), 1)
        .replace("- {区域1: 原因}\n- {区域2: 原因}\n- ...", format_bullets(restricted_areas), 1)
        .replace("- {候选1: 说明}\n- {候选2: 说明}\n- ...", format_bullets(auto_detected_candidates), 1)
        .replace("- {确认项1: 原因}\n- {确认项2: 原因}\n- ...", format_bullets(manual_review_items), 1)
    )


def generate_context_files(repo_root: Path, analysis: SemanticAnalysis | None = None) -> dict[str, str]:
    project_name = detect_project_name(repo_root)
    contract_index = discover_contract_index(repo_root)
    languages = detect_languages(repo_root)
    build_systems = detect_build_systems(repo_root)
    core_modules = detect_core_modules(repo_root)
    project_type = detect_project_type(repo_root)
    install_step, build_step, run_step = detect_usage_steps(repo_root, project_type)
    quick_step, bugfix_step, full_step = detect_validation_commands(repo_root, project_type, build_step)
    test_step = detect_test_command(repo_root, project_type, quick_step)
    project_summary = f"根据仓库证据识别为 {project_type} 项目。" if project_type != "Unknown" else "Unknown"
    architecture_overview = detect_architecture_overview(core_modules)
    dependency_graph = detect_module_dependency_graph(core_modules)
    module_interfaces = detect_module_interfaces(core_modules)
    key_module_markers = detect_key_module_markers(core_modules)
    high_risk_directories = detect_high_risk_directories(repo_root, project_type)
    restricted_areas = detect_restricted_areas(repo_root)
    language_framework_summary = detect_language_framework_summary(repo_root, project_type, languages)
    architecture_pattern = detect_architecture_pattern(repo_root, project_type)
    core_entry = detect_core_entry(repo_root)
    sdk_call_chain = detect_sdk_call_chain(repo_root)
    if project_type == "FastAPI":
        dependency_graph = sdk_call_chain
        architecture_overview = "FastAPI ASGI 入口把 HTTP 请求交给路由模块，再由下游 service/core 模块处理。"
        module_interfaces = [
            "ASGI 入口 -> routers：通过 FastAPI include_router 注册路由",
            "routers -> services/core：通过 Python 模块调用和依赖注入协作",
        ]
    version_marker = detect_version_marker(repo_root)
    style_rules = detect_style_rules(repo_root)
    style_anchors = detect_style_anchors(repo_root)
    architecture_rules = detect_architecture_rules(repo_root)
    forbidden_operations = detect_forbidden_operations(repo_root)
    detected_high_risk_files = detect_high_risk_files(repo_root)
    high_risk_files = detected_high_risk_files
    feature_paths = detect_feature_paths(repo_root)
    code_safety_rules = detect_code_safety_rules(repo_root)
    multi_version_notes = detect_multi_version_notes(repo_root)
    logging_rules = detect_logging_rules(repo_root)
    exploration_suggestions = detect_exploration_suggestions(repo_root)
    auto_detected_candidates_list = detect_nativebridge_signals(repo_root)

    if analysis is not None:
        project_type = analysis.claim("project_type", "Unknown")
        project_summary = analysis.claim("project_summary", "Unknown")
        language_framework_summary = analysis.claim("language_framework", "Unknown")
        architecture_pattern = analysis.claim("architecture_pattern", "Unknown")
        core_entry = analysis.claim("core_entry", "Unknown")
        sdk_call_chain = analysis.claim("core_flow", "Unknown")
        dependency_graph = analysis.claim("dependency_graph", "Unknown")
        version_marker = analysis.claim("version_marker", "Unknown")
        install_step = analysis.claim("install_command", "Unknown")
        build_step = analysis.claim("build_command", "Unknown")
        run_step = analysis.claim("run_command", "Unknown")
        test_step = analysis.claim("test_command", test_step)
        quick_step = analysis.claim("quick_command", "Unknown")
        bugfix_step = analysis.claim("bugfix_command", "Unknown")
        full_step = analysis.claim("full_command", "Unknown")
        style_rules = analysis.claim("style_rules", style_rules)
        architecture_rules = analysis.claim("architecture_rules", architecture_rules)
        forbidden_operations = analysis.claim("forbidden_operations", forbidden_operations)
        high_risk_files = merge_high_risk_files(
            analysis.claim("high_risk_files", "Unknown"),
            detected_high_risk_files,
        )
        feature_paths = analysis.claim("feature_paths", feature_paths)
        code_safety_rules = analysis.claim("code_safety_rules", code_safety_rules)
        multi_version_notes = analysis.claim("multi_version_notes", multi_version_notes)
        logging_rules = analysis.claim("logging_rules", logging_rules)
        exploration_suggestions = analysis.claim("exploration_suggestions", exploration_suggestions)
        core_modules = analysis.items("core_modules", core_modules)
        module_interfaces = analysis.items("module_interfaces", module_interfaces)
        key_module_markers = analysis.items("key_module_markers", key_module_markers)
        high_risk_directories = analysis.items("high_risk_directories", high_risk_directories)
        auto_detected_candidates_list = analysis.items("auto_detected_candidates", auto_detected_candidates_list)

    build_bootstrap = detect_build_bootstrap(repo_root, project_type, build_step)
    manual_review_items_list = detect_manual_review_items(
        repo_root,
        build_step,
        test_step,
        quick_step,
        bugfix_step,
        full_step,
    )
    if analysis is not None:
        manual_review_items_list.extend(analysis.manual_review_items)
    auto_detected_candidates = format_bullets(auto_detected_candidates_list)
    agents_manual_review_items = format_bullets(manual_review_items_list + list(contract_index.manual_review))

    generated_files = {
        "README.md": render_readme(
            repo_root,
            project_name,
            project_type,
            project_summary,
            languages,
            build_systems,
            core_modules,
            install_step,
            build_step,
            run_step,
        ),
        "AGENTS.md": render_agents(
            repo_root,
            project_name,
            contract_index,
            language_framework_summary,
            architecture_pattern,
            core_entry,
            sdk_call_chain,
            version_marker,
            style_rules,
            architecture_rules,
            forbidden_operations,
            high_risk_files,
            feature_paths,
            code_safety_rules,
            multi_version_notes,
            logging_rules,
            exploration_suggestions,
            auto_detected_candidates,
            agents_manual_review_items,
            style_anchors,
        ),
        "ARCHITECTURE.md": render_architecture(
            repo_root,
            dependency_graph,
            architecture_overview,
            sdk_call_chain,
            architecture_pattern,
            module_interfaces,
            key_module_markers,
        ),
        "HARNESS.md": render_harness(
            repo_root,
            project_type,
            build_step,
            build_bootstrap,
            test_step,
            quick_step,
            bugfix_step,
            full_step,
            high_risk_directories,
            restricted_areas,
            auto_detected_candidates_list,
            manual_review_items_list,
        ),
    }
    normalized_files: dict[str, str] = {}
    for file_name, content in generated_files.items():
        normalized, _ = strip_legacy_managed_markers(content)
        parse_markdown_sections(normalized, SECTION_SPECS[file_name])
        normalized_files[file_name] = normalized.rstrip("\n")
    validate_generated_documents(normalized_files)
    return normalized_files


def summarize_diff(file_name: str, existing: str, generated: str) -> tuple[str, str]:
    diff = list(
        difflib.unified_diff(
            existing.splitlines(),
            generated.splitlines(),
            fromfile=f"{file_name}（现有内容）",
            tofile=f"{file_name}（生成内容）",
            lineterm="",
        )
    )
    changed_line_count = sum(
        1 for line in diff if (line.startswith("+") or line.startswith("-")) and not line.startswith("+++") and not line.startswith("---")
    )
    summary = f"{file_name}：差异行数={changed_line_count}，现有行数={len(existing.splitlines())}，生成行数={len(generated.splitlines())}"
    return summary, "\n".join(diff)


def summarize_section_diffs(
    file_name: str,
    existing: str,
    merged: str,
    changed_ids: list[str],
) -> str:
    specs = SECTION_SPECS[file_name]
    cleaned_existing, legacy_ids = strip_legacy_managed_markers(existing)
    cleaned_merged, _ = strip_legacy_managed_markers(merged)
    existing_sections = parse_markdown_sections(cleaned_existing, specs)
    merged_sections = parse_markdown_sections(cleaned_merged, specs)
    rendered: list[str] = []
    if legacy_ids:
        rendered.extend(
            difflib.unified_diff(
                existing.splitlines(),
                cleaned_existing.splitlines(),
                fromfile=f"{file_name}:legacy-markers（现有内容）",
                tofile=f"{file_name}:legacy-markers（已移除）",
                lineterm="",
            )
        )
    for section_id in changed_ids:
        existing_body = existing_sections[section_id].body
        merged_body = merged_sections[section_id].body
        rendered.extend(
            difflib.unified_diff(
                existing_body.splitlines(),
                merged_body.splitlines(),
                fromfile=f"{file_name}:{section_id}（现有内容）",
                tofile=f"{file_name}:{section_id}（生成内容）",
                lineterm="",
            )
        )
    return "\n".join(rendered)


def prompt_overwrite_action(file_name: str) -> str:
    prompt = f"如何处理 {file_name}？[y] 应用 / [n] 跳过 / [all] 全部应用 / [none] 全部跳过 / [quit] 退出："
    while True:
        response = input(prompt).strip().lower()
        if response in {"y", "yes"}:
            return "yes"
        if response in {"n", "no", ""}:
            return "no"
        if response == "all":
            return "all"
        if response == "none":
            return "none"
        if response in {"q", "quit"}:
            return "quit"
        print("输入无效，请输入 y、n、all、none 或 quit。")


def write_initial_context_files(repo_root: Path, generated_files: dict[str, str], force: bool = False) -> int:
    differing_files: list[str] = []
    created_files: list[str] = []
    unchanged_files: list[str] = []

    for file_name, content in generated_files.items():
        target_path = repo_root / file_name
        generated_bytes = (content + "\n").encode("utf-8")
        if not target_path.exists():
            target_path.write_bytes(generated_bytes)
            created_files.append(file_name)
            continue

        if target_path.read_bytes() == generated_bytes:
            unchanged_files.append(file_name)
            continue

        differing_files.append(file_name)

    if created_files:
        print("已创建文件：")
        for file_name in created_files:
            print(f"- {file_name}")

    if unchanged_files:
        print("未变化的文件：")
        for file_name in unchanged_files:
            print(f"- {file_name}")

    if not differing_files:
        return 0

    print("以下上下文文件已有不同内容，本次未修改：")
    for file_name in differing_files:
        print(f"- {file_name}")
    if force:
        print("scan 模式下，即使使用 --force 也不会覆盖现有上下文文件。")
    print("请运行 `dev-harness-context refresh <repo-path>` 预览固定章节更新。")
    return 2


def refresh_context_files(repo_root: Path, generated_files: dict[str, str], force: bool = False) -> int:
    pending: list[tuple[str, Path, str, DocumentFormat, list[str], str]] = []
    missing: list[tuple[str, Path, bytes]] = []
    errors: list[tuple[str, str]] = []
    interactive = sys.stdin.isatty()

    for file_name, content in generated_files.items():
        target_path = repo_root / file_name
        generated = content + "\n"
        if not target_path.exists():
            missing.append((file_name, target_path, generated.encode("utf-8")))
            continue
        try:
            existing, document_format = decode_document(target_path.read_bytes())
        except ManagedDocumentError as exc:
            errors.append((file_name, str(exc)))
            continue

        try:
            merged, changed_ids, legacy_ids = merge_markdown_sections(
                existing,
                generated,
                SECTION_SPECS[file_name],
            )
        except ManagedDocumentError as exc:
            errors.append((file_name, str(exc)))
            continue
        if not changed_ids and not legacy_ids:
            continue
        displayed_ids = (["legacy-markers"] if legacy_ids else []) + changed_ids
        diff_text = summarize_section_diffs(file_name, existing, merged, changed_ids)
        pending.append((file_name, target_path, merged, document_format, displayed_ids, diff_text))

    if errors:
        for file_name, message in errors:
            print(f"错误：无法刷新 {file_name}：{message}")
        return 1

    for file_name, target_path, content in missing:
        target_path.write_bytes(content)
        print(f"已创建：{file_name}")

    if not pending:
        return 0

    print("检测到固定章节更新：")
    for file_name, _, _, _, changed_ids, _ in pending:
        print(f"- {file_name}: {', '.join(changed_ids)}")

    if not force and not interactive:
        for file_name, _, _, _, _, diff_text in pending:
            print(f"--- 章节差异开始：{file_name} ---")
            print(diff_text)
            print(f"--- 章节差异结束：{file_name} ---")
        print("当前仅预览；请使用 --force 重新运行，或在交互式终端中确认后应用固定章节更新。")
        return 2

    updated: list[str] = []
    skipped: list[str] = []
    interactive_mode = "ask"
    for file_name, target_path, merged, document_format, _, diff_text in pending:
        print(f"--- 章节差异开始：{file_name} ---")
        print(diff_text)
        print(f"--- 章节差异结束：{file_name} ---")
        if force or interactive_mode == "all":
            action = "yes"
        elif interactive_mode == "none":
            action = "no"
        else:
            action = prompt_overwrite_action(file_name)
        if action == "quit":
            print(f"已按要求退出，未修改：{file_name}")
            return 130
        if action == "all":
            interactive_mode = "all"
            action = "yes"
        elif action == "none":
            interactive_mode = "none"
            action = "no"
        if action == "yes":
            atomic_write_document(target_path, merged, document_format)
            updated.append(file_name)
            print(f"已更新固定章节：{file_name}")
        else:
            skipped.append(file_name)
            print(f"已跳过：{file_name}")

    return 2 if skipped else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="扫描真实仓库并生成 README.md、AGENTS.md、ARCHITECTURE.md 和 HARNESS.md。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    evidence_parser = subparsers.add_parser("evidence", help="以 JSON 收集不依赖框架的仓库证据")
    evidence_parser.add_argument("repo_path", type=Path, help="目标仓库根目录")

    scan_parser = subparsers.add_parser("scan", help="扫描仓库并生成上下文文件")
    scan_parser.add_argument("repo_path", type=Path, help="目标仓库根目录")
    scan_parser.add_argument("--force", action="store_true", help="仅为兼容旧调用保留；不会覆盖现有文件")
    scan_parser.add_argument("--analysis", type=Path, help="已校验的 AI 语义分析 JSON")

    refresh_parser = subparsers.add_parser("refresh", help="只刷新固定 Markdown 章节")
    refresh_parser.add_argument("repo_path", type=Path, help="目标仓库根目录")
    refresh_parser.add_argument("--force", action="store_true", help="不询问，直接应用固定章节更新")
    refresh_parser.add_argument("--analysis", type=Path, help="已校验的 AI 语义分析 JSON")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = args.repo_path.resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        print(f"错误：仓库路径不存在或不是目录：{repo_root}")
        return 1

    if args.command == "evidence":
        evidence = collect_repository_evidence(repo_root)
        print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True))
        if evidence["truncated"]:
            print("错误：仓库证据已被截断；请缩小扫描范围或提高扫描上限。", file=sys.stderr)
            return 2
        return 0

    analysis = None
    if args.analysis is not None:
        try:
            analysis = load_semantic_analysis(args.analysis.resolve(), repo_root)
        except SemanticAnalysisError as exc:
            print(f"错误：AI 语义分析无效：{exc}")
            return 1

    try:
        generated_files = generate_context_files(repo_root, analysis=analysis)
    except (ManagedDocumentError, FileNotFoundError, UnicodeError) as exc:
        print(f"错误：Context 模板无效：{exc}")
        return 1
    if args.command == "scan":
        return write_initial_context_files(repo_root, generated_files, force=args.force)
    if args.command == "refresh":
        return refresh_context_files(repo_root, generated_files, force=args.force)
    parser.error("未知命令")


def cli_main() -> int:
    return main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(cli_main())
