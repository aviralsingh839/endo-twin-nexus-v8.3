"""
EndoTwinCore - Central orchestrator for ENDO-TWIN research framework
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from pathlib import Path
import time

from ..identity.patient_identity import PatientIdentity
from ..physiology.physiological_state import PhysiologicalState
from ..baseline.personal_baseline import PersonalBaselineEngine
from ..longitudinal.longitudinal_engine import LongitudinalEngine
from ..provenance.provenance import ProvenanceTracker, ProvenanceLabel
from ..uncertainty.uncertainty import UncertaintyModel
from ..registry.model_registry import ModelRegistry
from ..models.chrono_pcos import ChronoPCOSModel

@dataclass
class TwinConfig:
    version: str = "8.3+"
    data_dir: Optional[Path] = None
    enable_audit: bool = True
    enable_provenance: bool = True
    enable_uncertainty: bool = True

class EndoTwinCore:
    """
    ENDO-TWIN CORE - Research Framework
    
    CHRONO-PCOS is first disease-specific module.
    
    This is NOT a perfect simulation of human.
    It is computational representation:
    data → features → baseline → longitudinal state → multimodal model → inference → uncertainty
    
    Clearly states:
    - research prototype
    - not diagnostic
    - not medical advice
    - not clinically validated unless evidence exists
    - model limitations
    - sensor limitations
    - uncertainty
    - need for clinical validation
    """

    def __init__(self, config: Optional[TwinConfig] = None):
        self.config = config or TwinConfig()
        self.version = self.config.version
        
        # Core engines
        self.identity_engine = PatientIdentity()
        self.physiology_engine = PhysiologicalState()
        self.baseline_engine = PersonalBaselineEngine()
        self.longitudinal_engine = LongitudinalEngine()
        self.provenance_tracker = ProvenanceTracker()
        self.uncertainty_model = UncertaintyModel()
        self.model_registry = ModelRegistry()
        
        # Disease-specific models - CHRONO-PCOS is first
        self.chrono_pcos_model = ChronoPCOSModel()
        
        # Register CHRONO-PCOS as disease-specific module
        self.model_registry.register_model(
            name="CHRONO-PCOS",
            version="8.3+",
            type="disease_specific",
            description="PCOS/PCOD risk pre-screening research module - first ENDO-TWIN disease-specific implementation",
            capabilities=["pcos_risk_signal", "circadian_analysis", "autonomic_analysis", "metabolic_context", "longitudinal_tracking"],
            limitations="Research prototype, not clinically validated, not diagnostic, requires clinical evaluation, engineering validation only",
            provenance=ProvenanceLabel.MODEL_INFERRED
        )

    def get_patient_twin(self, patient_id: str) -> Dict[str, Any]:
        """
        Get complete twin representation for patient
        Scoped to patient_id - no cross-patient contamination
        """
        identity = self.identity_engine.get_identity(patient_id)
        physiology = self.physiology_engine.get_state(patient_id)
        baseline = self.baseline_engine.get_baseline(patient_id)
        longitudinal = self.longitudinal_engine.get_timeline(patient_id)
        provenance = self.provenance_tracker.get_patient_provenance(patient_id)
        uncertainty = self.uncertainty_model.get_patient_uncertainty(patient_id)
        
        return {
            "patient_id": patient_id,
            "identity": identity,
            "physiology": physiology,
            "baseline": baseline,
            "longitudinal": longitudinal,
            "provenance": provenance,
            "uncertainty": uncertainty,
            "models": {
                "chrono_pcos": self.chrono_pcos_model.get_patient_model_state(patient_id)
            },
            "version": self.version,
            "disclaimer": "Research / risk-screening output — not a medical diagnosis",
            "framework": "ENDO-TWIN research prototype - computational representation, not perfect simulation"
        }

    def get_architecture(self) -> Dict[str, Any]:
        """Return ENDO-TWIN architecture for documentation/website"""
        return {
            "name": "ENDO-TWIN CORE",
            "version": self.version,
            "description": "Research framework for personalized physiological modelling",
            "disclaimer": "NOT clinically validated universal human digital twin - research prototype",
            "layers": {
                "data_layer": ["patients", "sensor_sessions", "measurements", "features", "clinical_records", "symptoms", "cycle_events", "ultrasound_studies", "ultrasound_features", "model_runs", "model_versions", "reports", "notes", "providers", "audit_events"],
                "twin_engine": ["identity", "physiology", "baseline", "longitudinal", "provenance", "uncertainty"],
                "ai_ml_layer": ["models", "registry", "training", "inference", "explainability"]
            },
            "disease_specific": {
                "chrono_pcos": {
                    "status": "IMPLEMENTED - first disease-specific module",
                    "capabilities": ["pcos_risk_signal", "circadian_analysis", "autonomic_analysis", "metabolic_context", "longitudinal_tracking"],
                    "version": "8.3+"
                },
                "future": {
                    "status": "CONCEPT - not implemented",
                    "examples": ["ENDO-TWIN NEXUS direction", "other endocrine research modules"],
                    "note": "Do not claim future functionality is already implemented"
                }
            },
            "flow": "data → features → baseline → longitudinal state → multimodal model → inference → uncertainty",
            "provenance_labels": ["MEASURED", "CLINICALLY_ENTERED", "IMAGE_DERIVED", "MODEL_INFERRED", "DEMO_DATA", "UNKNOWN"],
            "safety": "research prototype, not diagnostic, not medical advice, not clinically validated unless evidence exists"
        }
