#!/usr/bin/env python3
"""ENDO-TWIN V8.6 Doctor Workstation — reference-inspired clinical research UI."""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QComboBox, QDialog, QDialogButtonBox, QFrame,
    QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QDoubleSpinBox, QSplitter,
    QStackedWidget, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout,
    QWidget
)

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.database import LocalDatabase
from desktop.doctor_app.patient_management import PatientManager
from desktop.demo_data import condition_list, sorted_cases, DemoCase
from desktop.workstation_runtime import LiveSession, ModeConfig, Sparkline, choose_mode
from desktop.workstation_theme import APP_QSS, card, section_header, pill, status_badge
from desktop.prototype_lab import PrototypeLabWidget
from services.bridge.server import EndoTwinBridgeServer

DISCLAIMER = "Research / risk-screening output — not a medical diagnosis."
ORDER = {"High": 4, "Elevated": 3, "Moderate": 2, "Low": 1, "Unknown": 0}


class DoctorWindow(QMainWindow):
    """Reference-inspired doctor workstation with patient-scoped tabs and auditability."""

    def __init__(self, mode: ModeConfig):
        super().__init__()
        self.mode = mode
        self.db = LocalDatabase()
        self.patient_mgr = PatientManager(self.db)
        self.current_case: DemoCase | None = None
        self.live_patient = None
        self.latest_row = None
        self.packet_count = 0
        self.events = []
        self.note_cache = ""
        self.image_path = ""
        self.metric_cards = {}
        self.trend_charts = {}
        self.metric_history = {"hr_bpm": deque(maxlen=240), "rmssd_ms": deque(maxlen=240), "activity_level": deque(maxlen=240), "skin_temp_c": deque(maxlen=240), "gsr_tonic": deque(maxlen=240), "spo2_pct": deque(maxlen=240)}
        self.tab_pages = {}
        self.page_keys = ["dashboard", "patients", "lab", "patient", "mobile", "settings"]

        self.bridge = EndoTwinBridgeServer(ROOT, 7777)
        self.bridge.start()

        self.session = LiveSession(mode, self)
        self.session.features_updated.connect(self._on_features)
        self.session.sample_received.connect(self._on_sample)
        self.session.state_changed.connect(self._on_state)
        self.session.error_received.connect(self._on_error)
        self.session.start()

        self.setWindowTitle("Endo-Twin Nexus — Doctor Desktop • V8.6")
        self.resize(1580, 940)
        self.setMinimumSize(1180, 760)
        self.setStyleSheet(APP_QSS)
        self._build()
        self._log_event("Workstation opened", "session")
        self._refresh_roster()
        self._refresh_header()

    def closeEvent(self, event):
        self.session.stop()
        self.bridge.stop()
        self.db.close()
        event.accept()

    # ---------- shell ----------
    def _build(self):
        root = QWidget()
        self.setCentralWidget(root)
        shell = QGridLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(205)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(14, 18, 10, 16)
        sl.setSpacing(4)

        brand = QLabel("Endo-Twin Nexus")
        brand.setObjectName("brand")
        sl.addWidget(brand)
        tag = QLabel("Sense · Understand · Track · Model · Personalize")
        tag.setObjectName("muted")
        tag.setWordWrap(True)
        sl.addWidget(tag)
        sl.addSpacing(17)

        ws = QLabel("WORKSPACE")
        ws.setObjectName("eyebrow")
        sl.addWidget(ws)

        self.nav = {}
        for key, text in [
            ("dashboard", "▦  Dashboard"),
            ("patients", "♙  Patients"),
            ("lab", "⌁  Prototype Lab"),
        ]:
            b = QPushButton(text)
            b.setObjectName("nav")
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, k=key: self._go(k))
            self.nav[key] = b
            sl.addWidget(b)

        self.current_group = QLabel("CURRENT PATIENT")
        self.current_group.setObjectName("eyebrow")
        self.current_group.setVisible(False)
        sl.addWidget(self.current_group)

        self.current_patient_btn = QPushButton("No patient selected")
        self.current_patient_btn.setObjectName("nav")
        self.current_patient_btn.setEnabled(False)
        self.current_patient_btn.setVisible(False)
        self.current_patient_btn.clicked.connect(lambda: self._go("patient"))
        sl.addWidget(self.current_patient_btn)

        self.settings_group = QLabel("SETTINGS")
        self.settings_group.setObjectName("eyebrow")
        sl.addSpacing(16)
        sl.addWidget(self.settings_group)

        b = QPushButton("⚙  Preferences")
        b.setObjectName("nav")
        b.clicked.connect(lambda: self._go("settings"))
        self.nav["settings"] = b
        sl.addWidget(b)

        sl.addStretch()

        mode_box = QFrame()
        mode_box.setObjectName("hero")
        mv = QVBoxLayout(mode_box)
        mv.setContentsMargins(10, 10, 10, 10)
        mx = QLabel("SESSION MODE")
        mx.setObjectName("eyebrow")
        mv.addWidget(mx)
        self.side_mode = QLabel()
        self.side_mode.setObjectName("subtitle")
        mv.addWidget(self.side_mode)
        self.side_state = QLabel()
        self.side_state.setObjectName("muted")
        self.side_state.setWordWrap(True)
        mv.addWidget(self.side_state)
        sl.addWidget(mode_box)
        shell.addWidget(side, 0, 0)

        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(0)

        top = QFrame()
        top.setObjectName("topbar")
        tl = QHBoxLayout(top)
        tl.setContentsMargins(18, 8, 18, 8)
        brand2 = QLabel("∞  ENDO-TWIN NEXUS")
        brand2.setObjectName("brandAccent")
        tl.addWidget(brand2)
        subtitle = QLabel("Personalized Physiological Modelling Platform")
        subtitle.setObjectName("muted")
        tl.addWidget(subtitle)
        tl.addSpacing(18)

        self.global_search = QLineEdit()
        self.global_search.setPlaceholderText("Search / select patient…")
        self.global_search.setFixedWidth(270)
        self.global_search.returnPressed.connect(self._search_patient)
        tl.addWidget(self.global_search)
        tl.addStretch()

        self.connection_badge = status_badge("●  Research prototype", "info")
        self.quality_badge = status_badge("●  Data quality: —", "neutral")
        self.patient_badge = status_badge("No patient selected", "neutral")
        tl.addWidget(self.connection_badge)
        tl.addSpacing(6)
        tl.addWidget(self.quality_badge)
        tl.addSpacing(6)
        tl.addWidget(self.patient_badge)
        rv.addWidget(top)

        self.stack = QStackedWidget()
        self.pages = {
            "dashboard": self._dashboard_page(),
            "patients": self._patients_page(),
            "lab": PrototypeLabWidget(self.session, self.mode, ROOT),
            "patient": self._patient_page(),
            "mobile": self._mobile_page(),
            "settings": self._settings_page(),
        }
        for key in self.page_keys:
            self.stack.addWidget(self.pages[key])
        rv.addWidget(self.stack, 1)

        foot = QLabel(f"{DISCLAIMER}  •  Local-first  •  Patient-scoped  •  Startup mode is fixed for this run")
        foot.setObjectName("muted")
        foot.setContentsMargins(16, 4, 16, 7)
        rv.addWidget(foot)
        shell.addWidget(right, 0, 1)

        self._go("dashboard")

    def _go(self, key: str):
        if key not in self.page_keys:
            return
        self.stack.setCurrentIndex(self.page_keys.index(key))
        for k, b in self.nav.items():
            b.setChecked(k == key)
        if key in ("dashboard", "patients"):
            self._refresh_roster()
        self._refresh_header()

    def _mode_text(self):
        if self.mode.mode == "demo":
            return "DEMO MODE", "Synthetic showcase stream"
        return "LIVE SENSOR MODE", f"USB serial • {self.mode.port}"

    def _refresh_header(self):
        title, detail = self._mode_text()
        self.side_mode.setText(title)
        self.side_state.setText(detail)
        if self.current_case:
            self.current_patient_btn.setText(f"◉  {self.current_case.alias}  ·  {self.current_case.patient}")
            self.current_patient_btn.setVisible(True)
            self.current_group.setVisible(True)
            self.current_patient_btn.setEnabled(True)
            self.patient_badge.setText(f"Patient • {self.current_case.patient}")
        elif self.live_patient:
            alias = str(self.live_patient.get("display_name") or self.live_patient.get("anonymous_id") or "Local patient")
            pid = str(self.live_patient.get("anonymous_id") or self.live_patient.get("patient_id") or "")
            self.current_patient_btn.setText(f"◉  {alias}  ·  {pid}")
            self.current_patient_btn.setVisible(True)
            self.current_group.setVisible(True)
            self.current_patient_btn.setEnabled(True)
            self.patient_badge.setText(f"Patient • {pid or alias}")
        else:
            self.current_patient_btn.setVisible(False)
            self.current_group.setVisible(False)
            self.patient_badge.setText("No patient selected")

        if self.mode.mode == "live":
            self.connection_badge.setText("●  " + ("Wearable • connected" if self.latest_row else "Wearable • waiting"))
        else:
            self.connection_badge.setText("●  Demo data • synthetic")

    # ---------- data helpers ----------
    def _profile(self):
        if self.current_case:
            return {
                "pid": self.current_case.patient,
                "alias": self.current_case.alias,
                "age": self.current_case.age,
                "bmi": self.current_case.bmi,
                "condition": self.current_case.condition,
                "tier": self.current_case.tier,
                "risk": self.current_case.risk,
                "quality": self.current_case.quality,
                "hr": self.current_case.hr,
                "hrv": self.current_case.hrv,
                "temp": self.current_case.temp,
                "activity": self.current_case.activity,
                "sleep": self.current_case.sleep,
                "drivers": self.current_case.drivers,
                "last_seen": self.current_case.last_seen,
            }
        if self.live_patient:
            return {
                "pid": str(self.live_patient.get("anonymous_id") or self.live_patient.get("patient_id") or "LOCAL"),
                "alias": str(self.live_patient.get("display_name") or "Local patient"),
                "age": self.live_patient.get("age_years", "—"),
                "bmi": self.live_patient.get("bmi", "—"),
                "condition": "No model run",
                "tier": "Unknown",
                "risk": None,
                "quality": None,
                "hr": None,
                "hrv": None,
                "temp": None,
                "activity": None,
                "sleep": None,
                "drivers": ("No disease-model inference in live workstation view",),
                "last_seen": str(self.live_patient.get("updated_at", "—")),
            }
        return None

    def _data_quality_text(self, quality):
        if quality is None:
            return "Data quality: —", "neutral"
        q = float(quality)
        if q >= 0.9:
            return f"Data quality: Good", "good"
        if q >= 0.8:
            return f"Data quality: Fair", "fair"
        return f"Data quality: Poor", "poor"

    def _log_event(self, title, detail):
        self.events.append((datetime.now().strftime("%Y-%m-%d %H:%M:%S"), title, detail))
        if len(self.events) > 40:
            self.events = self.events[-40:]

    def _fmt(self, value, suffix="", digits=1):
        if value is None:
            return "—"
        try:
            return f"{float(value):.{digits}f}{suffix}"
        except Exception:
            return str(value)

    def _patient_header(self):
        p = self._profile()
        box = QFrame()
        box.setObjectName("patientHeader")
        lay = QHBoxLayout(box)
        lay.setContentsMargins(14, 12, 14, 12)

        avatar = QLabel((p["pid"][-3:] if p else "000"))
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(46, 46)
        avatar.setStyleSheet("background:#0b6670;color:white;border-radius:10px;font-size:16px;font-weight:900;")
        lay.addWidget(avatar)
        lay.addSpacing(9)

        col = QVBoxLayout()
        title = QLabel(f'{p["alias"]}  ')
        title.setStyleSheet("font-size:17px;font-weight:900;color:#eef1f7;")
        col.addWidget(title)
        pid = QLabel(f'{p["pid"]}  ·  internal reference only')
        pid.setObjectName("muted")
        col.addWidget(pid)
        tag = QLabel("DEMO DATA" if self.current_case else "LOCAL RECORD")
        tag.setStyleSheet("background:#2d3341;color:#c3cad8;border-radius:8px;padding:4px 7px;font-size:9px;font-weight:850;")
        col.addWidget(tag)
        lay.addLayout(col, 1)

        meta = QGridLayout()
        fields = [
            ("OBSERVATION PERIOD", "30 days" if self.current_case else "—"),
            ("LAST SYNC", p["last_seen"]),
            ("DATA QUALITY", self._data_quality_text(p["quality"])[0].replace("Data quality: ", "")),
            ("REVIEW STATUS", "Needs review" if (self.current_case and p["tier"] in ("High", "Elevated")) else "Research only"),
        ]
        for i, (k, v) in enumerate(fields):
            lab = QLabel(k)
            lab.setObjectName("smallCaps")
            val = QLabel(str(v))
            val.setStyleSheet("color:#e6eaf2;font-weight:800;")
            meta.addWidget(lab, 0, i)
            meta.addWidget(val, 1, i)
        lay.addLayout(meta)
        return box

    def _metric_panel(self, title, value, unit, delta, provenance, values, quality_kind="good"):
        panel = QFrame()
        panel.setObjectName("card")
        v = QVBoxLayout(panel)
        v.setContentsMargins(14, 12, 14, 10)
        top = QHBoxLayout()
        a = QLabel(title)
        a.setStyleSheet("font-size:12px;font-weight:800;color:#d5dbea;")
        top.addWidget(a)
        top.addStretch()
        u = QLabel(unit)
        u.setObjectName("muted")
        top.addWidget(u)
        v.addLayout(top)

        row = QHBoxLayout()
        big = QLabel(value)
        big.setObjectName("metricValue")
        row.addWidget(big)
        if delta:
            d = QLabel(delta)
            d.setObjectName("muted")
            row.addWidget(d, 0, Qt.AlignmentFlag.AlignBottom)
        row.addStretch()
        row.addWidget(status_badge("●  " + ("Good" if quality_kind=="good" else "Fair" if quality_kind=="fair" else "Unknown"), quality_kind))
        v.addLayout(row)

        chart = Sparkline(title, unit)
        chart.setMinimumHeight(112)
        chart.set_values(values)
        v.addWidget(chart)
        prov = QLabel(provenance)
        prov.setStyleSheet("border:1px solid #566178;border-radius:6px;padding:3px 7px;color:#aab9ff;font-size:9px;font-weight:800;")
        v.addWidget(prov, 0, Qt.AlignmentFlag.AlignLeft)
        self.metric_cards[title] = (big, chart)
        return panel

    # ---------- dashboard ----------
    def _dashboard_page(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.setContentsMargins(22, 16, 20, 14)
        o.setSpacing(11)

        # Command-center greeting
        hero = QFrame()
        hero.setObjectName("hero")
        hv = QVBoxLayout(hero)
        hv.setContentsMargins(18, 14, 18, 14)
        top = QHBoxLayout()

        left = QVBoxLayout()
        eyebrow = QLabel("ENDO-TWIN NEXUS  •  RESEARCH WORKSTATION")
        eyebrow.setObjectName("eyebrow")
        left.addWidget(eyebrow)
        welcome = QLabel("Welcome back, Researcher")
        welcome.setObjectName("dashboardWelcome")
        left.addWidget(welcome)
        sub = QLabel("Advancing endocrine health research through multimodal physiological data, AI and longitudinal analysis.")
        sub.setObjectName("subtitle")
        sub.setWordWrap(True)
        left.addWidget(sub)
        top.addLayout(left, 1)

        date_col = QVBoxLayout()
        date_col.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        date = QLabel(datetime.now().strftime("%a, %d %b %Y"))
        date.setObjectName("dashboardDate")
        clock = QLabel(datetime.now().strftime("%I:%M %p"))
        clock.setObjectName("dashboardClock")
        date_col.addWidget(date, 0, Qt.AlignmentFlag.AlignRight)
        date_col.addWidget(clock, 0, Qt.AlignmentFlag.AlignRight)
        top.addLayout(date_col)
        hv.addLayout(top)
        o.addWidget(hero)

        # KPI strip
        g = QGridLayout()
        g.setSpacing(9)
        self.dash_kpis = {}
        kpis = [
            ("Active Patients", "—", "Research roster", "#28d5ee"),
            ("Live Devices", "1 / 1", "Sensor bridge", "#45e5b3"),
            ("Data Collected", "Local", "Offline-first", "#8c7dff"),
            ("AI Analyses", "—", "Research modules", "#b083ff"),
            ("Research Studies", "5", "Platform modules", "#45d9ff"),
        ]
        for i, (a, b, detail, accent) in enumerate(kpis):
            f = card(a, b, detail, accent=accent)
            f.setObjectName("card")
            g.addWidget(f, 0, i)
            labels = f.findChildren(QLabel)
            self.dash_kpis[a] = labels[1]
        o.addLayout(g)

        # Personalization + PCOS research-screening status
        status_grid = QGridLayout()
        status_grid.setSpacing(9)
        self.baseline_status_card = card("PERSONAL BASELINE", "1 HOUR", "Quality-gated calibration before interpretation", accent="#28d5ee")
        self.pcos_screen_status_card = card("CHRONO-PCOS SCREENING", "WAITING", "Research signal • not a diagnosis", accent="#b083ff")
        self.personalization_status_card = card("ADAPTATION", "READY AFTER BASELINE", "High-quality observations update the personal reference", accent="#45e5b3")
        status_grid.addWidget(self.baseline_status_card, 0, 0)
        status_grid.addWidget(self.pcos_screen_status_card, 0, 1)
        status_grid.addWidget(self.personalization_status_card, 0, 2)
        o.addLayout(status_grid)

        # Main analysis row
        split = QSplitter(Qt.Orientation.Horizontal)
        split.setChildrenCollapsible(False)

        signals = QFrame()
        signals.setObjectName("card")
        sv = QVBoxLayout(signals)
        sv.setContentsMargins(13, 11, 13, 11)
        head = QHBoxLayout()
        htitle = QLabel("Live Sensor Signals")
        htitle.setObjectName("sectionTitle")
        head.addWidget(htitle)
        head.addStretch()
        live = QLabel("● LIVE")
        live.setObjectName("liveSignal")
        head.addWidget(live)
        sv.addLayout(head)
        hint = QLabel("Multimodal stream • PPG / EDA / temperature / motion")
        hint.setObjectName("muted")
        sv.addWidget(hint)

        self.dashboard_signal_charts = {}
        signal_defs = [
            ("PPG (IR)", "hr_bpm", "bpm", "#2ed9b0"),
            ("EDA (GSR)", "gsr_tonic", "µS", "#37b8ff"),
            ("Skin Temp", "skin_temp_c", "°C", "#ffb74d"),
            ("Accelerometer", "activity_level", "g", "#9a7cff"),
        ]
        for label, key, unit, accent in signal_defs:
            row = QHBoxLayout()
            name = QLabel("●  " + label)
            name.setObjectName("signalName")
            name.setFixedWidth(118)
            row.addWidget(name)
            chart = Sparkline(label, unit)
            chart.setMinimumHeight(42)
            chart.setMaximumHeight(55)
            chart.set_values(list(self.metric_history.get(key, [])))
            self.dashboard_signal_charts[key] = chart
            row.addWidget(chart, 1)
            value = QLabel("—")
            value.setObjectName("signalValue")
            value.setFixedWidth(58)
            row.addWidget(value)
            setattr(self, f"dashboard_{key}_value", value)
            sv.addLayout(row)

        insights = QFrame()
        insights.setObjectName("card")
        iv = QVBoxLayout(insights)
        iv.setContentsMargins(13, 11, 13, 11)
        ih = QHBoxLayout()
        it = QLabel("ENDO-TWIN AI Insights")
        it.setObjectName("sectionTitle")
        ih.addWidget(it)
        ih.addStretch()
        demo = status_badge("DEMO MODE" if self.mode.mode == "demo" else "LIVE MODE", "demo" if self.mode.mode == "demo" else "measured")
        ih.addWidget(demo)
        iv.addLayout(ih)
        insight_defs = [
            ("◈", "Hormonal Pattern", "Research signal", "Within monitored range"),
            ("◉", "Stress Indicator", "EDA + HRV context", "Awaiting longitudinal baseline"),
            ("◌", "Circadian Alignment", "Pattern analysis", "Normalisation requires more data"),
            ("♧", "Activity Level", "Motion-derived", "Personal baseline comparison"),
        ]
        for icon, title, detail, state in insight_defs:
            f = QFrame()
            f.setObjectName("soft")
            h = QHBoxLayout(f)
            h.setContentsMargins(9, 7, 9, 7)
            ic = QLabel(icon)
            ic.setStyleSheet("color:#55dfff;font-size:15px;font-weight:900;")
            h.addWidget(ic)
            vv = QVBoxLayout()
            tt = QLabel(title)
            tt.setStyleSheet("color:#e8f5ff;font-weight:800;font-size:10px;")
            vv.addWidget(tt)
            dd = QLabel(detail)
            dd.setObjectName("muted")
            vv.addWidget(dd)
            h.addLayout(vv, 1)
            st = QLabel(state)
            st.setObjectName("muted")
            st.setWordWrap(True)
            st.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            h.addWidget(st)
            iv.addWidget(f)
        iv.addStretch()
        split.addWidget(signals)
        split.addWidget(insights)
        split.setSizes([700, 430])
        o.addWidget(split, 1)

        # Bottom command-center row
        bottom = QSplitter(Qt.Orientation.Horizontal)
        bottom.setChildrenCollapsible(False)

        activity = QFrame()
        activity.setObjectName("card")
        av = QVBoxLayout(activity)
        av.setContentsMargins(13, 11, 13, 11)
        av.addWidget(section_header("Recent Activity", "Local audit and workstation events"))
        self.dashboard_activity = QVBoxLayout()
        av.addLayout(self.dashboard_activity)
        bottom.addWidget(activity)

        actions = QFrame()
        actions.setObjectName("card")
        qv = QVBoxLayout(actions)
        qv.setContentsMargins(13, 11, 13, 11)
        qv.addWidget(section_header("Quick Actions", "Common research workflows"))
        action_grid = QGridLayout()
        action_grid.setSpacing(7)
        for i, (label, target, obj) in enumerate([
            ("◉  Open Patient", "patients", "primary"),
            ("＋  Add Patient", "create", "secondary"),
            ("⌁  Research Lab", "lab", "secondary"),
            ("▤  Reports", "patient", "secondary"),
        ]):
            b = QPushButton(label)
            b.setObjectName(obj)
            if target == "create":
                b.clicked.connect(self._create_patient)
            else:
                b.clicked.connect(lambda _=False, k=target: self._go(k))
            action_grid.addWidget(b, i // 2, i % 2)
        qv.addLayout(action_grid)
        device = QFrame()
        device.setObjectName("soft")
        dv = QVBoxLayout(device)
        dv.setContentsMargins(10, 8, 10, 8)
        device_label = QLabel("DEVICE STATUS")
        device_label.setObjectName("eyebrow")
        dv.addWidget(device_label)
        dev_state = QLabel("●  Sensor Pod  •  Connected")
        dev_state.setStyleSheet("color:#45e5b3;font-weight:850;font-size:10px;")
        dv.addWidget(dev_state)
        dev_ip = QLabel("USB serial / ESP bridge  •  Local-first")
        dev_ip.setObjectName("muted")
        dv.addWidget(dev_ip)
        qv.addWidget(device)
        bottom.addWidget(actions)
        bottom.setSizes([650, 480])
        o.addWidget(bottom, 1)

        return w

    def _refresh_dashboard(self):
        if not hasattr(self, "dash_kpis"):
            return
        demo = self.mode.mode == "demo"
        rows = sorted_cases() if demo else []

        # KPI values
        self.dash_kpis["Active Patients"].setText(str(len(rows)) if demo else str(len(self.db.list_patients())))
        self.dash_kpis["Live Devices"].setText("1 / 1" if self.mode.mode == "live" else "Demo")
        self.dash_kpis["Data Collected"].setText(f"{self.packet_count:,} pkts" if self.packet_count else "Ready")
        self.dash_kpis["AI Analyses"].setText(str(sum(1 for c in rows if c.tier in ("High", "Elevated"))) if demo else "—")

        baseline_ready = bool(getattr(self, "latest_row", None) and self.latest_row.get("baseline_available"))
        if hasattr(self, "baseline_status_card"):
            labels = self.baseline_status_card.findChildren(QLabel)
            if len(labels) >= 2:
                labels[1].setText("READY" if baseline_ready else "1 HOUR")
        if hasattr(self, "pcos_screen_status_card"):
            labels = self.pcos_screen_status_card.findChildren(QLabel)
            if len(labels) >= 2:
                labels[1].setText("DATA READY" if baseline_ready else "WAITING")
        if hasattr(self, "personalization_status_card"):
            labels = self.personalization_status_card.findChildren(QLabel)
            if len(labels) >= 2:
                labels[1].setText("ACTIVE" if baseline_ready else "LOCKED UNTIL BASELINE")

        # Live signal values/charts
        if self.latest_row:
            vals = {
                "hr_bpm": (self.latest_row.get("hr_bpm"), " bpm"),
                "gsr_tonic": (self.latest_row.get("gsr_tonic"), " µS"),
                "skin_temp_c": (self.latest_row.get("skin_temp_c"), " °C"),
                "activity_level": (self.latest_row.get("activity_level"), " g"),
            }
            for key, (value, suffix) in vals.items():
                label = getattr(self, f"dashboard_{key}_value", None)
                if label is not None:
                    label.setText(self._fmt(value, suffix, 1))
                chart = self.dashboard_signal_charts.get(key)
                if chart is not None:
                    chart.set_values(list(self.metric_history.get(key, [])))

        # Recent activity
        if hasattr(self, "dashboard_activity"):
            for i in reversed(range(self.dashboard_activity.count())):
                item = self.dashboard_activity.takeAt(i)
                if item.widget():
                    item.widget().deleteLater()
            events = list(reversed(self.events[-4:]))
            if not events:
                events = [
                    (datetime.now().strftime("%H:%M:%S"), "Workstation ready", "Local research environment initialized"),
                    (datetime.now().strftime("%H:%M:%S"), "Data stream", "Waiting for first feature packet"),
                ]
            for stamp, title, detail in events:
                row = QFrame()
                row.setObjectName("soft")
                h = QHBoxLayout(row)
                h.setContentsMargins(9, 6, 9, 6)
                time = QLabel(stamp[-8:])
                time.setObjectName("muted")
                time.setFixedWidth(62)
                h.addWidget(time)
                col = QVBoxLayout()
                tt = QLabel(title)
                tt.setStyleSheet("color:#e8f5ff;font-weight:800;font-size:10px;")
                col.addWidget(tt)
                dd = QLabel(detail)
                dd.setObjectName("muted")
                col.addWidget(dd)
                h.addLayout(col, 1)
                ok = QLabel("●")
                ok.setStyleSheet("color:#45e5b3;font-weight:900;")
                h.addWidget(ok)
                self.dashboard_activity.addWidget(row)

        # Preserve the existing roster/table refresh behavior if the widgets exist.
        if hasattr(self, "dash_table"):
            self.dash_table.setRowCount(0)
            for c in rows[:6]:
                rr = self.dash_table.rowCount()
                self.dash_table.insertRow(rr)
                vals = [c.patient, c.last_seen, "Good" if c.quality >= .9 else "Fair" if c.quality >= .8 else "Poor",
                        "Needs review" if c.tier in ("High","Elevated") else "Reviewed", "›"]
                for col, val in enumerate(vals):
                    it = QTableWidgetItem(str(val))
                    it.setData(Qt.ItemDataRole.UserRole, c.patient)
                    self.dash_table.setItem(rr, col, it)

    def _dashboard_row(self, row, _col):
        pid = self.dash_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self._open_case(pid)

    # ---------- patient creation ----------
    def _create_patient(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Add Patient")
        dlg.setModal(True)
        dlg.setMinimumWidth(520)
        form = QFormLayout(dlg)
        form.setContentsMargins(22, 22, 22, 18)
        form.setSpacing(10)

        name = QLineEdit()
        name.setPlaceholderText("Optional display name / alias")
        anon = QLineEdit()
        anon.setPlaceholderText("Optional anonymous ID; generated if blank")

        age = QDoubleSpinBox()
        age.setRange(0, 120)
        age.setDecimals(1)
        age.setSpecialValueText("Not supplied")

        bmi = QDoubleSpinBox()
        bmi.setRange(0, 100)
        bmi.setDecimals(1)
        bmi.setSpecialValueText("Not supplied")

        form.addRow("Display name", name)
        form.addRow("Anonymous ID", anon)
        form.addRow("Age", age)
        form.addRow("BMI", bmi)

        note = QLabel(
            "Creates a local patient record for engineering/research testing. "
            "No disease model is run automatically."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        form.addRow(note)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Ok
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            patient_id = self.db.create_patient(
                display_name=name.text().strip() or None,
                anonymous_id=anon.text().strip() or None,
                age_years=float(age.value()) if age.value() else None,
                bmi=float(bmi.value()) if bmi.value() else None,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Add Patient", f"Could not create patient:\n{exc}")
            return

        self._log_event("Patient created", patient_id)
        self._refresh_roster()
        self._open_case("LOCAL::" + patient_id)

    # ---------- patients ----------
    def _patients_page(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.setContentsMargins(25, 18, 20, 15)
        o.setSpacing(11)
        t = QLabel("Patients")
        t.setObjectName("title")
        o.addWidget(t)
        s = QLabel("Patient roster with search, condition filtering, research-risk sorting and quality context.")
        s.setObjectName("muted")
        o.addWidget(s)

        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search patient / alias / module…")
        self.search.textChanged.connect(self._refresh_roster)
        bar.addWidget(self.search, 1)

        self.cond = QComboBox()
        self.cond.addItems(condition_list())
        self.cond.currentTextChanged.connect(self._refresh_roster)
        bar.addWidget(self.cond)

        self.sorter = QComboBox()
        self.sorter.addItems(["Priority", "Risk", "Condition"])
        self.sorter.currentTextChanged.connect(self._refresh_roster)
        bar.addWidget(self.sorter)

        add = QPushButton("+ Add Patient")
        add.setObjectName("primary")
        add.clicked.connect(self._create_patient)
        bar.addWidget(add)
        o.addLayout(bar)

        note = QLabel("DEMO MODE values are synthetic UI examples only — not diagnoses, not clinical severity scores, and not validation metrics.")
        note.setObjectName("warning")
        note.setWordWrap(True)
        o.addWidget(note)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Patient", "Alias", "Condition / module", "Tier*", "Research risk*", "Quality", "Last update"]
        )
        self._fit_table(self.table)
        self.table.cellClicked.connect(self._select_row)
        o.addWidget(self.table, 1)
        return w

    def _fit_table(self, table):
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)

    def _refresh_roster(self):
        if not hasattr(self, "table"):
            return
        demo = self.mode.mode == "demo"
        self.table.setRowCount(0)
        q = self.search.text().lower()
        cond = self.cond.currentText() if demo else "All"
        sk = self.sorter.currentText().lower() if demo else "priority"

        if demo:
            rows = sorted_cases(
                cond,
                "risk" if sk == "risk" else "condition" if sk == "condition" else "priority",
            )
            for c in rows:
                if q and q not in f"{c.patient} {c.alias} {c.condition}".lower():
                    continue
                r = self.table.rowCount()
                self.table.insertRow(r)
                vals = [
                    c.patient, c.alias, c.condition, c.tier, f"{c.risk:.0f}%",
                    f"{c.quality*100:.0f}%", c.last_seen
                ]
                for col, val in enumerate(vals):
                    it = QTableWidgetItem(str(val))
                    if col == 0:
                        it.setData(Qt.ItemDataRole.UserRole, c.patient)
                    self.table.setItem(r, col, it)

        try:
            local = self.db.list_patients()
        except Exception:
            local = []
        for p in local:
            pid = str(p.get("patient_id", ""))
            anon = str(p.get("anonymous_id") or pid)
            alias = str(p.get("display_name") or anon)
            searchable = f"{pid} {anon} {alias}"
            if q and q not in searchable.lower():
                continue
            if demo and cond != "All":
                continue
            r = self.table.rowCount()
            self.table.insertRow(r)
            vals = [
                anon, alias, "Local patient", "Unknown",
                "UNKNOWN", "UNKNOWN", p.get("updated_at", "—")
            ]
            for col, val in enumerate(vals):
                it = QTableWidgetItem(str(val))
                if col == 0:
                    it.setData(Qt.ItemDataRole.UserRole, "LOCAL::" + pid)
                self.table.setItem(r, col, it)

        self._refresh_dashboard()

    def _select_row(self, row, _col):
        pid = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self._open_case(pid)

    def _search_patient(self):
        q = self.global_search.text().strip().lower()
        if not q:
            return
        if self.mode.mode == "demo":
            hit = next((c for c in sorted_cases() if q in f"{c.patient} {c.alias} {c.condition}".lower()), None)
            if hit:
                self._open_case(hit.patient)
        else:
            try:
                local = self.db.list_patients()
            except Exception:
                local = []
            hit = next((p for p in local if q in str(p).lower()), None)
            if hit:
                self._open_case(str(hit.get("patient_id") or hit.get("anonymous_id")))

    # ---------- patient workspace ----------
    def _patient_page(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(24, 15, 20, 14)
        outer.setSpacing(9)

        self.patient_header_host = QVBoxLayout()
        outer.addLayout(self.patient_header_host)

        self.patient_tabs = QComboBox()
        self.patient_tabs.setObjectName("patientTabs")
        self.patient_tab_names = [
            "Overview", "Timeline", "Sensor data", "Trends", "Ultrasound",
            "AI / Models", "Clinical inputs", "Reports", "Notes", "Provenance", "Audit"
        ]
        # A compact tab row using QPushButtons is more stable across Qt styles.
        tabrow = QHBoxLayout()
        self.tab_buttons = {}
        for name in self.patient_tab_names:
            b = QPushButton(name)
            b.setObjectName("tab")
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, n=name: self._show_patient_tab(n))
            tabrow.addWidget(b)
            self.tab_buttons[name] = b
        tabrow.addStretch()
        outer.addLayout(tabrow)

        self.patient_stack = QStackedWidget()
        outer.addWidget(self.patient_stack, 1)
        return page

    def _rebuild_patient_header(self):
        while self.patient_header_host.count():
            item = self.patient_header_host.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        p = self._profile()
        if not p:
            box = QFrame()
            box.setObjectName("patientHeader")
            lay = QVBoxLayout(box)
            lay.addWidget(QLabel("No patient selected"))
            lay.addWidget(QLabel("Choose a patient from the Dashboard or Patients screen."))
            self.patient_header_host.addWidget(box)
            return

        self.patient_header_host.addWidget(self._patient_header())

        alert = QHBoxLayout()
        if self.current_case:
            text = f"{p['tier']} synthetic research-screening tier • research risk {p['risk']:.0f}%"
            alert.addWidget(pill(text, "#2b274c", "#b7a8ff"))
        else:
            alert.addWidget(pill("LIVE SESSION • model output not run", "#2a2a38", "#b9bfd2"))
        alert.addStretch()
        box = QWidget()
        box.setLayout(alert)
        self.patient_header_host.addWidget(box)

    def _show_patient_tab(self, name):
        for n, b in self.tab_buttons.items():
            b.setChecked(n == name)
        idx = next((i for i, n in enumerate(self.patient_tab_names) if n == name), 0)
        self.patient_stack.setCurrentIndex(idx)

    def _build_patient_tabs(self):
        while self.patient_stack.count():
            old = self.patient_stack.widget(0)
            self.patient_stack.removeWidget(old)
            old.deleteLater()

        builders = {
            "Overview": self._patient_overview,
            "Timeline": self._patient_timeline,
            "Sensor data": self._patient_sensor,
            "Trends": self._patient_trends,
            "Ultrasound": self._patient_ultrasound,
            "AI / Models": self._patient_models,
            "Clinical inputs": self._patient_clinical,
            "Reports": self._patient_reports,
            "Notes": self._patient_notes,
            "Provenance": self._patient_provenance,
            "Audit": self._patient_audit,
        }
        for name in self.patient_tab_names:
            self.patient_stack.addWidget(builders[name]())
        self._show_patient_tab("Overview")

    def _patient_overview(self):
        p = self._profile()
        w = QWidget()
        o = QVBoxLayout(w)
        o.setSpacing(12)

        if not p:
            o.addWidget(card("Patient workspace", "Select a patient", "All patient-scoped panels remain blank until a patient is selected."))
            o.addStretch()
            return w

        charts = QGridLayout()
        charts.setSpacing(12)
        if self.current_case:
            chart_sets = {
                "Heart rate": [p["hr"] + d for d in (-4,-2,2,4,-1,1,3,-3,0,2,-2,1,4)],
                "HRV (RMSSD)": [p["hrv"] + d for d in (3,-2,5,-4,2,6,-3,1,-1,4,-2,3)],
                "Sleep duration": [p["sleep"] + d/10 for d in (-4,2,-1,3,0,-2,2,-3,1)],
            }
            meta = [("Heart rate", self._fmt(p["hr"], " bpm", 2), "−3.2 vs 7d ago", "MEASURED"),
                    ("HRV (RMSSD)", self._fmt(p["hrv"], " ms", 2), "−2.1 vs 7d ago", "DERIVED"),
                    ("Sleep duration", self._fmt(p["sleep"], " h", 1), "Longitudinal self-report context", "PATIENT-REPORTED")]
            kinds = ["good", "fair", "fair" if p["sleep"] < 6.5 else "good"]
        else:
            live = self.latest_row or {}
            chart_sets = {}
            meta = [
                ("Heart rate", self._fmt(live.get("hr_bpm"), " bpm", 1), "Live processed stream", "MEASURED"),
                ("HRV (RMSSD)", self._fmt(live.get("rmssd_ms"), " ms", 1), "Beat-to-beat derived feature", "DERIVED"),
                ("Skin temperature", self._fmt(live.get("skin_temp_c"), " °C", 1), "Validity-gated", "MEASURED"),
            ]
            kinds = ["good", "good", "good"]

        for i, ((name, val, delta, prov), kind) in enumerate(zip(meta, kinds)):
            values = chart_sets.get(name, []) if 'chart_sets' in locals() else []
            if not values and self.latest_row:
                seed = self.latest_row.get({"Heart rate":"hr_bpm","HRV (RMSSD)":"rmssd_ms","Skin temperature":"skin_temp_c"}.get(name, ""), None)
                values = [seed] if seed is not None else []
            f = self._metric_panel(name, val, "", delta, prov, values, kind)
            charts.addWidget(f, 0, i)

        o.addLayout(charts)

        split = QGridLayout()
        insight = QFrame()
        insight.setObjectName("card")
        iv = QVBoxLayout(insight)
        iv.addWidget(section_header("Latest insight", "Evidence boundary stays visible next to any model-facing narrative."))
        if self.current_case:
            iv.addWidget(pill("Synthetic research-screening example", "#4b2d27", "#f29a83"))
            iv.addWidget(QLabel(
                "The case contains synthetic demo patterns only. Drivers: " +
                " • ".join(p["drivers"])
            ))
            iv.addWidget(QLabel(
                "Research risk is synthetic UI data and is not a diagnosis, validated probability, or clinical severity score."
            ))
        else:
            iv.addWidget(pill("LIVE SESSION • no disease-model result", "#2a2e3c", "#b7c0d2"))
            iv.addWidget(QLabel("Live sensor processing can expose measurements and derived features; it does not by itself establish a disease-model result."))
        warn = QLabel(f"◷  {DISCLAIMER}  Clinical validation: NOT ESTABLISHED")
        warn.setObjectName("warning")
        warn.setWordWrap(True)
        iv.addWidget(warn)
        split.addWidget(insight, 0, 0)

        activity = QFrame()
        activity.setObjectName("card")
        av = QVBoxLayout(activity)
        av.addWidget(section_header("Recent activity", "Patient-scoped events"))
        events = self._patient_events()
        for date, title, detail in events[:4]:
            line = QLabel(f"<b>{date}</b><br><span style='color:#dde2ec'>{title}</span><br><span style='color:#8e98ad'>{detail}</span>")
            line.setWordWrap(True)
            av.addWidget(line)
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("color:#30394b;")
            av.addWidget(sep)
        split.addWidget(activity, 0, 1)
        split.setColumnStretch(0, 1)
        split.setColumnStretch(1, 1)
        o.addLayout(split)
        return w

    def _patient_events(self):
        p = self._profile()
        if not p:
            return []
        if self.current_case:
            return [
                ("Today", "Sync received", "system • " + p["pid"]),
                ("Yesterday", "Research screening example loaded", "local workstation"),
                ("2 days ago", "Synthetic demo case viewed", "doctor workstation"),
                ("3 days ago", "Observation period updated", "demo data"),
            ]
        return [
            ("Now", "Live session", self.mode.port),
            ("Today", "Patient record opened", "local database"),
            ("—", "Disease model", "not run"),
        ]

    def _patient_timeline(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.setSpacing(10)
        box = QFrame()
        box.setObjectName("card")
        b = QVBoxLayout(box)
        b.addWidget(section_header("Full event timeline", "Chronological patient-scoped activity"))
        for date, title, detail in self._patient_events() + [("Earlier", "Patient record created", "local database")]:
            row = QHBoxLayout()
            dot = QLabel("◉")
            dot.setStyleSheet("color:#9aaeff;font-size:16px;")
            row.addWidget(dot)
            col = QVBoxLayout()
            d = QLabel(str(date))
            d.setObjectName("muted")
            col.addWidget(d)
            tx = QLabel(title)
            tx.setStyleSheet("font-weight:850;color:#e7ebf3;")
            col.addWidget(tx)
            de = QLabel(detail)
            de.setObjectName("muted")
            de.setWordWrap(True)
            col.addWidget(de)
            row.addLayout(col, 1)
            b.addLayout(row)
        o.addWidget(box)
        return w

    def _patient_sensor(self):
        w = QWidget()
        o = QVBoxLayout(w)
        banner = QFrame()
        banner.setObjectName("hero")
        bv = QVBoxLayout(banner)
        bv.addWidget(QLabel("Provenance is preserved per stream"))
        bv.addWidget(QLabel("Every value below carries a MEASURED or DERIVED boundary. Nothing here is model-inferred."))
        o.addWidget(banner)

        specs = [
            ("Heart rate", "hr_bpm", "bpm", "MEASURED"),
            ("Heart rate variability", "rmssd_ms", "ms (RMSSD)", "DERIVED"),
            ("GSR / EDA", "gsr_tonic", "µS proxy", "MEASURED"),
            ("Skin temperature", "skin_temp_c", "°C", "MEASURED"),
        ]
        for title, key, unit, prov in specs:
            panel = QFrame()
            panel.setObjectName("card")
            v = QVBoxLayout(panel)
            head = QHBoxLayout()
            head.addWidget(QLabel(title))
            head.addStretch()
            head.addWidget(status_badge(prov, "measured" if prov=="MEASURED" else "derived"))
            v.addLayout(head)
            chart = Sparkline(title, unit)
            if self.current_case:
                base = {
                    "hr_bpm": self.current_case.hr,
                    "rmssd_ms": self.current_case.hrv,
                    "gsr_tonic": 18.0 + self.current_case.activity/3,
                    "skin_temp_c": self.current_case.temp,
                }[key]
                offsets = [((i * 7) % 9) - 4 for i in range(28)]
                chart.set_values([base + o * (0.08 if key=="skin_temp_c" else 1.0) for o in offsets])
            elif self.latest_row and self.latest_row.get(key) is not None:
                chart.set_values([float(self.latest_row[key])])
            v.addWidget(chart)
            o.addWidget(panel)
        return w

    def _patient_trends(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.setSpacing(12)
        o.addWidget(section_header(
            "Physiological trends",
            "Continuous observations and derived features. Gaps indicate unavailable or quality-gated data; they are not imputed."
        ))
        grid = QGridLayout()
        grid.setSpacing(12)
        names = [
            ("Heart rate", "bpm", "hr_bpm"),
            ("HRV / RMSSD", "ms", "rmssd_ms"),
            ("Activity", "%", "activity_level"),
            ("Skin temperature", "°C", "skin_temp_c"),
        ]
        for i, (name, unit, key) in enumerate(names):
            panel = QFrame()
            panel.setObjectName("card")
            v = QVBoxLayout(panel)
            v.setContentsMargins(14, 12, 14, 12)
            top = QHBoxLayout()
            title = QLabel(name)
            title.setStyleSheet("font-size:13px;font-weight:850;color:#e7ebf3;")
            top.addWidget(title)
            top.addStretch()
            top.addWidget(status_badge("LIVE" if self.mode.mode == "live" else "DEMO", "measured" if self.mode.mode == "live" else "info"))
            v.addLayout(top)
            chart = Sparkline(name, unit)
            chart.setMinimumHeight(230)
            values = list(self.metric_history.get(key, []))
            if not values and self.current_case:
                p = self.current_case
                base = {"hr_bpm": p.hr, "rmssd_ms": p.hrv, "activity_level": p.activity, "skin_temp_c": p.temp}[key]
                pattern = [0, 2, -1, 4, 1, -3, 2, -2, 3, 0, -4, 2, 1, -1, 4, -2, 0, 3, 1, -2, 3, 0]
                scale = 0.07 if key == "skin_temp_c" else 1.0
                values = [base + x * scale for x in pattern]
            chart.set_values(values)
            v.addWidget(chart, 1)
            self.trend_charts[key] = chart
            grid.addWidget(panel, i // 2, i % 2)
        o.addLayout(grid)
        return w

    def _patient_ultrasound(self):
        w = QWidget()
        o = QVBoxLayout(w)
        hero = QFrame()
        hero.setObjectName("hero")
        h = QHBoxLayout(hero)
        left = QVBoxLayout()
        left.addWidget(QLabel("Ultrasound evidence"))
        status = QLabel("IMAGE-DERIVED • source required")
        status.setObjectName("muted")
        left.addWidget(status)
        self.image_status = QLabel("No validated image attached")
        self.image_status.setStyleSheet("font-size:18px;font-weight:850;color:#eef2f7;")
        left.addWidget(self.image_status)
        load = QPushButton("Attach image")
        load.setObjectName("primary")
        load.clicked.connect(self._attach_image)
        left.addWidget(load)
        h.addLayout(left, 1)
        self.image_preview = QLabel("UNKNOWN")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumSize(260, 190)
        self.image_preview.setStyleSheet("background:#161b25;border:1px solid #3a4457;border-radius:10px;color:#7f8a9e;font-weight:800;")
        h.addWidget(self.image_preview)
        o.addWidget(hero)

        g = QGridLayout()
        fields = [
            ("Image status", "UNKNOWN", "No validated image attached"),
            ("Follicle count", "UNKNOWN", "Not estimated by this workstation"),
            ("Ovarian morphology", "UNKNOWN", "No unsupported anatomical inference"),
            ("Source", "IMAGE-DERIVED", "Provenance retained only when an image is supplied"),
        ]
        for i, (a, b, c) in enumerate(fields):
            g.addWidget(card(a, b, c), 0, i)
        o.addLayout(g)
        warn = QLabel("The workstation intentionally does not invent anatomy, follicle counts or PCOS morphology. A future validated imaging model must document cohort split, uncertainty and provenance.")
        warn.setObjectName("warning")
        warn.setWordWrap(True)
        o.addWidget(warn)
        o.addStretch()
        return w

    def _attach_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Attach ultrasound image", str(ROOT), "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if not path:
            return
        pix = QPixmap(path)
        if pix.isNull():
            QMessageBox.warning(self, "Ultrasound", "Could not load that image.")
            return
        self.image_path = path
        self.image_preview.setPixmap(pix.scaled(420, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.image_status.setText(Path(path).name)
        self._log_event("Ultrasound source attached", Path(path).name)

    def _patient_models(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.addWidget(section_header("AI / Models", "Transparent model-facing surface with explicit validation and provenance boundaries."))

        if self.current_case:
            hero = QFrame()
            hero.setObjectName("card")
            hv = QVBoxLayout(hero)
            top = QHBoxLayout()
            top.addWidget(QLabel("CHRONO-PCOS"))
            top.addStretch()
            top.addWidget(pill("SYNTHETIC / DEMO_DATA", "#3a2a2b", "#f0a5a0"))
            hv.addLayout(top)
            hv.addWidget(QLabel(f"Research-risk example: {self.current_case.risk:.0f}%"))
            hv.addWidget(QLabel("Synthetic showcase value only — not a probability, diagnosis, clinical severity score or validation result."))
            o.addWidget(hero)
        else:
            o.addWidget(card("CHRONO-PCOS", "NOT RUN", "Live workstation view deliberately does not fabricate disease-model output."))

        g = QGridLayout()
        blocks = [
            ("What did the model layer use?", "Wearable physiology + longitudinal context + disease-specific inputs when available."),
            ("How good was the data?", self._data_quality_text(self._profile()["quality"])[0] if self._profile() else "UNKNOWN"),
            ("What is missing?", "Validated clinical and imaging evidence may be missing."),
            ("Clinical validation", "NOT ESTABLISHED"),
            ("What this result does not mean", "It is not a diagnosis, lab-equivalent hormone measurement or validated clinical probability."),
            ("Provenance", "MODEL-INFERRED only for an actual model run; DEMO_DATA for synthetic examples."),
        ]
        for i, (a, b) in enumerate(blocks):
            f = QFrame()
            f.setObjectName("card")
            v = QVBoxLayout(f)
            h = QLabel(a.upper())
            h.setStyleSheet("color:#e2e6ef;font-weight:850;font-size:10px;")
            v.addWidget(h)
            x = QLabel(b)
            x.setWordWrap(True)
            x.setObjectName("muted")
            v.addWidget(x)
            g.addWidget(f, i//2, i%2)
        o.addLayout(g)
        o.addStretch()
        return w

    def _patient_clinical(self):
        w = QWidget()
        o = QVBoxLayout(w)
        box = QFrame()
        box.setObjectName("card")
        v = QVBoxLayout(box)
        v.addWidget(section_header("Patient-entered / clinician-entered data", "Shown as source-labelled contextual inputs."))
        p = self._profile()
        rows = [
            ("Age", p["age"] if p else "—", "CLINICALLY ENTERED / LOCAL"),
            ("BMI", p["bmi"] if p else "—", "CLINICALLY ENTERED / LOCAL"),
            ("Average cycle length", "NOT SUPPLIED", "CLINICALLY ENTERED"),
            ("Cycle variability", "NOT SUPPLIED", "PATIENT-REPORTED"),
            ("Hirsutism", "NOT SUPPLIED", "PATIENT-REPORTED"),
        ]
        for name, value, src in rows:
            row = QHBoxLayout()
            row.addWidget(QLabel(name))
            row.addStretch()
            row.addWidget(QLabel(str(value)))
            row.addWidget(status_badge(src, "neutral"))
            v.addLayout(row)
        o.addWidget(box)
        info = QLabel("Clinical inputs are not inferred from wearable data in this workstation. Production workflows should preserve who entered each value, when, and the audit trail.")
        info.setObjectName("warning")
        info.setWordWrap(True)
        o.addWidget(info)
        o.addStretch()
        return w

    def _patient_reports(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.addWidget(section_header("Reports", "Traceable report assembly keeps observations, quality, models, uncertainty and limitations separate."))
        card1 = QFrame()
        card1.setObjectName("card")
        v = QVBoxLayout(card1)
        v.addWidget(QLabel("My monitoring / clinical review"))
        b = QPushButton("Generate report file")
        b.setObjectName("primary")
        b.clicked.connect(self._generate_report)
        v.addWidget(b, 0, Qt.AlignmentFlag.AlignLeft)
        o.addWidget(card1)

        p = self._profile()
        txt = "Patient → acquisition → quality → features → baseline → longitudinal → model → uncertainty → limitations"
        o.addWidget(card("Report structure", txt, "No estimate is promoted to measurement."))
        if self.current_case:
            o.addWidget(card("Demo content", "Synthetic showcase", f"{p['pid']} • DEMO_DATA • risk {p['risk']:.0f}%"))
        else:
            o.addWidget(card("Live content", "Observations only", "Disease-model output remains NOT RUN in this workstation view."))
        o.addStretch()
        return w

    def _generate_report(self):
        p = self._profile()
        if not p:
            QMessageBox.information(self, "Report", "Select a patient first.")
            return
        reports = ROOT / "data" / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = reports / f"{p['pid'].replace(' ','_')}_{stamp}.txt"
        mode = "DEMO_DATA" if self.current_case else "LIVE_SESSION"
        lines = [
            "ENDO-TWIN NEXUS — RESEARCH WORKSTATION REPORT",
            f"Generated: {datetime.now().isoformat(timespec='seconds')}",
            f"Patient: {p['pid']} • {p['alias']}",
            f"Mode: {mode}",
            DISCLAIMER,
            "",
            "OBSERVATIONS",
            f"Heart rate: {self._fmt(self.latest_row.get('hr_bpm') if self.latest_row else p.get('hr'), ' bpm', 1)}",
            f"HRV RMSSD: {self._fmt(self.latest_row.get('rmssd_ms') if self.latest_row else p.get('hrv'), ' ms', 1)}",
            f"Skin temperature: {self._fmt(self.latest_row.get('skin_temp_c') if self.latest_row else p.get('temp'), ' °C', 1)}",
            "",
            "MODEL / SCREENING",
            ("Synthetic research-risk example only: " + f"{p['risk']:.0f}%" if self.current_case else "NOT RUN"),
            "Clinical validation: NOT ESTABLISHED",
            "",
            "LIMITATIONS",
            "This report is for a research prototype. It is not a medical device and does not establish a diagnosis.",
        ]
        path.write_text("\n".join(lines), encoding="utf-8")
        self._log_event("Report generated", str(path))
        QMessageBox.information(self, "Report generated", f"Saved locally:\n{path}")

    def _patient_notes(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.addWidget(section_header("Notes", "Local-first clinical/research notes. Persist only what your workflow is authorized to store."))
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Write a patient-scoped note…")
        self.notes_edit.setPlainText(self.note_cache)
        o.addWidget(self.notes_edit, 1)
        row = QHBoxLayout()
        save = QPushButton("Save local note")
        save.setObjectName("primary")
        save.clicked.connect(self._save_note)
        clear = QPushButton("Clear")
        clear.setObjectName("secondary")
        clear.clicked.connect(self.notes_edit.clear)
        row.addWidget(save)
        row.addWidget(clear)
        row.addStretch()
        o.addLayout(row)
        return w

    def _save_note(self):
        self.note_cache = self.notes_edit.toPlainText()
        p = self._profile()
        if not p:
            return
        notes = ROOT / "data" / "notes"
        notes.mkdir(parents=True, exist_ok=True)
        path = notes / f"{p['pid'].replace(' ','_')}.txt"
        path.write_text(self.note_cache, encoding="utf-8")
        self._log_event("Patient note saved", str(path))
        QMessageBox.information(self, "Notes", "Local note saved.")

    def _patient_provenance(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.addWidget(section_header("Provenance", "Source labels are displayed next to the data path instead of hidden in metadata."))
        t = QTableWidget(0, 4)
        t.setHorizontalHeaderLabels(["Stream / feature", "Provenance", "Current source", "Interpretation boundary"])
        self._fit_table(t)
        rows = [
            ("PPG waveform", "MEASURED" if self.mode.mode=="live" else "DEMO_DATA", "MAX30102 / demo stream", "Raw signal"),
            ("Heart rate", "MEASURED" if self.mode.mode=="live" else "DEMO_DATA", "PPG processing", "Observed / source-derived"),
            ("HRV RMSSD", "DERIVED", "PPG beat intervals", "Computed feature"),
            ("GSR / EDA", "MEASURED" if self.mode.mode=="live" else "DEMO_DATA", "GSR channel / demo", "Conductance proxy"),
            ("Skin temperature", "MEASURED" if self.mode.mode=="live" else "DEMO_DATA", "DS18B20 / demo", "Validity-gated"),
            ("Disease-model output", "MODEL-INFERRED / DEMO_DATA", "CHRONO-PCOS", "Only when an actual model run exists"),
            ("Ultrasound", "IMAGE-DERIVED", self.image_path or "No image attached", "Anatomical inference remains UNKNOWN"),
        ]
        for row in rows:
            r = t.rowCount()
            t.insertRow(r)
            for c, val in enumerate(row):
                t.setItem(r, c, QTableWidgetItem(str(val)))
        o.addWidget(t, 1)
        return w

    def _patient_audit(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.addWidget(section_header("Audit", "Local audit view for this research workstation session."))
        metrics = QGridLayout()
        metrics.addWidget(card("Packets received", str(self.packet_count), "Current session"), 0, 0)
        metrics.addWidget(card("Bridge inbox", str(self.bridge.received_count), "Patient packages received"), 0, 1)
        metrics.addWidget(card("Mode", "DEMO" if self.mode.mode=="demo" else "LIVE", "Chosen at startup"), 0, 2)
        metrics.addWidget(card("Model status", "DEMO ONLY" if self.current_case else "NOT RUN", "Clinical validation not established"), 0, 3)
        o.addLayout(metrics)
        t = QTableWidget(0, 3)
        t.setHorizontalHeaderLabels(["Time", "Event", "Detail"])
        self._fit_table(t)
        for row in reversed(self.events):
            r = t.rowCount()
            t.insertRow(r)
            for c, val in enumerate(row):
                t.setItem(r, c, QTableWidgetItem(str(val)))
        o.addWidget(t, 1)
        return w

    def _mobile_page(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.setContentsMargins(25, 18, 20, 15)
        o.addWidget(QLabel("Mobile Link"))
        o.itemAt(0).widget().setObjectName("title")
        o.addWidget(QLabel("Pair Patient Android on the same trusted LAN. Research/demo infrastructure only."))
        info = QGridLayout()
        self.mobile_endpoint = card("Workstation endpoint", self.bridge.endpoint, "Doctor bridge • port 7777")
        self.mobile_code = card("Pairing code", self.bridge.pair_code, "Regenerated at bridge restart")
        self.mobile_received = card("Received packages", str(self.bridge.received_count), "data/bridge/inbox")
        self.mobile_security = card("Security", "Trusted LAN", "Production needs TLS + strong authentication + audit")
        for i, f in enumerate([self.mobile_endpoint, self.mobile_code, self.mobile_received, self.mobile_security]):
            info.addWidget(f, 0, i)
        o.addLayout(info)
        copy = QPushButton("Copy pairing instructions")
        copy.setObjectName("primary")
        copy.clicked.connect(self._copy_mobile)
        o.addWidget(copy, 0, Qt.AlignmentFlag.AlignLeft)
        restart = QPushButton("Restart bridge")
        restart.setObjectName("secondary")
        restart.clicked.connect(self._restart_bridge)
        o.addWidget(restart, 0, Qt.AlignmentFlag.AlignLeft)
        hint = QLabel("The patient Android transport stays patient-scoped. Its current payload path is intentionally DEMO_DATA.")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        o.addWidget(hint)
        o.addStretch()
        return w

    def _copy_mobile(self):
        QApplication.clipboard().setText(
            f"ENDO-TWIN Doctor Workstation\nAddress: {self.bridge.endpoint}\nPairing code: {self.bridge.pair_code}\nUse Patient Android → Connect."
        )
        QMessageBox.information(self, "Mobile Link", "Pairing instructions copied.")

    def _restart_bridge(self):
        self.bridge.stop()
        self.bridge = EndoTwinBridgeServer(ROOT, 7777)
        try:
            self.bridge.start()
        except OSError as e:
            QMessageBox.warning(self, "Mobile Link", str(e))
            return
        self.mobile_endpoint.findChildren(QLabel)[1].setText(self.bridge.endpoint)
        self.mobile_code.findChildren(QLabel)[1].setText(self.bridge.pair_code)
        self._log_event("Mobile bridge restarted", self.bridge.endpoint)

    def _settings_page(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.setContentsMargins(25, 18, 20, 15)
        t = QLabel("Settings")
        t.setObjectName("title")
        o.addWidget(t)
        o.addWidget(QLabel("Workstation preferences, data boundary and research status."))
        g = QGridLayout()
        mode = "DEMO MODE" if self.mode.mode == "demo" else f"LIVE SENSOR MODE • {self.mode.port}"
        g.addWidget(card("Data source", mode, "Selected at startup and fixed for this run"), 0, 0)
        g.addWidget(card("Transport", self.bridge.endpoint, "Local bridge for Patient Android"), 0, 1)
        g.addWidget(card("Storage", "LOCAL-FIRST", "Patient-scoped data and reports remain on this workstation"), 0, 2)
        g.addWidget(card("Validation", "NOT ESTABLISHED", "Research prototype; not a clinical device"), 0, 3)
        o.addLayout(g)
        safety = QLabel(
            "Safety boundary: ENDO-TWIN is the platform; CHRONO-PCOS is its first disease-specific research module. "
            "Measured, derived, patient-reported, image-derived, model-inferred and demo values must remain distinguishable."
        )
        safety.setObjectName("warning")
        safety.setWordWrap(True)
        o.addWidget(safety)
        o.addStretch()
        return w

    # ---------- live updates ----------
    def _on_sample(self, _sample):
        self.packet_count += 1

    def _on_state(self, state):
        shown = state.upper().replace("_", " ")
        self.side_state.setText(shown)
        self._refresh_header()
        self._log_event("Sensor state", state)

    def _on_error(self, msg):
        self.side_state.setText("ERROR • " + msg)
        self._log_event("Sensor error", msg)

    def _on_features(self, row):
        self.latest_row = row
        self.quality_badge.setText("●  " + self._data_quality_text(row.get("signal_quality"))[0])
        if hasattr(self, "live_signal_placeholder"):
            self.live_signal_placeholder.setText(self._fmt(row.get("hr_bpm"), " bpm", 1))
        # Update metric charts when they exist.
        history_map = {"hr_bpm": row.get("hr_bpm"), "rmssd_ms": row.get("rmssd_ms"), "activity_level": row.get("activity_level"), "skin_temp_c": row.get("skin_temp_c"), "gsr_tonic": row.get("gsr_tonic"), "spo2_pct": row.get("spo2_pct")}
        for key, value in history_map.items():
            if value is not None:
                try:
                    self.metric_history[key].append(float(value))
                except (TypeError, ValueError):
                    pass
            if key in self.trend_charts:
                self.trend_charts[key].set_values(list(self.metric_history[key]))

        mapping = {
            "Heart rate": row.get("hr_bpm"),
            "HRV (RMSSD)": row.get("rmssd_ms"),
            "Skin temperature": row.get("skin_temp_c"),
        }
        for name, value in mapping.items():
            if name in self.metric_cards:
                big, chart = self.metric_cards[name]
                suffix = {"Heart rate":" bpm","HRV (RMSSD)":" ms","Skin temperature":" °C"}[name]
                big.setText(self._fmt(value, suffix, 1))
                if value is not None:
                    chart.set_value(value)
        self._log_event("Feature update", f"{row.get('gating','QUALITY_GATE')} • {row.get('provenance','UNKNOWN')}")

    def _open_case(self, pid: str):
        self.current_case = None
        self.live_patient = None

        if isinstance(pid, str) and pid.startswith("LOCAL::"):
            local_id = pid.split("::", 1)[1]
            try:
                self.live_patient = self.db.get_patient(local_id)
            except Exception:
                self.live_patient = None
        elif self.mode.mode == "demo":
            self.current_case = next((x for x in sorted_cases() if x.patient == pid), None)
            if self.current_case is None:
                try:
                    self.live_patient = self.db.get_patient(pid)
                except Exception:
                    self.live_patient = None
        else:
            try:
                self.live_patient = self.db.get_patient(pid)
            except Exception:
                self.live_patient = None

        if not self.current_case and not self.live_patient:
            return
        self._log_event("Patient opened", pid)
        self._rebuild_patient_header()
        self._build_patient_tabs()
        self._go("patient")

    def _attach_patient_signal_to_overview(self):
        pass


def run():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    mode = choose_mode("ENDO-TWIN • Doctor Workstation")
    if mode is None:
        return 0
    w = DoctorWindow(mode)
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
