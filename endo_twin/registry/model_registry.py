"""
Model Registry - Model name, version, dataset version, training date, features, target, metrics, validation strategy, limitations, model approval, rollback, inference, uncertainty
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import time

@dataclass
class ModelVersion:
    name: str
    version: str
    type: str  # disease_specific, general, experimental
    description: str
    capabilities: List[str]
    limitations: str
    dataset_version: str = "PCOS_data.csv 541 rows + synthetic cohort 10 subjects 30 days 6 scenarios 60 days wrist_ppg SYNTHETIC"
    training_date: str = "2026-09-19"
    features: List[str] = None
    target: str = ""
    metrics: Dict[str, Any] = None
    validation_strategy: str = "Subject-level split not row-level avoid leakage"
    provenance: str = "MODEL_INFERRED"
    is_approved: bool = False
    created_at: float = 0

    def __post_init__(self):
        if self.features is None:
            self.features = ["HRV RMSSD", "activity level", "skin temp"]
        if self.metrics is None:
            self.metrics = {"status": "NOT ESTABLISHED - engineering validation only, never fabricate percentages if insufficient state insufficient"}
        if self.created_at == 0:
            self.created_at = time.time()

class ModelRegistry:
    """
    Model registry - model name, version, dataset version, training date, features, target, metrics, validation strategy, limitations, model approval, rollback, inference, uncertainty
    Never invent metrics if no trained model exists show Model not trained rather than fake accuracy
    """

    def __init__(self):
        self.version = "8.3+"
        self.models: Dict[str, List[ModelVersion]] = {}

    def register_model(self, name: str, version: str, type: str, description: str, capabilities: List[str], limitations: str, provenance: str = "MODEL_INFERRED", dataset_version: str = None, features: List[str] = None, target: str = "", metrics: Dict = None) -> ModelVersion:
        model = ModelVersion(
            name=name,
            version=version,
            type=type,
            description=description,
            capabilities=capabilities,
            limitations=limitations,
            provenance=provenance,
            dataset_version=dataset_version or "PCOS_data.csv 541 rows + synthetic cohort 10 subjects 30 days 6 scenarios 60 days wrist_ppg SYNTHETIC",
            features=features,
            target=target,
            metrics=metrics
        )
        
        if name not in self.models:
            self.models[name] = []
        self.models[name].append(model)
        
        return model

    def get_model(self, name: str, version: str = None) -> Optional[ModelVersion]:
        if name not in self.models:
            return None
        if version is None:
            # Return latest
            return sorted(self.models[name], key=lambda m: m.created_at, reverse=True)[0]
        for m in self.models[name]:
            if m.version == version:
                return m
        return None

    def list_models(self) -> Dict[str, List[Dict]]:
        result = {}
        for name, versions in self.models.items():
            result[name] = [
                {
                    "name": m.name,
                    "version": m.version,
                    "type": m.type,
                    "description": m.description,
                    "capabilities": m.capabilities,
                    "limitations": m.limitations,
                    "dataset_version": m.dataset_version,
                    "training_date": m.training_date,
                    "features": m.features,
                    "target": m.target,
                    "metrics": m.metrics,
                    "validation_strategy": m.validation_strategy,
                    "is_approved": m.is_approved,
                    "provenance": m.provenance
                }
                for m in versions
            ]
        return result

    def approve_model(self, name: str, version: str) -> bool:
        model = self.get_model(name, version)
        if model:
            model.is_approved = True
            return True
        return False

    def rollback_model(self, name: str, to_version: str) -> bool:
        # Rollback to previous version
        model = self.get_model(name, to_version)
        if model:
            # In real implementation, would set active version
            return True
        return False

    def get_registry_info(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "models": self.list_models(),
            "safety": "Never invent metrics if no trained model exists show Model not trained rather than fake accuracy, never hide uncertainty manufacture confidence training results",
            "disclaimer": "Model registry - model name, version, dataset version, training date, features, target, metrics, validation strategy, limitations, model approval, rollback, inference, uncertainty"
        }
