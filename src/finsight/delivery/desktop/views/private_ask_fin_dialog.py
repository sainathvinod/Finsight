"""Private, review-scoped Ask Fin right-side drawer."""
from __future__ import annotations

import re
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from finsight.application.ai.private_contracts import (
    AskFinContext,
    LocalAiSetupState,
)
from finsight.delivery.desktop.components.iconography import content_icon
from finsight.delivery.desktop.theme import tokens as t


_INLINE_CITATION = re.compile(r"\s*\[[a-z][a-z0-9_-]*:[^\[\]\s]+\]")


def _label(text: str, role: str, *, wrap: bool = False) -> QLabel:
    value = QLabel(text)
    value.setProperty("role", role)
    value.setWordWrap(wrap)
    return value


class PrivateAskFinDialog(QWidget):
    """Reusable integrated drawer backed only by the private Ask Fin service."""

    citationActivated = Signal(object)
    closeRequested = Signal()

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._context: AskFinContext | None = None
        self._review_id = ""
        self._no_review_selected = False
        self._provider_available: bool | None = None
        self._session_is_ready = False
        self._running = False
        self._running_reviews: set[str] = set()
        self._load_generation = 0
        self._suggested_buttons: list[QPushButton] = []
        self._conversation_by_review: dict[
            str, list[tuple[str, str]]
        ] = {}
        self.setObjectName("PrivateAskFinDrawer")
        self.setWindowTitle("Ask Fin")
        self.setAccessibleName("Ask Fin private assistant drawer")
        self.setMinimumWidth(360)
        self.setMaximumWidth(560)

        root = QVBoxLayout(self)
        root.setContentsMargins(t.SP_4, t.SP_4, t.SP_4, t.SP_4)
        root.setSpacing(t.SP_3)

        heading = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(t.SP_1)
        title_box.addWidget(_label("Ask Fin", "sectionHeader"))
        title_box.addWidget(
            _label(
                "Private explanations from your local Ollama model.",
                "sectionSub",
                wrap=True,
            )
        )
        heading.addLayout(title_box, 1)
        self._close_button = QPushButton()
        self._close_button.setObjectName("AskFinDrawerClose")
        self._close_button.setProperty("role", "quiet")
        self._close_button.setAccessibleName("Close Ask Fin")
        self._close_button.setToolTip("Close Ask Fin (Esc)")
        self._close_button.setFixedSize(32, 32)
        self._close_button.clicked.connect(self.request_close)
        self.refresh_icon()
        heading.addWidget(
            self._close_button, 0, Qt.AlignmentFlag.AlignTop
        )
        root.addLayout(heading)

        privacy = QFrame()
        privacy.setProperty("role", "noticeCard")
        privacy_layout = QVBoxLayout(privacy)
        privacy_layout.setContentsMargins(t.SP_3, t.SP_2, t.SP_3, t.SP_2)
        privacy_layout.setSpacing(t.SP_1)
        privacy_layout.addWidget(
            _label(
                "Private local AI · Ollama only · no cloud fallback",
                "success",
                wrap=True,
            )
        )
        privacy_layout.addWidget(
            _label(
                "Only authorized facts from this active review are sent to "
                "the local model. The deterministic rule engine remains the "
                "source of truth.",
                "context",
                wrap=True,
            )
        )
        root.addWidget(privacy)

        context_row = QHBoxLayout()
        context_row.setSpacing(t.SP_2)
        self._mode = _label("Preparing mode…", "statusPill")
        self._mode.setAccessibleName("Ask Fin mode")
        context_row.addWidget(self._mode)
        self._scope = _label("Active review", "context", wrap=True)
        self._scope.setAccessibleName("Ask Fin scope")
        context_row.addWidget(self._scope, 1)
        self._clear_scope = QPushButton("Clear scope")
        self._clear_scope.setProperty("role", "quiet")
        self._clear_scope.setAccessibleName(
            "Clear Ask Fin context and return to the active review"
        )
        self._clear_scope.setToolTip(
            "Return Ask Fin to the full active-review scope."
        )
        self._clear_scope.clicked.connect(self._clear_context)
        self._clear_scope.setVisible(False)
        context_row.addWidget(self._clear_scope)
        root.addLayout(context_row)

        self._unavailable_card = QFrame()
        self._unavailable_card.setObjectName("AskFinUnavailableCard")
        self._unavailable_card.setProperty("role", "noticeCard")
        unavailable_layout = QVBoxLayout(self._unavailable_card)
        unavailable_layout.setContentsMargins(
            t.SP_3, t.SP_3, t.SP_3, t.SP_3
        )
        unavailable_layout.setSpacing(t.SP_2)
        self._availability_guidance = _label(
            "Ask Fin could not connect to local Ollama. Start Ollama, then retry.",
            "warning",
            wrap=True,
        )
        self._availability_guidance.setAccessibleName(
            "Ask Fin unavailable message"
        )
        unavailable_layout.addWidget(self._availability_guidance)
        unavailable_actions = QHBoxLayout()
        self._retry_button = QPushButton("Retry")
        self._retry_button.setProperty("role", "secondary")
        self._retry_button.setAccessibleName(
            "Retry local Ask Fin connection"
        )
        self._retry_button.clicked.connect(self.retry)
        unavailable_actions.addWidget(self._retry_button)
        unavailable_actions.addStretch(1)
        unavailable_layout.addLayout(unavailable_actions)
        self._unavailable_card.setVisible(False)
        root.addWidget(self._unavailable_card)

        self._conversation_surface = QWidget()
        self._conversation_surface.setObjectName("AskFinConversationSurface")
        conversation_layout = QVBoxLayout(self._conversation_surface)
        conversation_layout.setContentsMargins(0, 0, 0, 0)
        conversation_layout.setSpacing(t.SP_3)

        self._greeting = _label(
            "Ask how FinSight works or ask about the recorded financial "
            "review after validation.",
            "cardDetail",
            wrap=True,
        )
        self._greeting.setAccessibleName("Ask Fin greeting")
        conversation_layout.addWidget(self._greeting)

        self._suggestions = QScrollArea()
        self._suggestions.setObjectName("AskFinSuggestions")
        self._suggestions.setFrameShape(QFrame.Shape.NoFrame)
        self._suggestions.setWidgetResizable(True)
        self._suggestions.setMaximumHeight(132)
        self._suggestions.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._suggestion_holder = QWidget()
        self._suggestion_layout = QVBoxLayout(self._suggestion_holder)
        self._suggestion_layout.setContentsMargins(0, 0, 0, 0)
        self._suggestion_layout.setSpacing(t.SP_1)
        self._suggestions.setWidget(self._suggestion_holder)
        conversation_layout.addWidget(self._suggestions)

        self._transcript = QTextBrowser()
        self._transcript.setObjectName("AskFinConversation")
        self._transcript.setAccessibleName("Ask Fin private conversation")
        self._transcript.setOpenExternalLinks(False)
        self._transcript.setPlaceholderText(
            "Your private conversation will appear here."
        )
        self._transcript.setMinimumHeight(128)
        self._transcript.setMaximumHeight(280)
        conversation_layout.addWidget(self._transcript)

        self._citation_holder = QWidget()
        self._citation_layout = QVBoxLayout(self._citation_holder)
        self._citation_layout.setContentsMargins(0, 0, 0, 0)
        self._citation_layout.setSpacing(t.SP_1)
        conversation_layout.addWidget(self._citation_holder)

        self._question_holder = QWidget()
        question_row = QHBoxLayout(self._question_holder)
        question_row.setContentsMargins(0, 0, 0, 0)
        question_row.setSpacing(t.SP_2)
        self._question = QLineEdit()
        self._question.setAccessibleName("Question for Ask Fin")
        self._question.setPlaceholderText(
            "Ask about this review or how FinSight works"
        )
        self._question.returnPressed.connect(self._send)
        question_row.addWidget(self._question, 1)
        self._send_button = QPushButton("Send")
        self._send_button.setProperty("role", "assistant")
        self._send_button.setAccessibleName("Send question to Ask Fin")
        self._send_button.clicked.connect(self._send)
        question_row.addWidget(self._send_button)
        conversation_layout.addWidget(self._question_holder)

        self._provider = _label(
            "Checking local Ollama…", "context", wrap=True
        )
        self._provider.setAccessibleName("Local Ask Fin connection")
        self._provider.setVisible(False)
        conversation_layout.addWidget(self._provider)
        self._message = _label("", "context", wrap=True)
        self._message.setAccessibleName("Ask Fin status message")
        conversation_layout.addWidget(self._message)
        conversation_layout.addStretch(1)
        root.addWidget(self._conversation_surface, 1)
        self._unavailable_filler = QWidget()
        self._unavailable_filler.setObjectName("AskFinUnavailableFiller")
        self._unavailable_filler.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self._unavailable_filler.setVisible(False)
        root.addWidget(self._unavailable_filler, 1)

        self._escape_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_Escape), self
        )
        self._escape_shortcut.setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        self._escape_shortcut.activated.connect(self.request_close)

    def request_close(self) -> None:
        self.hide()
        self.closeRequested.emit()

    def refresh_icon(self) -> None:
        """Refresh the drawer's theme-aware close glyph."""

        self._close_button.setIcon(content_icon("close", tone="header"))

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.request_close()
            event.accept()
            return
        super().keyPressEvent(event)

    def retry(self) -> None:
        self._provider_available = None
        self._session_is_ready = False
        self._sync_interaction_state()
        if self._review_id:
            self._load_session()
        else:
            self.initialize_status()

    def initialize_status(self) -> None:
        """Run the startup local-runtime check without reading review data."""

        self._load_generation += 1
        generation = self._load_generation
        self._provider_available = None
        self._sync_interaction_state()
        setup = getattr(
            self._controller,
            "private_ask_fin_setup_status_async",
            None,
        )
        if setup is not None:
            setup(
                lambda result: (
                    self._setup_status_ready(result)
                    if generation == self._load_generation
                    else None
                ),
                lambda error: (
                    self._provider_failed(error)
                    if generation == self._load_generation
                    else None
                ),
            )
            return
        self._controller.private_ask_fin_provider_status_async(
            lambda result: (
                self._provider_ready(result)
                if generation == self._load_generation
                else None
            ),
            lambda error: (
                self._provider_failed(error)
                if generation == self._load_generation
                else None
            ),
        )

    def open_for(
        self,
        *,
        review_id: str,
        object_type: str = "",
        object_id: str = "",
        label: str,
    ) -> None:
        self._no_review_selected = False
        self._review_id = review_id
        self._context = (
            AskFinContext(
                review_id=review_id,
                object_type=object_type,
                object_id=object_id,
                label=label,
            )
            if object_type and object_id
            else None
        )
        self._scope.setText(label or object_type.replace("_", " ").title())
        self._clear_scope.setVisible(self._context is not None)
        self._provider_available = None
        self._session_is_ready = False
        self._render_conversation()
        self._replace_citations(())
        self._sync_interaction_state()
        self.show()
        self._load_session()
        self._question.setFocus(Qt.FocusReason.OtherFocusReason)

    def open_without_review(self) -> None:
        """Open application-help framing before a review has been selected."""

        self._load_generation += 1
        self._no_review_selected = True
        self._review_id = ""
        self._context = None
        self._mode.setText("Help Mode")
        self._scope.setText("No review selected")
        self._clear_scope.setVisible(False)
        self._greeting.setText(
            "Create or open a financial review to ask grounded questions. "
            "Local setup status remains available here."
        )
        self._replace_suggestions(
            (
                "How do I start a financial review?",
                "What files does FinSight support?",
            )
        )
        self._session_is_ready = False
        self._provider_available = None
        self._render_conversation()
        self._replace_citations(())
        self._sync_interaction_state()
        self.show()
        self.initialize_status()

    def _set_running(
        self, running: bool, *, review_id: str | None = None
    ) -> None:
        key = review_id or self._review_id or "__help__"
        if running:
            self._running_reviews.add(key)
        else:
            self._running_reviews.discard(key)
        self._running = (
            (self._review_id or "__help__") in self._running_reviews
        )
        enabled = (
            not self._running
            and self._provider_available is True
            and self._session_is_ready
        )
        self._question.setEnabled(enabled)
        self._send_button.setEnabled(enabled)
        for button in self._suggested_buttons:
            button.setEnabled(enabled)
        self._send_button.setText("Working…" if self._running else "Send")

    def _clear_context(self) -> None:
        if not self._review_id:
            return
        self._context = None
        self._scope.setText("Active review")
        self._clear_scope.setVisible(False)
        self._session_is_ready = False
        self._sync_interaction_state()
        self._load_session()

    def _sync_interaction_state(self) -> None:
        key = self._review_id or "__help__"
        self._set_running(key in self._running_reviews, review_id=key)
        unavailable = self._provider_available is False
        self._unavailable_card.setVisible(unavailable)
        self._conversation_surface.setVisible(not unavailable)
        self._unavailable_filler.setVisible(unavailable)
        if self._provider_available is False:
            self._message.clear()
            self._message.setVisible(False)
        elif self._provider_available is None:
            self._message.setText("Connecting to local Ollama…")
            self._message.setVisible(True)
        elif self._no_review_selected:
            self._message.setText(
                "Create or open a review to start Application Help Mode. "
                "No information is sent to a cloud service."
            )
            self._message.setVisible(True)
        elif not self._session_is_ready:
            self._message.setText("Preparing private review context…")
            self._message.setVisible(True)
        else:
            self._message.clear()
            self._message.setVisible(False)

    def _load_session(self) -> None:
        self._load_generation += 1
        generation = self._load_generation
        self._sync_interaction_state()
        setup = getattr(
            self._controller,
            "private_ask_fin_setup_status_async",
            None,
        )
        if setup is not None:
            setup(
                lambda result: (
                    self._setup_status_ready(result)
                    if generation == self._load_generation
                    else None
                ),
                lambda error: (
                    self._provider_failed(error)
                    if generation == self._load_generation
                    else None
                ),
            )
        else:
            self._controller.private_ask_fin_provider_status_async(
                lambda result: (
                    self._provider_ready(result)
                    if generation == self._load_generation
                    else None
                ),
                lambda error: (
                    self._provider_failed(error)
                    if generation == self._load_generation
                    else None
                ),
            )
        self._controller.private_ask_fin_session_async(
            lambda result: (
                self._session_ready(result)
                if generation == self._load_generation
                else None
            ),
            lambda error: (
                self._session_failed(error)
                if generation == self._load_generation
                else None
            ),
            context=self._context,
        )

    def _setup_status_ready(self, status: Any) -> None:
        state = getattr(status, "state", None)
        available = state is LocalAiSetupState.HEALTHY
        self._provider_available = available
        labels = {
            LocalAiSetupState.NOT_INSTALLED: "Ollama not installed",
            LocalAiSetupState.SERVICE_NOT_RUNNING: (
                "Ollama service not running"
            ),
            LocalAiSetupState.MODEL_NOT_DOWNLOADED: (
                "Local model not downloaded"
            ),
            LocalAiSetupState.MODEL_NOT_APPROVED: "Local model unavailable",
            LocalAiSetupState.MODEL_VERIFICATION_FAILED: (
                "Local model unavailable"
            ),
            LocalAiSetupState.CONNECTION_FAILURE: (
                "Local Ollama connection failed"
            ),
            LocalAiSetupState.TIMEOUT: "Local Ollama timed out",
            LocalAiSetupState.HEALTHY: "Local Ollama ready",
        }
        self._provider.setText(labels.get(state, "Local Ollama unavailable"))
        self._provider.setProperty("role", "success" if available else "warning")
        self._availability_guidance.setText(
            self._setup_unavailable_message(state)
        )
        self._provider.style().unpolish(self._provider)
        self._provider.style().polish(self._provider)
        self._sync_interaction_state()

    def _provider_ready(self, status: Any) -> None:
        available = bool(getattr(status, "generation_available", False))
        self._provider_available = available
        self._provider.setText(
            "Local Ollama ready"
            if available
            else "Local Ollama unavailable"
        )
        self._provider.setProperty("role", "success" if available else "warning")
        self._availability_guidance.setText(
            self._provider_reason_message(
                str(getattr(status, "reason", "") or "")
            )
        )
        self._provider.style().unpolish(self._provider)
        self._provider.style().polish(self._provider)
        self._sync_interaction_state()

    def _provider_failed(self, _error: BaseException) -> None:
        self._provider_available = False
        self._provider.setText("Local Ollama connection failed")
        self._provider.setProperty("role", "warning")
        self._availability_guidance.setText(
            "Ask Fin could not connect to local Ollama. Start Ollama, then retry."
        )
        self._sync_interaction_state()

    @staticmethod
    def _setup_unavailable_message(state: Any) -> str:
        return {
            LocalAiSetupState.NOT_INSTALLED: (
                "Ask Fin could not find Ollama on this computer. Install or "
                "open Ollama, then retry."
            ),
            LocalAiSetupState.SERVICE_NOT_RUNNING: (
                "Ask Fin could not connect to local Ollama. Start Ollama, "
                "then retry."
            ),
            LocalAiSetupState.MODEL_NOT_DOWNLOADED: (
                "Ask Fin could not find the selected model in Ollama. "
                "Download the model, then retry."
            ),
            LocalAiSetupState.MODEL_NOT_APPROVED: (
                "Ask Fin could not use the selected local model. Retry the "
                "connection."
            ),
            LocalAiSetupState.MODEL_VERIFICATION_FAILED: (
                "Ask Fin could not use the selected local model. Retry the "
                "connection."
            ),
            LocalAiSetupState.CONNECTION_FAILURE: (
                "Ask Fin could not connect to local Ollama. Start Ollama, "
                "then retry."
            ),
            LocalAiSetupState.TIMEOUT: (
                "Local Ollama did not respond in time. Check that it is "
                "running, then retry."
            ),
        }.get(
            state,
            "Ask Fin could not connect to local Ollama. Start Ollama, then retry.",
        )

    @staticmethod
    def _provider_reason_message(reason: str) -> str:
        return {
            "status_timeout": (
                "The local Ollama service did not respond in time."
            ),
            "request_timeout": (
                "The local Ollama service did not respond in time."
            ),
            "model_missing": (
                "Ask Fin could not find the selected model in Ollama. "
                "Download the model, then retry."
            ),
            "model_identity_unconfigured": (
                "Ask Fin could not use the selected local model. Retry the "
                "connection."
            ),
            "connection_refused": (
                "Ask Fin could not connect to local Ollama. Start Ollama, "
                "then retry."
            ),
            "unreachable": (
                "Ask Fin could not connect to local Ollama. Start Ollama, "
                "then retry."
            ),
        }.get(
            reason,
            "Ask Fin could not connect to local Ollama. Start Ollama, then retry.",
        )

    def _session_ready(self, session: Any) -> None:
        mode = getattr(getattr(session, "mode", None), "value", "")
        self._mode.setText(
            "Help Mode"
            if mode == "application_help"
            else "Financial Review Mode"
        )
        self._greeting.setText(str(getattr(session, "greeting", "")))
        scope = str(getattr(session, "scope_label", "") or "")
        if scope:
            self._scope.setText(scope)
        self._replace_suggestions(
            tuple(getattr(session, "suggested_questions", ()) or ())
        )
        self._session_is_ready = True
        self._sync_interaction_state()

    def _session_failed(self, _error: BaseException) -> None:
        self._session_is_ready = False
        self._provider_available = False
        self._availability_guidance.setText(
            "Ask Fin could not prepare this review. Retry the connection."
        )
        self._sync_interaction_state()

    def _replace_suggestions(self, questions: tuple[str, ...]) -> None:
        for button in self._suggested_buttons:
            button.deleteLater()
        self._suggested_buttons.clear()
        for question in questions[:4]:
            button = QPushButton(question)
            button.setProperty("role", "summaryAction")
            button.setAccessibleName(f"Ask suggested question: {question}")
            button.setMaximumHeight(38)
            button.clicked.connect(
                lambda _checked=False, value=question: self._ask(value)
            )
            self._suggestion_layout.addWidget(button)
            self._suggested_buttons.append(button)
        self._sync_interaction_state()

    def _send(self) -> None:
        self._ask(self._question.text())

    def _ask(self, question: str) -> None:
        clean = str(question).strip()
        request_review_id = self._review_id or "__help__"
        if (
            request_review_id in self._running_reviews
            or not clean
            or self._provider_available is not True
            or not self._session_is_ready
        ):
            return
        request_context = self._context
        self._question.clear()
        self._append_conversation(
            "You", clean, review_id=request_review_id
        )
        self._set_running(True, review_id=request_review_id)
        self._message.setText(
            "Retrieving authorized review evidence locally…"
        )
        self._controller.private_ask_fin_ask_async(
            clean,
            lambda result: self._answer_ready(
                result, review_id=request_review_id
            ),
            lambda error: self._answer_failed(
                error, review_id=request_review_id
            ),
            context=request_context,
        )

    def _answer_ready(
        self, result: Any, *, review_id: str | None = None
    ) -> None:
        key = review_id or self._review_id or "__help__"
        self._set_running(False, review_id=key)
        answer = str(getattr(result, "answer_text", "") or "")
        status = getattr(getattr(result, "status", None), "value", "")
        if status == "unavailable":
            if key == (self._review_id or "__help__"):
                self._provider_available = False
                self._availability_guidance.setText(
                    "Ask Fin could not connect to local Ollama. Start Ollama, "
                    "then retry."
                )
                self._replace_citations(())
                self._sync_interaction_state()
            return
        display_answer = _INLINE_CITATION.sub("", answer).strip()
        self._append_conversation(
            "Ask Fin",
            display_answer or answer,
            review_id=key,
        )
        if key != (self._review_id or "__help__"):
            return
        self._message.setText(
            {
                "ok": "Answer grounded in the cited active-review records.",
                "refused": (
                    "Ask Fin cannot make financial decisions. Review the "
                    "recorded evidence and use human governance."
                ),
                "unanswerable": (
                    "The active review does not contain enough recorded "
                    "evidence to answer that question."
                ),
                "unavailable": (
                    "Local Ollama is unavailable. No external service was used."
                ),
            }.get(status, "Ask Fin could not complete the request.")
        )
        self._message.setVisible(True)
        self._replace_citations(
            tuple(getattr(result, "citations", ()) or ())
        )

    def _answer_failed(
        self,
        _error: BaseException,
        *,
        review_id: str | None = None,
    ) -> None:
        key = review_id or self._review_id or "__help__"
        self._set_running(False, review_id=key)
        if key != (self._review_id or "__help__"):
            return
        self._provider_available = False
        self._availability_guidance.setText(
            "Ask Fin could not connect to local Ollama. Start Ollama, then retry."
        )
        self._replace_citations(())
        self._sync_interaction_state()

    def _append_conversation(
        self,
        role: str,
        text: str,
        *,
        review_id: str | None = None,
    ) -> None:
        key = review_id or self._review_id or "__help__"
        self._conversation_by_review.setdefault(key, []).append((role, text))
        if key == (self._review_id or "__help__"):
            self._render_conversation()

    def _render_conversation(self) -> None:
        key = self._review_id or "__help__"
        rows = self._conversation_by_review.get(key, [])
        self._transcript.clear()
        for role, value in rows:
            self._transcript.append(
                f"<p><b>{self._escape(role)}</b><br>"
                f"{self._escape(value)}</p>"
            )

    def _replace_citations(self, citations: tuple[Any, ...]) -> None:
        while self._citation_layout.count():
            item = self._citation_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for citation in citations:
            label = str(getattr(citation, "label", "Open evidence"))
            action = QPushButton(f"Open source: {label}")
            action.setProperty("role", "quiet")
            action.setAccessibleName(f"Open Ask Fin citation {label}")
            action.clicked.connect(
                lambda _checked=False, value=citation:
                self.citationActivated.emit(value)
            )
            self._citation_layout.addWidget(action)

    @staticmethod
    def _escape(value: str) -> str:
        return (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )


# New code may use the explicit name while existing imports remain compatible.
PrivateAskFinDrawer = PrivateAskFinDialog


__all__ = ["PrivateAskFinDialog", "PrivateAskFinDrawer"]
