# Verifies: the visual leadership report (Product Owner workflow §14).
#   A) executive summary (RAG status shown as text); C) account-level detail; D) user-correction
#   disclosure (DEC-036); E) scope & limitations. B) the Financial Map is a view over EXISTING outputs
#   (DEC-037) — it connects accounts to their findings and computes nothing.
import os

from tests.support import build_synthetic_ged, build_synthetic_budget


def _to_analyzed(w, tmp_path, correct=False):
    ged = os.path.join(str(tmp_path), "g.xlsx"); bud = os.path.join(str(tmp_path), "b.xlsx")
    build_synthetic_ged(ged); build_synthetic_budget(bud)
    w._c.create_review("2026-07", "July", "2026")
    w._c.upload("2026-07", ged, bud)
    w._c._s.workflow.process(w._c._session_for("2026-07"))
    w._c.select_review("2026-07")
    if correct:
        verify = w._workspace.panel(4); verify.refresh()
        tab = verify._review.tab("GED")
        col = list(tab._records.columns).index("amount")
        tab.edit_cell(0, col, "12345")
    w._c.verify("2026-07")
    w._c.analyze("2026-07")


def test_report_shows_all_deterministic_sections(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _to_analyzed(w, tmp_path)
    report = w._workspace.panel(7)
    report.refresh()
    text = report.report_text()
    assert "status" in text.lower()                 # A) executive summary status
    assert "Account" in text                         # C) account-level detail
    assert "corrections" in text.lower()             # D) correction disclosure section
    assert "Scope" in text or "not available" in text.lower()   # E) scope & limitations


def test_no_corrections_states_so_honestly(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _to_analyzed(w, tmp_path, correct=False)
    report = w._workspace.panel(7); report.refresh()
    assert "No corrections were made" in report.report_text()


def test_corrections_are_disclosed_original_to_corrected(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _to_analyzed(w, tmp_path, correct=True)
    report = w._workspace.panel(7); report.refresh()
    text = report.report_text()
    assert "12345" in text and "→" in text          # discloses the corrected value original -> corrected


def test_financial_map_is_a_view_over_existing_findings(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _to_analyzed(w, tmp_path)
    graph = w._c.financial_map("2026-07")
    findings = w._c.findings("2026-07")
    # One finding node per finding, one account node per distinct account — nothing invented.
    accounts = {a["account"] for a in graph["accounts"]}
    assert accounts == {f.account for f in findings}
    total_finding_nodes = sum(len(a["findings"]) for a in graph["accounts"])
    assert total_finding_nodes == len(findings)
