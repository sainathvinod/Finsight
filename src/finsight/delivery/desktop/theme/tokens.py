# Design tokens — the ONLY place colors, spacing, radii, and type are defined.
# Restrained, monochrome, enterprise. A single muted accent is used solely for selection,
# keyboard focus, and links. No gradients, neon, or decorative color.
from __future__ import annotations

# --- Neutral palette (monochrome) ---
WHITE = "#FFFFFF"
BG_WORKSPACE = "#FFFFFF"     # primary working surface
BG_CHROME = "#F4F5F7"        # sidebar / app chrome (neutral gray)
BG_SUBTLE = "#FAFBFC"        # subtle panel / alternate row
BG_HOVER = "#EDEFF2"         # hover on neutral surfaces

TEXT_PRIMARY = "#1A1D21"     # dark charcoal
TEXT_SECONDARY = "#5B6470"
TEXT_MUTED = "#8A929E"
TEXT_ON_ACCENT = "#FFFFFF"

BORDER = "#E3E6EA"           # thin hairline
BORDER_STRONG = "#D0D5DB"

# --- Single accent (selection / focus / links) ---
ACCENT = "#2E5AAC"           # muted slate-blue
ACCENT_HOVER = "#274B8F"
ACCENT_SUBTLE_BG = "#EAF0FB" # selected-row / active-nav background
FOCUS_RING = "#2E5AAC"

# --- Status / severity secondary channel (never the sole channel; paired with shape + label) ---
SEVERITY = {
    "Critical": {"glyph": "⬟", "color": "#B4232A"},  # ⬟ pentagon
    "High":     {"glyph": "▲", "color": "#B8791B"},  # ▲ triangle
    "Medium":   {"glyph": "◆", "color": "#4B5563"},  # ◆ diamond
    "Low":      {"glyph": "▪", "color": "#8A929E"},  # ▪ small square
}
STATUS_OK = "#2F7A43"
STATUS_ATTENTION = "#B8791B"

# --- Spacing scale (px) ---
SP_1 = 4
SP_2 = 8
SP_3 = 12
SP_4 = 16
SP_5 = 24
SP_6 = 32

# --- Radii (modest; square-ish controls) ---
RADIUS_SM = 2
RADIUS_MD = 4

# --- Typography ---
FONT_FAMILY = '"Helvetica Neue", "SF Pro Text", "Segoe UI", Arial, sans-serif'
FONT_MONO = '"SF Mono", "Menlo", "Consolas", monospace'
FS_BASE = 13
FS_SMALL = 12
FS_LABEL = 11
FS_TITLE = 15
FS_H1 = 20

# --- Dimensions ---
SIDEBAR_W = 208
TOPBAR_H = 48
ROW_H = 30
