"""
General Provenance Tracker - No PCOS assumptions
Every important data object should indicate MEASURED/CLINICALLY_ENTERED/IMAGE-DERIVED/MODEL-INFERRED/DEMO_DATA/UNKNOWN
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import time

class GeneralProvenanceTracker:
    """General provenance tracker - first-class architecture"""
    
    def __init__(self):
        self.provenance_records: Dict[str, List[Dict]] = {}
    
    def get_patient_provenance(self, patient_id: str) -> Dict[str, Any]:
        """Get provenance for patient - GENERAL"""
        return {
            "patient_id": patient_id,
            "labels": ["MEASURED", "CLINICALLY_ENTERED", "IMAGE-DERIVED", "MODEL-INFERRED", "DEMO_DATA", "UNKNOWN"],
            "description": "Provenance first-class - every important data object indicates its origin",
            "examples": {
                "MEASURED": "Directly measured HR, temp, motion, GSR raw - quality, source generic analog Pulse Sensor, MPU6050, DS18B20",
                "CLINICALLY_ENTERED": "USER-ENTERED age, BMI, cycle, symptoms, glucose, BP - minimal collection",
                "IMAGE_DERIVED": "Cyst size, volume, morphology from ultrasound image - quality UNKNOWN by design unless computed",
                "MODEL_INFERRED": "Sleep regularity, circadian disruption, HRV derived, risk signals - confidence, limitations",
                "DEMO_DATA": "Demo providers, demo patients, synthetic - clearly labelled",
                "UNKNOWN": "If cannot reliably extract, return UNKNOWN, never invent"
            },
            "safety": "Never fabricate measurements, diagnoses, clinical validation, medical certainty. Never represent model inference as measurement. Never represent simulated data as real patient data.",
            "records": self.provenance_records.get(patient_id, [])
        }
    
    def track(self, patient_id: str, data_id: str, label: str, source: str = "", quality: float = 0.0):
        if patient_id not in self.provenance_records:
            self.provenance_records[patient_id] = []
        
        record = {
            "data_id": data_id,
            "patient_id": patient_id,
            "label": label,
            "source": source,
            "quality": quality,
            "timestamp": time.time()
        }
        self.provenance_records[patient_id].append(record)
        return record
