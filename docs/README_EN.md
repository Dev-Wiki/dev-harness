# dev-harness

A platform-agnostic project engineering contract layer for AI coding assistants. It standardizes context, documentation, planning, verification commands, and Git policy, and provides durable evidence workflows for known bugs and unknown codebase risks.

Its design goals are Consistency across agents, Evidence for important claims, and Continuity across long tasks and sessions. It is not a test framework, generic SDLC skill library, static analyzer, or auto-fix CLI.

Supports Cursor, Codex CLI, OpenCode, and Antigravity.

[中文 README →](../README.md)

[Documentation index →](README.md)

---

## Skills

| Skill | Description |
|-------|-------------|
| `dev-harness-context` | Scans a repo and generates `README.md`, `ARCHITECTURE.md`, `HARNESS.md`, `AGENTS.md` |
| `dev-harness-docs` | Organizes an existing `doc/` or `docs/` root, indexes, progressive navigation, SSOT, conditional Capability Catalogs, archives, and links, and syncs verified facts into existing docs |
| `dev-harness-planning` | Generates Dashboard and TaskDetails under the repository's existing documentation root |
| `dev-harness-commands` | Standardizes `build / test / quick / bugfix / full` command entry points |
| `dev-harness-git-workflow` | Validates branch naming, generates commit messages, blocks debug artifacts |
| `dev-harness-auto-fix` | Full pipeline: bug description / issue URL → root cause → fix → review → commit |
| `dev-harness-codebase-audit` | Dynamically partitions large repositories and persists evidence-backed findings without changing source; missing documentation-hub links become explicit Docs Refresh handoffs |
| `dev-harness-retro` | Explicit retrospective — classifies FACT / POLICY / LESSON and proposes contract promotions |

---

## Install

**macOS / Linux:**

```bash
./install.sh --ide cursor       # install to ~/.cursor
./install.sh --ide codex        # install to ~/.codex
./install.sh --ide opencode     # install to ~/.config/opencode
./install.sh --ide antigravity  # install to ~/.gemini/antigravity
```

**Windows:**

```powershell
.\install.bat --ide cursor
.\install.bat --ide codex
.\install.bat --ide opencode
.\install.bat --ide antigravity
```

**Custom target:**

```bash
./install.sh --target /path/to/target
```

**Export a portable bundle directory:**

```bash
./install.sh --export dist
# produces dist/bundle/
```

Maintainers create the versioned zip with `python release.py`.

**Install a single skill** (dependencies resolved automatically):

```bash
./install.sh --ide cursor --skill dev-harness-context
```

Without flags: interactive menu in TTY; defaults to `--ide cursor` in non-interactive environments.

---

## Usage

After installing, use skills directly in your AI assistant:

```
# Initialize a repo
scan this repo and generate context files

# Organize project documentation without creating a second doc root
audit and organize this repository's documentation structure and SSOT

# Inventory currently supported features, reusing an equivalent scope SSOT when present
inventory this repository's supported features and, when needed, create or refresh a Capability Catalog with product status, applicability, delivery baseline, and verification level

# Fix a bug
auto fix this bug: <description>
auto fix https://github.com/owner/repo/issues/123

# Audit unknown risks without modifying product source
initialize a codebase audit from the canonical project context; if the documentation hub does not link audit/Report.md, refresh that navigation before audit initialization

# Commit with standards
help me commit my changes

# Explicit retrospective
retro: summarize this session and propose promotion candidates
```

**`dev-harness-context` also ships a minimal CLI:**

```bash
dev-harness-context scan /path/to/repo
dev-harness-context evidence /path/to/repo
dev-harness-context scan /path/to/repo --analysis /tmp/context-analysis.json
dev-harness-context refresh /path/to/repo --analysis /tmp/context-analysis.json
```

Behavior:
- `evidence` emits a framework-agnostic repository inventory, analysis contract, and snapshot fingerprint
- AI-authored semantic analysis must cite repository-local evidence for every non-Unknown conclusion
- Commands without evidence, paths outside the repository, and stale fingerprints are rejected before writing
- `scan` creates only missing files; `refresh` updates fixed Markdown sections without injecting markers, while preserving user-owned sections and file format

