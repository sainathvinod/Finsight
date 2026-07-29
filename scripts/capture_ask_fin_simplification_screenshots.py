"""Capture focused evidence for the simplified local Ask Fin experience.

The harness exercises the real approved synthetic May 2026 review and the real
loopback Ollama runtime without providing an approved-model digest. It verifies
that Ask Fin becomes usable automatically, produces a grounded answer with
source citations, and collapses an unavailable runtime to one message plus one
Retry action.
"""
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
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from capture_stage2_screenshots import (
    _CaptureSession,
    _create_validated_may_review,
    _open_results_view,
    _wait,
)
from finsight.application.ai.private_contracts import (
    LocalAiSetupState,
    LocalAiSetupStatus,
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
    / "ask-fin-simplified"
)
QUESTION = "Why is Account 555035 over budget?"


class _NoCapture:
    def screen(self, _name: str) -> None:
        pass

    def dialog(self, _name: str, _dialog) -> None:
        pass


def _visible_buttons(drawer, text: str) -> list[QPushButton]:
    return [
        button
        for button in drawer.findChildren(QPushButton)
        if button.isVisibleTo(drawer) and button.text() == text
    ]


def _visible_labels_containing(drawer, text: str) -> list[QLabel]:
    needle = text.casefold()
    return [
        label
        for label in drawer.findChildren(QLabel)
        if label.isVisibleTo(drawer) and needle in label.text().casefold()
    ]


def main(output_directory: str | None = None) -> int:
    require_approved_fixtures()
    output = Path(output_directory) if output_directory else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)

    os.environ["FINSIGHT_AI_PROVIDER"] = "ollama"
    os.environ["FINSIGHT_OLLAMA_BASE_URL"] = "http://127.0.0.1:11434"
    os.environ["FINSIGHT_OLLAMA_MODEL"] = "llama3.2:3b"
    os.environ.pop("FINSIGHT_OLLAMA_MODEL_DIGEST", None)
    os.environ["FINSIGHT_AI_STATUS_TIMEOUT"] = "4"
    os.environ["FINSIGHT_AI_REQUEST_TIMEOUT"] = "120"

    if "FINSIGHT_OLLAMA_MODEL_DIGEST" in os.environ:
        raise RuntimeError("Digest-free automatic enablement was not exercised.")

    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("FinSight")
    app.setApplicationDisplayName("FinSight")

    with tempfile.TemporaryDirectory(
        prefix="finsight-ask-fin-simplified-"
    ) as temporary:
        temporary_path = Path(temporary)
        data_directory = temporary_path / "store"
        settings = QSettings(
            str(temporary_path / "appearance.ini"),
            QSettings.Format.IniFormat,
        )
        appearance = AppearanceManager(
            app,
            settings=AppearanceSettings(settings),
        )
        services = build_workflow1_demo_services(data_directory)
        ask_fin = build_workflow1_demo_private_ask_fin_backend(data_directory)
        controller = AppController(services, ask_fin_backend=ask_fin)
        window = MainWindow(controller, appearance_manager=appearance)
        window.resize(1440, 960)
        window.show()

        financial = _create_validated_may_review(
            app,
            window,
            _NoCapture(),
        )
        capture = _CaptureSession(app, window, appearance, output)

        _open_results_view(app, financial, financial._overview_tab)
        financial._show_ask_fin()
        drawer = window.view("ask_fin_drawer")
        _wait(
            app,
            lambda: (
                drawer.isVisible()
                and drawer._provider_available is True
                and drawer._session_is_ready
                and drawer._question.isEnabled()
                and drawer._send_button.isEnabled()
                and not drawer._unavailable_card.isVisible()
            ),
            "Ask Fin to become ready without a digest approval step",
        )
        if os.environ.get("FINSIGHT_OLLAMA_MODEL_DIGEST"):
            raise RuntimeError(
                "Ask Fin became ready only after a digest environment value "
                "was introduced."
            )
        if _visible_buttons(drawer, "Open Setup"):
            raise RuntimeError("The ready drawer still exposes Open Setup.")
        capture.screen("01-ready-immediately")

        drawer._question.setText(QUESTION)
        drawer._send_button.click()
        _wait(
            app,
            lambda: not drawer._running,
            "a completed response from local Ollama",
            timeout=180,
        )
        if not drawer._message.text().startswith("Answer grounded in"):
            raise RuntimeError(
                "The real local answer did not pass grounding: "
                f"{drawer._message.text()} · "
                f"{drawer._transcript.toPlainText()}"
            )
        if drawer._citation_layout.count() < 1:
            raise RuntimeError(
                "The real local answer did not include a source citation."
            )
        transcript = drawer._transcript.toPlainText()
        if QUESTION not in transcript:
            raise RuntimeError("The requested account question is not visible.")
        capture.screen("02-grounded-answer")

        unavailable = LocalAiSetupStatus(
            state=LocalAiSetupState.SERVICE_NOT_RUNNING,
            endpoint="http://127.0.0.1:11434",
            model="llama3.2:3b",
            message="Ollama is not running.",
        )
        drawer._setup_status_ready(unavailable)
        _wait(
            app,
            lambda: (
                drawer._unavailable_card.isVisible()
                and not drawer._conversation_surface.isVisible()
            ),
            "the simplified unavailable state",
        )
        if len(_visible_buttons(drawer, "Retry")) != 1:
            raise RuntimeError(
                "Unavailable Ask Fin must show exactly one Retry action."
            )
        if _visible_buttons(drawer, "Open Setup"):
            raise RuntimeError(
                "Unavailable Ask Fin must not show an Open Setup action."
            )
        unavailable_messages = _visible_labels_containing(
            drawer, "could not connect to local Ollama"
        )
        if len(unavailable_messages) != 1:
            raise RuntimeError(
                "Unavailable Ask Fin must show one clear connection message; "
                f"found {len(unavailable_messages)}."
            )
        capture.screen("03-unavailable-single-message")

        drawer._retry_button.click()
        _wait(
            app,
            lambda: (
                drawer._provider_available is True
                and drawer._session_is_ready
                and drawer._question.isEnabled()
                and drawer._send_button.isEnabled()
                and not drawer._unavailable_card.isVisible()
            ),
            "Retry to restore the real local Ollama session",
        )

        answer = drawer._conversation_by_review[
            financial._review.review_id
        ][-1][1]
        print("Automatic-enable digest environment: absent")
        print(f"Question: {QUESTION}")
        print("Real local Ask Fin answer:")
        print(answer)
        print(f"Citations shown: {drawer._citation_layout.count()}")
        print("Unavailable state: 1 message, 1 Retry, 0 Open Setup")
        print("Retry restored the ready composer: yes")
        print(f"Captured {len(capture.paths)} screenshots:")
        for path in capture.paths:
            print(path)

        window.close()
        appearance.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main(sys.argv[1] if len(sys.argv) > 1 else None)
    )
