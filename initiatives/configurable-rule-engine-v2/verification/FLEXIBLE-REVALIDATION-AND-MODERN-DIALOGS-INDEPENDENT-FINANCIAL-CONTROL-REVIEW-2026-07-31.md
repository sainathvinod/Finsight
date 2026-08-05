# Flexible Revalidation and Modern Dialogs — Independent Financial-Control Review

**Review date:** 2026-07-31  
**Review type:** Independent financial-control, governance, audit, and replay review  
**Verdict:** **PASS**

## Executive Verdict

The Flexible Revalidation correction passes independent financial-control review.

The completed implementation:

- pins each validation attempt to the exact reviewed dataset and immutable Rule Set Version confirmed by the actor;
- allocates one stable Validation Run ID before deterministic execution and retains it through confirmation, start, completion, or failure;
- executes only enabled members of the confirmed Rule Set;
- prevents Draft, Disabled, Retired, stale, hidden, or unconfirmed rules from entering the deterministic manifest;
- keeps all five protected baseline rules mandatory and routes successor changes through governed, separated duties;
- preserves prior Validation Runs and their sealed results;
- records successor revalidation as **Working** without silently replacing the prior **Published** generation;
- produces deterministic run-to-run comparison evidence;
- prevents an asynchronous result for one review from being presented as the result of another active review; and
- continues to match the independent financial oracle for the supplied Budget and GED fixtures.

No material financial-control defect remains in the reviewed scope.

## Scope

The independent review covered:

- direct revalidation from a completed review using the retained verified working data;
- same-Rule-Set reruns;
- exact pre-validation Rule Set confirmation;
- source-data, rule-version, configuration, actor, timestamp, prior-run, and new-run identity;
- Draft exclusion and fail-closed Draft handling;
- optional-rule creation, versioning, testing, activation, disablement, retirement, and supersession;
- protected-core-rule governance and ordinary-user restrictions;
- immutable execution-manifest construction;
- deterministic evaluation and persisted result ledgers;
- failed-attempt retention;
- prior-run preservation, historical replay, and run comparison;
- Working versus Published generation handling;
- audit coverage for revalidation and validation-attempt transitions;
- active-review isolation during asynchronous execution; and
- the Stage 1 independent financial oracle and five core-rule control matrix.

The modern-dialog visual and accessibility implementation was independently assessed in the companion UX review. Packaging was intentionally outside this task.

## Financial-Control Evidence

### 1. Verified working data is reused, but changed data fails closed

- `src/finsight/application/financial_review.py:348-379` records direct revalidation entry with the prior Run ID, prior Rule Set ID, verified source generation, and dataset fingerprint.
- `src/finsight/application/financial_review.py:381-401` requires the supplied dataset fingerprint to match the retained verified generation and restricts proposal creation to valid reviewed lifecycle states.
- `src/finsight/application/financial_review.py:807-867` rechecks review ownership, actor identity, dataset fingerprint, source generation, current Rule Set, prior Run ID, readiness, exact rules, and Draft dispositions immediately before execution.

**Assessment:** PASS. Revalidation avoids unnecessary re-upload or reverification while remaining fail-closed when its governed basis changes.

### 2. Exact Rule Set confirmation is sealed and auditable

- `src/finsight/application/financial_review.py:420-618` builds the review-local proposal from immutable Rule Set members and definition versions, including Rule IDs, versions, status, severity, evaluator key, parameters, required fields, grouping keys, and content hashes.
- `src/finsight/application/financial_review.py:620-702` rejects a stale proposal hash, allocates the Run ID, records source-data version, prior Run ID, rules, Draft exclusions, changes, actor, timestamp, and confirmation hash, and appends the `CONFIRMED` audit event.
- `src/finsight/infrastructure/financial_review_repository.py:54-92` constructs the executable manifest only from the immutable workspace Rule Set members whose stored `enabled` flag is true.
- `src/finsight/domain/financial_validation.py:278-327` validates stable ordering, unique Rule IDs, all protected baseline rules, certified core evaluators, supported classifications, allowlisted optional evaluator behavior, and valid exact financial thresholds.

**Assessment:** PASS. The engine receives the same exact enabled rules that the user confirmed; presentation logic does not add financial checks.

### 3. Stable Run identity exists before execution

