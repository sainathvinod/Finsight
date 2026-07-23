# Pattern — Review Selected Before Analysis

**Layer:** pattern (leaf). References standards and specs, never agents. Not a product requirement.
**Governs against:** [data-verification.md](../../standards/data-verification.md); `P-9`, `FR-026`, `DEC-027`.

## Convention
No financial dashboard, findings view, or analysis appears before a review is selected and its data is verified/certified. Selection and verification gate the analysis surface.

## Guidelines
- On launch, present review selection (create / open past), not a financial dashboard.
- Analysis and findings render only after certification of the review's data.
- Full financial review precedes findings; findings precede the leadership summary.

## Checks
- Attempting to view findings without a selected, certified review yields no financial output.
