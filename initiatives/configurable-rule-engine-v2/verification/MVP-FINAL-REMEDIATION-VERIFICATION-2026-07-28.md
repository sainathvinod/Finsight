# MVP Final Remediation — Consolidated Verification Record

- **Date:** 2026-07-28
- **Scope:** Final UX, configurable rules, evidence, analytics, appearance, accessibility, and review-disposal remediation
- **Implementation status:** **IMPLEMENTED**
- **Internal verification:** **PASS — TERMINAL FULL SUITE AND ENGINEERING CHECKS**
- **Visual-design review:** **PASS — LIGHT, DARK, SYSTEM, AND RESPONSIVE QA**
- **Accessibility verification:** **PASS FOR IMPLEMENTED SCOPE — NATIVE SCREEN-READER SMOKE PENDING HANDS-ON REVIEW**
- **Independent review:** **PASS — INITIAL FAIL PRESERVED; IR-01 AND IR-02 CLOSED ON BOUNDED RECHECK**
- **Hands-on acceptance:** Pending Project Owner
- **Windows packaging:** Not started by explicit scope

Internal implementation verification is complete and recorded below. The initial
independent review failed the earlier snapshot on two Major defects. Both were
remediated; the focused internal re-audit and bounded independent recheck passed.
Project Owner hands-on acceptance remains explicitly pending.

## 1. Build identity

| Item | Recorded value |
|---|---|
| Branch / commit | `codex/configurable-rule-engine-v2`; dirty working-tree snapshot, so no immutable final commit is claimed |
| Application version | `1.0.0` |
| Schema version | `12` (`m0012_workspace_baseline_upgrade_governance`) |
| Rule Set Version | Protected baseline `FINSIGHT-CORE-2.0`, Rule Set Version `1.0.0`; protected rule versions `2.0.0` |
| Python / Qt runtime | Python `3.11.15`; PySide6 `6.11.1` |
| Operating system and appearance mode | macOS `26.5.2` arm64; Light and Dark visual QA passed; System Default resolved to Light headlessly; live OS-switch behavior passed automated tests but cannot be manually observed in the headless run |
| Fixture Budget SHA-256 | `bf40584183c564d91831214781969422d77d50439989f75750f0bdbe2bfa2b14` |
| Fixture GED SHA-256 | `2213e3f1b10fee56fb4538112250fe37fbdaf36eb5e299fbfe6d17bd0f10603c` |

## 2. Exact changed-file inventory

See the [exact changed-file inventory](MVP-FINAL-REMEDIATION-CHANGED-FILES-2026-07-28.md).
It enumerates runtime source, migrations, tests, scripts, SDD documents,
pre/post-remediation design evidence, 96 primary Light/Dark captures, 96
responsive captures, and five comparison images while excluding local databases,
caches, and unrelated historical files.

## 3. Seven-step workflow verification

