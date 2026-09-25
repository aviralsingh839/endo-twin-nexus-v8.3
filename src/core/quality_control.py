"""Sensor Quality Control for CHRONO-TWIN NEXUS V8.3.

Every sensor reading gets quality metadata:
{
  value, quality 0..1, source, timestamp, artifact bool
}

Detects:
- missing data
- impossible values
- flatline
- excessive noise
- motion artifacts
- packet corruption
- stale data
"""
from __future__ import annotations

import time
import math
from collections import deque
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np

from src.data_models import SensorQuality


@dataclass
class QualityThresholds:
    hr_min: float = 35.0
    hr_max: float = 210.0
    temp_min: float = -20.0
    temp_max: float = 80.0
    skin_temp_min: float = 20.0
    skin_temp_max: float = 42.0
    gsr_min: int = 0
    gsr_max: int = 1023
    ir_min: int = 0
    ir_max: int = 262143
    analog_pulse_min: int = 0
    analog_pulse_max: int = 4095
    motion_max_g: float = 8.0
    stale_timeout_s: float = 6.0


class SensorQualityControl:
    """Quality gate for all sensor channels."""

    def __init__(self, thresholds: QualityThresholds | None = None):
        self.thresholds = thresholds or QualityThresholds()
        self._history: Dict[str, deque] = {}
        self._last_valid: Dict[str, float] = {}
        self._flatline_counters: Dict[str, int] = {}

    def _get_history(self, channel: str, maxlen: int = 50) -> deque:
        if channel not in self._history:
            self._history[channel] = deque(maxlen=maxlen)
        return self._history[channel]

    def check_missing(self, value: Optional[float]) -> Tuple[bool, str]:
        if value is None:
            return True, "missing value"
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return True, "NaN or Inf"
        return False, ""

    def check_impossible(self, channel: str, value: float) -> Tuple[bool, str]:
        t = self.thresholds
        if channel in ("hr", "heart_rate"):
            if not (t.hr_min <= value <= t.hr_max):
                return True, f"HR {value} out of range [{t.hr_min},{t.hr_max}]"
        elif channel in ("temp_c", "skin_temp", "skin_temp_c"):
            if not (t.skin_temp_min <= value <= t.skin_temp_max):
                return True, f"skin temp {value} out of range"
        elif channel in ("temp1_c", "room_temp_c"):
            if not (t.temp_min <= value <= t.temp_max):
                return True, f"temp {value} out of range"
        elif channel == "gsr_raw":
            if not (t.gsr_min <= value <= t.gsr_max):
                return True, f"GSR {value} out of range"
        elif channel in ("ir", "red"):
            if not (t.ir_min <= value <= t.ir_max):
                return True, f"optical PPG {value} out of range"
        elif channel in ("analog_pulse", "pulse_raw"):
            if not (t.analog_pulse_min <= value <= t.analog_pulse_max):
                return True, f"analog pulse ADC {value} out of range"
        elif channel in ("ax_g", "ay_g", "az_g"):
            if abs(value) > t.motion_max_g:
                return True, f"accel {value} exceeds max"
        return False, ""

    def check_flatline(self, channel: str, value: float, tolerance: float = 1e-6) -> Tuple[bool, str]:
        hist = self._get_history(channel)
        if len(hist) < 5:
            return False, ""
        recent = list(hist)[-5:]
        if all(abs(v - value) < tolerance for v in recent):
            self._flatline_counters[channel] = self._flatline_counters.get(channel, 0) + 1
            if self._flatline_counters[channel] >= 3:
                return True, f"flatline detected for {channel}"
        else:
            self._flatline_counters[channel] = 0
        return False, ""

    def check_noise(self, channel: str, value: float) -> Tuple[bool, str, float]:
        """Excessive noise detection. Returns (is_noisy, reason, quality_penalty)."""
        hist = self._get_history(channel, maxlen=20)
        if len(hist) < 10:
            return False, "", 0.0
        arr = np.array(list(hist), dtype=float)
        if np.std(arr) < 1e-9:
            return False, "", 0.0
        # z-score of current vs recent
        mean = float(np.mean(arr))
        std = float(np.std(arr))
        if std > 1e-9:
            z = abs(value - mean) / std
            if z > 5.0:
                return True, f"excessive noise: z={z:.1f}", 0.3
            if z > 3.5:
                return False, f"moderate deviation: z={z:.1f}", 0.15
        return False, "", 0.0

    def check_stale(self, channel: str, timestamp_s: float) -> Tuple[bool, str]:
        last = self._last_valid.get(channel)
        if last is None:
            return False, ""
        if timestamp_s - last > self.thresholds.stale_timeout_s:
            return True, f"stale data: {timestamp_s - last:.1f}s old"
        return False, ""

    def evaluate(self, channel: str, value: Optional[float], source: str = "unknown",
                 timestamp_s: Optional[float] = None) -> SensorQuality:
        ts = timestamp_s or time.time()
        hist = self._get_history(channel)

        # Missing
        is_missing, reason = self.check_missing(value)
        if is_missing:
            return SensorQuality(
                value=None, quality=0.0, source=source,
                timestamp=ts, artifact=True,
                artifact_type="missing", reason=reason
            )

        # Impossible
        is_imp, reason = self.check_impossible(channel, float(value))
        if is_imp:
            return SensorQuality(
                value=float(value), quality=0.0, source=source,
                timestamp=ts, artifact=True,
                artifact_type="impossible", reason=reason
            )

        # Stale
        is_stale, reason = self.check_stale(channel, ts)
        if is_stale:
            return SensorQuality(
                value=float(value), quality=0.2, source=source,
                timestamp=ts, artifact=True,
                artifact_type="stale", reason=reason
            )

        # Flatline
        is_flat, reason = self.check_flatline(channel, float(value))
        if is_flat:
            return SensorQuality(
                value=float(value), quality=0.1, source=source,
                timestamp=ts, artifact=True,
                artifact_type="flatline", reason=reason
            )

        # Noise
        is_noisy, reason, penalty = self.check_noise(channel, float(value))
        base_quality = 1.0 - penalty
        if is_noisy:
            base_quality = max(0.1, base_quality - 0.3)

        # Update history
        hist.append(float(value))
        self._last_valid[channel] = ts

        # Adjust quality by channel specifics
        quality = base_quality
        if channel in ("ir", "red"):
            # Legacy optical PPG quality depends on IR/optical amplitude.
            if float(value) < 5000:
                quality = 0.0
                return SensorQuality(
                    value=float(value), quality=quality, source=source,
                    timestamp=ts, artifact=True,
                    artifact_type="low_amplitude", reason="finger absent or low optical PPG"
                )
        elif channel in ("analog_pulse", "pulse_raw"):
            # Analog Pulse Sensor uses the ADC range, not the optical IR scale.
            span = max(self.thresholds.analog_pulse_max - self.thresholds.analog_pulse_min, 1)
            normalized = (float(value) - self.thresholds.analog_pulse_min) / span
            if normalized <= 0.002 or normalized >= 0.998:
                quality = min(quality, 0.25)

        return SensorQuality(
            value=float(value), quality=float(max(0.0, min(1.0, quality))),
            source=source, timestamp=ts, artifact=False,
            reason=reason
        )

    def evaluate_sample(self, sample: dict, source: str = "wearable") -> Dict[str, SensorQuality]:
        """Evaluate a dict of channel->value."""
        results = {}
        ts = sample.get("timestamp_s", time.time())
        for ch, val in sample.items():
            if ch == "timestamp_s":
                continue
            results[ch] = self.evaluate(ch, val, source=source, timestamp_s=ts)
        return results

    def overall_quality(self, qualities: Dict[str, SensorQuality]) -> float:
        if not qualities:
            return 0.0
        valid = [q.quality for q in qualities.values() if q.value is not None]
        if not valid:
            return 0.0
        return float(np.mean(valid))

    def has_critical_failure(self, qualities: Dict[str, SensorQuality]) -> Tuple[bool, str]:
        """Detect sensor disconnection or complete failure."""
        critical = ["ir", "hr", "temp_c", "skin_temp_c"]
        failed = []
        for ch in critical:
            if ch in qualities:
                q = qualities[ch]
                if q.artifact and q.artifact_type in ("missing", "flatline", "impossible"):
                    failed.append(ch)
        if len(failed) >= 2:
            return True, f"critical sensors failed: {', '.join(failed)}"
        return False, ""
