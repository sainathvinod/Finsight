# Cross-review Dashboard / portfolio overview (Phase 5.3). Deterministic read-model data only —
# no AI, no new financial calculation, no workflow mutation, no repository access. Shows portfolio
# KPIs, a "Needs attention" queue, and recent reviews; falls back to the shared first-run welcome
# when the database is empty.
from __future__ import annotations
from typing import Dict, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget, QScrollArea, QLabel, QPushButton,
)
from finsight.delivery.desktop.components import SectionHeader
from finsight.delivery.desktop.components.first_run import build_first_run_card
from finsight.delivery.desktop.views.workflow_meta import STEPS as WORKFLOW_STEPS, gates
from finsight.delivery.desktop import presentation as pres
from finsight.delivery.desktop.theme import tokens as t


def _card(label: str, value: str, detail: str = "") -> QWidget:
    card = QWidget()
    card.setProperty("role", "card")
    lay = QVBoxLayout(card)
    lay.setContentsMargins(t.SP_3, t.SP_3, t.SP_3, t.SP_3)
    lay.setSpacing(2)
    lbl = QLabel(label)
    lbl.setProperty("role", "cardLabel")
    lay.addWidget(lbl)
    val = QLabel(value)
    val.setProperty("role", "cardValue")
    lay.addWidget(val)
    if detail:
        det = QLabel(detail)
        det.setProperty("role", "cardDetail")
        det.setWordWrap(True)
        lay.addWidget(det)
    return card


