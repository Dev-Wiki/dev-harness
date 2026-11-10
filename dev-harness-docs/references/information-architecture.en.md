# Documentation information architecture

[English](information-architecture.en.md) | [简体中文](information-architecture.md)

Use this reference when defining navigation, assigning authoritative fact ownership, or organizing an existing documentation tree.

## Contents

1. Repository entry layers
2. Reading routes
3. Content placement
4. Capability catalog
5. Layers of authoritative facts
6. Archive lifecycle
7. Migration workflow
8. Verified-fact update rules
9. Optional content-authoring collaboration

## 1. Repository entry layers

Place information at the shallowest layer that can guide readers correctly:

| Layer | Common files | Responsibility |
|---|---|---|
| Repository entry | `README.md`, `AGENTS.md`, `ARCHITECTURE.md`, `HARNESS.md` | Project overview, collaboration rules, architecture summary, and executable commands |
| Documentation hub | `<docs-root>/README.md` | Reading routes, currently valid entry points, and category index |
| Route index | `<docs-root>/nav/*.md` | Progressive reading order for a reader group or task |
| Detailed documents | Product, architecture, how-to, reference, integration, deployment, and troubleshooting documents | Authoritative detailed explanations |
| Archive | Each topic's archive directory | Historical material no longer actively maintained |

Repository entry files link downward instead of carrying extensive detail.

## 2. Reading routes

Reading routes reflect real reader goals rather than copying the directory structure. Common options include:

| Reader goal | Optional route |
|---|---|
| Understand product scope or verify capabilities | Product |
| Implement or review code | Development and standards |
| Plan, deploy, operate, or troubleshoot | Delivery and operations |

Do not create these three routes automatically. Select routes for actual readers. A repository may need users, API integrators, and maintainers; a small service may need no `nav/` directory.

Each reading route explains:

- When it should be read.
- The minimum ordered set of entry points.
- Which large document collections require intermediate indexes.
- Which unrelated documents should not be loaded by default.

## 3. Content placement

Classify documents by purpose:

| Reader question | Document type | Common location |
|---|---|---|
| What is the scope of this issue or version? | Product requirements or overview | `product/` |
| Why is the system designed this way? | Design explanation or architecture rationale | `arch/` |
| How do I complete a specific task? | How-to guide | `how-to/` |
| What are the exact fields, options, or interfaces? | Reference | `reference/` or `integration/<provider>/` |
| What must contributors follow consistently? | Project standards | `standards/` |
| How do I deploy, recover, or deliver? | Operations guide | `deployment/` |
| How was a known failure diagnosed and resolved? | Troubleshooting record | `troubleshooting/` |
| What work and blockers are current? | Planning | `plan/` |
| What did the latest codebase audit confirm? | Codebase audit report | `audit/Report.md` |

Diátaxis can help assess content quality, but it is not a mandatory top-level directory structure. Existing domain directories may contain clearly identified how-to, reference, and design material without being reorganized for appearance alone.

Codebase Audit owns reports, Findings, tasks, and evidence under `<docs-root>/audit/`. Documentation governance only owns a stable link to `audit/Report.md` from `<docs-root>/README.md` or one justified reading route. Keep the entry concise. A root `README.md` that already links to the hub needs no mandatory extra shortcut.

## 4. Capability catalog

The capability catalog is authoritative for what the product currently supports. Establish it only when current capability facts are scattered, support differs by conditions or released versions, or current support cannot be answered reliably. Reuse an existing document with the same purpose regardless of its filename.

If no equivalent exists, use `<docs-root>/product/CAPABILITIES.md` when a product-documentation directory already exists; otherwise use `<docs-root>/CAPABILITIES.md`. Do not create `product/` merely to fit the convention.

Assign a stable ID to each independently verifiable capability that a user or integrator can operate and confirm, with these counting rules:

- Functional areas, pages, routes, interfaces, modules, tasks, and tests do not themselves count as independently countable product capabilities.
- Differences in role, platform, provider, vehicle, firmware, released version, or deployment mode belong in applicability rather than duplicate capability records.
- Record support status, applicability, version placement, and verification method separately.
- Derive totals from current capability details and state which version the totals describe.
- Preserve the ID when support status, applicability, version placement, verification method, or evidence changes.
- Pending-confirmation items do not enter supported totals.

Support status distinguishes supported, partial, experimental, and deprecated behavior. Version placement distinguishes released versions from current development. Verification method distinguishes code evidence, automated tests, execution, and target-environment validation. Applicability describes roles, platforms, providers, vehicles, firmware, versions, or deployment modes. None of these fields replaces another.

Follow the repository's primary language and writing conventions. Chinese documents use natural terms such as `产品功能清单`, `当前已支持功能`, `可独立验证的功能项`, `功能分类`, `功能说明`, `支持状态`, `适用范围`, `版本归属`, `验证方式`, `当前开发版本`, `权威维护文档`, and `已有同类功能说明文档`. Reserve observability terminology for logs, metrics, and traces rather than product-capability names. English repositories use natural English.

