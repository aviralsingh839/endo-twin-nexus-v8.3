#!/usr/bin/env python3
"""ENDO-TWIN V8.6 Patient Workstation — calm patient-facing research UI."""
from __future__ import annotations

import sys
import time
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QStackedWidget, QTextEdit, QVBoxLayout, QWidget,
    QProgressBar
)

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from desktop.demo_data import DEMO_CASES
from desktop.workstation_runtime import LiveSession, ModeConfig, Sparkline, choose_mode, RingGauge, metric_card, trend_panel
from desktop.workstation_theme import APP_QSS, card, section_header, status_badge
from src.personal_twin.profile_store import load_state, profile_summary, get_profile, select_participant, save_profile
from src.personal_twin.adaptive_model import PersonalAdaptiveModel
from src.personal_twin.baseline_capture import BaselineCapture
from src.personal_twin.baseline_store import baseline_summary
from src.personal_twin.participant_selector import choose_participant
from src.ui.pcos_complication_panel import PCODProgressPanel
from services.bridge.server import EndoTwinBridgeServer

DISCLAIMER = "Research / risk-screening output — not a medical diagnosis."


class PatientWindow(QMainWindow):
    """Single-patient local-first workstation inspired by the uploaded patient UI."""

    def __init__(self, mode: ModeConfig, participant_id: str):
        super().__init__()
        self.mode = mode
        self.participant_id = str(participant_id)
        self.profile = get_profile(self.participant_id)
        self.case = DEMO_CASES[0]
        self.latest_row = None
        self.feature_history = []
        self.note_text = ""
        self.metric_labels = {}
        self.visual_graphs = {}
        self.charts = {}
        self.personal_model = PersonalAdaptiveModel(self.participant_id)
        self.baseline_capture = BaselineCapture(self.participant_id, duration_s=60.0, min_samples=60, min_quality=0.45)
        self._baseline_ui_timer = QTimer(self)
        self._baseline_ui_timer.timeout.connect(self._update_baseline_capture_ui)
        self._baseline_ui_timer.start(500)

        self.bridge = EndoTwinBridgeServer(ROOT, 7778)
        self.bridge.start()

        self.session = None

        self.setWindowTitle("Endo-Twin Nexus — Patient Desktop • V8.6")
        self.resize(1480, 920)
        self.setMinimumSize(1120, 740)
        self.setStyleSheet(APP_QSS)
        self._build()
        self._refresh_header()

        self.session = LiveSession(mode, self)
        self.session.features_updated.connect(self._on_features)
        self.session.calibration_received.connect(self._on_ppg_calibration)
        self.session.state_changed.connect(self._on_state)
        self.session.error_received.connect(self._on_error)
        self.session.start()

    def closeEvent(self, event):
        self.session.stop()
        self.bridge.stop()
        event.accept()

    def _build(self):
        root = QWidget()
        self.setCentralWidget(root)
        shell = QGridLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(208)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(14, 18, 10, 16)

        brand = QLabel("Endo-Twin Nexus")
        brand.setObjectName("brand")
        sl.addWidget(brand)
        tag = QLabel("PATIENT WORKSPACE")
        tag.setObjectName("eyebrow")
        sl.addWidget(tag)
        desc = QLabel("Your measurements, history and reports — in one local-first view.")
        desc.setObjectName("muted")
        desc.setWordWrap(True)
        sl.addWidget(desc)
        sl.addSpacing(15)

        work = QLabel("WORKSPACE")
        work.setObjectName("eyebrow")
        sl.addWidget(work)

        self.nav = {}
        for key, text in [
            ("home", "▦  Overview"),
            ("health", "♥  My Health"),
            ("measure", "∿  Measurements"),
            ("timeline", "◷  Timeline"),
            ("reports", "▤  Reports"),
            ("connect", "⌁  Connect"),
            ("personal", "◫  Personal Twin"),
            ("complications", "⚕  PCOD Healing & Complications"),
            ("notes", "✎  Notes"),
        ]:
            b = QPushButton(text)
            b.setObjectName("nav")
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, k=key: self._go(k))
            self.nav[key] = b
            sl.addWidget(b)

        sl.addStretch()

        mode_box = QFrame()
        mode_box.setObjectName("hero")
        mv = QVBoxLayout(mode_box)
        mv.setContentsMargins(10, 10, 10, 10)
        e = QLabel("SESSION")
        e.setObjectName("eyebrow")
        mv.addWidget(e)
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
        b = QLabel("ENDO-TWIN")
        b.setStyleSheet("color:#ffffff;font-size:16px;font-weight:900;")
        tl.addWidget(b)
        s = QLabel("Understand your physiological patterns over time")
        s.setStyleSheet("color:#dce4fb;font-size:10px;font-weight:650;")
        tl.addWidget(s)
        tl.addStretch()
        self.mode_badge = status_badge("●  Demo data • synthetic", "info")
        self.quality_badge = status_badge("●  Data quality: —", "neutral")
        tl.addWidget(self.quality_badge)
        tl.addSpacing(6)
        tl.addWidget(self.mode_badge)
        rv.addWidget(top)

        self.stack = QStackedWidget()
        self.pages = {
            "home": self._overview(),
            "health": self._health(),
            "measure": self._measurements(),
            "timeline": self._timeline(),
            "reports": self._reports(),
            "connect": self._connect(),
            "personal": self._personal_twin(),
            "complications": self._complications(),
            "notes": self._notes(),
        }
        order = ["home", "health", "measure", "timeline", "reports", "connect", "personal", "complications", "notes"]
        for key in order:
            self.stack.addWidget(self.pages[key])
        rv.addWidget(self.stack, 1)
        foot = QLabel(f"{DISCLAIMER}  •  Patient-scoped  •  Local-first  •  Startup mode is fixed for this run")
        foot.setObjectName("muted")
        foot.setContentsMargins(15, 4, 15, 7)
        rv.addWidget(foot)
        shell.addWidget(right, 0, 1)
        self._go("home")

    def _go(self, key):
        order = ["home", "health", "measure", "timeline", "reports", "connect", "personal", "complications", "notes"]
        self.stack.setCurrentIndex(order.index(key))
        for k, b in self.nav.items():
            b.setChecked(k == key)

    def _refresh_header(self):
        alias = str(self.profile.get("alias") or self.participant_id)
        if self.mode.mode == "demo":
            self.side_mode.setText(f"PATIENT • {alias}")
            self.side_state.setText(f"Synthetic showcase stream • {self.participant_id}")
            self.mode_badge.setText("●  Demo data • synthetic")
        else:
            self.side_mode.setText(f"PATIENT • {alias}")
            self.side_state.setText(f"{self.participant_id} • {self.mode.port or self.mode.host}")
            self.mode_badge.setText("●  Live sensor")

    def _current_values(self):
        if self.mode.mode == "demo":
            return {
                "hr": self.case.hr,
                "hrv": self.case.hrv,
                "temp": self.case.temp,
                "activity": self.case.activity,
                "quality": self.case.quality,
                "sleep": self.case.sleep,
            }
        row = self.latest_row or {}
        return {
            "hr": row.get("hr_bpm"),
            "hrv": row.get("rmssd_ms"),
            "temp": row.get("skin_temp_c") if row.get("skin_temp_c") is not None else row.get("room_temp_c"),
            "activity": row.get("activity_level"),
            "quality": row.get("signal_quality"),
            "sleep": None,
        }

    def _fmt(self, v, suffix="", digits=1):
        if v is None:
            return "—"
        try:
            return f"{float(v):.{digits}f}{suffix}"
        except Exception:
            return str(v)

    def _metric(self, title, value, unit, detail, values, provenance):
        panel = QFrame()
        panel.setObjectName("card")
        v = QVBoxLayout(panel)
        head = QHBoxLayout()
        a = QLabel(title)
        a.setStyleSheet("font-weight:850;color:#dce2ed;font-size:12px;")
        head.addWidget(a)
        head.addStretch()
        head.addWidget(QLabel(unit))
        v.addLayout(head)
        val = QLabel(value)
        val.setObjectName("metricValue")
        v.addWidget(val)
        d = QLabel(detail)
        d.setObjectName("muted")
        d.setWordWrap(True)
        v.addWidget(d)
        chart = Sparkline(title, unit)
        chart.setMinimumHeight(100)
        if values:
            chart.set_values(values)
        v.addWidget(chart)
        v.addWidget(status_badge(provenance, "measured" if provenance=="MEASURED" else "derived"))
        self.metric_labels[title] = val
        self.charts[title] = chart
        return panel

    def _overview(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.setContentsMargins(24, 16, 20, 14)
        o.setSpacing(11)

        title = QLabel("Your hormonal health overview")
        title.setObjectName("title")
        o.addWidget(title)
        sub = QLabel(
            "A patient-first view of live measurements, personal baseline, longitudinal change and research context."
        )
        sub.setObjectName("muted")
        o.addWidget(sub)

        banner = QFrame()
        banner.setObjectName("patientHeader")
        bh = QHBoxLayout(banner)
        p_name = self.profile.get("patient_name") or self.profile.get("alias") or self.participant_id
        who = QLabel(str(p_name))
        who.setStyleSheet("font-size:18px;font-weight:900;")
        bh.addWidget(who)
        bh.addWidget(status_badge("PCOD: YES" if self.profile.get("has_pcod") is True else "PCOD: NO" if self.profile.get("has_pcod") is False else "PCOD: UNKNOWN", "info"))
        bh.addStretch()
        bh.addWidget(status_badge("DEMO_DATA" if self.mode.mode=="demo" else "MEASURED", "demo" if self.mode.mode=="demo" else "measured"))
        bh.addWidget(status_badge("Local-first", "neutral"))
        o.addWidget(banner)

        vals = self._current_values()
        baseline = baseline_summary(self.participant_id)
        kpi_defs = [
            ("Heart Rate", self._fmt(vals["hr"], " bpm", 0), "Processed pulse signal", "measured"),
            ("HRV (RMSSD)", self._fmt(vals["hrv"], " ms", 0), "Beat-to-beat feature", "derived"),
            ("Temperature", self._fmt(vals["temp"], " °C", 1), "Temperature channel", "measured"),
            ("GSR / Stress", self._fmt((self.latest_row or {}).get("gsr_tonic"), " rel.", 2), "EDA context", "measured"),
            ("Activity", self._fmt(vals["activity"], " %", 0), "IMU-derived activity", "derived"),
            ("Baseline", "READY" if baseline["available"] else "BUILDING", "Person-specific reference", "info"),
        ]
        kpis = QGridLayout()
        kpis.setSpacing(9)
        for i, (name, value, detail, kind) in enumerate(kpi_defs):
            kpis.addWidget(card(name, value, detail), 0, i)
        o.addLayout(kpis)

        main = QGridLayout()
        main.setSpacing(11)

        live = QFrame()
        live.setObjectName("card")
        lv = QVBoxLayout(live)
        lv.addWidget(section_header("Live Sensor Data", "Heart rate • HRV • temperature • GSR • activity"))
        for title_, val, unit, attr in [
            ("Heart rate", vals["hr"], "bpm", "hr_bpm"),
            ("HRV / RMSSD", vals["hrv"], "ms", "rmssd_ms"),
            ("Activity", vals["activity"], "%", "activity_level"),
        ]:
            row = QHBoxLayout()
            row.addWidget(QLabel(title_))
            row.addStretch()
            row.addWidget(QLabel(self._fmt(val, f" {unit}", 1)))
            lv.addLayout(row)
            chart = Sparkline(title_, unit)
            chart.setMinimumHeight(82)
            if attr in self.charts:
                chart.set_values(list(self.charts[title_].values))
            lv.addWidget(chart)
        main.addWidget(live, 0, 0, 2, 2)

        insights = QFrame()
        insights.setObjectName("card")
        iv = QVBoxLayout(insights)
        iv.addWidget(section_header("Personal Twin Insights", "Existing baseline + longitudinal context"))
        iv.addWidget(card("Learning samples", f"{self.personal_model.snapshot()['samples']:,}", "Quality-gated observations"))
        iv.addWidget(card("Baseline confidence", f"{baseline['confidence']:.2f}" if baseline["available"] else "—", "Stored person-specific baseline"))
        iv.addWidget(card("PCOD status", "Reported" if self.profile.get("has_pcod") is True else "Not reported" if self.profile.get("has_pcod") is False else "Unknown", "Set in Self-Learning Model"))
        btn = QPushButton("Open PCOD Healing & Complications")
        btn.setObjectName("primary")
        btn.clicked.connect(lambda: self._go("complications"))
        iv.addWidget(btn)
        main.addWidget(insights, 0, 2)
        o.addLayout(main, 1)

        quick = QFrame()
        quick.setObjectName("card")
        qv = QVBoxLayout(quick)
        qv.addWidget(section_header("Quick Actions", "Common patient workflows"))
        grid = QGridLayout()
        for i, (text, key) in enumerate([
            ("Log Symptoms", "notes"),
            ("Connect Wearable", "connect"),
            ("Personal Twin", "personal"),
            ("PCOD Healing", "complications"),
            ("View Reports", "reports"),
            ("Measurements", "measure"),
        ]):
            b = QPushButton(text)
            b.setObjectName("primary" if key in {"connect","personal"} else "secondary")
            b.clicked.connect(lambda _=False, k=key: self._go(k))
            grid.addWidget(b, i//3, i%3)
        qv.addLayout(grid)
        o.addWidget(quick)
        return w

    def _visual_series(self, key):
        if not key:
            return []
        values = []
        for row in self.feature_history:
            if isinstance(row, dict):
                value = row.get(key)
                if value is None and key == "skin_temp_c":
                    value = row.get("room_temp_c")
            else:
                value = getattr(row, key, None)
                if value is None and key == "skin_temp_c":
                    value = getattr(row, "room_temp_c", None)
            try:
                if value is not None:
                    values.append(float(value))
            except (TypeError, ValueError):
                pass
        if values:
            return values[-120:]
        if self.mode.mode == "demo":
            vals=self._current_values()
            base={"hr_bpm":vals["hr"],"rmssd_ms":vals["hrv"],"skin_temp_c":vals["temp"],"gsr_tonic":0.28,"activity_level":vals["activity"]}.get(key)
            if base is not None:
                scale=0.05 if key=="skin_temp_c" else max(abs(float(base))*0.05,0.5)
                return [float(base)+scale*x for x in [0,2,-1,3,1,-2,2,0,-1,2,1,-1,3,0]]
        return []

    def _health(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.setContentsMargins(24, 16, 20, 14)
        o.setSpacing(11)
        title = QLabel("My Health")
        title.setObjectName("title")
        o.addWidget(title)

        vals = self._current_values()
        snap = self.personal_model.snapshot()
        baseline = baseline_summary(self.participant_id)
        top = QGridLayout()
        for i, (name, value, detail, accent) in enumerate([
            ("Personal baseline", "READY" if baseline["available"] else "BUILDING", "Patient-specific reference", "#36d9b6"),
            ("Learning samples", f"{snap['samples']:,}", "Quality-gated observations", "#5d8dff"),
            ("Data quality", self._fmt((vals["quality"] or 0)*100, " %", 0), "Latest signal quality", "#ff4fa3"),
            ("PCOD status", "YES" if self.profile.get("has_pcod") is True else "NO" if self.profile.get("has_pcod") is False else "UNKNOWN", "Patient-reported", "#a86bff"),
        ]):
            top.addWidget(metric_card(name, value, detail, accent=accent), 0, i)
        o.addLayout(top)

        graphs = QGridLayout()
        series = [
            ("Heart rate", "bpm", "hr_bpm", "#ff4fa3"),
            ("HRV / RMSSD", "ms", "rmssd_ms", "#38bdf8"),
            ("Skin temperature", "°C", "skin_temp_c", "#ff9f43"),
            ("Activity", "%", "activity_level", "#31d7a1"),
        ]
        for i, (name, unit, key, accent) in enumerate(series):
            values = self._visual_series(key)
            panel = trend_panel(name, values, unit, accent, 165)
            graphs.addWidget(panel, i//2, i%2)
            self.visual_graphs[key] = panel.graph
        o.addLayout(graphs)

        bottom = QHBoxLayout()
        g = RingGauge("Baseline confidence", baseline["confidence"]*100 if baseline["available"] else None, "%", "#39c9ff")
        bottom.addWidget(g)
        g2 = RingGauge("Learning coverage", min(100.0, snap["samples"]/100.0*100.0), "%", "#7f62ff")
        bottom.addWidget(g2)
        note = QFrame()
        note.setObjectName("card")
        nv = QVBoxLayout(note)
        nv.addWidget(section_header("Today", "Visual summary"))
        nv.addWidget(QLabel("Green = measured/derived data • purple = Personal Twin • pink/orange = health signal"))
        nv.addWidget(status_badge("LOCAL • PATIENT-SCOPED", "info"))
        bottom.addWidget(note, 1)
        o.addLayout(bottom)
        return w

    def _measurements(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.setContentsMargins(24, 16, 20, 14)
        o.setSpacing(10)
        o.addWidget(section_header("Live Measurements", "Large visuals first; provenance remains visible on every metric."))

        vals = self._current_values()
        specs = [
            ("Heart rate", "hr", "bpm", "MEASURED", "#ff4fa3"),
            ("HRV / RMSSD", "hrv", "ms", "DERIVED", "#33a8ff"),
            ("Skin temperature", "temp", "°C", "MEASURED", "#ff9f43"),
            ("GSR / EDA", "gsr", "rel.", "MEASURED", "#a86bff"),
            ("Activity", "activity", "%", "DERIVED", "#31d7a1"),
            ("SpO₂", None, "%", "NOT AVAILABLE — analog PPG", "#44d9ff"),
        ]
        grid = QGridLayout()
        for i,(name,key,unit,prov,accent) in enumerate(specs):
            value = "—" if key is None else self._fmt(vals.get(key), f" {unit}", 1)
            card_widget = metric_card(name, value, prov, self._visual_series({"hr":"hr_bpm","hrv":"rmssd_ms","temp":"skin_temp_c","gsr":"gsr_tonic","activity":"activity"}.get(key),), accent, unit)
            grid.addWidget(card_widget, i//3, i%3)
        o.addLayout(grid)

        graphrow = QGridLayout()
        for i,(name,unit,key,accent) in enumerate([
            ("Cardiovascular", "", "hr_bpm", "#ff4fa3"),
            ("Autonomic", "", "rmssd_ms", "#39c9ff"),
            ("Stress / EDA", "", "gsr_tonic", "#a86bff"),
            ("Movement", "", "activity_level", "#31d7a1"),
        ]):
            p = trend_panel(name, self._visual_series(key), unit, accent, 190)
            graphrow.addWidget(p, i//2, i%2)
            self.visual_graphs[key] = p.graph
        o.addLayout(graphrow, 1)
        self.measure_status = QLabel("Waiting for stream…")
        self.measure_status.setObjectName("muted")
        o.addWidget(self.measure_status)
        return w

    def _timeline(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.setContentsMargins(24, 16, 20, 14)
        o.setSpacing(10)
        o.addWidget(section_header("Today’s Timeline", "Events and physiological movement, visualized together."))
        split = QGridLayout()

        box = QFrame()
        box.setObjectName("card")
        v = QVBoxLayout(box)
        v.addWidget(QLabel("RECENT EVENTS"))
        for idx, (date, head, detail) in enumerate([
            ("NOW", "Wearable stream", "Live observations linked to this patient"),
            ("TODAY", "Personal Twin", "Quality-gated learning updates"),
            ("TODAY", "Baseline", "Person-specific baseline stored locally" if baseline_summary(self.participant_id)["available"] else "Baseline is still being built"),
            ("EARLIER", "Report", "Local report workflow available"),
        ]):
            row = QHBoxLayout()
            badge = QLabel(f"{idx+1:02d}")
            badge.setStyleSheet("background:#5b3cff;color:white;border-radius:10px;padding:5px;font-weight:900;")
            row.addWidget(badge)
            txt = QVBoxLayout()
            txt.addWidget(QLabel(date))
            txt.addWidget(QLabel(f"<b>{head}</b>"))
            d = QLabel(detail); d.setObjectName("muted"); d.setWordWrap(True); txt.addWidget(d)
            row.addLayout(txt,1); v.addLayout(row)
        split.addWidget(box,0,0)

        gcol = QVBoxLayout()
        gcol.addWidget(trend_panel("Heart rate", self._visual_series("hr_bpm"), "bpm", "#ff4fa3", 145))
        gcol.addWidget(trend_panel("HRV", self._visual_series("rmssd_ms"), "ms", "#38bdf8", 145))
        split.addLayout(gcol,0,1)
        o.addLayout(split,1)
        return w

    def _personal_twin(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.setContentsMargins(24, 16, 20, 14)
        o.addWidget(section_header("Personal Adaptive Twin", "Your local patient-specific baseline and learning state."))

        snap = self.personal_model.snapshot()
        baseline = baseline_summary(self.participant_id)
        kpi = QGridLayout()
        kpi.addWidget(metric_card("Learning samples", f"{snap['samples']:,}", "Quality-gated", accent="#5b7cff"),0,0)
        kpi.addWidget(metric_card("Baseline", "READY" if baseline["available"] else "BUILDING", "Stored locally", accent="#32d6a0"),0,1)
        kpi.addWidget(metric_card("PCOD status", "YES" if self.profile.get("has_pcod") is True else "NO" if self.profile.get("has_pcod") is False else "UNKNOWN", "Set in patient profile", accent="#a86bff"),0,2)
        q = baseline["quality"]*100 if baseline["available"] else 0
        kpi.addWidget(metric_card("Baseline quality", f"{q:.0f}%", "Capture quality", accent="#ff9f43"),0,3)
        o.addLayout(kpi)

        capture = QFrame()
        capture.setObjectName("card")
        cv = QVBoxLayout(capture)
        cv.addWidget(section_header("Personal Baseline Capture", "60 seconds of real, quality-gated live windows. Demo/synthetic data is excluded."))
        self.baseline_capture_status = QLabel("Ready. Connect the wearable and start a baseline capture.")
        self.baseline_capture_status.setObjectName("muted")
        self.baseline_capture_status.setWordWrap(True)
        cv.addWidget(self.baseline_capture_status)
        self.baseline_progress = QProgressBar()
        self.baseline_progress.setRange(0, 100)
        self.baseline_progress.setValue(0)
        cv.addWidget(self.baseline_progress)
        br = QHBoxLayout()
        self.ppg_calibrate_btn = QPushButton("Calibrate PPG for Patient (5 s)")
        self.ppg_calibrate_btn.setObjectName("secondary")
        self.ppg_calibrate_btn.clicked.connect(self._calibrate_patient_ppg)
        br.addWidget(self.ppg_calibrate_btn)
        start_btn = QPushButton("Start / Restart 60 s Baseline")
        start_btn.setObjectName("primary")
        start_btn.clicked.connect(self._start_baseline_capture)
        br.addWidget(start_btn)
        stop_btn = QPushButton("Stop & Save")
        stop_btn.setObjectName("secondary")
        stop_btn.clicked.connect(self._stop_baseline_capture)
        br.addWidget(stop_btn)
        br.addStretch()
        cv.addLayout(br)
        o.addWidget(capture)

        graphs = QGridLayout()
        for i,(key,title,unit,accent) in enumerate([
            ("hr_bpm","Heart rate","bpm","#ff4fa3"),
            ("rmssd_ms","HRV","ms","#39c9ff"),
            ("skin_temp_c","Temperature","°C","#ff9f43"),
            ("gsr_tonic","GSR","","#a86bff"),
        ]):
            p = trend_panel(title,self._visual_series(key),unit,accent,175)
            graphs.addWidget(p,i//2,i%2); self.visual_graphs[key]=p.graph
        o.addLayout(graphs,1)

        row = QHBoxLayout()
        refresh = QPushButton("Refresh"); refresh.setObjectName("secondary"); refresh.clicked.connect(self._refresh_personal); row.addWidget(refresh)
        switch = QPushButton("Switch Patient"); switch.setObjectName("primary"); switch.clicked.connect(self._switch_patient); row.addWidget(switch)
        row.addStretch(); o.addLayout(row)
        return w

    def _calibrate_patient_ppg(self):
        if self.mode.mode == "demo" or self.session is None:
            self.baseline_capture_status.setText("Connect the wearable in LIVE mode before starting PPG calibration.")
            return
        self.session.write_command(f"PPG_PERSON={self.participant_id}")
        self.session.write_command("PPG_NEW_PERSON")
        self.baseline_capture_status.setText(
            f"PPG calibration started for {self.participant_id} • keep finger still for 5 s."
        )

    def _start_baseline_capture(self):
        if self.mode.mode == "demo":
            self.baseline_capture_status.setText("Live sensor mode is required for a real personal baseline. Demo data is never used.")
            return
        self.baseline_capture = BaselineCapture(self.participant_id, duration_s=60.0, min_samples=60, min_quality=0.45)
        self.baseline_capture.start()
        self.baseline_progress.setValue(0)
        self.baseline_capture_status.setText("Capturing… sit still, keep the pulse sensor positioned consistently, and avoid unnecessary movement.")

    def _stop_baseline_capture(self):
        result = self.baseline_capture.stop()
        self._show_baseline_result(result)

    def _update_baseline_capture_ui(self):
        if not hasattr(self, "baseline_capture_status"):
            return
        if self.baseline_capture.active:
            self.baseline_progress.setValue(int(self.baseline_capture.progress * 100))
            self.baseline_capture_status.setText(
                f"Capturing… {self.baseline_capture.accepted} quality-gated windows • "
                f"{self.baseline_capture.progress*100:.0f}% complete"
            )

    def _show_baseline_result(self, result):
        if result.get("ready"):
            self.baseline_progress.setValue(100)
            self.baseline_capture_status.setText(
                f"Baseline saved for {self.participant_id} • {result['samples']} windows • "
                f"quality {result['quality']*100:.0f}% • confidence {result['confidence']:.2f} • local storage"
            )
            self._refresh_personal()
        else:
            self.baseline_capture_status.setText(
                "Baseline not saved • " + str(result.get("error", "Need more valid live windows."))
            )

    def _auto_sync_baseline(self):
        if self.mode.mode == "demo" or len(self.feature_history) < 60:
            return
        try:
            rows = [
                r for r in self.feature_history[-160:]
                if str(r.get("gating", "")) == "USABLE"
                and not str(r.get("source", "")).lower().startswith("demo")
            ]
            if len(rows) >= 60:
                cap = BaselineCapture(self.participant_id, duration_s=0, min_samples=60, min_quality=0.45)
                cap.accepted_rows = rows[-120:]
                cap.started_at = time.time() - 60.0
                cap.active = True
                cap.finalize(force=True)
        except Exception:
            pass

    def _on_ppg_calibration(self, event):
        self.side_state.setText(
            f"PPG calibration saved • profile {event.profile_id} • quality {event.quality:.0f}%"
        )

    def _refresh_personal(self):
        self.personal_model.sync_from_disk()
        self.profile = get_profile(self.participant_id)
        snap = self.personal_model.snapshot()
        patient_name = self.profile.get("patient_name") or self.profile.get("alias") or self.participant_id
        stored_baseline = "YES" if baseline_summary(self.participant_id)["available"] else "NO"
        lines = [
            f"Participant: {self.participant_id}",
            f"Patient: {patient_name}",
            f"Profile: {profile_summary(self.profile)}",
            f"Learning samples: {snap['samples']:,}",
            f"Quality-weighted samples: {snap['quality_weighted_samples']:.2f}",
            "",
            f"Stored baseline: {stored_baseline}",
            "Learned reference ranges:",
        ]
        for name, item in snap.get("metrics", {}).items():
            lines.append(f"{name}: mean={item['mean']:.3f} • std={item['std']:.3f} • samples={item['samples']:.1f} • latest={item['last']}")
        self.personal_text.setText("\n".join(lines))

    def _switch_patient(self):
        pid = choose_participant("ENDO-TWIN • Patient Workstation — Select Patient")
        if not pid or pid == self.participant_id:
            return
        self.session.stop()
        select_participant(pid)
        self.participant_id = pid
        self.profile = get_profile(pid)
        self.feature_history = []
        self.visual_graphs.clear()
        self.personal_model.set_participant(pid)
        self.baseline_capture = BaselineCapture(pid, duration_s=60.0, min_samples=60, min_quality=0.45)
        self.latest_row = None
        self._refresh_header()
        self._refresh_personal()
        self.session = LiveSession(self.mode, self)
        self.session.features_updated.connect(self._on_features)
        self.session.state_changed.connect(self._on_state)
        self.session.error_received.connect(self._on_error)
        self.session.start()

    def _reports(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.setContentsMargins(24, 16, 20, 14)
        o.addWidget(section_header("Reports & Export", "Visual summary first, traceable local report second."))
        vals = self._current_values()
        grid = QGridLayout()
        for i,(title,value,detail,accent) in enumerate([
            ("Heart rate",self._fmt(vals["hr"]," bpm",0),"Latest observation","#ff4fa3"),
            ("HRV",self._fmt(vals["hrv"]," ms",0),"Derived from PPG","#39c9ff"),
            ("Temperature",self._fmt(vals["temp"]," °C",1),"Sensor channel","#ff9f43"),
            ("Activity",self._fmt(vals["activity"]," %",0),"IMU context","#31d7a1"),
        ]):
            grid.addWidget(metric_card(title,value,detail,self._visual_series({"Heart rate":"hr_bpm","HRV":"rmssd_ms","Temperature":"skin_temp_c","Activity":"activity_level"}[title]),accent),0,i)
        o.addLayout(grid)
        graph = trend_panel("30-window visual summary", self._visual_series("hr_bpm"), "bpm", "#5b7cff", 220)
        self.visual_graphs["report_hr"] = graph.graph
        o.addWidget(graph,1)
        actions=QHBoxLayout()
        b=QPushButton("Generate local report"); b.setObjectName("primary"); b.clicked.connect(self._generate_report); actions.addWidget(b)
        b2=QPushButton("Personal Twin"); b2.setObjectName("secondary"); b2.clicked.connect(lambda:self._go("personal")); actions.addWidget(b2)
        actions.addStretch(); o.addLayout(actions)
        return w

    def _generate_report(self):
        p = self.case
        reports = ROOT / "data" / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        path = reports / f"patient_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        vals = self._current_values()
        path.write_text(
            "\n".join([
                "ENDO-TWIN NEXUS — PATIENT WORKSPACE SUMMARY",
                f"Generated: {datetime.now().isoformat(timespec='seconds')}",
                DISCLAIMER,
                "",
                f"Heart rate: {self._fmt(vals['hr'], ' bpm', 1)}",
                f"HRV RMSSD: {self._fmt(vals['hrv'], ' ms', 1)}",
                f"Skin temperature: {self._fmt(vals['temp'], ' °C', 1)}",
                f"Activity: {self._fmt(vals['activity'], ' %', 1)}",
                "Disease-model output: NOT RUN on patient screen",
                "Ultrasound: UNKNOWN unless a validated pipeline provides an output",
            ]),
            encoding="utf-8",
        )
        QMessageBox.information(self, "Report", f"Saved locally:\n{path}")

    def _connect(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.setContentsMargins(24, 16, 20, 14)
        o.addWidget(section_header("Wearable & Workstation Connection", "Visual connection status for this patient session."))
        grid = QGridLayout()
        state = "CONNECTED" if self.latest_row else "WAITING"
        grid.addWidget(RingGauge("Wearable", 100 if self.latest_row else 0, "%", "#31d7a1"),0,0)
        grid.addWidget(metric_card("Patient bridge", self.bridge.endpoint, "Local bridge • patient-scoped", accent="#39c9ff"),0,1)
        grid.addWidget(metric_card("Doctor bridge", "7777", "Local workstation endpoint", accent="#a86bff"),0,2)
        grid.addWidget(metric_card("Packets", str(self.bridge.received_count), "Packages received", accent="#ff9f43"),0,3)
        o.addLayout(grid)
        if state == "CONNECTED":
            q = QLabel("●  Wearable connected • live patient stream")
            q.setStyleSheet("color:#31d7a1;font-weight:900;font-size:15px;")
        else:
            q = QLabel("○  Waiting for wearable data")
            q.setStyleSheet("color:#ffb14a;font-weight:850;font-size:15px;")
        o.addWidget(q)
        actions=QHBoxLayout()
        c=QPushButton("Copy patient endpoint"); c.setObjectName("primary"); c.clicked.connect(lambda:(QApplication.clipboard().setText(self.bridge.endpoint),QMessageBox.information(self,"Connect","Endpoint copied."))); actions.addWidget(c)
        c2=QPushButton("Personal Twin"); c2.setObjectName("secondary"); c2.clicked.connect(lambda:self._go("personal")); actions.addWidget(c2)
        actions.addStretch(); o.addLayout(actions)
        return w

    def _complications(self):
        panel = PCODProgressPanel("PCOD Healing & Complications")
        panel.pcod_status_changed.connect(self._save_pcod_status)
        panel.set_context(self.profile, self.feature_history, self.latest_row)
        self.pcod_progress_panel = panel
        return panel

    def _save_pcod_status(self, value):
        self.profile["has_pcod"] = value
        self.profile["updated_at"] = datetime.now().timestamp()
        try:
            save_profile(self.profile, set_active=True)
        except Exception as exc:
            self.side_state.setText(f"Profile save warning • {exc}")
        if hasattr(self, "pages") and "home" in self.pages:
            # Rebuild only the patient-facing status page on next navigation.
            pass

    def _notes(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.setContentsMargins(24, 16, 20, 14)
        o.addWidget(section_header("Symptoms & Notes", "Quick capture on the left, detailed note on the right."))
        body=QGridLayout()
        quick=QFrame(); quick.setObjectName("card"); qv=QVBoxLayout(quick)
        qv.addWidget(QLabel("QUICK SYMPTOMS"))
        for label in ["Cycle change","Pelvic discomfort","Acne / skin","Mood change","Sleep change","Fatigue"]:
            b=QPushButton(label); b.setObjectName("secondary"); qv.addWidget(b)
        body.addWidget(quick,0,0)
        note=QFrame(); note.setObjectName("card"); nv=QVBoxLayout(note)
        nv.addWidget(QLabel("PATIENT NOTE"))
        self.note_editor=QTextEdit(); self.note_editor.setPlaceholderText("Write something you want to remember…"); nv.addWidget(self.note_editor,1)
        save=QPushButton("Save local note"); save.setObjectName("primary"); save.clicked.connect(self._save_note); nv.addWidget(save,0,Qt.AlignmentFlag.AlignLeft)
        body.addWidget(note,0,1); o.addLayout(body,1)
        o.addWidget(status_badge("LOCAL • PATIENT-SCOPED", "info"))
        return w

    def _save_note(self):
        self.note_text = self.note_editor.toPlainText()
        notes = ROOT / "data" / "notes"
        notes.mkdir(parents=True, exist_ok=True)
        (notes / "patient-workspace-note.txt").write_text(self.note_text, encoding="utf-8")
        QMessageBox.information(self, "Notes", "Saved locally.")

    def _on_state(self, state):
        self.side_state.setText(state.upper().replace("_", " "))

    def _on_error(self, msg):
        self.side_state.setText("ERROR • " + msg)

    def _on_features(self, row):
        self.latest_row = row
        source = str(row.get("source", "")).lower()
        if source not in {"demo", "synthetic"} and not source.startswith("demo"):
            self.feature_history.append(dict(row))
            self.feature_history = self.feature_history[-1000:]
            result = self.baseline_capture.add_row(row)
            if result is not None:
                self._show_baseline_result(result)
        try:
            source = str(row.get("source", "")).lower()
            if source not in {"demo", "synthetic"} and not source.startswith("demo"):
                self.personal_model.observe(SimpleNamespace(**row), quality=row.get("signal_quality"))
                snap = self.personal_model.snapshot()
                if snap["samples"] >= 60 and snap["samples"] % 20 == 0:
                    self._auto_sync_baseline()
            self.personal_model.sync_from_disk()
            self.profile = get_profile(self.participant_id)
            if hasattr(self, "personal_text"):
                self._refresh_personal()
        except Exception as exc:
            self.side_state.setText(f"Learning warning • {exc}")
        if hasattr(self, "pcod_progress_panel"):
            self.pcod_progress_panel.set_context(self.profile, self.feature_history, row)
        for key in ("hr_bpm","rmssd_ms","skin_temp_c","gsr_tonic","activity_level"):
            graph=self.visual_graphs.get(key)
            if graph is not None:
                value=row.get(key)
                if value is None and key=="skin_temp_c":
                    value=row.get("room_temp_c")
                graph.set_value(value)
        q = row.get("signal_quality")
        if q is not None:
            self.quality_badge.setText(f"●  Data quality: {float(q)*100:.0f}%")
        vals = {
            "Heart rate": (row.get("hr_bpm"), " bpm"),
            "HRV (RMSSD)": (row.get("rmssd_ms"), " ms"),
            "Skin temperature": (row.get("skin_temp_c"), " °C"),
        }
        for title, (value, suffix) in vals.items():
            if title in self.metric_labels:
                self.metric_labels[title].setText(self._fmt(value, suffix, 1))
                if value is not None:
                    self.charts[title].set_value(value)
        if hasattr(self, "measure_chart") and row.get("activity_level") is not None:
            self.measure_chart.set_value(row["activity_level"])
            self.measure_status.setText(f"{row.get('gating','QUALITY_GATE')} • {row.get('provenance','UNKNOWN')} • {len(row.get('status_flags', []))} status flag(s)")


def run():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    participant_id = choose_participant("ENDO-TWIN • Patient Workstation — Select Patient")
    if not participant_id:
        return 0
    mode = choose_mode("ENDO-TWIN • Patient Workstation")
    if mode is None:
        return 0
    select_participant(participant_id)
    w = PatientWindow(mode, participant_id)
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
