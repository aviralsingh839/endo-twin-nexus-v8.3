"""Dependency-free DSP for the ENDO-TWIN wearable stream.

Pure-Python ports of the algorithms used by the PySide6 platform
(`src/signal_processing/*`) so the web workstation can derive heart rate, HRV,
electrodermal activity, skin temperature and motion from the raw ESP32-S3
packets without numpy/scipy.

Nothing here invents a measurement: when a window does not contain enough
usable samples every derived value is returned as ``None``.
"""
from __future__ import annotations

import math
import statistics
import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional, Tuple

MIN_HR_BPM = 35.0
MAX_HR_BPM = 200.0

# --------------------------------------------------------------------------- #
#  packet parsing  ($CP / $CP2 as emitted by hardware/esp32/endo_twin_wearable)
# --------------------------------------------------------------------------- #
ST_PPG_ABSENT = 0
ST_PPG_SAT = 1
ST_MPU_ERR = 2
ST_TEMP_ERR = 3
ST_GSR_SAT = 4
ST_I2C_ERR = 5
ST_PPG_ANALOG = 12
ST_PPG_INVALID = 13

STATUS_FLAGS = [
    (ST_PPG_ABSENT, "PPG_ABSENT", "No finger / no pulse signal"),
    (ST_PPG_SAT, "PPG_SATURATED", "Pulse sensor saturated"),
    (ST_MPU_ERR, "IMU_ERROR", "MPU6050 not responding"),
    (ST_TEMP_ERR, "TEMP_ERROR", "DS18B20 out of range"),
    (ST_GSR_SAT, "GSR_RAIL", "GSR electrode open or shorted"),
    (ST_I2C_ERR, "I2C_ERROR", "I2C bus error"),
    (ST_PPG_ANALOG, "PPG_ANALOG", "Analog pulse sensor (no SpO2 possible)"),
    (ST_PPG_INVALID, "PPG_INVALID", "Pulse sample out of ADC range"),
]


class PacketError(ValueError):
    pass


def xor_crc(text: str) -> int:
    c = 0
    for ch in text:
        c ^= ord(ch)
    return c & 0xFF


def _f(tok: str) -> Optional[float]:
    tok = (tok or "").strip()
    if not tok or tok.lower() in ("nan", "-1", "none", "null"):
        return None
    try:
        v = float(tok)
    except ValueError:
        return None
    return None if math.isnan(v) or math.isinf(v) else v


def parse_packet(line: str, require_crc: bool = False) -> Dict[str, Any]:
    """Parse one ``$CP``/``$CP2`` ASCII frame into a raw sample dict."""
    raw = (line or "").strip()
    if not raw:
        raise PacketError("empty line")
    if not (raw.startswith("$CP2,") or raw.startswith("$CP,")):
        raise PacketError("unknown frame: %s" % raw[:10])
    parts = raw.split(",")
    payload = ",".join(parts[:-1])
    crc_ok = None
    try:
        crc_ok = int(parts[-1], 16) == xor_crc(payload)
    except (ValueError, IndexError):
        crc_ok = False
    if require_crc and not crc_ok:
        raise PacketError("CRC mismatch")

    cp2 = raw.startswith("$CP2,")
    if cp2 and len(parts) < 25:
        raise PacketError("$CP2 expects 25 fields, got %d" % len(parts))
    if not cp2 and len(parts) < 15:
        raise PacketError("$CP expects 15 fields, got %d" % len(parts))

    if cp2:
        status = int(_f(parts[23]) or 0)
        sample = {
            "ms": _f(parts[1]), "pulse_raw": _f(parts[2]), "red": _f(parts[3]),
            "ax": _f(parts[4]), "ay": _f(parts[5]), "az": _f(parts[6]),
            "gx": _f(parts[7]), "gy": _f(parts[8]), "gz": _f(parts[9]),
            "temp_raw_c": _f(parts[10]), "temp1_c": _f(parts[11]),
            "gsr_raw": _f(parts[12]), "ecg": _f(parts[16]), "lux": _f(parts[18]),
            "room_temp_c": _f(parts[19]), "humidity": _f(parts[20]),
            "status": status,
        }
    else:
        status = int(_f(parts[13]) or 0)
        sample = {
            "ms": _f(parts[1]), "pulse_raw": _f(parts[2]), "red": _f(parts[3]),
            "ax": _f(parts[4]), "ay": _f(parts[5]), "az": _f(parts[6]),
            "gx": _f(parts[7]), "gy": _f(parts[8]), "gz": _f(parts[9]),
            "temp_raw_c": _f(parts[10]), "gsr_raw": _f(parts[11]),
            "lux": _f(parts[12]), "status": status,
        }
    sample["crc_ok"] = bool(crc_ok)
    sample["analog_ppg"] = bool(status & (1 << ST_PPG_ANALOG)) or sample.get("red") in (None, -1)
    sample["flags"] = [name for bit, name, _ in STATUS_FLAGS if status & (1 << bit)]
    sample["t"] = time.time()
    return sample


