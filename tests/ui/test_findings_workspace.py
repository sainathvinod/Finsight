# Verifies: Phase 5.2 Findings workspace — deterministic search/filter/sort, counts, empty states,
# selection, and CSV export. Pure filter/CSV logic tested directly; the view tested with a fake
# controller (crafted multi-finding data). No network, no repository, no AI.
import os

import pytest
from PySide6.QtWidgets import QFileDialog

from finsight.application.read_models.views import FindingView
from finsight.delivery.desktop import findings_filter as ff
from finsight.delivery.desktop.findings_export import findings_to_csv
from finsight.delivery.desktop.views.findings_view import FindingsView

pytestmark = pytest.mark.ui


def _f(fid, account, rule, sev, ftype, state, refs=()):
    return FindingView(id=fid, account=account, rule_id=rule, severity=sev, period="2026-07",
                       finding_type=ftype, evidence={"note": "x"}, source_refs=list(refs), state=state)


def _findings():
    return [
        _f("F1", "6100", "R-BUD-02", "Critical", "variance", "New", refs=["GED:6100"]),
        _f("F2", "6100", "R-BUD-02", "High", "variance", "Acknowledged"),
        _f("F3", "6200", "R-GED-02", "Medium", "duplicate", "New"),
        _f("F4", "7100", "R-BUD-02", "Low", "anomaly", "Dismissed"),
        _f("F5", "6300", "R-GED-04", "High", "delayed", "New"),
    ]


class FakeController:
    def __init__(self, findings=None, cid="2026-07", state="Analyzed", account_labels=None):
        self.active_review_id = cid
        self._findings = findings if findings is not None else _findings()
        self._state = state
        self._labels = account_labels or {}
    def findings(self, cid):
        return list(self._findings) if cid else []
    def workflow_state(self, cid):
        return self._state
    def account_labels(self, cid):
        return dict(self._labels) if cid else {}


# ===================== pure filter/sort =====================
class TestFindingsFilterPure:
    def test_default_sort_uses_severity_rank_not_lexicographic(self):
        out = ff.FindingsQuery().apply(_findings())
        assert [f.id for f in out] == ["F1", "F2", "F5", "F3", "F4"]   # Crit,High,High,Med,Low
        assert out[-1].severity == "Low"                                # not "Medium" (lexicographic bug)

    def test_search_case_insensitive_and_trimmed(self):
        out = ff.FindingsQuery(search="  BUD  ").apply(_findings())
        assert {f.id for f in out} == {"F1", "F2", "F4"}                # rule_id R-BUD-02

    def test_search_matches_type_and_account(self):
        assert [f.id for f in ff.FindingsQuery(search="duplicate").apply(_findings())] == ["F3"]
        assert [f.id for f in ff.FindingsQuery(search="6300").apply(_findings())] == ["F5"]

    def test_search_no_match(self):
        assert ff.FindingsQuery(search="zzz").apply(_findings()) == []

    def test_severity_filter(self):
        out = ff.FindingsQuery(severities=frozenset({"High"})).apply(_findings())
        assert [f.id for f in out] == ["F2", "F5"]

    def test_account_and_state_filters(self):
        assert [f.id for f in ff.FindingsQuery(account="6100").apply(_findings())] == ["F1", "F2"]
        assert {f.id for f in ff.FindingsQuery(state="New").apply(_findings())} == {"F1", "F3", "F5"}

    def test_combined_filters(self):
        out = ff.FindingsQuery(severities=frozenset({"High"}), state="New").apply(_findings())
        assert [f.id for f in out] == ["F5"]

    def test_sort_account_ascending(self):
        out = ff.FindingsQuery(sort_key="account", descending=False).apply(_findings())
        assert [f.id for f in out] == ["F1", "F2", "F3", "F5", "F4"]

    def test_sort_stable_and_deterministic(self):
        q = ff.FindingsQuery(sort_key="account", descending=False)
        assert [f.id for f in q.apply(_findings())] == [f.id for f in q.apply(_findings())]

    def test_distinct_options(self):
        assert ff.distinct_accounts(_findings()) == ["6100", "6200", "6300", "7100"]
        assert ff.distinct_states(_findings()) == ["Acknowledged", "Dismissed", "New"]


# ===================== pure CSV export =====================
class TestFindingsCsv:
    def test_headers_and_rows(self):
        csv_text = findings_to_csv(_findings())
        lines = csv_text.strip().splitlines()
        assert lines[0] == "Finding ID,Period,Account,Rule,Severity,Type,State,Source references"
        assert len(lines) == 6                                           # header + 5 findings
        assert "F1,2026-07,6100,R-BUD-02,Critical,variance,New,GED:6100" in csv_text

    def test_no_ai_or_evidence_blob(self):
        csv_text = findings_to_csv(_findings())
        for forbidden in ("evidence", "prompt", "answer", "note"):
            assert forbidden not in csv_text.lower()

    def test_deterministic(self):
        assert findings_to_csv(_findings()) == findings_to_csv(_findings())


# ===================== view: filters / counts =====================
def _view(qtbot, controller=None):
    v = FindingsView(controller or FakeController())
    qtbot.addWidget(v)
    return v

