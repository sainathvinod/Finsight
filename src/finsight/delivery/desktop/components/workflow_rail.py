from __future__ import annotations
from typing import List
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from finsight.delivery.desktop.theme import tokens as t

# Non-color state markers so the rail is legible without color.
_DONE = "●"     # ● completed
_CURRENT = "▶"  # ▶ current
_PENDING = "○"  # ○ not yet reached


class WorkflowRail(QWidget):
    """Vertical rail showing the canonical review workflow steps and the review's current position.
    Read-only status presentation (no navigation actions)."""

    def __init__(self, steps: List[str], parent=None):
        super().__init__(parent)
        self._steps = list(steps)
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(t.SP_1)
        self._labels: List[QLabel] = []
        for i, name in enumerate(self._steps, start=1):
            lbl = QLabel(f"{_PENDING}  {i}. {name}")
            lbl.setToolTip(f"Step {i} of {len(self._steps)}: {name}")
            self._labels.append(lbl)
            self._lay.addWidget(lbl)
        self.set_current(0)

    def set_current(self, current_index: int) -> None:
        """current_index is 0-based; steps before it are done, the one at it is current."""
        for i, lbl in enumerate(self._labels):
            name = self._steps[i]
            if i < current_index:
                marker, color, weight = _DONE, t.STATUS_OK, "normal"
            elif i == current_index:
                marker, color, weight = _CURRENT, t.ACCENT, "600"
            else:
                marker, color, weight = _PENDING, t.TEXT_MUTED, "normal"
            lbl.setText(f"{marker}  {i + 1}. {name}")
            lbl.setStyleSheet(f"color:{color}; font-weight:{weight};")
