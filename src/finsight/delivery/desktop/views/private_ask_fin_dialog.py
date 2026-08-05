"""Private, review-scoped Ask Fin right-side drawer."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QAccessible,
    QAccessibleAnnouncementEvent,
    QKeyEvent,
    QKeySequence,
    QShortcut,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from finsight.application.ai.private_contracts import (
    AskFinContext,
    LocalAiSetupState,
)
from finsight.delivery.desktop.components.iconography import content_icon
from finsight.delivery.desktop.theme import tokens as t


_INLINE_CITATION = re.compile(r"\s*\[[a-z][a-z0-9_-]*:[^\[\]\s]+\]")
_BULLET_LINE = re.compile(r"^(?:[-*•]|\d+[.)])\s+(.+)$")
_LABELED_LINE = re.compile(
    r"^(?:\*\*)?([A-Za-z][A-Za-z0-9 /&()'’–—-]{1,48})"
    r"(?:\*\*)?\s*:\s*(.+)$"
)
_PRESENTATION_MARKERS = re.compile(r"(\*\*|__|`)")
_SECTION_TITLES = {
    "direct answer",
    "evidence",
    "exact evidence",
    "key facts",
    "key supporting facts",
    "supporting evidence",
    "what happened",
    "why finsight flagged it",
    "why it matters",
    "what to look at next",
}


def _label(text: str, role: str, *, wrap: bool = False) -> QLabel:
    value = QLabel(text)
    value.setProperty("role", role)
    value.setTextFormat(Qt.TextFormat.PlainText)
    value.setWordWrap(wrap)
    return value


def _presentation_text(value: Any) -> str:
    """Remove lightweight model formatting without interpreting model markup."""

    return _PRESENTATION_MARKERS.sub("", str(value or "")).strip()


def _answer_blocks(text: str) -> tuple[tuple[str, str, str], ...]:
    """Parse plain-text answer structure into presentation-only blocks.

    The returned values are always rendered by ``QLabel`` in ``PlainText``
    mode. This deliberately supports readable labels and bullets without
    accepting HTML, Markdown, or any other executable rich-text surface.
    """

    blocks: list[tuple[str, str, str]] = []
    for raw_line in str(text or "").replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        bullet = _BULLET_LINE.match(line)
        if bullet:
            blocks.append(("bullet", "", _presentation_text(bullet.group(1))))
            continue
        labeled = _LABELED_LINE.match(line)
        if labeled:
            blocks.append(
                (
                    "fact",
                    _presentation_text(labeled.group(1)),
                    _presentation_text(labeled.group(2)),
                )
            )
            continue
        clean = _presentation_text(line)
        if clean.casefold().rstrip(":") in _SECTION_TITLES:
            blocks.append(("heading", "", clean.rstrip(":")))
        else:
            blocks.append(("paragraph", "", clean))
    return tuple(blocks)


def _follow_up_questions(value: Any) -> tuple[str, ...]:
    """Return a small, ordered set of safe presentation prompts."""

    if isinstance(value, str):
        values = (value,)
    else:
        try:
            values = tuple(value or ())
        except TypeError:
            values = ()
    output: list[str] = []
    seen: set[str] = set()
    for item in values:
        question = " ".join(str(item or "").split())
        normalized = question.casefold()
        if not question or normalized in seen:
            continue
        seen.add(normalized)
        output.append(question)
        if len(output) == 4:
            break
    return tuple(output)


def _evidence_group_label(object_type: str) -> str:
    return {
        "account": "Account evidence",
        "budget-source": "Budget evidence",
        "department": "Department evidence",
        "finding": "Finding evidence",
        "leadership-summary": "Review summary evidence",
        "review": "Review evidence",
        "rule-result": "Rule evidence",
        "transaction": "GED transaction evidence",
        "vendor": "Vendor evidence",
    }.get(object_type.casefold(), "Supporting evidence")


def _evidence_metadata(citation: Any) -> str:
    """Build a business-readable evidence locator from allow-listed fields."""

    navigation = getattr(citation, "navigation_target", {}) or {}
    if not isinstance(navigation, dict):
        try:
            navigation = dict(navigation)
        except (TypeError, ValueError):
            navigation = {}
    details = getattr(citation, "evidence_details", {}) or {}
    if not isinstance(details, dict):
        try:
            details = dict(details)
        except (TypeError, ValueError):
            details = {}

    def value(*keys: str) -> Any:
        for key in keys:
            if details.get(key) not in (None, ""):
                return details[key]
            if navigation.get(key) not in (None, ""):
                return navigation[key]
        return ""

    parts: list[str] = []
    source_role = str(value("source_role") or "").strip().upper()
    if source_role in {"BUDGET", "GED"}:
        parts.append(source_role)
    source_file = str(value("source_file", "file_name", "filename") or "").strip()
    if source_file:
        parts.append(source_file)
    worksheet = str(value("worksheet", "sheet") or "").strip()
    if worksheet:
        parts.append(worksheet)
    row = value("source_row", "row")
    if row not in (None, ""):
        parts.append(f"Row {row}")
    cell = str(value("cell", "source_cell", "excel_reference") or "").strip()
    if cell:
        parts.append(f"Cell {cell}")
    column = str(value("source_column", "column") or "").strip()
    if column and not cell:
        parts.append(f"Column {column}")
    rule = str(value("rule_name", "rule") or "").strip()
    version = str(value("rule_version") or "").strip()
    if rule:
        parts.append(f"Rule {rule}" + (f" · version {version}" if version else ""))
    return " · ".join(parts)


def _evidence_detail_rows(citation: Any) -> tuple[tuple[str, str], ...]:
    details = getattr(citation, "evidence_details", {}) or {}
    if not isinstance(details, dict):
        try:
            details = dict(details)
        except (TypeError, ValueError):
            details = {}
    field_map = (
        ("Account", ("account", "account_number", "account_name")),
        ("Vendor", ("vendor", "vendor_name")),
        (
            "Transaction",
            ("transaction_reference", "journal_number", "invoice_number"),
        ),
        ("Amount", ("amount", "amount_label")),
        ("Field", ("field", "field_name", "column_name")),
        ("Rule", ("rule_name", "rule")),
        ("Rule version", ("rule_version",)),
    )
    output: list[tuple[str, str]] = []
    for label, keys in field_map:
        value = next(
            (str(details[key]) for key in keys if details.get(key) not in (None, "")),
            "",
        )
        if value:
            output.append((label, value))
    return tuple(output)


def _context_value(context: Any, name: str) -> str:
    if isinstance(context, dict):
        return str(context.get(name) or "")
    return str(getattr(context, name, "") or "")


def _review_context(
    *,
    review_id: str,
    object_type: str,
    object_id: str,
    label: str = "",
    validation_run_id: str = "",
) -> AskFinContext:
    """Construct a review context compatible with the active app contract."""

    values: dict[str, Any] = {
        "review_id": review_id,
        "object_type": object_type,
        "object_id": object_id,
        "label": label,
    }
    fields = getattr(AskFinContext, "__dataclass_fields__", {})
    if validation_run_id and "validation_run_id" in fields:
        values["validation_run_id"] = validation_run_id
    return AskFinContext(**values)


@dataclass
class _ChatMessage:
    """Presentation-only message retained inside one review-scoped drawer."""

    role: str
    text: str
    status: str = ""
    citations: tuple[Any, ...] = ()
    pending: bool = False
    evidence_expanded: bool = False
    validation_run_id: str = ""
    follow_up_questions: tuple[str, ...] = ()

    @property
    def speaker(self) -> str:
        return "You" if self.role == "user" else "Fin"

    def __getitem__(self, index: int) -> str:
        """Keep old screenshot helpers readable without keeping the old UI."""

        return (self.speaker if self.role == "user" else "Ask Fin", self.text)[index]


class _TranscriptCompatibility:
    """Text-only compatibility seam for focused tests and capture scripts."""

    def __init__(self, owner: "PrivateAskFinDialog"):
        self._owner = owner

    def toPlainText(self) -> str:
        key = self._owner._review_id or "__help__"
        parts: list[str] = []
        for message in self._owner._conversation_by_review.get(key, ()):
            if message.pending:
                continue
            parts.extend((message.speaker, message.text))
        return "\n".join(parts)


class _CitationLayoutCompatibility:
    """Count the latest answer's sources without exposing a fake layout."""

    def __init__(self, owner: "PrivateAskFinDialog"):
        self._owner = owner

    def count(self) -> int:
        key = self._owner._review_id or "__help__"
        for message in reversed(self._owner._conversation_by_review.get(key, ())):
            if message.role == "assistant" and not message.pending:
                return len(message.citations)
        return 0


