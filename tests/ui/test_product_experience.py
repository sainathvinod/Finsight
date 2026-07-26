# Verifies: Phase 5.1 product-experience hardening — first run, review creation, IA, overview
# dashboard, verification transparency, humanized identifiers/audit, Ask Fin guidance, primary button.
# Deterministic; no live network; no real sleep.
import os

import pytest

from finsight.application.ai.ask_fin_contracts import (
    AskFinResult, AskFinStage, AskFinStatus, AiExecutionMetadata,
)
from finsight.application.ai.contracts import (
    AiAnswer, CitationNamespace, CitationReference, GroundingConfidence, ProviderStatus,
)
from finsight.delivery.desktop import presentation as pres
from finsight.delivery.desktop.theme import build_qss
from tests.support import build_synthetic_ged, build_synthetic_budget

pytestmark = pytest.mark.ui


def _files(tmp_path):
    ged = os.path.join(str(tmp_path), "ged.xlsx")
    bud = os.path.join(str(tmp_path), "budget.xlsx")
    build_synthetic_ged(ged)
    build_synthetic_budget(bud)
    return ged, bud


# --- Ask Fin fake backend ---
class FakeBackend:
    def __init__(self, result=None, status=None):
        self._result = result
        self._status = status or ProviderStatus(True, True, "ok")
    def provider_status(self):
        return self._status
    def explain(self, request):
        return self._result


def _answer(text="grounded", citations=(), gc=GroundingConfidence.HIGH, unable=False):
    return AiAnswer(text, unable, tuple(citations), gc, "ollama", "llama3.2:3b", "v1", "v1", "v1", "v1")


def _result(status, answer=None, error_code=None):
    return AskFinResult(status, answer, error_code, AskFinStage.COMPLETE, AiExecutionMetadata())


# ===================== presentation helpers (pure) =====================
class TestPresentation:
    def test_period_text(self):
        assert pres.period_text("July", "2026") == "July 2026"
        assert pres.period_text("", "") == "—"

    def test_state_label(self):
        assert pres.state_label("Exported") == "Exported"
        assert pres.state_label("Intake") == "Files uploaded"
        assert pres.state_label(None) == "Not started"

    def test_citation_label(self):
        assert pres.citation_label("finding:F1") == "Finding F1"
        assert pres.citation_label("run:run123") == "Rule run run123"
        assert pres.citation_label("weird") == "weird"

    def test_action_label(self):
        assert pres.action_label("run_analysis") == "Run Analysis"
        assert pres.action_label("setup") == "Setup"


# ===================== first run =====================
def test_first_run_guidance_on_empty_db(window_factory, empty_db):
    w = window_factory(empty_db)
    w.navigate("reviews")
    rv = w.view("reviews")
    assert rv.first_run_message()                       # non-empty welcome guidance
    assert rv.primary_action_text() == "Create first review"

def test_no_first_run_when_reviews_exist(window_factory, populated_db):
    w = window_factory(populated_db)
    w.navigate("reviews")
    assert w.view("reviews").first_run_message() == ""

def test_first_run_does_not_claim_ai_without_review(window_factory, empty_db):
    w = window_factory(empty_db)
    w.navigate("askfin")
    view = w.view("askfin")
    assert view.displayed_answer() == ""                # AI cannot answer with no review
    assert not view.ask_button_enabled()


# ===================== review creation =====================
def test_setup_period_and_primary(window_factory, empty_db):
    w = window_factory(empty_db)
    w.navigate("workspace")
    setup = w._workspace.panel(0)
    setup._month.setCurrentIndex(0)                     # January
    setup._year.setValue(2027)
    assert setup.displayed_review_period() == "January 2027"
    assert setup._create.property("role") == "primary"   # one clear primary Create action
    assert setup._year.minimum() >= 2000 and setup._year.maximum() <= 2100   # constrained

def test_create_generates_correct_request(window_factory, empty_db):
    w = window_factory(empty_db)
    w.navigate("workspace")
    setup = w._workspace.panel(0)
    setup._month.setCurrentIndex(6)
    setup._year.setValue(2026)
    setup._on_create()
    assert w._c.active_review_id == "2026-07"

