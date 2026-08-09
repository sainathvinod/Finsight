# Implements: V2 FR-126–137, NFR-092 — Workflow 2 Upload & Extraction desktop flow.
from __future__ import annotations

import uuid
from typing import Optional

from PySide6.QtCore import QEvent, QTimer, Qt, Signal
from PySide6.QtGui import (
    QAccessible,
    QAccessibleAnnouncementEvent,
    QKeySequence,
    QShortcut,
)
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from finsight.application.failure_contracts import safe_failure_message
from finsight.application.source_format import QT_FILE_FILTER
from finsight.delivery.desktop.components import (
    AdaptiveSidebar,
    NavItem,
    ReviewProgress,
)
from finsight.delivery.desktop.theme import tokens as t
from finsight.domain.source_intake import (
    EvidenceStatus,
    IntakeGateStatus,
    IntakePair,
    SourceInspection,
    SourceRole,
)
from finsight.domain.review_management import ReportingPeriod


def _label(text: str, role: str = "kvVal", *, wrap: bool = False) -> QLabel:
    value = QLabel(text)
    value.setProperty("role", role)
    value.setWordWrap(wrap)
    return value


def _evidence_text(inspection: SourceInspection, field_name: str) -> str:
    evidence = inspection.evidence_for(field_name)
    if evidence is None:
        return "Not available"
    if evidence.status is EvidenceStatus.PRESENT:
        return evidence.raw_value or evidence.normalized_value or "Present"
    if evidence.status is EvidenceStatus.WORKSPACE_ASSIGNED:
        return evidence.raw_value or "Workspace assigned / no source period"
    return evidence.status.value


def _department_text(inspection: SourceInspection) -> str:
    evidence = inspection.evidence_for("department_number")
    if evidence is None:
        return "Not available"
    if evidence.status is EvidenceStatus.PRESENT:
        return evidence.normalized_value or evidence.raw_value or "Present"
    return evidence.status.value


def _display_sha256(value: str) -> str:
    return " ".join(value[index : index + 8] for index in range(0, len(value), 8))


def _reporting_period_text(inspection: SourceInspection) -> str:
    evidence = inspection.evidence_for("reporting_period")
    if evidence is None:
        return "Not available"
    if evidence.status is EvidenceStatus.WORKSPACE_ASSIGNED:
        return "Workspace assigned / no source period"
    if evidence.status is EvidenceStatus.PRESENT and evidence.normalized_value:
        try:
            year, month = evidence.normalized_value.split("-", 1)
            return ReportingPeriod(year=int(year), month=int(month)).label
        except (TypeError, ValueError):
            pass
    return evidence.status.value


def _evidence_reference(evidence) -> str:
    if evidence is None:
        return "Source cell unavailable"
    if evidence.worksheet and evidence.cell:
        return f"{evidence.worksheet}!{evidence.cell}"
    return evidence.worksheet or evidence.cell or "Source cell unavailable"


def _raw_evidence(evidence) -> str:
    if evidence is None or evidence.raw_value is None:
        return "not provided"
    return f'"{evidence.raw_value}"'


def _issue_text(issues) -> str:
    """Return one concise business message; diagnostics remain in audit storage."""

    codes = {issue.code for issue in issues}
    if "FS-MET-002" in codes:
        return (
            "The Budget and GED reports belong to different departments. "
            "Please select matching reports."
        )
    if "FS-MET-004" in codes:
        return (
            "The GED reporting period does not match the selected review period. "
            "Select the correct file or update the review period."
        )
    if "FS-MET-001" in codes:
        return (
            "FinSight could not identify a department in both reports. "
            "Select reports that include the required department information."
        )
    if "FS-MET-003" in codes:
        return (
            "FinSight could not identify the GED reporting period. "
            "Select a GED report with the approved reporting-period header."
        )
    messages: list[str] = []
    for issue in issues:
        message = str(issue.message).strip()
        if message and message not in messages:
            messages.append(message.rstrip(".") + ".")
    if not messages:
        return ""
    remedy = next(
        (
            item.strip()
            for issue in issues
            for item in issue.permitted_remedies
            if item.strip()
        ),
        "",
    )
    return " ".join(messages + ([remedy] if remedy else []))


