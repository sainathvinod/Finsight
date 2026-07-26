from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut, QAction, QActionGroup
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                               QStackedWidget, QApplication, QDockWidget, QPushButton)
from finsight.delivery.desktop.components import NavItem
from finsight.delivery.desktop.views import (
    ReviewsView, OverviewView, FindingsView, AuditView, WorkflowView, AskFinView, DashboardView)
from finsight.delivery.desktop.views.welcome_view import WelcomeView
from finsight.delivery.desktop.theme import tokens as t
from finsight.delivery.desktop.theme.theming import ThemeManager

_THEME_LABELS = [("system", "System"), ("light", "Light"), ("dark", "Dark"),
                 ("high-contrast", "High Contrast")]

# (nav key, label) in order; index aligns with the workspace stack. "dashboard" is the portfolio
# launch home; "overview" is the active-review home; "workspace" is the guided workflow.
_NAV = [("dashboard", "Dashboard"), ("reviews", "Reviews"), ("overview", "Review Overview"),
        ("workspace", "Workflow"), ("findings", "Findings"), ("audit", "Audit"), ("askfin", "Ask Fin")]


class MainWindow(QMainWindow):
    """Application shell: left navigation, top application bar with active-review context, and the
    workspace stack. Read-only in Phase 2; no workflow actions are exposed."""

    def __init__(self, controller, parent=None, theme_manager=None):
        super().__init__(parent)
        self._c = controller
        self._theme = theme_manager or ThemeManager()
        self._current_key = "reviews"
        self.setWindowTitle("FinSight")
        self.resize(1180, 720)
        self.setMinimumSize(940, 600)

        central = QWidget()
        central.setObjectName("Workspace")
        outer = QHBoxLayout(central)
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
        # First-launch Welcome lives outside the nav stack order; shown before any review exists.
        self._welcome = WelcomeView(controller)
        self._stack.addWidget(self._welcome)
        right.addWidget(self._stack, 1)
        right_wrap = QWidget()
        right_wrap.setLayout(right)
        outer.addWidget(right_wrap, 1)
        self.setCentralWidget(central)

        # Persistent Ask Fin drawer (§17): available on EVERY screen, toggled from the top bar or Ctrl+/.
        # A second AskFinView instance (same experience as the nav screen), context-aware of the active
        # review. Product-help works before any review; deterministic answers work with the model off.
        self._ask_dock = QDockWidget("Ask Fin", self)
        self._ask_dock.setObjectName("AskFinDock")
        self._ask_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea
                                       | Qt.DockWidgetArea.LeftDockWidgetArea)
        self._ask_panel = AskFinView(controller)
        self._ask_dock.setWidget(self._ask_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._ask_dock)
        self._ask_dock.hide()
        self._ask_visible = False
        # Keep the drawer context-aware: refresh on active-review and workflow changes so a visible
        # drawer always reflects the current review (product-help before analysis, review-mode after).
        controller.activeReviewChanged.connect(lambda _c: self._ask_panel.refresh())
        controller.workflowChanged.connect(lambda _c: self._ask_panel.refresh())
        sc = QShortcut(QKeySequence("Ctrl+/"), self)
        sc.activated.connect(self.toggle_ask_fin)

        # wiring
        self._reviews.reviewActivated.connect(lambda _cid: self.navigate("overview"))
        self._reviews.newReviewRequested.connect(self._on_new_review)
        self._overview.openWorkflowRequested.connect(lambda: self.navigate("workspace"))
        self._dashboard.openReviewRequested.connect(self._on_open_from_dashboard)
        self._dashboard.newReviewRequested.connect(self._on_new_review)
        self._welcome.newReviewRequested.connect(self._on_new_review)
        self._welcome.askFinRequested.connect(lambda: self.navigate("askfin"))
        self._workspace.backToHomeRequested.connect(self._route_launch)   # first-step Back → Home
        self._c.activeReviewChanged.connect(self._on_active_changed)
        for i, (key, _label) in enumerate(_NAV):
            sc = QShortcut(QKeySequence(f"Ctrl+{i + 1}"), self)
            sc.activated.connect(lambda k=key: self.navigate(k))

        self._build_menu()
        self._route_launch()   # first-ever launch -> Welcome; returning users -> Dashboard home
        # ReviewsView selects its first row during construction (before the signal above was
        # connected), so sync the top-bar context to whatever is already active.
        self._on_active_changed(self._c.active_review_id or "")

    # --- accessibility: theme + zoom menu (§20) ---
    def _build_menu(self) -> None:
        view_menu = self.menuBar().addMenu("View")
        theme_menu = view_menu.addMenu("Theme")
        self._theme_group = QActionGroup(self)
        self._theme_group.setExclusive(True)
        self._theme_actions = {}
        for mode, label in _THEME_LABELS:
            act = QAction(label, self, checkable=True)
            act.setChecked(self._theme.mode == mode)
            act.triggered.connect(lambda _checked, m=mode: self._set_theme(m))
            self._theme_group.addAction(act)
            theme_menu.addAction(act)
            self._theme_actions[mode] = act
        view_menu.addSeparator()
        for label, seq, fn in [
            ("Zoom In", "Ctrl+=", self._theme.zoom_in),
            ("Zoom Out", "Ctrl+-", self._theme.zoom_out),
            ("Reset Zoom", "Ctrl+0", self._theme.reset_zoom),
            ("Larger Text", "Ctrl+Shift+=", self._theme.zoom_in)]:
            act = QAction(label, self)
            act.setShortcut(QKeySequence(seq))
            act.triggered.connect(lambda _checked=False, f=fn: f(QApplication.instance()))
            view_menu.addAction(act)

    def _set_theme(self, mode: str) -> None:
        self._theme.set_mode(mode, QApplication.instance())
        act = self._theme_actions.get(mode)
        if act is not None:
            act.setChecked(True)

    # --- persistent Ask Fin drawer (§17) ---
    def toggle_ask_fin(self) -> None:
        self._ask_visible = not self._ask_visible
        self._ask_dock.setVisible(self._ask_visible)
        if self._ask_visible:
            self._ask_panel.refresh()

    def ask_fin_drawer(self):                 # public seam
        return self._ask_panel

    def ask_fin_drawer_visible(self) -> bool:
        return self._ask_visible

    # --- public seams (theme) ---
    def theme_manager(self) -> ThemeManager:
        return self._theme

    # --- shell construction ---
    def _build_sidebar(self) -> QWidget:
        side = QWidget()
        side.setObjectName("Sidebar")
        side.setFixedWidth(t.SIDEBAR_W)
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
        self._ask_toggle = QPushButton("Ask Fin")
        self._ask_toggle.setProperty("role", "secondary")
        self._ask_toggle.setToolTip("Ask Fin — grounded help & explanations (Ctrl+/)")
        self._ask_toggle.clicked.connect(self.toggle_ask_fin)
        lay.addSpacing(t.SP_3)
        lay.addWidget(self._ask_toggle)
        return bar

    # --- navigation ---
    def navigate(self, key: str) -> None:
        index = [k for k, _ in _NAV].index(key)
        self._current_key = key
        self._stack.setCurrentIndex(index)
        for k, item in self._nav_items.items():
            item.setChecked(k == key)
        self._crumb.setText(dict(_NAV)[key])
        current = self._stack.currentWidget()
        if hasattr(current, "refresh"):
            current.refresh()
        self._nav_items[key].setFocus()

    def _route_launch(self) -> None:
        """First-ever launch (no reviews yet) opens the dedicated Welcome screen; returning users
        land on the Dashboard portfolio home. A guided product never opens to a blank table."""
        if self._has_reviews():
            self.navigate("dashboard")
        else:
            self.show_welcome()

    def _has_reviews(self) -> bool:
        try:
            return bool(self._c.reviews_with_status())
        except Exception:
            return False

    def show_welcome(self) -> None:
        self._current_key = "welcome"
        self._stack.setCurrentWidget(self._welcome)
        for item in self._nav_items.values():
            item.setChecked(False)
        self._crumb.setText("Welcome")
        self._welcome.setFocus()

    # --- public seams (stable API for tests and integrators) ---
    def current_view_key(self) -> str:
        return self._current_key

    def view(self, key: str):
        return {"dashboard": self._dashboard, "reviews": self._reviews, "overview": self._overview,
                "workspace": self._workspace, "findings": self._findings, "audit": self._audit,
                "askfin": self._askfin, "welcome": self._welcome}[key]

    def _on_new_review(self) -> None:
        self._c.begin_new_review()
        self.navigate("workspace")

    def _on_open_from_dashboard(self, cycle_id: str) -> None:
        self._c.select_review(cycle_id)
        self.navigate("overview")

    def _on_active_changed(self, cycle_id: str) -> None:
        if cycle_id:
            status = self._c.review_status(cycle_id)
            if status is not None:
                self._context.setText(f"Active review:  {status.month} {status.year}  ·  {status.state}")
                return
        self._context.setText("No review selected")
