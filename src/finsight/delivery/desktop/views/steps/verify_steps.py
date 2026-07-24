from __future__ import annotations
from typing import Dict, List, Tuple
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView,
)
from finsight.delivery.desktop.components.form_row import FormRow
from finsight.delivery.desktop.views.steps.base import StepPanel
from finsight.delivery.desktop.views.findings_view import FindingsView
from finsight.delivery.desktop.views.workflow_meta import rank, RANK
from finsight.delivery.desktop.theme import tokens as t
from finsight.application.errors import FinsightAppError


class VerificationPanel(StepPanel):
    """Shows a read-only preview of exactly what is being certified BEFORE the explicit approval — the
    reviewer never approves unseen data. Row-level cell preview is not available through the current
    read models, so this shows the best honest summary (sources, counts, readiness, issues) with the
    technical fingerprint kept in a secondary details line."""

    def __init__(self, controller):
        super().__init__(controller, "Verification",
                         "Review what was extracted, then explicitly approve it as the basis for analysis.")
        self._preview_rows: List[Tuple[str, str]] = []
        self._preview = QVBoxLayout(); self._preview.setSpacing(t.SP_2)
        holder = QWidget(); holder.setProperty("role", "card")
        inner = QVBoxLayout(holder); inner.setContentsMargins(t.SP_3, t.SP_3, t.SP_3, t.SP_3)
        inner.addLayout(self._preview)
        self._preview_holder = holder
        self.content.addWidget(holder)

        # Representative normalized rows per source (Phase 5.4). Session-scoped, read-only.
        self._sources: Dict[str, object] = {}
        self._rep_area = QVBoxLayout(); self._rep_area.setSpacing(t.SP_2)
        self.content.addLayout(self._rep_area)

        self._meaning = QLabel(); self._meaning.setProperty("role", "context"); self._meaning.setWordWrap(True)
        self.content.addWidget(self._meaning)
        self._details = QLabel(); self._details.setProperty("role", "context"); self._details.setWordWrap(True)
        self.content.addWidget(self._details)

        self._approve = QPushButton("Approve && verify data"); self._approve.setProperty("role", "primary")
        row = QHBoxLayout(); row.addWidget(self._approve); row.addStretch(1)
        self.content.addLayout(row)
        self._approve.clicked.connect(self._on_verify)

    def _set_preview(self, rows: List[Tuple[str, str]]):
        self._preview_rows = rows
        while self._preview.count():
            item = self._preview.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None); w.deleteLater()
        for label, value in rows:
            lbl = QLabel(str(value)); lbl.setProperty("role", "kvVal"); lbl.setWordWrap(True)
            self._preview.addWidget(FormRow(label, lbl, label_width=180))
        self._preview_holder.setVisible(bool(rows))

    def _on_verify(self):
        self.clear_message()
        try:
            self._c.verify(self.cid())
            self.show_success("Data verified. Analysis is now available.")
        except FinsightAppError as e:
            self.show_error(e)

    def verification_preview_rows(self) -> List[Tuple[str, str]]:   # public seam (summary)
        return list(self._preview_rows)

    # --- representative normalized rows (Phase 5.4) ---
    def _clear_rep(self):
        while self._rep_area.count():
            item = self._rep_area.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None); w.deleteLater()
        self._sources = {}

    def _render_representative(self, cid):
        self._clear_rep()
        preview = self._c.verification_preview(cid) if cid else None
        if preview is None:
            return
        for sp in preview.sources:
            self._sources[sp.source_type] = sp
            head = QLabel(f"{sp.source_type} — {sp.filename or '(source)'}  ·  "
                          f"{sp.accepted_rows} accepted, {sp.quarantined_rows} quarantined")
            head.setProperty("role", "cardLabel"); head.setWordWrap(True)
            self._rep_area.addWidget(head)
            if sp.rows:
                self._rep_area.addWidget(self._source_table(sp))
            else:
                none_lbl = QLabel("No representative rows available.")
                none_lbl.setProperty("role", "context")
                self._rep_area.addWidget(none_lbl)

    def _source_table(self, sp) -> QTableWidget:
        table = QTableWidget(len(sp.rows), len(sp.columns))
        table.setHorizontalHeaderLabels([c.replace("_", " ") for c in sp.columns])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)   # read-only
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMaximumHeight(220)
        for ri, row in enumerate(sp.rows):
            for ci, val in enumerate(row):
                table.setItem(ri, ci, QTableWidgetItem(str(val)))
        return table

    # --- new preview seams ---
    def verification_preview_columns(self, source: str):
        sp = self._sources.get(source)
        return list(sp.columns) if sp else []

    def verification_preview_values(self, source: str):
        sp = self._sources.get(source)
        return [list(r) for r in sp.rows] if sp else []

    def verification_source_summary(self, source: str) -> Dict[str, object]:
        sp = self._sources.get(source)
        if sp is None:
            return {}
        return {"filename": sp.filename, "period": sp.period, "accepted": sp.accepted_rows,
                "quarantined": sp.quarantined_rows, "available": sp.available}

    def refresh(self):
        cid = self.cid()
        state = self._c.workflow_state(cid) if cid else None
        snap = self._c.validation_snapshot(cid) if cid else None
        self._meaning.setText("")
        self._details.setText("")

        if snap is None:
            self._set_preview([])
            self._clear_rep()
            self._approve.setEnabled(False)
            self.show_info("Process the uploaded data (Processing) before verification.")
            return

        rows: List[Tuple[str, str]] = []
        for item in snap.provenance:
            rows.append(("Source", f"{item.doc_type}: {item.name}  ({item.period})"))
        rows.append(("Accepted GED rows", str(snap.ged_valid)))
        rows.append(("Accepted budget rows", str(snap.budget_valid)))
        rows.append(("Quarantined rows", str(snap.quarantined)))
        rows.append(("Dataset available", "Yes" if snap.available else "No"))
        if snap.rejected_reason:
            rows.append(("Issue", snap.rejected_reason))
        self._set_preview(rows)
        self._render_representative(cid)
        if snap.provenance:
            self._details.setText("Details:  " + "; ".join(
                f"{p.doc_type} fingerprint {p.fingerprint[:12]}…" for p in snap.provenance))

        if state and rank(state) >= RANK["Verified"]:
            self._approve.setEnabled(False)
            self.show_success("This data has been verified and certified as the basis for analysis.")
        elif snap.rejected_reason or not snap.available:
            self._approve.setEnabled(False)
            self.show_warning("Rejected or unavailable data cannot be verified. Resolve the issue above.")
        else:
            self._approve.setEnabled(True)
            self._meaning.setText(
                "Approval confirms that the normalized data shown is suitable for deterministic "
                "analysis. Source files remain unchanged.")
            self.clear_message()


