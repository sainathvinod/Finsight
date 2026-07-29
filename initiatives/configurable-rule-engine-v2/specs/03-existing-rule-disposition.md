# 03 — Existing FinSight Rule Disposition Register

- **Purpose:** Ensure the configurable-rule-engine initiative does not silently delete, demote, reclassify, or repurpose any rule in the existing approved FinSight Rules Catalog.
- **Source:** Root `../../../specs/05-rules-catalog.md`; HD-01, HD-17, HD-18, HD-27; FR-174; clarification CQ-13/CQ-29.
- **Status:** Requirements-reviewed preservation-complete register; independent PASS recorded; row-level baselining and future per-rule migration decisions remain governed.
- **Protection:** Every legacy rule retains its existing catalog meaning, identifier, phase/status, configuration, and traceability. None is part of the initial V2 active set unless a future governed migration explicitly says so.

## Decision values

The approved bulk disposition for the first V2 release is **Preserve unchanged**. This:

- retains every existing definition and status unchanged;
- does not assign a V2 classification or activate the rule in V2;
- does not map a legacy identifier to CORE-01 through CORE-05;
- requires a separate governed FR-174 decision before any future successor, V2 classification, controlled-evaluator mapping, activation, or retirement.

The five protected controls use the new collision-free IDs `R-VAL-01` through `R-VAL-05` defined in §2.12 of `01-functional-requirements.md`.

## Complete catalog inventory

| Existing Rule ID | Catalog family | V2 disposition | V2 classification | CORE mapping | Decision owner/evidence |
|---|---|---|---|---|---|
| R-BUD-01 | Budget | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-BUD-02 | Budget | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-BUD-03 | Budget | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-BUD-04 | Budget | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-BUD-05 | Budget | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-BUD-06 | Budget | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-GED-01 | GED | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-GED-02 | GED | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-GED-03 | GED | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-GED-04 | GED | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-GED-05 | GED | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-GED-06 | GED | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-GED-07 | GED | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-REC-01 | Reconciliation | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-REC-02 | Reconciliation | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-REC-03 | Reconciliation | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-REC-04 | Reconciliation | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-REC-05 | Reconciliation | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-FND-01 | Findings | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-FND-02 | Findings | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-FND-03 | Findings | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-FND-04 | Findings | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-FND-05 | Findings | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-RPT-01 | Reporting | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-RPT-02 | Reporting | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-RPT-03 | Reporting | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-HST-01 | History | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-HST-02 | History | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-HST-03 | History | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-HST-04 | History | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-RDY-01 | Readiness | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-RDY-02 | Readiness | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-RDY-03 | Readiness | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-RDY-04 | Readiness | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-RDY-05 | Readiness | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-RDY-06 | Readiness | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-RDY-07 | Readiness | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-INV-01 | Invoice review | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-INV-02 | Invoice review | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-INV-03 | Invoice review | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-INV-04 | Invoice review | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-INV-05 | Invoice review | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-INV-06 | Invoice review | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-INV-07 | Invoice review | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-INV-08 | Invoice review | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-INV-09 | Invoice review | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-INV-10 | Invoice review | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-INV-11 | Invoice review | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-RES-01 | Resource and contract | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-RES-02 | Resource and contract | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-RES-03 | Resource and contract | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-RES-04 | Resource and contract | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-RES-05 | Resource and contract | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-FOR-01 | Forecasting and scenarios | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-FOR-02 | Forecasting and scenarios | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-FOR-03 | Forecasting and scenarios | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |
| R-FOR-04 | Forecasting and scenarios | Preserve unchanged | Legacy approved; not assigned a V2 class | None | HD-01/HD-17/HD-18 preservation decision |

## Future migration gate

Requirements approval and the five-rule MVP are not blocked by an absent V2 mapping for a preserved legacy rule. Future migration of any row remains blocked until:

1. the proposed successor, V2 classification, controlled evaluator, lifecycle action, rationale, owner, and evidence are explicit;
2. any successor preserves the original rule version for historical replay;
3. the proposed identifier does not conflict with `R-VAL-01` through `R-VAL-05` or another catalog ID;
4. the applicable governance and activation tests pass;
5. an independent audit finds no omitted, duplicated, or silently repurposed catalog ID.