| Step/state | Required proof | Automated result | Screenshot / demonstration | Verdict |
|---|---|---|---|---|
| Welcome | Centered hierarchy, side-by-side actions, Recent Reviews, shell retained | Integrated UI/focused suite passed | [Light](screenshots/mvp-end-to-end/light/01-welcome.png) / [Dark](screenshots/mvp-end-to-end/dark/01-welcome.png) | **PASS** |
| Settings | Keyboard-accessible Light, Dark, and System Default destination with persisted shared preference | Appearance, restart, keyboard, 200% text, and shell-propagation tests passed | [Light](screenshots/mvp-end-to-end/light/01a-settings-appearance.png) / [Dark](screenshots/mvp-end-to-end/dark/01a-settings-appearance.png) | **PASS** |
| 1. Create | Period inputs, plain-language required-field errors, keyboard order | Focused UI/accessibility tests passed | [Light](screenshots/mvp-end-to-end/light/02-create-review.png) / [Dark](screenshots/mvp-end-to-end/dark/02-create-review.png); required error [Light](screenshots/mvp-end-to-end/light/02a-create-review-required-error.png) / [Dark](screenshots/mvp-end-to-end/dark/02a-create-review-required-error.png) | **PASS** |
| 2. Upload | Business-first metadata, File Details disclosure, resolved Budget department, mismatch messages | Focused source-intake/integrated tests passed | Empty [Light](screenshots/mvp-end-to-end/light/03-upload-empty.png) / [Dark](screenshots/mvp-end-to-end/dark/03-upload-empty.png); ready [Light](screenshots/mvp-end-to-end/light/04-upload-ready.png) / [Dark](screenshots/mvp-end-to-end/dark/04-upload-ready.png) | **PASS** |
| 3. Verify Data | Budget/GED tabs, search/filter/sort, edit/save/cancel/revert, provenance, history, attestations | Correction/audit and integrated UI tests passed | Budget [Light](screenshots/mvp-end-to-end/light/06-verify-budget.png) / [Dark](screenshots/mvp-end-to-end/dark/06-verify-budget.png); GED [Light](screenshots/mvp-end-to-end/light/07-verify-ged.png) / [Dark](screenshots/mvp-end-to-end/dark/07-verify-ged.png); history [Light](screenshots/mvp-end-to-end/light/11-change-history.png) / [Dark](screenshots/mvp-end-to-end/dark/11-change-history.png) | **PASS** |
| 4. Review Rules | Five protected rules, details/fields/keys/severity/version, optional lifecycle actions | Rule-management lifecycle and integrated UI tests passed | Core [Light](screenshots/mvp-end-to-end/light/13-rules-core-list-and-detail.png) / [Dark](screenshots/mvp-end-to-end/dark/13-rules-core-list-and-detail.png); optional lifecycle sequence `14`–`19` in both directories | **PASS** |
| Protected governance | Rule Administrator request, immutable qualification, different-person decision, exact request-time baseline, future-only activation, and global Approver route | Protected-governance application/migration/security/UI tests and focused internal re-audit passed | Request/queue/decision/history sequence `13a`–`13e` in both directories | **PASS** |
| Existing-workspace baseline adoption | Rule Administrator requests one exact upgrade; a different Financial Control Approver authorizes it; approval creates only one successor workspace Rule Set; Reviewer then creates the successor Review Version and Validation Run | Workspace-upgrade application, migration 0012, authorization, security, reconstruction, and UI tests passed | Available/request/pending/approver/decision/applied/revalidation sequence `28a`–`28i` in both directories | **PASS** |
| 5. Validate | Exact confirmed basis and Rule Set Version; deterministic progress | Integrated validation test and protected 986-scope oracle passed | [Light](screenshots/mvp-end-to-end/light/20-validation-progress.png) / [Dark](screenshots/mvp-end-to-end/dark/20-validation-progress.png) | **PASS** |
| 6. Review Results | Business-first summary, analytics, rule/evidence/findings/quality distinction | Integrated results/evidence test passed | Overview [Light](screenshots/mvp-end-to-end/light/21-executive-overview.png) / [Dark](screenshots/mvp-end-to-end/dark/21-executive-overview.png); evidence sequence `22`–`28` in both directories | **PASS** |
| 7. Complete | Completion, saved history, reopen, exact run identity in details | Persistence/reopen integration test passed | Complete [Light](screenshots/mvp-end-to-end/light/29-review-complete.png) / [Dark](screenshots/mvp-end-to-end/dark/29-review-complete.png); reopened [Light](screenshots/mvp-end-to-end/light/31-reopened-results.png) / [Dark](screenshots/mvp-end-to-end/dark/31-reopened-results.png) | **PASS** |
| Disposal | Past Reviews, Review Details, Results entry points; cancel and permanent confirm | Application isolation/authorization tests and UI delete test passed in recorded focused suites | [Light](screenshots/mvp-end-to-end/light/32-delete-review-confirmation.png) / [Dark](screenshots/mvp-end-to-end/dark/32-delete-review-confirmation.png) | **PASS** |

## 4. Verify Data edit and audit demonstration

Record one Budget edit and one GED edit/revert without changing fixture bytes.

