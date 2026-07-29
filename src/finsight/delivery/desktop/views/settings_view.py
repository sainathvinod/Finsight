"""Application-wide Settings destination for FinSight desktop preferences."""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from finsight.application.ai.private_contracts import LocalAiSetupState
from finsight.delivery.desktop.components import (
    AdaptiveSidebar,
    AppearanceControl,
    NavItem,
)
from finsight.delivery.desktop.theme import tokens as t

if TYPE_CHECKING:
    from finsight.delivery.desktop.theme import AppearanceManager


def _label(text: str, role: str, *, wrap: bool = False) -> QLabel:
    label = QLabel(text)
    label.setProperty("role", role)
    label.setWordWrap(wrap)
    return label


class SettingsView(QWidget):
    """Shell destination for persistent application preferences."""

    homeRequested = Signal()
    pastReviewsRequested = Signal()
    backRequested = Signal()
    askFinRequested = Signal()

    def __init__(
        self,
        controller,
        appearance_manager: "AppearanceManager | None",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._c = controller
        self._appearance_manager = appearance_manager
        self._last_setup_status = None
        self._setup_check_started = False
        self.setObjectName("AppearanceSettings")
        self.setAccessibleName("FinSight Settings")

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_sidebar())

        workspace = QWidget()
        workspace.setObjectName("Workflow1Workspace")
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)
        workspace_layout.addWidget(self._build_topbar())
        workspace_layout.addWidget(self._build_content(), 1)
        root.addWidget(workspace, 1)

    def _build_sidebar(self) -> QWidget:
        side = AdaptiveSidebar()
        side.setObjectName("Workflow1Sidebar")
        side.setAccessibleName("FinSight primary navigation")
        layout = QVBoxLayout(side)
        layout.setContentsMargins(t.SP_3, t.SP_4, t.SP_3, t.SP_3)
        layout.setSpacing(t.SP_1)
        layout.addWidget(_label("FinSight", "appTitle"))
        layout.addWidget(
            _label("Financial Review Assistant", "context", wrap=True)
        )
        layout.addSpacing(t.SP_4)
        layout.addWidget(_label("REVIEW WORKSPACE", "navGroup"))

        home = NavItem("home", "Home")
        home.activated.connect(lambda _key: self.homeRequested.emit())
        layout.addWidget(home)
        past = NavItem("past_reviews", "Past Reviews")
        past.activated.connect(lambda _key: self.pastReviewsRequested.emit())
        layout.addWidget(past)

        layout.addSpacing(t.SP_4)
        layout.addWidget(_label("APPLICATION", "navGroup"))
        self._settings_nav = NavItem("settings", "Settings")
        self._settings_nav.setChecked(True)
        self._settings_nav.setAccessibleDescription(
            "Settings is the current application destination."
        )
        layout.addWidget(self._settings_nav)

        layout.addSpacing(t.SP_4)
        layout.addWidget(_label("ASSISTANCE", "navGroup"))
        ask = NavItem("ask_fin", "Ask Fin")
        ask.setAccessibleDescription(
            "Ask Fin can explain how appearance preferences work."
        )
        ask.activated.connect(lambda _key: self._show_ask_fin_help())
        layout.addWidget(ask)
        layout.addStretch(1)
        return side

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("Workflow1TopBar")
        bar.setFixedHeight(t.TOPBAR_H)
        bar.setAccessibleName("FinSight application header")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(t.SP_5, 0, t.SP_5, 0)
        layout.setSpacing(t.SP_3)
        crumb = _label("Settings", "context")
        crumb.setAccessibleName("Current location")
        layout.addWidget(crumb)
        layout.addStretch(1)
        context = _label("Application preferences", "context")
        context.setAccessibleName("Settings context")
        layout.addWidget(context)
        ask = QPushButton("Ask Fin")
        ask.setProperty("role", "secondary")
        ask.setAccessibleName("Ask Fin")
        ask.setAccessibleDescription(
            "Explain FinSight application preferences."
        )
        ask.clicked.connect(self._show_ask_fin_help)
        layout.addWidget(ask)
        return bar

    def _build_content(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setObjectName("Workflow1Page")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        holder = QWidget()
        holder.setObjectName("Workflow1PageCanvas")
        outer = QHBoxLayout(holder)
        outer.setContentsMargins(t.SP_6, t.SP_5, t.SP_6, t.SP_6)
        outer.setSpacing(0)

        content = QWidget()
        content.setObjectName("Workflow1Content")
        content.setMaximumWidth(1120)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(t.SP_4)

        back = QPushButton("← Back")
        back.setProperty("role", "quiet")
        back.setAccessibleName("Back to previous FinSight page")
        back.clicked.connect(self.backRequested.emit)
        self.back_button = back
        content_layout.addWidget(back, 0, Qt.AlignmentFlag.AlignLeft)
        content_layout.addWidget(_label("Settings", "sectionHeader"))
        introduction = _label(
            "Choose application-wide preferences. Changes take effect "
            "immediately and remain selected after FinSight restarts.",
            "sectionSub",
            wrap=True,
        )
        introduction.setObjectName("SettingsIntroduction")
        introduction.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum
        )
        introduction.setMinimumHeight(introduction.sizeHint().height())
        content_layout.addWidget(introduction)

        card = QFrame()
        card.setObjectName("AppearanceSettingsCard")
        card.setProperty("role", "surfaceCard")
        card.setMinimumWidth(560)
        card.setMaximumWidth(680)
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        card_layout.setSpacing(t.SP_3)
        card_layout.addWidget(_label("Appearance", "sectionHeader"))
        appearance_help = _label(
            "Use the warm Light theme, the deep-navy Dark theme, or follow "
            "the operating-system appearance with System Default.",
            "sectionSub",
            wrap=True,
        )
        appearance_help.setObjectName("AppearanceSettingsHelp")
        appearance_help.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum
        )
        appearance_help.setMinimumHeight(appearance_help.sizeHint().height())
        card_layout.addWidget(appearance_help)
        if self._appearance_manager is not None:
            self.appearance_control = AppearanceControl(
                self._appearance_manager,
                parent=card,
            )
            card_layout.addWidget(
                self.appearance_control, 0, Qt.AlignmentFlag.AlignLeft
            )
            note = _label(
                "System Default follows operating-system appearance changes. "
                "Your selection is saved automatically.",
                "context",
                wrap=True,
            )
            note.setAccessibleName(
                "Appearance preference persistence information"
            )
            note.setObjectName("AppearanceSettingsPersistence")
            note.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum
            )
            note.setMinimumHeight(note.sizeHint().height())
            card_layout.addWidget(note)
        else:
            self.appearance_control = None
            unavailable = _label(
                "Appearance controls are unavailable in this diagnostic shell.",
                "warning",
                wrap=True,
            )
            unavailable.setAccessibleName(
                "Appearance controls unavailable"
            )
            card_layout.addWidget(unavailable)
        content_layout.addWidget(
            card,
            0,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
        )
        self.ask_fin_setup_card = self._build_ask_fin_setup_card()
        content_layout.addWidget(
            self.ask_fin_setup_card,
            0,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
        )
        content_layout.addStretch(1)
        outer.addWidget(content, 1, Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(holder)
        self._content_scroll = scroll
        return scroll

    def _show_ask_fin_help(self) -> None:
        self.askFinRequested.emit()

    def focus_ask_fin_setup(self) -> None:
        """Reveal and focus the local Ask Fin setup controls."""

        self._content_scroll.ensureWidgetVisible(
            self.ask_fin_setup_card, 0, t.SP_3
        )
        self.ollama_endpoint.setFocus(Qt.FocusReason.OtherFocusReason)

    def _build_ask_fin_setup_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("AskFinSetupCard")
        card.setProperty("role", "surfaceCard")
        card.setMinimumWidth(560)
        card.setMaximumWidth(680)
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        layout.setSpacing(t.SP_3)
        layout.addWidget(_label("Ask Fin", "sectionHeader"))
        layout.addWidget(
            _label(
                "Ask Fin connects automatically to Ollama on this computer. "
                "Change the endpoint or model only when needed. FinSight never "
                "sends review data to a cloud AI service.",
                "sectionSub",
                wrap=True,
            )
        )

        endpoint_label = _label("Ollama endpoint", "fieldLabel")
        layout.addWidget(endpoint_label)
        self.ollama_endpoint = QLineEdit()
        self.ollama_endpoint.setObjectName("AskFinEndpoint")
        self.ollama_endpoint.setAccessibleName("Local Ollama endpoint")
        self.ollama_endpoint.setPlaceholderText("http://localhost:11434")
        endpoint_label.setBuddy(self.ollama_endpoint)
        layout.addWidget(self.ollama_endpoint)

        model_label = _label("Local model", "fieldLabel")
        layout.addWidget(model_label)
        self.ollama_model = QComboBox()
        self.ollama_model.setObjectName("AskFinModel")
        self.ollama_model.setEditable(True)
        self.ollama_model.setAccessibleName("Local Ollama model")
        model_label.setBuddy(self.ollama_model)
        layout.addWidget(self.ollama_model)

        self.ask_fin_status = _label(
            "Status: Checking local Ollama…", "context", wrap=True
        )
        self.ask_fin_status.setObjectName("AskFinSetupStatus")
        self.ask_fin_status.setAccessibleName("Ask Fin connection status")
        layout.addWidget(self.ask_fin_status)
        self.ask_fin_models = _label(
            "Model availability: Checking…", "context", wrap=True
        )
        self.ask_fin_models.setObjectName("AskFinModelAvailability")
        layout.addWidget(self.ask_fin_models)
        self.ask_fin_instructions = _label(
            "FinSight is checking for the selected local model.",
            "cardDetail",
            wrap=True,
        )
        self.ask_fin_instructions.setObjectName("AskFinSetupInstructions")
        layout.addWidget(self.ask_fin_instructions)

        actions = QHBoxLayout()
        actions.setSpacing(t.SP_2)
        self.save_ask_fin_button = QPushButton("Save Settings")
        self.save_ask_fin_button.setProperty("role", "primary")
        self.save_ask_fin_button.setAccessibleName(
            "Save local Ask Fin settings"
        )
        self.save_ask_fin_button.clicked.connect(
            self._save_ask_fin_settings
        )
        actions.addWidget(self.save_ask_fin_button)
        self.test_ask_fin_button = QPushButton("Test Connection")
        self.test_ask_fin_button.setProperty("role", "secondary")
        self.test_ask_fin_button.setAccessibleName(
            "Test local Ask Fin connection"
        )
        self.test_ask_fin_button.clicked.connect(
            self._test_ask_fin_connection
        )
        actions.addWidget(self.test_ask_fin_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.ask_fin_command_panel = QWidget()
        command_row = QHBoxLayout(self.ask_fin_command_panel)
        command_row.setContentsMargins(0, 0, 0, 0)
        command_row.setSpacing(t.SP_2)
        self.ask_fin_command = QLineEdit()
        self.ask_fin_command.setObjectName("AskFinSetupCommand")
        self.ask_fin_command.setAccessibleName(
            "Ollama model download command"
        )
        self.ask_fin_command.setReadOnly(True)
        command_row.addWidget(self.ask_fin_command, 1)
        copy = QPushButton("Copy Command")
        copy.setProperty("role", "quiet")
        copy.setAccessibleName("Copy Ollama model download command")
        copy.clicked.connect(self._copy_ask_fin_command)
        command_row.addWidget(copy)
        self.ask_fin_command_panel.setVisible(False)
        layout.addWidget(self.ask_fin_command_panel)

        self._load_ask_fin_configuration()
        QTimer.singleShot(0, self._startup_ask_fin_check)
        return card

    def _load_ask_fin_configuration(self) -> None:
        try:
            snapshot = self._c.private_ask_fin_configuration()
        except (AttributeError, ValueError):
            self.ollama_endpoint.setText("http://localhost:11434")
            self.ollama_model.addItem("llama3.2:3b")
            self._update_download_command()
            return
        self.ollama_endpoint.setText(snapshot.endpoint)
        self.ollama_model.addItem(snapshot.model)
        self.ollama_model.setCurrentText(snapshot.model)
        if snapshot.environment_override:
            self.ask_fin_instructions.setText(
                "Environment configuration currently takes precedence over "
                "saved application settings."
            )
        self._update_download_command()

    def _startup_ask_fin_check(self) -> None:
        if self._setup_check_started:
            return
        self._setup_check_started = True
        self._test_ask_fin_connection()

    def _set_setup_running(self, running: bool) -> None:
        self.test_ask_fin_button.setEnabled(not running)
        self.save_ask_fin_button.setEnabled(not running)
        if running:
            self.ask_fin_status.setText("Status: Checking local Ollama…")

    def _test_ask_fin_connection(self) -> None:
        self._update_download_command()
        method = getattr(
            self._c, "private_ask_fin_setup_status_async", None
        )
        if method is None:
            self._setup_failed(
                RuntimeError("Ask Fin setup is unavailable.")
            )
            return
        self._set_setup_running(True)
        method(
            self._setup_ready,
            self._setup_failed,
            endpoint=self.ollama_endpoint.text().strip(),
            model=self.ollama_model.currentText().strip(),
            approved_model_digest=None,
        )

    def _setup_ready(self, status) -> None:
        self._set_setup_running(False)
        self._last_setup_status = status
        state = getattr(status, "state", None)
        labels = {
            LocalAiSetupState.NOT_INSTALLED: "Ollama not installed",
            LocalAiSetupState.SERVICE_NOT_RUNNING: "Service not running",
            LocalAiSetupState.MODEL_NOT_DOWNLOADED: "Model not downloaded",
            LocalAiSetupState.MODEL_NOT_APPROVED: "Local model unavailable",
            LocalAiSetupState.MODEL_VERIFICATION_FAILED: (
                "Local model unavailable"
            ),
            LocalAiSetupState.CONNECTION_FAILURE: "Connection failure",
            LocalAiSetupState.TIMEOUT: "Connection timeout",
            LocalAiSetupState.HEALTHY: "Healthy",
        }
        self.ask_fin_status.setText(
            f"Status: {labels.get(state, 'Unavailable')} — "
            f"{getattr(status, 'message', '')}"
        )
        healthy = state is LocalAiSetupState.HEALTHY
        self.ask_fin_status.setProperty(
            "role", "success" if healthy else "warning"
        )
        self.ask_fin_status.style().unpolish(self.ask_fin_status)
        self.ask_fin_status.style().polish(self.ask_fin_status)
        models = tuple(getattr(status, "available_models", ()) or ())
        self.ask_fin_models.setText(
            "Model availability: "
            + (
                ", ".join(models)
                if models
                else "No local models reported"
            )
        )
        current = self.ollama_model.currentText()
        for model in models:
            if self.ollama_model.findText(model) < 0:
                self.ollama_model.addItem(model)
        self.ollama_model.setCurrentText(current)
        self.ask_fin_command_panel.setVisible(
            state is LocalAiSetupState.MODEL_NOT_DOWNLOADED
        )
        instructions = {
            LocalAiSetupState.NOT_INSTALLED: (
                "Install Ollama from its official installer, then return here "
                "and select Test Connection. FinSight will not install it."
            ),
            LocalAiSetupState.SERVICE_NOT_RUNNING: (
                "Open the Ollama application or start its local service, then "
                "select Test Connection."
            ),
            LocalAiSetupState.MODEL_NOT_DOWNLOADED: (
                "Download the selected model yourself with the command below, "
                "then refresh the status."
            ),
            LocalAiSetupState.MODEL_NOT_APPROVED: (
                "FinSight could not use the selected local model. Confirm the "
                "model selection, then test the connection again."
            ),
            LocalAiSetupState.MODEL_VERIFICATION_FAILED: (
                "FinSight could not use the selected local model. Confirm the "
                "model selection, then test the connection again."
            ),
            LocalAiSetupState.CONNECTION_FAILURE: (
                "Confirm that the endpoint is a local loopback address and "
                "that Ollama is responding, then test the connection."
            ),
            LocalAiSetupState.TIMEOUT: (
                "The local service took too long to respond. Confirm it is "
                "responsive and select Test Connection."
            ),
            LocalAiSetupState.HEALTHY: (
                "Ask Fin is ready automatically. Review prompts remain on this "
                "computer."
            ),
        }
        self.ask_fin_instructions.setText(
            instructions.get(
                state,
                "Review the local Ollama settings and try again.",
            )
        )

    def _setup_failed(self, _error: BaseException) -> None:
        self._set_setup_running(False)
        self._last_setup_status = None
        self.ask_fin_command_panel.setVisible(False)
        self.ask_fin_status.setProperty("role", "warning")
        self.ask_fin_status.setText(
            "Status: Connection failure — FinSight could not validate the "
            "local-only setup."
        )
        self.ask_fin_instructions.setText(
            "Check that the endpoint uses http://localhost (or another "
            "loopback address) with an explicit port. No cloud fallback was "
            "attempted."
        )

    def _save_ask_fin_settings(self) -> None:
        try:
            self._c.private_ask_fin_save_configuration(
                endpoint=self.ollama_endpoint.text().strip(),
                model=self.ollama_model.currentText().strip(),
                approved_model_digest="",
            )
        except (AttributeError, ValueError):
            self.ask_fin_status.setProperty("role", "warning")
            self.ask_fin_status.setText(
                "Status: Settings not saved — use a local loopback endpoint "
                "and a valid local model name."
            )
            return
        self.ask_fin_instructions.setText(
            "Ask Fin settings saved. Checking the local model…"
        )
        self._test_ask_fin_connection()

    def _update_download_command(self) -> None:
        model = self.ollama_model.currentText().strip() or "llama3.2:3b"
        self.ask_fin_command.setText(f"ollama pull {model}")

    def _copy_ask_fin_command(self) -> None:
        self._update_download_command()
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self.ask_fin_command.text())


__all__ = ["SettingsView"]
