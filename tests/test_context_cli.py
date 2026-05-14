import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from context.cli import main


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

    def test_force_overwrites_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "demo-repo"
            repo_root.mkdir()
            (repo_root / "package.json").write_text('{"name":"demo-repo"}', encoding="utf-8")
            readme_path = repo_root / "README.md"
            readme_path.write_text("# Existing\n", encoding="utf-8")

            exit_code = main(["scan", str(repo_root), "--force"])

            self.assertEqual(exit_code, 0)
            self.assertNotEqual(readme_path.read_text(encoding="utf-8"), "# Existing\n")

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
