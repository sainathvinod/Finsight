# MVP Final Remediation — Exact Changed-File Inventory

- **Date:** 2026-07-28
- **Scope:** Consolidated final MVP remediation only
- **Excludes:** Unchanged Stage 1/2 fixtures, prior workflow implementation files
  untouched by this increment, local databases/WAL files, caches, generated Python
  bytecode, and unrelated historical artifacts
- **State:** Exact terminal remediation inventory used for the final bounded independent recheck

Paths are relative to the repository root.

## Runtime source

- `src/finsight/app.py`
- `src/finsight/application/disposal_registry.py`
- `src/finsight/application/failure_contracts.py`
- `src/finsight/application/financial_review.py`
- `src/finsight/application/review_disposal.py`
- `src/finsight/application/review_management.py`
- `src/finsight/application/rule_management.py`
- `src/finsight/application/security.py`
- `src/finsight/delivery/desktop/app.py`
- `src/finsight/delivery/desktop/components/__init__.py`
- `src/finsight/delivery/desktop/components/appearance_control.py`
- `src/finsight/delivery/desktop/components/charts.py`
- `src/finsight/delivery/desktop/components/confirmation_dialogs.py`
- `src/finsight/delivery/desktop/components/inline_message.py`
- `src/finsight/delivery/desktop/components/nav_item.py`
- `src/finsight/delivery/desktop/components/review_progress.py`
- `src/finsight/delivery/desktop/controllers/app_controller.py`
- `src/finsight/delivery/desktop/main_window.py`
- `src/finsight/delivery/desktop/theme/__init__.py`
- `src/finsight/delivery/desktop/theme/appearance.py`
- `src/finsight/delivery/desktop/theme/qss.py`
- `src/finsight/delivery/desktop/theme/tokens.py`
- `src/finsight/delivery/desktop/views/__init__.py`
- `src/finsight/delivery/desktop/views/financial_review_view.py`
- `src/finsight/delivery/desktop/views/review_management_view.py`
- `src/finsight/delivery/desktop/views/rules_repository_view.py`
- `src/finsight/delivery/desktop/views/settings_view.py`
- `src/finsight/delivery/desktop/views/source_intake_view.py`
- `src/finsight/domain/financial_validation.py`
- `src/finsight/domain/identity.py`
- `src/finsight/infrastructure/audit_stream.py`
- `src/finsight/infrastructure/authorization_manifest.py`
- `src/finsight/infrastructure/authorization_source.py`
- `src/finsight/infrastructure/disposal_registry.py`
- `src/finsight/infrastructure/financial_review_repository.py`
- `src/finsight/infrastructure/identity.py`
- `src/finsight/infrastructure/review_disposal.py`
- `src/finsight/infrastructure/review_management_repository.py`
- `src/finsight/infrastructure/secure_store.py`
- `src/finsight/infrastructure/source_intake_repository.py`

## Migrations

- `src/finsight/infrastructure/migrations/m0007_configurable_rules_and_reanalysis.py`
- `src/finsight/infrastructure/migrations/m0008_review_disposal.py`
- `src/finsight/infrastructure/migrations/m0009_protected_core_governance.py`
- `src/finsight/infrastructure/migrations/m0010_protected_core_governance_integrity.py`
- `src/finsight/infrastructure/migrations/m0011_protected_request_baseline_binding.py`
- `src/finsight/infrastructure/migrations/m0012_workspace_baseline_upgrade_governance.py`
- `src/finsight/infrastructure/migrations/runner.py`

## Automated tests

- `tests/accessibility/test_review_management_accessibility.py`
- `tests/ai/test_migration_0002.py`
- `tests/application/test_authorization.py`
- `tests/application/test_failure_contracts.py`
- `tests/application/test_financial_review.py`
- `tests/application/test_protected_rule_governance.py`
- `tests/application/test_reconstruction_architecture.py`
- `tests/application/test_review_disposal.py`
- `tests/application/test_rule_management.py`
- `tests/fitness/test_integrated_financial_review_architecture.py`
- `tests/infrastructure/test_disposal_registry.py`
- `tests/infrastructure/test_authorization_manifest.py`
- `tests/infrastructure/test_authorization_source.py`
- `tests/infrastructure/test_identity.py`
- `tests/migrations/test_migration_0003.py`
- `tests/migrations/test_migration_0006.py`
- `tests/migrations/test_migration_0007.py`
- `tests/migrations/test_migration_0008.py`
- `tests/migrations/test_migration_0009.py`
- `tests/migrations/test_migration_0010.py`
- `tests/migrations/test_migration_0011.py`
- `tests/migrations/test_migration_0012.py`
- `tests/migrations/test_migrations.py`
- `tests/security/test_workspace_baseline_upgrade_security.py`
- `tests/security/test_workflow1_security.py`
- `tests/ui/test_appearance.py`
- `tests/ui/test_integrated_financial_review.py`
- `tests/ui/test_protected_rule_governance.py`
- `tests/ui/test_review_deletion.py`
- `tests/ui/test_review_management.py`
- `tests/ui/test_source_intake.py`
- `tests/unit/test_financial_validation.py`
- `tests/unit/test_identity.py`