- `src/finsight/application/financial_review.py:637-679` allocates one `run_id` during confirmation and places it on the confirmation and `CONFIRMED` event.
- `src/finsight/application/financial_review.py:704-756` carries the same ID into `STARTED`.
- `src/finsight/application/financial_review.py:758-805` carries the same ID into `FAILED`, while preserving the prior completed result.
- `src/finsight/application/financial_review.py:975-979` uses the confirmation Run ID for the persisted deterministic result.
- `src/finsight/application/financial_review.py:1263-1305` records the same ID in `COMPLETED`, the prior/new relationship, comparison summary, publication state, ledger hash, and completion seal.
- `src/finsight/infrastructure/migrations/m0016_validation_run_identity.py:24-63` upgrades existing confirmation evidence with an immutable Run identity and requires it for new confirmations.
- `src/finsight/infrastructure/migrations/m0016_validation_run_identity.py:65-119` requires every attempt event to carry the matching confirmation Run ID and retains append-only protection.

**Assessment:** PASS. Confirmation, execution, failure evidence, and successful sealed results share one immutable attempt identity.

### 4. Draft and optional-rule behavior is deterministic and versioned

- `src/finsight/application/rule_management.py:207-269` records explicit review-local Draft exclusion/restoration with actor, time, reason, hash, and audit event.
- `src/finsight/application/rule_management.py:325-419` tests the exact Draft version against the reviewed dataset without changing review results.
- `src/finsight/application/rule_management.py:421-486` requires an exact successful test before activation, supersedes an optional predecessor, creates a successor Rule Set, and audits the binding.
- `src/finsight/application/rule_management.py:488-561` creates versioned Rule Sets for disablement, enablement, and retirement while retaining prior definitions and results.
- `src/finsight/infrastructure/financial_review_repository.py:366-379` distinguishes a predecessor retired because of successor activation as the plain-language **Superseded** status.
- `src/finsight/application/financial_review.py:471-518` blocks unresolved Draft/Tested candidates but permits an explicitly excluded Draft; `src/finsight/application/financial_review.py:495-512` independently verifies that the five protected rules remain included.

**Assessment:** PASS. Draft rules never execute silently, explicit exclusion does not block validation, and optional changes produce immutable successor Rule Sets.

### 5. Protected core rules remain governed baseline controls

- `src/finsight/application/rule_management.py:1450-1463` rejects every optional-rule mutation attempted against a `CORE-*` Rule ID.
- `src/finsight/application/rule_management.py:930-1040` enforces two-person protected-change approval, terminal decisions, baseline concurrency checks, immutable successor activation, predecessor retirement, and complete governance audit.
- `src/finsight/domain/financial_validation.py:287-307` refuses a manifest missing a core rule, misclassifying a core rule, or substituting an uncertified evaluator.
- `tests/application/test_protected_rule_governance.py:346-433` verifies immutable tested requests, no pre-approval baseline change, and rejection of incomplete or unconfirmed qualification data.

**Assessment:** PASS. Ordinary actions cannot delete, disable, or replace a protected control, while the approved governed successor path remains available.

### 6. Historical results remain reproducible and successor results remain Working

- `src/finsight/application/financial_review.py:1081-1195` creates a new rule-set-reanalysis generation based on the verified source generation and persists a new immutable Validation Run without mutating the predecessor.
- `src/finsight/application/financial_review.py:1193-1216` leaves a successor reanalysis in **Working**, retains the prior Published pointer, and does not silently supersede it.
- `src/finsight/infrastructure/financial_review_repository.py:1688-1883` persists separate run, execution, scope-result, finding, explanation, status, and leadership-summary records.
- `src/finsight/infrastructure/financial_review_repository.py:2295-2306` derives Published, Working, or Historical state from retained generation pointers.
- `src/finsight/infrastructure/financial_review_repository.py:2375-2388` reconstructs the complete retained run history.

**Assessment:** PASS. New analysis is reviewable without silently changing the trusted Published generation; prior sealed results remain replayable.

### 7. Comparison and audit evidence cover the material changes

- `src/finsight/infrastructure/financial_review_repository.py:2390-2553` compares rules added, removed, changed, and unchanged; rule status and version changes; findings added, removed, resolved, changed, and unchanged; finding-review status; and optional-rule effects.
- `src/finsight/application/financial_review.py:1233-1331` returns the comparison and appends completion and comparison audit records with prior/new Run IDs, Rule Set IDs, publication state, actor, timestamp, and summary counts.
- `src/finsight/infrastructure/migrations/m0015_validation_rule_set_confirmation.py:16-111` establishes append-only Draft-disposition, confirmation, attempt-event, and confirmation-to-run ledgers, with governed whole-review disposal as the only explicit deletion exception.

**Assessment:** PASS. The retained records are sufficient to reproduce and explain which rule change caused which result change.

### 8. Active-review isolation is preserved during asynchronous validation

- `src/finsight/delivery/desktop/controllers/app_controller.py:405-484` binds persistence to the originating review, emits origin-scoped change signals, and suppresses stale success or error callbacks after the active review changes.
- `src/finsight/delivery/desktop/views/financial_review_view.py:5789-5855` independently binds presentation callbacks to the initiating review and ignores callbacks after navigation to another review.
- `tests/ui/test_validation_async_review_isolation.py:55-152` verifies that a result remains persisted to review A but cannot be presented as review B.

