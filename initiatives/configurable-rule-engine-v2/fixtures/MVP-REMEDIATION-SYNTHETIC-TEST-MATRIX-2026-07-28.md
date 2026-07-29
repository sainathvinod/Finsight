# MVP Remediation Synthetic Expected-versus-Actual Matrix

- **Date:** 2026-07-28
- **Fixtures:** `Sample_Budget_Report.xlsx`, `Sample_GED_Report.xlsx`
- **Reference population:** 71 Budget detail records and 258 GED transactions
- **Expected environment:** Department `00-0245`; reporting period May 2026
- **Execution status:** **AUTOMATED DOMAIN ORACLE AND SCREENSHOT DEMONSTRATION RECORDED**
- **Rule-set-under-test:** `FINSIGHT-CORE-2.0`, Rule Set Version `1.0.0`; protected rule versions `2.0.0`
- **Validation Run ID:** Not assigned by the direct domain-oracle test; the screenshot demonstration uses its persisted demo-run identity

This artifact separates approved expected behavior from executed evidence. The
deterministic fixture oracle is asserted by
`tests/unit/test_financial_validation.py`. Light/Dark screenshots are linked as
presentation evidence, and final visual QA passed. The independent review remains
pending.

The protected baseline oracle is exactly **986 scope results = 979 PASS / 5 FAIL /
2 NOT_EVALUATED, with 5 findings**. The screenshot demonstration deliberately
activates one optional GED threshold rule to prove configurability. Its captured
run therefore contains **1,244 ledger rows**: the same 986 protected results plus
258 optional-rule scopes. That optional control creates no additional finding, so
the screenshot demonstration still shows the same five protected-control
findings.

## 1. Four intentional fixture issues across the five core rules

| Scenario | Budget-to-GED Reconciliation (CORE-05) | Budget Overrun (CORE-01) | Valid Account Coding (CORE-02) | Complete and Correct Data (CORE-04) | Duplicate Transactions (CORE-03) |
|---|---|---|---|---|---|
| TEST-01 — Budget row 91 / GED rows 246–289, `00-0245 / 555035` | Expected PASS: Budget ATD and summed GED are both `$1,250,000.00` | Expected FAIL: BGT `$1,100,000.00`, GED `$1,250,000.00`, overrun `$150,000.00` / `13.636…%` | Expected PASS for all involved transactions | Expected PASS for involved records and Budget calculations | Expected no duplicate group |
| TEST-02 — GED rows 65/66, `00-0245 / 533003` | Expected PASS; both rows remain in the GED sum | Expected account remains within BGT | Expected both transactions mapped | Expected required values valid | Expected one failed 15-material-field fingerprint group; row 65 reference and row 66 duplicate; duplicate-copy exposure `$82.50` |
| TEST-03 — missing `GED!O87`, `00-0245 / 537035` | Expected NOT_EVALUATED for this exact Budget key; no partial sum | Expected NOT_EVALUATED for this exact Budget key | Expected mapping remains valid because Amount is not a mapping key | Expected one failed transaction citing `GED!O87` | Expected null-token fingerprint remains evaluable and unique |
| TEST-04 — GED row 43, `00-0999 / 527015`, `$1,850.00` | Expected consequential FAIL for Budget key `00-0245 / 527015`: ATD `$1,850.00` versus exact-key GED `$0.00` | Expected valid Budget key remains within BGT using exact-key GED `$0.00`; unmapped row creates no Budget scope | Expected one failed transaction citing row 43 and both coding fields | Expected required fields remain parseable | Expected no duplicate group |

TEST-04 therefore produces two findings from one intentional source issue: the primary mapping exception and the exact-key reconciliation consequence. The four fixture issues are expected to produce five control findings.

## 2. Scenario evidence: expected versus actual