class DashboardView(QWidget):
    """Portfolio home: at-a-glance status across all review cycles."""

    openReviewRequested = Signal(str)     # cycle_id
    newReviewRequested = Signal()

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._c = controller
        self._summary = None
        self._empty_code = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self._stack = QStackedWidget()
        root.addWidget(self._stack, 1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        page = QWidget()
        page.setMaximumWidth(1040)
        self._page_lay = QVBoxLayout(page)
        self._page_lay.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        self._page_lay.setSpacing(t.SP_4)
        self._page_lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        head = QHBoxLayout()
        self._header = SectionHeader("Dashboard", "Portfolio status across all review cycles.")
        head.addWidget(self._header, 1)
        self._new_btn = QPushButton("New review")
        self._new_btn.setProperty("role", "primary")
        self._new_btn.clicked.connect(self.newReviewRequested.emit)
        head.addWidget(self._new_btn)
        self._page_lay.addLayout(head)

        self._kpis = QGridLayout()
        self._kpis.setSpacing(t.SP_3)
        self._page_lay.addLayout(self._kpis)

        self._attention_lbl = QLabel("Needs attention")
        self._attention_lbl.setProperty("role", "navGroup")
        self._page_lay.addWidget(self._attention_lbl)
        self._attention_box = QVBoxLayout()
        self._attention_box.setSpacing(t.SP_2)
        self._page_lay.addLayout(self._attention_box)

        self._recent_lbl = QLabel("Recent reviews")
        self._recent_lbl.setProperty("role", "navGroup")
        self._page_lay.addWidget(self._recent_lbl)
        self._recent_box = QVBoxLayout()
        self._recent_box.setSpacing(t.SP_2)
        self._page_lay.addLayout(self._recent_box)

        wrap = QWidget()
        wl = QHBoxLayout(wrap)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.addWidget(page)
        wl.addStretch(1)
        scroll.setWidget(wrap)
        self._stack.addWidget(scroll)

        first_run, self._first_run_btn = build_first_run_card(self.newReviewRequested.emit)
        self._stack.addWidget(first_run)
        self.refresh()

    # --- rendering ---
    def _clear(self, box) -> None:
        while box.count():
            item = box.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def _clear_grid(self) -> None:
        while self._kpis.count():
            item = self._kpis.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def _row(self, period: str, state: str, extra: str, cid: str) -> QWidget:
        row = QWidget()
        row.setProperty("role", "card")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(t.SP_3, t.SP_2, t.SP_3, t.SP_2)
        lay.setSpacing(t.SP_3)
        period_lbl = QLabel(period)
        period_lbl.setProperty("role", "kvVal")
        period_lbl.setMinimumWidth(120)
        lay.addWidget(period_lbl)
        state_lbl = QLabel(pres.state_label(state))
        state_lbl.setProperty("role", "context")
        state_lbl.setMinimumWidth(130)
        lay.addWidget(state_lbl)
        extra_lbl = QLabel(extra)
        extra_lbl.setProperty("role", "context")
        extra_lbl.setWordWrap(True)
        lay.addWidget(extra_lbl, 1)
        open_btn = QPushButton("Open")
        open_btn.setProperty("role", "secondary")
        open_btn.clicked.connect(lambda: self.open_review_from_dashboard(cid))
        lay.addWidget(open_btn)
        return row

    def refresh(self) -> None:
        self._summary = self._c.portfolio()
        s = self._summary
        if s.total_reviews == 0:
            self._empty_code = "first_run"
            self._stack.setCurrentIndex(1)
            return
        self._empty_code = ""
        self._stack.setCurrentIndex(0)

        self._clear_grid()
        recent0 = s.recent_reviews[0] if s.recent_reviews else None
        most_recent = pres.period_text(recent0.month, recent0.year) if recent0 else "—"
        cards = [
            _card("Total reviews", str(s.total_reviews), f"Most recent: {most_recent}"),
            _card("Needs attention", str(s.reviews_needing_attention), "Reviews with issues or in progress"),
            _card("Total findings", str(s.total_findings), ""),
            _card("Critical findings", str(s.critical_findings), "Across all reviews"),
            _card("High findings", str(s.high_findings), "Across all reviews"),
            _card("Completed", str(s.completed_reviews), "Exported reviews"),
        ]
        for i, card in enumerate(cards):
            self._kpis.addWidget(card, i // 3, i % 3)

        self._clear(self._attention_box)
        if s.attention_items:
            for a in s.attention_items:
                extra = a.reason + (f"  ·  {a.finding_count} finding(s)" if a.finding_count else "")
                self._attention_box.addWidget(
                    self._row(pres.period_text(a.month, a.year), a.state, extra, a.cycle_id))
        else:
            none_lbl = QLabel("Nothing needs attention — all reviews are complete and clean.")
            none_lbl.setProperty("role", "context")
            self._attention_box.addWidget(none_lbl)

        self._clear(self._recent_box)
        for r in s.recent_reviews:
            done, _enabled, current = gates(r.state)
            progress = f"{sum(1 for d in done if d)}/{len(WORKFLOW_STEPS)} steps"
            sev = []
            if r.critical:
                sev.append(f"{r.critical} critical")
            if r.high:
                sev.append(f"{r.high} high")
            extra = f"{progress}  ·  {r.finding_count} finding(s)" + (
                "  ·  " + ", ".join(sev) if sev else "")
            self._recent_box.addWidget(
                self._row(pres.period_text(r.month, r.year), r.state, extra, r.cycle_id))

    # --- public seams ---
    def portfolio_summary(self):
        return self._summary

    def dashboard_kpis(self) -> Dict[str, object]:
        s = self._summary
        if s is None:
            return {}
        recent0 = s.recent_reviews[0] if s.recent_reviews else None
        return {
            "total_reviews": s.total_reviews,
            "needs_attention": s.reviews_needing_attention,
            "total_findings": s.total_findings,
            "critical": s.critical_findings,
            "high": s.high_findings,
            "completed": s.completed_reviews,
            "most_recent_period": pres.period_text(recent0.month, recent0.year) if recent0 else "",
        }

    def attention_review_ids(self) -> List[str]:
        return [a.cycle_id for a in (self._summary.attention_items if self._summary else ())]

    def recent_review_ids(self) -> List[str]:
        return [r.cycle_id for r in (self._summary.recent_reviews if self._summary else ())]

    def dashboard_empty_state(self) -> str:
        return self._empty_code

    def open_review_from_dashboard(self, cycle_id: str) -> None:
        self.openReviewRequested.emit(cycle_id)

    def dashboard_primary_action_text(self) -> str:
        btn = self._first_run_btn if self._empty_code == "first_run" else self._new_btn
        return btn.text()