class AnalysisPanel(StepPanel):
    def __init__(self, controller):
        super().__init__(controller, "Analysis",
                         "Run the deterministic rules engine on the verified data.")
        self._run = QPushButton("Run analysis"); self._run.setProperty("role", "primary")
        row = QHBoxLayout(); row.addWidget(self._run); row.addStretch(1)
        self.content.addLayout(row)
        self._detail = QLabel(); self._detail.setProperty("role", "kvVal"); self._detail.setWordWrap(True)
        self._detail.setTextFormat(Qt.TextFormat.PlainText)
        self.content.addWidget(self._detail)
        # Technical run metadata lives in a secondary details line, not the primary surface.
        self._tech = QLabel(); self._tech.setProperty("role", "context"); self._tech.setWordWrap(True)
        self.content.addWidget(self._tech)
        self._run.clicked.connect(self._on_run)

    def _on_run(self):
        self.clear_message()
        try:
            res = self._c.analyze(self.cid())
            self.show_success(f"Analysis complete — {res.finding_count} finding(s).")
            self._detail.setText(f"{res.finding_count} finding(s) were produced from the verified data.")
            self._tech.setText(f"Details:  run {res.run_id} · configuration {res.config_version} · "
                               f"input fingerprint {res.input_fingerprint[:12]}…")
        except FinsightAppError as e:
            self.show_error(e)

    def refresh(self):
        cid = self.cid()
        state = self._c.workflow_state(cid) if cid else None
        r = rank(state)
        if r < RANK["Verified"]:
            self._run.setEnabled(False)
            self._detail.setText(""); self._tech.setText("")
            self.show_info("Verification is required before analysis.")
        elif r >= RANK["Analyzed"]:
            self._run.setEnabled(False)
            status = self._c.review_status(cid)
            n = status.finding_count if status else 0
            self._detail.setText(f"Analysis complete — {n} finding(s). See the Findings destination.")
            self.clear_message()
        else:
            self._run.setEnabled(True)
            self._detail.setText(""); self._tech.setText("")
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
