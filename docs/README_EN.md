# dev-harness

A platform-agnostic AI engineering skills bundle for structured bug fixing, code context initialization, and git workflow enforcement.

Not a test framework. Not a CLI that auto-fixes bugs. A set of process constraints that reduce the cost of reproduction, root cause analysis, regression, and verification — when working with AI-assisted development.

Supports Cursor, Codex CLI, OpenCode, and Antigravity.

[中文 README →](../README.md)

---

## Skills

| Skill | Description |
|-------|-------------|
| `dev-harness-pilot` | Entry point — routes to the right skill based on your goal |
| `dev-harness-context` | Scans a repo and generates `README.md`, `ARCHITECTURE.md`, `HARNESS.md`, `AGENTS.md` |
| `dev-harness-commands` | Standardizes `build / quick / bugfix / full` command entry points |
| `dev-harness-repro` | Converges reproduction steps and evidence |
| `dev-harness-triage` | Traces call chain, identifies root cause candidates |
| `dev-harness-regression` | Defines regression coverage and test anchors |
| `dev-harness-verify` | Defines layered verification commands and completion evidence |
| `dev-harness-git-workflow` | Validates branch naming, generates commit messages, blocks debug artifacts |
| `dev-harness-auto-fix` | Full pipeline: bug description / issue URL → root cause → fix → review → commit |
| `dev-harness-retro` | Post-task retrospective — extracts AI mistakes into `LESSONS.md` |

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

**Export a portable zip:**

```bash
./install.sh --export dist
# produces dist/dev-harness-vX.Y.Z.zip
```

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

# Fix a bug
auto fix this bug: <description>
auto fix https://github.com/owner/repo/issues/123

# Commit with standards
help me commit my changes

# Post-task retrospective
summarize what went wrong this session
```

**`dev-harness-context` also ships a minimal CLI:**

```bash
dev-harness-context scan /path/to/repo
dev-harness-context scan /path/to/repo --force
```

Behavior:
- Missing files are created automatically
- Existing files with differing content show a diff summary before overwriting
- `--force` overwrites without prompting

---

## Scanner Support

`dev-harness-context` detects project type and produces constraint-oriented `AGENTS.md`. Currently well-supported stacks:

| Stack | Notes |
|-------|-------|
| **WPF** | C# + optional C++/CLI native bridge |
| **Harmony** | HarmonyOS / ArkTS |
| **Win32** | C++ / MSBuild |
| **Qt** | Windows + Linux, with Shared C++ Core detection |

Other stacks: safe detection with `Unknown` fallback and manual confirmation prompts.

The generated `AGENTS.md` includes: call chain candidates, architecture boundary rules, forbidden operations list, high-risk file annotations, exploration suggestions, NativeBridge auto-detection candidates.

---

## Command Semantics

After onboarding with `dev-harness-commands`, four stable entry points are defined in `HARNESS.md`:

| Command | Meaning |
|---------|---------|
| `harness:build` | Full compilation / build |
| `harness:quick` | Fast compile-only check |
| `harness:bugfix` | Bug-specific verification |
| `harness:full` | Full build + all tests |

`full` means full build / full dependency graph verification — not packaging. Packaging should be marked `package/release-only` or CI-only.

---

## Repo Layout

```
dev-harness/
├── SKILL.md                    # pilot skill
├── auto-fix/SKILL.md
├── commands/SKILL.md
├── context/
│   ├── SKILL.md
│   ├── cli.py                  # context CLI entry point
│   ├── platform_profiles.py    # project type detection
│   └── repo_walk.py            # file walking utilities
├── git-workflow/SKILL.md
├── regression/SKILL.md
├── repro/SKILL.md
├── retro/SKILL.md
├── triage/SKILL.md
├── verify/SKILL.md
├── templates/context/          # AGENTS / HARNESS / README / ARCHITECTURE templates
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

V1 is the AI engineering onboarding layer for existing projects. Goals: context initialization, command semantics, bugfix baseline, NativeBridge risk surface.

V1 explicitly excludes: UI automation, screenshot-driven verification, log/metric/trace platforms, multi-worktree runtime, auto PR/review loop, native-layer auto-repair.

See `docs/V1_V2_BOUNDARIES.md` and `docs/V2_BACKLOG.md` for details.

---

## License

MIT
