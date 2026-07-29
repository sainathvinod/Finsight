"""Capture focused Stage 2 follow-up evidence with the real local Ollama path."""
# ruff: noqa: E402

from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QMessageBox

from capture_stage2_screenshots import (
    _CaptureSession,
    _create_validated_may_review,
    _open_results_view,
    _select_first_finding,
    _settle,
    _wait,
)
from finsight.delivery.desktop.controllers import AppController
from finsight.delivery.desktop.main_window import MainWindow
from finsight.delivery.desktop.theme import (
    AppearanceManager,
    AppearanceSettings,
)
from workflow1_demo_support import (
    build_workflow1_demo_private_ask_fin_backend,
    build_workflow1_demo_services,
)
from workflow2_demo_support import require_approved_fixtures


DEFAULT_OUTPUT = (
    REPOSITORY_ROOT
    / "initiatives"
    / "configurable-rule-engine-v2"
    / "verification"
    / "screenshots"
    / "stage2-followup"
)
MODEL_DIGEST = (
    "sha256:"
    "a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72"
)


class _NoCapture:
    def screen(self, _name: str) -> None:
        pass

    def dialog(self, _name: str, _dialog) -> None:
        pass


def main(output_directory: str | None = None) -> int:
    require_approved_fixtures()
    output = Path(output_directory) if output_directory else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)
    os.environ["FINSIGHT_AI_PROVIDER"] = "ollama"
    os.environ["FINSIGHT_OLLAMA_BASE_URL"] = "http://127.0.0.1:11434"
    os.environ["FINSIGHT_OLLAMA_MODEL"] = "llama3.2:3b"
    os.environ["FINSIGHT_OLLAMA_MODEL_DIGEST"] = MODEL_DIGEST
    os.environ["FINSIGHT_AI_STATUS_TIMEOUT"] = "4"
    os.environ["FINSIGHT_AI_REQUEST_TIMEOUT"] = "90"

    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("FinSight")
    app.setApplicationDisplayName("FinSight")

    with tempfile.TemporaryDirectory(
        prefix="finsight-stage2-followup-"
    ) as temporary:
        temporary_path = Path(temporary)
        settings = QSettings(
            str(temporary_path / "appearance.ini"),
            QSettings.Format.IniFormat,
        )
        appearance = AppearanceManager(
            app,
            settings=AppearanceSettings(settings),
        )
        services = build_workflow1_demo_services(temporary_path / "store")
        ask_fin = build_workflow1_demo_private_ask_fin_backend(
            temporary_path / "store"
        )
        controller = AppController(services, ask_fin_backend=ask_fin)
        window = MainWindow(controller, appearance_manager=appearance)
        window.resize(1440, 960)
        window.show()
        financial = _create_validated_may_review(
            app, window, _NoCapture()
        )
        capture = _CaptureSession(app, window, appearance, output)

        _open_results_view(app, financial, financial._overview_tab)
        financial._show_ask_fin()
        drawer = window.view("ask_fin_drawer")
        _wait(
            app,
            lambda: (
                drawer.isVisible()
                and drawer._provider.text() == "Local Ollama ready"
                and drawer._question.isEnabled()
            ),
            "healthy integrated Ask Fin drawer",
        )
        grounded_question = drawer._suggested_buttons[0].text()
        drawer._question.setText(grounded_question)
        drawer._send_button.click()
        _wait(
            app,
            lambda: not drawer._running,
            "a completed response from local Ollama",
            timeout=120,
        )
        if not drawer._message.text().startswith("Answer grounded in"):
            raise RuntimeError(
                "The real local Ask Fin response did not pass grounding: "
                f"{drawer._message.text()} · "
                f"{drawer._transcript.toPlainText()}"
            )
        if not drawer._citation_layout.count():
            raise RuntimeError(
                "The real local Ask Fin answer did not include a citation."
            )
        citation_count = drawer._citation_layout.count()
        capture.screen("01-ask-fin-grounded-answer")

        drawer.request_close()
        _select_first_finding(app, financial)
        financial._ask_fin_for_finding(financial._selected_finding)
        _wait(
            app,
            lambda: (
                drawer.isVisible()
                and drawer._scope.text() != "Active review"
                and bool(drawer._suggested_buttons)
                and drawer._session_is_ready
                and drawer._question.isEnabled()
            ),
            "finding-scoped Ask Fin drawer",
        )
        capture.screen("02-ask-fin-finding-scope")

        drawer.setupRequested.emit()
        settings_view = window.view("settings")
        _wait(
            app,
            lambda: (
                window.current_view_key() == "settings"
                and "Healthy" in settings_view.ask_fin_status.text()
            ),
            "healthy Ask Fin setup status",
        )
        capture.screen("03-ask-fin-setup")

        window._show_rules_repository(
            financial._review,
            financial._dataset,
            revalidation=True,
        )
        rules = window.view("rules_repository")
        _wait(
            app,
            lambda: rules._rule_table.topLevelItemCount() >= 5,
            "simplified Validation Rules page",
        )
        capture.screen("04-simplified-validation-rules")

        opened_messages: list[QMessageBox] = []
        original_exec = QMessageBox.exec

        def show_without_blocking(message: QMessageBox):
            opened_messages.append(message)
            message.show()
            _settle(app)
            return QMessageBox.StandardButton.Cancel

        QMessageBox.exec = show_without_blocking
        try:
            rules._rule_table.setCurrentItem(
                rules._rule_table.topLevelItem(0)
            )
            rules._delete_selected()
        finally:
            QMessageBox.exec = original_exec
        if not opened_messages:
            raise RuntimeError("Protected-rule warning was not shown.")
        capture.dialog(
            "05-protected-core-rule-warning", opened_messages[-1]
        )
        opened_messages[-1].close()

        answer = drawer._conversation_by_review[
            financial._review.review_id
        ][-1][1]
        print("Real local Ask Fin answer:")
        print(answer)
        print(f"Citations shown: {citation_count}")
        print(f"Captured {len(capture.paths)} focused screenshots:")
        for path in capture.paths:
            print(path)
        window.close()
        appearance.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
