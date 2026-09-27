"""Single-channel analog pulse-sensor processing.

Target: 10/20 Hz low-cost analog Pulse Sensor connected to ESP32 ADC.
The module deliberately does not estimate SpO2 because a single analog PPG
channel does not provide the red/IR pair required for conventional pulse
oximetry.
"""
from __future__ import annotations

from collections import deque
from typing import Deque, Tuple

import numpy as np

from src.config import MAX_HR_BPM, MIN_HR_BPM
from src.signal_processing.hrv import hrv_time_domain
from src.utils.math_utils import clamp


class AnalogPPGProcessor:
    def __init__(self, history_s: float = 180.0, fs_hz: float = 20.0):
        self.fs_hz = float(fs_hz)
        self.maxlen = int(history_s * self.fs_hz)
        self.times: Deque[float] = deque(maxlen=self.maxlen)
        self.raw: Deque[float] = deque(maxlen=self.maxlen)
        self.filtered: Deque[float] = deque(maxlen=self.maxlen)
        self.last_peaks: list[float] = []
        self.last_ibi_s: list[float] = []

    def add_sample(self, timestamp_s: float, value: float) -> None:
        x = float(value)
        self.times.append(float(timestamp_s))
        self.raw.append(x)
        n = len(self.raw)
        win = list(self.raw)[max(0, n - int(self.fs_hz * 12)):]
        arr = np.asarray(win, dtype=float)
        # Robust moving-median detrending followed by an exponential smoother.
        if arr.size >= 5:
            med = float(np.median(arr))
            baseline = float(np.median(
                np.asarray(list(self.raw)[max(0, n - int(self.fs_hz * 2)):], dtype=float)
            ))
            y = x - baseline + (0.15 * (x - med))
        else:
            y = x - float(np.mean(arr)) if arr.size else x
        if self.filtered:
            y = 0.35 * y + 0.65 * self.filtered[-1]
        self.filtered.append(float(y))

    def waveform(self, last_s: float = 20.0) -> Tuple[np.ndarray, np.ndarray]:
        if not self.times:
            return np.array([]), np.array([])
        t = np.asarray(self.times, dtype=float)
        y = np.asarray(self.filtered, dtype=float)
        mask = t >= t[-1] - last_s
        return t[mask] - t[-1], y[mask]

    def _bandpass(self, y: np.ndarray) -> np.ndarray:
        if y.size < 8:
            return y
        n = y.size
        spec = np.fft.rfft(y - np.mean(y))
        freqs = np.fft.rfftfreq(n, 1.0 / self.fs_hz)
        band = (freqs >= 0.65) & (freqs <= 3.5)
        out = np.zeros_like(spec)
        out[band] = spec[band]
        filtered = np.fft.irfft(out, n)
        return filtered.astype(float)

    def _peaks(self, window_s: float = 20.0) -> tuple[list[float], float, float]:
        if len(self.times) < int(self.fs_hz * 6):
            return [], 0.0, 0.0
        t = np.asarray(self.times, dtype=float)
        y = np.asarray(self.filtered, dtype=float)
        mask = t >= t[-1] - window_s
        t, y = t[mask], y[mask]
        if y.size < int(self.fs_hz * 6):
            return [], 0.0, 0.0

        y = self._bandpass(y)
        if np.std(y) < 1e-6:
            return [], 0.0, 0.0

        # Light Savitzky-free smoothing to stay NumPy-only.
        kernel = np.ones(3, dtype=float) / 3.0
        ys = np.convolve(y, kernel, mode="same")
        amp = float(np.percentile(ys, 95) - np.percentile(ys, 5))
        noise = float(np.median(np.abs(ys - np.median(ys)))) * 1.4826
        snr = float(amp / max(noise * 8.0, 1e-6))

        threshold = max(float(np.median(ys) + 0.35 * np.std(ys)), float(np.percentile(ys, 62)))
        min_distance = max(2, int(self.fs_hz * 60.0 / MAX_HR_BPM))
        peaks: list[int] = []
        for i in range(1, len(ys) - 1):
            if ys[i] >= ys[i - 1] and ys[i] > ys[i + 1] and ys[i] > threshold:
                if not peaks or i - peaks[-1] >= min_distance:
                    peaks.append(i)
                elif ys[i] > ys[peaks[-1]]:
                    peaks[-1] = i

        peak_times = [float(t[i]) for i in peaks]
        if len(peak_times) < 2:
            return peak_times, clamp(snr / 8.0, 0.0, 1.0), 0.0

        ibi = np.diff(peak_times)
        ibi = ibi[(ibi >= 60.0 / MAX_HR_BPM) & (ibi <= 60.0 / MIN_HR_BPM)]
        if ibi.size < 2:
            return peak_times, clamp(snr / 8.0, 0.0, 1.0), 0.0

        med = float(np.median(ibi))
        clean = ibi[np.abs(ibi - med) <= 0.25 * med]
        if clean.size < 2:
            clean = ibi

        regularity = float(np.mean(np.abs(clean - np.median(clean)) <= 0.12 * np.median(clean)))
        q = clamp(0.45 * min(1.0, snr / 8.0) + 0.55 * regularity, 0.0, 1.0)
        return peak_times, float(q), float(60.0 / np.median(clean))

    def features(self, motion_index: float = 0.0) -> dict[str, float | None]:
        peaks, pulse_quality, hr = self._peaks()
        self.last_peaks = peaks

        ibi = np.diff(peaks) if len(peaks) >= 3 else np.array([], dtype=float)
        ibi = ibi[(ibi >= 60.0 / MAX_HR_BPM) & (ibi <= 60.0 / MIN_HR_BPM)]
        if ibi.size >= 3:
            med = float(np.median(ibi))
            ibi = ibi[np.abs(ibi - med) <= 0.25 * med]
        self.last_ibi_s = ibi.tolist()

        # Motion is a reliability penalty, not a physiological value.
        motion_penalty = clamp(1.0 - float(motion_index) / 1.2, 0.0, 1.0)
        q = float(clamp(0.75 * pulse_quality + 0.25 * motion_penalty, 0.0, 1.0))

        if q < 0.45:
            hr = None

        hrv = (
            hrv_time_domain(self.last_ibi_s)
            if q >= 0.70 and len(self.last_ibi_s) >= 10
            else {"rmssd_ms": None, "sdnn_ms": None, "pnn50_pct": None}
        )
        if q < 0.70:
            hrv = {"rmssd_ms": None, "sdnn_ms": None, "pnn50_pct": None}

        raw = np.asarray(list(self.raw)[-int(self.fs_hz * 12):], dtype=float)
        amplitude = None
        if raw.size >= 10 and np.isfinite(raw).all():
            amplitude = float(np.percentile(raw, 95) - np.percentile(raw, 5))

        return {
            "hr_bpm": hr,
            "rmssd_ms": hrv.get("rmssd_ms"),
            "sdnn_ms": hrv.get("sdnn_ms"),
            "pnn50_pct": hrv.get("pnn50_pct"),
            "ppg_pulse_amplitude": amplitude,
            "ppg_quality": q,
        }