def test_upload_shows_three_source_cards_with_honest_invoice(window_factory, empty_db):
    w = window_factory(empty_db)
    w._c.create_review("2026-07", "July", "2026")
    w.navigate("workspace")
    upload = w._workspace.panel(1)
    upload.refresh()
    # Exactly three source cards: GED + Budget required, Invoice optional (captured, not analyzed).
    assert upload._ged_card.path() is None and upload._bud_card.path() is None
    upload.set_invoice("/tmp/inv.pdf")
    assert "not available" in upload._inv_card.status_text().lower()   # honest: invoice not analyzed
    # Required-only upload stays enabled without the invoice; invoice is optional.
    upload.set_ged("/tmp/g.xlsx"); upload.set_budget("/tmp/b.xlsx")
    assert upload._upload.isEnabled()


# ===================== navigation / IA =====================
def test_overview_is_review_home_on_open(window_factory, populated_db):
    w = window_factory(populated_db)
    rv = w.view("reviews")
    rv._on_open("2026-07")                              # open the review by cycle_id
    assert w.current_view_key() == "overview"           # lands on the dashboard, not a step panel

def test_overview_destination_exists_and_is_wired(window_factory, populated_db):
    w = window_factory(populated_db)
    assert w.view("overview") is w._overview            # single, wired Overview (no dead screen)
    w.navigate("overview")
    assert w.current_view_key() == "overview"

def test_findings_single_canonical_view(window_factory, populated_db):
    w = window_factory(populated_db)
    from finsight.delivery.desktop.views.findings_view import FindingsView
    assert isinstance(w.view("findings"), FindingsView)
    assert isinstance(w._workspace.panel(6)._inner, FindingsView)   # same canonical view reused


# ===================== overview dashboard =====================
def test_overview_summary_from_deterministic_data(window_factory, populated_db):
    w = window_factory(populated_db)
    w._c.select_review("2026-07")
    ov = w.view("overview")
    ov.refresh()
    s = ov.review_overview_summary()
    assert s["period"] == "July 2026"
    assert s["steps_total"] == 9
    assert s["finding_count"] >= 1
    assert set(s["severity"].keys()) == {"Critical", "High", "Medium", "Low"}
    assert s["next_action"]                             # a recommended next step is present

def test_overview_empty_without_review(window_factory, empty_db):
    w = window_factory(empty_db)
    ov = w.view("overview")
    ov.refresh()
    assert ov.review_overview_summary() == {}           # nothing invented when no review


