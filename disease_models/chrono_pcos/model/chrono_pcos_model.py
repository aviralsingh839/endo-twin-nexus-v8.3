"""
CHRONO-PCOS Disease Model - Implements DiseaseModel interface

Migrated from src/disease_modules/pcos.py
Now properly isolated as disease-specific model on general ENDO-TWIN platform.

General functionality (patient management, sensors, signal processing, etc.)
belongs in ENDO-TWIN Core.
PCOS-specific functionality belongs here.

This preserves original useful PCOS functionality while making architecture general.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
import time
import numpy as np

from src.endo_twin.models.disease_model_interface import (
    DiseaseModel, DiseaseModelManifest, DiseaseModelResult, DiseaseModelCategory
)
from ..manifest import CHRONO_PCOS_MANIFEST

# Import original PCOS logic - preserve working functionality
try:
    from src.disease_modules.pcos import PCOSModule as OriginalPCOSModule
    from src.data_models import SharedPhysiologicalFeatures
    from src.config import UserProfile
    ORIGINAL_AVAILABLE = True
except ImportError:
    ORIGINAL_AVAILABLE = False
    OriginalPCOSModule = None


class ChronoPCOSDiseaseModel(DiseaseModel):
    """
    CHRONO-PCOS - First disease-specific model on ENDO-TWIN platform.
    
    Implements DiseaseModel interface.
    Uses original PCOS module internally to preserve working functionality.
    
    ENDO-TWIN is general platform, CHRONO-PCOS is first disease-specific module.
    """
    
    def __init__(self):
        self._manifest = CHRONO_PCOS_MANIFEST
        self.original_module = None
        if ORIGINAL_AVAILABLE:
            try:
                self.original_module = OriginalPCOSModule()
            except:
                self.original_module = None
    
    @property
    def manifest(self) -> DiseaseModelManifest:
        return self._manifest
    
    def validate_input(self, features: Dict[str, Any], clinical_data: Optional[Dict] = None,
                      imaging_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Validate input for CHRONO-PCOS"""
        missing = []
        warnings = []
        
        # Check required features
        for req in self.manifest.required_features:
            if req not in features or features[req] is None:
                # Try alternative names
                alt_names = {
                    "heart_rate": ["hr", "hr_bpm", "heart_rate"],
                    "hrv_rmssd": ["hrv", "rmssd", "hrv_rmssd", "rmssd_ms"],
                    "activity_level": ["activity", "activity_level", "motion"],
                    "skin_temp_c": ["skin_temp", "temperature", "skin_temp_c", "temp_c"]
                }
                found = False
                for alt in alt_names.get(req, [req]):
                    if alt in features and features[alt] is not None:
                        found = True
                        break
                if not found:
                    missing.append(req)
        
        # Check quality
        quality = features.get("overall_quality", features.get("data_quality", 0.5))
        if isinstance(quality, (int, float)) and quality < 0.5:
            warnings.append(f"Low data quality: {quality}")
        
        # Clinical data checks
        if not clinical_data:
            warnings.append("No clinical data (age, BMI, cycle info) - reduces confidence")
        else:
            if "bmi" not in clinical_data and "usual_cycle_length_days" not in clinical_data:
                warnings.append("Missing BMI and cycle info")
        
        valid = len(missing) == 0
        if not valid:
            warnings.append(f"Missing required features: {missing}")
        
        return {
            "valid": valid or len(missing) <= 2,  # Allow partial with warnings
            "missing": missing,
            "warnings": warnings,
            "quality": quality if isinstance(quality, (int, float)) else 0.5
        }
    
    def analyze(self, features: Dict[str, Any], clinical_data: Optional[Dict] = None,
                imaging_data: Optional[Dict] = None, longitudinal_data: Optional[List] = None,
                baseline_data: Optional[Dict] = None, patient_id: str = "unknown") -> DiseaseModelResult:
        """
        Analyze with CHRONO-PCOS model.
        
        Preserves original PCOS functionality.
        Takes general physiological data, returns PCOS-specific interpretation.
        """
        
        # Convert general features dict to SharedPhysiologicalFeatures if original available
        if ORIGINAL_AVAILABLE and self.original_module:
            try:
                # Build SharedPhysiologicalFeatures from dict
                shared = SharedPhysiologicalFeatures()
                
                # Map general features to shared features
                shared.heart_rate = features.get("heart_rate", features.get("hr", features.get("hr_bpm")))
                shared.hrv_rmssd = features.get("hrv_rmssd", features.get("hrv", features.get("rmssd_ms")))
                shared.activity_level = features.get("activity_level", features.get("activity", 35))
                shared.skin_temp_c = features.get("skin_temp_c", features.get("skin_temp", features.get("temp_c", 32.5)))
                shared.sleep_duration_h = features.get("sleep_duration_h", 7.5)
                shared.sleep_regularity = features.get("sleep_regularity", 75)
                shared.circadian_stability_index = features.get("circadian_stability", 50)
                shared.gsr_tonic = features.get("gsr_tonic", 450)
                shared.stress_index = features.get("stress_index", 30)
                shared.circadian_disruption = features.get("circadian_disruption", 20)
                shared.temperature_rhythm_disruption = features.get("temperature_rhythm_disruption", 15)
                shared.low_activity_risk = features.get("low_activity_risk", 20)
                shared.autonomic_imbalance = features.get("autonomic_imbalance", 25)
                shared.overall_quality = features.get("overall_quality", features.get("data_quality", 0.85))
                shared.baseline_deviations = baseline_data or {}
                
                # Use original module to predict
                clinical = clinical_data or {}
                ultrasound = imaging_data or {}
                history = longitudinal_data or []
                
                result = self.original_module.predict(
                    shared=shared,
                    clinical=clinical,
                    ultrasound=ultrasound,
                    history=history
                )
                
                # Convert to general DiseaseModelResult
                return DiseaseModelResult(
                    model_name=self.manifest.name,
                    model_version=self.manifest.version,
                    patient_id=patient_id,
                    timestamp=time.time(),
                    signal=result.signal,
                    level=result.level,
                    confidence=result.confidence,
                    data_quality=result.data_quality,
                    clinical_validation=result.clinical_validation,
                    drivers=result.drivers,
                    explanation=result.explanation,
                    provenance=result.provenance,
                    limitations=result.limitations,
                    uncertainty={
                        "model_confidence": result.confidence,
                        "data_quality": result.data_quality,
                        "clinical_validation": result.clinical_validation,
                        "note": "Model output confidence, not clinical certainty"
                    },
                    extra=result.extra,
                    report_data={
                        "domain_scores": result.extra.get("domain_scores", {}),
                        "risk_percent": result.extra.get("risk_percent", 0),
                        "clinical_variables_present": result.extra.get("clinical_variables_present", False),
                        "ultrasound_present": result.extra.get("ultrasound_present", False)
                    }
                )
                
            except Exception as e:
                # Fallback if original module fails
                print(f"Original PCOS module failed: {e}, using fallback")
        
        # Fallback implementation - preserves functionality without original
        return self._fallback_analyze(features, clinical_data, imaging_data, longitudinal_data, baseline_data, patient_id)
    
    def _fallback_analyze(self, features: Dict[str, Any], clinical_data: Optional[Dict] = None,
                         imaging_data: Optional[Dict] = None, longitudinal_data: Optional[List] = None,
                         baseline_data: Optional[Dict] = None, patient_id: str = "unknown") -> DiseaseModelResult:
        """Fallback analysis if original module not available"""
        
        hr = features.get("heart_rate", features.get("hr", 72))
        hrv = features.get("hrv_rmssd", features.get("hrv", 48))
        activity = features.get("activity_level", features.get("activity", 35))
        temp = features.get("skin_temp_c", features.get("skin_temp", 32.5))
        quality = features.get("overall_quality", features.get("data_quality", 0.85))
        
        # Simple research risk logic - NOT diagnosis
        risk_score = 0
        
        # HRV low -> higher risk signal
        if hrv and hrv < 30:
            risk_score += 30
        elif hrv and hrv < 40:
            risk_score += 15
        
        # Activity low -> higher risk
        if activity and activity < 20:
            risk_score += 20
        
        # Clinical factors
        if clinical_data:
            bmi = clinical_data.get("bmi")
            if bmi and bmi > 25:
                risk_score += 20
            cycle_length = clinical_data.get("usual_cycle_length_days", clinical_data.get("cycle_length"))
            if cycle_length and (cycle_length < 21 or cycle_length > 35):
                risk_score += 25
            irregular = clinical_data.get("cycle_irregular")
            if irregular:
                risk_score += 25
        
        # Map to level
        if risk_score < 25:
            level = "low"
            signal = "pcos_associated_risk"
        elif risk_score < 50:
            level = "moderate"
            signal = "pcos_associated_risk"
        elif risk_score < 75:
            level = "elevated"
            signal = "elevated_pcos_associated_risk"
        else:
            level = "high"
            signal = "elevated_pcos_associated_risk"
        
        confidence = min(0.85, quality * 0.8 + 0.1) if isinstance(quality, (int, float)) else 0.5
        
        drivers = []
        if hrv and hrv < 40:
            drivers.append({"domain": "autonomic", "score": 100 - hrv, "contribution": f"HRV {hrv}ms low", "type": "physiological"})
        if clinical_data and clinical_data.get("cycle_irregular"):
            drivers.append({"domain": "cycle", "score": 60, "contribution": "Cycle irregularity", "type": "clinical"})
        if activity and activity < 30:
            drivers.append({"domain": "activity", "score": 100 - activity, "contribution": f"Activity {activity}% low", "type": "physiological"})
        
        if not drivers:
            drivers.append({"domain": "general", "score": 30, "contribution": "No strong drivers", "type": "physiological"})
        
        explanation = (
            f"PCOS-associated physiological and clinical risk signal: {risk_score:.1f}% ({level}). "
            f"Main drivers: {', '.join([d['domain'] for d in drivers[:2]])}. "
            f"This is a research estimate based on wearable physiology and clinical variables. "
            f"Not a diagnosis. Clinical evaluation required using Rotterdam criteria."
        )
        
        if imaging_data and imaging_data.get("cyst_size_mm"):
            explanation += f" Includes ultrasound cyst size {imaging_data.get('cyst_size_mm')}mm."
        
        provenance = {
            "clinical_variables": 0.4 if clinical_data else 0.1,
            "wearable_physiology": 0.35,
            "longitudinal": 0.15 if longitudinal_data and len(longitudinal_data) > 10 else 0.0,
            "ultrasound": 0.2 if imaging_data else 0.0,
            "metabolic": 0.1
        }
        
        return DiseaseModelResult(
            model_name=self.manifest.name,
            model_version=self.manifest.version,
            patient_id=patient_id,
            timestamp=time.time(),
            signal=signal,
            level=level,
            confidence=confidence,
            data_quality=quality if isinstance(quality, (int, float)) else 0.5,
            clinical_validation="NOT ESTABLISHED",
            drivers=drivers,
            explanation=explanation,
            provenance=provenance,
            limitations=self.manifest.limitations,
            uncertainty={
                "model_confidence": confidence,
                "data_quality": quality,
                "clinical_validation": "NOT ESTABLISHED",
                "note": "Model output confidence, not clinical certainty"
            },
            extra={
                "domain_scores": {"autonomic": 100 - (hrv or 50), "activity": 100 - (activity or 50)},
                "risk_percent": risk_score,
                "clinical_variables_present": bool(clinical_data),
                "ultrasound_present": bool(imaging_data)
            }
        )


# Factory function
def get_chrono_pcos_model() -> ChronoPCOSDiseaseModel:
    return ChronoPCOSDiseaseModel()


# For backward compatibility
ChronoPCOSModel = ChronoPCOSDiseaseModel
