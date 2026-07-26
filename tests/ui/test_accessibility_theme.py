# Verifies: accessibility themes + zoom (Product Owner workflow §20; F-14-05, NFR-024-027).
#   - Light / Dark / High-Contrast palettes re-theme the whole surface from one build_qss call.
#   - Zoom scales the numeric size tokens (fonts/spacing) without breaking layout.
#   - Severity keeps its shape+label glyph in every theme (no color-only meaning, NFR-025).
#   - The theme choice + zoom persist across app runs (settings-backed).
from finsight.delivery.desktop.theme import build_qss, tokens as t
from finsight.delivery.desktop.theme.palettes import make_palette
from finsight.delivery.desktop.theme.theming import ThemeManager


class _MemSettings:
    def __init__(self): self._d = {}
    def value(self, k, default=None): return self._d.get(k, default)
    def setValue(self, k, v): self._d[k] = v


def test_light_palette_matches_tokens():
    p = make_palette("light")
    assert p.BG_WORKSPACE == t.BG_WORKSPACE and p.TEXT_PRIMARY == t.TEXT_PRIMARY


def test_dark_palette_overrides_colors_not_shapes():
    p = make_palette("dark")
    assert p.BG_WORKSPACE != t.BG_WORKSPACE            # dark surface
    assert p.TEXT_PRIMARY != t.TEXT_PRIMARY
    assert p.SEVERITY == t.SEVERITY                    # severity shape+label unchanged (NFR-025)


def test_build_qss_reflects_the_palette():
    dark = build_qss(make_palette("dark"))
    light = build_qss(make_palette("light"))
    assert dark != light
    assert make_palette("dark").BG_WORKSPACE in dark   # the dark surface color is present


def test_high_contrast_is_pure_black_on_white():
    p = make_palette("high-contrast")
    assert p.TEXT_PRIMARY == "#000000" and p.BG_WORKSPACE == "#FFFFFF"


def test_zoom_scales_font_tokens():
    small = make_palette("light", 1.0)
    big = make_palette("light", 1.5)
    assert big.FS_BASE > small.FS_BASE and big.SP_3 > small.SP_3
    assert big.SEVERITY == small.SEVERITY              # glyphs never scale/change


def test_theme_choice_persists():
    s = _MemSettings()
    ThemeManager(s).__dict__  # construct
    tm = ThemeManager(s)
    tm._save = tm._save       # ensure method exists
    tm.mode = "dark"; tm.scale = 1.3; tm._save()
    reloaded = ThemeManager(s)
    assert reloaded.mode == "dark" and reloaded.scale == 1.3


def test_view_menu_switches_theme(window_factory, empty_db):
    w = window_factory(empty_db)
    tm = w.theme_manager()
    start = tm.mode
    # Toggle to dark via the same path the menu action uses.
    w._set_theme("dark")
    assert tm.mode == "dark"
    assert w._theme_actions["dark"].isChecked()
    w._set_theme(start or "system")
