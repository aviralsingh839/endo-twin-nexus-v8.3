"""Typed data containers for CHRONO-TWIN NEXUS V8.3."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import time


@dataclass
class SensorQuality:
    """Quality metadata for every sensor reading."""

    value: float | None
    quality: float  # 0..1
    source: str
    timestamp: float = field(default_factory=time.time)
    artifact: bool = False
    artifact_type: Optional[str] = None
    reason: str = ""

    def is_valid(self) -> bool:
        return self.value is not None and self.quality >= 0.3 and not self.artifact

    def as_dict(self) -> dict:
        return {
            "value": self.value,
            "quality": round(self.quality, 3),
            "source": self.source,
            "timestamp": self.timestamp,
            "artifact": self.artifact,
            "artifact_type": self.artifact_type,
            "reason": self.reason,
        }


@dataclass
class SensorSample:
    """One decoded Arduino sample with quality tracking."""

    timestamp_s: float
    ms: int
    ir: int
    red: int
    # V8.8: for the analog Pulse Sensor wearable, ir stores the single-channel
    # ADC waveform and red remains -1. The explicit source/status metadata keeps
    # optical MAX3010x data distinguishable from analog pulse data.
    ax_g: float
    ay_g: float
    az_g: float
    gx_dps: float
    gy_dps: float
    gz_dps: float
    temp_c: float
    gsr_raw: int
    lux: float
    ecg_raw: int = -1
    mic_raw: int = -1
    mic_rms: float = 0.0
    mic_pitch_hz: float = 0.0
    fsr_raw: int = -1
    temp1_c: float = float('nan')
    room_temp_c: float = float('nan')
    humidity_pct: float = float('nan')
    pressure_hpa: float = float('nan')
    buttons: int = 0
    status: int = 0
    ppg_quality: float = 1.0
    source: str = "serial"
    # V8.8: explicit PPG hardware/provenance.
    ppg_input_type: str = "OPTICAL_IR_RED"
    # V8.3 quality metadata
    quality_meta: Dict[str, SensorQuality] = field(default_factory=dict)


@dataclass
class FeatureVector:
    """Real-time physiological features with quality and baseline tracking."""

    timestamp_s: float = 0.0
    # Core vitals
    hr_bpm: Optional[float] = None
    resting_hr_bpm: Optional[float] = None
    spo2_pct: Optional[float] = None
    rmssd_ms: Optional[float] = None
    sdnn_ms: Optional[float] = None
    pnn50_pct: Optional[float] = None
    ppg_pulse_amplitude: Optional[float] = None
    # Environment / extras
    lux: Optional[float] = None
    fsr_raw: Optional[float] = None
    ecg_raw: Optional[float] = None
    ecg_hr_bpm: Optional[float] = None
    ecg_rmssd_ms: Optional[float] = None
    ecg_quality: float = 0.0
    mic_rms: Optional[float] = None
    mic_pitch_hz: Optional[float] = None
    voice_vasc_score: float = 0.0
    room_temp_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    pressure_hpa: Optional[float] = None
    mv_challenge_risk: float = 0.0
    # Activity / motion
    motion_index: float = 0.0
    activity_level: float = 0.0
    # Temperature
    skin_temp_c: Optional[float] = None
    temp_slope_c_per_min: float = 0.0
    # GSR / stress
    gsr_tonic: Optional[float] = None
    gsr_phasic_per_min: float = 0.0
    stress_index: float = 0.0
    acute_stress: float = 0.0
    chronic_stress: float = 0.0
    autonomic_imbalance: float = 0.0
    # Sleep
    sleep_status: str = "unknown"
    sleep_probability: float = 0.0
    deep_sleep_probability: float = 0.0
    rem_probability: float = 0.0
    sleep_duration_h: Optional[float] = None
    sleep_regularity: float = 0.0
    sleep_timing_h: Optional[float] = None
    # Metabolic
    glucose_risk: float = 0.0
    bp_risk: float = 0.0
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    insulin_resistance_probability: float = 0.0
    metabolic_syndrome_proxy: float = 0.0
    inflammation_score: float = 0.0
    # Circadian
    circadian_stability_index: float = 50.0
    circadian_disruption: float = 50.0
    low_activity_risk: float = 0.0
    temperature_rhythm_disruption: float = 50.0
    # Quality
    signal_quality: float = 0.0
    baseline_completeness: float = 0.0
    # Personalization
    baseline_available: bool = False
    baseline_age_s: Optional[float] = None
    baseline_confidence: float = 0.0
    hr_zscore: Optional[float] = None
    rmssd_zscore: Optional[float] = None
    skin_temp_zscore: Optional[float] = None
    gsr_zscore: Optional[float] = None
    resting_hr_zscore: Optional[float] = None
    activity_zscore: Optional[float] = None
    # FSR correction
    fsr_pressure_index: Optional[float] = None
    ppg_pulse_amplitude_corrected: Optional[float] = None
    # Anomaly
    anomaly_score: float = 0.0
    anomalies: List[str] = field(default_factory=list)
    # V8.3: quality per feature
    quality_per_feature: Dict[str, float] = field(default_factory=dict)
    # V8.3: shared representation cache
    shared_features: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, float | str | None]:
        return self.__dict__.copy()


@dataclass
class SharedPhysiologicalFeatures:
    """Common physiological representation consumed by disease modules.

    This avoids duplicating signal-processing code in every disease model.
    """

    timestamp_s: float = field(default_factory=time.time)
    # Heart
    heart_rate: Optional[float] = None
    resting_heart_rate: Optional[float] = None
    hrv_rmssd: Optional[float] = None
    hrv_sdnn: Optional[float] = None
    # Activity
    activity_level: float = 0.0
    motion_index: float = 0.0
    low_activity_risk: float = 0.0
    # Sleep / circadian
    sleep_duration_h: Optional[float] = None
    sleep_regularity: float = 0.0
    sleep_timing_h: Optional[float] = None
    sleep_probability: float = 0.0
    circadian_stability: float = 50.0
    circadian_disruption: float = 50.0
    day_night_activity_ratio: float = 0.0
    # Temperature
    skin_temp_c: Optional[float] = None
    temperature_trend_c_per_day: float = 0.0
    temperature_rhythm_disruption: float = 50.0
    # Stress / autonomic
    gsr_tonic: Optional[float] = None
    stress_index: float = 0.0
    autonomic_imbalance: float = 0.0
    # Recovery
    recovery_score: float = 50.0
    # Baseline deviations
    baseline_deviations: Dict[str, float] = field(default_factory=dict)
    trend_features: Dict[str, float] = field(default_factory=dict)
    # Quality
    sensor_quality: Dict[str, float] = field(default_factory=dict)
    overall_quality: float = 0.0
    # Provenance
    provenance: Dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "timestamp_s": self.timestamp_s,
            "heart_rate": self.heart_rate,
            "resting_heart_rate": self.resting_heart_rate,
            "hrv_rmssd": self.hrv_rmssd,
            "hrv_sdnn": self.hrv_sdnn,
            "activity_level": self.activity_level,
            "motion_index": self.motion_index,
            "low_activity_risk": self.low_activity_risk,
            "sleep_duration_h": self.sleep_duration_h,
            "sleep_regularity": self.sleep_regularity,
            "sleep_timing_h": self.sleep_timing_h,
            "sleep_probability": self.sleep_probability,
            "circadian_stability": self.circadian_stability,
            "circadian_disruption": self.circadian_disruption,
            "day_night_activity_ratio": self.day_night_activity_ratio,
            "skin_temp_c": self.skin_temp_c,
            "temperature_trend_c_per_day": self.temperature_trend_c_per_day,
            "temperature_rhythm_disruption": self.temperature_rhythm_disruption,
            "gsr_tonic": self.gsr_tonic,
            "stress_index": self.stress_index,
            "autonomic_imbalance": self.autonomic_imbalance,
            "recovery_score": self.recovery_score,
            "baseline_deviations": self.baseline_deviations,
            "trend_features": self.trend_features,
            "sensor_quality": self.sensor_quality,
            "overall_quality": self.overall_quality,
        }


@dataclass
class HormoneEstimate:
    name: str
    value: float
    unit: str
    ci_low: float
    ci_high: float
    confidence: float
    drivers: List[str] = field(default_factory=list)
    note: str = "Estimated Hormone Level - not measured"


@dataclass
class RiskResult:
    risk_percent: float
    ci_low: float
    ci_high: float
    confidence: float
    category: str
    domain_scores: Dict[str, float]
    contributions: List[Tuple[str, float, str]]
    explanation: str
    hormone_estimates: Dict[str, HormoneEstimate] = field(default_factory=dict)


@dataclass
class DiseaseModuleResult:
    """Structured output from a disease-specific module.

    Never returns 'DISEASE DETECTED' - only research signals.
    """

    module: str
    version: str
    signal: str  # e.g. 'circadian_deviation', 'metabolic_risk'
    level: str  # low, moderate, elevated, high
    confidence: float  # model confidence 0..1
    data_quality: float  # data quality 0..1
    clinical_validation: str = "NOT ESTABLISHED"  # NOT ESTABLISHED, PRELIMINARY, VALIDATED
    drivers: List[Dict[str, Any]] = field(default_factory=list)
    explanation: str = ""
    provenance: Dict[str, float] = field(default_factory=dict)
    limitations: str = ""
    timestamp_s: float = field(default_factory=time.time)
    extra: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "module": self.module,
            "signal": self.signal,
            "level": self.level,
            "confidence": round(self.confidence, 3),
            "data_quality": round(self.data_quality, 3),
            "clinical_status": "research_only",
            "clinical_validation": self.clinical_validation,
            "drivers": self.drivers,
            "explanation": self.explanation,
            "provenance": self.provenance,
            "limitations": self.limitations,
            "timestamp_s": self.timestamp_s,
            "extra": self.extra,
        }


@dataclass
class SleepMetrics:
    sleep_duration_min: float = 0.0
    time_in_bed_min: float = 0.0
    sleep_efficiency_pct: float = 0.0
    wake_frequency: int = 0
    restlessness_pct: float = 0.0
    deep_sleep_estimate_pct: float = 0.0
    rem_probability_pct: float = 0.0
    sleep_consistency_pct: float = 0.0
    circadian_disruption_pct: float = 50.0
    regularity_score: float = 0.0
    timing_sd_h: Optional[float] = None


@dataclass
class CircadianMetrics:
    stability_index: float = 50.0
    disruption_score: float = 50.0
    hr_r2: float = 0.0
    hrv_r2: float = 0.0
    temp_r2: float = 0.0
    gsr_r2: float = 0.0
    activity_regular: float = 0.0
    sleep_regular: float = 0.0
    light_regular: float = 0.0
    sleep_midpoint_sd_h: Optional[float] = None
