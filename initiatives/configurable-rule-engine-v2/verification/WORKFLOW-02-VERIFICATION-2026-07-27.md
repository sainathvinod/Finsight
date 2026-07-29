# Workflow 2 Verification — Upload & Extraction

- **Date:** 2026-07-27
- **Scope:** Workflow 2 only
- **Implementation status:** Complete
- **Internal verification:** **PASS**
- **Independent review:** **PASS**
- **Workflow 3:** Not started

## Delivered user journey

An authenticated Reviewer can enter Upload & Extraction from a persisted Draft review, select exactly
one Budget Report and one GED Report, see each source's safe extraction and structural-compatibility
state, and inspect the exact worksheet, report-level department, reporting period, record count, file
size, and SHA-256 evidence. Selecting the approved synthetic pair yields 71 Budget detail records and
258 GED transactions.

Saving rechecks both source identities, atomically retains the two bindings and metadata summary,
advances the working review from `Draft` to `Data Uploaded`, and opens the Step-4 Workspace Identity
summary. The summary displays source-provided Department Name `Applications Enginee` exactly as
supplied, Department Number `00-0245`, May 2026, both filenames/counts/fingerprints, match state, and
the original-source preservation policy.

The same pair and metadata summary reopen from encrypted persistence without storing workbook bytes or
the complete extracted row population. File-type and layout errors fail closed with actionable issue
codes. Department and reporting-period mismatches are retained as `Action required` gate evidence and
cannot silently progress to the unimplemented Workflow 3.

## Approved fixture evidence

| Fixture | Exact SHA-256 | Expected Workflow 2 result |
|---|---|---|
| `Sample_Budget_Report.xlsx` | `bf40584183c564d91831214781969422d77d50439989f75750f0bdbe2bfa2b14` | `Original Budget`; `00-0245`; workspace-assigned period; 71 detail records |
| `Sample_GED_Report.xlsx` | `2213e3f1b10fee56fb4538112250fe37fbdaf36eb5e299fbfe6d17bd0f10603c` | `GED`; `Applications Enginee`; `00-0245`; May 2026; 258 transactions |

Pre- and post-inspection fixture hashes are compared during internal verification. The files are opened
read-only by the application; screenshot-only mismatch workbooks are temporary derived copies and are
deleted after capture.

## Internal verification results

| Check | Result |
|---|---|
| Complete automated regression: `.venv/bin/python -m pytest -q` | **PASS — 926 passed in 19.21s** |
| Focused Workflow 2 domain/application/infrastructure/migration/UI/accessibility/fitness suite | **PASS — 65 passed in 4.04s** |
| Workflow 1 UI/accessibility regression | **PASS — 20 passed in 4.29s** |
| Import architecture: `PYTHONPATH=src .venv/bin/lint-imports --config .importlinter --no-cache` | **PASS — 3 contracts kept, 0 broken; 193 files / 758 dependencies analyzed** |
| Workflow 2 changed-file Ruff check | **PASS** |
| Git whitespace check: `git diff --check` | **PASS** |
| Dependency integrity: `.venv/bin/python -m pip check` | **PASS — no broken requirements found** |
| Dependency governance: `.venv/bin/python build/validate_deps.py` | **PASS — 0 failures, 3 non-blocking drift warnings** |
| Developer launch smoke: `FINSIGHT_SMOKE=1 QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/launch_workflow2_demo.py --empty` | **PASS — fresh temporary encrypted store and approved fixture paths used** |
| Approved source hash/count/metadata verification | **PASS — source hashes unchanged; 71 Budget records, 258 GED transactions, `00-0245`, `Applications Enginee`, May 2026** |
| Restart restoration and audit/atomicity checks | **PASS — encrypted restart restoration, append-only audit, all-or-nothing pair binding, and changed-source rejection covered** |
| Screenshot evidence | **PASS — eight visually inspected 1180×720 RGB PNG files** |

## Independent review

**PASS.** One independent reviewer who did not author Workflow 2 inspected the source, tests,
persistence/audit behavior, exact-fixture extraction, security boundary, accessibility, screenshots,
scope, and this consolidated evidence. The initial review identified three Major gaps: actionable
diagnostic identity/remedies, complete Step-4 raw/source-cell evidence, and paired safety-limit
boundary coverage. They were resolved in one bounded remediation cycle, and the same reviewer
confirmed all three repairs. No Blocker, Critical, or Major finding remains. See
[Independent Workflow 2 Review](../reviews/REVIEW-2026-07-27-workflow-02.md).

## Screenshot evidence

