# {Project Name} Capability Catalog

> Responsibility: this document is the writable owner for the product's current observable capabilities. It does not own future plans, release history, architecture detail, or task status.

## Summary

Recompute these counts from the leaf rows whenever the catalog changes. Keep current-repository support separate from the latest released baseline.

| Baseline | Supported | Partial | Experimental | Deprecated |
|---|---:|---:|---:|---:|
| Current repository | {count} | {count} | {count} | {count} |
| Latest released baseline or N/A | {count} | {count} | {count} | {count} |

## Current capabilities

| ID | Capability domain | Observable capability | Product status | Availability scope | Delivery baseline | Verification level | Evidence | Details |
|---|---|---|---|---|---|---|---|---|
| {stable-id} | {domain} | {user- or integrator-observable behavior} | {Supported / Partial / Experimental / Deprecated} | {roles, platforms, providers, versions, deployment modes, or all} | {released version / current repository / not released / N/A} | {Code evidence / Automated test / Runtime validation / Target-environment validation} | {repository path, test, or validation link} | {authoritative detail link} |

## Pending confirmation / 待确认

Items in this section are not current facts and are excluded from supported totals.

| ID | Capability domain | Candidate capability | Availability scope | Missing evidence | Candidate sources |
|---|---|---|---|---|---|
| {candidate-id} | {domain} | {claim requiring confirmation} | {known scope or Unknown} | {probe, test, runtime, release, or target-environment evidence required} | {non-authoritative source links} |

## Maintenance rules

- Count one stable leaf capability ID once; domains, pages, routes, APIs, modules, tasks, and tests are not capabilities by themselves.
- Record platform, role, provider, firmware, vehicle, or deployment differences in `Availability scope` instead of duplicating the same capability.
- Keep `Product status`, `Delivery baseline`, and `Verification level` independent.
- Preserve IDs when status, scope, delivery, or evidence changes; do not renumber unchanged capabilities.
- Link to detailed requirements, architecture, integration, validation, or usage documents instead of copying their content.
- Keep future work in planning documents and released deltas in CHANGELOG.
