# Review Overview — the home/dashboard for the active review (Phase 5.1). Deterministic read-model
# data only: period, state, workflow progress, findings by severity, source readiness, and the next
# recommended action. No AI, no invented metrics, no repository access, no financial logic.
from __future__ import annotations
from typing import Dict

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget, QLabel, QPushButton,
)
from finsight.delivery.desktop.components import SectionHeader, EmptyState
from finsight.delivery.desktop.views.workflow_meta import STEPS as WORKFLOW_STEPS, gates, rank, RANK
from finsight.delivery.desktop import presentation as pres
from finsight.delivery.desktop.theme import tokens as t

_SEVERITIES = ("Critical", "High", "Medium", "Low")


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
    val.setWordWrap(True)
    lay.addWidget(val)
    if detail:
        det = QLabel(detail)
        det.setProperty("role", "cardDetail")
        det.setWordWrap(True)
        lay.addWidget(det)
    return card


class OverviewView(QWidget):
    """At-a-glance review home: what's open, what's done, what remains, and what needs attention."""

    openWorkflowRequested = Signal()

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._c = controller
        self._summary: Dict[str, object] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        root.setSpacing(t.SP_3)
        self._stack = QStackedWidget()
        root.addWidget(self._stack, 1)

        page = QWidget()
        page.setMaximumWidth(980)                     # bounded content width — no giant canvas
        self._page_lay = QVBoxLayout(page)
        self._page_lay.setContentsMargins(0, 0, 0, 0)
        self._page_lay.setSpacing(t.SP_4)
        self._page_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._header = SectionHeader("Review Overview", "")
        self._page_lay.addWidget(self._header)
        self._cards = QGridLayout()
        self._cards.setSpacing(t.SP_3)
        self._page_lay.addLayout(self._cards)

        # next-action bar
        nxt = QHBoxLayout()
        self._next_lbl = QLabel("")
        self._next_lbl.setProperty("role", "kvVal")
        self._next_lbl.setWordWrap(True)
        nxt.addWidget(self._next_lbl, 1)
        self._continue = QPushButton("Continue in Workflow →")
        self._continue.setProperty("role", "primary")
        self._continue.clicked.connect(self.openWorkflowRequested.emit)
        nxt.addWidget(self._continue)
        self._page_lay.addLayout(nxt)

        page_wrap = QWidget()
        wrap = QHBoxLayout(page_wrap)
        wrap.setContentsMargins(0, 0, 0, 0)
        wrap.addWidget(page)
        wrap.addStretch(1)
        self._stack.addWidget(page_wrap)

        self._empty = EmptyState(
            "No review selected",
            "Choose a review from the Reviews screen to see its status, progress, and findings.")
        self._stack.addWidget(self._empty)
        self.refresh()

    def _clear_cards(self):
        while self._cards.count():
            item = self._cards.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def refresh(self) -> None:
        cid = self._c.active_review_id
        status = self._c.review_status(cid) if cid else None
        if status is None:
            self._stack.setCurrentWidget(self._empty)
            self._summary = {}
            return

        period = pres.period_text(status.month, status.year)
        state = status.state
        done, _enabled, current = gates(state)
        done_count = sum(1 for d in done if d)
        total_steps = len(WORKFLOW_STEPS)
        next_step = WORKFLOW_STEPS[current] if current >= 0 else "Review complete"

        findings = self._c.findings(cid) or []
        sev_counts = {s: 0 for s in _SEVERITIES}
        for f in findings:
            key = str(getattr(f, "severity", "")).title()
            if key in sev_counts:
                sev_counts[key] += 1
        sev_detail = "  ".join(f"{s}: {sev_counts[s]}" for s in _SEVERITIES)

        snap = self._c.validation_snapshot(cid)
        if snap is not None:
            source_val = "Ready" if snap.available else "Attention needed"
            source_detail = (f"{snap.ged_valid} GED rows, {snap.budget_valid} budget rows accepted"
                             + (f"; {snap.quarantined} quarantined" if snap.quarantined else ""))
            if snap.rejected_reason:
                source_detail = snap.rejected_reason
        elif rank(state) >= RANK["Processed"]:
            # A review processed in an earlier session: the in-session snapshot isn't loaded, but the
            # persisted state confirms the data was processed.
            source_val, source_detail = "Processed", "Source data was processed in an earlier session."
        else:
            source_val, source_detail = "Not yet processed", "Upload and process the source workbooks."

        attention = sev_counts["Critical"] + sev_counts["High"]
        attention_val = "None" if attention == 0 else f"{attention} to review"

        self._header.set_subtitle(f"{period}  ·  {pres.state_label(state)}")
        self._clear_cards()
        cards = [
            _card("Review period", period, pres.state_label(state)),
            _card("Workflow progress", f"{done_count} of {total_steps} steps", f"Next: {next_step}"),
            _card("Findings", str(len(findings)), sev_detail),
            _card("Needs attention", attention_val, "Critical + High findings"),
            _card("Source data", source_val, source_detail),
        ]
        for i, card in enumerate(cards):
            self._cards.addWidget(card, i // 3, i % 3)

        if current >= 0:
            self._next_lbl.setText(f"Next recommended step:  {next_step}")
            self._continue.setText(f"Go to {next_step} →")
            self._continue.setEnabled(True)
        else:
            self._next_lbl.setText("This review is complete. You can revisit any step from the Workflow.")
            self._continue.setText("Open Workflow →")
            self._continue.setEnabled(True)

        self._summary = {
            "period": period, "state": state, "state_label": pres.state_label(state),
            "steps_done": done_count, "steps_total": total_steps, "next_action": next_step,
            "finding_count": len(findings), "severity": dict(sev_counts),
            "source_ready": snap.available if snap is not None else False,
        }
        self._stack.setCurrentIndex(0)

    # --- public seam ---
    def review_overview_summary(self) -> Dict[str, object]:
        return dict(self._summary)
