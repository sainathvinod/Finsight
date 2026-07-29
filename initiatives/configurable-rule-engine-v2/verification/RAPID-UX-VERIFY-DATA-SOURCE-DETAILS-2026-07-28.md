# Rapid UX Verification — Verify Data Source Details

- **Date:** 2026-07-28
- **Lane:** Rapid UX
- **Scope:** Verify Data row-number presentation, on-demand source details,
  and table-height adjustment only
- **Status:** Ready for Project Owner hands-on review

## Lane entry checklist

1. Architecture, layer direction, or runtime dependencies changed: **No**
2. Extraction, business rules, calculations, validation, or financial meaning
   changed: **No**
3. Persistence, source lineage, data models, edit/audit behavior, identity,
   security, or privacy changed: **No**
4. Workflow state, navigation destination, governed action availability,
   permissions, or task outcome changed: **No**
5. Requirements, ADRs, architecture, governance, or release artifacts require
   revision: **No**

## Implemented presentation changes

- Hid the Qt table's unlabeled internal row header on both Verify Data tables.
- Retained `Source Row` as the sole visible row identity; its values continue
  to come directly from the source Excel worksheet.
- Removed the always-visible Selected Cell Evidence card.
- Added a compact `View Source` action to the data-tab header.
- Added an on-demand Source Details dialog with plain-language source file,
  worksheet, row, field/column, original value, reviewed value, and edited
  status.
- Kept internal record keys and raw Excel references inside a collapsed
  `View technical details` section.
- Removed raw source references from ordinary cell tooltips.
- Increased the data-tab minimum height from 360 to 430 pixels while keeping
  the confirmation section directly below the table.
- Reused source filenames already present in the authorized reconstruction
  inputs; no additional repository read or audit event was introduced.

## Files changed

- `src/finsight/delivery/desktop/controllers/app_controller.py`
- `src/finsight/delivery/desktop/views/financial_review_view.py`
- `tests/ui/test_source_intake.py`
- `tests/accessibility/test_source_intake_accessibility.py`
- `scripts/capture_mvp_screenshots.py`
- `initiatives/configurable-rule-engine-v2/verification/RAPID-UX-VERIFY-DATA-SOURCE-DETAILS-2026-07-28.md`
- `artifacts/design-qa/rapid-ux-verify-data/light/01-budget-data.png`
- `artifacts/design-qa/rapid-ux-verify-data/light/02-ged-data.png`
- `artifacts/design-qa/rapid-ux-verify-data/light/03-source-details-open.png`

## Targeted verification

- Impacted Verify Data UI and accessibility selection: **4 passed**
- Application launch smoke: **passed**
- Focused visual review of all three requested 1280 × 900 states:
  **passed with no material issue**
- Full regression suite: **not run, by Rapid UX Lane policy**
- Architecture/governance review: **not run; no governed impact was introduced**

## Screenshot evidence

- Budget Data:
  `artifacts/design-qa/rapid-ux-verify-data/light/01-budget-data.png`
- GED Data:
  `artifacts/design-qa/rapid-ux-verify-data/light/02-ged-data.png`
- Source Details open:
  `artifacts/design-qa/rapid-ux-verify-data/light/03-source-details-open.png`

## Known limitations

- The screenshots cover the requested Light appearance at 1280 × 900.
  Theme implementation was not changed.
- Native screen-reader behavior remains a hands-on verification item; keyboard
  operation, accessible names/descriptions, focus return, and the collapsed
  technical-details state are covered by the focused automated test.