| Evidence | Result |
|---|---|
| Original Budget/GED SHA-256 before edit | Budget `bf405841…2b14`; GED `2213e3f1…03c` |
| Unsaved Cancel leaves working value unchanged | **PASS — integrated UI test** |
| Save disabled until affirmation | **PASS — integrated UI test** |
| Saved correction shows source row/cell, Original, prior, Current, actor, timestamp | **PASS — application correction-history and integrated UI tests** |
| Individual revert creates linked audit event | **PASS — `test_review_local_correction_is_audited_reversible_and_never_changes_source`** |
| Validation basis uses the saved Current value | **PASS — financial-review validation tests** |
| Original workbook hashes remain byte-identical | **PASS — correction test reads both source files unchanged after edit/revert** |
| Screenshot references | Staged edit [Light](screenshots/mvp-end-to-end/light/08-verify-budget-staged-edit.png) / [Dark](screenshots/mvp-end-to-end/dark/08-verify-budget-staged-edit.png); governed save [Light](screenshots/mvp-end-to-end/light/09-governed-save-changes.png) / [Dark](screenshots/mvp-end-to-end/dark/09-governed-save-changes.png); saved edit [Light](screenshots/mvp-end-to-end/light/10-verify-budget-saved-edit.png) / [Dark](screenshots/mvp-end-to-end/dark/10-verify-budget-saved-edit.png) |

## 5. Rules Repository demonstration

| Scenario | Required result | Evidence | Verdict |
|---|---|---|---|
| Inspect protected rule | Protected status; purpose, fields, keys, severity, version visible | Rule manifest/repository tests and final visual QA passed; [Light](screenshots/mvp-end-to-end/light/13-rules-core-list-and-detail.png) / [Dark](screenshots/mvp-end-to-end/dark/13-rules-core-list-and-detail.png) | **PASS** |
| Ordinary protected delete/disable | Action unavailable or governed-route explanation; no mutation | Protected mutation rejection is asserted in `test_optional_rule_lifecycle_is_versioned_tested_and_bound` | **PASS** |
| Request protected successor | Complete confirmed dataset, released evaluator qualification, immutable candidate/test/request, and request-time baseline | Application and migration tests passed; request [Light](screenshots/mvp-end-to-end/light/13a-protected-change-request.png) / [Dark](screenshots/mvp-end-to-end/dark/13a-protected-change-request.png); pending evidence `13b` | **PASS** |
| Independently decide protected successor | Different Financial Control Approver sees before/after definitions, content hash, qualification metrics, future effect, requester, and baseline; approval creates a new future baseline while existing workspaces stay pinned | Separation-of-duties, stale-baseline, authorization-evidence, migration, and replay tests passed; queue/approval/history sequence `13c`–`13e` | **PASS** |
| Adopt effective baseline in an existing workspace | Request is bound to the current Rule Set, completed Validation Run, source baseline, and exact target; a different actor approves; exactly five target protected bindings replace their predecessors; optional/advisory bindings, historical runs, and other workspaces remain unchanged | Migration 0012 trigger tests, application governance tests, authorization denial evidence, and NFR-090 audit-schema reconciliation passed; Light/Dark sequence `28a`–`28g` | **PASS** |
| Add optional Draft | Attributable Draft version | Rule-management lifecycle test passed; add/draft captures `14`/`15` in both directories | **PASS — automated** |
| Edit optional Draft | Updated Draft content without rewriting activated history | Rule-management lifecycle test passed; edit capture `16` in both directories | **PASS — automated** |
| Test Draft | Deterministic test result retained | Rule-management lifecycle test passed; test captures `17`/`18` in both directories | **PASS — automated** |
| Save/activate optional version | Immutable version and new Rule Set Version | Rule-management lifecycle test passed; activation capture `19` in both directories | **PASS — automated** |
| Disable optional rule | Successor Rule Set Version; prior version retained | Rule-management lifecycle test asserts successor binding contains five core rules | **PASS — automated** |
| Delete/retire optional rule | Governed lifecycle semantics, no historical erasure | Rule-management lifecycle test asserts retirement creates a successor core-only set | **PASS — automated** |
| Revalidate | Previous run preserved; successor Review Version/Validation Run and outcome visible | Reanalysis/history tests passed; governed baseline revalidation progress/results are captured in screens `28h`/`28i` and the optional-rule lifecycle remains captured in `14`–`19` | **PASS** |

## 6. Synthetic deterministic matrix