| Screen/state | Evidence | SHA-256 |
|---|---|---|
| Empty Budget/GED upload cards | [01-upload-empty.png](screenshots/workflow-02/01-upload-empty.png) | `32cb8b7b75c9f4eca1fb03eec8915d69141043d40178aea9b045cceb2822228a` |
| Budget extracted; GED waiting | [02-budget-extracted.png](screenshots/workflow-02/02-budget-extracted.png) | `f85ebb5c05f2043991caf3f9abbc857fb85e33a5726da759d05e0f2a08eec85e` |
| Both approved sources extracted and matched | [03-both-extracted.png](screenshots/workflow-02/03-both-extracted.png) | `1c3241cfb8033f07244e7be6d5ae17822011ac066db68ac14676d489316d48b6` |
| Saved Workspace Identity summary | [04-metadata-matched.png](screenshots/workflow-02/04-metadata-matched.png) | `972721c6944d227a95b93973fc0e28db7cd607c7cb3cd1472e857e979ca4a327` |
| Unsupported file type | [05-file-type-error.png](screenshots/workflow-02/05-file-type-error.png) | `f3fc037cff7360f3b8fe5711f364ccc81705eba0c0fe38d6df47b233576c8457` |
| Missing required Budget worksheet/layout | [06-layout-error.png](screenshots/workflow-02/06-layout-error.png) | `40c6298b65043d1038018434eddbf0beb537be56c26566aa86653f8a6927cdf6` |
| Reporting-period mismatch gate | [07-reporting-period-mismatch.png](screenshots/workflow-02/07-reporting-period-mismatch.png) | `e3da4a25ffe3a9de784f107c8fafd18d42443181f220807310b85cb490bb937d` |
| Department mismatch gate | [08-department-mismatch.png](screenshots/workflow-02/08-department-mismatch.png) | `b487859aa4a03a730e717fc8e79a722cf3ef13fc814eadaccb6a2ce3a36f3da2` |

All captures were visually inspected. The approved wide shell, navigation, header, progress, cards,
status/error hierarchy, responsive use of space, and disabled Workflow 3 boundary are visible without
clipping. Error-state pages use a vertical scrollbar only where additional diagnostic content exceeds
the 720-pixel capture height; no page-level horizontal scroll is present.

## Exact Workflow 2 file inventory

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

### Approved fixtures

- `initiatives/configurable-rule-engine-v2/fixtures/README.md`
- `initiatives/configurable-rule-engine-v2/fixtures/Sample_Budget_Report.xlsx`
- `initiatives/configurable-rule-engine-v2/fixtures/Sample_GED_Report.xlsx`

### Developer verification utilities

- `scripts/capture_workflow2_screenshots.py`
- `scripts/launch_workflow2_demo.py`
- `scripts/workflow2_demo_support.py`

### Workflow 2 tests

- `tests/accessibility/test_source_intake_accessibility.py`
- `tests/application/test_source_intake.py`
- `tests/infrastructure/test_slv001_extractor.py`
- `tests/infrastructure/test_source_intake_repository.py`
- `tests/infrastructure/test_workbook_safety.py`
- `tests/migrations/test_migration_0005.py`
- `tests/ui/test_source_intake.py`
- `tests/unit/test_source_intake.py`
- `tests/fitness/test_workflow2_scope.py`

### Existing compatibility tests updated for migration 0005

- `tests/application/test_reconstruction_architecture.py`
- `tests/ai/test_migration_0002.py`
- `tests/migrations/test_migration_0003.py`
- `tests/migrations/test_migrations.py`

### Workflow 2 SDD and evidence artifacts

- `initiatives/configurable-rule-engine-v2/tasks/WORKFLOW-02-IMPLEMENTATION-PLAN.md`
- `initiatives/configurable-rule-engine-v2/tasks/README.md`
- `initiatives/configurable-rule-engine-v2/reviews/REVIEW-2026-07-27-workflow-02.md`
- `initiatives/configurable-rule-engine-v2/verification/README.md`
- `initiatives/configurable-rule-engine-v2/verification/WORKFLOW-02-VERIFICATION-2026-07-27.md`
- eight PNG files under
  `initiatives/configurable-rule-engine-v2/verification/screenshots/workflow-02/`

## Launch instructions

From the repository root:

```bash
.venv/bin/python scripts/launch_workflow2_demo.py
```

The default launch creates a fresh encrypted temporary developer store, creates a synthetic May 2026
Draft review, opens Workflow 2, and safely selects the two approved initiative fixtures. The temporary
store is deleted when the application exits.

Use `--empty` to exercise manual selection from empty upload cards:

```bash
.venv/bin/python scripts/launch_workflow2_demo.py --empty
```

Use an explicit developer-only path to exercise close/reopen persistence:

```bash
.venv/bin/python scripts/launch_workflow2_demo.py \
  --data-dir artifacts/workflow2-demo
```

The developer profile must not be used with real financial data.

## Known limitations and scope boundary

- `SLV-001` intentionally accepts only the approved `.xlsx` Budget/GED layouts. `.xls`, `.xlsm`,
  `.csv`, password-protected workbooks, and organization-specific variants require a future versioned
  source profile.
- Budget has no source reporting-period field in the approved layout; FinSight visibly records the
  selected workspace period instead of inferring one from filenames or values.
- Department Name is displayed exactly from GED evidence (`Applications Enginee` in the supplied
  fixture); no unverified expansion is invented.
- Source bytes and complete row populations are not copied into the encrypted store. The original
  workbook remains unchanged at its selected location; the store retains path hints, fingerprints,
  counts, profiles, evidence, and audit. Governed moved-source rebinding/reconstruction belongs to a
  later workflow.
- Mismatch pairs may be saved so the evidence is auditable, but their gate remains `Blocked`.
- Workflow 3 extraction review, correction, confirmation, and every validation/result feature are
  intentionally unavailable.
- Windows packaging, signing, and native runtime qualification remain reserved for their approved
  release gate.

## Gate statement

Workflow 2 has passed consolidated internal verification and independent review and is ready for
Project Owner hands-on review. Workflow 3 has not started and remains blocked.
