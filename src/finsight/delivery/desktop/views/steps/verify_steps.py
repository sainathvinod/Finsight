from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from finsight.delivery.desktop.views.steps.base import StepPanel
from finsight.delivery.desktop.views.findings_view import FindingsView
from finsight.delivery.desktop.views.workflow_meta import rank, RANK
from finsight.application.errors import FinsightAppError


class VerificationPanel(StepPanel):
    def __init__(self, controller):
        super().__init__(controller, "Verification",
                         "Review the extracted data, then explicitly approve it for analysis.")
        self._detail = QLabel(); self._detail.setProperty("role", "kvVal"); self._detail.setWordWrap(True)
        self.content.addWidget(self._detail)
        self._approve = QPushButton("Approve && verify data"); self._approve.setProperty("role", "secondary")
        row = QHBoxLayout(); row.addWidget(self._approve); row.addStretch(1)
        self.content.addLayout(row)
        self._approve.clicked.connect(self._on_verify)

    def _on_verify(self):
        self.clear_message()
        try:
            self._c.verify(self.cid())
            self.show_success("Data verified. Analysis is now available.")
        except FinsightAppError as e:
            self.show_error(e)

    def refresh(self):
        cid = self.cid()
        state = self._c.workflow_state(cid) if cid else None
        snap = self._c.validation_snapshot(cid) if cid else None
        if state and rank(state) >= RANK["Verified"]:
            self._detail.setText("This review's data has been verified and certified as the basis for analysis.")
            self._approve.setEnabled(False)
            self.clear_message()
        elif snap is None:
            self._detail.setText("")
            self._approve.setEnabled(False)
            self.show_info("Process the uploaded data (Processing) before verification.")
        elif snap.rejected_reason:
            self._detail.setText("")
            self._approve.setEnabled(False)
            self.show_warning(f"Rejected or unavailable data cannot be verified: {snap.rejected_reason}")
        else:
            self._detail.setText(
                f"You are approving {snap.ged_valid} GED rows and {snap.budget_valid} budget rows as the "
                f"certified basis for analysis ({snap.quarantined} row(s) quarantined). "
                "This does not modify the source files.")
            self._approve.setEnabled(True)
            self.clear_message()


class AnalysisPanel(StepPanel):
    def __init__(self, controller):
        super().__init__(controller, "Analysis",
                         "Run the deterministic rules engine on the verified data.")
        self._run = QPushButton("Run analysis"); self._run.setProperty("role", "secondary")
        row = QHBoxLayout(); row.addWidget(self._run); row.addStretch(1)
        self.content.addLayout(row)
        self._detail = QLabel(); self._detail.setProperty("role", "kvVal"); self._detail.setWordWrap(True)
        self._detail.setTextFormat(Qt.TextFormat.PlainText)
        self.content.addWidget(self._detail)
        self._run.clicked.connect(self._on_run)

    def _on_run(self):
        self.clear_message()
        try:
            res = self._c.analyze(self.cid())
            self.show_success(f"Analysis complete — {res.finding_count} finding(s).")
            self._detail.setText(
                f"Rule run: {res.run_id}\nConfiguration: {res.config_version}\n"
                f"Input fingerprint: {res.input_fingerprint}\nFindings: {res.finding_count}")
        except FinsightAppError as e:
            self.show_error(e)

    def refresh(self):
        cid = self.cid()
        state = self._c.workflow_state(cid) if cid else None
        r = rank(state)
        if r < RANK["Verified"]:
            self._run.setEnabled(False)
            self._detail.setText("")
            self.show_info("Verification is required before analysis.")
        elif r >= RANK["Analyzed"]:
            self._run.setEnabled(False)
            status = self._c.review_status(cid)
            n = status.finding_count if status else 0
            self._detail.setText(f"Analysis complete — {n} finding(s) persisted. See the Findings step.")
            self.clear_message()
        else:
            self._run.setEnabled(True)
            self._detail.setText("")
            self.clear_message()


class FindingsPanel(QWidget):
    """The Findings step reuses the standalone read-only findings view (table + evidence inspector)."""

    def __init__(self, controller):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self._inner = FindingsView(controller)
        lay.addWidget(self._inner)

    def refresh(self):
        self._inner.refresh()
