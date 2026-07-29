# Implements: V2 FR-123/124/125/197, NFR-092 — Workflow 1 Welcome/Create/Past/Open desktop flow.
from __future__ import annotations

import calendar
import uuid
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import (
    QAccessible,
    QAccessibleAnnouncementEvent,
    QColor,
    QIntValidator,
    QKeySequence,
    QShortcut,
)
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from finsight.application.failure_contracts import safe_failure_message
from finsight.delivery.desktop.components import (
    AdaptiveSidebar,
    DeleteReviewDialog,
    IconBadge,
    NavItem,
    ReviewProgress,
)
from finsight.domain.review_management import ReviewStatus
from finsight.delivery.desktop.theme import tokens as t


WELCOME_TITLE = "FinSight"
WELCOME_SUBTITLE = "Your Personal Financial Review Assistant"
WELCOME_DESCRIPTION = (
    "Create monthly financial reviews, validate Budget and GED reports, identify "
    "exceptions early, and generate leadership-ready insights through one guided "
    "workflow."
)


def _label(text: str, role: str = "kvVal", *, wrap: bool = False) -> QLabel:
    value = QLabel(text)
    value.setProperty("role", role)
    value.setWordWrap(wrap)
    return value


class _PastReviewCard(QFrame):
    def __init__(
        self,
        review,
        on_open,
        on_delete=None,
        *,
        action_label: str = "Open Review",
        role: str = "reviewCard",
        result_summary=None,
        parent=None,
    ):
        super().__init__(parent)
        self.review_id = review.review_id
        self.setProperty("role", role)
        self.setAccessibleName(
            f"{review.period.label}, {review.status.value}, {review.disposition.value}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(t.SP_4, t.SP_4, t.SP_4, t.SP_4)
        layout.setSpacing(t.SP_2)
        top = QHBoxLayout()
        top.setSpacing(t.SP_2)
        title = _label(review.period.label, "cardTitle", wrap=True)
        top.addWidget(title)
        status = _label(review.status.value, "statusPill")
        status.setAccessibleName("Review Status: " + review.status.value)
        top.addWidget(status)
        disposition = _label(review.disposition.value, "statusPill")
        disposition.setAccessibleName("Disposition: " + review.disposition.value)
        top.addWidget(disposition)
        top.addStretch(1)
        open_button = QPushButton(action_label)
        open_button.setProperty("role", "primary")
        open_button.setAccessibleName(f"{action_label} for {review.period.label}")
        open_button.clicked.connect(lambda: on_open(review.review_id))
        top.addWidget(open_button)
        delete_button = QPushButton("Delete")
        delete_button.setProperty("role", "destructive")
        delete_button.setAccessibleName(
            f"Delete review for {review.period.label}"
        )
        delete_button.setVisible(on_delete is not None)
        if on_delete is not None:
            delete_button.clicked.connect(lambda: on_delete(review))
        top.addWidget(delete_button)
        layout.addLayout(top)
        context = _label(
            f"{review.context_label}  ·  Review ID {review.review_id}", "context", wrap=True
        )
        context.setAccessibleName(
            f"{review.context_label}. Review ID {review.review_id}"
        )
        layout.addWidget(context)
        if result_summary:
            metrics = result_summary["metrics"]
            result_context = _label(
                f"Overall status: {metrics['overall_status']}  ·  "
                f"Findings: {metrics['findings']}  ·  "
                f"Rules: {metrics['rules_passed']} passed / "
                f"{metrics['rules_failed']} failed / "
                f"{metrics['rules_not_evaluated']} not evaluated",
                "cardDetail",
                wrap=True,
            )
            result_context.setAccessibleName(result_context.text())
            layout.addWidget(result_context)
            completion = result_summary.get("completion")
            completed_at = (
                completion["completed_at"]
                if completion
                else result_summary["completed_at"]
            )
            coverage = _label(
                f"{metrics['budget_records']} Budget records  ·  "
                f"{metrics['ged_transactions']} GED transactions  ·  "
                f"Recorded {completed_at}",
                "context",
                wrap=True,
            )
            coverage.setAccessibleName(coverage.text())
            layout.addWidget(coverage)
        self.open_button = open_button
        self.delete_button = delete_button


class ReviewManagementView(QWidget):
    askFinRequested = Signal()
    """Review Management launch surface for the guided FinSight workflow.

    The view calls application services through ``AppController`` and contains no repository, SQL,
    workbook, validation, or financial logic.
    """

    sourceIntakeRequested = Signal(object)
    settingsRequested = Signal()
    ruleGovernanceRequested = Signal()

    WELCOME = 0
    CREATE = 1
    PAST = 2
    REVIEW = 3

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._c = controller
        self._current_review = None
        self._create_request_id = None
        self._past_cards = []
        self._return_focus = None
        self._last_accessibility_announcement = ""
        self._last_availability_state = None
        self._last_duplicate_announcement = ""
        self._action_cards_stacked = None
        self._review_summary_stacked = None
        self._review_actions_stacked = None
        self.setObjectName("ReviewManagement")
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self._sidebar = self._build_sidebar()
        self._sidebar.widthAdjusted.connect(
            lambda _width: self._resize_landing_geometry()
        )
        root.addWidget(self._sidebar)

        workspace = QWidget()
        workspace.setObjectName("Workflow1Workspace")
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)
        workspace_layout.addWidget(self._build_topbar())
        self._stack = QStackedWidget()
        self._welcome_page = self._build_welcome()
        self._create_page = self._build_create()
        self._past_page = self._build_past()
        self._review_page = self._build_review()
        for page in (
            self._welcome_page,
            self._create_page,
            self._past_page,
            self._review_page,
        ):
            self._stack.addWidget(page)
        workspace_layout.addWidget(self._stack, 1)
        root.addWidget(workspace, 1)

        self._shortcuts = []
        self._add_shortcut(QKeySequence(Qt.Key.Key_Escape), self.go_back)
        self._add_shortcut(QKeySequence("Alt+N"), self.show_create)
        self._add_shortcut(QKeySequence("Alt+P"), self.show_past)
        self._c.reviewManagementChanged.connect(self._on_management_changed)
        QWidget.setTabOrder(self._month, self._year)
        QWidget.setTabOrder(self._year, self._create_back)
        QWidget.setTabOrder(self._create_back, self._create_submit)
        self.show_welcome()

    def _add_shortcut(self, sequence: QKeySequence, action) -> None:
        shortcut = QShortcut(sequence, self)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(action)
        self._shortcuts.append(shortcut)

    def _build_sidebar(self) -> QWidget:
        side = AdaptiveSidebar()
        side.setObjectName("Workflow1Sidebar")
        side.setAccessibleName("FinSight primary navigation")
        layout = QVBoxLayout(side)
        layout.setContentsMargins(t.SP_3, t.SP_4, t.SP_3, t.SP_3)
        layout.setSpacing(t.SP_1)

        brand = _label("FinSight", "appTitle")
        brand.setAccessibleName("FinSight")
        layout.addWidget(brand)
        layout.addWidget(
            _label("Financial Review Assistant", "context", wrap=True)
        )
        layout.addSpacing(t.SP_4)
        layout.addWidget(_label("REVIEW WORKSPACE", "navGroup"))

        self._home_nav = NavItem("welcome", "Home")
        self._home_nav.activated.connect(lambda _key: self.show_welcome())
        layout.addWidget(self._home_nav)
        self._reviews_nav = NavItem("past_reviews", "Past Reviews")
        self._reviews_nav.activated.connect(lambda _key: self.show_past())
        layout.addWidget(self._reviews_nav)

        layout.addSpacing(t.SP_4)
        layout.addWidget(_label("APPLICATION", "navGroup"))
        self._rule_governance_nav = NavItem(
            "rule_governance", "Rule Governance"
        )
        self._rule_governance_nav.setAccessibleDescription(
            "Open protected-rule requests and independent decisions."
        )
        self._rule_governance_nav.activated.connect(
            lambda _key: self.ruleGovernanceRequested.emit()
        )
        layout.addWidget(self._rule_governance_nav)
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
            "Ask Fin can explain how to start or reopen a financial review."
        )
        self._ask_fin_nav.setToolTip("Get help with the FinSight review workflow.")
        self._ask_fin_nav.activated.connect(
            lambda _key: self._show_ask_fin_help()
        )
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
        layout.setSpacing(t.SP_3)
        self._shell_crumb = _label("Home", "context")
        self._shell_crumb.setAccessibleName("Current location")
        layout.addWidget(self._shell_crumb)
        layout.addStretch(1)
        self._shell_context = _label("No review selected", "context")
        self._shell_context.setAccessibleName("Active review context")
        layout.addWidget(self._shell_context)
        self._ask_fin_button = QPushButton("Ask Fin")
        self._ask_fin_button.setObjectName("HeaderAskFinButton")
        self._ask_fin_button.setProperty("role", "secondary")
        self._ask_fin_button.setAccessibleName("Ask Fin")
        self._ask_fin_button.setAccessibleDescription(
            "Ask Fin can explain how to start or reopen a financial review."
        )
        self._ask_fin_button.setToolTip(
            "Get help with the FinSight review workflow."
        )
        self._ask_fin_button.setEnabled(True)
        self._ask_fin_button.clicked.connect(self._show_ask_fin_help)
        layout.addWidget(self._ask_fin_button)
        return bar

    def _content_page(
        self, *, maximum_width: int = 1120
    ) -> tuple[QScrollArea, QWidget, QVBoxLayout]:
        scroll = QScrollArea()
        scroll.setObjectName("Workflow1Page")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        holder = QWidget()
        holder.setObjectName("Workflow1PageCanvas")
        holder.setMinimumWidth(0)
        outer = QHBoxLayout(holder)
        outer.setContentsMargins(t.SP_6, t.SP_5, t.SP_6, t.SP_6)
        outer.setSpacing(0)
        content = QWidget()
        content.setObjectName("Workflow1Content")
        content.setMinimumWidth(0)
        content.setMaximumWidth(maximum_width)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(t.SP_4)
        outer.addWidget(content, 1, Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(holder)
        return scroll, content, content_layout

    @staticmethod
    def _surface_card(
        *, role: str = "surfaceCard"
    ) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setProperty("role", role)
        card.setMinimumWidth(0)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        layout.setSpacing(t.SP_3)
        return card, layout

    def _build_action_card(
        self,
        *,
        icon_name: str,
        icon_tone: str,
        object_name: str,
        title: str,
        description: str,
        button: QPushButton,
    ) -> QFrame:
        card, layout = self._surface_card(role="actionCard")
        card.setObjectName(object_name)
        card.setMinimumHeight(260)
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        layout.setContentsMargins(t.SP_5, t.SP_4, t.SP_5, t.SP_4)
        layout.setSpacing(t.SP_2)
        badge = IconBadge(
            icon_name,
            tone=icon_tone,
            accessible_name=f"{title} icon",
        )
        layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignHCenter)
        title_label = _label(title, "landingCardTitle", wrap=True)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setAccessibleName(title)
        layout.addWidget(title_label)
        description_label = _label(
            description, "landingCardDescription", wrap=True
        )
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setAccessibleName(description)
        description_label.setMinimumHeight(30)
        layout.addWidget(description_label)
        layout.addStretch(1)
        button.setMinimumHeight(40)
        button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(button)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(24, 35, 52, 38))
        card.setGraphicsEffect(shadow)
        card._landing_badge = badge
        card._landing_title = title_label
        card._landing_description = description_label
        return card

    def _build_progress(self) -> QFrame:
        self._workflow_progress = ReviewProgress(0)
        return self._workflow_progress

    def _build_welcome(self) -> QWidget:
        page, content, layout = self._content_page()
        page.setObjectName("FinSightLandingPage")
        self._welcome_content = content
        hero = QFrame()
        hero.setObjectName("LandingHero")
        hero.setProperty("role", "welcomeHero")
        hero.setAccessibleName("FinSight welcome")
        hero.setMinimumHeight(640)
        hero.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(t.SP_6, t.SP_6, t.SP_6, t.SP_6)
        hero_layout.setSpacing(0)
        self._landing_top_spacer = QSpacerItem(
            0,
            56,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Fixed,
        )
        hero_layout.addItem(self._landing_top_spacer)
        self._welcome_title = _label(WELCOME_TITLE, "landingTitle", wrap=True)
        self._welcome_title.setObjectName("LandingTitle")
        self._welcome_title.setAccessibleName(WELCOME_TITLE)
        self._welcome_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(self._welcome_title)
        hero_layout.addSpacing(t.SP_1)
        self._welcome_subtitle = _label(
            WELCOME_SUBTITLE, "landingSubtitle", wrap=True
        )
        self._welcome_subtitle.setObjectName("LandingSubtitle")
        self._welcome_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._welcome_subtitle.setAccessibleName(WELCOME_SUBTITLE)
        hero_layout.addWidget(self._welcome_subtitle)
        hero_layout.addSpacing(t.SP_4)
        self._welcome_description = _label(
            WELCOME_DESCRIPTION,
            "landingDescription",
            wrap=True,
        )
        self._welcome_description.setObjectName("LandingDescription")
        self._welcome_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._welcome_description.setMaximumWidth(690)
        self._welcome_description.setAccessibleName(WELCOME_DESCRIPTION)
        # QLabel's wrapped height-for-width can lag the final desktop width while
        # the page is first laid out. Reserve the two-line copy block explicitly
        # so the action cards can never occlude it at supported window sizes.
        self._welcome_description.setMinimumHeight(56)
        hero_layout.addWidget(
            self._welcome_description, 0, Qt.AlignmentFlag.AlignHCenter
        )
        hero_layout.addSpacing(t.SP_5)
        self._create_button = QPushButton("Create New Review")
        self._create_button.setObjectName("CreateNewReviewButton")
        self._create_button.setProperty("role", "primary")
        self._create_button.setAccessibleName("Create New Review")
        self._create_button.clicked.connect(self.show_create)
        self._past_button = QPushButton("Open Past Review")
        self._past_button.setObjectName("OpenPastReviewButton")
        self._past_button.setProperty("role", "secondary")
        self._past_button.setAccessibleName("Open Past Review")
        self._past_button.clicked.connect(self.show_past)

        self._create_action_card = self._build_action_card(
            icon_name="create_review",
            icon_tone="create",
            object_name="CreateReviewActionCard",
            title="Create New Review",
            description="Start a new monthly financial review.",
            button=self._create_button,
        )
        self._past_action_card = self._build_action_card(
            icon_name="open_review",
            icon_tone="open",
            object_name="OpenPastReviewActionCard",
            title="Open Past Review",
            description="Open and continue a previous review.",
            button=self._past_button,
        )
        self._action_grid = QGridLayout()
        self._action_grid.setContentsMargins(t.SP_2, t.SP_1, t.SP_2, t.SP_2)
        self._action_grid.setHorizontalSpacing(t.SP_5 - t.SP_1)
        self._action_grid.setVerticalSpacing(t.SP_3)
        self._action_grid.addWidget(self._create_action_card, 0, 0)
        self._action_grid.addWidget(self._past_action_card, 0, 1)
        self._action_grid.setColumnStretch(0, 1)
        self._action_grid.setColumnStretch(1, 1)
        self._action_holder = QWidget()
        self._action_holder.setObjectName("LandingActions")
        self._action_holder.setMinimumWidth(660)
        self._action_holder.setMaximumWidth(760)
        self._action_holder.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self._action_holder.setLayout(self._action_grid)
        hero_layout.addWidget(
            self._action_holder, 0, Qt.AlignmentFlag.AlignHCenter
        )
        hero_layout.addStretch(1)
        layout.addWidget(hero, 1)
        return page

    def _build_create(self) -> QWidget:
        page, _content, layout = self._content_page()
        self._create_page_back = QPushButton("← Back to Welcome")
        self._create_page_back.setProperty("role", "quiet")
        self._create_page_back.setAccessibleName("Back to Welcome")
        self._create_page_back.clicked.connect(self.show_welcome)
        layout.addWidget(
            self._create_page_back, 0, Qt.AlignmentFlag.AlignLeft
        )
        layout.addWidget(self._build_progress())
        self._create_title = _label(
            "Create Review — Reporting Period", "sectionHeader", wrap=True
        )
        self._create_title.setAccessibleName("Create New Review")
        layout.addWidget(self._create_title)
        layout.addWidget(
            _label(
                "Select the reporting month and four-digit year for this review.",
                "sectionSub",
                wrap=True,
            )
        )
        form_card, form_layout = self._surface_card()
        form_card.setMaximumWidth(720)
        form_card.setAccessibleName("Reporting period form")
        form_layout.addWidget(_label("Review period", "cardTitle"))
        form_layout.addWidget(
            _label(
                "The reporting period keeps each monthly review distinct.",
                "cardDetail",
                wrap=True,
            )
        )
        form = QGridLayout()
        form.setHorizontalSpacing(t.SP_4)
        form.setVerticalSpacing(t.SP_3)
        month_label = QLabel("Reporting month")
        month_label.setProperty("role", "kvKey")
        self._month = QComboBox()
        self._month.setAccessibleName("Reporting month")
        self._month.addItem("Select month", None)
        for month in range(1, 13):
            self._month.addItem(calendar.month_name[month], month)
        self._month.setMinimumHeight(48)
        month_label.setBuddy(self._month)
        form.addWidget(month_label, 0, 0)
        form.addWidget(self._month, 0, 1)
        year_label = QLabel("Reporting year")
        year_label.setProperty("role", "kvKey")
        self._year = QLineEdit()
        self._year.setAccessibleName("Reporting year")
        self._year.setPlaceholderText("YYYY")
        self._year.setMaxLength(4)
        self._year.setValidator(QIntValidator(1000, 9999, self._year))
        self._year.setMinimumHeight(48)
        year_label.setBuddy(self._year)
        form.addWidget(year_label, 1, 0)
        form.addWidget(self._year, 1, 1)
        form.setColumnStretch(1, 1)
        form_layout.addLayout(form)
        preview, preview_layout = self._surface_card(role="periodPreview")
        preview_layout.setContentsMargins(t.SP_4, t.SP_3, t.SP_4, t.SP_3)
        self._period_preview = _label(
            "Reporting period: Not selected", "kvVal", wrap=True
        )
        self._period_preview.setAccessibleName("Selected reporting period")
        preview_layout.addWidget(self._period_preview)
        form_layout.addWidget(preview)
        self._duplicate_warning = _label("", "context", wrap=True)
        self._duplicate_warning.setAccessibleName("Duplicate reporting period warning")
        self._duplicate_warning.setVisible(False)
        form_layout.addWidget(self._duplicate_warning)
        self._create_error = _label("", "error", wrap=True)
        self._create_error.setAccessibleName("Create review validation message")
        self._create_error.setVisible(False)
        form_layout.addWidget(self._create_error)
        row = QHBoxLayout()
        self._create_back = QPushButton("Cancel")
        self._create_back.setProperty("role", "secondary")
        self._create_back.setAccessibleName("Cancel and return to Welcome")
        self._create_back.clicked.connect(self.show_welcome)
        row.addWidget(self._create_back)
        row.addStretch(1)
        self._create_submit = QPushButton("Create Review")
        self._create_submit.setProperty("role", "primary")
        self._create_submit.setAccessibleName("Create Review")
        self._create_submit.clicked.connect(self._submit_create)
        row.addWidget(self._create_submit)
        form_layout.addLayout(row)
        layout.addWidget(form_card, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addStretch(1)
        self._create_form_card = form_card
        self._month.currentIndexChanged.connect(self._update_period_preview)
        self._year.textChanged.connect(self._update_period_preview)
        return page

    def _build_past(self) -> QWidget:
        page, content, root = self._content_page()
        self._past_holder = content
        self._past_scroll = page
        header = QHBoxLayout()
        titles = QVBoxLayout()
        self._past_title = _label("Past Reviews", "sectionHeader")
        self._past_title.setAccessibleName("Past Reviews")
        titles.addWidget(self._past_title)
        titles.addWidget(
            _label(
                "Open a saved review by its exact Review ID. Filters never change stored reviews.",
                "sectionSub",
                wrap=True,
            )
        )
        header.addLayout(titles, 1)
        self._past_back = QPushButton("← Back to Welcome")
        self._past_back.setProperty("role", "secondary")
        self._past_back.setAccessibleName("Back to Welcome")
        self._past_back.clicked.connect(self.show_welcome)
        header.addWidget(self._past_back, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(header)

        filter_card, filter_layout = self._surface_card()
        filter_card.setMaximumWidth(520)
        filter_row = QHBoxLayout()
        filter_row.setSpacing(t.SP_3)
        filter_label = QLabel("Review Status")
        filter_label.setProperty("role", "kvKey")
        self._status_filter = QComboBox()
        self._status_filter.setAccessibleName("Filter past reviews by Review Status")
        self._status_filter.addItem("All current statuses", None)
        for status in ReviewStatus:
            self._status_filter.addItem(status.value, status)
        filter_label.setBuddy(self._status_filter)
        filter_row.addWidget(filter_label)
        filter_row.addWidget(self._status_filter, 1)
        filter_layout.addLayout(filter_row)
        root.addWidget(filter_card, 0, Qt.AlignmentFlag.AlignLeft)
        self._past_message = _label("", "error", wrap=True)
        self._past_message.setAccessibleName("Past reviews message")
        self._past_message.setVisible(False)
        root.addWidget(self._past_message)
        root.addWidget(_label("Saved Reviews", "cardTitle"))
        self._past_container = QWidget()
        self._past_container.setMinimumWidth(0)
        self._past_container.setAccessibleName("Saved reviews")
        self._past_list = QVBoxLayout(self._past_container)
        self._past_list.setContentsMargins(0, 0, 0, 0)
        self._past_list.setSpacing(t.SP_2)
        self._past_list.setAlignment(Qt.AlignmentFlag.AlignTop)
        root.addWidget(self._past_container)
        root.addStretch(1)
        self._status_filter.currentIndexChanged.connect(self._refresh_past)
        return page

    def _build_review(self) -> QWidget:
        page, _content, layout = self._content_page()
        header = QHBoxLayout()
        titles = QVBoxLayout()
        self._review_title = _label("Review Workspace", "sectionHeader")
        self._review_title.setAccessibleName("Review Workspace")
        titles.addWidget(self._review_title)
        self._review_period = _label("", "cardTitle")
        self._review_period.setAccessibleName("Reporting period")
        titles.addWidget(self._review_period)
        header.addLayout(titles, 1)
        self._review_status = _label("", "statusPill")
        self._review_status.setAccessibleName("Review Status")
        header.addWidget(
            self._review_status, 0, Qt.AlignmentFlag.AlignTop
        )
        layout.addLayout(header)

        summary = QGridLayout()
        summary.setContentsMargins(0, 0, 0, 0)
        summary.setHorizontalSpacing(t.SP_3)
        summary.setVerticalSpacing(t.SP_3)
        lifecycle_card, lifecycle_layout = self._surface_card()
        lifecycle_layout.addWidget(_label("Lifecycle", "cardLabel"))
        self._review_disposition = _label("", "statusPill")
        self._review_disposition.setAccessibleName("Disposition")
        lifecycle_layout.addWidget(
            self._review_disposition, 0, Qt.AlignmentFlag.AlignLeft
        )
        context_card, context_layout = self._surface_card()
        context_layout.addWidget(_label("Review Context", "cardLabel"))
        self._review_context = _label("", "cardValue", wrap=True)
        self._review_context.setAccessibleName("Review Context")
        context_layout.addWidget(self._review_context)
        publication_card, publication_layout = self._surface_card()
        publication_layout.addWidget(_label("Publication Status", "cardLabel"))
        self._publication_status = _label("", "cardValue", wrap=True)
        self._publication_status.setAccessibleName("Publication Status")
        publication_layout.addWidget(self._publication_status)
        self._review_summary_cards = (
            lifecycle_card,
            context_card,
            publication_card,
        )
        self._review_summary = summary
        summary.addWidget(lifecycle_card, 0, 0)
        summary.addWidget(context_card, 0, 1)
        summary.addWidget(publication_card, 0, 2)
        for column in range(3):
            summary.setColumnStretch(column, 1)
        layout.addLayout(summary)

        details_card, details_layout = self._surface_card()
        details_layout.addWidget(_label("Review Details", "cardTitle"))
        details = QGridLayout()
        details.setHorizontalSpacing(t.SP_5)
        details.setVerticalSpacing(t.SP_2)
        details.addWidget(_label("Financial Status", "kvKey"), 0, 0)
        self._financial_status = _label("", "kvVal", wrap=True)
        self._financial_status.setAccessibleName("Financial Status")
        details.addWidget(self._financial_status, 0, 1)
        details.addWidget(_label("Review ID", "kvKey"), 1, 0)
        self._review_id = _label("", "mono", wrap=True)
        self._review_id.setAccessibleName("Review ID")
        self._review_id.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        self._review_id.setMinimumWidth(0)
        details.addWidget(self._review_id, 1, 1)
        details.setColumnStretch(1, 1)
        details_layout.addLayout(details)
        layout.addWidget(details_card)
        self._saved_message = _label(
            "This review is saved. You can safely close FinSight and return to it from View Past Reviews.",
            "context",
            wrap=True,
        )
        self._saved_message.setAccessibleName("Review persistence confirmation")
        layout.addWidget(self._saved_message)
        row = QGridLayout()
        row.setHorizontalSpacing(t.SP_2)
        row.setVerticalSpacing(t.SP_2)
        self._review_home = QPushButton("← Back to Welcome")
        self._review_home.setProperty("role", "secondary")
        self._review_home.setAccessibleName("Back to Welcome")
        self._review_home.clicked.connect(self.show_welcome)
        row.addWidget(self._review_home, 0, 0)
        self._review_past = QPushButton("View Past Reviews")
        self._review_past.setProperty("role", "secondary")
        self._review_past.setAccessibleName("View Past Reviews")
        self._review_past.clicked.connect(self.show_past)
        row.addWidget(self._review_past, 0, 2)
        self._review_continue = QPushButton("Continue to Upload && Extraction")
        self._review_continue.setProperty("role", "primary")
        self._review_continue.setAccessibleName(
            "Continue to Upload and Extraction"
        )
        self._review_continue.clicked.connect(
            lambda: self.sourceIntakeRequested.emit(self._current_review)
            if self._current_review is not None
            else None
        )
        row.addWidget(self._review_continue, 0, 3)
        self._review_delete = QPushButton("Delete Review")
        self._review_delete.setProperty("role", "destructive")
        self._review_delete.setAccessibleName("Permanently delete this review")
        self._review_delete.clicked.connect(
            lambda: self._delete_review(self._current_review)
            if self._current_review is not None
            else None
        )
        row.addWidget(self._review_delete, 0, 4)
        row.setColumnStretch(1, 1)
        layout.addLayout(row)
        self._review_actions = row
        layout.addStretch(1)
        return page

    # ---- navigation / interaction ----
    def _announce(
        self,
        message: str,
        *,
        assertive: bool = False,
        target: QWidget | None = None,
    ) -> None:
        """Expose a concise state change through Qt's native accessibility event channel."""

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

    def _show_ask_fin_help(self) -> None:
        self.askFinRequested.emit()

    @staticmethod
    def _focus_after_navigation(widget: QWidget) -> None:
        """Restore focus after both the page swap and the initiating key event complete."""

        widget.setFocus()
        QTimer.singleShot(0, widget, widget.setFocus)

    @staticmethod
    def _safe_error_message(error: BaseException) -> str:
        return safe_failure_message(
            error,
            fallback_correlation_id="corr_ui_" + uuid.uuid4().hex,
        )

    def _set_shell_state(self, location: str, navigation_key: str) -> None:
        self._shell_crumb.setText(location)
        landing = location == "Home"
        self._shell_crumb.setVisible(not landing)
        self._shell_context.setVisible(not landing)
        self._home_nav.setChecked(navigation_key == "welcome")
        self._reviews_nav.setChecked(navigation_key == "past_reviews")
        self._rule_governance_nav.setChecked(False)
        self._settings_nav.setChecked(False)
        if self._current_review is None:
            self._shell_context.setText("No review selected")
            return
        self._shell_context.setText(
            f"Active review: {self._current_review.period.label}  ·  "
            f"{self._current_review.status.value}"
        )

    def _set_past_availability(self, enabled: bool, explanation: str) -> None:
        self._past_button.setEnabled(enabled)
        self._reviews_nav.setEnabled(enabled)
        description = explanation or "Open saved reviews."
        self._past_button.setAccessibleDescription(description)
        self._reviews_nav.setAccessibleDescription(description)
        self._past_action_card.setProperty(
            "availability", "enabled" if enabled else "disabled"
        )
        self._past_action_card.style().unpolish(self._past_action_card)
        self._past_action_card.style().polish(self._past_action_card)
        # A disabled QPushButton can retain its pre-scale geometry after a
        # process-wide font or appearance change. Re-polish the control and
        # invalidate its card so the disabled state receives the same current
        # font metrics as the enabled action beside it.
        self._past_button.style().unpolish(self._past_button)
        self._past_button.style().polish(self._past_button)
        self._past_button.setMinimumHeight(
            self._past_button.minimumSizeHint().height()
        )
        self._past_button.updateGeometry()
        self._past_action_card.layout().invalidate()
        self._past_action_card.layout().activate()

    def _reflow_action_cards(self, stacked: bool) -> None:
        if stacked == self._action_cards_stacked:
            return
        self._action_grid.removeWidget(self._create_action_card)
        self._action_grid.removeWidget(self._past_action_card)
        if stacked:
            self._landing_top_spacer.changeSize(
                0,
                24,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Fixed,
            )
            self._action_holder.setMinimumWidth(0)
            self._action_holder.setMaximumWidth(620)
            self._action_grid.addWidget(self._create_action_card, 0, 0)
            self._action_grid.addWidget(self._past_action_card, 1, 0)
            self._action_grid.setColumnStretch(0, 1)
            self._action_grid.setColumnStretch(1, 0)
        else:
            self._landing_top_spacer.changeSize(
                0,
                56,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Fixed,
            )
            self._action_holder.setMinimumWidth(660)
            self._action_holder.setMaximumWidth(760)
            self._action_grid.addWidget(self._create_action_card, 0, 0)
            self._action_grid.addWidget(self._past_action_card, 0, 1)
            self._action_grid.setColumnStretch(0, 1)
            self._action_grid.setColumnStretch(1, 1)
        self._welcome_content.layout().invalidate()
        self._action_cards_stacked = stacked

    def _resize_landing_copy(self) -> None:
        # Reserve the nested page/hero margins plus a vertical-scrollbar gutter
        # so 200% text never creates a horizontal scroll path.
        available = (
            self.width()
            - self._sidebar.width()
            - (t.SP_6 * 4)
            - t.SP_5
        )
        self._welcome_description.setFixedWidth(
            min(690, max(240, available))
        )
        self._welcome_description.updateGeometry()

    def _resize_landing_geometry(self) -> None:
        self._resize_landing_copy()
        if self._action_cards_stacked is False:
            spacer_height = 56
            if self.height() < 940:
                spacer_height = 28
            if self.height() < 880:
                spacer_height = 16
            self._landing_top_spacer.changeSize(
                0,
                spacer_height,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Fixed,
            )
            available = (
                self.width()
                - self._sidebar.width()
                - (t.SP_6 * 4)
            )
            width = min(760, max(660, available))
            self._action_holder.setMinimumWidth(width)
            self._action_holder.setMaximumWidth(width)
            self._welcome_content.layout().invalidate()

    def _reflow_review_summary(self, stacked: bool) -> None:
        if stacked == self._review_summary_stacked:
            return
        for card in self._review_summary_cards:
            self._review_summary.removeWidget(card)
        if stacked:
            for row, card in enumerate(self._review_summary_cards):
                self._review_summary.addWidget(card, row, 0)
            self._review_summary.setColumnStretch(0, 1)
            self._review_summary.setColumnStretch(1, 0)
            self._review_summary.setColumnStretch(2, 0)
        else:
            for column, card in enumerate(self._review_summary_cards):
                self._review_summary.addWidget(card, 0, column)
                self._review_summary.setColumnStretch(column, 1)
        self._review_summary_stacked = stacked

    def _reflow_review_actions(self, stacked: bool) -> None:
        if stacked == self._review_actions_stacked:
            return
        for control in (
            self._review_home,
            self._review_past,
            self._review_continue,
            self._review_delete,
        ):
            self._review_actions.removeWidget(control)
        if stacked:
            self._review_actions.addWidget(self._review_home, 0, 0)
            self._review_actions.addWidget(self._review_past, 1, 0)
            self._review_actions.addWidget(self._review_continue, 2, 0)
            self._review_actions.addWidget(self._review_delete, 3, 0)
            self._review_actions.setColumnStretch(1, 0)
        else:
            self._review_actions.addWidget(self._review_home, 0, 0)
            self._review_actions.addWidget(self._review_past, 0, 2)
            self._review_actions.addWidget(self._review_continue, 0, 3)
            self._review_actions.addWidget(self._review_delete, 0, 4)
            self._review_actions.setColumnStretch(1, 1)
        self._review_actions_stacked = stacked

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        compact = self.width() < 1080
        self._reflow_action_cards(compact)
        self._resize_landing_geometry()
        self._reflow_review_summary(compact)
        self._reflow_review_actions(compact)

    def show_welcome(self) -> None:
        self._refresh_current_review()
        try:
            availability = self._c.review_management_availability()
            self._create_button.setEnabled(availability.can_create)
            reason = availability.explanation
            self._set_past_availability(availability.can_view_past, reason)
            can_govern_rules = any(
                role
                in {
                    "Rule Administrator",
                    "Financial Control Approver",
                }
                for role in availability.role_labels
            )
            self._rule_governance_nav.setEnabled(can_govern_rules)
            self._rule_governance_nav.setToolTip(
                "Open protected-rule governance."
                if can_govern_rules
                else "A Rule Administrator or Financial Control Approver role is required."
            )
            availability_state = (
                availability.can_create,
                availability.can_view_past,
                reason,
            )
            if availability_state != self._last_availability_state:
                availability_message = reason or (
                    "Saved reviews are available. Create New Review and View Past Reviews "
                    "are available."
                )
                self._announce(
                    availability_message,
                    target=self._past_button,
                )
                self._last_availability_state = availability_state
        except Exception as exc:
            # Manifest/store failures are deliberately non-sensitive at the UI boundary.
            self._create_button.setEnabled(False)
            self._rule_governance_nav.setEnabled(False)
            message = self._safe_error_message(exc)
            self._set_past_availability(False, message)
            availability_state = (False, False, message)
            if availability_state != self._last_availability_state:
                self._announce(
                    message, assertive=True, target=self._past_button
                )
                self._last_availability_state = availability_state
        self._stack.setCurrentIndex(self.WELCOME)
        self._set_shell_state("Home", "welcome")
        QTimer.singleShot(
            0, lambda: self._reflow_action_cards(self.width() < 1080)
        )
        self._focus_after_navigation(self._return_focus or self._create_button)
        self._return_focus = None

    def show_create(self) -> None:
        if not self._create_button.isEnabled():
            return
        self._return_focus = self._create_button
        self._create_request_id = uuid.uuid4().hex
        self._month.setCurrentIndex(0)
        self._year.clear()
        self._create_error.clear()
        self._create_error.setVisible(False)
        self._duplicate_warning.clear()
        self._duplicate_warning.setVisible(False)
        self._create_submit.setEnabled(True)
        self._stack.setCurrentIndex(self.CREATE)
        self._set_shell_state("Create Review", "welcome")
        self._focus_after_navigation(self._month)
        self._announce(
            "Create New Review. Create is the current stage of seven. "
            "Select a reporting month and year.",
            target=self._create_title,
        )

    def show_past(self) -> None:
        if self._stack.currentIndex() == self.WELCOME and not self._past_button.isEnabled():
            return
        self._return_focus = self._past_button
        self._refresh_current_review()
        self._stack.setCurrentIndex(self.PAST)
        self._set_shell_state("Past Reviews", "past_reviews")
        self._status_filter.blockSignals(True)
        self._status_filter.setCurrentIndex(0)
        self._status_filter.blockSignals(False)
        self._refresh_past()
        self._focus_after_navigation(self._status_filter)

    def _update_period_preview(self) -> None:
        month = self._month.currentData()
        year = self._year.text().strip()
        if month is not None and len(year) == 4:
            self._period_preview.setText(
                f"Reporting period: {calendar.month_name[int(month)]} {year}"
            )
            try:
                count = self._c.managed_review_period_count(int(month), int(year))
            except Exception:
                count = 0
            if count:
                noun = "review" if count == 1 else "reviews"
                self._duplicate_warning.setText(
                    f"{count} saved {noun} already use this reporting period. "
                    "Continuing creates a separate Review ID."
                )
                self._duplicate_warning.setAccessibleDescription(
                    self._duplicate_warning.text()
                )
                self._duplicate_warning.setVisible(True)
                if self._duplicate_warning.text() != self._last_duplicate_announcement:
                    self._announce(
                        self._duplicate_warning.text(),
                        target=self._duplicate_warning,
                    )
                    self._last_duplicate_announcement = self._duplicate_warning.text()
            else:
                self._duplicate_warning.clear()
                self._duplicate_warning.setVisible(False)
                self._last_duplicate_announcement = ""
        else:
            self._period_preview.setText("Reporting period: Not selected")
            self._duplicate_warning.clear()
            self._duplicate_warning.setVisible(False)
            self._last_duplicate_announcement = ""

    def _submit_create(self) -> None:
        missing = []
        month = self._month.currentData()
        if month is None:
            missing.append("reporting month")
        year_text = self._year.text().strip()
        if len(year_text) != 4 or not year_text.isdigit():
            missing.append("four-digit reporting year")
        if missing:
            message = "Please enter the required month and year."
            self._create_error.setText(message)
            self._create_error.setAccessibleDescription(message)
            self._create_error.setVisible(True)
            self._announce(message, assertive=True, target=self._create_error)
            (self._month if month is None else self._year).setFocus()
            return
        self._create_submit.setEnabled(False)
        try:
            review = self._c.create_managed_review(
                int(month), int(year_text), self._create_request_id
            )
        except Exception as exc:
            message = self._safe_error_message(exc)
            self._create_error.setText(message)
            self._create_error.setAccessibleDescription(message)
            self._create_error.setVisible(True)
            self._create_submit.setEnabled(True)
            self._announce(message, assertive=True, target=self._create_error)
            self._create_submit.setFocus()
            return
        self._current_review = review
        self._set_past_availability(True, "")
        self._show_review(review, "Review created and saved.")
        self._announce(
            "Review created and saved. Upload Documents is ready.",
            target=self._create_title,
        )
        self.sourceIntakeRequested.emit(review)

    def _clear_past(self) -> None:
        while self._past_list.count():
            item = self._past_list.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self._past_cards = []

    def _refresh_past(self) -> None:
        self._clear_past()
        selected = self._status_filter.currentData()
        statuses = None if selected is None else (selected,)
        try:
            reviews = self._c.managed_reviews(statuses=statuses)
            self._past_message.setVisible(False)
        except Exception as exc:
            reviews = []
            self._past_message.setText(self._safe_error_message(exc))
            self._past_message.setAccessibleDescription(self._past_message.text())
            self._past_message.setVisible(True)
            self._announce(
                self._past_message.text(),
                assertive=True,
                target=self._past_message,
            )
        if not reviews:
            empty = _label("No reviews match this Review Status.", "empty", wrap=True)
            empty.setAccessibleName("No matching past reviews")
            self._past_list.addWidget(empty)
            self._announce(empty.text(), target=empty)
            return
        for review in reviews:
            action_label = "Resume" if review.status is ReviewStatus.DRAFT else "Open"
            result_summary = self._c.financial_results(review.review_id)
            card = _PastReviewCard(
                review,
                self._open_past_review,
                self._delete_review,
                action_label=action_label,
                result_summary=result_summary,
            )
            self._past_cards.append(card)
            self._past_list.addWidget(card)
        noun = "review" if len(reviews) == 1 else "reviews"
        self._announce(
            f"{len(reviews)} saved {noun} displayed.",
            target=self._past_title,
        )

    def _refresh_current_review(self) -> None:
        if self._current_review is None:
            return
        try:
            self._current_review = next(
                (
                    review
                    for review in self._c.managed_reviews()
                    if review.review_id == self._current_review.review_id
                ),
                self._current_review,
            )
        except Exception:
            # Availability/error handling below remains the user-facing boundary.
            pass

    def _open_past_review(self, review_id: str) -> None:
        try:
            review = self._c.reopen_managed_review(review_id)
        except Exception as exc:
            self._past_message.setText(self._safe_error_message(exc))
            self._past_message.setAccessibleDescription(self._past_message.text())
            self._past_message.setVisible(True)
            self._announce(
                self._past_message.text(),
                assertive=True,
                target=self._past_message,
            )
            return
        self._current_review = review
        self._show_review(review, "Review reopened.")
        self.sourceIntakeRequested.emit(review)

    def _show_review(self, review, announcement: str) -> None:
        self._current_review = review
        self._set_past_availability(True, "")
        self._review_period.setText(review.period.label)
        self._review_status.setText(review.status.value)
        self._review_disposition.setText(review.disposition.value)
        self._review_context.setText(review.context_label)
        self._publication_status.setText(
            "Not created" if review.published_generation_id is None else "Published"
        )
        self._financial_status.setText("Not available — validation has not run")
        self._review_id.setText(review.review_id)
        self._review_continue.setText(
            "View Upload && Extraction"
            if review.status is ReviewStatus.DATA_UPLOADED
            else "Continue to Upload && Extraction"
        )
        self._review_continue.setAccessibleName(
            "View Upload and Extraction"
            if review.status is ReviewStatus.DATA_UPLOADED
            else "Continue to Upload and Extraction"
        )
        self._stack.setCurrentIndex(self.REVIEW)
        self._set_shell_state("Review Workspace", "past_reviews")
        self._focus_after_navigation(self._review_past)
        self._announce(
            f"{announcement} {review.period.label}. Review Status {review.status.value}.",
            target=self._review_title,
        )

    def _delete_review(self, review) -> None:
        if review is None:
            return
        try:
            preview = self._c.prepare_review_disposal(review.review_id)
        except Exception as exc:
            message = self._safe_error_message(exc)
            QMessageBox.warning(self, "Review not deleted", message)
            return
        dialog = DeleteReviewDialog(review.period.label, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            token = getattr(preview, "confirmation_token", "")
            if token:
                self._c.cancel_review_disposal(token)
            return
        token = (
            preview.get("confirmation_token")
            if isinstance(preview, dict)
            else getattr(preview, "confirmation_token", "")
        )
        try:
            self._c.confirm_review_disposal(review.review_id, token)
        except Exception as exc:
            message = self._safe_error_message(exc)
            QMessageBox.warning(self, "Review not deleted", message)
            return
        if (
            self._current_review is not None
            and self._current_review.review_id == review.review_id
        ):
            self._current_review = None
        QMessageBox.information(
            self,
            "Review deleted",
            f"The {review.period.label} review was permanently deleted. "
            "The original external workbooks were not changed.",
        )
        self._c.clear_review()
        self.show_past()

    def show_review_workspace(self, review) -> None:
        """Return from a later workflow surface without creating a reopen audit event."""

        self._show_review(review, "Review workspace opened.")

    def go_back(self) -> None:
        current = self._stack.currentIndex()
        if current in (self.CREATE, self.PAST):
            self.show_welcome()
        elif current == self.REVIEW:
            self.show_past()

    def _on_management_changed(self) -> None:
        if self._stack.currentIndex() == self.WELCOME:
            self.show_welcome()

    # ---- stable verification seams ----
    def current_screen(self) -> str:
        return ("welcome", "create", "past_reviews", "review_workspace")[
            self._stack.currentIndex()
        ]

    def welcome_title(self) -> str:
        return self._welcome_title.text()

    def past_reviews_enabled(self) -> bool:
        return self._past_button.isEnabled()

    def past_review_ids(self) -> list[str]:
        return [card.review_id for card in self._past_cards]

    def action_cards_side_by_side(self) -> bool:
        return not bool(self._action_cards_stacked)

    def shell_visible(self) -> bool:
        return self._home_nav.isVisibleTo(self) and self._ask_fin_button.isVisibleTo(self)

    def current_review_id(self):
        return self._current_review.review_id if self._current_review is not None else None

    def last_accessibility_announcement(self) -> str:
        return self._last_accessibility_announcement