# ===================== verification transparency =====================
def test_verification_preview_shows_what_is_approved(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    ged, bud = _files(tmp_path)
    w._c.create_review("2026-07", "July", "2026")
    w._c.upload("2026-07", ged, bud)
    w._c._s.workflow.process(w._c._session_for("2026-07"))   # process in-session → snapshot available
    verify = w._workspace.panel(4)
    verify.refresh()
    rows = verify.verification_preview_rows()
    labels = [lbl for lbl, _ in rows]
    assert any("GED" in lbl for lbl in labels)          # reviewer sees accepted counts
    assert any("Source" == lbl for lbl in labels)       # and the source documents
    assert verify._approve.isEnabled()                  # approvable once data is visible

def test_verification_blocked_without_data(window_factory, empty_db):
    w = window_factory(empty_db)
    w._c.create_review("2026-07", "July", "2026")
    verify = w._workspace.panel(4)
    verify.refresh()
    assert verify.verification_preview_rows() == []
    assert not verify._approve.isEnabled()              # cannot approve unavailable data


# ===================== humanized presentation =====================
def test_reviews_period_is_human(window_factory, populated_db):
    w = window_factory(populated_db)
    assert "July 2026" in w.view("reviews").review_periods()   # not "2026-07"

def test_audit_detail_not_raw_json(window_factory, populated_db):
    from PySide6.QtWidgets import QLabel
    w = window_factory(populated_db)
    w._c.select_review("2026-07")
    w.navigate("audit")
    av = w.view("audit")
    text = " ".join(lbl.text() for lbl in av._inspector.findChildren(QLabel))
    assert "{" not in text and "}" not in text          # no raw JSON braces on the primary surface


# ===================== Ask Fin guidance (six cases) =====================
def _askfin(window_factory, populated_db, backend, qtbot):
    w = window_factory(populated_db, ask_fin_backend=backend)
    w._c.select_review("2026-07")
    w.navigate("askfin")
    return w.view("askfin")

def test_guidance_provider_disabled(window_factory, populated_db, qtbot):
    v = _askfin(window_factory, populated_db,
                FakeBackend(status=ProviderStatus(True, False, "provider_disabled")), qtbot)
    qtbot.waitUntil(lambda: "Install Ollama" in v.ask_fin_guidance_text(), timeout=3000)

def test_guidance_unreachable(window_factory, populated_db, qtbot):
    v = _askfin(window_factory, populated_db,
                FakeBackend(status=ProviderStatus(True, False, "unreachable")), qtbot)
    qtbot.waitUntil(lambda: "could not be reached" in v.ask_fin_guidance_text(), timeout=3000)

def test_guidance_model_missing(window_factory, populated_db, qtbot):
    v = _askfin(window_factory, populated_db,
                FakeBackend(status=ProviderStatus(True, False, "model_missing")), qtbot)
    qtbot.waitUntil(lambda: "not installed" in v.ask_fin_guidance_text(), timeout=3000)

def test_guidance_no_review(window_factory, empty_db):
    w = window_factory(empty_db, ask_fin_backend=FakeBackend())
    w.navigate("askfin")
    view = w.view("askfin")
    assert not view.ask_button_enabled()                # no review → cannot ask

def test_guidance_demo_auth_refused(window_factory, populated_db, qtbot):
    backend = FakeBackend(result=_result(AskFinStatus.REFUSED, None, "demo_not_authorized"))
    v = _askfin(window_factory, populated_db, backend, qtbot)
    v.submit_question("why?")
    qtbot.waitUntil(lambda: not v.is_request_running(), timeout=3000)
    assert "not authorized" in v.displayed_message().lower()
    assert v.displayed_answer() == ""

def test_guidance_grounding_unavailable(window_factory, populated_db, qtbot):
    backend = FakeBackend(result=_result(AskFinStatus.FAILED, None, "grounding_unavailable"))
    v = _askfin(window_factory, populated_db, backend, qtbot)
    v.submit_question("why?")
    qtbot.waitUntil(lambda: not v.is_request_running(), timeout=3000)
    assert "no deterministic grounding" in v.displayed_message().lower()

def test_ask_fin_citation_labels_human(window_factory, populated_db, qtbot):
    ok = _result(AskFinStatus.OK, _answer(citations=[
        CitationReference(CitationNamespace.FINDING, "F1", "finding:F1")]))
    v = _askfin(window_factory, populated_db, FakeBackend(result=ok), qtbot)
    v.submit_question("why?")
    qtbot.waitUntil(lambda: not v.is_request_running(), timeout=3000)
    assert v.displayed_citations() == ["finding:F1"]    # canonical key preserved on the seam
    assert "Finding F1" in v._citations.text()          # human label on the surface


# ===================== primary button styling =====================
def test_primary_button_role_is_styled():
    qss = build_qss()
    assert 'QPushButton[role="primary"]' in qss         # the role now has explicit styling

def test_first_run_and_create_buttons_are_primary(window_factory, empty_db):
    w = window_factory(empty_db)
    rv = w.view("reviews")
    assert rv._first_run_btn.property("role") == "primary"
    w.navigate("workspace")
    assert w._workspace.panel(0)._create.property("role") == "primary"


# ===================== architecture guard =====================
def test_presentation_helpers_have_no_qt_or_infra():
    import finsight.delivery.desktop.presentation as p
    src = open(p.__file__, encoding="utf-8").read()
    for tok in ("PySide6", "finsight.infrastructure", "sqlite3", "urllib"):
        assert tok not in src
