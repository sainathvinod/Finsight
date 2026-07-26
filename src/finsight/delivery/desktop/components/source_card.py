# Implements:
#   Feature: F-01-02 (source upload); target-product §6 (one card per source)
#   Requirements: FR-001 (upload), FR-003/NFR-012 (read-only source handling), FR-004 (optional slots)
#   UI surface: Data Upload — one card per source (Budget, GED, Invoice).
#
# Product purpose:
#   A single source-upload card. It shows, per the target workflow §6: the expected document,
#   its purpose, the accepted file format (the ACTUAL policy — no false claims), a required/optional
#   marker, the chosen filename, the current status/validation state, any error, replace/remove
#   controls, and a confidentiality/handling line. Composition only — no storage or business logic;
#   the panel wires signals to the controller.
from __future__ import annotations
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from finsight.delivery.desktop.theme import tokens as t

_CONFIDENTIALITY = "Read only — your file is never modified, and nothing is uploaded or sent anywhere."


class SourceCard(QFrame):
    """One source slot. Emits chooseRequested when the user wants to pick/replace the file and
    removeRequested when they clear it. The owning panel performs the actual file dialog + upload."""

    chooseRequested = Signal()
    removeRequested = Signal()

    def __init__(self, title: str, purpose: str, accepted_label: str,
                 required: bool = True, note: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("role", "card")
        self._path = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.SP_4, t.SP_3, t.SP_4, t.SP_3)
        lay.setSpacing(t.SP_2)

        head = QHBoxLayout()
        head.setSpacing(t.SP_2)
        name = QLabel(title)
        name.setProperty("role", "cardTitle")
        head.addWidget(name)
        pill = QLabel("Required" if required else "Optional")
        pill.setProperty("role", "statusPill")
        head.addWidget(pill)
        head.addStretch(1)
        lay.addLayout(head)

        purpose_lbl = QLabel(purpose)
        purpose_lbl.setProperty("role", "context")
        purpose_lbl.setWordWrap(True)
        lay.addWidget(purpose_lbl)

        # accepted_label is passed verbatim by the panel (policy-derived for real sources), so the card
        # never re-states a format claim of its own.
        accepts = QLabel(accepted_label)
        accepts.setProperty("role", "kvKey")
        lay.addWidget(accepts)

        row = QHBoxLayout()
        row.setSpacing(t.SP_2)
        self._field = QLineEdit()
        self._field.setReadOnly(True)
        self._field.setPlaceholderText("No file selected")
        row.addWidget(self._field, 1)
        self._choose = QPushButton("Choose…")
        self._choose.setProperty("role", "secondary")
        self._choose.clicked.connect(self.chooseRequested.emit)
        row.addWidget(self._choose)
        self._remove = QPushButton("Remove")
        self._remove.setProperty("role", "secondary")
        self._remove.setVisible(False)
        self._remove.clicked.connect(self.removeRequested.emit)
        row.addWidget(self._remove)
        lay.addLayout(row)

        self._status = QLabel("Not selected")
        self._status.setProperty("role", "context")
        self._status.setWordWrap(True)
        lay.addWidget(self._status)

        if note:
            note_lbl = QLabel(note)
            note_lbl.setProperty("role", "context")
            note_lbl.setWordWrap(True)
            lay.addWidget(note_lbl)

        conf = QLabel(_CONFIDENTIALITY)
        conf.setProperty("role", "kvKey")
        conf.setWordWrap(True)
        lay.addWidget(conf)

    # --- state ---
    def set_file(self, path: str) -> None:
        self._path = path
        self._field.setText(path or "")
        self._choose.setText("Replace…")
        self._remove.setVisible(True)
        self._status.setProperty("role", "context")
        self._status.setText("Selected — not yet uploaded")
        self._status.style().unpolish(self._status); self._status.style().polish(self._status)

    def clear(self) -> None:
        self._path = None
        self._field.clear()
        self._choose.setText("Choose…")
        self._remove.setVisible(False)
        self._status.setText("Not selected")

    def path(self):
        return self._path

    def set_status(self, text: str) -> None:
        self._status.setText(text)

    # --- public seams (stable for tests) ---
    def status_text(self) -> str:
        return self._status.text()
