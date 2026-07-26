# Implements:
#   Report Financial Map (DEC-037): a VISUALIZATION over EXISTING deterministic results — it performs
#   no calculation and derives no new conclusion. It draws a relationship / node-link graph connecting
#   the analysis outputs FinSight already computed (accounts ↔ their findings). Severity is shown as a
#   shape glyph + label, never color alone (NFR-025). The report's Account-detail section is the
#   accessible tabular equivalent of this view.
#   Feature: F-07-01 / F-03-01 (presentation-extended).
from __future__ import annotations
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QFont
from PySide6.QtWidgets import QWidget, QSizePolicy
from finsight.delivery.desktop.components.severity import severity_text, severity_color
from finsight.delivery.desktop.theme import tokens as t

_ACCT_W = 140
_NODE_H = 26
_ROW_GAP = 10
_BAND_GAP = 18
_COL_GAP = 90
_FIND_W = 300
_MARGIN = 16


class FinancialMap(QWidget):
    """Node-link map: account nodes on the left, each connected to its finding nodes on the right.
    Deterministic layout (accounts sorted; findings pre-sorted by the read model)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._accounts = []
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_graph(self, graph) -> None:
        self._accounts = (graph or {}).get("accounts", []) if graph else []
        self.setMinimumHeight(self._computed_height())
        self.updateGeometry()
        self.update()

    # --- seams (stable for tests) ---
    def node_count(self) -> int:
        return len(self._accounts) + sum(len(a["findings"]) for a in self._accounts)

    def edge_count(self) -> int:
        return sum(len(a["findings"]) for a in self._accounts)

    def is_empty(self) -> bool:
        return not self._accounts

    def _band_height(self, account) -> int:
        rows = max(1, len(account["findings"]))
        return rows * _NODE_H + (rows - 1) * _ROW_GAP

    def _computed_height(self) -> int:
        if not self._accounts:
            return 60
        return _MARGIN * 2 + sum(self._band_height(a) for a in self._accounts) \
            + _BAND_GAP * (len(self._accounts) - 1)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.fillRect(self.rect(), QColor(t.BG_SUBTLE))
        if not self._accounts:
            p.setPen(QColor(t.TEXT_MUTED))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "No findings to map — nothing connected this period.")
            p.end()
            return

        acct_x = _MARGIN
        find_x = _MARGIN + _ACCT_W + _COL_GAP
        base_font = QFont(); base_font.setPointSize(9)
        p.setFont(base_font)
        y = _MARGIN
        for account in self._accounts:
            band_h = self._band_height(account)
            acct_rect = QRectF(acct_x, y + (band_h - _NODE_H) / 2, _ACCT_W, _NODE_H)
            self._draw_node(p, acct_rect, "Account " + account["account"], accent=True)
            fy = y
            for finding in account["findings"]:
                f_rect = QRectF(find_x, fy, _FIND_W, _NODE_H)
                # Connector from the account node to this finding node.
                p.setPen(QPen(QColor(t.BORDER_STRONG), 1))
                p.drawLine(int(acct_rect.right()), int(acct_rect.center().y()),
                           int(f_rect.left()), int(f_rect.center().y()))
                label = "%s  ·  %s" % (severity_text(finding["severity"]), finding["finding_type"])
                self._draw_node(p, f_rect, label, dot=severity_color(finding["severity"]))
                fy += _NODE_H + _ROW_GAP
            y += band_h + _BAND_GAP
        p.end()

    def _draw_node(self, p, rect, text, accent=False, dot=None):
        p.setPen(QPen(QColor(t.ACCENT if accent else t.BORDER_STRONG), 1))
        p.setBrush(QBrush(QColor(t.ACCENT_SUBTLE_BG if accent else t.WHITE)))
        p.drawRoundedRect(rect, 6, 6)
        if dot:  # secondary colour reinforcement only — the label already carries the glyph + words
            p.setBrush(QBrush(QColor(dot))); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(rect.left() + 8, rect.center().y() - 3, 6, 6))
        p.setPen(QColor(t.TEXT_PRIMARY))
        text_rect = rect.adjusted(18 if dot else 10, 0, -8, 0)
        p.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
