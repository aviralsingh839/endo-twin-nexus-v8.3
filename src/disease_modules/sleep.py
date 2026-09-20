"""Sleep / Circadian Health Module - V8.3.

Uses:
- activity, movement, HR, HRV, resting HR, temperature trends,
  sleep duration, timing, regularity, day/night activity pattern

Outputs:
- sleep regularity signal
- circadian disruption signal
- recovery signal
- persistent sleep deviation

Never diagnoses sleep disorders.
Language: 'sleep-related risk signal' or 'circadian disruption pattern'
"""
from __future__ import annotations

from typing import Dict, Optional, List
import numpy as np

from src.disease_modules.base import DiseaseModule
from src.data_models import SharedPhysiologicalFeatures, DiseaseModuleResult
from src.utils.math_utils import clamp


class SleepModule(DiseaseModule):
    @property
    def name(self) -> str:
        return "sleep_circadian"

    @property
    def version(self) -> str:
        return "8.3.0"

    @property
    def required_features(self) -> List[str]:
        return ["activity_level", "heart_rate", "hrv_rmssd"]

    @property
    def optional_features(self) -> List[str]:
        return ["sleep_duration_h", "sleep_regularity", "sleep_timing_h",
                "circadian_stability", "circadian_disruption",
                "skin_temp_c", "day_night_activity_ratio"]

    def _assess_sleep_duration(self, shared: SharedPhysiologicalFeatures) -> Tuple[float, str]:
        if shared.sleep_duration_h is None:
            return 50.0, "unknown - no sleep duration data"
        dur = shared.sleep_duration_h
        if 7 <= dur <= 9:
            return 10.0, f"normal duration {dur:.1f}h"
        if 6 <= dur < 7 or 9 < dur <= 10:
            return 35.0, f"mild deviation {dur:.1f}h"
        if 5 <= dur < 6 or 10 < dur <= 11:
            return 65.0, f"moderate deviation {dur:.1f}h"
        return 85.0, f"significant deviation {dur:.1f}h"

    def _assess_regularity(self, shared: SharedPhysiologicalFeatures) -> Tuple[float, str]:
        if shared.sleep_regularity == 0.0:
            return 50.0, "unknown regularity"
        # sleep_regularity is 0-100, higher is more regular
        irregularity = 100.0 - shared.sleep_regularity
        if irregularity < 20:
            return irregularity, f"regular pattern {shared.sleep_regularity:.0f}%"
        if irregularity < 40:
            return irregularity, f"mild irregularity {shared.sleep_regularity:.0f}%"
        if irregularity < 70:
            return irregularity, f"moderate irregularity {shared.sleep_regularity:.0f}%"
        return irregularity, f"high irregularity {shared.sleep_regularity:.0f}%"

    def _assess_circadian(self, shared: SharedPhysiologicalFeatures) -> Tuple[float, str]:
        disruption = shared.circadian_disruption
        if disruption < 25:
            return disruption, f"stable circadian {shared.circadian_stability:.0f}%"
        if disruption < 50:
            return disruption, f"mild circadian disruption {disruption:.0f}%"
        if disruption < 75:
            return disruption, f"moderate circadian disruption {disruption:.0f}%"
        return disruption, f"significant circadian disruption {disruption:.0f}%"

    def _assess_recovery(self, shared: SharedPhysiologicalFeatures) -> Tuple[float, str]:
        recovery = shared.recovery_score
        # Low recovery = higher risk signal
        risk = 100.0 - recovery
        if risk < 25:
            return risk, f"good recovery {recovery:.0f}%"
        if risk < 50:
            return risk, f"moderate recovery {recovery:.0f}%"
        return risk, f"reduced recovery {recovery:.0f}%"

    def predict(self, shared: SharedPhysiologicalFeatures, clinical: Optional[Dict] = None,
                ultrasound: Optional[Dict] = None, history: Optional[List] = None) -> DiseaseModuleResult:
        # Evaluate components
        duration_score, duration_desc = self._assess_sleep_duration(shared)
        regularity_score, regularity_desc = self._assess_regularity(shared)
        circadian_score, circadian_desc = self._assess_circadian(shared)
        recovery_score, recovery_desc = self._assess_recovery(shared)

        # Weighted combination
        # Sleep regularity and circadian are most important
        overall = (
            0.30 * regularity_score +
            0.30 * circadian_score +
            0.25 * duration_score +
            0.15 * recovery_score
        )

        # Persistence check from history
        persistent = False
        if history and len(history) >= 7:
            # Check last 7 days of sleep data
            recent_regularities = []
            for f in history[-20:]:
                if hasattr(f, 'sleep_regularity') and f.sleep_regularity:
                    recent_regularities.append(f.sleep_regularity)
            if recent_regularities and len(recent_regularities) >= 5:
                avg_reg = float(np.mean(recent_regularities))
                if avg_reg < 60:
                    persistent = True
                    overall = min(100.0, overall + 10.0)

        level = self._level_from_score(overall)
        confidence = self.confidence(shared)
        data_quality = self._check_data_quality(shared)

        # Determine primary signal
        scores = {
            "sleep_regularity": regularity_score,
            "circadian_disruption": circadian_score,
            "sleep_duration": duration_score,
            "recovery": recovery_score,
        }
        primary = max(scores, key=scores.get)

        signal_map = {
            "sleep_regularity": "sleep_regularity_deviation",
            "circadian_disruption": "circadian_disruption_pattern",
            "sleep_duration": "sleep_duration_deviation",
            "recovery": "reduced_recovery_signal",
        }
        signal = signal_map.get(primary, "sleep_related_signal")
        if persistent:
            signal = "persistent_" + signal

        drivers = [
            {"domain": "sleep_regularity", "score": round(regularity_score, 1), "description": regularity_desc, "type": "sleep"},
            {"domain": "circadian", "score": round(circadian_score, 1), "description": circadian_desc, "type": "circadian"},
            {"domain": "sleep_duration", "score": round(duration_score, 1), "description": duration_desc, "type": "sleep"},
            {"domain": "recovery", "score": round(recovery_score, 1), "description": recovery_desc, "type": "recovery"},
        ]
        drivers.sort(key=lambda x: x["score"], reverse=True)

        # Day/night pattern
        day_night_note = ""
        if shared.day_night_activity_ratio < 1.2:
            day_night_note = " Reduced day/night activity difference."
        elif shared.day_night_activity_ratio > 3.0:
            day_night_note = " Normal day/night activity pattern."

        explanation = (
            f"Sleep-related risk signal: {overall:.0f}% ({level}). "
            f"Primary: {drivers[0]['description']}. "
            f"Secondary: {drivers[1]['description']}.{day_night_note} "
            f"{'Persistent pattern over multiple days.' if persistent else 'Single assessment window.'} "
            f"This is a research signal, not a sleep disorder diagnosis."
        )

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
            provenance={
                "wearable_physiology": 0.6,
                "longitudinal": 0.3 if history else 0.1,
                "clinical": 0.1,
            },
            limitations=self.limitations(),
            extra={
                "sleep_duration_h": shared.sleep_duration_h,
                "sleep_regularity": shared.sleep_regularity,
                "circadian_stability": shared.circadian_stability,
                "recovery_score": shared.recovery_score,
                "day_night_ratio": shared.day_night_activity_ratio,
                "persistent": persistent,
            }
        )

    def limitations(self) -> str:
        return (
            "Research-only sleep and circadian health signal. Not a diagnosis of sleep disorder. "
            "Does not replace polysomnography or clinical sleep evaluation. "
            "Wearable sleep estimation is approximate. "
            "Circadian disruption pattern requires multiple days of data for confidence. "
            "Model not clinically validated for sleep disorder diagnosis."
        )


# Helper for type hint
from typing import Tuple
