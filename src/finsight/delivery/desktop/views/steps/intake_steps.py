from __future__ import annotations
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
                               QSpinBox, QPushButton, QProgressBar, QFileDialog)
from finsight.delivery.desktop.components import SectionHeader  # noqa: F401 (re-exported convenience)
from finsight.delivery.desktop.components.form_row import FormRow
from finsight.delivery.desktop.views.steps.base import StepPanel
from finsight.delivery.desktop import presentation as pres
from finsight.application.errors import FinsightAppError
from finsight.application.source_format import QT_FILE_FILTER as _WORKBOOKS, ACCEPTED_LABEL
from finsight.delivery.desktop.theme import tokens as t

_MONTHS = ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"]

# Approved Release-1 sources (backend-supported) and honestly-deferred future types (FR-004/NFR-045).
_DEFERRED_SOURCES = "Invoices, resource sheets, contracts/SOWs, and rate cards are planned and not yet accepted."

# Plain explanation of what the review period is and why it matters (§5). No invented rule — the
# period simply identifies the month a review belongs to (FR-005, F-01-03).
_PERIOD_EXPLAINER = (
    "The review period is the month this review belongs to. FinSight uses it to keep each month's "
    "files and findings separate, to prevent mixing periods, and to list this review on your home "
    "screen. Choose the month and year your financial data is for."
)


class SetupPanel(StepPanel):
    """First guided step (§5): create a review by choosing its period. Explains the period, prevents
    duplicate periods with a live warning + one-click open of the existing review, and offers clear
    Back (to Home) / Next (Create). The entered month/year are preserved across navigation."""

    backRequested = Signal()

    def __init__(self, controller):
        super().__init__(controller, "Create Review — Review Period",
                         "Choose the month this review is for.")
        # --- period explainer ---
        self._explainer = QLabel(_PERIOD_EXPLAINER)
        self._explainer.setProperty("role", "context")
        self._explainer.setWordWrap(True)
        self.content.addWidget(self._explainer)

        # --- create form ---
        self._form = QWidget()
        fl = QVBoxLayout(self._form)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(t.SP_3)
        self._month = QComboBox()
        self._month.addItems(_MONTHS)
        self._month.setCurrentIndex(6)                    # July, the demo period
        self._year = QSpinBox()                           # constrained numeric year
        self._year.setRange(2000, 2100)
        self._year.setValue(2026)
        self._year.setGroupSeparatorShown(False)
        # Prominent, human-readable resulting period (not the internal identifier).
        self._period = QLabel()
        self._period.setProperty("role", "cardValue")
        self._id_hint = QLabel()                          # internal id kept as small secondary detail
        self._id_hint.setProperty("role", "context")
        self._back = QPushButton("← Back to Home")
        self._back.setProperty("role", "secondary")
        self._open_existing = QPushButton("Open existing review")
        self._open_existing.setProperty("role", "secondary")
        self._open_existing.setVisible(False)
        self._create = QPushButton("Create review")
        self._create.setProperty("role", "primary")       # the one primary action on this screen
        fl.addWidget(FormRow("Month", self._month))
        fl.addWidget(FormRow("Year", self._year))
        fl.addWidget(FormRow("Review period", self._period))
        fl.addWidget(self._id_hint)
        row = QHBoxLayout()
        row.addWidget(self._back)
        row.addStretch(1)
        row.addWidget(self._open_existing)
        row.addWidget(self._create)
        fl.addLayout(row)
        self.content.addWidget(self._form)

        # --- existing-review note ---
        self._note = QLabel()
        self._note.setProperty("role", "kvVal")
        self._note.setWordWrap(True)
        self.content.addWidget(self._note)

        self._month.currentIndexChanged.connect(self._derive)
        self._year.valueChanged.connect(self._derive)
        self._create.clicked.connect(self._on_create)
        self._back.clicked.connect(self.backRequested.emit)
        self._open_existing.clicked.connect(self._on_open_existing)
        self._derive()

    def _derived_id(self) -> str:
        return f"{self._year.value()}-{self._month.currentIndex() + 1:02d}"

    def _derive(self):
        self._period.setText(pres.period_text(self._month.currentText(), str(self._year.value())))
        self._id_hint.setText(f"Internal identifier: {self._derived_id()}")
        self._check_period()

    def _check_period(self):
        """Live duplicate guard (§5): if a review already exists for the chosen period, warn clearly
        and offer to open it instead of creating a colliding one. Runs only while creating (no active
        review); never overrides a create error just surfaced."""
        if self.cid():
            return
        existing = self._c.review_status(self._derived_id())
        if existing is not None:
            self.show_warning(
                f"A review for {pres.period_text(existing.month, existing.year)} already exists "
                f"({pres.state_label(existing.state)}). Open it to continue, or choose a different "
                "month or year.")
            self._create.setEnabled(False)
            self._open_existing.setVisible(True)
        else:
            self.clear_message()
            self._create.setEnabled(True)
            self._open_existing.setVisible(False)

    def _on_open_existing(self):
        self._c.select_review(self._derived_id())

    def _on_create(self):
        self.clear_message()
        month, year = self._month.currentText(), str(self._year.value())
        if not year:                                      # validate before creation (QSpinBox guarantees)
            self.show_warning("Enter a valid year.")
            return
        try:
            self._c.create_review(self._derived_id(), month, year)
        except FinsightAppError as e:
            self.show_error(e)

    def displayed_review_period(self) -> str:             # public seam
        cid = self.cid()
        if cid:
            status = self._c.review_status(cid)
            if status is not None:
                return pres.period_text(status.month, status.year)
        return self._period.text()

    def refresh(self):
        cid = self.cid()
        if cid:
            status = self._c.review_status(cid)
            if status is not None:
                self.set_subtitle(f"{pres.period_text(status.month, status.year)}  ·  "
                                  f"{pres.state_label(status.state)}")
                self._note.setText(
                    f"Review “{pres.period_text(status.month, status.year)}” already exists "
                    f"({pres.state_label(status.state)}). Continue with Data Upload, or revisit a "
                    "completed step from the rail.")
            self._explainer.setVisible(False)
            self._form.setVisible(False)
            self._note.setVisible(True)
        else:
            self.set_subtitle("Choose the month this review is for.")
            self._explainer.setVisible(True)
            self._form.setVisible(True)
            self._note.setVisible(False)
            self._check_period()                          # re-evaluate duplicate state on (re)entry


