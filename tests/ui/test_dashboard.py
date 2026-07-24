# Verifies: Phase 5.3 cross-review Dashboard + portfolio read model. Deterministic; no AI; no
# workflow mutation; no repository/network. Pure read model tested directly; the view via a fake
# controller; navigation via the real window.
import os

import pytest

from finsight.application.read_models.views import FindingView, ReviewStatusView
from finsight.application.read_models.portfolio import PortfolioQueryService, PortfolioSummary
from finsight.delivery.desktop.views.dashboard_view import DashboardView

pytestmark = pytest.mark.ui


def _rv(cid, month, state, findings):
    return ReviewStatusView(cycle_id=cid, month=month, year="2026", state=state, finding_count=findings)


def _f(fid, sev):
    return FindingView(id=fid, account="6100", rule_id="R-BUD-02", severity=sev, period="2026-07",
                       finding_type="variance", evidence={}, source_refs=[], state="New")


class FakeReviews:
    def __init__(self, rows):
        self._rows = rows
    def list_with_status(self):
        return list(self._rows)


class FakeFindings:
    def __init__(self, by_cid):
        self._by = by_cid
    def list_for_cycle(self, cid):
        return list(self._by.get(cid, []))


def _portfolio():
    reviews = FakeReviews([
        _rv("2026-07", "July", "Exported", 1),
        _rv("2026-06", "June", "Exported", 0),      # clean completed → excluded from attention
        _rv("2026-05", "May", "Analyzed", 1),
        _rv("2026-04", "April", "Intake", 0),       # in progress → attention
    ])
    findings = FakeFindings({
        "2026-07": [_f("F1", "Critical")],
        "2026-05": [_f("F2", "High")],
    })
    return PortfolioQueryService(reviews, findings).summary()


# ===================== portfolio read model (pure) =====================
class TestPortfolioSummary:
    def test_totals(self):
        s = _portfolio()
        assert s.total_reviews == 4
        assert s.total_findings == 2
        assert s.critical_findings == 1
        assert s.high_findings == 1
        assert s.completed_reviews == 2

    def test_by_state(self):
        assert _portfolio().reviews_by_state == {"Exported": 2, "Analyzed": 1, "Intake": 1}

    def test_attention_includes_severity_and_in_progress_excludes_clean_completed(self):
        s = _portfolio()
        ids = [a.cycle_id for a in s.attention_items]
        assert ids == ["2026-07", "2026-05", "2026-04"]        # critical, then high, then in-progress
        assert "2026-06" not in ids                             # clean Exported excluded
        assert s.reviews_needing_attention == 3

    def test_attention_reasons_use_authoritative_facts(self):
        by_id = {a.cycle_id: a.reason for a in _portfolio().attention_items}
        assert "critical" in by_id["2026-07"].lower()
        assert "high" in by_id["2026-05"].lower()
        # 2026-04 is in Intake → stage-specific readiness blocker derived from persisted state
        assert "not processed" in by_id["2026-04"].lower()

    def test_recent_most_recent_first(self):
        assert [r.cycle_id for r in _portfolio().recent_reviews] == \
            ["2026-07", "2026-06", "2026-05", "2026-04"]

    def test_empty_portfolio(self):
        s = PortfolioQueryService(FakeReviews([]), FakeFindings({})).summary()
        assert s.total_reviews == 0
        assert s.attention_items == ()
        assert s.recent_reviews == ()

    def test_deterministic(self):
        assert _portfolio() == _portfolio()


# ===================== dashboard view (fake controller) =====================
class FakeController:
    def __init__(self, summary):
        self._summary = summary
    def portfolio(self):
        return self._summary


def _dash(qtbot, summary=None):
    v = DashboardView(FakeController(summary if summary is not None else _portfolio()))
    qtbot.addWidget(v)
    return v


def test_dashboard_kpis(qtbot):
    k = _dash(qtbot).dashboard_kpis()
    assert k["total_reviews"] == 4
    assert k["needs_attention"] == 3
    assert k["critical"] == 1 and k["high"] == 1
    assert k["completed"] == 2
    assert k["most_recent_period"] == "July 2026"

def test_dashboard_attention_and_recent_ids(qtbot):
    v = _dash(qtbot)
    assert v.attention_review_ids() == ["2026-07", "2026-05", "2026-04"]
    assert v.recent_review_ids() == ["2026-07", "2026-06", "2026-05", "2026-04"]
    assert v.dashboard_empty_state() == ""

def test_dashboard_first_run_when_empty(qtbot):
    v = _dash(qtbot, PortfolioSummary())
    assert v.dashboard_empty_state() == "first_run"
    assert v.dashboard_primary_action_text() == "Create first review"

def test_dashboard_open_review_emits(qtbot):
    v = _dash(qtbot)
    captured = []
    v.openReviewRequested.connect(captured.append)
    v.open_review_from_dashboard("2026-05")
    assert captured == ["2026-05"]

def test_dashboard_populated_primary_is_new_review(qtbot):
    assert _dash(qtbot).dashboard_primary_action_text() == "New review"


# ===================== navigation (real window) =====================
def test_dashboard_is_launch_home(window_factory, populated_db):
    w = window_factory(populated_db)
    assert w.current_view_key() == "dashboard"
    assert w.view("dashboard").dashboard_kpis()["total_reviews"] == 1

def test_empty_db_dashboard_shows_first_run(window_factory, empty_db):
    w = window_factory(empty_db)
    assert w.current_view_key() == "dashboard"
    assert w.view("dashboard").dashboard_empty_state() == "first_run"

def test_open_review_from_dashboard_sets_active_and_navigates(window_factory, populated_db):
    w = window_factory(populated_db)
    w.view("dashboard").open_review_from_dashboard("2026-07")
    assert w._c.active_review_id == "2026-07"
    assert w.current_view_key() == "overview"

def test_dashboard_refreshes_after_create(window_factory, empty_db):
    w = window_factory(empty_db)
    assert w.view("dashboard").dashboard_kpis().get("total_reviews", 0) == 0
    w._c.create_review("2026-07", "July", "2026")
    w.navigate("dashboard")                                 # refresh() on navigate — no stale cache
    assert w.view("dashboard").dashboard_kpis()["total_reviews"] == 1


# ===================== architecture =====================
def test_dashboard_and_portfolio_have_no_ai_or_infra_imports():
    files = [
        os.path.join("src", "finsight", "delivery", "desktop", "views", "dashboard_view.py"),
        os.path.join("src", "finsight", "application", "read_models", "portfolio.py"),
    ]
    forbidden = ("finsight.infrastructure", "sqlite3", "urllib", "ask_fin", "citations",
                 "provider", "OllamaProvider")
    offenders = []
    for path in files:
        for line in open(path, encoding="utf-8"):
            s = line.strip()
            if s.startswith("import ") or s.startswith("from "):
                for tok in forbidden:
                    if tok in s:
                        offenders.append((os.path.basename(path), tok))
    assert offenders == []