def status_report(status: int) -> List[Dict[str, Any]]:
    return [{"bit": b, "flag": n, "text": t, "set": bool(status & (1 << b))} for b, n, t in STATUS_FLAGS]


# --------------------------------------------------------------------------- #
#  calibration
# --------------------------------------------------------------------------- #
DEFAULT_CALIBRATION: Dict[str, Dict[str, Any]] = {
    "ppg": {
        "adc_bits": 12,
        "baseline_raw": 2048.0,      # DC offset of the analog pulse module
        "gain": 1.0,                 # waveform scale factor
        "invert": False,             # some modules output an inverted pulse
        "peak_threshold_k": 0.45,    # adaptive threshold = median + k * sigma
        "min_amplitude": 25.0,       # below this the window is 'no contact'
        "hr_offset_bpm": 0.0,        # reference-device correction
        "sample_rate_hz": 20.0,
        "notes": "Analog Pulse Sensor on ADC pin. No red channel -> SpO2 unavailable.",
    },
    "temp": {
        "offset_c": 0.0,             # single-point correction
        "slope": 1.0,                # two-point correction
        "ref_low_c": None, "meas_low_c": None,
        "ref_high_c": None, "meas_high_c": None,
        "skin_to_core_delta_c": 0.0,
        "smoothing_s": 20.0,
        "notes": "DS18B20 on OneWire. Calibrate against a clinical thermometer.",
    },
    "gsr": {
        "adc_bits": 12,
        "vref": 3.3,
        "series_resistor_ohm": 10000.0,
        "dry_baseline_raw": 450.0,   # captured on dry skin / electrodes off
        "gain_us": 1.0,              # scale on the derived microsiemens
        "offset_us": 0.0,
        "phasic_mad_k": 4.0,
        "notes": "Grove-style GSR. Capture the dry baseline before each session.",
    },
    "imu": {
        "ax_offset": 0.0, "ay_offset": 0.0, "az_offset": 0.0,
        "step_threshold_g": 0.18,
        "still_threshold_g": 0.04,
        "notes": "MPU6050. Place the device flat and still to zero the axes.",
    },
    "spo2": {
        "available": False,
        "reason": "The analog pulse sensor has a single channel; SpO2 needs red+IR.",
        "reference_pct": None,       # optional manual entry from a pulse oximeter
    },
}


