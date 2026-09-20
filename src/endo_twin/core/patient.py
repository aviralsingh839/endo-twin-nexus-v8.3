"""
ENDO-TWIN Core - General Patient Model

No PCOS-specific assumptions.
General physiological monitoring for any condition.

Patient is general - supports any disease model via disease_model_id.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


@dataclass
class Patient:
    """
    General patient - supports any disease model.
    
    No PCOS-specific fields in core.
    Disease-specific data stored via extensions or disease_models.
    """
    patient_id: str  # Stable ID like CP-0001, DEMO-001, PXXXXX
    anonymous_id: str  # PXXXXX
    display_name: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_demo: bool = False
    is_archived: bool = False
    
    # Minimal general demographics - USER-ENTERED, not diagnostic
    age_years: Optional[float] = None
    bmi: Optional[float] = None
    sex: Optional[str] = None  # optional, general
    
    # General metadata
    notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Disease model associations - which disease models are enabled for this patient
    enabled_disease_models: List[str] = field(default_factory=list)
    
    # General extensions - disease-specific data stored here or in separate tables
    # referencing patient_id and disease_model_id
    extensions: Dict[str, Any] = field(default_factory=dict)
    
    def enable_disease_model(self, model_name: str):
        """Enable a disease model for this patient"""
        if model_name not in self.enabled_disease_models:
            self.enabled_disease_models.append(model_name)
    
    def disable_disease_model(self, model_name: str):
        """Disable a disease model for this patient"""
        if model_name in self.enabled_disease_models:
            self.enabled_disease_models.remove(model_name)
    
    def is_disease_model_enabled(self, model_name: str) -> bool:
        return model_name in self.enabled_disease_models
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "anonymous_id": self.anonymous_id,
            "display_name": self.display_name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_demo": self.is_demo,
            "is_archived": self.is_archived,
            "age_years": self.age_years,
            "bmi": self.bmi,
            "sex": self.sex,
            "notes": self.notes,
            "tags": self.tags,
            "enabled_disease_models": self.enabled_disease_models,
            "extensions": self.extensions
        }
    
    @classmethod
    def create(cls, display_name: str, age_years: Optional[float] = None, 
               bmi: Optional[float] = None, is_demo: bool = False) -> Patient:
        """Create new patient with stable ID"""
        patient_id = f"CP-{uuid.uuid4().hex[:4].upper()}" if not is_demo else f"DEMO-{uuid.uuid4().hex[:3].upper()}"
        anonymous_id = f"P{uuid.uuid4().hex[:5].upper()}"
        return cls(
            patient_id=patient_id,
            anonymous_id=anonymous_id,
            display_name=display_name,
            age_years=age_years,
            bmi=bmi,
            is_demo=is_demo
        )


@dataclass
class PatientIdentity:
    """
    Patient identity management - general.
    Stable IDs, patient-scoped queries, no cross-patient contamination.
    """
    patients: Dict[str, Patient] = field(default_factory=dict)
    
    def create_patient(self, display_name: str, age_years: Optional[float] = None,
                      bmi: Optional[float] = None, is_demo: bool = False,
                      patient_id: Optional[str] = None) -> Patient:
        if patient_id and patient_id in self.patients:
            raise ValueError(f"Patient {patient_id} already exists")
        
        if patient_id:
            # Use provided ID (e.g., DEMO-001)
            patient = Patient(
                patient_id=patient_id,
                anonymous_id=f"P{uuid.uuid4().hex[:5].upper()}",
                display_name=display_name,
                age_years=age_years,
                bmi=bmi,
                is_demo=is_demo
            )
        else:
            patient = Patient.create(display_name, age_years, bmi, is_demo)
        
        self.patients[patient.patient_id] = patient
        return patient
    
    def get_patient(self, patient_id: str) -> Optional[Patient]:
        return self.patients.get(patient_id)
    
    def list_patients(self, include_archived: bool = False, include_demo: bool = True) -> List[Patient]:
        patients = list(self.patients.values())
        if not include_archived:
            patients = [p for p in patients if not p.is_archived]
        if not include_demo:
            patients = [p for p in patients if not p.is_demo]
        return patients
    
    def search_patients(self, query: str) -> List[Patient]:
        query_lower = query.lower()
        return [
            p for p in self.patients.values()
            if query_lower in p.patient_id.lower() or 
               query_lower in p.display_name.lower() or
               query_lower in p.anonymous_id.lower()
        ]
    
    def archive_patient(self, patient_id: str):
        if patient_id in self.patients:
            self.patients[patient_id].is_archived = True
            self.patients[patient_id].updated_at = datetime.now()
    
    def get_identity(self, patient_id: str) -> Optional[Dict[str, Any]]:
        patient = self.get_patient(patient_id)
        return patient.to_dict() if patient else None
