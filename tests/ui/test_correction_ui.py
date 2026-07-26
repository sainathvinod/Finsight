# Verifies: editable extraction review / correction UI (Product Owner workflow §10-11).
#   - Correctable cells on accepted rows are editable before verification; editing persists a
#     correction and re-renders the cell with a marker (not color alone) and the original in a tooltip.
#   - Reverting restores the original value.
#   - After verification the review is read-only (corrections are frozen).
import os

from tests.support import build_synthetic_ged, build_synthetic_budget


def _process(w, tmp_path):
    ged = os.path.join(str(tmp_path), "g.xlsx"); bud = os.path.join(str(tmp_path), "b.xlsx")
    build_synthetic_ged(ged); build_synthetic_budget(bud)
    w._c.create_review("2026-07", "July", "2026")
    w._c.upload("2026-07", ged, bud)
    w._c._s.workflow.process(w._c._session_for("2026-07"))
    w._c.select_review("2026-07")


def _amount_col(tab):
    # columns are ("status", ...normalized...); find the 'amount' column index.
    return list(tab._records.columns).index("amount")


def test_editing_a_cell_persists_a_correction_and_marks_it(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _process(w, tmp_path)
    verify = w._workspace.panel(4)
    verify.refresh()
    tab = verify._review.tab("GED")
    col = _amount_col(tab)
    tab.edit_cell(0, col, "13579")                       # user corrects the first accepted amount
    # A correction was persisted for this review...
    assert w._c.has_corrections("2026-07")
    corrections = w._c.corrections("2026-07")
    assert any(o.field == "amount" and o.current_value == "13579" for o in corrections)
    # ...and the re-rendered cell is marked as corrected (shape marker, not color) with the original.
    tab2 = verify._review.tab("GED")
    assert tab2._records.corrected_cells                 # at least one corrected cell
    assert tab2._records.originals                        # original preserved for compare/tooltip


def test_reverting_restores_original(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _process(w, tmp_path)
    verify = w._workspace.panel(4)
    verify.refresh()
    tab = verify._review.tab("GED")
    col = _amount_col(tab)
    tab.edit_cell(0, col, "222")
    assert w._c.has_corrections("2026-07")
    # Revert through the panel's handler (same path the context menu triggers).
    o = w._c.corrections("2026-07")[0]
    verify._on_revert(o.document_type, o.source_ref, o.field)
    assert not w._c.has_corrections("2026-07")            # effective correction cleared


def test_re_editing_a_corrected_account_never_captures_the_marker_glyph(window_factory, empty_db, tmp_path):
    # Regression (independent-review finding): the ✎ display marker must never leak into a saved
    # correction of a TEXT field (account). Re-editing an already-corrected account must store the
    # plain value, so the certified account code is exactly what the reviewer typed.
    from finsight.delivery.desktop.components.extraction_review import _CORRECTED_GLYPH
    w = window_factory(empty_db)
    _process(w, tmp_path)
    verify = w._workspace.panel(4)
    verify.refresh()
    tab = verify._review.tab("GED")
    acc = list(tab._records.columns).index("account")
    tab.edit_cell(0, acc, "6100")                        # first correction of the account
    verify.refresh()                                     # re-render -> the cell now shows "✎ 6100"
    tab2 = verify._review.tab("GED")
    tab2.edit_cell(0, acc, "6200")                       # re-edit the already-corrected cell
    stored = [o for o in w._c.corrections("2026-07") if o.field == "account"]
    assert stored, "account correction should be recorded"
    assert all(_CORRECTED_GLYPH not in o.current_value for o in stored)
    assert stored[-1].current_value == "6200"            # exactly what was typed, no glyph


def test_review_is_read_only_after_verification(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _process(w, tmp_path)
    w._c.verify("2026-07")                                # freeze the dataset
    verify = w._workspace.panel(4)
    verify.refresh()
    tab = verify._review.tab("GED")
    # Editing is disabled: the amount cell item is not editable once verified.
    col = _amount_col(tab)
    assert not tab._model.item(0, col).isEditable()
