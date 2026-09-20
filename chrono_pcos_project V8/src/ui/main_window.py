"""CHRONO-PCOS V8.1 main window.

Primary navigation (judge-facing):

  1. OVERVIEW          - headline risk, confidence, data quality, coverage,
                         why-did-it-change, personal baseline, risk trend,
                         WHAT CHANGED SINCE LAST ASSESSMENT
  2. LIVE WEARABLE     - connection + sensor cards + live PPG waveform
  3. LONGITUDINAL      - personal baseline, change-point analysis, personal
                         physiological fingerprint, trends
  4. PCOS ANALYSIS     - model inputs, contributors, what-is/derived/not-measured
  5. PATIENT INPUTS    - low-burden cycle / symptom / BP / glucose / weight /
                         manual wearable-style readings
  6. CARE & ADHERENCE  - record an existing care plan, log taken/skipped/
                         snoozed doses, goals, appointment reminders
  7. CLINICAL DASHBOARD- clinician view: what changed since last visit,
                         report history + compare, ultrasound, notes, care
                         journey (OBSERVED/ASSOCIATED/UNKNOWN), QR access,
                         Model A-E
  8. ULTRASOUND + FUSION - periodic clinical imaging CV (quality gate first,
                         features UNKNOWN until a validated dataset exists),
                         provenance-aware multimodal fusion, one-page summary,
                         full longitudinal HTML report + QR token, dataset
                         requirements
  9. VALIDATION/RESEARCH - model performance, leakage-safe validation, ablation
  10. ADVANCED / RESEARCH TOOLS - experimental/legacy modules kept out of the
                         main flow (hormone illustration, VoxVasc, metabolic
                         challenge, what-if, research lab, assistant, evidence
                         center, diagnostics, timeline, protocol)

The core identity is longitudinal phenotyping + clinical support: the wearable
is an acquisition device, the innovation is the personal baseline, change
engine, WHAT CHANGED summary, and clinician-facing timeline between visits.

LIVE vs DEMO is always explicit: a header badge shows LIVE MODE / DEMO MODE /
REPLAY / NO STREAM, and demo/synthetic sessions are excluded from analysis.
When signal quality or model confidence is insufficient, the risk number is
withheld with a visible banner - the app never forces a prediction.
"""
from __future__ import annotations

import json
import time
from collections import deque
from pathlib import Path

from PySide6.QtCore import QTime, QTimer, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
    QMainWindow,
)

from src.config import (
    APP_VERSION,
    APP_VERSION_LABEL,
    DATA_DIR,
    FEATURE_LOG_INTERVAL_S,
    LOG_DIR,
    SERIAL_BAUD,
    UserProfile,
    WIFI_BRIDGE_DEFAULT_PORT,
)
from src.data_models import FeatureVector, RiskResult, SensorSample
from src.features.circadian_features import CircadianAnalyzer
from src.features.realtime_features import RealtimeFeatureExtractor
from src.models.assistant import AssistantEngine
from src.models.care_plan import CarePlanManager
from src.models.change_detector import ChangeDetector
from src.models.clinical_record import ClinicalRecord
from src.models.composite_scores import compute_scores
from src.models.fingerprint import FingerprintEngine
from src.models.fusion import FusionEngine
from src.models.hormone_estimator import HormoneEstimator
from src.models.ultrasound_cv import UltrasoundCV
from src.models.multi_day import MultiDayAnalyzer
from src.models.recommendations import generate as generate_recommendations
from src.models.recommendations import warning_level
from src.models.registry import EventLabelStore, registry_summary
from src.models.risk_engine import RiskEngine
from src.serial_io.arduino_reader import ArduinoReader
from src.serial_io.led_controller import LEDController
from src.serial_io.network_reader import NetworkReader
from src.serial_io.packet_parser import decode_status_flags
from src.ui.care_plan_tab import CarePlanTab
from src.ui.circadian_clock import CircadianClockWidget
from src.ui.clinical_tab import ClinicalTab
from src.ui.diagnostics_panel import DiagnosticsPanel
from src.ui.digital_twin import DigitalTwinWidget
from src.ui.evidence_center_tab import EvidenceCenterTab
from src.ui.explanation_panel import ExplanationPanel
from src.ui.fingerprint_widget import FingerprintWidget
from src.ui.gauges import GaugeWidget
from src.ui.history_trends_tab import HistoryTrendsTab
from src.ui.hormone_panel import HormonePanel
from src.ui.live_plots import TimeSeriesPlot
from src.ui.metabolic_challenge import MetabolicChallengeWidget
from src.ui.patient_inputs_tab import PatientInputsTab
from src.ui.radar_chart import RadarChartWidget
from src.ui.research_tab import ResearchWidget
from src.ui.sleep_view import SleepViewWidget
from src.ui.vital_cards import VitalCard
from src.ui.voice_vasc_tab import VoiceVascTab
from src.ui.assistant_tab import AssistantTab
from src.ui.theme import ACCENT_STRONG, DARK_QSS, GREEN, ORANGE, RED, TEXT_MUTED, YELLOW
from src.ui.timeline_tab import TimelineTab
from src.ui.ultrasound_fusion_tab import UltrasoundFusionTab
from src.ui.validation_tab import ValidationTab
from src.ui.whatif_tab import WhatIfWidget
from src.validation.sqi import should_withhold
from src.validation.store import ValidationStore
from src.utils.demo_stream import DemoSensorStream
from src.utils.history_store import HistoryStore
from src.utils.replay import FeatureReplay, features_from_frame
from src.utils.report import weekly_report_text, write_pdf_report
from src.utils.storage import append_row_csv
from src.utils.synthetic import generate_week

DISCLAIMER_TEXT = (
    "This is a research / pre-screening estimate, NOT a diagnosis. "
    "Clinical evaluation by a qualified professional is required for any diagnosis."
)


class CalibrationWizard(QDialog):
    """Guided baseline-calibration dialog (feature 47)."""

    def __init__(self, parent=None, on_live=None, on_simulate=None):
        super().__init__(parent)
        self.setWindowTitle("Baseline calibration wizard")
        self.resize(520, 260)
        layout = QVBoxLayout(self)
        steps = QLabel(
            "Step 1 - Sit still and breathe normally, sensors on wrist/upper arm.\n"
            "Step 2 - Let the dashboard collect at least 5 calm minutes.\n"
            "Step 3 - Capture the baseline: your personal normal ranges are built.\n\n"
            "Afterwards the risk confidence, anomaly detection and change detection "
            "all use YOUR ranges instead of population defaults."
        )
        steps.setWordWrap(True)
        layout.addWidget(steps)
        row = QHBoxLayout()
        live_btn = QPushButton("Use live data (needs ~5 min collected)")
        live_btn.clicked.connect(lambda: (on_live() if on_live else None, self.accept()))
        sim_btn = QPushButton("Simulate 5-min calm baseline (demo)")
        sim_btn.clicked.connect(lambda: (on_simulate() if on_simulate else None, self.accept()))
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        row.addWidget(live_btn)
        row.addWidget(sim_btn)
        row.addWidget(cancel)
        layout.addLayout(row)


