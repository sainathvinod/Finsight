from __future__ import annotations
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtWidgets import QStackedWidget
from finsight.delivery.desktop.components.step_rail import StepRail
from finsight.delivery.desktop.views.workflow_meta import STEPS, gates
from finsight.delivery.desktop.views.steps import (
    SetupPanel, UploadPanel, ValidationPanel, ProcessingPanel,
    VerificationPanel, AnalysisPanel, FindingsPanel, SummaryPanel, ExportPanel,
)
from finsight.delivery.desktop.theme import tokens as t

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

        self._stack = QStackedWidget()
        self._panels = [
            SetupPanel(controller), UploadPanel(controller), ValidationPanel(controller),
            ProcessingPanel(controller), VerificationPanel(controller), AnalysisPanel(controller),
            FindingsPanel(controller), SummaryPanel(controller), ExportPanel(controller),
        ]
        for p in self._panels:
            self._stack.addWidget(p)
        outer.addWidget(self._stack, 1)

        self._rail.stepActivated.connect(self._on_rail)
        controller.activeReviewChanged.connect(lambda _c: self._on_active_changed())
        controller.workflowChanged.connect(lambda _c: self._on_workflow_changed())

        # Initialize to the active review's current step (set during window construction), or Setup.
        self._on_active_changed()

    # --- public seams (stable API for tests) ---
    def panel(self, step: int):
        return self._panels[step]

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
