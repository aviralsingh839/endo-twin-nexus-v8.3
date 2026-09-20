"""Shared Physiological Feature Representation - V8.3.

Common feature layer that disease modules consume.
Avoids duplicating signal-processing code in every disease model.

Example:
shared_features = {
  heart_rate,
  resting_heart_rate,
  hrv,
  activity,
  sleep_duration,
  sleep_regularity,
  temperature_trend,
  gsr,
  circadian_features,
  recovery_features,
  baseline_deviation,
  trend_features,
  sensor_quality
}
"""
from __future__ import annotations

from typing import Dict, Optional
import time
import numpy as np

from src.data_models import FeatureVector, SharedPhysiologicalFeatures
from src.core.personal_baseline import PersonalBaselineEngine


class SharedFeatureExtractor:
    """Builds shared representation from FeatureVector + baseline."""

    def __init__(self, baseline_engine: Optional[PersonalBaselineEngine] = None):
        self.baseline_engine = baseline_engine

    def extract(self, fv: FeatureVector, history: Optional[list] = None) -> SharedPhysiologicalFeatures:
        shared = SharedPhysiologicalFeatures(
            timestamp_s=fv.timestamp_s or time.time(),
            heart_rate=fv.hr_bpm,
            resting_heart_rate=fv.resting_hr_bpm or fv.hr_bpm,
            hrv_rmssd=fv.rmssd_ms,
            hrv_sdnn=fv.sdnn_ms,
            activity_level=fv.activity_level,
            motion_index=fv.motion_index,
            low_activity_risk=fv.low_activity_risk,
            sleep_duration_h=fv.sleep_duration_h,
            sleep_regularity=fv.sleep_regularity,
            sleep_timing_h=fv.sleep_timing_h,
            sleep_probability=fv.sleep_probability,
            circadian_stability=fv.circadian_stability_index,
            circadian_disruption=fv.circadian_disruption,
            skin_temp_c=fv.skin_temp_c,
            temperature_trend_c_per_day=fv.temp_slope_c_per_min * 1440.0 if fv.temp_slope_c_per_min else 0.0,
            temperature_rhythm_disruption=fv.temperature_rhythm_disruption,
            gsr_tonic=fv.gsr_tonic,
            stress_index=fv.stress_index,
            autonomic_imbalance=fv.autonomic_imbalance,
            overall_quality=fv.signal_quality,
        )

        # Baseline deviations
        if self.baseline_engine and self.baseline_engine.has_baseline:
            for metric in ["hr_bpm", "rmssd_ms", "skin_temp_c", "gsr_tonic", "activity_level"]:
                z = self.baseline_engine.zscore(metric, getattr(fv, metric, None))
                if z is not None:
                    shared.baseline_deviations[metric] = float(z)

        # Trend features from history
        if history and len(history) >= 5:
            shared.trend_features = self._compute_trends(history)
            shared.day_night_activity_ratio = self._day_night_ratio(history)
            shared.recovery_score = self._recovery_score(history)

        # Sensor quality per feature
        shared.sensor_quality = fv.quality_per_feature or {}
        if not shared.sensor_quality:
            # Fallback from overall quality
            shared.sensor_quality = {
                "hr": fv.signal_quality,
                "hrv": fv.signal_quality,
                "temp": fv.signal_quality,
                "gsr": fv.signal_quality,
                "activity": fv.signal_quality,
            }

        # Provenance (default to measured where available)
        for k in ["heart_rate", "hrv_rmssd", "activity_level", "skin_temp_c"]:
            if getattr(shared, k) is not None:
                shared.provenance[k] = "MEASURED"
            else:
                shared.provenance[k] = "UNKNOWN"

        return shared

    def _compute_trends(self, history: list) -> Dict[str, float]:
        """Compute simple trends from history."""
        trends = {}
        if len(history) < 5:
            return trends

        # Use last 24h vs previous 24h if possible
        now = history[-1].timestamp_s if hasattr(history[-1], 'timestamp_s') else time.time()
        recent = [f for f in history if now - f.timestamp_s <= 24*3600]
        previous = [f for f in history if 24*3600 < now - f.timestamp_s <= 48*3600]

        for attr in ["hr_bpm", "rmssd_ms", "activity_level", "skin_temp_c"]:
            try:
                recent_vals = [getattr(f, attr) for f in recent if getattr(f, attr, None) is not None]
                prev_vals = [getattr(f, attr) for f in previous if getattr(f, attr, None) is not None]
                if recent_vals and prev_vals:
                    recent_mean = float(np.mean(recent_vals))
                    prev_mean = float(np.mean(prev_vals))
                    if abs(prev_mean) > 1e-9:
                        trends[f"{attr}_24h_change_pct"] = (recent_mean - prev_mean) / abs(prev_mean) * 100.0
            except Exception:
                continue
        return trends

    def _day_night_ratio(self, history: list) -> float:
        """Day/night activity pattern."""
        try:
            import datetime
            day_act = []
            night_act = []
            for f in history[-100:]:  # last 100 points
                if not hasattr(f, 'timestamp_s'):
                    continue
                dt = datetime.datetime.fromtimestamp(f.timestamp_s)
                hour = dt.hour
                act = getattr(f, 'activity_level', 0.0) or 0.0
                if 6 <= hour <= 21:
                    day_act.append(act)
                else:
                    night_act.append(act)
            if day_act and night_act:
                day_mean = float(np.mean(day_act))
                night_mean = float(np.mean(night_act))
                if night_mean > 1e-9:
                    return day_mean / night_mean
        except Exception:
            pass
        return 1.0

    def _recovery_score(self, history: list) -> float:
        """Recovery signal from HRV and resting HR trends."""
        try:
            if len(history) < 10:
                return 50.0
            recent_hrv = [getattr(f, 'rmssd_ms', None) for f in history[-10:] if getattr(f, 'rmssd_ms', None) is not None]
            recent_hr = [getattr(f, 'hr_bpm', None) for f in history[-10:] if getattr(f, 'hr_bpm', None) is not None]
            if not recent_hrv or not recent_hr:
                return 50.0
            # Higher HRV and lower HR -> better recovery
            hrv_score = min(100.0, max(0.0, (float(np.mean(recent_hrv)) - 20.0) / 40.0 * 100.0))
            hr_score = min(100.0, max(0.0, (90.0 - float(np.mean(recent_hr))) / 30.0 * 100.0))
            return 0.6 * hrv_score + 0.4 * hr_score
        except Exception:
            return 50.0
