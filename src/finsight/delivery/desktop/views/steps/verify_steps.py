from __future__ import annotations
from typing import Dict, List, Tuple
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox
from finsight.delivery.desktop.components.form_row import FormRow
from finsight.delivery.desktop.components.extraction_review import ExtractionReview
from finsight.delivery.desktop.components.section_header import SectionHeader
from finsight.delivery.desktop.views.steps.base import StepPanel
from finsight.delivery.desktop.views.findings_view import FindingsView
from finsight.delivery.desktop.views.workflow_meta import rank, RANK
from finsight.delivery.desktop.theme import tokens as t
from finsight.application.errors import FinsightAppError
from finsight.application.attestation import attestation_statement


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

        # Full per-source extraction review (§9): every extracted record with lineage, search + sort.
        # `_sources` keeps the representative summary (Phase 5.4 seams) populated in parallel.
        self._sources: Dict[str, object] = {}
        self._review_head = SectionHeader("Extracted records",
                                          "Review every extracted record and its source before you verify.")
        self.content.addWidget(self._review_head)
        self._review = ExtractionReview()
        self._review.correctionEdited.connect(self._on_correction)
        self._review.revertRequested.connect(self._on_revert)
        self.content.addWidget(self._review)

        self._meaning = QLabel(); self._meaning.setProperty("role", "context"); self._meaning.setWordWrap(True)
        self.content.addWidget(self._meaning)
        self._details = QLabel(); self._details.setProperty("role", "context"); self._details.setWordWrap(True)
        self.content.addWidget(self._details)

        # §12 attestation: an explicit, branching human confirmation, required before analysis. The exact
        # statement depends on whether the reviewer corrected any value; it is recorded (with the user,
        # timestamp, whether corrections existed, and the verified fingerprint) by the verify audit fact.
        self._can_verify = False
        self._attest_head = SectionHeader("Verification attestation",
                                          "Confirm the data before FinSight analyzes it.")
        self.content.addWidget(self._attest_head)
        self._attest_statement = QLabel(attestation_statement(False))
        self._attest_statement.setProperty("role", "kvVal"); self._attest_statement.setWordWrap(True)
        self.content.addWidget(self._attest_statement)
        self._attest_check = QCheckBox("I confirm the statement above.")
        self._attest_check.toggled.connect(self._sync_approve)
        self.content.addWidget(self._attest_check)

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

    def _on_correction(self, document_type, source_ref, field, original, new_value):
        cid = self.cid()
        if not cid:
            return
        try:
            self._c.save_correction(cid, document_type, source_ref, field, original, new_value)
            self.clear_message()
        except FinsightAppError as e:
            self.show_error(e)
        self._render_representative(cid)     # re-render with the correction overlaid (or reverted on error)
        self._update_attestation()           # a correction switches to the "edited" attestation wording

    def _on_revert(self, document_type, source_ref, field):
        cid = self.cid()
        if not cid:
            return
        self._c.revert_correction(cid, document_type, source_ref, field)
        self._render_representative(cid)
        self._update_attestation()

    def verification_preview_rows(self) -> List[Tuple[str, str]]:   # public seam (summary)
        return list(self._preview_rows)

    # --- extraction review (§9) + representative summary seams (Phase 5.4) ---
    def _clear_rep(self):
        self._sources = {}
        self._review.set_data([], [])
        self._review_head.setVisible(False)
        self._review.setVisible(False)

    def _render_representative(self, cid):
        # Populate the representative-summary seams from the capped preview...
        self._sources = {}
        preview = self._c.verification_preview(cid) if cid else None
        if preview is not None:
            for sp in preview.sources:
                self._sources[sp.source_type] = sp
        # ...and drive the full all-records review from the uncapped extraction read model.
        review = self._c.extraction_review(cid) if cid else None
        if review is None:
            self._review_head.setVisible(False)
            self._review.setVisible(False)
            return
        records, omitted = review
        # Editable only before verification (FR-028: corrections are pre-approval). Once verified, the
        # extracted data is read-only — its corrections are frozen into the verified fingerprint.
        state = self._c.workflow_state(cid)
        editable = RANK["Processed"] <= rank(state) < RANK["Verified"]
        self._review.set_editable(editable)
        self._review.set_data(records, omitted)
        self._review_head.setVisible(True)
        self._review.setVisible(True)

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
            self._can_verify = False
            self._set_attestation_visible(False)
            self._approve.setEnabled(False)
            self.show_success("This data has been verified and certified as the basis for analysis.")
        elif snap.rejected_reason or not snap.available:
            self._can_verify = False
            self._set_attestation_visible(False)
            self._approve.setEnabled(False)
            self.show_warning("Rejected or unavailable data cannot be verified. Resolve the issue above.")
        else:
            self._can_verify = True
            self._set_attestation_visible(True)
            self._update_attestation()
            self._meaning.setText(
                "Approval confirms that the normalized data shown is suitable for deterministic "
                "analysis. Source files remain unchanged.")
            self.clear_message()
            self._sync_approve()

    def _set_attestation_visible(self, visible: bool) -> None:
        self._attest_head.setVisible(visible)
        self._attest_statement.setVisible(visible)
        self._attest_check.setVisible(visible)

    def _update_attestation(self) -> None:
        """Set the branching attestation wording (§12): the edited statement if the reviewer has
        corrections, else the no-edit statement. Re-checking is required when the wording changes."""
        cid = self.cid()
        statement = attestation_statement(bool(cid) and self._c.has_corrections(cid))
        if statement != self._attest_statement.text():
            self._attest_statement.setText(statement)
            self._attest_check.setChecked(False)          # a changed attestation must be re-confirmed

    def attestation_text(self) -> str:                    # public seam (stable for tests)
        return self._attest_statement.text()

    def _sync_approve(self) -> None:
        self._approve.setEnabled(self._can_verify and self._attest_check.isChecked())


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