class _AskFinComposer(QPlainTextEdit):
    """Compact multiline composer with desktop-chat keyboard behavior."""

    sendRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AskFinComposerInput")
        self.setAccessibleName("Question for Ask Fin")
        self.setAccessibleDescription(
            "Type a question. Press Enter to send or Shift plus Enter for a new line."
        )
        self.setPlaceholderText("Ask about this review or how FinSight works")
        self.setTabChangesFocus(True)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.document().contentsChanged.connect(self._adjust_height)
        self._adjust_height()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
                return
            self.sendRequested.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def text(self) -> str:
        """Compatibility with the former QLineEdit composer."""

        return self.toPlainText()

    def setText(self, value: str) -> None:
        """Compatibility with focused capture scripts."""

        self.setPlainText(value)
        self.moveCursor(QTextCursor.MoveOperation.End)

    def _adjust_height(self) -> None:
        document_height = int(self.document().documentLayout().documentSize().height())
        self.setFixedHeight(max(44, min(92, document_height + 14)))


class _AskFinMessageBubble(QFrame):
    """One visually and semantically grouped chat message."""

    citationActivated = Signal(object)
    evidenceStateChanged = Signal(bool)
    followUpActivated = Signal(str)

    def __init__(
        self,
        message: _ChatMessage,
        *,
        show_follow_ups: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self._message = message
        self.follow_up_buttons: list[QPushButton] = []
        self.setProperty("role", "chatBubble")
        self.setProperty("speaker", message.role)
        self.setProperty("state", "loading" if message.pending else message.status)
        self.setObjectName(
            "AskFinLoadingBubble"
            if message.pending
            else (
                "AskFinUserBubble"
                if message.role == "user"
                else "AskFinAssistantBubble"
            )
        )
        self.setAccessibleName(
            (
                "Fin is reviewing the recorded evidence"
                if message.pending
                else f"{message.speaker} message: {message.text}"
            )
        )
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Minimum,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(t.SP_3, t.SP_2, t.SP_3, t.SP_2)
        layout.setSpacing(t.SP_1)

        speaker = _label(message.speaker, "chatSpeaker")
        speaker.setProperty("speaker", message.role)
        layout.addWidget(speaker)

        if message.pending:
            body = _label(
                "Reviewing the recorded evidence…",
                "chatLoading",
                wrap=True,
            )
            body.setAccessibleName("Ask Fin is reviewing the recorded evidence")
            layout.addWidget(body)
            return

        response_body = QWidget()
        response_body.setProperty("role", "chatResponseBody")
        response_body.setAccessibleName(f"{message.speaker} message text")
        body_layout = QVBoxLayout(response_body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(t.SP_2)
        blocks = (
            _answer_blocks(message.text)
            if message.role == "assistant"
            else (("paragraph", "", message.text),)
        )
        if not blocks:
            blocks = (("paragraph", "", message.text),)
        for kind, label_text, block_text in blocks:
            if kind == "heading":
                section = _label(block_text, "chatSectionHeading", wrap=True)
                section.setAccessibleName(f"Response section: {block_text}")
                body_layout.addWidget(section)
                continue
            if kind == "fact":
                fact = QWidget()
                fact.setProperty("role", "chatFact")
                fact_layout = QHBoxLayout(fact)
                fact_layout.setContentsMargins(0, 0, 0, 0)
                fact_layout.setSpacing(t.SP_1)
                fact_label = _label(f"{label_text}:", "chatFactLabel", wrap=True)
                fact_label.setAccessibleName(f"{label_text} label")
                fact_layout.addWidget(fact_label, 0, Qt.AlignmentFlag.AlignTop)
                value = _label(block_text, "chatBody", wrap=True)
                value.setProperty("speaker", message.role)
                value.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByKeyboard
                    | Qt.TextInteractionFlag.TextSelectableByMouse
                )
                value.setAccessibleName(f"{label_text}: {block_text}")
                fact_layout.addWidget(value, 1)
                body_layout.addWidget(fact)
                continue
            if kind == "bullet":
                bullet = QWidget()
                bullet.setProperty("role", "chatBullet")
                bullet_layout = QHBoxLayout(bullet)
                bullet_layout.setContentsMargins(t.SP_1, 0, 0, 0)
                bullet_layout.setSpacing(t.SP_2)
                marker = _label("•", "chatBulletMarker")
                marker.setAccessibleName("Bullet")
                bullet_layout.addWidget(marker, 0, Qt.AlignmentFlag.AlignTop)
                value = _label(block_text, "chatBody", wrap=True)
                value.setProperty("speaker", message.role)
                value.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByKeyboard
                    | Qt.TextInteractionFlag.TextSelectableByMouse
                )
                value.setAccessibleName(f"Bullet: {block_text}")
                bullet_layout.addWidget(value, 1)
                body_layout.addWidget(bullet)
                continue
            paragraph = _label(block_text, "chatBody", wrap=True)
            paragraph.setProperty("speaker", message.role)
            paragraph.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByKeyboard
                | Qt.TextInteractionFlag.TextSelectableByMouse
            )
            paragraph.setAccessibleName(f"{message.speaker} message paragraph")
            body_layout.addWidget(paragraph)
        layout.addWidget(response_body)

        if message.role != "assistant":
            return

        if message.citations:
            count = len(message.citations)
            source_word = "source" if count == 1 else "sources"
            grounded = _label(
                f"Grounded in {count} verified {source_word}",
                "chatGrounding",
                wrap=True,
            )
            grounded.setAccessibleName(
                f"This answer is grounded in {count} verified {source_word}"
            )
            layout.addWidget(grounded)

            self.evidence_toggle = QPushButton(f"Show evidence ({count})")
            self.evidence_toggle.setObjectName("AskFinEvidenceToggle")
            self.evidence_toggle.setProperty("role", "quiet")
            self.evidence_toggle.setCheckable(True)
            self.evidence_toggle.setChecked(message.evidence_expanded)
            self.evidence_toggle.setAccessibleName(
                f"Show {count} evidence {source_word} for this answer"
            )
            self.evidence_toggle.toggled.connect(self._toggle_evidence)
            layout.addWidget(
                self.evidence_toggle,
                0,
                Qt.AlignmentFlag.AlignLeft,
            )

            self.evidence_panel = QFrame()
            self.evidence_panel.setProperty("role", "chatEvidence")
            self.evidence_panel.setAccessibleName(
                f"Evidence for this answer, {count} verified {source_word}"
            )
            evidence_layout = QVBoxLayout(self.evidence_panel)
            evidence_layout.setContentsMargins(t.SP_2, t.SP_2, t.SP_2, t.SP_2)
            evidence_layout.setSpacing(t.SP_2)
            if message.validation_run_id:
                run_label = _label(
                    f"Validation run: {message.validation_run_id}",
                    "chatEvidenceRun",
                    wrap=True,
                )
                run_label.setAccessibleName(
                    f"Validation run {message.validation_run_id}"
                )
                evidence_layout.addWidget(run_label)
            grouped: dict[str, list[Any]] = {}
            for citation in message.citations:
                object_type = str(
                    getattr(citation, "object_type", "source") or "source"
                ).casefold()
                grouped.setdefault(object_type, []).append(citation)
            for object_type, citations in grouped.items():
                group = QWidget()
                group.setProperty("role", "chatEvidenceGroup")
                group_layout = QVBoxLayout(group)
                group_layout.setContentsMargins(0, 0, 0, 0)
                group_layout.setSpacing(t.SP_1)
                group_title = _evidence_group_label(object_type)
                heading = _label(group_title, "chatEvidenceGroupHeading")
                heading.setAccessibleName(group_title)
                group_layout.addWidget(heading)
                for citation in citations:
                    item = QFrame()
                    item.setProperty("role", "chatEvidenceItem")
                    item_layout = QVBoxLayout(item)
                    item_layout.setContentsMargins(
                        t.SP_2,
                        t.SP_2,
                        t.SP_2,
                        t.SP_2,
                    )
                    item_layout.setSpacing(t.SP_1)
                    title_row = QHBoxLayout()
                    title_row.setContentsMargins(0, 0, 0, 0)
                    title_row.setSpacing(t.SP_2)
                    label = str(
                        getattr(citation, "label", "Recorded source")
                        or "Recorded source"
                    )
                    source = _label(label, "chatEvidenceLabel", wrap=True)
                    source.setAccessibleName(
                        f"Recorded {object_type.replace('-', ' ')} source: {label}"
                    )
                    title_row.addWidget(source, 1)
                    action = QPushButton("Open source")
                    action.setProperty("role", "quiet")
                    action.setAccessibleName(f"Open Ask Fin citation {label}")
                    action.clicked.connect(
                        lambda _checked=False, value=citation: (
                            self.citationActivated.emit(value)
                        )
                    )
                    title_row.addWidget(action, 0, Qt.AlignmentFlag.AlignTop)
                    item_layout.addLayout(title_row)
                    metadata = _evidence_metadata(citation)
                    if metadata:
                        locator = _label(
                            metadata,
                            "chatEvidenceMetadata",
                            wrap=True,
                        )
                        locator.setAccessibleName(f"Source location: {metadata}")
                        item_layout.addWidget(locator)
                    for detail_label, detail_value in _evidence_detail_rows(citation):
                        detail = QWidget()
                        detail.setProperty("role", "chatEvidenceDetail")
                        detail_layout = QHBoxLayout(detail)
                        detail_layout.setContentsMargins(0, 0, 0, 0)
                        detail_layout.setSpacing(t.SP_1)
                        key_label = _label(
                            f"{detail_label}:",
                            "chatEvidenceDetailLabel",
                        )
                        key_label.setAccessibleName(f"{detail_label} label")
                        detail_layout.addWidget(
                            key_label,
                            0,
                            Qt.AlignmentFlag.AlignTop,
                        )
                        value_label = _label(
                            detail_value,
                            "chatEvidenceDetailValue",
                            wrap=True,
                        )
                        value_label.setAccessibleName(f"{detail_label}: {detail_value}")
                        detail_layout.addWidget(value_label, 1)
                        item_layout.addWidget(detail)
                    group_layout.addWidget(item)
                evidence_layout.addWidget(group)
            self.evidence_panel.setVisible(message.evidence_expanded)
            layout.addWidget(self.evidence_panel)

        if show_follow_ups and message.follow_up_questions:
            follow_up = QWidget()
            follow_up.setProperty("role", "chatFollowUps")
            follow_up.setAccessibleName("Suggested follow-up questions")
            follow_up_layout = QVBoxLayout(follow_up)
            follow_up_layout.setContentsMargins(0, t.SP_1, 0, 0)
            follow_up_layout.setSpacing(t.SP_1)
            follow_up_layout.addWidget(_label("Continue with", "chatFollowUpHeading"))
            for question in message.follow_up_questions:
                row = QHBoxLayout()
                row.setContentsMargins(0, 0, 0, 0)
                button = QPushButton(question)
                button.setObjectName("AskFinFollowUpChip")
                button.setProperty("role", "askFinFollowUp")
                button.setAccessibleName(f"Ask follow-up question: {question}")
                button.setAccessibleDescription(
                    "Ask this grounded follow-up in the active review."
                )
                button.clicked.connect(
                    lambda _checked=False, value=question: self.followUpActivated.emit(
                        value
                    )
                )
                row.addWidget(button)
                row.addStretch(1)
                follow_up_layout.addLayout(row)
                self.follow_up_buttons.append(button)
            layout.addWidget(follow_up)

    def _toggle_evidence(self, expanded: bool) -> None:
        self._message.evidence_expanded = bool(expanded)
        self.evidence_panel.setVisible(bool(expanded))
        count = len(self._message.citations)
        self.evidence_toggle.setText(
            f"{'Hide' if expanded else 'Show'} evidence ({count})"
        )
        self.evidence_toggle.setAccessibleName(
            f"{'Hide' if expanded else 'Show'} {count} evidence "
            f"{'source' if count == 1 else 'sources'} for this answer"
        )
        self.evidenceStateChanged.emit(bool(expanded))


