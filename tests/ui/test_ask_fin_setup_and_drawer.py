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

    def private_ask_fin_setup_status_async(
        self, on_result, _on_error, **_kwargs
    ):
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
        self, on_result, _on_error, *, context=None
    ):
        on_result(
            PrivateAskFinSession(
                mode=AskFinMode.FINANCIAL_REVIEW,
                greeting="I can explain this recorded review.",
                suggested_questions=("What needs attention?",),
                review_id="review-1",
                scope_label=context.label if context else "Active review",
            )
        )

    def private_ask_fin_ask_async(
        self, _question, _on_result, _on_error, *, context=None
    ):
        raise AssertionError("not used")


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

    def private_ask_fin_setup_status_async(
        self, on_result, _on_error, **configuration
    ):
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
            approved_model_digest=configuration[
                "approved_model_digest"
            ],
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
    actions = drawer._unavailable_card.findChildren(
        type(drawer._send_button)
    )
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
            answer_text=(
                "Account spend is $12,000. "
                "[account:review-1:00-0245|555035]"
            ),
            citations=(
                SimpleNamespace(label="Account 555035"),
            ),
            review_id="review-1",
        ),
        review_id="review-1",
    )

    transcript = drawer._transcript.toPlainText()
    assert "Account spend is $12,000." in transcript
    assert "[account:" not in transcript
    assert drawer._citation_layout.count() == 1


def test_application_preferences_persist_and_environment_wins(tmp_path):
    settings = QSettings(
        str(tmp_path / "ask-fin.ini"), QSettings.Format.IniFormat
    )
    store = PrivateAskFinPreferenceStore(settings)
    digest = "sha256:" + ("a" * 64)
    store.save(
        endpoint="http://127.0.0.1:11434",
        model="llama3.2:3b",
        approved_model_digest=digest,
    )

    restarted = PrivateAskFinPreferenceStore(
        QSettings(
            str(tmp_path / "ask-fin.ini"), QSettings.Format.IniFormat
        )
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
    qtbot.wait(220)
    drawer = window.view("ask_fin_drawer")

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