The complete expected matrix is [MVP Remediation Synthetic Test Matrix](../fixtures/MVP-REMEDIATION-SYNTHETIC-TEST-MATRIX-2026-07-28.md).

| Oracle group | Expected | Actual | Verdict |
|---|---:|---:|---|
| Budget detail population | 71 | **71** | **PASS** |
| GED transaction population | 258 | **258** | **PASS** |
| Rule scope results | 986 | **986** | **PASS** |
| PASS / FAIL / NOT_EVALUATED | 979 / 5 / 2 | **979 / 5 / 2** | **PASS** |
| Control findings | 5 | **5: CORE-01, CORE-02, CORE-04, CORE-05, CORE-03** | **PASS** |
| Four intentional source issues | Exact TEST-01 through TEST-04 behavior | **All four source issues produced the five expected cross-rule findings** | **PASS** |

The direct domain oracle does not allocate a persisted Validation Run ID. Final
sealed-run identity remains a demonstration item, not a gap in the asserted
financial values.

The screenshot demonstration activates one optional threshold rule. Its captured
ledger therefore has **1,244 rows = 986 protected baseline scopes + 258 optional
scopes**. The optional rule adds no finding, so the five protected findings and
the 986-result protected oracle above remain unchanged.

## 7. Evidence drill-down verification

| Finding/result | Required visible evidence and navigation | Actual | Verdict |
|---|---|---|---|
| Budget overrun | BGT, GED spend, overrun amount/percentage, Budget row and contributing GED records | Oracle: BGT `$1,100,000.00`, GED `$1,250,000.00`, overrun `$150,000.00`, `13.64%`; [Light](screenshots/mvp-end-to-end/light/26-validation-results-evidence.png) / [Dark](screenshots/mvp-end-to-end/dark/26-validation-results-evidence.png) | **PASS** |
| Duplicate | Both rows side by side with approved material fields and exact source references | Source records `GED:GED:65` / `GED:GED:66`, exposure `$82.50`; [Light](screenshots/mvp-end-to-end/light/27-findings-duplicate-evidence.png) / [Dark](screenshots/mvp-end-to-end/dark/27-findings-duplicate-evidence.png) | **PASS** |
| Missing Amount | Exact `GED!O87` cell highlighted and focused | Automated structured-evidence checks assert row `87`, field `amount`, cell `O87`, Original/Current `None`, and origin `Original`; GED chart/table projection is captured in screen `24` | **PASS — automated** |
| Invalid coding | Row 43 Department/Account cells and Budget-map expectation | Automated structured-evidence checks identify Department `00-0999` and unmapped GED `$1,850.00`; the complete GED projection remains available in screen `24` | **PASS — automated** |
| Reconciliation | Budget ATD, summed GED, difference, and contributors together | CORE-05 identifies Account `527015`, exact-key GED `$0.00`, difference `$1,850.00`; comparison captures `25` in both themes | **PASS** |
| Rule result | Rule purpose, scope counts, affected records, and View Evidence | Protected oracle is 986 scopes = 979 PASS / 5 FAIL / 2 NOT_EVALUATED; captured optional-rule run is 1,244 scopes with the same five findings | **PASS** |
| Missing source after reopen | Persisted evidence remains; raw-context action explains unavailability | Persistence/reopen behavior passed; final source-unavailable manual demonstration pending | **Automated persistence PASS; source-unavailable demonstration pending** |

## 8. Visual analytics verification

For every chart, verify that the accessible table contains the exact same sealed projection values.