class _AskFinMessageRow(QWidget):
    """Responsive row that aligns user and Fin bubbles distinctly."""

    def __init__(self, bubble: _AskFinMessageBubble, *, role: str, parent=None):
        super().__init__(parent)
        self.bubble = bubble
        self.setProperty("role", "chatMessageRow")
        self.setProperty("speaker", role)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        if role == "user":
            layout.addStretch(1)
            layout.addWidget(bubble, 4)
        else:
            layout.addWidget(bubble, 4)
            layout.addStretch(1)

    def resizeEvent(self, event) -> None:
        self.bubble.setMaximumWidth(max(190, int(self.width() * 0.86)))
        super().resizeEvent(event)


class PrivateAskFinDialog(QWidget):
    """Reusable integrated drawer backed only by the private Ask Fin service."""

    citationActivated = Signal(object)
    closeRequested = Signal()

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._context: AskFinContext | None = None
        self._review_id = ""
        self._no_review_selected = False
        self._provider_available: bool | None = None
        self._session_is_ready = False
        self._running = False
        self._running_reviews: set[str] = set()
        self._load_generation = 0
        self._suggested_buttons: list[QPushButton] = []
        self._follow_up_buttons: list[QPushButton] = []
        self._conversation_by_review: dict[str, list[_ChatMessage]] = {}
        self._validation_run_by_review: dict[str, str] = {}
        self._resolved_context_by_review: dict[
            str,
            tuple[str, AskFinContext],
        ] = {}
        self._rendered_rows: list[_AskFinMessageRow] = []
        self._last_accessibility_announcement = ""
        self._scroll_animation: QPropertyAnimation | None = None
        self.setObjectName("PrivateAskFinDrawer")
        self.setWindowTitle("Ask Fin")
        self.setAccessibleName("Ask Fin private assistant drawer")
        self.setMinimumWidth(360)
        self.setMaximumWidth(560)

        root = QVBoxLayout(self)
        root.setContentsMargins(t.SP_4, t.SP_4, t.SP_4, t.SP_4)
        root.setSpacing(t.SP_3)

        heading = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(t.SP_1)
        title_box.addWidget(_label("Ask Fin", "sectionHeader"))
        title_box.addWidget(
            _label(
                "Private explanations from your local Ollama model.",
                "sectionSub",
                wrap=True,
            )
        )
        heading.addLayout(title_box, 1)
        self._close_button = QPushButton()
        self._close_button.setObjectName("AskFinDrawerClose")
        self._close_button.setProperty("role", "quiet")
        self._close_button.setAccessibleName("Close Ask Fin")
        self._close_button.setToolTip("Close Ask Fin (Esc)")
        self._close_button.setFixedSize(32, 32)
        self._close_button.clicked.connect(self.request_close)
        self.refresh_icon()
        heading.addWidget(self._close_button, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(heading)

        privacy = QFrame()
        privacy.setProperty("role", "askFinPrivacy")
        privacy_layout = QVBoxLayout(privacy)
        privacy_layout.setContentsMargins(t.SP_3, t.SP_2, t.SP_3, t.SP_2)
        privacy_layout.setSpacing(0)
        privacy_label = _label(
            "Private local AI · Ollama only · no cloud fallback",
            "askFinPrivacyText",
            wrap=True,
        )
        privacy_label.setAccessibleDescription(
            "Only authorized facts from the active review are sent to the "
            "local model. The deterministic rule engine remains the source "
            "of truth."
        )
        privacy_label.setToolTip(privacy_label.accessibleDescription())
        privacy_layout.addWidget(privacy_label)
        root.addWidget(privacy)

        context_row = QHBoxLayout()
        context_row.setSpacing(t.SP_2)
        self._mode = _label("Preparing mode…", "statusPill")
        self._mode.setAccessibleName("Ask Fin mode")
        context_row.addWidget(self._mode)
        self._scope = _label("Active review", "context", wrap=True)
        self._scope.setAccessibleName("Ask Fin scope")
        context_row.addWidget(self._scope, 1)
        self._clear_scope = QPushButton("Clear scope")
        self._clear_scope.setProperty("role", "quiet")
        self._clear_scope.setAccessibleName(
            "Clear Ask Fin context and return to the active review"
        )
        self._clear_scope.setToolTip("Return Ask Fin to the full active-review scope.")
        self._clear_scope.clicked.connect(self._clear_context)
        self._clear_scope.setVisible(False)
        context_row.addWidget(self._clear_scope)
        root.addLayout(context_row)

        self._unavailable_card = QFrame()
        self._unavailable_card.setObjectName("AskFinUnavailableCard")
        self._unavailable_card.setProperty("role", "noticeCard")
        unavailable_layout = QVBoxLayout(self._unavailable_card)
        unavailable_layout.setContentsMargins(t.SP_3, t.SP_3, t.SP_3, t.SP_3)
        unavailable_layout.setSpacing(t.SP_2)
        self._availability_guidance = _label(
            "Ask Fin could not connect to local Ollama. Start Ollama, then retry.",
            "warning",
            wrap=True,
        )
        self._availability_guidance.setAccessibleName("Ask Fin unavailable message")
        unavailable_layout.addWidget(self._availability_guidance)
        unavailable_actions = QHBoxLayout()
        self._retry_button = QPushButton("Retry")
        self._retry_button.setProperty("role", "secondary")
        self._retry_button.setAccessibleName("Retry local Ask Fin connection")
        self._retry_button.clicked.connect(self.retry)
        unavailable_actions.addWidget(self._retry_button)
        unavailable_actions.addStretch(1)
        unavailable_layout.addLayout(unavailable_actions)
        self._unavailable_card.setVisible(False)
        root.addWidget(self._unavailable_card)

        self._conversation_surface = QWidget()
        self._conversation_surface.setObjectName("AskFinConversationSurface")
        conversation_layout = QVBoxLayout(self._conversation_surface)
        conversation_layout.setContentsMargins(0, 0, 0, 0)
        conversation_layout.setSpacing(t.SP_2)

        self._conversation_scroll = QScrollArea()
        self._conversation_scroll.setObjectName("AskFinConversationScroll")
        self._conversation_scroll.setAccessibleName("Ask Fin conversation")
        self._conversation_scroll.setAccessibleDescription(
            "Review-scoped conversation. User messages are aligned right "
            "and Fin responses are aligned left."
        )
        self._conversation_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._conversation_scroll.setWidgetResizable(True)
        self._conversation_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._message_canvas = QWidget()
        self._message_canvas.setObjectName("AskFinMessageCanvas")
        self._message_layout = QVBoxLayout(self._message_canvas)
        self._message_layout.setContentsMargins(t.SP_1, t.SP_1, t.SP_1, t.SP_2)
        self._message_layout.setSpacing(t.SP_3)

        self._initial_panel = QFrame()
        self._initial_panel.setObjectName("AskFinInitialPanel")
        self._initial_panel.setProperty("role", "askFinInitial")
        self._initial_panel.setAccessibleName("Ask Fin conversation suggestions")
        initial_layout = QVBoxLayout(self._initial_panel)
        initial_layout.setContentsMargins(t.SP_3, t.SP_3, t.SP_3, t.SP_3)
        initial_layout.setSpacing(t.SP_2)
        initial_layout.addWidget(_label("What would you like to know?", "chatWelcome"))
        self._greeting = _label(
            "Ask how FinSight works or ask about the recorded financial "
            "review after validation.",
            "cardDetail",
            wrap=True,
        )
        self._greeting.setAccessibleName("Ask Fin greeting")
        initial_layout.addWidget(self._greeting)
        self._suggestion_holder = QWidget()
        self._suggestion_holder.setObjectName("AskFinSuggestions")
        self._suggestion_layout = QVBoxLayout(self._suggestion_holder)
        self._suggestion_layout.setContentsMargins(0, 0, 0, 0)
        self._suggestion_layout.setSpacing(t.SP_2)
        initial_layout.addWidget(self._suggestion_holder)
        self._suggestions = self._suggestion_holder
        self._message_layout.addWidget(self._initial_panel)
        self._message_layout.addStretch(1)
        self._conversation_scroll.setWidget(self._message_canvas)
        conversation_layout.addWidget(self._conversation_scroll, 1)

        self._message = _label("", "context", wrap=True)
        self._message.setAccessibleName("Ask Fin status message")
        self._message.setVisible(False)
        conversation_layout.addWidget(self._message)

        self._question_holder = QFrame()
        self._question_holder.setObjectName("AskFinComposerBar")
        self._question_holder.setProperty("role", "askFinComposerBar")
        question_row = QHBoxLayout(self._question_holder)
        question_row.setContentsMargins(t.SP_2, t.SP_2, t.SP_2, t.SP_2)
        question_row.setSpacing(t.SP_2)
        self._question = _AskFinComposer()
        self._question.sendRequested.connect(self._send)
        question_row.addWidget(self._question, 1)
        self._send_button = QPushButton("Send")
        self._send_button.setProperty("role", "assistant")
        self._send_button.setAccessibleName("Send question to Ask Fin")
        self._send_button.clicked.connect(self._send)
        question_row.addWidget(self._send_button, 0, Qt.AlignmentFlag.AlignBottom)
        conversation_layout.addWidget(self._question_holder)

        self._provider = _label("Checking local Ollama…", "context", wrap=True)
        self._provider.setParent(self)
        self._provider.setAccessibleName("Local Ask Fin connection")
        self._provider.setVisible(False)
        self._transcript = _TranscriptCompatibility(self)
        self._citation_layout = _CitationLayoutCompatibility(self)
        root.addWidget(self._conversation_surface, 1)
        self._unavailable_filler = QWidget()
        self._unavailable_filler.setObjectName("AskFinUnavailableFiller")
        self._unavailable_filler.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self._unavailable_filler.setVisible(False)
        root.addWidget(self._unavailable_filler, 1)

        self._escape_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self._escape_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._escape_shortcut.activated.connect(self.request_close)

    def request_close(self) -> None:
        self.hide()
        self.closeRequested.emit()

    def refresh_icon(self) -> None:
        """Refresh the drawer's theme-aware close glyph."""

        self._close_button.setIcon(content_icon("close", tone="header"))

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.request_close()
            event.accept()
            return
        super().keyPressEvent(event)

    def retry(self) -> None:
        self._provider_available = None
        self._session_is_ready = False
        self._sync_interaction_state()
        if self._review_id:
            self._load_session()
        else:
            self.initialize_status()

    def refresh_review(self) -> None:
        """Refresh the sealed run while preserving same-run conversation."""

        if not self._review_id:
            return
        self._session_is_ready = False
        self._sync_interaction_state()
        # Discover the authoritative run without sending a context from the
        # previous run. If the run is unchanged, the context remains usable;
        # if it changed, _session_ready clears continuation state and rebinds
        # any explicit UI selection to the new run.
        self._load_session(include_context=False)

    def initialize_status(self) -> None:
        """Run the startup local-runtime check without reading review data."""

        self._load_generation += 1
        generation = self._load_generation
        self._provider_available = None
        self._sync_interaction_state()
        setup = getattr(
            self._controller,
            "private_ask_fin_setup_status_async",
            None,
        )
        if setup is not None:
            setup(
                lambda result: (
                    self._setup_status_ready(result)
                    if generation == self._load_generation
                    else None
                ),
                lambda error: (
                    self._provider_failed(error)
                    if generation == self._load_generation
                    else None
                ),
            )
            return
        self._controller.private_ask_fin_provider_status_async(
            lambda result: (
                self._provider_ready(result)
                if generation == self._load_generation
                else None
            ),
            lambda error: (
                self._provider_failed(error)
                if generation == self._load_generation
                else None
            ),
        )

    def open_for(
        self,
        *,
        review_id: str,
        object_type: str = "",
        object_id: str = "",
        label: str,
    ) -> None:
        self._no_review_selected = False
        self._review_id = review_id
        self._context = (
            _review_context(
                review_id=review_id,
                object_type=object_type,
                object_id=object_id,
                label=label,
                validation_run_id=self._validation_run_by_review.get(review_id, ""),
            )
            if object_type and object_id
            else None
        )
        if self._context is not None:
            self._resolved_context_by_review.pop(review_id, None)
        self._scope.setText(label or object_type.replace("_", " ").title())
        self._clear_scope.setVisible(self._context is not None)
        self._provider_available = None
        self._session_is_ready = False
        self._render_conversation()
        self._sync_interaction_state()
        self.show()
        self._load_session()
        self._question.setFocus(Qt.FocusReason.OtherFocusReason)

    def open_without_review(self) -> None:
        """Open application-help framing before a review has been selected."""

        self._load_generation += 1
        self._no_review_selected = True
        self._review_id = ""
        self._context = None
        self._mode.setText("Help Mode")
        self._scope.setText("No review selected")
        self._clear_scope.setVisible(False)
        self._greeting.setText(
            "Create or open a financial review to ask grounded questions. "
            "Local setup status remains available here."
        )
        self._replace_suggestions(
            (
                "How do I start a financial review?",
                "What files does FinSight support?",
            )
        )
        self._session_is_ready = False
        self._provider_available = None
        self._render_conversation()
        self._sync_interaction_state()
        self.show()
        self.initialize_status()

    def _set_running(self, running: bool, *, review_id: str | None = None) -> None:
        key = review_id or self._review_id or "__help__"
        if running:
            self._running_reviews.add(key)
        else:
            self._running_reviews.discard(key)
        self._running = (self._review_id or "__help__") in self._running_reviews
        available = self._provider_available is True and self._session_is_ready
        self._question.setEnabled(available)
        self._question.setReadOnly(self._running or not available)
        self._send_button.setEnabled(available and not self._running)
        for button in self._suggested_buttons:
            button.setEnabled(available and not self._running)
        for button in self._follow_up_buttons:
            button.setEnabled(available and not self._running)
        self._send_button.setText("Send")
        self._send_button.setAccessibleDescription(
            (
                "Ask Fin is reviewing the recorded evidence."
                if self._running
                else "Send this question to the private local assistant."
            )
        )
        self._update_initial_state()

    def _clear_context(self) -> None:
        if not self._review_id:
            return
        self._context = None
        self._resolved_context_by_review.pop(self._review_id, None)
        self._scope.setText("Active review")
        self._clear_scope.setVisible(False)
        self._session_is_ready = False
        self._sync_interaction_state()
        self._load_session()

    def _sync_interaction_state(self) -> None:
        key = self._review_id or "__help__"
        self._set_running(key in self._running_reviews, review_id=key)
        unavailable = self._provider_available is False
        self._unavailable_card.setVisible(unavailable)
        self._conversation_surface.setVisible(not unavailable)
        self._unavailable_filler.setVisible(unavailable)
        if self._provider_available is False:
            self._message.clear()
            self._message.setVisible(False)
        elif self._provider_available is None:
            self._message.setText("Connecting to local Ollama…")
            self._message.setVisible(True)
        elif self._no_review_selected:
            self._message.setText(
                "Create or open a review to start Application Help Mode. "
                "No information is sent to a cloud service."
            )
            self._message.setVisible(True)
        elif not self._session_is_ready:
            self._message.setText("Preparing private review context…")
            self._message.setVisible(True)
        else:
            self._message.clear()
            self._message.setVisible(False)
        self._update_initial_state()

    def _load_session(self, *, include_context: bool = True) -> None:
        self._load_generation += 1
        generation = self._load_generation
        self._sync_interaction_state()
        setup = getattr(
            self._controller,
            "private_ask_fin_setup_status_async",
            None,
        )
        if setup is not None:
            setup(
                lambda result: (
                    self._setup_status_ready(result)
                    if generation == self._load_generation
                    else None
                ),
                lambda error: (
                    self._provider_failed(error)
                    if generation == self._load_generation
                    else None
                ),
            )
        else:
            self._controller.private_ask_fin_provider_status_async(
                lambda result: (
                    self._provider_ready(result)
                    if generation == self._load_generation
                    else None
                ),
                lambda error: (
                    self._provider_failed(error)
                    if generation == self._load_generation
                    else None
                ),
            )
        self._controller.private_ask_fin_session_async(
            lambda result: (
                self._session_ready(result)
                if generation == self._load_generation
                else None
            ),
            lambda error: (
                self._session_failed(error)
                if generation == self._load_generation
                else None
            ),
            context=self._context if include_context else None,
            review_id=self._review_id,
        )

    def _setup_status_ready(self, status: Any) -> None:
        state = getattr(status, "state", None)
        available = state is LocalAiSetupState.HEALTHY
        self._provider_available = available
        labels = {
            LocalAiSetupState.NOT_INSTALLED: "Ollama not installed",
            LocalAiSetupState.SERVICE_NOT_RUNNING: ("Ollama service not running"),
            LocalAiSetupState.MODEL_NOT_DOWNLOADED: ("Local model not downloaded"),
            LocalAiSetupState.MODEL_NOT_APPROVED: "Local model unavailable",
            LocalAiSetupState.MODEL_VERIFICATION_FAILED: ("Local model unavailable"),
            LocalAiSetupState.CONNECTION_FAILURE: ("Local Ollama connection failed"),
            LocalAiSetupState.TIMEOUT: "Local Ollama timed out",
            LocalAiSetupState.HEALTHY: "Local Ollama ready",
        }
        self._provider.setText(labels.get(state, "Local Ollama unavailable"))
        self._provider.setProperty("role", "success" if available else "warning")
        self._availability_guidance.setText(self._setup_unavailable_message(state))
        self._provider.style().unpolish(self._provider)
        self._provider.style().polish(self._provider)
        self._sync_interaction_state()

    def _provider_ready(self, status: Any) -> None:
        available = bool(getattr(status, "generation_available", False))
        self._provider_available = available
        self._provider.setText(
            "Local Ollama ready" if available else "Local Ollama unavailable"
        )
        self._provider.setProperty("role", "success" if available else "warning")
        self._availability_guidance.setText(
            self._provider_reason_message(str(getattr(status, "reason", "") or ""))
        )
        self._provider.style().unpolish(self._provider)
        self._provider.style().polish(self._provider)
        self._sync_interaction_state()

    def _provider_failed(self, _error: BaseException) -> None:
        self._provider_available = False
        self._provider.setText("Local Ollama connection failed")
        self._provider.setProperty("role", "warning")
        self._availability_guidance.setText(
            "Ask Fin could not connect to local Ollama. Start Ollama, then retry."
        )
        self._sync_interaction_state()

    @staticmethod
    def _setup_unavailable_message(state: Any) -> str:
        return {
            LocalAiSetupState.NOT_INSTALLED: (
                "Ask Fin could not find Ollama on this computer. Install or "
                "open Ollama, then retry."
            ),
            LocalAiSetupState.SERVICE_NOT_RUNNING: (
                "Ask Fin could not connect to local Ollama. Start Ollama, then retry."
            ),
            LocalAiSetupState.MODEL_NOT_DOWNLOADED: (
                "Ask Fin could not find the selected model in Ollama. "
                "Download the model, then retry."
            ),
            LocalAiSetupState.MODEL_NOT_APPROVED: (
                "Ask Fin could not use the selected local model. Retry the connection."
            ),
            LocalAiSetupState.MODEL_VERIFICATION_FAILED: (
                "Ask Fin could not use the selected local model. Retry the connection."
            ),
            LocalAiSetupState.CONNECTION_FAILURE: (
                "Ask Fin could not connect to local Ollama. Start Ollama, then retry."
            ),
            LocalAiSetupState.TIMEOUT: (
                "Local Ollama did not respond in time. Check that it is "
                "running, then retry."
            ),
        }.get(
            state,
            "Ask Fin could not connect to local Ollama. Start Ollama, then retry.",
        )

    @staticmethod
    def _provider_reason_message(reason: str) -> str:
        return {
            "status_timeout": ("The local Ollama service did not respond in time."),
            "request_timeout": ("The local Ollama service did not respond in time."),
            "model_missing": (
                "Ask Fin could not find the selected model in Ollama. "
                "Download the model, then retry."
            ),
            "model_identity_unconfigured": (
                "Ask Fin could not use the selected local model. Retry the connection."
            ),
            "connection_refused": (
                "Ask Fin could not connect to local Ollama. Start Ollama, then retry."
            ),
            "unreachable": (
                "Ask Fin could not connect to local Ollama. Start Ollama, then retry."
            ),
        }.get(
            reason,
            "Ask Fin could not connect to local Ollama. Start Ollama, then retry.",
        )

    def _session_ready(self, session: Any) -> None:
        key = self._review_id or "__help__"
        validation_run_id = str(getattr(session, "validation_run_id", "") or "")
        previous_run_id = self._validation_run_by_review.get(key)
        if (
            validation_run_id
            and previous_run_id
            and validation_run_id != previous_run_id
        ):
            # A citation is valid only for the sealed Validation Run that
            # produced it.  Start a clean conversation when the same review
            # is revalidated so an old bubble can never navigate into newer
            # evidence under the same review identifier.
            self._conversation_by_review.pop(key, None)
            self._running_reviews.discard(key)
            self._resolved_context_by_review.pop(key, None)
            self._render_conversation()
            self._announce(
                "Ask Fin cleared the previous conversation because this "
                "review has a new validation run."
            )
        if validation_run_id:
            self._validation_run_by_review[key] = validation_run_id
        resolved = self._resolved_context_by_review.get(key)
        if resolved is not None and resolved[0] != validation_run_id:
            self._resolved_context_by_review.pop(key, None)
        if self._context is not None and validation_run_id:
            self._context = _review_context(
                review_id=self._context.review_id,
                object_type=self._context.object_type,
                object_id=self._context.object_id,
                label=self._context.label,
                validation_run_id=validation_run_id,
            )
        mode = getattr(getattr(session, "mode", None), "value", "")
        self._mode.setText(
            "Help Mode" if mode == "application_help" else "Financial Review Mode"
        )
        self._greeting.setText(str(getattr(session, "greeting", "")))
        scope = str(getattr(session, "scope_label", "") or "")
        if self._context is not None:
            self._scope.setText(
                self._context.label
                or self._context.object_type.replace("_", " ").title()
            )
        elif scope:
            self._scope.setText(scope)
        self._replace_suggestions(
            tuple(getattr(session, "suggested_questions", ()) or ())
        )
        self._session_is_ready = True
        self._sync_interaction_state()

    def _session_failed(self, _error: BaseException) -> None:
        self._session_is_ready = False
        self._provider_available = False
        self._availability_guidance.setText(
            "Ask Fin could not prepare this review. Retry the connection."
        )
        self._sync_interaction_state()

    def _replace_suggestions(self, questions: tuple[str, ...]) -> None:
        while self._suggestion_layout.count():
            item = self._suggestion_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._suggested_buttons.clear()
        for question in questions[:4]:
            button = QPushButton(question)
            button.setProperty("role", "askFinPrompt")
            button.setAccessibleName(f"Ask suggested question: {question}")
            button.setAccessibleDescription(
                "Use this suggested question in the active review."
            )
            button.clicked.connect(
                lambda _checked=False, value=question: self._ask(value)
            )
            self._suggestion_layout.addWidget(button)
            self._suggested_buttons.append(button)
        self._sync_interaction_state()

    def _send(self) -> None:
        self._ask(self._question.text())

    def _ask(self, question: str) -> None:
        clean = str(question).strip()
        request_review_id = self._review_id or "__help__"
        if (
            request_review_id in self._running_reviews
            or not clean
            or self._provider_available is not True
            or not self._session_is_ready
        ):
            return
        request_context = self._safe_conversation_context(request_review_id)
        self._question.clear()
        messages = self._conversation_by_review.setdefault(request_review_id, [])
        validation_run_id = self._validation_run_by_review.get(request_review_id, "")
        messages.append(
            _ChatMessage(
                role="user",
                text=clean,
                validation_run_id=validation_run_id,
            )
        )
        messages.append(
            _ChatMessage(
                role="assistant",
                text="Reviewing the recorded evidence…",
                pending=True,
                validation_run_id=validation_run_id,
            )
        )
        if request_review_id == (self._review_id or "__help__"):
            self._render_conversation(animated=True)
        self._set_running(True, review_id=request_review_id)
        self._message.setText("Retrieving authorized review evidence locally…")
        self._message.setVisible(False)
        self._announce("Ask Fin is reviewing the recorded evidence.")
        self._controller.private_ask_fin_ask_async(
            clean,
            lambda result: self._answer_ready(result, review_id=request_review_id),
            lambda error: self._answer_failed(error, review_id=request_review_id),
            context=request_context,
            review_id=("" if request_review_id == "__help__" else request_review_id),
        )

    def _answer_ready(self, result: Any, *, review_id: str | None = None) -> None:
        key = review_id or self._review_id or "__help__"
        self._set_running(False, review_id=key)
        answer = str(getattr(result, "answer_text", "") or "")
        status = getattr(getattr(result, "status", None), "value", "")
        result_review_id = str(getattr(result, "review_id", "") or "")
        result_run_id = str(getattr(result, "validation_run_id", "") or "")
        expected_run_id = self._validation_run_by_review.get(key, "")
        if key != "__help__" and result_review_id and result_review_id != key:
            self._remove_pending(key)
            if key == (self._review_id or "__help__"):
                self._message.setText(
                    "Ask Fin did not return evidence for the active review."
                )
                self._message.setVisible(True)
                self._render_conversation(animated=True)
                self._announce("Ask Fin did not return evidence for the active review.")
            return
        if (
            key != "__help__"
            and expected_run_id
            and result_run_id
            and result_run_id != expected_run_id
        ):
            self._conversation_by_review.pop(key, None)
            self._running_reviews.discard(key)
            self._resolved_context_by_review.pop(key, None)
            if key == (self._review_id or "__help__"):
                self._render_conversation(animated=True)
                self._announce(
                    "Ask Fin discarded an answer from an older validation run."
                )
                # Reload the authoritative session rather than guessing which
                # run identifier is newer. This prevents repeated stale-run
                # rejections if revalidation completed while the drawer was
                # open.
                self.refresh_review()
            return
        if status == "unavailable":
            self._remove_pending(key)
            if key == (self._review_id or "__help__"):
                self._provider_available = False
                self._availability_guidance.setText(
                    "Ask Fin could not connect to local Ollama. Start Ollama, "
                    "then retry."
                )
                self._sync_interaction_state()
            return
        display_answer = _INLINE_CITATION.sub("", answer).strip()
        citations = tuple(getattr(result, "citations", ()) or ())
        follow_ups = _follow_up_questions(getattr(result, "follow_up_questions", ()))
        if status == "ok":
            self._capture_resolved_context(
                key,
                getattr(result, "resolved_context", None),
                validation_run_id=result_run_id or expected_run_id,
            )
        self._replace_pending(
            key,
            _ChatMessage(
                role="assistant",
                text=display_answer or answer,
                status=status,
                citations=citations,
                validation_run_id=result_run_id or expected_run_id,
                follow_up_questions=follow_ups,
            ),
        )
        if key != (self._review_id or "__help__"):
            return
        self._message.setText(
            {
                "ok": "Answer grounded in the cited active-review records.",
                "refused": (
                    "Ask Fin cannot make financial decisions. Review the "
                    "recorded evidence and use human governance."
                ),
                "unanswerable": (
                    "The active review does not contain enough recorded "
                    "evidence to answer that question."
                ),
                "unavailable": (
                    "Local Ollama is unavailable. No external service was used."
                ),
            }.get(status, "Ask Fin could not complete the request.")
        )
        self._message.setVisible(False)
        self._render_conversation(animated=True)
        self._question.setFocus(Qt.FocusReason.OtherFocusReason)
        source_count = len(citations)
        if status == "ok":
            self._announce(
                "Ask Fin answered"
                + (
                    f" with {source_count} recorded "
                    f"{'source' if source_count == 1 else 'sources'}."
                    if source_count
                    else "."
                )
            )
        elif status == "refused":
            self._announce("Ask Fin cannot make that financial decision.")
        elif status == "unanswerable":
            self._announce(
                "Ask Fin could not answer from the recorded review evidence."
            )
        else:
            self._announce("Ask Fin could not complete the request.")

    def _answer_failed(
        self,
        _error: BaseException,
        *,
        review_id: str | None = None,
    ) -> None:
        key = review_id or self._review_id or "__help__"
        self._set_running(False, review_id=key)
        self._remove_pending(key)
        if key != (self._review_id or "__help__"):
            return
        self._provider_available = False
        self._availability_guidance.setText(
            "Ask Fin could not connect to local Ollama. Start Ollama, then retry."
        )
        self._sync_interaction_state()
        self._announce("Ask Fin could not connect to local Ollama. Retry is available.")

    def _safe_conversation_context(self, key: str) -> AskFinContext | None:
        resolved = self._resolved_context_by_review.get(key)
        expected_run_id = self._validation_run_by_review.get(key, "")
        if resolved is not None and resolved[0] == expected_run_id:
            return resolved[1]
        if resolved is not None:
            self._resolved_context_by_review.pop(key, None)
        return self._context

    def _capture_resolved_context(
        self,
        key: str,
        context: Any,
        *,
        validation_run_id: str,
    ) -> None:
        if context is None or key == "__help__" or not validation_run_id:
            return
        review_id = _context_value(context, "review_id")
        object_type = _context_value(context, "object_type")
        object_id = _context_value(context, "object_id")
        label = _context_value(context, "label")
        context_run_id = _context_value(context, "validation_run_id")
        if (
            review_id != key
            or not object_type
            or not object_id
            or (context_run_id and context_run_id != validation_run_id)
        ):
            return
        safe_context = _review_context(
            review_id=review_id,
            object_type=object_type,
            object_id=object_id,
            label=label,
            validation_run_id=validation_run_id,
        )
        self._resolved_context_by_review[key] = (
            validation_run_id,
            safe_context,
        )
        if key == (self._review_id or "__help__"):
            self._scope.setText(
                label or f"{object_type.replace('_', ' ').title()} {object_id}"
            )
            self._clear_scope.setVisible(True)

    def _append_conversation(
        self,
        role: str,
        text: str,
        *,
        review_id: str | None = None,
    ) -> None:
        key = review_id or self._review_id or "__help__"
        normalized_role = (
            "user" if str(role).strip().casefold() in {"you", "user"} else "assistant"
        )
        self._conversation_by_review.setdefault(key, []).append(
            _ChatMessage(
                role=normalized_role,
                text=str(text),
                validation_run_id=self._validation_run_by_review.get(key, ""),
            )
        )
        if key == (self._review_id or "__help__"):
            self._render_conversation(animated=True)

    def _replace_pending(self, key: str, message: _ChatMessage) -> None:
        messages = self._conversation_by_review.setdefault(key, [])
        for index in range(len(messages) - 1, -1, -1):
            if messages[index].pending:
                messages[index] = message
                return
        messages.append(message)

    def _remove_pending(self, key: str) -> None:
        messages = self._conversation_by_review.get(key, [])
        self._conversation_by_review[key] = [
            message for message in messages if not message.pending
        ]
        if key == (self._review_id or "__help__"):
            self._render_conversation(animated=True)

    def _render_conversation(self, *, animated: bool = False) -> None:
        key = self._review_id or "__help__"
        for row in self._rendered_rows:
            self._message_layout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
        self._rendered_rows.clear()
        self._follow_up_buttons.clear()
        messages = tuple(self._conversation_by_review.get(key, ()))
        latest_answer_index = next(
            (
                index
                for index in range(len(messages) - 1, -1, -1)
                if messages[index].role == "assistant" and not messages[index].pending
            ),
            -1,
        )
        has_pending = any(message.pending for message in messages)
        for index, message in enumerate(messages):
            bubble = _AskFinMessageBubble(
                message,
                show_follow_ups=(
                    index == latest_answer_index
                    and not has_pending
                    and bool(message.follow_up_questions)
                ),
            )
            bubble.citationActivated.connect(self.citationActivated.emit)
            bubble.followUpActivated.connect(self._ask)
            bubble.evidenceStateChanged.connect(
                lambda _expanded: self._scroll_to_bottom(animated=True)
            )
            self._follow_up_buttons.extend(bubble.follow_up_buttons)
            row = _AskFinMessageRow(bubble, role=message.role)
            self._message_layout.insertWidget(
                max(1, self._message_layout.count() - 1),
                row,
            )
            self._rendered_rows.append(row)
        self._update_initial_state()
        self._scroll_to_bottom(animated=animated)

    def _update_initial_state(self) -> None:
        key = self._review_id or "__help__"
        has_messages = bool(self._conversation_by_review.get(key))
        self._initial_panel.setVisible(not has_messages)
        self._suggestion_holder.setVisible(
            not has_messages and bool(self._suggested_buttons)
        )

    def _scroll_to_bottom(self, *, animated: bool) -> None:
        self._message_layout.activate()
        self._message_canvas.adjustSize()
        bar = self._conversation_scroll.verticalScrollBar()
        target = bar.maximum()
        application = QApplication.instance()
        if (
            not animated
            or bar.value() >= target
            or (
                application is not None
                and application.platformName().casefold() == "offscreen"
            )
        ):
            bar.setValue(target)
            return
        if self._scroll_animation is not None:
            self._scroll_animation.stop()
        animation = QPropertyAnimation(bar, b"value", self)
        animation.setDuration(160)
        animation.setStartValue(bar.value())
        animation.setEndValue(target)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._scroll_animation = animation
        animation.start()

    def _announce(self, message: str) -> None:
        normalized = " ".join(str(message).split())
        if not normalized:
            return
        self._last_accessibility_announcement = normalized
        event = QAccessibleAnnouncementEvent(self, normalized)
        event.setPoliteness(QAccessible.AnnouncementPoliteness.Polite)
        QAccessible.updateAccessibility(event)

    def conversation_messages(
        self, review_id: str | None = None
    ) -> tuple[_ChatMessage, ...]:
        """Return the presentation messages for focused UI verification."""

        key = review_id or self._review_id or "__help__"
        return tuple(self._conversation_by_review.get(key, ()))


# New code may use the explicit name while existing imports remain compatible.
PrivateAskFinDrawer = PrivateAskFinDialog


__all__ = ["PrivateAskFinDialog", "PrivateAskFinDrawer"]
