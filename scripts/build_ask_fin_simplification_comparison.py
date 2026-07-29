"""Build same-viewport before/after evidence for Ask Fin simplification."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
BEFORE = (
    ROOT
    / "initiatives"
    / "configurable-rule-engine-v2"
    / "verification"
    / "screenshots"
    / "stage2"
    / "dark"
    / "11-private-ask-fin-local-status.png"
)
AFTER = (
    ROOT
    / "initiatives"
    / "configurable-rule-engine-v2"
    / "verification"
    / "screenshots"
    / "ask-fin-simplified"
    / "dark"
    / "03-unavailable-single-message.png"
)
OUTPUT = ROOT / "artifacts" / "design-qa" / "ask-fin-simplified"


def _font(size: int) -> ImageFont.ImageFont:
    for candidate in (
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _comparison(
    before: Image.Image,
    after: Image.Image,
    destination: Path,
    *,
    before_label: str,
    after_label: str,
) -> None:
    if before.size != after.size:
        raise ValueError(
            f"Viewport mismatch: before={before.size}, after={after.size}"
        )
    label_height = 54
    gutter = 16
    width, height = before.size
    canvas = Image.new(
        "RGB",
        (width * 2 + gutter, height + label_height),
        "#d6dae2",
    )
    canvas.paste(before, (0, label_height))
    canvas.paste(after, (width + gutter, label_height))
    draw = ImageDraw.Draw(canvas)
    font = _font(18)
    draw.text((20, 16), before_label, fill="#111827", font=font)
    draw.text(
        (width + gutter + 20, 16),
        after_label,
        fill="#111827",
        font=font,
    )
    canvas.save(destination, "PNG")


def main() -> int:
    before = Image.open(BEFORE).convert("RGB")
    after = Image.open(AFTER).convert("RGB")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    _comparison(
        before,
        after,
        OUTPUT / "01-unavailable-before-after-full.png",
        before_label="Before — disabled composer and duplicate outage copy",
        after_label="After — one clear message and one Retry action",
    )

    focus_width = 598
    before_focus = before.crop(
        (before.width - focus_width, 0, before.width, before.height)
    )
    after_focus = after.crop(
        (after.width - focus_width, 0, after.width, after.height)
    )
    _comparison(
        before_focus,
        after_focus,
        OUTPUT / "02-unavailable-before-after-drawer-focus.png",
        before_label="Before — Ask Fin unavailable",
        after_label="After — simplified unavailable state",
    )
    print(f"Built Ask Fin comparisons in {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
