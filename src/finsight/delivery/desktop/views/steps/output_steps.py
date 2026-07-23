from __future__ import annotations
import os
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QFileDialog
from finsight.delivery.desktop.views.steps.base import StepPanel
from finsight.delivery.desktop.views.workflow_meta import rank, RANK
from finsight.application.errors import FinsightAppError


class SummaryPanel(StepPanel):
    def __init__(self, controller):
        super().__init__(controller, "Leadership Summary",
                         "Deterministic Budget Health summary. No AI narrative.")
        self._gen = QPushButton("Generate summary"); self._gen.setProperty("role", "secondary")
        row = QHBoxLayout(); row.addWidget(self._gen); row.addStretch(1)
        self.content.addLayout(row)
        self._body = QLabel(); self._body.setProperty("role", "kvVal")
        self._body.setWordWrap(True); self._body.setTextFormat(Qt.TextFormat.PlainText)
        self.content.addWidget(self._body)
        self._gen.clicked.connect(self._on_gen)

    def _on_gen(self):
        self.clear_message()
        try:
            self._c.summarize(self.cid())
            self._render()
            self.show_success("Leadership summary generated.")
        except FinsightAppError as e:
            self.show_error(e)

    def _render(self):
        s = self._c.summary(self.cid())
        if not s:
            self._body.setText("")
            return
        lines = [f"Status: {s.status_label}", f"Findings: {s.finding_count}", ""]
        lines += ["• " + ln for ln in s.lines] if s.lines else ["No findings for this review."]
        self._body.setText("\n".join(lines))

    def refresh(self):
        r = rank(self._c.workflow_state(self.cid()) if self.cid() else None)
        if r < RANK["Analyzed"]:
            self._gen.setEnabled(False)
            self._body.setText("")
            self.show_info("Run analysis before generating the leadership summary.")
            return
        self._render()
        self._gen.setEnabled(r == RANK["Analyzed"])   # advance action only until summarized
        if r >= RANK["Summarized"]:
            self.clear_message()


class ExportPanel(StepPanel):
    def __init__(self, controller):
        super().__init__(controller, "Export",
                         "Export the deterministic review package as JSON. Source files are never modified.")
        self._export = QPushButton("Export…"); self._export.setProperty("role", "secondary")
        self._open = QPushButton("Open containing folder"); self._open.setProperty("role", "secondary")
        self._open.setVisible(False)
        row = QHBoxLayout(); row.addWidget(self._export); row.addWidget(self._open); row.addStretch(1)
        self.content.addLayout(row)
        self._last_dir = None
        self._export.clicked.connect(self._on_export)
        self._open.clicked.connect(self._on_open)

    def _on_export(self):
        cid = self.cid()
        default_name = f"{cid}-finsight-export.json"
        path, _ = QFileDialog.getSaveFileName(self, "Export review", default_name, "JSON (*.json)")
        if not path:
            return
        self.clear_message()
        try:
            result = self._c.export(cid)
        except FinsightAppError as e:
            self.show_error(e)
            return
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(result.json_text)
        except OSError as e:
            self.message.show_message(f"Could not write the export file: {e}", "error")
            return
        self._last_dir = os.path.dirname(path)
        self._open.setVisible(True)
        self.show_success(f"Exported to {path}")

    def _on_open(self):
        if self._last_dir:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._last_dir))

    def refresh(self):
        self._open.setVisible(False)
        r = rank(self._c.workflow_state(self.cid()) if self.cid() else None)
        if r < RANK["Summarized"]:
            self._export.setEnabled(False)
            self.show_info("Generate the leadership summary before export.")
        else:
            self._export.setEnabled(True)
            if r >= RANK["Exported"]:
                self.show_info("This review has been exported. You can export it again to a new file.")
            else:
                self.clear_message()
