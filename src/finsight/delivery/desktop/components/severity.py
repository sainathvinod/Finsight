from __future__ import annotations
from finsight.delivery.desktop.theme import tokens as t

# Severity is presented with a distinct SHAPE GLYPH + the text LABEL, so it is legible without
# color (NFR-025). Color, where used, is only a secondary reinforcement channel.


def severity_text(label: str) -> str:
    """Return 'glyph label' — e.g. '▲ High'. Never color alone; the glyph and words carry meaning."""
    spec = t.SEVERITY.get(label)
    glyph = spec["glyph"] if spec else "•"
    return f"{glyph} {label}"


def severity_color(label: str) -> str:
    spec = t.SEVERITY.get(label)
    return spec["color"] if spec else t.TEXT_SECONDARY
