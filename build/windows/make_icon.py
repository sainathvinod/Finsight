"""Generate build/windows/finsight.ico from the application's own brand tokens.

Run once (or whenever the brand palette changes):
    PYTHONPATH=src python build/windows/make_icon.py

Kept as a build asset generator rather than a checked-in binary so the icon cannot drift from
theme/tokens.py. Uses Qt, which the desktop build already depends on — no extra dependency.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF, Qt  # noqa: E402
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPainterPath  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from finsight.delivery.desktop.theme import tokens as t  # noqa: E402

# Windows shows the icon at these sizes; an .ico carries them all so none is machine-scaled.
SIZES = (16, 24, 32, 48, 64, 128, 256)


def _render(size: int) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    # Rounded-square field in the navigation navy — the colour of the application's own sidebar.
    field = QPainterPath()
    inset = size * 0.04
    radius = size * 0.22
    field.addRoundedRect(
        QRectF(inset, inset, size - 2 * inset, size - 2 * inset), radius, radius
    )
    painter.fillPath(field, QBrush(QColor(t.LIGHT.navigation)))

    # An ascending three-bar mark: the review moving from position to insight. Drawn from the
    # accent through to white so it stays legible once Windows scales it down to 16px.
    bars = (
        (0.24, 0.60, QColor(t.LIGHT.accent).lighter(135)),
        (0.44, 0.44, QColor(t.LIGHT.accent).lighter(165)),
        (0.64, 0.28, QColor("#FFFFFF")),
    )
    bar_width = size * 0.14
    baseline = size * 0.76
    for left_ratio, top_ratio, colour in bars:
        left = size * left_ratio
        top = size * top_ratio
        bar = QPainterPath()
        bar.addRoundedRect(
            QRectF(left, top, bar_width, baseline - top),
            bar_width * 0.32,
            bar_width * 0.32,
        )
        painter.fillPath(bar, QBrush(colour))

    painter.end()
    return image


def _ico_bytes(images: list[QImage]) -> bytes:
    """Assemble a multi-resolution .ico. Each entry is stored as PNG (supported since Vista)."""

    encoded = []
    for image in images:
        # The QByteArray must outlive the QBuffer that writes into it; binding it to a local
        # name keeps Python from collecting it mid-write (which segfaults the Qt binding).
        storage = QByteArray()
        buffer = QBuffer(storage)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        buffer.close()
        encoded.append(bytes(storage))

    count = len(encoded)
    header = b"\x00\x00\x01\x00" + count.to_bytes(2, "little")
    offset = 6 + 16 * count
    directory = b""
    for image, payload in zip(images, encoded):
        width = 0 if image.width() >= 256 else image.width()
        height = 0 if image.height() >= 256 else image.height()
        directory += bytes((width, height, 0, 0))
        directory += (1).to_bytes(2, "little")          # colour planes
        directory += (32).to_bytes(2, "little")         # bits per pixel
        directory += len(payload).to_bytes(4, "little")
        directory += offset.to_bytes(4, "little")
        offset += len(payload)
    return header + directory + b"".join(encoded)


def main() -> int:
    QApplication(sys.argv[:1])
    images = [_render(size) for size in SIZES]
    target = os.path.join(os.path.dirname(os.path.abspath(__file__)), "finsight.ico")
    with open(target, "wb") as handle:
        handle.write(_ico_bytes(images))
    print(f"wrote {target} ({os.path.getsize(target)} bytes, sizes: {', '.join(map(str, SIZES))})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
