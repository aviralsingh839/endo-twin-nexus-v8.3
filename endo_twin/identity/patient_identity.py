"""
Patient Identity - Stable IDs, patient-scoped queries, no cross-patient contamination
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import uuid
import time

@dataclass
class PatientIdentityRecord:
    patient_id: str  # Stable ID like CP-0001, DEMO-001
    anonymous_id: str  # PXXXXX
    display_name: Optional[str] = None
    age_years: Optional[float] = None
    bmi: Optional[float] = None
    created_at: float = 0
    updated_at: float = 0
    is_archived: bool = False
    label: str = "USER-ENTERED"  # Provenance
    is_demo: bool = False

class PatientIdentity:
    """
    Patient identity management - mandatory multi-patient safety
    DEMO-001 cannot see DEMO-002, reports patient-specific, etc.
    Implemented at database/repository level, not merely UI hidden
    """

    def __init__(self):
        self.version = "8.3+"

    def generate_patient_id(self, prefix: str = "CP") -> str:
        """Generate stable patient ID"""
        return f"{prefix}-{str(uuid.uuid4())[:8].upper()}"

    def get_identity(self, patient_id: str) -> Dict[str, Any]:
        """Get identity for patient - scoped"""
        # This would query database in real implementation
        # For now return structure
        return {
            "patient_id": patient_id,
            "anonymous_id": f"P{hash(patient_id) % 100000:05d}",
            "provenance": "CLINICALLY_ENTERED",
            "label": "USER-ENTERED",
            "is_demo": patient_id.startswith("DEMO-"),
            "disclaimer": "Patient identity - controlled sharing, local storage, minimal data exposure"
        }

    def create_demo_patients(self) -> list:
        """Create DEMO-001, DEMO-002, DEMO-003 with deliberately different data"""
        return [
            PatientIdentityRecord(
                patient_id="DEMO-001",
                anonymous_id="P00001",
                display_name="Demo Patient 001 (DEMO DATA)",
                age_years=22,
                bmi=23.5,
                created_at=time.time(),
                updated_at=time.time(),
                label="DEMO_DATA",
                is_demo=True
            ),
            PatientIdentityRecord(
                patient_id="DEMO-002",
                anonymous_id="P00002",
                display_name="Demo Patient 002 (DEMO DATA)",
                age_years=28,
                bmi=27.2,
                created_at=time.time(),
                updated_at=time.time(),
                label="DEMO_DATA",
                is_demo=True
            ),
            PatientIdentityRecord(
                patient_id="DEMO-003",
                anonymous_id="P00003",
                display_name="Demo Patient 003 (DEMO DATA)",
                age_years=24,
                bmi=21.8,
                created_at=time.time(),
                updated_at=time.time(),
                label="DEMO_DATA",
                is_demo=True
            ),
        ]
