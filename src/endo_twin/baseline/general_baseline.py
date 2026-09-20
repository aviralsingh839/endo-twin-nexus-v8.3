"""
General Baseline Engine - No PCOS assumptions
Learns what is normal for individual first.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import time

@dataclass
class GeneralBaseline:
    patient_id: str = ""
    feature_name: str = ""
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    std_value: Optional[float] = None
    confidence: float = 0.0
    observations: int = 0
    min_observations: int = 30

class GeneralBaselineEngine:
    """General baseline engine - learns what is normal for individual"""
    
    def __init__(self):
        self.baselines: Dict[str, Dict[str, GeneralBaseline]] = {}
    
    def get_baseline(self, patient_id: str) -> Dict[str, Any]:
        """Get baseline for patient - GENERAL"""
        if patient_id in self.baselines:
            patient_baselines = self.baselines[patient_id]
            return {
                "patient_id": patient_id,
                "has_baseline": len(patient_baselines) > 0,
                "baselines": {k: {"mean": v.mean_value, "median": v.median_value, "std": v.std_value, "confidence": v.confidence} for k, v in patient_baselines.items()},
                "description": "Personal baseline - learns what is normal for individual first, not population average",
                "scenarios": {
                    "stable": "LOW CHANGE SIGNAL - within normal variation",
                    "gradual": "EARLY CHANGE SIGNAL - slowly moves away",
                    "persistent": "PERSISTENT MULTIMODAL SIGNAL - multiple related signals abnormal",
                    "temporary": "TEMPORARY EVENT - brief change then return",
                    "sensor_failure": "LOW SENSOR CONFIDENCE - must not be interpreted as physiological abnormality",
                    "recovery": "RECOVERY TREND - abnormal returns toward baseline"
                }
            }
        return {
            "patient_id": patient_id,
            "has_baseline": False,
            "baselines": {},
            "description": "No baseline yet - need minimum observations",
            "min_observations": 30
        }
    
    def update_baseline(self, patient_id: str, feature_name: str, values: List[float]):
        if patient_id not in self.baselines:
            self.baselines[patient_id] = {}
        
        import numpy as np
        baseline = GeneralBaseline(
            patient_id=patient_id,
            feature_name=feature_name,
            mean_value=float(np.mean(values)) if values else None,
            median_value=float(np.median(values)) if values else None,
            std_value=float(np.std(values)) if values else None,
            confidence=min(1.0, len(values) / 30),
            observations=len(values)
        )
        self.baselines[patient_id][feature_name] = baseline
        return baseline