| Page | Required visual | Projection/table equality | Accessibility | Screenshot | Verdict |
|---|---|---|---|---|---|
| Executive Overview | Budget/actual, severity, rule outcomes, utilization, account status, reconciliation | Engine-projected chart/table integration test passed | Exact-table alternative and focused accessibility QA passed | [Light](screenshots/mvp-end-to-end/light/22-executive-analytics.png) / [Dark](screenshots/mvp-end-to-end/dark/22-executive-analytics.png) | **PASS** |
| Budget Data | BGT, ATD, EAC, remaining/overrun by account | Engine-projected chart/table integration test passed | Exact-table alternative and focused accessibility QA passed | [Light](screenshots/mvp-end-to-end/light/23-budget-chart-and-evidence.png) / [Dark](screenshots/mvp-end-to-end/dark/23-budget-chart-and-evidence.png) | **PASS** |
| GED Data | Spend by account/period, highest-spend, transaction counts | Engine-projected chart/table integration test passed | Exact-table alternative and focused accessibility QA passed | [Light](screenshots/mvp-end-to-end/light/24-ged-charts-and-evidence.png) / [Dark](screenshots/mvp-end-to-end/dark/24-ged-charts-and-evidence.png) | **PASS** |
| Budget vs GED | Grouped BGT, ATD, GED, variance, overrun, reconciliation difference | Engine-projected chart/table integration test passed | Exact-table alternative and focused accessibility QA passed | [Light](screenshots/mvp-end-to-end/light/25-budget-ged-comparison-chart.png) / [Dark](screenshots/mvp-end-to-end/dark/25-budget-ged-comparison-chart.png) | **PASS** |
| Missing Amount state | Partial/incomplete label; no zero coercion | `ged_is_complete = false`; CORE-01/05 each have one NOT_EVALUATED scope | Non-color `Incomplete`/NOT_EVALUATED text passed automated and visual QA | Coverage [Light](screenshots/mvp-end-to-end/light/28-data-quality-and-coverage.png) / [Dark](screenshots/mvp-end-to-end/dark/28-data-quality-and-coverage.png) | **PASS** |

## 9. Review-disposal verification

| Check | Required result | Actual | Verdict |
|---|---|---|---|
| Permission | Unauthorized actor denied; review unchanged | Application disposal test passed | **PASS** |
| Cancel | No review data or tombstone removed/created | Cancel/reused-token test passed | **PASS** |
| Confirmation | One-time, actor-bound, review-bound, stale-safe | Bound-token and cross-review rejection tests passed | **PASS** |
| Lifecycle coverage | Draft, Data Uploaded/in progress, Validation Complete, Closed/completed | Parameterized lifecycle disposal test passed | **PASS** |
| Two-review isolation | Target absent; unrelated review byte-for-byte/logically intact | Two-review isolation test passed | **PASS** |
| Shared records | Referenced shared rule/source records retained | Shared-artifact/rule retention assertions passed | **PASS** |
| External workbooks | Files still exist with identical bytes | External source preservation assertion passed | **PASS** |
| Receipt | Exact per-table inventory and opaque tombstone | Receipt/inventory and content-free audit assertions passed | **PASS** |
| Audit integrity | Target review stream retired; remaining streams verify after restart | External-anchor retirement/restart test passed | **PASS** |
| Interrupted publication | Committed tombstone reconciles external disposal state | Injected external-commit failure reconciliation test passed | **PASS** |
| Managed backup/key erasure | Not implemented in this remediation | Live-store scoped disposal is implemented; forensic SQLite page/WAL and prior-backup erasure are not claimed | **KNOWN LIMITATION** |

## 10. Appearance and design-consistency review

Final primary captures are 1280 × 900. Every state was also recaptured at
1180 × 860 under
[responsive Light](../../../artifacts/design-qa/final-1180x860/light/) and
[responsive Dark](../../../artifacts/design-qa/final-1180x860/dark/). The focused
review and five same-viewport comparisons are recorded in
[design-qa.md](../../../design-qa.md).

