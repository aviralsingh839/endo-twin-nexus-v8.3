"""Autonomic / Stress Regulation Module - V8.3.

Uses:
- HRV, resting HR, activity, sleep, temperature

Creates explainable stress/autonomic deviation estimator.
Separates ACUTE SIGNAL from PERSISTENT LONGITUDINAL CHANGE.
Not a mental-health diagnosis.
"""
from __future__ import annotations

from typing import Dict, Optional, List
import numpy as np

from src.disease_modules.base import DiseaseModule
from src.data_models import SharedPhysiologicalFeatures, DiseaseModuleResult
from src.utils.math_utils import clamp


class AutonomicModule(DiseaseModule):
    @property
    def name(self) -> str:
        return "autonomic_stress"

    @property
    def version(self) -> str:
        return "8.3.0"

    @property
    def required_features(self) -> List[str]:
        return ["hrv_rmssd", "heart_rate"]

    @property
    def optional_features(self) -> List[str]:
        return ["activity_level", "sleep_duration_h", "skin_temp_c",
                "stress_index", "autonomic_imbalance", "circadian_disruption"]

    def _assess_hrv(self, shared: SharedPhysiologicalFeatures) -> tuple[float, str]:
        if shared.hrv_rmssd is None:
            return 50.0, "no HRV data"
        hrv = shared.hrv_rmssd
        if hrv >= 50:
            return 15.0, f"good autonomic balance HRV {hrv:.0f}ms"
        if hrv >= 35:
            return 35.0, f"moderate HRV {hrv:.0f}ms"
        if hrv >= 20:
            return 65.0, f"reduced HRV {hrv:.0f}ms - possible autonomic strain"
        return 85.0, f"low HRV {hrv:.0f}ms - significant autonomic deviation"

    def _assess_stress_index(self, shared: SharedPhysiologicalFeatures) -> tuple[float, str]:
        si = shared.stress_index
        if si < 25:
            return si, f"low stress index {si:.0f}%"
        if si < 50:
            return si, f"moderate stress {si:.0f}%"
        if si < 75:
            return si, f"elevated stress {si:.0f}%"
        return si, f"high stress {si:.0f}%"

    def _separate_acute_persistent(self, shared: SharedPhysiologicalFeatures, history: Optional[List]) -> tuple[str, float, str]:
        """Separate acute vs persistent."""
        if not history or len(history) < 5:
            # Only current reading - acute
            if shared.stress_index > 70 or (shared.hrv_rmssd and shared.hrv_rmssd < 25):
                return "acute", shared.stress_index, "single elevated reading - acute signal"
            return "none", 0.0, "no acute signal"

        # Check persistence: last N readings
        recent_stress = []
        recent_hrv = []
        for f in history[-10:]:
            if hasattr(f, 'stress_index') and f.stress_index is not None:
                recent_stress.append(f.stress_index)
            if hasattr(f, 'rmssd_ms') and f.rmssd_ms is not None:
                recent_hrv.append(f.rmssd_ms)
            elif hasattr(f, 'hrv_rmssd') and getattr(f, 'hrv_rmssd', None) is not None:
                recent_hrv.append(getattr(f, 'hrv_rmssd'))

        if not recent_stress:
            return "none", 0.0, "insufficient history"

        avg_stress = float(np.mean(recent_stress))
        persistent_count = sum(1 for s in recent_stress if s > 60)

        if persistent_count >= 5 and avg_stress > 60:
            return "persistent", avg_stress, f"persistent elevation {persistent_count}/10 readings, avg {avg_stress:.0f}%"
        if persistent_count >= 3:
            return "intermittent", avg_stress, f"intermittent elevation {persistent_count}/10 readings"
        # Check if current is much higher than recent average - acute on top of baseline
        if recent_stress and shared.stress_index > np.mean(recent_stress) + 20:
            return "acute", shared.stress_index, f"acute spike {shared.stress_index:.0f}% vs recent avg {np.mean(recent_stress):.0f}%"

        return "none", avg_stress, f"stress within recent range avg {avg_stress:.0f}%"

    def predict(self, shared: SharedPhysiologicalFeatures, clinical: Optional[Dict] = None,
                ultrasound: Optional[Dict] = None, history: Optional[List] = None) -> DiseaseModuleResult:
        hrv_score, hrv_desc = self._assess_hrv(shared)
        stress_score, stress_desc = self._assess_stress_index(shared)
        acute_persistent_type, ap_score, ap_desc = self._separate_acute_persistent(shared, history)

        # Overall autonomic deviation. The GSR component (formerly 0.25) was
        # removed with the GSR hardware, so the two remaining signals keep their
        # original ratio: 0.35/0.75 and 0.40/0.75.
        overall = (
            0.467 * hrv_score +
            0.533 * stress_score
        )
        overall = clamp(overall, 0, 100)

        # Adjust for persistent
        if acute_persistent_type == "persistent":
            overall = min(100.0, overall + 10.0)
        elif acute_persistent_type == "acute":
            # Acute is less concerning for persistent signal, but still noted
            pass

        level = self._level_from_score(overall)
        confidence = self.confidence(shared)
        data_quality = self._check_data_quality(shared)

        # Signal type
        if acute_persistent_type == "acute":
            signal = "acute_autonomic_signal"
        elif acute_persistent_type == "persistent":
            signal = "persistent_autonomic_deviation"
        elif acute_persistent_type == "intermittent":
            signal = "intermittent_stress_pattern"
        else:
            signal = "autonomic_regulation_signal"

        # Recovery check
        recovery_note = ""
        if shared.recovery_score > 70:
            recovery_note = f" Good recovery {shared.recovery_score:.0f}%."
        elif shared.recovery_score < 40:
            recovery_note = f" Reduced recovery {shared.recovery_score:.0f}%."

        # Sleep impact
        sleep_note = ""
        if shared.sleep_duration_h is not None and shared.sleep_duration_h < 6:
            sleep_note = f" Short sleep {shared.sleep_duration_h:.1f}h may affect autonomic balance."

        drivers = [
            {"domain": "hrv", "score": round(hrv_score, 1), "description": hrv_desc, "type": "autonomic"},
            {"domain": "stress_index", "score": round(stress_score, 1), "description": stress_desc, "type": "stress"},
            {"domain": "temporal_pattern", "score": round(ap_score, 1), "description": ap_desc, "type": acute_persistent_type},
        ]
        drivers.sort(key=lambda x: x["score"], reverse=True)

        explanation = (
            f"Autonomic/stress regulation signal: {overall:.0f}% ({level}). "
            f"Primary: {drivers[0]['description']}. "
            f"Pattern: {ap_desc}.{recovery_note}{sleep_note} "
            f"This reflects physiological regulation, not a mental-health diagnosis."
        )

        provenance = {
            "wearable_physiology": 0.6,
            "longitudinal": 0.3 if history else 0.1,
            "clinical": 0.1,
        }

        return DiseaseModuleResult(
            module=self.name,
            version=self.version,
            signal=signal,
            level=level,
            confidence=confidence,
            data_quality=data_quality,
            clinical_validation="NOT ESTABLISHED",
            drivers=drivers[:3],
            explanation=explanation,
            provenance=provenance,
            limitations=self.limitations(),
            extra={
                "acute_vs_persistent": acute_persistent_type,
                "hrv_rmssd": shared.hrv_rmssd,
                "stress_index": shared.stress_index,
                "recovery_score": shared.recovery_score,
                "autonomic_imbalance": shared.autonomic_imbalance,
            }
        )

    def limitations(self) -> str:
        return (
            "Research-only autonomic/stress regulation signal. Not a mental-health diagnosis. "
            "HRV is influenced by many factors (activity, caffeine, temperature, illness). "
            "Acute stress signals are normal physiological responses. "
            "Persistent change requires multiple days of good-quality data. "
            "Does not diagnose anxiety, depression, or any psychiatric condition. "
            "Model not clinically validated."
        )
