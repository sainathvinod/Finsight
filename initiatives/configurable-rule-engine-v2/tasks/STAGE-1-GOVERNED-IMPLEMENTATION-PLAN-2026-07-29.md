# Stage 1 Governed Implementation Plan

- Status: Executed
- Date: 2026-07-29
- Lane: Governed

## Increment

1. Inspect the approved Budget/GED structures and freeze row and field
   contracts.
2. Build one exact Department Number + Account Number canonical dataset in the
   deterministic domain layer.
3. Make CORE-01 and CORE-05 consume that canonical aggregation, preserving
   incomplete-input semantics.
4. Record exact financial controls, full field coverage, account hierarchy,
   vendor, period, polarity, transaction, and comparison projections with the
   immutable Validation Run.
5. Enrich every rule result and Finding with its exact rule version.
6. Preserve immutable prior runs and classify added, removed, and changed
   findings during comparison.
7. Validate configurable thresholds before immutable Draft persistence and
   isolate administrative Drafts from ordinary review users.
8. Rebuild Results as interactive projections with exact-data alternatives,
   account drill-down, multi-record evidence, and source navigation.
9. Verify against a direct-OOXML `Decimal` oracle that imports no FinSight code.
10. Run focused tests, full regression, screenshot qualification, and one
    independent financial-correctness review.

## Boundaries retained

- No Ask Fin expansion.
- No Windows packaging, MSI, or installer work.
- No source-workbook mutation.
- No arbitrary expressions, Python, SQL, or executable user-authored rules.
- No unapproved accounting hierarchy or expense-type inference.
