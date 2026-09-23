# CHRONO-PCOS Model - First Disease-Specific Model on ENDO-TWIN Platform

## One Sentence

**ENDO-TWIN is the platform; CHRONO-PCOS is its first disease-specific model.**

## Overview

CHRONO-PCOS is first disease-specific implementation running on ENDO-TWIN-ready architecture.

- Location: `disease_models/chrono_pcos/`
- Implements: `DiseaseModel` interface
- Preserves: Original PCOS functionality from `src/disease_modules/pcos.py`
- General functionality belongs in ENDO-TWIN Core
- PCOS-specific functionality belongs here

## Manifest

```python
name: chrono_pcos
version: 8.3+
display_name: CHRONO-PCOS
description: PCOS/PCOD risk pre-screening research module - first disease-specific implementation on ENDO-TWIN platform
category: endocrine
required_features: heart_rate, hrv_rmssd, activity_level, skin_temp_c
capabilities: pcos_risk_signal, circadian_analysis, autonomic_analysis, metabolic_context, longitudinal_tracking, chrono_metabolic_fingerprinting, ultrasound_analysis, cycle_tracking, symptom_analysis
limitations: Research-only, not diagnostic, Rotterdam criteria requires clinician, not clinically validated, PPG-derived HRV less accurate than ECG, etc.
clinical_validation: NOT ESTABLISHED - Engineering validation only
```

## Original Functionality Preserved

### Audit of Original PCOS Application

Original PCOS application contains:

**Screens/Workflows**:
- Overview: personal physiological status
- Baseline: what is normal for user
- Trends: changes over time
- Health Signals: PCOS, Sleep, Cardiometabolic, Autonomic
- Data Quality: sensor status and confidence
- Clinical Inputs: manual clinical measurements
- Ultrasound: image and structured features
- Explanation: why system generated signal
- Report: research report
- Validation: engineering vs clinical

**Scientific Modules**:
- PCOSModule v8.3.0 - pcos_reproductive_metabolic
- SleepModule - circadian disruption
- CardiometabolicModule - cardiometabolic risk signal
- AutonomicModule - autonomic regulation signal
- PersonalBaselineEngine - mean, median, std, MAD, rolling, confidence, min obs, circadian context
- LongitudinalEngine - rolling windows, persistence, trend, change-point, recovery
- RealtimeFeatureExtractor - HR, HRV RMSSD/SDNN/pNN50, , motion, temp
- SharedFeatureExtractor - shared physiological representation
- SensorQualityControl - value, quality, source, timestamp, artifact
- FusionEngine - MultimodalFusion confidence weighted quality
- ExplanationEngine - drivers, baseline deviations, trends
- ChronoMetabolicFingerprint - circadian, autonomic, variability, activity, temp, metabolic, longitudinal

**Sensors**:
- MAX30102 PPG IR+RED HR SpO2 pulse amplitude - 20Hz $CP3
- MPU6050 motion ax ay az gx gy gz motion index activity level
- DS18B20 skin temp room temp temp slope
-  per min
- ECG Mega Hub (expanded lab)
- BME280 environmental (Mega Hub)

**Signal Processing**:
- Filtering bandpass 0.5-4Hz PPG lowpass baseline motion lowpass temp median 
- Baseline Removal PPG drift  temp baseline
- Artifact Detection motion MPU6050 correlation PPG amplitude HR outlier temp jumps
- Missing Handling short gaps interpolation quality penalty long gaps mark missing not fabricate
- Quality Control 0-1 per channel

**AI/ML**:
- Dataset public PCOS_data.csv 541 rows PUBLIC DATASET, wrist_ppg_during_exercise s1-s9, synthetic 10 subjects 30 days 6 scenarios 60 days wrist_ppg SYNTHETIC
- Training ModelTrainer subject-level split not row-level avoid leakage
- Validation ModelEvaluator Train/Validation/Test split
- Model Registry name, version, dataset version, training date, features, target, metrics, validation strategy, limitations
- Explainability ShapExplainer feature drivers SHAP values
- Modules PCOS, Sleep, Cardiometabolic, Autonomic with consistent API

**Ultrasound**:
- Pipeline IMAGE IMPORT → VALIDATION → PREPROCESSING → IMAGE ANALYSIS → FEATURE EXTRACTION → MODEL → UNCERTAINTY → REPORT
- Quality gate UNKNOWN by design unless computed
- Provenance CLINICALLY-ENTERED vs IMAGE-DERIVED fusion weight 0.20
- Every result labelled IMAGE-DERIVED

**Reports**:
- Professional reports with Research / risk-screening output — not a medical diagnosis
- Model transparency name/version/input/data quality/confidence/features/limitations
- Clearly separate MEASURED CLINICALLY ENTERED IMAGE-DERIVED MODEL-INFERRED DEMO_DATA UNKNOWN

**Database**:
- LocalDatabase 18 tables + EndoTwinDatabase 15+ tables
- Stable IDs CP-0001 DEMO-001 PXXXXX, foreign keys, patient-scoped queries, no cross-patient contamination
- Multi-patient safety DEMO-001/002/003 isolation PASS 7 FAIL 0

**Patient Management**:
- Create, search, open, archive, history
- Patient workspace scoped to patient_id

**Doctor Workflow**:
- Dashboard, patient management, physiological data, advanced analysis, ultrasound, longitudinal, notes, reports, provenance, explanation, database, diagnostics

**Demos**:
- Demo mode strong workflow DEMO PATIENT→Simulated sensor→Signal→AI→Fingerprint→Ultrasound→Screening→Doctor dashboard→Report labeled DEMO/SIMULATED
- Science-fair 16 steps integrated ecosystem
- Full showcase GUI 16 steps + ENDO-TWIN architecture

