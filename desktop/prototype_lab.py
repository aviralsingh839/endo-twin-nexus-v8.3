"""ENDO-TWIN prototype hardware validation lab.

This UI is an engineering test surface, not a clinical assessment tool.
It observes the same LiveSession that powers the workstation and reports
packet rate, received samples, channel states, quality and simple sanity checks.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QVBoxLayout, QWidget
)

from src.serial_io.arduino_reader import ArduinoReader
from desktop.workstation_theme import card, section_header, pill, status_badge


class PrototypeLabWidget(QWidget):
    """Hands-on sensor/protocol acceptance panel using the active LiveSession."""

    def __init__(self, session, mode, root: Path, parent=None):
        super().__init__(parent)
        self.session = session
        self.mode = mode
        self.root = root
        self.valid_packets = 0
        self.errors = 0
        self.test_active = False
        self.test_elapsed = 0
        self.test_packet_start = 0
        self.test_rows = []
        self.latest = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick_test)
        self._build()

        session.sample_received.connect(self._sample)
        session.features_updated.connect(self._features)
        session.error_received.connect(self._error)
        session.state_changed.connect(self._state)

    def _build(self):
        o = QVBoxLayout(self)
        o.setContentsMargins(24, 18, 20, 15)
        o.setSpacing(12)

        title = QLabel("Prototype Lab")
        title.setObjectName("title")
        o.addWidget(title)
        sub = QLabel(
            "Bench-test your modules before they become part of the main ENDO-TWIN model. "
            "This page validates wiring, transport, quality and processing—not clinical accuracy."
        )
        sub.setObjectName("muted")
        sub.setWordWrap(True)
        o.addWidget(sub)

        top = QGridLayout()
        top.setSpacing(10)
        self.mode_card = card(
            "Session mode",
            "DEMO" if self.mode.mode == "demo" else "LIVE",
            "Startup selection is fixed for this run."
        )
        self.port_card = card(
            "Serial input",
            self.mode.port if self.mode.mode == "live" else "Synthetic stream",
            "115200 baud • CRC-checked $CP3 in LIVE (legacy $CP/$CP2 also parse)"
        )
        self.packet_card = card("Packets", "0", "Valid packets received by this workstation")
        self.rate_card = card("Packet rate", "—", "Observed valid packet rate")
        for i, box in enumerate([self.mode_card, self.port_card, self.packet_card, self.rate_card]):
            top.addWidget(box, 0, i)
        o.addLayout(top)

        controls = QHBoxLayout()
        refresh = QPushButton("Refresh Ports")
        refresh.setObjectName("secondary")
        refresh.clicked.connect(self._refresh_ports)
        controls.addWidget(refresh)

        self.port_hint = QLabel(
            "Available: " + (", ".join(ArduinoReader.available_ports()) or "none detected")
        )
        self.port_hint.setObjectName("muted")
        controls.addWidget(self.port_hint, 1)

        self.test_button = QPushButton("Run 15 s Module Test")
        self.test_button.setObjectName("primary")
        self.test_button.clicked.connect(self._start_test)
        controls.addWidget(self.test_button)

        export = QPushButton("Export Test Report")
        export.setObjectName("secondary")
        export.clicked.connect(self._export_report)
        controls.addWidget(export)
        o.addLayout(controls)

        o.addWidget(section_header(
            "Module status",
            "A green state means the software received plausible data for that channel. It does not prove sensor calibration."
        ))

        grid = QGridLayout()
        grid.setSpacing(10)
        self.modules = {}
        specs = [
            ("PPG / MAX30102", "PPG", "IR + RED waveform, pulse quality - mount on skin, wrist or upper arm"),
            ("IMU / MPU6050", "IMU", "Acceleration + gyroscope"),
            ("DS18B20", "TEMP", "Skin-contact temperature validity at the chosen wear site"),
            ("ECG / AD8232", "ECG", "Raw ECG + lead-off state"),
            ("FSR", "FSR", "Pressure/contact context"),
            ("MAX4466", "MIC", "RMS + experimental pitch"),
            ("BH1750 / BME280", "ENV", "Light / environment - clothing changes what these see (docs/WEAR_SITES.md)"),
        ]
        for i, (name, key, detail) in enumerate(specs):
            box = QFrame()
            box.setObjectName("card")
            v = QVBoxLayout(box)
            head = QHBoxLayout()
            t = QLabel(name)
            t.setStyleSheet("font-weight:850;color:#dfe5ef;")
            head.addWidget(t)
            head.addStretch()
            badge = status_badge("NOT TESTED", "neutral")
            head.addWidget(badge)
            v.addLayout(head)
            value = QLabel("Waiting for live data…")
            value.setObjectName("muted")
            value.setWordWrap(True)
            v.addWidget(value)
            details = QLabel(detail)
            details.setObjectName("muted")
            details.setWordWrap(True)
            v.addWidget(details)
            self.modules[key] = (badge, value)
            grid.addWidget(box, i // 2, i % 2)
        o.addLayout(grid)

        self.test_summary = QFrame()
        self.test_summary.setObjectName("hero")
        sv = QVBoxLayout(self.test_summary)
        sv.addWidget(QLabel("Acceptance test"))
        self.test_status = QLabel(
            "Connect hardware, keep the PPG finger steady, and run the 15-second test."
        )
        self.test_status.setObjectName("muted")
        self.test_status.setWordWrap(True)
        sv.addWidget(self.test_status)
        self.test_summary.setVisible(False)
        o.addWidget(self.test_summary)

        note = QLabel(
            "Expected failure states are useful: missing sensors, bad packets, saturation, stale data "
            "and poor PPG quality should stay visible rather than being replaced with defaults."
        )
        note.setObjectName("warning")
        note.setWordWrap(True)
        o.addWidget(note)
        o.addStretch()

    def _refresh_ports(self):
        self.port_hint.setText(
            "Available: " + (", ".join(ArduinoReader.available_ports()) or "none detected")
        )

    def _set_module(self, key, state, value, kind):
        if key not in self.modules:
            return
        badge, label = self.modules[key]
        badge.setText(state)
        # status_badge returns a QLabel; update semantic colour class by rebuilding the style.
        style = {
            "good": ("#183d35", "#69d5b3", "#28604f"),
            "warn": ("#4a391e", "#e9ae45", "#6b5429"),
            "poor": ("#4d2b25", "#ee8c79", "#714139"),
            "neutral": ("#2a2f3b", "#b4bdcc", "#41495a"),
        }.get(kind, ("#2a2f3b", "#b4bdcc", "#41495a"))
        bg, fg, border = style
        badge.setStyleSheet(
            f"background:{bg};color:{fg};border:1px solid {border};"
            "border-radius:9px;padding:5px 8px;font-weight:800;font-size:10px;"
        )
        label.setText(value)

    def _sample(self, _sample):
        self.valid_packets += 1
        self.packet_card_value().setText(str(self.valid_packets))

    def packet_card_value(self):
        return self.packet_card.findChildren(QLabel)[1]

    def _error(self, msg):
        self.errors += 1
        if "Packet parse error" in msg or "crc" in msg.lower():
            self.test_status.setText(
                f"Packet errors: {self.errors} • latest: {msg}"
            )

    def _state(self, state):
        label = state.upper().replace("_", " ")
        self.test_status.setText(label if not self.test_active else self.test_status.text())
        if state.startswith("connected"):
            self.port_card.findChildren(QLabel)[1].setText(self.mode.port)

    def _features(self, row):
        self.latest = row
        q = row.get("signal_quality")
        ppgq = row.get("ppg_quality")
        flags = list(row.get("status_flags") or [])

        if self.mode.mode == "demo":
            source = "DEMO_DATA"
        else:
            source = "MEASURED"

        self._set_module(
            "PPG",
            "PASS" if ppgq is not None and float(ppgq) >= 0.50 else "CHECK",
            f"HR {row.get('hr_bpm') if row.get('hr_bpm') is not None else 'UNKNOWN'} bpm • "
            f"PPG quality {float(ppgq)*100:.0f}%" if ppgq is not None else "PPG quality UNKNOWN",
            "good" if ppgq is not None and float(ppgq) >= 0.70 else "warn"
        )
        self._set_module(
            "IMU",
            "PASS" if row.get("motion_index") is not None else "CHECK",
            f"Motion index {float(row.get('motion_index', 0.0)):.3f} • activity {float(row.get('activity_level', 0.0)):.1f}",
            "good" if row.get("motion_index") is not None else "warn"
        )
        temp = row.get("skin_temp_c")
        self._set_module(
            "TEMP",
            "PASS" if temp is not None else "CHECK",
            f"Skin temperature {temp:.2f} °C" if temp is not None else "UNKNOWN",
            "good" if temp is not None else "warn"
        )
        self._set_module(
        )
        self._set_module(
            "ECG",
            "LEADS OFF" if "ECG leads off" in flags else "SIGNAL",
            f"Raw {row.get('ecg_raw')} • {'check electrodes' if 'ECG leads off' in flags else 'lead state not flagged'}",
            "warn" if "ECG leads off" in flags else "good"
        )
        self._set_module(
            "FSR",
            "CHECK" if "FSR pressure artifact" in flags else "SIGNAL",
            f"Raw {row.get('fsr_raw')}",
            "warn" if "FSR pressure artifact" in flags else "good"
        )
        self._set_module(
            "MIC",
            "LOW" if "Microphone low signal" in flags else "SIGNAL",
            f"RMS {row.get('mic_rms') if row.get('mic_rms') is not None else 'UNKNOWN'} • "
            f"pitch {row.get('mic_pitch_hz') if row.get('mic_pitch_hz') is not None else 'UNKNOWN'} Hz",
            "warn" if "Microphone low signal" in flags else "good"
        )
        self._set_module(
            "ENV",
            "PASS" if row.get("room_temp_c") is not None or row.get("humidity_pct") is not None else "OPTIONAL",
            f"Room {row.get('room_temp_c') if row.get('room_temp_c') is not None else '—'} °C • "
            f"Humidity {row.get('humidity_pct') if row.get('humidity_pct') is not None else '—'}%",
            "good" if row.get("room_temp_c") is not None or row.get("humidity_pct") is not None else "neutral"
        )
        self._set_rate(row.get("sample_rate_hz"))
        if flags:
            visible = " • ".join(flags[:4])
            self.test_status.setText(f"{source} • quality {float(q)*100:.0f}% • flags: {visible}")
        elif q is not None:
            self.test_status.setText(f"{source} • quality {float(q)*100:.0f}% • no firmware flags")

        if self.test_active:
            self.test_rows.append(row)

    def _set_rate(self, rate):
        if rate is None:
            return
        self.rate_card.findChildren(QLabel)[1].setText(f"{float(rate):.1f} Hz")

    def _start_test(self):
        if self.test_active:
            return
        self.test_active = True
        self.test_elapsed = 0
        self.test_packet_start = self.valid_packets
        self.test_rows = []
        self.test_summary.setVisible(True)
        self.test_status.setText(
            "TEST RUNNING • keep the board still for IMU/TEMP and keep a stable finger on PPG."
        )
        self.test_button.setEnabled(False)
        self.test_button.setText("Test running…")
        self.timer.start(1000)

    def _tick_test(self):
        self.test_elapsed += 1
        left = max(0, 15 - self.test_elapsed)
        self.test_status.setText(
            f"TEST RUNNING • {left}s remaining • {self.valid_packets - self.test_packet_start} valid packets"
        )
        if self.test_elapsed >= 15:
            self.timer.stop()
            self.test_active = False
            self.test_button.setEnabled(True)
            self.test_button.setText("Run 15 s Module Test")
            self._finish_test()

    def _finish_test(self):
        rows = self.test_rows
        packets = self.valid_packets - self.test_packet_start
        flags = sorted({flag for row in rows for flag in (row.get("status_flags") or [])})
        have = {
            "ppg": any(r.get("raw_ir") is not None and r.get("raw_red") is not None for r in rows),
            "hr": any(r.get("hr_bpm") is not None for r in rows),
            "hrv": any(r.get("rmssd_ms") is not None for r in rows),
            "temp": any(r.get("skin_temp_c") is not None for r in rows),
            "imu": any(r.get("motion_index") is not None for r in rows),
        }
        qvals = [float(r["signal_quality"]) for r in rows if r.get("signal_quality") is not None]
        avg_q = sum(qvals) / len(qvals) if qvals else None
        lines = [
            "ENDO-TWIN PROTOTYPE MODULE TEST",
            f"Run time: {datetime.now().isoformat(timespec='seconds')}",
            f"Mode: {'DEMO_DATA' if self.mode.mode == 'demo' else 'LIVE SENSOR'}",
            f"Serial port: {self.mode.port or 'synthetic'}",
            f"Valid packets in test: {packets}",
            f"Packet/parse errors observed by lab: {self.errors}",
            f"Average aggregate signal quality: {avg_q:.3f}" if avg_q is not None else "Average aggregate signal quality: UNKNOWN",
            "",
            "MODULE CHECKS",
            f"PPG raw: {'PASS' if have['ppg'] else 'UNKNOWN'}",
            f"Pulse rate: {'PASS' if have['hr'] else 'UNKNOWN'}",
            f"HRV feature: {'PASS' if have['hrv'] else 'UNKNOWN / insufficient evidence'}",
            f"Temperature: {'PASS' if have['temp'] else 'UNKNOWN'}",
            f"IMU: {'PASS' if have['imu'] else 'UNKNOWN'}",
            f"Firmware flags: {'; '.join(flags) if flags else 'none observed'}",
            "",
            "INTERPRETATION",
            "PASS means the software received/processsed a signal during this engineering test.",
            "It does not establish sensor calibration, medical accuracy or clinical validity.",
        ]
        self.test_status.setText(
            f"TEST COMPLETE • {packets} packets • "
            f"average quality {avg_q*100:.0f}%" if avg_q is not None else f"TEST COMPLETE • {packets} packets"
        )
        self.test_summary.findChildren(QLabel)[1].setText("\n".join(lines))

    def _export_report(self):
        default_dir = self.root / "data" / "prototype_tests"
        default_dir.mkdir(parents=True, exist_ok=True)
        default = default_dir / f"prototype_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Prototype Test", str(default), "Text files (*.txt)"
        )
        if not path:
            return
        summary = self.test_summary.findChildren(QLabel)[1].text() if self.test_summary.isVisible() else "No completed test yet."
        Path(path).write_text(summary, encoding="utf-8")
        QMessageBox.information(self, "Prototype Lab", f"Saved test report:\n{path}")