| Screen/state | Light | Dark | System Default behavior | Visual-review result |
|---|---|---|---|---|
| Welcome — empty | [01 Light](screenshots/mvp-end-to-end/light/01-welcome.png) | [01 Dark](screenshots/mvp-end-to-end/dark/01-welcome.png) | System resolved to Light headlessly; automated OS-following test passed | **PASS** |
| Settings / Appearance | [01a Light](screenshots/mvp-end-to-end/light/01a-settings-appearance.png) | [01a Dark](screenshots/mvp-end-to-end/dark/01a-settings-appearance.png) | Shared preference persistence and OS-following tests passed | **PASS** |
| Welcome — recent reviews | [30 Light](screenshots/mvp-end-to-end/light/30-past-reviews.png) | [30 Dark](screenshots/mvp-end-to-end/dark/30-past-reviews.png) | Automated theme propagation passed | **PASS** |
| Create Review + error | [02/02a Light](screenshots/mvp-end-to-end/light/02a-create-review-required-error.png) | [02/02a Dark](screenshots/mvp-end-to-end/dark/02a-create-review-required-error.png) | Automated theme propagation passed | **PASS** |
| Upload ready and error presentation | [04 Light](screenshots/mvp-end-to-end/light/04-upload-ready.png) | [04 Dark](screenshots/mvp-end-to-end/dark/04-upload-ready.png) | Theme propagation and failure-presentation tests passed | **PASS** |
| Verify Data edit mode | [08 Light](screenshots/mvp-end-to-end/light/08-verify-budget-staged-edit.png) | [08 Dark](screenshots/mvp-end-to-end/dark/08-verify-budget-staged-edit.png) | Automated theme propagation passed | **PASS** |
| Save Changes dialog | [09 Light](screenshots/mvp-end-to-end/light/09-governed-save-changes.png) | [09 Dark](screenshots/mvp-end-to-end/dark/09-governed-save-changes.png) | Automated theme propagation passed | **PASS** |
| Rules Repository | [13 Light](screenshots/mvp-end-to-end/light/13-rules-core-list-and-detail.png) | [13 Dark](screenshots/mvp-end-to-end/dark/13-rules-core-list-and-detail.png) | Automated theme propagation passed | **PASS** |
| Protected governance queue and history | [13c Light](screenshots/mvp-end-to-end/light/13c-protected-change-approver-queue.png) / [13e Light](screenshots/mvp-end-to-end/light/13e-protected-change-approved-history.png) | [13c Dark](screenshots/mvp-end-to-end/dark/13c-protected-change-approver-queue.png) / [13e Dark](screenshots/mvp-end-to-end/dark/13e-protected-change-approved-history.png) | Global shell route, decision controls, and theme propagation passed | **PASS** |
| Workspace baseline governance and revalidation | [28a Light](screenshots/mvp-end-to-end/light/28a-workspace-upgrade-available.png), [28d Light](screenshots/mvp-end-to-end/light/28d-workspace-upgrade-approver-queue.png), [28f Light](screenshots/mvp-end-to-end/light/28f-workspace-upgrade-applied-history.png), [28g Light](screenshots/mvp-end-to-end/light/28g-workspace-upgrade-revalidation-required.png) | [28a Dark](screenshots/mvp-end-to-end/dark/28a-workspace-upgrade-available.png), [28d Dark](screenshots/mvp-end-to-end/dark/28d-workspace-upgrade-approver-queue.png), [28f Dark](screenshots/mvp-end-to-end/dark/28f-workspace-upgrade-applied-history.png), [28g Dark](screenshots/mvp-end-to-end/dark/28g-workspace-upgrade-revalidation-required.png) | Pure-role global route, modal focus, evidence panel, compact immutable-ID lists, and deterministic revalidation action passed at both desktop widths | **PASS** |
| Rule add/edit/test | Light sequence [14](screenshots/mvp-end-to-end/light/14-optional-rule-add.png), [16](screenshots/mvp-end-to-end/light/16-optional-rule-edit.png), [17](screenshots/mvp-end-to-end/light/17-optional-rule-test-result.png) | Dark sequence [14](screenshots/mvp-end-to-end/dark/14-optional-rule-add.png), [16](screenshots/mvp-end-to-end/dark/16-optional-rule-edit.png), [17](screenshots/mvp-end-to-end/dark/17-optional-rule-test-result.png) | Automated theme propagation passed | **PASS** |
| Executive Overview charts | [22 Light](screenshots/mvp-end-to-end/light/22-executive-analytics.png) | [22 Dark](screenshots/mvp-end-to-end/dark/22-executive-analytics.png) | Automated chart theme refresh passed | **PASS** |
| Validation Results evidence | [26 Light](screenshots/mvp-end-to-end/light/26-validation-results-evidence.png) | [26 Dark](screenshots/mvp-end-to-end/dark/26-validation-results-evidence.png) | Automated theme propagation passed | **PASS** |
| Findings duplicate/reconciliation | [27 Light](screenshots/mvp-end-to-end/light/27-findings-duplicate-evidence.png) | [27 Dark](screenshots/mvp-end-to-end/dark/27-findings-duplicate-evidence.png) | Automated theme propagation passed | **PASS** |
| Data Quality & Coverage | [28 Light](screenshots/mvp-end-to-end/light/28-data-quality-and-coverage.png) | [28 Dark](screenshots/mvp-end-to-end/dark/28-data-quality-and-coverage.png) | Automated theme propagation passed | **PASS** |
| Delete Review dialog | [32 Light](screenshots/mvp-end-to-end/light/32-delete-review-confirmation.png) | [32 Dark](screenshots/mvp-end-to-end/dark/32-delete-review-confirmation.png) | Automated theme propagation passed | **PASS** |
| Past Reviews / reopened results | [31 Light](screenshots/mvp-end-to-end/light/31-reopened-results.png) | [31 Dark](screenshots/mvp-end-to-end/dark/31-reopened-results.png) | Preference persistence/restart test passed | **PASS** |

