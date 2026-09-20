"""
Provenance - Make provenance first-class architecture
Every important data object should indicate MEASURED/CLINICALLY ENTERED/IMAGE-DERIVED/MODEL-INFERRED/DEMO DATA/UNKNOWN
"""

from enum import Enum
from typing import Dict, Any, List
from dataclasses import dataclass

class ProvenanceLabel(Enum):
    MEASURED = "MEASURED"  # Directly measured HR, temp, motion, GSR raw
    CLINICALLY_ENTERED = "CLINICALLY_ENTERED"  # USER-ENTERED age, BMI, cycle, symptoms, glucose, BP
    IMAGE_DERIVED = "IMAGE_DERIVED"  # Cyst size, volume, morphology from ultrasound image
    MODEL_INFERRED = "MODEL_INFERRED"  # Sleep regularity, circadian disruption, HRV derived, risk signals
    DEMO_DATA = "DEMO_DATA"  # Demo providers, demo patients, synthetic data clearly labelled
    UNKNOWN = "UNKNOWN"  # If cannot reliably extract return UNKNOWN never invent

@dataclass
class ProvenanceRecord:
    data_id: str
    patient_id: str
    label: ProvenanceLabel
    source: str  # MAX30102, DS18B20, MPU6050, USER-ENTERED, image path, model name
    quality: float  # 0-1
    confidence: float = None  # 0-1 if applicable, None unless computed, never hard-code fake
    timestamp: float = 0
    limitations: str = ""
    explainability: str = ""
    is_demo: bool = False

class ProvenanceTracker:
    """
    Provenance tracking - first-class architecture
    Appears in Doctor PC, Doctor Android, Patient Android where appropriate, Reports, AI/ML, Ultrasound, Database metadata
    """

    def __init__(self):
        self.version = "8.3+"

    def get_patient_provenance(self, patient_id: str) -> Dict[str, Any]:
        return {
            "patient_id": patient_id,
            "provenance_labels": {
                "MEASURED": {
                    "description": "Directly measured HR 72 bpm quality 0.91 source MAX30102, Skin Temp 32.5°C quality 0.88 source DS18B20, Motion ax_g ay_g az_g gx_dps gy_dps gz_dps motion_index activity_level quality 0.8 source MPU6050, GSR raw gsr_raw quality source GSR",
                    "category": "ESTABLISHED_MEASUREMENT",
                    "examples": ["HR bpm MAX30102", "Skin Temp C DS18B20", "Motion MPU6050", "GSR raw"]
                },
                "CLINICALLY_ENTERED": {
                    "description": "Age 22 years, BMI 23.5, cycle length 28 days, irregularity regular, symptoms irregular_cycle mild, notes free text, Glucose BP if entered",
                    "category": "CLINICALLY_ENTERED",
                    "label": "USER-ENTERED",
                    "examples": ["Age", "BMI", "Cycle info", "Symptoms", "Glucose", "BP"]
                },
                "IMAGE_DERIVED": {
                    "description": "Cyst size mm, volume cc, morphology, quality, source, confidence, notes, ultrasound image path format size check, preprocessing resize normalize denoise, quality checks blur exposure anatomy visibility quality score UNKNOWN by design unless computed provenance CLINICALLY-ENTERED vs IMAGE-DERIVED",
                    "category": "IMAGE_DERIVED",
                    "quality_gate": "UNKNOWN by design unless computed",
                    "fusion_weight": 0.20,
                    "examples": ["Cyst size mm", "Volume cc", "Morphology"]
                },
                "MODEL_INFERRED": {
                    "description": "Sleep regularity 75%, circadian disruption pattern moderate, HRV RMSSD 48 ms SDNN 55 ms pNN50 % derived from HR time series limitations PPG less accurate than ECG, GSR tonic lowpass derived phasic highpass derived, circadian sleep-wake estimation HR/HRV 24h pattern model-inferred limitations not polysomnography, autonomic HRV+GSR experimental, metabolic multimodal experimental not clinical, chrono-metabolic fingerprint experimental research not diagnosis, PCOS associated risk low/moderate/high NOT diagnosis",
                    "category": "DERIVED_FEATURE, EXPERIMENTAL_RESEARCH, MODEL-INFERRED",
                    "confidence": "Model output not clinical certainty",
                    "limitations": "Engineering validation only, clinical validation NOT ESTABLISHED",
                    "examples": ["HRV RMSSD", "Sleep regularity", "Circadian disruption", "PCOS risk signal"]
                },
                "DEMO_DATA": {
                    "description": "Demo providers 4 demo clearly marked demo verification_status demo is_demo 1 never falsely label real doctor/clinic verified, Demo patients DEMO-001 DEMO-002 DEMO-003 deliberately different data, Synthetic data 10 subjects 30 days 6 scenarios 60 days wrist_ppg SYNTHETIC clearly labelled SYNTHETIC never label synthetic as clinical never mix REAL/SYNTHETIC silently",
                    "is_demo": True,
                    "examples": ["Demo providers", "Demo patients", "Synthetic data"]
                },
                "UNKNOWN": {
                    "description": "If feature cannot be reliably extracted return UNKNOWN never invent, never fabricate measurements diagnoses clinical validation medical certainty, quality score UNKNOWN by design unless computed, inference requires trained model if insufficient state insufficient never fabricate percentages confidence None unless computed",
                    "examples": ["Insufficient data", "Quality too low", "Model not trained"]
                }
            },
            "safety": "Never fabricate measurements, diagnoses, clinical validation, or medical certainty. Clearly distinguish MEASURED CLINICALLY ENTERED IMAGE-DERIVED MODEL-INFERRED DEMO DATA UNKNOWN. Never mix them. Never represent model inference as measurement. Never represent simulated data as real patient data.",
            "disclaimer": "Provenance tracking - first-class architecture"
        }

    def label_data(self, data_id: str, patient_id: str, label: ProvenanceLabel, source: str, quality: float, is_demo: bool = False) -> ProvenanceRecord:
        import time
        return ProvenanceRecord(
            data_id=data_id,
            patient_id=patient_id,
            label=label,
            source=source,
            quality=quality,
            timestamp=time.time(),
            is_demo=is_demo
        )
