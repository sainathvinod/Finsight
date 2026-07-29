# Workflow 2 Implementation Plan — Upload & Extraction

- **Date:** 2026-07-27
- **Status:** Implementation, consolidated internal verification, and independent review complete
- **Authorization:** Project Owner approval of Workflow 1 and authorization of Workflow 2 dated
  2026-07-27
- **Parent plan:** [Technical Implementation Plan](../plans/TECHNICAL-IMPLEMENTATION-PLAN.md)
- **Architecture gate:** [Approved](../readiness/ARCHITECTURE-APPROVAL-2026-07-27.md)
- **Workflow 1 gate:** Approved by Project Owner after hands-on review
- **Workflow 3:** Prohibited until separate Project Owner approval

## 1. User outcome

An authenticated Reviewer can open a Draft review, select exactly one Budget Report and one GED
Report, see safe extraction progress and compatibility evidence, inspect report-level department and
reporting-period metadata, and save the pair to the encrypted review store without changing or copying
the workbook bytes. A saved pair survives restart as fingerprints, source metadata, lineage evidence,
counts, and an auditable `Data Uploaded` lifecycle state.

Department or reporting-period mismatches are retained as explicit blocking metadata-gate evidence.
They never silently enter a later cross-file workflow. Workflow 3 remains visibly unavailable.

## 2. Exact first-release source contract

Workflow 2 implements the approved sample reports as `SLV-001`, not a generic spreadsheet guesser.

### Budget Report

- required worksheet: `Original Budget`;
- exact row-1 headers A:H: `Account #`, `Account Name`, `bgt`, `atd`, `etc`, `eac`, `delta`,
  `Notes`;
- six-digit account rows are Budget detail records;
- three-digit account rows are group totals;
- blank rows are separators;
- the final `Grand Total` row carries the department number in column B as `Department NNNN`;
- the supplied synthetic fixture yields 71 Budget detail records and Department Number `00-0245`;
- the supplied layout has no report-period field, so period evidence is explicitly
  `workspace assigned / no source period`.

### GED Report

- required worksheet: `GED`;
- exact report title at row 1, reporting period at row 3, and run date at row 4;
- exact 15-column header at row 7 and body classification beginning at row 8;
- transaction candidates, repeated headers, account totals, the final department total, and blank
  rows are classified separately;
- a transaction with a blank required Amount remains a transaction candidate for the future CORE-04
  rule;
- account-total and department-total rows are not counted as transactions;
- the supplied synthetic fixture yields 258 GED transactions, Department Number `00-0245`, raw
  Department Name `Applications Enginee`, and reporting period May 2026.

The intentional transaction-level Department Number `00-0999` remains a GED transaction issue for
future CORE-02 evaluation. It does not override the authoritative report-level Department Number from
the exact department-total row and therefore does not create a false intake mismatch.

## 3. Architecture and implementation slices

### Domain and application

- immutable source-role, evidence, row-classification, inspection, pair, issue, and gate contracts;
- deterministic pair evaluation for source compatibility, department identity, and reporting period;
- read-only inspection orchestration and final source-identity verification;
- protected Review Management commands for inspection audit, atomic pair commit, idempotent replay,
  replacement lineage, and restart-safe summary restoration;
- only a compatible Budget/GED pair can be committed;
- mismatch pairs may be retained as `Data Uploaded` evidence, but their metadata gate is `Blocked`.

### Workbook safety and extraction

- `WRL-001` allows bounded `.xlsx` ZIP/OPC workbooks only;
- macros, ActiveX/OLE content, external links, unsafe archive paths, ambiguous duplicate members,
  unsupported protection/encryption, malformed XML, and configured resource-limit violations fail
  closed;
- inspection reads one bounded same-byte snapshot, calculates SHA-256, and never writes the selected
  workbook;
- `SLV-001` opens formula and cached-value projections read-only, validates exact sheets/headers,
  retains raw/cached/formula lineage, and applies the exact Budget/GED row classifiers;
- commit rechecks size and SHA-256 so a source changed after extraction cannot be bound.

### Persistence and audit

- additive migration 0005 stores append-only source binding versions, current binding pointers,
  metadata evidence, intake summaries, issue evidence, and idempotency records;
- encrypted persistence retains path hints, filename, size, SHA-256, worksheet/profile versions,
  counts, normalized/raw evidence, actor/time, match/gate status, and predecessor lineage;
- workbook bytes and complete extracted rows are not retained in the database;
- first pair commit atomically advances `Draft` to `Data Uploaded`; replacement appends a successor
  summary without silently rewriting history;
- audit records cover inspection start, completion/rejection/failure, source-intake
  completion/replacement, authorization, and lifecycle transition evidence.

### Desktop presentation and accessibility

- the approved FinSight shell is retained: left sidebar, top header, Ask Fin entry point, wide
  desktop workspace, cards, status badges, and an 11-step progress treatment;
