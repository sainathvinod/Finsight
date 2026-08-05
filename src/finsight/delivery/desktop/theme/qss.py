"""Build the global Qt stylesheet for authored and system high-contrast themes."""
from __future__ import annotations

import os

from PySide6.QtGui import QGuiApplication, QPalette

from finsight.delivery.desktop.theme import tokens as t


def _relative_luminance(red: int, green: int, blue: int) -> float:
    def channel(value: int) -> float:
        normalized = value / 255
        return (
            normalized / 12.92
            if normalized <= 0.04045
            else ((normalized + 0.055) / 1.055) ** 2.4
        )

    return (
        0.2126 * channel(red)
        + 0.7152 * channel(green)
        + 0.0722 * channel(blue)
    )


def _contrast_ratio(palette: QPalette) -> float:
    foreground = palette.color(QPalette.ColorRole.WindowText)
    background = palette.color(QPalette.ColorRole.Window)
    lighter = max(
        _relative_luminance(
            foreground.red(), foreground.green(), foreground.blue()
        ),
        _relative_luminance(
            background.red(), background.green(), background.blue()
        ),
    )
    darker = min(
        _relative_luminance(
            foreground.red(), foreground.green(), foreground.blue()
        ),
        _relative_luminance(
            background.red(), background.green(), background.blue()
        ),
    )
    return (lighter + 0.05) / (darker + 0.05)


def high_contrast_requested(palette: QPalette | None = None) -> bool:
    """Return whether FinSight must preserve the operating-system colors.

    An explicit test/deployment override takes precedence. Otherwise an extreme,
    strongly contrasting Window/WindowText palette is treated as an operating
    system high-contrast request.
    """

    override = os.environ.get("FINSIGHT_HIGH_CONTRAST", "").strip().lower()
    if override in {"1", "true", "yes", "on"}:
        return True
    if override in {"0", "false", "no", "off"}:
        return False
    active = palette
    if active is None:
        application = QGuiApplication.instance()
        active = (
            application.palette() if application is not None else QPalette()
        )
    foreground = active.color(QPalette.ColorRole.WindowText)
    background = active.color(QPalette.ColorRole.Window)
    luminances = (
        _relative_luminance(
            foreground.red(), foreground.green(), foreground.blue()
        ),
        _relative_luminance(
            background.red(), background.green(), background.blue()
        ),
    )
    return (
        min(luminances) <= 0.02
        and max(luminances) >= 0.95
        and _contrast_ratio(active) >= 7
    )


def _palette_color(palette: QPalette, role: QPalette.ColorRole) -> str:
    return palette.color(role).name()


