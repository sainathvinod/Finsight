# Verifies: Phase 4C.7 desktop Ask Fin view (FR-099). Deterministic fakes only — no live network, no
# real sleep. The whole AskFinService pipeline runs off the UI thread via the controller's run_async.
import os
import re
import threading

import pytest

from finsight.application.ai.ask_fin_contracts import (
    AskFinResult, AskFinStage, AskFinStatus, AiExecutionMetadata,
)
from finsight.application.ai.contracts import (
    AiAnswer, CitationNamespace, CitationReference, GroundingConfidence, ProviderStatus,
)

pytestmark = pytest.mark.ui


# --- fakes ---
def _answer(text="grounded explanation", citations=(), gc=GroundingConfidence.HIGH, unable=False):
    return AiAnswer(text, unable, tuple(citations), gc, "ollama", "llama3.2:3b", "v1", "v1", "v1", "v1")


def _cite(ns, ident, key):
    return CitationReference(ns, ident, key)


def _result(status, answer=None, error_code=None, last_stage=AskFinStage.COMPLETE):
    return AskFinResult(status, answer, error_code, last_stage, AiExecutionMetadata())


_OK = _result(AskFinStatus.OK, _answer(citations=[
    _cite(CitationNamespace.FINDING, "F1", "finding:F1"),
    _cite(CitationNamespace.RUN, "run123", "run:run123"),
]))
_DEGRADED = _result(AskFinStatus.DEGRADED, _answer("AI explanations are currently unavailable.",
                                                   gc=GroundingConfidence.UNAVAILABLE, unable=True))
_UNANSWERABLE = _result(AskFinStatus.UNANSWERABLE, _answer("Not enough context.",
                                                          gc=GroundingConfidence.UNAVAILABLE, unable=True))
_FAILED = _result(AskFinStatus.FAILED, None, error_code="provider_timeout", last_stage=AskFinStage.PROVIDER)
_REFUSED = _result(AskFinStatus.REFUSED, None, error_code="demo_not_authorized",
                   last_stage=AskFinStage.AUTHORIZATION)


class FakeBackend:
    def __init__(self, result=_OK, status=None, gate=None):
        self._result = result
        self._status = status or ProviderStatus(True, True, "ok")
        self._gate = gate                       # optional threading.Event to hold explain() open
        self.explain_calls = 0
        self.explain_thread = None
        self.last_request = None
    def provider_status(self):
        return self._status
    def explain(self, request):
        self.explain_calls += 1
        self.explain_thread = threading.current_thread()
        self.last_request = request
        if self._gate is not None:
            self._gate.wait(2.0)
        return self._result


def _askfin(window_factory, populated_db, backend):
    w = window_factory(populated_db, ask_fin_backend=backend)
    w._c.select_review("2026-07")
    w.navigate("askfin")
    return w, w.view("askfin")


def _wait_done(qtbot, view):
    qtbot.waitUntil(lambda: not view.is_request_running(), timeout=3000)


# --- construction / initial state ---
def test_view_loads_without_network(window_factory, populated_db):
    _w, view = _askfin(window_factory, populated_db, FakeBackend())
    assert view is not None

def test_no_selected_review_disables_submission(window_factory, empty_db):
    w = window_factory(empty_db, ask_fin_backend=FakeBackend())
    w.navigate("askfin")
    view = w.view("askfin")
    assert not w._c.active_review_id
    assert not view.ask_button_enabled()

def test_provider_status_rendered_safely(window_factory, populated_db, qtbot):
    _w, view = _askfin(window_factory, populated_db, FakeBackend(status=ProviderStatus(True, True, "ok")))
    qtbot.waitUntil(lambda: view.provider_status_text() == "Local AI ready", timeout=3000)
    # never leak transport internals
    assert "http" not in view.provider_status_text().lower()

def test_provider_status_disabled_wording(window_factory, populated_db, qtbot):
    _w, view = _askfin(window_factory, populated_db,
                       FakeBackend(status=ProviderStatus(True, False, "provider_disabled")))
    qtbot.waitUntil(lambda: view.provider_status_text() == "Local AI is disabled", timeout=3000)