class MainWindow(QMainWindow):
    def __init__(self, start_demo: bool = False, port: str | None = None, net: str | None = None,
                 db_path=None):
        super().__init__()
        self.setWindowTitle(f"CHRONO-PCOS v{APP_VERSION}, {APP_VERSION_LABEL}")
        self.resize(1600, 980)
        self.setStyleSheet(DARK_QSS)

        self.profile = UserProfile()
        self.extractor = RealtimeFeatureExtractor(self.profile)
        self.hormones = HormoneEstimator()
        self.risk_engine = RiskEngine()
        self.change_detector = ChangeDetector(baseline=self.extractor.baseline)
        self.circadian = CircadianAnalyzer()
        self.led = LEDController()
        self.stream = None
        self.sample_count = 0
        self.last_sample: SensorSample | None = None
        self.last_result: RiskResult | None = None
        self.last_decision = None
        self.raw_log_path = LOG_DIR / "live_samples.csv"

        # Local offline database, multi-day analysis, event labels, validation store.
        self.db = HistoryStore(db_path) if db_path else HistoryStore()
        self.vstore = ValidationStore(self.db.path)
        self.multi_day = MultiDayAnalyzer(self.db)
        self.events = EventLabelStore(self.db)
        # V6.2: care plan, clinical record and personal fingerprint engines.
        self.care = CarePlanManager(self.db)
        self.clinical = ClinicalRecord(self.db)
        self.fingerprint_engine = FingerprintEngine(baseline=self.extractor.baseline)
        # V8.1: ultrasound CV + multimodal fusion engines.
        self.us_cv = UltrasoundCV()
        self.fusion_engine = FusionEngine()
        self._reminder_alerted: set[str] = set()
        self._last_care_check = 0.0
        self.session_id: int | None = None
        self._last_feature_log = 0.0
        self._last_logs_refresh = 0.0
        self._last_change_eval = 0.0
        self._prev_risk: float | None = None
        self._prev_anomaly = 0.0
        self._prev_buttons = 0
        self._prev_status = 0
        self._last_alert_logged = ""
        self._measurement_mode = "rest"
        self._baseline_notice_shown = False
        self._recs_logged = False
        self.risk_history: deque = deque(maxlen=24 * 3600)
        self.replay: FeatureReplay | None = None

        self._build_ui()

        self.feature_timer = QTimer(self)
        self.feature_timer.timeout.connect(self._update_features_and_ui)
        self.feature_timer.start(1000)

        self.circadian_timer = QTimer(self)
        self.circadian_timer.timeout.connect(self._update_circadian_from_history)
        self.circadian_timer.start(60_000)

        if start_demo:
            self.start_demo()
        elif port:
            self.port_combo.setEditText(port)
            self.connect_serial()
        elif net:
            self.connect_network(net)

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        central = QWidget()
        central.setObjectName("CentralRoot")
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)
        self.setCentralWidget(central)

        header_frame = QFrame()
        header_frame.setObjectName("AppHeader")
        header = QHBoxLayout(header_frame)
        header.setContentsMargins(20, 12, 20, 12)
        title = QLabel("CHRONO-PCOS V8")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Longitudinal Multimodal Phenotyping + Periodic Clinical Imaging · research prototype, not clinically validated")
        subtitle.setObjectName("AppSubtitle")
        title_box = QVBoxLayout(); title_box.setSpacing(2); title_box.addWidget(title); title_box.addWidget(subtitle)

        # Live / demo badge, the single most important plainy indicator.
        self.mode_badge = QLabel("NO STREAM")
        self.mode_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_badge.setStyleSheet(self._badge_style(TEXT_MUTED))

        self.battery_label = QLabel("Battery: n/a")
        self.battery_label.setObjectName("SmallMuted")

        self.status_label = QLabel("Disconnected")
        self.status_label.setObjectName("StatusPill")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.warning_label = QLabel("")
        self.warning_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        header.addLayout(title_box, 2)
        header.addWidget(self.mode_badge)
        header.addSpacing(12)
        header.addWidget(self.battery_label)
        header.addSpacing(12)
        header.addWidget(self.status_label)
        header.addSpacing(16)
        header.addWidget(self.warning_label, 1)
        root.addWidget(header_frame)

        divider = QFrame()
        divider.setObjectName("HeaderDivider")
        divider.setFixedHeight(3)
        root.addWidget(divider)

        root.addWidget(self._make_controls())

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        root.addWidget(self.tabs, 1)
        self._build_overview_tab()
        self._build_live_tab()
        self._build_longitudinal_tab()
        self._build_pcos_analysis_tab()
        self._build_patient_inputs_tab()
        self._build_care_tab()
        self._build_clinical_tab()
        self._build_ultrasound_fusion_tab()
        self._build_validation_tab()
        self._build_advanced_tabs()

    @staticmethod
    def _badge_style(color: str) -> str:
        return (f"QLabel {{ background: {color}26; border: 1px solid {color}; color: {color}; "
                f"font-size: 10.5pt; font-weight: bold; padding: 5px 16px; border-radius: 12px; }}")

    def _set_mode_badge(self, mode: str):
        if not hasattr(self, "mode_badge"):
            return
        style_map = {
            "live": ("LIVE MODE", GREEN),
            "demo": ("DEMO MODE (SYNTHETIC)", ACCENT_STRONG),
            "replay": ("REPLAYING RECORDED DATA", ORANGE),
            "none": ("NO STREAM", TEXT_MUTED),
        }
        text, color = style_map.get(mode, ("NO STREAM", TEXT_MUTED))
        self.mode_badge.setText(text)
        self.mode_badge.setStyleSheet(self._badge_style(color))

    def _make_controls(self) -> QGroupBox:
        box = QGroupBox("Connection + participant inputs")
        outer = QVBoxLayout(box)

        row1 = QHBoxLayout()
        self.port_combo = QComboBox(); self.port_combo.setEditable(True); self.refresh_ports()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_ports)
        connect_btn = QPushButton("Connect Wearable")
        connect_btn.clicked.connect(self.connect_serial)
        demo_btn = QPushButton("Demo Mode (synthetic)")
        demo_btn.clicked.connect(self.start_demo)
        stop_btn = QPushButton("Stop")
        stop_btn.clicked.connect(self.stop_stream)
        row1.addWidget(QLabel("Port")); row1.addWidget(self.port_combo, 1)
        row1.addWidget(refresh_btn); row1.addWidget(connect_btn); row1.addWidget(demo_btn); row1.addWidget(stop_btn)
        self.net_edit = QLineEdit(); self.net_edit.setPlaceholderText("ESP8266 bridge IP:port, e.g. 192.168.4.1:7777")
        net_btn = QPushButton("Connect Wi-Fi Bridge")
        net_btn.clicked.connect(lambda: self.connect_network(self.net_edit.text().strip()))
        row1.addWidget(self.net_edit, 1); row1.addWidget(net_btn)
        judge_btn = QPushButton("Judge Mode (60 s demo)")
        judge_btn.clicked.connect(self._judge_demo)
        row1.addWidget(judge_btn)
        outer.addLayout(row1)

        row2 = QHBoxLayout()
        self.age_spin = QDoubleSpinBox(); self.age_spin.setRange(10, 60); self.age_spin.setValue(17); self.age_spin.setSuffix(" y")
        self.bmi_spin = QDoubleSpinBox(); self.bmi_spin.setRange(10, 60); self.bmi_spin.setValue(23); self.bmi_spin.setDecimals(1)
        self.sys_spin = QDoubleSpinBox(); self.sys_spin.setRange(0, 250); self.sys_spin.setValue(0); self.sys_spin.setDecimals(0); self.sys_spin.setSpecialValueText("none"); self.sys_spin.setSuffix(" SYS")
        self.dia_spin = QDoubleSpinBox(); self.dia_spin.setRange(0, 150); self.dia_spin.setValue(0); self.dia_spin.setDecimals(0); self.dia_spin.setSpecialValueText("none"); self.dia_spin.setSuffix(" DIA")
        self.cycle_spin = QSpinBox(); self.cycle_spin.setRange(0, 120); self.cycle_spin.setValue(0); self.cycle_spin.setSpecialValueText("unknown")
        self.length_spin = QSpinBox(); self.length_spin.setRange(0, 120); self.length_spin.setValue(0); self.length_spin.setSpecialValueText("unknown")
        self.glucose_spin = QDoubleSpinBox(); self.glucose_spin.setRange(0, 500); self.glucose_spin.setValue(0); self.glucose_spin.setSpecialValueText("none"); self.glucose_spin.setSuffix(" mg/dL")
        self.glucose_context = QComboBox(); self.glucose_context.addItems(["unknown", "fasting", "2hr post-meal", "random"])
        for w in [self.age_spin, self.bmi_spin, self.sys_spin, self.dia_spin, self.cycle_spin, self.length_spin, self.glucose_spin]:
            w.valueChanged.connect(self._profile_changed)
        self.glucose_context.currentTextChanged.connect(self._profile_changed)

        row2.addWidget(QLabel("Age")); row2.addWidget(self.age_spin)
        row2.addWidget(QLabel("BMI")); row2.addWidget(self.bmi_spin)
        row2.addWidget(QLabel("BP")); row2.addWidget(self.sys_spin); row2.addWidget(self.dia_spin)
        row2.addWidget(QLabel("Cycle day")); row2.addWidget(self.cycle_spin)
        row2.addWidget(QLabel("Length")); row2.addWidget(self.length_spin)
        row2.addWidget(QLabel("Glucose")); row2.addWidget(self.glucose_spin)
        row2.addWidget(self.glucose_context)
        outer.addLayout(row2)

        row3 = QHBoxLayout()
        self.height_spin = QDoubleSpinBox(); self.height_spin.setRange(0, 230); self.height_spin.setValue(0); self.height_spin.setDecimals(0); self.height_spin.setSpecialValueText("none"); self.height_spin.setSuffix(" cm")
        self.weight_spin = QDoubleSpinBox(); self.weight_spin.setRange(0, 200); self.weight_spin.setValue(0); self.weight_spin.setDecimals(1); self.weight_spin.setSpecialValueText("none"); self.weight_spin.setSuffix(" kg")
        self.waist_spin = QDoubleSpinBox(); self.waist_spin.setRange(0, 200); self.waist_spin.setValue(0); self.waist_spin.setDecimals(1); self.waist_spin.setSpecialValueText("none"); self.waist_spin.setSuffix(" cm")
        self.auto_bmi_label = QLabel("")
        self.auto_bmi_label.setObjectName("SmallMuted")
        for w in [self.height_spin, self.weight_spin, self.waist_spin]:
            w.valueChanged.connect(self._profile_changed)
        row3.addWidget(QLabel("Height")); row3.addWidget(self.height_spin)
        row3.addWidget(QLabel("Weight")); row3.addWidget(self.weight_spin)
        row3.addWidget(QLabel("Waist")); row3.addWidget(self.waist_spin)
        self.participant_edit = QLineEdit(); self.participant_edit.setPlaceholderText("Anonymous ID, e.g. P01")
        row3.addWidget(QLabel("Participant")); row3.addWidget(self.participant_edit)
        row3.addWidget(self.auto_bmi_label, 1)
        outer.addLayout(row3)
        return box

    # -------------------------------------------------------- 01 OVERVIEW
    def _build_overview_tab(self):
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content.setObjectName("OverviewScrollContent")
        root = QVBoxLayout(content)
        root.setContentsMargins(2, 2, 2, 2)
        root.setSpacing(9)

        # ---- Headline card: risk + confidence + quality + coverage ----
        head = QHBoxLayout()
        self.risk_gauge = GaugeWidget("PCOS-Related Risk Estimate (research)")
        head.addWidget(self.risk_gauge, 2)

        meta_box = QGroupBox("Estimate summary")
        mb = QVBoxLayout(meta_box)
        self.confidence_label = QLabel("Confidence: -")
        self.confidence_label.setObjectName("BigValue")
        self.quality_label = QLabel("Data quality: -")
        self.quality_label.setObjectName("BigValue")
        self.coverage_label = QLabel("Longitudinal coverage: -")
        self.coverage_label.setObjectName("BigValue")
        self.withheld_banner = QLabel("PREDICTION WITHHELD, INSUFFICIENT SIGNAL QUALITY")
        self.withheld_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.withheld_banner.setWordWrap(True)
        self.withheld_banner.setStyleSheet(
            "QLabel { background: #7f1d1d; border: 2px solid #f87171; color: #fecaca; "
            "font-size: 13pt; font-weight: bold; padding: 12px; border-radius: 8px; }")
        self.withheld_banner.hide()
        for w in [self.confidence_label, self.quality_label, self.coverage_label]:
            mb.addWidget(w)
        mb.addWidget(self.withheld_banner)
        head.addWidget(meta_box, 1)
        root.addLayout(head)

        # ---- Key vitals ----
        key_box = QGroupBox("Key vitals (live)")
        vg = QGridLayout(key_box)
        vg.setSpacing(8)
        self.cards = {}
        key_cards = [
            ("hr", "Heart Rate", "bpm"),
            ("hrv", "HRV (RMSSD)", "ms"),
            ("temp", "Skin Temp", "°C"),
            ("activity", "Activity", "%"),
            ("gsr", "GSR", "raw"),
            ("stress", "Stress Index", "%"),
            ("sleep", "Sleep Status", ""),
            ("quality", "Signal Quality", "%"),
            ("health", "Daily Health", "%"),
        ]
        for i, (key, title, unit) in enumerate(key_cards):
            card = VitalCard(title, unit)
            self.cards[key] = card
            vg.addWidget(card, i // 3, i % 3)
        root.addWidget(key_box)

        # ---- Digital twin flow (visual pipeline) ----
        twin_box = QGroupBox("Digital Twin Flow, live → features → model → estimate")
        tb = QVBoxLayout(twin_box)
        self.digital_twin = DigitalTwinWidget()
        tb.addWidget(self.digital_twin)
        root.addWidget(twin_box)

        # ---- Why did the estimate change? + personal baseline ----
        mid = QHBoxLayout()
        why_box = QGroupBox("WHY DID THE ESTIMATE CHANGE? (model contributors)")
        wb = QVBoxLayout(why_box)
        self.contributors_text = QTextEdit(); self.contributors_text.setReadOnly(True)
        self.contributors_text.setPlaceholderText("Feature contributions appear here once a risk estimate exists.")
        wb.addWidget(self.contributors_text)
        mid.addWidget(why_box, 3)

        bl_box = QGroupBox("Personal baseline (what is normal for THIS person)")
        bb = QVBoxLayout(bl_box)
        self.baseline_status = QLabel("No baseline yet, sit still for 5 minutes, then press the button (or the physical BASELINE button).")
        self.baseline_status.setWordWrap(True)
        self.ranges_label = QLabel("Using population defaults until baseline is captured.")
        self.ranges_label.setObjectName("SmallMuted")
        self.ranges_label.setWordWrap(True)
        self.capture_btn = QPushButton("Capture baseline (5 min)")
        self.capture_btn.clicked.connect(self._capture_baseline)
        wizard_btn = QPushButton("Calibration wizard")
        wizard_btn.clicked.connect(self._open_calibration_wizard)
        btn_row = QHBoxLayout(); btn_row.addWidget(self.capture_btn); btn_row.addWidget(wizard_btn)
        bb.addWidget(self.baseline_status)
        bb.addWidget(self.ranges_label)
        bb.addLayout(btn_row)
        mid.addWidget(bl_box, 2)
        root.addLayout(mid)

        # ---- Longitudinal risk trend ----
        trend_box = QGroupBox("Longitudinal trend (risk over time, real data only)")
        tb = QVBoxLayout(trend_box)
        self.risk_trend_plot = TimeSeriesPlot("Risk estimate", "%", "#f87171")
        tb.addWidget(self.risk_trend_plot)
        root.addWidget(trend_box)

        # ---- WHAT CHANGED SINCE LAST ASSESSMENT? ----
        wc_box = QGroupBox("WHAT CHANGED SINCE LAST ASSESSMENT? (evidence-linked)")
        wb = QVBoxLayout(wc_box)
        self.what_changed_overview = QTextEdit()
        self.what_changed_overview.setReadOnly(True)
        self.what_changed_overview.setPlaceholderText(
            "Evidence-linked changes (physiology, cycle, symptoms, adherence, model) appear here. "
            "Changes are temporally associated observations, never causes.")
        wb.addWidget(self.what_changed_overview)
        root.addWidget(wc_box)

        # ---- Permanent disclaimer ----
        disclaimer = QLabel(DISCLAIMER_TEXT)
        disclaimer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disclaimer.setWordWrap(True)
        disclaimer.setStyleSheet(
            "QLabel { color: #fbbf24; border: 1px solid #92400e; background: #451a03; "
            "font-size: 10.5pt; padding: 8px; border-radius: 6px; }")
        root.addWidget(disclaimer)

        scroll.setWidget(content)
        tab_layout.addWidget(scroll)
        self.tabs.addTab(tab, "01 Overview")

    # -------------------------------------------------- 02 LIVE WEARABLE
    def _build_live_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab); layout.setSpacing(10)

        conn_box = QGroupBox("Connection")
        cb = QHBoxLayout(conn_box)
        self.live_conn_label = QLabel("Disconnected")
        self.live_conn_label.setObjectName("BigValue")
        self.packet_count_label = QLabel("Packets: 0")
        self.packet_loss_label = QLabel("Packet loss: -")
        self.last_packet_label = QLabel("Last packet: -")
        for w in [self.live_conn_label, self.packet_count_label, self.packet_loss_label, self.last_packet_label]:
            cb.addWidget(w)
        cb.addStretch(1)
        self.live_withheld_banner = QLabel("PREDICTION WITHHELD, INSUFFICIENT SIGNAL QUALITY")
        self.live_withheld_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.live_withheld_banner.setWordWrap(True)
        self.live_withheld_banner.setStyleSheet(
            "QLabel { background: #7f1d1d; border: 2px solid #f87171; color: #fecaca; "
            "font-size: 13pt; font-weight: bold; padding: 10px; border-radius: 8px; }")
        self.live_withheld_banner.hide()
        cb.addWidget(self.live_withheld_banner, 1)
        layout.addWidget(conn_box)

        # Sensor cards (dedicated live copies, so the Overview stays clean).
        cards_box = QGroupBox("Live sensor readings")
        cg = QGridLayout(cards_box)
        cg.setSpacing(8)
        self.live_cards = {}
        live_cards = [
            ("hr", "Heart Rate", "bpm"),
            ("hrv", "HRV (RMSSD)", "ms"),
            ("temp", "Skin Temp", "°C"),
            ("activity", "Activity", "%"),
            ("gsr", "GSR", "raw"),
            ("quality", "Signal Quality", "%"),
        ]
        for i, (key, title, unit) in enumerate(live_cards):
            card = VitalCard(title, unit, compact=True)
            self.live_cards[key] = card
            cg.addWidget(card, 0, i)
        layout.addWidget(cards_box)

        # Live waveforms.
        plots_row = QHBoxLayout()
        left_col = QVBoxLayout()
        self.ppg_plot = TimeSeriesPlot("Live PPG waveform", "a.u.", "#3aa7f0")
        left_col.addWidget(self.ppg_plot, 3)
        self.hr_plot = TimeSeriesPlot("Heart Rate", "bpm", "#34d399")
        self.hrv_plot = TimeSeriesPlot("RMSSD HRV", "ms", "#fbbf24")
        self.temp_plot = TimeSeriesPlot("Skin Temperature", "°C", "#fb923c")
        plots_row.addLayout(left_col, 3)
        right_col = QVBoxLayout()
        right_col.addWidget(self.hr_plot)
        right_col.addWidget(self.hrv_plot)
        right_col.addWidget(self.temp_plot)
        plots_row.addLayout(right_col, 2)
        layout.addLayout(plots_row, 1)

        self.tabs.addTab(tab, "02 Live Wearable")

    # -------------------------------------------------- 03 LONGITUDINAL
    def _build_longitudinal_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab); layout.setSpacing(10)

        change_box = QGroupBox("Personal baseline → change detection")
        cb = QVBoxLayout(change_box)
        self.long_baseline_label = QLabel("Personal baseline: not captured yet (5 calm minutes needed).")
        self.long_baseline_label.setObjectName("SmallMuted")
        self.change_summary_label = QLabel("No longitudinal history yet, connect the wearable or load a recorded week.")
        self.change_summary_label.setWordWrap(True)
        self.change_summary_label.setObjectName("BigValue")
        self.change_details = QTextEdit(); self.change_details.setReadOnly(True)
        self.change_details.setPlaceholderText(
            "Per-metric change analysis appears here:\n"
            "· single-point deviation vs persistent deviation vs progressive change vs recovery\n"
            "· persistence (hours), slope per day, quality gate\n"
            "· a single abnormal reading is never interpreted as PCOS risk.")
        cb.addWidget(self.long_baseline_label)
        cb.addWidget(self.change_summary_label)
        cb.addWidget(self.change_details, 2)
        layout.addWidget(change_box, 2)

        # Personal physiological fingerprint, what is normal for THIS person.
        finger_box = QGroupBox("PERSONAL PHYSIOLOGICAL FINGERPRINT, baseline vs current state")
        fb = QVBoxLayout(finger_box)
        self.fingerprint_widget = FingerprintWidget()
        fb.addWidget(self.fingerprint_widget)
        layout.addWidget(finger_box, 2)

        self.history_tab = HistoryTrendsTab()
        self.history_tab.load_demo_week.connect(self._load_demo_week)
        self.history_tab.replay_latest.connect(self._replay_latest)
        self.history_tab.report_pdf.connect(self._weekly_report_pdf)
        self.history_tab.report_text.connect(self._weekly_report_text)
        self.history_tab.export_json.connect(self._export_json)
        layout.addWidget(self.history_tab, 3)

        self.tabs.addTab(tab, "03 Longitudinal")

    # ------------------------------------------------- 04 PCOS ANALYSIS
    def _build_pcos_analysis_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab); layout.setSpacing(10)

        summary_row = QHBoxLayout()
        summary_box = QGroupBox("PCOS-related risk estimate (research)")
        sb = QVBoxLayout(summary_box)
        self.analysis_risk_label = QLabel("-")
        self.analysis_risk_label.setObjectName("HeadlineValue")
        self.analysis_meta_label = QLabel("Confidence:, · Data quality:, · Coverage: -")
        self.analysis_meta_label.setObjectName("SmallMuted")
        self.analysis_reason_label = QLabel("")
        self.analysis_reason_label.setWordWrap(True)
        for w in [self.analysis_risk_label, self.analysis_meta_label, self.analysis_reason_label]:
            sb.addWidget(w)
        summary_row.addWidget(summary_box, 1)

        inputs_box = QGroupBox("Model inputs (V6)")
        ib = QGridLayout(inputs_box)
        self.input_status = {}
        inputs = [
            ("wearable", "Wearable (PPG + temp + IMU)"),
            ("longitudinal", "Longitudinal baseline / deviations"),
            ("cycle", "Menstrual cycle info"),
            ("symptoms", "Symptoms"),
            ("metabolic", "Optional BP / glucose"),
            ("ecg", "Optional periodic ECG"),
            ("ultrasound", "Ultrasound-derived (periodic)"),
        ]
        for i, (key, label) in enumerate(inputs):
            status = QLabel("-")
            status.setObjectName("SmallMuted")
            self.input_status[key] = status
            ib.addWidget(QLabel(label), i // 2, (i % 2) * 2)
            ib.addWidget(status, i // 2, (i % 2) * 2 + 1)
        summary_row.addWidget(inputs_box, 1)
        layout.addLayout(summary_row)

        mid = QHBoxLayout()
        self.explanation = ExplanationPanel()
        mid.addWidget(self.explanation, 3)

        right_col = QVBoxLayout()
        self.radar = RadarChartWidget()
        radar_box = QGroupBox("Risk domain fingerprint")
        rb = QVBoxLayout(radar_box); rb.addWidget(self.radar)
        right_col.addWidget(radar_box)

        trans_box = QGroupBox("Transparency, what this system measures")
        tb = QVBoxLayout(trans_box)
        trans = QLabel(
            "MEASURED:  PPG (pulse wave) · skin temperature · IMU (motion/activity) · optional GSR.\n\n"
            "DERIVED:  Heart rate · HRV · activity · sleep/wake timing · personal-baseline deviations · "
            "longitudinal change patterns.\n\n"
            "NOT DIRECTLY MEASURED:  testosterone · AMH · LH · FSH · insulin · estrogen · progesterone · "
            "ovarian morphology. Any hormone-like values shown in the research tools are model illustrations "
            "with no diagnostic meaning.\n\n"
            "Wording: features 'contributed to the model estimate', they do NOT 'cause' PCOS.")
        trans.setWordWrap(True)
        trans.setObjectName("SmallMuted")
        tb.addWidget(trans)
        right_col.addWidget(trans_box)
        mid.addLayout(right_col, 2)
        layout.addLayout(mid, 1)

        disclaimer = QLabel(DISCLAIMER_TEXT)
        disclaimer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disclaimer.setStyleSheet(
            "QLabel { color: #fbbf24; border: 1px solid #92400e; background: #451a03; "
            "font-size: 10.5pt; padding: 6px; border-radius: 6px; }")
        layout.addWidget(disclaimer)

        self.tabs.addTab(tab, "04 PCOS Analysis")

    # ------------------------------------------------ 05 PATIENT INPUTS
    def _build_patient_inputs_tab(self):
        self.patient_inputs = PatientInputsTab(self.db)
        self.patient_inputs.inputs_saved.connect(self._on_patient_inputs_saved)
        self.tabs.addTab(self.patient_inputs, "05 Patient Inputs")

    # ----------------------------------------- 06 CARE & ADHERENCE
    def _build_care_tab(self):
        self.care_tab = CarePlanTab(self.care)
        self.care_tab.data_changed.connect(self._on_care_data_changed)
        self.tabs.addTab(self.care_tab, "06 Care & Adherence")

    # --------------------------------------- 07 CLINICAL DASHBOARD
    def _build_clinical_tab(self):
        self.clinical_tab = ClinicalTab(
            self.db, self.clinical, self.care,
            report_metrics_fn=self._report_metrics,
        )
        self.tabs.addTab(self.clinical_tab, "07 Clinical Dashboard")

    # --------------------------------- 08 ULTRASOUND & MULTIMODAL FUSION
    def _build_ultrasound_fusion_tab(self):
        self.ultrasound_tab = UltrasoundFusionTab(self.db, report_metrics_fn=self._report_metrics)
        self.tabs.addTab(self.ultrasound_tab, "08 Ultrasound + Fusion")

    # ----------------------------------------- 09 VALIDATION / RESEARCH
    def _build_validation_tab(self):
        self.validation_tab = ValidationTab(self.db, self.vstore)
        self.tabs.addTab(self.validation_tab, "09 Validation / Research")

    # ---------------------------------------------- 07 ADVANCED TOOLS
    def _build_advanced_tabs(self):
        """Everything experimental / legacy lives here, out of the main flow."""
        advanced = QWidget()
        layout = QVBoxLayout(advanced)
        layout.setContentsMargins(0, 0, 0, 0)
        note = QLabel(
            "ADVANCED / RESEARCH TOOLS, experimental and legacy modules kept for research only. "
            "Nothing on these tabs feeds the headline risk estimate.")
        note.setObjectName("WarningText")
        note.setWordWrap(True)
        layout.addWidget(note)

        inner = QTabWidget()
        inner.setDocumentMode(True)

        # Sleep + circadian
        sleep_tab = QWidget(); sl = QHBoxLayout(sleep_tab); sl.setSpacing(12)
        left = QVBoxLayout()
        self.sleep_view = SleepViewWidget()
        left.addWidget(self.sleep_view, 3)
        win_box = QGroupBox("Sleep / wake timing input (sharpens sleep estimates)")
        wb = QHBoxLayout(win_box)
        self.sleep_onset_edit = QTimeEdit(); self.sleep_onset_edit.setTime(QTime(23, 0)); self.sleep_onset_edit.setDisplayFormat("HH:mm")
        self.wake_edit = QTimeEdit(); self.wake_edit.setTime(QTime(7, 0)); self.wake_edit.setDisplayFormat("HH:mm")
        wb.addWidget(QLabel("Sleep onset")); wb.addWidget(self.sleep_onset_edit)
        wb.addWidget(QLabel("Wake")); wb.addWidget(self.wake_edit)
        self.sleep_onset_edit.timeChanged.connect(self._sleep_window_changed)
        self.wake_edit.timeChanged.connect(self._sleep_window_changed)
        left.addWidget(win_box)
        sl.addLayout(left, 3)
        clock_box = QGroupBox("Circadian Clock")
        cb = QVBoxLayout(clock_box)
        self.clock = CircadianClockWidget(); cb.addWidget(self.clock)
        explain = QLabel("CSI uses HR, HRV, temperature, GSR, activity and sleep timing rhythms.")
        explain.setWordWrap(True); explain.setObjectName("SmallMuted"); cb.addWidget(explain)
        sl.addWidget(clock_box, 1)
        inner.addTab(sleep_tab, "Sleep + Circadian")

        # Hormone illustration, research only, clearly NOT a measurement.
        hormone_tab = QWidget(); hl = QHBoxLayout(hormone_tab)
        hormone_box = QGroupBox("Hormone illustration (RESEARCH ONLY, NOT MEASURED)")
        hb = QVBoxLayout(hormone_box)
        self.hormone_panel = HormonePanel()
        hb.addWidget(self.hormone_panel)
        note = QLabel(
            "These are illustrative model estimates from physiology, glucose and cycle data. "
            "They are NOT blood/urine hormone tests and NEVER enter the headline risk score. "
            "The system does not and cannot measure testosterone, AMH, LH, FSH or insulin directly.")
        note.setObjectName("WarningText"); note.setWordWrap(True); hb.addWidget(note)
        hl.addWidget(hormone_box, 2)
        pathway = QTextEdit(); pathway.setReadOnly(True)
        pathway.setText(
            "Hormone illustration pathway (research only):\n\n"
            "Current physiology → stress/autonomic state → metabolic state → endocrine tendency (illustration)\n\n"
            "The V6 headline PCOS risk is computed WITHOUT these values.\n"
            "Most reliable estimates: insulin tendency, cortisol tendency (still not measurements).\n"
            "Low-confidence estimates: testosterone, LH, FSH, estrogen, progesterone, AMH.")
        hl.addWidget(pathway, 1)
        inner.addTab(hormone_tab, "Hormone Illustration")

        self.challenge_widget = MetabolicChallengeWidget()
        inner.addTab(self.challenge_widget, "Metabolic Challenge")

        self.voice_vasc_tab = VoiceVascTab()
        inner.addTab(self.voice_vasc_tab, "VoxVasc")

        self.whatif = WhatIfWidget()
        self.whatif.simulation_ran.connect(self._on_simulation_ran)
        inner.addTab(self.whatif, "What-if Lab")

        self.research = ResearchWidget(self.db)
        inner.addTab(self.research, "Research Lab")

        self.assistant_engine = AssistantEngine(history_store=self.db, multi_day=self.multi_day)
        self.assistant_tab = AssistantTab(self.assistant_engine)
        inner.addTab(self.assistant_tab, "AI Assistant")

        self.evidence_tab = EvidenceCenterTab(self.vstore)
        inner.addTab(self.evidence_tab, "Evidence Center")

        self.diagnostics = DiagnosticsPanel()
        self.diagnostics.set_registry(registry_summary())
        self.diagnostics.export_requested.connect(self._export_csv)
        inner.addTab(self.diagnostics, "Diagnostics + Data")

        self.timeline_tab = TimelineTab(self.db)
        inner.addTab(self.timeline_tab, "Digital Twin Timeline")

        # Recommendations + alerts log (kept out of the main flow)
        log_tab = QWidget(); lg = QVBoxLayout(log_tab)
        rec_box = QGroupBox("Personalized recommendations")
        rb = QVBoxLayout(rec_box)
        self.recommendations_text = QTextEdit(); self.recommendations_text.setReadOnly(True)
        self.recommendations_text.setPlaceholderText("Explainable recommendations appear here.")
        rb.addWidget(self.recommendations_text)
        lg.addWidget(rec_box, 1)
        alert_box = QGroupBox("Alerts, sensor errors and data-quality warnings")
        ab = QVBoxLayout(alert_box)
        self.alert_text = QTextEdit(); self.alert_text.setReadOnly(True)
        self.alert_text.setPlaceholderText("Alerts, sensor errors, and data-quality warnings appear here.")
        ab.addWidget(self.alert_text)
        lg.addWidget(alert_box, 2)
        inner.addTab(log_tab, "Recommendations + Alerts")

        # Equipment + protocol
        proto_tab = QWidget(); pv = QVBoxLayout(proto_tab)
        txt = QTextEdit(); txt.setReadOnly(True)
        txt.setText(
            "Recommended optional equipment and connections:\n\n"
            "1) GSR sensor: VCC→5V, GND→GND, AO→A0.\n"
            "2) MAX4466 microphone (VoxVasc research proxy): VCC→5V, GND→GND, OUT→A1. Experimental only.\n"
            "3) AD8232 ECG checkpoint: 3.3V→3.3V, GND→GND, OUTPUT→A2, LO+→D11, LO-→D12. Battery-powered laptop only.\n"
            "4) Push buttons: one side→D3/D4/D5, other side→GND, INPUT_PULLUP.\n"
            "5) Optional digital BP monitor: DO NOT wire the cuff to Arduino. Cuff on the UPPER ARM not wearing PPG/GSR. "
            "Sit 5 min, measure, then type SYS and DIA in the top bar or Patient Inputs.\n\n"
            "Safety protocol:\n"
            "• Do not claim diagnosis. This is a research/pre-screening prototype.\n"
            "• Do not do a 75g glucose challenge on visitors. Use normal snack data or pre-recorded/volunteer data with consent.\n"
            "• Avoid finger-prick demonstration unless allowed by school safety rules.\n"
            "• Keep the laptop on battery if using body-connected electrodes.\n"
            "• Any research data collection from humans requires consent, adult/teacher/clinician oversight "
            "and institutional/ethics approval first."
        )
        pv.addWidget(txt)
        inner.addTab(proto_tab, "Equipment + Protocol")

        layout.addWidget(inner, 1)
        self.tabs.addTab(advanced, "10 Advanced / Research Tools")

    # --------------------------------------------------------------- control
    def refresh_ports(self):
        if not hasattr(self, "port_combo"):
            return
        current = self.port_combo.currentText()
        self.port_combo.clear()
        self.port_combo.addItems(ArduinoReader.available_ports())
        if current:
            self.port_combo.setEditText(current)

    def _profile_changed(self):
        height = float(self.height_spin.value()) if self.height_spin.value() > 0 else None
        weight = float(self.weight_spin.value()) if self.weight_spin.value() > 0 else None
        bmi = None
        if height and weight:
            bmi = weight / ((height / 100.0) ** 2)
            self.auto_bmi_label.setText(f"BMI auto from height/weight: {bmi:.1f}")
        else:
            bmi = float(self.bmi_spin.value()) if self.bmi_spin.value() > 0 else None
            self.auto_bmi_label.setText("")
        self.profile = UserProfile(
            age_years=float(self.age_spin.value()),
            bmi=bmi,
            height_cm=height,
            weight_kg=weight,
            waist_cm=float(self.waist_spin.value()) if self.waist_spin.value() > 0 else None,
            systolic_bp=float(self.sys_spin.value()) if self.sys_spin.value() > 0 else None,
            diastolic_bp=float(self.dia_spin.value()) if self.dia_spin.value() > 0 else None,
            cycle_day=int(self.cycle_spin.value()) if self.cycle_spin.value() > 0 else None,
            usual_cycle_length_days=int(self.length_spin.value()) if self.length_spin.value() > 0 else None,
            glucose_mg_dl=float(self.glucose_spin.value()) if self.glucose_spin.value() > 0 else None,
            glucose_context=self.glucose_context.currentText(),
        )
        self.extractor.set_profile(self.profile)

    def _on_patient_inputs_saved(self):
        self.patient_inputs.apply_to_profile(self.profile)
        self.extractor.set_profile(self.profile)
        # Keep the quick top-bar spinboxes in sync with the saved cycle info.
        if self.profile.cycle_day is not None:
            self.cycle_spin.setValue(self.profile.cycle_day)
        if self.profile.usual_cycle_length_days is not None:
            self.length_spin.setValue(self.profile.usual_cycle_length_days)
        self._alert("Patient inputs saved (local store). Cycle information now contributes to the estimate.")

    # ------------------------------------------------------------- sessions
    def _start_session(self, source: str) -> None:
        self._end_session()
        participant = getattr(self, "participant_edit", None)
        pid = participant.text().strip() if participant else ""
        self.session_id = self.db.start_session(source=source, note=source, participant_id=pid or None)
        self._recs_logged = False

    def _end_session(self) -> None:
        if self.session_id is not None:
            try:
                self.db.end_session(self.session_id, sample_count=self.sample_count)
            except Exception:
                pass
            self.session_id = None

    def closeEvent(self, event):  # noqa: N802
        self._end_session()
        super().closeEvent(event)

    def connect_serial(self):
        self.stop_stream()
        port = self.port_combo.currentText().strip()
        if not port:
            self._alert("Choose a serial port first.")
            return
        self._start_session(source=f"serial:{port}")
        self.stream = ArduinoReader(port=port, baud=SERIAL_BAUD, require_crc=True)
        self.stream.sample_received.connect(self._on_sample)
        self.stream.error_received.connect(self._on_error)
        self.stream.state_changed.connect(self._on_state_changed)
        self.led.set_writer(self.stream.write_command)
        self.stream.start()

    def connect_network(self, net: str):
        self.stop_stream()
        if not net:
            self._alert("Enter the ESP8266 bridge address, e.g. 192.168.4.1:7777")
            return
        host, _, port_s = net.partition(":")
        try:
            port = int(port_s) if port_s.isdigit() else WIFI_BRIDGE_DEFAULT_PORT
        except ValueError:
            port = WIFI_BRIDGE_DEFAULT_PORT
        self._start_session(source=f"net:{host}:{port}")
        self.stream = NetworkReader(host=host, port=port)
        self.stream.sample_received.connect(self._on_sample)
        self.stream.error_received.connect(self._on_error)
        self.stream.state_changed.connect(self._on_state_changed)
        self.led.set_writer(self.stream.write_command)
        self.stream.start()

    def start_demo(self):
        self.stop_stream()
        self._start_session(source="demo")
        self.stream = DemoSensorStream()
        self.stream.sample_received.connect(self._on_sample)
        self.stream.error_received.connect(self._on_error)
        self.stream.state_changed.connect(self._on_state_changed)
        self.led.set_writer(self.stream.write_command)
        self.stream.start()
        self._set_mode_badge("demo")
        self._alert("DEMO MODE: synthetic stream for UI testing only. It is excluded from analysis and never a dataset.")

    def stop_stream(self):
        self._end_session()
        if self.replay is not None:
            self.replay.stop()
            self.replay = None
        if self.stream is not None:
            try:
                self.stream.stop()
            except Exception:
                pass
            self.stream = None
        if hasattr(self, "status_label"):
            self._set_status("Stopped")
        self._set_mode_badge("none")
        if hasattr(self, "live_conn_label"):
            self.live_conn_label.setText("Disconnected")

    # --------------------------------------------------------------- updates
    def _on_sample(self, sample: SensorSample):
        self.last_sample = sample
        self.sample_count += 1
        self.extractor.add_sample(sample)
        if self.sample_count % 50 == 0:
            append_row_csv(self.raw_log_path, sample.__dict__)
        if hasattr(self, "packet_count_label"):
            self.packet_count_label.setText(f"Packets: {self.sample_count}")
            self.last_packet_label.setText(f"Last packet: {time.strftime('%H:%M:%S')}")

        # Physical buttons (rising edge only): mode / baseline / post-meal.
        buttons = sample.buttons or 0
        if buttons & 1 and not (self._prev_buttons & 1):
            self._on_mode_button()
        if buttons & 2 and not (self._prev_buttons & 2):
            self._on_baseline_button()
        if buttons & 4 and not (self._prev_buttons & 4):
            self._on_post_meal_button()
        self._prev_buttons = buttons

        if sample.status and sample.status != self._prev_status:
            flags = ", ".join(decode_status_flags(sample.status))
            self._alert("Sensor status: " + flags)
            self.db.log_quality(self.session_id, "warning", "sensor_status", flags)
        self._prev_status = sample.status

    def _update_features_and_ui(self):
        fv = self.extractor.compute()
        self._update_vital_cards(fv)
        self._update_plots(fv)
        self._update_risk(fv)
        self._update_live_conn()
        self.validation_tab.update_live(fv, self.last_result, self.last_sample)
        self.challenge_widget.set_current_feature(fv)
        self.voice_vasc_tab.update_live(fv.mic_pitch_hz, fv.mic_rms)
        self.diagnostics.update_sensors(self.last_sample, fv)
        self._update_baseline_ui()

        # Daily health score + early-warning banner + recommendations.
        scores = compute_scores(fv)
        recs = []
        self.cards["health"].set_value(scores.daily_health_score, decimals=0)
        self.cards["health"].set_color_state(
            "green" if scores.daily_health_score >= 65 else "yellow" if scores.daily_health_score >= 45 else "red")
        if self.last_result is not None:
            wl = warning_level(fv, self.last_result)
            colors = {"ok": GREEN, "watch": YELLOW, "caution": ORANGE, "alarm": RED}
            self.warning_label.setText(f"Early warning: {wl.upper()}")
            self.warning_label.setStyleSheet(f"font-size: 12pt; font-weight: bold; color: {colors.get(wl, GREEN)};")
            recs = generate_recommendations(fv, self.profile, self.last_result)
            self.recommendations_text.setPlainText(
                "\n".join(f"[{r.priority}] {r.text}" for r in recs))
            if self.session_id is not None and recs and not self._recs_logged:
                self._recs_logged = True
                self.db.log_event(self.session_id, "recommendation_issued", recs[0].text)

        # Live what-if simulations (research tab).
        if self.last_result is not None:
            self.whatif.set_current(fv, self.profile, self.last_result)

        # Auto-calibration notice (one time).
        if self.extractor.auto_captured and not self._baseline_notice_shown:
            self._baseline_notice_shown = True
            self._alert("Automatic baseline captured after 5 calm minutes, personalized ranges are now active.")

        # Change detection (throttled: 15 s; needs history depth to be meaningful).
        if time.time() - self._last_change_eval >= 15.0:
            self._last_change_eval = time.time()
            self._update_change_panel()

        # Care-plan dose/appointment reminders (throttled: 30 s, alert once/day).
        self._check_care_reminders()

        # Persist downsampled features + anomalies to the offline database.
        now = fv.timestamp_s
        if self.session_id is not None and now - self._last_feature_log >= FEATURE_LOG_INTERVAL_S:
            self._last_feature_log = now
            extra = json.dumps({
                "autonomic_imbalance": fv.autonomic_imbalance,
                "chronic_stress": fv.chronic_stress,
                "insulin_resistance_probability": fv.insulin_resistance_probability,
                "metabolic_syndrome_proxy": fv.metabolic_syndrome_proxy,
                "circadian_disruption": fv.circadian_disruption,
                "temperature_rhythm_disruption": fv.temperature_rhythm_disruption,
                "low_activity_risk": fv.low_activity_risk,
                "health_score": scores.daily_health_score,
                "light_exposure": fv.lux if fv.lux is not None else None,
                "anomaly_score": fv.anomaly_score,
            })
            self.db.log_feature(self.session_id, {
                "ts": fv.timestamp_s,
                "hr": fv.hr_bpm,
                "rmssd": fv.rmssd_ms,
                "spo2": fv.spo2_pct,
                "skin_temp": fv.skin_temp_c,
                "gsr": fv.gsr_tonic,
                "motion": fv.motion_index,
                "activity": fv.activity_level,
                "stress": fv.stress_index,
                "sleep_prob": fv.sleep_probability,
                "circadian": fv.circadian_stability_index,
                "risk": self.last_result.risk_percent if self.last_result else None,
                "anomaly": fv.anomaly_score,
                "signal_quality": fv.signal_quality,
            }, extra_json=extra)
        if self.session_id is not None:
            for a in self.extractor.last_anomalies:
                self.db.log_anomaly(self.session_id, fv.timestamp_s, a)
            self.extractor.last_anomalies = []

        self._refresh_diagnostics_logs()

        # Keep the AI assistant's context fresh.
        self.assistant_tab.refresh_context(
            fv,
            self.profile,
            self.last_result,
            baseline=self.extractor.baseline,
            anomalies=self.extractor.last_anomalies,
            recs=recs,
            live_mode=self._live_mode(),
        )

    def _live_mode(self) -> str:
        if self.replay is not None:
            return "replay"
        if self.stream is None:
            return "none"
        return "demo" if isinstance(self.stream, DemoSensorStream) else "live"

    def _update_live_conn(self):
        mode = self._live_mode()
        if mode == "live":
            self.live_conn_label.setText("Connected (live)")
        elif mode == "demo":
            self.live_conn_label.setText("DEMO MODE (synthetic)")
        elif mode == "replay":
            self.live_conn_label.setText("Replaying recorded data")
        else:
            self.live_conn_label.setText("Disconnected")
        self._set_mode_badge(mode)
        self._update_coverage_label(mode)

    def _update_coverage_label(self, mode: str):
        # Coverage counts REAL (non-demo) longitudinal days only.
        days = self.db.coverage_days(days=90, include_demo=False)
        suffix = ""
        if mode in ("demo", "replay"):
            suffix = " (demo/replay data excluded)"
        for label in [self.coverage_label]:
            if days > 0:
                label.setText(f"Longitudinal coverage: {days} days{suffix}")
            else:
                label.setText(f"Longitudinal coverage: 0 days{suffix}, connect live wearable for real data")

    def _update_vital_cards(self, fv: FeatureVector):
        self.cards["hr"].set_value(fv.hr_bpm, decimals=0)
        self.cards["hrv"].set_value(fv.rmssd_ms, decimals=1)
        self.cards["temp"].set_value(fv.skin_temp_c, decimals=2)
        self.cards["activity"].set_value(fv.activity_level, decimals=0)
        self.cards["gsr"].set_value(fv.gsr_tonic, decimals=0)
        self.cards["stress"].set_value(fv.stress_index, decimals=0)
        self.cards["sleep"].set_value(fv.sleep_status, f"P={fv.sleep_probability:.0f}%")
        self.cards["quality"].set_value(fv.signal_quality * 100.0, decimals=0)

        self.cards["stress"].set_color_state("red" if fv.stress_index > 70 else "yellow" if fv.stress_index > 45 else "green")
        self.cards["sleep"].set_color_state("blue" if fv.sleep_status == "sleep" else "gray")
        self.cards["quality"].set_color_state("green" if fv.signal_quality > 0.7 else "yellow" if fv.signal_quality > 0.4 else "red")

        # Dedicated live-tab cards.
        self.live_cards["hr"].set_value(fv.hr_bpm, decimals=0)
        self.live_cards["hrv"].set_value(fv.rmssd_ms, decimals=1)
        self.live_cards["temp"].set_value(fv.skin_temp_c, decimals=2)
        self.live_cards["activity"].set_value(fv.activity_level, decimals=0)
        self.live_cards["gsr"].set_value(fv.gsr_tonic, decimals=0)
        self.live_cards["quality"].set_value(fv.signal_quality * 100.0, decimals=0)
        self.live_cards["quality"].set_color_state("green" if fv.signal_quality > 0.7 else "yellow" if fv.signal_quality > 0.4 else "red")

    def _update_plots(self, fv: FeatureVector):
        x, y = self.extractor.ppg_waveform(last_s=20)
        self.ppg_plot.set_data(x, y)
        for attr, plot in [
            ("hr_bpm", self.hr_plot),
            ("rmssd_ms", self.hrv_plot),
            ("skin_temp_c", self.temp_plot),
        ]:
            px, py = self.extractor.history_arrays(attr, last_s=180)
            plot.set_data(px, py)
        self.sleep_view.add(fv.timestamp_s, fv.sleep_probability, fv.deep_sleep_probability, fv.rem_probability)
        self.clock.set_values(fv.circadian_stability_index, fv.sleep_probability)

    def _update_risk(self, fv: FeatureVector):
        # V6: the headline score uses defensible domains only. Hormone estimates
        # are computed for the research illustration tab and NEVER enter the score.
        phase = self.hormones.phase(self.profile)
        hormone_est = self.hormones.estimate(fv, self.profile)
        result = self.risk_engine.estimate(fv, hormones=hormone_est, phase=phase, profile=self.profile)
        self.last_result = result
        decision = should_withhold(fv, result)
        self.last_decision = decision

        self.risk_gauge.set_value(result.risk_percent, result.ci_low, result.ci_high)
        self.risk_gauge.set_withheld(None if decision.ok else (decision.reasons[0] if decision.reasons else "insufficient data"))
        withheld_text = "PREDICTION WITHHELD, " + (decision.reasons[0].upper() if decision.reasons else "INSUFFICIENT SIGNAL QUALITY")
        self.withheld_banner.setVisible(not decision.ok)
        self.withheld_banner.setText(withheld_text)
        self.live_withheld_banner.setVisible(not decision.ok)
        self.live_withheld_banner.setText(withheld_text)

        conf = result.confidence
        self.confidence_label.setText(f"Confidence: {conf:.0f}%, {'HIGH' if conf >= 66 else 'MODERATE' if conf >= 33 else 'LOW'}")
        self.quality_label.setText(f"Data quality: {fv.signal_quality * 100.0:.0f}/100")
        self._update_coverage_label(self._live_mode())

        # PCOS Analysis tab summary.
        self.analysis_risk_label.setText(f"{result.risk_percent:.0f}%" if decision.ok else "WITHHELD")
        self.analysis_meta_label.setText(
            f"Confidence: {conf:.0f}% · Data quality: {fv.signal_quality * 100.0:.0f}/100 · "
            f"Coverage: {self.db.coverage_days(days=90, include_demo=False)} days")
        self.analysis_reason_label.setText(
            result.explanation if decision.ok else
            ("Prediction withheld: " + "; ".join(decision.reasons)))

        # Model-input status grid.
        self.input_status["wearable"].setText("active" if fv.hr_bpm is not None else "no PPG data yet")
        self.input_status["longitudinal"].setText("personal baseline active" if fv.baseline_available else "collecting (5 min)")
        has_cycle = (self.profile.usual_cycle_length_days is not None
                     or self.profile.days_since_last_period is not None
                     or self.profile.cycle_irregular is not None)
        self.input_status["cycle"].setText("entered" if has_cycle else "not entered (optional)")
        self.input_status["symptoms"].setText("see Patient Inputs tab")
        has_metabolic = bool(self.profile.systolic_bp or self.profile.diastolic_bp or self.profile.glucose_mg_dl)
        self.input_status["metabolic"].setText("BP/glucose entered" if has_metabolic else "not entered (optional)")
        self.input_status["ecg"].setText(f"quality {fv.ecg_quality * 100.0:.0f}%" if fv.ecg_quality > 0 else "not connected (optional)")
        us_hist = self.db.ultrasound_history(limit=1) or self.db.ultrasound_images(limit=1)
        self.input_status["ultrasound"].setText(
            "examination recorded" if us_hist else "not entered (periodic, optional)")

        # Contributors (WHY DID THE ESTIMATE CHANGE?) + explanation.
        lines = []
        for label, score, _key in result.contributions[:5]:
            arrow = "▲" if score > 0 else "-"
            lines.append(f"{arrow} {label}: {score:.1f}")
        self.contributors_text.setPlainText("\n".join(lines) if lines else result.explanation)
        self.explanation.update_result(result)

        self.radar.set_scores(result.domain_scores)
        self.digital_twin.set_state(
            result.risk_percent,
            result.domain_scores.get("metabolic", 0),
            result.domain_scores.get("cycle", 0),
            result.domain_scores.get("stress_autonomic", 0),
        )
        self.led.set_risk_state(result.risk_percent, result.confidence)

        # Risk trend (live history only, demo data is excluded from analysis).
        if self._live_mode() == "live":
            self.risk_history.append((fv.timestamp_s, result.risk_percent))
        elif len(self.risk_history) < 2:
            pass
        if self.risk_history:
            t0 = self.risk_history[0][0]
            tx = [t - t0 for t, _ in self.risk_history]
            ty = [r for _, r in self.risk_history]
            self.risk_trend_plot.set_data(tx, ty)

        # Buzzer alerts: high-risk entry or strong anomaly.
        if self._prev_risk is not None:
            if result.risk_percent >= 75 and self._prev_risk < 75:
                self.led.beep()
            elif fv.anomaly_score >= 60 and self._prev_anomaly < 60:
                self.led.beep()
        self._prev_risk = result.risk_percent
        self._prev_anomaly = fv.anomaly_score
        if result.confidence < 35:
            self._alert("Low confidence: collect longer baseline, improve PPG contact, and add real cycle/symptom data.")

    def _update_change_panel(self):
        """Wire the (previously orphaned) ChangeDetector into the UI."""
        features = list(self.extractor.feature_history)
        report = self.change_detector.evaluate(features)
        bm = self.extractor.baseline
        if bm.has_baseline:
            when = time.strftime("%H:%M", time.localtime(bm.baseline.captured_at))
            self.long_baseline_label.setText(
                f"Personal baseline active (captured {when}, {bm.baseline.duration_s:.0f}s, "
                f"quality {bm.baseline.quality:.2f}). Change analysis compares against YOUR ranges.")
        else:
            self.long_baseline_label.setText(
                "Personal baseline: not captured yet (5 calm minutes needed). Change analysis uses "
                "the earliest stable part of the current session as reference.")

        if report.n_windows == 0:
            return
        kind = report.overall_kind
        kind_colors = {"normal": GREEN, "deviation": ORANGE, "insufficient_quality": YELLOW}
        color = kind_colors.get(kind, TEXT_MUTED)
        self.change_summary_label.setText(f"Change state: {kind.upper()}, {report.summary}")
        self.change_summary_label.setStyleSheet(f"color: {color}; font-size: 12pt; font-weight: bold;")
        parts = [f"Window: {report.n_windows} feature points · mean signal quality {report.data_quality * 100.0:.0f}%"]
        for key in sorted(report.per_metric):
            mc = report.per_metric[key]
            parts.append("• " + mc.phrase())
        if report.contributors:
            parts.append("Moving metrics: " + ", ".join(report.contributors))
        self.change_details.setPlainText("\n".join(parts))

        # V6.2: personal physiological fingerprint + WHAT CHANGED summaries.
        self._update_fingerprint_and_what_changed(features, report)

    def _update_fingerprint_and_what_changed(self, features, change_report):
        """Fingerprint + WHAT CHANGED summaries fed from the change report."""
        finger = self.fingerprint_engine.compute(features)
        self.fingerprint_widget.set_report(finger)

        from src.models.what_changed import WhatChangedEngine

        wc = WhatChangedEngine(self.db).compute(
            change=change_report,
            profile=self.profile,
            current=self.last_result,
            previous_risk=self._previous_assessment_risk(),
            adherence=self.care.adherence_summary(days=60),
        )
        self.what_changed_overview.setPlainText(
            wc.plain_text() if wc else "No meaningful changes detected in the available window.")

        participant = getattr(self, "participant_edit", None)
        pid = participant.text().strip() if participant else "anonymous"
        self.clinical_tab.set_current_result(self.last_result)
        self.clinical_tab.set_current(
            change=change_report,
            risk=self.last_result.risk_percent if self.last_result else None,
            confidence=self.last_result.confidence if self.last_result else None,
            profile=self.profile,
            participant=pid,
            coverage_days=self.db.coverage_days(days=90, include_demo=False),
            data_quality=(features[-1].signal_quality if features else 0.0) or 0.0,
            monitoring_days=self._monitoring_days(),
        )
        # V8.1: keep the ultrasound/fusion tab in sync with live context.
        self.ultrasound_tab.set_current(
            profile=self.profile,
            risk=self.last_result.risk_percent if self.last_result else None,
            change=change_report,
            fingerprint=finger,
        )

    def _previous_assessment_risk(self) -> float | None:
        evs = self.db.events(kind="recommendation_issued", limit=1)
        if evs:
            return self.db.risk_at_time(evs[0]["ts"])
        reports = self.clinical.reports()
        if len(reports) >= 2:
            return self.db.risk_at_time(reports[1]["ts"])
        return None

    def _monitoring_days(self) -> float | None:
        sessions = self.db.session_summary(limit=1)
        if sessions:
            return max(1.0, (time.time() - sessions[0]["started_at"]) / 86400.0)
        return None

    def _report_metrics(self) -> dict:
        """Current periodic-report metrics for the Clinical tab's 'save report'."""
        profile = self.multi_day.build_profile(days=7, trajectory_days=30,
                                               include_demo=self._live_mode() == "demo")
        out = {}
        if profile.days:
            latest = profile.days[-1].as_dict()
            for k in ["mean_hr", "resting_hr", "rmssd", "temp_amp", "activity",
                      "night_sleep", "circadian", "stress", "risk", "health"]:
                v = latest.get(k)
                if v is not None:
                    out[k] = float(v)
        if self.last_result is not None:
            out["risk"] = self.last_result.risk_percent
            out["confidence"] = self.last_result.confidence
        return out

    def _check_care_reminders(self):
        """Alert once per (med/appointment, day) about due dose slots."""
        if time.time() - self._last_care_check < 30.0:
            return
        self._last_care_check = time.time()
        today = time.strftime("%Y-%m-%d")
        for m in self.care.due_medications():
            key = f"med-{m['medication_id']}-{today}"
            if key not in self._reminder_alerted:
                self._reminder_alerted.add(key)
                self._alert(f"Care plan reminder (bookkeeping only): {m['name']} {m['dose']} {m['unit']} "
                            f"dose slot not yet logged today.")
        for a in self.care.due_appointments():
            key = f"appt-{a['id']}-{today}"
            if key not in self._reminder_alerted:
                self._reminder_alerted.add(key)
                import datetime as _dt

                due = _dt.date.fromtimestamp(a["due_ts"]).isoformat()
                self._alert(f"Upcoming reminder: {a.get('kind', 'appointment').title()} "
                            f"({a.get('note') or 'see care plan'}) due {due}.")
        self.care_tab.refresh()

    def _on_care_data_changed(self):
        self.clinical_tab.refresh()
        self._alert("Care plan / adherence record updated (local store).")

    def _update_circadian_from_history(self):
        metrics = self.circadian.analyze(self.extractor.feature_history)
        self.extractor.circadian_metrics = metrics
        if self.extractor.last_feature is not None:
            self.extractor.last_feature.circadian_stability_index = metrics.stability_index
            self.extractor.last_feature.circadian_disruption = metrics.disruption_score
            if metrics.temp_r2 > 0:
                self.extractor.last_feature.temperature_rhythm_disruption = max(0.0, min(100.0, 100.0 - 100.0 * metrics.temp_r2))
        self.history_tab.refresh(self.multi_day.build_profile(days=7, trajectory_days=30, include_demo=self._live_mode() == "demo"))
        self.history_tab.set_sessions(self.db.session_compare(limit=15))
        if self.last_result is not None:
            evs = self.db.events(kind="recommendation_issued", limit=1)
            if evs:
                old_risk = self.db.risk_at_time(evs[0]["ts"])
                if old_risk is not None:
                    self.history_tab.set_before_after(old_risk, self.last_result.risk_percent, evs[0]["ts"])

    def _refresh_diagnostics_logs(self):
        if time.time() - self._last_logs_refresh < 30.0:
            return
        self._last_logs_refresh = time.time()
        self.diagnostics.set_quality_log(self.db.quality_log(limit=100))
        self.diagnostics.set_error_log(self.db.error_log(limit=100))
        self.diagnostics.set_calibrations(self.db.calibration_history(limit=20))

    def _set_status(self, text: str, state: str = "gray"):
        """Update the header connection pill with a semantic color."""
        color = {
            "green": GREEN, "yellow": YELLOW, "orange": ORANGE, "red": RED,
            "blue": ACCENT_STRONG, "gray": TEXT_MUTED,
        }.get(state, TEXT_MUTED)
        self.status_label.setText(text)
        self.status_label.setStyleSheet(
            f"QLabel {{ background: {color}22; border: 1px solid {color}; color: {color}; "
            f"font-size: 10.5pt; font-weight: bold; padding: 5px 14px; border-radius: 12px; }}"
        )

    def _on_state_changed(self, text: str):
        if text.startswith("connected:"):
            self._set_status("Connected, " + text[len("connected:"):], "green")
            self._set_mode_badge("live")
        elif text == "reconnecting":
            self._set_status("Reconnecting…", "orange")
        elif text == "demo-running":
            self._set_status("Demo mode (synthetic) running", "blue")
            self._set_mode_badge("demo")
        elif text == "demo-stopped":
            self._set_status("Demo stopped")
            self._set_mode_badge("none")
        elif text == "stopped":
            self._set_status("Stopped")
            self._set_mode_badge("none")
        else:
            self._set_status(text)

    def _alert(self, text: str):
        if not hasattr(self, "alert_text"):
            return
        timestamp = time.strftime("%H:%M:%S")
        self.alert_text.append(f"[{timestamp}] {text}")
        if text != self._last_alert_logged:
            self._last_alert_logged = text
            if any(k in text.lower() for k in ("error", "failed", "unreachable", "lost", "problem", "could not")):
                try:
                    self.db.log_error(self.session_id, "error", text)
                except Exception:
                    pass

    def _on_error(self, text: str):
        self.db.log_error(self.session_id, "error", text)
        self._alert(text)

    # ------------------------------------------------- baseline / buttons
    def _capture_baseline(self):
        ok = self.extractor.capture_baseline()
        if ok:
            bl = self.extractor.baseline.baseline
            stats_json = json.dumps({k: v.to_dict() for k, v in bl.stats.items()})
            self.db.log_calibration(bl.duration_s, bl.quality, stats_json)
            self._alert("Personal baseline captured, personalized normal ranges are now active.")
            self.led.beep()
        else:
            self._alert(f"Baseline capture failed: {self.extractor.last_capture_error}")
        self._update_baseline_ui()

    def _update_baseline_ui(self):
        bm = self.extractor.baseline
        if not hasattr(self, "baseline_status"):
            return
        if bm.has_baseline:
            when = time.strftime("%H:%M", time.localtime(bm.baseline.captured_at))
            self.baseline_status.setText(
                f"Personal baseline active (captured {when}, {bm.baseline.duration_s:.0f}s, "
                f"quality {bm.baseline.quality:.2f}). Live signals are compared against your own ranges.")
            parts = []
            for metric, label in [("hr_bpm", "HR"), ("rmssd_ms", "RMSSD"), ("skin_temp_c", "Temp"), ("gsr_tonic", "GSR")]:
                rng = bm.normal_range(metric)
                if rng is not None:
                    parts.append(f"{label} {rng[0]:.1f}-{rng[1]:.1f}")
            self.ranges_label.setText("Personalized normal ranges: " + "; ".join(parts) if parts else "Personalized normal ranges: --")
            self.capture_btn.setText("Re-capture baseline (5 min)")
        else:
            self.baseline_status.setText("No baseline yet, sit still for 5 minutes, then press the button (or the physical BASELINE button).")
            self.ranges_label.setText("Using population defaults until baseline is captured.")
            self.capture_btn.setText("Capture baseline (5 min)")

    def _on_mode_button(self):
        modes = ["rest", "stress", "activity"]
        idx = (modes.index(self._measurement_mode) + 1) % len(modes) if self._measurement_mode in modes else 0
        self._measurement_mode = modes[idx]
        self.db.log_event(self.session_id, "mode_button", self._measurement_mode)
        self.led.beep()
        self._alert(f"Mode button pressed: measurement mode set to '{self._measurement_mode}' (logged for future model training).")

    def _on_baseline_button(self):
        self.db.log_event(self.session_id, "baseline_button", "pressed")
        self._capture_baseline()

    def _on_post_meal_button(self):
        self.profile.time_since_meal_min = 0.0
        self.db.log_event(self.session_id, "post_meal", "time_since_meal reset to 0")
        self.led.beep()
        self._alert("Post-meal/event button pressed: glucose context reset (marker logged for future model training).")

    def _sleep_window_changed(self):
        onset = self.sleep_onset_edit.time().hour() + self.sleep_onset_edit.time().minute() / 60.0
        wake = self.wake_edit.time().hour() + self.wake_edit.time().minute() / 60.0
        self.extractor.set_sleep_window(onset, wake)
        self.db.log_event(self.session_id, "sleep_window", f"onset {onset:.1f}h, wake {wake:.1f}h")

    # --------------------------------------------- what-if / demo / replay
    def _on_simulation_ran(self, detail: str):
        self.db.log_event(self.session_id, "whatif", detail)

    def _fill_calm_history(self, seconds: int = 300) -> None:
        """Fill the extractor history with a synthetic calm 5-minute window (demo only)."""
        import numpy as np

        from src.data_models import FeatureVector as _FV

        now = time.time()
        rows = []
        for i in range(seconds):
            rows.append(_FV(
                timestamp_s=now - seconds + i,
                hr_bpm=float(72 + np.random.normal(0, 2)),
                rmssd_ms=float(42 + np.random.normal(0, 4)),
                skin_temp_c=32.5,
                gsr_tonic=float(450 + np.random.normal(0, 18)),
                activity_level=8.0,
                motion_index=0.04,
                signal_quality=0.85,
            ))
        self.extractor.feature_history.extend(rows)

    def _judge_demo(self):
        """Judge Mode: 60-second guided demonstration on clearly-labeled synthetic data."""
        self.stop_stream()
        self._start_session(source="demo")
        self._fill_calm_history()
        ok = self.extractor.capture_baseline()
        self._update_baseline_ui()
        sid, n = generate_week(self.db, days=7, patient=1, participant="judge-demo")
        self.history_tab.refresh(self.multi_day.build_profile(days=7, trajectory_days=30, include_demo=True))
        self.history_tab.set_sessions(self.db.session_compare(limit=15))
        self._seed_demo_clinical()
        self.clinical_tab.refresh()
        self._set_mode_badge("demo")
        self.tabs.setCurrentIndex(0)
        self._alert(f"Judge demo ready: baseline {'captured' if ok else 'failed'}; "
                    f"{n} DEMONSTRATION rows loaded (synthetic, not a medical result, session #{sid}). "
                    "See Overview → Longitudinal → PCOS Analysis → Clinical Dashboard for the flow.")

    def _seed_demo_clinical(self):
        """Demo-only clinical record: clearly-labelled synthetic visits/reports."""
        import datetime as _dt

        def _days_ago(d: int) -> float:
            return time.time() - d * 86400.0

        # Synthetic care plan (DEMO only, bookkeeping illustration).
        mid = self.care.add_medication("Metformin (DEMO plan)", dose="500", unit="mg",
                                       cadence="twice_daily", time_of_day="evening",
                                       food_instruction="after food", start_days_ago=40)
        self.care.log_taken(mid); self.care.log_taken(mid)
        self.care.log_skipped(mid)
        self.care.add_goal("4 activity sessions / week (DEMO goal)", kind="activity")
        self.care.add_appointment(kind="test", due_in_days=5, note="Repeat HbA1c + ultrasound (DEMO)")

        # Synthetic visits, notes and ultrasound (DEMO only).
        self.clinical.add_visit("Initial assessment (DEMO, synthetic)", clinician="demo")
        self.clinical.add_note("Synthetic demo record; not a real patient.", clinician="demo")
        self.clinical.add_ultrasound(cyst_size_mm=18.0, volume_cc=3.1,
                                     morphology="simple cyst (DEMO)", source="clinical",
                                     summary="Synthetic demo ultrasound observation")
        # One saved periodic report from '4 weeks ago' with metrics.
        profile = self.multi_day.build_profile(days=7, trajectory_days=30, include_demo=True)
        metrics = {"risk": 41.0, "mean_hr": 74.0, "rmssd": 38.0, "activity": 28.0, "stress": 42.0}
        self.clinical.save_report(
            "periodic", "judge-demo",
            "CHRONO-PCOS periodic report (DEMO, synthetic, 4 weeks ago). Not a medical document.",
            metrics)
        self.db.log_event(None, "demo_clinical", "seeded demo visits/reports/ultrasound/care-plan")

    def _load_demo_week(self):
        sid, n = generate_week(self.db, days=7, patient=0, participant="demo-week")
        self.history_tab.refresh(self.multi_day.build_profile(days=7, trajectory_days=30, include_demo=True))
        self.history_tab.set_sessions(self.db.session_compare(limit=15))
        self._alert(f"Loaded {n} DEMONSTRATION rows (session #{sid}). Synthetic, excluded from real analysis.")

    def _replay_latest(self):
        sessions = self.db.session_compare(limit=1)
        if not sessions:
            self._alert("No sessions in the database to replay.")
            return
        sid = sessions[0]["id"]
        df = self.db.features_for_session(sid)
        feats = features_from_frame(df)
        if not feats:
            self._alert(f"Session #{sid} has no recorded features to replay.")
            return
        if self.replay is not None:
            self.replay.stop()
        self.replay = FeatureReplay(feats, interval_ms=120)
        self.replay.step.connect(self._on_replay_step)
        self.replay.finished.connect(self._on_replay_finished)
        self.replay.start()
        self._set_status(f"Replaying session #{sid} (recorded data)", "blue")
        self._set_mode_badge("replay")
        self._alert(f"Replaying recorded session #{sid} on the live dashboard.")

    def _on_replay_step(self, fv):
        self.extractor.last_feature = fv
        self.extractor.feature_history.append(fv)
        self._update_vital_cards(fv)
        self._update_plots(fv)
        self._update_risk(fv)

    def _on_replay_finished(self):
        self.replay = None
        self._set_status("Replay finished")
        self._set_mode_badge("none")

    # ----------------------------------------------------------- reports
    def _current_report_args(self):
        profile = self.multi_day.build_profile(days=7, trajectory_days=30, include_demo=self._live_mode() == "demo")
        participant = getattr(self, "participant_edit", None)
        pid = participant.text().strip() if participant else "anonymous"
        rec_lines = [self.recommendations_text.toPlainText()] if hasattr(self, "recommendations_text") else []
        recs = [l for l in (rec_lines[0].splitlines() if rec_lines and rec_lines[0] else [])]
        return profile, pid, recs

    def _weekly_report_text(self):
        profile, pid, recs = self._current_report_args()
        default = DATA_DIR / "exports" / f"weekly_report_{time.strftime('%Y%m%d')}.txt"
        path, _ = QFileDialog.getSaveFileName(self, "Save weekly report", str(default), "Text (*.txt);;Markdown (*.md)")
        if not path:
            return
        try:
            text = weekly_report_text(profile, pid, recs)
            Path(path).write_text(text, encoding="utf-8")
            self._alert(f"Weekly report saved to {path}")
        except Exception as exc:
            self._alert(f"Report save failed: {exc}")

    def _weekly_report_pdf(self):
        profile, pid, recs = self._current_report_args()
        default = DATA_DIR / "exports" / f"weekly_report_{time.strftime('%Y%m%d')}.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Save weekly report PDF", str(default), "PDF (*.pdf)")
        if not path:
            return
        ok = write_pdf_report(path, profile, pid, recs)
        self._alert(f"PDF report {'saved' if ok else 'failed'} to {path}")

    def _export_json(self):
        default_dir = DATA_DIR / "exports"
        default_dir.mkdir(parents=True, exist_ok=True)
        default_path = default_dir / f"features_{time.strftime('%Y%m%d_%H%M%S')}.json"
        path, _ = QFileDialog.getSaveFileName(self, "Export features to JSON", str(default_path), "JSON (*.json)")
        if not path:
            return
        try:
            df = self.db.features_as_frame(days=30, include_demo=False)
            df.to_json(path, orient="records", indent=1)
            self._alert(f"Exported {len(df)} feature rows to {path}")
        except Exception as exc:
            self._alert(f"JSON export failed: {exc}")

    def _open_calibration_wizard(self):
        dlg = CalibrationWizard(self, on_live=self._capture_baseline, on_simulate=self._simulate_calibration)
        dlg.exec()

    def _simulate_calibration(self):
        self._fill_calm_history()
        ok = self.extractor.capture_baseline()
        self._update_baseline_ui()
        self._alert(f"Simulated calibration {'captured' if ok else 'failed'} (demo data only).")

    def _export_csv(self):
        default_dir = DATA_DIR / "exports"
        default_dir.mkdir(parents=True, exist_ok=True)
        default_path = default_dir / f"features_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Export features to CSV", str(default_path), "CSV (*.csv)")
        if not path:
            return
        try:
            n = self.db.export_features_csv(path, days=30, include_demo=False)
            self._alert(f"Exported {n} feature rows to {path}")
        except Exception as exc:
            self._alert(f"CSV export failed: {exc}")
