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

    if build_step != "Unknown" and quick_step == "Unknown":
        quick_step = build_step

    return quick_step, bugfix_step, full_step


def detect_high_risk_directories(repo_root: Path, project_type: str) -> list[str]:
    risks: list[str] = []
    for candidate, description in [
        ("resources", "resource assets or localization files"),
        ("res", "resource assets or localization files"),
        ("native", "native layer or platform bridge"),
        ("packaging", "packaging or installer assets"),
        ("installer", "installer or deployment assets"),
        ("third_party", "third-party vendored code"),
    ]:
        path = repo_root / candidate
        if path.exists():
            risks.append(f"{candidate}: {description}")

    if project_type == "WPF":
        if (repo_root / "App.xaml").exists():
            risks.append("App.xaml: application bootstrap and UI resource merge points")
        if list(repo_root.glob("*.csproj")):
            risks.append("*.csproj: packaging, references, and build configuration")
    elif project_type == "Qt":
        if (repo_root / "CMakeLists.txt").exists():
            risks.append("CMakeLists.txt: build graph and Qt module linking")
        if list(repo_root.glob("*.ui")):
            risks.append("*.ui: generated UI layout definitions")
        if (repo_root / "shared_cpp").exists():
            risks.append("shared_cpp: shared native core used by Windows client UI layers")
        if first_matching_file(repo_root, "*.h", "*.hpp"):
            risks.append("*.h/*.hpp: exported C++ headers and ABI boundary")
    elif project_type == "Harmony":
        if (repo_root / "module.json5").exists():
            risks.append("module.json5: app packaging and module declaration")
        if (repo_root / "build-profile.json5").exists():
            risks.append("build-profile.json5: build targets and signing profile")
    elif project_type == "Win32":
        if repo_contains_vcxproj(repo_root):
            risks.append("*.vcxproj: Visual C++ build graph, toolchain, and linker settings")
        if repo_contains_pattern(repo_root, "*.rc"):
            risks.append("*.rc: Win32 resource script and packaging metadata")

    return risks or ["Unknown"]
