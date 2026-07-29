# MVP Final Remediation — Consolidated Implementation Plan

- **Date:** 2026-07-28
- **Status:** In progress; verification evidence pending
- **Scope:** One consolidated remediation increment
- **Approval gate:** Existing Workflow Phase Implementation gate
- **Explicit exclusion:** Windows packaging and release

## Objective

Remediate the existing FinSight MVP without rebuilding it:

`Welcome → Create → Upload → Verify Data → Review Rules → Validate → Review Results → Complete → Reopen`

The increment reuses the existing extraction, reviewed-copy reconstruction, deterministic engine, persistence, audit, identity, and desktop shell boundaries.

## Batched work packages

| Package | Implementation outcome | Primary trace |
|---|---|---|
| Shell and visual system | Centered Welcome hierarchy; warm cream/navy design; consistent cards/tables; Light/Dark/System preference and live refresh | REM-FR-001, REM-FR-018/019 |
| Business-facing failures and metadata | Plain-language primary messages; optional technical disclosure; simplified upload cards; resolved Budget department display | REM-FR-002–004 |
| Verify Data working copy | Budget/GED tabs; search/filter/sort; explicit edit/save/cancel/revert; value provenance; source evidence; governed save and readiness attestations | REM-FR-005/006 |
| Rules Repository | Seven-step progress; protected rule inspection; optional rule add/edit/test/version/enable/disable/retire/delete lifecycle; immutable Rule Set Version; revalidation comparison | REM-FR-007–010 |
| Deterministic analytics | Chart-ready sealed projections and accessible chart/table consumers for overview, Budget, GED, and Budget/GED comparison | REM-FR-011/012 |
| Rule Results and evidence | Rule-oriented execution view, exception-oriented Findings, Data Quality & Coverage, exact source evidence, row/cell highlighting and navigation | REM-FR-013–016 |
| Review disposal | Three UI entry points; strong confirmation; authorized one-time token; atomic scoped disposal; opaque receipt; unrelated-review and external-file preservation | REM-FR-017 |
| Bounded Ask Fin | Keep shell entry visible; explain product, recorded findings, rules, and charts only | REM-FR-020 |
| Accessibility and resilience | Keyboard/focus, non-color status, chart alternatives, theme contrast, resizing/scaling, source-unavailable evidence state | REM-NFR-001–004 |
| Consolidated evidence | Automated tests, synthetic matrix, screenshots, demonstrations, accessibility evidence, launch instructions, limitations, one independent review | REM-NFR-005 |

## Delivery sequence

1. Extend shared theme/appearance and failure-presentation foundations.
2. Correct Welcome and upload/metadata presentation.
3. complete Verify Data edit/save/revert/audit behavior and attestation.
4. Insert Review Rules and implement governed optional-rule workflows.
5. Extend deterministic result projections for structured evidence and analytics.
6. Refactor Results, Findings, Data Quality & Coverage, and source navigation.
7. Connect governed review disposal to the three required UI locations.
8. Run one consolidated internal verification and design consistency review.
9. Produce the complete evidence package.
10. Conduct one independent end-to-end review and resolve only material defects.
11. Stop for Project Owner hands-on acceptance.

Related implementation may proceed in parallel only where ownership boundaries do not create competing financial calculations or migration conflicts.

## Required implementation invariants

- Delivery code does not import or invoke financial evaluators.
- All pass/fail/not-evaluated states, aggregates, ratios, and chart values originate from deterministic engine projections.
- Rule version changes are append-only and create a successor Rule Set Version.
- Completed runs and findings remain immutable and comparable.
- Edit cancellation does not append correction events.
- Edit save never writes source workbooks.
- Disposal cancellation changes no review data.
- Disposal confirmation is review-bound, actor-bound, one-time, and commit-authorized.
- Theme changes affect presentation only.
- Technical details remain accessible without becoming primary UI content.

## Verification seams

| Risk | Required proof |
|---|---|
| Engine/UI rule semantic drift | Rule-name/purpose/version assertions across manifest, repository, UI, tests, and reports |
| UI recalculates financial truth | Architecture fitness checks and oracle comparison of persisted chart/result projections |
| Edits alter source files | Before/after source SHA-256 and workbook-byte equality |
| Unsaved edits leak into validation | Cancel/save/reconstruct/validate tests |
| Optional rule mutates history | Version/lifecycle/run comparison persistence tests |
| Evidence cannot locate source | Finding-to-row/cell UI tests, duplicate pair, reconciliation contributors, overrun links |
| Dark mode hides information | Screenshot comparison plus contrast and accessibility checks |
| Deletion crosses review boundary | Two-review isolation and shared-artifact tests |
| Disposal breaks audit startup | External-anchor retirement and restart reconciliation tests |
| External workbook is deleted | Filesystem preservation assertion |
| Missing Amount appears as zero | Partial/incomplete chart and NOT_EVALUATED oracle assertions |

## Exit criteria

This plan is not complete until the verification artifact records:

- exact changed files;
- exact commands and results;
- required screenshots in Light and Dark modes, plus System-mode behavior;
- rule add/edit/test and revalidation demonstration;
- Verify Data edit/audit demonstration;
- disposal demonstration;
- rule-to-evidence drill-down demonstration;
- expected-versus-actual fixture matrix;
- accessibility and visual-design results;
- launch instructions;
- known limitations; and
- independent-review identity, findings, remediation, and verdict.

Unexecuted checks remain `PENDING`; they shall not be converted to PASS by documentation alone.