- Step 3 shows exactly two responsive role-labeled cards, clear read-only-source notice, filename,
  worksheet, department, period, count, file size, full fingerprint, compatibility state, and issues;
- Step 4 shows the report identity, period comparison, source evidence, preservation statement,
  mismatch codes, and an explicit Workflow 3 scope boundary;
- card layouts reflow at compact and 200%-scaled widths without page-level horizontal scrolling;
- keyboard order, focus after navigation, Delete removal for focused unsaved selections, accessible
  names/descriptions, high contrast, and polite/assertive status announcements are covered.

## 4. Requirements traceability

| Contract | Workflow 2 realization |
|---|---|
| FR-126 | Exactly Budget Report and GED Report upload roles |
| FR-127 | Per-source filename, role, compatibility/extraction state, count, fingerprint, and issue evidence |
| FR-128 | Compatible two-source pair required; later workflow remains blocked |
| FR-129 | Budget Grand Total and GED department-total identity with raw source evidence |
| FR-130 | Exact GED row-3 period plus visible Budget workspace assignment |
| FR-131 | Step-4 pre-validation metadata summary |
| FR-132 | Exact worksheet/header/row-shape diagnostics with source location |
| FR-133 | No Application Engineering allow-list or department-specific execution path |
| FR-134 | Deterministic report-level Department Number mismatch gate |
| FR-135 | Deterministic selected-review/GED period mismatch gate |
| FR-180–FR-183 | Exact Budget/GED field mappings and row classification |
| NFR-081, NFR-086–088 | Bounded failures, safe user messages, correlation/audit evidence |
| NFR-092–096 | Accessible desktop layout, keyboard operation, scaling, and non-color status |
| NFR-105–106, NFR-109–110 | Read-only source handling, fingerprints, lineage, and restart-safe evidence |

## 5. Implementation inventory

### Application source

- `src/finsight/app.py`
- `src/finsight/application/failure_contracts.py`
- `src/finsight/application/review_management.py`
- `src/finsight/application/source_intake.py`
- `src/finsight/delivery/desktop/controllers/app_controller.py`
- `src/finsight/delivery/desktop/main_window.py`
- `src/finsight/delivery/desktop/theme/qss.py`
- `src/finsight/delivery/desktop/views/__init__.py`
- `src/finsight/delivery/desktop/views/review_management_view.py`
- `src/finsight/delivery/desktop/views/source_intake_view.py`
- `src/finsight/domain/source_intake.py`
- `src/finsight/infrastructure/migrations/m0005_v2_source_intake.py`
- `src/finsight/infrastructure/migrations/runner.py`
- `src/finsight/infrastructure/review_management_repository.py`
- `src/finsight/infrastructure/slv001_extractor.py`
- `src/finsight/infrastructure/source_intake_repository.py`
- `src/finsight/infrastructure/workbook_safety.py`

### Fixtures and developer evidence

- `initiatives/configurable-rule-engine-v2/fixtures/README.md`
- `initiatives/configurable-rule-engine-v2/fixtures/Sample_Budget_Report.xlsx`
- `initiatives/configurable-rule-engine-v2/fixtures/Sample_GED_Report.xlsx`
- `scripts/workflow2_demo_support.py`
- `scripts/launch_workflow2_demo.py`
- `scripts/capture_workflow2_screenshots.py`
- Workflow 2 plan, verification, review, and screenshot evidence under this initiative.

### Automated tests

- `tests/accessibility/test_source_intake_accessibility.py`
- `tests/application/test_source_intake.py`
- `tests/infrastructure/test_slv001_extractor.py`
- `tests/infrastructure/test_source_intake_repository.py`
- `tests/infrastructure/test_workbook_safety.py`
- `tests/migrations/test_migration_0005.py`
- `tests/ui/test_source_intake.py`
- `tests/unit/test_source_intake.py`
- `tests/fitness/test_workflow2_scope.py`
- narrow migration-head expectation updates in
  `tests/ai/test_migration_0002.py`,
  `tests/application/test_reconstruction_architecture.py`,
  `tests/migrations/test_migration_0003.py`, and `tests/migrations/test_migrations.py`.

## 6. Verification and review

One consolidated internal pass covers source-domain determinism, real-fixture row classifications,
workbook safety, persistence/migration/atomicity, authorization/audit, UI, accessibility, restart
restoration, source-byte hashes, changed-file lint, architecture boundaries, dependencies, launch
smoke, screenshot generation, and the full regression suite.

After internal PASS, one independent reviewer who did not implement Workflow 2 will inspect the frozen
increment and evidence. Only material defects will be repaired, batched once, and rechecked. Wording or
format-only churn is excluded.

## 7. Explicit exclusions

Workflow 2 does not implement extracted-record editing or confirmation, a sealed Review Version,
corrections/reversions, deterministic validation, rules, findings, analytics, Ask Fin review Q&A,
reports/exports, review-history additions beyond the inherited Workflow 1 list, installer work, or
Windows release qualification. The disabled Extraction Review action is a scope marker only.
