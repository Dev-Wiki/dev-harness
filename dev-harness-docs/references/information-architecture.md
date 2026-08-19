# Documentation information architecture

Use this reference when defining navigation, assigning SSOT ownership, or reorganizing an existing documentation tree.

## Contents

1. Repository entry layers
2. Reader routes
3. Content placement
4. Capability Catalog
5. SSOT layers
6. Archive lifecycle
7. Migration protocol
8. Verified-fact update discipline
9. Optional content-authoring integration

## 1. Repository entry layers

Keep information at the shallowest layer that can route the reader correctly:

| Layer | Typical files | Responsibility |
|---|---|---|
| Repository entry | `README.md`, `AGENTS.md`, `ARCHITECTURE.md`, `HARNESS.md` | Project overview, agent rules, architecture summary, executable commands |
| Documentation hub | `<docs-root>/README.md` | Reader routes, active entry points, category index |
| Route index | `<docs-root>/nav/*.md` | Progressive reading order for one audience or task family |
| Deep documentation | Product, architecture, how-to, reference, integration, deployment, troubleshooting | Authoritative detail |
| Archive | Topic-specific archive directories | Historical material that is no longer actively maintained |

Keep deep prose out of repository entry files. Link downward instead.

## 2. Reader routes

Prefer routes based on real reader intent rather than directory mirroring. Common route families include:

| Intent | Possible route |
|---|---|
| Understand scope or validate a feature | Product |
| Implement or review code | Development and standards |
| Plan, deploy, operate, or troubleshoot | Delivery and operations |

Do not create these three routes automatically. Derive routes from the repository's actual audiences. A library may need `Users`, `API integrators`, and `Maintainers`; a small service may need no `nav/` directory at all.

For every route, state:

- when to read it;
- the minimal ordered entry set;
- which large collections require an intermediate index;
- which unrelated collections must not be loaded by default.

## 3. Content placement

Use purpose as the primary classifier:

| Reader question | Document type | Common destination |
|---|---|---|
| What problem or version does this belong to? | Product requirement or overview | `product/` |
| Why is the system designed this way? | Explanation or architecture rationale | `arch/` |
| How do I accomplish a concrete task? | How-to | `how-to/` |
| What are the exact fields, options, or interfaces? | Reference | `reference/` or `integration/<provider>/` |
| What must contributors consistently follow? | Standard | `standards/` |
| How is this deployed, restored, or delivered? | Operations guide | `deployment/` |
| How was a known failure diagnosed and resolved? | Troubleshooting record | `troubleshooting/` |
| What work is active and what blocks it? | Plan | `plan/` |
| What problems did the latest codebase audit confirm? | Codebase Audit report | `audit/Report.md` |

Use Diataxis as a content-quality lens, not as a mandatory top-level directory layout. Existing domain directories may contain clearly labeled how-to, reference, and explanation documents without being reorganized solely for theoretical purity.

Codebase Audit owns the report, findings, tasks, and evidence under `<docs-root>/audit/`. Documentation governance owns only the stable link from `<docs-root>/README.md` or one justified route index to `audit/Report.md`. Keep that entry concise; a root README shortcut is optional when it already links to the documentation hub.

## 4. Capability Catalog

A Capability Catalog is the authoritative document for what the product supports now. Establish one only when current-function facts are scattered, support varies by applicability or released version, or the repository cannot reliably answer what it supports now. Reuse an existing document that already serves the same current-function purpose, regardless of filename.

If no such document exists, use `<docs-root>/product/CAPABILITIES.md` when an established product directory already exists; otherwise use `<docs-root>/CAPABILITIES.md`. Do not create `product/` solely to match this convention.

Use one stable ID for each independently verifiable function item that a user or integrator can exercise and confirm. Apply these counting rules:

- functional areas, screens, routes, endpoints, modules, tasks, and tests are not independently countable product functions;
- record role, platform, provider, vehicle, firmware, release, or deployment differences as applicability instead of duplicating the same function item;
- keep support status, applicability, version placement, and verification method as separate facts;
- calculate summary totals from current function rows and state which version the total represents;
- preserve an ID when support status, applicability, version placement, verification method, or evidence changes;
- exclude `Pending confirmation / 待确认` rows from supported totals.

Support status answers whether the behavior is supported, partially supported, experimental, or deprecated. Version placement distinguishes released versions from the current development version. Verification method distinguishes code evidence, automated tests, runtime validation, and target-environment validation. Applicability records the roles, platforms, providers, vehicles, firmware, versions, or deployment modes for which the function is available. One field must not silently stand in for another.

