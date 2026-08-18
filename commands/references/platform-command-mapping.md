# Platform command mapping guidance

Use this reference only after repository evidence identifies a relevant platform. These are mapping heuristics, never command evidence.

## Desktop and native

- WPF: prefer a project `dotnet build` for build/quick, an existing `dotnet test` or `vstest` entry for test, and a solution build for full.
- Win32: prefer project MSBuild for build/quick, existing `ctest` or `vstest` for test, and solution MSBuild for full. Packaging, signing, and installers stay `package/release-only`.
- Qt: prefer the repository's CMake preset/build entry, with `ctest` only when the test graph is present. Preserve the configured Qt Kit and generator.

## Mobile and device-dependent

- Harmony: map local Hvigor module/project commands by product and buildMode. Device tests are `device-required`; packaging scripts do not occupy local full.
- Android/iOS: record device/simulator, host OS, signing, and variant requirements explicitly. Do not mark a device flow as automatically runnable.
- Flutter: Dart unit/widget tests may be automatic; `integration_test` and native bridge validation may be `device-required`.

## Services and toolchains

- Go: use repository-backed `go build` / `go test` entries and preserve package scope.
- Node.js / TypeScript: use actual package-manager scripts and workspace scope; lifecycle and install scripts are preconditions, not validation evidence.
- Python services: use the repository's pytest/tox/nox entry. A dependency install command is not a build command; projects without a build may use `N/A`.

## Platform / Variant records

When one semantic command has multiple realizations, write separate records rather than joining incompatible commands:

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

Simple repositories may keep the legacy single `BuildCommand` / `TestCommand` / `QuickCommand` / `BugfixCommand` / `FullCommand` fields.
