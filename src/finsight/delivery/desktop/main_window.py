from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from finsight.delivery.desktop.components import (
    AdaptiveSidebar,
    AppearanceMenuButton,
    IconBadge,
    NavItem,
)
from finsight.delivery.desktop.views import (
    ReviewsView, OverviewView, FindingsView, AuditView, WorkflowView, AskFinView, DashboardView,
    ReviewManagementView, SourceIntakeView, FinancialReviewView, RulesRepositoryView,
    SettingsView)
from finsight.domain.review_management import ReviewStatus
from finsight.delivery.desktop.theme import tokens as t
from finsight.delivery.desktop.views.private_ask_fin_dialog import (
    PrivateAskFinDrawer,
)

if TYPE_CHECKING:
    from finsight.delivery.desktop.theme import AppearanceManager

# (nav key, label) in order; index aligns with the workspace stack. "dashboard" is the portfolio
# launch home; "overview" is the active-review home; "workspace" is the guided workflow.
_NAV = [("dashboard", "Dashboard"), ("reviews", "Reviews"), ("overview", "Review Overview"),
        ("workspace", "Workflow"), ("findings", "Findings"), ("audit", "Audit"), ("askfin", "Ask Fin")]


class MainWindow(QMainWindow):
    """Application shell: left navigation, top application bar with active-review context, and the
    workspace stack. Read-only in Phase 2; no workflow actions are exposed."""

    def __init__(
        self,
        controller,
        parent=None,
        *,
        appearance_manager: "AppearanceManager | None" = None,
    ):
        super().__init__(parent)
        self._c = controller
        self._appearance_manager = appearance_manager
        self._appearance_controls: dict[str, AppearanceMenuButton] = {}
        self._current_key = "reviews"
        self.setWindowTitle("FinSight")
        self.resize(1180, 720)
        self.setMinimumSize(940, 600)

        legacy_shell = QWidget()
        legacy_shell.setObjectName("Workspace")
        outer = QHBoxLayout(legacy_shell)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._build_sidebar())

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        right.addWidget(self._build_topbar())
        self._stack = QStackedWidget()
        self._dashboard = DashboardView(controller)
        self._reviews = ReviewsView(controller)
        self._overview = OverviewView(controller)
        self._workspace = WorkflowView(controller)
        self._findings = FindingsView(controller)
        self._audit = AuditView(controller)
        self._askfin = AskFinView(controller)
        for v in (self._dashboard, self._reviews, self._overview, self._workspace, self._findings,
                  self._audit, self._askfin):
            self._stack.addWidget(v)
        right.addWidget(self._stack, 1)
        right_wrap = QWidget()
        right_wrap.setLayout(right)
        outer.addWidget(right_wrap, 1)
        # Workflow 1 launch surface. The prior FinSight shell remains intact behind its public
        # navigation seam for regression compatibility, but is not reachable from the production
        # Review Management UI during this increment.
        self._root_stack = QStackedWidget()
        self._review_management = ReviewManagementView(controller)
        self._source_intake = SourceIntakeView(controller)
        self._financial_review = FinancialReviewView(controller)
        self._rules_repository = RulesRepositoryView(controller)
        self._settings_view = SettingsView(controller, appearance_manager)
        self._settings_return_index = 0
        self._navigation_history: list[tuple[int, ...]] = []
        self._navigation_current: tuple[int, ...] | None = None
        self._navigation_capture_scheduled = False
        self._restoring_navigation = False
        self._navigation_back_buttons: dict[str, QPushButton] = {}
        if self._appearance_manager is not None:
            self._install_appearance_controls()
        self._root_stack.addWidget(self._review_management)
        self._root_stack.addWidget(self._source_intake)
        self._root_stack.addWidget(self._financial_review)
        self._root_stack.addWidget(self._rules_repository)
        self._root_stack.addWidget(self._settings_view)
        self._root_stack.addWidget(legacy_shell)
        self._ask_fin_drawer = PrivateAskFinDrawer(controller)
        self._ask_fin_drawer.setVisible(False)
        self._application_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._application_splitter.setObjectName("ApplicationAndAskFin")
        self._application_splitter.setAccessibleName(
            "FinSight workspace and Ask Fin assistant"
        )
        self._application_splitter.setChildrenCollapsible(False)
        self._application_splitter.addWidget(self._root_stack)
        self._application_splitter.addWidget(self._ask_fin_drawer)
        self._application_splitter.setStretchFactor(0, 1)
        self._application_splitter.setStretchFactor(1, 0)
        self._application_splitter.setSizes([self.width(), 0])
        self.setCentralWidget(self._application_splitter)
        if self._appearance_manager is not None:
            self._appearance_manager.appearanceChanged.connect(
                self._refresh_icons
            )
            self._refresh_icons()

        # wiring
        self._reviews.reviewActivated.connect(lambda _cid: self.navigate("overview"))
        self._reviews.newReviewRequested.connect(self._on_new_review)
        self._overview.openWorkflowRequested.connect(lambda: self.navigate("workspace"))
        self._dashboard.openReviewRequested.connect(self._on_open_from_dashboard)
        self._dashboard.newReviewRequested.connect(self._on_new_review)
        self._review_management.sourceIntakeRequested.connect(
            self._show_source_intake
        )
        self._review_management.ruleGovernanceRequested.connect(
            self._show_rule_governance
        )
        self._source_intake.homeRequested.connect(self.show_review_management)
        self._source_intake.pastReviewsRequested.connect(self._show_past_reviews)
        self._source_intake.reviewRequested.connect(self._show_review_workspace)
        self._source_intake.financialReviewRequested.connect(
            self._show_financial_review
        )
        self._financial_review.homeRequested.connect(self.show_review_management)
        self._financial_review.pastReviewsRequested.connect(self._show_past_reviews)
        self._financial_review.rulesRequested.connect(self._show_rules_repository)
        self._rules_repository.homeRequested.connect(self.show_review_management)
        self._rules_repository.pastReviewsRequested.connect(self._show_past_reviews)
        self._rules_repository.backRequested.connect(self._return_from_rules)
        self._rules_repository.validationRequested.connect(
            self._start_validation_from_rules
        )
        self._financial_review.askFinRequested.connect(
            self._open_ask_fin_context
        )
        for view in (
            self._review_management,
            self._source_intake,
            self._rules_repository,
            self._settings_view,
        ):
            view.askFinRequested.connect(self._open_ask_fin)
        self._ask_fin_drawer.closeRequested.connect(
            self._close_ask_fin_drawer
        )
        self._ask_fin_drawer.citationActivated.connect(
            self._navigate_ask_fin_citation
        )
        # Compatibility seam for existing screenshot and focused UI helpers.
        self._financial_review._private_ask_fin_dialog = (
            self._ask_fin_drawer
        )
        for view in (
            self._review_management,
            self._source_intake,
            self._financial_review,
            self._rules_repository,
        ):
            settings_requested = getattr(view, "settingsRequested", None)
            if settings_requested is not None:
                settings_requested.connect(self._show_settings)
        self._settings_view.homeRequested.connect(self.show_review_management)
        self._settings_view.pastReviewsRequested.connect(self._show_past_reviews)
        self._settings_view.backRequested.connect(self._return_from_settings)
        self._install_navigation_controls()
        self._hide_embedded_back_controls()
        self._install_navigation_history()
        self._c.activeReviewChanged.connect(self._on_active_changed)
        self._c.financialReviewChanged.connect(
            self._on_financial_review_changed
        )
        self._legacy_shortcuts = []
        for i, (key, _label) in enumerate(_NAV):
            sc = QShortcut(QKeySequence(f"Ctrl+{i + 1}"), self)
            sc.activated.connect(lambda k=key: self.navigate(k))
            sc.setEnabled(False)
            self._legacy_shortcuts.append(sc)

        self._current_key = "welcome"
        self._root_stack.setCurrentIndex(0)
        self._navigation_current = self._capture_navigation_state()
        self._update_back_visibility()
        # ReviewsView selects its first row during construction (before the signal above was
        # connected), so sync the top-bar context to whatever is already active.
        self._on_active_changed(self._c.active_review_id or "")
        QTimer.singleShot(0, self._ask_fin_drawer.initialize_status)

    # --- shell construction ---
    def _install_appearance_controls(self) -> None:
        """Add one shared-manager appearance entry point to every active shell."""

        views = {
            "review_management": self._review_management,
            "source_intake": self._source_intake,
            "financial_review": self._financial_review,
            "rules_repository": self._rules_repository,
            "settings": self._settings_view,
        }
        for key, view in views.items():
            header = view.findChild(QWidget, "Workflow1TopBar")
            if header is None or header.layout() is None:
                continue
            control = AppearanceMenuButton(
                self._appearance_manager,
                parent=header,
            )
            ask_button = getattr(view, "_ask_fin_button", None)
            if ask_button is None:
                ask_button = next(
                    (
                        button
                        for button in header.findChildren(QPushButton)
                        if button.accessibleName() == "Ask Fin"
                    ),
                    None,
                )
            insert_at = header.layout().indexOf(ask_button)
            if insert_at >= 0:
                header.layout().insertWidget(insert_at, control)
            else:
                header.layout().addWidget(control)
            self._appearance_controls[key] = control

    def _refresh_icons(self, *_appearance) -> None:
        """Refresh theme-aware glyph colors across every composed shell."""

        for item in self.findChildren(NavItem):
            item.refresh_icon()
        for badge in self.findChildren(IconBadge):
            badge.refresh_icon()
        for control in self.findChildren(AppearanceMenuButton):
            control.refresh_icon()
        self._ask_fin_drawer.refresh_icon()

    def _install_navigation_controls(self) -> None:
        """Install one predictable Back action in every modern application header."""

        views = {
            "review_management": self._review_management,
            "source_intake": self._source_intake,
            "financial_review": self._financial_review,
            "rules_repository": self._rules_repository,
            "settings": self._settings_view,
        }
        for key, view in views.items():
            header = view.findChild(QWidget, "Workflow1TopBar")
            if header is None or header.layout() is None:
                continue
            for label in header.findChildren(
                QLabel, options=Qt.FindChildOption.FindDirectChildrenOnly
            ):
                label.setMinimumWidth(0)
                label.setSizePolicy(
                    QSizePolicy.Policy.Ignored,
                    QSizePolicy.Policy.Preferred,
                )
            back = QPushButton("← Back", header)
            back.setObjectName("GlobalBackButton")
            back.setProperty("role", "secondary")
            back.setAccessibleName("Back to previous FinSight page")
            back.setAccessibleDescription(
                "Return to the previous page while preserving your review state and filters."
            )
            back.setToolTip(
                "Back (%s)"
                % QKeySequence(QKeySequence.StandardKey.Back).toString(
                    QKeySequence.SequenceFormat.NativeText
                )
            )
            back.clicked.connect(self.go_back)
            header.layout().insertWidget(0, back)
            self._navigation_back_buttons[key] = back

        # Platform-resolved Back. A literal "Alt+Left" is the macOS "move to previous word"
        # text-editing gesture, so it navigated away mid-edit and abandoned the form.
        # StandardKey.Back maps to the native sequence on each platform.
        self._global_back_shortcut = QShortcut(
            QKeySequence(QKeySequence.StandardKey.Back), self
        )
        self._global_back_shortcut.setContext(
            Qt.ShortcutContext.WindowShortcut
        )
        self._global_back_shortcut.activated.connect(self.go_back)

    def _hide_embedded_back_controls(self) -> None:
        """Keep one visible Back action per view in the shared header."""

        controls = (
            self._review_management._create_page_back,
            self._review_management._past_back,
            self._review_management._review_home,
            self._source_intake._upload_home,
            self._source_intake._metadata_back,
            self._rules_repository._back,
            self._settings_view.back_button,
        )
        for control in controls:
            control.hide()

    def _install_navigation_history(self) -> None:
        """Observe page and analytical-subview changes as one application history."""

        observed = [
            self._root_stack,
            self._review_management._stack,
            self._source_intake._stack,
            self._financial_review._stack,
            self._stack,
        ]
        for attribute in (
            "_results_tabs",
            "_analysis_tabs",
            "_ged_sections",
            "_finding_sections",
        ):
            widget = getattr(self._financial_review, attribute, None)
            if widget is not None:
                observed.append(widget)
        for widget in observed:
            widget.currentChanged.connect(self._schedule_navigation_capture)

    @staticmethod
    def _current_index(owner, attribute: str) -> int:
        widget = getattr(owner, attribute, None)
        return int(widget.currentIndex()) if widget is not None else -1

    def _capture_navigation_state(self) -> tuple[int, ...]:
        return (
            int(self._root_stack.currentIndex()),
            self._current_index(self._review_management, "_stack"),
            self._current_index(self._source_intake, "_stack"),
            self._current_index(self._financial_review, "_stack"),
            self._current_index(self._financial_review, "_results_tabs"),
            self._current_index(self._financial_review, "_analysis_tabs"),
            self._current_index(self._financial_review, "_ged_sections"),
            self._current_index(self._financial_review, "_finding_sections"),
            int(self._stack.currentIndex()),
        )

    def _schedule_navigation_capture(self, *_index) -> None:
        if self._restoring_navigation or self._navigation_capture_scheduled:
            return
        self._navigation_capture_scheduled = True
        QTimer.singleShot(0, self._commit_navigation_state)

    def _state_is_meaningful(self, state: tuple[int, ...]) -> bool:
        root_index = state[0]
        if root_index != 2:
            return True
        return state[3] not in {
            int(self._financial_review.PROCESSING),
            int(self._financial_review.VALIDATING),
        }

    def _commit_navigation_state(self) -> None:
        self._navigation_capture_scheduled = False
        if self._restoring_navigation:
            return
        state = self._capture_navigation_state()
        previous = self._navigation_current
        if previous is None:
            self._navigation_current = state
        elif state != previous:
            if self._state_is_meaningful(previous):
                if not self._navigation_history or self._navigation_history[-1] != previous:
                    self._navigation_history.append(previous)
                    del self._navigation_history[:-100]
            self._navigation_current = state
        self._update_back_visibility()

    @staticmethod
    def _restore_index(owner, attribute: str, index: int) -> None:
        widget = getattr(owner, attribute, None)
        if widget is not None and 0 <= index < widget.count():
            widget.setCurrentIndex(index)

    def _restore_navigation_state(self, state: tuple[int, ...]) -> None:
        self._restoring_navigation = True
        try:
            self._restore_index(self._review_management, "_stack", state[1])
            self._restore_index(self._source_intake, "_stack", state[2])
            self._restore_index(self._financial_review, "_stack", state[3])
            self._restore_index(self._financial_review, "_results_tabs", state[4])
            self._restore_index(self._financial_review, "_analysis_tabs", state[5])
            self._restore_index(self._financial_review, "_ged_sections", state[6])
            self._restore_index(self._financial_review, "_finding_sections", state[7])
            if 0 <= state[8] < self._stack.count():
                self._stack.setCurrentIndex(state[8])
            if 0 <= state[0] < self._root_stack.count():
                self._root_stack.setCurrentIndex(state[0])
            self._navigation_current = self._capture_navigation_state()
        finally:
            self._restoring_navigation = False
        self._update_back_visibility()
        self._focus_after_back()

    def _fallback_back(self) -> None:
        root_index = self._root_stack.currentIndex()
        if root_index == 0:
            self._review_management.go_back()
        elif root_index == 1:
            self._source_intake._back()
        elif root_index == 2:
            self._show_past_reviews()
        elif root_index == 3:
            self._return_from_rules(getattr(self._rules_repository, "_review", None))
        elif root_index == 4:
            self._return_from_settings()
        elif root_index == 5:
            self.show_review_management()

    def go_back(self) -> None:
        """Return to the prior application state without rebuilding the current page."""

        if self._navigation_capture_scheduled:
            self._commit_navigation_state()
        current = self._capture_navigation_state()
        while self._navigation_history and self._navigation_history[-1] == current:
            self._navigation_history.pop()
        if not self._navigation_history:
            self._fallback_back()
            self._navigation_current = self._capture_navigation_state()
            self._update_back_visibility()
            return
        self._restore_navigation_state(self._navigation_history.pop())

    def _focus_after_back(self) -> None:
        root_index = self._root_stack.currentIndex()
        target = None
        if root_index == 0:
            screen = self._review_management.current_screen()
            target = (
                getattr(self._review_management, "_create_button", None)
                if screen == "welcome"
                else self._navigation_back_buttons.get(
                    "review_management"
                )
            )
        elif root_index == 1:
            target = self._navigation_back_buttons.get("source_intake")
        elif root_index in (2, 3, 4):
            key = ("financial_review", "rules_repository", "settings")[root_index - 2]
            target = self._navigation_back_buttons.get(key)
        if target is not None and target.isVisible():
            target.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def _update_back_visibility(self) -> None:
        root_index = self._root_stack.currentIndex()
        visible_key = {
            0: "review_management",
            1: "source_intake",
            2: "financial_review",
            3: "rules_repository",
            4: "settings",
        }.get(root_index)
        for key, button in self._navigation_back_buttons.items():
            show = key == visible_key
            if key == "review_management" and show:
                show = self._review_management.current_screen() != "welcome"
            button.setVisible(show)
            button.setEnabled(show)

    def can_go_back(self) -> bool:
        if self._navigation_capture_scheduled:
            self._commit_navigation_state()
        return bool(self._navigation_history) or (
            self._root_stack.currentIndex() != 0
            or self._review_management.current_screen() != "welcome"
        )

    def navigation_history_depth(self) -> int:
        if self._navigation_capture_scheduled:
            self._commit_navigation_state()
        return len(self._navigation_history)

    def back_button(self, key: str) -> QPushButton | None:
        return self._navigation_back_buttons.get(key)

    def _build_sidebar(self) -> QWidget:
        side = AdaptiveSidebar()
        side.setObjectName("Sidebar")
        lay = QVBoxLayout(side)
        lay.setContentsMargins(t.SP_3, t.SP_4, t.SP_3, t.SP_3)
        lay.setSpacing(t.SP_1)

        title = QLabel("FinSight")
        title.setProperty("role", "appTitle")
        lay.addWidget(title)
        lay.addSpacing(t.SP_4)

        group = QLabel("WORKSPACE")
        group.setProperty("role", "navGroup")
        lay.addWidget(group)

        self._nav_items = {}
        for key, label in _NAV:
            item = NavItem(key, label)
            item.activated.connect(self.navigate)
            self._nav_items[key] = item
            lay.addWidget(item)
        lay.addStretch(1)
        return side

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(t.TOPBAR_H)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(t.SP_5, 0, t.SP_5, 0)
        self._crumb = QLabel("Reviews")
        self._crumb.setProperty("role", "context")
        lay.addWidget(self._crumb)
        lay.addStretch(1)
        self._context = QLabel("No review selected")
        self._context.setProperty("role", "context")
        lay.addWidget(self._context)
        return bar

    # --- navigation ---
    def navigate(self, key: str) -> None:
        index = [k for k, _ in _NAV].index(key)
        self._root_stack.setCurrentIndex(5)
        for shortcut in self._legacy_shortcuts:
            shortcut.setEnabled(True)
        self._current_key = key
        self._stack.setCurrentIndex(index)
        for k, item in self._nav_items.items():
            item.setChecked(k == key)
        self._crumb.setText(dict(_NAV)[key])
        current = self._stack.currentWidget()
        if hasattr(current, "refresh"):
            current.refresh()
        self._nav_items[key].setFocus()

    # --- public seams (stable API for tests and integrators) ---
    def current_view_key(self) -> str:
        if self._root_stack.currentIndex() == 0:
            return self._review_management.current_screen()
        if self._root_stack.currentIndex() == 1:
            return self._source_intake.current_screen()
        if self._root_stack.currentIndex() == 2:
            return self._financial_review.current_screen()
        if self._root_stack.currentIndex() == 3:
            return self._rules_repository.current_screen()
        if self._root_stack.currentIndex() == 4:
            return "settings"
        return self._current_key

    def view(self, key: str):
        return {"review_management": self._review_management,
                "source_intake": self._source_intake,
                "financial_review": self._financial_review,
                "rules_repository": self._rules_repository,
                "settings": self._settings_view,
                "ask_fin_drawer": self._ask_fin_drawer,
                "dashboard": self._dashboard, "reviews": self._reviews, "overview": self._overview,
                "workspace": self._workspace, "findings": self._findings, "audit": self._audit,
                "askfin": self._askfin}[key]

    def appearance_control(self, key: str) -> AppearanceMenuButton | None:
        """Return the header appearance entry point for a workflow shell."""

        return self._appearance_controls.get(key)

    def show_review_management(self) -> None:
        for shortcut in self._legacy_shortcuts:
            shortcut.setEnabled(False)
        self._root_stack.setCurrentIndex(0)
        self._review_management.show_welcome()

    def _show_source_intake(self, review) -> None:
        if review is None:
            return
        self._c.select_review(review.review_id)
        if review.status is not ReviewStatus.DRAFT:
            self._show_financial_review(review)
            return
        self._root_stack.setCurrentIndex(1)
        self._source_intake.open_review(review)

    def _show_financial_review(self, review) -> None:
        if review is None:
            return
        self._c.select_review(review.review_id)
        self._root_stack.setCurrentIndex(2)
        self._financial_review.open_review(review)

    def _show_rules_repository(self, review, dataset, revalidation=False) -> None:
        if review is None or dataset is None:
            return
        self._root_stack.setCurrentIndex(3)
        self._rules_repository.open_review(
            review, dataset, revalidation=bool(revalidation)
        )

    def _show_rule_governance(self) -> None:
        self._root_stack.setCurrentIndex(3)
        self._rules_repository.open_governance_queue()

    def _return_from_rules(self, _review) -> None:
        if _review is None:
            self.show_review_management()
            return
        revalidation = bool(self._rules_repository._revalidation)
        self._root_stack.setCurrentIndex(2)
        self._financial_review.return_from_rules(revalidation=revalidation)

    def _start_validation_from_rules(
        self, review, dataset, revalidation=False, confirmation=None
    ) -> None:
        self._root_stack.setCurrentIndex(2)
        self._financial_review.start_validation_from_rules(
            review,
            dataset,
            revalidation=bool(revalidation),
            confirmation=confirmation,
        )

    def _show_past_reviews(self) -> None:
        self._root_stack.setCurrentIndex(0)
        self._review_management.show_past()

    def _show_settings(self) -> None:
        current = self._root_stack.currentIndex()
        if current != 4:
            self._settings_return_index = current
        self._root_stack.setCurrentIndex(4)

    def _open_ask_fin(self) -> None:
        self._open_ask_fin_context(
            self._c.active_review_id or "", "", "", "Active review"
        )

    def _open_ask_fin_context(
        self,
        review_id: str,
        object_type: str,
        object_id: str,
        label: str,
    ) -> None:
        """Reveal the application-integrated local assistant drawer."""

        selected_review = review_id or self._c.active_review_id or ""
        if not selected_review:
            self._reveal_ask_fin_drawer()
            self._ask_fin_drawer.open_without_review()
            return
        if self._c.active_review_id != selected_review:
            self._c.select_review(selected_review)
        self._reveal_ask_fin_drawer()
        self._ask_fin_drawer.open_for(
            review_id=selected_review,
            object_type=object_type,
            object_id=object_id,
            label=label or "Active review",
        )

    def _reveal_ask_fin_drawer(self) -> None:
        if self._ask_fin_drawer.isVisible() and self._ask_fin_drawer.width():
            return
        available = max(self._application_splitter.width(), self.width())
        target = max(360, min(520, round(available * 0.34)))
        self._ask_fin_drawer.setMinimumWidth(0)
        self._ask_fin_drawer.setMaximumWidth(0)
        self._ask_fin_drawer.show()
        self._application_splitter.setSizes(
            [max(520, available - target), target]
        )
        animation = QPropertyAnimation(
            self._ask_fin_drawer, b"maximumWidth", self
        )
        animation.setDuration(180)
        animation.setStartValue(0)
        animation.setEndValue(target)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        def finish() -> None:
            self._ask_fin_drawer.setMinimumWidth(360)
            self._ask_fin_drawer.setMaximumWidth(560)
            self._application_splitter.setSizes(
                [max(520, available - target), target]
            )

        animation.finished.connect(finish)
        self._ask_fin_animation = animation
        animation.start()

    def _close_ask_fin_drawer(self) -> None:
        self._ask_fin_drawer.hide()
        self._ask_fin_drawer.setMinimumWidth(360)
        self._ask_fin_drawer.setMaximumWidth(560)
        self._application_splitter.setSizes(
            [self._application_splitter.width(), 0]
        )

    def _navigate_ask_fin_citation(self, citation) -> None:
        self._root_stack.setCurrentIndex(2)
        self._financial_review._navigate_ask_fin_citation(citation)

    def _return_from_settings(self) -> None:
        target = self._settings_return_index
        if target < 0 or target > 3:
            self.show_review_management()
            return
        self._root_stack.setCurrentIndex(target)

    def _show_review_workspace(self) -> None:
        review = self._source_intake.current_review()
        if review is None:
            self.show_review_management()
            return
        self._root_stack.setCurrentIndex(0)
        self._review_management.show_review_workspace(review)

    def _on_new_review(self) -> None:
        self._c.begin_new_review()
        self.navigate("workspace")

    def _on_open_from_dashboard(self, cycle_id: str) -> None:
        self._c.select_review(cycle_id)
        self.navigate("overview")

    def _on_active_changed(self, cycle_id: str) -> None:
        if (
            self._ask_fin_drawer.isVisible()
            and cycle_id
            and cycle_id != self._ask_fin_drawer._review_id
        ):
            self._ask_fin_drawer.open_for(
                review_id=cycle_id,
                label="Active review",
            )
        if cycle_id:
            status = self._c.review_status(cycle_id)
            if status is not None:
                self._context.setText(f"Active review:  {status.month} {status.year}  ·  {status.state}")
                return
        self._context.setText("No review selected")

    def _on_financial_review_changed(self, review_id: str) -> None:
        """Refresh visible Ask Fin grounding after review/run changes."""

        if (
            self._ask_fin_drawer.isVisible()
            and review_id
            and review_id == self._ask_fin_drawer._review_id
        ):
            self._ask_fin_drawer.refresh_review()