# --- submission ---
def test_empty_question_not_submitted(window_factory, populated_db):
    backend = FakeBackend()
    _w, view = _askfin(window_factory, populated_db, backend)
    view.set_question("   ")
    view.submit_question()
    assert backend.explain_calls == 0

def test_request_carries_current_review(window_factory, populated_db, qtbot):
    backend = FakeBackend()
    _w, view = _askfin(window_factory, populated_db, backend)
    view.set_question("why is 6100 high?")
    view.submit_question()
    _wait_done(qtbot, view)
    assert backend.last_request.cycle_id == "2026-07"
    assert backend.last_request.question == "why is 6100 high?"
    assert backend.last_request.conversation_id is None       # one-shot (§11 minimal option)

def test_internal_whitespace_preserved_edges_trimmed(window_factory, populated_db, qtbot):
    backend = FakeBackend()
    _w, view = _askfin(window_factory, populated_db, backend)
    view.set_question("   why is   6100   high?  ")
    view.submit_question()
    _wait_done(qtbot, view)
    assert backend.last_request.question == "why is   6100   high?"

def test_runs_off_ui_thread(window_factory, populated_db, qtbot):
    backend = FakeBackend()
    _w, view = _askfin(window_factory, populated_db, backend)
    view.submit_question("q")
    _wait_done(qtbot, view)
    assert backend.explain_thread is not None
    assert backend.explain_thread is not threading.main_thread()

def test_duplicate_submission_blocked_while_running(window_factory, populated_db, qtbot):
    gate = threading.Event()
    backend = FakeBackend(gate=gate)
    _w, view = _askfin(window_factory, populated_db, backend)
    view.submit_question("q1")
    qtbot.waitUntil(lambda: view.is_request_running(), timeout=3000)
    assert not view.ask_button_enabled()                      # controls disabled during execution
    assert not view.question_input_enabled()
    view.submit_question("q2")                                # ignored while running
    gate.set()
    _wait_done(qtbot, view)
    assert backend.explain_calls == 1
    assert view.question_input_enabled()                      # controls restored afterward


# --- status rendering ---
@pytest.mark.parametrize("result,expect_answer,expect_state", [
    (_OK, "grounded explanation", "showing_result"),
    (_DEGRADED, "AI explanations are currently unavailable.", "showing_result"),
    (_UNANSWERABLE, "Not enough context.", "showing_result"),
])
def test_answer_bearing_statuses(window_factory, populated_db, qtbot, result, expect_answer, expect_state):
    _w, view = _askfin(window_factory, populated_db, FakeBackend(result=result))
    view.submit_question("q")
    _wait_done(qtbot, view)
    assert view.current_status() == expect_state
    assert view.displayed_answer() == expect_answer

def test_failed_shows_no_answer_and_safe_message(window_factory, populated_db, qtbot):
    _w, view = _askfin(window_factory, populated_db, FakeBackend(result=_FAILED))
    view.submit_question("q")
    _wait_done(qtbot, view)
    assert view.displayed_answer() == ""                      # no AiAnswer for FAILED
    assert view.current_status() == "error"
    assert "did not respond" in view.displayed_message()      # from error_code, not exception text

def test_refused_shows_no_answer_and_auth_message(window_factory, populated_db, qtbot):
    _w, view = _askfin(window_factory, populated_db, FakeBackend(result=_REFUSED))
    view.submit_question("q")
    _wait_done(qtbot, view)
    assert view.displayed_answer() == ""
    assert "not authorized" in view.displayed_message().lower()
    assert "not an AI provider failure" in view.displayed_message()   # distinct from provider failure


# --- answer / citation / grounding rendering ---
def test_citations_in_canonical_order(window_factory, populated_db, qtbot):
    _w, view = _askfin(window_factory, populated_db, FakeBackend(result=_OK))
    view.submit_question("q")
    _wait_done(qtbot, view)
    assert view.displayed_citations() == ["finding:F1", "run:run123"]

