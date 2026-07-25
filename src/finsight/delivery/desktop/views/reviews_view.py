# Implements:
#   Feature: F-01-01 — Monthly Review Cycle Workspace (Recent Reviews home; incl. abandonment/inactivity, DEC-035)
#   Requirements: FR-006, FR-081 (cycle grouping/status); FR-108 (non-destructive)
#   ADRs: ADR-014 (abandonment + inactivity); ADR-011 §9 (published = trusted status);
#         ADR-013 (Ollama-independent core)
#   UI surface: Reviews (home) screen.
#
# Product purpose:
#   The reviews home: a scannable list of per-review CARDS (period, workflow status + progress, source
#   readiness, finding count + severity, lifecycle, and the next recommended action) — not a bare
#   table. Selecting a card sets the active review; Open navigates into it. A first-run welcome shows
#   when the database is empty. Each card also offers explicit, reversible abandon/resume (ADR-014).
#
# Trust / lifecycle constraints:
#   - All values come from the real read-only services (reviews/status, findings, lifecycle) — no
#     manufactured metrics. Navigating here never silently changes the active review (Phase 6.4a):
#     refresh re-highlights the active review's card by cycle_id and only defaults to the first card
#     when nothing is active. Abandonment is non-destructive. No AI dependency.
from __future__ import annotations
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QPushButton, QLabel, QScrollArea, QFrame,
)
from finsight.delivery.desktop.components import SectionHeader
from finsight.delivery.desktop.components.first_run import build_first_run_card, FIRST_RUN_LEAD
from finsight.delivery.desktop.views.workflow_meta import STEPS as WORKFLOW_STEPS, gates
from finsight.delivery.desktop import presentation as pres
from finsight.delivery.desktop.theme import tokens as t

# Next recommended action per persisted workflow state (guides the reviewer to what's next).
_NEXT_ACTION = {
    "Created": "Upload the GED and Budget Tracker sources.",
    "Intake": "Process the uploaded sources to check readiness.",
    "Processed": "Verify the extracted data to certify the source.",
    "Verified": "Run the deterministic analysis.",
    "Analyzed": "Generate the leadership summary.",
    "Summarized": "Export the review package.",
    "Exported": "Review complete — revisit any step from the Workflow.",
}


class ReviewCard(QFrame):
    """One review as a rich, clickable card. Emits selected(cid) on click and opened(cid) on Open."""

    selected = Signal(str)
    opened = Signal(str)

    def __init__(self, cid: str, parent=None):
        super().__init__(parent)
        self._cid = cid
        self.setProperty("role", "reviewCard")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(t.SP_4, t.SP_3, t.SP_4, t.SP_3)
        outer.setSpacing(t.SP_2)

        top = QHBoxLayout()
        top.setSpacing(t.SP_2)
        self._title = QLabel(""); self._title.setProperty("role", "cardTitle")
        top.addWidget(self._title)
        self._status = QLabel(""); self._status.setProperty("role", "statusPill")
        top.addWidget(self._status)
        self._disposition = QLabel(""); self._disposition.setProperty("role", "pillAbandoned")
        self._disposition.setVisible(False)
        top.addWidget(self._disposition)
        top.addStretch(1)
        self._open = QPushButton("Open"); self._open.setProperty("role", "primary")
        self._open.clicked.connect(lambda: self.opened.emit(self._cid))
        top.addWidget(self._open)
        outer.addLayout(top)

        self._metrics = QLabel(""); self._metrics.setProperty("role", "context"); self._metrics.setWordWrap(True)
        outer.addWidget(self._metrics)

        action_row = QHBoxLayout()
        self._next = QLabel(""); self._next.setProperty("role", "kvVal"); self._next.setWordWrap(True)
        action_row.addWidget(self._next, 1)
        self._lifecycle_btn = QPushButton(""); self._lifecycle_btn.setProperty("role", "secondary")
        action_row.addWidget(self._lifecycle_btn)
        outer.addLayout(action_row)

    def cycle_id(self) -> str:
        return self._cid

    def set_data(self, *, period, state, progress, findings, severity, readiness, next_action,
                 abandoned, inactivity, active):
        self._title.setText(period)
        self._status.setText(pres.state_label(state))
        self._disposition.setVisible(abandoned)
        self._disposition.setText("Abandoned")
        # metrics line: progress · readiness · findings + severity  (+ inactivity when present)
        parts = [progress, readiness, findings]
        if severity:
            parts.append(severity)
        if inactivity:
            parts.append(inactivity)
        self._metrics.setText("   ·   ".join(p for p in parts if p))
        self._next.setText(("This review is abandoned — resume it to continue."
                            if abandoned else "Next:  " + next_action))
        self._lifecycle_btn.setText("Resume review" if abandoned else "Mark abandoned")
        self.setProperty("role", "reviewCardActive" if active else "reviewCard")
        self.style().unpolish(self); self.style().polish(self)

    def lifecycle_button(self) -> QPushButton:
        return self._lifecycle_btn

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self._cid)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.opened.emit(self._cid)
        super().mouseDoubleClickEvent(event)


