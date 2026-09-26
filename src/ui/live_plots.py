"""PyQtGraph plot wrappers - V8.4 Smooth Live Dashboard.

Supports both legacy TimeSeriesPlot and new SmoothLivePlot for 20Hz rendering.
"""
from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from collections import deque
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from src.ui.theme import TEXT_MUTED, style_plot
from src.ui.theme_v83_premium import DARK as PREMIUM_DARK


class TimeSeriesPlot(QWidget):
    """Legacy trend plot - preserved for Trends tab."""
    def __init__(self, title: str, y_label: str = "", color: str = "#3aa7f0", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(title)
        self.label.setStyleSheet(f"font-weight: 600; color: {TEXT_MUTED}; font-size: 10.5pt;")
        self.plot = pg.PlotWidget()
        style_plot(self.plot, y_label=y_label, x_label="seconds ago")
        self.curve = self.plot.plot(pen=pg.mkPen(color, width=2))
        self.curve.setShadowPen(pg.mkPen(color, width=5, alpha=0.25))
        layout.addWidget(self.label)
        layout.addWidget(self.plot)

    def set_data(self, x, y):
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        mask = np.isfinite(x) & np.isfinite(y)
        if mask.sum() == 0:
            self.curve.setData([], [])
        else:
            self.curve.setData(x[mask], y[mask])


class SmoothLivePlot(QWidget):
    """V8.4 Smooth 20Hz ring-buffer plot with glow and downsampling."""
    def __init__(self, title: str, y_label: str = "", color: str = "#3aa7f0", history_s: float = 10.0, fs_hz: float = 50.0, parent=None):
        super().__init__(parent)
        self.history_s = history_s
        self.maxlen = int(history_s * fs_hz * 1.2)
        self.times: deque = deque(maxlen=self.maxlen)
        self.values: deque = deque(maxlen=self.maxlen)
        self.title_str = title
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.label = QLabel(title)
        self.label.setStyleSheet(f"font-weight: 600; color: {TEXT_MUTED}; font-size: 10pt;")
        self.plot = pg.PlotWidget()
        self.plot.setBackground(PREMIUM_DARK["plot_bg"])
        self.plot.showGrid(x=True, y=True, alpha=0.12)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.getAxis("left").setPen(pg.mkPen(PREMIUM_DARK["border_light"]))
        self.plot.getAxis("left").setTextPen(pg.mkPen(PREMIUM_DARK["text_muted"]))
        self.plot.getAxis("bottom").setPen(pg.mkPen(PREMIUM_DARK["border_light"]))
        self.plot.getAxis("bottom").setTextPen(pg.mkPen(PREMIUM_DARK["text_muted"]))
        if y_label:
            self.plot.getAxis("left").setLabel(y_label)
        self.plot.getAxis("bottom").setLabel("s ago")
        self.plot.getViewBox().setDefaultPadding(0.02)
        self.curve = self.plot.plot(pen=pg.mkPen(color, width=2.2))
        self.glow = self.plot.plot(pen=pg.mkPen(color, width=6, alpha=0.18))
        layout.addWidget(self.label)
        layout.addWidget(self.plot)

    def push(self, timestamp_s: float, value: float):
        if not np.isfinite(value):
            return
        self.times.append(timestamp_s)
        self.values.append(value)

    def refresh(self):
        if len(self.times) < 2:
            return
        t = np.array(self.times, dtype=float)
        v = np.array(self.values, dtype=float)
        now = t[-1]
        mask = t >= (now - self.history_s)
        t = t[mask]
        v = v[mask]
        if t.size < 2:
            return
        x = t - now
        if x.size > 800:
            step = x.size // 800
            x = x[::step]
            v = v[::step]
        self.curve.setData(x, v)
        self.glow.setData(x, v)

    def set_title(self, title: str):
        self.title_str = title
        self.label.setText(title)
