"""Feature Extraction - V8.3.

RAW DATA -> Sensor Quality Control -> Signal Processing -> Physiological Feature Extraction -> Personal Baseline

Produces FeatureVector and SharedPhysiologicalFeatures.
"""
from __future__ import annotations

import time
import math
from collections import deque
from typing import Deque, Optional

import numpy as np

from src.config import BASELINE_CAPTURE_S, BASELINE_MIN_SAMPLES, DEFAULT_PROFILE, UserProfile
from src.data_models import FeatureVector, SensorSample
from src.core.quality_control import SensorQualityControl
from src.core.personal_baseline import PersonalBaselineEngine
from src.core.shared_features import SharedFeatureExtractor
from src.signal_processing.ppg import PPGProcessor
from src.signal_processing.imu import IMUProcessor
from src.signal_processing.gsr import GSRProcessor
from src.signal_processing.temperature import TemperatureProcessor
from src.signal_processing.ecg import ECGProcessor
from src.utils.quality import completeness_score


class RealtimeFeatureExtractor:
    """Streaming feature extractor with quality control."""

    def __init__(self, profile: UserProfile | None = None, baseline_engine: Optional[PersonalBaselineEngine] = None):
        self.profile = profile or DEFAULT_PROFILE
        self.baseline_engine = baseline_engine or PersonalBaselineEngine()
        self.quality_control = SensorQualityControl()
        self.shared_extractor = SharedFeatureExtractor(baseline_engine=self.baseline_engine)

        # Signal processors
        self.ppg_input_type = "OPTICAL_IR_RED"
        self.ppg = PPGProcessor(input_type=self.ppg_input_type)
        self.imu = IMUProcessor()
        self.gsr = GSRProcessor()
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
            bl = self.baseline_engine.capture_from_features(rows, min_samples=BASELINE_MIN_SAMPLES)
            self.auto_captured = False
            self.last_capture_error = None
            return True
        except ValueError as exc:
            self.last_capture_error = str(exc)
            return False

    def add_sample(self, sample: SensorSample) -> None:
        self.last_sample = sample
        if sample.ppg_input_type:
            self.ppg_input_type = sample.ppg_input_type.upper()
        # Quality check per channel - V8.4 shoulder+forearm
        # Analog Pulse Sensor uses ADC, not optical thresholds
        # Includes BME280 (room temp/hum/press) + BH1750 (lux) + DS18B20 (skin temp)
        base_channels = {
            "ax_g": sample.ax_g,
            "ay_g": sample.ay_g,
            "az_g": sample.az_g,
            "temp_c": sample.temp_c,
            "gsr_raw": sample.gsr_raw,
            "ecg_raw": sample.ecg_raw,
            "room_temp_c": sample.room_temp_c if sample.room_temp_c and not math.isnan(sample.room_temp_c) else None,
            "humidity_pct": sample.humidity_pct if sample.humidity_pct and not math.isnan(sample.humidity_pct) else None,
            "pressure_hpa": sample.pressure_hpa if sample.pressure_hpa and not math.isnan(sample.pressure_hpa) else None,
            "lux": sample.lux if sample.lux and not math.isnan(sample.lux) else None,
        }
        # Remove None for quality check
        quality_input_clean = {k: v for k, v in base_channels.items() if v is not None and not (isinstance(v, float) and math.isnan(v))}
        if sample.ppg_input_type in {"ANALOG_PULSE", "ANALOG_PULSE_SENSOR"}:
            quality_input = {"analog_pulse": sample.ir, **quality_input_clean}
        else:
            quality_input = {"ir": sample.ir, "red": sample.red, **quality_input_clean}

        qualities = self.quality_control.evaluate_sample(quality_input, source=sample.source, timestamp_s=sample.timestamp_s)
        self._quality_history.append({k: v.quality for k, v in qualities.items()})

        self.ppg.add_sample(sample.timestamp_s, sample.ir, sample.red, input_type=sample.ppg_input_type)
        self.imu.add_sample(sample.timestamp_s, sample.ax_g, sample.ay_g, sample.az_g,
                            sample.gx_dps, sample.gy_dps, sample.gz_dps)
        self.gsr.add_sample(sample.timestamp_s, sample.gsr_raw)
        self.temp.add_sample(sample.timestamp_s, sample.temp_c)
        self.ecg.add_sample(sample.timestamp_s, sample.ecg_raw)
        self.last_lux = sample.lux if sample.lux is not None and sample.lux >= 0 else self.last_lux
        # Env history for trends
        if not hasattr(self, '_env_history'):
            self._env_history = deque(maxlen=3600)
        self._env_history.append({
            "room_temp": sample.room_temp_c,
            "hum": sample.humidity_pct,
            "press": sample.pressure_hpa,
            "lux": sample.lux,
            "skin_temp": sample.temp_c,
            "ts": sample.timestamp_s
        })

    def compute(self) -> FeatureVector:
        now = time.time()
        imu_f = self.imu.features()
        ppg_f = self.ppg.features(motion_index=imu_f["motion_index"])
        gsr_f = self.gsr.features()
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
            gsr_tonic=gsr_f.get("gsr_tonic"),
            gsr_phasic_per_min=gsr_f.get("gsr_phasic_per_min") or 0.0,
        )

        # Quality: mean over present sensors only
        quality_parts = [ppg_f.get("ppg_quality") or 0.0]
        if fv.ecg_quality > 0:
            quality_parts.append(float(fv.ecg_quality))
        if fv.skin_temp_c is not None:
            quality_parts.append(1.0)
        if fv.gsr_tonic is not None:
            quality_parts.append(1.0)
        fv.signal_quality = float(np.mean(quality_parts)) if quality_parts else 0.0
        fv.baseline_completeness = min(1.0, (now - self.start_time) / (5 * 60.0))

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
            fv.stress_index = 0.0
            fv.autonomic_imbalance = 0.0

        # Completeness adjustment
        completeness_values = [fv.hr_bpm, fv.rmssd_ms, fv.skin_temp_c, fv.gsr_tonic]
        if self.ppg_input_type not in {"ANALOG_PULSE", "ANALOG_PULSE_SENSOR"}:
            completeness_values.append(fv.spo2_pct)
        c = completeness_score(*completeness_values)
        fv.signal_quality = 0.7 * fv.signal_quality + 0.3 * c

        # Personal baseline
        if self.baseline_engine.has_baseline:
            fv.baseline_available = True
            fv.baseline_age_s = now - self.baseline_engine.baseline.captured_at
            fv.baseline_completeness = 1.0
            fv.baseline_confidence = self.baseline_engine.baseline.confidence
            fv.hr_zscore = self.baseline_engine.zscore("hr_bpm", fv.hr_bpm)
            fv.rmssd_zscore = self.baseline_engine.zscore("rmssd_ms", fv.rmssd_ms)
            fv.skin_temp_zscore = self.baseline_engine.zscore("skin_temp_c", fv.skin_temp_c)
            fv.gsr_zscore = self.baseline_engine.zscore("gsr_tonic", fv.gsr_tonic)
            fv.resting_hr_zscore = self.baseline_engine.zscore("resting_hr_bpm", fv.resting_hr_bpm)
            fv.activity_zscore = self.baseline_engine.zscore("activity_level", fv.activity_level)
        else:
            elapsed = now - self.start_time
            if not self.auto_captured and elapsed >= BASELINE_CAPTURE_S:
                recent = [f for f in self.feature_history if now - f.timestamp_s <= BASELINE_CAPTURE_S]
                if recent and float(np.mean([f.signal_quality for f in recent])) >= 0.5:
                    self.auto_captured = self.capture_baseline()
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

        self.last_feature = fv
        self.feature_history.append(fv)
        return fv

    def ppg_waveform(self, last_s: float = 20.0):
        return self.ppg.waveform(last_s=last_s)

    def history_arrays(self, attr: str, last_s: float = 180.0):
        if not self.feature_history:
            return np.array([]), np.array([])
        t = np.array([f.timestamp_s for f in self.feature_history])
        y = np.array([getattr(f, attr, np.nan) if getattr(f, attr, None) is not None else np.nan for f in self.feature_history], dtype=float)
        mask = t >= (t[-1] - last_s)
        return t[mask] - t[-1], y[mask]
