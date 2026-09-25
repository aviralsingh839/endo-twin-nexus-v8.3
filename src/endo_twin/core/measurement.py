"""
ENDO-TWIN Core - General Measurement Model

No PCOS-specific assumptions.
General physiological measurements for any condition.

Supports:
- Patient
- Observation
- Measurement
- SensorReading
- Signal
- Feature
- Baseline
- TimelineEvent
- LongitudinalSeries
- Model
- Prediction
- Explanation
- Uncertainty
- Provenance
- Report
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import uuid
import time


class ProvenanceLabel(str, Enum):
    MEASURED = "MEASURED"
    CLINICALLY_ENTERED = "CLINICALLY_ENTERED"
    IMAGE_DERIVED = "IMAGE-DERIVED"
    MODEL_INFERRED = "MODEL-INFERRED"
    DEMO_DATA = "DEMO_DATA"
    UNKNOWN = "UNKNOWN"


class MeasurementType(str, Enum):
    # General physiological
    HEART_RATE = "heart_rate"
    HRV_RMSSD = "hrv_rmssd"
    HRV_SDNN = "hrv_sdnn"
    HRV_PNN50 = "hrv_pnn50"
    PPG = "ppg"
    GSR = "gsr"
    TEMPERATURE = "temperature"
    MOTION = "motion"
    ACTIVITY = "activity"
    SLEEP = "sleep"
    SPO2 = "spo2"
    
    # General derived
    CIRCADIAN = "circadian"
    AUTONOMIC = "autonomic"
    METABOLIC = "metabolic"
    
    # General clinical
    BMI = "bmi"
    BLOOD_PRESSURE = "blood_pressure"
    GLUCOSE = "glucose"
    
    # General imaging
    ULTRASOUND = "ultrasound"
    IMAGING = "imaging"
    
    # General
    SYMPTOM = "symptom"
    CLINICAL_OBSERVATION = "clinical_observation"


@dataclass
class SensorReading:
    """Raw sensor reading - general"""
    reading_id: str = field(default_factory=lambda: f"READ-{uuid.uuid4().hex[:8]}")
    patient_id: str = ""
    sensor_type: str = ""  # generic analog Pulse Sensor, MPU6050, DS18B20, GSR, etc.
    timestamp: float = field(default_factory=time.time)
    values: Dict[str, Any] = field(default_factory=dict)  # raw values
    quality: float = 0.0  # 0-1
    provenance: ProvenanceLabel = ProvenanceLabel.MEASURED
    is_demo: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "reading_id": self.reading_id,
            "patient_id": self.patient_id,
            "sensor_type": self.sensor_type,
            "timestamp": self.timestamp,
            "values": self.values,
            "quality": self.quality,
            "provenance": self.provenance.value,
            "is_demo": self.is_demo,
            "metadata": self.metadata
        }


@dataclass
class Measurement:
    """Processed measurement - general"""
    measurement_id: str = field(default_factory=lambda: f"MEAS-{uuid.uuid4().hex[:8]}")
    patient_id: str = ""
    session_id: Optional[str] = None
    measurement_type: MeasurementType = MeasurementType.HEART_RATE
    value: Optional[float] = None
    value_json: Dict[str, Any] = field(default_factory=dict)  # for complex values
    unit: str = ""
    timestamp: float = field(default_factory=time.time)
    quality: float = 0.0  # 0-1
    provenance: ProvenanceLabel = ProvenanceLabel.MEASURED
    source: str = ""  # generic analog Pulse Sensor, USER-ENTERED, etc.
    confidence: Optional[float] = None
    limitations: str = ""
    is_demo: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "measurement_id": self.measurement_id,
            "patient_id": self.patient_id,
            "session_id": self.session_id,
            "measurement_type": self.measurement_type.value,
            "value": self.value,
            "value_json": self.value_json,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "quality": self.quality,
            "provenance": self.provenance.value,
            "source": self.source,
            "confidence": self.confidence,
            "limitations": self.limitations,
            "is_demo": self.is_demo,
            "metadata": self.metadata
        }


@dataclass
class Feature:
    """Extracted feature - general"""
    feature_id: str = field(default_factory=lambda: f"FEAT-{uuid.uuid4().hex[:8]}")
    patient_id: str = ""
    session_id: Optional[str] = None
    measurement_id: Optional[str] = None
    feature_name: str = ""
    feature_value: Optional[float] = None
    feature_json: Dict[str, Any] = field(default_factory=dict)
    category: str = "established_measurement"  # established_measurement, derived_feature, experimental_research, ml_prediction, clinical_interpretation
    quality: float = 0.0
    provenance: ProvenanceLabel = ProvenanceLabel.MEASURED
    source: str = ""
    confidence: Optional[float] = None
    limitations: str = ""
    explainability: str = ""
    is_demo: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_id": self.feature_id,
            "patient_id": self.patient_id,
            "session_id": self.session_id,
            "measurement_id": self.measurement_id,
            "feature_name": self.feature_name,
            "feature_value": self.feature_value,
            "feature_json": self.feature_json,
            "category": self.category,
            "quality": self.quality,
            "provenance": self.provenance.value,
            "source": self.source,
            "confidence": self.confidence,
            "limitations": self.limitations,
            "explainability": self.explainability,
            "is_demo": self.is_demo,
            "metadata": self.metadata
        }


@dataclass
class Observation:
    """General clinical observation - not disease-specific"""
    observation_id: str = field(default_factory=lambda: f"OBS-{uuid.uuid4().hex[:8]}")
    patient_id: str = ""
    observation_type: str = ""  # symptom, clinical, cycle, etc.
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    provenance: ProvenanceLabel = ProvenanceLabel.CLINICALLY_ENTERED
    source: str = "USER-ENTERED"
    is_demo: bool = False
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "patient_id": self.patient_id,
            "observation_type": self.observation_type,
            "data": self.data,
            "timestamp": self.timestamp,
            "provenance": self.provenance.value,
            "source": self.source,
            "is_demo": self.is_demo,
            "notes": self.notes
        }


@dataclass
class TimelineEvent:
    """General timeline event"""
    event_id: str = field(default_factory=lambda: f"TIMELINE-{uuid.uuid4().hex[:8]}")
    patient_id: str = ""
    event_type: str = ""  # sensor_session, symptom_entry, clinical_entry, imaging, analysis, model_run, report_generated, etc.
    title: str = ""
    description: str = ""
    timestamp: float = field(default_factory=time.time)
    provenance: ProvenanceLabel = ProvenanceLabel.MEASURED
    data: Dict[str, Any] = field(default_factory=dict)
    is_demo: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "patient_id": self.patient_id,
            "event_type": self.event_type,
            "title": self.title,
            "description": self.description,
            "timestamp": self.timestamp,
            "provenance": self.provenance.value,
            "data": self.data,
            "is_demo": self.is_demo
        }


@dataclass
class Baseline:
    """General personal baseline"""
    baseline_id: str = field(default_factory=lambda: f"BASE-{uuid.uuid4().hex[:8]}")
    patient_id: str = ""
    feature_name: str = ""
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    std_value: Optional[float] = None
    mad_value: Optional[float] = None
    confidence: float = 0.0
    min_observations: int = 0
    current_observations: int = 0
    baseline_period_start: Optional[float] = None
    baseline_period_end: Optional[float] = None
    circadian_context: Dict[str, Any] = field(default_factory=dict)
    provenance: ProvenanceLabel = ProvenanceLabel.MEASURED
    is_demo: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_id": self.baseline_id,
            "patient_id": self.patient_id,
            "feature_name": self.feature_name,
            "mean_value": self.mean_value,
            "median_value": self.median_value,
            "std_value": self.std_value,
            "mad_value": self.mad_value,
            "confidence": self.confidence,
            "min_observations": self.min_observations,
            "current_observations": self.current_observations,
            "baseline_period_start": self.baseline_period_start,
            "baseline_period_end": self.baseline_period_end,
            "circadian_context": self.circadian_context,
            "provenance": self.provenance.value,
            "is_demo": self.is_demo
        }


@dataclass
class LongitudinalSeries:
    """General longitudinal series"""
    series_id: str = field(default_factory=lambda: f"LONG-{uuid.uuid4().hex[:8]}")
    patient_id: str = ""
    feature_name: str = ""
    data_points: List[Dict[str, Any]] = field(default_factory=list)  # [{timestamp, value, quality}, ...]
    baseline_id: Optional[str] = None
    trend: str = "stable"  # stable, increasing, decreasing, fluctuating
    persistence: float = 0.0  # 0-1, how persistent is change
    change_detected: bool = False
    recovery_detected: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "series_id": self.series_id,
            "patient_id": self.patient_id,
            "feature_name": self.feature_name,
            "data_points": self.data_points,
            "baseline_id": self.baseline_id,
            "trend": self.trend,
            "persistence": self.persistence,
            "change_detected": self.change_detected,
            "recovery_detected": self.recovery_detected
        }