def test_view_initial_shows_all(qtbot):
    v = _view(qtbot)
    assert v.total_count() == 5
    assert v.filtered_count() == 5
    assert v.displayed_finding_ids() == ["F1", "F2", "F5", "F3", "F4"]

def test_view_search_filters(qtbot):
    v = _view(qtbot)
    v.set_search_text("duplicate")
    assert v.displayed_finding_ids() == ["F3"]
    v.set_search_text("")
    assert v.filtered_count() == 5

def test_view_severity_filter_and_count(qtbot):
    v = _view(qtbot)
    v.set_severity_filter(["High"])
    assert v.displayed_finding_ids() == ["F2", "F5"]
    assert v.filtered_count() == 2 and v.total_count() == 5

def test_view_account_and_state_filters(qtbot):
    v = _view(qtbot)
    v.set_account_filter("6100")
    assert v.displayed_finding_ids() == ["F1", "F2"]
    v.set_account_filter(None)
    v.set_state_filter("New")
    assert set(v.displayed_finding_ids()) == {"F1", "F3", "F5"}

def test_view_clear_filters(qtbot):
    v = _view(qtbot)
    v.set_search_text("bud")
    v.set_severity_filter(["Critical"])
    v.clear_filters()
    assert v.filtered_count() == 5
    assert v.active_sort() == ("severity", "desc")

def test_view_header_sort_toggles(qtbot):
    v = _view(qtbot)
    v._on_sort_column(1)                       # account column
    assert v.active_sort() == ("account", "asc")
    assert v.displayed_finding_ids() == ["F1", "F2", "F3", "F5", "F4"]
    v._on_sort_column(1)                       # toggle
    assert v.active_sort() == ("account", "desc")


# ===================== view: empty states =====================
def test_empty_no_review(qtbot):
    v = _view(qtbot, FakeController(cid=None))
    assert v.displayed_empty_state() == "no_review"

def test_empty_no_findings(qtbot):
    v = _view(qtbot, FakeController(findings=[], state="Analyzed"))
    assert v.displayed_empty_state() == "no_findings"

def test_empty_not_ready(qtbot):
    v = _view(qtbot, FakeController(findings=[], state="Intake"))
    assert v.displayed_empty_state() == "not_ready"

def test_empty_no_matches(qtbot):
    v = _view(qtbot)
    v.set_search_text("zzz")
    assert v.displayed_empty_state() == "no_matches"
    assert not v.export_action_enabled()


# ===================== view: selection =====================
def test_selection_retained_when_still_visible(qtbot):
    v = _view(qtbot)
    v._table.selectRow(1)                       # F2 (High, 6100)
    assert v.selected_finding_id() == "F2"
    v.set_severity_filter(["High"])             # F2 still visible
    assert v.selected_finding_id() == "F2"

def test_selection_moves_when_filtered_out(qtbot):
    v = _view(qtbot)
    for i, fid in enumerate(v.displayed_finding_ids()):
        if fid == "F5":
            v._table.selectRow(i)
    assert v.selected_finding_id() == "F5"
    v.set_account_filter("6100")                # F5 not in 6100
    assert v.selected_finding_id() in ("F1", "F2")   # moved deterministically to a visible finding
    assert "F5" not in v.displayed_finding_ids()


# ===================== view: export =====================
def test_export_all_vs_filtered(qtbot, tmp_path, monkeypatch):
    v = _view(qtbot)
    dest = os.path.join(str(tmp_path), "all.csv")
    monkeypatch.setattr(QFileDialog, "getSaveFileName",
                        staticmethod(lambda *a, **k: (dest, "CSV (*.csv)")))
    v._on_export()
    assert len(open(dest).read().strip().splitlines()) == 6            # header + 5

    v.set_severity_filter(["High"])
    dest2 = os.path.join(str(tmp_path), "filtered.csv")
    monkeypatch.setattr(QFileDialog, "getSaveFileName",
                        staticmethod(lambda *a, **k: (dest2, "CSV (*.csv)")))
    v._on_export()
    body = open(dest2).read()
    assert len(body.strip().splitlines()) == 3                          # header + 2 High findings
    assert "current filter" in v._count.text().lower()                  # honestly labelled

def test_export_cancel_writes_nothing(qtbot, tmp_path, monkeypatch):
    v = _view(qtbot)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: ("", "")))
    v._on_export()                                                       # must not raise / write
    assert not list(tmp_path.iterdir())

def test_export_disabled_when_no_matches(qtbot):
    v = _view(qtbot)
    v.set_search_text("zzz")
    assert not v.export_action_enabled()


# ===================== architecture =====================
def test_findings_delivery_has_no_repo_ai_or_transport_imports():
    base = os.path.join("src", "finsight", "delivery", "desktop")
    files = [os.path.join(base, "views", "findings_view.py"),
             os.path.join(base, "findings_filter.py"),
             os.path.join(base, "findings_export.py")]
    forbidden = ("finsight.infrastructure", "sqlite3", "urllib", "ask_fin", "citations",
                 "validation", "provider", "OllamaProvider")
    offenders = []
    for path in files:
        for line in open(path, encoding="utf-8"):
            s = line.strip()
            if s.startswith("import ") or s.startswith("from "):
                for tok in forbidden:
                    if tok in s:
                        offenders.append((os.path.basename(path), tok))
    assert offenders == []
