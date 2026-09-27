"""Automatic raw-sensor calibration for the ENDO-TWIN wearable.

This layer separates *raw acquisition* from *analysis-ready calibration*.
Calibration is intentionally conservative:
- IMU/gyro: startup zero-offset calibration while the pod is stationary.
- Analog PPG/GSR: robust baseline centering and scale estimation; raw values are
  retained and the normalized signal is used for analysis.
- BME280/BH1750: startup reference capture is recorded, but absolute values are
  not silently shifted because there is no physical reference standard.
- A slow adaptive baseline is used only for channels marked baseline-relative.

This is engineering calibration, not metrology or clinical calibration.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import time
from typing import Any

import numpy as np


CALIBRATION_CHANNELS = (
    "analog_ppg_raw", "gsr_raw",
    "ax_g", "ay_g", "az_g",
    "gx_dps", "gy_dps", "gz_dps",
    "room_temp_c", "humidity_pct", "pressure_hpa", "lux",
)


@dataclass
class ChannelCalibration:
    channel: str
    samples: int = 0
    center: float | None = None
    scale: float | None = None
    mad: float | None = None
    offset: float = 0.0
    mode: str = "reference"
    ready: bool = False
    confidence: float = 0.0
    updated_at: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "samples": self.samples,
            "center": self.center,
            "scale": self.scale,
            "mad": self.mad,
            "offset": self.offset,
            "mode": self.mode,
            "ready": self.ready,
            "confidence": round(float(self.confidence), 3),
            "updated_at": self.updated_at,
        }


class RawAutoCalibrator:
    """Streaming, robust calibration state for wearable channels."""

    def __init__(self, warmup_s: float = 8.0, min_samples: int = 80,
                 history_len: int = 500, adaptive_alpha: float = 0.002):
        self.warmup_s = float(warmup_s)
        self.min_samples = int(min_samples)
        self.history_len = int(history_len)
        self.adaptive_alpha = float(adaptive_alpha)
        self.started_at = time.time()
        self.channels: dict[str, ChannelCalibration] = {}
        self.history: dict[str, list[float]] = {}
        self._last_transform: dict[str, float] = {}
        self.reset()

    def reset(self) -> None:
        self.started_at = time.time()
        self.channels = {
            c: ChannelCalibration(c, mode=self._mode_for(c))
            for c in CALIBRATION_CHANNELS
        }
        self.history = {c: [] for c in CALIBRATION_CHANNELS}
        self._last_transform = {}

    @staticmethod
    def _mode_for(channel: str) -> str:
        if channel in {"ax_g", "ay_g", "az_g", "gx_dps", "gy_dps", "gz_dps"}:
            return "offset"
        if channel in {"analog_ppg_raw", "gsr_raw"}:
            return "baseline_relative"
        return "reference"

    @staticmethod
    def _finite(value: Any) -> bool:
        try:
            return value is not None and math.isfinite(float(value))
        except (TypeError, ValueError):
            return False

    def _append(self, channel: str, value: Any) -> None:
        if channel not in self.history or not self._finite(value):
            return
        arr = self.history[channel]
        arr.append(float(value))
        if len(arr) > self.history_len:
            del arr[:-self.history_len]

    @staticmethod
    def _robust_stats(values: list[float]) -> tuple[float, float, float]:
        x = np.asarray(values, dtype=float)
        center = float(np.median(x))
        mad = float(np.median(np.abs(x - center)))
        robust_sigma = max(1.4826 * mad, float(np.std(x)) * 0.25, 1e-6)
        q01, q99 = np.percentile(x, [1, 99])
        scale = max(float(q99 - q01) / 4.0, robust_sigma, 1e-6)
        return center, scale, mad

    def _is_stationary(self) -> bool:
        # Require enough IMU data and low dynamic acceleration/rotation.
        a = [self.history[k][-40:] for k in ("ax_g", "ay_g", "az_g")]
        g = [self.history[k][-40:] for k in ("gx_dps", "gy_dps", "gz_dps")]
        if any(len(v) < 20 for v in a + g):
            return False
        # update() evaluates each channel immediately after append(), so
        # the three axes can differ by one sample. Align to the common tail.
        n = min(len(v) for v in a + g)
        if n < 20:
            return False
        av = np.asarray([v[-n:] for v in a], dtype=float)
        gv = np.asarray([v[-n:] for v in g], dtype=float)
        acc_mag = np.sqrt(np.sum(av * av, axis=0))
        gyro_mag = np.sqrt(np.sum(gv * gv, axis=0))
        return (
            float(np.std(acc_mag)) < 0.035
            and float(np.mean(np.abs(acc_mag - np.median(acc_mag)))) < 0.035
            and float(np.median(gyro_mag)) < 7.0
            and float(np.std(gyro_mag)) < 5.0
        )

    def _update_channel(self, channel: str) -> None:
        vals = self.history[channel]
        state = self.channels[channel]
        state.samples = len(vals)
        state.updated_at = time.time()
        if len(vals) < self.min_samples:
            state.ready = False
            state.confidence = min(0.49, len(vals) / max(self.min_samples, 1) * 0.49)
            return

        # IMU offsets are captured only while the pod is still.
        if state.mode == "offset" and not self._is_stationary():
            state.ready = False
            state.confidence = 0.45
            return

        center, scale, mad = self._robust_stats(vals)
        state.center = center
        state.scale = scale
        state.mad = mad

        if channel == "az_g":
            # Preserve the gravity vector: zero the measured resting error around
            # the observed +/-1g orientation rather than forcing az to zero.
            sign = 1.0 if center >= 0 else -1.0
            state.offset = center - sign
        else:
            state.offset = center

        state.ready = True
        stability = 1.0 / (1.0 + (mad / max(scale, 1e-6)))
        state.confidence = float(min(1.0, 0.70 + 0.30 * stability))

    def update(self, sample: Any) -> None:
        for channel in CALIBRATION_CHANNELS:
            value = getattr(sample, channel, None)
            if self._finite(value):
                self._append(channel, value)
                self._update_channel(channel)

    def _adaptive_center(self, channel: str, value: float) -> float:
        state = self.channels[channel]
        center = state.center
        if center is None or not state.ready:
            return float(value)
        # Baseline-relative channels may adapt slowly, but only after the startup
        # calibration is ready. Large transient changes must not become baseline.
        recent = self.history[channel][-30:]
        if len(recent) >= 15:
            recent_center = float(np.median(recent))
            scale = max(float(state.scale or 1.0), 1e-6)
            if abs(recent_center - center) <= 3.0 * scale:
                center = (1.0 - self.adaptive_alpha) * center + self.adaptive_alpha * recent_center
                state.center = center
        return float(center)

    def transform_value(self, channel: str, value: Any) -> float | None:
        if not self._finite(value):
            return None
        x = float(value)
        state = self.channels.get(channel)
        if state is None or not state.ready:
            return x

        if state.mode == "offset":
            if channel == "az_g":
                sign = 1.0 if float(state.center or 0.0) >= 0 else -1.0
                return x - float(state.offset)  # preserves signed ~1g at rest
            return x - float(state.offset)

        if state.mode == "baseline_relative":
            center = self._adaptive_center(channel, x)
            scale = max(float(state.scale or 1.0), 1e-6)
            return (x - center) / scale

        # Reference channels retain physical units. The calibration metadata is
        # still available to UI/reports without corrupting absolute measurements.
        return x

    def transform_sample(self, sample: Any) -> dict[str, float | None]:
        return {
            c: self.transform_value(c, getattr(sample, c, None))
            for c in CALIBRATION_CHANNELS
        }

    @property
    def ready_fraction(self) -> float:
        if not self.channels:
            return 0.0
        # Mandatory analytic channels drive overall readiness.
        required = ("analog_ppg_raw", "gsr_raw", "ax_g", "ay_g", "az_g", "gx_dps", "gy_dps", "gz_dps")
        vals = [self.channels[c].ready for c in required]
        return float(sum(vals) / len(vals))

    @property
    def is_ready(self) -> bool:
        return self.ready_fraction >= 0.75 and (time.time() - self.started_at) >= self.warmup_s

    @property
    def status(self) -> str:
        if self.is_ready:
            return "READY"
        if time.time() - self.started_at < self.warmup_s:
            return "WARMING_UP"
        return "PARTIAL"

    def snapshot(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "ready_fraction": round(self.ready_fraction, 3),
            "elapsed_s": round(time.time() - self.started_at, 1),
            "channels": {k: v.as_dict() for k, v in self.channels.items()},
        }