Focused design review recorded:

- Welcome hierarchy;
- navigation consistency;
- card alignment and form density;
- table readability;
- chart clarity;
- error-message presentation;
- Rules Repository;
- evidence views;
- delete dialog;
- Light/Dark/System consistency;
- keyboard focus; and
- zoom/resizing.

## 11. Accessibility verification

| Check | Tool/method | Result | Evidence |
|---|---|---|---|
| Complete keyboard journey | Automated accessibility/UI suite | Focus/order assertions passed | 41-test focused suite below |
| Focus visibility and restoration | Automated appearance/UI suite + focused visual review | Focus styling/navigation/restoration assertions and visual review passed | Light/Dark captures and test suite |
| Accessible names/descriptions | Automated accessibility suite | Passed | `tests/accessibility/` |
| Dialog focus/trap/escape | Automated UI tests + focused visual review | Save/delete dialog paths and safe default focus passed | Screens `09` and `32` |
| Status not color-only | Automated text assertions + visual review | Explicit PASS/FAIL/NOT_EVALUATED, severity, edited, and required labels passed | Results/coverage/error captures |
| Chart labels and table alternatives | Integrated UI tests + visual review | Exact table alternatives, label legibility, and chart theme passed | Screens `22`–`25` |
| Light/Dark contrast | Theme tests + visual review | Authored contrast checks and all 96 primary captures passed | Both 48-screen directories |
| OS scaling / application zoom | Focused UI/accessibility test at 200% | Passed | 41-test focused suite |
| Window resizing / no clipping | 96 responsive captures at 1180 × 860 | Passed; no material clipping or overlap remains | `artifacts/design-qa/final-1180x860/` |
| Screen-reader/native accessibility smoke | Manual native check | Not performed in the headless environment | **PENDING HANDS-ON ITEM** |

## 12. Automated and engineering checks

