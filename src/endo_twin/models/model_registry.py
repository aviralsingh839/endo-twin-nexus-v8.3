"""
Model Registry - General Platform

Manages all models:
- General Physiological Models (baseline, longitudinal, etc.)
- Personal Baseline Models
- Longitudinal Models
- Disease Models (CHRONO-PCOS first, future models)

ENDO-TWIN Core does NOT depend directly on CHRONO-PCOS.
Disease models register themselves via this registry.
Core application works even when no disease model selected.
Adding dummy future model possible without rewriting core.

Structure:
AI & Models
├── General Physiological Models
├── Personal Baseline Models
├── Longitudinal Models
└── Disease Models
    └── CHRONO-PCOS (first)
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, field
from pathlib import Path
import json
import time

from .disease_model_interface import DiseaseModel, DiseaseModelManifest, DiseaseModelCategory
from .plugin_discovery import discover_disease_models


@dataclass
class GeneralModelInfo:
    """Info for general physiological models (not disease-specific)"""
    name: str
    version: str
    display_name: str
    description: str
    category: str  # baseline, longitudinal, physiological, etc.
    capabilities: List[str] = field(default_factory=list)
    limitations: str = ""
    is_available: bool = True


class ModelRegistry:
    """
    General model registry - manages both general and disease-specific models.
    
    General models are built-in to ENDO-TWIN Core.
    Disease models are plugins that implement DiseaseModel interface.
    """
    
    def __init__(self):
        self.general_models: Dict[str, GeneralModelInfo] = {}
        self.disease_models: Dict[str, DiseaseModel] = {}
        self.disease_model_classes: Dict[str, Type[DiseaseModel]] = {}
        
        # Register general models
        self._register_general_models()
    
    def _register_general_models(self):
        """Register general physiological models that are part of ENDO-TWIN Core"""
        
        # Personal Baseline Models
        self.register_general_model(GeneralModelInfo(
            name="personal_baseline",
            version="8.3+",
            display_name="Personal Baseline Engine",
            description="Learns what is normal for individual first - mean, median, std, MAD, rolling, confidence, min obs, circadian context",
            category="baseline",
            capabilities=["mean", "median", "std", "MAD", "rolling_baseline", "confidence", "circadian_context", "deviation_detection"],
            limitations="Requires minimum observations, baseline period needed"
        ))
        
        # Longitudinal Models
        self.register_general_model(GeneralModelInfo(
            name="longitudinal",
            version="8.3+",
            display_name="Longitudinal Engine",
            description="Rolling windows, persistence, trend, change-point, recovery, missing handling, confidence - detects persistent changes not one abnormal reading",
            category="longitudinal",
            capabilities=["rolling_windows", "persistence", "trend", "change_point", "recovery", "6_scenarios"],
            limitations="Requires history, not single measurement"
        ))
        
        # Physiological Models
        self.register_general_model(GeneralModelInfo(
            name="physiological_state",
            version="8.3+",
            display_name="Physiological State",
            description="Computational representation of physiological state - NOT perfect simulation, data → features → baseline → longitudinal state",
            category="physiological",
            capabilities=["hr", "hrv", "activity", "temperature", "gsr", "sleep_circadian", "autonomic", "metabolic_context"],
            limitations="Computational representation, not perfect simulation"
        ))
        
        # Signal Processing
        self.register_general_model(GeneralModelInfo(
            name="signal_processing",
            version="8.3+",
            display_name="Signal Processing",
            description="Filtering, baseline removal, artifact detection, quality control, missing handling - 20Hz $CP2 CRC XOR",
            category="signal",
            capabilities=["filtering", "baseline_removal", "artifact_detection", "quality_control", "missing_handling"],
            limitations="Quality affected by motion, pressure, skin tone"
        ))
        
        # Feature Extraction
        self.register_general_model(GeneralModelInfo(
            name="feature_extraction",
            version="8.3+",
            display_name="Feature Extraction",
            description="Established MEASURED HR, temp, motion, GSR, derived HRV RMSSD/SDNN/pNN50, experimental circadian, autonomic, metabolic",
            category="features",
            capabilities=["hr", "hrv_rmssd", "hrv_sdnn", "hrv_pnn50", "activity", "temperature", "gsr_tonic", "gsr_phasic", "sleep_regularity"],
            limitations="PPG-derived HRV less accurate than ECG"
        ))
        
        # Chrono-Metabolic (general concept, PCOS interpretation is disease-specific)
        self.register_general_model(GeneralModelInfo(
            name="chrono_metabolic",
            version="8.3+",
            display_name="Chrono-Metabolic Fingerprinting",
            description="Combines circadian, autonomic, variability, activity, temp, metabolic, longitudinal into fingerprint with provenance and explainability",
            category="fingerprint",
            capabilities=["circadian", "autonomic", "variability", "activity", "temperature", "metabolic", "longitudinal", "multisystem"],
            limitations="Experimental research, not diagnosis, requires validation"
        ))
    
    def discover_external_disease_models(self) -> List[str]:
        """Discover optional packaged disease-model factories without hard dependencies."""
        registered = []
        for candidate in discover_disease_models():
            try:
                model = candidate() if isinstance(candidate, type) else candidate()
                if isinstance(model, DiseaseModel):
                    self.register_disease_model(model)
                    registered.append(model.name)
            except Exception:
                # A broken optional plugin must never prevent ENDO-TWIN from launching.
                continue
        return registered

    def register_general_model(self, model_info: GeneralModelInfo):
        """Register a general physiological model"""
        self.general_models[model_info.name] = model_info
    
    def register_disease_model(self, model: DiseaseModel):
        """Register a disease-specific model instance"""
        self.disease_models[model.name] = model
        self.disease_model_classes[model.name] = model.__class__
    
    def register_disease_model_class(self, model_class: Type[DiseaseModel]):
        """Register a disease model class (will be instantiated when needed)"""
        # Create temporary instance to get manifest
        try:
            temp_instance = model_class()
            self.disease_model_classes[temp_instance.name] = model_class
            self.disease_models[temp_instance.name] = temp_instance
        except Exception as e:
            print(f"Failed to register disease model class {model_class}: {e}")
    
    def get_general_model(self, name: str) -> Optional[GeneralModelInfo]:
        return self.general_models.get(name)
    
    def get_disease_model(self, name: str) -> Optional[DiseaseModel]:
        return self.disease_models.get(name)
    
    def list_general_models(self) -> List[GeneralModelInfo]:
        return list(self.general_models.values())
    
    def list_disease_models(self) -> List[DiseaseModel]:
        return list(self.disease_models.values())
    
    def list_all_models(self) -> Dict[str, List]:
        return {
            "general": self.list_general_models(),
            "disease": self.list_disease_models()
        }
    
    def get_available_disease_models(self) -> List[DiseaseModel]:
        """Get only available disease models"""
        return [m for m in self.disease_models.values() if m.is_available()]
    
    def get_disease_models_by_category(self, category: DiseaseModelCategory) -> List[DiseaseModel]:
        return [m for m in self.disease_models.values() if m.manifest.category == category]
    
    def is_disease_model_available(self, name: str) -> bool:
        model = self.get_disease_model(name)
        return model.is_available() if model else False
    
    def get_registry_info(self) -> Dict[str, Any]:
        """Get complete registry info for UI display"""
        return {
            "general_models": [
                {
                    "name": m.name,
                    "version": m.version,
                    "display_name": m.display_name,
                    "description": m.description,
                    "category": m.category,
                    "capabilities": m.capabilities,
                    "limitations": m.limitations,
                    "is_available": m.is_available
                }
                for m in self.general_models.values()
            ],
            "disease_models": [
                {
                    "name": m.name,
                    "version": m.version,
                    "display_name": m.display_name,
                    "description": m.description,
                    "category": m.manifest.category.value,
                    "capabilities": m.manifest.capabilities,
                    "limitations": m.manifest.limitations,
                    "clinical_validation": m.manifest.clinical_validation,
                    "required_features": m.manifest.required_features,
                    "is_available": m.is_available()
                }
                for m in self.disease_models.values()
            ],
            "summary": {
                "total_general": len(self.general_models),
                "total_disease": len(self.disease_models),
                "available_disease": len(self.get_available_disease_models()),
                "first_disease_model": "CHRONO-PCOS" if "chrono_pcos" in self.disease_models or "pcos_reproductive_metabolic" in self.disease_models else "none"
            }
        }
    
    def analyze_with_disease_model(self, model_name: str, features: Dict[str, Any], 
                                   clinical_data: Optional[Dict] = None,
                                   imaging_data: Optional[Dict] = None,
                                   longitudinal_data: Optional[List] = None,
                                   baseline_data: Optional[Dict] = None,
                                   patient_id: str = "unknown") -> Optional[Any]:
        """Analyze with specific disease model"""
        model = self.get_disease_model(model_name)
        if not model:
            return None
        
        validation = model.validate_input(features, clinical_data, imaging_data)
        if not validation.get("valid", False):
            # Still analyze but with low quality warning
            pass
        
        result = model.analyze(features, clinical_data, imaging_data, longitudinal_data, baseline_data, patient_id)
        return result
    
    def get_disease_model_manifests(self) -> List[DiseaseModelManifest]:
        """Get manifests for all disease models"""
        return [m.manifest for m in self.disease_models.values()]


# Global registry instance
GLOBAL_MODEL_REGISTRY = ModelRegistry()


def get_global_registry() -> ModelRegistry:
    return GLOBAL_MODEL_REGISTRY
