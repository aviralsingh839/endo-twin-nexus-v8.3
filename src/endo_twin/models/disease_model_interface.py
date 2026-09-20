"""
DiseaseModel Interface - General Platform

ENDO-TWIN is general personalized physiological modelling platform.
CHRONO-PCOS is first disease-specific model built on platform.

This interface allows future disease models to plug into same platform
without rewriting core application.

General functionality belongs in ENDO-TWIN Core.
Disease-specific functionality belongs in disease-specific model.

Interface:
- name
- version
- description
- required_features
- analyze()
- explain()
- generate_report()
- validate_input()
- get_uncertainty()
- get_limitations()
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class DiseaseModelCategory(str, Enum):
    ENDOCRINE = "endocrine"
    CARDIOMETABOLIC = "cardiometabolic"
    SLEEP = "sleep"
    AUTONOMIC = "autonomic"
    RESPIRATORY = "respiratory"
    GENERAL = "general"
    RESEARCH = "research"


@dataclass
class DiseaseModelManifest:
    """Manifest for disease model - what it is, what it needs, what it does"""
    name: str
    version: str
    display_name: str
    description: str
    category: DiseaseModelCategory
    author: str = "ENDO-TWIN Research"
    required_features: List[str] = None
    optional_features: List[str] = None
    capabilities: List[str] = None
    limitations: str = ""
    clinical_validation: str = "NOT ESTABLISHED"
    data_requirements: str = ""
    version_history: List[Dict] = None
    
    def __post_init__(self):
        if self.required_features is None:
            self.required_features = []
        if self.optional_features is None:
            self.optional_features = []
        if self.capabilities is None:
            self.capabilities = []
        if self.version_history is None:
            self.version_history = []


@dataclass
class DiseaseModelResult:
    """Result from disease model analysis - general structure"""
    model_name: str
    model_version: str
    patient_id: str
    timestamp: float
    signal: str  # e.g., "pcos_associated_risk", "elevated", "low"
    level: str  # low/moderate/elevated/high
    confidence: float  # 0-1, model output confidence, not clinical certainty
    data_quality: float  # 0-1, quality of input data
    clinical_validation: str  # NOT ESTABLISHED unless evidence
    drivers: List[Dict]  # what drove the result
    explanation: str  # human readable explanation
    provenance: Dict[str, float]  # where data came from
    limitations: str
    uncertainty: Dict[str, Any] = None
    extra: Dict[str, Any] = None
    report_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.uncertainty is None:
            self.uncertainty = {}
        if self.extra is None:
            self.extra = {}
        if self.report_data is None:
            self.report_data = {}


class DiseaseModel(ABC):
    """
    Base class for all disease-specific models.
    
    ENDO-TWIN Core should NOT depend directly on any specific disease model.
    Disease models implement this interface and are discovered via registry.
    
    Example:
    - CHRONO-PCOS implements DiseaseModel
    - Future models implement same interface
    - Core application works even when no disease model selected
    - Adding dummy future model possible without rewriting core
    """
    
    @property
    @abstractmethod
    def manifest(self) -> DiseaseModelManifest:
        """Return manifest describing the model"""
        pass
    
    @property
    def name(self) -> str:
        return self.manifest.name
    
    @property
    def version(self) -> str:
        return self.manifest.version
    
    @property
    def display_name(self) -> str:
        return self.manifest.display_name
    
    @property
    def description(self) -> str:
        return self.manifest.description
    
    @property
    def required_features(self) -> List[str]:
        return self.manifest.required_features
    
    @property
    def optional_features(self) -> List[str]:
        return self.manifest.optional_features
    
    @abstractmethod
    def validate_input(self, features: Dict[str, Any], clinical_data: Optional[Dict] = None, 
                      imaging_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Validate input data for this disease model.
        Returns: {valid: bool, missing: [], warnings: [], quality: float}
        """
        pass
    
    @abstractmethod
    def analyze(self, features: Dict[str, Any], clinical_data: Optional[Dict] = None,
                imaging_data: Optional[Dict] = None, longitudinal_data: Optional[List] = None,
                baseline_data: Optional[Dict] = None, patient_id: str = "unknown") -> DiseaseModelResult:
        """
        Analyze data and return disease-specific result.
        
        This is the main entry point - takes general physiological data
        and returns disease-specific interpretation.
        
        Must NOT claim diagnosis - returns research risk signal.
        Must preserve provenance.
        Must handle missing data gracefully.
        """
        pass
    
    def explain(self, result: DiseaseModelResult) -> str:
        """Explain result in human understandable language"""
        return result.explanation
    
    def generate_report(self, result: DiseaseModelResult, include_disclaimer: bool = True) -> Dict[str, Any]:
        """Generate report data for this disease model"""
        report = {
            "model_name": result.model_name,
            "model_version": result.model_version,
            "display_name": self.display_name,
            "patient_id": result.patient_id,
            "timestamp": result.timestamp,
            "signal": result.signal,
            "level": result.level,
            "confidence": result.confidence,
            "data_quality": result.data_quality,
            "clinical_validation": result.clinical_validation,
            "drivers": result.drivers,
            "explanation": result.explanation,
            "provenance": result.provenance,
            "limitations": result.limitations,
            "uncertainty": result.uncertainty,
            "extra": result.extra
        }
        if include_disclaimer:
            report["disclaimer"] = "Research / risk-screening output — not a medical diagnosis. Requires clinical evaluation."
            report["framework"] = "ENDO-TWIN - General platform, CHRONO-PCOS is first disease-specific module"
        return report
    
    def get_uncertainty(self, result: DiseaseModelResult) -> Dict[str, Any]:
        """Get uncertainty information for result"""
        return result.uncertainty or {
            "model_confidence": result.confidence,
            "data_quality": result.data_quality,
            "note": "Model output confidence, not clinical certainty",
            "limitations": result.limitations
        }
    
    def get_limitations(self) -> str:
        """Get limitations of this disease model"""
        return self.manifest.limitations
    
    def get_capabilities(self) -> List[str]:
        """Get capabilities of this disease model"""
        return self.manifest.capabilities
    
    def is_available(self) -> bool:
        """Check if model is available (e.g., has required dependencies)"""
        return True
    
    def get_version_info(self) -> Dict[str, Any]:
        """Get version info for display"""
        return {
            "name": self.manifest.name,
            "version": self.manifest.version,
            "display_name": self.manifest.display_name,
            "description": self.manifest.description,
            "category": self.manifest.category.value,
            "capabilities": self.manifest.capabilities,
            "limitations": self.manifest.limitations,
            "clinical_validation": self.manifest.clinical_validation,
            "required_features": self.manifest.required_features,
            "optional_features": self.manifest.optional_features
        }
