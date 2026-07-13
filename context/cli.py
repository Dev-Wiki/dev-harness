from __future__ import annotations

import argparse
import difflib
import json
import os
import sys
from itertools import islice
from pathlib import Path

from context.contracts import ContractIndex, discover_contract_index
from context.managed import (
    DocumentFormat,
    ManagedDocumentError,
    atomic_write_document,
    decode_document,
    merge_managed_blocks,
    migrate_legacy_document,
    parse_managed_blocks,
)
from context.platform_profiles import (
    detect_high_risk_directories as profile_detect_high_risk_directories,
    detect_project_type as profile_detect_project_type,
    detect_validation_commands as profile_detect_validation_commands,
    get_harmony_build_command,
    get_win32_build_command,
    get_wpf_build_command,
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

TARGET_FILES = ("README.md", "AGENTS.md", "ARCHITECTURE.md", "HARNESS.md")
TEMPLATE_FILES = (
    "README.template.md",
    "AGENTS.template.md",
    "ARCHITECTURE.template.md",
    "HARNESS.template.md",
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
    ".h": "C/C++ Header",
    ".hpp": "C/C++ Header",
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
    raise FileNotFoundError("Cannot locate context templates directory")


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
        ("requirements.txt", "requirements.txt"),
        ("Cargo.toml", "Cargo"),
        ("go.mod", "Go Modules"),
        ("pom.xml", "Maven"),
        ("build.gradle", "Gradle"),
        ("build.gradle.kts", "Gradle"),
        ("CMakeLists.txt", "CMake"),
        ("Makefile", "Make"),
        ("*.sln", ".NET Solution"),
        ("*.csproj", ".NET Project"),
    ]
    for pattern, label in file_markers:
        matches = list(repo_root.glob(pattern))
        if matches and label not in build_systems:
            build_systems.append(label)
    return build_systems


def describe_directory(directory: Path) -> str | None:
    if (directory / "SKILL.md").exists():
        return "contains skill source files"

    languages = detect_languages(directory)
    if languages:
        return f"contains {', '.join(languages)} source files"

    child_files = [path for path in directory.iterdir() if path.is_file()]
    if child_files:
        return "contains project files"

    child_dirs = [path for path in directory.iterdir() if path.is_dir()]
    if child_dirs:
        return "contains submodules or grouped resources"

    return None


def detect_core_modules(repo_root: Path) -> list[str]:
    modules: list[str] = []
    for child in sorted(repo_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name in SKIP_DIR_NAMES or child.name.startswith("."):
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

    return install_step, build_step, run_step


def detect_project_type(repo_root: Path) -> str:
    return profile_detect_project_type(repo_root)


def detect_validation_commands(repo_root: Path, project_type: str, build_step: str) -> tuple[str, str, str]:
    return profile_detect_validation_commands(repo_root, project_type, build_step)


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
        f"- **WorkingDirectory**: `{repo_root}`",
    ]

    if project_type in {"WPF", "Win32"}:
        lines.append("- **RecommendedTerminal**: Windows PowerShell 7 或 cmd")
        if is_wsl_host():
            lines.append("- **CanRunBuildHere**: no")
            lines.append("- **Reason**: 当前宿主是 WSL，Windows 客户端编译链容易受路径、SDK、MSBuild 发现和子进程语义影响")
        elif sys.platform == "win32":
            lines.append("- **CanRunBuildHere**: yes")
        else:
            lines.append("- **CanRunBuildHere**: unknown")
            lines.append("- **Reason**: 当前宿主不是 Windows，需在 Windows PowerShell/cmd 中确认工具链")

        if project_type == "WPF":
            lines.append("- **Preflight**: `dotnet --info`; 若使用旧式 .NET Framework 项目，还需确认 Visual Studio Build Tools")
            if first_matching_file(repo_root, "global.json"):
                lines.append("- **Evidence**: `global.json` 会约束 .NET SDK 版本")
            if first_matching_file(repo_root, "NuGet.config", "packages.config"):
                lines.append("- **Preflight**: 先执行 NuGet restore 或确认私有源可访问")
        else:
            lines.append("- **Preflight**: `where msbuild`; 确认 Visual Studio Build Tools、Windows SDK、PlatformToolset、Configuration/Platform")
            if first_matching_file(repo_root, "*.vcxproj"):
                lines.append("- **Evidence**: 检测到 `.vcxproj`，需要 Windows 原生 MSBuild 工具链")
    elif project_type == "Harmony":
        lines.append("- **RecommendedTerminal**: 项目约定的本机 shell；Windows 下优先 PowerShell/cmd")
        lines.append("- **CanRunBuildHere**: unknown")
        lines.append("- **Preflight**: `ohpm --version`; `hvigorw --version`; 确认 DevEco / hvigor / ohpm 与签名配置")
    elif project_type == "Qt":
        lines.append("- **RecommendedTerminal**: 已加载 Qt/CMake 工具链环境的终端")
        lines.append("- **CanRunBuildHere**: unknown")
        lines.append("- **Preflight**: `cmake --version`; `ctest --version`; 确认 Qt Kit、生成器和 build preset")
    else:
        lines.append("- **RecommendedTerminal**: Unknown")
        lines.append("- **CanRunBuildHere**: unknown")

    if build_step == "Unknown":
        lines.append("- **MissingCommands**: build 命令缺失，不能启动编译")
    else:
        lines.append(f"- **BuildCommand**: `{build_step}`")
    lines.append("- **FailureEvidence**: 记录完整命令、工作目录、终端类型、退出码、前 50 行和最后 100 行构建日志")
    return "\n".join(lines)


def detect_high_risk_directories(repo_root: Path, project_type: str) -> list[str]:
    return profile_detect_high_risk_directories(repo_root, project_type)


def detect_restricted_areas(repo_root: Path) -> list[str]:
    restricted: list[str] = []
    for candidate, description in [
        ("bin", "generated build outputs"),
        ("obj", "generated intermediate outputs"),
        ("dist", "packaged artifacts"),
        ("build", "generated build directory"),
        ("node_modules", "third-party installed dependencies"),
        (".git", "version control metadata"),
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
        summary_parts.append("Qt Client")
        if has_shared_cpp_core:
            summary_parts.append("Shared C++ Core")
    elif project_type == "Harmony":
        summary_parts.append("Harmony")
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


def detect_architecture_pattern(repo_root: Path) -> str:
    if first_matching_file(repo_root, "*ViewModel.cs") or (repo_root / "ViewModel").exists():
        return "MVVM"
    return "Unknown"


def detect_core_entry(repo_root: Path) -> str:
    entry = first_matching_file(repo_root, "App.xaml.cs", "Program.cs", "main.cpp", "main.cc")
    return relative_display(entry, repo_root) if entry else "Unknown"


def detect_sdk_call_chain(repo_root: Path) -> str:
    project_type = detect_project_type(repo_root)
    has_shared_cpp_core, _ = detect_shared_cpp_core_info(repo_root)
    if project_type == "Qt" and has_shared_cpp_core:
        return "Qt UI -> Qt Controller/Service -> C++ wrapper -> Shared C++ Core"

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
    """Sample real file paths (+ one structural line) so agents align with existing style."""
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
    items.append("- 未确认线程模型、资源释放和 ABI 约束前，禁止直接改底层 native bridge")
    return "\n".join(items)


def detect_high_risk_files(repo_root: Path) -> str:
    candidates: list[tuple[str, str]] = []
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

    if not candidates:
        return "Unknown"

    return "\n".join(f"- `{path}`: {reason}" for path, reason in candidates)


def detect_feature_paths(repo_root: Path) -> str:
    suggestions: list[str] = []
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
        signals.append("Qt Client -> Shared C++ Core: 检测到 Qt UI 与共享 C++ 底层链路")
        for marker in shared_cpp_markers[:3]:
            signals.append(f"`{marker}`: Shared C++ Core 候选")

    for path in islice(iter_matching_files(repo_root, "*.vcxproj"), 3):
        signals.append(f"`{relative_display(path, repo_root)}`: 检测到原生工程或桥接工程")

    for path in islice(iter_matching_files(repo_root, "*.cs"), 30):
        content = path.read_text(encoding="utf-8", errors="ignore")
        relative_path = relative_display(path, repo_root)
        if "DllImport" in content:
            signals.append(f"`{relative_path}`: 检测到 DllImport / PInvoke")
        if "MarshalAs" in content or "System.Runtime.InteropServices.Marshal" in content:
            signals.append(f"`{relative_path}`: 检测到 MarshalAs / marshaling")
        if "delegate" in content and ("Callback" in content or "Observer" in content):
            signals.append(f"`{relative_path}`: 检测到 callback / observer 定义")

    for path in islice(iter_matching_files(repo_root, "*.cpp", "*.h", "*.hpp"), 30):
        content = path.read_text(encoding="utf-8", errors="ignore")
        relative_path = relative_display(path, repo_root)
        if any(token in content for token in ("windows.h", "HWND", "HANDLE", "CreateWindow", "SendMessage", "GetMessage")):
            signals.append(f"`{relative_path}`: 检测到 Win32 API 使用")

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
            items.append(f"`{header_markers[0]}`: C++ 导出头文件或 ABI 边界需人工确认")
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

    if build_step == "Unknown" or quick_step == "Unknown" or full_step == "Unknown":
        items.append("build / quick / full 命令映射不完整，需人工确认最终入口")

    high_risk_cpp = first_matching_file(repo_root, "*.cpp")
    if high_risk_cpp:
        items.append(f"`{relative_display(high_risk_cpp, repo_root)}` 是否允许 AI 直接修改，需人工确认")

    return items or ["Unknown"]


def detect_architecture_overview(core_modules: list[str]) -> str:
    if not core_modules:
        return "Unknown"
    module_names = ", ".join(item.split(":", 1)[0] for item in core_modules[:5])
    return f"Repository is organized around top-level modules: {module_names}."


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
    if not items:
        return "- Unknown"
    return "\n".join(f"- {item}" for item in items)


def render_readme(
    repo_root: Path,
    project_name: str,
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
        .replace("{项目简介或 Unknown}", "Unknown", 1)
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
        .replace("{SDK 调用链或 Unknown}", sdk_call_chain, 1)
        .replace("{版本识别点或 Unknown}", version_marker, 1)
        .replace("{命名与风格约束或 Unknown}", style_rules, 1)
        .replace("{架构边界规则或 Unknown}", architecture_rules, 1)
        .replace("{禁止操作清单或 Unknown}", forbidden_operations, 1)
        .replace("{高风险文件标注或 Unknown}", high_risk_files, 1)
        .replace("{新增功能标准路径或 Unknown}", feature_paths, 1)
        .replace("{代码安全规范或 Unknown}", code_safety_rules, 1)
        .replace("{多版本注意事项或 Unknown}", multi_version_notes, 1)
        .replace("{日志规范或 Unknown}", logging_rules, 1)
        .replace("{提问与探索建议或 Unknown}", exploration_suggestions, 1)
        .replace("{自动识别候选或 Unknown}", auto_detected_candidates, 1)
        .replace("{需人工确认或 Unknown}", manual_review_items, 1)
        .replace("{代码风格锚点或 Unknown}", style_anchors, 1)
    )


def render_architecture(
    repo_root: Path,
    dependency_graph: str,
    architecture_overview: str,
    module_interfaces: list[str],
    key_module_markers: list[str],
) -> str:
    template = read_template("ARCHITECTURE.template.md", repo_root)
    return (
        template.replace("{文本表示的依赖关系，例如 ModuleA -> ModuleB -> ModuleC 或 Unknown}", dependency_graph, 1)
        .replace("{主要功能调用链或 Unknown}", "Unknown", 1)
        .replace("{如 MVC、MVVM、微服务等，无法确定标记 Unknown}", "Unknown", 1)
        .replace("- {模块1 -> 模块2: 接口类型或 Unknown}\n- {模块2 -> 模块3: 接口类型或 Unknown}", format_bullets(module_interfaces), 1)
        .replace("- {模块1: 上游/下游/核心功能说明或 Unknown}\n- {模块2: 上游/下游/核心功能说明或 Unknown}", format_bullets(key_module_markers), 1)
    )


def render_harness(
    repo_root: Path,
    project_type: str,
    build_step: str,
    build_bootstrap: str,
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
        .replace("{编译启动诊断或 Unknown}", build_bootstrap, 1)
        .replace("{命令或 Unknown}", quick_step, 1)
        .replace("{命令或 Unknown}", bugfix_step, 1)
        .replace("{命令或 Unknown}", full_step, 1)
        .replace("- {目录1: 风险说明}\n- {目录2: 风险说明}\n- ...", format_bullets(high_risk_directories), 1)
        .replace("- {区域1: 原因}\n- {区域2: 原因}\n- ...", format_bullets(restricted_areas), 1)
        .replace("- {候选1: 说明}\n- {候选2: 说明}\n- ...", format_bullets(auto_detected_candidates), 1)
        .replace("- {确认项1: 原因}\n- {确认项2: 原因}\n- ...", format_bullets(manual_review_items), 1)
    )


def generate_context_files(repo_root: Path) -> dict[str, str]:
    project_name = detect_project_name(repo_root)
    contract_index = discover_contract_index(repo_root)
    languages = detect_languages(repo_root)
    build_systems = detect_build_systems(repo_root)
    core_modules = detect_core_modules(repo_root)
    project_type = detect_project_type(repo_root)
    install_step, build_step, run_step = detect_usage_steps(repo_root, project_type)
    quick_step, bugfix_step, full_step = detect_validation_commands(repo_root, project_type, build_step)
    build_bootstrap = detect_build_bootstrap(repo_root, project_type, build_step)
    architecture_overview = detect_architecture_overview(core_modules)
    dependency_graph = detect_module_dependency_graph(core_modules)
    module_interfaces = detect_module_interfaces(core_modules)
    key_module_markers = detect_key_module_markers(core_modules)
    high_risk_directories = detect_high_risk_directories(repo_root, project_type)
    restricted_areas = detect_restricted_areas(repo_root)
    language_framework_summary = detect_language_framework_summary(repo_root, project_type, languages)
    architecture_pattern = detect_architecture_pattern(repo_root)
    core_entry = detect_core_entry(repo_root)
    sdk_call_chain = detect_sdk_call_chain(repo_root)
    version_marker = detect_version_marker(repo_root)
    style_rules = detect_style_rules(repo_root)
    style_anchors = detect_style_anchors(repo_root)
    architecture_rules = detect_architecture_rules(repo_root)
    forbidden_operations = detect_forbidden_operations(repo_root)
    high_risk_files = detect_high_risk_files(repo_root)
    feature_paths = detect_feature_paths(repo_root)
    code_safety_rules = detect_code_safety_rules(repo_root)
    multi_version_notes = detect_multi_version_notes(repo_root)
    logging_rules = detect_logging_rules(repo_root)
    exploration_suggestions = detect_exploration_suggestions(repo_root)
    auto_detected_candidates_list = detect_nativebridge_signals(repo_root)
    manual_review_items_list = detect_manual_review_items(
        repo_root,
        build_step,
        quick_step,
        bugfix_step,
        full_step,
    )
    auto_detected_candidates = format_bullets(auto_detected_candidates_list)
    agents_manual_review_items = format_bullets(manual_review_items_list + list(contract_index.manual_review))

    return {
        "README.md": render_readme(
            repo_root,
            project_name,
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
            module_interfaces,
            key_module_markers,
        ),
        "HARNESS.md": render_harness(
            repo_root,
            project_type,
            build_step,
            build_bootstrap,
            quick_step,
            bugfix_step,
            full_step,
            high_risk_directories,
            restricted_areas,
            auto_detected_candidates_list,
            manual_review_items_list,
        ),
    }


def summarize_diff(file_name: str, existing: str, generated: str) -> tuple[str, str]:
    diff = list(
        difflib.unified_diff(
            existing.splitlines(),
            generated.splitlines(),
            fromfile=f"{file_name} (existing)",
            tofile=f"{file_name} (generated)",
            lineterm="",
        )
    )
    changed_line_count = sum(
        1 for line in diff if (line.startswith("+") or line.startswith("-")) and not line.startswith("+++") and not line.startswith("---")
    )
    summary = f"{file_name}: diff lines={changed_line_count}, existing_lines={len(existing.splitlines())}, generated_lines={len(generated.splitlines())}"
    return summary, "\n".join(diff)


def summarize_managed_diffs(file_name: str, existing: str, merged: str, changed_ids: list[str]) -> str:
    existing_blocks = parse_managed_blocks(existing)
    merged_blocks = parse_managed_blocks(merged)
    rendered: list[str] = []
    for block_id in changed_ids:
        existing_body = existing_blocks[block_id].body if block_id in existing_blocks else ""
        merged_body = merged_blocks[block_id].body
        rendered.extend(
            difflib.unified_diff(
                existing_body.splitlines(),
                merged_body.splitlines(),
                fromfile=f"{file_name}:{block_id} (existing)",
                tofile=f"{file_name}:{block_id} (generated)",
                lineterm="",
            )
        )
    return "\n".join(rendered)


def prompt_overwrite_action(file_name: str) -> str:
    prompt = f"Action for {file_name}? [y]es / [n]o / [all] / [none] / [quit]: "
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
        print("Invalid choice. Enter one of: y, n, all, none, quit.")


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
        print("Created files:")
        for file_name in created_files:
            print(f"- {file_name}")

    if unchanged_files:
        print("Unchanged files:")
        for file_name in unchanged_files:
            print(f"- {file_name}")

    if not differing_files:
        return 0

    print("Existing context files differ and were left unchanged:")
    for file_name in differing_files:
        print(f"- {file_name}")
    if force:
        print("--force cannot overwrite existing context files during scan.")
    print("Run `dev-harness-context refresh <repo-path>` to preview managed-block updates.")
    return 2


def refresh_context_files(repo_root: Path, generated_files: dict[str, str], force: bool = False) -> int:
    pending: list[tuple[str, Path, str, DocumentFormat, list[str], str]] = []
    missing: list[tuple[str, Path, bytes]] = []
    errors: list[tuple[str, str]] = []
    legacy_blocked: list[str] = []
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
            existing_blocks = parse_managed_blocks(existing)
        except ManagedDocumentError as exc:
            errors.append((file_name, str(exc)))
            continue

        if not existing_blocks:
            if force or not interactive:
                legacy_blocked.append(file_name)
                continue
            try:
                migration = migrate_legacy_document(existing, generated)
            except ManagedDocumentError as exc:
                errors.append((file_name, str(exc)))
                continue
            if not migration.safe_section_ids:
                legacy_blocked.append(file_name)
                continue
            merged = migration.merged_text
            changed_ids = list(migration.safe_section_ids)
            diff_text = "\n".join(
                difflib.unified_diff(
                    existing.splitlines(),
                    merged.splitlines(),
                    fromfile=f"{file_name}:legacy (existing)",
                    tofile=f"{file_name}:legacy (managed)",
                    lineterm="",
                )
            )
            pending.append((file_name, target_path, merged, document_format, changed_ids, diff_text))
            continue

        try:
            merged, changed_ids = merge_managed_blocks(existing, generated)
        except ManagedDocumentError as exc:
            errors.append((file_name, str(exc)))
            continue
        if not changed_ids:
            continue
        diff_text = summarize_managed_diffs(file_name, existing, merged, changed_ids)
        pending.append((file_name, target_path, merged, document_format, changed_ids, diff_text))

    if errors:
        for file_name, message in errors:
            print(f"Error: cannot refresh {file_name}: {message}")
        return 1

    if legacy_blocked:
        print("Legacy context files require interactive migration and were left unchanged:")
        for file_name in legacy_blocked:
            print(f"- {file_name}")
        if force:
            print("--force cannot bypass legacy migration confirmation.")
        return 2

    for file_name, target_path, content in missing:
        target_path.write_bytes(content)
        print(f"Created: {file_name}")

    if not pending:
        return 0

    print("Managed-block updates detected:")
    for file_name, _, _, _, changed_ids, _ in pending:
        print(f"- {file_name}: {', '.join(changed_ids)}")

    if not force and not interactive:
        for file_name, _, _, _, _, diff_text in pending:
            print(f"--- BEGIN MANAGED DIFF: {file_name} ---")
            print(diff_text)
            print(f"--- END MANAGED DIFF: {file_name} ---")
        print("Preview only; re-run with --force or use an interactive terminal to apply managed-block updates.")
        return 2

    updated: list[str] = []
    skipped: list[str] = []
    interactive_mode = "ask"
    for file_name, target_path, merged, document_format, _, diff_text in pending:
        print(f"--- BEGIN MANAGED DIFF: {file_name} ---")
        print(diff_text)
        print(f"--- END MANAGED DIFF: {file_name} ---")
        if force or interactive_mode == "all":
            action = "yes"
        elif interactive_mode == "none":
            action = "no"
        else:
            action = prompt_overwrite_action(file_name)
        if action == "quit":
            print(f"Quit requested. Left unchanged: {file_name}")
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
            print(f"Updated managed blocks: {file_name}")
        else:
            skipped.append(file_name)
            print(f"Skipped: {file_name}")

    return 2 if skipped else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate README.md, AGENTS.md, and ARCHITECTURE.md from a real repository scan.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="scan repository and generate context files")
    scan_parser.add_argument("repo_path", type=Path, help="target repository root path")
    scan_parser.add_argument("--force", action="store_true", help="accepted for compatibility; existing files are never overwritten")

    refresh_parser = subparsers.add_parser("refresh", help="refresh only dev-harness managed blocks")
    refresh_parser.add_argument("repo_path", type=Path, help="target repository root path")
    refresh_parser.add_argument("--force", action="store_true", help="apply managed-block updates without prompting")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = args.repo_path.resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        print(f"Error: repository path does not exist or is not a directory: {repo_root}")
        return 1

    generated_files = generate_context_files(repo_root)
    if args.command == "scan":
        return write_initial_context_files(repo_root, generated_files, force=args.force)
    if args.command == "refresh":
        return refresh_context_files(repo_root, generated_files, force=args.force)
    parser.error("unknown command")


def cli_main() -> int:
    return main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(cli_main())
