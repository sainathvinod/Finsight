from __future__ import annotations
from typing import List
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from finsight.delivery.desktop.theme import tokens as t

# Non-color state markers (legible without color).
_DONE = "●"
_CURRENT = "▶"
_PENDING = "○"


class StepRail(QWidget):
    """Interactive nine-step workflow rail. Completed steps are revisitable; the current step is
    marked; future/unreachable steps are disabled. Emits stepActivated(index) for enabled steps."""

    stepActivated = Signal(int)

    def __init__(self, steps: List[str], parent=None):
        super().__init__(parent)
        self._buttons: List[QPushButton] = []
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(t.SP_1)
        for i, name in enumerate(steps):
            btn = QPushButton(f"{_PENDING}  {i + 1}. {name}")
            btn.setProperty("nav", True)
            btn.setCheckable(True)
            btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(f"Step {i + 1} of {len(steps)}: {name}")
            btn.clicked.connect(lambda _checked=False, idx=i: self.stepActivated.emit(idx))
            self._buttons.append(btn)
            lay.addWidget(btn)
        lay.addStretch(1)
        self._steps = list(steps)

    def update_states(self, done: List[bool], enabled: List[bool], current: int, displayed: int) -> None:
        for i, btn in enumerate(self._buttons):
            if done[i]:
                marker = _DONE
            elif i == current:
                marker = _CURRENT
            else:
                marker = _PENDING
            btn.setText(f"{marker}  {i + 1}. {self._steps[i]}")
            btn.setEnabled(enabled[i])
            btn.setChecked(i == displayed)
            btn.setToolTip(self._tooltip(i, done[i], enabled[i], current))

    def _tooltip(self, i: int, done: bool, enabled: bool, current: int) -> str:
        name = self._steps[i]
        if done:
            return f"{name} — completed (view only)"
        if not enabled:
            return f"{name} — not yet available"
        if i == current:
            return f"{name} — current step"
        return name

    def focus_step(self, index: int) -> None:
        if 0 <= index < len(self._buttons):
            self._buttons[index].setFocus()
