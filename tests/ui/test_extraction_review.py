# Verifies: per-source extraction review before verification (Product Owner workflow §9).
#   - One tab per provided source (GED, Budget Tracker), each listing EVERY extracted record.
#   - Every record carries its lineage (the `source` cell = file!row).
#   - Per-tab search filters the records; row status is shown as text (not color alone).
#   - A captured-but-not-extracted invoice is named as omitted, never implied to have run.
# Authority: F-01-09, FR-016/FR-027, S-07. No invented rule.
import os

from tests.support import build_synthetic_ged, build_synthetic_budget


def _files(tmp_path):
    ged = os.path.join(str(tmp_path), "ged.xlsx"); bud = os.path.join(str(tmp_path), "budget.xlsx")
    build_synthetic_ged(ged); build_synthetic_budget(bud)
    return ged, bud


def _process(w, tmp_path, invoice=None):
    ged, bud = _files(tmp_path)
    w._c.create_review("2026-07", "July", "2026")
    w._c.upload("2026-07", ged, bud, invoice_path=invoice)
    w._c._s.workflow.process(w._c._session_for("2026-07"))
    w._c.select_review("2026-07")


def test_review_has_a_tab_per_source_with_all_records(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _process(w, tmp_path)
    verify = w._workspace.panel(4)
    verify.refresh()
    names = verify._review.source_names()
    assert "GED" in names and "Budget Tracker" in names
    # ALL records shown (not capped at the representative 10): match the read model's totals.
    records, _omitted = w._c.extraction_review("2026-07")
    by_type = {r.source_type: r for r in records}
    for name in names:
        tab = verify._review.tab(name)
        assert tab.total_rows() == by_type[name].accepted_rows + by_type[name].quarantined_rows


def test_records_carry_lineage(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _process(w, tmp_path)
    records, _ = w._c.extraction_review("2026-07")
    ged = next(r for r in records if r.source_type == "GED")
    assert "source" in ged.columns and "status" in ged.columns
    # Each row's lineage cell points back to the source file/row (e.g. "GED!R..").
    src_idx = ged.columns.index("source")
    assert all(row[src_idx] for row in ged.rows)


def test_search_filters_records(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _process(w, tmp_path)
    verify = w._workspace.panel(4)
    verify.refresh()
    tab = verify._review.tab("GED")
    total = tab.total_rows()
    assert total >= 1
    tab.set_filter("zzzz-no-such-record")
    assert tab.visible_rows() == 0
    tab.set_filter("")
    assert tab.visible_rows() == total


def test_captured_invoice_is_named_as_omitted_not_analyzed(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    inv = os.path.join(str(tmp_path), "inv.pdf"); open(inv, "wb").write(b"%PDF x")
    _process(w, tmp_path, invoice=inv)
    _records, omitted = w._c.extraction_review("2026-07")
    assert any(name == "inv.pdf" and "not extracted" in note.lower()
               for (_st, name, note) in omitted)
