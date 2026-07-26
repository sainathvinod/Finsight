# Verifies: historical comparison over stored reviews (Product Owner workflow §15).
#   - Deterministic, descriptive: reports finding-count delta and accounts newly-flagged / resolved /
#     recurring as FACTS over the two reviews' stored findings. No new metric or threshold.
#   - Compares to the immediately-prior ANALYZED review; None when there is no prior.
import os

from tests.support import build_synthetic_ged, build_synthetic_budget
from finsight.application.read_models.history import compare


class _F:
    def __init__(self, account): self.account = account


def test_compare_reports_deltas_as_facts():
    cur = [_F("6100"), _F("6200")]
    prior = [_F("6100"), _F("9999")]
    c = compare("July 2026", "June 2026", cur, prior)
    assert c.finding_delta == 0
    assert c.newly_flagged_accounts == ("6200",)
    assert c.resolved_accounts == ("9999",)
    assert c.recurring_accounts == ("6100",)
    assert any("6200" in ln for ln in c.change_lines)


def _analyze(w, cid, month, tmp_path, bump=False):
    ged = os.path.join(str(tmp_path), f"g{cid}.xlsx"); bud = os.path.join(str(tmp_path), f"b{cid}.xlsx")
    build_synthetic_ged(ged); build_synthetic_budget(bud)
    w._c.create_review(cid, month, "2026")
    w._c.upload(cid, ged, bud)
    w._c._s.workflow.process(w._c._session_for(cid))
    if bump:
        # Perturb this period's data by +1 on the first GED amount so its verified fingerprint (and
        # thus finding IDs, which embed the fingerprint) differ from the other period — real months
        # never share identical data. Still leaves account 6100 over budget, so it stays flagged.
        records, _ = w._c.extraction_review(cid)
        ged_rec = records[0]
        acol = list(ged_rec.columns).index("amount")
        src, orig = ged_rec.source_refs[0], ged_rec.rows[0][acol]
        w._c.save_correction(cid, "GED", src, "amount", orig, str(int(float(orig)) + 1))
    w._c.verify(cid)
    w._c.analyze(cid)


def test_controller_compares_to_prior_analyzed_review(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _analyze(w, "2026-06", "June", tmp_path)
    _analyze(w, "2026-07", "July", tmp_path, bump=True)
    comp = w._c.historical_comparison("2026-07")
    assert comp is not None
    assert comp.prior_period == "June 2026" and comp.current_period == "July 2026"
    # Same synthetic data -> the flagged account recurs; nothing manufactured.
    assert "6100" in comp.recurring_accounts


def test_no_prior_returns_none(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _analyze(w, "2026-07", "July", tmp_path)
    assert w._c.historical_comparison("2026-07") is None   # earliest analyzed review


def test_overview_shows_comparison_section(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _analyze(w, "2026-06", "June", tmp_path)
    _analyze(w, "2026-07", "July", tmp_path, bump=True)
    w._c.select_review("2026-07")
    ov = w.view("overview"); ov.refresh()
    lines = ov.comparison_lines()
    assert lines and any("June 2026" in ln for ln in lines)
