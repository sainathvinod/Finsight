# Shared first-run welcome card (Phase 5.1 guidance, reused by Reviews and the Dashboard in 5.3 so
# the two never diverge). Concise and professional — not a marketing page.
from __future__ import annotations
from typing import Callable, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from finsight.delivery.desktop.theme import tokens as t

FIRST_RUN_TITLE = "Welcome to FinSight"
FIRST_RUN_LEAD = ("FinSight runs a monthly financial review end to end: upload the source workbooks, "
                  "verify the extracted data, run the deterministic analysis, review findings, and "
                  "export the package — with a complete audit trail throughout.")
FIRST_RUN_POINTS = [
    "Lifecycle:  Create → Upload → Verify → Analyze → Findings → Summary → Export.",
    "Your source files are never modified — FinSight only reads them.",
    "Deterministic analysis is the source of truth; every finding traces to a rule and its inputs.",
    "Ask Fin explains verified results — it never creates findings, amounts, or decisions.",
]


def build_first_run_card(on_create: Callable[[], None]) -> Tuple[QWidget, QPushButton]:
    """Return (centered welcome card widget, primary 'Create first review' button)."""
    wrap = QWidget()
    outer = QVBoxLayout(wrap)
    outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
    card = QWidget()
    card.setProperty("role", "card")
    card.setMaximumWidth(640)
    lay = QVBoxLayout(card)
    lay.setContentsMargins(t.SP_6, t.SP_6, t.SP_6, t.SP_6)
    lay.setSpacing(t.SP_3)
    title = QLabel(FIRST_RUN_TITLE)
    title.setProperty("role", "sectionHeader")
    lay.addWidget(title)
    lead = QLabel(FIRST_RUN_LEAD)
    lead.setProperty("role", "kvVal")
    lead.setWordWrap(True)
    lay.addWidget(lead)
    for point in FIRST_RUN_POINTS:
        p = QLabel("•  " + point)
        p.setProperty("role", "context")
        p.setWordWrap(True)
        lay.addWidget(p)
    row = QHBoxLayout()
    row.addStretch(1)
    button = QPushButton("Create first review")
    button.setProperty("role", "primary")
    button.clicked.connect(lambda: on_create())
    row.addWidget(button)
    lay.addLayout(row)
    outer.addWidget(card)
    return wrap, button