class UploadPanel(StepPanel):
    def __init__(self, controller):
        super().__init__(controller, "Data Upload",
                         "Select the two required source workbooks. Your source files are never modified.")
        self._ged = None
        self._bud = None
        self._ged_field = QLineEdit(); self._ged_field.setReadOnly(True)
        self._ged_field.setPlaceholderText(ACCEPTED_LABEL)
        self._bud_field = QLineEdit(); self._bud_field.setReadOnly(True)
        self._bud_field.setPlaceholderText(ACCEPTED_LABEL)
        ged_btn = QPushButton("Choose GED…"); ged_btn.setProperty("role", "secondary")
        bud_btn = QPushButton("Choose Budget…"); bud_btn.setProperty("role", "secondary")
        ged_row = QWidget(); gl = QHBoxLayout(ged_row); gl.setContentsMargins(0, 0, 0, 0); gl.setSpacing(t.SP_2)
        gl.addWidget(self._ged_field, 1); gl.addWidget(ged_btn)
        bud_row = QWidget(); bl = QHBoxLayout(bud_row); bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(t.SP_2)
        bl.addWidget(self._bud_field, 1); bl.addWidget(bud_btn)
        self.content.addWidget(FormRow("General Expense Detail  (required)", ged_row, label_width=220))
        self._ged_purpose = QLabel("The month's expense transactions to analyze.")
        self._ged_purpose.setProperty("role", "context"); self.content.addWidget(self._ged_purpose)
        self.content.addWidget(FormRow("Budget Tracker  (required)", bud_row, label_width=220))
        self._bud_purpose = QLabel("Approved budget and actuals to compare spending against.")
        self._bud_purpose.setProperty("role", "context"); self.content.addWidget(self._bud_purpose)
        self._deferred = QLabel(_DEFERRED_SOURCES)     # honest: not silently pretended as accepted
        self._deferred.setProperty("role", "context"); self._deferred.setWordWrap(True)
        self.content.addWidget(self._deferred)
        self._upload = QPushButton("Upload files"); self._upload.setProperty("role", "primary")
        self._upload.setEnabled(False)
        row = QHBoxLayout(); row.addStretch(1); row.addWidget(self._upload)
        self.content.addLayout(row)
        ged_btn.clicked.connect(self._choose_ged)
        bud_btn.clicked.connect(self._choose_bud)
        self._upload.clicked.connect(self._on_upload)

    def _choose_ged(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select GED workbook", "", _WORKBOOKS)
        if path:
            self.set_ged(path)

    def _choose_bud(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Budget workbook", "", _WORKBOOKS)
        if path:
            self.set_budget(path)

    def set_ged(self, path):    # also used by tests to inject a selection
        self._ged = path; self._ged_field.setText(path); self._sync()

    def set_budget(self, path):
        self._bud = path; self._bud_field.setText(path); self._sync()

    def _sync(self):
        self._upload.setEnabled(bool(self._ged and self._bud and self.cid()))

    def _on_upload(self):
        self.clear_message()
        try:
            self._c.upload(self.cid(), self._ged, self._bud)
        except FinsightAppError as e:
            self.show_error(e)

    def refresh(self):
        self._sync()
        if self.cid() and self._c.workflow_state(self.cid()) not in (None, "Created"):
            self.show_info("Files were recorded for this review. Re-select and upload again to continue "
                           "in a new session.")
        else:
            self.clear_message()


class ValidationPanel(StepPanel):
    def __init__(self, controller):
        super().__init__(controller, "Upload Validation",
                         "Validation, row counts, and provenance from the processing pipeline.")
        self._body = QVBoxLayout(); self._body.setSpacing(t.SP_2)
        holder = QWidget(); holder.setLayout(self._body)
        self.content.addWidget(holder)

    def _clear_body(self):
        while self._body.count():
            item = self._body.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None); w.deleteLater()

    def _line(self, key, val):
        self._body.addWidget(FormRow(key, self._value_label(val), label_width=170))

    def _value_label(self, text):
        lbl = QLabel(str(text)); lbl.setProperty("role", "kvVal"); lbl.setWordWrap(True)
        return lbl

    def refresh(self):
        self._clear_body()
        cid = self.cid()
        snap = self._c.validation_snapshot(cid) if cid else None
        if snap is None:
            self.show_info("Run Processing to produce validation results.")
            return
        self.clear_message()
        self._line("Accepted GED rows", snap.ged_valid)
        self._line("Accepted budget rows", snap.budget_valid)
        self._line("Quarantined rows", snap.quarantined)
        self._line("Dataset available", "Yes" if snap.available else "No")
        if snap.rejected_reason:
            self._line("Rejection reason", snap.rejected_reason)
        for cap, val in (snap.readiness or {}).items():
            self._line("Readiness · " + str(cap), val)
        for item in snap.provenance:
            self._line("Provenance · " + item.doc_type,
                       f"{item.name}  ·  {item.period}  ·  {item.fingerprint[:12]}…")


class ProcessingPanel(StepPanel):
    def __init__(self, controller):
        super().__init__(controller, "Processing",
                         "Run the deterministic extraction and normalization pipeline.")
        self._run = QPushButton("Run processing"); self._run.setProperty("role", "secondary")
        self._progress = QProgressBar(); self._progress.setRange(0, 0)  # indeterminate (no measurable %)
        self._progress.setVisible(False); self._progress.setFixedWidth(180)
        self._status = QLabel(); self._status.setProperty("role", "sectionSub")
        row = QHBoxLayout(); row.setSpacing(t.SP_3)
        row.addWidget(self._run); row.addWidget(self._progress); row.addWidget(self._status)
        row.addStretch(1)
        self.content.addLayout(row)
        self._run.clicked.connect(self._on_run)
        controller.processingChanged.connect(self._set_busy)

    def _on_run(self):
        self.clear_message()
        self._run.setEnabled(False)
        self._c.process_async(self.cid(), on_result=self._done, on_error=self._failed)

    def _done(self, val):
        if val.available:
            self.show_success(f"Processed: {val.ged_valid} GED rows and {val.budget_valid} budget rows accepted"
                              f"; {val.quarantined} quarantined.")
        else:
            self.show_warning(f"Validation rejected: {val.rejected_reason}")
        self._run.setEnabled(True)

    def _failed(self, exc):
        self.show_error(exc)
        self._run.setEnabled(True)

    def _set_busy(self, busy):
        self._progress.setVisible(busy)
        self._status.setText("Processing…" if busy else "")
        self._run.setEnabled(not busy)

    def refresh(self):
        cid = self.cid()
        state = self._c.workflow_state(cid) if cid else None
        has_files = bool(cid and self._c.has_session_context(cid))
        self._run.setEnabled(has_files)
        if not has_files:
            self.show_info("Upload the source files (Data Upload) before processing.")
        elif state in ("Processed", "Verified", "Analyzed", "Summarized", "Exported"):
            self.show_success("Processing complete. See Upload Validation for details.")
        else:
            self.clear_message()
