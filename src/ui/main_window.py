"""Main Window for CHRONO-TWIN NEXUS V8.3.

Dashboard sections:
- Overview: personal physiological status
- Baseline: what is normal for user
- Trends: changes over time
- Health Signals: PCOS, Sleep, Cardiometabolic, Autonomic
- Data Quality: sensor status and confidence
- Clinical Inputs: manual clinical measurements
- Ultrasound: image and structured features
- Explanation: why system generated signal
- Report: research report

Keeps V8.1 wearable pod and mega hub working.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from collections import deque

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QGroupBox, QGridLayout, QTextEdit,
    QDoubleSpinBox, QSpinBox, QComboBox, QScrollArea, QFrame,
    QLineEdit, QProgressBar, QSplitter, QFileDialog, QCheckBox
)

from src.config import APP_VERSION, APP_VERSION_LABEL, APP_NAME, APP_TAGLINE, UserProfile, DATA_DIR
from src.data_models import FeatureVector, SensorSample, SharedPhysiologicalFeatures
from src.core.personal_baseline import PersonalBaselineEngine
from src.core.adaptive_learning import AdaptiveWearableModel
from src.core.longitudinal_engine import LongitudinalEngine
from src.core.feature_extraction import RealtimeFeatureExtractor
from src.core.shared_features import SharedFeatureExtractor
from src.core.quality_control import SensorQualityControl
from src.disease_modules.registry import GLOBAL_REGISTRY
from src.fusion.multimodal_fusion import FusionEngine
from src.explainability.explanation_engine import ExplanationEngine
from src.serial_io.arduino_reader import ArduinoReader
from src.serial_io.network_reader import NetworkReader
from src.ui.theme import (DARK_QSS, ACCENT_STRONG, GREEN, ORANGE, RED,
                          YELLOW, TEXT_MUTED, TEXT)
from src.ui.gauges import GaugeWidget
from src.ui.vital_cards import VitalCard
from src.ui.live_plots import TimeSeriesPlot
from src.ui.learning_panel import LearningStatusPanel
from src.utils.demo_stream import DemoSensorStream
from src.utils.history_store import HistoryStore
from src.utils.synthetic import generate_subject_timeline, SyntheticSubjectProfile
from src.utils.public_study import PublicStudyManager

DISCLAIMER = "Research prototype, NOT a diagnosis. Clinical evaluation required."


class MainWindow(QMainWindow):
    def __init__(self, start_demo: bool = False, port: str | None = None, net: str | None = None, db_path=None):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} - {APP_VERSION_LABEL}")
        self.resize(1600, 1000)
        self.setStyleSheet(DARK_QSS)

        # Core engines
        self.profile = UserProfile()
        self.baseline_engine = PersonalBaselineEngine()
        # One continually-learning model per wearer. Its state lives in
        # data/adaptive/<id>/ and is resumed on the next launch.
        self.adaptive_model = AdaptiveWearableModel("local-workspace")
        self.longitudinal_engine = LongitudinalEngine(baseline=self.baseline_engine)
        self.extractor = RealtimeFeatureExtractor(profile=self.profile, baseline_engine=self.baseline_engine,
                                                  learner=self.adaptive_model)
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
        self.public_study = PublicStudyManager(self.history_store)
        self.public_study.attach_latest()
        self._last_public_study_log = 0.0

        # Timers
        self.feature_timer = QTimer()
        self.feature_timer.timeout.connect(self._update_features)
        self.feature_timer.start(1000)

        self.risk_timer = QTimer()
        self.risk_timer.timeout.connect(self._update_risk)
        self.risk_timer.start(2000)

        # Unified ENDO-TWIN scientific workstation shell.
        central = QWidget()
        self.setCentralWidget(central)
        shell = QVBoxLayout(central)
        shell.setContentsMargins(14, 14, 14, 14)
        shell.setSpacing(10)

        topbar = QFrame()
        topbar.setObjectName("WorkstationTopbar")
        top = QHBoxLayout(topbar)
        top.setContentsMargins(16, 12, 16, 12)
        brand = QVBoxLayout()
        title = QLabel("ENDO-TWIN NEXUS")
        title.setObjectName("AppTitle")
        subtitle = QLabel("UNIFIED SCIENTIFIC WORKSTATION  •  Sense  •  Model  •  Predict  •  Personalize")
        subtitle.setObjectName("AppSubtitle")
        brand.addWidget(title)
        brand.addWidget(subtitle)
        top.addLayout(brand)
        top.addStretch()
        self.top_mode = QLabel("●  NO STREAM")
        self.top_mode.setObjectName("StatusPill")
        self.top_quality = QLabel("QUALITY  —")
        self.top_quality.setObjectName("StatusPill")
        self.top_baseline = QLabel("BASELINE  •  1 HOUR")
        self.top_baseline.setObjectName("StatusPill")
        self.top_patient = QLabel("NO PATIENT")
        self.top_patient.setObjectName("StatusPill")
        for pill in (self.top_mode, self.top_quality, self.top_baseline, self.top_patient):
            top.addWidget(pill)
        shell.addWidget(topbar)

        workspace = QHBoxLayout()
        workspace.setSpacing(10)

        sidebar = QFrame()
        sidebar.setObjectName("WorkstationSidebar")
        sidebar.setFixedWidth(218)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(10, 12, 10, 12)
        nav.setSpacing(5)

        nav_brand = QLabel("RESEARCH CONTROL")
        nav_brand.setObjectName("SidebarEyebrow")
        nav.addWidget(nav_brand)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().hide()
        pages = [
            ("⌂", "Command Center"),
            ("◉", "Personal Baseline"),
            ("∿", "Trends & Analysis"),
            ("✦", "CHRONO-PCOS / Signals"),
            ("◌", "Data Quality"),
            ("＋", "Clinical Inputs"),
            ("▣", "Ultrasound"),
            ("◇", "AI Explainability"),
            ("▤", "Research Reports"),
            ("✓", "Validation"),
            ("◫", "Participant Study"),
        ]
        self._nav_buttons = []
        for idx, (icon, label) in enumerate(pages):
            btn = QPushButton(f"{icon}   {label}")
            btn.setObjectName("WorkstationNav")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, i=idx: self._select_workstation_page(i))
            nav.addWidget(btn)
            self._nav_buttons.append(btn)
        nav.addStretch()

        nav_note = QLabel("RESEARCH PROTOTYPE\nNot a diagnostic device")
        nav_note.setObjectName("SidebarNote")
        nav_note.setWordWrap(True)
        nav.addWidget(nav_note)
        workspace.addWidget(sidebar)

        self.tabs.addTab(self._build_overview_tab(), "Dashboard")
        self.tabs.addTab(self._build_baseline_tab(), "Baseline")
        self.tabs.addTab(self._build_trends_tab(), "Trends & Analysis")
        self.tabs.addTab(self._build_health_signals_tab(), "Health Signals")
        self.tabs.addTab(self._build_data_quality_tab(), "Data Quality")
        self.tabs.addTab(self._build_clinical_tab(), "Clinical Inputs")
        self.tabs.addTab(self._build_ultrasound_tab(), "Ultrasound")
        self.tabs.addTab(self._build_explanation_tab(), "AI Insights")
        self.tabs.addTab(self._build_report_tab(), "Reports")
        self.tabs.addTab(self._build_validation_tab(), "Validation")
        self.tabs.addTab(self._build_public_study_tab(), "3-Day Study")
        workspace.addWidget(self.tabs, 1)
        shell.addLayout(workspace, 1)

        self.status_label = QLabel(f"{APP_NAME} • {APP_VERSION_LABEL} • {DISCLAIMER}")
        self.status_label.setObjectName("SmallMuted")
        shell.addWidget(self.status_label)
        self._select_workstation_page(0)

        if start_demo:
            self.start_demo()
        if port:
            self.connect_serial(port)
        if net:
            self.connect_network(net)

    def _named_label(self, text: str, object_name: str):
        label = QLabel(text)
        label.setObjectName(object_name)
        return label

    def _select_workstation_page(self, index: int):
        if not hasattr(self, "tabs"):
            return
        self.tabs.setCurrentIndex(int(index))
        for i, button in enumerate(getattr(self, "_nav_buttons", [])):
            button.setChecked(i == index)

    def _build_header(self):
        box = QGroupBox(f"{APP_NAME} V8.3 - {APP_TAGLINE}")
        layout = QHBoxLayout(box)

        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        self.port_combo.addItems(["COM5", "/dev/ttyACM0", "/dev/ttyUSB0"])
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_ports)
        connect_btn = QPushButton("Connect Wearable")
        connect_btn.clicked.connect(self.connect_serial)
        demo_btn = QPushButton("Demo Mode (Synthetic)")
        demo_btn.clicked.connect(self.start_demo)
        stop_btn = QPushButton("Stop")
        stop_btn.clicked.connect(self.stop_stream)

        self.net_edit = QLineEdit()
        self.net_edit.setPlaceholderText("ESP32-S3 wearable IP:port e.g. 192.168.4.1:7777")
        net_btn = QPushButton("Connect Wi-Fi Bridge")
        net_btn.clicked.connect(lambda: self.connect_network(self.net_edit.text().strip()))

        scenario_btn = QPushButton("Load Scenario")
        scenario_btn.clicked.connect(self._load_scenario_dialog)

        layout.addWidget(QLabel("Port"))
        layout.addWidget(self.port_combo, 1)
        layout.addWidget(refresh_btn)
        layout.addWidget(connect_btn)
        layout.addWidget(demo_btn)
        layout.addWidget(stop_btn)
        layout.addWidget(self.net_edit, 1)
        layout.addWidget(net_btn)
        layout.addWidget(scenario_btn)

        return box

    def _build_overview_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        root = QVBoxLayout(content)
        root.setSpacing(12)

        hero = QFrame()
        hero.setObjectName("ScienceHero")
        hv = QVBoxLayout(hero)
        hv.setContentsMargins(20, 17, 20, 17)
        row = QHBoxLayout()
        left = QVBoxLayout()
        eyebrow = QLabel("ENDO-TWIN NEXUS  •  MULTIMODAL PHYSIOLOGY")
        eyebrow.setObjectName("HeroEyebrow")
        left.addWidget(eyebrow)
        h = QLabel("Scientific Command Center")
        h.setObjectName("HeroTitle")
        left.addWidget(h)
        desc = QLabel("A unified workspace for acquisition, personal calibration, longitudinal physiology, CHRONO-PCOS research signals and auditable evidence.")
        desc.setObjectName("HeroSubtitle")
        desc.setWordWrap(True)
        left.addWidget(desc)
        row.addLayout(left, 1)
        right = QVBoxLayout()
        right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.mode_label = QLabel("●  NO STREAM")
        self.mode_label.setObjectName("HeroStatus")
        right.addWidget(self.mode_label, 0, Qt.AlignmentFlag.AlignRight)
        self.baseline_label = QLabel("BASELINE  •  1 HOUR CALIBRATION")
        self.baseline_label.setObjectName("HeroStatus")
        right.addWidget(self.baseline_label, 0, Qt.AlignmentFlag.AlignRight)
        self.confidence_label = QLabel("Model confidence —")
        self.confidence_label.setObjectName("HeroMetric")
        right.addWidget(self.confidence_label, 0, Qt.AlignmentFlag.AlignRight)
        row.addLayout(right)
        hv.addLayout(row)
        root.addWidget(hero)

        cards_row = QGridLayout()
        cards_row.setSpacing(9)
        self.cards = {}
        for i, (key, title, unit) in enumerate([
            ("hr", "Heart Rate", "bpm"),
            ("hrv", "HRV RMSSD", "ms"),
            ("temp", "Skin Temperature", "°C"),
            ("activity", "Activity", "%"),
            ("gsr", "GSR", "raw"),
            ("stress", "Stress Index", "%"),
        ]):
            card = VitalCard(title, unit)
            self.cards[key] = card
            cards_row.addWidget(card, 0, i)
        root.addLayout(cards_row)

        scientific = QGridLayout()
        scientific.setSpacing(9)

        baseline_box = QFrame()
        baseline_box.setObjectName("ScienceCard")
        bv = QVBoxLayout(baseline_box)
        bv.setContentsMargins(14, 12, 14, 12)
        bv.addWidget(self._named_label("\"PERSONAL BASELINE\"", "CardEyebrow"))
        self.baseline_science = QLabel("CALIBRATING • first-hour quality-gated window")
        self.baseline_science.setObjectName("CardValue")
        self.baseline_science.setWordWrap(True)
        bv.addWidget(self.baseline_science)
        self.baseline_detail = QLabel("The system learns the participant's own physiological reference before longitudinal interpretation.")
        self.baseline_detail.setObjectName("SmallMuted")
        self.baseline_detail.setWordWrap(True)
        bv.addWidget(self.baseline_detail)

        pcos_box = QFrame()
        pcos_box.setObjectName("ScienceCard")
        pv = QVBoxLayout(pcos_box)
        pv.setContentsMargins(14, 12, 14, 12)
        pv.addWidget(self._named_label("\"CHRONO-PCOS  •  RESEARCH SCREENING\"", "CardEyebrow"))
        self.pcos_science = QLabel("INSUFFICIENT DATA")
        self.pcos_science.setObjectName("CardValue")
        pv.addWidget(self.pcos_science)
        self.pcos_detail = QLabel("Wearable physiology is contextual evidence. This surface never represents a wearable reading as a diagnosis.")
        self.pcos_detail.setObjectName("SmallMuted")
        self.pcos_detail.setWordWrap(True)
        pv.addWidget(self.pcos_detail)

        quality_box = QFrame()
        quality_box.setObjectName("ScienceCard")
        qv = QVBoxLayout(quality_box)
        qv.setContentsMargins(14, 12, 14, 12)
        qv.addWidget(self._named_label("\"EVIDENCE & PROVENANCE\"", "CardEyebrow"))
        self.quality_label = QLabel("DATA QUALITY  —")
        self.quality_label.setObjectName("CardValue")
        qv.addWidget(self.quality_label)
        self.coverage_label = QLabel("Coverage —")
        self.coverage_label.setObjectName("SmallMuted")
        qv.addWidget(self.coverage_label)
        qv.addWidget(self._named_label("\"MEASURED → DERIVED → MODEL-INFERRED\"", "ProvenanceLine"))

        scientific.addWidget(baseline_box, 0, 0)
        scientific.addWidget(pcos_box, 0, 1)
        scientific.addWidget(quality_box, 0, 2)
        root.addLayout(scientific)

        signal_box = QFrame()
        signal_box.setObjectName("ScienceCard")
        sv = QVBoxLayout(signal_box)
        sv.setContentsMargins(14, 12, 14, 12)
        sv.addWidget(self._named_label("\"LIVE MULTIMODAL STREAM\"", "CardEyebrow"))
        self.shared_text = QTextEdit()
        self.shared_text.setReadOnly(True)
        self.shared_text.setMinimumHeight(145)
        self.shared_text.setPlaceholderText("PPG • ECG • GSR • temperature • motion • environmental channels will appear here.")
        sv.addWidget(self.shared_text)
        root.addWidget(signal_box)

        signals_box = QFrame()
        signals_box.setObjectName("ScienceCard")
        sig_layout = QVBoxLayout(signals_box)
        sig_layout.setContentsMargins(14, 12, 14, 12)
        sig_layout.addWidget(self._named_label("\"RESEARCH SIGNAL MATRIX\"", "CardEyebrow"))
        self.signal_labels = {}
        matrix = QGridLayout()
        matrix.setSpacing(7)
        for i, mod in enumerate(["pcos", "sleep", "cardiometabolic", "autonomic"]):
            cell = QFrame()
            cell.setObjectName("SignalCell")
            vl = QVBoxLayout(cell)
            vl.setContentsMargins(10, 9, 10, 9)
            title = QLabel(mod.upper())
            title.setObjectName("SignalTitle")
            vl.addWidget(title)
            lbl = QLabel("WAITING FOR QUALITY-GATED DATA")
            lbl.setObjectName("SmallMuted")
            lbl.setWordWrap(True)
            vl.addWidget(lbl)
            self.signal_labels[mod] = lbl
            matrix.addWidget(cell, i // 2, i % 2)
        sig_layout.addLayout(matrix)
        root.addWidget(signals_box)

        disc = QLabel(DISCLAIMER + "  •  Wearable data alone cannot diagnose PCOS/PCOD or other disease.")
        disc.setWordWrap(True)
        disc.setObjectName("WarningText")
        root.addWidget(disc)

        scroll.setWidget(content)
        layout.addWidget(scroll)
        return tab

    def _build_public_study_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        title = QLabel("3-Day Public Wearable Test")
        title.setObjectName("BigValue")
        layout.addWidget(title)
        info = QLabel(
            "Anonymous research recording for a volunteer wearing the ESP32-S3 pod for three days. "
            "Use only the generated participant code. Do not enter names, phone numbers, addresses, emails, "
            "diagnoses or other direct identifiers. Raw data stays local in SQLite until you explicitly export it."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        consent = QCheckBox("Participant has been informed and agrees to this research-prototype recording.")
        layout.addWidget(consent)
        row = QHBoxLayout()
        start = QPushButton("Start 3-Day Study")
        finish = QPushButton("Finish Study")
        refresh = QPushButton("Refresh Timeline")
        export = QPushButton("Export Study CSV")
        load = QPushButton("Load Into Analysis")
        for w in (start, finish, refresh, export, load): row.addWidget(w)
        layout.addLayout(row)
        self.public_study_status = QLabel("No public study active.")
        self.public_study_status.setWordWrap(True)
        layout.addWidget(self.public_study_status)
        self.public_study_timeline = QTextEdit()
        self.public_study_timeline.setReadOnly(True)
        layout.addWidget(self.public_study_timeline, 1)

        def refresh_view():
            study = self.public_study.study
            if not study:
                self.public_study_status.setText("No public study active. Start a new anonymous 3-day test.")
                self.public_study_timeline.setText("DAY 1  • waiting\nDAY 2  • waiting\nDAY 3  • waiting")
                return
            elapsed = min(3.0, study.elapsed_days)
            self.public_study_status.setText(
                f"Participant: {study.participant_id}   |   Study: {study.study_id}\n"
                f"Status: {study.status}   |   Elapsed: {elapsed:.2f}/3.00 days\n"
                "REAL acquisition is stored separately from DEMO/SYNTHETIC data."
            )
            rows = self.public_study.daily_summary()
            lines = []
            for idx, day in enumerate(rows[-3:], 1):
                lines.append(
                    f"DAY {idx}  {day['day']}\n"
                    f"  Samples: {day['samples']:,}\n"
                    f"  Quality: {day['quality']:.0%}"
                )
                if day.get("hr") is not None: lines[-1] += f"\n  HR median: {day['hr']:.1f} bpm"
                if day.get("rmssd") is not None: lines[-1] += f"\n  HRV RMSSD median: {day['rmssd']:.1f} ms"
                if day.get("gsr") is not None: lines[-1] += f"\n  GSR median: {day['gsr']:.1f}"
                if day.get("activity") is not None: lines[-1] += f"\n  Activity mean: {day['activity']:.1f}"
                lines[-1] += "\n  Acquisition quality ≠ clinical validity."
            while len(lines) < 3: lines.append(f"DAY {len(lines)+1}  • waiting for recorded data")
            self.public_study_timeline.setText("\n\n".join(lines))

        def start_study():
            if not consent.isChecked():
                self.public_study_status.setText("Consent acknowledgement is required before starting the public test.")
                return
            study = self.public_study.start()
            self.public_study_status.setText(f"Started {study.study_id} with anonymous participant code {study.participant_id}.")
            refresh_view()

        def finish_study():
            self.public_study.finish()
            refresh_view()

        def export_study():
            if not self.public_study.study: return
            path, _ = QFileDialog.getSaveFileName(self, "Export public study CSV", "endo_twin_public_3day.csv", "CSV (*.csv)")
            if path:
                n = self.public_study.export_csv(path)
                self.public_study_status.setText(f"Exported {n:,} study feature rows to {path}")

        start.clicked.connect(start_study)
        finish.clicked.connect(finish_study)
        refresh.clicked.connect(refresh_view)
        export.clicked.connect(export_study)
        load.clicked.connect(self._load_public_study_features)
        refresh_view()
        return tab

    def _build_baseline_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        root = QVBoxLayout(content)

        info = QLabel(
            "Personal Baseline Engine V8.3\n"
            "Learns what is normal for THIS person: mean, median, std, robust MAD, rolling baseline, confidence, "
            "minimum observations, seasonal/circadian context.\n"
            "CURRENT vs PERSONAL BASELINE -> normalized deviation (z-score, % change)"
        )
        info.setWordWrap(True)
        root.addWidget(info)

        self.baseline_status = QLabel("No baseline yet. Collect at least 5 min calm data, then capture.")
        self.baseline_status.setWordWrap(True)
        root.addWidget(self.baseline_status)

        btn_row = QHBoxLayout()
        capture_btn = QPushButton("Capture Baseline (1 hour)")
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

        # Continual-learning status: tier, wearing time, what unlocks next, history.
        self.learning_panel = LearningStatusPanel(palette={
            "text": TEXT, "muted": TEXT_MUTED, "accent": ACCENT_STRONG,
            "good": GREEN, "warn": YELLOW, "bad": RED,
        })
        root.addWidget(self.learning_panel)

        scroll.setWidget(content)
        layout.addWidget(scroll)
        return tab

    def _build_trends_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel(
            "Longitudinal Engine - Heart of V8.3\n"
            "Rolling windows, persistence detection, trend detection, change-point detection, recovery detection, "
            "missing-data handling, confidence scoring.\n"
            "ONE ABNORMAL -> weak signal, REPEATED CHANGE -> stronger, MULTIPLE FEATURES -> multimodal, "
            "PERSISTENT + GOOD QUALITY -> higher confidence"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.trend_plot = TimeSeriesPlot("HR Trend", "bpm", RED)
        layout.addWidget(self.trend_plot)

        self.trend_plot2 = TimeSeriesPlot("HRV Trend", "ms", ACCENT_STRONG)
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

        # PCOS
        pcos_tab = QWidget()
        pcos_layout = QVBoxLayout(pcos_tab)
        pcos_info = QLabel("MODULE A - PCOS / Reproductive-Metabolic Risk\nPCOS-associated physiological and clinical risk signals (not 'wearable detects PCOS')\nDistinguishes: clinical variables, wearable physiology, ultrasound, combined/fused")
        pcos_info.setWordWrap(True)
        pcos_layout.addWidget(pcos_info)
        self.pcos_text = QTextEdit()
        self.pcos_text.setReadOnly(True)
        pcos_layout.addWidget(self.pcos_text)
        tabs.addTab(pcos_tab, "PCOS / Reproductive-Metabolic")

        # Sleep
        sleep_tab = QWidget()
        sleep_layout = QVBoxLayout(sleep_tab)
        sleep_info = QLabel("MODULE B - Sleep / Circadian Health\nUses activity, HR, HRV, temp, sleep duration/timing/regularity, day/night pattern\nOutputs: sleep regularity signal, circadian disruption signal, recovery signal, persistent deviation\nLanguage: 'sleep-related risk signal' or 'circadian disruption pattern' (not diagnosis)")
        sleep_info.setWordWrap(True)
        sleep_layout.addWidget(sleep_info)
        self.sleep_text = QTextEdit()
        self.sleep_text.setReadOnly(True)
        sleep_layout.addWidget(self.sleep_text)
        tabs.addTab(sleep_tab, "Sleep / Circadian")

        # Cardiometabolic
        cardio_tab = QWidget()
        cardio_layout = QVBoxLayout(cardio_tab)
        cardio_info = QLabel("MODULE C - Cardiometabolic Risk (research-oriented)\nFeatures: resting HR, HRV, activity, BMI, age, BP if entered, glucose if entered, sleep, temp, longitudinal\nOutputs: cardiometabolic risk signal, reduced activity trend, elevated RHR trend, metabolic flag\nNever claims diabetes/hypertension/CVD diagnosis")
        cardio_info.setWordWrap(True)
        cardio_layout.addWidget(cardio_info)
        self.cardio_text = QTextEdit()
        self.cardio_text.setReadOnly(True)
        cardio_layout.addWidget(self.cardio_text)
        tabs.addTab(cardio_tab, "Cardiometabolic")

        # Autonomic
        auto_tab = QWidget()
        auto_layout = QVBoxLayout(auto_tab)
        auto_info = QLabel("MODULE D - Autonomic / Stress Regulation\nUses HRV, resting HR, GSR, activity, sleep, temp\nExplainable estimator separating ACUTE SIGNAL from PERSISTENT LONGITUDINAL CHANGE\nNot a mental-health diagnosis")
        auto_info.setWordWrap(True)
        auto_layout.addWidget(auto_info)
        self.autonomic_text = QTextEdit()
        self.autonomic_text.setReadOnly(True)
        auto_layout.addWidget(self.autonomic_text)
        tabs.addTab(auto_tab, "Autonomic / Stress")

        # Future
        future_tab = QWidget()
        future_layout = QVBoxLayout(future_tab)
        future_info = QLabel("Future Modules - Not Implemented\nThese modules require appropriate dataset, validated features, scientifically defensible labels.\nMarked as 'Future research module - not implemented' and not generating fake data.")
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

        info = QLabel("Sensor Quality - Every reading has quality metadata: value, quality 0..1, source, timestamp, artifact\nDetects: missing data, impossible values, flatline, excessive noise, motion artifacts, packet corruption, stale data\nBad data must not silently become model input.")
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

        info = QLabel("Ultrasound - Periodic clinical imaging\nProvenance preserved: source image -> preprocessing -> detected features -> quality -> uncertainty\nIf feature cannot be reliably extracted: return UNKNOWN, never invent.\nFeatures labelled as CLINICALLY-ENTERED or IMAGE-DERIVED")
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

        info = QLabel("Explainability - Every risk signal explains main contributing factors\nDrivers: e.g. resting HR increased from baseline, HRV decreased, sleep regularity decreased, activity decreased\nThen: 'These changes are not specific to one disease and should not be interpreted as a diagnosis.'")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.explanation_text = QTextEdit()
        self.explanation_text.setReadOnly(True)
        layout.addWidget(self.explanation_text)

        return tab

    def _build_report_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel("Report Generation - Research report with limitations and recommendation: 'Discuss relevant findings with qualified healthcare professional.'\nIncludes: subject ID, observation period, sensor data, data quality, personal baseline, longitudinal changes, disease signals, contributing factors, ultrasound if available, clinical inputs, limitations")
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

        info = QLabel("Validation - Engineering vs Clinical\nTests: baseline accuracy, trend detection, persistence, recovery, missing sensor handling, noisy data, multimodal fusion, disease module isolation, subject-level validation, reproducibility")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.validation_text = QTextEdit()
        self.validation_text.setReadOnly(True)
        self.validation_text.setText(
            "CHRONO-TWIN NEXUS V8.3 Validation Status\n"
            "========================================\n\n"
            "Engineering Validation:\n"
            "- Personal baseline: mean, median, std, MAD, rolling, confidence, min obs, circadian context - IMPLEMENTED\n"
            "- Longitudinal engine: rolling windows, persistence, trend, change-point, recovery, missing handling, confidence - IMPLEMENTED\n"
            "- Shared representation: heart_rate, resting_hr, hrv, activity, sleep, temp, gsr, circadian, recovery, baseline_dev, trends, quality - IMPLEMENTED\n"
            "- Disease modules: PCOS, Sleep, Cardiometabolic, Autonomic with consistent API - IMPLEMENTED\n"
            "- Sensor quality: missing, impossible, flatline, noise, motion, corruption, stale - IMPLEMENTED\n"
            "- Hardware failure tests: disconnected MAX30102, temp, corrupted packet, duplicate, delayed, missing, noisy PPG, motion, reconnection - IMPLEMENTED\n"
            "- Synthetic longitudinal data with 6 scenarios - IMPLEMENTED\n"
            "- Multimodal fusion with provenance - IMPLEMENTED\n"
            "- Explainability - IMPLEMENTED\n"
            "- Subject-level validation (no leakage) - IMPLEMENTED\n"
            "- Data honesty: REAL, SYNTHETIC, PUBLIC, USER-ENTERED labelled - IMPLEMENTED\n\n"
            "Clinical Validation: NOT ESTABLISHED\n"
            "- All modules are research-only signals\n"
            "- No diagnostic claims\n"
            "- Requires ethics-approved prospective study\n"
            "- Model confidence vs data quality vs clinical validation separated\n\n"
            "Hardware:\n"
            "- Wearable Nano Pod: MAX30102 + MPU6050 + DS18B20 + optional GSR - PRESERVED from V8.1\n"
            "- Mega Hub: expanded experimental sensors - PRESERVED\n"
            "- Software gracefully handles missing sensors - IMPLEMENTED\n"
        )
        layout.addWidget(self.validation_text)

        return tab

    # ------------------------------------------------- logic
    def _refresh_ports(self):
        # Simple refresh - in real app would scan serial ports
        self.port_combo.addItem("/dev/ttyACM0")

    def connect_serial(self, port=None):
        p = port or self.port_combo.currentText()
        try:
            self.arduino_reader = ArduinoReader(port=p, baud=115200)
            self.arduino_reader.start()
            self.mode_label.setText(f"Mode: LIVE SERIAL {p}")
            self.mode_label.setStyleSheet(f"font-weight: bold; color: {GREEN};")
        except Exception as e:
            self.mode_label.setText(f"Mode: SERIAL FAILED {e}")
            self.mode_label.setStyleSheet(f"font-weight: bold; color: {RED};")

    def connect_network(self, hostport: str):
        if not hostport:
            return
        try:
            parts = hostport.split(":")
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 7777
            self.network_reader = NetworkReader(host=host, port=port)
            self.network_reader.start()
            self.mode_label.setText(f"Mode: LIVE NETWORK {hostport}")
            self.mode_label.setStyleSheet(f"font-weight: bold; color: {GREEN};")
        except Exception as e:
            self.mode_label.setText(f"Mode: NETWORK FAILED {e}")

    def start_demo(self):
        self.demo_stream = DemoSensorStream()
        self.demo_stream.start()
        self.mode_label.setText("Mode: DEMO SYNTHETIC - clearly labelled")
        self.mode_label.setStyleSheet(f"font-weight: bold; color: {YELLOW};")

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
        self.mode_label.setStyleSheet(f"font-weight: bold; color: {RED};")

    def _load_scenario_dialog(self):
        # Load one of the 6 scenarios as demo
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
            # Convert to FeatureVectors
            from src.data_models import FeatureVector
            vectors = []
            for row in data["data"][:200]:  # load first 200 for demo
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
            self.mode_label.setStyleSheet(f"font-weight: bold; color: {ACCENT_STRONG};")
            self._update_risk()
        except Exception as e:
            self.mode_label.setText(f"Failed to load scenario: {e}")

    def _update_features(self):
        sample = None
        if self.arduino_reader and self.arduino_reader.has_sample():
            sample = self.arduino_reader.get_sample()
        elif self.network_reader and self.network_reader.has_sample():
            sample = self.network_reader.get_sample()
        elif self.demo_stream and self.demo_stream.has_sample():
            sample = self.demo_stream.get_sample()

        if sample:
            # Convert to SensorSample if needed
            if isinstance(sample, dict):
                # demo stream dict
                from src.data_models import SensorSample
                import time
                s = SensorSample(
                    timestamp_s=time.time(),
                    ms=int(sample.get("ms", 0)),
                    ir=int(sample.get("ir", 5000)),
                    red=int(sample.get("red", 5000)),
                    ax_g=float(sample.get("ax", 0)),
                    ay_g=float(sample.get("ay", 0)),
                    az_g=float(sample.get("az", 1)),
                    gx_dps=float(sample.get("gx", 0)),
                    gy_dps=float(sample.get("gy", 0)),
                    gz_dps=float(sample.get("gz", 0)),
                    temp_c=float(sample.get("temp_c", 32.5)),
                    gsr_raw=int(sample.get("gsr", 450)),
                    lux=float(sample.get("lux", 100)),
                    source="demo" if self.demo_stream else "serial"
                )
                sample = s

            self.extractor.add_sample(sample)
            fv = self.extractor.compute()
            self.feature_history.append(fv)
            if self.public_study.study and (time.time() - self._last_public_study_log) >= 10.0:
                try:
                    self.public_study.record_feature(fv)
                    self._last_public_study_log = time.time()
                except Exception as e:
                    self.history_store.log_error(self.public_study.study.session_id, "study", str(e))
            if len(self.feature_history) > 5000:
                self.feature_history = self.feature_history[-5000:]

            # Update UI vitals
            self._update_vital_cards(fv)

            # Update shared
            try:
                shared = self.shared_extractor.extract(fv, self.feature_history[-50:])
                self.current_shared = shared
                self.shared_history.append(shared)
                if len(self.shared_history) > 500:
                    self.shared_history = self.shared_history[-500:]
                self.shared_text.setText(self.explanation_engine.explain_shared_features(shared))
            except Exception as e:
                pass

    def _update_vital_cards(self, fv: FeatureVector):
        def set_card(key, value, fmt="{:.0f}"):
            if key in self.cards:
                if value is None:
                    self.cards[key].set_value("—")
                else:
                    try:
                        self.cards[key].set_value(fmt.format(value))
                    except:
                        self.cards[key].set_value(str(value))

        set_card("hr", fv.hr_bpm)
        set_card("hrv", fv.rmssd_ms)
        set_card("temp", fv.skin_temp_c, "{:.1f}")
        set_card("activity", fv.activity_level)
        set_card("gsr", fv.gsr_tonic)
        set_card("stress", fv.stress_index)
        set_card("sleep", fv.sleep_probability)
        set_card("quality", fv.signal_quality * 100 if fv.signal_quality else 0)
        set_card("recovery", fv.shared_features.get("recovery_score", 50) if isinstance(fv.shared_features, dict) else 50)

    def _update_risk(self):
        if not self.feature_history:
            return
        if not self.current_shared:
            return

        # Longitudinal
        try:
            longitudinal_report = self.longitudinal_engine.evaluate(self.feature_history[-200:])
            self.longitudinal_text.setText(self.explanation_engine.explain_longitudinal(longitudinal_report))
        except Exception as e:
            longitudinal_report = None
            self.longitudinal_text.setText(f"Longitudinal error: {e}")

        # Clinical data
        clinical = self.clinical_data.copy()
        clinical["profile"] = self.profile

        # Disease modules
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

        # Update health signals tab
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

            # Overview signal labels
            if name in self.signal_labels:
                self.signal_labels[name].setText(
                    f"{result.signal}\nLevel: {result.level}\nConf: {result.confidence:.2f}\nQuality: {result.data_quality:.2f}\n{result.explanation[:150]}..."
                )
                # Color by level
                if result.level == "high":
                    self.signal_labels[name].setStyleSheet(f"color: {RED}; font-weight: bold;")
                elif result.level == "elevated":
                    self.signal_labels[name].setStyleSheet(f"color: {ORANGE};")
                elif result.level == "moderate":
                    self.signal_labels[name].setStyleSheet(f"color: {YELLOW};")
                else:
                    self.signal_labels[name].setStyleSheet(f"color: {GREEN};")

        # Fusion
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

            # Update overview gauges
            overall_risk = 0
            if module_results:
                # Average of elevated signals or max
                scores = []
                for r in module_results.values():
                    # Map level to score
                    level_map = {"low": 15, "moderate": 40, "elevated": 65, "high": 85}
                    scores.append(level_map.get(r.level, 30))
                overall_risk = float(sum(scores) / len(scores)) if scores else 0

            if hasattr(self, "pcos_science"):
                self.pcos_science.setText(f"RESEARCH INDEX: {overall_risk:.0f}/100")
            self.confidence_label.setText(f"Model Confidence: {fusion_result.confidence_breakdown.get('model_confidence', 0):.2f}")
            self.quality_label.setText(f"Data Quality: {fusion_result.confidence_breakdown.get('data_quality', 0):.2f}")
            self.coverage_label.setText(f"Coverage: {fusion_result.confidence_breakdown.get('fusion_coverage', 0):.0%}")
            if hasattr(self, "quality_label"):
                self.quality_label.setText(f"DATA QUALITY  {fusion_result.confidence_breakdown.get('data_quality', 0):.2f}")

            # Baseline + continual-learning status
            learning = self.adaptive_model.status()
            if self.baseline_engine.has_baseline:
                self.baseline_label.setText(
                    f"Baseline: YES (conf {self.baseline_engine.baseline.confidence:.2f}, "
                    f"{self.baseline_engine.baseline.days_covered} days)  •  "
                    f"model {learning['tier'].upper()} v{learning['model_version']}")
                self.baseline_label.setStyleSheet(f"color: {GREEN};")
            else:
                self.baseline_label.setText(
                    f"Baseline: CALIBRATING - need ~1 hour quality-gated data  •  "
                    f"model {learning['tier'].upper()} ({learning['worn_hours']:.1f} h worn)")
                self.baseline_label.setStyleSheet(f"color: {YELLOW};")
            self.learning_panel.update_from(learning)

            # Data quality tab
            self.quality_text.setText(
                context.summary_text() + "\n\n" + self.explanation_engine.explain_fusion(fusion_result)
            )

            # Explanation tab
            self.explanation_text.setText(
                self.explanation_engine.generate_report_explanation(
                    self.current_shared, longitudinal_report, fusion_result
                )
            )

            # Baseline tab details
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
                self.baseline_comparison.setText(
                    "\n".join([f"{k}: current {v.get('current')} vs baseline {v.get('baseline_median')} -> {v.get('deviation_pct')}%, z={v.get('zscore')}, status {v.get('status')}" for k, v in comp.items()])
                )

        except Exception as e:
            print(f"Fusion error: {e}")
            import traceback
            traceback.print_exc()

    def _load_public_study_features(self):
        study = self.public_study.study
        if not study:
            self.public_study_status.setText("No public study selected.")
            return
        df = self.history_store.features_for_session(study.session_id)
        if df.empty:
            self.public_study_status.setText("The study has no imported feature rows yet. Import the Android CSV first.")
            return
        rows = []
        for _, r in df.iterrows():
            def num(name, default=None):
                v = r.get(name, default)
                try:
                    return float(v) if v is not None else default
                except (TypeError, ValueError):
                    return default
            rows.append(FeatureVector(
                timestamp_s=float(r["ts"]),
                hr_bpm=num("hr"),
                rmssd_ms=num("rmssd"),
                spo2_pct=num("spo2"),
                skin_temp_c=num("skin_temp"),
                gsr_tonic=num("gsr"),
                motion_index=num("motion", 0.0),
                activity_level=num("activity", 0.0),
                stress_index=num("stress", 0.0),
                sleep_probability=num("sleep_prob", 0.0),
                circadian_stability_index=num("circadian", 50.0),
                signal_quality=num("signal_quality", 0.0),
            ))
        self.feature_history = rows
        self.baseline_status.setText(f"Loaded {len(rows):,} imported public-study feature rows for {study.participant_id}.")
        self.public_study_status.setText(f"Loaded {len(rows):,} rows into desktop analysis.")
        self._update_vital_cards(rows[-1])
        self._update_risk()

    def _capture_baseline(self):
        try:
            if self.public_study.study and self.feature_history:
                self.baseline_engine.capture_from_features(self.feature_history)
                self.baseline_status.setText(
                    f"Baseline captured from public study. Confidence {self.baseline_engine.baseline.confidence:.2f}, "
                    f"{self.baseline_engine.baseline.days_covered} days, {len(self.baseline_engine.baseline.stats)} metrics"
                )
                return
            success = self.extractor.capture_baseline()
            if success:
                self.baseline_status.setText(
                    f"Baseline captured! Confidence {self.baseline_engine.baseline.confidence:.2f}, "
                    f"{self.baseline_engine.baseline.days_covered} days, {len(self.baseline_engine.baseline.stats)} metrics"
                )
            else:
                self.baseline_status.setText(f"Baseline failed: {self.extractor.last_capture_error}")
        except Exception as e:
            self.baseline_status.setText(f"Baseline failed: {e}")

    def _clinical_changed(self):
        # Update profile
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

        # Build report
        lines = [
            f"{'='*60}",
            f"CHRONO-TWIN NEXUS V8.3 RESEARCH REPORT",
            f"{'='*60}",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Subject ID: Anonymous (no identifiers stored)",
            f"Observation period: {len(self.feature_history)} samples over {(self.feature_history[-1].timestamp_s - self.feature_history[0].timestamp_s)/3600:.1f}h" if len(self.feature_history) > 1 else "Observation period: insufficient",
            f"",
            f"DISCLAIMER: {DISCLAIMER}",
            f"This is a research estimate, NOT a diagnosis. Clinical evaluation required.",
            f"",
            f"--- Sensor Data Available ---",
            f"Wearable: {'Yes' if self.feature_history else 'No'} ({len(self.feature_history)} samples)",
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



def run(start_demo: bool = True, port: str | None = None, net: str | None = None, db_path=None):
    """Launch the unified ENDO-TWIN scientific workstation."""
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow(start_demo=start_demo, port=port, net=net, db_path=db_path)
    window.showMaximized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run(start_demo=True))