## Launch, demonstration, and capture scripts

- `scripts/build_design_qa_comparisons.py`
- `scripts/capture_mvp_screenshots.py`
- `scripts/launch_mvp_demo.py`
- `scripts/workflow1_demo_support.py`

## SDD and remediation documentation

- `design-qa.md`
- `initiatives/configurable-rule-engine-v2/README.md`
- `initiatives/configurable-rule-engine-v2/docs/FINANCIAL-REVIEW-WORKFLOW.md`
- `initiatives/configurable-rule-engine-v2/docs/MVP-REMEDIATION-ARCHITECTURE-2026-07-28.md`
- `initiatives/configurable-rule-engine-v2/fixtures/MVP-REMEDIATION-SYNTHETIC-TEST-MATRIX-2026-07-28.md`
- `initiatives/configurable-rule-engine-v2/fixtures/README.md`
- `initiatives/configurable-rule-engine-v2/readiness/MVP-FINAL-REMEDIATION-STAGE-PACKAGE-2026-07-28.md`
- `initiatives/configurable-rule-engine-v2/requirements/MVP-REMEDIATION-DELTA-2026-07-28.md`
- `initiatives/configurable-rule-engine-v2/requirements/README.md`
- `initiatives/configurable-rule-engine-v2/reviews/REVIEW-2026-07-27-mvp-end-to-end.md`
- `initiatives/configurable-rule-engine-v2/reviews/REVIEW-2026-07-28-mvp-final-remediation.md`
- `initiatives/configurable-rule-engine-v2/tasks/MVP-END-TO-END-IMPLEMENTATION-PLAN.md`
- `initiatives/configurable-rule-engine-v2/tasks/MVP-FINAL-REMEDIATION-IMPLEMENTATION-PLAN-2026-07-28.md`
- `initiatives/configurable-rule-engine-v2/tasks/README.md`
- `initiatives/configurable-rule-engine-v2/verification/MVP-END-TO-END-VERIFICATION-2026-07-27.md`
- `initiatives/configurable-rule-engine-v2/verification/MVP-FINAL-REMEDIATION-CHANGED-FILES-2026-07-28.md`
- `initiatives/configurable-rule-engine-v2/verification/MVP-FINAL-REMEDIATION-VERIFICATION-2026-07-28.md`
- `initiatives/configurable-rule-engine-v2/verification/README.md`

## Design audit and comparison evidence

- `artifacts/design-audit/pre-remediation/AUDIT.md`
- `artifacts/design-audit/pre-remediation/01-welcome.png`
- `artifacts/design-audit/pre-remediation/02-create-review.png`
- `artifacts/design-audit/pre-remediation/03-upload-documents-empty.png`
- `artifacts/design-audit/pre-remediation/04-upload-documents-ready.png`
- `artifacts/design-audit/pre-remediation/05-processing.png`
- `artifacts/design-audit/pre-remediation/06-verify-budget-data.png`
- `artifacts/design-audit/pre-remediation/07-verify-ged-data.png`
- `artifacts/design-audit/pre-remediation/08-review-confirmation.png`
- `artifacts/design-audit/pre-remediation/09-validation.png`
- `artifacts/design-audit/pre-remediation/10-results-executive-overview.png`
- `artifacts/design-audit/pre-remediation/11-results-budget-vs-ged.png`
- `artifacts/design-audit/pre-remediation/12-results-validation-rules.png`
- `artifacts/design-audit/pre-remediation/13-results-findings.png`
- `artifacts/design-audit/pre-remediation/14-results-data-quality.png`
- `artifacts/design-audit/pre-remediation/15-review-complete.png`
- `artifacts/design-audit/pre-remediation/16-past-reviews.png`
- `artifacts/design-audit/pre-remediation/17-reopened-read-only-results.png`
- `artifacts/design-audit/pre-remediation/18-reopened-read-only-budget-data.png`
- `artifacts/design-qa/01-create-review-comparison.png`
- `artifacts/design-qa/02-upload-comparison.png`
- `artifacts/design-qa/03-verify-data-comparison.png`
- `artifacts/design-qa/04-results-overview-comparison.png`
- `artifacts/design-qa/05-findings-comparison.png`

The 18 superseded, unthemed end-to-end captures were retained as historical
pre-remediation evidence rather than mixed into the final gallery. Their exact
location is:

