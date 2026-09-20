"""PCOS / Reproductive-Metabolic Risk Module - V8.3.

Keeps and improves existing V8.1 PCOS pipeline.
Distinguishes:
1. clinical-variable prediction
2. wearable physiological signals
3. ultrasound-derived features
4. combined/fused research estimate

Language: 'PCOS-associated physiological and clinical risk signals'
Never: 'wearable detects PCOS'
"""
from __future__ import annotations

from typing import Dict, Optional, List, Tuple
import numpy as np

from src.disease_modules.base import DiseaseModule
from src.data_models import SharedPhysiologicalFeatures, DiseaseModuleResult
from src.config import UserProfile
from src.utils.math_utils import clamp, sigmoid


# Domain weights - research priors, same as V8.1 but documented
CYCLE_W = 1.20
METABOLIC_W = 0.90
AUTONOMIC_W = 0.60
SLEEP_W = 0.50
CIRCADIAN_W = 0.50
TEMPERATURE_W = 0.35
GLUCOSE_W = 0.35
ACTIVITY_W = 0.30
BP_W = 0.20
INTERCEPT = -3.0
CYCLE_NEUTRAL = 15.0


class PCOSModule(DiseaseModule):
    """PCOS-associated risk signals."""

    @property
    def name(self) -> str:
        return "pcos_reproductive_metabolic"

    @property
    def version(self) -> str:
        return "8.3.0"

    @property
    def required_features(self) -> List[str]:
        return ["heart_rate", "hrv_rmssd", "activity_level", "skin_temp_c"]

    @property
    def optional_features(self) -> List[str]:
        return ["sleep_duration_h", "sleep_regularity", "circadian_stability",
                "gsr_tonic", "stress_index", "temperature_rhythm_disruption"]

    def __init__(self, profile: Optional[UserProfile] = None):
        self.profile = profile

    def _cycle_score(self, profile: Optional[UserProfile], clinical: Optional[Dict] = None) -> float:
        """Cycle irregularity 0-100 from self-reported info only."""
        p = profile or self.profile
        if p is None and not clinical:
            return CYCLE_NEUTRAL
        length = None
        dslp = None
        irregular = None
        if p:
            length = p.usual_cycle_length_days
            dslp = p.days_since_last_period
            irregular = p.cycle_irregular
        if clinical:
            length = clinical.get("usual_cycle_length_days", length)
            dslp = clinical.get("days_since_last_period", dslp)
            irregular = clinical.get("cycle_irregular", irregular)

        if length is None and dslp is None and irregular is None:
            return CYCLE_NEUTRAL
        parts: List[float] = []
        if length is not None:
            parts.append(clamp(abs(float(length) - 28.0) / 20.0 * 100.0, 0.0, 100.0))
        if irregular is True:
            parts.append(60.0)
        elif irregular is False:
            parts.append(10.0)
        if dslp is not None and dslp > 35:
            parts.append(clamp((float(dslp) - 35.0) / 25.0 * 100.0, 0.0, 100.0))
        if not parts:
            return CYCLE_NEUTRAL
        return float(np.mean(parts))

    def _domain_scores(self, shared: SharedPhysiologicalFeatures, profile: Optional[UserProfile],
                       clinical: Optional[Dict], ultrasound: Optional[Dict]) -> Dict[str, float]:
        # Sleep risk from shared
        sleep_risk = 50.0
        if shared.sleep_duration_h is not None:
            # Short sleep <6h or long >10h -> higher risk
            if shared.sleep_duration_h < 6:
                sleep_risk = clamp((6 - shared.sleep_duration_h) / 3 * 100.0, 0, 100)
            elif shared.sleep_duration_h > 10:
                sleep_risk = clamp((shared.sleep_duration_h - 10) / 2 * 100.0, 0, 100)
            else:
                sleep_risk = 20.0
        if shared.sleep_regularity:
            sleep_risk = 0.7 * sleep_risk + 0.3 * (100.0 - shared.sleep_regularity)

        metabolic = 0.0
        if clinical:
            # BMI, glucose etc
            bmi = clinical.get("bmi") or (profile.bmi if profile else None)
            if bmi:
                if bmi > 25:
                    metabolic += clamp((bmi - 25) / 10 * 100.0, 0, 100) * 0.5
            glucose = clinical.get("glucose_mg_dl") or (profile.glucose_mg_dl if profile else None)
            if glucose and glucose > 100:
                metabolic += clamp((glucose - 100) / 50 * 100.0, 0, 100) * 0.5

        # Use shared features for metabolic proxy
        if shared.hrv_rmssd is not None and shared.hrv_rmssd < 30:
            metabolic += clamp((30 - shared.hrv_rmssd) / 20 * 100.0, 0, 100) * 0.3

        stress_autonomic = clamp(max(shared.stress_index, shared.autonomic_imbalance), 0, 100)
        circadian = clamp(shared.circadian_disruption, 0, 100)
        temp_rhythm = clamp(shared.temperature_rhythm_disruption, 0, 100)
        low_activity = clamp(shared.low_activity_risk, 0, 100)

        # Glucose and BP from clinical
        glucose_risk = 0.0
        bp_risk = 0.0
        if clinical:
            g = clinical.get("glucose_mg_dl")
            if g:
                glucose_risk = clamp((float(g) - 90) / 60 * 100.0, 0, 100) if g > 90 else 0.0
            sys_bp = clinical.get("systolic_bp")
            if sys_bp and sys_bp > 120:
                bp_risk = clamp((float(sys_bp) - 120) / 40 * 100.0, 0, 100)

        cycle = self._cycle_score(profile, clinical)

        return {
            "cycle": cycle,
            "metabolic": clamp(metabolic, 0, 100),
            "glucose": glucose_risk,
            "bp": bp_risk,
            "stress_autonomic": stress_autonomic,
            "sleep": sleep_risk,
            "circadian": circadian,
            "temperature_rhythm": temp_rhythm,
            "low_activity": low_activity,
        }

    def _risk_from_scores(self, d: Dict[str, float]) -> float:
        c = d["cycle"] / 100.0
        m = d["metabolic"] / 100.0
        a = d["stress_autonomic"] / 100.0
        s = d["sleep"] / 100.0
        ci = d["circadian"] / 100.0
        t = d["temperature_rhythm"] / 100.0
        l = d["low_activity"] / 100.0
        g = d["glucose"] / 100.0
        b = d["bp"] / 100.0
        z = (INTERCEPT + CYCLE_W * c + METABOLIC_W * m + AUTONOMIC_W * a +
             SLEEP_W * s + CIRCADIAN_W * ci + TEMPERATURE_W * t +
             GLUCOSE_W * g + ACTIVITY_W * l + BP_W * b)
        return float(clamp(100.0 * sigmoid(z), 0.0, 100.0))

    def predict(self, shared: SharedPhysiologicalFeatures, clinical: Optional[Dict] = None,
                ultrasound: Optional[Dict] = None, history: Optional[List] = None) -> DiseaseModuleResult:
        profile = clinical.get("profile") if clinical and "profile" in clinical else self.profile
        if isinstance(profile, dict):
            # Convert dict to UserProfile-like
            from src.config import UserProfile
            p = UserProfile()
            for k, v in profile.items():
                if hasattr(p, k):
                    setattr(p, k, v)
            profile = p

        domains = self._domain_scores(shared, profile, clinical, ultrasound)
        risk = self._risk_from_scores(domains)

        # Provenance breakdown
        provenance = {}
        clinical_weight = 0.4 if clinical else 0.1
        wearable_weight = 0.25
        longitudinal_weight = 0.0
        ultrasound_weight = 0.0
        metabolic_weight = 0.15

        if history and len(history) > 10:
            longitudinal_weight = 0.25
            wearable_weight = 0.20
            clinical_weight = 0.35 if clinical else 0.15

        if ultrasound and ultrasound.get("cyst_size_mm") is not None:
            ultrasound_weight = 0.20
            # Reduce others proportionally
            total = clinical_weight + wearable_weight + longitudinal_weight + metabolic_weight + ultrasound_weight
            if total > 0:
                clinical_weight = clinical_weight / total
                wearable_weight = wearable_weight / total
                longitudinal_weight = longitudinal_weight / total
                metabolic_weight = metabolic_weight / total
                ultrasound_weight = ultrasound_weight / total

        provenance = {
            "clinical_variables": round(clinical_weight, 2),
            "wearable_physiology": round(wearable_weight, 2),
            "longitudinal": round(longitudinal_weight, 2),
            "ultrasound": round(ultrasound_weight, 2),
            "metabolic": round(metabolic_weight, 2),
        }

        level = self._level_from_score(risk)
        confidence = self.confidence(shared)
        data_quality = self._check_data_quality(shared)

        # Drivers
        sorted_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)
        drivers = []
        for name, score in sorted_domains[:3]:
            drivers.append({
                "domain": name,
                "score": round(float(score), 1),
                "contribution": f"{name} {score:.0f}%",
                "type": "clinical" if name == "cycle" else "physiological" if name in ("stress_autonomic", "sleep", "circadian") else "metabolic"
            })

        # Explanation
        explanation = (
            f"PCOS-associated physiological and clinical risk signal: {risk:.1f}% ({level}). "
            f"Main drivers: {', '.join([d['domain'] for d in drivers[:2]])}. "
            f"This is a research estimate based on {', '.join([k for k,v in provenance.items() if v>0.05])}. "
            f"Not a diagnosis. Clinical evaluation required."
        )

        # Ultrasound context
        if ultrasound:
            if ultrasound.get("source") == "CLINICALLY-ENTERED":
                explanation += " Includes clinically-entered ultrasound features."
            elif ultrasound.get("source") == "IMAGE-DERIVED":
                explanation += " Includes image-derived ultrasound features (quality-gated)."

        return DiseaseModuleResult(
            module=self.name,
            version=self.version,
            signal="pcos_associated_risk" if risk < 50 else "elevated_pcos_associated_risk",
            level=level,
            confidence=confidence,
            data_quality=data_quality,
            clinical_validation="NOT ESTABLISHED",
            drivers=drivers,
            explanation=explanation,
            provenance=provenance,
            limitations=self.limitations() + " PCOS diagnosis requires Rotterdam criteria and clinician evaluation.",
            extra={
                "domain_scores": domains,
                "risk_percent": risk,
                "clinical_variables_present": bool(clinical),
                "ultrasound_present": bool(ultrasound),
                "baseline_deviations": shared.baseline_deviations,
            }
        )

    def limitations(self) -> str:
        return (
            "Research-only PCOS-associated risk signal. Not a diagnostic test. "
            "PCOS diagnosis requires clinical evaluation using Rotterdam criteria (oligo-anovulation, "
            "hyperandrogenism, polycystic ovaries) by qualified professional. "
            "Wearable physiology alone cannot diagnose PCOS. "
            "Ultrasound features are UNKNOWN by design until validated labelled dataset exists. "
            "Model not clinically validated."
        )
