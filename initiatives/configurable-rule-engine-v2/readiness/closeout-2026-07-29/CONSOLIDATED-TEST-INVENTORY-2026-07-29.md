# FinSight Consolidated Test Inventory and Financial-Correctness Closeout

**Date:** 2026-07-29
**Reviewer scope:** deterministic finance, rule engine, result persistence/history,
architecture/code quality, and consolidated automated-test evidence
**Review mode:** read-only; no production code was changed
**Verdict:** **FAIL — not ready for packaging**

## 1. Executive conclusion

The current application has substantial, useful automated coverage and the supplied
May 2026 synthetic fixture still reproduces its expected totals and four intentional
source-data scenarios. The latest repository state is nevertheless not a releasable
financial baseline:

1. the current full suite is red: **4 failed, 1,212 passed, 2 subtests passed**;
2. the engine's CORE-04 behavior and Stage 1 oracle contradict the approved CORE-04
   contract;
3. the overall-status and RAG projector violates the approved core-only status policy;
4. CORE-03 miscalculates exposure and summary counts for duplicate groups larger than
   two;
5. valid but out-of-review-period GED rows are included in CORE-01 and CORE-05 sums;
6. the production composition still builds a legacy financial engine and legacy result
   shell alongside the V2 deterministic engine; and
7. nearly all V2 work remains uncommitted in a very large dirty worktree, so there is no
   immutable release-candidate revision to reproduce.

A governed stabilization and regression stage is mandatory before packaging.

## 2. Current automated inventory

Collection command:

```text
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest --collect-only -q
```

Result: **1,216 tests collected in 0.34 seconds**, across **127 test files**.

| Test area (directory) | Files | Collected cases |
|---|---:|---:|
| AI / Ask Fin | 24 | 440 |
| UI | 21 | 237 |
| Application services | 24 | 177 |
| Infrastructure | 14 | 135 |
| Migrations | 15 | 75 |
| Unit | 7 | 52 |
| Fitness / architecture | 5 | 52 |
| Accessibility | 4 | 20 |
| Integration | 3 | 8 |
| Security | 2 | 8 |
| Root-level workflow/security tests | 5 | 9 |
| Crash safety | 1 | 1 |
| Determinism | 1 | 1 |
| Golden | 1 | 1 |
| **Total** | **127** | **1,216** |

The directory categories are more reliable than pytest markers: markers exist in
`pyproject.toml`, but coverage is not consistently marked by test type.

### Platform skips and expected failures

No `xfail` declarations were found. Three tests use `skipif(os.name != "posix")`:

- `tests/infrastructure/test_secure_store.py` — POSIX group-permission profile;
- `tests/infrastructure/test_disposal_registry.py` — POSIX permission contract;
- `tests/infrastructure/test_disposal_registry.py` — POSIX group-permission contract.

They execute on the current macOS host but will be skipped on Windows. Therefore the
current suite does **not** prove a Windows equivalent for those permission controls.

## 3. Tests executed during closeout

