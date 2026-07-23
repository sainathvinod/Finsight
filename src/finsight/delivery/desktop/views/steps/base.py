from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from finsight.delivery.desktop.components import SectionHeader
from finsight.delivery.desktop.components.message import InlineMessage
from finsight.application.errors import FinsightAppError
from finsight.delivery.desktop.theme import tokens as t


class StepPanel(QWidget):
    """Base for a workflow step panel: a header, an inline (non-modal) message area, and a content
    region subclasses fill via `self.content`."""

    def __init__(self, controller, title: str, subtitle: str = ""):
        super().__init__()
        self._c = controller
        root = QVBoxLayout(self)
        root.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        root.setSpacing(t.SP_3)
        self._header = SectionHeader(title, subtitle)
        root.addWidget(self._header)
        self.message = InlineMessage()
        root.addWidget(self.message)
        self.content = QVBoxLayout()
        self.content.setSpacing(t.SP_3)
        self.content.setAlignment(Qt.AlignmentFlag.AlignTop)
        root.addLayout(self.content)
        root.addStretch(1)

    def cid(self):
        return self._c.active_review_id

    def set_subtitle(self, text: str) -> None:
        self._header.set_subtitle(text)

    def show_error(self, exc) -> None:
        text = exc.message if isinstance(exc, FinsightAppError) else str(exc)
        self.message.show_message(text, "error")

    def show_success(self, text: str) -> None:
        self.message.show_message(text, "success")

    def show_info(self, text: str) -> None:
        self.message.show_message(text, "info")

    def show_warning(self, text: str) -> None:
        self.message.show_message(text, "warning")

    def clear_message(self) -> None:
        self.message.clear_message()

    def refresh(self) -> None:  # overridden
        pass
