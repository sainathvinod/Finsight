from __future__ import annotations
import os
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QHBoxLayout, QVBoxLayout, QWidget, QLabel, QPushButton, QFileDialog,
                               QFrame)
from finsight.delivery.desktop.components.section_header import SectionHeader
from finsight.delivery.desktop.components.severity import severity_text
from finsight.delivery.desktop.components.financial_map import FinancialMap
from finsight.delivery.desktop.views.steps.base import StepPanel
from finsight.delivery.desktop.views.workflow_meta import rank, RANK
from finsight.application.errors import FinsightAppError
from finsight.delivery.desktop.theme import tokens as t


class SummaryPanel(StepPanel):
    """The visual leadership report (§14): A) leadership summary, B) visual financial map,
    C) account-level detail, D) user-correction disclosure, E) scope & limitations. Every element is a
    view over EXISTING deterministic outputs — the report computes nothing and adds no AI narrative."""

    def __init__(self, controller):
        super().__init__(controller, "Leadership Report",
                         "Deterministic leadership report — a view over the verified analysis. No AI narrative.")
        self._gen = QPushButton("Generate report"); self._gen.setProperty("role", "secondary")
        row = QHBoxLayout(); row.addWidget(self._gen); row.addStretch(1)
        self.content.addLayout(row)
        self._report = QVBoxLayout(); self._report.setSpacing(t.SP_4)
        self._report_holder = QWidget(); self._report_holder.setLayout(self._report)
        self.content.addWidget(self._report_holder)
        self._gen.clicked.connect(self._on_gen)

    def report_text(self) -> str:                         # public seam (stable for tests)
        return " ".join(lbl.text() for lbl in self._report_holder.findChildren(QLabel))

    def _on_gen(self):
        self.clear_message()
        try:
            self._c.summarize(self.cid())
            self._render()
            self.show_success("Leadership report generated.")
        except FinsightAppError as e:
            self.show_error(e)

    # --- report rendering (deterministic; a view over existing outputs) ---
    def _clear_report(self):
        while self._report.count():
            item = self._report.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None); w.deleteLater()

    def _section(self, title: str, subtitle: str = "") -> QVBoxLayout:
        self._report.addWidget(SectionHeader(title, subtitle))
        inner = QVBoxLayout(); inner.setSpacing(t.SP_2)
        box = QWidget(); box.setProperty("role", "card")
        wrap = QVBoxLayout(box); wrap.setContentsMargins(t.SP_4, t.SP_3, t.SP_4, t.SP_3)
        wrap.addLayout(inner)
        self._report.addWidget(box)
        return inner

    def _text(self, layout, text, role="kvVal"):
        lbl = QLabel(text); lbl.setProperty("role", role); lbl.setWordWrap(True)
        layout.addWidget(lbl)
        return lbl

    def _render(self):
        self._clear_report()
        cid = self.cid()
        s = self._c.summary(cid) if cid else None
        if not s:
            return

        # A) Leadership summary — overall status (RAG shown as TEXT, not color alone) + budget health.
        a = self._section("Executive summary", f"{s.period}")
        status = QLabel(f"Overall status:  {s.status_label}")
        status.setProperty("role", "cardValue"); a.addWidget(status)
        self._text(a, f"{s.finding_count} finding(s) in this review.", role="cardDetail")
        for ln in (s.lines or ["No budget-health findings for this review."]):
            self._text(a, "• " + ln, role="kvVal")

        # B) Visual financial map — a relationship view over the SAME deterministic results (DEC-037).
        self._report.addWidget(SectionHeader(
            "Financial map", "How accounts, findings and vendors relate — a view of the analysis above."))
        fmap = FinancialMap()
        fmap.set_graph(self._c.financial_map(cid))
        self._report.addWidget(fmap)

        # C) Account-level detail — findings grouped by account.
        findings = self._c.findings(cid) or []
        c = self._section("Account detail", "Findings grouped by account.")
        if not findings:
            self._text(c, "No findings were raised.", role="context")
        else:
            by_account = {}
            for f in findings:
                by_account.setdefault(f.account, []).append(f)
            for account in sorted(by_account):
                self._text(c, f"Account {account}", role="cardLabel")
                for f in by_account[account]:
                    self._text(c, f"    {severity_text(f.severity)}  ·  {f.finding_type}  ·  {f.rule_id}",
                               role="kvVal")

        # D) User-correction disclosure (DEC-036) — original -> corrected, or a plain "no corrections".
        corrections = self._c.corrections(cid) or []
        d = self._section("User corrections",
                          "Corrections the reviewer approved before analysis (analysis used these values).")
        if not corrections:
            self._text(d, "No corrections were made; the analysis used the data exactly as extracted.",
                       role="context")
        else:
            for o in corrections:
                self._text(d, f"{o.document_type} · {o.source_ref} · {o.field}:  "
                              f"{o.original_value}  →  {o.current_value}", role="kvVal")

        # E) Scope & limitations — omitted/unavailable sources + AI availability. Honest, never implied.
        e = self._section("Scope & limitations",
                          "What this review did and did not cover.")
        for note in self._scope_notes(cid):
            self._text(e, "• " + note, role="kvVal")

    def _scope_notes(self, cid):
        notes = []
        actions = [ev.action for ev in (self._c.audit_timeline(cid) or [])]
        omitted = set()
        for ev in (self._c.audit_timeline(cid) or []):
            if ev.action == "missing_source_acknowledged":
                omitted.update(ev.detail.get("missing", []))
        if "upload_invoice" in actions:
            notes.append("An invoice was captured for the record but NOT analyzed — invoice analysis is "
                         "not available in this release.")
        if "Invoice" in omitted:
            notes.append("No invoice was provided; invoice review was not part of this analysis.")
        notes.append("Budget-vs-GED reconciliation and budget analysis ran on the verified data.")
        ai_ok = self._c.ask_fin_available() if hasattr(self._c, "ask_fin_available") else False
        notes.append("AI assistance (Ask Fin) is %s; it only explains verified results and never creates "
                     "findings, amounts, or decisions." % ("available" if ai_ok else "not available"))
        return notes

    def refresh(self):
        r = rank(self._c.workflow_state(self.cid()) if self.cid() else None)
        if r < RANK["Analyzed"]:
            self._gen.setEnabled(False)
            self._clear_report()
            self.show_info("Run analysis before generating the leadership report.")
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