class ReviewsView(QWidget):
    """Reviews home: rich per-review cards (or a first-run welcome when the database is empty)."""

    reviewActivated = Signal(str)   # cycle_id when a review is opened
    newReviewRequested = Signal()   # user asked to create a new review

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._c = controller
        self._selected_cid = None
        self._cards = {}                       # cycle_id -> ReviewCard

        root = QVBoxLayout(self)
        root.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        root.setSpacing(t.SP_3)
        header_row = QHBoxLayout()
        header_row.addWidget(SectionHeader("Reviews", "Your monthly reviews — select one to open it."), 1)
        self._new_btn = QPushButton("New review")
        self._new_btn.setProperty("role", "primary")
        self._new_btn.clicked.connect(self.newReviewRequested.emit)
        header_row.addWidget(self._new_btn)
        root.addLayout(header_row)

        self._stack = QStackedWidget()
        # card list (scrollable)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        holder = QWidget(); holder.setMaximumWidth(1040)
        self._list = QVBoxLayout(holder)
        self._list.setContentsMargins(0, 0, 0, 0)
        self._list.setSpacing(t.SP_2)
        self._list.setAlignment(Qt.AlignmentFlag.AlignTop)
        wrap = QWidget(); wl = QHBoxLayout(wrap); wl.setContentsMargins(0, 0, 0, 0)
        wl.addWidget(holder); wl.addStretch(1)
        scroll.setWidget(wrap)
        self._stack.addWidget(scroll)
        first_run, self._first_run_btn = build_first_run_card(self.newReviewRequested.emit)
        self._stack.addWidget(first_run)
        root.addWidget(self._stack, 1)

        controller.reviewDispositionChanged.connect(lambda _c: self.refresh())
        self.refresh()

    # --- rendering ---
    def _clear(self):
        while self._list.count():
            item = self._list.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None); w.deleteLater()
        self._cards = {}

    def refresh(self) -> None:
        rows = self._c.reviews_with_status()
        active = self._c.active_review_id
        self._stack.setCurrentIndex(0 if rows else 1)       # cards, else first-run welcome
        self._clear()
        if not rows:
            self._selected_cid = None
            return
        # Non-destructive selection (Phase 6.4a): highlight the ACTIVE review; only default-select the
        # first card when nothing is active — rendering here never changes the active review.
        if active and any(r.cycle_id == active for r in rows):
            self._selected_cid = active
        elif not active:
            self._c.select_review(rows[0].cycle_id)          # default-select first when none active
            self._selected_cid = rows[0].cycle_id
        else:
            self._selected_cid = active                      # active not in list (rare) — leave unchanged
        for r in rows:
            card = ReviewCard(r.cycle_id)
            card.selected.connect(self._on_select)
            card.opened.connect(self._on_open_cid)
            card.lifecycle_button().clicked.connect(lambda _=False, cid=r.cycle_id: self._on_lifecycle(cid))
            self._cards[r.cycle_id] = card
            self._list.addWidget(card)
            self._populate(card, r)

    def _populate(self, card, r):
        state = r.state
        done, _enabled, _current = gates(state)
        progress = "%d/%d steps" % (sum(1 for d in done if d), len(WORKFLOW_STEPS))
        findings = self._c.findings(r.cycle_id)
        crit = sum(1 for f in findings if f.severity == "Critical")
        high = sum(1 for f in findings if f.severity == "High")
        sev = ", ".join(p for p in ("%d critical" % crit if crit else "",
                                    "%d high" % high if high else "") if p)
        status = self._c.review_lifecycle_status(r.cycle_id)
        abandoned = status.disposition.value == "Abandoned"
        readiness = "Source verified" if state in ("Verified", "Analyzed", "Summarized", "Exported") \
            else ("Source processed" if state == "Processed" else "Awaiting sources")
        card.set_data(
            period=pres.period_text(r.month, r.year), state=state, progress=progress,
            findings=("%d finding(s)" % r.finding_count), severity=sev, readiness=readiness,
            next_action=_NEXT_ACTION.get(state, ""), abandoned=abandoned,
            inactivity=(status.message or ""), active=(r.cycle_id == self._selected_cid))

    # --- interaction ---
    def _on_select(self, cid):
        self._c.select_review(cid)             # controller no-op if already active (non-destructive)
        self._selected_cid = cid
        self._reselect()

    def _reselect(self):
        for cid, card in self._cards.items():
            card.setProperty("role", "reviewCardActive" if cid == self._selected_cid else "reviewCard")
            card.style().unpolish(card); card.style().polish(card)

    def _on_open_cid(self, cid):
        self._c.select_review(cid)
        self._selected_cid = cid
        self.reviewActivated.emit(cid)

    def _on_lifecycle(self, cid):
        status = self._c.review_lifecycle_status(cid)
        if status.disposition.value == "Abandoned":
            self._c.resume_abandoned_review(cid)
        else:
            self._c.abandon_review(cid)         # explicit, audited, non-destructive; reversible

    # --- public seams (stable API for tests) ---
    def selected_review_id(self):
        return self._selected_cid

    def review_periods(self):
        """Human-readable period text shown on each review card (in list order)."""
        return [card._title.text() for card in self._cards.values()]

    def refresh_preserves_active_review(self) -> bool:
        active = self._c.active_review_id
        return active is None or self._selected_cid == active

    def first_run_message(self) -> str:
        return FIRST_RUN_LEAD if self._stack.currentIndex() == 1 else ""

    def primary_action_text(self) -> str:
        return self._first_run_btn.text()

    def lifecycle_message(self) -> str:
        card = self._cards.get(self._selected_cid)
        return card._next.text() if card is not None else ""

    def lifecycle_action_text(self) -> str:
        card = self._cards.get(self._selected_cid)
        return card.lifecycle_button().text() if card is not None else ""

    def _refresh_lifecycle(self) -> None:      # retained seam; a full refresh re-renders lifecycle state
        self.refresh()

    def _on_open(self, cid_or_index):
        cid = cid_or_index if isinstance(cid_or_index, str) else self._selected_cid
        if cid:
            self._on_open_cid(cid)
