"""Integrated reviewed-data, deterministic validation, and financial-results UI."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Iterable
import uuid
import re

from PySide6.QtCore import QSortFilterProxyModel, Qt, QTimer, Signal
from PySide6.QtGui import (
    QAccessible,
    QAccessibleAnnouncementEvent,
    QColor,
    QStandardItem,
    QStandardItemModel,
    QFont,
    QPalette,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QSplitter,
    QTabWidget,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finsight.application.failure_contracts import safe_failure_message
from finsight.delivery.desktop.components import (
    AdaptiveSidebar,
    DeleteReviewDialog,
    DialogVariant,
    FinancialChartCard,
    GovernedSaveDialog,
    InAppDialog,
    InAppTextPromptDialog,
    NavItem,
    ReviewProgress,
    show_in_app_message,
)
from finsight.delivery.desktop.theme import tokens as t
from finsight.domain.review_management import ReviewStatus
from finsight.domain.source_intake import RowKind


RECORD_ID_ROLE = int(Qt.ItemDataRole.UserRole) + 1
FIELD_ROLE = RECORD_ID_ROLE + 1
ORIGINAL_ROLE = FIELD_ROLE + 1
SOURCE_CELL_ROLE = ORIGINAL_ROLE + 1
SOURCE_ROLE_ROLE = SOURCE_CELL_ROLE + 1
WORKSHEET_ROLE = SOURCE_ROLE_ROLE + 1
SOURCE_ROW_ROLE = WORKSHEET_ROLE + 1
PROJECTION_ROLE = SOURCE_ROW_ROLE + 1
FINANCIAL_TONE_ROLE = PROJECTION_ROLE + 1

RULE_PURPOSES = {
    "CORE-05": (
        "Confirm that Budget actual-to-date agrees exactly with summed GED activity "
        "for each department and account."
    ),
    "CORE-01": (
        "Identify account scopes where recorded GED spend exceeds the approved BGT."
    ),
    "CORE-02": (
        "Confirm that every GED transaction uses a department and account found in Budget."
    ),
    "CORE-04": (
        "Confirm required GED values and approved Budget EAC and DELTA calculations "
        "are complete, parseable, and internally consistent."
    ),
    "CORE-03": (
        "Detect repeated GED transactions using the approved 15-field fingerprint."
    ),
}

FINDING_TITLES = {
    "CORE-01": "Account over budget",
    "CORE-02": "Unmapped GED transaction",
    "CORE-03": "Candidate duplicate GED transaction",
    "CORE-04": "Missing or invalid required GED value",
    "CORE-05": "Budget-to-GED reconciliation mismatch",
}


@dataclass(frozen=True)
class _ToneText:
    text: str
    tone: str = ""


class _FinancialToneDelegate(QStyledItemDelegate):
    """Render semantic financial tones from the active application theme."""

    def paint(self, painter, option, index) -> None:
        tone = _display(index.data(FINANCIAL_TONE_ROLE))
        app = QApplication.instance()
        high_contrast = bool(
            app.property("finsightHighContrast") if app is not None else False
        )
        if not tone or high_contrast:
            super().paint(painter, option, index)
            return
        themed = QStyleOptionViewItem(option)
        self.initStyleOption(themed, index)
        palette_name = (
            _display(app.property("finsightResolvedTheme"))
            if app is not None
            else "light"
        )
        colors = t.palette_for(palette_name or "light")
        semantic = {
            "favorable": colors.success,
            "unfavorable": colors.error,
            "incomplete": colors.warning,
        }.get(tone)
        if semantic:
            color = QColor(semantic)
            themed.palette.setColor(QPalette.ColorRole.Text, color)
            themed.palette.setColor(
                QPalette.ColorRole.HighlightedText, color
            )
            themed.font.setBold(True)
        style = (
            themed.widget.style()
            if themed.widget is not None
            else QApplication.style()
        )
        style.drawControl(
            QStyle.ControlElement.CE_ItemViewItem,
            themed,
            painter,
            themed.widget,
        )


def _label(text: str, role: str = "kvVal", *, wrap: bool = False) -> QLabel:
    value = QLabel(text)
    value.setProperty("role", role)
    value.setWordWrap(wrap)
    return value


def _display(value: Any) -> str:
    return "" if value is None else str(value)


def _human_status(value: Any) -> str:
    return {
        "PASS": "Pass",
        "FAIL": "Fail",
        "NOT_EVALUATED": "Not evaluated",
        "PROTECTED_BASELINE": "Protected baseline",
    }.get(str(value), _display(value))


def _safe_error(error: BaseException) -> str:
    return safe_failure_message(
        error, fallback_correlation_id="corr_ui_" + uuid.uuid4().hex
    )


def _review_guidance(finding: dict[str, Any]) -> str:
    """Return non-binding review guidance without mutating sealed findings."""

    explanation = dict(finding.get("explain_this") or {})
    return str(
        explanation.get("recommended_next_step")
        or (
            "Review the recorded evidence and determine the appropriate next "
            "step under the organization's approval process."
        )
    )


def _variance_text(label: Any, cents: Any) -> _ToneText:
    if cents is None:
        return _ToneText(f"Incomplete · {_display(label) or 'Unavailable'}", "incomplete")
    numeric = int(cents)
    if numeric > 0:
        return _ToneText(f"Unfavorable · {_display(label)}", "unfavorable")
    if numeric < 0:
        return _ToneText(f"Favorable · {_display(label)}", "favorable")
    return _ToneText(f"On budget · {_display(label)}")


def _content_page() -> tuple[QScrollArea, QWidget, QVBoxLayout]:
    scroll = QScrollArea()
    scroll.setObjectName("Workflow1Page")
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    holder = QWidget()
    holder.setObjectName("Workflow1PageCanvas")
    outer = QHBoxLayout(holder)
    outer.setContentsMargins(t.SP_6, t.SP_5, t.SP_6, t.SP_6)
    content = QWidget()
    content.setObjectName("Workflow1Content")
    content.setMaximumWidth(1240)
    layout = QVBoxLayout(content)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(t.SP_4)
    outer.addWidget(content, 1, Qt.AlignmentFlag.AlignTop)
    scroll.setWidget(holder)
    return scroll, content, layout


def _card(role: str = "surfaceCard") -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setProperty("role", role)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(t.SP_4, t.SP_4, t.SP_4, t.SP_4)
    layout.setSpacing(t.SP_2)
    return frame, layout


class _ContainsFilter(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._row_kind = "All rows"

    def set_row_kind(self, value: str) -> None:
        self.beginFilterChange()
        self._row_kind = value
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def filterAcceptsRow(self, source_row, source_parent) -> bool:
        model = self.sourceModel()
        if self._row_kind != "All rows":
            row_kind = str(
                model.index(source_row, 1, source_parent).data() or ""
            )
            if row_kind != self._row_kind:
                return False
        expression = self.filterRegularExpression()
        if expression.pattern() == "":
            return True
        for column in range(model.columnCount()):
            text = str(model.index(source_row, column, source_parent).data() or "")
            if expression.match(text).hasMatch():
                return True
        return False


class _FindingsFilter(_ContainsFilter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._severity = "All severities"
        self._rule = "All rules"
        self._status = "All statuses"
        self._account = "All accounts"
        self._vendor = "All vendors"
        self._department = "All departments"
        self._review_required = "All review states"

    def set_severity(self, value: str) -> None:
        self.beginFilterChange()
        self._severity = value
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def set_rule(self, value: str) -> None:
        self.beginFilterChange()
        self._rule = value
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def set_status(self, value: str) -> None:
        self.beginFilterChange()
        self._status = value
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def set_account(self, value: str) -> None:
        self.beginFilterChange()
        self._account = value
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def set_vendor(self, value: str) -> None:
        self.beginFilterChange()
        self._vendor = value
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def set_department(self, value: str) -> None:
        self.beginFilterChange()
        self._department = value
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def set_review_required(self, value: str) -> None:
        self.beginFilterChange()
        self._review_required = value
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def filterAcceptsRow(self, source_row, source_parent) -> bool:
        model = self.sourceModel()
        severity = str(model.index(source_row, 0, source_parent).data() or "")
        finding = model.index(
            source_row, 0, source_parent
        ).data(PROJECTION_ROLE) or {}
        rule = str(finding.get("rule_id", ""))
        status = str(
            finding.get("review_status")
            or finding.get("status")
            or "New"
        )
        if self._severity != "All severities" and severity != self._severity:
            return False
        if self._rule != "All rules" and rule != self._rule:
            return False
        if self._status != "All statuses" and status != self._status:
            return False
        if (
            self._account != "All accounts"
            and str(finding.get("account_number", "")) != self._account
        ):
            return False
        if (
            self._department != "All departments"
            and str(finding.get("department_number", ""))
            != self._department
        ):
            return False
        supporting = (
            finding.get("explain_this", {}).get("supporting_evidence", {})
        )
        vendors = tuple(str(item) for item in supporting.get("vendors", ()))
        if self._vendor != "All vendors" and self._vendor not in vendors:
            return False
        review_required = bool(finding.get("review_required", True))
        if (
            self._review_required == "Review required"
            and not review_required
        ):
            return False
        if (
            self._review_required == "Review complete"
            and review_required
        ):
            return False
        return super().filterAcceptsRow(source_row, source_parent)

    def lessThan(self, left, right) -> bool:
        if left.column() == 0 and right.column() == 0:
            priority = {
                "Critical": 0,
                "High": 1,
                "Medium": 2,
                "Low": 3,
            }
            left_value = priority.get(str(left.data() or ""), 9)
            right_value = priority.get(str(right.data() or ""), 9)
            if left_value != right_value:
                return left_value < right_value
        return super().lessThan(left, right)


class _GedResultsFilter(QSortFilterProxyModel):
    """Source-supported GED filters for the Stage 2 transaction workspace."""

    COLUMNS = {
        "department": 1,
        "account": 3,
        "period": 5,
        "vendor": 8,
        "amount": 11,
        "findings": 12,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._values: dict[str, Any] = {}

    def set_value(self, key: str, value: Any) -> None:
        self.beginFilterChange()
        self._values[key] = value
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    @staticmethod
    def _money(value: Any) -> float | None:
        text = str(value or "").strip().replace("$", "").replace(",", "")
        if not text:
            return None
        if text.startswith("(") and text.endswith(")"):
            text = "-" + text[1:-1]
        try:
            return float(text)
        except ValueError:
            return None

    def filterAcceptsRow(self, source_row, source_parent) -> bool:
        model = self.sourceModel()
        for key in ("vendor", "account", "department", "period"):
            expected = str(self._values.get(key, "") or "")
            if not expected or expected == "All":
                continue
            actual = str(
                model.index(
                    source_row, self.COLUMNS[key], source_parent
                ).data()
                or ""
            )
            if actual != expected:
                return False
        amount = self._money(
            model.index(
                source_row, self.COLUMNS["amount"], source_parent
            ).data()
        )
        minimum = self._money(self._values.get("minimum"))
        maximum = self._money(self._values.get("maximum"))
        if minimum is not None and (amount is None or amount < minimum):
            return False
        if maximum is not None and (amount is None or amount > maximum):
            return False
        finding_filter = str(self._values.get("finding", "All"))
        badges = str(
            model.index(
                source_row, self.COLUMNS["findings"], source_parent
            ).data()
            or ""
        )
        has_finding = badges not in {"", "No findings"}
        if finding_filter == "With finding" and not has_finding:
            return False
        if finding_filter == "No finding" and has_finding:
            return False
        return True


class FinancialReviewView(QWidget):
    homeRequested = Signal()
    pastReviewsRequested = Signal()
    settingsRequested = Signal()
    rulesRequested = Signal(object, object, bool)
    askFinRequested = Signal(str, str, str, str)

    PROCESSING = 0
    VERIFY = 1
    VALIDATING = 2
    RESULTS = 3
    COMPLETE = 4

    PROCESS_STAGES = (
        "Reading files",
        "Extracting Budget data",
        "Extracting GED data",
        "Identifying department",
        "Identifying reporting period",
        "Preparing data review",
    )
    VALIDATION_STAGES = (
        "Preparing reviewed data",
        "Running budget-overrun validation",
        "Checking Budget/GED mappings",
        "Checking duplicates",
        "Checking required fields",
        "Reconciling Budget ATD to GED",
        "Preparing results",
    )

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.setObjectName("FinancialReview")
        self._c = controller
        self._review = None
        self._dataset = None
        self._projection = None
        self._read_only = False
        self._pending: dict[tuple[str, str], Any] = {}
        self._edit_mode = False
        self._process_index = 0
        self._validation_index = 0
        self._process_finished = False
        self._validation_finished = False
        self._last_accessibility_announcement = ""

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
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_processing_page())
        self._stack.addWidget(self._build_verify_page())
        self._stack.addWidget(self._build_validation_page())
        self._stack.addWidget(self._build_results_page())
        self._stack.addWidget(self._build_complete_page())
        workspace_layout.addWidget(self._stack, 1)
        root.addWidget(workspace, 1)

        self._process_timer = QTimer(self)
        self._process_timer.setInterval(180)
        self._process_timer.timeout.connect(self._advance_process_visual)
        self._validation_timer = QTimer(self)
        self._validation_timer.setInterval(160)
        self._validation_timer.timeout.connect(self._advance_validation_visual)

    def _build_sidebar(self):
        side = AdaptiveSidebar()
        side.setObjectName("Workflow1Sidebar")
        layout = QVBoxLayout(side)
        layout.setContentsMargins(t.SP_3, t.SP_4, t.SP_3, t.SP_3)
        layout.setSpacing(t.SP_1)
        layout.addWidget(_label("FinSight", "appTitle"))
        layout.addWidget(_label("Financial Review Assistant", "context", wrap=True))
        layout.addSpacing(t.SP_4)
        layout.addWidget(_label("REVIEW WORKSPACE", "navGroup"))
        home = NavItem("home", "Home")
        home.activated.connect(lambda _key: self.homeRequested.emit())
        layout.addWidget(home)
        past = NavItem("past", "Past Reviews")
        past.activated.connect(lambda _key: self.pastReviewsRequested.emit())
        layout.addWidget(past)
        self._review_nav = NavItem("financial_review", "Financial Review")
        self._review_nav.setChecked(True)
        layout.addWidget(self._review_nav)
        layout.addSpacing(t.SP_4)
        layout.addWidget(_label("APPLICATION", "navGroup"))
        self._settings_nav = NavItem("settings", "Settings")
        self._settings_nav.activated.connect(
            lambda _key: self.settingsRequested.emit()
        )
        layout.addWidget(self._settings_nav)
        layout.addSpacing(t.SP_4)
        layout.addWidget(_label("ASSISTANCE", "navGroup"))
        ask = NavItem("ask", "Ask Fin")
        ask.activated.connect(lambda _key: self._show_ask_fin())
        layout.addWidget(ask)
        layout.addStretch(1)
        return side

    def _build_topbar(self):
        bar = QWidget()
        bar.setObjectName("Workflow1TopBar")
        bar.setFixedHeight(t.TOPBAR_H)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(t.SP_5, 0, t.SP_5, 0)
        self._crumb = _label("Financial Review", "context")
        layout.addWidget(self._crumb)
        layout.addStretch(1)
        self._context = _label("No review selected", "context")
        layout.addWidget(self._context)
        ask = QPushButton("Ask Fin")
        ask.setProperty("role", "secondary")
        ask.setAccessibleName("Ask Fin")
        ask.setAccessibleDescription(
            "Explain the guided workflow or the currently recorded validation results."
        )
        ask.clicked.connect(self._show_ask_fin)
        layout.addWidget(ask)
        return bar

    def _build_stage_card(self, names: Iterable[str]):
        card, layout = _card()
        labels = []
        for name in names:
            row = QHBoxLayout()
            row.addWidget(_label(name, "kvVal"))
            row.addStretch(1)
            status = _label("Pending", "statusPill")
            status.setAccessibleName(f"{name}: Pending")
            row.addWidget(status)
            layout.addLayout(row)
            labels.append(status)
        progress = QProgressBar()
        progress.setTextVisible(False)
        progress.setRange(0, len(labels))
        layout.addWidget(progress)
        return card, labels, progress

    def _build_processing_page(self):
        page, _content, layout = _content_page()
        self._process_progress = ReviewProgress(1)
        layout.addWidget(self._process_progress)
        layout.addWidget(_label("Preparing Your Financial Data", "sectionHeader"))
        layout.addWidget(
            _label(
                "FinSight is reading the saved source reports and creating a review-local "
                "working copy. The original files remain unchanged.",
                "sectionSub",
                wrap=True,
            )
        )
        card, self._process_labels, self._process_bar = self._build_stage_card(
            self.PROCESS_STAGES
        )
        layout.addWidget(card)
        self._process_error = _label("", "error", wrap=True)
        self._process_error.setVisible(False)
        layout.addWidget(self._process_error)
        layout.addStretch(1)
        return page

    def _build_validation_page(self):
        page, _content, layout = _content_page()
        self._validation_progress = ReviewProgress(4)
        layout.addWidget(self._validation_progress)
        layout.addWidget(_label("Running Financial Validation", "sectionHeader"))
        layout.addWidget(
            _label(
                "The five protected baseline controls are running against the exact "
                "reviewed data version you confirmed.",
                "sectionSub",
                wrap=True,
            )
        )
        card, self._validation_labels, self._validation_bar = self._build_stage_card(
            self.VALIDATION_STAGES
        )
        layout.addWidget(card)
        self._validation_error = _label("", "error", wrap=True)
        self._validation_error.setVisible(False)
        layout.addWidget(self._validation_error)
        layout.addStretch(1)
        return page

    def _reset_stages(self, labels, bar):
        for label in labels:
            label.setText("Pending")
            label.setProperty("role", "statusPill")
        bar.setValue(0)

    def _set_stage(self, labels, bar, index):
        stage_names = (
            self.PROCESS_STAGES
            if labels is self._process_labels
            else self.VALIDATION_STAGES
        )
        for position, label in enumerate(labels):
            if position < index:
                label.setText("Complete")
                label.setProperty("role", "success")
            elif position == index:
                label.setText("In progress")
                label.setProperty("role", "pillAttention")
            else:
                label.setText("Pending")
                label.setProperty("role", "statusPill")
            label.style().unpolish(label)
            label.style().polish(label)
            label.setAccessibleName(f"{stage_names[position]}: {label.text()}")
        bar.setValue(min(index, len(labels)))

    def _advance_process_visual(self):
        if self._process_index < len(self._process_labels) - 1:
            self._process_index += 1
            self._set_stage(
                self._process_labels, self._process_bar, self._process_index
            )
        elif self._process_finished:
            self._process_timer.stop()
            self._process_bar.setValue(len(self._process_labels))
            for label in self._process_labels:
                label.setText("Complete")
                label.setProperty("role", "success")
            self._show_verify()

    def _advance_validation_visual(self):
        if self._validation_index < len(self._validation_labels) - 1:
            self._validation_index += 1
            self._set_stage(
                self._validation_labels,
                self._validation_bar,
                self._validation_index,
            )
        elif self._validation_finished:
            self._validation_timer.stop()
            self._validation_bar.setValue(len(self._validation_labels))
            for label in self._validation_labels:
                label.setText("Complete")
                label.setProperty("role", "success")
            self._show_results()

    def _build_verify_page(self):
        page, _content, layout = _content_page()
        self._verify_progress = ReviewProgress(2)
        layout.addWidget(self._verify_progress)
        heading = QHBoxLayout()
        titles = QVBoxLayout()
        titles.addWidget(_label("Verify Extracted Data", "sectionHeader"))
        titles.addWidget(
            _label(
                "Review the complete extracted rows, make review-local corrections when "
                "needed, and preserve original source evidence.",
                "sectionSub",
                wrap=True,
            )
        )
        heading.addLayout(titles, 1)
        self._edit_button = QPushButton("Edit Mode")
        self._edit_button.setProperty("role", "secondary")
        self._edit_button.setAccessibleName("Enter reviewed-data edit mode")
        self._edit_button.clicked.connect(self._toggle_edit)
        heading.addWidget(self._edit_button)
        layout.addLayout(heading)

        toolbar = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search the current table")
        self._search.setAccessibleName("Search reviewed data")
        self._search.textChanged.connect(self._apply_search)
        toolbar.addWidget(self._search, 1)
        self._row_filter = QComboBox()
        self._row_filter.setAccessibleName("Filter reviewed data by row type")
        self._row_filter.addItems(
            (
                "All rows",
                RowKind.BUDGET_DETAIL.value,
                RowKind.BUDGET_GROUP_TOTAL.value,
                RowKind.BUDGET_SEPARATOR.value,
                RowKind.BUDGET_GRAND_TOTAL.value,
                RowKind.GED_TRANSACTION.value,
                RowKind.GED_ACCOUNT_TOTAL.value,
                RowKind.GED_DEPARTMENT_TOTAL.value,
                RowKind.GED_BLANK.value,
            )
        )
        self._row_filter.currentTextChanged.connect(self._apply_row_filter)
        toolbar.addWidget(self._row_filter)
        self._save_changes = QPushButton("Save Changes")
        self._save_changes.setProperty("role", "primary")
        self._save_changes.setAccessibleName("Save reviewed-data changes")
        self._save_changes.setAccessibleDescription(
            "Available after one or more review-local values have been edited."
        )
        self._save_changes.setEnabled(False)
        self._save_changes.clicked.connect(self._save_pending_changes)
        toolbar.addWidget(self._save_changes)
        self._cancel_changes = QPushButton("Cancel Changes")
        self._cancel_changes.setProperty("role", "secondary")
        self._cancel_changes.setAccessibleName("Cancel unsaved reviewed-data changes")
        self._cancel_changes.setAccessibleDescription(
            "Available after one or more review-local values have been edited."
        )
        self._cancel_changes.setEnabled(False)
        self._cancel_changes.clicked.connect(self._cancel_pending_changes)
        toolbar.addWidget(self._cancel_changes)
        self._revert_cell = QPushButton("Revert Selected Cell")
        self._revert_cell.setProperty("role", "secondary")
        self._revert_cell.setAccessibleName("Revert selected cell to original value")
        self._revert_cell.clicked.connect(self._revert_selected)
        toolbar.addWidget(self._revert_cell)
        self._history = QPushButton("Change History")
        self._history.setProperty("role", "secondary")
        self._history.setAccessibleName("Open reviewed-data change history")
        self._history.clicked.connect(self._show_history)
        toolbar.addWidget(self._history)
        layout.addLayout(toolbar)

        self._data_tabs = QTabWidget()
        self._data_tabs.setAccessibleName("Budget and GED reviewed data")
        self._budget_table = self._new_table("Budget Data")
        self._ged_table = self._new_table("GED Data")
        self._data_tabs.addTab(self._budget_table, "Budget Data")
        self._data_tabs.addTab(self._ged_table, "GED Data")
        self._data_tabs.currentChanged.connect(self._review_tab_changed)
        self._source_details = QPushButton("View Source")
        self._source_details.setObjectName("ViewSourceDetailsButton")
        self._source_details.setProperty("role", "secondary")
        self._source_details.setAccessibleName("View source details")
        self._source_details.setAccessibleDescription(
            "Select an extracted data value to view its source details."
        )
        self._source_details.setEnabled(False)
        self._source_details.clicked.connect(self._open_source_details)
        self._data_tabs.setCornerWidget(
            self._source_details, Qt.Corner.TopRightCorner
        )
        self._data_tabs.setMinimumHeight(430)
        layout.addWidget(self._data_tabs)

        self._edit_status = _label("", "context", wrap=True)
        layout.addWidget(self._edit_status)
        confirm, confirm_layout = _card()
        self._attestation = QCheckBox()
        self._attestation.stateChanged.connect(
            lambda state: self._continue_validation.setEnabled(
                bool(state) and not self._pending
            )
        )
        confirm_layout.addWidget(self._attestation)
        self._audit_warning = _label(
            "Changes are recorded in the audit history with the original value, "
            "edited value, user, and timestamp.",
            "cardDetail",
            wrap=True,
        )
        confirm_layout.addWidget(self._audit_warning)
        actions = QHBoxLayout()
        actions.addStretch(1)
        self._continue_validation = QPushButton("Continue to Review Rules")
        self._continue_validation.setProperty("role", "primary")
        self._continue_validation.setAccessibleName("Continue to Review Rules")
        self._continue_validation.setAccessibleDescription(
            "Confirm the reviewed Budget and GED data before reviewing the bound rules."
        )
        self._continue_validation.setEnabled(False)
        self._continue_validation.clicked.connect(self._open_confirmation)
        actions.addWidget(self._continue_validation)
        confirm_layout.addLayout(actions)
        layout.addWidget(confirm)
        return page

    def _new_table(self, name):
        table = QTableView()
        table.setAccessibleName(name)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        table.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setAccessibleDescription(
            "Rows are identified by Source Row from the original Excel worksheet."
        )
        return table

    def _record_model(self, records: Iterable[Any]):
        records = tuple(records)
        fields: list[str] = []
        for record in records:
            for field in record.current:
                if field not in fields:
                    fields.append(field)
        headers = [
            "Source Row",
            "Row Type",
            "Value Status",
            *[item.replace("_", " ").title() for item in fields],
        ]
        model = QStandardItemModel(0, len(headers), self)
        model.setHorizontalHeaderLabels(headers)
        model.blockSignals(True)
        for record in records:
            row_items = [
                QStandardItem(str(record.row_number)),
                QStandardItem(record.row_kind),
                QStandardItem(
                    "Edited"
                    if any(
                        record.current.get(field) != record.original.get(field)
                        for field in fields
                    )
                    else "Original"
                ),
            ]
            for field in fields:
                item = QStandardItem(_display(record.current.get(field)))
                item.setData(record.record_id, RECORD_ID_ROLE)
                item.setData(field, FIELD_ROLE)
                item.setData(_display(record.original.get(field)), ORIGINAL_ROLE)
                item.setData(record.cells.get(field, ""), SOURCE_CELL_ROLE)
                item.setData(record.source_role, SOURCE_ROLE_ROLE)
                item.setData(record.worksheet, WORKSHEET_ROLE)
                item.setData(record.row_number, SOURCE_ROW_ROLE)
                item.setToolTip(
                    f"Original value: {_display(record.original.get(field)) or '(blank)'}\n"
                    f"Current reviewed value: {_display(record.current.get(field)) or '(blank)'}\n"
                    "Use View Source for source details."
                )
                if record.current.get(field) != record.original.get(field):
                    font = QFont(item.font())
                    font.setBold(True)
                    item.setFont(font)
                    item.setData(
                        f"Edited value. Current {_display(record.current.get(field)) or 'blank'}. "
                        f"Original {_display(record.original.get(field)) or 'blank'}.",
                        Qt.ItemDataRole.AccessibleTextRole,
                    )
                row_items.append(item)
            for item in row_items:
                item.setEditable(False)
            model.appendRow(row_items)
        model.blockSignals(False)
        model.itemChanged.connect(self._stage_item_change)
        proxy = _ContainsFilter(self)
        proxy.setSourceModel(model)
        proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        return model, proxy

    def _populate_verify_tables(self):
        self._budget_model, self._budget_proxy = self._record_model(
            self._dataset.budget_records
        )
        self._ged_model, self._ged_proxy = self._record_model(
            self._dataset.ged_records
        )
        self._budget_table.setModel(self._budget_proxy)
        self._ged_table.setModel(self._ged_proxy)
        for table in (self._budget_table, self._ged_table):
            table.resizeColumnsToContents()
            table.horizontalHeader().setStretchLastSection(False)
            table.selectionModel().currentChanged.connect(
                lambda index, _previous, target=table: self._show_cell(
                    target, index
                )
            )
        self._source_details.setEnabled(False)
        self._source_details.setAccessibleDescription(
            "Select an extracted data value to view its source details."
        )
        self._set_models_editable(False)

    def _set_models_editable(self, editable: bool):
        for model in (
            getattr(self, "_budget_model", None),
            getattr(self, "_ged_model", None),
        ):
            if model is None:
                continue
            # Changing QStandardItem flags emits itemChanged even though no data
            # value changed. Suppress those presentation-only notifications so
            # entering Edit Mode cannot stage the entire workbook as corrections.
            was_blocked = model.blockSignals(True)
            try:
                for row in range(model.rowCount()):
                    for column in range(model.columnCount()):
                        model.item(row, column).setEditable(
                            editable and column >= 3
                        )
            finally:
                model.blockSignals(was_blocked)
        trigger = (
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
            if editable
            else QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._budget_table.setEditTriggers(trigger)
        self._ged_table.setEditTriggers(trigger)

    def _toggle_edit(self):
        if self._read_only:
            return
        self._edit_mode = not self._edit_mode
        self._set_models_editable(self._edit_mode)
        self._edit_button.setText("Exit Edit Mode" if self._edit_mode else "Edit Mode")
        self._edit_status.setText(
            "Double-click a value to edit the reviewed working copy."
            if self._edit_mode
            else "Edit mode is off."
        )

    def _stage_item_change(self, item):
        record_id = item.data(RECORD_ID_ROLE)
        field = item.data(FIELD_ROLE)
        if not record_id or not field:
            return
        self._pending[(record_id, field)] = item.text()
        item.setToolTip(
            f"Original value: {item.data(ORIGINAL_ROLE) or '(blank)'}\n"
            f"Current reviewed value: {item.text() or '(blank)'}\n"
            "Edited status: Unsaved change\n"
            "Use View Source for source details."
        )
        self._save_changes.setEnabled(True)
        self._cancel_changes.setEnabled(True)
        self._attestation.setChecked(False)
        self._continue_validation.setEnabled(False)
        self._edit_status.setText(
            f"{len(self._pending)} unsaved reviewed value change(s)."
        )

    def _apply_dataset_value(self, record_id, field, value, count):
        def change(records):
            output = []
            for record in records:
                if record.record_id == record_id:
                    current = dict(record.current)
                    current[field] = value
                    record = replace(record, current=current)
                output.append(record)
            return tuple(output)

        self._dataset = replace(
            self._dataset,
            budget_records=change(self._dataset.budget_records),
            ged_records=change(self._dataset.ged_records),
            correction_count=count,
        )

    def _save_pending_changes(self):
        if not self._pending:
            return
        confirmation = GovernedSaveDialog(len(self._pending), self)
        if confirmation.exec() != QDialog.DialogCode.Accepted:
            self._edit_status.setText("Changes are still unsaved.")
            return
        try:
            for (record_id, field), value in tuple(self._pending.items()):
                event = self._c.save_financial_correction(
                    self._dataset,
                    record_id=record_id,
                    field_name=field,
                    new_value=value if value != "" else None,
                )
                self._apply_dataset_value(
                    record_id,
                    field,
                    value if value != "" else None,
                    int(event["current_correction_count"]),
                )
        except Exception as exc:
            show_in_app_message(
                self,
                "Changes not saved",
                _safe_error(exc),
                variant=DialogVariant.ERROR,
            )
            return
        self._pending.clear()
        self._save_changes.setEnabled(False)
        self._cancel_changes.setEnabled(False)
        self._edit_status.setText(
            f"Saved review-local corrections: {self._dataset.correction_count}. "
            "Changes are recorded in the audit history with the original value, "
            "edited value, user, and timestamp."
        )
        self._populate_verify_tables()
        self._update_attestation()

    def _cancel_pending_changes(self):
        self._pending.clear()
        self._save_changes.setEnabled(False)
        self._cancel_changes.setEnabled(False)
        self._populate_verify_tables()
        self._edit_status.setText("Unsaved changes were discarded.")
        self._update_attestation()

    def _current_table_and_index(self):
        table = (
            self._budget_table
            if self._data_tabs.currentIndex() == 0
            else self._ged_table
        )
        return table, table.currentIndex()

    def _show_cell(self, table, index):
        current_table, _current_index = self._current_table_and_index()
        if table is not current_table:
            return
        details = self._source_details_for(table, index)
        self._source_details.setEnabled(details is not None)
        self._source_details.setAccessibleDescription(
            (
                f"View source details for {details['field_plain']}, "
                f"source row {details['source_row']}."
            )
            if details is not None
            else "Select an extracted data value to view its source details."
        )

    def _source_details_for(self, table, index):
        if not index.isValid() or table.model() is None:
            return None
        source = table.model().mapToSource(index)
        item = table.model().sourceModel().itemFromIndex(source)
        record_id = item.data(RECORD_ID_ROLE)
        field = item.data(FIELD_ROLE)
        if not record_id or not field:
            return None
        source_role = str(item.data(SOURCE_ROLE_ROLE) or "")
        worksheet = str(item.data(WORKSHEET_ROLE) or "")
        source_row = str(item.data(SOURCE_ROW_ROLE) or "")
        source_cell = str(item.data(SOURCE_CELL_ROLE) or "")
        column_match = re.match(r"([A-Za-z]+)", source_cell)
        column = column_match.group(1).upper() if column_match else "Unavailable"
        field_plain = field.replace("_", " ").title()
        original = str(item.data(ORIGINAL_ROLE) or "(blank)")
        current = item.text() or "(blank)"
        return {
            "record_id": str(record_id),
            "source_role": source_role,
            "worksheet": worksheet,
            "source_row": source_row,
            "source_cell": source_cell,
            "field_plain": field_plain,
            "field_column": f"{field_plain} (column {column})",
            "original": original,
            "current": current,
            "edited": "Edited" if current != original else "Not edited",
        }

    def _open_source_details(self):
        table, index = self._current_table_and_index()
        details = self._source_details_for(table, index)
        if details is None:
            return
        source_file = self._c.financial_source_file_name(
            self._review.review_id, details["source_role"]
        )
        dialog = InAppDialog(
            "Source Details",
            "See where the selected reviewed value came from.",
            variant=DialogVariant.INFORMATION,
            parent=self,
            object_name="SourceDetailsDialog",
            minimum_width=620,
        )
        dialog.setAccessibleName("Source Details")
        dialog.resize(620, 430)
        layout = dialog.content_layout
        detail_card, detail_layout = _card()
        grid = QGridLayout()
        rows = (
            ("Source file", source_file),
            ("Worksheet", details["worksheet"]),
            ("Source row", details["source_row"]),
            ("Field / column", details["field_column"]),
            ("Original value", details["original"]),
            ("Current reviewed value", details["current"]),
            ("Edited status", details["edited"]),
        )
        for row, (title, value) in enumerate(rows):
            key = _label(title, "kvKey")
            key.setAccessibleName(title)
            shown = _label(value, "kvVal", wrap=True)
            shown.setAccessibleName(f"{title}: {value}")
            shown.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByKeyboard
                | Qt.TextInteractionFlag.TextSelectableByMouse
            )
            grid.addWidget(key, row, 0, Qt.AlignmentFlag.AlignTop)
            grid.addWidget(shown, row, 1)
        grid.setColumnStretch(1, 1)
        detail_layout.addLayout(grid)
        layout.addWidget(detail_card)

        technical = _label(
            f"Internal record key: {details['record_id']}\n"
            f"Excel reference: {details['worksheet']}!{details['source_cell']}",
            "context",
            wrap=True,
        )
        technical.setObjectName("SourceTechnicalDetails")
        technical.setAccessibleName("Technical source details")
        technical.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByKeyboard
            | Qt.TextInteractionFlag.TextSelectableByMouse
        )
        technical.setVisible(False)
        layout.addWidget(technical)

        technical_toggle = QPushButton("View technical details")
        technical_toggle.setObjectName("SourceTechnicalDetailsToggle")
        technical_toggle.setProperty("role", "quiet")
        technical_toggle.setCheckable(True)
        technical_toggle.setAccessibleName("View technical details")
        technical_toggle.setAccessibleDescription(
            "Show the internal record key and raw Excel reference."
        )

        def toggle_technical(expanded):
            technical.setVisible(bool(expanded))
            label = (
                "Hide technical details"
                if expanded
                else "View technical details"
            )
            technical_toggle.setText(label)
            technical_toggle.setAccessibleName(label)

        technical_toggle.toggled.connect(toggle_technical)
        dialog.actions_layout.insertWidget(1, technical_toggle)
        close = dialog.add_action(
            "Close",
            role="primary",
            accessible_name="Close source details",
            accept=True,
            default=True,
        )
        close.setObjectName("CloseSourceDetailsButton")
        dialog.set_safe_focus(close)
        dialog.exec()
        self._source_details.setFocus()

    def _revert_selected(self):
        if self._read_only:
            return
        table, index = self._current_table_and_index()
        if not index.isValid():
            show_in_app_message(
                self,
                "Revert value",
                "Select a data cell first.",
            )
            return
        source = table.model().mapToSource(index)
        item = table.model().sourceModel().itemFromIndex(source)
        record_id, field = item.data(RECORD_ID_ROLE), item.data(FIELD_ROLE)
        if not record_id or not field:
            return
        original = item.data(ORIGINAL_ROLE)
        try:
            event = self._c.save_financial_correction(
                self._dataset,
                record_id=record_id,
                field_name=field,
                new_value=original if original != "" else None,
            )
            self._apply_dataset_value(
                record_id,
                field,
                original if original != "" else None,
                int(event["current_correction_count"]),
            )
        except Exception as exc:
            show_in_app_message(
                self,
                "Value not reverted",
                _safe_error(exc),
                variant=DialogVariant.ERROR,
            )
            return
        self._populate_verify_tables()
        self._edit_status.setText(
            "The selected value was reverted to the original extracted value and audited."
        )
        self._update_attestation()

    def _show_history(self):
        dialog = InAppDialog(
            "Reviewed Data Change History",
            "Review every saved change to the working financial data.",
            variant=DialogVariant.INFORMATION,
            parent=self,
            object_name="ReviewedDataChangeHistoryDialog",
            minimum_width=900,
        )
        dialog.resize(900, 420)
        layout = dialog.content_layout
        table = QTableWidget()
        table.verticalHeader().setVisible(False)
        headers = (
            "Time",
            "User",
            "Action",
            "Record",
            "Field",
            "Original",
            "Prior",
            "New",
            "Source",
        )
        history = self._c.financial_correction_history(self._review.review_id)
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(history))
        for row_number, event in enumerate(history):
            values = (
                event["occurred_at"],
                event["actor_id"],
                event["action"],
                event["record_id"],
                event["field_name"],
                _display(event["original_value"]),
                _display(event["prior_value"]),
                _display(event["new_value"]),
                f"{event['worksheet_name']}!{event['source_cell']}",
            )
            for column, value in enumerate(values):
                table.setItem(row_number, column, QTableWidgetItem(str(value)))
        table.resizeColumnsToContents()
        layout.addWidget(table)
        close = dialog.add_action(
            "Close",
            role="primary",
            accessible_name="Close change history",
            accept=True,
            default=True,
        )
        dialog.set_safe_focus(close)
        dialog.exec()

    def _apply_search(self, text=None):
        text = self._search.text() if text is None else text
        proxy = (
            getattr(self, "_budget_proxy", None)
            if self._data_tabs.currentIndex() == 0
            else getattr(self, "_ged_proxy", None)
        )
        if proxy is not None:
            proxy.setFilterFixedString(text)

    def _apply_row_filter(self, value=None):
        value = self._row_filter.currentText() if value is None else value
        proxy = (
            getattr(self, "_budget_proxy", None)
            if self._data_tabs.currentIndex() == 0
            else getattr(self, "_ged_proxy", None)
        )
        if proxy is not None:
            proxy.set_row_kind(value)

    def _review_tab_changed(self, _index):
        self._row_filter.setCurrentText("All rows")
        self._apply_search()
        self._apply_row_filter()
        self._source_details.setEnabled(False)
        self._source_details.setAccessibleDescription(
            "Select an extracted data value to view its source details."
        )

    def _update_attestation(self):
        if self._dataset is None:
            return
        text = (
            "I have reviewed the Budget and GED data and confirm it is ready "
            "for validation."
        )
        self._attestation.setText(text)
        self._attestation.setAccessibleName("Reviewed data confirmation")
        self._attestation.setChecked(False)
        self._continue_validation.setEnabled(False)

    def _open_confirmation(self):
        dialog = InAppDialog(
            "Confirm data for validation",
            "Confirm this reviewed working copy. FinSight will preserve its "
            "source evidence, then show the exact rules that will run.",
            variant=DialogVariant.CONFIRMATION,
            parent=self,
            object_name="ConfirmReviewedDataDialog",
            minimum_width=620,
        )
        dialog.resize(620, 420)
        layout = dialog.content_layout
        summary, summary_layout = _card()
        for title, value in (
            ("Budget records", f"{len(self._dataset.budget_details):,}"),
            ("GED transactions", f"{len(self._dataset.ged_transactions):,}"),
            (
                "Department",
                f"{self._dataset.department_name} · {self._dataset.department_number}",
            ),
            ("Reporting period", self._dataset.reporting_period),
            (
                "Reviewed categories",
                "Department/account, dates and fiscal periods, descriptions, financial amounts",
            ),
            ("Recorded corrections", str(self._dataset.correction_count)),
        ):
            row = QHBoxLayout()
            row.addWidget(_label(title, "kvKey"))
            row.addStretch(1)
            row.addWidget(_label(value, "kvVal", wrap=True))
            summary_layout.addLayout(row)
        layout.addWidget(summary)
        back = dialog.add_action(
            "Go back and review",
            role="secondary",
            accessible_name="Go back and review extracted data",
            reject=True,
            default=True,
        )
        dialog.add_action(
            "Continue to Review Rules",
            role="primary",
            accessible_name="Continue to Review Rules",
            accept=True,
        )
        dialog.set_safe_focus(back)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self._review = self._c.confirm_financial_data(
                    self._dataset, self._attestation.text()
                )
            except Exception as exc:
                show_in_app_message(
                    self,
                    "Data not confirmed",
                    _safe_error(exc),
                    variant=DialogVariant.ERROR,
                )
                return
            self.rulesRequested.emit(self._review, self._dataset, False)

    def _build_results_page(self):
        page, _content, layout = _content_page()
        self._results_progress = ReviewProgress(5)
        # The review stage remains available to accessibility APIs, while the
        # recorded-results workspace uses the quieter leader-oriented header
        # approved for Stage 2.
        self._results_progress.setVisible(False)
        layout.addWidget(self._results_progress)
        heading = QHBoxLayout()
        title_box = QVBoxLayout()
        self._results_eyebrow = _label("", "context")
        title_box.addWidget(self._results_eyebrow)
        title_box.addWidget(_label("Financial Review", "sectionHeader"))
        self._results_subtitle = _label("", "sectionSub", wrap=True)
        title_box.addWidget(self._results_subtitle)
        heading.addLayout(title_box, 1)
        self._ask_fin_results_button = QPushButton("Ask Fin")
        self._ask_fin_results_button.setProperty("role", "assistant")
        self._ask_fin_results_button.setAccessibleName(
            "Ask Fin about this recorded review"
        )
        self._ask_fin_results_button.clicked.connect(self._show_ask_fin)
        heading.addWidget(self._ask_fin_results_button)
        self._leadership_summary_button = QPushButton("Leadership Summary")
        self._leadership_summary_button.setProperty("role", "primary")
        self._leadership_summary_button.setAccessibleName(
            "Open the deterministic leadership summary"
        )
        self._leadership_summary_button.clicked.connect(
            lambda: self._open_results_tab(self._review_summary_tab)
        )
        heading.addWidget(self._leadership_summary_button)
        layout.addLayout(heading)

        governance_actions = QHBoxLayout()
        governance_actions.addStretch(1)
        self._complete_button = QPushButton("Complete Review")
        self._complete_button.setProperty("role", "secondary")
        self._complete_button.setAccessibleName("Complete financial review")
        self._complete_button.clicked.connect(self._complete_review)
        governance_actions.addWidget(self._complete_button)
        self._review_rules_button = QPushButton("Review Rules / Revalidate")
        self._review_rules_button.setProperty("role", "quiet")
        self._review_rules_button.setAccessibleName(
            "Review rules and create a new validation run"
        )
        self._review_rules_button.clicked.connect(
            lambda: self.rulesRequested.emit(
                self._review, self._dataset, True
            )
            if self._dataset is not None
            else None
        )
        governance_actions.addWidget(self._review_rules_button)
        self._delete_review_button = QPushButton("Delete Review")
        self._delete_review_button.setProperty("role", "destructive")
        self._delete_review_button.setAccessibleName(
            "Permanently delete this financial review"
        )
        self._delete_review_button.clicked.connect(self._delete_review)
        governance_actions.addWidget(self._delete_review_button)
        layout.addLayout(governance_actions)

        metadata, metadata_layout = _card()
        metadata.setObjectName("Stage2ReviewMetadata")
        metadata_grid = QGridLayout()
        self._results_period = _label("", "kvVal", wrap=True)
        self._results_files = _label("", "kvVal", wrap=True)
        self._results_entities = _label("", "kvVal", wrap=True)
        self._results_records = _label("", "kvVal", wrap=True)
        for column, (title, value) in enumerate(
            (
                ("Period", self._results_period),
                ("Files", self._results_files),
                ("Entities", self._results_entities),
                ("Records", self._results_records),
            )
        ):
            metadata_grid.addWidget(_label(title, "kvKey"), 0, column)
            metadata_grid.addWidget(value, 1, column)
            metadata_grid.setColumnStretch(column, 1)
        metadata_layout.addLayout(metadata_grid)
        capability_row = QHBoxLayout()
        capability_row.addWidget(_label("Capabilities", "kvKey"))
        self._results_capabilities = _label(
            "Budget · GED · Reconciliation", "kvVal", wrap=True
        )
        capability_row.addWidget(self._results_capabilities)
        capability_row.addStretch(1)
        self._results_completeness = _label("", "success")
        capability_row.addWidget(self._results_completeness)
        metadata_layout.addLayout(capability_row)
        layout.addWidget(metadata)

        self._results_tabs = QTabWidget()
        self._results_tabs.setAccessibleName("Financial Review result sections")
        self._overview_tab = QWidget()
        self._financial_analysis_tab = QWidget()
        self._ged_results_tab = QWidget()
        self._findings_tab = QWidget()
        self._review_summary_tab = QWidget()
        for widget, title in (
            (self._overview_tab, "Overview"),
            (self._financial_analysis_tab, "Financial Analysis"),
            (self._ged_results_tab, "GED Detail"),
            (self._findings_tab, "Findings"),
            (self._review_summary_tab, "Review Summary"),
        ):
            self._results_tabs.addTab(widget, title)

        analysis_layout = QVBoxLayout(self._financial_analysis_tab)
        analysis_layout.setContentsMargins(0, 0, 0, 0)
        self._analysis_tabs = QTabWidget()
        self._analysis_tabs.setAccessibleName(
            "Financial analysis sections"
        )
        self._account_analysis_tab = QWidget()
        self._vendor_analysis_tab = QWidget()
        self._department_analysis_tab = QWidget()
        self._comparison_tab = QWidget()
        self._reconciliation_tab = QWidget()
        for widget, title in (
            (self._account_analysis_tab, "Account Analysis"),
            (self._vendor_analysis_tab, "Vendor Analysis"),
            (self._department_analysis_tab, "Department Analysis"),
            (self._comparison_tab, "Budget vs Actual"),
            (self._reconciliation_tab, "Reconciliation"),
        ):
            self._analysis_tabs.addTab(widget, title)
        analysis_layout.addWidget(self._analysis_tabs)

        ged_layout = QVBoxLayout(self._ged_results_tab)
        ged_layout.setContentsMargins(0, 0, 0, 0)
        self._ged_sections = QTabWidget()
        self._ged_sections.setAccessibleName(
            "GED detail and data quality sections"
        )
        self._ged_transactions_tab = QWidget()
        self._quality_tab = QWidget()
        self._ged_sections.addTab(self._ged_transactions_tab, "Transactions")
        self._ged_sections.addTab(self._quality_tab, "Data Quality")
        ged_layout.addWidget(self._ged_sections)

        findings_layout = QVBoxLayout(self._findings_tab)
        findings_layout.setContentsMargins(0, 0, 0, 0)
        self._finding_sections = QTabWidget()
        self._finding_sections.setAccessibleName(
            "Findings and recorded rule details"
        )
        self._finding_list_tab = QWidget()
        self._rule_results_tab = QWidget()
        self._finding_sections.addTab(self._finding_list_tab, "Findings")
        self._finding_sections.addTab(
            self._rule_results_tab, "Rule Details"
        )
        findings_layout.addWidget(self._finding_sections)

        # Account Analysis is also the source-level Budget drill-down surface.
        self._budget_results_tab = self._account_analysis_tab
        self._results_tabs.tabBar().setUsesScrollButtons(True)
        self._results_tabs.tabBar().setElideMode(
            Qt.TextElideMode.ElideRight
        )
        self._results_tabs.setMinimumHeight(520)
        layout.addWidget(self._results_tabs)
        return page

    def _replace_layout(self, widget):
        old = widget.layout()
        if old is not None:
            while old.count():
                item = old.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            old.setAlignment(Qt.AlignmentFlag.AlignTop)
            return old
        new_layout = QVBoxLayout()
        new_layout.setContentsMargins(t.SP_4, t.SP_4, t.SP_4, t.SP_4)
        new_layout.setSpacing(t.SP_3)
        # QTabWidget shares the largest page size hint. Chart-heavy pages can
        # therefore make simpler pages taller than the viewport; pin each page's
        # content to the top so rule/findings evidence never drifts below the fold.
        new_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        widget.setLayout(new_layout)
        return new_layout

    def _metric_card(
        self,
        title,
        value,
        detail="",
        on_activate=None,
        *,
        tone: str = "",
    ):
        button = QPushButton(
            "\n".join(
                item for item in (str(title), str(value), str(detail)) if item
            )
        )
        button.setProperty("role", "metricButton")
        if tone:
            button.setProperty("tone", tone)
        button.setAccessibleName(
            f"{title}: {value}. {detail} Open related financial details."
        )
        button.setToolTip("Open related financial details.")
        content = QVBoxLayout(button)
        content.setContentsMargins(t.SP_3, t.SP_2, t.SP_3, t.SP_2)
        content.setSpacing(2)
        content.addWidget(_label(str(title), "metricLabel"))
        content.addWidget(_label(str(value), "metricValue", wrap=True))
        if detail:
            content.addWidget(_label(str(detail), "context", wrap=True))
        if on_activate is not None:
            button.clicked.connect(on_activate)
        return button

    def _open_results_tab(self, widget) -> None:
        if widget is self._budget_results_tab:
            self._results_tabs.setCurrentWidget(self._financial_analysis_tab)
            self._analysis_tabs.setCurrentWidget(self._account_analysis_tab)
        elif widget in {
            self._account_analysis_tab,
            self._vendor_analysis_tab,
            self._department_analysis_tab,
            self._comparison_tab,
            self._reconciliation_tab,
        }:
            self._results_tabs.setCurrentWidget(self._financial_analysis_tab)
            self._analysis_tabs.setCurrentWidget(widget)
        elif widget is self._quality_tab:
            self._results_tabs.setCurrentWidget(self._ged_results_tab)
            self._ged_sections.setCurrentWidget(self._quality_tab)
        elif widget is self._ged_transactions_tab:
            self._results_tabs.setCurrentWidget(self._ged_results_tab)
            self._ged_sections.setCurrentWidget(self._ged_transactions_tab)
        elif widget is self._rule_results_tab:
            self._results_tabs.setCurrentWidget(self._findings_tab)
            self._finding_sections.setCurrentWidget(self._rule_results_tab)
        elif widget is self._finding_list_tab:
            self._results_tabs.setCurrentWidget(self._findings_tab)
            self._finding_sections.setCurrentWidget(self._finding_list_tab)
        else:
            self._results_tabs.setCurrentWidget(widget)

    def _open_findings_filter(
        self, *, severity: str | None = None, rule_id: str | None = None
    ) -> None:
        self._open_results_tab(self._findings_tab)
        self._finding_sections.setCurrentWidget(self._finding_list_tab)
        if severity and hasattr(self, "_findings_severity"):
            self._findings_severity.setCurrentText(severity)
        if rule_id and hasattr(self, "_findings_rule"):
            self._findings_rule.setCurrentText(rule_id)

    def _open_finding_by_id(self, finding_id: str) -> None:
        self._open_results_tab(self._finding_list_tab)
        if not hasattr(self, "_findings_proxy"):
            return
        for row in range(self._findings_proxy.rowCount()):
            source = self._findings_proxy.mapToSource(
                self._findings_proxy.index(row, 0)
            )
            finding = self._findings_model.item(
                source.row(), 0
            ).data(PROJECTION_ROLE)
            if finding and str(finding.get("finding_id")) == finding_id:
                self._findings_result_table.selectRow(row)
                self._set_finding_explanation_visible(True)
                return

    def _open_rule_from_chart(self, rule_id: str) -> None:
        self._open_results_tab(self._rule_results_tab)
        model = getattr(self, "_rule_summary_model", None)
        table = getattr(self, "_rule_summary_table", None)
        if model is None or table is None:
            return
        for row in range(model.rowCount()):
            execution = model.item(row, 0).data(PROJECTION_ROLE)
            if execution and execution.get("rule_id") == rule_id:
                table.selectRow(row)
                table.setFocus()
                return

    def _focus_ged_value(self, header: str, value: str) -> None:
        self._open_results_tab(self._ged_results_tab)
        table = getattr(self, "_ged_results_table", None)
        if table is None:
            return
        model = table.model()
        column = next(
            (
                index
                for index in range(model.columnCount())
                if model.headerData(index, Qt.Orientation.Horizontal) == header
            ),
            None,
        )
        if column is None:
            return
        for row in range(model.rowCount()):
            if _display(model.index(row, column).data()) == value:
                table.setCurrentIndex(model.index(row, column))
                table.scrollTo(
                    model.index(row, column),
                    QAbstractItemView.ScrollHint.PositionAtCenter,
                )
                table.setFocus()
                return

    def _quality_metric_button(
        self, title: str, value: Any, detail: str, rule_id: str | None = None
    ) -> QPushButton:
        button = QPushButton(f"{value}\n{title}\n{detail}")
        button.setProperty("role", "metricButton")
        button.setAccessibleName(f"{title}: {value}. {detail}")
        button.setToolTip("Open the affected records.")

        def open_records():
            if rule_id:
                self._open_findings_filter(rule_id=rule_id)
            else:
                self._open_results_tab(self._ged_transactions_tab)

        button.clicked.connect(open_records)
        return button

    @staticmethod
    def _chart_from_projection(
        title: str,
        description: str,
        chart_data: Any,
        *,
        value_axis_title: str = "",
        view: str = "default",
        on_activate=None,
    ) -> QWidget:
        """Render engine-projected values without calculating financial truth."""

        chart_data = FinancialReviewView._normalize_chart_projection(
            chart_data, view=view
        )
        if not chart_data or not chart_data.get("categories"):
            card, layout = _card()
            layout.addWidget(_label(title, "cardTitle"))
            layout.addWidget(
                _label(
                    "This visualization is unavailable for the recorded run. "
                    "Use the exact result table below.",
                    "cardDetail",
                    wrap=True,
                )
            )
            return card
        card = FinancialChartCard(
            title,
            description,
            categories=tuple(chart_data["categories"]),
            category_keys=tuple(
                chart_data.get("category_keys", chart_data["categories"])
            ),
            series={
                str(name): tuple(values)
                for name, values in chart_data.get("series", {}).items()
            },
            display_values={
                str(name): tuple(values)
                for name, values in chart_data.get("display", {}).items()
            }
            or None,
            value_axis_title=value_axis_title,
        )
        if on_activate is not None:
            card.categoryActivated.connect(on_activate)
        return card

    @staticmethod
    def _normalize_chart_projection(
        value: Any, *, view: str = "default"
    ) -> dict[str, Any] | None:
        """Adapt sealed chart projections to the reusable chart component.

        The validation engine supplies all aggregates, counts, integer cents,
        and display labels. This method only selects plotted fields and converts
        integer cents to the display axis unit.
        """

        if not value:
            return None
        if isinstance(value, dict) and value.get("categories"):
            return value

        def money(cents: Any) -> float:
            return 0.0 if cents is None else float(cents) / 100.0

        if isinstance(value, dict):
            if {"bgt_cents", "atd_cents", "ged_cents"} <= set(value):
                return {
                    "categories": ["BGT", "Budget ATD", "GED spend"],
                    "category_keys": [
                        "financial-summary",
                        "financial-summary",
                        "financial-summary",
                    ],
                    "series": {
                        "Amount": [
                            money(value.get("bgt_cents")),
                            money(value.get("atd_cents")),
                            money(value.get("ged_cents")),
                        ]
                    },
                    "display": {
                        "Amount": [
                            value.get("bgt_label", "Not available"),
                            value.get("atd_label", "Not available"),
                            value.get("ged_label", "Not available"),
                        ]
                    },
                }
            if {"over_budget", "within_budget", "not_evaluated"} <= set(value):
                return {
                    "categories": [
                        "Over budget",
                        "Within budget",
                        "Not evaluated",
                    ],
                    "series": {
                        "Accounts": [
                            value["over_budget"],
                            value["within_budget"],
                            value["not_evaluated"],
                        ]
                    },
                    "category_keys": [
                        "over-budget",
                        "within-budget",
                        "not-evaluated",
                    ],
                }
            if {"reconciled", "different", "not_evaluated"} <= set(value):
                return {
                    "categories": [
                        "Reconciled",
                        "Different",
                        "Not evaluated",
                    ],
                    "series": {
                        "Accounts": [
                            value["reconciled"],
                            value["different"],
                            value["not_evaluated"],
                        ]
                    },
                    "category_keys": [
                        "reconciled",
                        "different",
                        "not-evaluated",
                    ],
                }
            return None

        if not isinstance(value, (list, tuple)) or not value:
            return None
        rows = [item for item in value if isinstance(item, dict)]
        if not rows:
            return None
        sample = rows[0]
        if "severity" in sample:
            return {
                "categories": [item["severity"] for item in rows],
                "category_keys": [item["severity"] for item in rows],
                "series": {"Findings": [item["count"] for item in rows]},
            }
        if "rule_id" in sample and "status" in sample:
            return {
                "categories": [item["rule_id"] for item in rows],
                "category_keys": [item["rule_id"] for item in rows],
                "series": {
                    "Passed": [item["passed"] for item in rows],
                    "Failed": [item["failed"] for item in rows],
                    "Not evaluated": [
                        item["not_evaluated"] for item in rows
                    ],
                },
            }
        if "bgt_cents" in sample:
            if view == "ranked":
                rows = rows[:12]
            else:
                rows = sorted(
                    rows,
                    key=lambda item: abs(
                        item.get("ged_cents")
                        if item.get("ged_cents") is not None
                        else (item.get("bgt_cents") or 0)
                    ),
                    reverse=True,
                )[:12]
            if "ged_cents" in sample:
                if view == "bgt_ged":
                    fields = (
                        ("BGT", "bgt_cents", "bgt_label"),
                        ("GED spend", "ged_cents", "ged_label"),
                    )
                elif view == "atd_ged":
                    fields = (
                        ("Budget ATD", "atd_cents", "atd_label"),
                        ("GED spend", "ged_cents", "ged_label"),
                    )
                elif view == "ranked":
                    fields = (
                        (
                            "Remaining budget",
                            "remaining_cents",
                            "remaining_label",
                        ),
                        ("Overrun", "overrun_cents", "overrun_label"),
                    )
                else:
                    fields = (
                        ("BGT", "bgt_cents", "bgt_label"),
                        ("Budget ATD", "atd_cents", "atd_label"),
                        ("GED spend", "ged_cents", "ged_label"),
                        (
                            "Remaining budget",
                            "remaining_cents",
                            "remaining_label",
                        ),
                        ("Overrun", "overrun_cents", "overrun_label"),
                        (
                            "Reconciliation difference",
                            "reconciliation_difference_cents",
                            "reconciliation_difference_label",
                        ),
                    )
            else:
                fields = (
                    ("BGT", "bgt_cents", "bgt_label"),
                    ("ATD", "atd_cents", "atd_label"),
                    ("ETC", "etc_cents", "etc_label"),
                    ("EAC", "eac_cents", "eac_label"),
                    ("DELTA", "delta_cents", "delta_label"),
                    ("Remaining", "remaining_cents", "remaining_label"),
                    ("Overrun", "overrun_cents", "overrun_label"),
                )
            return {
                "categories": [item["account_number"] for item in rows],
                "category_keys": [
                    item.get("scope_key", item["account_number"])
                    for item in rows
                ],
                "series": {
                    label: [money(item.get(field)) for item in rows]
                    for label, field, _display_field in fields
                },
                "display": {
                    label: [
                        item.get(display_field, "Not available")
                        for item in rows
                    ]
                    for label, _field, display_field in fields
                },
            }
        if "amount_cents" in sample:
            sort_field = (
                "transaction_count"
                if view == "count"
                else "amount_cents"
            )
            rows = sorted(
                rows,
                key=lambda item: item.get(sort_field) or 0,
                reverse=True,
            )[:12]
            categories = [
                (
                    f"Row {item.get('source_row')}"
                    if view == "largest" and item.get("source_row")
                    else str(
                        item.get("account_number")
                        or item.get("fiscal_period")
                        or item.get("vendor_name")
                        or item.get("polarity")
                        or (
                            f"Row {item.get('source_row')}"
                            if item.get("source_row")
                            else ""
                        )
                        or "Unknown"
                    )
                )
                for item in rows
            ]
            category_keys = [
                str(
                    item.get("scope_key")
                    or item.get("record_id")
                    or item.get("account_number")
                    or item.get("fiscal_period")
                    or item.get("vendor_name")
                    or item.get("polarity")
                    or "Unknown"
                )
                for item in rows
            ]
            if view == "count":
                return {
                    "categories": categories,
                    "category_keys": category_keys,
                    "series": {
                        "Transactions": [
                            item["transaction_count"] for item in rows
                        ]
                    },
                }
            return {
                "categories": categories,
                "category_keys": category_keys,
                "series": {
                    "GED spend": [
                        money(item.get("amount_cents")) for item in rows
                    ]
                },
                "display": {
                    "GED spend": [
                        item.get("amount_label", "Not available")
                        for item in rows
                    ]
                },
            }
        return None

    def _build_account_drilldown(self) -> QWidget:
        card, layout = _card()
        card.setAccessibleName("Department and account financial drill-down")
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.addWidget(_label("Account Financial Drill-down", "cardTitle"))
        title_box.addWidget(
            _label(
                "Review → Department → Account / category → Budget summary → "
                "GED transactions → vendor → transaction → source evidence",
                "cardDetail",
                wrap=True,
            )
        )
        header.addLayout(title_box, 1)
        self._account_selector = QComboBox()
        self._account_selector.setAccessibleName(
            "Select department and account for financial drill-down"
        )
        accounts = self._projection["metrics"].get(
            "canonical_financial_dataset", {}
        ).get("accounts", ())
        for account in accounts:
            label = (
                f"{account['account_number']} · {account['account_name']}"
                + (
                    " · Unmapped"
                    if account.get("budget_mapping") == "UNMAPPED"
                    else ""
                )
            )
            self._account_selector.addItem(label, account["scope_key"])
        self._account_selector.currentIndexChanged.connect(
            self._show_account_drilldown
        )
        header.addWidget(self._account_selector)
        close = QPushButton("Close Detail")
        close.setProperty("role", "quiet")
        close.setAccessibleName("Close account financial drill-down")
        close.clicked.connect(lambda: card.setVisible(False))
        header.addWidget(close)
        layout.addLayout(header)

        self._account_context = _label("", "sectionSub", wrap=True)
        layout.addWidget(self._account_context)
        self._account_summary = QTableWidget()
        self._account_summary.setAccessibleName(
            "Selected account Budget and GED summary"
        )
        self._account_summary.verticalHeader().setVisible(False)
        self._account_summary.setColumnCount(2)
        self._account_summary.setHorizontalHeaderLabels(("Financial value", "Recorded result"))
        self._account_summary.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._account_summary.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self._account_summary.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._account_summary.setMaximumHeight(330)
        layout.addWidget(self._account_summary)

        layout.addWidget(_label("Contributing GED Transactions", "cardTitle"))
        self._account_transactions = QTableWidget()
        self._account_transactions.setAccessibleName(
            "Contributing GED transactions for selected account"
        )
        transaction_headers = (
            "Source Row",
            "Fiscal Period",
            "Journal Number",
            "Vendor",
            "Description",
            "Amount",
        )
        self._account_transactions.setColumnCount(len(transaction_headers))
        self._account_transactions.setHorizontalHeaderLabels(transaction_headers)
        self._account_transactions.verticalHeader().setVisible(False)
        self._account_transactions.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._account_transactions.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._account_transactions.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._account_transactions.setMinimumHeight(300)
        layout.addWidget(self._account_transactions)

        actions = QHBoxLayout()
        self._account_budget_source = QPushButton("Show Budget Source")
        self._account_budget_source.setProperty("role", "secondary")
        self._account_budget_source.setAccessibleName(
            "Show selected account Budget source evidence"
        )
        self._account_budget_source.clicked.connect(
            self._open_account_budget_source
        )
        actions.addWidget(self._account_budget_source)
        self._account_ged_source = QPushButton(
            "Show Selected Transaction Source"
        )
        self._account_ged_source.setProperty("role", "secondary")
        self._account_ged_source.setAccessibleName(
            "Show selected contributing GED transaction source evidence"
        )
        self._account_ged_source.clicked.connect(
            self._open_account_transaction_source
        )
        actions.addWidget(self._account_ged_source)
        self._account_findings = QPushButton("View Account Findings")
        self._account_findings.setProperty("role", "secondary")
        self._account_findings.setAccessibleName(
            "View findings for selected department and account"
        )
        self._account_findings.clicked.connect(
            self._open_selected_account_findings
        )
        actions.addWidget(self._account_findings)
        ask_account = QPushButton("Ask Fin About Account")
        ask_account.setProperty("role", "assistant")
        ask_account.setAccessibleName(
            "Ask Fin about the selected account"
        )
        ask_account.clicked.connect(self._ask_fin_about_selected_account)
        actions.addWidget(ask_account)
        actions.addStretch(1)
        layout.addLayout(actions)
        self._show_account_drilldown()
        self._account_drilldown_card = card
        return card

    def _selected_account_projection(self) -> dict[str, Any] | None:
        if not hasattr(self, "_account_selector"):
            return None
        scope_key = self._account_selector.currentData()
        return next(
            (
                item
                for item in self._projection["metrics"]
                .get("canonical_financial_dataset", {})
                .get("accounts", ())
                if item["scope_key"] == scope_key
            ),
            None,
        )

    def _show_account_drilldown(self, _index: int | None = None) -> None:
        account = self._selected_account_projection()
        if account is None:
            return
        self._account_context.setText(
            f"{self._projection['basis']['department_name']} "
            f"({account['department_number']}) → {account['account_number']} → "
            f"{account['account_name'] or 'Account name unavailable'}\n"
            f"{account['ged_transaction_count']} GED transaction(s) · "
            f"{account['finding_count']} finding(s) · "
            f"Reconciliation: {_human_status(account['reconciliation_status'])}"
        )

        rows = (
            ("BGT", account["bgt_label"]),
            ("Budget ATD", account["atd_label"]),
            ("ETC", account["etc_label"]),
            ("EAC", account["eac_label"]),
            ("DELTA", account["delta_label"]),
            ("Summed GED Amount", account["summed_ged_amount_label"]),
            (
                "ATD − GED Difference",
                account["budget_to_ged_difference_label"],
            ),
            ("Remaining Budget", account["remaining_budget_label"]),
            ("Over-budget Amount", account["over_budget_amount_label"]),
            ("Budget Utilization", account["budget_utilization_label"]),
            (
                "Rule Outcomes",
                " · ".join(
                    f"{item['rule_id']} {_human_status(item['status'])}"
                    for item in account["rule_outcomes"]
                )
                or "No applicable rule result",
            ),
            (
                "Finding Badges",
                ", ".join(account["finding_badges"]) or "None",
            ),
            (
                "Original / Edited Provenance",
                (
                    f"Budget {account['provenance']['budget_value_origin']} · "
                    f"{account['provenance']['edited_ged_field_count']} edited "
                    "GED field(s)"
                ),
            ),
        )
        self._account_summary.setRowCount(len(rows))
        for row, (label, value) in enumerate(rows):
            self._account_summary.setItem(row, 0, QTableWidgetItem(label))
            self._account_summary.setItem(row, 1, QTableWidgetItem(_display(value)))
        self._account_summary.resizeRowsToContents()

        record_ids = set(account["contributing_ged_records"])
        records = (
            [
                record
                for record in self._dataset.ged_transactions
                if record.record_id in record_ids
            ]
            if self._dataset is not None
            else []
        )
        self._account_transactions.setRowCount(len(records))
        for row, record in enumerate(records):
            values = (
                record.row_number,
                record.value("fiscal_period"),
                record.value("journal_number"),
                record.value("vendor_name"),
                record.value("journal_line_description")
                or record.value("journal_description"),
                record.value("amount"),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(_display(value))
                if column == 0:
                    item.setData(RECORD_ID_ROLE, record.record_id)
                self._account_transactions.setItem(row, column, item)
        self._account_transactions.resizeColumnsToContents()
        if records:
            self._account_transactions.selectRow(0)
        self._account_budget_source.setEnabled(
            bool(account.get("budget_source_record"))
        )
        self._account_ged_source.setEnabled(bool(records))
        self._account_findings.setEnabled(bool(account["finding_count"]))

    def _ask_fin_about_selected_account(self) -> None:
        account = self._selected_account_projection()
        if account is None:
            return
        self._open_private_ask_fin(
            object_type="account",
            object_id=str(account["scope_key"]),
            label=f"{account['account_number']} {account['account_name']}",
        )

    def _open_account_drilldown(self, scope_key: str) -> None:
        self._open_results_tab(self._comparison_tab)
        if hasattr(self, "_account_drilldown_card"):
            self._account_drilldown_card.setVisible(True)
        if not hasattr(self, "_account_selector"):
            return
        index = self._account_selector.findData(scope_key)
        if index >= 0:
            self._account_selector.setCurrentIndex(index)
            self._account_selector.setFocus()

    def _open_account_status_group(self, status_key: str) -> None:
        expected = {
            "over-budget": "FAIL",
            "within-budget": "PASS",
            "not-evaluated": "NOT_EVALUATED",
        }.get(status_key)
        accounts = self._projection["metrics"].get(
            "canonical_financial_dataset", {}
        ).get("accounts", ())
        match = next(
            (
                account
                for account in accounts
                if any(
                    result["rule_id"] == "CORE-01"
                    and result["status"] == expected
                    for result in account["rule_outcomes"]
                )
            ),
            None,
        )
        if match is not None:
            self._open_account_drilldown(match["scope_key"])
        else:
            self._open_results_tab(self._comparison_tab)

    def _open_reconciliation_status_group(self, status_key: str) -> None:
        expected = {
            "reconciled": "PASS",
            "different": "FAIL",
            "not-evaluated": "NOT_EVALUATED",
        }.get(status_key)
        accounts = self._projection["metrics"].get(
            "canonical_financial_dataset", {}
        ).get("accounts", ())
        match = next(
            (
                account
                for account in accounts
                if any(
                    result["rule_id"] == "CORE-05"
                    and result["status"] == expected
                    for result in account["rule_outcomes"]
                )
            ),
            None,
        )
        if match is not None:
            self._open_account_drilldown(match["scope_key"])
        else:
            self._open_results_tab(self._comparison_tab)

    def _open_polarity_source(self, polarity: str) -> None:
        group = next(
            (
                item
                for item in self._projection["metrics"]
                .get("analytics", {})
                .get("ged_by_polarity", ())
                if item["polarity"] == polarity
            ),
            None,
        )
        records = group.get("contributing_ged_records", ()) if group else ()
        if records:
            self._open_source_record(str(records[0]), field_name="amount")
        else:
            self._open_results_tab(self._ged_results_tab)

    def _open_account_budget_source(self) -> None:
        account = self._selected_account_projection()
        if account and account.get("budget_source_record"):
            self._open_source_record(
                str(account["budget_source_record"]),
                field_name="bgt",
            )

    def _open_account_transaction_source(self) -> None:
        row = self._account_transactions.currentRow()
        item = self._account_transactions.item(row, 0) if row >= 0 else None
        record_id = item.data(RECORD_ID_ROLE) if item else None
        if record_id:
            self._open_source_record(str(record_id), field_name="amount")

    def _open_selected_account_findings(self) -> None:
        account = self._selected_account_projection()
        if account is None:
            return
        self._open_results_tab(self._findings_tab)
        self._findings_search.setText(account["account_number"])

    def _budget_actual_rows_card(self, accounts) -> QWidget:
        """Render explicit Budget/Actual values with compact supporting bars."""

        card, layout = _card()
        title_row = QHBoxLayout()
        title_row.addWidget(_label("Budget vs Actual by account", "cardTitle"))
        title_row.addStretch(1)
        title_row.addWidget(
            _label("Over budget is shown in red; favorable is green.", "context")
        )
        layout.addLayout(title_row)
        ordered = sorted(
            accounts,
            key=lambda item: (
                -(item.get("overrun_cents") or 0),
                item.get("remaining_cents") or 0,
                str(item.get("account_number", "")),
            ),
        )[:8]
        for item in ordered:
            bgt = item.get("bgt_cents")
            actual = item.get("ged_cents")
            max_value = max(abs(bgt or 0), abs(actual or 0), 1)
            variance_cents = item.get("actual_variance_cents")
            overrun = (variance_cents or 0) > 0
            row = QFrame()
            row.setProperty("role", "analysisRow")
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(t.SP_2, t.SP_1, t.SP_2, t.SP_1)
            row_layout.setSpacing(t.SP_1)
            header = QHBoxLayout()
            header.addWidget(
                _label(
                    f"{item.get('account_number', '')} "
                    f"{item.get('account_name', '')}".strip(),
                    "kvVal",
                ),
                1,
            )
            if variance_cents is None or not item.get("complete", False):
                variance_text = "Incomplete"
                variance_role = "warning"
            elif variance_cents > 0:
                variance_text = (
                    f"over {item.get('actual_variance_label')} "
                    f"({item.get('actual_variance_percentage_label')})"
                )
                variance_role = "error"
            elif variance_cents < 0:
                variance_text = (
                    f"under {str(item.get('actual_variance_label')).removeprefix('-')} "
                    f"({item.get('actual_variance_percentage_label')})"
                )
                variance_role = "success"
            else:
                variance_text = "On budget · +0.00%"
                variance_role = "success"
            variance = _label(
                variance_text,
                variance_role,
            )
            header.addWidget(variance)
            open_button = QPushButton("View")
            open_button.setProperty("role", "quiet")
            open_button.setAccessibleName(
                f"Open account {item.get('account_number')} details"
            )
            open_button.clicked.connect(
                lambda _checked=False, scope=item.get("scope_key", ""):
                self._open_account_drilldown(str(scope))
            )
            header.addWidget(open_button)
            row_layout.addLayout(header)
            for label_text, cents, display, tone in (
                ("Budget", bgt, item.get("bgt_label"), "budget"),
                (
                    "Actual",
                    actual,
                    item.get("ged_label"),
                    "actualOver" if overrun else "actualUnder",
                ),
            ):
                value_row = QHBoxLayout()
                caption = _label(label_text, "kvKey")
                caption.setFixedWidth(54)
                value_row.addWidget(caption)
                bar = QProgressBar()
                bar.setTextVisible(False)
                bar.setRange(0, 1000)
                bar.setValue(
                    min(1000, int(abs(cents or 0) * 1000 / max_value))
                )
                bar.setProperty("tone", tone)
                bar.setAccessibleName(
                    f"{label_text} for account {item.get('account_number')}: "
                    f"{display}"
                )
                value_row.addWidget(bar, 1)
                amount = _label(str(display), "kvVal")
                amount.setMinimumWidth(112)
                amount.setAlignment(
                    Qt.AlignmentFlag.AlignRight
                    | Qt.AlignmentFlag.AlignVCenter
                )
                value_row.addWidget(amount)
                row_layout.addLayout(value_row)
            layout.addWidget(row)
        return card

    def _severity_summary_card(self, severity_rows) -> QWidget:
        card, layout = _card()
        layout.addWidget(_label("Findings by severity", "cardTitle"))
        total = sum(int(item.get("count", 0)) for item in severity_rows)
        layout.addWidget(_label(str(total), "metricValue"))
        layout.addWidget(_label("recorded findings", "context"))
        for item in severity_rows:
            severity = str(item.get("severity", ""))
            count = int(item.get("count", 0))
            action = QPushButton(f"{severity}    {count}")
            action.setProperty("role", "severityAction")
            action.setProperty("severity", severity.lower())
            action.setAccessibleName(
                f"Open {count} {severity.lower()} findings"
            )
            action.clicked.connect(
                lambda _checked=False, value=severity:
                self._open_findings_filter(severity=value)
            )
            layout.addWidget(action)
        layout.addStretch(1)
        return card

    def _vendor_spend_card(self, vendor_rows) -> QWidget:
        """Show grounded vendor spend as compact horizontal bars."""

        card, layout = _card()
        card.setAccessibleName("Spend by vendor")
        title_row = QHBoxLayout()
        title_row.addWidget(_label("Spend by vendor", "cardTitle"))
        title_row.addStretch(1)
        title_row.addWidget(
            _label(
                "Prior-period comparison is not available in these reports.",
                "context",
            )
        )
        layout.addLayout(title_row)
        named = sorted(
            (
                item
                for item in vendor_rows
                if item.get("vendor_name") != "No vendor recorded"
            ),
            key=lambda item: abs(item.get("amount_cents") or 0),
            reverse=True,
        )
        maximum = max(
            (abs(item.get("amount_cents") or 0) for item in named),
            default=1,
        )
        for item in named[:8]:
            row = QHBoxLayout()
            vendor = _label(str(item["vendor_name"]), "kvVal")
            vendor.setMinimumWidth(210)
            row.addWidget(vendor)
            bar = QProgressBar()
            bar.setRange(0, 1000)
            bar.setTextVisible(False)
            bar.setValue(
                min(
                    1000,
                    int(
                        abs(item.get("amount_cents") or 0)
                        * 1000
                        / maximum
                    ),
                )
            )
            bar.setProperty("tone", "actual")
            bar.setAccessibleName(
                f"{item['vendor_name']} recorded spend: "
                f"{item['amount_label']}"
            )
            row.addWidget(bar, 1)
            amount = _label(str(item["amount_label"]), "kvVal")
            amount.setMinimumWidth(118)
            amount.setAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            )
            row.addWidget(amount)
            count = _label(
                f"{item['transaction_count']} transactions", "context"
            )
            count.setMinimumWidth(104)
            row.addWidget(count)
            view = QPushButton("View")
            view.setProperty("role", "quiet")
            view.setAccessibleName(
                f"Open GED transactions for {item['vendor_name']}"
            )
            view.clicked.connect(
                lambda _checked=False, value=item["vendor_name"]:
                self._focus_ged_value("Vendor", str(value))
            )
            row.addWidget(view)
            layout.addLayout(row)
        unassigned = next(
            (
                item
                for item in vendor_rows
                if item.get("vendor_name") == "No vendor recorded"
            ),
            None,
        )
        if unassigned is not None:
            detail = (
                f"No vendor recorded · {unassigned['amount_label']} · "
                f"{unassigned['transaction_count']} transactions"
            )
            if not unassigned.get("complete"):
                detail += (
                    f" · {unassigned.get('missing_amount_count', 0)} "
                    "missing amount"
                )
            layout.addWidget(_label(detail, "warning", wrap=True))
        return card

    def _populate_results(self):
        projection = self._projection
        metrics = projection["metrics"]
        basis = projection["basis"]
        completion = projection.get("completion")
        analytics = metrics.get("analytics", {})
        vendor_count = sum(
            item.get("vendor_name") != "No vendor recorded"
            for item in analytics.get("ged_by_vendor", ())
        )
        self._results_eyebrow.setText(
            f"Financial Review · {basis['reporting_period']}"
        )
        self._results_subtitle.setText(
            f"{basis['department_name']} · {basis['department_number']} · "
            f"{projection.get('publication_state', 'Recorded')} · "
            f"Validation Run {projection['run_id']}"
        )
        self._results_period.setText(str(basis["reporting_period"]))
        self._results_files.setText(
            f"{basis['budget_filename']} · {basis['ged_filename']}"
        )
        self._results_entities.setText(
            f"1 department · {metrics['budget_records']} accounts · "
            f"{vendor_count} vendors"
        )
        self._results_records.setText(
            f"{metrics['ged_transactions']} GED transactions · "
            f"{metrics['budget_records']} budget accounts · "
            f"{metrics.get('corrections', 0)} edits"
        )
        self._results_completeness.setText(
            "Complete results"
            if metrics.get("scope_not_evaluated", 0) == 0
            else (
                f"Recorded results · {metrics['scope_not_evaluated']} "
                "not evaluated"
            )
        )
        self._complete_button.setVisible(not bool(completion))
        revalidation_available = self._dataset is not None
        self._review_rules_button.setEnabled(revalidation_available)
        revalidation_help = (
            "Open the current Rule Set and create another Validation Run "
            "using the verified working data."
            if revalidation_available
            else "Verified working data could not be reconstructed. Reopen "
            "the review or restore the unchanged source files before revalidation."
        )
        self._review_rules_button.setToolTip(revalidation_help)
        self._review_rules_button.setAccessibleDescription(
            revalidation_help
        )
        self._results_progress.set_step(
            5,
            completed_steps={6} if completion else set(),
        )
        self._read_only = True

        overview = self._replace_layout(self._overview_tab)
        identity, identity_layout = _card("noticeCard")
        identity_layout.addWidget(
            _label(
                "Recorded financial status, material exceptions, supporting "
                "evidence, and items requiring human review.",
                "context",
                wrap=True,
            )
        )
        comparison = projection.get("comparison")
        if comparison:
            identity_layout.addWidget(
                _label(
                    "New Validation Run compared with prior run · "
                    f"{len(comparison.get('findings_added', ()))} findings added · "
                    f"{len(comparison.get('findings_removed', ()))} removed · "
                    f"{len(comparison.get('findings_changed', ()))} changed · "
                    f"{len(comparison.get('findings_unchanged', ()))} unchanged. "
                    "The prior run remains preserved.",
                    "cardDetail",
                    wrap=True,
                )
            )
        details_button = QPushButton("Review Details")
        details_button.setProperty("role", "quiet")
        details_button.setCheckable(True)
        details_button.setAccessibleName("Show validation audit details")
        identity_layout.addWidget(
            details_button, 0, Qt.AlignmentFlag.AlignLeft
        )
        audit_details, audit_details_layout = _card()
        audit_details.setProperty("role", "secondaryDetails")
        for title, value in (
            ("Validation Run ID", projection["run_id"]),
            ("Rule Set Version", projection["rule_set_id"]),
            ("Review Version", projection["generation_id"]),
            (
                "Verification Basis",
                basis["generation_id"],
            ),
        ):
            detail_row = QHBoxLayout()
            detail_row.addWidget(_label(title, "kvKey"))
            detail_row.addStretch(1)
            detail_row.addWidget(_label(value, "mono", wrap=True))
            audit_details_layout.addLayout(detail_row)
        audit_details.setVisible(False)
        details_button.toggled.connect(audit_details.setVisible)
        details_button.toggled.connect(
            lambda expanded: details_button.setText(
                "Hide Review Details" if expanded else "Review Details"
            )
        )
        identity_layout.addWidget(audit_details)
        overview.addWidget(identity)
        totals = metrics["financial_totals"]
        controls = metrics.get("financial_control_report", {})
        missing_amounts = (
            controls.get("ged", {})
            .get("total_eligible_amount", {})
            .get("missing_or_unparseable_amount_count", 0)
        )
        metrics_grid = QGridLayout()
        overall_status = str(metrics["overall_status"])
        rag_status = str(metrics["rag_status"])
        overall_tone = (
            "warning"
            if "incomplete" in overall_status.casefold()
            else (
                "danger"
                if "red" in rag_status.casefold()
                else (
                    "success"
                    if "green" in rag_status.casefold()
                    else "warning"
                )
            )
        )
        cards = (
            (
                "Overall Status",
                overall_status,
                rag_status,
                lambda: self._open_results_tab(self._comparison_tab),
                overall_tone,
            ),
            (
                "Total Budget",
                totals["bgt"],
                "Planned budget",
                lambda: self._open_results_tab(self._budget_results_tab),
                "",
            ),
            (
                "Actual Spend",
                totals["ged"],
                (
                    "All required amounts present"
                    if totals["ged_is_complete"]
                    else (
                        f"Parseable total · {missing_amounts} required "
                        "amount(s) missing"
                    )
                ),
                lambda: self._open_results_tab(self._ged_results_tab),
                "",
            ),
            (
                "Estimate at Completion",
                totals["eac"],
                "ATD plus ETC",
                lambda: self._open_results_tab(self._budget_results_tab),
                "",
            ),
            (
                "Variance",
                analytics.get("financial_summary", {}).get(
                    "actual_variance_label", "Unavailable"
                ),
                analytics.get("financial_summary", {}).get(
                    "actual_variance_percentage_label",
                    "Unavailable while Actual is incomplete",
                ),
                lambda: self._open_results_tab(self._comparison_tab),
                "",
            ),
            (
                "Findings Requiring Attention",
                sum(
                    bool(item.get("review_required", True))
                    for item in projection["findings"]
                ),
                (
                    f"{metrics['findings_by_severity']['High']} high · "
                    f"{metrics['findings_by_severity']['Medium']} medium"
                ),
                lambda: self._open_results_tab(self._findings_tab),
                "",
            ),
        )
        for index, values in enumerate(cards):
            metrics_grid.addWidget(
                self._metric_card(
                    values[0],
                    values[1],
                    values[2],
                    values[3],
                    tone=values[4],
                ),
                index // 3,
                index % 3,
            )
        for column in range(3):
            metrics_grid.setColumnStretch(column, 1)
        overview.addLayout(metrics_grid)
        analytics = metrics.get("analytics", {})
        chart_grid = QGridLayout()
        chart_grid.setHorizontalSpacing(t.SP_3)
        chart_grid.setVerticalSpacing(t.SP_3)
        chart_grid.addWidget(
            self._budget_actual_rows_card(
                analytics.get("comparison_by_account", ())
            ),
            0,
            0,
        )
        chart_grid.addWidget(
            self._severity_summary_card(
                analytics.get("findings_by_severity", ())
            ),
            0,
            1,
        )
        chart_grid.setColumnStretch(0, 1)
        chart_grid.setColumnStretch(1, 0)
        overview.addLayout(chart_grid)
        top, top_layout = _card()
        top_layout.addWidget(_label("Top Findings", "cardTitle"))
        for finding in projection["findings"][:5]:
            finding_row, finding_layout = _card("surfaceRaised")
            finding_header = QHBoxLayout()
            finding_header.addWidget(
                _label(
                    f"{finding['severity']} · "
                    f"{finding.get('business_title') or finding['rule_name']}",
                    "cardValue",
                    wrap=True,
                ),
                1,
            )
            finding_header.addWidget(
                _label(
                    str(finding.get("review_status", "New")),
                    "statusPill",
                )
            )
            finding_layout.addLayout(finding_header)
            finding_layout.addWidget(
                _label(
                    f"{finding['department_number']} / "
                    f"{finding['account_number']} · "
                    f"{finding.get('what_happened') or finding['explanation']}",
                    "cardDetail",
                    wrap=True,
                )
            )
            finding_actions = QHBoxLayout()
            explain = QPushButton("Explain This")
            explain.setProperty("role", "quiet")
            explain.setAccessibleName(
                f"Explain {finding['rule_name']} finding for "
                f"{finding['department_number']} {finding['account_number']}"
            )
            explain.clicked.connect(
                lambda _checked=False, item=finding:
                self._open_finding_by_id(str(item["finding_id"]))
            )
            finding_actions.addWidget(explain)
            ask = QPushButton("Ask Fin")
            ask.setProperty("role", "assistant")
            ask.setAccessibleName(
                f"Ask Fin about {finding['rule_name']} finding"
            )
            ask.clicked.connect(
                lambda _checked=False, item=finding:
                self._ask_fin_for_finding(item)
            )
            finding_actions.addWidget(ask)
            finding_actions.addStretch(1)
            finding_layout.addLayout(finding_actions)
            top_layout.addWidget(finding_row)
        overview.addWidget(top)
        next_card, next_layout = _card()
        next_layout.addWidget(_label("Items to Review Next", "cardTitle"))
        for finding in projection["findings"][:3]:
            action = QPushButton(
                f"Review {finding['account_number']} · "
                f"{finding.get('business_title') or finding['rule_name']}"
            )
            action.setProperty("role", "summaryAction")
            action.setAccessibleName(
                f"Open evidence for review item: {_review_guidance(finding)}"
            )
            action.setToolTip(_review_guidance(finding))
            action.clicked.connect(
                lambda _checked=False, item=finding: self._open_findings_filter(
                    rule_id=item["rule_id"]
                )
            )
            next_layout.addWidget(action)
        overview.addWidget(next_card)
        overview.addStretch(1)

        self._populate_budget_results_tab()
        self._populate_ged_results_tab()

        comparison = self._replace_layout(self._comparison_tab)
        comparison.addWidget(
            _label(
                "Budget and GED values aligned by exact Department Number + Account "
                "Number. Every status comes from the sealed deterministic rule ledger.",
                "sectionSub",
                wrap=True,
            )
        )
        comparison_projection = metrics.get("analytics", {}).get(
            "comparison_by_account", ()
        )
        comparison.addWidget(
            self._budget_actual_rows_card(comparison_projection)
        )
        comparison.addWidget(self._build_account_drilldown())
        self._account_drilldown_card.setVisible(False)
        comparison_details = {
            (item["department_number"], item["account_number"]): item
            for item in metrics["account_comparisons"]
        }

        def comparison_rows():
            for item in comparison_projection:
                details = comparison_details[
                    (item["department_number"], item["account_number"])
                ]
                yield (
                    f"{item['account_number']} {item['account_name']}",
                    item["department_number"],
                    item["bgt_label"],
                    item["ged_label"],
                    details["budget_etc"],
                    details["budget_eac"],
                    _variance_text(
                        item["actual_variance_label"],
                        item.get("actual_variance_cents"),
                    ),
                    _variance_text(
                        item["actual_variance_percentage_label"],
                        item.get("actual_variance_cents"),
                    ),
                    (
                        f"{_human_status(details['reconciliation_status'])} · "
                        f"{details['ged_transaction_count']} GED rows"
                    ),
                )

        comparison.addWidget(
            self._projection_table(
                (
                    "Account",
                    "Department",
                    "BGT",
                    "Actual",
                    "ETC",
                    "EAC",
                    "Actual Variance",
                    "Variance %",
                    "Completeness / Reconciliation",
                ),
                comparison_rows(),
            )
        )
        self._populate_stage2_analysis_tabs()

        self._populate_rule_results_tab()

        findings_layout = self._replace_layout(self._finding_list_tab)
        findings_filter_card, findings_toolbar = _card("surfaceRaised")
        self._findings_search = QLineEdit()
        self._findings_search.setPlaceholderText("Search findings and evidence")
        self._findings_search.setAccessibleName("Search findings")
        search_row = QHBoxLayout()
        search_row.addWidget(self._findings_search, 1)
        self._explain_finding_button = QPushButton("Explain This")
        self._explain_finding_button.setProperty("role", "primary")
        self._explain_finding_button.setAccessibleName(
            "Open a deterministic explanation for the selected finding"
        )
        search_row.addWidget(self._explain_finding_button)
        ask_finding = QPushButton("Ask Fin")
        ask_finding.setProperty("role", "assistant")
        ask_finding.setAccessibleName(
            "Ask Fin about the selected recorded finding"
        )
        ask_finding.clicked.connect(self._show_ask_fin)
        search_row.addWidget(ask_finding)
        findings_toolbar.addLayout(search_row)
        filter_grid = QGridLayout()
        self._findings_severity = QComboBox()
        self._findings_severity.setAccessibleName("Filter findings by severity")
        self._findings_severity.addItems(
            ("All severities", "Critical", "High", "Medium", "Low")
        )
        self._findings_rule = QComboBox()
        self._findings_rule.setAccessibleName("Filter findings by rule")
        self._findings_rule.addItems(
            ("All rules", *(item["rule_id"] for item in projection["executions"]))
        )
        self._findings_status = QComboBox()
        self._findings_status.setAccessibleName(
            "Filter findings by review status"
        )
        self._findings_status.addItems(
            (
                "All statuses",
                "New",
                "Acknowledged",
                "In Review",
                "Resolved",
                "Dismissed",
            )
        )
        self._findings_account = QComboBox()
        self._findings_account.setAccessibleName(
            "Filter findings by account"
        )
        self._findings_account.addItems(
            (
                "All accounts",
                *sorted(
                    {
                        str(item.get("account_number", ""))
                        for item in projection["findings"]
                        if item.get("account_number")
                    }
                ),
            )
        )
        self._findings_vendor = QComboBox()
        self._findings_vendor.setAccessibleName("Filter findings by vendor")
        self._findings_vendor.addItems(
            (
                "All vendors",
                *sorted(
                    {
                        str(vendor)
                        for item in projection["findings"]
                        for vendor in item.get("explain_this", {})
                        .get("supporting_evidence", {})
                        .get("vendors", ())
                        if vendor
                    }
                ),
            )
        )
        self._findings_department = QComboBox()
        self._findings_department.setAccessibleName(
            "Filter findings by department"
        )
        self._findings_department.addItems(
            (
                "All departments",
                *sorted(
                    {
                        str(item.get("department_number", ""))
                        for item in projection["findings"]
                        if item.get("department_number")
                    }
                ),
            )
        )
        self._findings_review_required = QComboBox()
        self._findings_review_required.setAccessibleName(
            "Filter findings by review-required state"
        )
        self._findings_review_required.addItems(
            ("All review states", "Review required", "Review complete")
        )
        for index, (title, control) in enumerate(
            (
                ("Severity", self._findings_severity),
                ("Status", self._findings_status),
                ("Rule", self._findings_rule),
                ("Account", self._findings_account),
                ("Vendor", self._findings_vendor),
                ("Department", self._findings_department),
                ("Follow-up", self._findings_review_required),
            )
        ):
            row = (index // 4) * 2
            column = index % 4
            filter_grid.addWidget(_label(title, "kvKey"), row, column)
            filter_grid.addWidget(control, row + 1, column)
            filter_grid.setColumnStretch(column, 1)
        findings_toolbar.addLayout(filter_grid)
        findings_layout.addWidget(findings_filter_card)
        self._findings_count = _label("", "context")
        findings_layout.addWidget(self._findings_count)
        self._findings_result_table = self._findings_table(
            projection["findings"]
        )
        findings_splitter = QSplitter(Qt.Orientation.Horizontal)
        findings_splitter.setAccessibleName(
            "Findings and selected finding evidence"
        )
        findings_splitter.addWidget(self._findings_result_table)
        finding_detail = self._build_finding_detail_panel()
        self._findings_result_table.setMinimumWidth(300)
        finding_detail.setMinimumWidth(340)
        findings_splitter.addWidget(finding_detail)
        findings_splitter.setChildrenCollapsible(False)
        findings_splitter.setStretchFactor(0, 5)
        findings_splitter.setStretchFactor(1, 7)
        findings_splitter.setMinimumHeight(440)
        findings_splitter.setSizes((520, 720))
        findings_layout.addWidget(findings_splitter)
        self._findings_splitter = findings_splitter
        finding_detail.setVisible(False)
        self._finding_detail_panel = finding_detail
        self._explain_finding_button.clicked.connect(
            lambda: self._set_finding_explanation_visible(True)
        )
        self._findings_result_table.doubleClicked.connect(
            lambda _index: self._set_finding_explanation_visible(True)
        )
        if self._findings_proxy.rowCount():
            self._findings_result_table.selectRow(0)
            self._show_finding_detail(
                self._findings_proxy.index(0, 0),
                self._findings_proxy.index(-1, -1),
            )

        quality = self._replace_layout(self._quality_tab)
        quality.addWidget(
            _label(
                f"Complete rule-result coverage: {metrics['rule_results']} results · "
                f"{metrics['scope_passed']} passed · {metrics['scope_failed']} failed · "
                f"{metrics['scope_not_evaluated']} not evaluated.",
                "sectionSub",
                wrap=True,
            )
        )
        quality_counts = metrics["data_quality_counts"]
        quality_grid = QGridLayout()
        quality_cards = (
            ("Budget detail rows", metrics["budget_records"], "Evaluated account rows", None),
            ("GED transaction rows", metrics["ged_transactions"], "Evaluated transactions", None),
            ("Excluded rows", quality_counts["excluded_records"], "Totals, groups, and blanks", None),
            ("Missing required values", quality_counts["missing_fields"], "Required data", "CORE-04"),
            ("Unparseable values", quality_counts["invalid_values"], "Present but invalid", "CORE-04"),
            ("Duplicate candidates", quality_counts["duplicate_records"], "Repeated copies", "CORE-03"),
            ("Unmapped transactions", quality_counts["unmapped_transactions"], "Budget mapping", "CORE-02"),
            ("Department mismatches", quality_counts["department_mismatches"], "Upload gate", None),
            ("Period mismatches", quality_counts["period_mismatches"], "Upload gate", None),
            (
                "Reconciliation not evaluated",
                metrics.get("reconciliation_not_evaluated", 0),
                "Incomplete scopes",
                "CORE-05",
            ),
            (
                "Reviewed edits",
                metrics.get("corrections", 0),
                f"{metrics['budget_records'] + metrics['ged_transactions']} original rows retained",
                None,
            ),
        )
        for index, values in enumerate(quality_cards):
            quality_grid.addWidget(
                self._quality_metric_button(*values), index // 3, index % 3
            )
        for column in range(3):
            quality_grid.setColumnStretch(column, 1)
        quality.addLayout(quality_grid)
        quality.addWidget(_label("Exact Financial Control Totals", "cardTitle"))
        control_report = metrics.get("financial_control_report", {})
        control_rows = []
        for field_name, value in (
            control_report.get("budget", {}).get("totals", {})
        ).items():
            control_rows.append(
                (
                    f"Budget {field_name.upper()}",
                    value["display"],
                    value["exact_decimal"],
                    value["formula"],
                    value["source_row_count"],
                    "Complete" if value["complete"] else "Incomplete",
                )
            )
        ged_control = control_report.get("ged", {})
        for label, key in (
            ("Eligible GED Amount", "total_eligible_amount"),
            ("Mapped GED Amount", "mapped_amount"),
            ("Unmapped GED Amount", "unmapped_amount"),
            ("Excluded GED Transaction Amount", "excluded_transaction_amount"),
        ):
            value = ged_control.get(key, {})
            control_rows.append(
                (
                    label,
                    value.get("display", "Unavailable"),
                    value.get("exact_decimal", "Unavailable"),
                    value.get("formula", ""),
                    value.get("source_row_count", ""),
                    (
                        "Complete"
                        if value.get("complete", True)
                        else (
                            "Incomplete · "
                            f"{value.get('missing_or_unparseable_amount_count', 0)} "
                            "missing/unparseable"
                        )
                    ),
                )
            )
        quality.addWidget(
            self._projection_table(
                (
                    "Control",
                    "Display Value",
                    "Exact Decimal",
                    "Formula / Aggregation Logic",
                    "Source Rows",
                    "Completeness",
                ),
                control_rows,
            )
        )
        quality.addWidget(_label("Row Inclusion and Exclusion", "cardTitle"))
        row_treatments = []
        for source, section in (
            ("Budget", control_report.get("budget", {})),
            ("GED", control_report.get("ged", {})),
        ):
            for item in section.get("row_types", ()):
                row_treatments.append(
                    (
                        source,
                        item["row_type"],
                        item["count"],
                        item["treatment"],
                        ", ".join(str(row) for row in item["source_rows"]),
                    )
                )
        quality.addWidget(
            self._projection_table(
                (
                    "Source",
                    "Row Type",
                    "Count",
                    "Treatment",
                    "Source Rows",
                ),
                row_treatments,
            )
        )
        quality.addWidget(_label("Evaluation Coverage Gaps", "cardTitle"))
        quality.addWidget(
            self._projection_table(
                (
                    "Rule",
                    "Scope",
                    "Status",
                    "Department",
                    "Account",
                    "Explanation",
                    "Evidence",
                ),
                (
                    (
                        item["rule_id"],
                        item["scope_id"],
                        _human_status(item["status"]),
                        item["department_number"],
                        item["account_number"],
                        item["explanation"],
                        ", ".join(item["evidence"]),
                    )
                    for item in projection["scope_results"]
                    if item["status"] == "NOT_EVALUATED"
                ),
            )
        )
        self._populate_review_summary_tab()
        quality.addWidget(_label("Approved Source Field Coverage", "cardTitle"))
        quality.addWidget(
            self._projection_table(
                (
                    "Source",
                    "Column",
                    "Field",
                    "Canonical Dataset",
                    "Used For",
                    "Displayed Where",
                    "Validation Impact",
                    "Exclusion Reason",
                ),
                (
                    (
                        item["source"],
                        item["source_column"],
                        item["source_field"],
                        item["dataset"],
                        item["used_for"],
                        item["displayed_where"],
                        item["validation_impact"],
                        item["exclusion_reason"] or "Not excluded",
                    )
                    for item in metrics.get("field_coverage", ())
                ),
            )
        )

    @staticmethod
    def _combined_status(statuses: Iterable[str]) -> str:
        values = set(statuses)
        if "FAIL" in values:
            return "Finding"
        if "NOT_EVALUATED" in values:
            return "Not evaluated"
        return "Pass"

    def _source_unavailable(self, widget, title: str) -> bool:
        if self._dataset is not None:
            return False
        layout = self._replace_layout(widget)
        layout.addWidget(
            _label(
                f"{title} cannot be reconstructed because the preserved source path "
                "is unavailable. The sealed validation ledger, comparisons, findings, "
                "and summary metrics remain available.",
                "context",
                wrap=True,
            )
        )
        layout.addWidget(
            self._chart_from_projection(
                "Budget by account",
                "BGT, ATD, ETC, EAC, DELTA, and remaining budget or overrun "
                "for the highest-impact account scopes in this recorded run.",
                self._projection["metrics"].get("analytics", {}).get(
                    "budget_by_account"
                ),
                value_axis_title="Amount",
                on_activate=self._open_account_drilldown,
            )
        )
        layout.addStretch(1)
        return True

    def _populate_stage2_analysis_tabs(self) -> None:
        metrics = self._projection["metrics"]
        analytics = metrics.get("analytics", {})

        vendor_layout = self._replace_layout(self._vendor_analysis_tab)
        vendor_layout.addWidget(
            _label(
                "Vendor spend uses only recorded GED transactions. Prior-period "
                "change is not shown because the uploaded reports contain no "
                "authoritative prior-review comparison.",
                "sectionSub",
                wrap=True,
            )
        )
        vendor_layout.addWidget(
            self._vendor_spend_card(analytics.get("ged_by_vendor", ()))
        )
        vendor_accounts: dict[str, set[str]] = {}
        vendor_record_ids: dict[str, set[str]] = {}
        if self._dataset is not None:
            for record in self._dataset.ged_transactions:
                vendor = (
                    _display(record.value("vendor_name"))
                    or "No vendor recorded"
                )
                account = _display(record.value("account_number"))
                if account:
                    vendor_accounts.setdefault(vendor, set()).add(account)
                vendor_record_ids.setdefault(vendor, set()).add(
                    record.record_id
                )

        def vendor_finding_count(vendor: str) -> int:
            record_ids = vendor_record_ids.get(vendor, set())
            return sum(
                bool(record_ids.intersection(finding["source_records"]))
                for finding in self._projection["findings"]
            )

        self._vendor_analysis_table = self._projection_table(
            (
                "Vendor",
                "Recorded Spend",
                "Accounts",
                "Transactions",
                "Findings",
                "Completeness",
            ),
            (
                (
                    item["vendor_name"],
                    item["amount_label"],
                    len(vendor_accounts.get(item["vendor_name"], set())),
                    item["transaction_count"],
                    vendor_finding_count(item["vendor_name"]),
                    (
                        "Complete"
                        if item.get("complete")
                        else (
                            f"Incomplete · {item.get('missing_amount_count', 0)} "
                            "missing amount"
                        )
                    ),
                )
                for item in analytics.get("ged_by_vendor", ())
            ),
        )
        self._vendor_analysis_table.activated.connect(
            lambda index: self._focus_ged_value(
                "Vendor", _display(index.siblingAtColumn(0).data())
            )
        )
        vendor_layout.addWidget(self._vendor_analysis_table)
        vendor_actions = QHBoxLayout()
        open_vendor = QPushButton("Open Selected Vendor Transactions")
        open_vendor.setProperty("role", "primary")
        open_vendor.setAccessibleName(
            "Open GED transactions for the selected vendor"
        )
        open_vendor.clicked.connect(self._open_selected_vendor_transactions)
        vendor_actions.addWidget(open_vendor)
        ask_vendor = QPushButton("Ask Fin About Vendor")
        ask_vendor.setProperty("role", "assistant")
        ask_vendor.setAccessibleName(
            "Ask Fin about the selected vendor's recorded spend"
        )
        ask_vendor.clicked.connect(self._ask_fin_about_selected_vendor)
        vendor_actions.addWidget(ask_vendor)
        vendor_actions.addStretch(1)
        vendor_layout.addLayout(vendor_actions)

        department_layout = self._replace_layout(
            self._department_analysis_tab
        )
        department_layout.addWidget(
            _label(
                "The approved source pair contains one department. FinSight "
                "shows that department without fabricating portfolio peers.",
                "sectionSub",
                wrap=True,
            )
        )
        basis = self._projection["basis"]
        totals = metrics["financial_totals"]
        financial_summary = analytics.get("financial_summary", {})
        self._department_analysis_table = self._projection_table(
            (
                "Department",
                "Accounts",
                "Budget",
                "Actual Spend",
                "ETC",
                "EAC",
                "Actual Variance",
                "Variance %",
                "Findings",
            ),
            (
                (
                    f"{basis['department_number']} "
                    f"{basis['department_name']}",
                    metrics["budget_records"],
                    totals["bgt"],
                    totals["ged"],
                    totals["etc"],
                    totals["eac"],
                    _variance_text(
                        financial_summary.get(
                            "actual_variance_label", "Unavailable"
                        ),
                        financial_summary.get("actual_variance_cents"),
                    ),
                    _variance_text(
                        financial_summary.get(
                            "actual_variance_percentage_label",
                            "Unavailable",
                        ),
                        financial_summary.get("actual_variance_cents"),
                    ),
                    metrics["findings"],
                ),
            ),
        )
        self._department_analysis_table.activated.connect(
            lambda _index: self._open_results_tab(
                self._account_analysis_tab
            )
        )
        department_layout.addWidget(self._department_analysis_table)
        open_department = QPushButton("Open Department Accounts")
        open_department.setProperty("role", "primary")
        open_department.setAccessibleName(
            f"Open accounts for department {basis['department_number']}"
        )
        open_department.clicked.connect(
            lambda: self._open_results_tab(self._account_analysis_tab)
        )
        department_actions = QHBoxLayout()
        department_actions.addWidget(open_department)
        ask_department = QPushButton("Ask Fin About Department")
        ask_department.setProperty("role", "assistant")
        ask_department.setAccessibleName(
            f"Ask Fin about department {basis['department_number']}"
        )
        ask_department.clicked.connect(
            lambda: self._open_private_ask_fin(
                object_type="department",
                object_id=str(basis["department_number"]),
                label=(
                    f"{basis['department_number']} "
                    f"{basis['department_name']}"
                ),
            )
        )
        department_actions.addWidget(ask_department)
        department_actions.addStretch(1)
        department_layout.addLayout(department_actions)

        reconciliation_layout = self._replace_layout(
            self._reconciliation_tab
        )
        reconciliation_layout.addWidget(
            _label(
                "Budget ATD is compared with the exact summed GED Amount for "
                "each Department Number + Account Number. Incomplete scopes "
                "remain Not evaluated.",
                "sectionSub",
                wrap=True,
            )
        )
        reconciliation_layout.addWidget(
            self._projection_table(
                (
                    "Department",
                    "Account",
                    "Account Name",
                    "Budget ATD",
                    "Summed GED",
                    "Difference",
                    "Status",
                    "Budget Source Row",
                    "GED Source Rows",
                ),
                (
                    (
                        item["department_number"],
                        item["account_number"],
                        item["account_name"],
                        item["budget_atd"],
                        item["ged_amount"],
                        item["variance_atd_to_ged"],
                        _human_status(item["reconciliation_status"]),
                        item["budget_source_row"],
                        ", ".join(
                            str(row)
                            for row in item["contributing_ged_rows"]
                        ),
                    )
                    for item in metrics["account_comparisons"]
                ),
            )
        )

    def _selected_vendor_name(self) -> str:
        table = getattr(self, "_vendor_analysis_table", None)
        if table is None or not table.currentIndex().isValid():
            return ""
        return _display(
            table.model().index(table.currentIndex().row(), 0).data()
        )

    def _open_selected_vendor_transactions(self) -> None:
        vendor = self._selected_vendor_name()
        if vendor:
            self._focus_ged_value("Vendor", vendor)

    def _ask_fin_about_selected_vendor(self) -> None:
        vendor = self._selected_vendor_name()
        if not vendor:
            show_in_app_message(
                self,
                "Ask Fin",
                "Select a vendor first.",
            )
            return
        self._open_private_ask_fin(
            object_type="vendor",
            object_id=vendor,
            label=vendor,
        )

    def _populate_review_summary_tab(self) -> None:
        layout = self._replace_layout(self._review_summary_tab)
        projection = self._projection
        metrics = projection["metrics"]
        basis = projection["basis"]
        summary = dict(projection.get("leadership_summary") or {})
        layout.addWidget(
            _label(
                f"{basis['reporting_period']} Leadership Summary",
                "sectionHeader",
            )
        )
        layout.addWidget(
            _label(
                "Generated deterministically from the preserved validation run. "
                "Ask Fin may explain this summary but cannot change its figures "
                "or conclusions.",
                "sectionSub",
                wrap=True,
            )
        )
        status_card, status_layout = _card()
        status_layout.addWidget(_label("Overall Review Status", "cardLabel"))
        status_layout.addWidget(
            _label(
                str(summary.get("overall_status") or metrics["overall_status"]),
                "metricValue",
            )
        )
        status_layout.addWidget(
            _label(
                f"{metrics['findings']} recorded findings · "
                f"{metrics['budget_overruns']} budget overrun findings · "
                f"{metrics['reconciliation_findings']} reconciliation findings",
                "cardDetail",
                wrap=True,
            )
        )
        layout.addWidget(status_card)
        totals = metrics["financial_totals"]
        financial_position = dict(summary.get("financial_position") or {})
        facts = QGridLayout()
        for index, (title, value, detail, destination) in enumerate(
            (
                (
                    "Budget",
                    financial_position.get("budget", totals["bgt"]),
                    "Approved BGT",
                    self._account_analysis_tab,
                ),
                (
                    "Actual Spend",
                    financial_position.get("actual_spend", totals["ged"]),
                    "Summed GED Amount",
                    self._ged_transactions_tab,
                ),
                (
                    "EAC",
                    financial_position.get("eac", totals["eac"]),
                    "ATD + ETC",
                    self._account_analysis_tab,
                ),
                (
                    "Budget Remaining",
                    financial_position.get("variance", totals["delta"]),
                    financial_position.get(
                        "variance_basis", "Budget DELTA (BGT − EAC)"
                    ),
                    self._comparison_tab,
                ),
                (
                    "Rules Executed",
                    metrics["rules_executed"],
                    f"{metrics['rules_failed']} failed",
                    self._rule_results_tab,
                ),
                (
                    "Data Quality",
                    metrics["data_quality"],
                    f"{metrics['missing_required_data']} missing",
                    self._quality_tab,
                ),
            )
        ):
            facts.addWidget(
                self._metric_card(
                    title,
                    value,
                    detail,
                    lambda _checked=False, target=destination:
                    self._open_results_tab(target),
                ),
                index // 3,
                index % 3,
            )
        layout.addLayout(facts)
        priorities, priorities_layout = _card()
        priorities_layout.addWidget(
            _label("Leadership Priorities", "cardTitle")
        )
        priority_findings = summary.get("highest_priority_findings") or [
            {
                "finding_id": item["finding_id"],
                "severity": item["severity"],
                "title": item.get("business_title") or item["rule_name"],
                "what_happened": item.get("what_happened")
                or item["explanation"],
            }
            for item in projection["findings"][:5]
        ]
        if priority_findings:
            for priority in priority_findings:
                action = QPushButton(
                    f"{priority['severity']} · {priority['title']} · "
                    "Open supporting evidence"
                )
                action.setProperty("role", "summaryAction")
                action.setAccessibleName(
                    f"Open evidence for {priority['title']}: "
                    f"{priority['what_happened']}"
                )
                action.setToolTip(str(priority["what_happened"]))
                action.clicked.connect(
                    lambda _checked=False, finding_id=priority["finding_id"]:
                    self._open_finding_by_id(str(finding_id))
                )
                priorities_layout.addWidget(action)
        else:
            priorities_layout.addWidget(
                _label("No recorded findings require review.", "success")
            )
        layout.addWidget(priorities)
        for limitation in summary.get("data_quality_limitations", ()):
            layout.addWidget(_label(str(limitation), "warning", wrap=True))
        if summary.get("decision_boundary"):
            layout.addWidget(
                _label(
                    str(summary["decision_boundary"]),
                    "context",
                    wrap=True,
                )
            )
        run_details, run_layout = _card("surfaceRaised")
        run_layout.addWidget(_label("Recorded Run", "cardTitle"))
        run_layout.addWidget(
            self._projection_table(
                ("Validation Run", "Rule Set", "Review Version", "Timestamp"),
                (
                    (
                        projection["run_id"],
                        projection["rule_set_id"],
                        projection["generation_id"],
                        projection["completed_at"],
                    ),
                ),
            )
        )
        layout.addWidget(run_details)
        layout.addStretch(1)

    def _populate_budget_results_tab(self) -> None:
        if self._source_unavailable(self._budget_results_tab, "Budget source data"):
            return
        layout = self._replace_layout(self._budget_results_tab)
        layout.addWidget(
            _label(
                "Select an account to drill into its Budget values, contributing "
                "GED transactions, vendors, findings, and preserved source rows.",
                "sectionSub",
                wrap=True,
            )
        )
        accounts = [
            item
            for item in self._projection["metrics"]
            .get("canonical_financial_dataset", {})
            .get("accounts", ())
            if item.get("budget_source_record")
        ]
        actual_by_scope = {
            item["scope_key"]: item
            for item in self._projection["metrics"]
            .get("analytics", {})
            .get("comparison_by_account", ())
        }

        def account_rows():
            for item in accounts:
                actual = actual_by_scope.get(item["scope_key"], {})
                variance_cents = actual.get("actual_variance_cents")
                yield (
                    item["budget_source_row"],
                    item["department_number"],
                    item["account_number"],
                    item["account_name"],
                    item["bgt_label"],
                    item["summed_ged_amount_label"],
                    item["eac_label"],
                    _variance_text(
                        actual.get("actual_variance_label", "Unavailable"),
                        variance_cents,
                    ),
                    _variance_text(
                        actual.get(
                            "actual_variance_percentage_label",
                            "Unavailable",
                        ),
                        variance_cents,
                    ),
                    len(item.get("vendors", ())),
                    item["ged_transaction_count"],
                    item["finding_count"],
                    _human_status(item["reconciliation_status"]),
                    item["budget_source_record"],
                )

        self._budget_results_table = self._projection_table(
            (
                "Source Row",
                "Department",
                "Account",
                "Account Name",
                "BGT",
                "GED Actual",
                "EAC",
                "Actual Variance",
                "Variance %",
                "Vendors",
                "Transactions",
                "Findings",
                "Reconciliation",
                "Source Record",
            ),
            account_rows(),
        )
        self._budget_results_table.setColumnHidden(13, True)
        self._budget_results_table.activated.connect(
            lambda index: self._open_account_drilldown(
                f"{_display(index.siblingAtColumn(1).data())}|"
                f"{_display(index.siblingAtColumn(2).data())}"
            )
        )
        layout.addWidget(self._budget_results_table)
        actions = QHBoxLayout()
        open_account = QPushButton("Open Selected Account")
        open_account.setProperty("role", "primary")
        open_account.clicked.connect(
            lambda: self._open_account_drilldown(
                f"{_display(self._budget_results_table.model().index(self._budget_results_table.currentIndex().row(), 1).data())}|"
                f"{_display(self._budget_results_table.model().index(self._budget_results_table.currentIndex().row(), 2).data())}"
            )
            if self._budget_results_table.currentIndex().isValid()
            else None
        )
        actions.addWidget(open_account)
        budget_action = QPushButton("View Finding")
        budget_action.setProperty("role", "secondary")
        budget_action.clicked.connect(
            lambda: self._open_finding_for_table(
                self._budget_results_table, 13
            )
        )
        actions.addWidget(budget_action)
        actions.addStretch(1)
        layout.addLayout(actions)

    def _populate_ged_results_tab(self) -> None:
        if self._source_unavailable(
            self._ged_transactions_tab, "GED source data"
        ):
            return
        layout = self._replace_layout(self._ged_transactions_tab)
        layout.addWidget(
            _label(
                "All extracted GED rows. Transaction status combines mapping, "
                "duplicate, and required-data results from the sealed ledger.",
                "sectionSub",
                wrap=True,
            )
        )
        filter_card, filter_layout = _card("surfaceRaised")
        filter_grid = QGridLayout()
        transactions = tuple(self._dataset.ged_transactions)

        def selector(label_text: str, values) -> QComboBox:
            box = QComboBox()
            box.setAccessibleName(f"Filter GED transactions by {label_text}")
            box.addItem("All")
            box.addItems(
                sorted(
                    {
                        _display(value)
                        for value in values
                        if _display(value)
                    }
                )
            )
            return box

        self._ged_vendor_filter = selector(
            "vendor", (row.value("vendor_name") for row in transactions)
        )
        self._ged_account_filter = selector(
            "account", (row.value("account_number") for row in transactions)
        )
        self._ged_department_filter = selector(
            "department",
            (row.value("department_number") for row in transactions),
        )
        self._ged_period_filter = selector(
            "fiscal period",
            (row.value("fiscal_period") for row in transactions),
        )
        for column, (title, control) in enumerate(
            (
                ("Vendor", self._ged_vendor_filter),
                ("Account", self._ged_account_filter),
                ("Department", self._ged_department_filter),
                ("Fiscal Period", self._ged_period_filter),
            )
        ):
            filter_grid.addWidget(_label(title, "kvKey"), 0, column)
            filter_grid.addWidget(control, 1, column)
        self._ged_min_filter = QLineEdit()
        self._ged_min_filter.setPlaceholderText("No minimum")
        self._ged_min_filter.setAccessibleName("Minimum GED Amount")
        self._ged_max_filter = QLineEdit()
        self._ged_max_filter.setPlaceholderText("No maximum")
        self._ged_max_filter.setAccessibleName("Maximum GED Amount")
        self._ged_finding_filter = QComboBox()
        self._ged_finding_filter.setAccessibleName(
            "Filter GED transactions by finding presence"
        )
        self._ged_finding_filter.addItems(
            ("All", "With finding", "No finding")
        )
        for column, (title, control) in enumerate(
            (
                ("Minimum Amount", self._ged_min_filter),
                ("Maximum Amount", self._ged_max_filter),
                ("Finding", self._ged_finding_filter),
            )
        ):
            filter_grid.addWidget(_label(title, "kvKey"), 2, column)
            filter_grid.addWidget(control, 3, column)
        filter_layout.addLayout(filter_grid)
        layout.addWidget(filter_card)
        findings_by_record: dict[str, list[dict[str, Any]]] = {}
        for finding in self._projection["findings"]:
            for record_id in finding["source_records"]:
                findings_by_record.setdefault(record_id, []).append(finding)

        fields = (
            "department_number",
            "department_name",
            "account_number",
            "account_name",
            "fiscal_period",
            "journal_number",
            "journal_date",
            "vendor_name",
            "journal_description",
            "journal_line_description",
            "amount",
        )

        def rows():
            for record in transactions:
                row_findings = findings_by_record.get(record.record_id, [])
                rule_badges = ", ".join(
                    dict.fromkeys(item["rule_name"] for item in row_findings)
                )
                yield (
                    record.row_number,
                    *(_display(record.value(field_name)) for field_name in fields),
                    rule_badges or "No findings",
                    record.record_id,
                )

        self._ged_results_table = self._projection_table(
                (
                    "Source Row",
                    "Department",
                    "Department Name",
                    "Account",
                    "Account Name",
                    "Fiscal Period",
                    "Journal Number",
                    "Journal Date",
                    "Vendor",
                    "Journal Description",
                    "Journal-line Description",
                    "Amount",
                    "Findings",
                    "Source Record",
                ),
                rows(),
        )
        self._ged_results_proxy = _GedResultsFilter(self)
        self._ged_results_proxy.setSourceModel(
            self._ged_results_table.model()
        )
        self._ged_results_table.setModel(self._ged_results_proxy)
        self._ged_results_table.setColumnHidden(13, True)
        self._ged_result_count = _label(
            f"{len(transactions)} GED transactions", "context"
        )
        layout.addWidget(self._ged_result_count)
        layout.addWidget(self._ged_results_table)
        for key, control in (
            ("vendor", self._ged_vendor_filter),
            ("account", self._ged_account_filter),
            ("department", self._ged_department_filter),
            ("period", self._ged_period_filter),
            ("finding", self._ged_finding_filter),
        ):
            control.currentTextChanged.connect(
                lambda value, name=key: self._set_ged_filter(name, value)
            )
        self._ged_min_filter.textChanged.connect(
            lambda value: self._set_ged_filter("minimum", value)
        )
        self._ged_max_filter.textChanged.connect(
            lambda value: self._set_ged_filter("maximum", value)
        )
        ged_actions = QHBoxLayout()
        open_transaction = QPushButton("Open Selected Transaction")
        open_transaction.setProperty("role", "primary")
        open_transaction.setAccessibleName(
            "Open details and source evidence for the selected GED transaction"
        )
        open_transaction.clicked.connect(self._open_selected_ged_details)
        ged_actions.addWidget(open_transaction)
        ged_action = QPushButton("View Finding")
        ged_action.setProperty("role", "secondary")
        ged_action.clicked.connect(
            lambda: self._open_finding_for_table(
                self._ged_results_table, 13
            )
        )
        ged_actions.addWidget(ged_action)
        ged_actions.addStretch(1)
        layout.addLayout(ged_actions)
        self._ged_results_table.doubleClicked.connect(
            lambda _index: self._open_selected_ged_details()
        )

    def _set_ged_filter(self, key: str, value: Any) -> None:
        proxy = getattr(self, "_ged_results_proxy", None)
        if proxy is None:
            return
        proxy.set_value(key, value)
        self._ged_result_count.setText(
            f"{proxy.rowCount()} of {proxy.sourceModel().rowCount()} "
            "GED transactions"
        )

    def _open_selected_ged_details(self) -> None:
        table = getattr(self, "_ged_results_table", None)
        if table is None or not table.currentIndex().isValid():
            show_in_app_message(
                self,
                "GED Transaction Details",
                "Select a GED transaction first.",
            )
            return
        row = table.currentIndex().row()
        record_id = _display(table.model().index(row, 13).data())
        record = next(
            (
                item
                for item in self._dataset.ged_transactions
                if item.record_id == record_id
            ),
            None,
        )
        if record is None:
            return
        row_findings = [
            item
            for item in self._projection["findings"]
            if record_id in item["source_records"]
        ]
        dialog = InAppDialog(
            "GED Transaction Details",
            f"Source row {record.row_number} · recorded values and preserved "
            "source lineage",
            variant=DialogVariant.INFORMATION,
            parent=self,
            object_name="GEDTransactionDetailsDialog",
            minimum_width=820,
        )
        dialog.resize(820, 680)
        layout = dialog.content_layout
        summary, summary_layout = _card()
        summary_grid = QGridLayout()
        summary_values = (
            ("Department", record.value("department_number")),
            ("Department Name", record.value("department_name")),
            ("Account", record.value("account_number")),
            ("Account Name", record.value("account_name")),
            ("Vendor", record.value("vendor_name") or "No vendor recorded"),
            ("Fiscal Period", record.value("fiscal_period")),
            ("Journal Number", record.value("journal_number")),
            ("Journal Date", record.value("journal_date")),
            (
                "Amount",
                record.value("amount")
                if record.value("amount") is not None
                else "Missing",
            ),
            (
                "Findings",
                ", ".join(
                    item.get("business_title") or item["rule_name"]
                    for item in row_findings
                )
                or "No findings",
            ),
        )
        for index, (title, value) in enumerate(summary_values):
            row_number = index // 2
            column = (index % 2) * 2
            summary_grid.addWidget(
                _label(title, "kvKey"),
                row_number,
                column,
                Qt.AlignmentFlag.AlignTop,
            )
            summary_grid.addWidget(
                _label(_display(value), "kvVal", wrap=True),
                row_number,
                column + 1,
            )
        summary_grid.setColumnStretch(1, 1)
        summary_grid.setColumnStretch(3, 1)
        summary_layout.addLayout(summary_grid)
        summary_layout.addWidget(
            _label(
                "Journal description: "
                f"{_display(record.value('journal_description')) or 'Blank'}",
                "cardDetail",
                wrap=True,
            )
        )
        summary_layout.addWidget(
            _label(
                "Journal-line description: "
                f"{_display(record.value('journal_line_description')) or 'Blank'}",
                "cardDetail",
                wrap=True,
            )
        )
        layout.addWidget(summary)
        source_file = self._c.financial_source_file_name(
            self._review.review_id, "GED"
        )
        layout.addWidget(
            _label(
                f"Source evidence · {source_file} · {record.worksheet} · "
                f"row {record.row_number}",
                "cardTitle",
                wrap=True,
            )
        )
        evidence = QTableWidget()
        evidence.setAccessibleName(
            "GED transaction original and reviewed source values"
        )
        evidence.verticalHeader().setVisible(False)
        evidence.setColumnCount(5)
        evidence.setHorizontalHeaderLabels(
            ("Field", "Cell", "Original", "Current Reviewed", "Edited")
        )
        evidence.setRowCount(len(record.current))
        for evidence_row, field_name in enumerate(record.current):
            original = record.original.get(field_name)
            current = record.current.get(field_name)
            values = (
                field_name.replace("_", " ").title(),
                record.cells.get(field_name, ""),
                _display(original) or "(blank)",
                _display(current) or "(blank)",
                "Yes" if current != original else "No",
            )
            for column, value in enumerate(values):
                evidence.setItem(
                    evidence_row, column, QTableWidgetItem(str(value))
                )
        evidence.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        evidence.setAlternatingRowColors(True)
        evidence.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        evidence.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        evidence.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        evidence.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        evidence.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )
        layout.addWidget(evidence, 1)
        open_account = QPushButton("Open Related Account")
        open_account.setProperty("role", "secondary")
        open_account.setAccessibleName(
            "Open the related account analysis"
        )
        open_account.clicked.connect(
            lambda: (
                dialog.accept(),
                self._open_account_drilldown(
                    f"{_display(record.value('department_number'))}|"
                    f"{_display(record.value('account_number'))}"
                ),
            )
        )
        dialog.actions_layout.insertWidget(1, open_account)
        if row_findings:
            open_finding = QPushButton("Open Related Finding")
            open_finding.setProperty("role", "secondary")
            open_finding.clicked.connect(
                lambda: (
                    dialog.accept(),
                    self._open_finding_by_id(
                        str(row_findings[0]["finding_id"])
                    ),
                )
            )
            dialog.actions_layout.insertWidget(2, open_finding)
        ask_fin = QPushButton("Ask Fin")
        ask_fin.setProperty("role", "assistant")
        ask_fin.setAccessibleName(
            f"Ask Fin about GED source row {record.row_number}"
        )
        ask_fin.clicked.connect(
            lambda: (
                dialog.accept(),
                self._open_private_ask_fin(
                    object_type="transaction",
                    object_id=record_id,
                    label=f"GED row {record.row_number}",
                ),
            )
        )
        dialog.actions_layout.insertWidget(
            dialog.actions_layout.count(), ask_fin
        )
        close = dialog.add_action(
            "Close",
            role="primary",
            accessible_name="Close GED transaction details",
            accept=True,
            default=True,
        )
        dialog.set_safe_focus(close)
        dialog.exec()

    def _populate_rule_results_tab(self) -> None:
        layout = self._replace_layout(self._rule_results_tab)
        layout.addWidget(
            _label(
                "Rule performance shows which controls ran and how every evaluated "
                "scope concluded. Select a rule to inspect its recorded evidence.",
                "sectionSub",
                wrap=True,
            )
        )
        try:
            comparison = self._c.latest_validation_comparison(
                self._review.review_id
            )
        except Exception:
            comparison = None
        if comparison:
            comparison_card, comparison_layout = _card()
            comparison_layout.addWidget(
                _label("Compared with Prior Validation Run", "cardTitle")
            )
            comparison_layout.addWidget(
                _label(
                    f"{len(comparison['rules_added'])} rule(s) added · "
                    f"{len(comparison['rules_removed'])} removed · "
                    f"{len(comparison['rules_changed'])} changed · "
                    f"{len(comparison.get('rules_unchanged', ())) } unchanged · "
                    f"{len(comparison['findings_added'])} finding(s) added · "
                    f"{len(comparison.get('findings_removed', comparison['findings_resolved']))} removed · "
                    f"{len(comparison.get('findings_changed', ())) } changed · "
                    f"{len(comparison.get('findings_unchanged', ())) } unchanged. "
                    "Both runs remain retained and historically reproducible.",
                    "cardDetail",
                    wrap=True,
                )
            )
            comparison_table = QTableWidget()
            comparison_table.setAccessibleName(
                "Previous and current validation outcome comparison"
            )
            comparison_table.verticalHeader().setVisible(False)
            comparison_table.setColumnCount(2)
            comparison_table.setHorizontalHeaderLabels(
                ("Change", "Recorded details")
            )
            comparison_rows = (
                ("Rules added", ", ".join(comparison["rules_added"]) or "None"),
                (
                    "Rules removed",
                    ", ".join(comparison["rules_removed"]) or "None",
                ),
                (
                    "Rules changed",
                    ", ".join(
                        item["rule_id"]
                        for item in comparison["rules_changed"]
                    )
                    or "None",
                ),
                (
                    "Rules unchanged",
                    ", ".join(
                        item["rule_id"]
                        for item in comparison.get(
                            "rules_unchanged", ()
                        )
                    )
                    or "None",
                ),
                (
                    "Rule version changes",
                    ", ".join(
                        item["rule_id"]
                        for item in comparison.get(
                            "rule_version_changes", ()
                        )
                    )
                    or "None",
                ),
                (
                    "Status changes",
                    ", ".join(
                        item["rule_id"]
                        for item in comparison.get(
                            "status_changes", ()
                        )
                    )
                    or "None",
                ),
                (
                    "Findings added",
                    ", ".join(
                        item["rule_id"]
                        for item in comparison["findings_added"]
                    )
                    or "None",
                ),
                (
                    "Findings removed",
                    ", ".join(
                        item["rule_id"]
                        for item in comparison.get(
                            "findings_removed",
                            comparison["findings_resolved"],
                        )
                    )
                    or "None",
                ),
                (
                    "Findings changed",
                    ", ".join(
                        item["rule_id"]
                        for item in comparison.get("findings_changed", ())
                    )
                    or "None",
                ),
                (
                    "Findings unchanged",
                    ", ".join(
                        item["rule_id"]
                        for item in comparison.get(
                            "findings_unchanged", ()
                        )
                    )
                    or "None",
                ),
                (
                    "Optional rule effects",
                    ", ".join(
                        f"{item['rule_id']}: {item['effect'].title()}"
                        for item in comparison.get(
                            "optional_rule_effects", ()
                        )
                    )
                    or "None",
                ),
            )
            comparison_table.setRowCount(len(comparison_rows))
            comparison_table.setEditTriggers(
                QAbstractItemView.EditTrigger.NoEditTriggers
            )
            for row, (label, details) in enumerate(comparison_rows):
                comparison_table.setItem(
                    row, 0, QTableWidgetItem(label)
                )
                comparison_table.setItem(
                    row, 1, QTableWidgetItem(details)
                )
            comparison_table.resizeColumnsToContents()
            comparison_layout.addWidget(comparison_table)
            layout.addWidget(comparison_card)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setAccessibleName("Rule results and selected rule evidence")

        summary_card, summary_layout = _card()
        summary_layout.addWidget(_label("Rules executed", "cardTitle"))
        headers = (
            "Rule",
            "Version",
            "Outcome",
            "Evaluated",
            "Passed",
            "Failed",
            "Not evaluated",
            "Findings",
            "Severity",
        )
        model = QStandardItemModel(0, len(headers), self)
        model.setHorizontalHeaderLabels(list(headers))
        findings_by_rule = {
            execution["rule_id"]: [
                finding
                for finding in self._projection["findings"]
                if finding["rule_id"] == execution["rule_id"]
            ]
            for execution in self._projection["executions"]
        }
        for execution in self._projection["executions"]:
            total = (
                execution["pass_count"]
                + execution["fail_count"]
                + execution["not_evaluated_count"]
            )
            row = [
                QStandardItem(execution["rule_name"]),
                QStandardItem(execution["version"]),
                QStandardItem(_human_status(execution["status"])),
                QStandardItem(str(total)),
                QStandardItem(str(execution["pass_count"])),
                QStandardItem(str(execution["fail_count"])),
                QStandardItem(str(execution["not_evaluated_count"])),
                QStandardItem(str(len(findings_by_rule[execution["rule_id"]]))),
                QStandardItem(
                    str(
                        self._projection["metrics"]["rule_severity"].get(
                            execution["rule_id"], ""
                        )
                    )
                ),
            ]
            row[0].setData(execution, PROJECTION_ROLE)
            model.appendRow(row)
        table = QTableView()
        table.setAccessibleName("Validation results by rule")
        table.setModel(model)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.resizeColumnsToContents()
        summary_layout.addWidget(table)
        summary_card.setMinimumWidth(300)
        splitter.addWidget(summary_card)

        detail_card, detail_layout = _card()
        detail_layout.addWidget(_label("Selected Rule Evidence", "cardTitle"))
        self._selected_rule_title = _label(
            "Select a rule.", "cardValue", wrap=True
        )
        detail_layout.addWidget(self._selected_rule_title)
        self._selected_rule_purpose = _label("", "cardDetail", wrap=True)
        detail_layout.addWidget(self._selected_rule_purpose)
        self._selected_rule_outcome = _label("", "statusPill", wrap=True)
        self._selected_rule_outcome.setMinimumHeight(28)
        detail_layout.addWidget(
            self._selected_rule_outcome,
            0,
            Qt.AlignmentFlag.AlignLeft,
        )
        self._rule_scope_table = QTableView()
        self._rule_scope_table.setAccessibleName(
            "Selected rule evaluations and affected records"
        )
        self._rule_scope_table.verticalHeader().setVisible(False)
        self._rule_scope_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._rule_scope_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._rule_scope_table.setAlternatingRowColors(True)
        detail_layout.addWidget(self._rule_scope_table)
        detail_card.setMinimumWidth(340)
        evidence_actions = QHBoxLayout()
        self._rule_evidence_selector = QComboBox()
        self._rule_evidence_selector.setAccessibleName(
            "Select source evidence for the selected rule result"
        )
        evidence_actions.addWidget(self._rule_evidence_selector, 1)
        self._open_rule_evidence = QPushButton("Show Evidence in Source Data")
        self._open_rule_evidence.setProperty("role", "secondary")
        self._open_rule_evidence.setAccessibleName(
            "Open selected rule evaluation source evidence"
        )
        self._open_rule_evidence.clicked.connect(
            self._open_selected_rule_evidence
        )
        evidence_actions.addWidget(self._open_rule_evidence)
        evidence_actions.addStretch(1)
        detail_layout.addLayout(evidence_actions)
        splitter.addWidget(detail_card)
        splitter.setChildrenCollapsible(False)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 7)
        splitter.setMinimumHeight(440)
        splitter.setSizes((520, 720))
        layout.addWidget(splitter)
        self._rule_results_splitter = splitter
        self._rule_summary_model = model
        self._rule_summary_table = table
        table.selectionModel().currentRowChanged.connect(
            self._show_rule_evidence
        )
        if model.rowCount():
            table.selectRow(0)
            self._show_rule_evidence(model.index(0, 0), model.index(-1, -1))

    def _show_rule_evidence(self, current, _previous) -> None:
        if not current.isValid():
            return
        execution = self._rule_summary_model.item(current.row(), 0).data(
            PROJECTION_ROLE
        )
        if not execution:
            return
        rule_id = execution["rule_id"]
        self._selected_rule_title.setText(
            f"{execution['rule_name']} · Version {execution['version']}"
        )
        self._selected_rule_purpose.setText(
            str(execution.get("purpose") or RULE_PURPOSES.get(rule_id, ""))
        )
        self._selected_rule_outcome.setText(
            f"{_human_status(execution['status'])} · "
            f"{execution['pass_count']} passed · "
            f"{execution['fail_count']} failed · "
            f"{execution['not_evaluated_count']} not evaluated"
        )
        results = [
            item
            for item in self._projection["scope_results"]
            if item["rule_id"] == rule_id
        ]
        results.sort(
            key=lambda item: (
                {"FAIL": 0, "NOT_EVALUATED": 1, "PASS": 2}.get(
                    item["status"], 9
                ),
                item["scope_id"],
            )
        )
        headers = (
            "Outcome",
            "Rule Version",
            "Department",
            "Account",
            "Workbook",
            "Worksheet / Row / Cell",
            "Original",
            "Reviewed",
            "Expected",
            "Actual",
            "Explanation",
            "Review Guidance",
        )
        model = QStandardItemModel(0, len(headers), self)
        model.setHorizontalHeaderLabels(list(headers))
        findings = [
            finding
            for finding in self._projection["findings"]
            if finding["rule_id"] == rule_id
        ]
        for result in results:
            record_id = (
                result["source_records"][0]
                if result["source_records"]
                else ""
            )
            evidence = (
                result.get("evidence_details", [None])[0]
                if result.get("evidence_details")
                else (result["evidence"][0] if result["evidence"] else "")
            )
            source = self._source_record_details(record_id, evidence)
            action = next(
                (
                    _review_guidance(finding)
                    for finding in findings
                    if set(finding["source_records"]).intersection(
                        result["source_records"]
                    )
                ),
                "No action required.",
            )
            values = (
                _human_status(result["status"]),
                result.get("rule_version", execution["version"]),
                result["department_number"],
                result["account_number"],
                source["workbook"],
                source["location"],
                source["original"],
                source["current"],
                result["expected"],
                result["actual"],
                result["explanation"],
                action,
            )
            items = [QStandardItem(_display(value)) for value in values]
            items[0].setData(result, PROJECTION_ROLE)
            model.appendRow(items)
        self._rule_scope_model = model
        self._rule_scope_table.setModel(model)
        self._rule_scope_table.resizeColumnsToContents()
        self._rule_scope_table.selectionModel().currentRowChanged.connect(
            self._populate_rule_source_selector
        )
        if model.rowCount():
            self._rule_scope_table.selectRow(0)
            self._populate_rule_source_selector(
                model.index(0, 0), model.index(-1, -1)
            )
        else:
            self._rule_evidence_selector.clear()
        self._open_rule_evidence.setEnabled(
            self._rule_evidence_selector.count() > 0
        )

    def _populate_rule_source_selector(self, current, _previous) -> None:
        self._rule_evidence_selector.clear()
        if not current.isValid():
            self._open_rule_evidence.setEnabled(False)
            return
        result = self._rule_scope_model.item(current.row(), 0).data(
            PROJECTION_ROLE
        )
        if not result:
            self._open_rule_evidence.setEnabled(False)
            return
        details_by_record = {
            str(item.get("record_id", "")): item
            for item in result.get("evidence_details", ())
        }
        for record_id in result.get("source_records", ()):
            detail = details_by_record.get(record_id, {})
            source = self._source_record_details(record_id, detail)
            self._rule_evidence_selector.addItem(
                f"{source['workbook']} · {source['location']}",
                (
                    record_id,
                    str(detail.get("field", "")),
                ),
            )
        self._open_rule_evidence.setEnabled(
            self._rule_evidence_selector.count() > 0
        )

    def _source_record_details(self, record_id: str, evidence: Any) -> dict[str, str]:
        role = record_id.partition(":")[0]
        parts = record_id.split(":")
        worksheet = parts[1] if len(parts) > 1 else ""
        row = parts[2] if len(parts) > 2 else ""
        cell = ""
        if isinstance(evidence, dict):
            worksheet = str(evidence.get("worksheet", worksheet))
            row = str(evidence.get("row", row))
            cell = str(evidence.get("cell", ""))
        elif isinstance(evidence, str) and "!" in evidence:
            worksheet, cell = evidence.split("!", 1)
        record = None
        if self._dataset is not None:
            record = next(
                (
                    item
                    for item in (
                        *self._dataset.budget_records,
                        *self._dataset.ged_records,
                    )
                    if item.record_id == record_id
                ),
                None,
            )
        original = current = ""
        if isinstance(evidence, dict):
            original = _display(evidence.get("original_value"))
            current = _display(evidence.get("current_value"))
        if record is not None and cell:
            field = next(
                (
                    name
                    for name, source_cell in record.cells.items()
                    if source_cell == cell
                ),
                None,
            )
            if field:
                original = _display(record.original.get(field))
                current = _display(record.current.get(field))
        basis = self._projection.get("basis", {}) if self._projection else {}
        workbook = (
            basis.get("budget_filename", "Budget Report")
            if role == "BUDGET"
            else (
                basis.get("ged_filename", "GED Report")
                if role == "GED"
                else "Recorded result"
            )
        )
        location = " · ".join(
            value
            for value in (
                worksheet,
                f"row {row}" if row else "",
                f"cell {cell}" if cell else "",
            )
            if value
        )
        return {
            "workbook": workbook,
            "location": location or "Recorded scope evidence",
            "original": original or "See recorded evidence",
            "current": current or "See recorded evidence",
        }

    def _open_selected_rule_evidence(self) -> None:
        index = self._rule_scope_table.currentIndex()
        if not index.isValid():
            return
        if self._rule_evidence_selector.count():
            record_id, field_name = self._rule_evidence_selector.currentData()
            self._open_source_record(record_id, field_name=field_name)

    def _findings_table(self, findings):
        headers = (
            "Severity",
            "Finding",
            "What happened",
            "Affected records",
            "Status",
            "Follow-up",
            "Source Evidence",
            "Explain",
            "Ask Fin",
        )
        model = QStandardItemModel(0, len(headers), self)
        model.setHorizontalHeaderLabels(list(headers))
        for item in findings:
            source_rows = []
            for detail in item.get("evidence_details", ()):
                label = (
                    f"{detail.get('source_role', 'Source')} · "
                    f"{detail.get('worksheet', '')} row {detail.get('row', '')}"
                )
                if detail.get("cell"):
                    label += f" · cell {detail['cell']}"
                if label not in source_rows:
                    source_rows.append(label)
            affected_vendors = [
                str(vendor)
                for vendor in item.get("explain_this", {})
                .get("supporting_evidence", {})
                .get("vendors", ())
                if vendor
            ]
            affected_scope = (
                f"{item['department_number']} / {item['account_number']}"
            )
            if affected_vendors:
                affected_scope += (
                    f" · {len(affected_vendors)} "
                    f"{'vendor' if len(affected_vendors) == 1 else 'vendors'}"
                )
            values = (
                item["severity"],
                item.get("business_title")
                or FINDING_TITLES.get(item["rule_id"], item["rule_name"]),
                item.get("what_happened") or item["explanation"],
                affected_scope,
                (
                    item.get("review_status")
                    or item.get("status")
                    or "New"
                ),
                (
                    "Human review required"
                    if item.get("review_required", True)
                    else "Review complete"
                ),
                "Open Evidence",
                "Explain This",
                "Ask Fin",
            )
            row = [QStandardItem(_display(value)) for value in values]
            row[0].setData(item, PROJECTION_ROLE)
            row[2].setToolTip(_display(values[2]))
            row[3].setToolTip(
                " · ".join(
                    part
                    for part in (
                        f"{item['department_number']} / {item['account_number']}",
                        ", ".join(affected_vendors),
                    )
                    if part
                )
            )
            row[6].setToolTip(
                "; ".join(source_rows) or "Recorded source evidence"
            )
            model.appendRow(row)
        proxy = _FindingsFilter(self)
        proxy.setSourceModel(model)
        proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        table = QTableView()
        table.setAccessibleName("Validation findings")
        table.setAccessibleDescription(
            "Select a finding row. In the Open Evidence, Explain, or Ask Fin "
            "column, press Enter to open that action."
        )
        table.setModel(proxy)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)
        table.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setWordWrap(False)
        header = table.horizontalHeader()
        fixed_widths = {
            0: 74,
            1: 155,
            3: 120,
            4: 86,
            5: 108,
            6: 105,
            7: 86,
            8: 68,
        }
        for column, width in fixed_widths.items():
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(column, width)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setDefaultSectionSize(42)
        table.setMinimumHeight(420)

        def activate_finding_action(index) -> None:
            if not index.isValid():
                return
            table.selectRow(index.row())
            if index.column() in {6, 7}:
                self._set_finding_explanation_visible(True)
            elif index.column() == 8:
                finding = index.siblingAtColumn(0).data(PROJECTION_ROLE)
                if finding:
                    self._ask_fin_for_finding(finding)

        table.clicked.connect(activate_finding_action)
        table.activated.connect(activate_finding_action)

        def update_count():
            count = proxy.rowCount()
            self._findings_count.setText(
                f"{count} {'finding' if count == 1 else 'findings'} shown"
            )

        self._findings_search.textChanged.connect(
            lambda text: (proxy.setFilterFixedString(text), update_count())
        )
        self._findings_severity.currentTextChanged.connect(
            lambda text: (proxy.set_severity(text), update_count())
        )
        self._findings_rule.currentTextChanged.connect(
            lambda text: (proxy.set_rule(text), update_count())
        )
        self._findings_status.currentTextChanged.connect(
            lambda text: (proxy.set_status(text), update_count())
        )
        self._findings_account.currentTextChanged.connect(
            lambda text: (proxy.set_account(text), update_count())
        )
        self._findings_vendor.currentTextChanged.connect(
            lambda text: (proxy.set_vendor(text), update_count())
        )
        self._findings_department.currentTextChanged.connect(
            lambda text: (proxy.set_department(text), update_count())
        )
        self._findings_review_required.currentTextChanged.connect(
            lambda text: (proxy.set_review_required(text), update_count())
        )
        update_count()
        self._findings_model = model
        self._findings_proxy = proxy
        table._finsight_model = model
        table._finsight_proxy = proxy
        table.selectionModel().currentRowChanged.connect(
            self._show_finding_detail
        )
        return table

    def _set_finding_explanation_visible(self, visible: bool) -> None:
        panel = getattr(self, "_finding_detail_panel", None)
        if panel is None:
            return
        panel.setVisible(visible)
        if visible:
            self._findings_splitter.setSizes((620, 620))
            panel.setFocus()
            self._announce(
                "Deterministic finding explanation opened with supporting evidence."
            )
        else:
            self._findings_splitter.setSizes((1200, 0))
            self._findings_result_table.setFocus()

    def _build_finding_detail_panel(self) -> QWidget:
        card, layout = _card()
        card.setAccessibleName("Selected finding evidence")
        header = QHBoxLayout()
        header.addWidget(_label("Explain This", "cardTitle"))
        header.addStretch(1)
        close = QPushButton("Close")
        close.setProperty("role", "quiet")
        close.setAccessibleName("Close finding explanation")
        close.clicked.connect(
            lambda: self._set_finding_explanation_visible(False)
        )
        header.addWidget(close)
        layout.addLayout(header)
        self._finding_title = _label("Select a finding.", "cardValue", wrap=True)
        layout.addWidget(self._finding_title)
        self._finding_badge = _label("", "statusPill", wrap=True)
        self._finding_badge.setMinimumHeight(28)
        layout.addWidget(self._finding_badge, 0, Qt.AlignmentFlag.AlignLeft)
        status_row = QHBoxLayout()
        status_row.addWidget(_label("Review status", "kvKey"))
        self._finding_status_control = QComboBox()
        self._finding_status_control.setAccessibleName(
            "Selected finding review status"
        )
        self._finding_status_control.addItems(
            ("New", "Acknowledged", "In Review", "Resolved", "Dismissed")
        )
        status_row.addWidget(self._finding_status_control)
        change_status = QPushButton("Update Status")
        change_status.setProperty("role", "secondary")
        change_status.setAccessibleName(
            "Save an audited review-status change"
        )
        change_status.clicked.connect(self._change_finding_status)
        status_row.addWidget(change_status)
        status_row.addStretch(1)
        layout.addLayout(status_row)
        layout.addWidget(_label("What happened", "cardTitle"))
        self._finding_what = _label("", "cardDetail", wrap=True)
        layout.addWidget(self._finding_what)
        layout.addWidget(_label("Why FinSight flagged it", "cardTitle"))
        self._finding_why_flagged = _label("", "cardDetail", wrap=True)
        layout.addWidget(self._finding_why_flagged)
        layout.addWidget(_label("Why it matters", "cardTitle"))
        self._finding_why_matters = _label("", "cardDetail", wrap=True)
        layout.addWidget(self._finding_why_matters)
        layout.addWidget(_label("Supporting evidence", "cardTitle"))
        self._finding_evidence = _label("", "cardDetail", wrap=True)
        self._finding_evidence.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByKeyboard
            | Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self._finding_evidence)
        self._finding_comparison = QTableWidget()
        self._finding_comparison.setAccessibleName(
            "Finding expected and actual evidence"
        )
        self._finding_comparison.verticalHeader().setVisible(False)
        self._finding_comparison.setColumnCount(3)
        self._finding_comparison.setHorizontalHeaderLabels(
            ("Evidence", "Original / expected", "Current / actual")
        )
        comparison_header = self._finding_comparison.horizontalHeader()
        comparison_header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed
        )
        comparison_header.resizeSection(0, 180)
        comparison_header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        comparison_header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self._finding_comparison.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._finding_comparison.setMinimumHeight(240)
        layout.addWidget(self._finding_comparison)
        layout.addWidget(
            _label("Contributing GED transactions", "cardTitle")
        )
        self._finding_transactions_empty = _label(
            "No contributing GED transactions are recorded for this finding.",
            "context",
            wrap=True,
        )
        layout.addWidget(self._finding_transactions_empty)
        self._finding_transactions = QTableWidget()
        self._finding_transactions.setAccessibleName(
            "Contributing GED transactions and source lineage"
        )
        self._finding_transactions.setColumnCount(8)
        self._finding_transactions.setHorizontalHeaderLabels(
            (
                "Source Row",
                "Vendor",
                "Journal / Invoice Ref",
                "Description",
                "Date",
                "Amount",
                "Workbook",
                "Worksheet",
            )
        )
        self._finding_transactions.verticalHeader().setVisible(False)
        self._finding_transactions.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._finding_transactions.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._finding_transactions.setHorizontalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        transaction_header = self._finding_transactions.horizontalHeader()
        for column, width in enumerate(
            (86, 170, 150, 230, 105, 115, 190, 135)
        ):
            transaction_header.setSectionResizeMode(
                column, QHeaderView.ResizeMode.Fixed
            )
            transaction_header.resizeSection(column, width)
        self._finding_transactions.setMinimumHeight(118)
        self._finding_transactions.setMaximumHeight(190)
        layout.addWidget(self._finding_transactions)
        layout.addWidget(_label("Non-binding next step", "cardTitle"))
        self._finding_next_step = _label("", "cardDetail", wrap=True)
        layout.addWidget(self._finding_next_step)
        self._finding_evidence_selector = QComboBox()
        self._finding_evidence_selector.setAccessibleName(
            "Select an affected source record for this finding"
        )
        layout.addWidget(self._finding_evidence_selector)
        self._open_finding = QPushButton("Show Evidence in Source Data")
        self._open_finding.setProperty("role", "primary")
        self._open_finding.setAccessibleName(
            "Show selected finding evidence in its source data table"
        )
        self._open_finding.clicked.connect(self._open_selected_finding)
        finding_actions = QHBoxLayout()
        finding_actions.addWidget(self._open_finding)
        self._finding_ask_fin = QPushButton("Ask Fin")
        self._finding_ask_fin.setProperty("role", "assistant")
        self._finding_ask_fin.setAccessibleName(
            "Ask Fin about the selected recorded finding"
        )
        self._finding_ask_fin.clicked.connect(
            self._ask_fin_for_selected_finding
        )
        finding_actions.addWidget(self._finding_ask_fin)
        finding_actions.addStretch(1)
        layout.addLayout(finding_actions)
        technical = QPushButton("Technical details")
        technical.setProperty("role", "quiet")
        technical.setCheckable(True)
        technical.setAccessibleName(
            "Show or hide technical rule and audit details"
        )
        technical_details = _label(
            "Rule version, configuration, evidence IDs, and audit attribution "
            "remain available under Rule Details.",
            "mono",
            wrap=True,
        )
        technical_details.setVisible(False)
        technical.toggled.connect(technical_details.setVisible)
        layout.addWidget(technical, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(technical_details)
        self._finding_technical_details = technical_details
        return card

    def _change_finding_status(self) -> None:
        finding = getattr(self, "_selected_finding", None)
        if finding is None or self._review is None:
            return
        target = self._finding_status_control.currentText()
        current = str(finding.get("review_status") or "New")
        if target == current:
            show_in_app_message(
                self,
                "Review status unchanged",
                f"This finding is already {target}.",
            )
            return
        prompt = InAppTextPromptDialog(
            "Update Finding Status",
            (
                f"Reason for changing this finding from {current} to "
                f"{target}:"
            ),
            parent=self,
            placeholder="Record the review rationale.",
            accept_text="Update Status",
            required_message=(
                "Enter a reason so the review-status change is auditable."
            ),
        )
        if prompt.exec() != QDialog.DialogCode.Accepted:
            self._finding_status_control.setCurrentText(current)
            return
        reason = prompt.text_value()
        try:
            self._c.financial_update_finding_status(
                self._review.review_id,
                str(finding["finding_id"]),
                target,
                reason=reason,
            )
            refreshed = self._c.financial_results(
                self._review.review_id
            )
        except Exception as exc:
            show_in_app_message(
                self,
                "Status not updated",
                _safe_error(exc),
                variant=DialogVariant.WARNING,
            )
            self._finding_status_control.setCurrentText(current)
            return
        self._projection = refreshed
        self._populate_results()
        self._open_results_tab(self._finding_list_tab)
        show_in_app_message(
            self,
            "Review status updated",
            f"The finding is now {target}. The original validation result "
            "was not changed.",
        )

    def _show_finding_detail(self, current, _previous) -> None:
        if not current.isValid() or not hasattr(self, "_finding_title"):
            return
        source_index = self._findings_proxy.mapToSource(current)
        finding = self._findings_model.item(source_index.row(), 0).data(
            PROJECTION_ROLE
        )
        if not finding:
            return
        self._selected_finding = finding
        explanation = dict(finding.get("explain_this") or {})
        self._finding_title.setText(
            str(
                finding.get("business_title")
                or explanation.get("business_title")
                or FINDING_TITLES.get(
                    finding["rule_id"], finding["rule_name"]
                )
            )
        )
        self._finding_badge.setText(
            f"{finding['severity']} severity · "
            f"{finding['department_number']} / {finding['account_number']}"
        )
        self._finding_status_control.setCurrentText(
            str(finding.get("review_status") or "New")
        )
        self._finding_what.setText(
            str(explanation.get("what_happened") or finding["explanation"])
        )
        self._finding_why_flagged.setText(
            str(
                explanation.get("why_flagged")
                or (
                    f"{finding['rule_name']} evaluated the recorded values "
                    f"against {finding['expected']}. The recorded result was "
                    f"{finding['actual']}."
                )
            )
        )
        self._finding_why_matters.setText(
            str(
                explanation.get("why_it_matters")
                or (
                    "This exception can affect the completeness, reliability, "
                    "or interpretation of the monthly financial review."
                )
            )
        )
        self._finding_next_step.setText(
            _review_guidance(finding)
        )
        technical = dict(explanation.get("technical_details") or {})
        self._finding_technical_details.setText(
            "\n".join(
                (
                    f"Rule: {technical.get('rule_id', finding['rule_id'])} · "
                    f"Version {technical.get('rule_version', finding.get('rule_version', 'Unavailable'))}",
                    f"Validation Run: {technical.get('validation_run_id', self._projection['run_id'])}",
                    f"Formula: {technical.get('calculation_formula', 'See recorded rule definition.')}",
                    f"Expected: {technical.get('expected', finding['expected'])}",
                    f"Actual: {technical.get('actual', finding['actual'])}",
                )
            )
        )
        evidence_details = list(finding.get("evidence_details", ()))
        source_lines = []
        if evidence_details:
            by_record: dict[str, list[dict[str, Any]]] = {}
            for detail in evidence_details:
                by_record.setdefault(
                    str(detail.get("record_id", "")), []
                ).append(detail)
            for record_id, details in by_record.items():
                source = self._source_record_details(record_id, details[0])
                if len(details) == 1:
                    location = source["location"]
                else:
                    worksheet = str(details[0].get("worksheet", ""))
                    row = str(details[0].get("row", ""))
                    location = " · ".join(
                        item
                        for item in (
                            worksheet,
                            f"row {row}" if row else "",
                            f"{len(details)} recorded fields",
                        )
                        if item
                    )
                source_lines.append(
                    f"{source['workbook']} · {location}"
                )
            if len(source_lines) > 6:
                remaining = len(source_lines) - 6
                source_lines = [
                    *source_lines[:6],
                    f"… and {remaining} more source record(s) retained in evidence.",
                ]
        else:
            for record_id in finding["source_records"]:
                details = self._source_record_details(
                    record_id,
                    next(iter(finding.get("evidence", ())), ""),
                )
                source_lines.append(
                    f"{details['workbook']} · {details['location']}"
                )
        supporting = dict(explanation.get("supporting_evidence") or {})
        recorded_values = [
            f"{name}: {supporting[name]}"
            for name in (
                "budget",
                "budget_atd",
                "ged_actual",
                "variance",
                "variance_percentage",
            )
            if name in supporting
        ]
        self._finding_evidence.setText(
            "\n".join((*source_lines, *recorded_values))
        )
        rows: list[tuple[str, Any, Any]] = [
            ("Condition", finding["expected"], finding["actual"]),
            (
                "Original / edited provenance",
                finding["original_or_edited_value"],
                "See cell-level evidence below",
            ),
            (
                "Source references",
                ", ".join(finding["evidence"]),
                f"{len(evidence_details)} recorded cell value(s)",
            ),
        ]
        transactions = list(
            explanation.get("contributing_transactions", ())
        )
        self._finding_transactions.setRowCount(len(transactions))
        for row, transaction in enumerate(transactions):
            values = (
                transaction.get("source_row", ""),
                transaction.get("vendor", "No vendor recorded"),
                (
                    transaction.get("journal_or_invoice_reference")
                    or transaction.get("journal_number")
                    or "No reference recorded"
                ),
                transaction.get("description", "")
                or "No description recorded",
                transaction.get("date", "") or "No date recorded",
                transaction.get("amount_label", "Unavailable"),
                (
                    transaction.get("workbook")
                    or transaction.get("source_file")
                    or "Unavailable"
                ),
                transaction.get("worksheet", "") or "Unavailable",
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(_display(value))
                cell.setToolTip(_display(value))
                self._finding_transactions.setItem(row, column, cell)
        self._finding_transactions_empty.setVisible(not transactions)
        self._finding_transactions.setVisible(bool(transactions))
        if (
            finding["rule_id"] == "CORE-03"
            and len(finding["source_records"]) >= 2
        ):
            reference_id, copy_id = finding["source_records"][:2]
            by_record_field = {
                (str(item.get("record_id")), str(item.get("field"))): item
                for item in evidence_details
            }
            fields = [
                field
                for record_id, field in by_record_field
                if record_id == reference_id
                and (copy_id, field) in by_record_field
            ]
            rows.append(
                (
                    "Duplicate records",
                    reference_id,
                    copy_id,
                )
            )
            for field in fields:
                reference = by_record_field[(reference_id, field)]
                copy = by_record_field[(copy_id, field)]
                rows.append(
                    (
                        field.replace("_", " ").title(),
                        reference.get("current_value"),
                        copy.get("current_value"),
                    )
                )
        else:
            for detail in evidence_details:
                source = self._source_record_details(
                    str(detail.get("record_id", "")), detail
                )
                rows.append(
                    (
                        (
                            f"{source['workbook']} · {source['location']} · "
                            f"{str(detail.get('field', '')).replace('_', ' ').title()}"
                        ),
                        detail.get("original_value"),
                        (
                            f"{_display(detail.get('current_value'))} "
                            f"({detail.get('value_origin', 'Original')})"
                        ),
                    )
                )
        self._finding_comparison.setRowCount(len(rows))
        for row, (label, original, current_value) in enumerate(rows):
            self._finding_comparison.setItem(row, 0, QTableWidgetItem(label))
            self._finding_comparison.setItem(
                row, 1, QTableWidgetItem(_display(original))
            )
            self._finding_comparison.setItem(
                row, 2, QTableWidgetItem(_display(current_value))
            )
        self._finding_comparison.resizeRowsToContents()
        finding_header = self._finding_comparison.horizontalHeader()
        finding_header.resizeSection(
            0, min(220, finding_header.sectionSizeHint(0))
        )
        self._finding_evidence_selector.clear()
        details_by_record = {
            str(item.get("record_id", "")): item for item in evidence_details
        }
        for record_id in finding["source_records"]:
            source = self._source_record_details(
                record_id, details_by_record.get(record_id, "")
            )
            detail = details_by_record.get(record_id, {})
            self._finding_evidence_selector.addItem(
                f"{source['workbook']} · {source['location']}",
                (
                    record_id,
                    str(detail.get("field", "")),
                ),
            )
        self._open_finding.setEnabled(
            self._finding_evidence_selector.count() > 0
        )
        self._finding_ask_fin.setEnabled(True)

    def _ask_fin_for_selected_finding(self) -> None:
        finding = getattr(self, "_selected_finding", None)
        if finding is not None:
            self._ask_fin_for_finding(finding)

    def _open_selected_finding(self) -> None:
        finding = getattr(self, "_selected_finding", None)
        if finding and self._finding_evidence_selector.count():
            record_id, field_name = self._finding_evidence_selector.currentData()
            self._open_source_record(record_id, field_name=field_name)

    def _open_source_record(
        self, record_id: str, *, field_name: str = ""
    ) -> None:
        role, _separator, remainder = record_id.partition(":")
        parts = remainder.rsplit(":", 1)
        try:
            source_row = int(parts[1]) if len(parts) == 2 else None
        except ValueError:
            source_row = None
        if role == "BUDGET":
            self._open_results_tab(self._budget_results_tab)
            table = getattr(self, "_budget_results_table", None)
            field_columns = {
                "account_number": 2,
                "account_name": 3,
                "bgt": 4,
                "atd": 4,
                "etc": 4,
                "eac": 6,
                "delta": 4,
            }
        elif role == "GED":
            self._open_results_tab(self._ged_transactions_tab)
            table = getattr(self, "_ged_results_table", None)
            field_columns = {
                "department_number": 1,
                "department_name": 2,
                "account_number": 3,
                "account_name": 4,
                "fiscal_period": 5,
                "journal_number": 6,
                "journal_date": 7,
                "vendor_name": 8,
                "journal_description": 9,
                "journal_line_description": 10,
                "amount": 11,
            }
        else:
            return
        if table is None or source_row is None:
            return
        model = table.model()
        for row in range(model.rowCount()):
            if model.index(row, 0).data() == source_row:
                column = field_columns.get(field_name, 0)
                table.setCurrentIndex(model.index(row, column))
                table.scrollTo(
                    model.index(row, column),
                    QAbstractItemView.ScrollHint.PositionAtCenter,
                )
                table.setFocus()
                return

    def _open_finding_for_table(
        self, table: QTableView, record_column: int
    ) -> None:
        index = table.currentIndex()
        if not index.isValid():
            show_in_app_message(
                self,
                "View Finding",
                "Select an affected source row first.",
            )
            return
        record_id = _display(
            table.model().index(index.row(), record_column).data()
        )
        finding = next(
            (
                item
                for item in self._projection["findings"]
                if record_id in item["source_records"]
            ),
            None,
        )
        if finding is None:
            show_in_app_message(
                self,
                "View Finding",
                "The selected row has no recorded finding.",
            )
            return
        self._open_results_tab(self._finding_list_tab)
        self._findings_search.setText(record_id)
        if self._findings_proxy.rowCount():
            self._findings_result_table.selectRow(0)

    def _populate_read_only_data_tab(self, widget, records, title):
        layout = self._replace_layout(widget)
        if not records:
            layout.addWidget(
                _label(
                    f"{title} cannot be reconstructed because the original saved-path "
                    "source is unavailable. The sealed validation ledger remains complete.",
                    "context",
                    wrap=True,
                )
            )
            layout.addStretch(1)
            return
        model, proxy = self._record_model(records)
        table = QTableView()
        table.setModel(proxy)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.resizeColumnsToContents()
        layout.addWidget(table)
        table._finsight_model = model
        table._finsight_proxy = proxy

    def _projection_table(self, headers, rows):
        model = QStandardItemModel(0, len(headers), self)
        model.setHorizontalHeaderLabels(list(headers))
        for values in rows:
            items = []
            for value in values:
                item = QStandardItem()
                display_value = value.text if isinstance(value, _ToneText) else value
                item.setData(
                    (
                        display_value
                        if isinstance(display_value, (int, float))
                        else _display(display_value)
                    ),
                    Qt.ItemDataRole.DisplayRole,
                )
                if isinstance(value, _ToneText) and value.tone:
                    item.setData(value.tone, FINANCIAL_TONE_ROLE)
                items.append(item)
            model.appendRow(items)
            header_index = {name: index for index, name in enumerate(headers)}
            source_index = header_index.get("Source Record")
            record_id = (
                _display(values[source_index])
                if source_index is not None and source_index < len(values)
                else ""
            )
            row_findings = (
                [
                    finding
                    for finding in self._projection.get("findings", ())
                    if record_id in finding["source_records"]
                ]
                if record_id and self._projection
                else []
            )
            if row_findings:
                for name in ("Validation Status", "Rule Badges", "Severity"):
                    column = header_index.get(name)
                    if column is not None:
                        font = QFont(items[column].font())
                        font.setBold(True)
                        items[column].setFont(font)
                        items[column].setToolTip(
                            "Affected record. Use View Finding for the complete "
                            "expected, actual, provenance, and recommended action."
                        )
                field_headers = {
                    "BUDGET": {
                        "C": "BGT",
                        "D": "ATD",
                        "E": "ETC",
                        "F": "EAC",
                        "G": "DELTA",
                    },
                    "GED": {
                        "A": "Department",
                        "C": "Account",
                        "E": "Fiscal Period",
                        "F": "Journal Number",
                        "G": "Journal Date",
                        "H": "Invoice Amount",
                        "O": "Amount",
                    },
                }
                role = record_id.partition(":")[0]
                for finding in row_findings:
                    for evidence in finding.get("evidence", ()):
                        if not isinstance(evidence, str):
                            continue
                        match = re.search(r"!([A-Z]+)(\d+)", evidence)
                        if not match:
                            continue
                        field_header = field_headers.get(role, {}).get(
                            match.group(1)
                        )
                        field_column = header_index.get(field_header)
                        if field_column is None:
                            continue
                        field_item = items[field_column]
                        font = QFont(field_item.font())
                        font.setBold(True)
                        field_item.setFont(font)
                        if not field_item.text():
                            field_item.setText("(blank) · Needs attention")
                        field_item.setToolTip(
                            f"{finding['rule_name']}: {finding['explanation']}\n"
                            f"Expected: {finding['expected']}\n"
                            f"Actual: {finding['actual']}"
                        )
        table = QTableView()
        table.setAccessibleName(f"Financial review table: {headers[0]}")
        table.setModel(model)
        table.setItemDelegate(_FinancialToneDelegate(table))
        table.verticalHeader().setVisible(False)
        if "Source Record" in headers:
            table.setColumnHidden(headers.index("Source Record"), True)
        table.setSortingEnabled(True)
        table.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.resizeColumnsToContents()
        table.setMinimumHeight(360)
        table._finsight_model = model
        return table

    def _build_complete_page(self):
        page, _content, layout = _content_page()
        self._complete_progress = ReviewProgress(6)
        layout.addWidget(self._complete_progress)
        layout.addStretch(1)
        card, card_layout = _card()
        card.setMinimumSize(680, 250)
        card.setMaximumWidth(760)
        self._complete_card = card
        card_layout.addWidget(_label("Financial Review Complete", "sectionHeader"))
        self._complete_summary = _label("", "sectionSub", wrap=True)
        self._complete_summary.setMinimumHeight(46)
        card_layout.addWidget(self._complete_summary)
        self._complete_preservation = _label(
            "The source fingerprints, reviewed-data version, corrections, audit "
            "history, protected rule versions, complete result ledger, findings, "
            "metrics, and completion timestamp are preserved.",
            "cardDetail",
            wrap=True,
        )
        self._complete_preservation.setMinimumHeight(54)
        card_layout.addWidget(self._complete_preservation)
        actions = QHBoxLayout()
        results = QPushButton("Open Saved Results")
        self._complete_results_button = results
        results.setProperty("role", "secondary")
        results.setAccessibleName("Open saved financial review results")
        results.clicked.connect(self._show_results)
        actions.addWidget(results)
        actions.addStretch(1)
        past = QPushButton("View Past Reviews")
        past.setProperty("role", "primary")
        past.setAccessibleName("View past financial reviews")
        past.clicked.connect(self.pastReviewsRequested.emit)
        actions.addWidget(past)
        card_layout.addLayout(actions)
        layout.addWidget(card, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)
        return page

    def open_review(self, review):
        self._review = review
        self._dataset = None
        self._projection = None
        self._pending.clear()
        self._context.setText(
            f"Active review: {review.period.label} · {review.status.value}"
        )
        if review.status is ReviewStatus.DRAFT:
            raise FinancialReviewError("Draft reviews must open at Upload Documents.")
        if review.status is ReviewStatus.DATA_UPLOADED:
            self._start_processing()
            return
        if review.status is ReviewStatus.DATA_REVIEWED:
            self._start_processing(resume_rules=True)
            return
        projection = self._c.financial_results(review.review_id)
        if projection is None:
            self._show_error(
                self._validation_error,
                "Saved validation results could not be found for this review.",
            )
            self._stack.setCurrentIndex(self.VALIDATING)
            return
        self._projection = projection
        self._read_only = True
        self._try_reconstruct_for_results()

    def _start_processing(self, *, resume_rules=False):
        self._stack.setCurrentIndex(self.PROCESSING)
        self._crumb.setText("Upload · Processing")
        self._reset_stages(self._process_labels, self._process_bar)
        self._process_index = 0
        self._process_finished = False
        self._set_stage(self._process_labels, self._process_bar, 0)
        self._process_timer.start()
        self._announce(
            "Preparing financial data. Reading the saved Budget and GED reports."
        )

        def done(dataset):
            self._dataset = dataset
            self._process_finished = True
            if resume_rules:
                self._process_timer.stop()
                self.rulesRequested.emit(self._review, self._dataset, False)

        def failed(exc):
            self._process_timer.stop()
            self._show_error(self._process_error, _safe_error(exc))

        self._c.prepare_financial_data_async(
            self._review.review_id, lambda _stage: None, done, failed
        )

    def _show_verify(self):
        self._stack.setCurrentIndex(self.VERIFY)
        self._crumb.setText("Verify Data")
        self._read_only = False
        self._populate_verify_tables()
        self._search.clear()
        self._row_filter.setCurrentText("All rows")
        self._edit_status.setText(
            f"{len(self._dataset.budget_details):,} Budget records and "
            f"{len(self._dataset.ged_transactions):,} GED transactions are ready for review."
        )
        self._update_attestation()
        self._search.setFocus()
        self._announce(
            f"Data review is ready. {len(self._dataset.budget_details)} Budget "
            f"records and {len(self._dataset.ged_transactions)} GED transactions "
            "are available for verification."
        )

    def _start_validation(self, confirmation):
        validation_review_id = self._review.review_id

        def is_current_validation_context() -> bool:
            return bool(
                self._review is not None
                and self._review.review_id == validation_review_id
                and self._c.active_review_id == validation_review_id
            )

        self._stack.setCurrentIndex(self.VALIDATING)
        self._crumb.setText("Validate")
        self._context.setText(
            f"Active review: {self._review.period.label} · "
            f"{self._review.status.value}"
        )
        self._reset_stages(self._validation_labels, self._validation_bar)
        self._validation_index = 0
        self._validation_finished = False
        self._set_stage(self._validation_labels, self._validation_bar, 0)
        self._validation_timer.start()
        included_rules = [
            item
            for item in (confirmation or {}).get("rules", ())
            if item.get("included")
        ]
        self._announce(
            "Deterministic validation started with the confirmed Rule Set: "
            f"{len(included_rules)} active rules."
        )

        def done(projection):
            if not is_current_validation_context():
                return
            self._projection = projection
            try:
                self._review = next(
                    (
                        review
                        for review in self._c.managed_reviews()
                        if review.review_id == self._review.review_id
                    ),
                    self._review,
                )
            except Exception:
                # The sealed result remains authoritative even if refreshing the
                # display-only lifecycle badge is temporarily unavailable.
                pass
            self._context.setText(
                f"Active review: {self._review.period.label} · "
                f"{self._review.status.value}"
            )
            self._validation_finished = True

        def failed(exc):
            if not is_current_validation_context():
                return
            self._validation_timer.stop()
            self._show_error(self._validation_error, _safe_error(exc))

        self._c.validate_financial_async(
            self._dataset,
            lambda _stage: None,
            done,
            failed,
            confirmation_id=str(confirmation["confirmation_id"]),
        )

    def start_validation_from_rules(
        self,
        review,
        dataset,
        *,
        revalidation=False,
        confirmation=None,
    ):
        """Resume the journey after the versioned Rules Repository step."""

        self._review = review
        self._dataset = dataset
        if confirmation is None:
            self._show_error(
                self._validation_error,
                "Confirm the proposed Rule Set before validation.",
            )
            return
        if revalidation and hasattr(self._c, "revalidate_financial_async"):
            self._start_revalidation()
            return
        self._start_validation(confirmation)

    def return_from_rules(self, *, revalidation: bool = False) -> None:
        if revalidation and self._projection is not None:
            self._show_results()
        elif self._dataset is not None:
            self._show_verify()

    def _show_results(self):
        if self._projection is None:
            return
        self._stack.setCurrentIndex(self.RESULTS)
        self._crumb.setText("Review Results")
        self._populate_results()
        self._announce(
            f"Financial review results are ready. "
            f"{self._projection['metrics']['findings']} findings were recorded."
        )

    def _try_reconstruct_for_results(self):
        self._stack.setCurrentIndex(self.RESULTS)
        self._crumb.setText("Review Results · Saved")

        def done(dataset):
            self._dataset = dataset
            self._show_results()

        def failed(_exc):
            self._dataset = None
            self._show_results()

        self._c.prepare_financial_data_async(
            self._review.review_id, lambda _stage: None, done, failed
        )

    def _complete_review(self):
        try:
            self._review = self._c.complete_financial_review(
                self._review.review_id
            )
            self._projection = self._c.financial_results(self._review.review_id)
        except Exception as exc:
            show_in_app_message(
                self,
                "Review not completed",
                _safe_error(exc),
                variant=DialogVariant.ERROR,
            )
            return
        completion = self._projection["completion"]
        self._complete_summary.setText(
            f"{self._projection['basis']['department_name']} · "
            f"{self._projection['basis']['reporting_period']}\n"
            f"Completed {completion['completed_at']} · "
            f"Validation Run {self._projection['run_id']}"
        )
        self._complete_progress.set_step(6, all_complete=True)
        self._stack.setCurrentIndex(self.COMPLETE)
        self._crumb.setText("Complete")
        self._context.setText(
            f"Active review: {self._review.period.label} · "
            f"{self._review.status.value}"
        )
        self._announce(
            "Financial review completed and saved. The recorded results are read-only."
        )

    def _delete_review(self) -> None:
        """Delete only the selected FinSight review after governed confirmation."""

        if self._review is None:
            return
        try:
            preview = self._c.prepare_review_disposal(self._review.review_id)
        except Exception as exc:
            show_in_app_message(
                self,
                "Review not deleted",
                _safe_error(exc),
                variant=DialogVariant.WARNING,
            )
            return
        token = getattr(preview, "confirmation_token", "")
        dialog = DeleteReviewDialog(self._review.period.label, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            if token:
                self._c.cancel_review_disposal(token)
            return
        try:
            self._c.confirm_review_disposal(self._review.review_id, token)
        except Exception as exc:
            show_in_app_message(
                self,
                "Review not deleted",
                _safe_error(exc),
                variant=DialogVariant.WARNING,
            )
            return
        show_in_app_message(
            self,
            "Review deleted",
            f"The {self._review.period.label} review was permanently deleted. "
            "The original external workbooks were not changed.",
        )
        self._review = None
        self._dataset = None
        self._projection = None
        self.pastReviewsRequested.emit()

    def _show_ask_fin(self):
        if self._review is None:
            show_in_app_message(
                self,
                "Ask Fin",
                "Create or open a review before starting a private Ask Fin "
                "conversation.",
            )
            return
        object_type = ""
        object_id = ""
        label = "Active review"
        if (
            self._projection is not None
            and self._results_tabs.currentWidget() is self._findings_tab
            and getattr(self, "_selected_finding", None)
        ):
            finding = self._selected_finding
            object_type = "finding"
            object_id = str(finding["finding_id"])
            label = str(
                finding.get("business_title")
                or FINDING_TITLES.get(
                    finding["rule_id"], finding["rule_name"]
                )
            )
        elif (
            self._projection is not None
            and self._results_tabs.currentWidget()
            is self._financial_analysis_tab
            and hasattr(self, "_account_selector")
            and self._analysis_tabs.currentWidget()
            in {self._account_analysis_tab, self._comparison_tab}
        ):
            account = self._selected_account_projection()
            if account is not None:
                object_type = "account"
                object_id = str(account["scope_key"])
                label = (
                    f"{account['account_number']} "
                    f"{account['account_name']}"
                )
        self._open_private_ask_fin(
            object_type=object_type,
            object_id=object_id,
            label=label,
        )

    def _ask_fin_for_finding(self, finding: dict[str, Any]) -> None:
        self._selected_finding = finding
        self._open_private_ask_fin(
            object_type="finding",
            object_id=str(finding["finding_id"]),
            label=str(
                finding.get("business_title")
                or FINDING_TITLES.get(
                    finding["rule_id"], finding["rule_name"]
                )
            ),
        )

    def _open_private_ask_fin(
        self,
        *,
        object_type: str = "",
        object_id: str = "",
        label: str = "Active review",
    ) -> None:
        if self._review is None:
            return
        self.askFinRequested.emit(
            self._review.review_id,
            object_type,
            object_id,
            label,
        )

    def _navigate_ask_fin_citation(self, citation: Any) -> None:
        target = dict(getattr(citation, "navigation_target", {}) or {})
        object_type = str(getattr(citation, "object_type", "")).casefold()
        object_id = str(getattr(citation, "object_id", ""))
        if object_type == "finding":
            self._open_finding_by_id(object_id)
        elif object_type == "account":
            self._open_account_drilldown(object_id)
        elif object_type == "vendor":
            self._open_results_tab(self._vendor_analysis_tab)
            table = getattr(self, "_vendor_analysis_table", None)
            if table is not None:
                for row in range(table.model().rowCount()):
                    index = table.model().index(row, 0)
                    if _display(index.data()) == object_id:
                        table.setCurrentIndex(index)
                        table.scrollTo(index)
                        table.setFocus()
                        break
        elif object_type in {"transaction", "budget-source"}:
            self._open_source_record(
                str(target.get("record_id") or object_id)
            )
        elif target.get("view") == "findings":
            self._open_results_tab(self._finding_list_tab)
        elif target.get("view") == "financial_analysis":
            tab = str(target.get("tab", "account"))
            self._open_results_tab(
                {
                    "account": self._account_analysis_tab,
                    "vendor": self._vendor_analysis_tab,
                    "department": self._department_analysis_tab,
                    "reconciliation": self._reconciliation_tab,
                }.get(tab, self._account_analysis_tab)
            )
        else:
            self._open_results_tab(self._overview_tab)

    def _announce(self, message: str) -> None:
        normalized = " ".join(message.split())
        if not normalized:
            return
        self._last_accessibility_announcement = normalized
        event = QAccessibleAnnouncementEvent(self, normalized)
        event.setPoliteness(QAccessible.AnnouncementPoliteness.Polite)
        QAccessible.updateAccessibility(event)

    @staticmethod
    def _show_error(label, message):
        label.setText(message)
        label.setAccessibleDescription(message)
        label.setVisible(True)

    def current_screen(self):
        return {
            self.PROCESSING: "processing",
            self.VERIFY: "verify_data",
            self.VALIDATING: "validation_progress",
            self.RESULTS: "financial_review_results",
            self.COMPLETE: "review_complete",
        }[self._stack.currentIndex()]

    def current_dataset(self):
        return self._dataset

    def current_projection(self):
        return self._projection


class FinancialReviewError(RuntimeError):
    pass
