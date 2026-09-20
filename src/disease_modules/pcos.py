"""PCOS / Reproductive-Metabolic research module.

Scientific boundary:
- Wearable physiology is contextual research evidence, not a standalone PCOS
  diagnostic criterion.
- Adult diagnostic context follows the 2023 international guideline structure:
  two of ovulatory dysfunction, hyperandrogenism, and polycystic ovarian
  morphology/elevated AMH, with appropriate exclusion of mimicking disorders.
- In adolescents, diagnosis requires both irregular menstrual cycles (defined
  by years post-menarche) and clinical/biochemical hyperandrogenism; pelvic
  ultrasound and AMH are not diagnostic tests in this age group.
- This module does not diagnose PCOS and does not output a calibrated clinical
  probability. Any research index is explicitly heuristic and unvalidated.
"""
from __future__ import annotations

from typing import Dict, Optional, List, Any
import numpy as np

from src.disease_modules.base import DiseaseModule
from src.data_models import SharedPhysiologicalFeatures, DiseaseModuleResult
from src.config import UserProfile
from src.utils.math_utils import clamp, sigmoid

# Research-only heuristic weights. These are NOT trained/calibrated clinical
# model coefficients and must not be interpreted as odds/probabilities.
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
    """PCOS-associated research phenotyping signal."""

    @property
    def name(self) -> str:
        return "pcos_reproductive_metabolic"

    @property
    def version(self) -> str:
        return "8.6.1"

    @property
    def required_features(self) -> List[str]:
        return ["heart_rate", "hrv_rmssd", "activity_level", "skin_temp_c"]

    @property
    def optional_features(self) -> List[str]:
        return [
            "sleep_duration_h", "sleep_regularity", "circadian_stability",
            "gsr_tonic", "stress_index", "temperature_rhythm_disruption"
        ]

    def __init__(self, profile: Optional[UserProfile] = None):
        self.profile = profile

    def _clinical_context(self, clinical: Optional[Dict] = None) -> Dict[str, Any]:
        c = clinical or {}
        age = c.get("age_years", c.get("age"))
        years_post_menarche = c.get("years_post_menarche")

        irregular = c.get("cycle_irregular")
        if irregular is None:
            irregular = c.get("cycle_irregularity")
        cycle_length = c.get("usual_cycle_length_days", c.get("cycle_length"))
        hyper = bool(
            c.get("clinical_hyperandrogenism")
            or c.get("biochemical_hyperandrogenism")
            or c.get("hirsutism")
            or c.get("severe_acne")
            or c.get("androgen_elevated")
        )
        biochemical_hyper = bool(c.get("biochemical_hyperandrogenism") or c.get("androgen_elevated"))
        pcom = bool(
            c.get("pcom_present")
            or c.get("polycystic_ovary_morphology")
            or c.get("ultrasound_pcom")
            or c.get("amh_elevated")
        )
        exclusions = bool(
            c.get("exclusions_completed")
            or c.get("mimics_excluded")
            or c.get("diagnostic_exclusions_completed")
        )

        # When years-post-menarche is available, use guideline-oriented
        # adolescent cycle thresholds rather than an adult 28-day heuristic.
        irregular_guideline = irregular
        if years_post_menarche is not None and cycle_length is not None:
            try:
                ypm = float(years_post_menarche)
                cl = float(cycle_length)
                if ypm < 1:
                    irregular_guideline = None
                elif ypm < 3:
                    irregular_guideline = cl < 21 or cl > 45
                else:
                    irregular_guideline = cl < 21 or cl > 35
                if ypm >= 1 and cl > 90:
                    irregular_guideline = True
            except (TypeError, ValueError):
                pass

        if irregular is True:
            irregular_guideline = True

        adolescent = years_post_menarche is not None and float(years_post_menarche) < 8
        adult = age is not None and float(age) >= 18

        if adolescent:
            diagnostic_supported = bool(irregular_guideline is True and hyper and exclusions)
            status = "adolescent_supported_context" if diagnostic_supported else "adolescent_at_risk_or_insufficient"
            # Ultrasound/AMH is deliberately excluded from adolescent criteria.
            criterion_groups = int(irregular_guideline is True) + int(hyper)
        elif adult:
            criterion_groups = (
                int(bool(irregular_guideline))
                + int(hyper)
                + int(pcom)
            )
            diagnostic_supported = criterion_groups >= 2 and exclusions
            status = "adult_supported_context" if diagnostic_supported else "adult_insufficient_context"
        else:
            criterion_groups = (
                int(bool(irregular_guideline))
                + int(hyper)
                + int(pcom)
            )
            diagnostic_supported = criterion_groups >= 2 and exclusions and age is not None
            status = "age_unknown_insufficient_context"

        return {
            "age_years": age,
            "years_post_menarche": years_post_menarche,
            "adolescent": adolescent,
            "adult": adult,
            "irregular_cycles": irregular_guideline,
            "hyperandrogenism": hyper,
            "biochemical_hyperandrogenism": biochemical_hyper,
            "pcom_or_amh": pcom,
            "exclusions_completed": exclusions,
            "criterion_groups": criterion_groups,
            "diagnostic_supported_context": diagnostic_supported,
            "status": status,
        }

    def _cycle_score(self, profile: Optional[UserProfile], clinical: Optional[Dict] = None) -> float:
        """Cycle-context score from entered menstrual information only."""
        p = profile or self.profile
        if p is None and not clinical:
            return CYCLE_NEUTRAL

        c = clinical or {}
        length = c.get("usual_cycle_length_days", c.get("cycle_length", getattr(p, "usual_cycle_length_days", None) if p else None))
        irregular = c.get("cycle_irregular", c.get("cycle_irregularity", getattr(p, "cycle_irregular", None) if p else None))
        dslp = c.get("days_since_last_period", getattr(p, "days_since_last_period", None) if p else None)
        years_post_menarche = c.get("years_post_menarche")

        parts: List[float] = []
        if length is not None:
            try:
                cl = float(length)
                if years_post_menarche is not None:
                    ypm = float(years_post_menarche)
                    if ypm < 1:
                        return CYCLE_NEUTRAL
                    abnormal = (cl > 90) or (21 > cl) or (cl > 45 if ypm < 3 else cl > 35)
                    parts.append(100.0 if abnormal else 10.0)
                else:
                    parts.append(clamp(abs(cl - 28.0) / 20.0 * 100.0, 0.0, 100.0))
            except (TypeError, ValueError):
                pass

        if irregular is True:
            parts.append(60.0)
        elif irregular is False:
            parts.append(10.0)

        if dslp is not None:
            try:
                if float(dslp) > 90:
                    parts.append(100.0)
                elif float(dslp) > 35:
                    parts.append(clamp((float(dslp) - 35.0) / 55.0 * 100.0, 0.0, 100.0))
            except (TypeError, ValueError):
                pass

        return float(np.mean(parts)) if parts else CYCLE_NEUTRAL

    def _domain_scores(
        self,
        shared: SharedPhysiologicalFeatures,
        profile: Optional[UserProfile],
        clinical: Optional[Dict],
        ultrasound: Optional[Dict],
    ) -> Dict[str, float]:
        # These domains describe contextual physiology; they are not PCOS
        # diagnostic criteria.
        sleep_risk = 50.0
        if shared.sleep_duration_h is not None:
            h = float(shared.sleep_duration_h)
            if h < 6:
                sleep_risk = clamp((6 - h) / 3 * 100.0, 0, 100)
            elif h > 10:
                sleep_risk = clamp((h - 10) / 2 * 100.0, 0, 100)
            else:
                sleep_risk = 20.0
        if shared.sleep_regularity:
            sleep_risk = 0.7 * sleep_risk + 0.3 * (100.0 - shared.sleep_regularity)

        metabolic = 0.0
        if clinical:
            bmi = clinical.get("bmi") or (profile.bmi if profile else None)
            if bmi is not None and float(bmi) > 25:
                metabolic += clamp((float(bmi) - 25) / 10 * 100.0, 0, 100) * 0.5
            glucose = clinical.get("glucose_mg_dl") or (profile.glucose_mg_dl if profile else None)
            if glucose is not None and float(glucose) > 100:
                metabolic += clamp((float(glucose) - 100) / 50 * 100.0, 0, 100) * 0.5

        if shared.hrv_rmssd is not None and float(shared.hrv_rmssd) < 30:
            metabolic += clamp((30 - float(shared.hrv_rmssd)) / 20 * 100, 0, 100) * 0.3

        stress_autonomic = clamp(max(float(shared.stress_index), float(shared.autonomic_imbalance)), 0, 100)
        circadian = clamp(float(shared.circadian_disruption), 0, 100)
        temp_rhythm = clamp(float(shared.temperature_rhythm_disruption), 0, 100)
        low_activity = clamp(float(shared.low_activity_risk), 0, 100)

        glucose_risk = 0.0
        bp_risk = 0.0
        if clinical:
            g = clinical.get("glucose_mg_dl")
            if g is not None:
                glucose_risk = clamp((float(g) - 90) / 60 * 100, 0, 100) if float(g) > 90 else 0.0
            sys_bp = clinical.get("systolic_bp")
            if sys_bp is not None and float(sys_bp) > 120:
                bp_risk = clamp((float(sys_bp) - 120) / 40 * 100, 0, 100)

        return {
            "cycle": self._cycle_score(profile, clinical),
            "metabolic": clamp(metabolic, 0, 100),
            "glucose": glucose_risk,
            "bp": bp_risk,
            "stress_autonomic": stress_autonomic,
            "sleep": sleep_risk,
            "circadian": circadian,
            "temperature_rhythm": temp_rhythm,
            "low_activity": low_activity,
        }

    def _research_index_from_context(self, d: Dict[str, float]) -> float:
        c = d["cycle"] / 100.0
        m = d["metabolic"] / 100.0
        a = d["stress_autonomic"] / 100.0
        s = d["sleep"] / 100.0
        ci = d["circadian"] / 100.0
        t = d["temperature_rhythm"] / 100.0
        l = d["low_activity"] / 100.0
        g = d["glucose"] / 100.0
        b = d["bp"] / 100.0
        z = (
            INTERCEPT
            + CYCLE_W * c
            + METABOLIC_W * m
            + AUTONOMIC_W * a
            + SLEEP_W * s
            + CIRCADIAN_W * ci
            + TEMPERATURE_W * t
            + GLUCOSE_W * g
            + ACTIVITY_W * l
            + BP_W * b
        )
        return float(clamp(100.0 * sigmoid(z), 0.0, 100.0))

    def predict(
        self,
        shared: SharedPhysiologicalFeatures,
        clinical: Optional[Dict] = None,
        ultrasound: Optional[Dict] = None,
        history: Optional[List] = None,
    ) -> DiseaseModuleResult:
        profile = clinical.get("profile") if clinical and "profile" in clinical else self.profile
        if isinstance(profile, dict):
            p = UserProfile()
            for k, v in profile.items():
                if hasattr(p, k):
                    setattr(p, k, v)
            profile = p

        context = self._clinical_context(clinical)

        # A disease-specific score is not produced when the clinical context
        # is incomplete. This prevents wearable-only pseudo-diagnosis.
        if not context["diagnostic_supported_context"]:
            return DiseaseModuleResult(
                module=self.name,
                version=self.version,
                signal="insufficient_disease_evidence",
                level="unknown",
                confidence=0.0,
                data_quality=self._check_data_quality(shared),
                clinical_validation="NOT ESTABLISHED",
                drivers=[],
                explanation=(
                    "Insufficient disease-specific evidence for an exploratory "
                    "PCOS phenotype signal. Wearable physiology alone is not "
                    "a PCOS diagnostic criterion. Missing evidence remains UNKNOWN."
                ),
                provenance={
                    "clinical_variables": 1.0 if clinical else 0.0,
                    "wearable_physiology": 1.0 if self._check_data_quality(shared) > 0 else 0.0,
                    "ultrasound": 1.0 if ultrasound else 0.0,
                },
                limitations=self.limitations(),
                extra={
                    "score_interpretation": "not produced",
                    "research_index": None,
                    "diagnostic_context": context,
                    "history_observations": len(history or []),
                },
            )

        domains = self._domain_scores(shared, profile, clinical, ultrasound)
        index = self._research_index_from_context(domains)
        level = self._level_from_score(index)
        confidence = min(0.60, self.confidence(shared))
        data_quality = self._check_data_quality(shared)

        sorted_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)
        drivers = [
            {
                "domain": name,
                "score": round(float(score), 1),
                "contribution": f"{name} {score:.0f}% context signal",
                "type": "clinical" if name == "cycle" else "physiological_context",
            }
            for name, score in sorted_domains[:3]
        ]

        explanation = (
            f"Exploratory physiological-context index: {index:.1f}% ({level}). "
            "This is a heuristic, uncalibrated research index after disease-specific "
            "clinical context gating; it is not a diagnostic probability. "
            "Wearable physiology contributes context only."
        )

        return DiseaseModuleResult(
            module=self.name,
            version=self.version,
            signal="pcos_context_signal",
            level=level,
            confidence=confidence,
            data_quality=data_quality,
            clinical_validation="NOT ESTABLISHED",
            drivers=drivers,
            explanation=explanation,
            provenance={
                "clinical_variables": 0.45,
                "wearable_physiology": 0.30,
                "longitudinal": 0.15 if history and len(history) > 10 else 0.0,
                "ultrasound": 0.10 if ultrasound else 0.0,
            },
            limitations=self.limitations(),
            extra={
                "domain_scores": domains,
                "research_index": index,
                "research_index_is_probability": False,
                "diagnostic_context": context,
                "history_observations": len(history or []),
                "output_type": "exploratory_research_signal",
                "diagnostic_use": False,
            },
        )

    def limitations(self) -> str:
        return (
            "Research-only PCOS-associated physiological-context module. It is "
            "not a diagnostic test and does not output a calibrated clinical "
            "probability. Wearable physiology alone cannot diagnose PCOS. "
            "Adult diagnostic assessment should use an appropriate evidence-based "
            "clinical pathway and exclude mimicking disorders. In adolescents, "
            "diagnostic assessment differs from adults and ultrasound/AMH should "
            "not be used for PCOS diagnosis. Clinical validation of this software "
            "module is NOT ESTABLISHED."
        )
