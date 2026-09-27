#!/usr/bin/env python3
"""ENDO-TWIN V8.6 Patient Workstation — calm patient-facing research UI."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QStackedWidget, QTextEdit, QVBoxLayout, QWidget
)

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from desktop.demo_data import DEMO_CASES
from desktop.workstation_runtime import LiveSession, ModeConfig, Sparkline, choose_mode
from desktop.workstation_theme import APP_QSS, card, section_header, status_badge
from src.personal_twin.profile_store import load_state, profile_summary, get_profile, select_participant
from src.personal_twin.adaptive_model import PersonalAdaptiveModel
from src.personal_twin.participant_selector import choose_participant
from src.ui.pcos_complication_panel import PCOSComplicationPanel
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
        self.note_text = ""
        self.metric_labels = {}
        self.charts = {}
        self.personal_model = PersonalAdaptiveModel(self.participant_id)

        self.bridge = EndoTwinBridgeServer(ROOT, 7778)
        self.bridge.start()

        self.session = LiveSession(mode, self)
        self.session.features_updated.connect(self._on_features)
        self.session.state_changed.connect(self._on_state)
        self.session.error_received.connect(self._on_error)
        self.session.start()

        self.setWindowTitle("Endo-Twin Nexus — Patient Desktop • V8.6")
        self.resize(1480, 920)
        self.setMinimumSize(1120, 740)
        self.setStyleSheet(APP_QSS)
        self._build()
        self._refresh_header()

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
            ("complications", "⚕  Complications"),
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
        order = ["home", "health", "measure", "timeline", "reports", "connect", "notes"]
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
            "temp": row.get("skin_temp_c"),
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

        title = QLabel("How am I doing?")
        title.setObjectName("title")
        o.addWidget(title)
        sub = QLabel("Longitudinal overview — your latest observations, baseline progress and changes worth discussing.")
        sub.setObjectName("muted")
        o.addWidget(sub)

        banner = QFrame()
        banner.setObjectName("patientHeader")
        bh = QHBoxLayout(banner)
        p = QLabel("Demo Patient 021" if self.mode.mode == "demo" else "Your local record")
        p.setStyleSheet("font-size:16px;font-weight:900;")
        bh.addWidget(p)
        bh.addStretch()
        bh.addWidget(status_badge("DEMO_DATA" if self.mode.mode=="demo" else "LOCAL RECORD", "info"))
        bh.addWidget(status_badge("Research prototype", "neutral"))
        o.addWidget(banner)

        vals = self._current_values()
        charts = QGridLayout()
        charts.setSpacing(12)
        series = {
            "Heart rate": [vals["hr"] + x for x in (-4,-1,3,1,-2,2,0,4,-3,1,2)] if vals["hr"] is not None else [],
            "HRV (RMSSD)": [vals["hrv"] + x for x in (3,-2,4,-1,2,0,-3,5)] if vals["hrv"] is not None else [],
            "Skin temperature": [vals["temp"] + x*0.06 for x in (-3,1,4,0,-1,2,-2,3)] if vals["temp"] is not None else [],
        }
        cards = [
            ("Heart rate", self._fmt(vals["hr"], " bpm", 0), "Latest processed pulse signal", "MEASURED"),
            ("HRV (RMSSD)", self._fmt(vals["hrv"], " ms", 0), "Beat-to-beat derived feature", "DERIVED"),
            ("Skin temperature", self._fmt(vals["temp"], " °C", 1), "Validity-gated temperature", "MEASURED"),
        ]
        for i, (name, value, detail, prov) in enumerate(cards):
            charts.addWidget(self._metric(name, value, "", detail, series[name], prov), 0, i)
        o.addLayout(charts)

        lower = QGridLayout()
        left = QFrame()
        left.setObjectName("card")
        lv = QVBoxLayout(left)
        lv.addWidget(section_header("Today's snapshot", "Simple context, not a diagnosis."))
        for a, b in [
            ("Activity", self._fmt(vals["activity"], " %", 0)),
            ("Sleep duration", self._fmt(vals["sleep"], " h", 1)),
            ("Signal quality", self._fmt(vals["quality"]*100 if vals["quality"] is not None else None, " %", 0)),
        ]:
            row = QHBoxLayout()
            row.addWidget(QLabel(a))
            row.addStretch()
            row.addWidget(QLabel(b))
            lv.addLayout(row)
        lower.addWidget(left, 0, 0)

        right = QFrame()
        right.setObjectName("card")
        rv = QVBoxLayout(right)
        rv.addWidget(section_header("What changed?", "Compare repeated observations instead of a single value."))
        if self.mode.mode == "demo":
            rv.addWidget(QLabel("Your demo case is shown with synthetic values to demonstrate the timeline and reporting workflow."))
            rv.addWidget(QLabel("Discuss persistent changes, symptoms or concerns with a qualified clinician."))
        else:
            rv.addWidget(QLabel("Live measurements are visible here while the sensor stream is active."))
            rv.addWidget(QLabel("No disease-model inference is generated from this patient screen."))
        lower.addWidget(right, 0, 1)
        lower.setColumnStretch(0, 1)
        lower.setColumnStretch(1, 1)
        o.addLayout(lower)
        o.addStretch()
        return w

    def _health(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.setContentsMargins(24, 16, 20, 14)
        title = QLabel("My Health")
        title.setObjectName("title")
        o.addWidget(title)
        o.addWidget(QLabel("Build a personal baseline from repeated observations and patient-entered context."))
        grid = QGridLayout()
        vals = self._current_values()
        for i, (a, b, c) in enumerate([
            ("Personal baseline", "Building", "Requires repeated observations"),
            ("Activity", self._fmt(vals["activity"], " %", 0), "IMU-derived activity index"),
            ("Temperature", self._fmt(vals["temp"], " °C", 1), "Validity-gated sensor channel"),
            ("Sleep duration", self._fmt(vals["sleep"], " h", 1), "Patient-reported/demo context"),
        ]):
            grid.addWidget(card(a, b, c), 0, i)
        o.addLayout(grid)
        o.addWidget(section_header("Your data has provenance", "MEASURED • DERIVED • PATIENT-REPORTED • IMAGE-DERIVED • MODEL-INFERRED • DEMO_DATA • UNKNOWN"))
        o.addStretch()
        return w

    def _measurements(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.setContentsMargins(24, 16, 20, 14)
        title = QLabel("Measurements")
        title.setObjectName("title")
        o.addWidget(title)
        o.addWidget(QLabel("Live sensor processing and derived features, kept distinct from disease-model inference."))

        grid = QGridLayout()
        vals = self._current_values()
        specs = [
            ("Heart rate", self._fmt(vals["hr"], " bpm", 1), "Processed from PPG", "MEASURED"),
            ("HRV RMSSD", self._fmt(vals["hrv"], " ms", 1), "Cleaned beat-to-beat intervals", "DERIVED"),
            ("SpO₂", "—", "Quality-gated research estimate", "DERIVED"),
            ("Skin temperature", self._fmt(vals["temp"], " °C", 1), "Validity-gated", "MEASURED"),
            ("GSR / EDA", "—", "Conductance proxy", "MEASURED"),
            ("Activity", self._fmt(vals["activity"], " %", 1), "IMU-derived index", "DERIVED"),
        ]
        for i, (a, b, c, p) in enumerate(specs):
            panel = card(a, b, c)
            panel.layout().addWidget(status_badge(p, "measured" if p=="MEASURED" else "derived"))
            grid.addWidget(panel, i//3, i%3)
        o.addLayout(grid)
        self.measure_chart = Sparkline("Activity / motion", "%")
        self.measure_chart.setMinimumHeight(210)
        if vals["activity"] is not None:
            self.measure_chart.set_values([vals["activity"] + x for x in (-9,-4,2,6,-2,3,8,-5,0,4)])
        o.addWidget(self.measure_chart)
        self.measure_status = QLabel("Waiting for stream…")
        self.measure_status.setObjectName("muted")
        o.addWidget(self.measure_status)
        return w

    def _timeline(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.setContentsMargins(24, 16, 20, 14)
        title = QLabel("My timeline")
        title.setObjectName("title")
        o.addWidget(title)
        o.addWidget(QLabel("Chronological patient-scoped events and sessions."))
        box = QFrame()
        box.setObjectName("card")
        v = QVBoxLayout(box)
        events = [
            ("Today", "Current session", "Live measurements / demo stream"),
            ("Today", "Latest observations", "PPG, HRV, activity and temperature path"),
            ("Earlier", "Baseline building", "Repeated observations remain longitudinal context"),
            ("Earlier", "Report workflow", "Research report generated locally"),
        ]
        for date, head, detail in events:
            row = QHBoxLayout()
            dot = QLabel("◉")
            dot.setStyleSheet("color:#9aaeff;font-size:15px;")
            row.addWidget(dot)
            col = QVBoxLayout()
            d = QLabel(date)
            d.setObjectName("muted")
            col.addWidget(d)
            h = QLabel(head)
            h.setStyleSheet("font-weight:850;color:#e7ebf3;")
            col.addWidget(h)
            de = QLabel(detail)
            de.setObjectName("muted")
            de.setWordWrap(True)
            col.addWidget(de)
            row.addLayout(col, 1)
            v.addLayout(row)
        o.addWidget(box)
        o.addStretch()
        return w

    def _personal_twin(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.setContentsMargins(24, 16, 20, 14)
        o.addWidget(section_header("My Personal Adaptive Twin", "Patient-scoped learning shared with the Doctor and Unified Workstations."))
        self.personal_text = QTextEdit()
        self.personal_text.setReadOnly(True)
        o.addWidget(self.personal_text, 1)
        row = QHBoxLayout()
        refresh = QPushButton("Refresh learned data")
        refresh.clicked.connect(self._refresh_personal)
        row.addWidget(refresh)
        switch = QPushButton("Switch Patient")
        switch.clicked.connect(self._switch_patient)
        row.addWidget(switch)
        row.addStretch()
        o.addLayout(row)
        self._refresh_personal()
        return w

    def _refresh_personal(self):
        self.personal_model.sync_from_disk()
        self.profile = get_profile(self.participant_id)
        snap = self.personal_model.snapshot()
        lines = [
            f"Participant: {self.participant_id}",
            f"Profile: {profile_summary(self.profile)}",
            f"Learning samples: {snap['samples']:,}",
            f"Quality-weighted samples: {snap['quality_weighted_samples']:.2f}",
            "",
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
        self.personal_model.set_participant(pid)
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
        title = QLabel("Reports")
        title.setObjectName("title")
        o.addWidget(title)
        o.addWidget(QLabel("Review-ready summaries keep source, quality, uncertainty and limitations visible."))
        box = QFrame()
        box.setObjectName("card")
        v = QVBoxLayout(box)
        v.addWidget(QLabel("My monitoring summary"))
        v.addWidget(QLabel("Observation → quality → baseline → longitudinal context → model layer → limitations"))
        b = QPushButton("Generate local demo report")
        b.setObjectName("primary")
        b.clicked.connect(self._generate_report)
        v.addWidget(b, 0, Qt.AlignmentFlag.AlignLeft)
        o.addWidget(box)
        o.addWidget(card("Clinical validation", "NOT ESTABLISHED", "This prototype is not a medical device or diagnostic system."))
        o.addStretch()
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
        title = QLabel("Connect")
        title.setObjectName("title")
        o.addWidget(title)
        o.addWidget(QLabel("Pair your Patient Android app with the Doctor Workstation on a trusted local network."))
        grid = QGridLayout()
        grid.addWidget(card("Patient bridge", self.bridge.endpoint, "This workstation • port 7778"), 0, 0)
        grid.addWidget(card("Doctor bridge", "Port 7777", "Doctor workstation endpoint"), 0, 1)
        grid.addWidget(card("Packages received", str(self.bridge.received_count), "Local bridge inbox"), 0, 2)
        o.addLayout(grid)
        c = QPushButton("Copy patient endpoint")
        c.setObjectName("primary")
        c.clicked.connect(lambda: (QApplication.clipboard().setText(self.bridge.endpoint), QMessageBox.information(self, "Connect", "Endpoint copied.")))
        o.addWidget(c, 0, Qt.AlignmentFlag.AlignLeft)
        note = QLabel("Transport is research LAN infrastructure. Production health systems need encrypted transport, strong authentication, authorization and audit logging.")
        note.setObjectName("warning")
        note.setWordWrap(True)
        o.addWidget(note)
        o.addStretch()
        return w

    def _complications(self):
        panel = PCOSComplicationPanel("PCOS / Complication Context")
        p = load_state().get("profile", {})
        clinical = {
            "age_years": p.get("age_years"),
            "bmi": p.get("bmi"),
            "systolic_bp": p.get("systolic_bp"),
            "diastolic_bp": p.get("diastolic_bp"),
            "glucose_mg_dl": p.get("glucose_mg_dl"),
            "cycle_irregular": p.get("cycle_irregular"),
            "usual_cycle_length_days": p.get("usual_cycle_length_days"),
            "days_since_last_period": p.get("days_since_last_period"),
            "years_post_menarche": p.get("years_post_menarche"),
        }
        panel.set_context(clinical, self.latest_row)
        self.complication_panel = panel
        return panel

    def _notes(self):
        w = QWidget()
        o = QVBoxLayout(w)
        o.setContentsMargins(24, 16, 20, 14)
        title = QLabel("Notes")
        title.setObjectName("title")
        o.addWidget(title)
        o.addWidget(QLabel("Local patient-scoped notes for personal context and clinician discussion."))
        self.note_editor = QTextEdit()
        self.note_editor.setPlaceholderText("Write something you want to remember…")
        o.addWidget(self.note_editor, 1)
        save = QPushButton("Save local note")
        save.setObjectName("primary")
        save.clicked.connect(self._save_note)
        o.addWidget(save, 0, Qt.AlignmentFlag.AlignLeft)
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
        try:
            source = str(row.get("source", "")).lower()
            if source not in {"demo", "synthetic"} and not source.startswith("demo"):
                self.personal_model.observe(SimpleNamespace(**row), quality=row.get("signal_quality"))
            self.personal_model.sync_from_disk()
            self.profile = get_profile(self.participant_id)
            if hasattr(self, "personal_text"):
                self._refresh_personal()
        except Exception as exc:
            self.side_state.setText(f"Learning warning • {exc}")
        if hasattr(self, "complication_panel"):
            self.complication_panel.set_context(
                {k: v for k, v in load_state().get("profile", {}).items()}, row
            )
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