**Assessment:** PASS. No cross-review presentation or result-association defect remains in the reviewed asynchronous path.

### 9. Financial results still match the independent oracle

- `tests/integration/test_stage1_financial_oracle.py:6-33` runs the independent OOXML oracle with no FinSight implementation dependency and requires every totals, row, known-issue, and rule control to pass.
- `tests/unit/test_financial_validation.py:42-63` verifies all five protected-rule execution counts and statuses.
- `tests/unit/test_financial_validation.py:66-138` verifies the exact five findings, source evidence, totals, severity counts, missing amount, duplicate, invalid mapping, overrun, and reconciliation behavior.
- `tests/unit/test_financial_validation.py:241-317` verifies exact Decimal totals and Budget/GED row inclusion and exclusion controls.

Verified fixture totals remain:

- BGT: `$10,372,000.00`
- ATD: `$3,500,095.00`
- ETC: `$5,882,000.00`
- EAC: `$9,382,095.00`
- DELTA: `$989,905.00`
- parseable GED Amount total: `$3,500,095.00` with the approved missing-amount incompleteness retained

**Assessment:** PASS. Revalidation did not change calculation semantics, Decimal arithmetic, source-row treatment, or the five protected rules.

## Material Findings Found and Resolved During Review

| ID | Finding | Resolution | Verification |
|---|---|---|---|
| FC-01 | Activating an edited optional version originally left its predecessor without an explicit Superseded lifecycle state. | Activation now appends a `RETIRED` event with a `SUPERSEDED_BY_<version>` reason and exposes **Superseded** as the display status. | `src/finsight/application/rule_management.py:433-480`; `src/finsight/infrastructure/financial_review_repository.py:366-379`; `tests/application/test_rule_management.py:376-444` |
| FC-02 | Successor reanalysis originally advanced publication automatically, contrary to the approved Working-before-promotion lifecycle. | A successor is now retained as Working; the prior Published pointer remains and no generation supersession is created. | `src/finsight/application/financial_review.py:1193-1216`; `tests/application/test_rule_management.py:101-171` |
| FC-03 | The original attempt ledger did not allocate a new Run ID until successful persistence, leaving start/failure evidence without the required new-run identity. | Migration 16 adds stable pre-execution Run identity and enforces that all confirmation/attempt events use the same ID. | `src/finsight/infrastructure/migrations/m0016_validation_run_identity.py:24-119`; `tests/migrations/test_migration_0016.py:11-58`; `tests/application/test_rule_management.py:121-170,330-373` |
| FC-04 | A late asynchronous callback could persist correctly to review A but be delivered while review B was active. | Origin-bound controller and view guards now suppress stale callbacks while preserving the originating review's persisted result and signals. | `src/finsight/delivery/desktop/controllers/app_controller.py:405-484`; `src/finsight/delivery/desktop/views/financial_review_view.py:5789-5855`; `tests/ui/test_validation_async_review_isolation.py:55-152` |

All four material findings were corrected before this verdict and passed focused and full regression verification.

## Automated Verification

Independent focused financial-control command:

```text
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q \
  tests/application/test_rule_management.py \
  tests/application/test_protected_rule_governance.py \
  tests/application/test_financial_review.py \
  tests/migrations/test_migration_0015.py \
  tests/migrations/test_migration_0016.py \
  tests/integration/test_stage1_financial_oracle.py \
  tests/unit/test_financial_validation.py \
  tests/ui/test_revalidation_rules_workflow.py \
  tests/ui/test_validation_async_review_isolation.py
```

Result:

```text
65 passed in 23.33s
```

Final governed regression after all corrections:

```text
1300 passed, 1 skipped, 2 subtests passed in 186.40s
```

Additional settled verification:

```text
Migration/schema-head focused checks: 12 passed
Ruff: PASS
```

The one declared skip did not represent a failure in the reviewed financial-control path.

## Residual Notes

- This verdict does not approve Windows packaging or deployment; the request explicitly stops before packaging.
- This review confirms the corrected Working/Published separation. Governed promotion remains a distinct lifecycle action and must not be bypassed by revalidation.
- Platform screen-reader behavior is covered by the companion UX review's stated hands-on limitation and does not alter this financial-control verdict.

## Independent Verdict

**PASS.** The reviewed implementation satisfies the Flexible Revalidation financial-control acceptance criteria. Exact Rule Set execution, protected baseline governance, immutable pre-execution Run identity, deterministic result persistence, prior-run preservation, Working/Published separation, run comparison, auditability, active-review isolation, and independent financial correctness all pass. No material financial-control defect remains.
