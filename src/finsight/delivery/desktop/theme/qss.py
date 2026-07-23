# Builds the Qt stylesheet from tokens. No colors/sizes are hardcoded outside tokens.py.
from __future__ import annotations
from finsight.delivery.desktop.theme import tokens as t


def build_qss() -> str:
    return f"""
* {{
    font-family: {t.FONT_FAMILY};
    font-size: {t.FS_BASE}px;
    color: {t.TEXT_PRIMARY};
}}
QWidget#Workspace, QStackedWidget > QWidget {{ background: {t.BG_WORKSPACE}; }}
QWidget#Sidebar {{ background: {t.BG_CHROME}; border-right: 1px solid {t.BORDER}; }}
QWidget#TopBar {{ background: {t.BG_WORKSPACE}; border-bottom: 1px solid {t.BORDER}; }}
QWidget#Inspector {{ background: {t.BG_SUBTLE}; border-left: 1px solid {t.BORDER}; }}

QLabel[role="appTitle"] {{ font-size: {t.FS_TITLE}px; font-weight: 600; color: {t.TEXT_PRIMARY}; }}
QLabel[role="sectionHeader"] {{ font-size: {t.FS_H1}px; font-weight: 600; color: {t.TEXT_PRIMARY}; }}
QLabel[role="sectionSub"] {{ font-size: {t.FS_SMALL}px; color: {t.TEXT_SECONDARY}; }}
QLabel[role="navGroup"] {{ font-size: {t.FS_LABEL}px; font-weight: 600; color: {t.TEXT_MUTED}; }}
QLabel[role="context"] {{ font-size: {t.FS_SMALL}px; color: {t.TEXT_SECONDARY}; }}
QLabel[role="empty"] {{ font-size: {t.FS_BASE}px; color: {t.TEXT_MUTED}; }}
QLabel[role="emptyTitle"] {{ font-size: {t.FS_TITLE}px; font-weight: 600; color: {t.TEXT_SECONDARY}; }}
QLabel[role="kvKey"] {{ font-size: {t.FS_SMALL}px; color: {t.TEXT_MUTED}; }}
QLabel[role="kvVal"] {{ font-size: {t.FS_BASE}px; color: {t.TEXT_PRIMARY}; }}
QLabel[role="mono"] {{ font-family: {t.FONT_MONO}; }}

/* Navigation items */
QPushButton[nav="true"] {{
    text-align: left;
    padding: {t.SP_2}px {t.SP_3}px;
    border: none;
    border-radius: {t.RADIUS_MD}px;
    background: transparent;
    color: {t.TEXT_SECONDARY};
}}
QPushButton[nav="true"]:hover {{ background: {t.BG_HOVER}; color: {t.TEXT_PRIMARY}; }}
QPushButton[nav="true"]:checked {{ background: {t.ACCENT_SUBTLE_BG}; color: {t.ACCENT}; font-weight: 600; }}
QPushButton[nav="true"]:focus {{ outline: none; border: 1px solid {t.FOCUS_RING}; }}
QPushButton[nav="true"]:disabled {{ color: {t.TEXT_MUTED}; }}

/* Tables */
QTableView {{
    background: {t.BG_WORKSPACE};
    alternate-background-color: {t.BG_SUBTLE};
    gridline-color: {t.BORDER};
    border: 1px solid {t.BORDER};
    border-radius: {t.RADIUS_MD}px;
    selection-background-color: {t.ACCENT_SUBTLE_BG};
    selection-color: {t.TEXT_PRIMARY};
}}
QTableView::item {{ padding: {t.SP_1}px {t.SP_2}px; }}
QTableView::item:focus {{ outline: none; }}
QHeaderView::section {{
    background: {t.BG_CHROME};
    color: {t.TEXT_SECONDARY};
    padding: {t.SP_1}px {t.SP_2}px;
    border: none;
    border-bottom: 1px solid {t.BORDER_STRONG};
    font-size: {t.FS_SMALL}px;
    font-weight: 600;
}}

/* Inputs / secondary buttons */
QLineEdit {{
    border: 1px solid {t.BORDER_STRONG};
    border-radius: {t.RADIUS_MD}px;
    padding: {t.SP_1}px {t.SP_2}px;
    background: {t.WHITE};
}}
QLineEdit:focus {{ border: 1px solid {t.FOCUS_RING}; }}
QPushButton[role="secondary"] {{
    border: 1px solid {t.BORDER_STRONG};
    border-radius: {t.RADIUS_MD}px;
    padding: {t.SP_1}px {t.SP_3}px;
    background: {t.WHITE};
    color: {t.TEXT_PRIMARY};
}}
QPushButton[role="secondary"]:hover {{ background: {t.BG_HOVER}; }}
QPushButton[role="secondary"]:focus {{ border: 1px solid {t.FOCUS_RING}; }}
QPushButton:disabled {{ color: {t.TEXT_MUTED}; border-color: {t.BORDER}; }}

QScrollArea {{ border: none; background: transparent; }}
QToolTip {{ background: {t.TEXT_PRIMARY}; color: {t.WHITE}; border: none; padding: 3px 6px; }}
"""
