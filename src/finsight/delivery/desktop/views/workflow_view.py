from __future__ import annotations
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtWidgets import QStackedWidget, QFileDialog
from finsight.delivery.desktop.components.step_rail import StepRail
from finsight.delivery.desktop.components.recovery_banner import RecoveryBanner
from finsight.delivery.desktop.views.workflow_meta import STEPS, gates
from finsight.delivery.desktop.views.steps import (
    SetupPanel, UploadPanel, ValidationPanel, ProcessingPanel,
    VerificationPanel, AnalysisPanel, FindingsPanel, SummaryPanel, ExportPanel,
)
from finsight.delivery.desktop.theme import tokens as t
from finsight.domain.review_cycle import has_reached, CycleState
from finsight.application.source_format import QT_FILE_FILTER

_VALIDATION_STEP = 2
_VERIFICATION_STEP = 4


class WorkflowView(QWidget):
    """The interactive nine-step review workspace: an interactive step rail on the left and the
    step panels on the right. Step availability follows the persisted CycleState; the workflow
    never fakes a transition (each panel calls the workflow command service)."""

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._c = controller
        self._displayed = 0

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        rail_col = QWidget()
        rail_col.setObjectName("Sidebar")
        rail_col.setFixedWidth(232)
        rl = QVBoxLayout(rail_col)
        rl.setContentsMargins(t.SP_3, t.SP_4, t.SP_3, t.SP_3)
        rl.setSpacing(t.SP_2)
        group = QLabel("WORKFLOW"); group.setProperty("role", "navGroup")
        rl.addWidget(group)
        self._rail = StepRail(STEPS)
        rl.addWidget(self._rail)
        rl.addStretch(1)
        outer.addWidget(rail_col)

        right = QWidget()
        right_col = QVBoxLayout(right)
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(0)
        self._recovery = RecoveryBanner()
        self._recovery.locateRequested.connect(self._on_locate)
        right_col.addWidget(self._recovery)

        self._stack = QStackedWidget()
        self._panels = [
            SetupPanel(controller), UploadPanel(controller), ValidationPanel(controller),
            ProcessingPanel(controller), VerificationPanel(controller), AnalysisPanel(controller),
            FindingsPanel(controller), SummaryPanel(controller), ExportPanel(controller),
        ]
        for p in self._panels:
            self._stack.addWidget(p)
        right_col.addWidget(self._stack, 1)
        outer.addWidget(right, 1)

        self._rail.stepActivated.connect(self._on_rail)
        controller.activeReviewChanged.connect(lambda _c: self._on_active_changed())
        controller.workflowChanged.connect(lambda _c: self._on_workflow_changed())
        controller.reviewRecoveryChanged.connect(lambda _c: self._refresh_recovery())

        # Initialize to the active review's current step (set during window construction), or Setup.
        self._on_active_changed()

    # --- public seams (stable API for tests) ---
    def panel(self, step: int):
        return self._panels[step]

    def recovery_banner(self) -> RecoveryBanner:
        return self._recovery

    def current_step(self) -> int:
        return self._displayed

    def _state(self):
        cid = self._c.active_review_id
        return self._c.workflow_state(cid) if cid else None

    def _apply(self, index):
        self._displayed = index
        done, enabled, current = gates(self._state())
        self._rail.update_states(done, enabled, current, index)
        self._stack.setCurrentIndex(index)
        self._panels[index].refresh()

    def refresh(self):
        done, enabled, current = gates(self._state())
        disp = self._displayed
        if not enabled[disp]:
            disp = current if current >= 0 else 8
        self._apply(disp)

    def _on_rail(self, index):
        _done, enabled, _current = gates(self._state())
        if enabled[index]:
            self._apply(index)

    def _on_active_changed(self):
        _done, _enabled, current = gates(self._state())
        if current >= 0:
            target = current
        elif self._c.active_review_id:
            target = 8      # a fully completed review opens on Export
        else:
            target = 0      # no review yet -> Review Setup
        self._apply(target)
        self._maybe_reconstruct()
        self._refresh_recovery()

    # --- Phase 6.4c recovery surface ---
    def _maybe_reconstruct(self):
        """Resume a review that needs a source-derived working set to continue (pre-analysis, not yet
        cached). Analyzed+ reviews are viewable from persisted results, so navigation never forces a
        reconstruction of them. reconstruct_async is a cheap no-op for cache hits / pre-intake."""
        cid = self._c.active_review_id
        if not cid:
            return
        state = self._c.workflow_state(cid)
        if state is None:
            return
        if has_reached(state, CycleState.INTAKE) and not has_reached(state, CycleState.ANALYZED):
            self._c.reconstruct_async(cid, lambda _r: None, lambda _e: None)

    def _refresh_recovery(self):
        cid = self._c.active_review_id
        self._recovery.show_result(self._c.last_recovery(cid) if cid else None)

    def _on_locate(self, document_type: str):
        cid = self._c.active_review_id
        if not cid:
            return
        # Filenames only reach the banner; the OS dialog handles paths — nothing else displays them.
        path, _ = QFileDialog.getOpenFileName(self, "Locate %s source" % document_type, "",
                                              QT_FILE_FILTER)
        if not path:
            return
        result = self._c.rebind_source(cid, document_type, path)
        if result.ok or result.status.value == "MOVED_SOURCE_CANDIDATE":
            self._c.reconstruct_async(cid, lambda _r: None, lambda _e: None)

    def _on_workflow_changed(self):
        _done, _enabled, current = gates(self._state())
        target = current if current >= 0 else 8
        # If processing rejected the data, land on Upload Validation (to show why) instead of
        # Verification (which would be a dead end).
        if target == _VERIFICATION_STEP:
            cid = self._c.active_review_id
            snap = self._c.validation_snapshot(cid) if cid else None
            if snap is not None and snap.rejected_reason:
                target = _VALIDATION_STEP
        self._apply(target)
