# Phase 6.4c — review recovery banner. Renders a single, precise recovery state above the workflow.
# Presentation only: it displays the application-computed RecoveryMessage (what happened / what
# remains valid / what cannot continue / what to do). It shows FILENAMES, never full local paths, and
# never raw fingerprints (a short id is available under the Details tooltip only). It offers "Locate…"
# only where re-selecting the source can help. Nothing here is sent to AI, journals, or exports.
from __future__ import annotations
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from finsight.delivery.desktop.theme import tokens as t

# Statuses where re-selecting/locating the source is the corrective action.
_LOCATABLE = {"MISSING_SOURCE", "MOVED_SOURCE_CANDIDATE", "CHANGED_SOURCE", "UNREADABLE_SOURCE",
              "UNSUPPORTED_SOURCE", "MISSING_BINDING", "LEGACY_METADATA_INCOMPLETE"}
# Statuses that need no banner at all (the review is simply ready).
_SILENT = {"READY_FROM_CACHE", "RECONSTRUCTED_MATCH", "NO_SOURCE_REQUIRED", None}


class RecoveryBanner(QWidget):
    """A non-blocking recovery notice. `locateRequested(document_type)` fires when the reviewer wants
    to re-select a source. Visibility state is tracked internally (pytest-qt reports isVisible()==False
    on an unshown top-level window, so tests read the seams below, not Qt visibility)."""

    locateRequested = Signal(str)      # document_type to locate

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("role", "card")
        self._shown = False
        self._status = None
        self._document_type = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.SP_4, t.SP_3, t.SP_4, t.SP_3)
        lay.setSpacing(t.SP_1)
        self._headline = QLabel("")
        self._headline.setProperty("role", "sectionHeader")
        self._headline.setWordWrap(True)
        lay.addWidget(self._headline)
        self._detail = QLabel("")
        self._detail.setProperty("role", "kvVal")
        self._detail.setWordWrap(True)
        lay.addWidget(self._detail)
        row = QHBoxLayout()
        row.addStretch(1)
        self._locate = QPushButton("Locate file…")
        self._locate.setProperty("role", "secondary")
        self._locate.clicked.connect(self._on_locate)
        row.addWidget(self._locate)
        lay.addLayout(row)
        self.clear()

    def _on_locate(self):
        if self._document_type:
            self.locateRequested.emit(self._document_type)

    def show_result(self, result) -> None:
        """Render a RecoveryResult, or hide the banner for ready/none states."""
        status = result.status.value if result is not None else None
        if status in _SILENT:
            self.clear()
            return
        self._status = status
        self._document_type = result.document_type
        msg = result.message
        # Headline = what happened; detail = what remains valid + what to do (honest, no blame).
        self._headline.setText(msg.what_happened)
        parts = [p for p in (msg.remains_valid, msg.cannot_continue, msg.action_required) if p]
        self._detail.setText("  ".join(parts))
        # Short id available under a tooltip only (Details) — never shown inline; no full path ever.
        tip = ""
        if result.recorded_fingerprint_short:
            tip = "Verified id " + result.recorded_fingerprint_short
            if result.current_fingerprint_short:
                tip += " · current id " + result.current_fingerprint_short
        self._detail.setToolTip(tip)
        self._locate.setVisible(status in _LOCATABLE and bool(result.document_type))
        self.setVisible(True)
        self._shown = True

    def clear(self) -> None:
        self._status = None
        self._document_type = None
        self._headline.setText("")
        self._detail.setText("")
        self.setVisible(False)
        self._shown = False

    # --- public seams (stable for tests; independent of Qt window visibility) ---
    def is_shown(self) -> bool:
        return self._shown

    def status(self):
        return self._status

    def headline_text(self) -> str:
        return self._headline.text()

    def message_text(self) -> str:
        return (self._headline.text() + " " + self._detail.text()).strip()

    def locate_available(self) -> bool:
        return self._shown and self._locate.isVisibleTo(self)