---

## Generic AI Recognition and Enhancement Profiles

`dev-harness-context` uses AI to identify new languages and architectures from repository evidence, without requiring a new hard-coded detector. Built-in profiles remain as offline fallbacks and domain-risk enhancements:

| Stack | Notes |
|-------|-------|
| **WPF** | C# + optional C++/CLI native bridge |
| **Harmony** | HarmonyOS / ArkTS |
| **Win32** | C++ / MSBuild |
| **Qt** | Windows + Linux, with Shared C++ Core detection |
| **Go** | Service boundaries, concurrency, persistence, and CGO risk prompts |
| **Flutter** | State ownership, Platform Channels, and native boundaries |
| **Node.js / TypeScript** | Workspaces, package entry points, plugins, and lifecycle hooks |
| **FastAPI** | ASGI/router/service flow, auth/migration risks, and pytest/uvicorn evidence |

Other stacks use the same evidence → AI analysis → deterministic validation pipeline. Only insufficiently supported claims become `Unknown`; low-confidence claims are routed to manual review.

The generated `AGENTS.md` includes: call chain candidates, architecture boundary rules, forbidden operations list, high-risk file annotations, exploration suggestions, NativeBridge auto-detection candidates.

---

## Command Semantics

After onboarding with `dev-harness-commands`, five stable entry points are defined in `HARNESS.md`:

| Command | Meaning |
|---------|---------|
| `harness:build` | Full compilation / build |
| `harness:test` | Repository-backed automated test entry |
| `harness:quick` | Fast compile-only check |
| `harness:bugfix` | Bug-specific verification |
| `harness:full` | Full build + all tests |

`full` means full build / full dependency graph verification — not packaging. Packaging should be marked `package/release-only` or CI-only.

---

## Repo Layout

```
dev-harness/
├── auto-fix/SKILL.md
├── codebase-audit/
│   ├── SKILL.md
│   ├── runtime.py             # snapshot, drift, state, finding and output guards
│   ├── references/
│   └── templates/
├── commands/SKILL.md
├── context/
│   ├── SKILL.md
│   ├── cli.py                  # context CLI entry point
│   ├── platform_profiles.py    # project type detection
│   ├── repo_walk.py            # file walking utilities
│   └── templates/              # AGENTS / HARNESS / README / ARCHITECTURE templates
├── dev-harness-docs/
│   ├── SKILL.md
│   ├── references/             # information architecture and migration rules
│   └── assets/                 # documentation index, rules, and route templates
├── planning/
│   ├── SKILL.md
│   └── templates/              # Dashboard / TaskDetails planning templates
├── git-workflow/SKILL.md
├── retro/SKILL.md
├── docs/                       # guides and reference docs
├── tests/                      # unittest suite
├── install.py                  # cross-platform install / export script
├── install.sh
├── install.bat
├── release.py                  # build release zip
└── VERSION
```

---

## V1 / V2 Boundary

V1 / VNext is the current project-contract layer for existing projects. It covers canonical context, documentation and planning governance, conditional current-capability catalogs, five verification command semantics, Git policy discovery, evidence-driven bug fixing, and resumable codebase audit with an explicit documentation-discoverability handoff. The v1.8.0 design record introduced this VNext evolution, v1.9.0 extends it with capability inventory and audit discoverability, and v1.9.1 improves Chinese terminology and template localization without changing the V1 boundary; VNext is not another name for the V2 backlog.

V1 explicitly excludes: UI automation, screenshot-driven verification, log/metric/trace platforms, multi-worktree runtime, auto PR/review loop, native-layer auto-repair.

See the [current V1 / VNext and V2 boundary](V1_V2_BOUNDARIES.md), the [implemented VNext design record](dev-harness%20VNext%20%E4%BC%98%E5%8C%96%E4%B8%8E%20Codebase%20Audit%20%E8%AE%BE%E8%AE%A1%E6%96%B9%E6%A1%88.md), and the [V2 backlog](V2_BACKLOG.md). The boundary document owns current scope; the backlog owns future candidates.

---

## License

MIT
