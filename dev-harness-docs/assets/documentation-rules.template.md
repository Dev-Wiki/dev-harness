# Documentation maintenance

> Documentation root: `{docs-root}`

## Entry layers

| Layer | Owner | Responsibility |
|---|---|---|
| Repository entry | `README.md`, `AGENTS.md`, `ARCHITECTURE.md`, `HARNESS.md` | Short summaries and links |
| Documentation hub | `{docs-root}/README.md` | Reader routes and active indexes |
| Deep documentation | `{docs-root}/...` | Authoritative product and engineering detail |

## Placement rules

| Content | Destination |
|---|---|
| {Document type} | `{docs-root}/{directory}/` |

Create a destination only when the repository has content for it. Do not create empty category directories.

## SSOT map

| Fact or topic | Writable owner | Linking indexes | Archive condition |
|---|---|---|---|
| {Changing fact} | `{path}` | `{path}` | {Condition} |

Keep status and detailed decisions in the writable owner. Keep indexes concise and link to the owner instead of repeating details.

When applicable, assign these facts to separate owners:

- current observable capabilities → the existing current-scope SSOT or a Capability Catalog;
- future work and task status → `{docs-root}/plan/`;
- released changes → the project CHANGELOG;
- codebase audit claims and evidence → `{docs-root}/audit/`, with only a concise route from the documentation hub.

## Navigation rules

- Keep every active document reachable from `{docs-root}/README.md` or one route index.
- Read indexes before deep documents.
- Open large reference collections through their local README or interface index.
- Link an existing `{docs-root}/audit/Report.md` from the documentation hub; do not copy its findings into the index.
- Keep root repository documents lightweight.

## Archive rules

1. Link the archived document to the current authority.
2. Mark it archived or superseded before moving it.
3. Update incoming links and active indexes.
4. Preserve historical content unless deletion is explicitly approved.
