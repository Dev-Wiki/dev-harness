# V2_BACKLOG

[English](V2_BACKLOG.en.md) | [简体中文](V2_BACKLOG.md)

> Document role: this file is a pool of future candidates beyond the current V1 / VNext boundary, not a committed Roadmap.
> See [`CAPABILITIES.md`](CAPABILITIES.en.md) for currently supported capabilities, [`V1_V2_BOUNDARIES.md`](V1_V2_BOUNDARIES.en.md) for version boundaries and completion criteria, and the [VNext improvements and Codebase Audit design](dev-harness%20VNext%20%E4%BC%98%E5%8C%96%E4%B8%8E%20Codebase%20Audit%20%E8%AE%BE%E8%AE%A1%E6%96%B9%E6%A1%88.md) for the v1.8.0 design rationale.

## Purpose

This file records capabilities explicitly placed in the next-stage scheduling pool after `dev-harness` V1 is complete.

Principles:

- Record only work **outside the V1 boundary**.
- Record only work **worth doing but unsuitable for further expansion of V1**.
- Use **P0 / P1 / P2** as the default coarse priority levels.

## Relationship to the VNext design

The Project Contract, five-command semantics, explicit Retro, progressive references, and Codebase Audit V1 implemented from the VNext design are no longer backlog items. This file retains deeper capabilities built on top of them, such as stronger NativeBridge analysis, execution-environment isolation, UI/Observability Harnesses, and automated Agent Loops.

“Enhanced command mapping” adds automatic selection and preflight over the current Platform / Variant recording contract. “Runtime Harness” means isolation orchestration for task-execution environments. Neither is the Codebase Audit state runtime that has already shipped.

## P0

### 1. Deeper NativeBridge support

- Extract more detailed `Service -> Interface -> Bridge -> Native` call chains automatically.
- Show relationships among bridge functions, P/Invoke, callbacks, and observers.
- Distinguish `C++/CLI`, `P/Invoke`, and pure Win32 DLL wrapper bridge patterns.
- Classify `ABI / marshaling / thread / handle / callback` risks more precisely.
- Support writing human-confirmation results back to `AGENTS.md` / `HARNESS.md`.

### 2. High-risk file scoring

- Assign priority or risk levels in addition to listing high-risk candidates.
- Combine factors such as file size, reference count, entry-point status, and involvement in bridges or state machines.
- Distinguish areas where blind changes are forbidden from areas that may change after human confirmation.

### 3. Enhanced command mapping

- Add stronger automatic selection and execution adaptation over the current build / test / quick / bugfix / full and Platform / Variant recording contracts.
- Extract evidence from actual scripts, solution files, hvigor, cmake, and other real configuration.
- Provide verifiable preflight for complex device matrices and remote build environments without expanding into a generic CI/CD assistant.

## P1

### 4. Runtime Harness

- Independent run directories for each task
- Worktree-based isolated execution
- Start / stop / cleanup scripts
- Runtime probes and health checks

### 5. UI Harness

- Launch client applications.
- Capture screenshots.
- Perform minimum smoke verification.
- Perform basic automated UI checks.

### 6. Observability Harness

- Standardize local log entry points.
- Define log-file locations.
- Provide metric / Trace query entry points.
- Provide an observation layer that AI can read directly.

## P2

### 7. Agent Loop Automation

- Automatic review
- Automatic feedback-and-fix loops
- Self-repair for failed commands
- Documentation staleness detection and doc gardening

### 8. Project-type template expansion

- `templates/<stack>/`
- WPF-specific templates
- Qt-specific templates
- Harmony-specific templates

### 9. Stronger architecture analysis

- Improved module dependency graphs
- More accurate architecture-pattern recognition
- More precise identification of entry points, state machines, and callback-dispatch centers

## Not currently entering V2

The following should not be scheduled directly into V2 at present:

- Fully automatic changes to native SDK core implementations
- Fully automatic proof of ABI / marshaling correctness
- Low-level C++ / Win32 automatic repair without human confirmation
- A universal “super runtime” for every platform from the outset

## Conditions for starting V2

Start V2 formally only after:

1. V1 has been piloted in at least 2–3 real client projects.
2. Real problems have been collected rather than features being invented from assumptions.
3. Frequent pain points can be clearly distinguished from features that merely look sophisticated.
