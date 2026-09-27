"""Reusable front-end-only visual widgets for ENDO-TWIN desktop workstations."""
from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from desktop.workstation_runtime import Sparkline


class RingGauge(QWidget):
    """Compact radial KPI; presentation only."""

    def __init__(self, title: str, value: float | None = None, suffix: str = "%", accent: str = "#5b3cff", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.suffix = suffix
        self.accent = accent
        self.setMinimumSize(150, 150)

    def set_value(self, value: float | None):
        self.value = value
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height()) - 22
        cx = self.width() / 2
        cy = self.height() / 2 - 5
        rect = int(cx - side / 2), int(cy - side / 2), int(side), int(side)

        p.setPen(QPen(QColor("#1c2947"), 11, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(*rect, 0, 360 * 16)

        if self.value is not None:
            pct = max(0.0, min(100.0, float(self.value)))
            p.setPen(QPen(QColor(self.accent), 11, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawArc(*rect, 90 * 16, int(-pct * 360 * 16 / 100.0))

        p.setPen(QColor("#f4f8ff"))
        font = QFont(self.font())
        font.setPointSize(19)
        font.setBold(True)
        p.setFont(font)
        shown = "—" if self.value is None else f"{float(self.value):.0f}{self.suffix}"
        p.drawText(self.rect().adjusted(0, -2, 0, 10), Qt.AlignmentFlag.AlignCenter, shown)

        p.setPen(QColor("#8ea6c2"))
        font.setPointSize(8)
        font.setBold(True)
        p.setFont(font)
        p.drawText(self.width() // 2 - 70, int(cy + side / 2 / 1.25), 140, 22, Qt.AlignmentFlag.AlignCenter, self.title)


def metric_card(title: str, value: str, detail: str, values: Iterable[float] | None = None,
                accent: str = "#39c9ff", unit: str = "") -> QFrame:
    frame = QFrame()
    frame.setObjectName("card")
    outer = QVBoxLayout(frame)
    outer.setContentsMargins(13, 11, 13, 11)
    head = QHBoxLayout()
    left = QLabel(title)
    left.setObjectName("sectionTitle")
    head.addWidget(left)
    head.addStretch()
    outer.addLayout(head)

    row = QHBoxLayout()
    value_label = QLabel(value)
    value_label.setObjectName("bigValue")
    value_label.setStyleSheet(f"color:{accent};")
    row.addWidget(value_label)
    row.addStretch()
    if values is not None:
        chart = Sparkline(title, unit, line=accent)
        chart.setMinimumHeight(60)
        chart.setMaximumHeight(75)
        chart.set_values(list(values))
        row.addWidget(chart, 1)
    outer.addLayout(row)

    detail_label = QLabel(detail)
    detail_label.setObjectName("muted")
    detail_label.setWordWrap(True)
    outer.addWidget(detail_label)
    return frame


def trend_panel(title: str, values: Iterable[float] | None = None,
                unit: str = "", accent: str = "#39c9ff", height: int = 185) -> QFrame:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(12, 10, 12, 10)
    top = QHBoxLayout()
    label = QLabel(title)
    label.setObjectName("sectionTitle")
    top.addWidget(label)
    top.addStretch()
    latest = QLabel("Latest —")
    latest.setObjectName("muted")
    top.addWidget(latest)
    layout.addLayout(top)

    graph = Sparkline(title, unit, line=accent)
    graph.setMinimumHeight(height)
    graph.setMaximumHeight(height + 25)
    if values:
        data = list(values)
        graph.set_values(data)
        latest.setText(f"Latest {data[-1]:.1f}{unit}")
    layout.addWidget(graph, 1)
    frame.graph = graph
    frame.latest_label = latest
    return frame
