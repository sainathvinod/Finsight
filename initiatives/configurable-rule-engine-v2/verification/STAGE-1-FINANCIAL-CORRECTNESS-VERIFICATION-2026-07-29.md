# Stage 1 Financial Correctness — Consolidated Verification

- **Date:** 2026-07-29
- **Lane:** Governed
- **Scope:** financial hierarchy, canonical financial dataset, deterministic
  validation, rule-driven results, source evidence, analytics, and retained-run
  comparison
- **Implementation:** Complete
- **Internal verification:** PASS
- **Independent financial review:** PASS — one initial Medium defect closed on
  bounded recheck
- **Hands-on acceptance:** Pending Project Owner
- **Explicitly excluded:** Ask Fin expansion, Windows packaging, MSI generation,
  and unrelated cosmetic work

## 1. Qualified source identity

| Source | Worksheet | SHA-256 | Qualified population |
|---|---|---|---:|
| `Sample_Budget_Report.xlsx` | `Original Budget` | `bf40584183c564d91831214781969422d77d50439989f75750f0bdbe2bfa2b14` | 71 six-digit Budget detail rows |
| `Sample_GED_Report.xlsx` | `GED` | `2213e3f1b10fee56fb4538112250fe37fbdaf36eb5e299fbfe6d17bd0f10603c` | 258 transaction rows |

The original workbook bytes were not modified. FinSight reads the approved
source layouts, preserves their source row/cell lineage, and constructs reviewed
working records for validation.

## 2. Financial hierarchy and canonical truth

The implemented hierarchy is:

```text
Review
└── Department
    └── Account
        ├── Account Name / category
        ├── Budget summary
        └── GED transactions
            └── Vendor
                └── Individual transaction
                    └── Source evidence
```

The full field, key, row, formula, decimal, lineage, and unavailable-level
contract is recorded in
[Stage 1 Financial Hierarchy and Canonical Dataset](../docs/STAGE-1-FINANCIAL-HIERARCHY-AND-CANONICAL-DATASET.md).

One `CFD-1.0` projection is recorded with each Validation Run. It contains the
union of 71 Budget account scopes and the one intentional unmapped GED scope.
Validation, findings, KPIs, charts, exact-data alternatives, detail tables, run
comparison, report/export projections, and future Ask Fin grounding consume that
recorded result. Delivery views do not recalculate financial truth.

## 3. Exact financial control report

All financial controls use `Decimal`, quantized to two decimal places.

| Control | Included rows | Exact result |
|---|---:|---:|
| Total Budget BGT | 71 Budget detail rows | $10,372,000.00 |
| Total Budget ATD | 71 Budget detail rows | $3,500,095.00 |
| Total Budget ETC | 71 Budget detail rows | $5,882,000.00 |
| Total Budget EAC | 71 Budget detail rows | $9,382,095.00 |
| Total Budget DELTA | 71 Budget detail rows | $989,905.00 |
| Parseable eligible GED Amount | 257 of 258 transactions | $3,500,095.00 |
| Mapped GED Amount | Exact Budget keys | $3,498,245.00 |
| Unmapped GED Amount | Non-Budget key | $1,850.00 |
| Excluded GED transaction Amount | No excluded transaction population | $0.00 |

The eligible GED total is explicitly incomplete because `GED!O87` is blank.
FinSight does not convert the blank to zero. Source account and department total
rows display $7,000,190.00 in aggregate, but those presentation controls are
excluded from transaction spend to avoid double counting.

### Row inclusion and exclusion

| Dataset | Included | Excluded controls |
|---|---:|---|
| Budget | 71 detail rows | 11 group totals, 11 separators, 1 grand total |
| GED | 258 transactions | 31 account totals, 1 department total, 2 blank rows |

Every included/excluded count, formula, and source classification is available
in the application Data Quality & Coverage page and in the independent oracle.

## 4. Independent expected-versus-actual oracle

The independent verifier opens the XLSX ZIP/XML packages directly with the
Python standard library, uses `Decimal`, and imports no FinSight module or
spreadsheet library:

