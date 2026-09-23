"""
CHRONO-PCOS Manifest - Describes the disease model

ENDO-TWIN is the platform, CHRONO-PCOS is its first disease-specific model.
"""

from src.endo_twin.models.disease_model_interface import DiseaseModelManifest, DiseaseModelCategory

CHRONO_PCOS_MANIFEST = DiseaseModelManifest(
    name="chrono_pcos",
    version="8.6.1",
    display_name="CHRONO-PCOS",
    description="PCOS/PCOD disease-specific research-context module - first disease-specific implementation on ENDO-TWIN platform. Combines physiological sensing, longitudinal context, clinical inputs, and optional imaging evidence for exploratory research signals; not diagnosis.",
    category=DiseaseModelCategory.ENDOCRINE,
    author="ENDO-TWIN Research - Class 11 Research Innovation",
    required_features=["heart_rate", "hrv_rmssd", "activity_level", "skin_temp_c"],
    optional_features=[
        "sleep_duration_h", "sleep_regularity", "circadian_stability",
        "stress_index", "temperature_rhythm_disruption",
        "cycle_length", "cycle_irregularity", "bmi", "age"
    ],
    capabilities=[
        "pcos_risk_signal",
        "circadian_analysis",
        "autonomic_analysis",
        "metabolic_context",
        "longitudinal_tracking",
        "chrono_metabolic_fingerprinting",
        "ultrasound_analysis",
        "cycle_tracking",
        "symptom_analysis"
    ],
    limitations=(
        "Research-only PCOS-associated risk signal. Not a diagnostic test. "
        "PCOS diagnosis requires clinical evaluation using Rotterdam criteria "
        "(oligo-anovulation, hyperandrogenism, polycystic ovaries) by qualified professional. "
        "Wearable physiology alone cannot diagnose PCOS. "
        "Ultrasound features are UNKNOWN by design until validated labelled dataset exists. "
        "Model not clinically validated. "
        "PPG-derived HRV less accurate than ECG. "
        "Skin temp not core temp. "
        "Wrist activity not whole-body calorimetry. "
        "Sleep-wake from wrist PPG model-inferred not polysomnography. "
        "Chrono-metabolic fingerprint experimental research, not diagnosis."
    ),
    clinical_validation="NOT ESTABLISHED - Engineering validation only",
    data_requirements="PPG HR, HRV, activity, temperature, clinical cycle info, optional ultrasound",
    version_history=[
        {"version": "V0", "status": "CONCEPT", "description": "Original PCOS concept"},
        {"version": "V1-V3", "status": "IMPLEMENTED", "description": "Basic sensing, signal processing, multi-sensor"},
        {"version": "V4-V6", "status": "IMPLEMENTED", "description": "Baseline, longitudinal, disease modules, fusion"},
        {"version": "V7", "status": "IMPLEMENTED", "description": "UI & Reports"},
        {"version": "V8", "status": "IMPLEMENTED", "description": "CHRONO-TWIN NEXUS modular"},
        {"version": "V8.1", "status": "IMPLEMENTED", "description": "PCOS-focused longitudinal phenotyping + ultrasound"},
        {"version": "V8.3+", "status": "IMPLEMENTED", "description": "Full ecosystem Patient/Doctor Android/Doctor PC/Local DB/Care/Website"},
        {"version": "V8.3+ → ENDO-TWIN", "status": "IMPLEMENTED", "description": "General platform ENDO-TWIN + CHRONO-PCOS as first disease model"}
    ]
)
