# Stage 1 Financial Hierarchy and Canonical Dataset

- Status: Implemented and verified
- Date: 2026-07-29
- Scope: approved `Sample_Budget_Report.xlsx` and `Sample_GED_Report.xlsx`
- Canonical schema: `CFD-1.0`
- Financial control schema: `FCR-1.0`

## Supported hierarchy

```text
Review
└── Department
    └── Account
        ├── Account name / expense category
        ├── Budget values
        │   ├── BGT
        │   ├── ATD
        │   ├── ETC
        │   ├── EAC
        │   └── DELTA
        └── GED transactions
            ├── Fiscal period
            ├── Journal number and date
            ├── Vendor
            ├── Invoice and check information
            ├── Journal and line descriptions
            └── Amount
```

`Account Name` is the source-supported expense-category label. FinSight does
not invent an additional expense-type layer. A mapped account uses the Budget
Account Name as the canonical account label; an unmapped GED scope retains its
GED Account Name as evidence.

The Budget file contains no dedicated Department Number or reporting-period
column. Department identity and period are established during the approved
intake gate from the GED report and review workspace. The exact source
Department Name is retained; FinSight does not expand or silently correct
truncated source text.

## Matching and grouping

| Purpose | Deterministic key |
|---|---|
| Budget-to-GED join | normalized Department Number + six-digit Account Number |
| Budget analysis | Department Number + Account Number |
| GED account analysis | Department Number + Account Number |
| Fiscal-period analysis | Fiscal Period |
| Vendor analysis | Vendor Name; blank values are labeled `No vendor recorded` |
| Duplicate control | canonical typed values of all 15 GED fields |

The canonical account population is the union of:

- every valid six-digit Budget detail account under the intake-approved
  Department Number; and
- every GED Department Number + Account Number combination, including a
  combination that does not map to Budget.

The approved fixtures therefore produce 72 canonical scopes: 71 mapped Budget
accounts and one intentional unmapped GED scope (`00-0999 / 527015`).

## Exact source fields

### Budget — worksheet `Original Budget`

| Column | Field | Canonical treatment |
|---|---|---|
| A | Account Number | account key and row classification |
| B | Account Name | account/category label |
| C | BGT | planned Budget |
| D | ATD | Budget actual-to-date |
| E | ETC | estimate to complete |
| F | EAC | estimate at completion; checked as `ATD + ETC` |
| G | DELTA | Budget variance; checked as `BGT - EAC` |
| H | Notes | source context and reviewed-value evidence |

### GED — worksheet `GED`

| Column | Field | Canonical treatment |
|---|---|---|
| A | Department Number | join key and required field |
| B | Department Name | department evidence and duplicate fingerprint |
| C | Account Number | join key and required field |
| D | Account Name | transaction category evidence |
| E | Fiscal Period | eligibility, required field, and period analysis |
| F | Journal Number | required field and journal traceability |
| G | Journal Date | required field and date evidence |
| H | Invoice Amount | invoice evidence when applicable |
| I | Check Number | payment evidence |
| J | Invoice Date | invoice evidence |
| K | Vendor Name | vendor analysis |
| L | Agency | transaction evidence |
| M | Journal Description | transaction explanation |
| N | Journal Line Description | line-level explanation |
| O | Amount | financial aggregation and validation |

All 23 approved source fields are present in the recorded field-coverage
projection. Each is displayed in the complete Budget or GED table, available
in account/source drill-down, used by a documented rule or calculation, or
identified as evidence without an independent pass/fail effect. No approved
field is silently excluded.

## Row inclusion and exclusion

### Budget

- Header: row 1; never a financial record.
- Included: 71 rows whose Account Number is exactly six digits.
- Excluded from detail aggregation:
  - 11 three-digit group-total rows;
  - 11 separator rows;
  - one Grand Total row.
- Group and Grand Total rows remain visible source controls. They are never
  added to detail rows, preventing double counting.

### GED

- Report metadata: rows 1–6.
- Header: row 7.
- Included: 258 transaction rows beginning at row 8.
- Excluded from transaction aggregation:
  - 31 `TOTAL FOR ACCOUNT` rows;
  - one `TOTAL FOR DEPARTMENT` row;
  - two blank rows.
- Excluded total rows retain their displayed values as source evidence but are
  not transactions and are never added to GED spend.
- The missing `GED!O87` Amount is not replaced with zero. Its account retains
  the parseable subtotal as evidence, while complete account totals and
  dependent rules are `NOT_EVALUATED`.

## Formula and decimal policy

- All financial truth uses Python `Decimal` quantized to two fractional digits.
- Binary floating point is not used for totals, comparisons, utilization,
  findings, or exact table values.
- Charts receive recorded integer-cent projections. Conversion to a drawing
  coordinate does not change the sealed exact values shown in each chart's
  accessible `Exact data` table.
- Budget formula cells retain their original formula and cached value in source
  lineage. The deterministic required-data control independently verifies:
  - `EAC = ATD + ETC`; and
  - `DELTA = BGT - EAC`.
- The approved fixtures contain no Budget formula-relationship failure.

## Canonical account contract

Every `CFD-1.0` account record contains:

- Department Number and Department Name;
- Account Number and Account Name;
- BGT, ATD, ETC, EAC, and DELTA as exact cents and display labels;
- parseable GED subtotal;
- complete Summed GED Amount or explicit `Not evaluated`;
- GED transaction count and missing/invalid input counts;
- ATD-to-GED difference;
- remaining Budget and over-budget amount;
- Budget utilization percentage;
- reconciliation status;
- all active-rule outcomes;
- finding count and badges;
- source Budget record and row;
- every contributing GED record and row;
- original-versus-edited provenance.

The same persisted projection is consumed by validation result tables, charts,
summaries, findings, exports, reports, retained-run comparison, and future Ask
Fin grounding. Delivery code selects and renders recorded fields; it does not
independently aggregate Budget or GED values.

## Source lineage

Every source record carries:

- source role and exact uploaded filename through the Validation Run basis;
- worksheet;
- source Excel row;
- field-to-cell mapping;
- original extracted value;
- current reviewed value;
- edited/original value origin.

Findings retain all implicated source records. Multi-row evidence, including
the duplicate at GED rows 65–66, is selectable rather than reduced to the first
record.

## Unavailable hierarchy levels

The supplied reports do not provide an approved:

- enterprise business-unit hierarchy above Department;
- expense type distinct from Account Name;
- vendor master hierarchy;
- project, cost center, location, or legal-entity dimension;
- deterministic parent/child relationship among three-digit Budget group
  totals and six-digit detail accounts beyond their source ordering.

FinSight therefore does not invent these levels. They remain possible future
configurable mappings under a governed schema extension.
