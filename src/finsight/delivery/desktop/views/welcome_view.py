# Implements:
#   Epic: E-01 — Guided Monthly Review Workflow (walking-skeleton home)
#   Feature: F-01-01 — Monthly Review Cycle Workspace (first-launch welcome surface)
#   Requirements: FR-006, FR-081; NFR-068 (low-training adoption)
#   ADRs: ADR-002 (delivery layering); ADR-013 (Ollama-optional core)
#   Decisions: DEC-022 ("Monthly Review in a Box"); DEC-025 (Recent Reviews home)
#   UI surface: First-ever launch (no reviews yet).
#
# Product purpose:
#   The dedicated first-launch welcome. When a user opens FinSight and no reviews exist, this is the
#   first screen (not Dashboard/Reviews/a blank table): a large "Welcome to FinSight" hero, a plain
#   description of what FinSight does, and a single prominent CREATE NEW REVIEW action. Ask Fin is
#   reachable from here as a contextual helper.
#
# Trust / lifecycle constraints:
#   - No repositories/SQL/financial logic here (delivery layer). Reads only whether reviews exist,
#     via the controller. It creates nothing itself — CREATE NEW REVIEW hands off to the workflow.
#   - Independent of Ollama; Ask Fin availability is honest and optional.
from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from finsight.delivery.desktop.components.first_run import FIRST_RUN_LEAD, FIRST_RUN_POINTS
from finsight.delivery.desktop.theme import tokens as t

_HERO_TITLE = "Welcome to FinSight"
_HERO_LEAD = ("FinSight helps finance teams turn monthly financial files into a verified, auditable "
              "review — with deterministic analysis, clear reporting, and locally-grounded AI assistance.")


class WelcomeView(QWidget):
    """First-ever-launch welcome. Emits newReviewRequested / askFinRequested."""

    newReviewRequested = Signal()
    askFinRequested = Signal()

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._c = controller

        outer = QVBoxLayout(self)
        outer.setContentsMargins(t.SP_6, t.SP_6, t.SP_6, t.SP_6)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hero = QWidget()
        hero.setFixedWidth(600)  # comfortable reading column; keeps wrapping stable across resize
        lay = QVBoxLayout(hero)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(t.SP_4)

        title = QLabel(_HERO_TITLE)
        title.setProperty("role", "heroTitle")
        lay.addWidget(title)

        lead = QLabel(_HERO_LEAD)
        lead.setProperty("role", "heroLead")
        lead.setWordWrap(True)
        lay.addWidget(lead)

        points = QVBoxLayout()
        points.setSpacing(t.SP_2)
        for p in FIRST_RUN_POINTS:
            lbl = QLabel("•  " + p)
            lbl.setProperty("role", "heroPoint")
            lbl.setWordWrap(True)
            points.addWidget(lbl)
        lay.addLayout(points)

        lay.addSpacing(t.SP_3)
        actions = QHBoxLayout()
        actions.setSpacing(t.SP_3)
        self._create = QPushButton("Create New Review")
        self._create.setProperty("role", "heroPrimary")
        self._create.clicked.connect(self.newReviewRequested.emit)
        actions.addWidget(self._create)
        self._ask = QPushButton("Ask Fin")
        self._ask.setProperty("role", "secondary")
        self._ask.clicked.connect(self.askFinRequested.emit)
        actions.addWidget(self._ask)
        actions.addStretch(1)
        lay.addLayout(actions)

        hint = QLabel("New here? Ask Fin can explain how FinSight works and which files you need.")
        hint.setProperty("role", "context")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        wrap = QHBoxLayout()
        wrap.addStretch(1)
        wrap.addWidget(hero)
        wrap.addStretch(1)
        outer.addLayout(wrap)

    # --- public seams (stable for tests) ---
    def hero_title(self) -> str:
        return _HERO_TITLE

    def lead_text(self) -> str:
        return _HERO_LEAD

    def primary_action_text(self) -> str:
        return self._create.text()

    def refresh(self) -> None:
        # Stateless welcome; nothing to recompute. (Present so the shell can call refresh() uniformly.)
        pass
