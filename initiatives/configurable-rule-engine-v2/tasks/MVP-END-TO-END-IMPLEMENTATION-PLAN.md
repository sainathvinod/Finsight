# Integrated MVP End-to-End Implementation Plan

Status: Completed and independently verified
Date: 2026-07-27
Scope authority: Project Owner's end-to-end workflow-alignment request

## Objective

Deliver one continuous FinSight financial-review journey using the approved
walking-skeleton visual direction and the supplied synthetic Budget/GED reference
model:

`Welcome → Create → Upload → Process → Verify Data → Confirm → Validate → Review
Results → Complete → Reopen`

This integrated increment reuses the approved Review Management and Upload &
Extraction foundations. It does not create another application, alter source
workbooks, or begin Windows packaging.

## Work packages

| Package | Delivery |
|---|---|
| Guided shell and navigation | One desktop path with the six approved stages: Create, Upload, Verify Data, Validate, Review Results, Complete. Technical workspace pages do not interrupt the primary journey. |
| Data preparation | Fingerprint-verified reconstruction of the two saved source reports on a worker thread, followed by an automatic transition to Verify Data. |
| Human data review | Complete Budget and GED tables, search, row-kind filtering, sorting, review-local edit/save/cancel/revert, original/current/source-cell evidence, history, attestation, and confirmation dialog. |
| Governed rule execution | Load the persisted `FINSIGHT-CORE-1.0` manifest, dispatch the five protected rule versions through the deterministic evaluator registry, and fail closed if the governed baseline is incomplete or unknown. |
| Sealed result model | Persist one immutable validation run, five rule executions, all 915 scope results, five findings, summary metrics, fingerprints, reviewed generation, rule versions, and audit evidence. |
| Financial Review | Seven tabs: Executive Overview, Budget Data, GED Data, Budget vs GED Comparison, Validation Results, Findings, and Data Quality. All business status comes from the sealed rule-engine projection. |
| Completion and history | Record completion, close the review, show a complete-state screen, enrich Past Reviews with saved metrics, and reopen closed reviews directly into read-only saved results. |
| Ask Fin boundary | Keep Ask Fin visible for product help and explanations of recorded results; never let it calculate or decide validation outcomes. |
| Verification | Golden fixture oracle, positive/negative/boundary rule tests, migration and persistence tests, UI/accessibility tests, architecture fitness checks, visual comparison, launch smoke test, and one independent end-to-end review. |

## Acceptance traceability

| Requirement | Verification seam |
|---|---|
| Exactly two required sources | Source-intake UI/application tests and Upload screenshots |
| Original reports remain unchanged | SHA-256/size verification before reconstruction; correction tests prove original/current separation |
| Review-local corrections are attributable and reversible | Append-only correction events plus edit/revert application and UI tests |
| All five protected rules execute through one engine | Persisted manifest tests, engine dispatch tests, architecture fitness tests, and five execution rows |
| Results are complete and reproducible | 915-row scope ledger, hashes/seals, persisted projection, restart/reopen tests |
| Dashboard and tabs do not recalculate validation | Delivery-layer import/engine-invocation fitness test |
| Completed review reopens read-only | Integrated UI and application persistence tests |
| Walking-skeleton direction is preserved | Same-viewport comparisons and `design-qa.md` |

## Explicitly out of scope

- Windows executable, installer, signing, and release packaging
- Additional workbook layouts beyond the approved SLV-001 Budget/GED reference model
- Rule-authoring and protected-rule approval screens
- Deep Ask Fin review Q&A or AI-generated financial decisions
- Organization-wide accounting-policy semantics beyond the supplied report contract

## Exit

The increment exits only when consolidated internal verification passes, the
expected-versus-actual fixture matrix matches, visual QA passes, and the independent
review reports no remaining Blocker, Critical, or Major defect.
