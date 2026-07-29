# Workflow 1 Implementation Plan — Review Management

- **Date:** 2026-07-27
- **Status:** Complete; internal verification and independent review PASS
- **Authorization:** Project Owner instruction dated 2026-07-27
- **Parent plan:** [Technical Implementation Plan](../plans/TECHNICAL-IMPLEMENTATION-PLAN.md)
- **Architecture gate:** [Approved](../readiness/ARCHITECTURE-APPROVAL-2026-07-27.md)
- **Next workflow:** Blocked

## 1. User outcome

An attributable, authorized user can launch FinSight, create a persisted monthly financial review, close
and reopen the application, find the saved review, and explicitly reopen it. The complete increment stays
inside Review Management and creates no financial source, extraction, correction, validation, finding,
analytics, Ask Fin, report, export, or package record.

## 2. Scoped design refinement

The latest Project Owner instruction and the approved Technical Implementation Plan require review
creation and restart-safe persistence in Workflow 1. Two older Architecture paragraphs describe reporting
period selection as volatile until upload. For this increment the newer, more specific direction controls:

1. Workflow 1 atomically creates the inherited Review Cycle, one Working Candidate, one `Draft` Review
   Status event, identity/authorization evidence, and creation audit evidence.
2. Workflow 2 later binds the two source reports and advances that same candidate to `Data Uploaded`.
3. No Review Version/ReviewGeneration is created before explicit extraction review confirmation.

This is a timing clarification only. It does not alter the verified-data boundary, rule engine, result
ledger, publication model, or any Workflow 2 behavior.

## 3. Acceptance contract

The increment must satisfy W1-01 through W1-20:

- exact Welcome title and accessible, keyboard-operable Create/Past actions;
- `View Past Reviews` disabled with an accessible reason when no review exists;
- full reporting month/year selection with deterministic validation;
- opaque Review ID, Working Candidate, `Draft` status, active disposition, and no downstream records;
- atomic/idempotent creation, encrypted restart-safe persistence, and explicit reopen by Review ID;
- all seven lifecycle statuses represented, with only `Draft` creatable in this workflow;
- attributable creation/reopen audit facts protected by an HMAC chain;
- replaceable actor identity, three-role/extensible permission model, explicit-denial precedence, and
  signed external role-manifest validation;
- fail-closed identity, authorization, manifest, store, migration, audit-chain, and registry behavior;
- Past Reviews status filtering and clear separation of lifecycle, disposition, analytical/publication,
  and future financial status;
- accessibility names, focus, keyboard journeys, high contrast, and 200% text scaling; and
- a full regression run proving no Workflow 2+ behavior was added or changed.

## 4. Allowed implementation files

Only these existing files may be edited:

- `.importlinter`
- `pyproject.toml`
- `requirements.txt`
- `requirements-dev.txt`
- `DEPENDENCIES.md`
- `build/versions.json`
- `conftest.py`
- `src/finsight/app.py`
- `src/finsight/application/read_models/views.py`
- `src/finsight/application/read_models/queries.py`
- `src/finsight/application/workflow.py`
- `src/finsight/application/transition_engine.py`
- `src/finsight/delivery/desktop/app.py`
- `src/finsight/delivery/desktop/controllers/app_controller.py`
- `src/finsight/delivery/desktop/main_window.py`
- `src/finsight/delivery/desktop/views/__init__.py`
- `src/finsight/delivery/desktop/theme/qss.py`
- `src/finsight/domain/review_cycle.py`
- `src/finsight/infrastructure/audit.py`
- `src/finsight/infrastructure/persistence.py`
- `src/finsight/infrastructure/migrations/runner.py`
- `tests/ui/conftest.py`
- existing Workflow 1-adjacent tests only when an approved V2 contract intentionally supersedes a legacy
  assertion.

These new files may be created:

- `src/finsight/domain/identity.py`
- `src/finsight/domain/review_management.py`
- `src/finsight/application/security.py`
- `src/finsight/application/review_management.py`
- `src/finsight/application/disposal_registry.py`
- `src/finsight/application/failure_contracts.py`
- `src/finsight/infrastructure/identity.py`
- `src/finsight/infrastructure/authorization_manifest.py`
- `src/finsight/infrastructure/authorization_source.py`
- `src/finsight/infrastructure/secure_store.py`
- `src/finsight/infrastructure/review_management_repository.py`
- `src/finsight/infrastructure/audit_stream.py`
- `src/finsight/infrastructure/disposal_registry.py`
- `src/finsight/infrastructure/runtime_paths.py`
- `src/finsight/infrastructure/migrations/m0004_v2_review_management.py`
- `src/finsight/delivery/desktop/views/review_management_view.py`
- `tests/unit/test_identity.py`
- `tests/unit/test_review_management.py`
- `tests/application/test_authorization.py`
- `tests/application/test_failure_contracts.py`
- `tests/application/test_review_management.py`
- `tests/infrastructure/test_identity.py`
- `tests/infrastructure/test_authorization_manifest.py`
- `tests/infrastructure/test_authorization_source.py`
- `tests/infrastructure/test_secure_store.py`
- `tests/infrastructure/test_audit_stream.py`
- `tests/infrastructure/test_review_management_repository.py`
- `tests/infrastructure/test_disposal_registry.py`
- `tests/infrastructure/test_runtime_paths.py`
- `tests/migrations/test_migration_0004.py`
- `tests/ui/test_review_management.py`
- `tests/accessibility/test_review_management_accessibility.py`
- `tests/security/test_workflow1_security.py`
- `tests/fitness/test_workflow1_scope.py`
- `scripts/capture_workflow1_screenshots.py`
- `scripts/launch_workflow1_demo.py`
- `scripts/workflow1_demo_support.py`
- Workflow 1 evidence, review, qualification, and screenshot files under this initiative.

If a material defect requires a file outside this list, this plan must be updated before that file is
touched. Workbook readers, ingestion, normalization, corrections, validation/rules, analytics, AI,
reports/exports, fixtures, build recipes, and installer sources are explicitly prohibited.

### Independent-review remediation allowance

The independent Workflow 1 review found material defects in authorization pre-store validation and
commit-time refresh, immutable authorization history, audit rollback anchoring, machine-scoped local
storage, accessibility evidence, diagnostic failures, and release/test composition isolation. The same
Workflow 1 scope therefore additionally permits:

- `src/finsight/diagnostics.py` and a narrowly scoped new application/infrastructure diagnostic or
  authorization-source module if separation requires it;
- `tests/support.py` or one new Workflow 1 test-composition helper under `tests/`;
- existing tests that call the composition root and must explicitly inject the test-only security
  profile;
- `scripts/launch_workflow1_demo.py`;
- material-review regression tests and updated verification/review evidence; and
- the already allowed desktop, theme, application security/review-management, persistence, registry,
  migration, and composition files needed to close the findings.

This allowance does not authorize any workbook, extraction, correction, deterministic rule, finding,
analytics, AI, report/export, fixture, installer, or packaging implementation.

## 5. Verification and review

One internal verification pass will run focused Workflow 1 tests, migration/security/accessibility tests,
the complete existing suite, Ruff, import-linter, dependency validation, a clean encrypted-store launch
smoke, and a fresh-process restart journey. Screenshots will cover empty Welcome, Create New Review,
populated Welcome, Past Reviews, and the opened Draft review.

One independent reviewer who did not author the implementation inspected the frozen diff and evidence.
The initial FAIL findings were repaired as one bounded material-defect remediation cycle and rechecked by
the same reviewer. The final verdict is PASS. Workflow 2 remains blocked pending Project Owner approval.
