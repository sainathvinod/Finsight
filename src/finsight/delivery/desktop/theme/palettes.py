# Accessibility palettes + zoom (target-product §20; F-14-05, NFR-024–027, DEC-030).
#   The design tokens (tokens.py) are the LIGHT baseline. A palette is the same token names with color
#   overrides (Dark, High Contrast) and, for zoom, numeric size tokens (fonts/spacing/radii/dimensions)
#   multiplied by a scale. build_qss(palette) re-themes the ENTIRE surface from one call — every widget
#   selects via role/nav properties, so no per-screen work is needed. Severity keeps its shape+label
#   glyph so meaning never depends on color (NFR-025).
from __future__ import annotations
import types
from finsight.delivery.desktop.theme import tokens as _t

# Numeric size tokens that scale with zoom (colors/strings/SEVERITY are never scaled).
_SCALABLE = ("FS_BASE", "FS_SMALL", "FS_LABEL", "FS_TITLE", "FS_H1",
             "SP_1", "SP_2", "SP_3", "SP_4", "SP_5", "SP_6",
             "RADIUS_SM", "RADIUS_MD", "SIDEBAR_W", "TOPBAR_H", "ROW_H")

# Dark theme — dark surfaces, light text, a brighter accent for contrast on dark.
DARK = {
    "WHITE": "#242A31",            # used as input/card fill in QSS -> a dark surface here
    "BG_WORKSPACE": "#1A1D21",
    "BG_CHROME": "#22262B",
    "BG_SUBTLE": "#1F2226",
    "BG_HOVER": "#2A2F35",
    "TEXT_PRIMARY": "#E8EAED",
    "TEXT_SECONDARY": "#AEB6C0",
    "TEXT_MUTED": "#7C8592",
    "TEXT_ON_ACCENT": "#0F1114",
    "BORDER": "#333941",
    "BORDER_STRONG": "#454C55",
    "ACCENT": "#6E97E0",
    "ACCENT_HOVER": "#82A6E6",
    "ACCENT_SUBTLE_BG": "#26324A",
    "FOCUS_RING": "#8FB0EC",
}

# High-contrast — pure black/white with a strong focus ring (WCAG AAA-oriented).
HIGH_CONTRAST = {
    "WHITE": "#FFFFFF",
    "BG_WORKSPACE": "#FFFFFF",
    "BG_CHROME": "#FFFFFF",
    "BG_SUBTLE": "#FFFFFF",
    "BG_HOVER": "#E6E6E6",
    "TEXT_PRIMARY": "#000000",
    "TEXT_SECONDARY": "#000000",
    "TEXT_MUTED": "#1A1A1A",
    "TEXT_ON_ACCENT": "#FFFFFF",
    "BORDER": "#000000",
    "BORDER_STRONG": "#000000",
    "ACCENT": "#0000CC",
    "ACCENT_HOVER": "#0000AA",
    "ACCENT_SUBTLE_BG": "#D6E0FF",
    "FOCUS_RING": "#0000CC",
}

# Named color palettes. LIGHT is the tokens baseline (no overrides).
PALETTES = {"light": {}, "dark": DARK, "high-contrast": HIGH_CONTRAST}


def make_palette(name: str = "light", scale: float = 1.0):
    """Return a palette namespace exposing every token name — color overrides for `name`, numeric size
    tokens multiplied by `scale`. Defaults reproduce the light tokens exactly."""
    overrides = PALETTES.get(name, {})
    ns = types.SimpleNamespace()
    for key in dir(_t):
        if key.isupper():
            setattr(ns, key, getattr(_t, key))
    for key in _SCALABLE:
        val = getattr(ns, key, None)
        if isinstance(val, (int, float)):
            setattr(ns, key, max(1, round(val * scale)))
    for key, value in overrides.items():
        setattr(ns, key, value)
    ns.NAME = name
    ns.SCALE = scale
    return ns
