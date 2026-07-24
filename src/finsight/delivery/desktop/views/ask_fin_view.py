# Ask Fin desktop view (Phase 4C.7). A focused explanation panel bound to the CURRENT review. It
# runs the whole AskFinService pipeline OFF the UI thread through the controller (worker-local SQLite
# connection) and renders AskFinResult by status. The view holds NO pipeline logic: no masking,
# validation, citation, provider, or repository access. It imports only application contracts.
from __future__ import annotations
from enum import Enum
from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QPushButton, QPlainTextEdit, QTextEdit, QLabel,
)
from finsight.application.ai.ask_fin_contracts import AskFinStatus
from finsight.application.ai.contracts import GroundingConfidence
from finsight.delivery.desktop.components import SectionHeader, EmptyState
from finsight.delivery.desktop.components.message import InlineMessage
from finsight.delivery.desktop import presentation as pres
from finsight.delivery.desktop.theme import tokens as t


class AskFinUiState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    SHOWING_RESULT = "showing_result"
    ERROR = "error"


_GROUNDING_TEXT = {
    GroundingConfidence.HIGH: "High grounding",
    GroundingConfidence.MEDIUM: "Partial grounding",
    GroundingConfidence.UNAVAILABLE: "Grounding unavailable",
}
_GROUNDING_TOOLTIP = ("This reflects the availability and completeness of deterministic grounding, "
                      "not model certainty or guaranteed factual correctness.")

# Provider-status reason → user-friendly, non-sensitive text (no URLs, no transport internals).
_PROVIDER_TEXT = {
    "ok": "AI provider ready",
    "provider_disabled": "AI generation is turned off",
    "model_missing": "Configured AI model is not installed",
    "unreachable": "AI provider is not reachable",
    "status_timeout": "AI provider did not respond in time",
    "malformed_status_response": "AI provider status is unavailable",
}
# Concise availability guidance per provider state (no environment-variable commands for reviewers).
_PROVIDER_GUIDANCE = {
    "ok": "",
    "provider_disabled": "Ask Fin is disabled for this session. Local development access must be "
                         "enabled before launching FinSight.",
    "model_missing": "The configured AI model is not installed for the local AI service.",
    "unreachable": "The AI provider could not be reached. Ensure the local AI service is running.",
    "status_timeout": "The AI provider did not respond in time. It may be starting up.",
    "malformed_status_response": "The AI provider status could not be read.",
}

# Non-sensitive error_code → user-friendly message. Unknown codes fall back to a safe generic message.
_ERROR_TEXT = {
    "demo_not_authorized": "Ask Fin is not authorized in the current mode.",
    "grounding_unavailable": "This review has no deterministic grounding to explain.",
    "conversation_not_found": "The referenced conversation could not be found.",
    "masking_failed": "The request could not be safely prepared for the AI provider.",
    "prompt_build_failed": "The request could not be prepared.",
    "provider_timeout": "The AI provider did not respond in time. Please try again.",
    "provider_unavailable": "The AI provider is currently unavailable.",
    "provider_error": "The AI provider returned an unexpected result.",
    "response_format": "The AI response was malformed and could not be validated.",
    "invalid_json": "The AI response was malformed and could not be validated.",
    "citation_not_in_context": "The AI response cited data that is not in the current review.",
    "malformed_citation": "The AI response cited data in an invalid form and was rejected.",
    "omitted_finding_cited": "The AI response cited a finding that was not included in context.",
}


def _error_text(code: Optional[str]) -> str:
    return _ERROR_TEXT.get(code or "", "Ask Fin could not complete this request.")