def _high_contrast_qss(palette: QPalette) -> str:
    """Use system colors and strong non-color cues across every MVP surface."""

    window = _palette_color(palette, QPalette.ColorRole.Window)
    window_text = _palette_color(palette, QPalette.ColorRole.WindowText)
    base = _palette_color(palette, QPalette.ColorRole.Base)
    text = _palette_color(palette, QPalette.ColorRole.Text)
    button = _palette_color(palette, QPalette.ColorRole.Button)
    button_text = _palette_color(palette, QPalette.ColorRole.ButtonText)
    highlight = _palette_color(palette, QPalette.ColorRole.Highlight)
    highlighted_text = _palette_color(
        palette, QPalette.ColorRole.HighlightedText
    )
    disabled_text = _palette_color(palette, QPalette.ColorRole.Mid)
    return f"""
/* finsight-system-high-contrast */
QWidget#Workspace,
QWidget#ReviewManagement,
QWidget#SourceIntake,
QWidget#FinancialReview,
QWidget#RulesRepository,
QWidget#AppearanceSettings,
QWidget#PrivateAskFinDrawer,
QWidget#Workflow1Workspace,
QWidget#Workflow1PageCanvas,
QWidget#Workflow1Content,
QStackedWidget,
QScrollArea,
QDialog,
QDialog QWidget {{
    background: {window};
    color: {window_text};
}}
QWidget#ReviewManagement QLabel,
QWidget#SourceIntake QLabel,
QWidget#FinancialReview QLabel,
QWidget#RulesRepository QLabel,
QWidget#AppearanceSettings QLabel,
QWidget#PrivateAskFinDrawer QLabel,
QDialog QLabel {{
    background: transparent;
    color: {window_text};
}}
QWidget[role="card"],
QWidget[role="reviewCard"],
QWidget[role="reviewCardActive"],
QWidget[role="surfaceCard"],
QWidget[role="actionCard"],
QWidget[role="actionCardDisabled"],
QWidget[role="emptyStateCard"],
QWidget[role="progressCard"],
QWidget[role="periodPreview"],
QWidget[role="recentReviewRow"],
QWidget[role="sourceCard"],
QWidget[role="noticeCard"],
QWidget[role="reviewProgress"],
QWidget[role="chartCard"],
QWidget[role="evidencePanel"],
QWidget[role="landingIconBadge"],
QWidget[role="askFinPrivacy"],
QWidget[role="askFinInitial"],
QWidget[role="chatBubble"],
QWidget[role="chatEvidence"],
QWidget[role="chatEvidenceItem"],
QWidget[role="askFinComposerBar"] {{
    background: {base};
    color: {text};
    border: 2px solid {window_text};
    border-radius: 0;
}}
QLabel[role="statusPill"],
QLabel[role="pillAttention"],
QLabel[role="pillAbandoned"],
QLabel[role="error"],
QLabel[role="success"],
QLabel[role="warning"] {{
    background: {base};
    color: {text};
    border: 2px solid {text};
    border-radius: 0;
    padding: {t.SP_1}px {t.SP_2}px;
    font-weight: 600;
}}
QLineEdit,
QComboBox,
QSpinBox,
QDateEdit,
QTextEdit,
QPlainTextEdit,
QAbstractItemView,
QTableView {{
    background: {base};
    color: {text};
    border: 2px solid {text};
    border-radius: 0;
    selection-background-color: {highlight};
    selection-color: {highlighted_text};
}}
QHeaderView::section {{
    background: {button};
    color: {button_text};
    border: 0;
    border-bottom: 2px solid {text};
}}
QPushButton,
QToolButton {{
    background: {button};
    color: {button_text};
    border: 2px solid {button_text};
    border-radius: 0;
}}
QWidget#ReviewManagement QPushButton,
QWidget#ReviewManagement QToolButton,
QWidget#SourceIntake QPushButton,
QWidget#SourceIntake QToolButton,
QWidget#FinancialReview QPushButton,
QWidget#FinancialReview QToolButton,
QWidget#RulesRepository QPushButton,
QWidget#RulesRepository QToolButton,
QWidget#AppearanceSettings QPushButton,
QWidget#AppearanceSettings QToolButton,
QDialog QPushButton,
QDialog QToolButton {{
    background: {button};
    color: {button_text};
    border: 2px solid {button_text};
    border-radius: 0;
}}
QPushButton[role="metricButton"],
QPushButton[role="summaryAction"] {{
    min-height: 58px;
    padding: {t.SP_2}px {t.SP_3}px;
    text-align: left;
}}
QPushButton:focus,
QToolButton:focus,
QLineEdit:focus,
QComboBox:focus,
QSpinBox:focus,
QDateEdit:focus,
QTextEdit:focus,
QPlainTextEdit:focus,
QTableView:focus,
QTabBar::tab:focus {{
    border: 3px solid {highlight};
}}
QPushButton:disabled,
QToolButton:disabled {{
    background: {button};
    color: {disabled_text};
    border: 2px dashed {disabled_text};
}}
QCheckBox::indicator {{
    background: {base};
    border: 2px solid {text};
}}
QCheckBox::indicator:checked {{
    background: {highlight};
    border: 2px solid {text};
}}
QProgressBar {{
    background: {base};
    color: {text};
    border: 2px solid {text};
    border-radius: 0;
}}
QProgressBar::chunk {{ background: {highlight}; }}
QTabWidget::pane {{ background: {base}; border: 2px solid {text}; }}
QTabBar::tab {{
    background: {button};
    color: {button_text};
    border: 2px solid transparent;
}}
QTabBar::tab:selected {{
    background: {highlight};
    color: {highlighted_text};
    border: 2px solid {text};
}}
QMenu,
QToolTip {{
    background: {base};
    color: {text};
    border: 2px solid {text};
}}
QMenu::item:selected {{
    background: {highlight};
    color: {highlighted_text};
}}
"""


def _theme_value(
    theme: t.ThemePalette | str | None,
) -> t.ThemePalette:
    if theme is None:
        return t.LIGHT
    if isinstance(theme, t.ThemePalette):
        return theme
    return t.palette_for(theme)


