from __future__ import annotations
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
                               QPushButton, QProgressBar, QFileDialog)
from finsight.delivery.desktop.components import SectionHeader  # noqa: F401 (re-exported convenience)
from finsight.delivery.desktop.components.form_row import FormRow
from finsight.delivery.desktop.views.steps.base import StepPanel
from finsight.application.errors import FinsightAppError
from finsight.delivery.desktop.theme import tokens as t

_MONTHS = ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"]
_WORKBOOKS = "Workbooks (*.xlsx *.xls);;All files (*)"


class SetupPanel(StepPanel):
    def __init__(self, controller):
        super().__init__(controller, "Review Setup",
                         "Create a new review, or continue the one you selected.")
        # --- create form ---
        self._form = QWidget()
        fl = QVBoxLayout(self._form)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(t.SP_3)
        self._month = QComboBox()
        self._month.addItems(_MONTHS)
        self._year = QLineEdit()
        self._year.setPlaceholderText("e.g. 2026")
        self._cid = QLineEdit()
        self._cid.setReadOnly(True)
        self._cid.setPlaceholderText("generated from month and year")
        self._create = QPushButton("Create review")
        self._create.setProperty("role", "secondary")
        fl.addWidget(FormRow("Month", self._month))
        fl.addWidget(FormRow("Year", self._year))
        fl.addWidget(FormRow("Identifier", self._cid))
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self._create)
        fl.addLayout(row)
        self.content.addWidget(self._form)

        # --- existing-review note ---
        self._note = QLabel()
        self._note.setProperty("role", "kvVal")
        self._note.setWordWrap(True)
        self.content.addWidget(self._note)

        self._month.currentIndexChanged.connect(self._derive)
        self._year.textChanged.connect(self._derive)
        self._create.clicked.connect(self._on_create)
        self._derive()

    def _derive(self):
        y = self._year.text().strip()
        self._cid.setText(f"{y}-{self._month.currentIndex() + 1:02d}" if y else "")

    def _on_create(self):
        self.clear_message()
        try:
            self._c.create_review(self._cid.text().strip(), self._month.currentText(), self._year.text().strip())
        except FinsightAppError as e:
            self.show_error(e)

    def refresh(self):
        cid = self.cid()
        if cid:
            status = self._c.review_status(cid)
            if status is not None:
                self.set_subtitle(f"{status.month} {status.year}  ·  State: {status.state}")
                self._note.setText(
                    f"Review “{status.month} {status.year}” exists (state: {status.state}). "
                    "Continue with Data Upload, or revisit a completed step from the rail.")
            self._form.setVisible(False)
            self._note.setVisible(True)
        else:
            self.set_subtitle("Create a new review, or continue the one you selected.")
            self._form.setVisible(True)
            self._note.setVisible(False)


class UploadPanel(StepPanel):
    def __init__(self, controller):
        super().__init__(controller, "Data Upload",
                         "Select the General Expense Detail and Budget workbooks. Sources are never modified.")
        self._ged = None
        self._bud = None
        self._ged_field = QLineEdit(); self._ged_field.setReadOnly(True)
        self._bud_field = QLineEdit(); self._bud_field.setReadOnly(True)
        ged_btn = QPushButton("Choose GED…"); ged_btn.setProperty("role", "secondary")
        bud_btn = QPushButton("Choose Budget…"); bud_btn.setProperty("role", "secondary")
        ged_row = QWidget(); gl = QHBoxLayout(ged_row); gl.setContentsMargins(0, 0, 0, 0); gl.setSpacing(t.SP_2)
        gl.addWidget(self._ged_field, 1); gl.addWidget(ged_btn)
        bud_row = QWidget(); bl = QHBoxLayout(bud_row); bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(t.SP_2)
        bl.addWidget(self._bud_field, 1); bl.addWidget(bud_btn)
        self.content.addWidget(FormRow("GED file", ged_row))
        self.content.addWidget(FormRow("Budget file", bud_row))
        self._upload = QPushButton("Upload files"); self._upload.setProperty("role", "secondary")
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
