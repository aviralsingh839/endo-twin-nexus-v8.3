"""
Physiological State - Represents current physiological state with provenance and uncertainty
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from ..provenance.provenance import ProvenanceLabel

@dataclass
class PhysiologicalMeasurement:
    name: str
    value: Any
    unit: str
    timestamp: float
    quality: float  # 0-1
    provenance: ProvenanceLabel
    source: str
    limitations: str = ""
    confidence: Optional[float] = None

class PhysiologicalState:
    """
    Physiological representation - part of ENDO-TWIN
    
    NOT perfect simulation, computational representation
    data → features → baseline → longitudinal state → multimodal model → inference → uncertainty
    """

    def __init__(self):
        self.version = "8.3+"

    def get_state(self, patient_id: str) -> Dict[str, Any]:
        """Get physiological state scoped to patient"""
        return {
            "patient_id": patient_id,
            "measurements": {
                "hr": {
                    "value": "MEASURED - requires actual sensor data",
                    "provenance": ProvenanceLabel.MEASURED.value if hasattr(ProvenanceLabel, 'MEASURED') else "MEASURED",
                    "source": "MAX30102 PPG IR+RED",
                    "quality": "0-1 per channel",
                    "limitations": "Requires good quality PPG, motion artifacts affect"
                },
                "hrv": {
                    "value": "DERIVED - RMSSD, SDNN, pNN50 from HR time series",
                    "provenance": "DERIVED_FEATURE",
                    "source": "PPG-derived HRV",
                    "quality": "0.85 typical",
                    "limitations": "PPG-derived HRV less accurate than ECG"
                },
                "temperature": {
                    "value": "MEASURED - skin temp",
                    "provenance": "MEASURED",
                    "source": "DS18B20",
                    "quality": "0.88 typical",
                    "limitations": "Skin temp not core temp, affected environment"
                },
                "motion": {
                    "value": "MEASURED - ax_g ay_g az_g gx_dps gy_dps gz_dps motion_index activity_level",
                    "provenance": "MEASURED",
                    "source": "MPU6050",
                    "quality": "0.8 typical",
                    "limitations": "Wrist activity not whole-body calorimetry"
                },
                "gsr": {
                    "value": "MEASURED + DERIVED - tonic lowpass, phasic highpass",
                    "provenance": "MEASURED",
                    "source": "GSR sensor",
                    "quality": "0.7-0.9",
                    "limitations": "Affected by environment, motion"
                }
            },
            "provenance": "MEASURED, DERIVED, MODEL-INFERRED clearly distinguished",
            "disclaimer": "Physiological state - computational representation, not perfect simulation"
        }
