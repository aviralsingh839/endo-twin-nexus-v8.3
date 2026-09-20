"""Stress and autonomic-balance estimation.

Explainable formula-based estimation from autonomic and arousal features.
"""
from __future__ import annotations

from src.config import DEFAULT_RESTING_HR, DEFAULT_RMSSD_MS
from src.data_models import FeatureVector
from src.utils.math_utils import clamp, sigmoid, zscore


class StressEstimator:
    def estimate(self, fv: FeatureVector, gsr_z: float = 0.0) -> dict[str, float]:
        hr_z = zscore(fv.hr_bpm, DEFAULT_RESTING_HR, 12.0)
        rmssd_z = zscore(fv.rmssd_ms, DEFAULT_RMSSD_MS, 18.0)
        motion_z = zscore(fv.motion_index, 0.10, 0.22)
        temp_drop_z = zscore(-(fv.temp_slope_c_per_min or 0.0), 0.0, 0.03)
        phasic_z = zscore(fv.gsr_phasic_per_min, 1.0, 4.0)

        formula = 100.0 * sigmoid(
            0.9 * hr_z
            - 1.1 * rmssd_z
            + 0.9 * phasic_z
            + 0.5 * gsr_z
            - 0.5 * max(motion_z, 0.0)
            + 0.3 * temp_drop_z
        )

        acute = formula

        # Motion gate: if highly active, stress confidence and stress estimate are reduced.
        if fv.activity_level > 45:
            acute = 0.65 * acute

        chronic = clamp(0.55 * fv.chronic_stress + 0.45 * acute if fv.chronic_stress else acute * 0.7, 0.0, 100.0)
        autonomic = 100.0 * sigmoid(-1.0 * rmssd_z + 0.5 * hr_z + 0.4 * gsr_z)
        return {
            "acute_stress": float(clamp(acute, 0.0, 100.0)),
            "chronic_stress": float(clamp(chronic, 0.0, 100.0)),
            "autonomic_imbalance": float(clamp(autonomic, 0.0, 100.0)),
            "stress_index": float(clamp(0.65 * acute + 0.35 * chronic, 0.0, 100.0)),
        }
