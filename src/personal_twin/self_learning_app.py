"""Standalone Personal Twin / Self-Learning workstation.

Workflow:
1. Select or create a person.
2. Enter patient name and contextual details.
3. Select the wearable transport.
4. Capture that person's research baseline.
5. Persist adaptive learning + baseline under that participant ID.

No demo data is allowed to become a learned baseline.
"""
from __future__ import annotations

import json
import math
import sys
import time
from datetime import datetime

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QFormLayout, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from src.personal_twin.profile_store import (
    append_event, get_profile, list_profiles, select_participant,
)
from src.personal_twin.adaptive_model import PersonalAdaptiveModel
from src.personal_twin.onboarding import MULTI_PERSON_DISCLAIMER, PersonalTwinOnboarding
from src.personal_twin.baseline_store import baseline_engine, baseline_summary
from src.data_models import FeatureVector
from src.utils.history_store import HistoryStore
from desktop.workstation_runtime import LiveSession, ModeConfig, choose_mode, RingGauge, metric_card, trend_panel


def row_to_feature(row: dict) -> FeatureVector:
    def num(key, default=None):
        value = row.get(key, default)
        try:
            return float(value) if value is not None else default
        except (TypeError, ValueError):
            return default

    return FeatureVector(
        timestamp_s=num("timestamp", time.time()),
        hr_bpm=num("hr_bpm"),
        rmssd_ms=num("rmssd_ms"),
        sdnn_ms=num("sdnn_ms"),
        spo2_pct=num("spo2_pct"),
        skin_temp_c=num("skin_temp_c"),
        room_temp_c=num("room_temp_c"),
        humidity_pct=num("humidity_pct"),
        pressure_hpa=num("pressure_hpa"),
        lux=num("lux"),
        gsr_tonic=num("gsr_tonic"),
        gsr_phasic_per_min=num("gsr_phasic_per_min", 0.0),
        motion_index=num("motion_index", 0.0),
        activity_level=num("activity_level", 0.0),
        signal_quality=num("signal_quality", 0.0),
        stress_index=num("stress_index", 0.0),
        sleep_probability=num("sleep_probability", 0.0),
        sleep_duration_h=num("sleep_duration_h"),
        sleep_regularity=num("sleep_regularity", 0.0),
        circadian_stability_index=num("circadian_stability_index", 50.0),
    )


class SelfLearningWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ENDO-TWIN • Self-Learning Personal Twin")
        self.resize(1300, 820)

        self.participant_id = None
        self.personal_model = None
        self.session = None
        self.session_id = None
        self.baseline_rows: list[FeatureVector] = []
        self.capture_started_at = None
        self.visual_graphs = {}
        self.latest_feature = None
        self.history_store = HistoryStore()

        root = QVBoxLayout(self)

        hero = QFrame()
        hero.setObjectName("hero")
        hv = QVBoxLayout(hero)
        title = QLabel("Self-Learning Personal Twin")
        title.setStyleSheet("font-size:30px;font-weight:900;")
        hv.addWidget(title)
        sub = QLabel(
            "Create a separate patient record, capture that person's baseline, and keep "
            "the learned data available to the Doctor, Patient and Unified Workstations."
        )
        sub.setWordWrap(True)
        hv.addWidget(sub)
        root.addWidget(hero)

        split = QHBoxLayout()

        left = QFrame()
        lv = QVBoxLayout(left)
        lv.addWidget(QLabel("PATIENTS"))
        self.people = QListWidget()
        self.people.currentItemChanged.connect(self._select_from_list)
        lv.addWidget(self.people, 1)

        actions = QHBoxLayout()
        add = QPushButton("＋ New Patient")
        add.clicked.connect(self._add_patient)
        actions.addWidget(add)
        edit = QPushButton("Edit")
        edit.clicked.connect(self._edit_patient)
        actions.addWidget(edit)
        lv.addLayout(actions)

        split.addWidget(left, 1)

        right = QFrame()
        rv = QVBoxLayout(right)

        self.patient_title = QLabel("No patient selected")
        self.patient_title.setStyleSheet("font-size:24px;font-weight:900;")
        rv.addWidget(self.patient_title)

        self.patient_details = QLabel("Create a patient to begin.")
        self.patient_details.setWordWrap(True)
        rv.addWidget(self.patient_details)

        live_card = QFrame()
        lv = QVBoxLayout(live_card)
        lv.addWidget(QLabel("LIVE READINGS"))
        live_grid = QGridLayout()
        self.live_hr = QLabel("HR: —")
        self.live_hrv = QLabel("HRV: —")
        self.live_temp = QLabel("Temperature: —")
        self.live_gsr = QLabel("GSR: —")
        self.live_activity = QLabel("Activity: —")
        self.live_quality = QLabel("Quality: —")
        for idx, widget in enumerate([self.live_hr,self.live_hrv,self.live_temp,self.live_gsr,self.live_activity,self.live_quality]):
            widget.setStyleSheet("font-size:15px;font-weight:750;")
            live_grid.addWidget(widget, idx//3, idx%3)
        lv.addLayout(live_grid)
        rv.addWidget(live_card)

        self.baseline_card = QFrame()
        bv = QVBoxLayout(self.baseline_card)
        bv.addWidget(QLabel("PERSONAL BASELINE"))
        self.baseline_status = QLabel("No baseline stored")
        self.baseline_status.setStyleSheet("font-size:20px;font-weight:850;")
        bv.addWidget(self.baseline_status)

        baseline_grid = QGridLayout()
        self.baseline_samples = QLabel("Samples: —")
        self.baseline_quality = QLabel("Quality: —")
        self.baseline_conf = QLabel("Confidence: —")
        self.baseline_captured = QLabel("Captured: —")
        baseline_grid.addWidget(self.baseline_samples, 0, 0)
        baseline_grid.addWidget(self.baseline_quality, 0, 1)
        baseline_grid.addWidget(self.baseline_conf, 1, 0)
        baseline_grid.addWidget(self.baseline_captured, 1, 1)
        bv.addLayout(baseline_grid)
        rv.addWidget(self.baseline_card)

        visual = QGridLayout()
        summary = baseline_summary(self.participant_id) if self.participant_id else {"available": False, "quality": 0.0, "confidence": 0.0}
        snap = self.personal_model.snapshot() if self.personal_model else {"samples": 0}
        visual.addWidget(metric_card("Learning samples", f"{snap['samples']:,}", "Patient-specific", accent="#39c9ff"), 0, 0)
        visual.addWidget(metric_card("Baseline status", "READY" if summary["available"] else "BUILDING", "Stored locally", accent="#31d7a1"), 0, 1)
        visual.addWidget(RingGauge("Confidence", summary["confidence"] * 100 if summary["available"] else 0, "%", "#7d62ff"), 0, 2)
        self.baseline_hr_graph = trend_panel("Baseline HR", [], "bpm", "#ff4fa3", 135)
        self.baseline_hrv_graph = trend_panel("Baseline HRV", [], "ms", "#39c9ff", 135)
        visual.addWidget(self.baseline_hr_graph, 1, 0, 1, 2)
        visual.addWidget(self.baseline_hrv_graph, 1, 2)
        rv.addLayout(visual)

        capture_row = QHBoxLayout()
        self.duration = QSpinBox()
        self.duration.setRange(1, 60)
        self.duration.setValue(5)
        self.duration.setSuffix(" min")
        capture_row.addWidget(QLabel("Research baseline duration"))
        capture_row.addWidget(self.duration)

        self.ppg_calibrate = QPushButton("Calibrate PPG (5 s)")
        self.ppg_calibrate.setEnabled(False)
        self.ppg_calibrate.clicked.connect(self._calibrate_ppg)
        capture_row.addWidget(self.ppg_calibrate)

        self.capture = QPushButton("Start Baseline Capture")
        self.capture.setObjectName("primary")
        self.capture.clicked.connect(self._start_capture)
        capture_row.addWidget(self.capture)

        self.stop = QPushButton("Stop")
        self.stop.clicked.connect(self._stop_capture)
        self.stop.setEnabled(False)
        capture_row.addWidget(self.stop)
        capture_row.addStretch()
        rv.addLayout(capture_row)

        self.progress = QLabel("Waiting for a patient and wearable.")
        self.progress.setWordWrap(True)
        rv.addWidget(self.progress)

        disc = QLabel(MULTI_PERSON_DISCLAIMER)
        disc.setWordWrap(True)
        disc.setObjectName("warning")
        rv.addWidget(disc)

        note = QLabel(
            "Baseline is a research/personalization reference, not a medical diagnosis or clinical calibration. "
            "Repeated measurements over time improve the personal reference."
        )
        note.setWordWrap(True)
        rv.addWidget(note)

        rv.addStretch()
        split.addWidget(right, 2)
        root.addLayout(split, 1)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._capture_tick)

        self._refresh_people()

    def _refresh_people(self):
        current = self.participant_id
        self.people.clear()
        for p in list_profiles():
            pid = str(p.get("participant_id"))
            alias = str(p.get("patient_name") or p.get("alias") or "Unnamed")
            item = QListWidgetItem(f"{alias}  •  {pid}")
            item.setData(Qt.ItemDataRole.UserRole, pid)
            self.people.addItem(item)
            if pid == current:
                self.people.setCurrentItem(item)
        if self.people.currentRow() < 0 and self.people.count():
            self.people.setCurrentRow(0)
        self._refresh_patient_view()

    def _select_from_list(self, current, _previous):
        if current is None:
            return
        pid = str(current.data(Qt.ItemDataRole.UserRole))
        select_participant(pid)
        self.participant_id = pid
        self.personal_model = PersonalAdaptiveModel(pid)
        self._refresh_patient_view()

    def _add_patient(self):
        dlg = PersonalTwinOnboarding(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_people()

    def _edit_patient(self):
        if not self.participant_id:
            QMessageBox.information(self, "Patient", "Select a patient first.")
            return
        dlg = PersonalTwinOnboarding(self.participant_id, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_people()

    @staticmethod
    def _fmt(value, suffix=""):
        if value is None:
            return "—"
        try:
            value = float(value)
            if not math.isfinite(value):
                return "—"
            return f"{value:.1f}{suffix}"
        except (TypeError, ValueError):
            return str(value)

    def _refresh_patient_view(self):
        if not self.participant_id:
            self.patient_title.setText("No patient selected")
            self.patient_details.setText("Create a patient to begin.")
            self.baseline_status.setText("No baseline stored")
            self.baseline_samples.setText("Samples: —")
            self.baseline_quality.setText("Quality: —")
            self.baseline_conf.setText("Confidence: —")
            self.baseline_captured.setText("Captured: —")
            return

        p = get_profile(self.participant_id)
        self.patient_title.setText(str(p.get("patient_name") or p.get("alias") or self.participant_id))
        self.patient_details.setText(
            f"Participant ID: {self.participant_id}\n{json.dumps({k:v for k,v in p.items() if k not in {'participant_id','updated_at','provenance'}}, indent=2)}"
        )

        summary = baseline_summary(self.participant_id)
        if not summary["available"]:
            self.baseline_status.setText("NO BASELINE STORED")
            self.baseline_samples.setText("Samples: 0")
            self.baseline_quality.setText("Quality: —")
            self.baseline_conf.setText("Confidence: —")
            self.baseline_captured.setText("Captured: —")
        else:
            self.baseline_status.setText("BASELINE STORED")
            self.baseline_samples.setText(f"Samples: {summary['samples']:,}")
            self.baseline_quality.setText(f"Quality: {summary['quality']:.2f}")
            self.baseline_conf.setText(f"Confidence: {summary['confidence']:.2f}")
            stamp = datetime.fromtimestamp(float(summary["captured_at"])).strftime("%Y-%m-%d %H:%M")
            self.baseline_captured.setText(f"Captured: {stamp}")

        if self.personal_model is None:
            self.personal_model = PersonalAdaptiveModel(self.participant_id)

    def _calibrate_ppg(self):
        if self.session is None:
            self.progress.setText("Start a LIVE baseline session first.")
            return
        self.session.write_command(f"PPG_PERSON={self.participant_id}")
        self.session.write_command("PPG_NEW_PERSON")
        self.progress.setText(f"PPG calibration started for {self.participant_id} • keep finger still for 5 s.")

    def _start_capture(self):
        if not self.participant_id:
            QMessageBox.warning(self, "Baseline", "Create or select a patient first.")
            return

        self._stop_capture()
        mode = choose_mode("ENDO-TWIN • Baseline Capture")
        if mode is None:
            return
        if mode.mode == "demo":
            QMessageBox.warning(
                self, "Baseline Capture",
                "Demo data cannot be stored as a person's baseline. Choose ESP32 USB or Wi-Fi live mode."
            )
            return

        self.baseline_rows = []
        self.feature_window_count = 0
        self.capture_started_at = time.time()
        self.personal_model = PersonalAdaptiveModel(self.participant_id)
        self.session = LiveSession(mode, self)
        self.session.features_updated.connect(self._on_features)
        self.session.calibration_received.connect(self._on_ppg_calibration)
        self.session.sample_received.connect(self._on_sample)
        self.session.error_received.connect(self._on_error)
        self.session.state_changed.connect(self._on_state)
        self.session_id = self.history_store.start_session(
            source=f"self-learning:{mode.mode}",
            note="Patient baseline capture",
            participant_id=self.participant_id,
        )
        self.session.start()
        self.capture.setEnabled(False)
        self.stop.setEnabled(True)
        self.ppg_calibrate.setEnabled(True)
        self.progress.setText(
            f"CAPTURING BASELINE • {self.duration.value()} min • keep the wearable positioned calmly."
        )
        self.refresh_timer.start(1000)
        append_event({
            "kind": "baseline_capture_started",
            "participant_id": self.participant_id,
            "duration_target_s": self.duration.value() * 60,
        })

    def _stop_capture(self):
        self.refresh_timer.stop()
        if self.session is not None:
            try:
                self.session.stop()
            except Exception:
                pass
            self.session = None
        if self.session_id is not None:
            try:
                self.history_store.end_session(self.session_id, sample_count=len(self.baseline_rows))
            except Exception:
                pass
            self.session_id = None
        self.stop.setEnabled(False)
        self.capture.setEnabled(True)
        self.ppg_calibrate.setEnabled(False)

    def _on_ppg_calibration(self, event):
        self.progress.setText(f"PPG calibration saved • {event.profile_id} • quality {event.quality:.0f}%")

    def _on_state(self, state):
        self.progress.setText(f"Baseline capture • {state.replace('_', ' ').upper()} • {len(self.baseline_rows)} feature windows")

    def _on_error(self, msg):
        self.progress.setText(f"Wearable error • {msg}")

    def _on_sample(self, sample):
        source = str(getattr(sample, "source", "")).lower()
        if source.startswith("serial") or source.startswith("wifi"):
            append_event({
                "kind": "raw_sensor_sample",
                "participant_id": self.participant_id,
                "ms": getattr(sample, "ms", None),
                "source": getattr(sample, "source", None),
                "values": {
                    key: getattr(sample, key, None) for key in (
                        "analog_ppg_raw", "ir", "red", "gsr_raw",
                        "ax_g", "ay_g", "az_g", "gx_dps", "gy_dps", "gz_dps",
                        "temp_c", "room_temp_c", "humidity_pct", "pressure_hpa", "lux", "status"
                    )
                }
            })

    def _on_features(self, row):
        if str(row.get("source", "")).lower() in {"demo", "synthetic"}:
            return
        feature = row_to_feature(row)
        q = float(row.get("signal_quality", 0.0) or 0.0)
        usable = str(row.get("gating", "")) == "USABLE" and q >= 0.45
        if usable:
            self.baseline_rows.append(feature)
        self.baseline_hr_graph.graph.set_values([x.hr_bpm for x in self.baseline_rows if x.hr_bpm is not None][-120:])
        self.baseline_hrv_graph.graph.set_values([x.rmssd_ms for x in self.baseline_rows if x.rmssd_ms is not None][-120:])
        if self.session_id is not None:
            try:
                self.history_store.log_feature(
                    self.session_id,
                    {
                        "ts": feature.timestamp_s,
                        "hr": feature.hr_bpm,
                        "rmssd": feature.rmssd_ms,
                        "skin_temp": feature.skin_temp_c,
                        "gsr": feature.gsr_tonic,
                        "activity": feature.activity_level,
                        "stress": feature.stress_index,
                        "sleep_prob": feature.sleep_probability,
                        "signal_quality": feature.signal_quality,
                    },
                    extra_json=json.dumps({
                        "participant_id": self.participant_id,
                        "source": "SELF_LEARNING_BASELINE",
                    }),
                )
            except Exception:
                pass
        self.personal_model.observe(feature, quality=feature.signal_quality)
        self.latest_feature = feature
        self.live_hr.setText(f"HR: {self._fmt(feature.hr_bpm, ' bpm')}")
        self.live_hrv.setText(f"HRV: {self._fmt(feature.rmssd_ms, ' ms')}")
        temp = feature.skin_temp_c if feature.skin_temp_c is not None else feature.room_temp_c
        self.live_temp.setText(f"Temperature: {self._fmt(temp, ' °C')}")
        self.live_gsr.setText(f"GSR: {self._fmt(feature.gsr_tonic, '')}")
        self.live_activity.setText(f"Activity: {self._fmt(feature.activity_level, '')}")
        self.live_quality.setText(f"Quality: {feature.signal_quality*100:.0f}%")
        self.progress.setText(
            f"LIVE • {self.feature_window_count} feature windows • "
            f"CAPTURING • {len(self.baseline_rows)} usable feature windows • "
            f"latest quality {feature.signal_quality:.2f}"
        )

    def _capture_tick(self):
        if self.capture_started_at is None:
            return
        elapsed = time.time() - self.capture_started_at
        target = self.duration.value() * 60
        self.progress.setText(
            f"CAPTURING BASELINE • {elapsed/60.0:.1f}/{self.duration.value()} min • "
            f"{len(self.baseline_rows)} quality-gated feature windows"
        )
        if elapsed >= target:
            self._finish_capture()

    def _finish_capture(self):
        if not self.baseline_rows:
            self._stop_capture()
            QMessageBox.warning(self, "Baseline", "No live feature windows were received.")
            return
        self._stop_capture()
        engine = baseline_engine(self.participant_id)
        try:
            if len(self.baseline_rows) < 60:
                self.capture_started_at = None
                QMessageBox.warning(self, "Baseline", f"Only {len(self.baseline_rows)} quality-gated windows were captured. Need at least 60.")
                return
            baseline = engine.capture_from_features(
                self.baseline_rows,
                min_samples=60,
            )
            self.personal_model.flush()
            append_event({
                "kind": "baseline_capture_completed",
                "participant_id": self.participant_id,
                "samples": baseline.samples,
                "duration_s": baseline.duration_s,
                "quality": baseline.quality,
                "confidence": baseline.confidence,
                "metrics": list(baseline.stats.keys()),
            })
            self.capture_started_at = None
            self.baseline_rows = []
            self._refresh_patient_view()
            self.progress.setText(
                f"BASELINE STORED for {self.participant_id}. "
                f"{baseline.samples} windows • quality {baseline.quality:.2f}."
            )
        except Exception as exc:
            self.capture_started_at = None
            self.baseline_rows = []
            self.progress.setText(f"Baseline not stored • {exc}")
            QMessageBox.warning(self, "Baseline", str(exc))


def run():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    w = SelfLearningWindow()
    w.showMaximized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
