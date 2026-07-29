"""Accessible seven-stage progress used by the integrated review journey."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from finsight.delivery.desktop.theme import tokens as t


REVIEW_STEPS = (
    "Create",
    "Upload",
    "Verify Data",
    "Review Rules",
    "Validate",
    "Review Results",
    "Complete",
)


class ReviewProgress(QFrame):
    def __init__(self, active_step: int = 0, parent=None):
        super().__init__(parent)
        self.setProperty("role", "reviewProgress")
        self.setAccessibleName("Financial review workflow progress")
        self._items: list[tuple[QLabel, QLabel]] = []
        layout = QHBoxLayout(self)
        layout.setContentsMargins(t.SP_4, t.SP_3, t.SP_4, t.SP_3)
        layout.setSpacing(t.SP_2)
        for index, name in enumerate(REVIEW_STEPS):
            item = QWidget()
            item_layout = QVBoxLayout(item)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(t.SP_1)
            marker = QLabel(str(index + 1))
            marker.setAlignment(Qt.AlignmentFlag.AlignCenter)
            marker.setFixedSize(24, 24)
            marker.setProperty("role", "stepPending")
            marker.setAccessibleName(f"Step {index + 1}, {name}")
            label = QLabel(name)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setProperty("role", "stepLabelPending")
            label.setWordWrap(True)
            label.setMinimumWidth(0)
            label.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )
            item_layout.addWidget(marker, 0, Qt.AlignmentFlag.AlignHCenter)
            item_layout.addWidget(label)
            layout.addWidget(item, 1)
            self._items.append((marker, label))
        self.set_step(active_step)

    def set_step(
        self,
        active_step: int,
        *,
        all_complete: bool = False,
        completed_steps: set[int] | None = None,
    ) -> None:
        active_step = max(0, min(active_step, len(REVIEW_STEPS) - 1))
        completed_steps = completed_steps or set()
        states = []
        for index, (marker, label) in enumerate(self._items):
            completed = all_complete or index < active_step or index in completed_steps
            active = not all_complete and index == active_step
            if completed:
                icon = self.style().standardIcon(
                    QStyle.StandardPixmap.SP_DialogApplyButton
                )
                marker.setPixmap(icon.pixmap(18, 18))
                marker.setText("")
                marker.setProperty("role", "stepComplete")
                label.setProperty("role", "stepLabelComplete")
                state = "complete"
            elif active:
                marker.clear()
                marker.setText(str(index + 1))
                marker.setProperty("role", "stepActive")
                label.setProperty("role", "stepLabelActive")
                state = "current"
            else:
                marker.clear()
                marker.setText(str(index + 1))
                marker.setProperty("role", "stepPending")
                label.setProperty("role", "stepLabelPending")
                state = "upcoming"
            for widget in (marker, label):
                style = widget.style()
                if isinstance(style, QStyle):
                    style.unpolish(widget)
                    style.polish(widget)
                widget.update()
            marker.setAccessibleDescription(
                f"{REVIEW_STEPS[index]} is {state}."
            )
            states.append(f"{REVIEW_STEPS[index]} {state}")
        self.setAccessibleDescription("; ".join(states))
