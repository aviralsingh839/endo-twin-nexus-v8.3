"""Shared pure-Python logic for the V8.7 unified workstation."""
from __future__ import annotations
from typing import Optional
from src.data_models import SharedPhysiologicalFeatures
from src.disease_modules.pcos import PCOSModule

DISCLAIMER = "Research-only physiological context signal — not a PCOS/PCOD diagnosis or clinical probability."

def disease_context(patient: dict) -> dict:
    return {
        "age_years": patient.get("age_years"),
        "age": patient.get("age_years"),
        "bmi": patient.get("bmi"),
        "cycle_irregular": patient.get("cycle_irregular"),
        "usual_cycle_length_days": patient.get("cycle_length"),
        "years_post_menarche": patient.get("years_post_menarche"),
        "clinical_hyperandrogenism": patient.get("hyperandrogenism"),
        "biochemical_hyperandrogenism": patient.get("biochemical_hyperandrogenism"),
        "pcom_present": patient.get("pcom_present"),
        "exclusions_completed": patient.get("exclusions_completed"),
        "glucose_mg_dl": patient.get("glucose_mg_dl"),
        "systolic_bp": patient.get("systolic_bp"),
        "diastolic_bp": patient.get("diastolic_bp"),
    }

def context_ready(patient: dict) -> tuple[bool, str]:
    c = disease_context(patient)
    age = c.get("age_years")
    if age is None:
        return False, "Age is missing."
    try:
        adult = float(age) >= 18
    except (TypeError, ValueError):
        return False, "Age is invalid."
    if not bool(c.get("exclusions_completed")):
        return False, "Diagnostic exclusions are not marked complete."
    cycle = bool(c.get("cycle_irregular"))
    hyper = bool(c.get("clinical_hyperandrogenism") or c.get("biochemical_hyperandrogenism"))
    pcom = bool(c.get("pcom_present"))
    if adult and (int(cycle) + int(hyper) + int(pcom) < 2):
        return False, "Need at least two disease-evidence groups for an exploratory adult context signal."
    if not adult and not (cycle and hyper):
        return False, "Adolescent exploratory context requires irregular cycles plus hyperandrogenism evidence."
    return True, "Disease-specific evidence gate satisfied."

def build_shared_from_feature(feature, source: str | None = None) -> SharedPhysiologicalFeatures:
    src = source or getattr(feature, "_source", None)
    demo = src == "demo"
    return SharedPhysiologicalFeatures(
        timestamp_s=feature.timestamp_s,
        heart_rate=feature.hr_bpm,
        resting_heart_rate=feature.resting_hr_bpm,
        hrv_rmssd=feature.rmssd_ms,
        hrv_sdnn=feature.sdnn_ms,
        activity_level=feature.activity_level,
        motion_index=feature.motion_index,
        low_activity_risk=feature.low_activity_risk,
        sleep_duration_h=feature.sleep_duration_h,
        sleep_regularity=feature.sleep_regularity,
        sleep_timing_h=feature.sleep_timing_h,
        sleep_probability=feature.sleep_probability,
        circadian_stability=feature.circadian_stability_index,
        circadian_disruption=feature.circadian_disruption,
        skin_temp_c=feature.skin_temp_c,
        temperature_trend_c_per_day=feature.temp_slope_c_per_min * 1440.0,
        temperature_rhythm_disruption=feature.temperature_rhythm_disruption,
        gsr_tonic=feature.gsr_tonic,
        stress_index=feature.stress_index,
        autonomic_imbalance=feature.autonomic_imbalance,
        recovery_score=50.0,
        sensor_quality=feature.quality_per_feature or {},
        overall_quality=feature.signal_quality,
        provenance={
            "heart_rate": "DEMO_DATA" if demo else ("MEASURED" if feature.hr_bpm is not None else "UNKNOWN"),
            "hrv_rmssd": "DEMO_DATA" if demo else ("DERIVED" if feature.rmssd_ms is not None else "UNKNOWN"),
            "skin_temp_c": "DEMO_DATA" if demo else ("MEASURED" if feature.skin_temp_c is not None else "UNKNOWN"),
            "activity_level": "DEMO_DATA" if demo else ("DERIVED" if feature.activity_level is not None else "UNKNOWN"),
        },
    )

def compute_research_index(patient: dict, feature, module: Optional[PCOSModule] = None, source: str | None = None):
    ready, reason = context_ready(patient)
    if not ready:
        return None, None, reason
    if feature is None:
        return None, None, "Waiting for live feature data."
    result = (module or PCOSModule()).predict(
        build_shared_from_feature(feature, source),
        disease_context(patient),
        ultrasound=None,
        history=[],
    )
    index = result.extra.get("research_index", result.extra.get("risk_percent"))
    return index, result, result.explanation