- `artifacts/design-audit/pre-remediation/legacy-mvp-end-to-end/01-welcome.png`
- `artifacts/design-audit/pre-remediation/legacy-mvp-end-to-end/02-create-review.png`
- `artifacts/design-audit/pre-remediation/legacy-mvp-end-to-end/03-upload-documents-empty.png`
- `artifacts/design-audit/pre-remediation/legacy-mvp-end-to-end/04-upload-documents-ready.png`
- `artifacts/design-audit/pre-remediation/legacy-mvp-end-to-end/05-processing.png`
- `artifacts/design-audit/pre-remediation/legacy-mvp-end-to-end/06-verify-budget-data.png`
- `artifacts/design-audit/pre-remediation/legacy-mvp-end-to-end/07-verify-ged-data.png`
- `artifacts/design-audit/pre-remediation/legacy-mvp-end-to-end/08-review-confirmation.png`
- `artifacts/design-audit/pre-remediation/legacy-mvp-end-to-end/09-validation.png`
- `artifacts/design-audit/pre-remediation/legacy-mvp-end-to-end/10-results-executive-overview.png`
- `artifacts/design-audit/pre-remediation/legacy-mvp-end-to-end/11-results-budget-vs-ged.png`
- `artifacts/design-audit/pre-remediation/legacy-mvp-end-to-end/12-results-validation-rules.png`
- `artifacts/design-audit/pre-remediation/legacy-mvp-end-to-end/13-results-findings.png`
- `artifacts/design-audit/pre-remediation/legacy-mvp-end-to-end/14-results-data-quality.png`
- `artifacts/design-audit/pre-remediation/legacy-mvp-end-to-end/15-review-complete.png`
- `artifacts/design-audit/pre-remediation/legacy-mvp-end-to-end/16-past-reviews.png`
- `artifacts/design-audit/pre-remediation/legacy-mvp-end-to-end/17-reopened-read-only-results.png`
- `artifacts/design-audit/pre-remediation/legacy-mvp-end-to-end/18-reopened-read-only-budget-data.png`

## Post-remediation screenshot evidence

Both primary theme directories contain this exact 48-file sequence at 1280 × 900:

1. `01-welcome.png`
2. `01a-settings-appearance.png`
3. `02-create-review.png`
4. `02a-create-review-required-error.png`
5. `03-upload-empty.png`
6. `04-upload-ready.png`
7. `05-processing.png`
8. `06-verify-budget.png`
9. `07-verify-ged.png`
10. `08-verify-budget-staged-edit.png`
11. `09-governed-save-changes.png`
12. `10-verify-budget-saved-edit.png`
13. `11-change-history.png`
14. `12-confirm-data-for-validation.png`
15. `13-rules-core-list-and-detail.png`
16. `13a-protected-change-request.png`
17. `13b-protected-change-pending.png`
18. `13c-protected-change-approver-queue.png`
19. `13d-protected-change-approval.png`
20. `13e-protected-change-approved-history.png`
21. `14-optional-rule-add.png`
22. `15-optional-rule-draft.png`
23. `16-optional-rule-edit.png`
24. `17-optional-rule-test-result.png`
25. `18-optional-rule-tested.png`
26. `19-optional-rule-activated.png`
27. `20-validation-progress.png`
28. `21-executive-overview.png`
29. `22-executive-analytics.png`
30. `23-budget-chart-and-evidence.png`
31. `24-ged-charts-and-evidence.png`
32. `25-budget-ged-comparison-chart.png`
33. `26-validation-results-evidence.png`
34. `27-findings-duplicate-evidence.png`
35. `28-data-quality-and-coverage.png`
36. `28a-workspace-upgrade-available.png`
37. `28b-workspace-upgrade-request.png`
38. `28c-workspace-upgrade-pending.png`
39. `28d-workspace-upgrade-approver-queue.png`
40. `28e-workspace-upgrade-authorization.png`
41. `28f-workspace-upgrade-applied-history.png`
42. `28g-workspace-upgrade-revalidation-required.png`
43. `28h-workspace-upgrade-revalidation-progress.png`
44. `28i-workspace-upgrade-revalidated-results.png`
45. `29-review-complete.png`
46. `30-past-reviews.png`
47. `31-reopened-results.png`
48. `32-delete-review-confirmation.png`

Directory prefixes:

- `initiatives/configurable-rule-engine-v2/verification/screenshots/mvp-end-to-end/light/`
- `initiatives/configurable-rule-engine-v2/verification/screenshots/mvp-end-to-end/dark/`

Therefore the primary post-remediation evidence inventory is exactly 96 theme
captures: 48 Light and the same 48 Dark.

## Responsive screenshot evidence

The same exact 48-file sequence is captured at 1180 × 860 under:

- `artifacts/design-qa/final-1180x860/light/`
- `artifacts/design-qa/final-1180x860/dark/`

The responsive evidence inventory is exactly 96 additional captures: 48 Light and
48 Dark. Together, primary and responsive theme evidence totals 192 screenshots.
The five comparison images listed in the prior section are separate combined
walking-skeleton comparisons.
