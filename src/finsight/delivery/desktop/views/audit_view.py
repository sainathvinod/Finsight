from __future__ import annotations
import json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QSplitter, QScrollArea
from finsight.delivery.desktop.components import SectionHeader, EmptyState, DetailInspector, AuditTimeline
from finsight.delivery.desktop.theme import tokens as t


class AuditView(QWidget):
    """Read-only append-only audit timeline with a selected-event inspector."""

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._c = controller
        self._events = []

        root = QVBoxLayout(self)
        root.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        root.setSpacing(t.SP_3)
        self._header = SectionHeader("Audit", "")
        root.addWidget(self._header)

        self._stack = QStackedWidget()
        root.addWidget(self._stack, 1)

        split = QSplitter(Qt.Orientation.Horizontal)
        self._timeline = AuditTimeline()
        self._timeline.currentChanged.connect(self._on_event)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._timeline)
        scroll.setFrameShape(QScrollArea.Shape.StyledPanel)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._inspector = DetailInspector("Event")
        split.addWidget(scroll)
        split.addWidget(self._inspector)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)
        split.setSizes([620, 360])   # explicit initial proportion so the timeline is not collapsed
        self._stack.addWidget(split)

        self._empty = EmptyState(
            "No audit events",
            "This review has no recorded audit events, or no review is selected.",
            "Every workflow action appends an event to the audit trail.",
        )
        self._stack.addWidget(self._empty)
        self.refresh()

    def refresh(self) -> None:
        cid = self._c.active_review_id
        self._events = self._c.audit_timeline(cid) if cid else []
        if self._events:
            self._header.set_subtitle(f"{len(self._events)} event(s), oldest first")
            self._timeline.set_events(self._events)  # selects first -> _on_event fills inspector
            self._stack.setCurrentIndex(0)
        else:
            self._header.set_subtitle("")
            self._inspector.show_placeholder("Select an event to see its detail.")
            self._stack.setCurrentWidget(self._empty)

    def _on_event(self, index: int) -> None:
        if not (0 <= index < len(self._events)):
            return
        e = self._events[index]
        self._inspector.begin(f"Event: {e.action}")
        self._inspector.add_section("Event")
        self._inspector.add_row("Action", e.action)
        self._inspector.add_row("Actor", e.actor)
        self._inspector.add_row("Timestamp", e.ts, mono=True)
        self._inspector.add_section("Detail")
        if e.detail:
            for k, v in e.detail.items():
                self._inspector.add_row(k, json.dumps(v) if not isinstance(v, str) else v, mono=True)
        else:
            self._inspector.add_row("(none)", "")