class _SourceCard(QFrame):
    chooseRequested = Signal(object)
    removeRequested = Signal(object)

    def __init__(self, role: SourceRole, parent=None):
        super().__init__(parent)
        self.role = role
        self.setProperty("role", "sourceCard")
        self.setAccessibleName(role.label + " upload")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(t.SP_4, t.SP_4, t.SP_4, t.SP_4)
        layout.setSpacing(t.SP_2)

        top = QHBoxLayout()
        title = _label(role.label, "cardTitle")
        top.addWidget(title)
        top.addStretch(1)
        self.status = _label("Waiting for file", "statusPill")
        self.status.setAccessibleName(role.label + " status: Waiting for file")
        top.addWidget(self.status)
        layout.addLayout(top)

        description = (
            "Select the monthly Budget workbook in the approved real-report layout."
            if role is SourceRole.BUDGET
            else "Select the General Expense Detail workbook in the approved real-report layout."
        )
        layout.addWidget(_label(description, "cardDetail", wrap=True))
        self.file_name = _label("No file selected", "cardValue", wrap=True)
        self.file_name.setAccessibleName(role.label + " file name")
        layout.addWidget(self.file_name)

        details = QGridLayout()
        details.setHorizontalSpacing(t.SP_3)
        details.setVerticalSpacing(t.SP_1)
        details.addWidget(_label("Upload status", "kvKey"), 0, 0)
        self.upload_status = _label("Waiting for file", "kvVal", wrap=True)
        self.upload_status.setAccessibleName(role.label + " upload status")
        details.addWidget(self.upload_status, 0, 1)
        details.addWidget(_label("Extraction status", "kvKey"), 1, 0)
        self.extraction_status = _label("Not started", "kvVal", wrap=True)
        self.extraction_status.setAccessibleName(role.label + " extraction status")
        details.addWidget(self.extraction_status, 1, 1)
        details.addWidget(_label("Worksheet / layout", "kvKey"), 2, 0)
        self.worksheet = _label("—", "kvVal", wrap=True)
        self.worksheet.setAccessibleName(role.label + " worksheet and layout status")
        details.addWidget(self.worksheet, 2, 1)
        details.addWidget(_label("Department name", "kvKey"), 3, 0)
        self.department_name = _label("—", "kvVal", wrap=True)
        self.department_name.setAccessibleName(role.label + " Department Name")
        details.addWidget(self.department_name, 3, 1)
        details.addWidget(_label("Department number", "kvKey"), 4, 0)
        self.department = _label("—", "kvVal", wrap=True)
        self.department.setAccessibleName(role.label + " Department Number")
        details.addWidget(self.department, 4, 1)
        details.addWidget(_label("Reporting period", "kvKey"), 5, 0)
        self.period = _label("—", "kvVal", wrap=True)
        self.period.setAccessibleName(role.label + " reporting period")
        details.addWidget(self.period, 5, 1)
        details.addWidget(_label("Records", "kvKey"), 6, 0)
        self.record_count = _label("—", "kvVal")
        self.record_count.setAccessibleName(role.label + " record count")
        details.addWidget(self.record_count, 6, 1)
        details.setColumnStretch(1, 1)
        layout.addLayout(details)

        self.file_details_button = QPushButton("File details")
        self.file_details_button.setProperty("role", "quiet")
        self.file_details_button.setCheckable(True)
        self.file_details_button.setAccessibleName(
            "Show " + role.label + " file details"
        )
        layout.addWidget(
            self.file_details_button, 0, Qt.AlignmentFlag.AlignLeft
        )
        self.file_details = QFrame()
        self.file_details.setProperty("role", "secondaryDetails")
        file_details_layout = QVBoxLayout(self.file_details)
        file_details_layout.setContentsMargins(
            t.SP_3, t.SP_2, t.SP_3, t.SP_2
        )
        file_details_layout.setSpacing(t.SP_1)
        self.file_size = _label("File size: —", "context", wrap=True)
        self.file_size.setAccessibleName(role.label + " file size")
        file_details_layout.addWidget(self.file_size)
        self.fingerprint = _label(
            "SHA-256 fingerprint will appear after safe extraction.",
            "context",
            wrap=True,
        )
        self.fingerprint.setAccessibleName(role.label + " source fingerprint")
        self.fingerprint.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByKeyboard
            | Qt.TextInteractionFlag.TextSelectableByMouse
        )
        file_details_layout.addWidget(self.fingerprint)
        self.binding = _label("Not saved to this review yet.", "context", wrap=True)
        self.binding.setAccessibleName(role.label + " binding actor and time")
        file_details_layout.addWidget(self.binding)
        self.file_details.setVisible(False)
        layout.addWidget(self.file_details)
        self.file_details_button.toggled.connect(self._toggle_file_details)
        self.issues = _label("", "error", wrap=True)
        self.issues.setAccessibleName(role.label + " extraction issues")
        self.issues.setVisible(False)
        layout.addWidget(self.issues)
        layout.addStretch(1)

        actions = QHBoxLayout()
        self.choose = QPushButton("Select .xlsx File")
        self.choose.setProperty("role", "secondary")
        self.choose.setAccessibleName("Select " + role.label + " .xlsx file")
        self.choose.setAccessibleDescription(
            "Select or replace this source. Press Delete while this control has "
            "focus to remove an unsaved selection."
        )
        self.choose.clicked.connect(lambda: self.chooseRequested.emit(role))
        actions.addWidget(self.choose)
        self.remove = QPushButton("Remove")
        self.remove.setProperty("role", "quiet")
        self.remove.setAccessibleName("Remove selected " + role.label)
        self.remove.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.remove.clicked.connect(lambda: self.removeRequested.emit(role))
        self.remove.setVisible(False)
        actions.addWidget(self.remove)
        actions.addStretch(1)
        layout.addLayout(actions)

    def show_processing(self, file_name: str) -> None:
        self.file_name.setText(file_name)
        self.status.setText("Reading safely…")
        self.status.setAccessibleName(self.role.label + " status: Reading safely")
        self.upload_status.setText("Selected")
        self.extraction_status.setText("Reading safely…")
        self.choose.setEnabled(False)
        self.issues.clear()
        self.issues.setVisible(False)

    def show_inspection(self, inspection: SourceInspection) -> None:
        self.choose.setEnabled(True)
        self.choose.setText("Replace File")
        self.remove.setVisible(True)
        self.file_name.setText(inspection.file_name)
        self.status.setText(
            "Compatible" if inspection.is_compatible else "Action required"
        )
        self.status.setAccessibleName(
            self.role.label + " status: " + self.status.text()
        )
        self.upload_status.setText("Selected")
        self.extraction_status.setText(inspection.extraction_status.value)
        self.worksheet.setText(
            f"{inspection.worksheet_name or 'Not found'} · "
            f"{'Compatible' if inspection.is_compatible else 'Action required'}"
        )
        self.department_name.setText(
            _evidence_text(inspection, "department_name")
        )
        self.department.setText(
            _department_text(inspection)
        )
        self.period.setText(
            "Workspace assigned / no source period"
            if self.role is SourceRole.BUDGET
            else _reporting_period_text(inspection)
        )
        noun = (
            "Budget records"
            if self.role is SourceRole.BUDGET
            else "GED transactions"
        )
        self.record_count.setText(f"{inspection.record_count:,} {noun}")
        self.file_size.setText(f"File size: {inspection.byte_size:,} bytes")
        self.fingerprint.setText(
            "SHA-256  "
            + (_display_sha256(inspection.sha256) if inspection.sha256 else "Unavailable")
        )
        self.fingerprint.setAccessibleDescription(
            "Full SHA-256 " + (inspection.sha256 or "Unavailable")
        )
        self.binding.setText("Extracted in this session; not saved to the review yet.")
        issue_text = _issue_text(inspection.issues)
        self.issues.setText(issue_text)
        self.issues.setAccessibleDescription(issue_text)
        self.issues.setVisible(bool(issue_text))

    def reset(self) -> None:
        self.status.setText("Waiting for file")
        self.status.setAccessibleName(
            self.role.label + " status: Waiting for file"
        )
        self.file_name.setText("No file selected")
        self.upload_status.setText("Waiting for file")
        self.extraction_status.setText("Not started")
        self.worksheet.setText("—")
        self.department_name.setText("—")
        self.department.setText("—")
        self.period.setText("—")
        self.record_count.setText("—")
        self.file_size.setText("File size: —")
        self.fingerprint.setText(
            "SHA-256 fingerprint will appear after safe extraction."
        )
        self.binding.setText("Not saved to this review yet.")
        self.file_details_button.setChecked(False)
        self.issues.clear()
        self.issues.setVisible(False)
        self.choose.setText("Select .xlsx File")
        self.choose.setEnabled(True)
        self.remove.setVisible(False)

    def show_binding(self, actor_id: str, occurred_at: str) -> None:
        self.binding.setText(
            f"Saved by {actor_id}  ·  {occurred_at}"
        )

    def set_resolved_department_name(self, name: str) -> None:
        """Show a cross-report name only after the pair gate confirms matching IDs."""

        if not name:
            return
        if self.role is SourceRole.BUDGET:
            self.department_name.setText(
                f"{name} (confirmed from matched GED report)"
            )
            self.department_name.setAccessibleDescription(
                "The Budget report supplies the department number. The name was "
                "resolved from the GED report after the department numbers matched."
            )
        else:
            self.department_name.setText(name)

    def _toggle_file_details(self, expanded: bool) -> None:
        self.file_details.setVisible(expanded)
        self.file_details_button.setText(
            "Hide file details" if expanded else "File details"
        )
        self.file_details_button.setAccessibleName(
            ("Hide " if expanded else "Show ")
            + self.role.label
            + " file details"
        )


