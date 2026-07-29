# Stage 1 Manual Validation Oracle

- Status: PASS
- Date: 2026-07-29
- Budget SHA-256:
  `bf40584183c564d91831214781969422d77d50439989f75750f0bdbe2bfa2b14`
- GED SHA-256:
  `2213e3f1b10fee56fb4538112250fe37fbdaf36eb5e299fbfe6d17bd0f10603c`
- Independent oracle:
  [`STAGE-1-INDEPENDENT-ORACLE-2026-07-29.json`](../verification/STAGE-1-INDEPENDENT-ORACLE-2026-07-29.json)
- Oracle SHA-256:
  `63637b6e2b18b15f73d5f087e734a7715eb64f9790195944c1df0d94de9ed06e`

## Independence method

`scripts/verify_stage1_financial_oracle.py` opens the two XLSX ZIP packages and
reads workbook and worksheet XML with the Python standard library. It imports
no FinSight module and no spreadsheet library. It classifies rows from the raw
source values, evaluates relationships with `Decimal`, and compares observed
facts with explicit expected controls.

The 2,530-line JSON artifact contains the expected and observed values for all
71 Budget account scopes, their GED source-row populations, all total and row
controls, the known synthetic issues, and the complete five-rule outcome
matrix. A nonmatching control makes the verifier exit nonzero.

Run:

```bash
.venv/bin/python scripts/verify_stage1_financial_oracle.py --compact
```

## Exact totals control matrix

| Control | Formula | Expected | FinSight actual | Difference | Result |
|---|---|---:|---:|---:|---|
| Total Budget BGT | Sum C on 71 six-digit detail rows | $10,372,000.00 | $10,372,000.00 | $0.00 | PASS |
| Total Budget ATD | Sum D on 71 six-digit detail rows | $3,500,095.00 | $3,500,095.00 | $0.00 | PASS |
| Total Budget ETC | Sum E on 71 six-digit detail rows | $5,882,000.00 | $5,882,000.00 | $0.00 | PASS |
| Total Budget EAC | Sum F on 71 six-digit detail rows | $9,382,095.00 | $9,382,095.00 | $0.00 | PASS |
| Total Budget DELTA | Sum G on 71 six-digit detail rows | $989,905.00 | $989,905.00 | $0.00 | PASS |
| Parseable eligible GED Amount | Sum O on GED transaction rows only | $3,500,095.00 | $3,500,095.00 | $0.00 | PASS |
| Mapped GED Amount | Eligible GED on exact Budget keys | $3,498,245.00 | $3,498,245.00 | $0.00 | PASS |
| Unmapped GED Amount | Eligible GED without exact Budget key | $1,850.00 | $1,850.00 | $0.00 | PASS |
| Excluded GED transaction Amount | Excluded transaction population | $0.00 | $0.00 | $0.00 | PASS |

The parseable GED total is explicitly incomplete because one of 258
transaction Amounts is blank. The source account-total and department-total
rows display a combined $7,000,190.00, but that amount is presentation evidence
and is excluded to prevent double counting.

## Row controls

| Source | Row type | Expected | Actual | Result |
|---|---|---:|---:|---|
| Budget | detail | 71 | 71 | PASS |
| Budget | group total | 11 | 11 | PASS |
| Budget | separator | 11 | 11 | PASS |
| Budget | grand total | 1 | 1 | PASS |
| GED | transaction | 258 | 258 | PASS |
| GED | account total | 31 | 31 | PASS |
| GED | department total | 1 | 1 | PASS |
| GED | blank | 2 | 2 | PASS |
| GED | missing/unparseable transaction Amount | 1 | 1 | PASS |

All 71 Budget detail rows satisfy `EAC = ATD + ETC` and
`DELTA = BGT - EAC`. No formula-relationship failure exists in this fixture.

## Known synthetic issue matrix

| Scenario | Expected control | FinSight actual | Difference | Result |
|---|---|---|---|---|
| Budget overrun | Account 555035; Budget row 91; BGT $1,100,000.00; GED $1,250,000.00; overrun $150,000.00; 113.64% utilization | Exact match | None | PASS |
| Duplicate | GED rows 65–66; Account 533003; $82.50 duplicate-copy exposure; all 15 GED fields match | Exact match | None | PASS |
| Required Amount | `GED!O87` blank; Account 537035 | Exact match; amount is not replaced with zero | None | PASS |
| Invalid mapping | GED row 43; `00-0999 / 527015`; $1,850.00 | Exact match | None | PASS |
| Consequent reconciliation | Budget row 11, `00-0245 / 527015`; ATD $1,850.00; GED $0.00; difference $1,850.00 | Exact match | $0.00 | PASS |
| Dependent completeness | Account 537035 overrun and reconciliation are `NOT_EVALUATED` because row 87 Amount is blank | Exact match | None | PASS |

The duplicate fingerprint comparison is:

| GED field | Row 65 | Row 66 |
|---|---|---|
| Department Number | 00-0245 | 00-0245 |
| Department Name | Applications Enginee | Applications Enginee |
| Account Number | 533003 | 533003 |
| Account Name | Transportation - Employee | Transportation - Employee |
| Fiscal Period | 2026-02 | 2026-02 |
| Journal Number | PCARD_0126 | PCARD_0126 |
| Journal Date | 2026-02-28 | 2026-02-28 |
| Invoice Amount | blank | blank |
| Check Number | . | . |
| Invoice Date | . | . |
| Vendor Name | blank | blank |
| Agency | 9999COR | 9999COR |
| Journal Description | SH - MONTHLY PCARD IMPORT | SH - MONTHLY PCARD IMPORT |
| Journal Line Description | T.Hasan 01/15/26 Lyft *ri | T.Hasan 01/15/26 Lyft *ri |
| Amount | $82.50 | $82.50 |

## Five-rule expected-versus-actual matrix

Stable Core IDs retain the established product numbering even though this
document presents reconciliation first.

| Rule | Expected PASS | Expected FAIL | Expected NOT_EVALUATED | FinSight actual | Result |
|---|---:|---:|---:|---|---|
| CORE-05 Budget-to-GED Reconciliation | 69 | 1 | 1 | 69 / 1 / 1 | PASS |
| CORE-01 Budget Overrun | 69 | 1 | 1 | 69 / 1 / 1 | PASS |
| CORE-02 Valid Account Coding | 257 | 1 | 0 | 257 / 1 / 0 | PASS |
| CORE-04 Complete and Correct Data | 328 | 1 | 0 | 328 / 1 / 0 | PASS |
| CORE-03 Duplicate Transactions | 256 | 1 | 0 | 256 / 1 / 0 | PASS |

Total scope results:

- 986 evaluated ledger entries;
- 979 PASS;
- 5 FAIL;
- 2 NOT_EVALUATED;
- 5 Findings.

Expected and actual Review status:

- Overall: `Incomplete`;
- RAG: `At Risk (Red)`;
- Findings: four High and one Medium;
- Budget Overrun findings: one;
- Valid Mapping findings: one;
- Required Data findings: one;
- Reconciliation findings: one;
- Duplicate findings: one.

## Traceability conclusion

Every amount in this matrix traces to:

- the Budget detail row and financial column used;
- every contributing GED transaction row and Amount cell;
- the exact matching key;
- the immutable Rule ID and version;
- the retained Validation Run and Rule Set version.

No control difference remains.
