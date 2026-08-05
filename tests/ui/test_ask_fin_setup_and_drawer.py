"""Focused UI checks for local setup and the integrated Ask Fin drawer."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QLabel, QWidget

from finsight.application.ai.contracts import ProviderStatus
from finsight.application.ai.private_contracts import (
    AskFinMode,
    LocalAiSetupState,
    LocalAiSetupStatus,
    PrivateAskFinResult,
    PrivateAskFinSession,
    PrivateAskFinStatus,
    PrivateCitation,
)
from finsight.delivery.desktop.ask_fin_preferences import (
    PrivateAskFinPreferenceStore,
)
from finsight.delivery.desktop.views.private_ask_fin_dialog import (
    PrivateAskFinDialog,
)
from finsight.delivery.desktop.views.settings_view import SettingsView


pytestmark = pytest.mark.ui


class _DrawerController:
    def __init__(self, state=LocalAiSetupState.HEALTHY):
        self.state = state
        self.validation_run_id = "run-1"

    def private_ask_fin_setup_status_async(self, on_result, _on_error, **_kwargs):
        on_result(
            LocalAiSetupStatus(
                state=self.state,
                endpoint="http://localhost:11434",
                model="llama3.2:3b",
                message=(
                    "Ask Fin is ready."
                    if self.state is LocalAiSetupState.HEALTHY
                    else "Start the local Ollama service."
                ),
            )
        )

    def private_ask_fin_provider_status_async(self, on_result, _on_error):
        on_result(ProviderStatus(True, True, "ok"))

    def private_ask_fin_session_async(
        self, on_result, _on_error, *, context=None, review_id=None
    ):
        on_result(
            PrivateAskFinSession(
                mode=AskFinMode.FINANCIAL_REVIEW,
                greeting="I can explain this recorded review.",
                suggested_questions=("What needs attention?",),
                review_id="review-1",
                validation_run_id=self.validation_run_id,
                scope_label=context.label if context else "Active review",
            )
        )

    def private_ask_fin_ask_async(
        self,
        _question,
        _on_result,
        _on_error,
        *,
        context=None,
        review_id=None,
    ):
        raise AssertionError("not used")


class _DeferredDrawerController(_DrawerController):
    def __init__(self):
        super().__init__()
        self.pending = None
        self.questions = []

    def private_ask_fin_ask_async(
        self,
        question,
        on_result,
        on_error,
        *,
        context=None,
        review_id=None,
    ):
        self.questions.append((question, context))
        self.pending = (on_result, on_error)

    def answer(self, text="Recorded review summary"):
        on_result, _on_error = self.pending
        on_result(
            PrivateAskFinResult(
                status=PrivateAskFinStatus.OK,
                mode=AskFinMode.FINANCIAL_REVIEW,
                answer_text=(f"{text} [account:review-1:00-0245|555035]"),
                citations=(
                    PrivateCitation(
                        key="account:review-1:00-0245|555035",
                        review_id="review-1",
                        object_type="account",
                        object_id="00-0245|555035",
                        label="Account 555035",
                        navigation_target={
                            "view": "financial_analysis",
                            "tab": "account",
                        },
                    ),
                ),
                review_id="review-1",
                validation_run_id="run-1",
            )
        )

    def answer_with_presentation(
        self,
        *,
        text: str,
        follow_up_questions: tuple[str, ...],
        resolved_context=None,
    ):
        on_result, _on_error = self.pending
        on_result(
            SimpleNamespace(
                status=PrivateAskFinStatus.OK,
                mode=AskFinMode.FINANCIAL_REVIEW,
                answer_text=text,
                citations=(
                    PrivateCitation(
                        key="account:review-1:00-0245|555035",
                        review_id="review-1",
                        object_type="account",
                        object_id="00-0245|555035",
                        label="Account 555035 — Outside Consultants' Fees",
                        navigation_target={
                            "view": "financial_analysis",
                            "tab": "account",
                        },
                    ),
                    PrivateCitation(
                        key="transaction:review-1:GED-246",
                        review_id="review-1",
                        object_type="transaction",
                        object_id="GED-246",
                        label="GED row 246",
                        navigation_target={
                            "view": "source_evidence",
                            "source_role": "GED",
                            "worksheet": "General Expense Detail",
                            "source_row": 246,
                        },
                        evidence_details={
                            "account_number": "555035",
                            "vendor_name": "TEKSYSTEMS",
                            "transaction_reference": "PCARD_0526",
                            "amount_label": "$125,000.00",
                        },
                    ),
                ),
                follow_up_questions=follow_up_questions,
                resolved_context=resolved_context,
                review_id="review-1",
                validation_run_id="run-1",
            )
        )


class _SettingsController:
    def __init__(self):
        self.probes = []
        self.saved = []

    def private_ask_fin_configuration(self):
        return SimpleNamespace(
            endpoint="http://localhost:11434",
            model="llama3.2:3b",
            approved_model_digest="",
            environment_override=False,
        )

    def private_ask_fin_setup_status_async(self, on_result, _on_error, **configuration):
        self.probes.append(configuration)
        on_result(
            LocalAiSetupStatus(
                state=LocalAiSetupState.HEALTHY,
                endpoint=configuration["endpoint"],
                model=configuration["model"],
                message="Ask Fin is ready.",
                available_models=("llama3.2:3b",),
                observed_model_digest="sha256:" + ("a" * 64),
            )
        )

    def private_ask_fin_save_configuration(self, **configuration):
        self.saved.append(configuration)
        return SimpleNamespace(
            endpoint=configuration["endpoint"],
            model=configuration["model"],
            approved_model_digest=configuration["approved_model_digest"],
            environment_override=False,
        )


def test_drawer_is_embeddable_closes_with_escape_and_preserves_review_history(
    qtbot,
):
    parent = QWidget()
    qtbot.addWidget(parent)
    host = PrivateAskFinDialog(_DrawerController(), parent=parent)
    parent.show()
    host.open_for(review_id="review-1", label="Active review")
    host._append_conversation("You", "Explain the variance")

    assert host.isVisible()
    assert not host.isWindow()
    assert host.minimumWidth() >= 360
    assert host.maximumWidth() <= 560
    assert host._question.isEnabled()
    assert "Explain the variance" in host._transcript.toPlainText()
    assert not host._initial_panel.isVisible()

    host.open_for(review_id="review-2", label="Active review")
    assert "Explain the variance" not in host._transcript.toPlainText()
    host.open_for(review_id="review-1", label="Active review")
    assert "Explain the variance" in host._transcript.toPlainText()

    qtbot.keyClick(host, Qt.Key.Key_Escape)
    assert not host.isVisible()


def test_unavailable_drawer_shows_one_message_and_one_retry_action(qtbot):
    controller = _DrawerController(LocalAiSetupState.SERVICE_NOT_RUNNING)
    drawer = PrivateAskFinDialog(controller)
    qtbot.addWidget(drawer)
    drawer.open_for(review_id="review-1", label="Active review")

    assert drawer._unavailable_card.isVisible()
    assert not drawer._conversation_surface.isVisible()
    assert not drawer._question.isEnabled()
    actions = drawer._unavailable_card.findChildren(type(drawer._send_button))
    assert [button.text() for button in actions] == ["Retry"]
    assert not any(
        button.text() == "Open Setup"
        for button in drawer.findChildren(type(drawer._send_button))
    )
    assert "start ollama" in drawer._availability_guidance.text().lower()

    controller.state = LocalAiSetupState.HEALTHY
    qtbot.mouseClick(drawer._retry_button, Qt.MouseButton.LeftButton)

    assert not drawer._unavailable_card.isVisible()
    assert drawer._conversation_surface.isVisible()
    assert drawer._question.isEnabled()


def test_late_answer_never_appears_in_a_different_review(qtbot):
    drawer = PrivateAskFinDialog(_DrawerController())
    qtbot.addWidget(drawer)
    drawer.open_for(review_id="review-1", label="Active review")
    drawer._set_running(True, review_id="review-1")
    drawer.open_for(review_id="review-2", label="Active review")

    drawer._answer_ready(
        PrivateAskFinResult(
            status=PrivateAskFinStatus.OK,
            mode=AskFinMode.FINANCIAL_REVIEW,
            answer_text="Review one private answer",
            citations=(),
            review_id="review-1",
        ),
        review_id="review-1",
    )

    assert "Review one private answer" not in drawer._transcript.toPlainText()
    drawer.open_for(review_id="review-1", label="Active review")
    assert "Review one private answer" in drawer._transcript.toPlainText()


def test_revalidation_clears_old_chat_and_rejects_stale_run_answer(qtbot):
    controller = _DrawerController()
    drawer = PrivateAskFinDialog(controller)
    qtbot.addWidget(drawer)
    drawer.open_for(review_id="review-1", label="Active review")
    drawer._append_conversation("You", "Summarize the original run")
    drawer._capture_resolved_context(
        "review-1",
        SimpleNamespace(
            review_id="review-2",
            object_type="finding",
            object_id="wrong-review-finding",
            validation_run_id="run-1",
        ),
        validation_run_id="run-1",
    )
    assert "review-1" not in drawer._resolved_context_by_review
    drawer._capture_resolved_context(
        "review-1",
        SimpleNamespace(
            review_id="review-1",
            object_type="finding",
            object_id="finding-1",
            label="Finding 1",
            validation_run_id="run-1",
        ),
        validation_run_id="run-1",
    )
    assert drawer.conversation_messages()
    assert "review-1" in drawer._resolved_context_by_review

    controller.validation_run_id = "run-2"
    drawer.refresh_review()

    assert not drawer.conversation_messages()
    assert "review-1" not in drawer._resolved_context_by_review
    assert drawer._initial_panel.isVisible()
    assert drawer._validation_run_by_review["review-1"] == "run-2"

    drawer._append_conversation("You", "Summarize the current run")
    drawer._conversation_by_review["review-1"].append(
        SimpleNamespace(
            role="assistant",
            text="Reviewing the recorded evidence…",
            status="",
            citations=(),
            pending=True,
            evidence_expanded=False,
            validation_run_id="run-2",
            speaker="Fin",
        )
    )
    drawer._answer_ready(
        PrivateAskFinResult(
            status=PrivateAskFinStatus.OK,
            mode=AskFinMode.FINANCIAL_REVIEW,
            answer_text="Stale answer",
            citations=(),
            review_id="review-1",
            validation_run_id="run-1",
        ),
        review_id="review-1",
    )

    assert "Stale answer" not in drawer._transcript.toPlainText()
    assert not drawer.conversation_messages()
    assert drawer._initial_panel.isVisible()
    assert drawer._validation_run_by_review["review-1"] == "run-2"
    assert drawer._last_accessibility_announcement == (
        "Ask Fin discarded an answer from an older validation run."
    )


def test_visible_drawer_refreshes_when_financial_review_changes(
    window_factory,
    empty_db,
    qtbot,
    monkeypatch,
):
    window = window_factory(empty_db)
    window.show()
    drawer = window._ask_fin_drawer
    drawer._review_id = "review-1"
    drawer.show()
    refreshes: list[str] = []
    monkeypatch.setattr(
        drawer,
        "refresh_review",
        lambda: refreshes.append("review-1"),
    )

    window._c.financialReviewChanged.emit("another-review")
    assert not refreshes

    window._c.financialReviewChanged.emit("review-1")
    qtbot.waitUntil(lambda: bool(refreshes))
    assert refreshes == ["review-1"]


def test_drawer_hides_raw_inline_tokens_and_blocks_help_suggestions(qtbot):
    drawer = PrivateAskFinDialog(_DrawerController())
    qtbot.addWidget(drawer)
    drawer.open_without_review()

    assert drawer._suggested_buttons
    assert all(not button.isEnabled() for button in drawer._suggested_buttons)

    drawer.open_for(review_id="review-1", label="Active review")
    drawer._answer_ready(
        PrivateAskFinResult(
            status=PrivateAskFinStatus.OK,
            mode=AskFinMode.FINANCIAL_REVIEW,
            answer_text=("Account spend is $12,000. [account:review-1:00-0245|555035]"),
            citations=(SimpleNamespace(label="Account 555035"),),
            review_id="review-1",
        ),
        review_id="review-1",
    )

    transcript = drawer._transcript.toPlainText()
    assert "Account spend is $12,000." in transcript
    assert "[account:" not in transcript
    assert drawer._citation_layout.count() == 1


def test_chat_hides_prompts_on_first_message_and_replaces_loading_bubble(qtbot):
    controller = _DeferredDrawerController()
    drawer = PrivateAskFinDialog(controller)
    qtbot.addWidget(drawer)
    drawer.resize(520, 760)
    drawer.open_for(review_id="review-1", label="May 2026 review")

    assert drawer._initial_panel.isVisible()
    assert drawer._suggested_buttons[0].isVisibleTo(drawer)

    drawer._question.setText("Summarize this review")
    qtbot.keyClick(
        drawer._question,
        Qt.Key.Key_Return,
        modifier=Qt.KeyboardModifier.ShiftModifier,
    )
    assert drawer._question.text().endswith("\n")
    drawer._question.setText("Summarize this review")
    qtbot.keyClick(drawer._question, Qt.Key.Key_Return)

    assert controller.questions[0][0] == "Summarize this review"
    assert not drawer._initial_panel.isVisible()
    assert not drawer._suggested_buttons[0].isVisibleTo(drawer)
    messages = drawer.conversation_messages()
    assert [message.role for message in messages] == ["user", "assistant"]
    assert messages[-1].pending
    assert drawer.findChild(QWidget, "AskFinLoadingBubble") is not None
    assert not drawer._send_button.isEnabled()
    assert drawer._last_accessibility_announcement == (
        "Ask Fin is reviewing the recorded evidence."
    )

    controller.answer()

    messages = drawer.conversation_messages()
    assert not any(message.pending for message in messages)
    assert messages[-1].citations[0].label == "Account 555035"
    assert drawer.findChild(QWidget, "AskFinLoadingBubble") is None
    assert drawer.findChild(QWidget, "AskFinAssistantBubble") is not None
    assert drawer._send_button.isEnabled()
    assert drawer._question.focusPolicy() == Qt.FocusPolicy.StrongFocus
    assert drawer._last_accessibility_announcement == (
        "Ask Fin answered with 1 recorded source."
    )
    assert drawer._conversation_scroll.verticalScrollBar().value() == (
        drawer._conversation_scroll.verticalScrollBar().maximum()
    )


def test_each_fin_answer_retains_its_own_expandable_evidence(qtbot):
    controller = _DeferredDrawerController()
    drawer = PrivateAskFinDialog(controller)
    qtbot.addWidget(drawer)
    drawer.open_for(review_id="review-1", label="Active review")

    for index in range(2):
        drawer._question.setText(f"Question {index + 1}")
        qtbot.keyClick(drawer._question, Qt.Key.Key_Return)
        controller.answer(f"Answer {index + 1}")

    messages = drawer.conversation_messages()
    answers = [
        message
        for message in messages
        if message.role == "assistant" and not message.pending
    ]
    assert len(answers) == 2
    assert all(len(message.citations) == 1 for message in answers)
    toggles = [
        button
        for button in drawer.findChildren(type(drawer._send_button))
        if button.objectName() == "AskFinEvidenceToggle"
    ]
    assert len(toggles) == 2
    qtbot.mouseClick(toggles[0], Qt.MouseButton.LeftButton)
    assert toggles[0].text() == "Hide evidence (1)"
    assert toggles[1].text() == "Show evidence (1)"


def test_fin_answer_uses_plain_structured_blocks_and_context_follow_ups(qtbot):
    controller = _DeferredDrawerController()
    drawer = PrivateAskFinDialog(controller)
    qtbot.addWidget(drawer)
    drawer.resize(520, 780)
    drawer.open_for(review_id="review-1", label="May 2026 review")

    drawer._question.setText("Summarize this review")
    qtbot.keyClick(drawer._question, Qt.Key.Key_Return)
    controller.answer_with_presentation(
        text=(
            "Here’s a summary of your May 2026 review:\n\n"
            "**Overall Status:** Incomplete\n"
            "**Budget:** $10,372,000\n"
            "Key supporting facts\n"
            "- One required GED amount is missing.\n"
            "- <b>This remains plain text.</b>"
        ),
        follow_up_questions=(
            "Show supporting evidence",
            "Why is the review incomplete?",
        ),
        resolved_context=SimpleNamespace(
            review_id="review-1",
            object_type="account",
            object_id="00-0245|555035",
            label="Account 555035",
            validation_run_id="run-1",
        ),
    )

    role_labels = {
        str(label.property("role")): [
            item.text()
            for item in drawer.findChildren(QLabel)
            if str(item.property("role")) == str(label.property("role"))
        ]
        for label in drawer.findChildren(QLabel)
    }
    assert "Overall Status:" in role_labels["chatFactLabel"]
    assert "Budget:" in role_labels["chatFactLabel"]
    assert "Key supporting facts" in role_labels["chatSectionHeading"]
    assert len(role_labels["chatBulletMarker"]) == 2
    assert "<b>This remains plain text.</b>" in role_labels["chatBody"]
    assert all(
        label.textFormat() == Qt.TextFormat.PlainText
        for label in drawer.findChildren(QLabel)
        if str(label.property("role")).startswith("chat")
    )

    follow_ups = [
        button
        for button in drawer.findChildren(type(drawer._send_button))
        if button.objectName() == "AskFinFollowUpChip"
    ]
    assert [button.text() for button in follow_ups] == [
        "Show supporting evidence",
        "Why is the review incomplete?",
    ]
    assert all(
        button.accessibleName().startswith("Ask follow-up") for button in follow_ups
    )

    qtbot.mouseClick(follow_ups[0], Qt.MouseButton.LeftButton)
    assert controller.questions[-1][0] == "Show supporting evidence"
    assert controller.questions[-1][1].review_id == "review-1"
    assert controller.questions[-1][1].object_type == "account"
    assert controller.questions[-1][1].object_id == "00-0245|555035"
    assert controller.questions[-1][1].validation_run_id == "run-1"
    assert not drawer.findChildren(type(drawer._send_button), "AskFinFollowUpChip")
    assert drawer.findChild(QWidget, "AskFinLoadingBubble") is not None

    drawer._clear_context()
    assert "review-1" not in drawer._resolved_context_by_review
    assert drawer._scope.text() == "Active review"


def test_evidence_is_grouped_with_readable_source_location_and_keyboard_actions(
    qtbot,
):
    controller = _DeferredDrawerController()
    drawer = PrivateAskFinDialog(controller)
    qtbot.addWidget(drawer)
    drawer.resize(520, 780)
    drawer.open_for(review_id="review-1", label="May 2026 review")

    drawer._question.setText("Show the supporting rows")
    qtbot.keyClick(drawer._question, Qt.Key.Key_Return)
    controller.answer_with_presentation(
        text="Account 555035 is over budget.",
        follow_up_questions=("Show contributing transactions",),
    )

    toggle = drawer.findChild(type(drawer._send_button), "AskFinEvidenceToggle")
    assert toggle is not None
    assert toggle.focusPolicy() != Qt.FocusPolicy.NoFocus
    qtbot.keyClick(toggle, Qt.Key.Key_Space)
    assert toggle.isChecked()

    group_headings = [
        label.text()
        for label in drawer.findChildren(QLabel)
        if label.property("role") == "chatEvidenceGroupHeading"
    ]
    metadata = [
        label.text()
        for label in drawer.findChildren(QLabel)
        if label.property("role") == "chatEvidenceMetadata"
    ]
    assert group_headings == ["Account evidence", "GED transaction evidence"]
    assert metadata == ["GED · General Expense Detail · Row 246"]
    evidence_details = [
        label.text()
        for label in drawer.findChildren(QLabel)
        if label.property("role") == "chatEvidenceDetailValue"
    ]
    assert evidence_details == [
        "555035",
        "TEKSYSTEMS",
        "PCARD_0526",
        "$125,000.00",
    ]
    assert any(
        label.text() == "Validation run: run-1"
        and label.accessibleName() == "Validation run run-1"
        for label in drawer.findChildren(QLabel)
    )
    source_actions = [
        button
        for button in drawer.findChildren(type(drawer._send_button))
        if button.text() == "Open source"
    ]
    assert len(source_actions) == 2
    assert all(
        button.focusPolicy() != Qt.FocusPolicy.NoFocus for button in source_actions
    )


def test_application_preferences_persist_and_environment_wins(tmp_path):
    settings = QSettings(str(tmp_path / "ask-fin.ini"), QSettings.Format.IniFormat)
    store = PrivateAskFinPreferenceStore(settings)
    digest = "sha256:" + ("a" * 64)
    store.save(
        endpoint="http://127.0.0.1:11434",
        model="llama3.2:3b",
        approved_model_digest=digest,
    )

    restarted = PrivateAskFinPreferenceStore(
        QSettings(str(tmp_path / "ask-fin.ini"), QSettings.Format.IniFormat)
    )
    saved = restarted.snapshot(environment={})
    overridden = restarted.snapshot(
        environment={
            "FINSIGHT_OLLAMA_BASE_URL": "http://localhost:11435",
            "FINSIGHT_OLLAMA_MODEL": "local-test:latest",
            "FINSIGHT_OLLAMA_MODEL_DIGEST": "sha256:" + ("b" * 64),
        }
    )

    assert saved.endpoint == "http://127.0.0.1:11434"
    assert saved.approved_model_digest == ""
    assert overridden.endpoint == "http://localhost:11435"
    assert overridden.model == "local-test:latest"
    assert overridden.approved_model_digest == "sha256:" + ("b" * 64)
    assert overridden.environment_override


def test_settings_exposes_plain_language_setup_actions_without_installing(
    qtbot,
):
    controller = _SettingsController()
    view = SettingsView(controller, appearance_manager=None)
    qtbot.addWidget(view)
    view.show()
    view._test_ask_fin_connection()

    assert view.ollama_endpoint.text() == "http://localhost:11434"
    assert view.ollama_model.currentText() == "llama3.2:3b"
    assert "Healthy" in view.ask_fin_status.text()
    assert "ready automatically" in view.ask_fin_instructions.text()
    assert "llama3.2:3b" in view.ask_fin_models.text()
    assert view.ask_fin_command.text() == "ollama pull llama3.2:3b"
    assert not view.ask_fin_command_panel.isVisible()
    assert view.test_ask_fin_button.accessibleName()
    assert view.save_ask_fin_button.accessibleName()
    visible_copy = " ".join(
        label.text() for label in view.ask_fin_setup_card.findChildren(QLabel)
    )
    assert "approve" not in visible_copy.lower()

    view._save_ask_fin_settings()
    assert controller.saved[-1]["approved_model_digest"] == ""


def test_main_window_hosts_non_modal_drawer_without_setup_workflow(
    window_factory, empty_db, qtbot
):
    window = window_factory(empty_db)
    window.show()

    window.view("review_management").askFinRequested.emit()
    drawer = window.view("ask_fin_drawer")
    qtbot.waitUntil(
        lambda: drawer.isVisibleTo(window) and drawer.width() >= 360,
        timeout=1200,
    )

    assert drawer.isVisibleTo(window)
    assert not drawer.isWindow()
    assert window._root_stack.isVisibleTo(window)
    assert drawer.parentWidget() is window._application_splitter
    assert drawer.width() >= 360
    assert drawer.width() <= 560
    assert drawer._mode.text() == "Help Mode"
    assert drawer._scope.text() == "No review selected"
    assert not any(
        button.text() == "Open Setup"
        for button in drawer.findChildren(type(drawer._send_button))
    )
