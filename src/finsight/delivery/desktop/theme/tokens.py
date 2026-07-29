"""Semantic design tokens for the FinSight desktop application.

The application has two authored palettes. ``System Default`` is resolved by the
appearance service to one of these palettes, except when the operating system is
using a high-contrast palette; high contrast always keeps the system colors.

The module-level color aliases remain the light-palette values for compatibility
with older presentation components. New code should consume a ``ThemePalette``
through :func:`palette_for`.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class ThemePalette:
    """A complete semantic color contract for one authored appearance."""

    name: str
    is_dark: bool
    canvas: str
    chrome: str
    surface: str
    surface_raised: str
    surface_subtle: str
    surface_hover: str
    navigation: str
    navigation_hover: str
    navigation_active: str
    navigation_text: str
    navigation_muted: str
    navigation_active_text: str
    text_primary: str
    text_secondary: str
    text_muted: str
    text_on_accent: str
    text_on_assistant: str
    border: str
    border_strong: str
    accent: str
    accent_hover: str
    accent_subtle: str
    assistant: str
    assistant_hover: str
    assistant_subtle: str
    focus_ring: str
    success: str
    success_subtle: str
    warning: str
    warning_subtle: str
    error: str
    error_subtle: str
    disabled_surface: str
    disabled_text: str
    tooltip_surface: str
    tooltip_text: str
    chart_budget: str
    chart_actual: str
    chart_eac: str
    chart_neutral: str

    @property
    def severity(self) -> Mapping[str, Mapping[str, str]]:
        """Return severity colors with a text glyph as the second status channel."""

        return MappingProxyType(
            {
                "Critical": MappingProxyType({"glyph": "⬟", "color": self.error}),
                "High": MappingProxyType({"glyph": "▲", "color": self.warning}),
                "Medium": MappingProxyType(
                    {"glyph": "◆", "color": self.text_secondary}
                ),
                "Low": MappingProxyType({"glyph": "▪", "color": self.text_muted}),
            }
        )


LIGHT = ThemePalette(
    name="light",
    is_dark=False,
    canvas="#F4F6F9",
    chrome="#F8FAFC",
    surface="#FFFFFF",
    surface_raised="#FFFFFF",
    surface_subtle="#EEF2F7",
    surface_hover="#E7EEF6",
    navigation="#17324F",
    navigation_hover="#224363",
    navigation_active="#EAF2FA",
    navigation_text="#F5F8FC",
    navigation_muted="#B9C8D8",
    navigation_active_text="#174F86",
    text_primary="#202938",
    text_secondary="#536174",
    text_muted="#748196",
    text_on_accent="#FFFFFF",
    text_on_assistant="#FFFFFF",
    border="#D7DFE9",
    border_strong="#B9C6D5",
    accent="#175493",
    accent_hover="#104476",
    accent_subtle="#E7F0FA",
    assistant="#0B7D80",
    assistant_hover="#08666A",
    assistant_subtle="#E2F3F2",
    focus_ring="#2B6FB7",
    success="#1B7A49",
    success_subtle="#E5F4EB",
    warning="#A65D00",
    warning_subtle="#FFF0D3",
    error="#C42A20",
    error_subtle="#FBE8E6",
    disabled_surface="#E9EDF2",
    disabled_text="#758195",
    tooltip_surface="#202938",
    tooltip_text="#F8FAFC",
    chart_budget="#98A4B5",
    chart_actual="#175493",
    chart_eac="#6E86A3",
    chart_neutral="#5F6C7E",
)

DARK = ThemePalette(
    name="dark",
    is_dark=True,
    canvas="#101722",
    chrome="#141D29",
    surface="#182330",
    surface_raised="#1D2A39",
    surface_subtle="#222F3F",
    surface_hover="#293A4E",
    navigation="#0C1621",
    navigation_hover="#17283A",
    navigation_active="#223B57",
    navigation_text="#EEF3F8",
    navigation_muted="#A4B2C2",
    navigation_active_text="#F5F8FC",
    text_primary="#F0F3F7",
    text_secondary="#B9C3CF",
    text_muted="#96A3B2",
    text_on_accent="#FFFFFF",
    text_on_assistant="#102635",
    border="#344457",
    border_strong="#53657A",
    accent="#78AFE5",
    accent_hover="#91BEEA",
    accent_subtle="#203A55",
    assistant="#52C5C1",
    assistant_hover="#70D5D1",
    assistant_subtle="#193D3E",
    focus_ring="#8FC4F5",
    success="#6DD097",
    success_subtle="#173A2D",
    warning="#F1B950",
    warning_subtle="#493616",
    error="#FF8C86",
    error_subtle="#4B2629",
    disabled_surface="#263241",
    disabled_text="#8B98A8",
    tooltip_surface="#EDF2F7",
    tooltip_text="#101722",
    chart_budget="#98A8BC",
    chart_actual="#78AFE5",
    chart_eac="#C3CFDD",
    chart_neutral="#AAB5C2",
)

PALETTES: Mapping[str, ThemePalette] = MappingProxyType(
    {LIGHT.name: LIGHT, DARK.name: DARK}
)


def palette_for(name: str) -> ThemePalette:
    """Resolve an authored palette by stable lowercase name."""

    try:
        return PALETTES[str(name).strip().lower()]
    except KeyError as exc:
        raise ValueError(f"Unknown FinSight theme palette: {name!r}") from exc


# --- Compatibility aliases (light palette) ---------------------------------
# Existing components import these module attributes. They intentionally remain
# stable while those components migrate to semantic, runtime-aware styling.
WHITE = LIGHT.surface
BG_WORKSPACE = LIGHT.surface
BG_CHROME = LIGHT.chrome
BG_SUBTLE = LIGHT.surface_subtle
BG_HOVER = LIGHT.surface_hover
TEXT_PRIMARY = LIGHT.text_primary
TEXT_SECONDARY = LIGHT.text_secondary
TEXT_MUTED = LIGHT.text_muted
TEXT_ON_ACCENT = LIGHT.text_on_accent
BORDER = LIGHT.border
BORDER_STRONG = LIGHT.border_strong
ACCENT = LIGHT.accent
ACCENT_HOVER = LIGHT.accent_hover
ACCENT_SUBTLE_BG = LIGHT.accent_subtle
FOCUS_RING = LIGHT.focus_ring
SEVERITY = LIGHT.severity
STATUS_OK = LIGHT.success
STATUS_ATTENTION = LIGHT.warning

# --- Spacing scale (px) ----------------------------------------------------
SP_1 = 4
SP_2 = 8
SP_3 = 12
SP_4 = 16
SP_5 = 24
SP_6 = 32

# Rounded deliberately: panels/cards are softer than compact controls.
RADIUS_SM = 6
RADIUS_MD = 10

# --- Typography ------------------------------------------------------------
FONT_FAMILY = '"Segoe UI Variable Text", "SF Pro Text", "Segoe UI", Arial, sans-serif'
FONT_DISPLAY = FONT_FAMILY
FONT_MONO = '"SF Mono", "Cascadia Mono", "Menlo", "Consolas", monospace'
FS_BASE = 14
FS_SMALL = 12
FS_LABEL = 11
FS_TITLE = 16
FS_H1 = 24
FS_BRAND = 32
FS_LANDING_TITLE = 116
FS_LANDING_SUBTITLE = 38
FS_LANDING_DESCRIPTION = 21

# --- Dimensions ------------------------------------------------------------
# Wide enough for primary-navigation group labels at 200% text scaling while
# retaining a generous desktop workspace at the supported 940px minimum width.
SIDEBAR_W = 240
TOPBAR_H = 56
ROW_H = 34