```bash
.venv/bin/python scripts/verify_stage1_financial_oracle.py --compact
```

Artifact:
[Stage 1 Independent Oracle JSON](STAGE-1-INDEPENDENT-ORACLE-2026-07-29.json)
(`SHA-256 63637b6e2b18b15f73d5f087e734a7715eb64f9790195944c1df0d94de9ed06e`).

The human-readable control matrix is
[Stage 1 Manual Validation Oracle](../fixtures/STAGE-1-MANUAL-VALIDATION-ORACLE-2026-07-29.md).

| Known scenario | Expected | FinSight actual | Verdict |
|---|---|---|---|
| Overrun | Account 555035; BGT $1,100,000.00; GED $1,250,000.00; overrun $150,000.00; 113.64% | Exact match | PASS |
| Exact duplicate | GED rows 65–66; account 533003; $82.50; all 15 material fields equal | Exact match | PASS |
| Missing required amount | `GED!O87` blank; account 537035; dependent outcomes not evaluated | Exact match | PASS |
| Invalid coding | GED row 43; `00-0999 / 527015`; $1,850.00 | Exact match | PASS |
| Reconciliation effect | Budget row 11; `00-0245 / 527015`; ATD $1,850.00; GED $0.00; difference $1,850.00 | Exact match | PASS |

## 5. Five protected baseline rules

Stable product Rule IDs retain their established numbering.

| Rule | PASS | FAIL | NOT_EVALUATED | Findings | Verdict |
|---|---:|---:|---:|---:|---|
| CORE-05 Budget-to-GED Reconciliation | 69 | 1 | 1 | 1 | PASS |
| CORE-01 Budget Overrun | 69 | 1 | 1 | 1 | PASS |
| CORE-02 Valid Account Coding | 257 | 1 | 0 | 1 | PASS |
| CORE-04 Complete and Correct Data | 328 | 1 | 0 | 1 | PASS |
| CORE-03 Exact Duplicate Transactions | 256 | 1 | 0 | 1 | PASS |
| **Total ledger** | **979** | **5** | **2** | **5** | **PASS** |

Every result and finding identifies the Rule ID, exact immutable rule version,
Rule Set Version, Validation Run, scope, explanation, expected/actual values,
recommended action, and implicated source records.

## 6. Configurable-rule result pipeline

Optional rules use the same deterministic pipeline as protected controls:

```text
Rule Repository
→ Active Rule Set
→ Deterministic Rule Engine
→ Rule Results
→ Findings
→ Charts and Analytics
→ Reports
→ Future Ask Fin explanations
```

Automated lifecycle proof covers:

- rejecting invalid or unsafe threshold definitions before Draft persistence;
- creating and testing an attributable optional Draft;
- activating an immutable rule version in a successor Rule Set Version;
- editing through another version rather than rewriting history;
- disabling the optional binding only in a successor Rule Set;
- creating a successor Review Version and Validation Run for revalidation;
- regenerating summaries, results, findings, and analytics from that run;
- classifying findings as added, removed, or changed;
- reopening and reproducing every prior run without overwrite; and
- preventing ordinary review users from seeing unbound administrative Drafts.

The screenshot demonstration contains six active rules. This intentionally proves
that results and analytics are not hard-coded to the five baseline rules.

## 7. Results, hierarchy, and source evidence

All charts are keyboard focusable and mouse/keyboard activatable. Each chart has
an exact-data table alternative derived from the same persisted projection.
KPI and chart activation drills into the relevant result or account context.

### Visual analysis delivered

| Results area | Business questions answered |
|---|---|
| Executive Overview | overall status; BGT, ATD, GED, ETC, EAC, DELTA; account and transaction populations; rules and findings; severity; utilization; reconciliation and account status |
| Budget Data | BGT, ATD, ETC, EAC, DELTA, remaining/overrun by account |
| GED Data | spend and count by account, period, vendor, largest transactions, and positive/negative activity |
| Budget vs GED | BGT vs GED, Budget ATD vs GED, ranked remaining/overrun, and reconciliation status |
| Account drill-down | Budget summary, GED total, every contributing transaction, vendors, descriptions, periods, findings, and direct source actions |
| Data Quality & Coverage | exact controls, inclusion/exclusion counts, missing/invalid/unmapped/duplicate states, evaluation coverage, and all 23 approved source fields |

