"""Build same-viewport walking-skeleton versus MVP comparison images."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "artifacts" / "ui-verification"
IMPLEMENTATION = (
    ROOT
    / "artifacts"
    / "design-qa"
    / "final-1180x860"
    / "light"
)
OUTPUT = ROOT / "artifacts" / "design-qa"

PAIRS = (
    (
        "01-create-review-comparison.png",
        "01b-create-review-period.png",
        "02-create-review.png",
    ),
    (
        "02-upload-comparison.png",
        "01c-data-upload-three-sources.png",
        "04-upload-ready.png",
    ),
    (
        "03-verify-data-comparison.png",
        "01f-extraction-review.png",
        "06-verify-budget.png",
    ),
    (
        "04-results-overview-comparison.png",
        "02-dashboard-home.png",
        "21-executive-overview.png",
    ),
    (
        "05-findings-comparison.png",
        "06-findings.png",
        "27-findings-duplicate-evidence.png",
    ),
)


def _font(size: int) -> ImageFont.ImageFont:
    candidates = (
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _build(output_name: str, reference_name: str, implementation_name: str) -> None:
    reference = Image.open(REFERENCE / reference_name).convert("RGB")
    implementation = Image.open(IMPLEMENTATION / implementation_name).convert("RGB")
    if reference.size != implementation.size:
        raise ValueError(
            f"Viewport mismatch: {reference_name}={reference.size}, "
            f"{implementation_name}={implementation.size}"
        )
    label_height = 54
    gutter = 16
    width, height = reference.size
    canvas = Image.new(
        "RGB",
        (width * 2 + gutter, height + label_height),
        "#e5e7eb",
    )
    canvas.paste(reference, (0, label_height))
    canvas.paste(implementation, (width + gutter, label_height))
    draw = ImageDraw.Draw(canvas)
    font = _font(18)
    draw.text((20, 16), "Walking-skeleton reference", fill="#111827", font=font)
    draw.text(
        (width + gutter + 20, 16),
        "Implemented FinSight MVP",
        fill="#111827",
        font=font,
    )
    canvas.save(OUTPUT / output_name, "PNG")


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for pair in PAIRS:
        _build(*pair)
    print(f"Built {len(PAIRS)} visual comparisons in {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
