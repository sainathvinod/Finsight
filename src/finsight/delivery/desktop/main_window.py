from __future__ import annotations
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                               QStackedWidget)
from finsight.delivery.desktop.components import NavItem
from finsight.delivery.desktop.views import ReviewsView, OverviewView, FindingsView, AuditView
from finsight.delivery.desktop.theme import tokens as t

# (nav key, label) in order; index aligns with the workspace stack.
_NAV = [("reviews", "Reviews"), ("overview", "Review Overview"),
        ("findings", "Findings"), ("audit", "Audit")]


class MainWindow(QMainWindow):
    """Application shell: left navigation, top application bar with active-review context, and the
    workspace stack. Read-only in Phase 2; no workflow actions are exposed."""

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._c = controller
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
        self._reviews = ReviewsView(controller)
        self._overview = OverviewView(controller)
        self._findings = FindingsView(controller)
        self._audit = AuditView(controller)
        for v in (self._reviews, self._overview, self._findings, self._audit):
            self._stack.addWidget(v)
        right.addWidget(self._stack, 1)
        right_wrap = QWidget()
        right_wrap.setLayout(right)
        outer.addWidget(right_wrap, 1)
        self.setCentralWidget(central)

        # wiring
        self._reviews.reviewActivated.connect(lambda _cid: self.navigate("overview"))
        self._c.activeReviewChanged.connect(self._on_active_changed)
        for i, (key, _label) in enumerate(_NAV):
            sc = QShortcut(QKeySequence(f"Ctrl+{i + 1}"), self)
            sc.activated.connect(lambda k=key: self.navigate(k))

        self.navigate("reviews")
        # ReviewsView selects its first row during construction (before the signal above was
        # connected), so sync the top-bar context to whatever is already active.
        self._on_active_changed(self._c.active_review_id or "")

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
        return bar

    # --- navigation ---
    def navigate(self, key: str) -> None:
        index = [k for k, _ in _NAV].index(key)
        self._stack.setCurrentIndex(index)
        for k, item in self._nav_items.items():
            item.setChecked(k == key)
        self._crumb.setText(dict(_NAV)[key])
        current = self._stack.currentWidget()
        if hasattr(current, "refresh"):
            current.refresh()
        self._nav_items[key].setFocus()

    def _on_active_changed(self, cycle_id: str) -> None:
        if cycle_id:
            status = self._c.review_status(cycle_id)
            if status is not None:
                self._context.setText(f"Active review:  {status.month} {status.year}  ·  {status.state}")
                return
        self._context.setText("No review selected")
