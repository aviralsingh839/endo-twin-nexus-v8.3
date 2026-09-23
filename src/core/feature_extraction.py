"""Feature Extraction - V8.3.

RAW DATA -> Sensor Quality Control -> Signal Processing -> Physiological Feature Extraction -> Personal Baseline

Produces FeatureVector and SharedPhysiologicalFeatures.
"""
from __future__ import annotations

import time
from collections import deque
from typing import Deque, Optional

import numpy as np

from src.config import BASELINE_CAPTURE_S, BASELINE_MIN_DURATION_S, BASELINE_MIN_SAMPLES, DEFAULT_PROFILE, UserProfile
from src.data_models import FeatureVector, SensorSample
from src.core.quality_control import SensorQualityControl
from src.core.personal_baseline import PersonalBaselineEngine
from src.core.adaptive_learning import AdaptiveWearableModel
from src.core.shared_features import SharedFeatureExtractor
from src.signal_processing.ppg import PPGProcessor
from src.signal_processing.imu import IMUProcessor
from src.signal_processing.temperature import TemperatureProcessor
from src.signal_processing.ecg import ECGProcessor
from src.utils.quality import completeness_score


class RealtimeFeatureExtractor:
    """Streaming feature extractor with quality control."""

    def __init__(self, profile: UserProfile | None = None, baseline_engine: Optional[PersonalBaselineEngine] = None,
                 learner: Optional[AdaptiveWearableModel] = None):
        self.profile = profile or DEFAULT_PROFILE
        self.baseline_engine = baseline_engine or PersonalBaselineEngine()
        # Continual self-learning layer. When present it keeps updating for as long as
        # the device is worn, and its norms take precedence over the frozen snapshot.
        self.learner = learner
        self.learning_events: list = []
        self.quality_control = SensorQualityControl()
        self.shared_extractor = SharedFeatureExtractor(baseline_engine=self.baseline_engine)

        # Signal processors
        self.ppg = PPGProcessor()
        self.imu = IMUProcessor()
        self.temp = TemperatureProcessor(history_s=24 * 3600)
        self.ecg = ECGProcessor()

        self.last_feature = FeatureVector(timestamp_s=time.time())
        self.last_lux: float | None = None
        self.last_sample: SensorSample | None = None
        self.feature_history: Deque[FeatureVector] = deque(maxlen=24 * 3600)
        self.start_time = time.time()
        self.sleep_onset_h: float | None = None
        self.wake_h: float | None = None
        self.auto_captured: bool = False
        self.last_capture_error: str | None = None
        self.circadian_metrics = None

        # For sleep and stress estimators - use simple versions
        self._quality_history: Deque[dict] = deque(maxlen=100)

    def set_profile(self, profile: UserProfile) -> None:
        self.profile = profile

    def set_sleep_window(self, onset_h: float | None, wake_h: float | None) -> None:
        self.sleep_onset_h = onset_h
        self.wake_h = wake_h

    def capture_baseline(self, window_s: float = BASELINE_CAPTURE_S) -> bool:
        now = time.time()
        rows = [f for f in self.feature_history if now - f.timestamp_s <= window_s]
        try:
            bl = self.baseline_engine.capture_from_features(rows, min_samples=BASELINE_MIN_SAMPLES, min_duration_s=BASELINE_MIN_DURATION_S)
            self.auto_captured = False
            self.last_capture_error = None
            return True
        except ValueError as exc:
            self.last_capture_error = str(exc)
            return False

    def add_sample(self, sample: SensorSample) -> None:
        self.last_sample = sample
        # Quality check per channel
        qualities = self.quality_control.evaluate_sample({
            "ir": sample.ir,
            "red": sample.red,
            "ax_g": sample.ax_g,
            "ay_g": sample.ay_g,
            "az_g": sample.az_g,
            "temp_c": sample.temp_c,
            "ecg_raw": sample.ecg_raw,
        }, source=sample.source)
        self._quality_history.append({k: v.quality for k, v in qualities.items()})

        self.ppg.add_sample(sample.timestamp_s, sample.ir, sample.red)
        self.imu.add_sample(sample.timestamp_s, sample.ax_g, sample.ay_g, sample.az_g,
                            sample.gx_dps, sample.gy_dps, sample.gz_dps)
        self.temp.add_sample(sample.timestamp_s, sample.temp_c)
        self.ecg.add_sample(sample.timestamp_s, sample.ecg_raw)
        self.last_lux = sample.lux if sample.lux is not None and sample.lux >= 0 else self.last_lux

    def compute(self) -> FeatureVector:
        now = time.time()
        imu_f = self.imu.features()
        ppg_f = self.ppg.features(motion_index=imu_f["motion_index"])
        temp_f = self.temp.features()
        ecg_f = self.ecg.features()

        hr_best = ecg_f.get("ecg_hr_bpm") if (ecg_f.get("ecg_quality") or 0) > 0.55 else ppg_f.get("hr_bpm")
        rmssd_best = ecg_f.get("ecg_rmssd_ms") if (ecg_f.get("ecg_quality") or 0) > 0.55 else ppg_f.get("rmssd_ms")

        # Resting HR: low activity + stable
        resting_hr = None
        if hr_best and imu_f["activity_level"] < 15:
            resting_hr = hr_best

        fv = FeatureVector(
            timestamp_s=now,
            hr_bpm=hr_best,
            resting_hr_bpm=resting_hr,
            spo2_pct=ppg_f.get("spo2_pct"),
            rmssd_ms=rmssd_best,
            sdnn_ms=ppg_f.get("sdnn_ms"),
            pnn50_pct=ppg_f.get("pnn50_pct"),
            ppg_pulse_amplitude=ppg_f.get("ppg_pulse_amplitude"),
            lux=self.last_lux,
            fsr_raw=self.last_sample.fsr_raw if self.last_sample else None,
            ecg_raw=self.last_sample.ecg_raw if self.last_sample else None,
            ecg_hr_bpm=ecg_f.get("ecg_hr_bpm"),
            ecg_rmssd_ms=ecg_f.get("ecg_rmssd_ms"),
            ecg_quality=ecg_f.get("ecg_quality") or 0.0,
            mic_rms=self.last_sample.mic_rms if self.last_sample else None,
            mic_pitch_hz=self.last_sample.mic_pitch_hz if self.last_sample else None,
            room_temp_c=self.last_sample.room_temp_c if self.last_sample else None,
            humidity_pct=self.last_sample.humidity_pct if self.last_sample else None,
            pressure_hpa=self.last_sample.pressure_hpa if self.last_sample else None,
            motion_index=imu_f["motion_index"],
            activity_level=imu_f["activity_level"],
            low_activity_risk=imu_f["low_activity_risk"],
            skin_temp_c=temp_f.get("skin_temp_c"),
            temp_slope_c_per_min=temp_f.get("temp_slope_c_per_min") or 0.0,
        )

        # Quality: mean over present sensors only
        quality_parts = [ppg_f.get("ppg_quality") or 0.0]
        if fv.ecg_quality > 0:
            quality_parts.append(float(fv.ecg_quality))
        if fv.skin_temp_c is not None:
            quality_parts.append(1.0)
        fv.signal_quality = float(np.mean(quality_parts)) if quality_parts else 0.0
        fv.baseline_completeness = min(1.0, (now - self.start_time) / BASELINE_CAPTURE_S)

        # Sleep estimate - simple heuristic
        import datetime as _dt
        dt = _dt.datetime.fromtimestamp(now)
        hour = dt.hour + dt.minute / 60.0
        # Sleep probability based on time and motion
        if hour >= 22 or hour <= 6:
            time_prior = 0.8
        else:
            time_prior = 0.1
        motion_factor = max(0.0, 1.0 - fv.motion_index / 0.5)
        hr_factor = 0.0
        if fv.hr_bpm and fv.hr_bpm < 65:
            hr_factor = 0.3
        sleep_prob = (time_prior * 0.5 + motion_factor * 0.3 + hr_factor * 0.2) * 100.0
        fv.sleep_probability = float(sleep_prob)
        fv.sleep_status = "sleep" if sleep_prob > 60 else "wake"
        fv.sleep_duration_h = 7.5  # placeholder, updated from history
        fv.sleep_regularity = 75.0

        # Circadian from baseline engine or default
        cm = self.circadian_metrics
        if cm is not None:
            fv.circadian_stability_index = float(cm.stability_index)
            fv.circadian_disruption = float(cm.disruption_score)
        else:
            fv.circadian_stability_index = 70.0
            fv.circadian_disruption = 30.0

        # Stress - simple
        if fv.rmssd_ms and fv.hr_bpm:
            # Low HRV + high HR = higher stress
            hrv_norm = max(0.0, min(1.0, (fv.rmssd_ms - 20) / 40.0))
            hr_norm = max(0.0, min(1.0, (fv.hr_bpm - 60) / 40.0))
            fv.stress_index = float((1 - hrv_norm) * 0.6 + hr_norm * 0.4) * 100.0
            fv.autonomic_imbalance = float((1 - hrv_norm) * 100.0)
        else:
            fv.stress_index = 30.0
            fv.autonomic_imbalance = 30.0

        # Completeness adjustment
        c = completeness_score(fv.hr_bpm, fv.rmssd_ms, fv.skin_temp_c, fv.spo2_pct)
        fv.signal_quality = 0.7 * fv.signal_quality + 0.3 * c

        # Personal baseline
        if self.baseline_engine.has_baseline:
            fv.baseline_available = True
            fv.baseline_age_s = now - self.baseline_engine.baseline.captured_at
            fv.baseline_completeness = 1.0
            fv.baseline_confidence = self.baseline_engine.baseline.confidence
            fv.hr_zscore = self._z("hr_bpm", fv.hr_bpm, now)
            fv.rmssd_zscore = self._z("rmssd_ms", fv.rmssd_ms, now)
            fv.skin_temp_zscore = self._z("skin_temp_c", fv.skin_temp_c, now)
            fv.resting_hr_zscore = self._z("resting_hr_bpm", fv.resting_hr_bpm, now)
            fv.activity_zscore = self._z("activity_level", fv.activity_level, now)
        else:
            elapsed = now - self.start_time
            if not self.auto_captured and elapsed >= BASELINE_CAPTURE_S:
                recent = [f for f in self.feature_history if now - f.timestamp_s <= BASELINE_CAPTURE_S]
                if recent and float(np.mean([f.signal_quality for f in recent])) >= 0.5:
                    self.auto_captured = self.capture_baseline(window_s=BASELINE_CAPTURE_S)
                    fv.baseline_available = self.baseline_engine.has_baseline
                    fv.baseline_completeness = 1.0 if self.baseline_engine.has_baseline else fv.baseline_completeness

        # FSR correction
        fsr = self.last_sample.fsr_raw if self.last_sample is not None else None
        if fsr is not None and fsr > 0:
            from src.utils.math_utils import clamp
            fv.fsr_pressure_index = clamp(fsr / 420.0, 0.4, 2.5)
            if fv.ppg_pulse_amplitude is not None:
                fv.ppg_pulse_amplitude_corrected = fv.ppg_pulse_amplitude / fv.fsr_pressure_index
            if fv.fsr_pressure_index > 1.8 or fv.fsr_pressure_index < 0.5:
                fv.signal_quality = clamp(fv.signal_quality - 0.15, 0.0, 1.0)

        # Shared features
        try:
            shared = self.shared_extractor.extract(fv, list(self.feature_history)[-50:])
            fv.shared_features = shared.as_dict()
        except Exception:
            pass

        # Continual learning happens after the row has been scored, so a sample is
        # never compared against a norm it has already been folded into.
        self.learning_events = []
        if self.learner is not None:
            try:
                self.learning_events = self.learner.observe(fv)
            except Exception:
                self.learning_events = []

        self.last_feature = fv
        self.feature_history.append(fv)
        return fv

    def _z(self, metric: str, value: Optional[float], ts: float) -> Optional[float]:
        """Personal z-score from the continually-learned norm, else the frozen snapshot."""
        if self.learner is not None:
            try:
                z = self.learner.z(metric, value, at_ts=ts)
            except Exception:
                z = None
            if z is not None:
                return z
        return self.baseline_engine.zscore(metric, value)

    def ppg_waveform(self, last_s: float = 20.0):
        return self.ppg.waveform(last_s=last_s)

    def history_arrays(self, attr: str, last_s: float = 180.0):
        if not self.feature_history:
            return np.array([]), np.array([])
        t = np.array([f.timestamp_s for f in self.feature_history])
        y = np.array([getattr(f, attr, np.nan) if getattr(f, attr, None) is not None else np.nan for f in self.feature_history], dtype=float)
        mask = t >= (t[-1] - last_s)
        return t[mask] - t[-1], y[mask]