def merge_calibration(stored: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    out = {k: dict(v) for k, v in DEFAULT_CALIBRATION.items()}
    for sensor, params in (stored or {}).items():
        if sensor in out and isinstance(params, dict):
            out[sensor].update({k: v for k, v in params.items() if k != "notes" or v})
        elif isinstance(params, dict):
            out[sensor] = dict(params)
    return out


# --------------------------------------------------------------------------- #
#  processors
# --------------------------------------------------------------------------- #
def _median(xs: List[float]) -> float:
    return statistics.median(xs) if xs else 0.0


def _pct(xs: List[float], p: float) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    k = (len(s) - 1) * (p / 100.0)
    lo, hi = math.floor(k), math.ceil(k)
    return s[int(k)] if lo == hi else s[lo] + (s[hi] - s[lo]) * (k - lo)


class PulseProcessor:
    """Analog-pulse waveform -> HR, IBI, HRV, contact quality."""

    def __init__(self, history_s: float = 180.0):
        self.history_s = history_s
        self.t: Deque[float] = deque(maxlen=6000)
        self.y: Deque[float] = deque(maxlen=6000)
        self.raw: Deque[float] = deque(maxlen=6000)
        self.ibi_s: Deque[float] = deque(maxlen=400)
        self.peaks: List[float] = []

    def add(self, ts: float, raw: Optional[float], cal: Dict[str, Any]) -> None:
        if raw is None:
            return
        base = float(cal.get("baseline_raw") or 0.0)
        gain = float(cal.get("gain") or 1.0)
        v = (raw - base) * gain
        if cal.get("invert"):
            v = -v
        self.t.append(ts)
        self.y.append(v)
        self.raw.append(raw)
        self._trim()

    def _trim(self) -> None:
        if not self.t:
            return
        cutoff = self.t[-1] - self.history_s
        while self.t and self.t[0] < cutoff:
            self.t.popleft(); self.y.popleft(); self.raw.popleft()

    def amplitude(self, window_s: float = 12.0) -> Optional[float]:
        w = [v for ts, v in zip(self.t, self.y) if ts >= self.t[-1] - window_s] if self.t else []
        if len(w) < 10:
            return None
        return _pct(w, 95) - _pct(w, 5)

    def detect(self, cal: Dict[str, Any], window_s: float = 20.0) -> List[float]:
        if len(self.t) < 40:
            return []
        t0 = self.t[-1] - window_s
        ts = [a for a in self.t if a >= t0]
        ys = [b for a, b in zip(self.t, self.y) if a >= t0]
        if len(ys) < 20:
            return []
        med = _median(ys)
        ys = [v - med for v in ys]
        try:
            sigma = statistics.pstdev(ys)
        except statistics.StatisticsError:
            return []
        if sigma < 1e-6:
            return []
        k = float(cal.get("peak_threshold_k") or 0.45)
        thr = max(_median(ys) + k * sigma, _pct(ys, 60))
        refractory = 60.0 / MAX_HR_BPM
        peaks: List[float] = []
        last = -1e9
        for i in range(1, len(ys) - 1):
            if ys[i] > thr and ys[i] >= ys[i - 1] and ys[i] > ys[i + 1]:
                if ts[i] - last >= refractory:
                    peaks.append(ts[i]); last = ts[i]
        self.peaks = peaks
        return peaks

    def features(self, cal: Dict[str, Any], motion_index: float = 0.0) -> Dict[str, Optional[float]]:
        amp = self.amplitude()
        min_amp = float(cal.get("min_amplitude") or 0.0)
        contact = amp is not None and amp >= min_amp
        peaks = self.detect(cal) if contact else []
        ibis = []
        for a, b in zip(peaks, peaks[1:]):
            d = b - a
            if 60.0 / MAX_HR_BPM <= d <= 60.0 / MIN_HR_BPM:
                ibis.append(d)
        if len(ibis) >= 3:
            med = _median(ibis)
            ibis = [d for d in ibis if abs(d - med) < 0.25 * med]
        for d in ibis:
            if not self.ibi_s or abs(self.ibi_s[-1] - d) > 1e-9:
                self.ibi_s.append(d)

        hr = rmssd = sdnn = pnn50 = None
        if len(ibis) >= 3:
            hr = 60.0 / (sum(ibis) / len(ibis)) + float(cal.get("hr_offset_bpm") or 0.0)
            diffs = [(b - a) * 1000.0 for a, b in zip(ibis, ibis[1:])]
            if diffs:
                rmssd = math.sqrt(sum(d * d for d in diffs) / len(diffs))
                pnn50 = 100.0 * sum(1 for d in diffs if abs(d) > 50.0) / len(diffs)
            if len(ibis) >= 4:
                sdnn = statistics.pstdev([d * 1000.0 for d in ibis])

        quality = 0.0
        if contact and amp:
            span = max(_median([abs(v) for v in self.y]) or 1.0, 1.0)
            perfusion = min(amp / (span * 6.0), 1.0)
            quality = max(0.0, min(1.0, 0.45 * perfusion + 0.35 * (1.0 if hr else 0.0)
                                   + 0.20 * max(0.0, 1.0 - motion_index)))
        return {
            "hr_bpm": hr, "rmssd_ms": rmssd, "sdnn_ms": sdnn, "pnn50_pct": pnn50,
            "ibi_count": len(ibis), "amplitude": amp, "contact": contact,
            "quality": quality, "spo2_pct": None,
        }

    def waveform(self, n: int = 180) -> List[float]:
        return [round(v, 2) for v in list(self.y)[-n:]]


class GSRProcessor:
    def __init__(self) -> None:
        self.t: Deque[float] = deque(maxlen=3000)
        self.raw: Deque[float] = deque(maxlen=3000)

    def add(self, ts: float, raw: Optional[float]) -> None:
        if raw is None:
            return
        self.t.append(ts); self.raw.append(float(raw))

    def to_microsiemens(self, raw: float, cal: Dict[str, Any]) -> Optional[float]:
        """Voltage divider -> skin conductance. Returns None for rail readings."""
        bits = int(cal.get("adc_bits") or 12)
        full = float((1 << bits) - 1)
        if raw <= 1 or raw >= full - 1:
            return None
        vref = float(cal.get("vref") or 3.3)
        rs = float(cal.get("series_resistor_ohm") or 10000.0)
        v = (raw / full) * vref
        if v <= 0 or v >= vref:
            return None
        r_skin = rs * (vref - v) / v
        us = 1e6 / max(r_skin, 1.0)
        return us * float(cal.get("gain_us") or 1.0) + float(cal.get("offset_us") or 0.0)

    def features(self, cal: Dict[str, Any], window_s: float = 60.0) -> Dict[str, Optional[float]]:
        if len(self.raw) < 5:
            return {"gsr_us": None, "gsr_tonic": None, "gsr_phasic_per_min": None, "gsr_raw": None}
        t0 = self.t[-1] - window_s
        xs = [r for ts, r in zip(self.t, self.raw) if ts >= t0]
        if len(xs) < 5:
            xs = list(self.raw)[-5:]
        us = [u for u in (self.to_microsiemens(r, cal) for r in xs) if u is not None]
        if not us:
            return {"gsr_us": None, "gsr_tonic": None, "gsr_phasic_per_min": None, "gsr_raw": xs[-1]}
        tonic = _median(us)
        diffs = [b - a for a, b in zip(us, us[1:])] or [0.0]
        med_d = _median(diffs)
        mad = _median([abs(d - med_d) for d in diffs]) + 1e-6
        k = float(cal.get("phasic_mad_k") or 4.0)
        events = sum(1 for d in diffs if d > med_d + k * mad)
        minutes = max((self.t[-1] - max(self.t[0], t0)) / 60.0, 1e-3)
        base = float(cal.get("dry_baseline_raw") or 0.0)
        return {
            "gsr_us": round(us[-1], 4), "gsr_tonic": round(tonic, 4),
            "gsr_phasic_per_min": round(min(events / minutes, 60.0), 2),
            "gsr_raw": xs[-1], "gsr_above_baseline": round(xs[-1] - base, 1) if base else None,
        }


class TempProcessor:
    def __init__(self) -> None:
        self.t: Deque[float] = deque(maxlen=3000)
        self.c: Deque[float] = deque(maxlen=3000)

    def apply(self, raw_c: Optional[float], cal: Dict[str, Any]) -> Optional[float]:
        if raw_c is None or not (-20.0 < raw_c < 80.0):
            return None
        return raw_c * float(cal.get("slope") or 1.0) + float(cal.get("offset_c") or 0.0)

    def add(self, ts: float, raw_c: Optional[float], cal: Dict[str, Any]) -> None:
        v = self.apply(raw_c, cal)
        if v is None:
            return
        self.t.append(ts); self.c.append(v)

    def features(self, cal: Dict[str, Any], window_s: float = 300.0) -> Dict[str, Optional[float]]:
        if not self.c:
            return {"skin_temp_c": None, "temp_slope_c_per_min": None, "core_estimate_c": None}
        smooth = float(cal.get("smoothing_s") or 0.0)
        recent = [v for ts, v in zip(self.t, self.c) if ts >= self.t[-1] - max(smooth, 1.0)]
        cur = _median(recent) if recent else self.c[-1]
        slope = None
        win = [(ts, v) for ts, v in zip(self.t, self.c) if ts >= self.t[-1] - window_s]
        if len(win) >= 10:
            dt = (win[-1][0] - win[0][0]) / 60.0
            if dt > 0.2:
                slope = (win[-1][1] - win[0][1]) / dt
        delta = float(cal.get("skin_to_core_delta_c") or 0.0)
        return {
            "skin_temp_c": round(cur, 2),
            "temp_slope_c_per_min": round(slope, 4) if slope is not None else None,
            "core_estimate_c": round(cur + delta, 2) if delta else None,
        }


class IMUProcessor:
    def __init__(self) -> None:
        self.t: Deque[float] = deque(maxlen=3000)
        self.mag: Deque[float] = deque(maxlen=3000)
        self.steps = 0
        self._armed = True

    def add(self, ts: float, ax: Optional[float], ay: Optional[float], az: Optional[float],
            cal: Dict[str, Any]) -> None:
        if ax is None or ay is None or az is None:
            return
        ax -= float(cal.get("ax_offset") or 0.0)
        ay -= float(cal.get("ay_offset") or 0.0)
        az -= float(cal.get("az_offset") or 0.0)
        m = math.sqrt(ax * ax + ay * ay + az * az)
        self.t.append(ts); self.mag.append(m)
        dev = abs(m - 1.0)
        thr = float(cal.get("step_threshold_g") or 0.18)
        if self._armed and dev > thr:
            self.steps += 1
            self._armed = False
        elif dev < thr * 0.4:
            self._armed = True

    def features(self, cal: Dict[str, Any], window_s: float = 60.0) -> Dict[str, Optional[float]]:
        if len(self.mag) < 5:
            return {"motion_index": None, "steps": self.steps, "activity": None, "still": None}
        t0 = self.t[-1] - window_s
        xs = [m for ts, m in zip(self.t, self.mag) if ts >= t0] or list(self.mag)
        dev = [abs(m - 1.0) for m in xs]
        mi = min(sum(dev) / len(dev) / 0.5, 1.0)
        still_thr = float(cal.get("still_threshold_g") or 0.04)
        act = "Still" if mi * 0.5 < still_thr else "Light" if mi < 0.25 else "Moderate" if mi < 0.55 else "Vigorous"
        return {"motion_index": round(mi, 3), "steps": self.steps, "activity": act,
                "still": bool(mi * 0.5 < still_thr)}
