from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QLabel
from finsight.delivery.desktop.components import SectionHeader, WorkflowRail, EmptyState
from finsight.delivery.desktop.theme import tokens as t

# Canonical nine-step review workflow (preserved from the current product sequence).
WORKFLOW_STEPS = [
    "Review Setup", "Data Upload", "Upload Validation", "Processing", "Verification",
    "Analysis", "Findings", "Leadership Summary", "Export",
]

# Presentation-only mapping from the persisted CycleState to the workflow step the review has
# reached. This is display logic, not business logic — it changes no state and computes nothing.
_STATE_TO_STEP = {
    "Created": 0, "Intake": 1, "Validated": 2, "Processed": 3, "Verified": 4,
    "Analyzed": 6, "Summarized": 7, "Exported": 8,
}


class OverviewView(QWidget):
    """Read-only review overview: identity, state, the nine-step workflow rail, finding count and
    the deterministic Budget Health summary."""

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._c = controller

        root = QVBoxLayout(self)
        root.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        root.setSpacing(t.SP_3)

        self._stack = QStackedWidget()
        root.addWidget(self._stack, 1)

        # content page
        self._page = QWidget()
        page = QVBoxLayout(self._page)
        page.setContentsMargins(0, 0, 0, 0)
        page.setSpacing(t.SP_4)
        self._header = SectionHeader("Review Overview", "")
        page.addWidget(self._header)

        body = QHBoxLayout()
        body.setSpacing(t.SP_6)

        # left: workflow rail
        rail_box = QVBoxLayout()
        rail_lbl = QLabel("WORKFLOW")
        rail_lbl.setProperty("role", "navGroup")
        rail_box.addWidget(rail_lbl)
        self._rail = WorkflowRail(WORKFLOW_STEPS)
        rail_box.addWidget(self._rail)
        rail_box.addStretch(1)
        rail_wrap = QWidget()
        rail_wrap.setLayout(rail_box)
        body.addWidget(rail_wrap)

        # right: status + summary
        right = QVBoxLayout()
        right.setSpacing(t.SP_3)
        self._status_lbl = QLabel()
        self._status_lbl.setProperty("role", "kvVal")
        right.addWidget(self._status_lbl)

        sum_hdr = QLabel("BUDGET HEALTH SUMMARY")
        sum_hdr.setProperty("role", "navGroup")
        right.addWidget(sum_hdr)
        self._summary_lbl = QLabel()
        self._summary_lbl.setProperty("role", "kvVal")
        self._summary_lbl.setWordWrap(True)
        self._summary_lbl.setTextFormat(Qt.TextFormat.PlainText)  # summary is plain text, never rich
        right.addWidget(self._summary_lbl)
        right.addStretch(1)
        right_wrap = QWidget()
        right_wrap.setLayout(right)
        body.addWidget(right_wrap, 1)

        page.addLayout(body)
        self._stack.addWidget(self._page)

        self._empty = EmptyState(
            "No review selected",
            "Choose a review from the Reviews screen to see its workflow and summary.",
        )
        self._stack.addWidget(self._empty)

        self.refresh()

    def refresh(self) -> None:
        cid = self._c.active_review_id
        if not cid:
            self._stack.setCurrentWidget(self._empty)
            return
        status = self._c.review_status(cid)
        if status is None:
            self._stack.setCurrentWidget(self._empty)
            return
        self._header.set_subtitle(f"{status.month} {status.year}  ·  State: {status.state}")
        self._rail.set_current(_STATE_TO_STEP.get(status.state, 0))
        self._status_lbl.setText(f"Findings: {status.finding_count}")

        summary = self._c.summary(cid)
        if summary and summary.lines:
            text = f"Status: {summary.status_label}\n\n" + "\n".join("• " + ln for ln in summary.lines)
        elif summary:
            text = f"Status: {summary.status_label}\n\nNo findings for this review."
        else:
            text = "Summary unavailable."
        self._summary_lbl.setText(text)
        self._stack.setCurrentWidget(self._page)
