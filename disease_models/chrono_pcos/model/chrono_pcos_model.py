"""
CHRONO-PCOS disease-model adapter.

ENDO-TWIN is the general platform. CHRONO-PCOS is the first
disease-specific research module.

V8.6.1 science hardening:
- No fabricated fallback sensor values.
- Missing/low-quality evidence returns UNKNOWN / INSUFFICIENT_EVIDENCE.
- Wearable physiology is treated as contextual research evidence, not as a
  diagnostic criterion for PCOS.
- No ultrasound anatomy is invented when no validated image-derived feature
  exists.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from src.endo_twin.models.disease_model_interface import (
    DiseaseModel,
    DiseaseModelManifest,
    DiseaseModelResult,
)
from ..manifest import CHRONO_PCOS_MANIFEST

try:
    from src.disease_modules.pcos import PCOSModule as OriginalPCOSModule
    from src.data_models import SharedPhysiologicalFeatures
    ORIGINAL_AVAILABLE = True
except ImportError:
    OriginalPCOSModule = None
    SharedPhysiologicalFeatures = None
    ORIGINAL_AVAILABLE = False


class ChronoPCOSDiseaseModel(DiseaseModel):
    """CHRONO-PCOS research module with explicit evidence gates."""

    def __init__(self) -> None:
        self._manifest: DiseaseModelManifest = CHRONO_PCOS_MANIFEST
        self.original_module = None
        if ORIGINAL_AVAILABLE:
            try:
                self.original_module = OriginalPCOSModule()
            except Exception:
                self.original_module = None

    @property
    def manifest(self) -> DiseaseModelManifest:
        return self._manifest

    def validate_input(
        self,
        features: Dict[str, Any],
        clinical_data: Optional[Dict] = None,
        imaging_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Validate evidence before allowing an exploratory research result."""
        missing = [
            key for key in self.manifest.required_features
            if features.get(key) is None
            and not any(
                features.get(alt) is not None
                for alt in self._aliases(key)
            )
        ]

        quality = self._quality(features)
        warnings: List[str] = []

        if quality < 0.50:
            warnings.append(f"Overall physiological data quality below gate: {quality:.2f}")

        clinical_keys = {
            "usual_cycle_length_days",
            "cycle_length",
            "cycle_irregular",
            "cycle_irregularity",
            "clinical_hyperandrogenism",
            "biochemical_hyperandrogenism",
            "total_testosterone",
            "free_testosterone",
            "androgen_index",
        }
        clinical_present = bool(clinical_data) and any(
            clinical_data.get(k) is not None for k in clinical_keys
        )

        image_present = bool(imaging_data) and any(
            imaging_data.get(k) is not None
            for k in ("fnpo", "follicle_number_per_ovary", "ovarian_volume_ml",
                      "fnps", "polycystic_ovary_morphology")
        )

        if not clinical_present and not image_present:
            warnings.append(
                "No PCOS-specific clinical/imaging evidence supplied. "
                "Wearable physiology alone is not a diagnostic criterion."
            )

        if missing:
            warnings.append(f"Missing required research features: {missing}")

        valid = not missing and quality >= 0.50 and (clinical_present or image_present)
        return {
            "valid": valid,
            "missing": missing,
            "warnings": warnings,
            "quality": quality,
            "clinical_evidence_present": clinical_present,
            "imaging_evidence_present": image_present,
        }

    @staticmethod
    def _aliases(key: str) -> List[str]:
        return {
            "heart_rate": ["heart_rate", "hr", "hr_bpm"],
            "hrv_rmssd": ["hrv_rmssd", "hrv", "rmssd", "rmssd_ms"],
            "activity_level": ["activity_level", "activity", "motion"],
            "skin_temp_c": ["skin_temp_c", "skin_temp", "temperature", "temp_c"],
        }.get(key, [key])

    @staticmethod
    def _quality(features: Dict[str, Any]) -> float:
        value = features.get(
            "overall_quality",
            features.get("data_quality", features.get("signal_quality", 0.0)),
        )
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return 0.0

    def _insufficient_evidence(
        self,
        *,
        patient_id: str,
        validation: Dict[str, Any],
    ) -> DiseaseModelResult:
        limitations = (
            "Research-only module. Insufficient evidence is represented as UNKNOWN "
            "rather than filled with defaults. Wearable physiology is contextual "
            "research evidence and cannot diagnose PCOS. Clinical assessment must "
            "follow an appropriate PCOS diagnostic pathway; this prototype does "
            "not establish a diagnosis or clinical probability."
        )
        return DiseaseModelResult(
            model_name=self.manifest.name,
            model_version=self.manifest.version,
            patient_id=patient_id,
            timestamp=time.time(),
            signal="insufficient_evidence",
            level="unknown",
            confidence=0.0,
            data_quality=float(validation.get("quality", 0.0)),
            clinical_validation="NOT ESTABLISHED",
            drivers=[],
            explanation=(
                "No validated disease-model result is produced for this input. "
                "Missing or inadequate evidence remains UNKNOWN."
            ),
            provenance={
                "wearable_physiology": 1.0 if validation.get("quality", 0.0) > 0 else 0.0,
                "clinical_variables": 1.0 if validation.get("clinical_evidence_present") else 0.0,
                "ultrasound": 1.0 if validation.get("imaging_evidence_present") else 0.0,
            },
            limitations=limitations,
            uncertainty={
                "model_confidence": 0.0,
                "data_quality": validation.get("quality", 0.0),
                "missing_features": validation.get("missing", []),
                "warnings": validation.get("warnings", []),
                "clinical_validation": "NOT ESTABLISHED",
                "note": "UNKNOWN / insufficient evidence is preferable to imputation.",
            },
            extra={
                "insufficient_evidence": True,
                "clinical_evidence_present": bool(validation.get("clinical_evidence_present")),
                "imaging_evidence_present": bool(validation.get("imaging_evidence_present")),
            },
        )

    def analyze(
        self,
        features: Dict[str, Any],
        clinical_data: Optional[Dict] = None,
        imaging_data: Optional[Dict] = None,
        longitudinal_data: Optional[List] = None,
        baseline_data: Optional[Dict] = None,
        patient_id: str = "unknown",
    ) -> DiseaseModelResult:
        """Run the module only when evidence passes the input gate."""
        validation = self.validate_input(features, clinical_data, imaging_data)
        if not validation["valid"]:
            return self._insufficient_evidence(
                patient_id=patient_id,
                validation=validation,
            )

        if not self.original_module or SharedPhysiologicalFeatures is None:
            return self._insufficient_evidence(
                patient_id=patient_id,
                validation={
                    **validation,
                    "warnings": validation["warnings"]
                    + ["Trained/validated disease-model implementation is unavailable."],
                },
            )

        try:
            shared = SharedPhysiologicalFeatures()
            shared.heart_rate = self._value(features, "heart_rate")
            shared.hrv_rmssd = self._value(features, "hrv_rmssd")
            shared.activity_level = self._value(features, "activity_level", default=None)
            shared.skin_temp_c = self._value(features, "skin_temp_c", default=None)

            # These are optional contextual features. They remain absent when
            # the source does not supply them; no synthetic defaults are used.
            for attr, key in (
                ("sleep_duration_h", "sleep_duration_h"),
                ("sleep_regularity", "sleep_regularity"),
                ("circadian_stability", "circadian_stability"),
                ("stress_index", "stress_index"),
                ("circadian_disruption", "circadian_disruption"),
                ("temperature_rhythm_disruption", "temperature_rhythm_disruption"),
                ("low_activity_risk", "low_activity_risk"),
                ("autonomic_imbalance", "autonomic_imbalance"),
            ):
                if features.get(key) is not None:
                    setattr(shared, attr, features[key])

            shared.overall_quality = validation["quality"]
            shared.baseline_deviations = baseline_data or {}

            result = self.original_module.predict(
                shared=shared,
                clinical=clinical_data or {},
                ultrasound=imaging_data or {},
                history=longitudinal_data or [],
            )

            # Preserve the original research output structure but reframe it
            # explicitly as exploratory and unvalidated.
            result.explanation = (
                result.explanation
                + " Wearable features are contextual research signals, not "
                "standalone PCOS diagnostic criteria. This module is not clinically validated."
            )
            result.clinical_validation = "NOT ESTABLISHED"
            result.extra = {
                **(result.extra or {}),
                "output_type": "exploratory_research_signal",
                "diagnostic_use": False,
                "wearable_is_diagnostic_criterion": False,
                "clinical_evidence_present": validation["clinical_evidence_present"],
                "imaging_evidence_present": validation["imaging_evidence_present"],
            }
            return result

        except Exception as exc:
            # Never substitute hard-coded physiological values after a model
            # failure. Preserve an explicit UNKNOWN state.
            return self._insufficient_evidence(
                patient_id=patient_id,
                validation={
                    **validation,
                    "warnings": validation["warnings"]
                    + [f"Model execution failed; no fallback imputation used: {exc}"],
                },
            )

    @staticmethod
    def _value(features: Dict[str, Any], key: str, default: Any = None) -> Any:
        aliases = ChronoPCOSDiseaseModel._aliases(key)
        for alias in aliases:
            if features.get(alias) is not None:
                return features[alias]
        return default

    # Kept for API compatibility with earlier callers.
    def get_uncertainty(self, result: DiseaseModelResult) -> Dict[str, Any]:
        return result.uncertainty or {
            "model_confidence": result.confidence,
            "data_quality": result.data_quality,
            "clinical_validation": result.clinical_validation,
        }


def get_chrono_pcos_model() -> ChronoPCOSDiseaseModel:
    return ChronoPCOSDiseaseModel()


ChronoPCOSModel = ChronoPCOSDiseaseModel