### Show Evidence

Every finding has a `Show Evidence` view with:

- plain-language reason and recommended corrective action;
- Rule ID and version;
- exact Department and Account;
- expected value, actual value, difference/overrun, and source values used;
- source filename, worksheet, row, and relevant cell/column;
- all implicated Budget and GED records, selectable for multi-record findings;
  and
- direct `Show Evidence in Source Data` navigation.

The duplicate view retains both rows and their field-by-field match. The missing
Amount view identifies `GED!O87`; the mapping view identifies GED row 43; the
overrun and reconciliation views retain their Budget row and complete GED
contributor sets.

## 8. Complete field coverage

The recorded `field_coverage` projection contains all 23 approved fields:
8 Budget columns and 15 GED columns. Every row identifies its dataset, use,
display destination, validation effect, and any deliberate absence of a direct
pass/fail effect. No approved source field is silently ignored.

The matrix is visible under Data Quality & Coverage and specified in the
[canonical dataset contract](../docs/STAGE-1-FINANCIAL-HIERARCHY-AND-CANONICAL-DATASET.md#exact-source-fields).

## 9. Persistence, edit, and retained-run proof

| Required behavior | Verification |
|---|---|
| Original workbooks remain unchanged | Fixture hashes remain exact before and after reviewed-value edits |
| Reviewed values drive validation | Existing correction and revalidation tests pass |
| Original/current/edit provenance retained | Canonical records and source evidence expose value origin |
| Revalidation creates a new run | Optional-rule lifecycle test retains four successive runs |
| Prior runs remain reproducible | Repository reopen reconstructs previous results and Rule Set Versions |
| Run comparison | Added, removed, and changed findings are recorded with before/after evidence |
| Reopen | Reopened results, comparison, and account hierarchy are captured in both themes |

## 10. Visual and accessibility qualification

- 130 deterministic screenshots: 65 states × Light and Dark at 1440 × 960.
- System Default smoke resolved to Light in the headless environment.
- Native tables hide internal row headers; source rows always refer to Excel.
- Charts and interactive KPIs expose accessible names, descriptions, focus
  states, non-color outcome labels, and exact-data alternatives.
- Keyboard activation is supported with Enter, Return, or Space.
- Cream/navy Light and Dark themes retain readable status, chart, table, focus,
  and evidence contrast.

Screenshot gallery:
[Stage 1 Financial Correctness Screenshots](screenshots/stage-1-financial-correctness/).

Key Light / Dark examples:

| Evidence | Light | Dark |
|---|---|---|
| Executive overview | [Light](screenshots/stage-1-financial-correctness/light/21-executive-overview.png) | [Dark](screenshots/stage-1-financial-correctness/dark/21-executive-overview.png) |
| Overview totals, severity, and outcomes | [Light](screenshots/stage-1-financial-correctness/light/22-executive-analytics.png) | [Dark](screenshots/stage-1-financial-correctness/dark/22-executive-analytics.png) |
| Overview utilization and reconciliation | [Light](screenshots/stage-1-financial-correctness/light/22a-overview-reconciliation-and-utilization.png) | [Dark](screenshots/stage-1-financial-correctness/dark/22a-overview-reconciliation-and-utilization.png) |
| Budget account analysis | [Light](screenshots/stage-1-financial-correctness/light/23-budget-chart-and-evidence.png) | [Dark](screenshots/stage-1-financial-correctness/dark/23-budget-chart-and-evidence.png) |
| GED account, count, and period analysis | [Light](screenshots/stage-1-financial-correctness/light/24-ged-charts-and-evidence.png) | [Dark](screenshots/stage-1-financial-correctness/dark/24-ged-charts-and-evidence.png) |
| Vendor and largest transactions | [Light](screenshots/stage-1-financial-correctness/light/24a-ged-vendor-and-largest-transaction-charts.png) | [Dark](screenshots/stage-1-financial-correctness/dark/24a-ged-vendor-and-largest-transaction-charts.png) |
| Positive / negative activity | [Light](screenshots/stage-1-financial-correctness/light/24b-ged-positive-negative-activity.png) | [Dark](screenshots/stage-1-financial-correctness/dark/24b-ged-positive-negative-activity.png) |
| Budget / GED comparison | [Light](screenshots/stage-1-financial-correctness/light/25-budget-ged-comparison-chart.png) | [Dark](screenshots/stage-1-financial-correctness/dark/25-budget-ged-comparison-chart.png) |
| Ranked variance and reconciliation | [Light](screenshots/stage-1-financial-correctness/light/25a-comparison-ranked-and-reconciliation-charts.png) | [Dark](screenshots/stage-1-financial-correctness/dark/25a-comparison-ranked-and-reconciliation-charts.png) |
| Account 555035 drill-down | [Light](screenshots/stage-1-financial-correctness/light/25b-account-555035-budget-and-ged-summary.png) | [Dark](screenshots/stage-1-financial-correctness/dark/25b-account-555035-budget-and-ged-summary.png) |
| Contributing transactions | [Light](screenshots/stage-1-financial-correctness/light/25c-account-555035-contributing-transactions.png) | [Dark](screenshots/stage-1-financial-correctness/dark/25c-account-555035-contributing-transactions.png) |
| Optional rule revalidation comparison | [Light](screenshots/stage-1-financial-correctness/light/28j-rule-edit-and-revalidation-comparison.png) | [Dark](screenshots/stage-1-financial-correctness/dark/28j-rule-edit-and-revalidation-comparison.png) |
| Reopened account hierarchy | [Light](screenshots/stage-1-financial-correctness/light/31b-reopened-account-financial-hierarchy.png) | [Dark](screenshots/stage-1-financial-correctness/dark/31b-reopened-account-financial-hierarchy.png) |

Five protected finding examples:

- [CORE-01 overrun](screenshots/stage-1-financial-correctness/light/27a-core-01-budget-overrun-evidence.png)
- [CORE-02 mapping](screenshots/stage-1-financial-correctness/light/27b-core-02-budget-mapping-evidence.png)
- [CORE-03 duplicate](screenshots/stage-1-financial-correctness/light/27c-core-03-exact-duplicate-evidence.png)
- [CORE-04 required data](screenshots/stage-1-financial-correctness/light/27d-core-04-required-data-evidence.png)
- [CORE-05 reconciliation](screenshots/stage-1-financial-correctness/light/27e-core-05-reconciliation-evidence.png)

## 11. Engineering verification

| Check | Command | Result |
|---|---|---|
| Independent workbook oracle | `.venv/bin/python scripts/verify_stage1_financial_oracle.py --compact` | PASS |
| Stage 1 focused tests | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q tests/ui/test_integrated_financial_review.py tests/accessibility/test_financial_results_accessibility.py tests/unit/test_financial_validation.py tests/application/test_rule_management.py tests/integration/test_stage1_financial_oracle.py` | PASS — 30 passed |
| Full regression suite | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q` | PASS — 1,042 passed in 75.43s after final review remediation |
| Ruff | `.venv/bin/ruff check` over every Stage 1 Python file | PASS |
| Import architecture | `PYTHONPATH=src .venv/bin/lint-imports` | PASS — 3 contracts kept, 0 broken |
| Git whitespace | `git diff --check` | PASS |
| Launch smoke | `QT_QPA_PLATFORM=offscreen FINSIGHT_SMOKE=1 .venv/bin/python scripts/launch_mvp_demo.py --data-dir <temporary-directory>` | PASS |
| Screenshot qualification | `QT_QPA_PLATFORM=offscreen FINSIGHT_CAPTURE_WIDTH=1440 FINSIGHT_CAPTURE_HEIGHT=960 .venv/bin/python scripts/capture_mvp_screenshots.py initiatives/configurable-rule-engine-v2/verification/screenshots/stage-1-financial-correctness` | PASS — 130 screenshots |

## 12. Exact Stage 1 changed-file inventory

Runtime:

- `src/finsight/domain/financial_validation.py`
- `src/finsight/application/rule_management.py`
- `src/finsight/infrastructure/financial_review_repository.py`
- `src/finsight/delivery/desktop/controllers/app_controller.py`
- `src/finsight/delivery/desktop/components/charts.py`
- `src/finsight/delivery/desktop/views/financial_review_view.py`
- `src/finsight/delivery/desktop/theme/qss.py`

Tests and executable verification:

- `tests/unit/test_financial_validation.py`
- `tests/application/test_rule_management.py`
- `tests/ui/test_integrated_financial_review.py`
- `tests/accessibility/test_financial_results_accessibility.py`
- `tests/integration/test_stage1_financial_oracle.py`
- `scripts/verify_stage1_financial_oracle.py`
- `scripts/capture_mvp_screenshots.py`

Stage artifacts:

- `docs/STAGE-1-FINANCIAL-HIERARCHY-AND-CANONICAL-DATASET.md`
- `fixtures/STAGE-1-MANUAL-VALIDATION-ORACLE-2026-07-29.md`
- `tasks/STAGE-1-GOVERNED-IMPLEMENTATION-PLAN-2026-07-29.md`
- `verification/STAGE-1-INDEPENDENT-ORACLE-2026-07-29.json`
- this verification record
- final independent review record
- `verification/screenshots/stage-1-financial-correctness/` (130 PNG files)

This inventory is scoped to this Stage 1 request. The repository already
contained unrelated retained work and a dirty working tree; none was discarded.

## 13. Launch instructions

From the repository root:

```bash
.venv/bin/python scripts/launch_mvp_demo.py \
  --data-dir artifacts/mvp-hands-on-store
```

The supplied data directory persists reviews, rule versions, Validation Runs,
findings, evidence, audit history, and comparison state across application
restart. Use the approved fixtures under
`initiatives/configurable-rule-engine-v2/fixtures/`.

## 14. Known limitations

- Source ingestion remains intentionally limited to the approved `Original
  Budget` and `GED` XLSX layouts.
- The Budget source has no Department Number or reporting period; the approved
  intake contract resolves them from GED and workspace metadata.
- Account Name is the only approved expense-category label. No expense-type,
  business-unit, vendor-master, project, cost-center, location, or legal-entity
  hierarchy is inferred.
- Three-digit Budget group totals remain source controls, not an invented
  canonical parent layer.
- Ranked charts show a readable top subset; exact tables and account
  drill-down retain the complete population.
- The blank `GED!O87` makes the eligible GED total explicitly incomplete and
  makes amount-dependent results for that account `NOT_EVALUATED`.
- Configurable Stage 1 semantics use the governed `ged_amount_threshold`
  evaluator family. Adding a new semantic evaluator family requires a governed
  schema and trusted deterministic implementation; arbitrary executable
  expressions are rejected.
- Persisted results remain available if a source workbook later becomes
  unavailable, but direct raw-row navigation requires the preserved source.
- Ask Fin is visible but was not expanded. Windows packaging, installer
  qualification, and MSI generation remain out of scope.
- System mode followed the headless environment and resolved to Light. Native
  screen-reader smoke and Project Owner hands-on acceptance remain manual gates.

## 15. Gate statement

Independent review initially found one Medium chart-interaction defect. The
reconciliation chart now drills into the deterministic reconciliation-status
account group; keyboard activation through its exact-data table is covered by
the focused UI test. The bounded recheck passed with no remaining material
defect. See
[Independent Review — Stage 1 Financial Correctness](../reviews/REVIEW-2026-07-29-stage-1-financial-correctness.md).

Stage 1 does not authorize Ask Fin expansion or Windows packaging. This package
stops for Project Owner hands-on financial-correctness review.