### Migration

**GENERAL** → ENDO-TWIN Core (`src/endo_twin/`):

- patient management → `src/endo_twin/core/patient.py` PatientIdentity
- sensors → `src/endo_twin/physiology/` general
- signal acquisition → `src/serial_io/` preserved
- signal processing → `src/signal_processing/` + `src/endo_twin/signals/` general
- feature extraction → `src/core/feature_extraction.py` + `src/endo_twin/features/` general
- baseline → `src/core/personal_baseline.py` + `src/endo_twin/baseline/` general
- longitudinal analysis → `src/core/longitudinal_engine.py` + `src/endo_twin/longitudinal/` general
- database → `database/` general + disease-specific references disease_model_id
- reports → `reports/` general + `disease_models/chrono_pcos/reports/` specific
- provenance → `endo_twin/provenance/` + `src/endo_twin/provenance/` general
- model registry → `endo_twin/registry/` + `src/endo_twin/models/model_registry.py` general + disease
- uncertainty → `endo_twin/uncertainty/` + `src/endo_twin/uncertainty/` general
- visualization → `src/ui/` general

**PCOS-SPECIFIC** → CHRONO-PCOS (`disease_models/chrono_pcos/`):

- PCOS features → `disease_models/chrono_pcos/features/pcos_features.py` cycle_length, cycle_irregularity, pcos_symptoms, chrono_metabolic_pcos
- PCOS risk logic → `disease_models/chrono_pcos/model/chrono_pcos_model.py` _cycle_score, _domain_scores, _risk_from_scores
- PCOS model → `disease_models/chrono_pcos/model/chrono_pcos_model.py` ChronoPCOSDiseaseModel implements DiseaseModel
- PCOS-specific ultrasound → `disease_models/chrono_pcos/ultrasound/pcos_ultrasound.py` cyst_size_mm, ovarian_volume_cc, cyst_count - Rotterdam criteria
- Chrono-Metabolic PCOS interpretation → `disease_models/chrono_pcos/chrono_metabolic/pcos_chrono_metabolic.py` circadian, autonomic, metabolic patterns interpreted for PCOS research
- PCOS-specific reports → `disease_models/chrono_pcos/reports/pcos_reports.py` extends general report with PCOS analysis

## Model Interface

Implements `DiseaseModel`:

```python
@property
def manifest(self) -> DiseaseModelManifest:
    return CHRONO_PCOS_MANIFEST

def validate_input(features, clinical_data, imaging_data) -> {valid, missing, warnings, quality}
    # Check required features: heart_rate, hrv_rmssd, activity_level, skin_temp_c
    # Check quality, clinical data, warnings

def analyze(features, clinical_data, imaging_data, longitudinal_data, baseline_data, patient_id) -> DiseaseModelResult
    # Convert general features dict to SharedPhysiologicalFeatures
    # Use original PCOSModule.predict() internally to preserve functionality
    # Convert to general DiseaseModelResult
    # Fallback if original not available

def explain(result) -> str
def generate_report(result, include_disclaimer) -> Dict
def get_uncertainty(result) -> Dict
def get_limitations() -> str
```

## Original Logic Preserved

From `src/disease_modules/pcos.py`:

- Domain weights: CYCLE_W 1.20, METABOLIC_W 0.90, AUTONOMIC_W 0.60, SLEEP_W 0.50, CIRCADIAN_W 0.50, TEMPERATURE_W 0.35, GLUCOSE_W 0.35, ACTIVITY_W 0.30, BP_W 0.20, INTERCEPT -3.0
- _cycle_score: cycle irregularity 0-100 from self-reported info only, length, days since last period, irregular
- _domain_scores: sleep risk, metabolic, stress_autonomic, circadian, temperature_rhythm, low_activity, glucose_risk, bp_risk, cycle
- _risk_from_scores: sigmoid with weights, clamp 0-100
- predict: provenance breakdown clinical_variables, wearable_physiology, longitudinal, ultrasound, metabolic, level from score, confidence, data quality, drivers, explanation
- limitations: Research-only, Rotterdam criteria, wearable alone cannot diagnose, ultrasound UNKNOWN by design, not clinically validated

All preserved in new ChronoPCOSDiseaseModel.

## Acceptance Tests

**TEST 5**: Open CHRONO-PCOS. Original useful PCOS functionality must still exist. PASS = migration preserved scientific functionality.

- ChronoPCOSDiseaseModel uses original PCOSModule internally
- Original logic preserved
- Features: cycle_length, cycle_irregularity, pcos_symptoms, chrono_metabolic_pcos
- Risk logic: cycle score, domain scores, risk from scores
- Model: PCOSModule v8.3.0
- Ultrasound: cyst_size_mm, ovarian_volume_cc, cyst_count
- Chrono-Metabolic: circadian, autonomic, metabolic interpretation for PCOS
- Reports: PCOS-specific reports

## Safety

- Research-only PCOS-associated risk signal, not diagnostic test
- PCOS diagnosis requires clinical evaluation using Rotterdam criteria by qualified professional
- Wearable physiology alone cannot diagnose PCOS
- Ultrasound features UNKNOWN by design until validated labelled dataset exists
- Model not clinically validated
- Never claim diagnosis, clinical validation, medical accuracy, diagnostic sensitivity specificity, clinical superiority, regulatory approval unless actual documented evidence exists
- Always distinguish MEASURED CLINICALLY_ENTERED IMAGE-DERIVED MODEL-INFERRED DEMO_DATA UNKNOWN
- Never represent model inference as measurement
- Never represent simulated data as real patient data
- Never fabricate ML metrics, clinical records

## One Sentence

**ENDO-TWIN is the platform; CHRONO-PCOS is its first disease-specific model.**