| Test | Expected deterministic result | Expected evidence presentation | Actual deterministic result | Actual evidence presentation | Verdict |
|---|---|---|---|---|---|
| TEST-01 | One High CORE-01 finding; CORE-05 passes | Budget row/account plus contributing GED records; BGT, GED spend, `$150,000.00` overrun and percentage; Budget/GED linked navigation | **Actual:** one CORE-01 finding for `00-0245 / 555035`; actual evidence includes BGT `$1,100,000.00`, GED spend `$1,250,000.00`, overrun `$150,000.00`, and `13.64%`; CORE-05 passes | Rule-oriented evidence: [Light](../verification/screenshots/mvp-end-to-end/light/26-validation-results-evidence.png) / [Dark](../verification/screenshots/mvp-end-to-end/dark/26-validation-results-evidence.png). Budget comparison: [Light](../verification/screenshots/mvp-end-to-end/light/25-budget-ged-comparison-chart.png) / [Dark](../verification/screenshots/mvp-end-to-end/dark/25-budget-ged-comparison-chart.png) | **PASS — automated oracle** |
| TEST-02 | One Medium CORE-03 finding; both transactions stay in aggregation | GED rows 65 and 66 side by side; all approved material fields; reference/duplicate labels; `$82.50` duplicate-copy exposure | **Actual:** one CORE-03 finding with source records `GED:GED:65` and `GED:GED:66`; actual evidence includes `$82.50`; both rows remain in aggregation | Duplicate evidence: [Light](../verification/screenshots/mvp-end-to-end/light/27-findings-duplicate-evidence.png) / [Dark](../verification/screenshots/mvp-end-to-end/dark/27-findings-duplicate-evidence.png) | **PASS — automated oracle** |
| TEST-03 | One High CORE-04 finding; CORE-01 and CORE-05 NOT_EVALUATED only for the affected key | Exact Amount cell `O87` highlighted; Original/Current provenance; plain-language missing-value action; charts marked partial/incomplete | **Actual:** one CORE-04 finding with evidence `GED!O87`; structured evidence identifies `GED:GED:87`, worksheet `GED`, row `87`, field `amount`, cell `O87`, Original `None`, Current `None`, origin `Original`; exactly one CORE-01 and one CORE-05 scope are NOT_EVALUATED | Exact cell/provenance is asserted by automated structured-evidence checks. GED projection: [Light](../verification/screenshots/mvp-end-to-end/light/24-ged-charts-and-evidence.png) / [Dark](../verification/screenshots/mvp-end-to-end/dark/24-ged-charts-and-evidence.png). Coverage: [Light](../verification/screenshots/mvp-end-to-end/light/28-data-quality-and-coverage.png) / [Dark](../verification/screenshots/mvp-end-to-end/dark/28-data-quality-and-coverage.png) | **PASS — automated oracle** |
| TEST-04 | One High CORE-02 mapping finding plus one High CORE-05 finding | GED row 43 coding cells; Budget key `00-0245 / 527015`; ATD and exact-key GED `$0.00`; contributing-record navigation | **Actual:** CORE-02 finding identifies Department `00-0999`; consequential CORE-05 finding identifies Account `527015`, exact-key GED `$0.00`, and Budget ATD-to-GED variance `$1,850.00` | Exact mapping/reconciliation evidence is asserted by automated structured-evidence checks. Comparison: [Light](../verification/screenshots/mvp-end-to-end/light/25-budget-ged-comparison-chart.png) / [Dark](../verification/screenshots/mvp-end-to-end/dark/25-budget-ged-comparison-chart.png). GED projection: [Light](../verification/screenshots/mvp-end-to-end/light/24-ged-charts-and-evidence.png) / [Dark](../verification/screenshots/mvp-end-to-end/dark/24-ged-charts-and-evidence.png) | **PASS — automated oracle** |

Stop conditions:

- subtotal, total, separator, or blank rows enter rule populations;
- duplicate rows are deduplicated before aggregation;
- blank Amount is coerced to zero or a partial account total is treated as complete;
- account-only rather than Department + Account matching is used;
- report-level department matching is broken by the intentional transaction-level `00-0999`;
- a chart or UI table reports a financial result inconsistent with the sealed ledger; or
- evidence requires the user to manually search the spreadsheet.

## 3. Five core-rule ledger: expected versus actual

| Protected core rule | Expected scopes | Expected PASS | Expected FAIL | Expected NOT_EVALUATED | Expected roll-up | Expected findings | Actual scopes / distribution | Actual roll-up / findings | Verdict |
|---|---:|---:|---:|---:|---|---:|---|---|---|
| CORE-05 — Budget-to-GED Reconciliation | 71 | 69 | 1 | 1 | NOT_EVALUATED | 1 | **71 = 69 / 1 / 1** | **NOT_EVALUATED / 1** | **PASS** |
| CORE-01 — Budget Overrun | 71 | 69 | 1 | 1 | NOT_EVALUATED | 1 | **71 = 69 / 1 / 1** | **NOT_EVALUATED / 1** | **PASS** |
| CORE-02 — Valid Account Coding | 258 | 257 | 1 | 0 | FAIL | 1 | **258 = 257 / 1 / 0** | **FAIL / 1** | **PASS** |
| CORE-04 — Complete and Correct Data | 329 | 328 | 1 | 0 | FAIL | 1 | **329 = 328 / 1 / 0** | **FAIL / 1** | **PASS** |
| CORE-03 — Duplicate Transactions | 257 | 256 | 1 | 0 | FAIL | 1 | **257 = 256 / 1 / 0** | **FAIL / 1** | **PASS** |
| **Total** | **986** | **979** | **5** | **2** | — | **5** | **986 = 979 / 5 / 2** | **5 findings** | **PASS** |