| Check | Exact command | Result |
|---|---|---|
| Current full repository suite | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q` | **FAIL — 4 failed, 1,212 passed, 2 subtests passed in 81.98s** |
| Four failing tests, isolated | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q tests/ui/test_appearance.py::test_header_appearance_entry_points_fit_at_two_hundred_percent_text_scaling tests/ui/test_appearance.py::test_settings_is_a_keyboard_accessible_shell_destination tests/ui/test_ask_fin_setup_and_drawer.py::test_main_window_hosts_non_modal_drawer_without_setup_workflow tests/ui/test_desktop.py::test_ui_code_has_no_sqlite_or_repository_imports` | **FAIL — 3 failed, 1 passed in 1.62s** |
| Current Stage 1 oracle/core/rules/history selection | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q tests/integration/test_stage1_financial_oracle.py tests/unit/test_financial_validation.py tests/application/test_rule_management.py tests/application/test_financial_review.py` | **PASS — 29 passed in 4.94s** |
| Independent OOXML/Decimal oracle | `.venv/bin/python scripts/verify_stage1_financial_oracle.py --compact` | **PASS for its encoded expectations** |
| Import contracts | `PYTHONPATH=src .venv/bin/lint-imports` | **PASS — 235 files, 1,008 dependencies, 3/3 contracts kept** |
| Focused Ruff | `.venv/bin/ruff check src/finsight/domain/financial_validation.py src/finsight/domain/finding_explanations.py src/finsight/application/financial_review.py src/finsight/infrastructure/financial_review_repository.py src/finsight/delivery/desktop/views/financial_review_view.py src/finsight/delivery/desktop/components/charts.py` | **PASS** |
| Whitespace patch check | `git diff --check` | **PASS** |
| Integrated launch smoke | `QT_QPA_PLATFORM=offscreen FINSIGHT_SMOKE=1 .venv/bin/python scripts/launch_mvp_demo.py --data-dir <temporary-directory>` | **PASS — clean launch and exit** |

### Current full-suite failures

| Failure | Reproduction | Classification | Release action |
|---|---|---|---|
| Appearance selector clips at 200% text scale (`135 < 144`) | Fails in full and isolated runs | Accessibility defect | **Must fix before packaging** |
| Settings Back button has `NoFocus` | Fails in full and isolated runs | Accessibility defect | **Must fix before packaging** |
| Ask Fin drawer rendered at width 169 instead of at least 360 | Fails in full run; passes in isolated four-test run | Order-dependent/brittle UI behavior or test isolation defect | **Must fix before packaging** and add stable open-animation completion assertion |
| `delivery/desktop/ask_fin_preferences.py` imports `finsight.infrastructure` | Fails in full and isolated runs | Architecture dependency defect | **Must fix before packaging** |

The import-linter result does not negate the last failure. The current import-linter
contracts omit infrastructure from the declared layer stack, while the targeted UI
fitness test enforces the stricter approved boundary. The contract configuration should
be strengthened so the two checks cannot disagree.

## 4. Historical verification evidence

| Stage | Recorded verification |
|---|---|
| Workflow 1 | 861 full-suite passes; focused 154 and 20 passes |
| Workflow 2 | 926 full-suite passes; focused 65 and Workflow 1 regression 20 |
| MVP end-to-end | 940 full-suite passes |
| MVP final remediation | 1,019 full-suite passes; focused 41, 50, 66; independent 82 |
| Stage 1 | 1,042 full-suite passes in 75.43s; focused 30 |
| Stage 2 consolidated | **latest previously recorded clean full suite: 1,190 passes in 77.02s**; focused UI/accessibility 18; privacy/security 465; Ask Fin 103 |
| Stage 2 follow-up | focused 261 and 59 passes; explicitly no full regression |
| Ask Fin simplification | focused 200 + 2 subtests, then 56 + 2 subtests; launch smoke; no full regression |
| Current closeout | **4 failed, 1,212 passed, 2 subtests passed** |

`test-results.txt` contains only `23 passed in 0.20s`; it is stale smoke evidence and
must not be described as the current suite result.

## 5. Synthetic fixture and arithmetic reconfirmation

The independent verifier imports neither FinSight nor a spreadsheet library. It reads
OOXML directly and uses `Decimal`. Its current fixture facts still pass:

| Control | Verified value |
|---|---:|
| Budget detail records | 71 |
| GED transactions | 258 |
| BGT | $10,372,000.00 |
| ATD | $3,500,095.00 |
| ETC | $5,882,000.00 |
| EAC | $9,382,095.00 |
| DELTA | $989,905.00 |
| Parseable GED Amount | $3,500,095.00 |
| Mapped GED Amount | $3,498,245.00 |
| Unmapped GED Amount | $1,850.00 |
| Account 555035 overrun | $150,000.00 |
| Exact duplicate rows | GED 65 and 66, $82.50 each |
| Missing required Amount | GED O87 |
| Unmapped transaction | GED row 43, `00-0999 + 527015`, $1,850.00 |
| Consequential CORE-05 difference | `00-0245 + 527015`, $1,850.00 |

Money parsing and core arithmetic in `domain/financial_validation.py` use `Decimal`,
reject non-finite/scientific/overprecision inputs, quantize to two places, and project
integer cents plus exact labels. Charts convert cents to `float` only for visual
coordinates; exact labels and accessible tables consume recorded labels. No inspected
Ask Fin or presentation path creates authoritative financial pass/fail values.

This fixture pass is necessary but not sufficient: the independent verifier duplicates
several implementation assumptions that conflict with the approved specification, as
described below.

## 6. Material financial and rule-contract defects

### FC-01 — CORE-04 silently includes Budget formula controls

**Classification:** Must fix before packaging — material specification defect.

Approved V2 requirements define CORE-04 as one scope per GED transaction and exactly
six required GED fields:

- `specs/01-functional-requirements.md` §2.7, FR-162, §11.4, and §12;
- `docs/RULE-ENGINE-DESIGN.md` §10.

Implementation at `src/finsight/domain/financial_validation.py:1083`–`1188` adds one
CORE-04 scope for every Budget detail row, validates BGT/ATD/ETC/EAC/DELTA, and performs
EAC/DELTA formula checks. That changes the protected control without a governed
protected-rule version.

The manual oracle and independent script were then authored to expect the drift:
CORE-04 reports 328 PASS + 1 FAIL and the run reports 986 scopes. Under the approved
contract, CORE-04 has 258 GED scopes (257 PASS + 1 FAIL), and the five-rule run has 915
scope results (908 PASS + 5 FAIL + 2 NOT_EVALUATED).

**Action:** choose one governed outcome:

1. remove Budget scopes from CORE-04 and regenerate the oracle/evidence; or
2. introduce the Budget checks as a separately governed optional/new protected rule,
   preserving CORE-04's approved identity and history.

**Verification:** contract boundary tests, regenerated independent oracle, historical
replay, and a full clean suite.

### FC-02 — optional rules change V1 Overall Review Status

**Classification:** Must fix before packaging — material financial-status defect.

At `financial_validation.py:689`–`720`, failed and not-evaluated counts include every
execution. Requirements §2.7 and FR-158 require Overall Review Status to use only the
five selected Core Mandatory executions.

A direct closeout probe with all five core rules PASS and one optional threshold FAIL
produced:

```text
overall = Attention Required
rag = At Risk (Red)
budget_health = Healthy
```

Expected: `Healthy / On Track (Green)`, with the optional failure visible but excluded
from V1 overall status.

### FC-03 — RAG is independently and incorrectly derived

**Classification:** Must fix before packaging.

`financial_validation.py:720` sets red whenever any finding exists. Required mapping is
one-to-one from persisted Overall Review Status:

- Healthy → On Track (Green);
- Attention Required → Needs Attention (Yellow);
- Incomplete → At Risk (Red).

The probe above demonstrates an `Attention Required / At Risk (Red)` impossible pair.
The UI also chooses the `warning` tone first for textual `Incomplete` at
`financial_review_view.py:2691`–`2703`, weakening the required red visual mapping.

### FC-04 — summary health/status projections use the wrong source

**Classification:** Must fix before packaging.

`financial_validation.py:721`–`735` differs from the exact §2.7 projection:

- Budget Health becomes Incomplete for any rule's incomplete execution, not CORE-01;
- Data Quality never becomes Incomplete for CORE-02/CORE-04 NOT_EVALUATED;
- Reconciliation's PASS label is `Reconciled`, not required `Healthy`;
- summary execution counts do not distinguish core/optional/advisory status policy.

### FC-05 — CORE-03 exposure and summary count fail for groups larger than two

**Classification:** Must fix before packaging.

At `financial_validation.py:1006`, duplicate-copy exposure uses only `rows[1]`.
Requirements require the sum of every member after the deterministic reference row.
At line 748, `duplicate_transactions` counts failed groups, not `member count - 1`.

A direct three-member closeout probe returned:

```text
3 identical transactions; duplicate-copy exposure $100.00
summary duplicate_transactions = 1
```

For three $100 copies, both values must be `$200.00` and `2`.

### FC-06 — valid out-of-review-period rows are included in financial sums

**Classification:** Must fix before packaging.

Requirements §11.3–§11.5 include a GED row only when its Fiscal Period is in the
selected year and no later than the selected month. Canonicalization at
`financial_validation.py:432`–`469` checks only that `YYYY-MM` parses and then sums all
transactions. `dataset.reporting_period` is not used for eligibility.

A direct May 2026 probe with one valid `2026-06` row returned CORE-01 FAIL, CORE-05
FAIL, and GED `$100.00`. Under the approved contract, that row is outside the eligible
May YTD aggregate; CORE-01 and CORE-05 should evaluate the exact-key empty sum.

### FC-07 — CORE-03 scalar canonicalization is incomplete

**Classification:** Must fix before packaging.

`_canonical_field` treats every non-amount/non-date Python value as text. The approved
fingerprint requires canonical parsed values for required fields and type-tagged
spreadsheet scalars for optional numeric/date/text cells. Numeric-vs-text optional
cells, numeric account representations, and date-string/date-cell equivalence therefore
risk false duplicate matches or misses. No boundary test covers these type distinctions.

## 7. Architecture and code-quality findings

### CQ-01 — two financial engines remain composed

**Classification:** Must fix before packaging.

`src/finsight/app.py:181`–`193` still constructs the legacy `domain.rules.RulesEngine`,
`AnalysisService`, and `Orchestrator`. The same production `build_query_services`
constructs `CoreFinancialValidationEngine` at lines 878–899. `AppServices` exposes both
the legacy workflow and V2 financial-review services.

`main_window.py` also builds a complete legacy Dashboard/Reviews/Overview/Workflow/
Findings/Audit/Ask Fin stack and places it at root-stack index 5. Although normal V2
navigation does not expose it, `navigate()` still activates it, and controller legacy
analysis methods remain callable.

This contradicts the single deterministic rule-engine source-of-truth decision and
creates obsolete views, duplicate result/query paths, and future maintenance risk.
Remove the legacy production composition and shell, or quarantine it behind an explicit
non-production adapter that cannot be present in the packaged build.

### CQ-02 — fitness contract gap

**Classification:** Must fix before packaging.

Import-linter passes while the UI dependency fitness test fails. Add infrastructure to
the explicit architecture contracts so delivery cannot import it directly, then move
Ask Fin preference persistence behind an application port.

### CQ-03 — UI computes descriptive result aggregates

**Classification:** Should fix.

`financial_review_view.py` reconstructs vendor account/finding counts by traversing the
dataset and persisted findings, and adds record totals in the UI. These do not currently
decide pass/fail, but ADR-V2-007 and the rule-engine design require shared recorded
projections for dashboards and consumers. Move reusable aggregates to the sealed
analytics projection to avoid report/UI divergence.

### CQ-04 — run selection uses SQLite `rowid`

**Classification:** Should fix.

`financial_review_repository.py` selects and orders retained runs using implicit
`rowid`. Add an explicit immutable run sequence / completed timestamp plus deterministic
tie-breaker. This improves replay portability and avoids depending on SQLite storage
internals.

### CQ-05 — uncommitted release state

**Classification:** Must fix before packaging.

The worktree contains 29 modified tracked files plus the V2 implementation,
migrations 0004–0014, tests, initiative documents, scripts, and artifacts as untracked
content. The last commit predates V2. A clean immutable commit/tag is required before
independent release verification; generated screenshots and accidental `--help/`
artifacts should not be mixed with product source.

## 8. Coverage strengths

- exact `Decimal` fixture totals and intentional scenarios;
- all five current engine outcomes for the supplied sample;
- source-row/cell evidence for each sample finding;
- correction, confirmation, append-only finding status, persistence and restart;
- optional-rule create/edit/test/activate/disable/reanalysis history;
- protected baseline and workspace-upgrade separation of duties;
- retained prior runs and run comparisons;
- charts' exact-data alternatives and core result keyboard drill-down;
- migrations through schema 14;
- Ask Fin grounding/privacy/security coverage is extensive (440 AI cases);
- domain import independence and result-consumer fitness checks;
- launch smoke and source-file preservation.

## 9. Missing or brittle high-risk tests

| Gap | Classification | Required verification |
|---|---|---|
| Core-only status with optional FAIL and NOT_EVALUATED | Must fix before packaging | Direct status-policy unit matrix |
| Exact RAG mapping for all three overall statuses | Must fix before packaging | Domain and UI role/token assertions |
| CORE-04 exactly one scope per GED row | Must fix before packaging | Contract scope-count tests independent of sample oracle |
| Duplicate groups of 3+ and unavailable amount among later copies | Must fix before packaging | Exposure/count boundary matrix |
| Fiscal Period before/at/after selected month and wrong year | Must fix before packaging | CORE-01/05 eligible-population matrix |
| Fingerprint scalar type distinctions and canonical equivalence | Must fix before packaging | Typed 15-field fingerprint matrix |
| Budget Health/Data Quality/Reconciliation exact source policy | Must fix before packaging | Table-driven projection tests |
| All-invalid/empty scope enumeration and missing core execution | Must fix before packaging | Completion/status-policy tests |
| Clean Windows test execution | Must fix before packaging | Windows CI on supported Python/Qt/SQLCipher versions |
| POSIX controls' Windows equivalents | Must fix before packaging | ACL/store/disposal tests using Windows APIs |
| Native screen reader | Must fix before pilot | NVDA manual/automated smoke |
| Large-workbook performance and UI responsiveness | Must fix before pilot | representative load/latency/memory test |
| Ask Fin drawer test isolation | Must fix before packaging | deterministic animation completion and suite-order test |
| Clean install/upgrade/repair/uninstall | Must fix before packaging | clean Windows VM installer matrix |

There is only one large integrated financial UI test
(`test_guided_mvp_runs_to_completion_and_reopens_read_only`, 865 lines). It supplies
excellent breadth but is brittle and makes failures expensive to localize. Retain it as
an end-to-end test and split critical financial, evidence, and navigation contracts into
smaller focused tests.

## 10. Full-regression-before-packaging decision

**A full governed regression is required before packaging, but rerunning the unchanged
state is not sufficient.** The current run already proves the baseline is red.

Required sequence:

1. reconcile the approved CORE-04 contract and regenerate the independent oracle;
2. fix status/RAG/summary projections, period eligibility, and CORE-03 boundaries;
3. remove or isolate the legacy engine/shell and correct the delivery dependency;
4. fix the three UI/accessibility issues and the order-dependent drawer behavior;
5. add the missing boundary tests above;
6. create a clean, reviewable release-candidate commit;
7. run Ruff, strengthened import contracts, the independent oracle, and the entire
   offscreen suite from that exact commit;
8. run the suite and installer verification on a clean supported Windows VM;
9. preserve logs, hashes, skip reasons, and exact commit/build identities.

Packaging entry requires zero unexpected failures, no unresolved material finance
defect, reviewed skips only, a clean source baseline, and reproducible oracle evidence.

## 11. Evidence read and inspected

Primary specifications and architecture:

- `docs/00-project-understanding.md`
- `initiatives/configurable-rule-engine-v2/specs/01-functional-requirements.md`
- `initiatives/configurable-rule-engine-v2/docs/APPLICATION-ARCHITECTURE.md`
- `initiatives/configurable-rule-engine-v2/docs/PERSISTENCE-MODEL.md`
- `initiatives/configurable-rule-engine-v2/docs/RULE-ENGINE-DESIGN.md`
- `initiatives/configurable-rule-engine-v2/docs/STAGE-1-FINANCIAL-HIERARCHY-AND-CANONICAL-DATASET.md`
- `initiatives/configurable-rule-engine-v2/plans/TECHNICAL-IMPLEMENTATION-PLAN.md`
- `initiatives/configurable-rule-engine-v2/tasks/STAGE-1-GOVERNED-IMPLEMENTATION-PLAN-2026-07-29.md`

Oracle/review/verification evidence:

- `fixtures/SYNTHETIC-VALIDATION-EXPECTATIONS.md`
- `fixtures/STAGE-1-MANUAL-VALIDATION-ORACLE-2026-07-29.md`
- `verification/STAGE-1-INDEPENDENT-ORACLE-2026-07-29.json`
- `reviews/REVIEW-2026-07-29-stage-1-financial-correctness.md`
- `verification/STAGE-1-FINANCIAL-CORRECTNESS-VERIFICATION-2026-07-29.md`
- `verification/STAGE-2-CONSOLIDATED-VERIFICATION-2026-07-29.md`
- `verification/STAGE-2-FOLLOWUP-ASK-FIN-NAVIGATION-RULES-2026-07-29.md`
- `verification/STAGE-2-ASK-FIN-SIMPLIFICATION-2026-07-29.md`
- `test-results.txt`, `pyproject.toml`, `.importlinter`

High-risk implementation:

- `domain/financial_validation.py`, `domain/finding_explanations.py`,
  `domain/money.py`, `domain/rules.py`, `domain/verified_dataset.py`
- `application/financial_review.py`, `application/rule_management.py`,
  `application/analysis.py`, `application/verification.py`
- `infrastructure/financial_review_repository.py`, migrations 0006–0014
- `delivery/desktop/views/financial_review_view.py`,
  `delivery/desktop/components/charts.py`, `app.py`, `main_window.py`,
  and `controllers/app_controller.py`

High-risk tests were read in full:

- `tests/unit/test_financial_validation.py`
- `tests/integration/test_stage1_financial_oracle.py`
- `tests/application/test_financial_review.py`
- `tests/application/test_rule_management.py`
- `tests/application/test_finding_explanations.py`
- `tests/ui/test_integrated_financial_review.py`
- `tests/accessibility/test_financial_results_accessibility.py`
- `tests/fitness/test_integrated_financial_review_architecture.py`

## 12. Final recommendation

**Next governed stage: Stabilization and Regression.** Do not begin packaging,
leadership-export expansion, or additional product features. The current May fixture is
internally arithmetically consistent, but the protected-rule contract, status policy,
period eligibility, duplicate boundary, architecture baseline, and full suite must be
corrected and independently reverified first.