Do not infer support solely from an implementation inventory. Menus and routes may preserve deprecated behavior, tests may cover rejection or disabled paths, and plans or requirements may describe unimplemented work. Every current capability needs evidence and a link to the authoritative detailed rules.

The catalog owns current support only. Planning owns future work and task state, CHANGELOG owns released changes, and architecture, reference, integration, verification, and usage documents own their details.

Organize reader-facing prose in the order ordinary users and PMs need: purpose, support, applicability, limitations, and entry points. Put IDs, code, tests, and technical constraints in expandable details within the same item; do not create another manually synchronized catalog.

Initial full inventory, incremental synchronization, and repeatable full reconciliation follow [capability maintenance](capability-maintenance.en.md). Full reconciliation checks implementation scope and existing records, preserves stable IDs, and gives every old ID an outcome. Unchecked scope must not be marked complete. The catalog keeps only the latest complete inventory summary; Git or existing verification records preserve prior results.

## 5. Layers of authoritative facts

Changing project facts have three layers:

| Layer | May contain | Must not contain |
|---|---|---|
| Index | State, priority, short scope, and links | Detailed implementation history or repeated acceptance steps |
| Topic | Cross-task decisions, authoritative topic state, and outcome summary | Unrelated project-wide summaries |
| Requirements, implementation, or reference | Local details, steps, exact interfaces, and acceptance evidence | Cross-topic status summaries |

For each changing fact, record:

```text
Fact: <information that changes>
Authoritative document: <the sole continuously maintained source>
Reference entry: <index or document linking to this fact>
Archive condition: <when the authority stops being current>
```

When two documents both appear authoritative, do not merge them silently. Identify their readers, select one authority based on evidence, and after confirmation turn the other into a link or historical snapshot.

## 6. Archive lifecycle

Archive only when active maintenance has ended:

1. Identify the current authority that supersedes or summarizes the document.
2. Add an explicit archived or superseded notice with a relative link to that authority.
3. Move the document into the nearest domain archive when the move improves current navigation.
4. Update all repository-owned incoming links.
5. Remove it from current indexes; if historically useful, retain it only under a clearly historical section.
6. Preserve the body as historical evidence unless deletion is explicitly authorized.

Do not use `archive/` as a catch-all for documents with unclear ownership.

## 7. Migration workflow

Before reorganizing an existing tree, present a move map:

| Current path | Destination | Document type | Authority | Links requiring updates | Risk |
|---|---|---|---|---|---|
| `<path>` | `<path>` | `<type>` | `<owner>` | `<count or files>` | `<low / medium / high>` |

Follow these rules:

- Preserve stable public paths when reorganization offers little benefit.
- Prefer indexes over moving dozens of valid documents.
- Separate generated from human-maintained documents.
- Preserve documentation-framework route metadata and sidebar configuration.
- Case-only renames and non-ASCII path changes may affect cross-platform compatibility.
- Ask for confirmation before broad moves, deletion, or changes that cannot retain redirects.

## 8. Verified-fact update rules

After code or verification changes, write only proven, reusable project facts into existing documents.

Every admitted fact must:

- Be established by current code, configuration, or successful verification.
- Be repeatedly useful to future developers.
- Have a clear authoritative document and stable scope.

Exclude task logs, commit summaries, one-off paths, failed attempts, and personal preferences by default.

Update workflow:

1. Read the diff, design or review artifacts, and verification evidence.
2. Find the existing authoritative document instead of creating another authority to house one fact.
3. Propose minimal additions, corrections, and deletions with evidence for each, without opportunistic full rewrites.
4. Preserve human-maintained sections, encoding, heading levels, line endings, writing style, and framework metadata.
5. Check links, commands, versions, examples, and duplication. Keep unverified material pending confirmation rather than presenting it as fact.
6. Report changed files, verification basis, and unresolved documentation gaps.

Managed sections of `README.md`, `AGENTS.md`, `ARCHITECTURE.md`, and `HARNESS.md` are refreshed by `dev-harness-context`. Release and CHANGELOG facts belong to the project's Git workflow. These rules do not bypass ownership boundaries.

## 9. Optional content-authoring collaboration

Once structure and ownership are established, add content as needed:

- Evidence-backed reference material generated from code and tests.
- Design rationale and tradeoffs.
- Task-oriented how-to guides with verification steps.
- Tutorials only when newcomers actually need a progressive learning path.

Content-authoring collaboration is optional. The core `dev-harness-docs` workflow for structure, authoritative sources, and verified-fact updates must not depend on gstack or other external documentation packages. When relevant skills are available, use them only for heavier authoring or audits:

- For new Diátaxis tutorials, API references, and design explanations, hand the resolved `<docs-root>`, document types, current index, and authoritative documents to the content-authoring skill.
- Delegate post-release repository-wide audits and coverage reports to a release-oriented documentation skill.

Routine verified-fact synchronization remains owned by this skill's Update operation, so projects without external packages retain safe defaults.
