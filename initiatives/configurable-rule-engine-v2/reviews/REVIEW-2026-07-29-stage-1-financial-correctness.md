# Independent Review — Stage 1 Financial Correctness

- **Date:** 2026-07-29
- **Initiative:** Configurable Rule Engine V2
- **Reviewer:** Codex independent read-only agent
  `/root/stage1_independent_review`
- **Scope:** financial hierarchy, canonical truth, exact controls, five protected
  rules, configurable-rule revalidation, findings, analytics, source evidence,
  accessibility, and retained-run reproducibility
- **Git HEAD:** `a298040a8408c04342818a65a186a0d72c87956a`
- **Snapshot qualification:** dirty working-tree snapshot; no immutable final
  commit is claimed
- **Initial verdict:** FAIL — one Medium material interaction defect
- **Final verdict:** **PASS — MATERIAL DEFECT CLOSED**
- **Hands-on acceptance:** Pending Project Owner

## Evidence independently examined

- the complete Stage 1 request and direct configurable-rule additions;
- financial engine, rule lifecycle, persistence, run comparison, charts,
  drill-down, and evidence implementation;
- hierarchy specification, manual oracle, consolidated verification, and the
  independent OOXML oracle JSON;
- 130 screenshots: 65 Light and 65 Dark;
- all five protected finding evidence examples;
- optional-rule edit/revalidation comparison and reopened results; and
- approved Budget/GED fixture fingerprints.

## Independent commands

```bash
.venv/bin/python scripts/verify_stage1_financial_oracle.py --compact
```

**PASS.** Exact totals, row classifications, five known source scenarios, and
all five rule matrices matched.

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q \
  tests/unit/test_financial_validation.py \
  tests/application/test_rule_management.py \
  tests/integration/test_stage1_financial_oracle.py \
  tests/ui/test_integrated_financial_review.py \
  tests/accessibility/test_financial_results_accessibility.py
```

**PASS — 30 passed in 8.07s.**

```bash
.venv/bin/ruff check \
  src/finsight/delivery/desktop/views/financial_review_view.py \
  tests/ui/test_integrated_financial_review.py
```

**PASS — all checks passed.**

## Initial material finding

| ID | Severity | Observation | Required correction | Final status |
|---|---|---|---|---|
| IR-ST1-01 | Medium | The Budget-vs-GED `Reconciled versus unreconciled accounts` chart exposed mouse/keyboard activation, but its handler was a no-op. This violated the explicit requirement that every chart drill into financial hierarchy. | Connect the chart to deterministic reconciliation-status drill-down and add a keyboard assertion using the exact-data alternative. | **CLOSED** |

## Remediation and bounded recheck

The chart now calls `_open_reconciliation_status_group`. The focused UI test
selects the exact-data `Different` row, presses Enter, and verifies that the
account hierarchy opens `00-0245 / 527015`, the sole reconciliation failure in
the approved fixture.

The reviewer re-read the change, reran the 30-test Stage 1 selection and Ruff,
and issued a final **PASS**.

## Financial-correctness conclusion

The reviewer independently confirmed:

- account `555035`: BGT $1,100,000.00, GED $1,250,000.00, overrun
  $150,000.00, 113.64% utilization;
- GED rows 65–66: all 15 approved fields match, with both rows retained;
- `GED!O87`: blank is never converted to zero; CORE-04 fails and dependent
  CORE-01/CORE-05 account outcomes are `NOT_EVALUATED`;
- GED row 43: `00-0999 / 527015`, $1,850.00, invalid mapping;
- Budget row 11: `00-0245 / 527015`, ATD $1,850.00, GED $0.00,
  reconciliation difference $1,850.00;
- optional-rule add, edit, disable, revalidate, added/removed/changed finding
  comparison, immutable history, exact rule versions, updated charts/summaries,
  and restart reproducibility; and
- exact `Decimal` financial truth rendered from sealed cents/display
  projections rather than independently recalculated by the UI.

## Known evidence limitations

- Static screenshots do not prove interaction; Qt keyboard and drill-down tests
  provide that evidence.
- Native screen-reader and real operating-system System-theme checks remain
  hands-on activities.
- The reviewer reran the focused 30-test Stage 1 selection, not the separately
  recorded full regression suite.
- Ask Fin expansion and Windows packaging were correctly excluded.

## Final verdict

**PASS — no material Stage 1 defect remains.**

Project Owner hands-on acceptance is still required. This review does not
authorize Ask Fin expansion or Windows packaging.