Match the repository's primary language and local writing conventions. For zh-CN documents, use `产品功能清单`, `当前已支持功能`, `可独立验证的功能项`, `功能分类`, `功能说明`, `支持状态`, `适用范围`, `版本归属`, `验证方式`, `当前开发版本`, `权威维护文档`, and `已有同类功能说明文档`. Use `可观测性` only for engineering observability such as logs, metrics, and distributed traces, never as a label for product functions. English repositories may use natural English equivalents.

Do not infer support from implementation inventory alone. Menus and routes can remain for deprecated behavior; tests can cover rejected or disabled paths; plans and requirements can describe work that does not exist. Every current row needs evidence and a link to the authoritative document for its detailed rules.

The catalog is authoritative for current support only. Planning owns future work and task state, CHANGELOG owns released deltas, and architecture, reference, integration, validation, and usage documents own local detail.

## 5. SSOT layers

Use three layers for changing project facts:

| Layer | May contain | Must not contain |
|---|---|---|
| Index | Status, priority, one-line scope, links | Detailed implementation history or duplicated acceptance steps |
| Topic | Cross-task decisions, authoritative topic status, summarized outcomes | Unrelated project-wide rollups |
| Requirement / implementation / reference | Local detail, steps, exact interfaces, acceptance evidence | Cross-topic status aggregation |

For each fact that changes over time, record:

```text
Fact: <what changes>
Authoritative document: <single maintained document>
Readers: <indexes or documents that link to it>
Archive rule: <when the authoritative document stops being active>
```

When two documents appear authoritative, do not merge them silently. Identify their audiences, select one authority with evidence, and convert the other into a link or historical snapshot after confirmation.

## 6. Archive lifecycle

Archive only when active maintenance has ended:

1. Identify the current authority that supersedes or summarizes the document.
2. Add a clear archived or superseded banner with a relative link to that authority.
3. Move the document into the nearest domain archive when a move improves active navigation.
4. Update every incoming project-owned link.
5. Remove it from active indexes and list it only in a clearly historical section when still useful.
6. Preserve the body as historical evidence unless the user explicitly authorizes deletion.

Never use `archive/` as a dumping ground for documents whose ownership is merely unclear.

## 7. Migration protocol

For an existing tree, propose a table before applying moves:

| Current path | Proposed path | Classification | SSOT owner | Link updates | Risk |
|---|---|---|---|---|---|
| `<path>` | `<path>` | `<type>` | `<owner>` | `<count or files>` | `<low/medium/high>` |

Use these rules:

- Keep stable public paths when the organizational gain is small.
- Prefer adding an index over moving dozens of valid documents.
- Separate generated documentation from hand-maintained documentation.
- Preserve documentation-framework routing metadata and sidebar configuration.
- Treat case-only renames and non-ASCII path changes as portability-sensitive.
- Request confirmation for bulk moves, deletions, or redirects that cannot be preserved.

## 8. Verified-fact update discipline

After code or validation changes, only verified, reusable project facts may be written into existing documents.

Admission gate — every fact must satisfy all of:

- proven by current code, configuration, or a successful validation;
- something future developers will repeatedly need;
- a clear owning document and stable scope.

Excluded by default: task logs, commit summaries, one-off paths, failed attempts, and personal preferences.

Update flow:

1. Read the diff, design or review artifacts, and validation evidence.
2. Locate the existing SSOT owner; do not create a second authority to host a fact.
3. Produce a minimal add/correct/delete plan with per-fact evidence; no opportunistic rewrites.
4. Preserve human-authored sections, encoding, heading levels, line endings, style, and framework metadata.
5. Check links, commands, versions, examples, and duplicates; put unverified items into a `待确认` section instead of writing them as facts.
6. Report modified files, how each was verified, and the remaining documentation gaps.

Managed context sections (`README.md` / `AGENTS.md` / `ARCHITECTURE.md` / `HARNESS.md`) are refreshed by `dev-harness-context`; release and CHANGELOG facts belong to the project Git workflow. This discipline does not bypass those owners.

## 9. Optional content-authoring integration

After structure and ownership are settled, a content-writing workflow may fill identified gaps:

- Generate factual reference material from code and tests.
- Write explanations for design rationale and trade-offs.
- Write task-focused how-to guides with verification.
- Write tutorials only when newcomers need a guided learning path.

Keep this integration optional. The core `dev-harness-docs` workflow (structure, SSOT, and the verified-fact update discipline) must not require gstack or another external documentation package. If such a skill is available, use it only for heavier authoring or audit work:

- from-scratch Diataxis generation (tutorials, API references, explanations) → a content-authoring skill, passing the resolved `<docs-root>`, target document type, existing index, and SSOT owner;
- post-ship full-repository audit and coverage reporting → a release-oriented documentation skill.

Everyday verified-fact sync stays inside this skill's Update operation, so projects without external packages still get a safe default.
