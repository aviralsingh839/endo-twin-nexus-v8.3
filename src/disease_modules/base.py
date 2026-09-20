"""Disease Module API for CHRONO-TWIN NEXUS V8.3.

Consistent interface:
DiseaseModule
  name
  version
  required_features
  optional_features
  predict()
  explain()
  confidence()
  limitations()

Each module returns structured information, never 'DISEASE DETECTED'.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import time

from src.data_models import SharedPhysiologicalFeatures, DiseaseModuleResult


class DiseaseModule(ABC):
    """Base class for all disease-specific research modules."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @property
    @abstractmethod
    def required_features(self) -> List[str]:
        """Features that must be present for a reliable signal."""
        pass

    @property
    def optional_features(self) -> List[str]:
        """Features that improve confidence if present."""
        return []

    @abstractmethod
    def predict(self, shared: SharedPhysiologicalFeatures, clinical: Optional[Dict] = None,
                ultrasound: Optional[Dict] = None, history: Optional[List] = None) -> DiseaseModuleResult:
        """Generate a research risk signal from shared features."""
        pass

    def explain(self, result: DiseaseModuleResult) -> str:
        return result.explanation

    def confidence(self, shared: SharedPhysiologicalFeatures, result: Optional[DiseaseModuleResult] = None) -> float:
        """Compute model confidence based on data availability and quality."""
        if not shared:
            return 0.0
        present_required = sum(1 for f in self.required_features if getattr(shared, f, None) is not None)
        total_required = len(self.required_features) if self.required_features else 1
        coverage = present_required / total_required

        present_optional = sum(1 for f in self.optional_features if getattr(shared, f, None) is not None)
        total_optional = len(self.optional_features) if self.optional_features else 1
        optional_coverage = present_optional / total_optional if self.optional_features else 0.5

        quality = shared.overall_quality if hasattr(shared, 'overall_quality') else 0.5

        conf = 0.5 * coverage + 0.2 * optional_coverage + 0.3 * quality
        return float(max(0.0, min(1.0, conf)))

    def limitations(self) -> str:
        return (
            "Research-only signal. Not a diagnosis. Requires clinical evaluation. "
            "Model not clinically validated for diagnostic use."
        )

    def _level_from_score(self, score: float) -> str:
        """Convert 0-100 score to research signal level."""
        if score < 25:
            return "low"
        if score < 50:
            return "moderate"
        if score < 75:
            return "elevated"
        return "high"

    def _check_data_quality(self, shared: SharedPhysiologicalFeatures) -> float:
        if not shared:
            return 0.0
        return float(shared.overall_quality if hasattr(shared, 'overall_quality') else 0.5)
