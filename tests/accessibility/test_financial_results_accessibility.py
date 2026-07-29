"""Focused accessibility checks for deterministic financial-result charts."""
from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtTest import QSignalSpy

from finsight.delivery.desktop.components import FinancialChartCard


pytestmark = pytest.mark.ui


def _financial_chart() -> FinancialChartCard:
    return FinancialChartCard(
        "Budget status by account",
        "Planned Budget and recorded GED spend by account.",
        categories=("525005", "555035"),
        category_keys=("00-0245|525005", "00-0245|555035"),
        series={
            "BGT": (2_500_000, 1_100_000),
            "GED spend": (1_650_000, 1_250_000),
        },
        display_values={
            "BGT": ("$2,500,000.00", "$1,100,000.00"),
            "GED spend": ("$1,650,000.00", "$1,250,000.00"),
        },
        value_axis_title="Amount",
    )


def test_chart_and_exact_table_support_keyboard_drill_down(qtbot):
    card = _financial_chart()
    qtbot.addWidget(card)
    card.resize(900, 520)
    card.show()
    chart_spy = QSignalSpy(card.categoryActivated)

    assert card.accessibleName() == "Budget status by account"
    assert card.chart.focusPolicy() == Qt.FocusPolicy.StrongFocus
    assert "Left and Right Arrow" in card.chart.accessibleDescription()
    assert "Exact data" == card.tabs.tabText(1)
    assert card.table.accessibleName() == (
        "Budget status by account exact data table"
    )
    assert "press Enter" in card.table.accessibleDescription()
    assert card.table.verticalHeader().isHidden()

    card.chart.setFocus()
    qtbot.keyClick(card.chart, Qt.Key.Key_Right)
    qtbot.keyClick(card.chart, Qt.Key.Key_Enter)
    assert chart_spy.count() == 1
    assert chart_spy.at(0)[0] == "00-0245|555035"

    card.tabs.setCurrentWidget(card.table)
    card.table.setCurrentCell(0, 0)
    card.table.setFocus()
    qtbot.keyClick(card.table, Qt.Key.Key_Enter)
    assert chart_spy.count() == 2
    assert chart_spy.at(1)[0] == "00-0245|525005"


def test_exact_table_preserves_visible_status_and_values_at_large_text_scale(
    qtbot, qapp
):
    original_font = QFont(qapp.font())
    scaled_font = QFont(original_font)
    scaled_font.setPointSizeF(max(18, original_font.pointSizeF() * 2))
    qapp.setFont(scaled_font)
    card = None
    try:
        card = _financial_chart()
        qtbot.addWidget(card)
        card.resize(940, 600)
        card.show()
        qapp.processEvents()

        headers = [
            card.table.horizontalHeaderItem(column).text()
            for column in range(card.table.columnCount())
        ]
        assert headers == ["Category", "BGT", "GED spend"]
        assert card.table.item(1, 0).text() == "555035"
        assert card.table.item(1, 1).text() == "$1,100,000.00"
        assert card.table.item(1, 2).text() == "$1,250,000.00"
        assert card.table.horizontalScrollBar() is not None
        assert card.tabs.isVisibleTo(card)
        assert card.table.accessibleDescription()
    finally:
        if card is not None:
            card.close()
        qapp.setFont(original_font)
