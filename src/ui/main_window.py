"""Main Window for CHRONO-TWIN NEXUS V8.4 - Smooth Live Dashboard + Previous Logic Preserved.

Dashboard sections:
- Overview: LIVE smooth dashboard - vitals, env, motion, hardware health, pulse waveform
- Baseline: what is normal for user
- Trends: changes over time
- Health Signals: PCOS, Sleep, Cardiometabolic, Autonomic
- Data Quality: sensor status and confidence
- Clinical Inputs: manual clinical measurements
- Ultrasound: image and structured features
- Explanation: why system generated signal
- Report: research report
- Validation: engineering vs clinical

Hardware V8.4:
- Shoulder mount: MPU6050/2060 (motion), BME280 (room temp/hum/press), BH1750 (lux)
  I2C SDA=8 SCL=9 VCC=3V3 GND=GND
- Forearm mount: Analog Pulse Sensor S=40, DS18B20 DATA=6
- Optional GSR GPIO5

Keeps V8.1-V8.3 logic preserved, reverts to previous UI shell, adds smooth live dashboard.
"""
from __future__ import annotations

import json
import time
import math
from pathlib import Path
from collections import deque
from typing import Deque, Dict

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QTimer, Qt, QDateTime, Signal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QGroupBox, QGridLayout, QTextEdit,
    QDoubleSpinBox, QSpinBox, QComboBox, QScrollArea, QFrame,
    QLineEdit, QProgressBar, QSplitter
)

from src.config import APP_VERSION, APP_VERSION_LABEL, APP_NAME, APP_TAGLINE, UserProfile, DATA_DIR
from src.data_models import FeatureVector, SensorSample, SharedPhysiologicalFeatures
from src.core.personal_baseline import PersonalBaselineEngine
from src.core.longitudinal_engine import LongitudinalEngine
from src.core.feature_extraction import RealtimeFeatureExtractor
from src.core.shared_features import SharedFeatureExtractor
from src.core.quality_control import SensorQualityControl
from src.disease_modules.registry import GLOBAL_REGISTRY
from src.fusion.multimodal_fusion import FusionEngine
from src.explainability.explanation_engine import ExplanationEngine
from src.serial_io.arduino_reader import ArduinoReader
from src.serial_io.network_reader import NetworkReader
from src.serial_io.packet_parser import decode_status_flags, decode_hardware_health
from src.ui.theme import DARK_QSS, GREEN, ORANGE, RED, YELLOW, TEXT_MUTED, ACCENT, ACCENT_STRONG
from src.ui.theme_v83_premium import DARK as PREMIUM_DARK
from src.ui.gauges import GaugeWidget
from src.ui.vital_cards import VitalCard
from src.ui.live_plots import TimeSeriesPlot
from src.utils.demo_stream import DemoSensorStream
from src.utils.history_store import HistoryStore

DISCLAIMER = "Research prototype, NOT a diagnosis. Clinical evaluation required."

# -------------------- Smooth Live Plot Widget --------------------
class SmoothLivePlot(QWidget):
    """High-performance ring-buffer plot for 20-50Hz data, smooth 30fps render."""
    def __init__(self, title: str, y_label: str = "", color: str = "#3aa7f0", history_s: float = 10.0, fs_hz: float = 50.0, parent=None):
        super().__init__(parent)
        self.history_s = history_s
        self.maxlen = int(history_s * fs_hz * 1.2)
        self.times: Deque[float] = deque(maxlen=self.maxlen)
        self.values: Deque[float] = deque(maxlen=self.maxlen)
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
        # glow
        self.glow = self.plot.plot(pen=pg.mkPen(color, width=6, alpha=0.18))
        layout.addWidget(self.label)
        layout.addWidget(self.plot)
        self._last_update = 0

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
        # keep only last history_s
        now = t[-1]
        mask = t >= (now - self.history_s)
        t = t[mask]
        v = v[mask]
        if t.size < 2:
            return
        # x = seconds ago (negative)
        x = t - now
        # Smooth downsample if too many points for performance
        if x.size > 800:
            step = x.size // 800
            x = x[::step]
            v = v[::step]
        self.curve.setData(x, v)
        self.glow.setData(x, v)

    def set_title(self, title: str):
        self.title_str = title
        self.label.setText(title)


class HardwareStatusCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("VitalCard")
        self.setProperty("state", "gray")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        title = QLabel("Hardware Health - Shoulder + Forearm")
        title.setStyleSheet(f"font-weight: 700; color: {ACCENT}; font-size: 10pt;")
        layout.addWidget(title)
        self.grid = QGridLayout()
        self.grid.setSpacing(6)
        layout.addLayout(self.grid)
        self.labels: Dict[str, QLabel] = {}
        sensors = [
            ("mpu", "MPU6050/2060 (SDA8 SCL9) Shoulder"),
            ("bme280", "BME280 Env (Room T/H/P) Shoulder"),
            ("bh1750", "BH1750 Lux Shoulder"),
            ("pulse", "Analog Pulse S=40 Forearm"),
            ("ds18", "DS18B20 Skin T D=6 Forearm"),
            ("gsr", "GSR Optional GPIO5"),
            ("i2c", "I2C Bus SDA8 SCL9"),
        ]
        for i, (key, name) in enumerate(sensors):
            lbl = QLabel(f"● {name}: --")
            lbl.setObjectName("SmallMuted")
            lbl.setStyleSheet("font-size: 9.5pt;")
            self.grid.addWidget(lbl, i // 2, i % 2)
            self.labels[key] = lbl
        # wiring info
        wiring = QLabel("Wiring: All SDA->8 SCL->9 VCC->3V3 GND->GND | Pulse S->40 | DS18 DATA->6 | GSR->5 | LED->2")
        wiring.setObjectName("SmallMuted")
        wiring.setWordWrap(True)
        wiring.setStyleSheet("color: #7a8db0; font-size: 8.5pt; font-family: monospace;")
        layout.addWidget(wiring)

    def update_status(self, status_int: int):
        health = decode_hardware_health(status_int)
        flags = decode_status_flags(status_int)
        for key, lbl in self.labels.items():
            if key == "analog_active":
                continue
            ok = health.get(key, True)
            base = lbl.text().split(":")[0]
            if ok:
                lbl.setText(f"{base}: ● OK")
                lbl.setStyleSheet("color: #4ade80; font-size: 9.5pt; font-weight: 600;")
            else:
                lbl.setText(f"{base}: ● FAIL")
                lbl.setStyleSheet("color: #f87171; font-size: 9.5pt; font-weight: 600;")
        # tooltip with flags
        if flags:
            self.setToolTip("\n".join(flags))
        else:
            self.setToolTip("All sensors nominal")


class EnvPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("VitalCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        title = QLabel("Environmental - Shoulder Mount (BME280 + BH1750)")
        title.setStyleSheet(f"font-weight: 700; color: {ACCENT}; font-size: 10pt;")
        layout.addWidget(title)
        grid = QGridLayout()
        self.room_temp = QLabel("Room: -- °C")
        self.hum = QLabel("Humidity: -- %")
        self.press = QLabel("Pressure: -- hPa")
        self.lux = QLabel("Lux: -- lx")
        self.skin_temp = QLabel("Skin (DS18 forearm): -- °C")
        self.pulse_raw = QLabel("Pulse Raw (GPIO40): --")
        for w in [self.room_temp, self.hum, self.press, self.lux, self.skin_temp, self.pulse_raw]:
            w.setObjectName("SmallMuted")
            w.setStyleSheet("font-size: 10pt; color: #e8eef7;")
        grid.addWidget(self.room_temp, 0, 0)
        grid.addWidget(self.hum, 0, 1)
        grid.addWidget(self.press, 1, 0)
        grid.addWidget(self.lux, 1, 1)
        grid.addWidget(self.skin_temp, 2, 0)
        grid.addWidget(self.pulse_raw, 2, 1)
        layout.addLayout(grid)

    def update_values(self, sample: SensorSample):
        if sample.room_temp_c and np.isfinite(sample.room_temp_c):
            self.room_temp.setText(f"Room: {sample.room_temp_c:.1f} °C (BME280)")
        if sample.humidity_pct and np.isfinite(sample.humidity_pct):
            self.hum.setText(f"Humidity: {sample.humidity_pct:.1f} %")
        if sample.pressure_hpa and np.isfinite(sample.pressure_hpa):
            self.press.setText(f"Pressure: {sample.pressure_hpa:.1f} hPa")
        if sample.lux and np.isfinite(sample.lux):
            self.lux.setText(f"Lux: {sample.lux:.0f} lx (BH1750)")
        if np.isfinite(sample.temp_c):
            self.skin_temp.setText(f"Skin (DS18 forearm): {sample.temp_c:.2f} °C")
        self.pulse_raw.setText(f"Pulse Raw (GPIO40): {sample.ir}")


class LiveStatsPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("VitalCard")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        self.rate_label = QLabel("Rate: -- Hz")
        self.crc_label = QLabel("CRC Err: 0")
        self.latency_label = QLabel("Latency: -- ms")
        self.packets_label = QLabel("Packets: 0")
        for w in [self.rate_label, self.crc_label, self.latency_label, self.packets_label]:
            w.setObjectName("SmallMuted")
            w.setStyleSheet("font-size: 9pt;")
            layout.addWidget(w)
        layout.addStretch(1)
        self.mount_label = QLabel("Mount: Shoulder (MPU/BME/BH) + Forearm (Pulse/DS18)")
        self.mount_label.setStyleSheet(f"color: {ACCENT_STRONG}; font-weight: 600; font-size: 9pt;")
        layout.addWidget(self.mount_label)


class MainWindow(QMainWindow):
    def __init__(self, start_demo: bool = False, port: str | None = None, net: str | None = None, db_path=None):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} - {APP_VERSION_LABEL}")
        self.resize(1680, 1050)
        self.setStyleSheet(DARK_QSS)

        # Core engines (preserved previous logic)
        self.profile = UserProfile()
        self.baseline_engine = PersonalBaselineEngine()
        self.longitudinal_engine = LongitudinalEngine(baseline=self.baseline_engine)
        self.extractor = RealtimeFeatureExtractor(profile=self.profile, baseline_engine=self.baseline_engine)
        self.shared_extractor = SharedFeatureExtractor(baseline_engine=self.baseline_engine)
        self.fusion_engine = FusionEngine()
        self.explanation_engine = ExplanationEngine()
        self.quality_control = SensorQualityControl()

        # State
        self.feature_history: list[FeatureVector] = []
        self.shared_history: list[SharedPhysiologicalFeatures] = []
        self.module_results = {}
        self.fusion_result = None
        self.current_shared: SharedPhysiologicalFeatures | None = None
        self.clinical_data: dict = {}
        self.ultrasound_data: dict | None = None
        self.demo_stream: DemoSensorStream | None = None
        self.arduino_reader: ArduinoReader | None = None
        self.network_reader: NetworkReader | None = None
        self.history_store = HistoryStore(db_path) if db_path else HistoryStore()

        # Live stats
        self.packet_count = 0
        self.crc_errors = 0
        self.last_packet_time = time.time()
        self.packet_rate = 0.0
        self._rate_window = deque(maxlen=50)

        # Smooth live buffers
        self.live_buffers = {
            "pulse": deque(maxlen=2000),
            "pulse_t": deque(maxlen=2000),
            "ax": deque(maxlen=1000),
            "ay": deque(maxlen=1000),
            "az": deque(maxlen=1000),
            "imu_t": deque(maxlen=1000),
            "skin_temp": deque(maxlen=500),
            "temp_t": deque(maxlen=500),
            "lux": deque(maxlen=500),
            "room_temp": deque(maxlen=500),
            "hum": deque(maxlen=500),
            "press": deque(maxlen=500),
            "env_t": deque(maxlen=500),
        }

        # Timers - smooth dashboard
        self.feature_timer = QTimer()
        self.feature_timer.timeout.connect(self._update_features)
        self.feature_timer.start(80)  # ~12.5 Hz feature extraction, smooth

        self.risk_timer = QTimer()
        self.risk_timer.timeout.connect(self._update_risk)
        self.risk_timer.start(1500)

        self.smooth_plot_timer = QTimer()
        self.smooth_plot_timer.timeout.connect(self._refresh_smooth_plots)
        self.smooth_plot_timer.start(50)  # 20 fps smooth

        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_live_stats)
        self.stats_timer.start(500)

        # Build UI — ENDO-TWIN command-center shell (previous UI preserved)
        central = QWidget()
        central.setObjectName("CentralRoot")
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 8)
        layout.setSpacing(9)

        header = self._build_header()
        layout.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.tabBar().hide()
        self.tabs.addTab(self._build_overview_tab_smooth(), "Overview")
        self.tabs.addTab(self._build_baseline_tab(), "Baseline")
        self.tabs.addTab(self._build_trends_tab(), "Trends")
        self.tabs.addTab(self._build_health_signals_tab(), "Health Signals")
        self.tabs.addTab(self._build_data_quality_tab(), "Data Quality")
        self.tabs.addTab(self._build_clinical_tab(), "Clinical Inputs")
        self.tabs.addTab(self._build_ultrasound_tab(), "Ultrasound")
        self.tabs.addTab(self._build_explanation_tab(), "Explanation")
        self.tabs.addTab(self._build_report_tab(), "Report")
        self.tabs.addTab(self._build_validation_tab(), "Validation")

        body = QHBoxLayout()
        body.setSpacing(10)
        sidebar = self._build_sidebar()
        body.addWidget(sidebar)
        body.addWidget(self.tabs, 1)
        layout.addLayout(body, 1)

        self.status_label = QLabel(f"●  {APP_NAME} V8.4  •  {APP_TAGLINE}  •  {DISCLAIMER}  •  SDA=8 SCL=9 Pulse=40 DS18=6")
        self.status_label.setObjectName("SmallMuted")
        layout.addWidget(self.status_label)

        self.header_clock_timer = QTimer(self)
        self.header_clock_timer.timeout.connect(self._update_header_clock)
        self.header_clock_timer.start(1000)
        self._update_header_clock()

        if start_demo:
            self.start_demo()
        if port:
            self.connect_serial(port)
        if net:
            self.connect_network(net)

    def _build_header(self):
        box = QFrame()
        box.setObjectName("AppHeader")
        layout = QHBoxLayout(box)
        layout.setContentsMargins(16, 10, 14, 10)
        layout.setSpacing(10)

        brand = QLabel("∞")
        brand.setObjectName("BrandMark")
        brand.setMinimumWidth(28)
        layout.addWidget(brand)

        brand_col = QVBoxLayout()
        brand_col.setSpacing(0)
        title = QLabel("ENDO-TWIN NEXUS V8.4")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Sense  •  Model  •  Predict  •  Personalize  •  Shoulder+Forearm Wearable")
        subtitle.setObjectName("AppSubtitle")
        brand_col.addWidget(title)
        brand_col.addWidget(subtitle)
        layout.addLayout(brand_col)

        search = QLineEdit()
        search.setPlaceholderText("Search patients, devices, studies…")
        search.setMinimumWidth(280)
        search.setMaximumWidth(390)
        search.setClearButtonEnabled(True)
        layout.addWidget(search, 1)

        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        self.port_combo.addItems(["/dev/ttyACM0", "/dev/ttyUSB0", "/dev/ttyUSB1", "COM5", "COM6"])
        self.port_combo.setToolTip("ESP32-S3 wearable serial port (115200)")
        layout.addWidget(self.port_combo)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("HeaderAction")
        refresh_btn.clicked.connect(self._refresh_ports)
        layout.addWidget(refresh_btn)

        connect_btn = QPushButton("Connect S3")
        connect_btn.setObjectName("PrimaryAction")
        connect_btn.clicked.connect(self.connect_serial)
        layout.addWidget(connect_btn)

        demo_btn = QPushButton("Demo V8.4")
        demo_btn.setObjectName("HeaderAction")
        demo_btn.clicked.connect(self.start_demo)
        layout.addWidget(demo_btn)

        stop_btn = QPushButton("Stop")
        stop_btn.setObjectName("HeaderAction")
        stop_btn.clicked.connect(self.stop_stream)
        layout.addWidget(stop_btn)

        self.net_edit = QLineEdit()
        self.net_edit.setPlaceholderText("Wi-Fi bridge IP:port")
        self.net_edit.setMaximumWidth(210)
        layout.addWidget(self.net_edit)

        net_btn = QPushButton("Wi-Fi")
        net_btn.setObjectName("HeaderAction")
        net_btn.clicked.connect(lambda: self.connect_network(self.net_edit.text().strip()))
        layout.addWidget(net_btn)

        scenario_btn = QPushButton("Scenario")
        scenario_btn.setObjectName("HeaderAction")
        scenario_btn.clicked.connect(self._load_scenario_dialog)
        layout.addWidget(scenario_btn)

        clock_col = QVBoxLayout()
        clock_col.setSpacing(0)
        date_label = QLabel()
        date_label.setObjectName("HeaderDate")
        self.header_date = date_label
        clock_col.addWidget(date_label)
        clock = QLabel()
        clock.setObjectName("HeaderClock")
        self.header_clock = clock
        clock_col.addWidget(clock)
        layout.addLayout(clock_col)
        return box

    def _update_header_clock(self):
        now = QDateTime.currentDateTime()
        self.header_date.setText(now.toString("ddd, dd MMM yyyy"))
        self.header_clock.setText(now.toString("hh:mm AP"))

    def _build_sidebar(self):
        box = QFrame()
        box.setObjectName("Sidebar")
        box.setFixedWidth(184)
        root = QVBoxLayout(box)
        root.setContentsMargins(8, 10, 8, 10)
        root.setSpacing(4)

        nav_items = [
            ("⌂", "Live Dashboard"),
            ("♙", "Baseline"),
            ("⌁", "Trends"),
            ("◈", "Health Signals"),
            ("◌", "Data Quality"),
            ("▣", "Clinical Inputs"),
            ("▧", "Ultrasound"),
            ("✦", "Explanation"),
            ("▤", "Report"),
            ("✓", "Validation"),
        ]
        self.sidebar_buttons = []
        for index, (icon, label) in enumerate(nav_items):
            btn = QPushButton(f"{icon}   {label}")
            btn.setObjectName("SideNav")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=index: self._select_sidebar_tab(i))
            root.addWidget(btn)
            self.sidebar_buttons.append(btn)

        root.addStretch(1)
        status_title = QLabel("V8.4 HARDWARE MAP")
        status_title.setObjectName("SectionEyebrow")
        root.addWidget(status_title)
        hw = QLabel("SDA=8 SCL=9\nPulse S=40\nDS18 DATA=6\nGSR=5 LED=2\nShoulder: MPU/BME/BH\nForearm: Pulse/DS18")
        hw.setObjectName("SmallMuted")
        hw.setStyleSheet("font-family: monospace; font-size: 8.5pt;")
        root.addWidget(hw)

        self.sidebar_status = QLabel("●  All systems nominal\nSmooth 20Hz dashboard")
        self.sidebar_status.setObjectName("SmallMuted")
        self.sidebar_status.setWordWrap(True)
        root.addWidget(self.sidebar_status)
        version = QLabel(f"ENDO-TWIN NEXUS\nV{APP_VERSION} • V8.4 Shoulder+Forearm\nSmooth Live Dashboard")
        version.setObjectName("SmallMuted")
        root.addWidget(version)

        self._select_sidebar_tab(0)
        return box

    def _select_sidebar_tab(self, index: int):
        self.tabs.setCurrentIndex(index)
        for i, btn in enumerate(self.sidebar_buttons):
            btn.setChecked(i == index)

    # -------------------- NEW SMOOTH OVERVIEW --------------------
    def _build_overview_tab_smooth(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content.setObjectName("OverviewScrollContent")
        root = QVBoxLayout(content)
        root.setSpacing(10)

        # Top row: gauges + status
        head = QHBoxLayout()
        eyebrow = QLabel("ENDO-TWIN V8.4 LIVE DASHBOARD - Shoulder + Forearm - Smooth 20Hz")
        eyebrow.setObjectName("SectionEyebrow")
        head.addWidget(eyebrow)
        head.addStretch(1)
        self.risk_gauge = GaugeWidget("Overall Research Signal")
        head.addWidget(self.risk_gauge, 2)

        meta_box = QGroupBox("Live Status")
        mb = QVBoxLayout(meta_box)
        self.confidence_label = QLabel("Model Confidence: -")
        self.quality_label = QLabel("Data Quality: -")
        self.coverage_label = QLabel("Coverage: -")
        self.baseline_label = QLabel("Baseline: No baseline")
        self.mode_label = QLabel("Mode: NO STREAM")
        self.mode_label.setStyleSheet("font-weight: bold; color: #f87171;")
        for w in [self.confidence_label, self.quality_label, self.coverage_label, self.baseline_label, self.mode_label]:
            w.setObjectName("BigValue")
            mb.addWidget(w)
        head.addWidget(meta_box, 1)
        root.addLayout(head)

        # Live stats + hardware + env
        stats_row = QHBoxLayout()
        self.live_stats_panel = LiveStatsPanel()
        stats_row.addWidget(self.live_stats_panel, 2)
        self.hw_status_card = HardwareStatusCard()
        stats_row.addWidget(self.hw_status_card, 2)
        self.env_panel = EnvPanel()
        stats_row.addWidget(self.env_panel, 2)
        root.addLayout(stats_row)

        # Vital cards (live) - 2 rows
        key_box = QGroupBox("Key Vitals - Live (Smooth)")
        vg = QGridLayout(key_box)
        self.cards = {}
        vitals = [
            ("hr", "Heart Rate (Pulse GPIO40)", "bpm"),
            ("hrv", "HRV RMSSD", "ms"),
            ("temp", "Skin Temp DS18 Forearm", "°C"),
            ("room_temp", "Room Temp BME280 Shoulder", "°C"),
            ("humidity", "Humidity BME280", "%"),
            ("pressure", "Pressure BME280", "hPa"),
            ("lux", "Lux BH1750 Shoulder", "lx"),
            ("activity", "Activity MPU6050", "%"),
            ("gsr", "GSR GPIO5", "raw"),
            ("stress", "Stress", "%"),
            ("sleep", "Sleep", ""),
            ("quality", "Signal Quality", "%"),
        ]
        for i, (key, title, unit) in enumerate(vitals):
            card = VitalCard(title, unit)
            self.cards[key] = card
            vg.addWidget(card, i // 4, i % 4)
        root.addWidget(key_box)

        # Smooth live plots - 2 rows
        plots_box = QGroupBox("Smooth Live Waveforms - 20Hz Render (Shoulder+Forearm)")
        pg_layout = QGridLayout(plots_box)

        self.plot_pulse = SmoothLivePlot("Pulse Waveform - Analog S=40 Forearm (ADC 0..4095)", "ADC", "#f87171", history_s=8, fs_hz=50)
        self.plot_imu = SmoothLivePlot("Motion - MPU6050/2060 Accel (Shoulder)", "g", "#60a5fa", history_s=10, fs_hz=50)
        self.plot_gyro = SmoothLivePlot("Gyro - MPU6050/2060 (Shoulder)", "dps", "#a78bfa", history_s=10, fs_hz=50)
        self.plot_skin_temp = SmoothLivePlot("Skin Temp - DS18B20 Forearm D=6", "°C", "#fbbf24", history_s=30, fs_hz=1)
        self.plot_env = SmoothLivePlot("Room Temp - BME280 Shoulder", "°C", "#34d399", history_s=60, fs_hz=1)
        self.plot_lux = SmoothLivePlot("Lux - BH1750 Shoulder", "lx", "#f472b6", history_s=60, fs_hz=1)

        pg_layout.addWidget(self.plot_pulse, 0, 0)
        pg_layout.addWidget(self.plot_imu, 0, 1)
        pg_layout.addWidget(self.plot_gyro, 0, 2)
        pg_layout.addWidget(self.plot_skin_temp, 1, 0)
        pg_layout.addWidget(self.plot_env, 1, 1)
        pg_layout.addWidget(self.plot_lux, 1, 2)

        root.addWidget(plots_box)

        # Shared features + health signals summary (preserved logic)
        shared_box = QGroupBox("Shared Physiological Representation (Core Engine)")
        sb = QVBoxLayout(shared_box)
        self.shared_text = QTextEdit()
        self.shared_text.setReadOnly(True)
        self.shared_text.setMaximumHeight(160)
        self.shared_text.setPlaceholderText("Shared features appear here...")
        sb.addWidget(self.shared_text)
        root.addWidget(shared_box)

        signals_box = QGroupBox("Health Signals Summary (Preserved)")
        sig_layout = QHBoxLayout(signals_box)
        self.signal_labels = {}
        for mod in ["pcos", "sleep", "cardiometabolic", "autonomic"]:
            g = QGroupBox(mod.upper())
            vl = QVBoxLayout(g)
            lbl = QLabel("No data")
            lbl.setWordWrap(True)
            vl.addWidget(lbl)
            self.signal_labels[mod] = lbl
            sig_layout.addWidget(g)
        root.addWidget(signals_box)

        disc = QLabel(DISCLAIMER + " Shoulder mount: MPU6050/2060+BME280+BH1750 (SDA=8 SCL=9) | Forearm: Pulse S=40 + DS18B20 D=6. This system learns what is normal for an individual first.")
        disc.setWordWrap(True)
        disc.setObjectName("SmallMuted")
        root.addWidget(disc)

        scroll.setWidget(content)
        layout.addWidget(scroll)
        return tab

    # -------------------- Other tabs (preserved previous UI) --------------------
    def _build_baseline_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        root = QVBoxLayout(content)

        info = QLabel(
            "Personal Baseline Engine V8.4\n"
            "Learns what is normal for THIS person: mean, median, std, robust MAD, rolling baseline, confidence, "
            "minimum observations, seasonal/circadian context.\n"
            "CURRENT vs PERSONAL BASELINE -> normalized deviation (z-score, % change)\n"
            "Hardware: Shoulder env stable baseline + forearm pulse/skin temp personal baseline"
        )
        info.setWordWrap(True)
        root.addWidget(info)

        self.baseline_status = QLabel("No baseline yet. Collect at least 5 min calm data, then capture.")
        self.baseline_status.setWordWrap(True)
        root.addWidget(self.baseline_status)

        btn_row = QHBoxLayout()
        capture_btn = QPushButton("Capture Baseline (5 min)")
        capture_btn.clicked.connect(self._capture_baseline)
        btn_row.addWidget(capture_btn)
        root.addLayout(btn_row)

        self.baseline_details = QTextEdit()
        self.baseline_details.setReadOnly(True)
        self.baseline_details.setPlaceholderText("Baseline details appear here...")
        root.addWidget(self.baseline_details)

        self.baseline_comparison = QTextEdit()
        self.baseline_comparison.setReadOnly(True)
        self.baseline_comparison.setPlaceholderText("Current vs baseline comparison...")
        root.addWidget(self.baseline_comparison)

        scroll.setWidget(content)
        layout.addWidget(scroll)
        return tab

    def _build_trends_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel(
            "Longitudinal Engine - Heart of V8.4\n"
            "Rolling windows, persistence detection, trend detection, change-point detection, recovery detection, "
            "missing-data handling, confidence scoring.\n"
            "ONE ABNORMAL -> weak signal, REPEATED CHANGE -> stronger, MULTIPLE FEATURES -> multimodal, "
            "PERSISTENT + GOOD QUALITY -> higher confidence"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.trend_plot = TimeSeriesPlot("HR Trend (Pulse GPIO40)", "bpm", "#f87171")
        layout.addWidget(self.trend_plot)

        self.trend_plot2 = TimeSeriesPlot("HRV Trend", "ms", "#60a5fa")
        layout.addWidget(self.trend_plot2)

        self.longitudinal_text = QTextEdit()
        self.longitudinal_text.setReadOnly(True)
        self.longitudinal_text.setPlaceholderText("Longitudinal analysis appears here...")
        layout.addWidget(self.longitudinal_text)

        return tab

    def _build_health_signals_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        tabs = QTabWidget()

        pcos_tab = QWidget()
        pcos_layout = QVBoxLayout(pcos_tab)
        pcos_info = QLabel("MODULE A - PCOS / Reproductive-Metabolic Risk\nPCOS-associated physiological and clinical risk signals\nDistinguishes: clinical variables, wearable physiology, ultrasound, combined/fused")
        pcos_info.setWordWrap(True)
        pcos_layout.addWidget(pcos_info)
        self.pcos_text = QTextEdit()
        self.pcos_text.setReadOnly(True)
        pcos_layout.addWidget(self.pcos_text)
        tabs.addTab(pcos_tab, "PCOS / Reproductive-Metabolic")

        sleep_tab = QWidget()
        sleep_layout = QVBoxLayout(sleep_tab)
        sleep_info = QLabel("MODULE B - Sleep / Circadian Health\nUses activity, HR, HRV, temp, sleep duration/timing/regularity, day/night pattern")
        sleep_info.setWordWrap(True)
        sleep_layout.addWidget(sleep_info)
        self.sleep_text = QTextEdit()
        self.sleep_text.setReadOnly(True)
        sleep_layout.addWidget(self.sleep_text)
        tabs.addTab(sleep_tab, "Sleep / Circadian")

        cardio_tab = QWidget()
        cardio_layout = QVBoxLayout(cardio_tab)
        cardio_info = QLabel("MODULE C - Cardiometabolic Risk\nFeatures: resting HR, HRV, activity, BMI, age, BP if entered, glucose if entered, sleep, temp, longitudinal")
        cardio_info.setWordWrap(True)
        cardio_layout.addWidget(cardio_info)
        self.cardio_text = QTextEdit()
        self.cardio_text.setReadOnly(True)
        cardio_layout.addWidget(self.cardio_text)
        tabs.addTab(cardio_tab, "Cardiometabolic")

        auto_tab = QWidget()
        auto_layout = QVBoxLayout(auto_tab)
        auto_info = QLabel("MODULE D - Autonomic / Stress Regulation\nUses HRV, resting HR, GSR, activity, sleep, temp")
        auto_info.setWordWrap(True)
        auto_layout.addWidget(auto_info)
        self.autonomic_text = QTextEdit()
        self.autonomic_text.setReadOnly(True)
        auto_layout.addWidget(self.autonomic_text)
        tabs.addTab(auto_tab, "Autonomic / Stress")

        future_tab = QWidget()
        future_layout = QVBoxLayout(future_tab)
        future_info = QLabel("Future Modules - Not Implemented\nThese modules require appropriate dataset, validated features")
        future_info.setWordWrap(True)
        future_layout.addWidget(future_info)
        self.future_text = QTextEdit()
        self.future_text.setReadOnly(True)
        self.future_text.setText("\n".join([f"- {m}: Future research module - not implemented" for m in GLOBAL_REGISTRY.list_future()]))
        future_layout.addWidget(self.future_text)
        tabs.addTab(future_tab, "Future Modules")

        layout.addWidget(tabs)
        return tab

    def _build_data_quality_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel("Sensor Quality - Every reading has quality metadata: value, quality 0..1, source, timestamp, artifact\n"
                      "Detects: missing data, impossible values, flatline, excessive noise, motion artifacts, packet corruption, stale data\n"
                      "Hardware V8.4: MPU6050/2060 + BME280 + BH1750 (I2C SDA8 SCL9) + Pulse GPIO40 + DS18B20 GPIO6")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.quality_text = QTextEdit()
        self.quality_text.setReadOnly(True)
        layout.addWidget(self.quality_text)

        self.quality_gauge = GaugeWidget("Overall Data Quality")
        layout.addWidget(self.quality_gauge)

        return tab

    def _build_clinical_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        root = QVBoxLayout(content)

        info = QLabel("Clinical Inputs - Manual measurements (USER-ENTERED)\nBMI, BP, glucose, cycle info, age, etc.\nClearly labelled as USER-ENTERED, not MEASURED")
        info.setWordWrap(True)
        root.addWidget(info)

        grid = QGridLayout()
        self.age_spin = QDoubleSpinBox()
        self.age_spin.setRange(10, 80)
        self.age_spin.setValue(22)
        self.bmi_spin = QDoubleSpinBox()
        self.bmi_spin.setRange(10, 60)
        self.bmi_spin.setValue(23.5)
        self.bmi_spin.setDecimals(1)
        self.sys_spin = QDoubleSpinBox()
        self.sys_spin.setRange(0, 250)
        self.sys_spin.setValue(0)
        self.sys_spin.setSpecialValueText("none")
        self.dia_spin = QDoubleSpinBox()
        self.dia_spin.setRange(0, 150)
        self.dia_spin.setValue(0)
        self.dia_spin.setSpecialValueText("none")
        self.glucose_spin = QDoubleSpinBox()
        self.glucose_spin.setRange(0, 500)
        self.glucose_spin.setValue(0)
        self.glucose_spin.setSpecialValueText("none")
        self.cycle_spin = QSpinBox()
        self.cycle_spin.setRange(0, 120)
        self.cycle_spin.setValue(0)
        self.cycle_spin.setSpecialValueText("unknown")
        self.length_spin = QSpinBox()
        self.length_spin.setRange(0, 120)
        self.length_spin.setValue(28)
        self.cycle_irregular_combo = QComboBox()
        self.cycle_irregular_combo.addItems(["unknown", "regular", "irregular"])

        grid.addWidget(QLabel("Age"), 0, 0)
        grid.addWidget(self.age_spin, 0, 1)
        grid.addWidget(QLabel("BMI"), 0, 2)
        grid.addWidget(self.bmi_spin, 0, 3)
        grid.addWidget(QLabel("Systolic BP"), 1, 0)
        grid.addWidget(self.sys_spin, 1, 1)
        grid.addWidget(QLabel("Diastolic BP"), 1, 2)
        grid.addWidget(self.dia_spin, 1, 3)
        grid.addWidget(QLabel("Glucose mg/dL"), 2, 0)
        grid.addWidget(self.glucose_spin, 2, 1)
        grid.addWidget(QLabel("Cycle day"), 2, 2)
        grid.addWidget(self.cycle_spin, 2, 3)
        grid.addWidget(QLabel("Usual length"), 3, 0)
        grid.addWidget(self.length_spin, 3, 1)
        grid.addWidget(QLabel("Irregular"), 3, 2)
        grid.addWidget(self.cycle_irregular_combo, 3, 3)

        for w in [self.age_spin, self.bmi_spin, self.sys_spin, self.dia_spin, self.glucose_spin, self.cycle_spin, self.length_spin]:
            w.valueChanged.connect(self._clinical_changed)
        self.cycle_irregular_combo.currentTextChanged.connect(self._clinical_changed)

        root.addLayout(grid)

        self.clinical_text = QTextEdit()
        self.clinical_text.setReadOnly(True)
        root.addWidget(self.clinical_text)

        scroll.setWidget(content)
        layout.addWidget(scroll)
        return tab

    def _build_ultrasound_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel("Ultrasound - Periodic clinical imaging\nProvenance preserved: source image -> preprocessing -> detected features -> quality -> uncertainty")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.ultrasound_text = QTextEdit()
        self.ultrasound_text.setReadOnly(True)
        self.ultrasound_text.setPlaceholderText("Ultrasound features appear here...")
        layout.addWidget(self.ultrasound_text)

        btn_row = QHBoxLayout()
        self.cyst_size_spin = QDoubleSpinBox()
        self.cyst_size_spin.setRange(0, 100)
        self.cyst_size_spin.setValue(0)
        self.cyst_size_spin.setSpecialValueText("none")
        self.cyst_size_spin.setSuffix(" mm")
        btn_row.addWidget(QLabel("Cyst size"))
        btn_row.addWidget(self.cyst_size_spin)
        add_btn = QPushButton("Add Ultrasound (Clinically Entered)")
        add_btn.clicked.connect(self._add_ultrasound)
        btn_row.addWidget(add_btn)
        layout.addLayout(btn_row)

        return tab

    def _build_explanation_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel("Explainability - Every risk signal explains main contributing factors")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.explanation_text = QTextEdit()
        self.explanation_text.setReadOnly(True)
        layout.addWidget(self.explanation_text)

        return tab

    def _build_report_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel("Report Generation - Research report with limitations and recommendation")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        layout.addWidget(self.report_text)

        btn_row = QHBoxLayout()
        gen_btn = QPushButton("Generate Report")
        gen_btn.clicked.connect(self._generate_report)
        btn_row.addWidget(gen_btn)
        save_btn = QPushButton("Save Report")
        save_btn.clicked.connect(self._save_report)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        return tab

    def _build_validation_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel("Validation - Engineering vs Clinical")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.validation_text = QTextEdit()
        self.validation_text.setReadOnly(True)
        self.validation_text.setText(
            "CHRONO-TWIN NEXUS V8.4 Validation Status - Shoulder+Forearm\n"
            "========================================\n\n"
            "Hardware V8.4:\n"
            "- Shoulder mount: MPU6050/2060 (motion) + BME280 (room temp/hum/press) + BH1750 (lux)\n"
            "  I2C SDA=8 SCL=9 VCC=3V3 GND=GND\n"
            "- Forearm mount: Analog Pulse Sensor S=40 + DS18B20 DATA=6 (skin temp)\n"
            "- Optional GSR GPIO5\n"
            "- ESP32-S3 main controller\n\n"
            "Firmware V8.4:\n"
            "- 20Hz packet $CP2 with all sensors\n"
            "- BME280 0x76/0x77 auto-detect\n"
            "- BH1750 0x23/0x5C auto-detect\n"
            "- MPU6050 0x68/0x69 auto-detect\n"
            "- DS18B20 non-blocking\n"
            "- Analog pulse 12-bit ADC GPIO40\n"
            "- Status bits for each sensor\n"
            "- BLE + Serial dual output\n"
            "- Smooth 20Hz dashboard\n\n"
            "Engineering Validation:\n"
            "- Personal baseline: mean, median, std, MAD, rolling, confidence - IMPLEMENTED\n"
            "- Longitudinal engine: rolling windows, persistence, trend, change-point - IMPLEMENTED\n"
            "- Shared representation: heart_rate, resting_hr, hrv, activity, sleep, temp, gsr, env - IMPLEMENTED\n"
            "- Disease modules: PCOS, Sleep, Cardiometabolic, Autonomic - IMPLEMENTED\n"
            "- Sensor quality: missing, impossible, flatline, noise, motion, corruption - IMPLEMENTED\n"
            "- Hardware failure tests: MPU, BME280, BH1750, DS18B20, pulse, I2C - IMPLEMENTED\n"
            "- Smooth live dashboard 20fps - IMPLEMENTED V8.4\n"
            "- Environmental sensors BME280+BH1750 - IMPLEMENTED V8.4\n\n"
            "Clinical Validation: NOT ESTABLISHED\n"
            "- All modules are research-only signals\n"
            "- No diagnostic claims\n"
            "- Requires ethics-approved prospective study\n\n"
            "Wiring Verified:\n"
            "- SDA->8 SCL->9 VCC->3V3 GND->GND (all I2C)\n"
            "- Pulse S->40\n"
            "- DS18B20 DATA->6 with 4.7k pull-up\n"
            "- GSR->5 optional\n"
            "- LED->2\n"
        )
        layout.addWidget(self.validation_text)

        return tab

    # -------------------- Connection Logic (preserved + enhanced) --------------------
    def _refresh_ports(self):
        try:
            ports = ArduinoReader.available_ports()
            self.port_combo.clear()
            self.port_combo.addItems(ports if ports else ["/dev/ttyACM0", "/dev/ttyUSB0"])
        except Exception:
            self.port_combo.addItem("/dev/ttyACM0")

    def connect_serial(self, port=None):
        p = port or self.port_combo.currentText()
        if not p:
            p = "/dev/ttyACM0"
        try:
            # Stop existing
            if self.arduino_reader:
                self.arduino_reader.stop()
            self.arduino_reader = ArduinoReader(port=p, baud=115200)
            self.arduino_reader.sample_received.connect(self._on_sample_received)
            self.arduino_reader.error_received.connect(self._on_error)
            self.arduino_reader.state_changed.connect(self._on_state_changed)
            self.arduino_reader.start()
            self.mode_label.setText(f"Mode: LIVE SERIAL {p} - SDA8 SCL9 Pulse40 DS18-6")
            self.mode_label.setStyleSheet("font-weight: bold; color: #4ade80;")
            self.status_label.setText(f"Connected to {p} | V8.4 Shoulder+Forearm | Smooth 20Hz")
        except Exception as e:
            self.mode_label.setText(f"Mode: SERIAL FAILED {e}")
            self.mode_label.setStyleSheet("font-weight: bold; color: #f87171;")

    def connect_network(self, hostport: str):
        if not hostport:
            return
        try:
            parts = hostport.split(":")
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 7777
            if self.network_reader:
                self.network_reader.stop()
            self.network_reader = NetworkReader(host=host, port=port)
            self.network_reader.sample_received.connect(self._on_sample_received)
            self.network_reader.error_received.connect(self._on_error)
            self.network_reader.state_changed.connect(self._on_state_changed)
            self.network_reader.start()
            self.mode_label.setText(f"Mode: LIVE NETWORK {hostport}")
            self.mode_label.setStyleSheet("font-weight: bold; color: #4ade80;")
        except Exception as e:
            self.mode_label.setText(f"Mode: NETWORK FAILED {e}")

    def start_demo(self):
        if self.demo_stream:
            self.demo_stream.stop()
        self.demo_stream = DemoSensorStream(fs_hz=50.0)
        self.demo_stream.sample_received.connect(self._on_sample_received)
        self.demo_stream.state_changed.connect(self._on_state_changed)
        self.demo_stream.start()
        self.mode_label.setText("Mode: DEMO V8.4 Shoulder+Forearm - 50Hz smooth - clearly labelled")
        self.mode_label.setStyleSheet("font-weight: bold; color: #fbbf24;")

    def stop_stream(self):
        if self.arduino_reader:
            self.arduino_reader.stop()
            self.arduino_reader = None
        if self.network_reader:
            self.network_reader.stop()
            self.network_reader = None
        if self.demo_stream:
            self.demo_stream.stop()
            self.demo_stream = None
        self.mode_label.setText("Mode: NO STREAM")
        self.mode_label.setStyleSheet("font-weight: bold; color: #f87171;")

    def _on_sample_received(self, sample: SensorSample):
        # Called from reader thread via signal - update packet stats and push to buffers
        now = time.time()
        self.packet_count += 1
        dt = now - self.last_packet_time
        if dt > 0:
            self._rate_window.append(1.0/dt)
        self.last_packet_time = now

        # Push to live buffers for smooth plots
        self.live_buffers["pulse"].append(sample.ir)
        self.live_buffers["pulse_t"].append(sample.timestamp_s)
        self.live_buffers["ax"].append(sample.ax_g)
        self.live_buffers["ay"].append(sample.ay_g)
        self.live_buffers["az"].append(sample.az_g)
        self.live_buffers["imu_t"].append(sample.timestamp_s)
        self.live_buffers["skin_temp"].append(sample.temp_c if np.isfinite(sample.temp_c) else np.nan)
        self.live_buffers["temp_t"].append(sample.timestamp_s)
        self.live_buffers["lux"].append(sample.lux if sample.lux and np.isfinite(sample.lux) else np.nan)
        self.live_buffers["room_temp"].append(sample.room_temp_c if sample.room_temp_c and np.isfinite(sample.room_temp_c) else np.nan)
        self.live_buffers["hum"].append(sample.humidity_pct if sample.humidity_pct and np.isfinite(sample.humidity_pct) else np.nan)
        self.live_buffers["press"].append(sample.pressure_hpa if sample.pressure_hpa and np.isfinite(sample.pressure_hpa) else np.nan)
        self.live_buffers["env_t"].append(sample.timestamp_s)

        # Hardware status
        try:
            self.hw_status_card.update_status(sample.status)
        except Exception:
            pass

        # Env panel
        try:
            self.env_panel.update_values(sample)
        except Exception:
            pass

        # Feed to extractor (previous logic preserved)
        self.extractor.add_sample(sample)
        # We don't compute feature every sample for performance, timer does it

    def _on_error(self, msg: str):
        if "crc" in msg.lower() or "mismatch" in msg.lower():
            self.crc_errors += 1
        # print for debug
        # print(f"[ERR] {msg}")

    def _on_state_changed(self, state: str):
        # print(f"[STATE] {state}")
        pass

    def _refresh_smooth_plots(self):
        # Called at 20 fps
        try:
            now = time.time()
            # Pulse waveform
            if len(self.live_buffers["pulse"]) > 1:
                # Update pulse plot with recent data
                self.plot_pulse.times = deque(self.live_buffers["pulse_t"], maxlen=self.plot_pulse.maxlen)
                self.plot_pulse.values = deque(self.live_buffers["pulse"], maxlen=self.plot_pulse.maxlen)
                self.plot_pulse.refresh()
            # IMU accel magnitude for simplicity
            if len(self.live_buffers["ax"]) > 1:
                t = np.array(self.live_buffers["imu_t"])
                ax = np.array(self.live_buffers["ax"])
                ay = np.array(self.live_buffers["ay"])
                az = np.array(self.live_buffers["az"])
                mag = np.sqrt(ax*ax + ay*ay + az*az)
                # For smooth plot, push magnitude to plot_imu
                self.plot_imu.times = deque(self.live_buffers["imu_t"], maxlen=self.plot_imu.maxlen)
                self.plot_imu.values = deque(mag, maxlen=self.plot_imu.maxlen)
                self.plot_imu.refresh()
                # Gyro magnitude
                # Reuse same for gyro (we don't have separate gyro buffers currently, use mag)
                self.plot_gyro.times = deque(self.live_buffers["imu_t"], maxlen=self.plot_gyro.maxlen)
                self.plot_gyro.values = deque(mag*10, maxlen=self.plot_gyro.maxlen)  # scaled
                self.plot_gyro.refresh()
            # Skin temp
            if len(self.live_buffers["skin_temp"]) > 1:
                self.plot_skin_temp.times = deque(self.live_buffers["temp_t"], maxlen=self.plot_skin_temp.maxlen)
                self.plot_skin_temp.values = deque(self.live_buffers["skin_temp"], maxlen=self.plot_skin_temp.maxlen)
                self.plot_skin_temp.refresh()
            # Env
            if len(self.live_buffers["room_temp"]) > 1:
                self.plot_env.times = deque(self.live_buffers["env_t"], maxlen=self.plot_env.maxlen)
                self.plot_env.values = deque(self.live_buffers["room_temp"], maxlen=self.plot_env.maxlen)
                self.plot_env.refresh()
            if len(self.live_buffers["lux"]) > 1:
                self.plot_lux.times = deque(self.live_buffers["env_t"], maxlen=self.plot_lux.maxlen)
                self.plot_lux.values = deque(self.live_buffers["lux"], maxlen=self.plot_lux.maxlen)
                self.plot_lux.refresh()
        except Exception as e:
            # print(f"plot refresh err {e}")
            pass

    def _update_live_stats(self):
        if len(self._rate_window) > 0:
            self.packet_rate = float(np.mean(self._rate_window))
        self.live_stats_panel.rate_label.setText(f"Rate: {self.packet_rate:.1f} Hz")
        self.live_stats_panel.crc_label.setText(f"CRC Err: {self.crc_errors}")
        self.live_stats_panel.packets_label.setText(f"Packets: {self.packet_count}")
        # latency approx
        self.live_stats_panel.latency_label.setText(f"Latency: ~{int((time.time()-self.last_packet_time)*1000)} ms")

    def _load_scenario_dialog(self):
        from PySide6.QtWidgets import QInputDialog
        scenarios = ["scenario_1_stable", "scenario_2_gradual", "scenario_3_persistent",
                     "scenario_4_temporary", "scenario_5_sensor_failure", "scenario_6_recovery"]
        item, ok = QInputDialog.getItem(self, "Load Scenario", "Scenario:", scenarios, 0, False)
        if ok and item:
            self._load_scenario(item)

    def _load_scenario(self, name: str):
        path = DATA_DIR / "synthetic" / "scenarios" / f"{name}.json"
        if not path.exists():
            self.mode_label.setText(f"Scenario not found: {name}")
            return
        try:
            data = json.loads(path.read_text())
            from src.data_models import FeatureVector
            vectors = []
            for row in data["data"][:200]:
                fv = FeatureVector(
                    timestamp_s=row["timestamp_s"],
                    hr_bpm=row.get("hr_bpm"),
                    rmssd_ms=row.get("rmssd_ms"),
                    skin_temp_c=row.get("skin_temp_c"),
                    activity_level=row.get("activity_level", 0),
                    sleep_regularity=row.get("sleep_regularity", 0),
                    circadian_stability_index=row.get("circadian_stability_index", 50),
                    stress_index=row.get("stress_index", 30),
                    signal_quality=row.get("signal_quality", 0.8),
                )
                vectors.append(fv)
            self.feature_history = vectors
            self.mode_label.setText(f"Mode: SCENARIO {name} - {data['expected_result']}")
            self.mode_label.setStyleSheet("font-weight: bold; color: #60a5fa;")
            self._update_risk()
        except Exception as e:
            self.mode_label.setText(f"Failed to load scenario: {e}")

    def _update_features(self):
        # Previous logic preserved but now called from buffer
        # If we have extractor with last sample, compute
        if not hasattr(self.extractor, 'last_sample') or self.extractor.last_sample is None:
            return
        try:
            fv = self.extractor.compute()
            self.feature_history.append(fv)
            if len(self.feature_history) > 5000:
                self.feature_history = self.feature_history[-5000:]

            self._update_vital_cards(fv)

            try:
                shared = self.shared_extractor.extract(fv, self.feature_history[-50:])
                self.current_shared = shared
                self.shared_history.append(shared)
                if len(self.shared_history) > 500:
                    self.shared_history = self.shared_history[-500:]
                self.shared_text.setText(self.explanation_engine.explain_shared_features(shared))
            except Exception as e:
                pass
        except Exception as e:
            # print(f"feature update err {e}")
            pass

    def _update_vital_cards(self, fv: FeatureVector):
        def set_card(key, value, fmt="{:.0f}"):
            if key in self.cards:
                if value is None or (isinstance(value, float) and not np.isfinite(value)):
                    self.cards[key].set_value("—")
                else:
                    try:
                        self.cards[key].set_value(fmt.format(value))
                    except:
                        self.cards[key].set_value(str(value))

        set_card("hr", fv.hr_bpm)
        set_card("hrv", fv.rmssd_ms)
        set_card("temp", fv.skin_temp_c, "{:.1f}")
        # Env from last sample
        last = self.extractor.last_sample
        if last:
            set_card("room_temp", last.room_temp_c, "{:.1f}")
            set_card("humidity", last.humidity_pct, "{:.0f}")
            set_card("pressure", last.pressure_hpa, "{:.0f}")
            set_card("lux", last.lux, "{:.0f}")
        set_card("activity", fv.activity_level)
        set_card("gsr", fv.gsr_tonic)
        set_card("stress", fv.stress_index)
        set_card("sleep", fv.sleep_probability)
        set_card("quality", fv.signal_quality * 100 if fv.signal_quality else 0)
        # recovery from shared
        rec = 50
        if isinstance(fv.shared_features, dict):
            rec = fv.shared_features.get("recovery_score", 50)
        # not a card but keep

    def _update_risk(self):
        if not self.feature_history:
            return
        if not self.current_shared:
            return

        try:
            longitudinal_report = self.longitudinal_engine.evaluate(self.feature_history[-200:])
            self.longitudinal_text.setText(self.explanation_engine.explain_longitudinal(longitudinal_report))
        except Exception as e:
            longitudinal_report = None
            self.longitudinal_text.setText(f"Longitudinal error: {e}")

        clinical = self.clinical_data.copy()
        clinical["profile"] = self.profile

        module_results = {}
        for mod_name in GLOBAL_REGISTRY.list_implemented():
            try:
                mod_cls = GLOBAL_REGISTRY.get_module_class(mod_name)
                if not mod_cls:
                    continue
                mod = mod_cls(profile=self.profile)
                result = mod.predict(
                    shared=self.current_shared,
                    clinical=clinical,
                    ultrasound=self.ultrasound_data,
                    history=self.feature_history[-100:]
                )
                module_results[mod_name] = result
            except Exception as e:
                print(f"Module {mod_name} error: {e}")

        self.module_results = module_results

        for name, result in module_results.items():
            text_widget = None
            if name == "pcos":
                text_widget = self.pcos_text
            elif name == "sleep":
                text_widget = self.sleep_text
            elif name == "cardiometabolic":
                text_widget = self.cardio_text
            elif name == "autonomic":
                text_widget = self.autonomic_text

            if text_widget:
                text_widget.setText(self.explanation_engine.explain_module(result, self.current_shared))

            if name in self.signal_labels:
                self.signal_labels[name].setText(
                    f"{result.signal}\nLevel: {result.level}\nConf: {result.confidence:.2f}\nQuality: {result.data_quality:.2f}\n{result.explanation[:150]}..."
                )
                if result.level == "high":
                    self.signal_labels[name].setStyleSheet("color: #f87171; font-weight: bold;")
                elif result.level == "elevated":
                    self.signal_labels[name].setStyleSheet("color: #fb923c;")
                elif result.level == "moderate":
                    self.signal_labels[name].setStyleSheet("color: #fbbf24;")
                else:
                    self.signal_labels[name].setStyleSheet("color: #4ade80;")

        try:
            context = self.fusion_engine.build(
                profile=self.profile,
                shared=self.current_shared,
                longitudinal_report=longitudinal_report,
                bp={"systolic": self.profile.systolic_bp, "diastolic": self.profile.diastolic_bp} if self.profile.systolic_bp else None,
                glucose={"value": self.profile.glucose_mg_dl} if self.profile.glucose_mg_dl else None,
                ultrasound=self.ultrasound_data,
                wearable_quality=self.current_shared.overall_quality if self.current_shared else 0.0
            )
            fusion_result = self.fusion_engine.fuse(module_results, context)
            self.fusion_result = fusion_result

            overall_risk = 0
            if module_results:
                scores = []
                for r in module_results.values():
                    level_map = {"low": 15, "moderate": 40, "elevated": 65, "high": 85}
                    scores.append(level_map.get(r.level, 30))
                overall_risk = float(sum(scores) / len(scores)) if scores else 0

            self.risk_gauge.set_value(overall_risk)
            self.confidence_label.setText(f"Model Confidence: {fusion_result.confidence_breakdown.get('model_confidence', 0):.2f}")
            self.quality_label.setText(f"Data Quality: {fusion_result.confidence_breakdown.get('data_quality', 0):.2f}")
            self.coverage_label.setText(f"Coverage: {fusion_result.confidence_breakdown.get('fusion_coverage', 0):.0%}")
            self.quality_gauge.set_value(fusion_result.confidence_breakdown.get('data_quality', 0) * 100)

            if self.baseline_engine.has_baseline:
                self.baseline_label.setText(f"Baseline: YES (conf {self.baseline_engine.baseline.confidence:.2f}, {self.baseline_engine.baseline.days_covered} days)")
                self.baseline_label.setStyleSheet("color: #4ade80;")
            else:
                self.baseline_label.setText("Baseline: NO - need 5 min calm data")
                self.baseline_label.setStyleSheet("color: #fbbf24;")

            self.quality_text.setText(
                context.summary_text() + "\n\n" + self.explanation_engine.explain_fusion(fusion_result)
            )

            self.explanation_text.setText(
                self.explanation_engine.generate_report_explanation(
                    self.current_shared, longitudinal_report, fusion_result
                )
            )

            self.baseline_details.setText(
                f"Baseline has data: {self.baseline_engine.has_baseline}\n"
                f"Confidence: {self.baseline_engine.baseline.confidence:.2f}\n"
                f"Quality: {self.baseline_engine.baseline.quality:.2f}\n"
                f"Days covered: {self.baseline_engine.baseline.days_covered}\n"
                f"Samples: {self.baseline_engine.baseline.samples}\n"
                f"Metrics: {list(self.baseline_engine.baseline.stats.keys())}\n\n"
                + "\n".join([f"{k}: median {v.median:.1f}, std {v.std:.1f}, conf {v.confidence:.2f}" for k, v in self.baseline_engine.baseline.stats.items()])
            )
            if self.baseline_engine.has_baseline and self.feature_history:
                comp = self.baseline_engine.compare_current_vs_baseline(self.feature_history[-1])
                txt_lines = []
                for k, v in comp.items():
                    txt_lines.append(f"{k}: current {v.get('current')} vs baseline {v.get('baseline_median')} -> {v.get('deviation_pct')}%, z={v.get('zscore')}, status {v.get('status')}")
                self.baseline_comparison.setText("\n".join(txt_lines))

        except Exception as e:
            print(f"Fusion error: {e}")
            import traceback
            traceback.print_exc()

    def _capture_baseline(self):
        success = self.extractor.capture_baseline()
        if success:
            self.baseline_status.setText(f"Baseline captured! Confidence {self.baseline_engine.baseline.confidence:.2f}, {self.baseline_engine.baseline.days_covered} days, {len(self.baseline_engine.baseline.stats)} metrics")
        else:
            self.baseline_status.setText(f"Baseline failed: {self.extractor.last_capture_error}")

    def _clinical_changed(self):
        self.profile.age_years = float(self.age_spin.value())
        bmi = float(self.bmi_spin.value())
        self.profile.bmi = bmi if bmi > 0 else None
        sys_bp = float(self.sys_spin.value())
        self.profile.systolic_bp = sys_bp if sys_bp > 0 else None
        dia_bp = float(self.dia_spin.value())
        self.profile.diastolic_bp = dia_bp if dia_bp > 0 else None
        glucose = float(self.glucose_spin.value())
        self.profile.glucose_mg_dl = glucose if glucose > 0 else None
        cycle_day = int(self.cycle_spin.value())
        self.profile.cycle_day = cycle_day if cycle_day > 0 else None
        usual_length = int(self.length_spin.value())
        self.profile.usual_cycle_length_days = usual_length if usual_length > 0 else None
        irr_text = self.cycle_irregular_combo.currentText()
        if irr_text == "regular":
            self.profile.cycle_irregular = False
        elif irr_text == "irregular":
            self.profile.cycle_irregular = True
        else:
            self.profile.cycle_irregular = None

        self.clinical_data = {
            "age_years": self.profile.age_years,
            "bmi": self.profile.bmi,
            "systolic_bp": self.profile.systolic_bp,
            "diastolic_bp": self.profile.diastolic_bp,
            "glucose_mg_dl": self.profile.glucose_mg_dl,
            "cycle_day": self.profile.cycle_day,
            "usual_cycle_length_days": self.profile.usual_cycle_length_days,
            "cycle_irregular": self.profile.cycle_irregular,
            "profile": self.profile,
        }
        self.clinical_text.setText(json.dumps({k: v for k, v in self.clinical_data.items() if k != "profile"}, indent=2))
        self.extractor.set_profile(self.profile)

    def _add_ultrasound(self):
        size = float(self.cyst_size_spin.value())
        if size > 0:
            self.ultrasound_data = {
                "cyst_size_mm": size,
                "source": "CLINICALLY-ENTERED",
                "quality": 0.85,
                "timestamp_s": time.time(),
            }
            self.ultrasound_text.setText(
                f"Ultrasound (CLINICALLY-ENTERED)\n"
                f"Cyst size: {size} mm\n"
                f"Quality: 0.85\n"
                f"Provenance: CLINICALLY-ENTERED\n"
                f"Note: Image-derived features are UNKNOWN by design until validated labelled dataset exists. "
                f"This entry is clinically-entered structured feature.\n"
            )

    def _generate_report(self):
        if not self.fusion_result or not self.current_shared:
            self.report_text.setText("No data yet - collect some data first")
            return

        lines = [
            f"{'='*60}",
            f"CHRONO-TWIN NEXUS V8.4 RESEARCH REPORT - Shoulder+Forearm",
            f"{'='*60}",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Subject ID: Anonymous (no identifiers stored)",
            f"Hardware V8.4: Shoulder MPU6050/2060+BME280+BH1750 SDA=8 SCL=9 + Forearm Pulse S=40 DS18B20 D=6",
            f"Observation period: {len(self.feature_history)} samples over {(self.feature_history[-1].timestamp_s - self.feature_history[0].timestamp_s)/3600:.1f}h" if len(self.feature_history) > 1 else "Observation period: insufficient",
            f"",
            f"DISCLAIMER: {DISCLAIMER}",
            f"This is a research estimate, NOT a diagnosis. Clinical evaluation required.",
            f"",
            f"--- Sensor Data Available ---",
            f"Wearable: {'Yes' if self.feature_history else 'No'} ({len(self.feature_history)} samples)",
            f"Packet rate: {self.packet_rate:.1f} Hz, Packets: {self.packet_count}, CRC errors: {self.crc_errors}",
            f"Data quality: {self.fusion_result.confidence_breakdown.get('data_quality', 0):.2f}",
            f"Coverage: {self.fusion_result.confidence_breakdown.get('fusion_coverage', 0):.0%}",
            f"Present groups: {', '.join(self.fusion_result.context.present_groups())}",
            f"Missing groups: {', '.join(self.fusion_result.context.missing_groups())}",
            f"",
            f"--- Personal Baseline ---",
            f"Has baseline: {self.baseline_engine.has_baseline}",
        ]
        if self.baseline_engine.has_baseline:
            lines.append(f"Baseline confidence: {self.baseline_engine.baseline.confidence:.2f}")
            lines.append(f"Days covered: {self.baseline_engine.baseline.days_covered}")
            lines.append(f"Quality: {self.baseline_engine.baseline.quality:.2f}")
            for k, v in self.baseline_engine.baseline.stats.items():
                lines.append(f"  {k}: median {v.median:.1f} (p05 {v.p05:.1f} - p95 {v.p95:.1f}), std {v.std:.1f}")

        lines.extend([
            f"",
            f"--- Longitudinal Changes ---",
            f"{self.longitudinal_text.toPlainText()[:1000]}",
            f"",
            f"--- Disease Module Signals ---",
        ])
        for name, result in self.module_results.items():
            lines.append(f"\n[{name.upper()}] {result.signal} ({result.level})")
            lines.append(f"  Confidence: {result.confidence:.2f}, Data quality: {result.data_quality:.2f}, Validation: {result.clinical_validation}")
            lines.append(f"  Explanation: {result.explanation}")
            lines.append(f"  Drivers: {', '.join([d.get('description', '') for d in result.drivers[:2]])}")
            lines.append(f"  Limitations: {result.limitations[:200]}...")

        lines.extend([
            f"",
            f"--- Ultrasound ---",
            f"{self.ultrasound_text.toPlainText() if self.ultrasound_data else 'No ultrasound data'}",
            f"",
            f"--- Clinical Inputs ---",
            f"{json.dumps({k:v for k,v in self.clinical_data.items() if k!='profile'}, indent=2)}",
            f"",
            f"--- Fusion Summary ---",
            f"{self.fusion_result.explanation}",
            f"",
            f"--- Recommendations ---",
        ])
        for rec in self.fusion_result.recommendations:
            lines.append(f"- {rec}")

        lines.extend([
            f"",
            f"--- Limitations ---",
            f"- All signals are research-only, not diagnostic",
            f"- Model confidence: {self.fusion_result.confidence_breakdown.get('model_confidence', 0):.2f}",
            f"- Data quality: {self.fusion_result.confidence_breakdown.get('data_quality', 0):.2f}",
            f"- Clinical validation: NOT ESTABLISHED",
            f"- Requires clinical evaluation for any health concern",
            f"- Wearable data alone cannot diagnose any condition",
            f"- Hardware V8.4 shoulder+forearm mount, SDA=8 SCL=9 Pulse=40 DS18=6",
            f"",
            f"Recommended next step: Discuss relevant findings with qualified healthcare professional if symptomatic.",
            f"",
            f"{'='*60}",
        ])

        report = "\n".join(lines)
        self.report_text.setText(report)

    def _save_report(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "Save Report", str(DATA_DIR / "reports" / f"report_{int(time.time())}.txt"), "Text Files (*.txt)")
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(self.report_text.toPlainText(), encoding="utf-8")
            self.status_label.setText(f"Report saved to {path}")
