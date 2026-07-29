# V2 Test Fixtures

This directory contains the Project Owner-approved synthetic workbooks used to
verify the exact `SLV-001` source-layout contract. The master generated
workbooks under `outputs/` remain untouched.

| Fixture | Expected worksheet | Expected record count | SHA-256 |
|---|---|---:|---|
| `Sample_Budget_Report.xlsx` | `Original Budget` | 71 six-digit Budget detail records | `bf40584183c564d91831214781969422d77d50439989f75750f0bdbe2bfa2b14` |
| `Sample_GED_Report.xlsx` | `GED` | 258 GED transaction candidates | `2213e3f1b10fee56fb4538112250fe37fbdaf36eb5e299fbfe6d17bd0f10603c` |

Expected report-level identity:

- Department Number: `00-0245`
- Department Name: `Applications Enginee` (the exact truncated source value)
- GED reporting period: May 2026
- Budget reporting period: workspace assigned; the Budget layout has no source period

The intentional GED row with Department Number `00-0999` is transaction-level
test data and must not redefine the report-level department. The missing GED
Amount remains a transaction candidate. Neither condition is a Workflow 2
source-layout rejection.

The cross-rule expected oracle and executed automated actual-results ledger for
the final remediation are recorded in
[MVP-REMEDIATION-SYNTHETIC-TEST-MATRIX-2026-07-28.md](MVP-REMEDIATION-SYNTHETIC-TEST-MATRIX-2026-07-28.md).

The independently derived Stage 1 controls, exact totals, source-row scenarios,
and five-rule matrix are recorded in
[STAGE-1-MANUAL-VALIDATION-ORACLE-2026-07-29.md](STAGE-1-MANUAL-VALIDATION-ORACLE-2026-07-29.md).
