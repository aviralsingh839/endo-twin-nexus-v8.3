"""Wearable link for the ENDO-TWIN NEXUS workstation.

Owns the connection to the ESP32-S3 wearable and turns its `$CP2` frames into
calibrated, persisted physiology. Four transports, all dependency-free:

``ble``     Browser Web Bluetooth (the firmware's GATT service). The page reads
            notifications and POSTs the frames to /api/device/ingest.
``usb``     Browser Web Serial (Chrome/Edge) at 115200 baud, same POST path.
``serial``  Server-side pyserial reader (only when pyserial is installed).
``wifi``    The board (or any script) POSTs frames straight to /api/device/ingest.
``bridge``  Tail newline-delimited frames dropped into data/bridge/inbox/.

The manager keeps a rolling buffer for the live view and writes calibrated rows
into the platform's own SQLite tables when a recording session is active.
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

from signals import (GSRProcessor, IMUProcessor, PacketError, PulseProcessor, TempProcessor,
                     merge_calibration, parse_packet, status_report)

TRANSPORTS = {
    "ble": "Bluetooth LE (browser)",
    "usb": "USB serial (browser)",
    "serial": "USB serial (server / pyserial)",
    "wifi": "Wi-Fi HTTP ingest",
    "bridge": "Bridge folder",
}
STALE_AFTER_S = 6.0
FLUSH_EVERY_S = 2.0
LIVE_LABEL = "LIVE_DEVICE"


class DeviceManager:
    """Single wearable link shared by every browser tab."""

    def __init__(self, api) -> None:
        self.api = api                      # WorkstationAPI (for DB writes)
        self.lock = threading.RLock()
        self.state = "disconnected"         # disconnected|waiting|connected|stale|error
        self.transport: Optional[str] = None
        self.endpoint: Optional[str] = None
        self.device_name: Optional[str] = None
        self.firmware: Optional[str] = None
        self.error: Optional[str] = None
        self.connected_at: Optional[float] = None
        self.last_packet_at: Optional[float] = None

        self.packets = 0
        self.bad_crc = 0
        self.bad_frames = 0
        self.seq = 0
        self.buffer: Deque[Dict[str, Any]] = deque(maxlen=1200)
        self.log: Deque[str] = deque(maxlen=120)
        self.status_bits = 0

        self.pulse = PulseProcessor()
        self.gsr = GSRProcessor()
        self.temp = TempProcessor()
        self.imu = IMUProcessor()

        self.session_id: Optional[str] = None
        self.session_patient: Optional[str] = None
        self.session_started: Optional[float] = None
        self.session_rows = 0
        self._pending: List[Dict[str, Any]] = []
        self._last_flush = time.time()
        self._serial_stop = threading.Event()
        self._serial_thread: Optional[threading.Thread] = None
        self._bridge_stop = threading.Event()
        self._bridge_thread: Optional[threading.Thread] = None
        self._rate: Deque[float] = deque(maxlen=60)
        self._ms0: Optional[float] = None      # device clock anchor
        self._t0: Optional[float] = None       # host clock anchor

    # ----------------------------- calibration ---------------------------- #
    def calibration(self, patient_id: Optional[str] = None) -> Dict[str, Any]:
        return merge_calibration(self.api.get_calibration(patient_id))

    def save_calibration(self, patch: Dict[str, Any], patient_id: Optional[str] = None) -> Dict[str, Any]:
        cur = self.api.get_calibration(patient_id) or {}
        for sensor, params in (patch or {}).items():
            if not isinstance(params, dict):
                continue
            cur.setdefault(sensor, {})
            for k, v in params.items():
                cur[sensor][k] = v
        self.api.set_calibration(cur, patient_id)
        return self.calibration(patient_id)

    def reset_calibration(self, sensor: Optional[str] = None,
                          patient_id: Optional[str] = None) -> Dict[str, Any]:
        cur = self.api.get_calibration(patient_id) or {}
        if sensor:
            cur.pop(sensor, None)
        else:
            cur = {}
        self.api.set_calibration(cur, patient_id)
        return self.calibration(patient_id)

    def capture_baseline(self, sensor: str, patient_id: Optional[str] = None) -> Dict[str, Any]:
        """Use the samples currently in the buffer as the resting reference."""
        with self.lock:
            if not self.buffer:
                raise ValueError("No samples captured yet — connect the wearable first.")
            recent = list(self.buffer)[-200:]
        patch: Dict[str, Any] = {}
        if sensor == "ppg":
            vals = [s["raw"]["pulse_raw"] for s in recent if s["raw"].get("pulse_raw") is not None]
            if not vals:
                raise ValueError("No pulse samples in the buffer.")
            vals.sort()
            patch = {"ppg": {"baseline_raw": round(vals[len(vals) // 2], 1)}}
        elif sensor == "gsr":
            vals = [s["raw"]["gsr_raw"] for s in recent if s["raw"].get("gsr_raw") is not None]
            if not vals:
                raise ValueError("No GSR samples in the buffer.")
            vals.sort()
            patch = {"gsr": {"dry_baseline_raw": round(vals[len(vals) // 2], 1)}}
        elif sensor == "imu":
            axs = [s["raw"].get("ax") for s in recent if s["raw"].get("ax") is not None]
            ays = [s["raw"].get("ay") for s in recent if s["raw"].get("ay") is not None]
            azs = [s["raw"].get("az") for s in recent if s["raw"].get("az") is not None]
            if not axs:
                raise ValueError("No IMU samples in the buffer.")
            avg = lambda xs: round(sum(xs) / len(xs), 4)
            patch = {"imu": {"ax_offset": avg(axs), "ay_offset": avg(ays), "az_offset": avg(azs) - 1.0}}
        else:
            raise ValueError("Baseline capture is available for ppg, gsr and imu.")
        return self.save_calibration(patch, patient_id)

    def reference_point(self, sensor: str, reference: float, point: str = "low",
                        patient_id: Optional[str] = None) -> Dict[str, Any]:
        """Two-point calibration against a trusted reference instrument."""
        with self.lock:
            recent = list(self.buffer)[-60:]
        if sensor == "temp":
            vals = [s["raw"].get("temp_raw_c") for s in recent if s["raw"].get("temp_raw_c") is not None]
            if not vals:
                raise ValueError("No temperature samples in the buffer.")
            measured = round(sum(vals) / len(vals), 3)
            cal = self.calibration(patient_id)["temp"]
            patch = {"temp": {f"ref_{point}_c": float(reference), f"meas_{point}_c": measured}}
            lo_r = float(reference) if point == "low" else cal.get("ref_low_c")
            lo_m = measured if point == "low" else cal.get("meas_low_c")
            hi_r = float(reference) if point == "high" else cal.get("ref_high_c")
            hi_m = measured if point == "high" else cal.get("meas_high_c")
            if None not in (lo_r, lo_m, hi_r, hi_m) and abs(hi_m - lo_m) > 0.05:
                slope = (hi_r - lo_r) / (hi_m - lo_m)
                patch["temp"].update({"slope": round(slope, 5),
                                      "offset_c": round(lo_r - slope * lo_m, 4)})
            else:
                patch["temp"]["offset_c"] = round(float(reference) - measured, 4)
                patch["temp"]["slope"] = 1.0
            return self.save_calibration(patch, patient_id)
        if sensor == "ppg":
            feats = self.pulse.features(self.calibration(patient_id)["ppg"])
            if not feats.get("hr_bpm"):
                raise ValueError("No stable pulse yet — wait for a heart rate reading.")
            return self.save_calibration(
                {"ppg": {"hr_offset_bpm": round(float(reference) - feats["hr_bpm"], 2)}}, patient_id)
        if sensor == "gsr":
            vals = [s["derived"].get("gsr_us") for s in recent if s["derived"].get("gsr_us") is not None]
            if not vals:
                raise ValueError("No usable GSR reading — check the electrodes.")
            measured = sum(vals) / len(vals)
            if measured <= 0:
                raise ValueError("Measured conductance is zero.")
            return self.save_calibration({"gsr": {"gain_us": round(float(reference) / measured, 4)}}, patient_id)
        if sensor == "spo2":
            return self.save_calibration({"spo2": {"reference_pct": float(reference)}}, patient_id)
        raise ValueError("Unsupported sensor for reference calibration: %s" % sensor)

    # ------------------------------ connection ---------------------------- #
    def connect(self, transport: str, opts: Dict[str, Any]) -> Dict[str, Any]:
        transport = (transport or "").lower()
        if transport not in TRANSPORTS:
            raise ValueError("Unknown transport '%s'" % transport)
        self.disconnect(keep_stats=False)
        with self.lock:
            self._ms0 = self._t0 = None
            self.transport = transport
            self.endpoint = opts.get("endpoint") or opts.get("port") or opts.get("path")
            self.device_name = opts.get("name") or "ENDO-TWIN Wearable"
            self.firmware = opts.get("firmware")
            self.error = None
            self.connected_at = time.time()
            self.state = "connected" if transport in ("ble", "usb") else "waiting"
            self._note(f"link opened · {TRANSPORTS[transport]}"
                       + (f" · {self.endpoint}" if self.endpoint else ""))
        if transport == "serial":
            self._start_serial(self.endpoint, int(opts.get("baud") or 115200))
        if transport == "bridge":
            self._start_bridge(self.endpoint)
        if opts.get("patientId"):
            try:
                self.start_session(opts["patientId"])
            except Exception:
                pass
        return self.status()

    def disconnect(self, keep_stats: bool = True) -> Dict[str, Any]:
        self._serial_stop.set(); self._bridge_stop.set()
        if self._serial_thread and self._serial_thread.is_alive():
            self._serial_thread.join(timeout=1.5)
        if self._bridge_thread and self._bridge_thread.is_alive():
            self._bridge_thread.join(timeout=1.5)
        self._serial_thread = self._bridge_thread = None
        if self.session_id:
            try:
                self.stop_session()
            except Exception:
                pass
        with self.lock:
            self.state = "disconnected"
            self.transport = None
            self.endpoint = None
            self.connected_at = None
            if not keep_stats:
                self.packets = self.bad_crc = self.bad_frames = 0
                self.buffer.clear(); self._rate.clear()
            self._note("link closed")
        return self.status()

    @staticmethod
    def list_ports() -> Dict[str, Any]:
        try:
            from serial.tools import list_ports  # type: ignore
        except Exception:
            return {"available": False, "ports": [],
                    "hint": "Server-side serial needs pyserial (pip install pyserial). "
                            "Use the browser USB / Bluetooth options instead — they need no extra package."}
        ports = [{"device": p.device, "description": p.description,
                  "hwid": getattr(p, "hwid", "")} for p in list_ports.comports()]
        return {"available": True, "ports": ports, "hint": None}

    def _start_serial(self, port: Optional[str], baud: int) -> None:
        try:
            import serial  # type: ignore
        except Exception:
            with self.lock:
                self.state = "error"
                self.error = ("pyserial is not installed in this environment. "
                              "Install it (pip install pyserial) or use the browser USB / BLE transport.")
                self._note("serial unavailable: pyserial missing")
            return
        if not port:
            with self.lock:
                self.state = "error"; self.error = "No serial port selected."
            return
        self._serial_stop = threading.Event()

        def run() -> None:
            try:
                with serial.Serial(port, baud, timeout=1.0) as ser:
                    with self.lock:
                        self.state = "connected"; self._note(f"serial open {port} @ {baud}")
                    while not self._serial_stop.is_set():
                        line = ser.readline().decode("utf-8", "ignore").strip()
                        if line:
                            self.ingest_line(line)
            except Exception as exc:                      # pragma: no cover - hardware path
                with self.lock:
                    self.state = "error"; self.error = str(exc); self._note(f"serial error: {exc}")

        self._serial_thread = threading.Thread(target=run, daemon=True)
        self._serial_thread.start()

    def _start_bridge(self, path: Optional[str]) -> None:
        folder = Path(path or (Path(__file__).resolve().parent.parent / "data" / "bridge" / "inbox"))
        folder.mkdir(parents=True, exist_ok=True)
        self.endpoint = str(folder)
        self._bridge_stop = threading.Event()

        def run() -> None:
            offsets: Dict[str, int] = {}
            with self.lock:
                self._note(f"watching {folder}")
            while not self._bridge_stop.is_set():
                try:
                    for f in sorted(folder.glob("*")):
                        if not f.is_file():
                            continue
                        pos = offsets.get(f.name, 0)
                        size = f.stat().st_size
                        if size <= pos:
                            continue
                        with f.open("r", errors="ignore") as fh:
                            fh.seek(pos)
                            for line in fh:
                                line = line.strip()
                                if line:
                                    self.ingest_line(line)
                            offsets[f.name] = fh.tell()
                except Exception as exc:                  # pragma: no cover
                    with self.lock:
                        self.error = str(exc)
                time.sleep(0.4)

        self._bridge_thread = threading.Thread(target=run, daemon=True)
        self._bridge_thread.start()

    # -------------------------------- ingest ------------------------------ #
    def ingest_line(self, line: str) -> Optional[Dict[str, Any]]:
        try:
            raw = parse_packet(line)
        except PacketError as exc:
            with self.lock:
                self.bad_frames += 1
                self._note(f"bad frame: {exc}")
            return None
        return self._accept(raw, line)

    def ingest(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Accept frames (`lines`/`line`) or already-decoded `samples`."""
        lines = body.get("lines") or ([body["line"]] if body.get("line") else [])
        if isinstance(lines, str):
            lines = lines.splitlines()
        accepted = 0
        for ln in lines:
            if self.ingest_line(ln):
                accepted += 1
        for s in body.get("samples") or []:
            if isinstance(s, dict):
                s = dict(s)
                s.setdefault("t", time.time())
                s.setdefault("crc_ok", True)
                s.setdefault("status", 0)
                s.setdefault("flags", [])
                if self._accept(s, None):
                    accepted += 1
        if body.get("name") or body.get("firmware") or body.get("transport"):
            with self.lock:
                self.device_name = body.get("name") or self.device_name
                self.firmware = body.get("firmware") or self.firmware
                if body.get("transport") and not self.transport:
                    self.transport = body["transport"]
                    self.connected_at = self.connected_at or time.time()
        return {"accepted": accepted, "status": self.status()}

    def _timestamp(self, raw: Dict[str, Any]) -> float:
        """Reconstruct sample time from the device millisecond clock.

        Frames arrive in batches (BLE notifications, HTTP posts), so host arrival
        time would squash a second of physiology into a few milliseconds and
        destroy the beat intervals. The board's own `ms` counter keeps the
        spacing exact; we only re-anchor it when the device reboots or drifts.
        """
        now = float(raw.get("t") or time.time())
        ms = raw.get("ms")
        if ms is None:
            return now
        ms = float(ms)
        if self._ms0 is None or self._t0 is None or ms < (self._ms0 - 1000):
            self._ms0, self._t0 = ms, now
            return now
        ts = self._t0 + (ms - self._ms0) / 1000.0
        if abs(ts - now) > 30.0:                 # clock drift / long stall -> re-anchor
            self._ms0, self._t0 = ms, now
            return now
        return ts

    def _accept(self, raw: Dict[str, Any], line: Optional[str]) -> Optional[Dict[str, Any]]:
        cal = self.calibration(self.session_patient)
        ts = self._timestamp(raw)
        with self.lock:
            if not raw.get("crc_ok", True):
                self.bad_crc += 1
            self.packets += 1
            self.seq += 1
            self._rate.append(time.time())
            self.last_packet_at = time.time()
            self.status_bits = int(raw.get("status") or 0)
            if self.state in ("waiting", "stale", "disconnected", "error"):
                self.state = "connected"
                self.error = None
                if not self.transport:
                    self.transport = "wifi"
                self.connected_at = self.connected_at or ts

            self.pulse.add(ts, raw.get("pulse_raw"), cal["ppg"])
            self.gsr.add(ts, raw.get("gsr_raw"))
            self.temp.add(ts, raw.get("temp_raw_c"), cal["temp"])
            self.imu.add(ts, raw.get("ax"), raw.get("ay"), raw.get("az"), cal["imu"])

            imu_f = self.imu.features(cal["imu"])
            pulse_f = self.pulse.features(cal["ppg"], imu_f.get("motion_index") or 0.0)
            gsr_f = self.gsr.features(cal["gsr"])
            temp_f = self.temp.features(cal["temp"])
            derived = {**pulse_f, **gsr_f, **temp_f, **imu_f}
            sample = {"seq": self.seq, "t": ts, "raw": raw, "derived": derived,
                      "flags": raw.get("flags") or []}
            self.buffer.append(sample)
            if line and self.seq % 10 == 1:
                self._note(line if len(line) < 150 else line[:150] + "…")
            if self.session_id:
                self._pending.append(sample)
        self._maybe_flush()
        return sample

    def _note(self, text: str) -> None:
        self.log.appendleft(time.strftime("%H:%M:%S") + "  " + text)

    def rate_hz(self) -> float:
        if len(self._rate) < 2:
            return 0.0
        span = self._rate[-1] - self._rate[0]
        return round((len(self._rate) - 1) / span, 2) if span > 0.05 else 0.0

    # ------------------------------- sessions ----------------------------- #
    def start_session(self, patient_id: str, note: Optional[str] = None) -> Dict[str, Any]:
        if not patient_id:
            raise ValueError("A participant must be selected before recording.")
        if self.session_id:
            self.stop_session()
        sid = "SES-" + uuid.uuid4().hex[:10].upper()
        self.api.create_session(sid, patient_id, source="ESP32_WEARABLE",
                                label=LIVE_LABEL, notes=note or "Live wearable recording")
        with self.lock:
            self.session_id = sid
            self.session_patient = patient_id
            self.session_started = time.time()
            self.session_rows = 0
            self._pending = []
            self._note(f"recording started -> {sid} ({patient_id})")
        return self.status()

    def stop_session(self) -> Dict[str, Any]:
        self._flush(force=True)
        with self.lock:
            sid, rows = self.session_id, self.session_rows
            started = self.session_started
            self.session_id = None
            self.session_started = None
            self._note(f"recording stopped · {rows} rows written")
        if sid:
            self.api.close_session(sid, rows, quality=self._quality())
        return {"session_id": sid, "rows": rows,
                "duration_s": round(time.time() - started, 1) if started else 0, "status": self.status()}

    def _quality(self) -> float:
        vals = [s["derived"].get("quality") for s in list(self.buffer)[-300:]
                if s["derived"].get("quality") is not None]
        return round(sum(vals) / len(vals), 3) if vals else 0.0

    def _maybe_flush(self) -> None:
        if self.session_id and (time.time() - self._last_flush) >= FLUSH_EVERY_S:
            self._flush()

    def _flush(self, force: bool = False) -> None:
        with self.lock:
            if not self.session_id or (not self._pending and not force):
                return
            batch, self._pending = self._pending, []
            sid, pid = self.session_id, self.session_patient
            self._last_flush = time.time()
        if not batch:
            return
        rows = self.api.write_samples(sid, pid, batch, label=LIVE_LABEL)
        with self.lock:
            self.session_rows += rows

    # -------------------------------- status ------------------------------ #
    def status(self) -> Dict[str, Any]:
        with self.lock:
            now = time.time()
            state = self.state
            if state == "connected" and self.last_packet_at and now - self.last_packet_at > STALE_AFTER_S:
                state = self.state = "stale"
            last = list(self.buffer)[-1] if self.buffer else None
            return {
                "state": state,
                "connected": state == "connected",
                "transport": self.transport,
                "transportLabel": TRANSPORTS.get(self.transport or "", None),
                "endpoint": self.endpoint,
                "deviceName": self.device_name,
                "firmware": self.firmware,
                "error": self.error,
                "connectedAt": self.connected_at,
                "lastPacketAt": self.last_packet_at,
                "secondsSincePacket": round(now - self.last_packet_at, 2) if self.last_packet_at else None,
                "packets": self.packets,
                "badCrc": self.bad_crc,
                "badFrames": self.bad_frames,
                "rateHz": self.rate_hz(),
                "statusBits": status_report(self.status_bits),
                "flags": last["flags"] if last else [],
                "live": last["derived"] if last else None,
                "raw": last["raw"] if last else None,
                "session": {
                    "id": self.session_id, "patientId": self.session_patient,
                    "rows": self.session_rows, "startedAt": self.session_started,
                    "durationS": round(now - self.session_started, 1) if self.session_started else 0,
                    "recording": bool(self.session_id),
                },
                "buffered": len(self.buffer),
                "quality": self._quality(),
                "spo2Available": False,
                "log": list(self.log)[:40],
                "serverTime": now,
            }

    def stream(self, since: int = 0, limit: int = 300) -> Dict[str, Any]:
        with self.lock:
            items = [s for s in self.buffer if s["seq"] > since][-limit:]
            wave = self.pulse.waveform(180)
        return {
            "since": since, "seq": self.seq, "count": len(items),
            "samples": [{
                "seq": s["seq"], "t": s["t"],
                "pulse": s["raw"].get("pulse_raw"), "temp": s["derived"].get("skin_temp_c"),
                "gsr": s["derived"].get("gsr_us"), "hr": s["derived"].get("hr_bpm"),
                "hrv": s["derived"].get("rmssd_ms"), "motion": s["derived"].get("motion_index"),
                "quality": s["derived"].get("quality"),
            } for s in items],
            "waveform": wave,
            "status": self.status(),
        }