class SourceIntakeView(QWidget):
    askFinRequested = Signal()
    """Workflow 2 UI; all workbook and persistence work is delegated to services."""

    homeRequested = Signal()
    pastReviewsRequested = Signal()
    settingsRequested = Signal()
    reviewRequested = Signal()
    financialReviewRequested = Signal(object)

    UPLOAD = 0
    METADATA = 1

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._c = controller
        self._review = None
        self._budget: Optional[SourceInspection] = None
        self._ged: Optional[SourceInspection] = None
        self._pair: Optional[IntakePair] = None
        self._request_id = None
        self._last_accessibility_announcement = ""
        self._cards_stacked = None
        self._identity_cards_stacked = None
        self._metadata_header_stacked = None
        self.setObjectName("SourceIntake")

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_sidebar())

        workspace = QWidget()
        workspace.setObjectName("Workflow1Workspace")
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_topbar())
        self._stack = QStackedWidget()
        self._upload_page = self._build_upload_page()
        self._metadata_page = self._build_metadata_page()
        self._stack.addWidget(self._upload_page)
        self._stack.addWidget(self._metadata_page)
        layout.addWidget(self._stack, 1)
        root.addWidget(workspace, 1)

        self._shortcuts = []
        self._add_shortcut(QKeySequence(Qt.Key.Key_Escape), self._back)
        # Both delete keys remove the focused source. A MacBook keyboard has no forward-delete
        # key — the key labelled "delete" reports Key_Backspace — so binding Key_Delete alone
        # left the action unreachable without Fn on the primary macOS test hardware.
        self._add_shortcut(
            QKeySequence(Qt.Key.Key_Delete), self._remove_focused_source
        )
        self._add_shortcut(
            QKeySequence(Qt.Key.Key_Backspace), self._remove_focused_source
        )
        self._set_upload_tab_order()
        self._budget_card.choose.installEventFilter(self)
        self._ged_card.choose.installEventFilter(self)

    def _add_shortcut(self, sequence: QKeySequence, action) -> None:
        shortcut = QShortcut(sequence, self)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(action)
        self._shortcuts.append(shortcut)

    def eventFilter(self, watched, event) -> bool:
        if event.type() is QEvent.Type.KeyPress:
            if watched is self._budget_card.choose and event.key() == Qt.Key.Key_Tab:
                self._ged_card.choose.setFocus()
                return True
            if (
                watched is self._ged_card.choose
                and event.key() == Qt.Key.Key_Tab
                and self._save_button.isEnabled()
            ):
                self._save_button.setFocus()
                return True
        return super().eventFilter(watched, event)

    def _build_sidebar(self) -> QWidget:
        side = AdaptiveSidebar()
        side.setObjectName("Workflow1Sidebar")
        side.setAccessibleName("FinSight primary navigation")
        layout = QVBoxLayout(side)
        layout.setContentsMargins(t.SP_3, t.SP_4, t.SP_3, t.SP_3)
        layout.setSpacing(t.SP_1)
        layout.addWidget(_label("FinSight", "appTitle"))
        layout.addWidget(_label("Financial Review Assistant", "context", wrap=True))
        layout.addSpacing(t.SP_4)
        layout.addWidget(_label("REVIEW WORKSPACE", "navGroup"))
        self._home_nav = NavItem("welcome", "Home")
        self._home_nav.activated.connect(lambda _key: self.homeRequested.emit())
        layout.addWidget(self._home_nav)
        self._past_nav = NavItem("past_reviews", "Past Reviews")
        self._past_nav.activated.connect(
            lambda _key: self.pastReviewsRequested.emit()
        )
        layout.addWidget(self._past_nav)
        self._upload_nav = NavItem("upload", "Upload && Extraction")
        self._upload_nav.setChecked(True)
        self._upload_nav.activated.connect(lambda _key: self.show_upload())
        layout.addWidget(self._upload_nav)
        layout.addSpacing(t.SP_4)
        layout.addWidget(_label("APPLICATION", "navGroup"))
        self._settings_nav = NavItem("settings", "Settings")
        self._settings_nav.activated.connect(
            lambda _key: self.settingsRequested.emit()
        )
        layout.addWidget(self._settings_nav)
        layout.addSpacing(t.SP_4)
        layout.addWidget(_label("ASSISTANCE", "navGroup"))
        self._ask_fin_nav = NavItem("ask_fin", "Ask Fin")
        self._ask_fin_nav.setEnabled(True)
        self._ask_fin_nav.setAccessibleDescription(
            "Ask Fin can explain FinSight and, after validation, recorded results."
        )
        self._ask_fin_nav.activated.connect(lambda _key: self._show_ask_fin_help())
        layout.addWidget(self._ask_fin_nav)
        layout.addStretch(1)
        return side

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("Workflow1TopBar")
        bar.setFixedHeight(t.TOPBAR_H)
        bar.setAccessibleName("FinSight application header")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(t.SP_5, 0, t.SP_5, 0)
        self._shell_crumb = _label("Upload & Extraction", "context")
        self._shell_crumb.setAccessibleName("Current location")
        layout.addWidget(self._shell_crumb)
        layout.addStretch(1)
        self._shell_context = _label("No review selected", "context")
        self._shell_context.setAccessibleName("Active review context")
        layout.addWidget(self._shell_context)
        self._ask_fin_button = QPushButton("Ask Fin")
        self._ask_fin_button.setProperty("role", "secondary")
        self._ask_fin_button.setAccessibleName("Ask Fin")
        self._ask_fin_button.setAccessibleDescription(
            "Ask Fin can explain the guided review workflow. It does not make "
            "financial validation decisions."
        )
        self._ask_fin_button.setEnabled(True)
        self._ask_fin_button.clicked.connect(self._show_ask_fin_help)
        layout.addWidget(self._ask_fin_button)
        return bar

    def _content_page(self) -> tuple[QScrollArea, QWidget, QVBoxLayout]:
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
        content = QWidget()
        content.setObjectName("Workflow1Content")
        content.setMaximumWidth(1120)
        content.setMinimumWidth(0)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(t.SP_4)
        outer.addWidget(content, 1, Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(holder)
        return scroll, content, content_layout

    @staticmethod
    def _surface_card(role: str = "surfaceCard") -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setProperty("role", role)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(t.SP_4, t.SP_4, t.SP_4, t.SP_4)
        layout.setSpacing(t.SP_2)
        return card, layout

    def _progress(self, step: int, label: str) -> QFrame:
        progress = ReviewProgress(1)
        if step == 3:
            self._upload_progress = progress
        else:
            self._metadata_progress = progress
        return progress

    def _build_upload_page(self) -> QWidget:
        page, _content, layout = self._content_page()
        layout.addWidget(self._progress(3, "Upload & Extraction"))
        header = QGridLayout()
        header.setHorizontalSpacing(t.SP_3)
        header.setVerticalSpacing(t.SP_2)
        titles_widget = QWidget()
        titles = QVBoxLayout(titles_widget)
        titles.setContentsMargins(0, 0, 0, 0)
        titles.setSpacing(t.SP_1)
        self._upload_title = _label("Upload Financial Reports", "sectionHeader")
        self._upload_title.setAccessibleName("Upload Financial Reports")
        titles.addWidget(self._upload_title)
        titles.addWidget(
            _label(
                "Add exactly one Budget Report and one GED Report. FinSight reads "
                "each source without changing it, validates the real report layout, "
                "and preserves source evidence for the review.",
                "sectionSub",
                wrap=True,
            )
        )
        header.addWidget(titles_widget, 0, 0)
        self._upload_home = QPushButton("← Back to Home")
        self._upload_home.setProperty("role", "secondary")
        self._upload_home.setAccessibleName("Back to FinSight Home")
        self._upload_home.clicked.connect(self.homeRequested.emit)
        header.addWidget(
            self._upload_home,
            0,
            1,
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )
        header.setColumnStretch(0, 1)
        layout.addLayout(header)

        notice, notice_layout = self._surface_card("noticeCard")
        notice_layout.addWidget(_label("Original files stay unchanged", "cardTitle"))
        notice_layout.addWidget(
            _label(
                "FinSight never edits the uploaded workbooks. Extracted values become a "
                "review-local working copy with source row and cell evidence.",
                "cardDetail",
                wrap=True,
            )
        )
        layout.addWidget(notice)

        self._source_grid = QGridLayout()
        self._source_grid.setHorizontalSpacing(t.SP_3)
        self._source_grid.setVerticalSpacing(t.SP_3)
        self._budget_card = _SourceCard(SourceRole.BUDGET)
        self._ged_card = _SourceCard(SourceRole.GED)
        self._budget_card.chooseRequested.connect(self._choose_source)
        self._ged_card.chooseRequested.connect(self._choose_source)
        self._budget_card.removeRequested.connect(self._remove_source)
        self._ged_card.removeRequested.connect(self._remove_source)
        self._source_grid.addWidget(self._budget_card, 0, 0)
        self._source_grid.addWidget(self._ged_card, 0, 1)
        self._source_grid.setColumnStretch(0, 1)
        self._source_grid.setColumnStretch(1, 1)
        layout.addLayout(self._source_grid)

        self._pair_message = _label(
            "Select both approved .xlsx reports to continue.",
            "context",
            wrap=True,
        )
        self._pair_message.setAccessibleName("Upload and extraction status")
        layout.addWidget(self._pair_message)
        self._upload_error = _label("", "error", wrap=True)
        self._upload_error.setAccessibleName("Upload and extraction error")
        self._upload_error.setVisible(False)
        layout.addWidget(self._upload_error)
        actions = QHBoxLayout()
        actions.addStretch(1)
        self._save_button = QPushButton("Continue to Data Review")
        self._save_button.setProperty("role", "primary")
        self._save_button.setAccessibleName("Save sources and continue to data review")
        self._save_button.setEnabled(False)
        self._save_button.clicked.connect(self._save_sources)
        actions.addWidget(self._save_button)
        layout.addLayout(actions)
        layout.addStretch(1)
        return page

    def _build_metadata_page(self) -> QWidget:
        page, _content, layout = self._content_page()
        layout.addWidget(self._progress(4, "Source Details"))
        header = QGridLayout()
        header.setHorizontalSpacing(t.SP_3)
        header.setVerticalSpacing(t.SP_2)
        titles_widget = QWidget()
        titles = QVBoxLayout(titles_widget)
        titles.setContentsMargins(0, 0, 0, 0)
        titles.setSpacing(t.SP_1)
        self._metadata_title = _label(
            "Upload & Extraction Summary", "sectionHeader"
        )
        self._metadata_title.setAccessibleName("Upload and Extraction Summary")
        titles.addWidget(self._metadata_title)
        titles.addWidget(
            _label(
                "Confirm the report-level department and reporting-period evidence "
                "before the next workflow begins.",
                "sectionSub",
                wrap=True,
            )
        )
        header.addWidget(titles_widget, 0, 0)
        self._metadata_status = _label("", "statusPill")
        self._metadata_status.setAccessibleName("Metadata gate status")
        header.addWidget(
            self._metadata_status,
            0,
            1,
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )
        header.setColumnStretch(0, 1)
        layout.addLayout(header)
        self._metadata_header = header
        self._metadata_header_titles = titles_widget

        self._identity_grid = QGridLayout()
        self._identity_grid.setHorizontalSpacing(t.SP_3)
        self._identity_grid.setVerticalSpacing(t.SP_3)
        department_card, department_layout = self._surface_card()
        department_layout.addWidget(_label("Department Identity", "cardTitle"))
        self._department_name = _label("", "cardValue", wrap=True)
        self._department_name.setAccessibleName("Department Name")
        department_layout.addWidget(self._department_name)
        self._department_number = _label("", "mono", wrap=True)
        self._department_number.setAccessibleName("Department Number")
        department_layout.addWidget(self._department_number)
        self._department_comparison = _label("", "cardDetail", wrap=True)
        self._department_comparison.setAccessibleName(
            "Department comparison result"
        )
        department_layout.addWidget(self._department_comparison)

        period_card, period_layout = self._surface_card()
        period_layout.addWidget(_label("Reporting Period", "cardTitle"))
        self._selected_period = _label("", "cardValue", wrap=True)
        self._selected_period.setAccessibleName("Selected reporting period")
        period_layout.addWidget(self._selected_period)
        self._period_comparison = _label("", "cardDetail", wrap=True)
        self._period_comparison.setAccessibleName(
            "Reporting period comparison result"
        )
        period_layout.addWidget(self._period_comparison)
        self._identity_grid.addWidget(department_card, 0, 0)
        self._identity_grid.addWidget(period_card, 0, 1)
        self._identity_cards = (department_card, period_card)
        self._identity_grid.setColumnStretch(0, 1)
        self._identity_grid.setColumnStretch(1, 1)
        layout.addLayout(self._identity_grid)

        sources, sources_layout = self._surface_card()
        sources_layout.addWidget(_label("Source Evidence", "cardTitle"))
        source_grid = QGridLayout()
        source_grid.setHorizontalSpacing(t.SP_5)
        source_grid.setVerticalSpacing(t.SP_2)
        source_grid.addWidget(_label("Budget Report", "kvKey"), 0, 0)
        self._summary_budget = _label("", "kvVal", wrap=True)
        source_grid.addWidget(self._summary_budget, 0, 1)
        source_grid.addWidget(_label("GED Report", "kvKey"), 1, 0)
        self._summary_ged = _label("", "kvVal", wrap=True)
        source_grid.addWidget(self._summary_ged, 1, 1)
        source_grid.addWidget(_label("Source preservation", "kvKey"), 2, 0)
        self._source_preservation = _label(
            "Original workbooks read only; fingerprints and source metadata retained.",
            "kvVal",
            wrap=True,
        )
        source_grid.addWidget(self._source_preservation, 2, 1)
        source_grid.setColumnStretch(1, 1)
        sources_layout.addLayout(source_grid)
        layout.addWidget(sources)

        self._metadata_issues = _label("", "error", wrap=True)
        self._metadata_issues.setAccessibleName("Metadata gate findings")
        self._metadata_issues.setVisible(False)
        layout.addWidget(self._metadata_issues)
        self._workflow3_notice = _label(
            "Extraction Review is not part of this increment. No extracted value "
            "can be edited or confirmed here.",
            "context",
            wrap=True,
        )
        self._workflow3_notice.setAccessibleName("Workflow scope notice")
        layout.addWidget(self._workflow3_notice)
        actions = QHBoxLayout()
        self._metadata_back = QPushButton("← Back to Upload")
        self._metadata_back.setProperty("role", "secondary")
        self._metadata_back.setAccessibleName("Back to Upload and Extraction")
        self._metadata_back.clicked.connect(self.show_upload)
        actions.addWidget(self._metadata_back)
        actions.addStretch(1)
        self._next_workflow = QPushButton("Continue to Extraction Review")
        self._next_workflow.setProperty("role", "primary")
        self._next_workflow.setAccessibleName(
            "Continue to Extraction Review unavailable"
        )
        self._next_workflow.setAccessibleDescription(
            "Workflow 3 has not been implemented in this increment."
        )
        self._next_workflow.setEnabled(False)
        actions.addWidget(self._next_workflow)
        layout.addLayout(actions)
        layout.addStretch(1)
        return page

    def open_review(self, review) -> None:
        self._review = review
        self._budget = None
        self._ged = None
        self._pair = None
        self._request_id = uuid.uuid4().hex
        self._budget_card.reset()
        self._ged_card.reset()
        self._shell_context.setText(
            f"Active review: {review.period.label}  ·  {review.status.value}"
        )
        self._set_upload_tab_order()
        persisted = self._c.source_intake_summary(review.review_id)
        if persisted is not None:
            self._render_persisted_summary(persisted)
            self._stack.setCurrentIndex(self.METADATA)
            self._shell_crumb.setText("Source Details")
            self._focus_after_navigation(self._metadata_back)
            return
        self.show_upload()

    def _choose_source(self, role: SourceRole) -> None:
        path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            f"Select {role.label}",
            "",
            QT_FILE_FILTER,
        )
        if path:
            self.select_source_path(role, path)

    def _set_upload_tab_order(self) -> None:
        QWidget.setTabOrder(self._budget_card.choose, self._ged_card.choose)
        QWidget.setTabOrder(self._ged_card.choose, self._save_button)

    def _remove_focused_source(self) -> None:
        focus = self.focusWidget()
        if focus is self._budget_card.choose:
            self._remove_source(SourceRole.BUDGET)
        elif focus is self._ged_card.choose:
            self._remove_source(SourceRole.GED)

    def _remove_source(self, role: SourceRole) -> None:
        if role is SourceRole.BUDGET:
            self._budget = None
            self._budget_card.reset()
        else:
            self._ged = None
            self._ged_card.reset()
        self._pair = None
        self._save_button.setEnabled(False)
        self._pair_message.setText(
            "Selection removed. Select both approved .xlsx reports to continue."
        )
        target = (
            self._budget_card.choose
            if role is SourceRole.BUDGET
            else self._ged_card.choose
        )
        self._focus_after_navigation(target)

    def select_source_path(self, role: SourceRole, path: str) -> None:
        self._request_id = uuid.uuid4().hex
        card = self._budget_card if role is SourceRole.BUDGET else self._ged_card
        card.show_processing(path.replace("\\", "/").split("/")[-1])
        self._save_button.setEnabled(False)
        self._upload_error.clear()
        self._upload_error.setVisible(False)
        self._pair_message.setText(f"Reading {role.label} safely…")

        def done(inspection: SourceInspection) -> None:
            if role is SourceRole.BUDGET:
                self._budget = inspection
            else:
                self._ged = inspection
            card.show_inspection(inspection)
            self._refresh_pair_state()
            self._announce(
                f"{role.label} extraction "
                + ("complete." if inspection.is_compatible else "requires action."),
                assertive=not inspection.is_compatible,
                target=card.status,
            )

        def failed(error: BaseException) -> None:
            card.choose.setEnabled(True)
            message = self._safe_error(error)
            self._upload_error.setText(message)
            self._upload_error.setAccessibleDescription(message)
            self._upload_error.setVisible(True)
            self._pair_message.setText(f"{role.label} could not be read.")
            self._announce(
                message, assertive=True, target=self._upload_error
            )

        self._c.inspect_source_async(path, role, done, failed)

    def _refresh_pair_state(self) -> None:
        self._set_upload_tab_order()
        if self._budget is None or self._ged is None:
            self._pair = None
            self._save_button.setEnabled(False)
            self._pair_message.setText(
                "One report is ready. Select the remaining approved .xlsx report."
            )
            return
        if not self._budget.is_compatible or not self._ged.is_compatible:
            self._pair = None
            self._save_button.setEnabled(False)
            self._pair_message.setText(
                "Correct the source compatibility issue before saving this pair."
            )
            return
        self._pair = self._c.evaluate_source_pair(
            self._budget, self._ged, self._review.period
        )
        self._save_button.setEnabled(True)
        if self._pair.gate_status is IntakeGateStatus.READY:
            confirmed_name = self._pair.department_name or ""
            self._budget_card.set_resolved_department_name(confirmed_name)
            self._ged_card.set_resolved_department_name(confirmed_name)
            self._pair_message.setText(
                "Both reports are compatible and their report metadata matches."
            )
        else:
            self._pair_message.setText(
                "Both reports are compatible. A department or reporting-period "
                "mismatch will block the next workflow."
            )

    def _save_sources(self) -> None:
        if self._pair is None or self._review is None:
            return
        self._save_button.setEnabled(False)
        self._budget_card.choose.setEnabled(False)
        self._ged_card.choose.setEnabled(False)
        self._pair_message.setText(
            "Verifying source fingerprints and saving both source bindings…"
        )

        def done(result) -> None:
            self._review = result.review
            self._budget_card.choose.setEnabled(True)
            self._ged_card.choose.setEnabled(True)
            self._budget_card.remove.setVisible(False)
            self._ged_card.remove.setVisible(False)
            actor = result.persisted_summary["committed_actor_id"]
            occurred = result.persisted_summary["committed_at"]
            self._budget_card.show_binding(actor, occurred)
            self._ged_card.show_binding(actor, occurred)
            self._save_button.setEnabled(False)
            self._render_pair(result.pair)
            self._shell_context.setText(
                f"Active review: {result.review.period.label}  ·  "
                f"{result.review.status.value}"
            )
            if result.pair.gate_status is IntakeGateStatus.BLOCKED:
                self.show_upload()
                self._upload_error.setText(_issue_text(result.pair.issues))
                self._upload_error.setVisible(True)
                self._announce(
                    "Both sources were saved, but department or reporting-period "
                    "evidence must be corrected before data review.",
                    assertive=True,
                    target=self._upload_error,
                )
                return
            self._announce(
                "Both sources were saved. Preparing the reviewed working copy.",
                target=self._pair_message,
            )
            self.financialReviewRequested.emit(result.review)

        def failed(error: BaseException) -> None:
            self._save_button.setEnabled(True)
            self._budget_card.choose.setEnabled(True)
            self._ged_card.choose.setEnabled(True)
            message = self._safe_error(error)
            self._upload_error.setText(message)
            self._upload_error.setAccessibleDescription(message)
            self._upload_error.setVisible(True)
            self._pair_message.setText(
                "Sources were not saved. The Draft review is unchanged."
            )
            self._announce(
                message, assertive=True, target=self._upload_error
            )

        self._c.commit_source_pair_async(
            self._review.review_id,
            self._pair,
            self._request_id,
            done,
            failed,
        )

    def _render_pair(self, pair: IntakePair) -> None:
        ready = pair.gate_status is IntakeGateStatus.READY
        self._metadata_status.setText(
            "Metadata matched" if ready else "Action required"
        )
        self._metadata_status.setAccessibleName(
            "Metadata gate status: " + self._metadata_status.text()
        )
        self._department_name.setText(
            pair.department_name or "Department Name unavailable"
        )
        self._department_number.setText(
            pair.department_number or "Department Number mismatch"
        )
        budget_dept = _department_text(pair.budget)
        ged_dept = _department_text(pair.ged)
        budget_department_evidence = pair.budget.evidence_for(
            "department_number"
        )
        ged_department_evidence = pair.ged.evidence_for(
            "department_number"
        )
        self._department_comparison.setText(
            f"Budget: {budget_dept} · raw "
            f"{_raw_evidence(budget_department_evidence)} · "
            f"{_evidence_reference(budget_department_evidence)}\n"
            f"GED: {ged_dept} · raw "
            f"{_raw_evidence(ged_department_evidence)} · "
            f"{_evidence_reference(ged_department_evidence)}\n"
            + ("Result: Match" if budget_dept == ged_dept else "Result: Mismatch")
        )
        self._selected_period.setText(pair.selected_period.label)
        ged_period_evidence = pair.ged.evidence_for("reporting_period")
        budget_period_evidence = pair.budget.evidence_for("reporting_period")
        ged_period = (
            pair.ged_period.label if pair.ged_period is not None else "Unavailable"
        )
        self._period_comparison.setText(
            f"Selected review: {pair.selected_period.label} · Reviewer selection\n"
            f"GED: {ged_period} · raw {_raw_evidence(ged_period_evidence)} · "
            f"{_evidence_reference(ged_period_evidence)}\n"
            "Budget: workspace assigned / no source period · "
            f"{_evidence_reference(budget_period_evidence)}\n"
            + (
                "Result: Match"
                if pair.ged_period == pair.selected_period
                else "Result: Mismatch"
            )
        )
        self._summary_budget.setText(
            f"{pair.budget.file_name}  ·  "
            f"{pair.budget.record_count:,} Budget records"
        )
        self._summary_ged.setText(
            f"{pair.ged.file_name}  ·  "
            f"{pair.ged.record_count:,} GED transactions"
        )
        issue_text = _issue_text(pair.issues)
        self._metadata_issues.setText(issue_text)
        self._metadata_issues.setAccessibleDescription(issue_text)
        self._metadata_issues.setVisible(bool(issue_text))

    def _show_ask_fin_help(self) -> None:
        self.askFinRequested.emit()

    def _render_persisted_summary(self, summary) -> None:
        pair = getattr(summary, "pair", None)
        if pair is not None:
            self._pair = pair
            self._budget = pair.budget
            self._ged = pair.ged
            self._budget_card.show_inspection(pair.budget)
            self._ged_card.show_inspection(pair.ged)
            if pair.gate_status is IntakeGateStatus.READY:
                self._budget_card.set_resolved_department_name(
                    pair.department_name or ""
                )
                self._ged_card.set_resolved_department_name(
                    pair.department_name or ""
                )
            self._budget_card.remove.setVisible(False)
            self._ged_card.remove.setVisible(False)
            self._budget_card.show_binding(
                summary.committed_actor_id, summary.committed_at
            )
            self._ged_card.show_binding(
                summary.committed_actor_id, summary.committed_at
            )
            self._render_pair(pair)
            return
        # Repository projections deliberately contain no workbook bytes or rows.
        self._metadata_status.setText(
            "Metadata matched"
            if getattr(summary, "gate_status", "") in ("READY", "Ready")
            else "Action required"
        )
        self._department_name.setText(
            getattr(summary, "department_name", None)
            or "Department Name unavailable"
        )
        self._department_number.setText(
            getattr(summary, "department_number", None)
            or "Department Number mismatch"
        )
        self._selected_period.setText(
            getattr(summary, "selected_period_label", None)
            or self._review.period.label
        )
        self._department_comparison.setText(
            getattr(summary, "department_comparison", None)
            or "Report-level evidence retained with the saved intake."
        )
        self._period_comparison.setText(
            getattr(summary, "period_comparison", None)
            or "Selected and extracted period evidence retained with the saved intake."
        )
        self._summary_budget.setText(
            getattr(summary, "budget_summary", None)
            or "Saved Budget source evidence"
        )
        self._summary_ged.setText(
            getattr(summary, "ged_summary", None)
            or "Saved GED source evidence"
        )
        issues = tuple(getattr(summary, "issues", ()) or ())
        issue_text = "\n".join(str(item) for item in issues)
        self._metadata_issues.setText(issue_text)
        self._metadata_issues.setVisible(bool(issue_text))

    def show_upload(self) -> None:
        self._stack.setCurrentIndex(self.UPLOAD)
        self._shell_crumb.setText("Upload & Extraction")
        self._focus_after_navigation(self._budget_card.choose)

    def show_metadata(self) -> None:
        self._stack.setCurrentIndex(self.METADATA)
        self._shell_crumb.setText("Source Details")
        self._focus_after_navigation(self._metadata_back)

    def _back(self) -> None:
        if self._stack.currentIndex() == self.METADATA:
            self.show_upload()
        else:
            self.homeRequested.emit()

    def _reflow_cards(self, stacked: bool) -> None:
        if self._cards_stacked == stacked:
            return
        self._source_grid.removeWidget(self._budget_card)
        self._source_grid.removeWidget(self._ged_card)
        if stacked:
            self._source_grid.addWidget(self._budget_card, 0, 0)
            self._source_grid.addWidget(self._ged_card, 1, 0)
            self._source_grid.setColumnStretch(1, 0)
        else:
            self._source_grid.addWidget(self._budget_card, 0, 0)
            self._source_grid.addWidget(self._ged_card, 0, 1)
            self._source_grid.setColumnStretch(1, 1)
        self._source_grid.setColumnStretch(0, 1)
        self._cards_stacked = stacked
        if hasattr(self, "_save_button"):
            self._set_upload_tab_order()

    def _reflow_identity_cards(self, stacked: bool) -> None:
        if stacked == self._identity_cards_stacked:
            return
        for card in self._identity_cards:
            self._identity_grid.removeWidget(card)
        if stacked:
            self._identity_grid.addWidget(self._identity_cards[0], 0, 0)
            self._identity_grid.addWidget(self._identity_cards[1], 1, 0)
            self._identity_grid.setColumnStretch(1, 0)
        else:
            self._identity_grid.addWidget(self._identity_cards[0], 0, 0)
            self._identity_grid.addWidget(self._identity_cards[1], 0, 1)
            self._identity_grid.setColumnStretch(1, 1)
        self._identity_grid.setColumnStretch(0, 1)
        self._identity_cards_stacked = stacked

    def _reflow_metadata_header(self, stacked: bool) -> None:
        if stacked == self._metadata_header_stacked:
            return
        self._metadata_header.removeWidget(self._metadata_header_titles)
        self._metadata_header.removeWidget(self._metadata_status)
        self._metadata_header.addWidget(self._metadata_header_titles, 0, 0)
        if stacked:
            self._metadata_header.addWidget(
                self._metadata_status,
                1,
                0,
                Qt.AlignmentFlag.AlignLeft,
            )
            self._metadata_header.setColumnStretch(1, 0)
        else:
            self._metadata_header.addWidget(
                self._metadata_status,
                0,
                1,
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
            )
            self._metadata_header.setColumnStretch(1, 0)
        self._metadata_header.setColumnStretch(0, 1)
        self._metadata_header_stacked = stacked

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        compact = self.width() < 1080
        self._reflow_cards(compact)
        self._reflow_identity_cards(compact)
        self._reflow_metadata_header(compact)

    def _announce(
        self,
        message: str,
        *,
        assertive: bool = False,
        target: Optional[QWidget] = None,
    ) -> None:
        normalized = " ".join(message.split())
        if not normalized:
            return
        self._last_accessibility_announcement = normalized
        event = QAccessibleAnnouncementEvent(target or self, normalized)
        event.setPoliteness(
            QAccessible.AnnouncementPoliteness.Assertive
            if assertive
            else QAccessible.AnnouncementPoliteness.Polite
        )
        QAccessible.updateAccessibility(event)

    @staticmethod
    def _focus_after_navigation(widget: QWidget) -> None:
        widget.setFocus()
        QTimer.singleShot(0, widget, widget.setFocus)

    @staticmethod
    def _safe_error(error: BaseException) -> str:
        return safe_failure_message(
            error, fallback_correlation_id="corr_ui_" + uuid.uuid4().hex
        )

    # Stable verification seams.
    def current_screen(self) -> str:
        return (
            "upload_extraction"
            if self._stack.currentIndex() == self.UPLOAD
            else "workspace_identity"
        )

    def source_cards_side_by_side(self) -> bool:
        return not bool(self._cards_stacked)

    def current_pair(self) -> Optional[IntakePair]:
        return self._pair

    def current_review(self):
        return self._review

    def last_accessibility_announcement(self) -> str:
        return self._last_accessibility_announcement