NOT_EVALUATED takes rule-level precedence over FAIL and PASS, but shall not hide failed or passing scope results.

## 4. Expected financial/control projection

| Output | Expected | Actual | Verdict |
|---|---:|---|---|
| BGT | `$10,372,000.00` | `$10,372,000.00` | **PASS** |
| Budget ATD | `$3,500,095.00` | `$3,500,095.00` | **PASS** |
| GED total | `$3,500,095.00`, explicitly identified as affected by one missing transaction Amount where completeness is discussed | `$3,500,095.00`; `ged_is_complete = false` | **PASS** |
| Mapped GED | `$3,498,245.00` | `$3,498,245.00` | **PASS** |
| Unmapped GED | `$1,850.00` | `$1,850.00` | **PASS** |
| ETC | `$5,882,000.00` | `$5,882,000.00` | **PASS** |
| EAC | `$9,382,095.00` | `$9,382,095.00` | **PASS** |
| DELTA | `$989,905.00` | `$989,905.00` | **PASS** |
| Overall Review Status | `Incomplete` / `At Risk (Red)` | `Incomplete` / `At Risk (Red)` | **PASS** |
| Findings by severity | Four High, one Medium | Critical `0`; High `4`; Medium `1`; Low `0` | **PASS** |
| Budget overruns | One | `1` | **PASS** |
| Duplicate copies beyond reference row | One | `1`; duplicate source records are rows `65` and `66` | **PASS** |
| Missing required values | One | `1`; exact evidence is `GED!O87` | **PASS** |
| Consequential reconciliation failures | One | `1`; Account `527015`, variance `$1,850.00` | **PASS** |

## 5. Positive and boundary checks required for the same five rules

| Rule | Positive case | Boundary case | Negative case | Actual evidence |
|---|---|---|---|---|
| CORE-05 | Equal parseable Budget ATD and summed GED passes | Signed cent-precise equality passes | Unequal values fail; incomplete exact key is NOT_EVALUATED | `test_budget_boundary_equal_to_bgt_passes_and_reconciles`, `test_approved_signed_reversal_is_valid_financial_data`, and `test_missing_amount_fails_required_rule_and_blocks_only_aggregates` passed in the recorded suite |
| CORE-01 | GED below BGT passes | GED exactly equal to BGT passes | GED above BGT fails; incomplete exact key is NOT_EVALUATED | Boundary equality, overrun evidence, signed reversal, and missing-Amount NOT_EVALUATED tests passed |
| CORE-02 | Exact Department + Account exists | Leading zeros remain significant strings | Missing composite key fails; account-only match is prohibited | Fixture oracle passed with 257 mapped scopes and one exact composite-key failure for `00-0999 / 527015` |
| CORE-04 | Required values parse and Budget equations reconcile | Approved signed reversal/adjustment parses | Missing/unparseable required value or invalid approved Budget equation fails | Signed reversal, missing Amount, and Budget EAC/DELTA mismatch tests passed; fixture ledger is 328 PASS / 1 FAIL |
| CORE-03 | Distinct material field prevents duplicate group | Exactly two matching rows yield one group and one duplicate copy | All approved material fields equal yields failure; Journal Number alone is insufficient | Fixture oracle passed with one duplicate fingerprint group, rows 65/66, and 256 distinct passing fingerprints |

## 6. Rule Repository consistency

| Check | Expected | Actual | Verdict |
|---|---|---|---|
| UI names/purposes match this matrix | Exact match | Core repository list/detail captured in [Light](../verification/screenshots/mvp-end-to-end/light/13-rules-core-list-and-detail.png) and [Dark](../verification/screenshots/mvp-end-to-end/dark/13-rules-core-list-and-detail.png); final visual QA passed | **PASS** |
| Rule manifest uses exact versions shown in Review Rules | Exact persisted identity | Domain and rule-management tests verify `FINSIGHT-CORE-2.0`, Rule Set Version `1.0.0`, and protected rule version `2.0.0` | **PASS — automated** |
| Reports and saved results retain the same names/versions | Exact match | Integrated persistence/reopen test passed; reopened screen captured in [Light](../verification/screenshots/mvp-end-to-end/light/31-reopened-results.png) and [Dark](../verification/screenshots/mvp-end-to-end/dark/31-reopened-results.png) | **PASS** |
| Optional-rule change preserves the prior run | Prior and successor both visible | Rule-management/reanalysis tests passed; Draft/Test/Activate states captured under screenshot sequence `14`–`19`; captured optional run has 1,244 rows and the same five findings | **PASS** |
| Charts match sealed result projections | No independent variance | Engine projection and integrated UI tests passed; chart/table screens captured under sequence `21`–`25` in both theme directories; final visual QA passed | **PASS** |