def build_qss(
    *,
    theme: t.ThemePalette | str | None = None,
    high_contrast: bool | None = None,
    palette: QPalette | None = None,
) -> str:
    """Build a scalable global stylesheet for a FinSight appearance.

    Point sizes derive from Qt's current application font, preserving operating
    system text scaling. Passing only ``palette`` retains the legacy API used by
    high-contrast tests and deployment probes.
    """

    colors = _theme_value(theme)
    application = QGuiApplication.instance()
    system_point_size = (
        application.font().pointSizeF() if application is not None else -1
    )
    if system_point_size <= 0:
        system_point_size = t.FS_BASE * 0.75

    def points(token_size: int) -> str:
        return f"{system_point_size * token_size / t.FS_BASE:.2f}pt"

    heading_point_size = min(
        system_point_size * t.FS_H1 / t.FS_BASE,
        system_point_size + 4,
    )
    landing_title_point_size = min(
        system_point_size * t.FS_LANDING_TITLE / t.FS_BASE,
        74,
    )
    landing_subtitle_point_size = min(
        system_point_size * t.FS_LANDING_SUBTITLE / t.FS_BASE,
        system_point_size + 16,
    )
    landing_description_point_size = min(
        system_point_size * t.FS_LANDING_DESCRIPTION / t.FS_BASE,
        system_point_size + 4,
    )

    p = colors
    base_qss = f"""
/* finsight-theme-{p.name} */
* {{
    color: {p.text_primary};
}}
QWidget#Workspace,
QWidget#ReviewManagement,
QWidget#SourceIntake,
QWidget#FinancialReview,
QWidget#RulesRepository,
QWidget#AppearanceSettings,
QWidget#Workflow1Workspace,
QStackedWidget > QWidget {{
    background: {p.canvas};
}}
QWidget#Workflow1Page,
QWidget#Workflow1PageCanvas,
QWidget#Workflow1Content {{
    background: {p.canvas};
}}
QScrollArea {{ border: none; background: transparent; }}

/* Application shell */
QWidget#Sidebar,
QWidget#Workflow1Sidebar,
AdaptiveSidebar#Sidebar,
AdaptiveSidebar#Workflow1Sidebar,
#Sidebar,
#Workflow1Sidebar {{
    background: {p.navigation};
    border-right: 1px solid {p.border};
}}
QWidget#Sidebar QLabel,
QWidget#Workflow1Sidebar QLabel,
AdaptiveSidebar#Sidebar QLabel,
AdaptiveSidebar#Workflow1Sidebar QLabel,
#Sidebar QLabel,
#Workflow1Sidebar QLabel {{
    background: transparent;
    color: {p.navigation_text};
}}
QWidget#Sidebar QLabel[role="context"],
QWidget#Sidebar QLabel[role="navGroup"],
QWidget#Workflow1Sidebar QLabel[role="context"],
QWidget#Workflow1Sidebar QLabel[role="navGroup"],
AdaptiveSidebar#Sidebar QLabel[role="context"],
AdaptiveSidebar#Sidebar QLabel[role="navGroup"],
AdaptiveSidebar#Workflow1Sidebar QLabel[role="context"],
AdaptiveSidebar#Workflow1Sidebar QLabel[role="navGroup"],
#Sidebar QLabel[role="context"],
#Sidebar QLabel[role="navGroup"],
#Workflow1Sidebar QLabel[role="context"],
#Workflow1Sidebar QLabel[role="navGroup"] {{
    color: {p.navigation_muted};
}}
QWidget#Sidebar QLabel[role="context"],
QWidget#Workflow1Sidebar QLabel[role="context"],
AdaptiveSidebar#Sidebar QLabel[role="context"],
AdaptiveSidebar#Workflow1Sidebar QLabel[role="context"],
#Sidebar QLabel[role="context"],
#Workflow1Sidebar QLabel[role="context"] {{
    font-size: {points(17)};
}}
QWidget#TopBar,
QWidget#Workflow1TopBar {{
    background: {p.surface};
    border-bottom: 1px solid {p.border};
}}
QWidget#Inspector {{
    background: {p.surface_subtle};
    border-left: 1px solid {p.border};
}}

/* Type hierarchy */
QLabel[role="appTitle"] {{
    font-family: {t.FONT_DISPLAY};
    font-size: {points(t.FS_BRAND)};
    font-weight: 700;
}}
QLabel[role="sectionHeader"] {{
    font-size: {heading_point_size:.2f}pt;
    font-weight: 700;
    color: {p.text_primary};
}}
QLabel[role="sectionSub"] {{
    font-size: {points(t.FS_SMALL)};
    color: {p.text_secondary};
}}
QLabel[role="landingTitle"] {{
    font-family: {t.FONT_DISPLAY};
    font-size: {landing_title_point_size:.2f}pt;
    font-weight: 700;
    color: {p.accent if not p.is_dark else p.text_primary};
}}
QLabel[role="landingSubtitle"] {{
    font-family: {t.FONT_DISPLAY};
    font-size: {landing_subtitle_point_size:.2f}pt;
    font-weight: 650;
    color: {p.text_primary};
}}
QLabel[role="landingDescription"] {{
    font-size: {landing_description_point_size:.2f}pt;
    color: {p.text_secondary};
}}
QLabel[role="navGroup"] {{
    font-size: {points(t.FS_LABEL)};
    font-weight: 700;
    color: {p.text_muted};
}}
QLabel[role="context"] {{
    font-size: {points(t.FS_SMALL)};
    color: {p.text_secondary};
}}
QLabel[role="empty"] {{ color: {p.text_muted}; }}
QLabel[role="emptyTitle"] {{
    font-size: {points(t.FS_TITLE)};
    font-weight: 650;
    color: {p.text_secondary};
}}
QLabel[role="kvKey"] {{
    font-size: {points(t.FS_SMALL)};
    color: {p.text_muted};
}}
QLabel[role="kvVal"] {{ color: {p.text_primary}; }}
QLabel[role="mono"] {{ font-family: {t.FONT_MONO}; }}
QLabel[role="error"] {{ color: {p.error}; font-weight: 600; }}
QLabel[role="success"] {{ color: {p.success}; font-weight: 650; }}
QLabel[role="warning"] {{ color: {p.warning}; font-weight: 650; }}

/* Navigation */
QPushButton[nav="true"] {{
    min-height: 30px;
    font-size: {points(18)};
    text-align: left;
    padding: {t.SP_2}px {t.SP_3}px;
    border: 2px solid transparent;
    border-radius: {t.RADIUS_SM}px;
    background: transparent;
    color: {p.navigation_text};
}}
QPushButton[nav="true"]:hover {{
    background: {p.navigation_hover};
    color: {p.navigation_text};
}}
QPushButton[nav="true"]:checked {{
    background: {p.navigation_active};
    color: {p.navigation_active_text};
    font-weight: 700;
}}
QPushButton[nav="true"]:focus {{
    border: 2px solid {p.focus_ring};
}}
QPushButton[nav="true"]:disabled {{ color: {p.navigation_muted}; }}
QWidget#Workflow1Sidebar[density="wide"] QLabel[role="appTitle"],
QWidget#Sidebar[density="wide"] QLabel[role="appTitle"],
AdaptiveSidebar#Workflow1Sidebar[density="wide"] QLabel[role="appTitle"],
AdaptiveSidebar#Sidebar[density="wide"] QLabel[role="appTitle"],
#Workflow1Sidebar[density="wide"] QLabel[role="appTitle"],
#Sidebar[density="wide"] QLabel[role="appTitle"] {{
    font-size: {points(40)};
}}
QWidget#Workflow1Sidebar[density="wide"] QLabel[role="context"],
QWidget#Sidebar[density="wide"] QLabel[role="context"],
AdaptiveSidebar#Workflow1Sidebar[density="wide"] QLabel[role="context"],
AdaptiveSidebar#Sidebar[density="wide"] QLabel[role="context"],
#Workflow1Sidebar[density="wide"] QLabel[role="context"],
#Sidebar[density="wide"] QLabel[role="context"] {{
    font-size: {points(18)};
}}
QWidget#Workflow1Sidebar[density="wide"] QLabel[role="navGroup"],
QWidget#Sidebar[density="wide"] QLabel[role="navGroup"],
AdaptiveSidebar#Workflow1Sidebar[density="wide"] QLabel[role="navGroup"],
AdaptiveSidebar#Sidebar[density="wide"] QLabel[role="navGroup"],
#Workflow1Sidebar[density="wide"] QLabel[role="navGroup"],
#Sidebar[density="wide"] QLabel[role="navGroup"] {{
    font-size: {points(14)};
}}
QWidget#Workflow1Sidebar[density="wide"] QPushButton[nav="true"],
QWidget#Sidebar[density="wide"] QPushButton[nav="true"],
AdaptiveSidebar#Workflow1Sidebar[density="wide"] QPushButton[nav="true"],
AdaptiveSidebar#Sidebar[density="wide"] QPushButton[nav="true"],
#Workflow1Sidebar[density="wide"] QPushButton[nav="true"],
#Sidebar[density="wide"] QPushButton[nav="true"] {{
    min-height: 36px;
    font-size: {points(22)};
    padding: 10px 14px;
}}
AdaptiveSidebar#Workflow1Sidebar[density="wide"] QPushButton[nav="true"]:checked,
AdaptiveSidebar#Sidebar[density="wide"] QPushButton[nav="true"]:checked,
#Workflow1Sidebar[density="wide"] QPushButton[nav="true"]:checked,
#Sidebar[density="wide"] QPushButton[nav="true"]:checked {{
    background: {p.navigation_active};
    color: {p.navigation_active_text};
}}
AdaptiveSidebar#Workflow1Sidebar[density="wide"] QPushButton[nav="true"]:disabled,
AdaptiveSidebar#Sidebar[density="wide"] QPushButton[nav="true"]:disabled,
#Workflow1Sidebar[density="wide"] QPushButton[nav="true"]:disabled,
#Sidebar[density="wide"] QPushButton[nav="true"]:disabled {{
    color: {p.navigation_muted};
}}

/* Inputs */
QLineEdit,
QComboBox,
QSpinBox,
QDateEdit,
QTextEdit,
QPlainTextEdit {{
    border: 1px solid {p.border_strong};
    border-radius: {t.RADIUS_SM}px;
    padding: 2px 6px;
    background: {p.surface};
    color: {p.text_primary};
    selection-background-color: {p.accent_subtle};
    selection-color: {p.text_primary};
}}
QLineEdit:focus,
QComboBox:focus,
QSpinBox:focus,
QDateEdit:focus,
QTextEdit:focus,
QPlainTextEdit:focus {{
    border: 2px solid {p.focus_ring};
}}
QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox QAbstractItemView {{
    background: {p.surface_raised};
    color: {p.text_primary};
    border: 1px solid {p.border_strong};
    selection-background-color: {p.accent_subtle};
    selection-color: {p.text_primary};
}}

/* Buttons */
QPushButton,
QToolButton {{
    border: 2px solid transparent;
    border-radius: {t.RADIUS_SM}px;
    padding: 2px {t.SP_3}px;
}}
QPushButton[role="secondary"],
QToolButton[role="secondary"] {{
    border-color: {p.border_strong};
    background: {p.surface};
    color: {p.text_primary};
}}
QPushButton[role="secondary"]:hover,
QToolButton[role="secondary"]:hover {{
    background: {p.surface_hover};
}}
QWidget#Workflow1TopBar QPushButton,
QWidget#Workflow1TopBar QToolButton {{
    min-height: 32px;
    font-size: {points(16)};
}}
QPushButton[role="quiet"],
QToolButton[role="quiet"] {{
    background: transparent;
    color: {p.accent};
    font-weight: 650;
}}
QPushButton[role="quiet"]:hover,
QToolButton[role="quiet"]:hover {{
    background: {p.accent_subtle};
}}
QPushButton[role="primary"],
QToolButton[role="primary"] {{
    border-color: {p.accent};
    background: {p.accent};
    color: {p.text_on_accent};
    font-weight: 700;
}}
QPushButton[role="primary"]:hover,
QToolButton[role="primary"]:hover {{
    background: {p.accent_hover};
    border-color: {p.accent_hover};
}}
QPushButton[role="assistant"],
QToolButton[role="assistant"] {{
    border-color: {p.assistant};
    background: {p.assistant};
    color: {p.text_on_assistant};
    font-weight: 700;
}}
QPushButton[role="assistant"]:hover,
QToolButton[role="assistant"]:hover {{
    background: {p.assistant_hover};
    border-color: {p.assistant_hover};
}}

/* Embedded Ask Fin conversation */
QWidget#PrivateAskFinDrawer {{
    background: {p.canvas};
    border-left: 1px solid {p.border};
}}
QFrame[role="askFinPrivacy"] {{
    background: {p.assistant_subtle};
    border: 1px solid {p.assistant};
    border-radius: {t.RADIUS_MD}px;
}}
QLabel[role="askFinPrivacyText"] {{
    color: {p.assistant_hover if not p.is_dark else p.assistant};
    font-size: {points(t.FS_SMALL)};
    font-weight: 700;
}}
QScrollArea#AskFinConversationScroll,
QWidget#AskFinMessageCanvas,
QWidget[role="chatMessageRow"] {{
    background: transparent;
    border: none;
}}
QFrame[role="askFinInitial"] {{
    background: {p.surface};
    border: 1px solid {p.border};
    border-radius: {t.RADIUS_MD}px;
}}
QLabel[role="chatWelcome"] {{
    color: {p.text_primary};
    font-size: {points(t.FS_TITLE)};
    font-weight: 700;
}}
QPushButton[role="askFinPrompt"] {{
    min-height: 38px;
    padding: {t.SP_2}px {t.SP_3}px;
    text-align: left;
    background: {p.surface_subtle};
    color: {p.text_primary};
    border: 1px solid {p.border};
    border-radius: {t.RADIUS_MD}px;
}}
QPushButton[role="askFinPrompt"]:hover {{
    background: {p.assistant_subtle};
    border-color: {p.assistant};
}}
QFrame[role="chatBubble"] {{
    background: {p.surface_raised};
    border: 1px solid {p.border};
    border-radius: {t.RADIUS_MD}px;
}}
QFrame[role="chatBubble"][speaker="user"] {{
    background: {p.accent};
    border-color: {p.accent};
}}
QFrame[role="chatBubble"][speaker="assistant"][state="loading"] {{
    background: {p.assistant_subtle};
    border-color: {p.assistant};
}}
QFrame[role="chatBubble"][speaker="assistant"][state="refused"],
QFrame[role="chatBubble"][speaker="assistant"][state="unanswerable"] {{
    border-left: 4px solid {p.warning};
}}
QLabel[role="chatSpeaker"] {{
    color: {p.text_secondary};
    font-size: {points(t.FS_LABEL)};
    font-weight: 700;
}}
QLabel[role="chatSpeaker"][speaker="user"],
QLabel[role="chatBody"][speaker="user"] {{
    color: {p.text_on_accent};
}}
QLabel[role="chatBody"] {{
    color: {p.text_primary};
    font-size: {points(t.FS_BASE)};
}}
QWidget[role="chatResponseBody"],
QWidget[role="chatFact"],
QWidget[role="chatBullet"],
QWidget[role="chatFollowUps"],
QWidget[role="chatEvidenceGroup"],
QWidget[role="chatEvidenceDetail"] {{
    background: transparent;
    border: none;
}}
QLabel[role="chatSectionHeading"] {{
    color: {p.text_primary};
    font-size: {points(t.FS_BASE)};
    font-weight: 700;
    padding-top: {t.SP_1}px;
}}
QLabel[role="chatFactLabel"] {{
    color: {p.text_primary};
    font-size: {points(t.FS_BASE)};
    font-weight: 700;
}}
QLabel[role="chatBulletMarker"] {{
    color: {p.assistant};
    font-size: {points(t.FS_BASE)};
    font-weight: 700;
}}
QFrame[role="chatBubble"][speaker="user"] QLabel[role="chatSectionHeading"],
QFrame[role="chatBubble"][speaker="user"] QLabel[role="chatFactLabel"],
QFrame[role="chatBubble"][speaker="user"] QLabel[role="chatBulletMarker"] {{
    color: {p.text_on_accent};
}}
QLabel[role="chatLoading"] {{
    color: {p.text_secondary};
    font-size: {points(t.FS_BASE)};
    font-style: italic;
}}
QLabel[role="chatGrounding"] {{
    color: {p.success};
    font-size: {points(t.FS_LABEL)};
    font-weight: 650;
}}
QFrame[role="chatEvidence"] {{
    background: {p.surface_subtle};
    border: 1px solid {p.border};
    border-radius: {t.RADIUS_SM}px;
}}
QLabel[role="chatEvidenceRun"] {{
    color: {p.text_secondary};
    font-size: {points(t.FS_LABEL)};
}}
QLabel[role="chatEvidenceGroupHeading"] {{
    color: {p.text_primary};
    font-size: {points(t.FS_SMALL)};
    font-weight: 700;
    padding-top: {t.SP_1}px;
}}
QFrame[role="chatEvidenceItem"] {{
    background: {p.surface};
    border: 1px solid {p.border};
    border-radius: {t.RADIUS_SM}px;
}}
QLabel[role="chatEvidenceLabel"] {{
    color: {p.text_primary};
    font-size: {points(t.FS_SMALL)};
    font-weight: 650;
}}
QLabel[role="chatEvidenceMetadata"] {{
    color: {p.text_secondary};
    font-size: {points(t.FS_LABEL)};
}}
QLabel[role="chatEvidenceDetailLabel"] {{
    color: {p.text_secondary};
    font-size: {points(t.FS_LABEL)};
    font-weight: 700;
}}
QLabel[role="chatEvidenceDetailValue"] {{
    color: {p.text_primary};
    font-size: {points(t.FS_LABEL)};
}}
QLabel[role="chatFollowUpHeading"] {{
    color: {p.text_secondary};
    font-size: {points(t.FS_LABEL)};
    font-weight: 700;
}}
QPushButton[role="askFinFollowUp"] {{
    min-height: 30px;
    padding: {t.SP_1}px {t.SP_2}px;
    text-align: left;
    background: {p.assistant_subtle};
    color: {p.assistant_hover if not p.is_dark else p.text_primary};
    border: 1px solid {p.assistant};
    border-radius: {t.RADIUS_MD}px;
    font-size: {points(t.FS_SMALL)};
}}
QPushButton[role="askFinFollowUp"]:hover {{
    background: {p.surface_hover};
    border-color: {p.assistant_hover};
}}
QPushButton[role="askFinFollowUp"]:focus {{
    border: 2px solid {p.focus_ring};
}}
QPushButton[role="askFinFollowUp"]:disabled {{
    color: {p.text_muted};
    border-color: {p.border};
    background: {p.surface_subtle};
}}
QFrame[role="askFinComposerBar"] {{
    background: {p.surface};
    border: 1px solid {p.border_strong};
    border-radius: {t.RADIUS_MD}px;
}}
QPlainTextEdit#AskFinComposerInput {{
    background: transparent;
    color: {p.text_primary};
    border: none;
    padding: {t.SP_1}px;
    selection-background-color: {p.accent_subtle};
    selection-color: {p.text_primary};
}}
QPlainTextEdit#AskFinComposerInput:focus {{
    border: 2px solid {p.focus_ring};
    border-radius: {t.RADIUS_SM}px;
}}
QPushButton[role="metricButton"] {{
    min-height: 58px;
    padding: {t.SP_2}px {t.SP_3}px;
    text-align: left;
    background: {p.surface};
    color: transparent;
    border: 1px solid {p.border};
    border-radius: {t.RADIUS_MD}px;
}}
QPushButton[role="metricButton"]:hover {{
    background: {p.surface_hover};
    border-color: {p.border_strong};
}}
QPushButton[role="metricButton"][tone="warning"] {{
    border-left: 4px solid {p.warning};
}}
QPushButton[role="metricButton"][tone="danger"] {{
    border-left: 4px solid {p.error};
}}
QPushButton[role="metricButton"][tone="success"] {{
    border-left: 4px solid {p.success};
}}
QPushButton[role="summaryAction"] {{
    min-height: 46px;
    padding: {t.SP_2}px {t.SP_3}px;
    text-align: left;
    background: {p.surface_subtle};
    color: {p.text_primary};
    border: 1px solid {p.border};
    border-radius: {t.RADIUS_SM}px;
}}
QPushButton[role="summaryAction"]:hover {{
    background: {p.accent_subtle};
    border-color: {p.accent};
}}
QPushButton[role="severityAction"] {{
    min-height: 28px;
    padding: {t.SP_1}px {t.SP_2}px;
    text-align: left;
    background: {p.surface};
    border: 1px solid {p.border};
    border-radius: {t.RADIUS_SM}px;
    font-weight: 650;
}}
QPushButton[role="severityAction"][severity="critical"] {{
    color: {p.error};
    border-left: 4px solid {p.error};
}}
QPushButton[role="severityAction"][severity="high"] {{
    color: {p.warning};
    border-left: 4px solid {p.warning};
}}
QPushButton[role="severityAction"][severity="medium"] {{
    color: {p.accent};
    border-left: 4px solid {p.accent};
}}
QPushButton[role="severityAction"][severity="low"] {{
    color: {p.text_secondary};
    border-left: 4px solid {p.text_secondary};
}}
QPushButton[role="danger"],
QToolButton[role="danger"] {{
    border-color: {p.error};
    background: {p.error};
    color: {p.surface};
    font-weight: 700;
}}
QPushButton:focus,
QToolButton:focus {{
    border: 2px solid {p.focus_ring};
}}
QPushButton:disabled,
QToolButton:disabled {{
    background: {p.disabled_surface};
    border-color: {p.border};
    color: {p.disabled_text};
}}

/* Cards and panels */
QWidget[role="card"] {{
    background: {p.surface_subtle};
    border: 1px solid {p.border};
    border-radius: {t.RADIUS_MD}px;
}}
QWidget[role="surfaceCard"],
QWidget[role="actionCard"],
QWidget[role="emptyStateCard"],
QWidget[role="progressCard"],
QWidget[role="sourceCard"],
QWidget[role="noticeCard"],
QWidget[role="recentReviewRow"],
QWidget[role="reviewCard"],
QWidget[role="chartCard"],
QWidget[role="evidencePanel"] {{
    background: {p.surface};
    border: 1px solid {p.border};
    border-radius: {t.RADIUS_MD}px;
}}
QWidget[role="welcomeHero"] {{
    background: transparent;
    border: none;
}}
QWidget#CreateReviewActionCard,
QWidget#OpenPastReviewActionCard {{
    background: {p.surface_raised};
    border: 1px solid {p.border};
    border-radius: 14px;
}}
QWidget[role="landingIconBadge"] {{
    border: none;
    border-radius: 30px;
}}
QWidget[role="landingIconBadge"][tone="create"] {{
    background: {p.accent_subtle};
}}
QWidget[role="landingIconBadge"][tone="open"] {{
    background: {p.warning_subtle if not p.is_dark else p.surface_subtle};
}}
QLabel[role="landingCardTitle"] {{
    font-size: {points(22)};
    font-weight: 700;
    color: {p.text_primary};
}}
QLabel[role="landingCardDescription"] {{
    font-size: {points(18)};
    color: {p.text_secondary};
}}
QPushButton#CreateNewReviewButton,
QPushButton#OpenPastReviewButton {{
    min-height: 36px;
    font-size: {points(16)};
}}
QWidget[role="surfaceRaised"] {{
    background: {p.surface_raised};
    border: 1px solid {p.border};
    border-radius: {t.RADIUS_MD}px;
}}
QWidget[role="analysisRow"] {{
    background: transparent;
    border-bottom: 1px solid {p.border};
}}
QWidget[role="actionCard"]:hover,
QWidget[role="recentReviewRow"]:hover,
QWidget[role="reviewCard"]:hover {{
    border-color: {p.border_strong};
    background: {p.surface_raised};
}}
QWidget#CreateReviewActionCard:hover,
QWidget#OpenPastReviewActionCard:hover {{
    border-color: {p.border_strong};
    background: {p.surface};
}}
QWidget[role="actionCardDisabled"] {{
    background: {p.disabled_surface};
    border: 1px solid {p.border};
    border-radius: {t.RADIUS_MD}px;
}}
QWidget[role="reviewCardActive"] {{
    background: {p.accent_subtle};
    border: 2px solid {p.accent};
    border-radius: {t.RADIUS_MD}px;
}}
QWidget[role="periodPreview"] {{
    background: {p.accent_subtle};
    border: 1px solid {p.border};
    border-radius: {t.RADIUS_MD}px;
}}
QWidget[role="progressCard"] {{
    border-left: {t.SP_1}px solid {p.accent};
}}
QLabel[role="cardLabel"] {{
    font-size: {points(t.FS_LABEL)};
    font-weight: 700;
    color: {p.text_muted};
}}
QLabel[role="cardValue"],
QLabel[role="cardTitle"] {{
    font-size: {points(t.FS_TITLE)};
    font-weight: 700;
    color: {p.text_primary};
}}
QLabel[role="cardDetail"] {{
    font-size: {points(t.FS_SMALL)};
    color: {p.text_secondary};
}}

/* Workflow progress */
QWidget[role="reviewProgress"] {{
    background: {p.surface};
    border: 1px solid {p.border};
    border-radius: {t.RADIUS_MD}px;
}}
QLabel[role="stepActive"] {{
    background: {p.accent};
    color: {p.text_on_accent};
    border-radius: 12px;
    font-weight: 700;
}}
QLabel[role="stepPending"] {{
    background: {p.surface_subtle};
    color: {p.text_muted};
    border: 1px solid {p.border};
    border-radius: 12px;
}}
QLabel[role="stepComplete"] {{ background: transparent; }}
QLabel[role="stepLabelActive"] {{ color: {p.accent}; font-weight: 700; }}
QLabel[role="stepLabelComplete"] {{ color: {p.text_primary}; font-weight: 650; }}
QLabel[role="stepLabelPending"] {{ color: {p.text_muted}; }}

/* Tables */
QTableView,
QTableWidget,
QTreeWidget {{
    background: {p.surface};
    alternate-background-color: {p.surface_subtle};
    color: {p.text_primary};
    gridline-color: {p.border};
    border: 1px solid {p.border};
    border-radius: {t.RADIUS_SM}px;
    selection-background-color: {p.accent_subtle};
    selection-color: {p.text_primary};
}}
QTableView:focus,
QTableWidget:focus,
QTreeWidget:focus {{ border: 2px solid {p.focus_ring}; }}
QTableView::item,
QTableWidget::item,
QTreeWidget::item {{
    min-height: {t.ROW_H}px;
    padding: {t.SP_1}px {t.SP_2}px;
}}
QHeaderView::section {{
    background: {p.surface_subtle};
    color: {p.text_secondary};
    padding: {t.SP_2}px;
    border: none;
    border-bottom: 1px solid {p.border_strong};
    font-size: {points(t.FS_SMALL)};
    font-weight: 700;
}}

/* Tabs */
QTabWidget::pane {{
    border: 1px solid {p.border};
    background: {p.surface};
}}
QTabBar::tab {{
    background: {p.surface_subtle};
    color: {p.text_secondary};
    padding: {t.SP_2}px {t.SP_3}px;
    border: 2px solid transparent;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{
    background: {p.surface};
    color: {p.accent};
    font-weight: 700;
    border-bottom: 2px solid {p.accent};
}}
QTabBar::tab:focus {{ border: 2px solid {p.focus_ring}; }}

/* Metrics and state labels */
QLabel[role="metricValue"] {{
    font-size: {points(t.FS_H1)};
    font-weight: 700;
    color: {p.text_primary};
}}
QLabel[role="metricLabel"] {{
    font-size: {points(t.FS_SMALL)};
    color: {p.text_secondary};
}}
QLabel[role="statusPill"] {{
    font-size: {points(t.FS_LABEL)};
    font-weight: 700;
    color: {p.text_secondary};
    background: {p.surface_subtle};
    border: 1px solid {p.border};
    border-radius: {t.RADIUS_SM}px;
    padding: 2px 7px;
}}
QLabel[role="pillAttention"] {{
    font-size: {points(t.FS_LABEL)};
    font-weight: 700;
    color: {p.warning};
    background: {p.warning_subtle};
    border: 1px solid {p.warning};
    border-radius: {t.RADIUS_SM}px;
    padding: 2px 7px;
}}
QLabel[role="pillAbandoned"] {{
    font-size: {points(t.FS_LABEL)};
    font-weight: 700;
    color: {p.text_muted};
    background: {p.disabled_surface};
    border: 1px solid {p.border_strong};
    border-radius: {t.RADIUS_SM}px;
    padding: 2px 7px;
}}

/* Progress and checks */
QProgressBar {{
    min-height: {t.SP_2}px;
    max-height: {t.SP_2}px;
    background: {p.border};
    border: none;
    border-radius: {t.SP_1}px;
    color: {p.text_primary};
}}
QProgressBar::chunk {{
    background: {p.accent};
    border-radius: {t.SP_1}px;
}}
QProgressBar[tone="budget"]::chunk {{ background: {p.chart_budget}; }}
QProgressBar[tone="actual"]::chunk {{ background: {p.accent}; }}
QProgressBar[tone="actualOver"]::chunk {{ background: {p.error}; }}
QProgressBar[tone="actualUnder"]::chunk {{ background: {p.success}; }}
QCheckBox {{ spacing: {t.SP_2}px; color: {p.text_primary}; }}
QCheckBox::indicator {{
    width: 17px;
    height: 17px;
    border: 2px solid {p.border_strong};
    border-radius: 4px;
    background: {p.surface};
}}
QCheckBox::indicator:checked {{
    background: {p.accent};
    border-color: {p.accent};
}}
QCheckBox:focus {{
    border: 2px solid {p.focus_ring};
    border-radius: {t.RADIUS_SM}px;
}}

/* Appearance control, dialogs, menus, and supporting chrome */
QWidget[role="appearanceControl"] {{
    background: transparent;
}}
QDialog {{
    background: {p.canvas};
    color: {p.text_primary};
}}
QMenu {{
    background: {p.surface_raised};
    color: {p.text_primary};
    border: 1px solid {p.border_strong};
}}
QMenu::item {{ padding: {t.SP_2}px {t.SP_4}px; }}
QMenu::item:selected {{
    background: {p.accent_subtle};
    color: {p.text_primary};
}}
QToolTip {{
    background: {p.tooltip_surface};
    color: {p.tooltip_text};
    border: 1px solid {p.border_strong};
    padding: {t.SP_1}px {t.SP_2}px;
}}
"""

    active_palette = palette
    if active_palette is None:
        active_palette = (
            application.palette() if application is not None else QPalette()
        )
    use_high_contrast = (
        high_contrast_requested(active_palette)
        if high_contrast is None
        else high_contrast
    )
    return (
        base_qss + _high_contrast_qss(active_palette)
        if use_high_contrast
        else base_qss
    )
