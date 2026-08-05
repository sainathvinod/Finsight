"""Focused UI checks for the private, review-scoped Stage 2 Ask Fin panel."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QPushButton, QWidget

from finsight.application.ai.contracts import ProviderStatus
from finsight.application.ai.private_contracts import (
    AskFinMode,
    PrivateAskFinResult,
    PrivateAskFinSession,
    PrivateAskFinStatus,
    PrivateCitation,
)
from finsight.delivery.desktop.views.private_ask_fin_dialog import (
    PrivateAskFinDialog,
)


pytestmark = pytest.mark.ui


class _PrivateAskFinController:
    def __init__(self):
        self.questions: list[tuple[str, object]] = []
        self.session_contexts: list[object] = []
        self.session_review_ids: list[str | None] = []
        self.question_review_ids: list[str | None] = []

    def private_ask_fin_provider_status_async(self, on_result, _on_error):
        on_result(
            ProviderStatus(
                operational=True,
                generation_available=True,
                reason="ok",
            )
        )

    def private_ask_fin_session_async(
        self, on_result, _on_error, *, context=None, review_id=None
    ):
        self.session_contexts.append(context)
        self.session_review_ids.append(review_id)
        on_result(
            PrivateAskFinSession(
                mode=AskFinMode.FINANCIAL_REVIEW,
                greeting=(
                    "I can explain the recorded May 2026 review and its "
                    "deterministic evidence."
                ),
                suggested_questions=(
                    "Why did FinSight flag this finding?",
                    "Which source rows support it?",
                ),
                review_id="review-may-2026",
                reporting_period="May 2026",
                validation_run_id="run-1",
                scope_label=context.label if context is not None else "Active review",
            )
        )

    def private_ask_fin_ask_async(
        self,
        question,
        on_result,
        _on_error,
        *,
        context=None,
        review_id=None,
    ):
        self.questions.append((question, context))
        self.question_review_ids.append(review_id)
        on_result(
            PrivateAskFinResult(
                status=PrivateAskFinStatus.OK,
                mode=AskFinMode.FINANCIAL_REVIEW,
                answer_text=(
                    "The recorded finding failed because the GED transaction "
                    "did not map to a Budget department/account combination."
                ),
                citations=(
                    PrivateCitation(
                        key="finding:finding-1",
                        review_id="review-may-2026",
                        object_type="finding",
                        object_id="finding-1",
                        label="Valid Account Coding finding",
                        navigation_target={"tab": "findings"},
                    ),
                ),
                review_id="review-may-2026",
                reporting_period="May 2026",
                validation_run_id="run-1",
            )
        )


def test_private_ask_fin_uses_real_provider_contract_and_accessible_greeting(
    qtbot,
):
    controller = _PrivateAskFinController()
    dialog = PrivateAskFinDialog(controller)
    qtbot.addWidget(dialog)

    dialog.open_for(
        review_id="review-may-2026",
        object_type="finding",
        object_id="finding-1",
        label="Valid Account Coding",
    )

    assert dialog.isVisible()
    assert dialog.windowTitle() == "Ask Fin"
    assert dialog._provider.text() == "Local Ollama ready"
    assert dialog._mode.text() == "Financial Review Mode"
    assert dialog._scope.text() == "Valid Account Coding"
    assert dialog._clear_scope.isVisible()
    assert dialog._clear_scope.accessibleName()
    assert "recorded May 2026 review" in dialog._greeting.text()
    assert dialog._question.accessibleName() == "Question for Ask Fin"
    assert dialog._question.focusPolicy() != Qt.FocusPolicy.NoFocus
    assert dialog._send_button.accessibleName() == "Send question to Ask Fin"
    assert len(dialog._suggested_buttons) == 2
    assert all(
        button.accessibleName().startswith("Ask suggested question:")
        for button in dialog._suggested_buttons
    )
    assert controller.session_review_ids == ["review-may-2026"]
    assert dialog._initial_panel.isVisible()

    qtbot.mouseClick(dialog._suggested_buttons[0], Qt.MouseButton.LeftButton)
    assert controller.questions
    question, context = controller.questions[0]
    assert question == "Why did FinSight flag this finding?"
    assert context.review_id == "review-may-2026"
    assert context.object_type == "finding"
    assert context.object_id == "finding-1"
    assert controller.question_review_ids == ["review-may-2026"]
    assert "did not map to a Budget" in dialog._transcript.toPlainText()
    assert not dialog._initial_panel.isVisible()
    messages = dialog.conversation_messages()
    assert [message.role for message in messages] == ["user", "assistant"]
    assert not any(message.pending for message in messages)
    assert messages[-1].citations
    user_bubble = dialog.findChild(QWidget, "AskFinUserBubble")
    fin_bubble = dialog.findChild(QWidget, "AskFinAssistantBubble")
    assert user_bubble is not None
    assert fin_bubble is not None
    assert user_bubble.accessibleName().startswith("You message:")
    assert fin_bubble.accessibleName().startswith("Fin message:")

    evidence_toggles = [
        button
        for button in dialog.findChildren(QPushButton)
        if button.objectName() == "AskFinEvidenceToggle"
    ]
    assert len(evidence_toggles) == 1
    assert evidence_toggles[0].text() == "Show evidence (1)"
    citation_spy = QSignalSpy(dialog.citationActivated)
    qtbot.mouseClick(evidence_toggles[0], Qt.MouseButton.LeftButton)
    assert evidence_toggles[0].text() == "Hide evidence (1)"
    citation_buttons = [
        button
        for button in dialog.findChildren(QPushButton)
        if button.text() == "Open source"
    ]
    assert len(citation_buttons) == 1
    assert citation_buttons[0].accessibleName() == (
        "Open Ask Fin citation Valid Account Coding finding"
    )
    qtbot.mouseClick(citation_buttons[0], Qt.MouseButton.LeftButton)
    assert citation_spy.count() == 1
    assert dialog._message.text() == (
        "Answer grounded in the cited active-review records."
    )
    assert not dialog._message.isVisible()
    assert dialog._last_accessibility_announcement == (
        "Ask Fin answered with 1 recorded source."
    )

    qtbot.mouseClick(dialog._clear_scope, Qt.MouseButton.LeftButton)
    assert controller.session_contexts[-1] is None
    assert dialog._context is None
    assert dialog._scope.text() == "Active review"
    assert not dialog._clear_scope.isVisible()
    assert dialog._question.isEnabled()


class _UnavailablePrivateAskFinController(_PrivateAskFinController):
    def private_ask_fin_provider_status_async(self, on_result, _on_error):
        on_result(
            ProviderStatus(
                operational=False,
                generation_available=False,
                reason="model_identity_unconfigured",
            )
        )


def test_private_ask_fin_unavailable_state_is_fail_closed_and_reassuring(qtbot):
    dialog = PrivateAskFinDialog(_UnavailablePrivateAskFinController())
    qtbot.addWidget(dialog)

    dialog.open_for(
        review_id="review-may-2026",
        label="Active review",
    )

    assert dialog._provider.text() == "Local Ollama unavailable"
    assert not dialog._question.isEnabled()
    assert not dialog._send_button.isEnabled()
    assert dialog._unavailable_card.isVisible()
    assert not dialog._conversation_surface.isVisible()
    assert dialog._availability_guidance.text() == (
        "Ask Fin could not use the selected local model. Retry the connection."
    )
    assert [
        button.text() for button in dialog._unavailable_card.findChildren(QPushButton)
    ] == ["Retry"]
    assert not dialog._message.isVisible()


class _MidRequestUnavailableController(_PrivateAskFinController):
    def private_ask_fin_ask_async(
        self,
        _question,
        _on_result,
        on_error,
        *,
        context=None,
        review_id=None,
    ):
        on_error(RuntimeError("local Ollama stopped"))


def test_mid_request_failure_uses_the_same_single_retry_state(qtbot):
    dialog = PrivateAskFinDialog(_MidRequestUnavailableController())
    qtbot.addWidget(dialog)
    dialog.open_for(review_id="review-may-2026", label="Active review")

    dialog._question.setText("Explain this variance")
    qtbot.mouseClick(dialog._send_button, Qt.MouseButton.LeftButton)

    assert dialog._unavailable_card.isVisible()
    assert not dialog._conversation_surface.isVisible()
    assert dialog._availability_guidance.text() == (
        "Ask Fin could not connect to local Ollama. Start Ollama, then retry."
    )
    assert [
        button.text() for button in dialog._unavailable_card.findChildren(QPushButton)
    ] == ["Retry"]
