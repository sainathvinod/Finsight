# ADR-V2-007 — Ledger-Only Consumers and Append-Only Derived Records

- **Status:** Proposed
- **Date:** 2026-07-27
- **Deciders:** Project Owner; Software Architect; Data Architect; Finance Control Owner
- **Generalizes:** Root ADR-015 export/report identity
- **Narrowly amends:** Root ADR-011 §7 supersession freeze, solely for FR-171/FR-172 historical lifecycle and Derived Records
- **Related contracts:** AC-04, AC-05, and AC-06

## Context

Dashboards, analytics, reports, exports, findings, and Ask Fin can undermine trust if each recomputes financial logic or silently uses a different working, published, or historical generation.

## Decision

Every validation conclusion outside the deterministic engine is a read-only projection of one complete persisted Validation Run, Rule Execution, and Rule Result ledger.

Consumer modules:

- receive ledger query/read-model ports only;
- cannot import evaluator or Finding-creation modules;
- cannot synthesize PASS, FAIL, NOT_EVALUATED, risk, severity, RAG, or reconciliation status;
- display `Unavailable` when required ledger support is absent;
- bind exactly one Review Version/Generation and Validation Run; and
- default to the published generation.

The §2.7 Review Summary mapping is implemented once as a versioned domain/application projection and shared by UI, PDF, XLSX, and Ask Fin grounding. Presentation-only descriptive aggregates are labeled `Descriptive` and cannot affect Overall Review Status.

The first post-validation destination is the Review Summary. A successor run may be shown only with `Working — Unpublished` and the still-published identity alongside it. Historical output is labeled `Historical`. Generations are never mixed.

The inherited analytical sequence remains authoritative and is represented by append-only generation events:

- fresh confirmation creates native `VERIFIED` with trigger `HUMAN_CONFIRMATION`; reanalysis creates native `VERIFIED` with trigger `INHERITED_VERIFICATION_BASIS`, basis reference, and the original verifier/time;
- the atomic complete-ledger transaction appends `ANALYZED` and then `SUMMARIZED`, because that same transaction persists the engine-produced Review Summary projection;
- the first successfully completed PDF report or XLSX export appends `EXPORTED` in its Derived Record completion transaction whether the generation is working, published, historical, or superseded.

To reconcile FR-171/FR-172 with ADR-011 §7, V2 narrows the supersession freeze. Supersession leaves the financial, verification, run/result, publication/supersession facts and every prior Review Status/Derived Record fact immutable, but it does not block otherwise legal append-only lifecycle events or a Closed/Archived/historical generation's first retained report/export. That first artifact may append the sole `SUMMARIZED` → `EXPORTED` event without reopening, republishing, promoting, reviewing, closing, archiving, or unsuperseding the generation.

Derived Record request creation serializes with promotion and pins the exact creation-time publication/supersession label. Promotion first yields an authorized `Historical — Superseded` artifact; request creation first preserves its earlier label even if promotion follows. Concurrent first completions serialize so both artifacts may complete but exactly one state event is appended. Viewing the on-screen summary, failed/blocked artifact generation, Ask Fin output, and external delivery do not advance analytical state. Publication is orthogonal: a working/unpublished or historical/superseded generation can be `EXPORTED` without becoming published.

A migrated `LEGACY_SNAPSHOT` event may begin only at the state actually recorded by the legacy row, with null prior and unknown historical transition actor/time; it does not fabricate the native path. The per-generation compatibility mirror follows events, while the cycle compatibility mirror follows only the working generation.

PDF reports, spreadsheet-compatible exports, and retained Ask Fin responses are append-only Derived Records. Every request first creates a Generation Event and terminates as `Completed`, `Failed`, or `Blocked`. A completed record pins:

- Review/Generation, Validation Run, Rule Set Version, and creation-time publication state;
- department, period, source filenames, actor, and timestamps;
- renderer/context/policy version;
- content fingerprint; and
- predecessor/regeneration link when applicable.

Regeneration always creates a new record and never overwrites authoritative history. If the generation is already `EXPORTED`, regeneration adds no duplicate analytical-state event.

The first release uses:

- printable/PDF Review Summary and evidence detail; and
- macro-free XLSX exports with `Review Summary`, `Findings`, `Rule Results`, and `Financial Summary` worksheets.

Ask Fin additionally follows ADR-V2-005.

## Consequences

Every screenshot, export, report, chart, and explanation identifies the exact review being discussed. The design intentionally duplicates some persisted summary projections to make historical display possible without source reconstruction, but it does not duplicate evaluation logic.

## Verification

- Architecture fitness tests forbid evaluator imports in consumer packages.
- Projection tests reconcile every displayed value to source ledger IDs.
- Working/published/historical isolation tests.
- Report/XLSX identity, fingerprint, accessibility, and macro-absence tests.
- Native fresh/inherited and legacy-snapshot tests; exact `VERIFIED` → `ANALYZED` → `SUMMARIZED` → `EXPORTED` tests; a Closed superseded `SUMMARIZED` generation's first historical report/export; request-label/promotion and concurrent-first-export races; failed/blocked generation for non-supersession causes; Ask Fin no-transition; and regeneration-as-new-record/no-duplicate-state cases.
- Missing-ledger tests render unavailable rather than recalculating.

## Approval effect

Approval binds every downstream product surface to the engine ledger. It does not authorize renderer or UI implementation before the full Architecture gate.
