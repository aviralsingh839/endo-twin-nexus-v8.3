"""PPG processing: filtering, peak detection, HR and quality-gated HRV.

Engineering note:
PPG-derived pulse-rate variability is not interchangeable with ECG-derived HRV.
This module therefore separates short-window HR from HRV outputs and withholds
HRV when there are not enough clean intervals or signal quality is inadequate.
"""
from __future__ import annotations

from collections import deque
from typing import Deque, Tuple

import numpy as np

from src.config import MAX_HR_BPM, MIN_HR_BPM, PPG_FS_HZ
from src.signal_processing.filters import DCBlocker, ExponentialSmoother
from src.signal_processing.hrv import hrv_time_domain
from src.signal_processing.spo2 import estimate_spo2
from src.utils.quality import ppg_quality


class PPGProcessor:
    def __init__(self, history_s: float = 180.0, fs_hz: float = PPG_FS_HZ):
        self.fs_hz = fs_hz
        self.maxlen = int(history_s * fs_hz)
        self.times: Deque[float] = deque(maxlen=self.maxlen)
        self.ir_raw: Deque[float] = deque(maxlen=self.maxlen)
        self.red_raw: Deque[float] = deque(maxlen=self.maxlen)
        self.ir_filt: Deque[float] = deque(maxlen=self.maxlen)
        self._dc = DCBlocker(r=0.97)
        self._smooth = ExponentialSmoother(alpha=0.35)
        self.last_peaks: list[float] = []
        self.last_ibi_s: list[float] = []

    def add_sample(self, timestamp_s: float, ir: int, red: int) -> None:
        if not self.times:
            self._dc.x_prev = float(ir)
            self._dc.y_prev = 0.0
        y = self._smooth.update(self._dc.update(float(ir)))
        self.times.append(float(timestamp_s))
        self.ir_raw.append(float(ir))
        self.red_raw.append(float(red))
        self.ir_filt.append(float(y))

    def waveform(self, last_s: float = 20.0) -> Tuple[np.ndarray, np.ndarray]:
        if not self.times:
            return np.array([]), np.array([])
        t = np.asarray(self.times, dtype=float)
        y = np.asarray(self.ir_filt, dtype=float)
        mask = t >= (t[-1] - last_s)
        return t[mask] - t[-1], y[mask]

    def _detect_peaks(self, window_s: float = 20.0) -> list[float]:
        if len(self.times) < max(5, int(5 * self.fs_hz)):
            return []
        t = np.asarray(self.times, dtype=float)
        y = np.asarray(self.ir_filt, dtype=float)
        mask = t >= (t[-1] - window_s)
        t = t[mask]
        y = y[mask]
        if y.size < max(25, int(3 * self.fs_hz)):
            return []

        warmup = int(2 * self.fs_hz)
        if y.size > warmup + 10:
            t = t[warmup:]
            y = y[warmup:]

        y = y - np.median(y)
        noise = float(np.std(y))
        if noise < 1e-6:
            return []

        threshold = max(0.45 * noise, float(np.percentile(y, 60)))
        candidate_idx = np.flatnonzero(
            (y[1:-1] > threshold)
            & (y[1:-1] >= y[:-2])
            & (y[1:-1] > y[2:])
        ) + 1
        if candidate_idx.size == 0:
            return []

        min_distance_s = 60.0 / MAX_HR_BPM
        peaks: list[float] = []
        for idx in candidate_idx.tolist():
            ti = float(t[idx])
            if not peaks or ti - peaks[-1] >= min_distance_s:
                peaks.append(ti)
            elif y[idx] > y[np.argmin(np.abs(t - peaks[-1]))]:
                peaks[-1] = ti
        return peaks

    def features(self, motion_index: float = 0.0) -> dict[str, float | None]:
        peaks = self._detect_peaks()
        self.last_peaks = peaks

        hr: float | None = None
        ibi = np.array([], dtype=float)
        if len(peaks) >= 3:
            ibi = np.diff(peaks)
            ibi = ibi[
                (ibi >= 60.0 / MAX_HR_BPM)
                & (ibi <= 60.0 / MIN_HR_BPM)
            ]
            if ibi.size:
                med = float(np.median(ibi))
                if med > 0:
                    ibi = ibi[np.abs(ibi - med) < 0.25 * med]
                    if ibi.size:
                        hr = float(60.0 / np.median(ibi))
            self.last_ibi_s = ibi.tolist()
        else:
            self.last_ibi_s = []

        n = int(12 * self.fs_hz)
        recent_ir = np.asarray(list(self.ir_raw)[-n:], dtype=float)
        recent_red = np.asarray(list(self.red_raw)[-n:], dtype=float)
        spo2, spo2_q = estimate_spo2(recent_red, recent_ir)

        if recent_ir.size >= 10:
            ppg_amp = float(
                (np.percentile(recent_ir, 95) - np.percentile(recent_ir, 5))
                / max(np.median(recent_ir), 1.0)
            )
        else:
            ppg_amp = None

        q = ppg_quality(
            recent_ir,
            recent_red,
            motion_index=motion_index,
            fs_hz=self.fs_hz,
        )
        q = float(0.7 * q + 0.3 * spo2_q)

        hrv = (
            hrv_time_domain(self.last_ibi_s)
            if len(self.last_ibi_s) >= 10
            else {
                "rmssd_ms": None,
                "sdnn_ms": None,
                "pnn50_pct": None,
                "mean_hr_bpm": None,
            }
        )

        # Engineering gates, not clinical thresholds.
        if q < 0.50:
            hr = None
        if q < 0.70 or len(self.last_ibi_s) < 10:
            hrv = {
                "rmssd_ms": None,
                "sdnn_ms": None,
                "pnn50_pct": None,
                "mean_hr_bpm": hrv.get("mean_hr_bpm") if q >= 0.50 else None,
            }
        if q < 0.70:
            spo2 = None

        return {
            "hr_bpm": hr,
            "spo2_pct": spo2,
            "rmssd_ms": hrv.get("rmssd_ms"),
            "sdnn_ms": hrv.get("sdnn_ms"),
            "pnn50_pct": hrv.get("pnn50_pct"),
            "ppg_pulse_amplitude": ppg_amp,
            "ppg_quality": q,
        }
