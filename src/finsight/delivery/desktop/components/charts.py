"""Accessible, theme-aware charts over sealed deterministic projection data."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import ceil

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)

from finsight.delivery.desktop.theme import tokens as t


class _GroupedBarChart(QWidget):
    """Small native chart renderer without financial aggregation logic."""

    categoryActivated = Signal(str)

    def __init__(
        self,
        *,
        title: str,
        description: str,
        categories: Sequence[str],
        category_keys: Sequence[str] | None,
        series: Mapping[str, Sequence[float | int]],
        value_axis_title: str,
        parent=None,
    ):
        super().__init__(parent)
        self._categories = tuple(str(item) for item in categories)
        self._category_keys = tuple(
            str(item) for item in (category_keys or categories)
        )
        self._series = {
            str(label): tuple(float(value) for value in values)
            for label, values in series.items()
        }
        self._axis_title = value_axis_title
        self._selected_index = 0 if self._categories else -1
        self.setMinimumHeight(280)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(title + " chart")
        self.setAccessibleDescription(
            description
            + " Use Left and Right Arrow to select a category and Enter to "
            "open its financial drill-down. Exact values are available on "
            "the adjacent Exact data tab."
        )

    def _activate_selected(self) -> None:
        if 0 <= self._selected_index < len(self._category_keys):
            self.categoryActivated.emit(
                self._category_keys[self._selected_index]
            )

    def keyPressEvent(self, event) -> None:
        if not self._categories:
            super().keyPressEvent(event)
            return
        if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Up):
            self._selected_index = max(0, self._selected_index - 1)
            self.update()
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Right, Qt.Key.Key_Down):
            self._selected_index = min(
                len(self._categories) - 1, self._selected_index + 1
            )
            self.update()
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self._activate_selected()
            event.accept()
            return
        super().keyPressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._categories:
            left, right = 66.0, 18.0
            width = max(1.0, self.width() - left - right)
            relative = min(max(event.position().x() - left, 0.0), width - 1)
            self._selected_index = min(
                len(self._categories) - 1,
                int(relative / (width / len(self._categories))),
            )
            self.update()
            self._activate_selected()
        super().mouseReleaseEvent(event)

    @staticmethod
    def _compact(value: float) -> str:
        absolute = abs(value)
        if absolute >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if absolute >= 1_000:
            return f"{value / 1_000:.0f}K"
        return f"{value:.0f}"

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        palette = self.palette()
        foreground = palette.color(palette.ColorRole.Text)
        muted = palette.color(palette.ColorRole.PlaceholderText)
        border = palette.color(palette.ColorRole.Mid)
        background = palette.color(palette.ColorRole.Base)
        painter.fillRect(self.rect(), background)
        if not self._categories or not self._series:
            painter.setPen(foreground)
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "No chart data available",
            )
            return

        values = [
            value for row in self._series.values() for value in row
        ] or [0.0]
        minimum = min(0.0, min(values))
        maximum = max(0.0, max(values))
        if minimum == maximum:
            maximum = minimum + 1.0

        left, top, right, bottom = 66.0, 48.0, 18.0, 54.0
        plot = QRectF(
            left,
            top,
            max(1.0, self.width() - left - right),
            max(1.0, self.height() - top - bottom),
        )
        span = maximum - minimum

        def y_for(value: float) -> float:
            return plot.bottom() - ((value - minimum) / span) * plot.height()

        painter.setPen(QPen(border, 1))
        for tick in range(5):
            fraction = tick / 4
            value = minimum + span * fraction
            y = y_for(value)
            painter.drawLine(plot.left(), y, plot.right(), y)
            painter.setPen(muted)
            painter.drawText(
                QRectF(0, y - 10, left - 8, 20),
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter,
                self._compact(value),
            )
            painter.setPen(QPen(border, 1))

        painter.setPen(foreground)
        if self._axis_title:
            painter.drawText(
                QRectF(8, 8, 180, 24),
                Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignVCenter,
                self._axis_title,
            )

        dark = palette.color(palette.ColorRole.Window).lightness() < 128
        colors = (
            (
                "#8AB4E0",
                "#5A93C9",
                "#F2B84B",
                "#5BC08A",
                "#FF7B72",
                "#C6A0E8",
            )
            if dark
            else (
                "#163B63",
                "#3E6F9E",
                "#B36B00",
                "#237A57",
                "#B42318",
                "#6D4C8E",
            )
        )
        series_items = list(self._series.items())
        axis_label_width = (
            painter.fontMetrics().horizontalAdvance(self._axis_title)
            if self._axis_title
            else 0
        )
        legend_x = max(plot.left(), 12.0 + axis_label_width + 16.0)
        for index, (label, _series_values) in enumerate(series_items):
            color = QColor(colors[index % len(colors)])
            painter.fillRect(QRectF(legend_x, 14, 12, 12), color)
            painter.setPen(foreground)
            label_width = painter.fontMetrics().horizontalAdvance(label)
            painter.drawText(
                QRectF(legend_x + 17, 9, label_width + 4, 24),
                Qt.AlignmentFlag.AlignVCenter,
                label,
            )
            legend_x += label_width + 34

        category_width = plot.width() / max(1, len(self._categories))
        widest_category = max(
            painter.fontMetrics().horizontalAdvance(category)
            for category in self._categories
        )
        category_label_step = max(
            1,
            ceil((widest_category + 8.0) / max(1.0, category_width)),
        )
        group_width = category_width * 0.78
        bar_width = max(2.0, group_width / max(1, len(series_items)))
        zero_y = y_for(0.0)
        for category_index, category in enumerate(self._categories):
            group_left = (
                plot.left()
                + category_index * category_width
                + (category_width - group_width) / 2
            )
            for series_index, (_label, series_values) in enumerate(
                series_items
            ):
                value = (
                    series_values[category_index]
                    if category_index < len(series_values)
                    else 0.0
                )
                value_y = y_for(value)
                y = min(zero_y, value_y)
                height = max(1.0, abs(zero_y - value_y))
                painter.fillRect(
                    QRectF(
                        group_left + series_index * bar_width,
                        y,
                        max(1.0, bar_width - 2.0),
                        height,
                    ),
                    QColor(colors[series_index % len(colors)]),
                )
            if category_index % category_label_step == 0:
                painter.setPen(foreground)
                painter.drawText(
                    QRectF(
                        plot.left() + category_index * category_width,
                        plot.bottom() + 7,
                        category_width * category_label_step,
                        32,
                    ),
                    Qt.AlignmentFlag.AlignLeft
                    | Qt.AlignmentFlag.AlignTop,
                    category,
                )
            if category_index == self._selected_index and self.hasFocus():
                painter.setPen(QPen(foreground, 2, Qt.PenStyle.DashLine))
                painter.drawRect(
                    QRectF(
                        plot.left() + category_index * category_width + 1,
                        plot.top() + 1,
                        max(1.0, category_width - 2),
                        max(1.0, plot.height() - 2),
                    )
                )

        painter.setPen(QPen(foreground, 1))
        painter.drawLine(plot.left(), zero_y, plot.right(), zero_y)


class _ActivatingTableWidget(QTableWidget):
    """Exact-data table whose keyboard activation matches the visual chart."""

    rowActivated = Signal(int)

    def keyPressEvent(self, event) -> None:
        if event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
            Qt.Key.Key_Space,
        ):
            row = self.currentRow()
            if row >= 0:
                self.rowActivated.emit(row)
                event.accept()
                return
        super().keyPressEvent(event)


class FinancialChartCard(QFrame):
    """A labeled chart paired with its exact table alternative.

    Callers provide values already calculated by the deterministic engine. This
    component formats no financial truth and performs no business aggregation.
    """

    categoryActivated = Signal(str)

    def __init__(
        self,
        title: str,
        description: str,
        *,
        categories: Sequence[str],
        category_keys: Sequence[str] | None = None,
        series: Mapping[str, Sequence[float | int]],
        display_values: Mapping[str, Sequence[str]] | None = None,
        value_axis_title: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.setProperty("role", "chartCard")
        self.setAccessibleName(title)
        self.setAccessibleDescription(description)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )
        self.setMaximumHeight(520)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(t.SP_4, t.SP_4, t.SP_4, t.SP_4)
        layout.setSpacing(t.SP_2)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        heading = QLabel(title)
        heading.setProperty("role", "cardTitle")
        heading.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(heading)
        subtitle = QLabel(description)
        subtitle.setWordWrap(True)
        subtitle.setProperty("role", "cardDetail")
        subtitle.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
        )
        subtitle.setMaximumHeight(64)
        layout.addWidget(subtitle)

        self.tabs = QTabWidget()
        self.tabs.setAccessibleName(title + " chart and exact data")
        # The exact-data table may contain many rows, but it must scroll inside
        # the card rather than inflating every QTabWidget page and pushing chart
        # labels below the desktop viewport.
        self.tabs.setMinimumHeight(320)
        self.tabs.setMaximumHeight(380)
        self.tabs.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.tabs.setFixedHeight(360)
        self.chart = _GroupedBarChart(
            title=title,
            description=description,
            categories=categories,
            category_keys=category_keys,
            series=series,
            value_axis_title=value_axis_title,
        )
        self.chart.categoryActivated.connect(self.categoryActivated)
        self.chart_view = self.chart
        self.tabs.addTab(self.chart, "Chart")

        exact = display_values or {
            label: [str(value) for value in values]
            for label, values in series.items()
        }
        self.table = _ActivatingTableWidget(
            len(categories), len(series) + 1
        )
        self.table.setAccessibleName(title + " exact data table")
        self.table.verticalHeader().setVisible(False)
        self.table.setHorizontalHeaderLabels(["Category", *series.keys()])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, category in enumerate(categories):
            self.table.setItem(row, 0, QTableWidgetItem(str(category)))
            for column, label in enumerate(series, 1):
                values = exact.get(label, ())
                value = values[row] if row < len(values) else ""
                self.table.setItem(row, column, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()
        keys = tuple(str(item) for item in (category_keys or categories))
        self.table.cellActivated.connect(
            lambda row, _column: self.categoryActivated.emit(keys[row])
            if 0 <= row < len(keys)
            else None
        )
        self.table.cellDoubleClicked.connect(
            lambda row, _column: self.categoryActivated.emit(keys[row])
            if 0 <= row < len(keys)
            else None
        )
        self.table.rowActivated.connect(
            lambda row: self.categoryActivated.emit(keys[row])
            if 0 <= row < len(keys)
            else None
        )
        self.table.setAccessibleDescription(
            "Select a category and press Enter to open its financial drill-down."
        )
        self.tabs.addTab(self.table, "Exact data")
        layout.addWidget(self.tabs)


__all__ = ["FinancialChartCard"]
