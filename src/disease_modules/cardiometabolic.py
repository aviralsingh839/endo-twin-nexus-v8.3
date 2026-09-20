"""Cardiometabolic Risk Module - V8.3 (research-oriented).

Potential features:
- resting HR, HRV, activity, BMI, age, BP if manually entered,
  glucose if manually entered, sleep, temperature, longitudinal changes

Outputs:
- cardiometabolic risk signal
- reduced activity trend
- elevated resting-HR trend
- metabolic data flag

Never claims diagnosis of diabetes, hypertension, CVD.
"""
from __future__ import annotations

from typing import Dict, Optional, List
import numpy as np

from src.disease_modules.base import DiseaseModule
from src.data_models import SharedPhysiologicalFeatures, DiseaseModuleResult
from src.utils.math_utils import clamp


class CardiometabolicModule(DiseaseModule):
    @property
    def name(self) -> str:
        return "cardiometabolic"

    @property
    def version(self) -> str:
        return "8.3.0"

    @property
    def required_features(self) -> List[str]:
        return ["heart_rate", "resting_heart_rate", "activity_level", "hrv_rmssd"]

    @property
    def optional_features(self) -> List[str]:
        return ["skin_temp_c", "sleep_duration_h", "stress_index",
                "baseline_deviations", "trend_features"]

    def _assess_resting_hr(self, shared: SharedPhysiologicalFeatures, clinical: Optional[Dict]) -> tuple[float, str]:
        rhr = shared.resting_heart_rate or shared.heart_rate
        if rhr is None:
            return 50.0, "no resting HR data"
        # Age adjustment if available
        age = clinical.get("age_years") if clinical else None
        threshold_high = 80 if (age and age < 50) else 85
        threshold_low = 50
        if rhr < threshold_low:
            return 20.0, f"low resting HR {rhr:.0f} bpm (athletic may be normal)"
        if rhr <= 70:
            return 10.0, f"normal resting HR {rhr:.0f} bpm"
        if rhr <= threshold_high:
            return 35.0, f"mildly elevated resting HR {rhr:.0f} bpm"
        if rhr <= 90:
            return 65.0, f"elevated resting HR {rhr:.0f} bpm"
        return 85.0, f"high resting HR {rhr:.0f} bpm"

    def _assess_hrv(self, shared: SharedPhysiologicalFeatures) -> tuple[float, str]:
        if shared.hrv_rmssd is None:
            return 50.0, "no HRV data"
        hrv = shared.hrv_rmssd
        if hrv >= 50:
            return 10.0, f"good HRV {hrv:.0f} ms"
        if hrv >= 35:
            return 30.0, f"moderate HRV {hrv:.0f} ms"
        if hrv >= 20:
            return 60.0, f"reduced HRV {hrv:.0f} ms"
        return 80.0, f"low HRV {hrv:.0f} ms"

    def _assess_activity(self, shared: SharedPhysiologicalFeatures, history: Optional[List]) -> tuple[float, str, bool]:
        act = shared.activity_level
        if act < 15:
            base = 75.0
            desc = f"low activity {act:.0f}%"
        elif act < 30:
            base = 40.0
            desc = f"moderate activity {act:.0f}%"
        else:
            base = 15.0
            desc = f"good activity {act:.0f}%"

        # Trend: reduced activity over time
        reduced_trend = False
        if history and len(history) >= 10:
            recent = [getattr(f, 'activity_level', None) for f in history[-10:] if getattr(f, 'activity_level', None) is not None]
            older = [getattr(f, 'activity_level', None) for f in history[-20:-10] if getattr(f, 'activity_level', None) is not None]
            if recent and older:
                recent_mean = float(np.mean(recent))
                older_mean = float(np.mean(older))
                if recent_mean < older_mean * 0.8:
                    reduced_trend = True
                    base = min(100.0, base + 20.0)
                    desc += f", decreasing trend ({older_mean:.0f}% -> {recent_mean:.0f}%)"

        return base, desc, reduced_trend

    def _assess_metabolic_clinical(self, clinical: Optional[Dict]) -> tuple[float, str, List[str]]:
        if not clinical:
            return 0.0, "no clinical metabolic data", []
        flags = []
        score = 0.0
        bmi = clinical.get("bmi")
        if bmi:
            if bmi >= 30:
                score += 40.0
                flags.append(f"BMI {bmi:.1f} (obesity range)")
            elif bmi >= 25:
                score += 20.0
                flags.append(f"BMI {bmi:.1f} (overweight)")
        sys_bp = clinical.get("systolic_bp")
        dia_bp = clinical.get("diastolic_bp")
        if sys_bp and sys_bp >= 130:
            score += 30.0
            flags.append(f"elevated systolic BP {sys_bp:.0f}")
        if dia_bp and dia_bp >= 85:
            score += 20.0
            flags.append(f"elevated diastolic BP {dia_bp:.0f}")
        glucose = clinical.get("glucose_mg_dl")
        if glucose:
            if glucose >= 126:
                score += 40.0
                flags.append(f"high glucose {glucose:.0f} mg/dL")
            elif glucose >= 100:
                score += 20.0
                flags.append(f"elevated glucose {glucose:.0f} mg/dL")
        return clamp(score, 0, 100), "; ".join(flags) if flags else "clinical metabolic data normal", flags

    def predict(self, shared: SharedPhysiologicalFeatures, clinical: Optional[Dict] = None,
                ultrasound: Optional[Dict] = None, history: Optional[List] = None) -> DiseaseModuleResult:
        rhr_score, rhr_desc = self._assess_resting_hr(shared, clinical)
        hrv_score, hrv_desc = self._assess_hrv(shared)
        act_score, act_desc, reduced_trend = self._assess_activity(shared, history)
        metabolic_score, metabolic_desc, metabolic_flags = self._assess_metabolic_clinical(clinical)

        # Baseline deviation: persistent increase in RHR or decrease in HRV
        baseline_penalty = 0.0
        baseline_notes = []
        if shared.baseline_deviations:
            hr_dev = shared.baseline_deviations.get("hr_bpm") or shared.baseline_deviations.get("resting_hr_bpm")
            if hr_dev and hr_dev > 1.5:
                baseline_penalty += 15.0
                baseline_notes.append(f"RHR {hr_dev:+.1f} SD above baseline")
            hrv_dev = shared.baseline_deviations.get("rmssd_ms")
            if hrv_dev and hrv_dev < -1.5:
                baseline_penalty += 15.0
                baseline_notes.append(f"HRV {hrv_dev:+.1f} SD below baseline")

        overall = (
            0.30 * rhr_score +
            0.25 * hrv_score +
            0.25 * act_score +
            0.20 * metabolic_score +
            baseline_penalty * 0.3
        )
        overall = clamp(overall, 0, 100)

        level = self._level_from_score(overall)
        confidence = self.confidence(shared)
        data_quality = self._check_data_quality(shared)

        # Signal type
        if reduced_trend:
            signal = "reduced_activity_trend"
        elif rhr_score > 60:
            signal = "elevated_resting_hr_trend"
        elif metabolic_flags:
            signal = "metabolic_data_flag"
        else:
            signal = "cardiometabolic_risk_signal"

        drivers = [
            {"domain": "resting_hr", "score": round(rhr_score, 1), "description": rhr_desc, "type": "cardiac"},
            {"domain": "hrv", "score": round(hrv_score, 1), "description": hrv_desc, "type": "autonomic"},
            {"domain": "activity", "score": round(act_score, 1), "description": act_desc, "type": "lifestyle"},
            {"domain": "metabolic_clinical", "score": round(metabolic_score, 1), "description": metabolic_desc, "type": "clinical", "flags": metabolic_flags},
        ]
        drivers.sort(key=lambda x: x["score"], reverse=True)

        # Longitudinal note
        longitudinal_note = ""
        if baseline_notes:
            longitudinal_note = f" Longitudinal: {'; '.join(baseline_notes)}."
        if reduced_trend:
            longitudinal_note += " Persistent reduced activity pattern."

        explanation = (
            f"Cardiometabolic research signal: {overall:.0f}% ({level}). "
            f"Primary: {drivers[0]['description']}. "
            f"Secondary: {drivers[1]['description']}."
            f"{longitudinal_note} "
            f"This is a research-oriented screening signal, not a diagnosis of diabetes, hypertension, or cardiovascular disease."
        )

        provenance = {
            "wearable_physiology": 0.5,
            "clinical_variables": 0.3 if clinical else 0.05,
            "longitudinal": 0.2 if history else 0.05,
            "metabolic": 0.2 if metabolic_flags else 0.05,
        }
        # Normalize
        total = sum(provenance.values())
        if total > 0:
            provenance = {k: round(v/total, 2) for k, v in provenance.items()}

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
                "resting_hr": shared.resting_heart_rate,
                "hrv_rmssd": shared.hrv_rmssd,
                "activity_level": shared.activity_level,
                "metabolic_flags": metabolic_flags,
                "reduced_activity_trend": reduced_trend,
                "baseline_notes": baseline_notes,
            }
        )

    def limitations(self) -> str:
        return (
            "Research-only cardiometabolic risk signal. Not a diagnosis of diabetes, hypertension, "
            "or cardiovascular disease. Resting HR and HRV are influenced by many factors (stress, "
            "caffeine, illness). Activity trends require multiple days. Clinical metabolic data "
            "(BP, glucose) are user-entered and not validated. Requires clinical evaluation for any "
            "metabolic or cardiovascular concern. Model not clinically validated."
        )
