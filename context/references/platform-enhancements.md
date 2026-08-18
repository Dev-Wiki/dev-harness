# Context platform enhancement guidance

Profiles enhance evidence collection and risk prompts; they never decide whether an unfamiliar stack can be understood.

Read only the relevant section after generic repository evidence has identified a likely platform.

- Qt / WPF / Win32 with shared native code: trace UI or controller → wrapper/interop → shared C++ core; surface ABI, ownership, handles, callbacks, message loops, conditional compilation, and thread boundaries for manual review.
- Harmony: identify ArkUI/ArkTS entry points, product/target variants, NAPI/native bridges, lifecycle, packaging, signing, and device requirements.
- Go: identify `cmd` entry points, `internal`/`pkg` dependencies, persistence, concurrency, CGO, and package-cycle risks.
- Flutter: identify state ownership, Platform Channels, native platform implementations, lifecycle, and device-only verification.
- Node.js / TypeScript: identify workspace dependencies, package entry points, plugin manifests, lifecycle hooks, and supply-chain scripts.
- FastAPI: identify ASGI entry, router registration, service/core flow, dependency injection, auth, migrations, external integrations, and pytest/uvicorn evidence. Use `N/A` when no independent build exists.

For any other stack, follow the same Evidence Collector → AI Semantic Analyzer → Deterministic Validator / Writer path. Mark only the unsupported claim `Unknown`; do not stop because a profile is absent.