| Command/check | Exact command | Result |
|---|---|---|
| Full regression | `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q` | **PASS — 1,019 passed in 68.36s on the terminal remediation state** |
| Focused accessibility, appearance, and governance UI | `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/ui/test_appearance.py tests/accessibility tests/ui/test_protected_rule_governance.py` | **PASS — 41 passed in 15.49s** |
| Focused workspace-upgrade seam | `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/application/test_protected_rule_governance.py tests/application/test_authorization.py tests/security/test_workspace_baseline_upgrade_security.py tests/migrations/test_migration_0012.py tests/migrations/test_migrations.py tests/ui/test_protected_rule_governance.py` | **PASS — 50 passed in 5.84s; includes production composed-role DENY/no-ALLOW evidence and transition-specific NFR-090 schemas** |
| Focused governance re-audit | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q tests/application/test_protected_rule_governance.py tests/application/test_authorization.py tests/application/test_rule_management.py tests/application/test_financial_review.py tests/migrations/test_migration_0012.py tests/security/test_workspace_baseline_upgrade_security.py tests/ui/test_protected_rule_governance.py tests/ui/test_integrated_financial_review.py tests/accessibility --disable-warnings` | **PASS — 66 passed in 23.21s; exact NFR-090 schemas/counts, one DENY/zero ALLOW self-decision evidence, five protected bindings, preserved history/other workspaces, Reviewer revalidation, pure-role UI, and accessibility verified** |
| Rule oracle | `.venv/bin/pytest -q tests/unit/test_financial_validation.py` (also included in focused/full runs) | **PASS — 71 Budget, 258 GED, 986 scopes = 979 PASS / 5 FAIL / 2 NOT_EVALUATED; five findings** |
| UI/accessibility | Focused Qt offscreen accessibility/appearance/governance suite plus final 48-state Light/Dark and responsive visual QA | **PASS for implemented scope; native screen-reader smoke remains a hands-on item** |
| Persistence/migrations/disposal | Focused application, migration, repository, governance, and disposal selections | **PASS in recorded focused/full runs, including schema 12, append-only protected workspace-upgrade governance, and governed review disposal** |
| Import architecture | `PYTHONPATH=src .venv/bin/lint-imports --config .importlinter --no-cache` | **PASS — 3 contracts kept, 0 broken across 217 files / 898 dependencies** |
| Ruff | Ruff over every changed/untracked remediation Python file except the identified historical migration test | **PASS — every remediation-touched or newly authored Python file is clean.** |
| Dependency integrity/minimums | `.venv/bin/python -m pip check` | **PASS — no broken requirements found** |
| Python compilation | `.venv/bin/python -m compileall -q src tests scripts` | **PASS** |
| Git whitespace | `git diff --check` | **PASS** |
| Launch/restart smoke | Launcher opened twice against the same temporary persistent store | **PASS — the same store reopened successfully; saved-review persistence is covered by the integrated completion/reopen test** |

Do not omit failing or skipped tests. Record whether any failure is pre-existing, newly introduced, or unresolved.

## 13. Independent review

- Review record: [Independent Review — MVP Final Remediation](../reviews/REVIEW-2026-07-28-mvp-final-remediation.md)
- Reviewer identity: Codex independent review agent `/root/independent_final_review`
- Initial verdict: **FAIL — two Major defects**
- Material findings: **IR-01 missing Settings destination; IR-02 missing protected baseline governance**
- Repair/recheck: **IR-01 closed on the intermediate recheck; IR-02 closed after governed existing-workspace baseline adoption and successor revalidation were added**
- Final independent evidence: **82 passed in 24.00s; 96 independent screenshots (48 Light + 48 Dark); exact 843-file snapshot/digest match; no remaining material finding**
- Final verdict: **PASS**

## 14. Launch instructions

From the repository root:

```bash
.venv/bin/python scripts/launch_mvp_demo.py --data-dir artifacts/mvp-hands-on-store
```

The demo uses the approved synthetic Budget and GED fixtures under
`initiatives/configurable-rule-engine-v2/fixtures/`. The supplied data directory
is persistent: reviews and audit state remain available after closing and
reopening the application. This is test data only; Windows packaging is not part
of this remediation gate.

## 15. Known limitations

- Windows packaging, signing, installer creation, and native Windows
  qualification remain outside this gate by explicit scope.
- Source support remains limited to the approved `.xlsx` Budget/GED layouts.
- Ask Fin remains bounded to product help and persisted-result explanations.
- If original source files are unavailable, sealed results/evidence remain, but
  raw reconstructed source-row context may be unavailable.
- Live-store review disposal does not claim forensic erasure of SQLite pages/WAL
  or previously created backups; retained-store/key destruction and backup
  revocation are not implemented in this remediation.
- Shared source-artifact provenance remains when another review still references
  the same artifact.
- System Default resolved to Light in the headless environment. Live
  operating-system appearance switching is automated but was not manually
  observable headlessly.
- Native screen-reader smoke and Project Owner hands-on acceptance remain
  pending.

## 16. Gate statement

**Current statement:** Internal automated, deterministic, governance,
visual-design, and accessibility verification passed for the implemented
remediation scope. The bounded independent review passed with IR-01 and IR-02
closed and no remaining material finding. Project Owner hands-on acceptance and
native screen-reader smoke remain hands-on items. This package does not authorize
Windows packaging.
