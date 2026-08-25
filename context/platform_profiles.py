from __future__ import annotations

from pathlib import Path

from context.repo_walk import (
    first_matching_file,
    repo_contains_pattern,
    repo_contains_vcxproj,
    sample_matching_files,
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _repo_has_file(repo_root: Path, *names: str) -> bool:
    return any((repo_root / name).exists() for name in names)


def _file_contains_any(path: Path, needles: list[str]) -> bool:
    content = _read_text(path)
    return any(needle in content for needle in needles)


def _relative_display(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def has_harmony_packaging_scripts(repo_root: Path) -> bool:
    return (repo_root / "buildScript" / "app_build.sh").exists() and any((repo_root / "buildScript").glob("*_package.py"))


def get_harmony_build_command(repo_root: Path) -> str:
    if has_harmony_packaging_scripts(repo_root):
        return "cd entry && ohpm install && cd .. && hvigorw clean --no-daemon && hvigorw assembleHap --mode module -p product=default -p buildMode=release --no-daemon"
    return "hvigorw assembleHap --mode module -p product=default -p buildMode=release --no-daemon"


def get_harmony_quick_command(repo_root: Path) -> str:
    return get_harmony_build_command(repo_root)


def get_harmony_full_command(repo_root: Path) -> str:
    return "hvigorw assembleApp --mode project -p product=default -p buildMode=release --no-daemon"


def get_wpf_build_command(repo_root: Path) -> str:
    project_file = first_matching_file(repo_root, "*.csproj")
    if project_file:
        return f"dotnet build {_relative_display(project_file, repo_root)}"
    return "dotnet build"


def get_wpf_full_command(repo_root: Path) -> str:
    solution_file = first_matching_file(repo_root, "*.sln")
    if solution_file:
        return f"dotnet build {_relative_display(solution_file, repo_root)}"
    return get_wpf_build_command(repo_root)


def get_win32_build_command(repo_root: Path) -> str:
    project_file = first_matching_file(repo_root, "*.vcxproj")
    if project_file:
        return f"msbuild {_relative_display(project_file, repo_root)} /p:Configuration=Debug"
    return "Unknown"


def get_win32_full_command(repo_root: Path) -> str:
    solution_file = first_matching_file(repo_root, "*.sln")
    if solution_file:
        return f"msbuild {_relative_display(solution_file, repo_root)} /m /p:Configuration=Debug"
    return get_win32_build_command(repo_root)


def get_qt_build_command(repo_root: Path) -> str:
    if (repo_root / "CMakePresets.json").exists():
        return "cmake --build --preset default"
    if (repo_root / "CMakeLists.txt").exists():
        return "cmake -S . -B build && cmake --build build"
    pro_files = list(repo_root.glob("*.pro")) + list(repo_root.glob("*/*.pro"))
    if pro_files:
        pro_dir = pro_files[0].parent
        pro_name = pro_files[0].stem
        rel = pro_dir.relative_to(repo_root).as_posix()
        return f"cd {rel} && qmake {pro_name}.pro && make -j$(nproc)"
    return "Unknown"


def get_qt_quick_command(repo_root: Path) -> str:
    if (repo_root / "CMakePresets.json").exists():
        return "ctest --preset default --output-on-failure"
    if (repo_root / "CMakeLists.txt").exists():
        return "ctest --test-dir build --output-on-failure"
    return "Unknown"


def find_fastapi_entry(repo_root: Path) -> Path | None:
    """返回负责创建 FastAPI 应用的 ASGI 模块。"""
    candidates = sample_matching_files(repo_root, 200, "*.py")
    candidates.sort(
        key=lambda path: (
            path.parent != repo_root,
            "tests" in path.relative_to(repo_root).parts,
            path.name not in {"main.py", "app.py"},
            len(path.relative_to(repo_root).parts),
            path.relative_to(repo_root).as_posix(),
        )
    )
    for path in candidates:
        if _file_contains_any(path, ["FastAPI("]) and _file_contains_any(
            path,
            ["from fastapi import", "import fastapi"],
        ):
            return path
    return None


def _has_fastapi_dependency(repo_root: Path) -> bool:
    dependency_files = [
        *repo_root.glob("requirements*.txt"),
        *repo_root.glob("pyproject.toml"),
        *repo_root.glob("Pipfile"),
    ]
    return any("fastapi" in _read_text(path).lower() for path in dependency_files)


def detect_project_type(repo_root: Path) -> str:
    if any(repo_root.glob("*.csproj")):
        app_xaml = repo_root / "App.xaml"
        if app_xaml.exists():
            return "WPF"
        for project_file in repo_root.glob("*.csproj"):
            content = _read_text(project_file)
            if "UseWPF" in content or "WindowsDesktop" in content:
                return "WPF"

    if _repo_has_file(repo_root, "hvigorfile.ts", "hvigorfile.js", "build-profile.json5"):
        return "Harmony"
    if _repo_has_file(repo_root, "oh-package.json5", "module.json5"):
        return "Harmony"

    cmake_file = repo_root / "CMakeLists.txt"
    if cmake_file.exists():
        content = _read_text(cmake_file)
        if "find_package(Qt" in content or "Qt6" in content or "Qt5" in content:
            return "Qt"
    if list(repo_root.glob("*.pro")) or list(repo_root.glob("*.pri")) or list(repo_root.glob("*.ui")):
        return "Qt"

    if repo_contains_vcxproj(repo_root):
        native_sources = sample_matching_files(
            repo_root,
            30,
            "*.cpp",
            "*.cc",
            "*.cxx",
            "*.c",
            "*.h",
            "*.hpp",
        )
        if any(
            _file_contains_any(path, ["WinMain", "WNDCLASSEX", "CreateWindow", "DefWindowProc", "RegisterClass"])
            for path in native_sources
        ):
            return "Win32"
        if any(
            _file_contains_any(path, ["windows.h", "HWND", "HANDLE", "WM_", "SendMessage", "GetMessage"])
            for path in native_sources
        ):
            return "Win32"

    if _has_fastapi_dependency(repo_root) or find_fastapi_entry(repo_root):
        return "FastAPI"

    return "Unknown"


def detect_validation_commands(repo_root: Path, project_type: str, build_step: str) -> tuple[str, str, str]:
    quick_step = "Unknown"
    bugfix_step = "Unknown"
    full_step = "Unknown"

    if project_type == "WPF":
        if list(repo_root.glob("*.sln")) or list(repo_root.glob("*.csproj")):
            quick_step = get_wpf_build_command(repo_root)
            full_step = get_wpf_full_command(repo_root)
    elif project_type == "Qt":
        if (repo_root / "CMakeLists.txt").exists():
            quick_step = get_qt_quick_command(repo_root)
            bugfix_step = quick_step
            full_step = get_qt_quick_command(repo_root)
        elif list(repo_root.glob("*.pro")) or list(repo_root.glob("*/*.pro")):
            quick_step = get_qt_build_command(repo_root)
            bugfix_step = quick_step
            full_step = quick_step
    elif project_type == "Harmony":
        if _repo_has_file(repo_root, "hvigorfile.ts", "hvigorfile.js"):
            quick_step = get_harmony_quick_command(repo_root)
            bugfix_step = quick_step
            full_step = get_harmony_full_command(repo_root)
    elif project_type == "Win32":
        quick_step = get_win32_build_command(repo_root)
        full_step = get_win32_full_command(repo_root)
    elif project_type == "FastAPI" and (repo_root / "tests").is_dir():
        quick_step = "python -m pytest -q"
        bugfix_step = quick_step
        full_step = quick_step

    if (
        build_step != "Unknown"
        and not build_step.startswith("N/A")
        and quick_step == "Unknown"
    ):
        quick_step = build_step

    return quick_step, bugfix_step, full_step


def detect_high_risk_directories(repo_root: Path, project_type: str) -> list[str]:
    risks: list[str] = []
    for candidate, description in [
        ("resources", "资源文件或本地化文件"),
        ("res", "资源文件或本地化文件"),
        ("native", "原生层或平台桥接层"),
        ("packaging", "打包或安装程序资源"),
        ("installer", "安装或部署资源"),
        ("third_party", "仓库内维护的第三方代码"),
    ]:
        path = repo_root / candidate
        if path.exists():
            risks.append(f"{candidate}: {description}")

    if project_type == "WPF":
        if (repo_root / "App.xaml").exists():
            risks.append("App.xaml：应用启动与 UI 资源合并入口")
        if list(repo_root.glob("*.csproj")):
            risks.append("*.csproj：打包、引用与构建配置")
    elif project_type == "Qt":
        if (repo_root / "CMakeLists.txt").exists():
            risks.append("CMakeLists.txt：构建图与 Qt 模块链接配置")
        if list(repo_root.glob("*.ui")):
            risks.append("*.ui：UI 布局定义")
        if (repo_root / "shared_cpp").exists():
            risks.append("shared_cpp：供 Windows 客户端 UI 层复用的共享原生核心")
        if first_matching_file(repo_root, "*.h", "*.hpp"):
            risks.append("*.h/*.hpp：导出的 C++ 头文件与 ABI 边界")
    elif project_type == "Harmony":
        if (repo_root / "module.json5").exists():
            risks.append("module.json5：应用打包与模块声明")
        if (repo_root / "build-profile.json5").exists():
            risks.append("build-profile.json5：构建目标与签名配置")
    elif project_type == "Win32":
        if repo_contains_vcxproj(repo_root):
            risks.append("*.vcxproj：Visual C++ 构建图、工具链与链接器设置")
        if repo_contains_pattern(repo_root, "*.rc"):
            risks.append("*.rc：Win32 资源脚本与打包元数据")
    elif project_type == "FastAPI":
        for candidate, description in [
            ("app/routers", "HTTP 路由定义与对外 API 边界"),
            ("app/core", "应用配置、安全与共享基础设施"),
            ("app/services", "业务逻辑与外部集成边界"),
            ("migrations", "数据库结构迁移"),
        ]:
            if (repo_root / candidate).exists():
                risks.append(f"{candidate}: {description}")
        entry = find_fastapi_entry(repo_root)
        if entry:
            risks.append(f"{_relative_display(entry, repo_root)}：ASGI 应用启动与中间件装配入口")

    return risks or ["Unknown"]