@pytest.mark.parametrize("gc,text", [
    (GroundingConfidence.HIGH, "High grounding"),
    (GroundingConfidence.MEDIUM, "Partial grounding"),
    (GroundingConfidence.UNAVAILABLE, "Grounding unavailable"),
])
def test_grounding_confidence_wording(window_factory, populated_db, qtbot, gc, text):
    result = _result(AskFinStatus.OK, _answer(citations=[_cite(CitationNamespace.FINDING, "F1", "finding:F1")],
                                              gc=gc))
    _w, view = _askfin(window_factory, populated_db, FakeBackend(result=result))
    view.submit_question("q")
    _wait_done(qtbot, view)
    assert view.grounding_text() == text


# --- privacy ---
def test_no_raw_or_exception_content_displayed(window_factory, populated_db, qtbot):
    # A worker exception path must show a safe generic message, never internals.
    class Boom:
        def provider_status(self):
            return ProviderStatus(True, True, "ok")
        def explain(self, request):
            raise RuntimeError("SECRET-STACK-INTERNAL at 0xdeadbeef")
    _w, view = _askfin(window_factory, populated_db, Boom())
    view.submit_question("q")
    _wait_done(qtbot, view)
    assert view.displayed_answer() == ""
    assert "SECRET-STACK-INTERNAL" not in view.displayed_message()
    assert view.displayed_message() == "Ask Fin could not complete this request."

def test_unknown_error_code_maps_safely(window_factory, populated_db, qtbot):
    _w, view = _askfin(window_factory, populated_db,
                       FakeBackend(result=_result(AskFinStatus.FAILED, None, error_code="weird_new_code")))
    view.submit_question("q")
    _wait_done(qtbot, view)
    assert view.displayed_message() == "Ask Fin could not complete this request."


# --- threading: repeated sequential questions ---
def test_repeated_sequential_questions(window_factory, populated_db, qtbot):
    backend = FakeBackend(result=_OK)
    _w, view = _askfin(window_factory, populated_db, backend)
    for _ in range(3):
        view.submit_question("q")
        _wait_done(qtbot, view)
    assert backend.explain_calls == 3
    assert view.displayed_answer() == "grounded explanation"

def test_closing_view_during_request_is_safe(window_factory, populated_db, qtbot):
    gate = threading.Event()
    backend = FakeBackend(gate=gate)
    w, view = _askfin(window_factory, populated_db, backend)
    view.submit_question("q")
    qtbot.waitUntil(lambda: view.is_request_running(), timeout=3000)
    w.close()                                                 # replace/close during an in-flight request
    gate.set()
    qtbot.wait(50)                                            # let the queued signal drain; must not crash


# --- architecture ---
def test_ask_fin_delivery_has_no_provider_or_pipeline_imports():
    files = [
        os.path.join("src", "finsight", "delivery", "desktop", "views", "ask_fin_view.py"),
        os.path.join("src", "finsight", "delivery", "desktop", "controllers", "app_controller.py"),
    ]
    forbidden = ("urllib", "OllamaProvider", "providers.ollama", "ResponseValidator", "CitationVerifier",
                 "MaskingService", "PromptBuilder", "finsight.infrastructure", "sqlite3")
    offenders = []
    for path in files:
        for line in open(path, encoding="utf-8"):
            s = line.strip()
            if s.startswith("import ") or s.startswith("from "):
                for tok in forbidden:
                    if tok in s:
                        offenders.append((os.path.basename(path), tok))
    assert offenders == []


def test_no_urllib_anywhere_in_desktop():
    base = os.path.join("src", "finsight", "delivery", "desktop")
    offenders = []
    for dp, _dirs, files in os.walk(base):
        for fn in files:
            if fn.endswith(".py"):
                txt = open(os.path.join(dp, fn), encoding="utf-8").read()
                if re.search(r"^\s*(import|from)\s+urllib", txt, re.M):
                    offenders.append(os.path.join(dp, fn))
    assert offenders == []