class AskFinView(QWidget):
    """Explanation panel for the current review. Renders OK / DEGRADED / UNANSWERABLE / FAILED /
    REFUSED distinctly and never shows a technical failure as though it were an AI answer.

    Presentation state is tracked in explicit fields (not Qt isVisible(), which depends on the
    top-level window being shown) so the public test seams are reliable headless."""

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._c = controller
        self._state = AskFinUiState.IDLE
        self._running = False
        self._status_probed = False
        self._shown_answer = ""
        self._shown_citations: List[str] = []
        self._shown_message = ""
        self._shown_grounding = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        root.setSpacing(t.SP_3)
        self._header = SectionHeader("Ask Fin", "Explanations grounded in this review's verified data.")
        root.addWidget(self._header)

        self._stack = QStackedWidget()
        root.addWidget(self._stack, 1)
        self._stack.addWidget(self._build_content())
        self._empty = EmptyState(
            "Ask Fin unavailable",
            "Select a processed review to ask grounded questions about it.",
            "Ask Fin explains deterministic results only; it never creates findings or decisions.")
        self._stack.addWidget(self._empty)

        self.refresh()

    # --- construction ---
    def _build_content(self) -> QWidget:
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(t.SP_3)

        self._provider_status = QLabel("")
        self._provider_status.setProperty("role", "context")
        lay.addWidget(self._provider_status)
        self._guidance = QLabel("")
        self._guidance.setProperty("role", "context")
        self._guidance.setWordWrap(True)
        self._guidance.setVisible(False)
        lay.addWidget(self._guidance)

        self._question = QPlainTextEdit()
        self._question.setPlaceholderText("Ask a question about this review…")
        self._question.setFixedHeight(72)
        self._question.textChanged.connect(self._sync_ask_enabled)
        lay.addWidget(self._question)

        row = QHBoxLayout()
        row.addStretch(1)
        self._ask = QPushButton("Ask")
        self._ask.setProperty("role", "primary")
        self._ask.clicked.connect(lambda: self.submit_question())
        row.addWidget(self._ask)
        lay.addLayout(row)

        self._message = InlineMessage()
        lay.addWidget(self._message)

        self._grounding = QLabel("")
        self._grounding.setProperty("role", "context")
        self._grounding.setToolTip(_GROUNDING_TOOLTIP)
        self._grounding.setVisible(False)
        lay.addWidget(self._grounding)

        self._answer = QTextEdit()
        self._answer.setReadOnly(True)                 # plain-text answer; no rich-text interpretation
        self._answer.setVisible(False)
        lay.addWidget(self._answer, 1)

        self._citations = QLabel("")
        self._citations.setProperty("role", "context")
        self._citations.setWordWrap(True)
        self._citations.setVisible(False)
        lay.addWidget(self._citations)
        return content

    # --- lifecycle ---
    def refresh(self) -> None:
        available = self._c.ask_fin_available() and bool(self._c.active_review_id)
        self._stack.setCurrentIndex(0 if available else 1)
        if available and not self._status_probed:
            self._status_probed = True
            self._provider_status.setText("Checking AI provider…")
            self._c.ask_fin_provider_status_async(self._on_provider_status, self._on_provider_status_error)
        self._sync_ask_enabled()   # always: keep the Ask button disabled when unavailable/no review

    # --- submission ---
    def submit_question(self, text: Optional[str] = None) -> None:
        if self._running or not self._c.ask_fin_available() or not self._c.active_review_id:
            return
        raw = self._question.toPlainText() if text is None else text
        question = raw.strip()                          # trim only UI whitespace; internal preserved
        if not question:
            return
        self._running = True
        self._state = AskFinUiState.RUNNING
        self._clear_output()
        self._set_message("Asking Fin…", "info")
        self._sync_controls_enabled()
        self._c.ask_fin_explain_async(question, self._on_result, self._on_error)

    def _on_result(self, result) -> None:
        self._running = False
        self._render_result(result)
        self._sync_controls_enabled()

    def _on_error(self, _exc) -> None:
        # AskFinService returns a result rather than raising; reaching here means the worker itself
        # failed (e.g. local DB error). Show a safe generic message — never exception internals.
        self._running = False
        self._state = AskFinUiState.ERROR
        self._clear_output()
        self._set_message("Ask Fin could not complete this request.", "error")
        self._sync_controls_enabled()

    # --- rendering ---
    def _render_result(self, result) -> None:
        self._clear_output()
        status = result.status
        if status == AskFinStatus.OK:
            self._state = AskFinUiState.SHOWING_RESULT
            self._show_answer(result.answer)
            self._set_message("Answer grounded in this review's verified data.", "success")
        elif status == AskFinStatus.DEGRADED:
            self._state = AskFinUiState.SHOWING_RESULT
            self._show_answer(result.answer)
            self._set_message(
                "Live AI generation is unavailable — showing a safe fallback response.", "warning")
        elif status == AskFinStatus.UNANSWERABLE:
            self._state = AskFinUiState.SHOWING_RESULT
            self._show_answer(result.answer)
            self._set_message(
                "The available grounding was insufficient to answer this question.", "warning")
        elif status == AskFinStatus.REFUSED:
            self._state = AskFinUiState.SHOWING_RESULT
            self._set_message(
                "Ask Fin is not authorized in the current mode (not an AI provider failure).", "info")
        else:  # FAILED
            self._state = AskFinUiState.ERROR
            self._set_message(_error_text(result.error_code), "error")

    def _show_answer(self, answer) -> None:
        self._shown_answer = answer.answer_text
        self._answer.setPlainText(answer.answer_text)   # exactly as the validated AiAnswer supplies it
        self._answer.setVisible(True)
        self._shown_grounding = _GROUNDING_TEXT.get(answer.grounding_confidence, "")
        self._grounding.setText(self._shown_grounding)
        self._grounding.setVisible(True)
        if answer.citations:
            self._shown_citations = [c.key for c in answer.citations]     # canonical keys (seam/tooltip)
            labels = [pres.citation_label(c.key) for c in answer.citations]  # human labels (display)
            self._citations.setText("Citations:   " + "    ".join(labels))
            self._citations.setToolTip("Citation keys:  " + ", ".join(self._shown_citations))
            self._citations.setVisible(True)

    def _set_message(self, text: str, kind: str) -> None:
        self._shown_message = text
        self._message.show_message(text, kind)

    def _clear_output(self) -> None:
        self._shown_answer = ""
        self._shown_citations = []
        self._shown_grounding = ""
        self._shown_message = ""
        self._answer.clear()
        self._answer.setVisible(False)
        self._grounding.setVisible(False)
        self._citations.clear()
        self._citations.setVisible(False)
        self._message.clear_message()

    def _on_provider_status(self, status) -> None:
        self._provider_status.setText(_PROVIDER_TEXT.get(status.reason, "AI provider status unknown"))
        guidance = _PROVIDER_GUIDANCE.get(status.reason, "")
        self._guidance.setText(guidance)
        self._guidance.setVisible(bool(guidance))

    def _on_provider_status_error(self, _exc) -> None:
        self._provider_status.setText("AI provider status unavailable")
        self._guidance.setText("The AI provider status could not be read.")
        self._guidance.setVisible(True)

    # --- control state ---
    def _sync_controls_enabled(self) -> None:
        self._question.setEnabled(not self._running)
        self._sync_ask_enabled()

    def _sync_ask_enabled(self) -> None:
        ready = (not self._running and self._c.ask_fin_available()
                 and bool(self._c.active_review_id)
                 and bool(self._question.toPlainText().strip()))
        self._ask.setEnabled(ready)

    # --- public seams (stable API for tests and integrators) ---
    def current_status(self) -> str:
        return self._state.value

    def is_request_running(self) -> bool:
        return self._running

    def set_question(self, text: str) -> None:
        self._question.setPlainText(text)

    def question_input_enabled(self) -> bool:
        return self._question.isEnabled()

    def ask_button_enabled(self) -> bool:
        return self._ask.isEnabled()

    def displayed_answer(self) -> str:
        return self._shown_answer

    def displayed_citations(self) -> List[str]:
        return list(self._shown_citations)

    def displayed_message(self) -> str:
        return self._shown_message

    def grounding_text(self) -> str:
        return self._shown_grounding

    def provider_status_text(self) -> str:
        return self._provider_status.text()

    def ask_fin_guidance_text(self) -> str:
        """Availability guidance for the current provider state ('' when ready). Result-specific
        guidance (REFUSED / grounding-unavailable) is surfaced via displayed_message()."""
        return self._guidance.text()
