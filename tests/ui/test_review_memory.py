# Verifies: local structured review memory (Product Owner §16; ADR-009).
#   Deterministic, cited, review-isolated, local-only. Written by the deterministic comparison path
#   (never the model), on analysis, when a prior review exists. Never changes deterministic results.
import os

from tests.support import build_synthetic_ged, build_synthetic_budget


def _analyze(w, cid, month, tmp_path, bump=False):
    ged = os.path.join(str(tmp_path), f"g{cid}.xlsx"); bud = os.path.join(str(tmp_path), f"b{cid}.xlsx")
    build_synthetic_ged(ged); build_synthetic_budget(bud)
    w._c.create_review(cid, month, "2026")
    w._c.upload(cid, ged, bud)
    w._c._s.workflow.process(w._c._session_for(cid))
    if bump:                                              # distinct data so finding IDs don't collide
        records, _ = w._c.extraction_review(cid)
        rec = records[0]; acol = list(rec.columns).index("amount")
        w._c.save_correction(cid, "GED", rec.source_refs[0], "amount",
                             rec.rows[0][acol], str(int(float(rec.rows[0][acol])) + 1))
    w._c.verify(cid); w._c.analyze(cid)


def test_memory_written_from_comparison_is_cited_and_isolated(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _analyze(w, "2026-06", "June", tmp_path)
    _analyze(w, "2026-07", "July", tmp_path, bump=True)
    mem = w._c.review_memory("2026-07")
    assert mem, "expected system-derived memory for the recurring account"
    e = mem[0]
    assert e.source_type == "comparison" and e.source_id.startswith("account:")   # cited
    assert "6100" in e.content
    # Review-isolated: the earlier review (no prior) has no comparison memory.
    assert w._c.review_memory("2026-06") == []


def test_memory_is_deterministic_and_idempotent(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _analyze(w, "2026-06", "June", tmp_path)
    _analyze(w, "2026-07", "July", tmp_path, bump=True)
    before = len(w._c.review_memory("2026-07"))
    w._c.record_review_memory("2026-07")                  # re-run
    assert len(w._c.review_memory("2026-07")) == before   # no duplicates


def test_memory_shows_in_ask_fin_review_mode(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _analyze(w, "2026-06", "June", tmp_path)
    _analyze(w, "2026-07", "July", tmp_path, bump=True)
    w._c.select_review("2026-07")
    w.toggle_ask_fin()
    panel = w.ask_fin_drawer()
    assert any("6100" in note for note in panel.remembered_notes())


def test_memory_does_not_change_deterministic_results(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _analyze(w, "2026-06", "June", tmp_path)
    _analyze(w, "2026-07", "July", tmp_path, bump=True)
    findings_before = len(w._c.findings("2026-07"))
    w._c.record_review_memory("2026-07")                  # writing memory again...
    assert len(w._c.findings("2026-07")) == findings_before   # ...never touches findings
