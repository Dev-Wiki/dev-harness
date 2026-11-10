# Platform command mapping guide

[English](platform-command-mapping.en.md) | [简体中文](platform-command-mapping.md)

Read this guide only after repository evidence identifies the relevant platform. These are mapping heuristics, not evidence that a command exists or can run.

## Desktop and native projects

- WPF: normally map `build` / `quick` to project-level `dotnet build`, use an existing `dotnet test` or `vstest` entry for `test`, and use a solution-level build for `full`.
- Win32: normally map `build` / `quick` to project-level MSBuild, use existing `ctest` or `vstest` for `test`, and solution-level MSBuild for `full`. Packaging, signing, and installers belong to `package/release-only`, not local verification entry points.
- Qt: prefer the repository's existing CMake presets or build entry points. Use `ctest` only if the test graph actually exists. Preserve the project's Qt Kit and generator.

## Mobile and device-dependent scenarios

- Harmony: map local Hvigor module- or project-level commands by product and buildMode. Mark device tests `device-required`; packaging scripts cannot occupy local `full`.
- Android/iOS: explicitly record device or emulator, host OS, signing, and build-variant requirements. Device-dependent workflows must not be labeled automatically executable.
- Flutter: evidence may establish automatic Dart unit and widget tests. `integration_test` and native-bridge verification should normally be `device-required`.

## Services and toolchains

- Go: use the repository's existing `go build` / `go test` entry points and preserve package scope.
- Node.js / TypeScript: use actual package-manager scripts and workspace scopes. Lifecycle and installation scripts are prerequisites, not verification evidence.
- Python services: use existing pytest, tox, or nox entry points. Dependency installation is not a build command. Projects without a separate build step may use `N/A`.

## Platform / build-variant records

When one semantic command has several implementations, record them separately instead of joining incompatible commands:

```text
Purpose: build
Command: <repository-backed command>
WorkingDirectory: <repo-relative path>
Platform: PC | Phone | Windows | Linux | ...
Variant: Debug | Release | product name | ...
Preconditions: <toolchain or dependency>
DeviceRequirement: none | device-required | manual-only
Shell / Environment: <only when required>
Evidence: <path or successful run>
Status: candidate | confirmed | missing
```

Simple repositories can retain older single-value fields `BuildCommand` / `TestCommand` / `QuickCommand` / `BugfixCommand` / `FullCommand`. These field names and enums are internal contracts and stay untranslated; Chinese reader-facing explanations use natural Chinese.
