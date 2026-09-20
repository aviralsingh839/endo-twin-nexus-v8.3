# ENDO-TWIN V8.5 — Current Operating Path

ENDO-TWIN is the personalized physiological modelling platform; CHRONO-PCOS is its first disease-specific research module.

## Start
\`\`\`bash
./START.sh
\`\`\`

## Workstations
\`\`\`bash
./START.sh doctor
./START.sh patient-pc
\`\`\`

## Android
\`\`\`bash
./setup_android.sh
./build_apks.sh all
\`\`\`

## Mobile connection
Doctor Workstation → Mobile Link → address + 6-digit code.
Patient Android → Connect → Pair → Send latest session.

The bridge is local-LAN research infrastructure, not production clinical security.

---

# ENDO-TWIN - Personalized Physiological Modelling Platform
### CHRONO-PCOS is First Disease-Specific Model
### **Sense • Model • Predict • Personalize • Connect**

> **One Sentence: ENDO-TWIN is the platform; CHRONO-PCOS is its first disease-specific model.**
> **Research Prototype, Not a Medical Device, Not Clinically Validated, Not a Diagnosis**

---

## What is ENDO-TWIN?

**ENDO-TWIN is a general personalized physiological modelling platform.**

**CHRONO-PCOS is the FIRST disease-specific model/module available inside ENDO-TWIN.**

ENDO-TWIN provides:

- General physiological monitoring
- General patient data
- General measurements
- General longitudinal tracking
- General personal baseline
- General signal processing
- General multimodal fusion
- General AI/ML infrastructure
- General reports
- General patient/doctor workflows

AND THEN optionally:

- Disease-specific models

First available disease model: **CHRONO-PCOS** - PCOS/PCOD risk pre-screening research module.

Future disease models should plug into same platform without rewriting core.

---

## Brand / UI

Main application is general-purpose, not PCOS-only.

Identity:

```
ENDO-TWIN
Personalized Physiological Modelling Platform
Understand your physiological patterns over time.
```

Home/dashboard communicates:

```
"Understand your physiological patterns over time."
```

Rather than "PCOS detection" unless user explicitly selected CHRONO-PCOS model.

---

## General Application

Main application contains general sections:

- **Dashboard** - Personal Physiological Overview - general
- **My Profile** - General patient data - minimal collection
- **Measurements** - General measurements - HR, HRV, activity, temp, GSR - MEASURED with quality
- **Sensors** - General sensors - MAX30102 PPG, MPU6050 motion, DS18B20 temp, GSR - 20Hz $CP2
- **Health Timeline** - Chronological health events - sensor session, symptom entry, clinical entry, imaging, analysis, model run, report
- **Personal Baseline** - What is normal for YOU - mean, median, std, MAD, rolling, confidence, min obs, circadian context - learns what is normal for individual first
- **Trends** - Longitudinal trends - daily, weekly, monthly - never fabricate trends
- **Physiological Patterns** - Circadian, autonomic, metabolic, activity, temperature - multisystem interaction, chrono-metabolic fingerprinting general concept
- **Sleep/Circadian** - General sleep - sleep regularity, circadian disruption pattern - MODEL-INFERRED experimental
- **Activity** - General activity - motion index, activity level - MEASURED
- **Stress/Autonomic** - General stress - HRV RMSSD + GSR tonic/phasic - derived + experimental
- **Metabolic Data** - General metabolic - multimodal HR, HRV, activity, temp, GSR hypothesized - experimental
- **Reports** - General reports - professional with provenance MEASURED/CLINICALLY_ENTERED/IMAGE-DERIVED/MODEL-INFERRED/DEMO_DATA/UNKNOWN, uncertainty, limitations, disclaimer
- **AI & Models** - General Physiological Models, Personal Baseline Models, Longitudinal Models, Disease Models
- **Disease Models** - Plugin architecture - CHRONO-PCOS first, future models concept
- **Doctor Sharing** - Controlled sharing/export - deliberate not automatic
- **Data & Privacy** - Local-first, offline, privacy-focused, no cloud upload private health
- **Settings** - General settings

Exact terminology adapted to existing implementation.

---

## Disease Model System - Plugin Architecture

```
Disease Models

├── CHRONO-PCOS (first, IMPLEMENTED)
│   ├── Overview
│   ├── PCOS-specific analysis
│   ├── Chrono-Metabolic PCOS interpretation
│   ├── Ultrasound PCOS analysis
│   ├── PCOS research model
│   └── PCOS report
│
├── Future Model A (concept, dummy for extensibility test)
├── Future Model B (concept)
└── Future Model C (concept)
```

Main ENDO-TWIN application works even when no disease model selected - **TEST 3 PASS**.

### Disease Model Interface

```python
class DiseaseModel:
    name: str
    version: str
    display_name: str
    description: str
    required_features: List[str]
    
    def validate_input(features, clinical_data, imaging_data) -> {valid, missing, warnings, quality}
    def analyze(features, clinical_data, imaging_data, longitudinal_data, baseline_data, patient_id) -> DiseaseModelResult
    def explain(result) -> str
    def generate_report(result, include_disclaimer) -> Dict
    def get_uncertainty(result) -> Dict
    def get_limitations() -> str
```

CHRONO-PCOS implements this interface.
Future disease models implement same interface.
Core does NOT depend directly on CHRONO-PCOS.

Location: `src/endo_twin/models/disease_model_interface.py`

Registry: `src/endo_twin/models/model_registry.py` - manages general + disease models.

---

## CHRONO-PCOS Migration - First Disease Model

Existing original PCOS application migrated into:

```
disease_models/chrono_pcos/
├── __init__.py
├── manifest.py - CHRONO_PCOS_MANIFEST
├── model/
│   └── chrono_pcos_model.py - ChronoPCOSDiseaseModel implements DiseaseModel
├── features/
│   └── pcos_features.py - PCOS-specific features: cycle_length, cycle_irregularity, pcos_symptoms, chrono_metabolic_pcos
├── ultrasound/
│   └── pcos_ultrasound.py - PCOS-specific ultrasound: cyst_size_mm, ovarian_volume_cc, cyst_count - Rotterdam criteria
├── chrono_metabolic/
│   └── pcos_chrono_metabolic.py - PCOS-specific chrono-metabolic interpretation
├── reports/
│   └── pcos_reports.py - PCOS-specific reports extends general
└── tests/
```

**BUT** not simply moving entire old folder.

Separated:

**GENERAL** (ENDO-TWIN Core - `src/endo_twin/`):

- patient management → `src/endo_twin/core/patient.py` PatientIdentity
- sensors → `src/endo_twin/physiology/` general
- signal acquisition → `src/serial_io/` preserved
- signal processing → `src/signal_processing/` + `src/endo_twin/signals/` general
- feature extraction → `src/core/feature_extraction.py` + `src/endo_twin/features/` general
- baseline → `src/core/personal_baseline.py` + `src/endo_twin/baseline/` general
- longitudinal analysis → `src/core/longitudinal_engine.py` + `src/endo_twin/longitudinal/` general
- database → `database/` general + disease-specific references disease_model_id
- reports → `reports/` general + `disease_models/chrono_pcos/reports/` specific
- provenance → `endo_twin/provenance/` + `src/endo_twin/provenance/` general - MEASURED/CLINICALLY_ENTERED/IMAGE-DERIVED/MODEL-INFERRED/DEMO_DATA/UNKNOWN first-class
- model registry → `endo_twin/registry/` + `src/endo_twin/models/model_registry.py` general + disease
- uncertainty → `endo_twin/uncertainty/` + `src/endo_twin/uncertainty/` general
- visualization → `src/ui/` general

**PCOS-SPECIFIC** (CHRONO-PCOS - `disease_models/chrono_pcos/`):

- PCOS features
- PCOS risk logic
- PCOS model
- PCOS-specific ultrasound analysis
- Chrono-Metabolic PCOS interpretation
- PCOS-specific reports

### Important: Do NOT Lose Original Application

Original PCOS application's useful functionality is valuable.

Audited:

- screens: Overview, Baseline, Trends, Health Signals (PCOS, Sleep, Cardiometabolic, Autonomic), Data Quality, Clinical Inputs, Ultrasound, Explanation, Report, Validation
- workflows: sensor connection, guided measurement, symptom logging, cycle tracking, results, reports, sharing, find care
- scientific modules: PCOSModule v8.3.0, SleepModule, CardiometabolicModule, AutonomicModule, PersonalBaselineEngine, LongitudinalEngine, RealtimeFeatureExtractor, SharedFeatureExtractor, SensorQualityControl, FusionEngine, ExplanationEngine, ChronoMetabolicFingerprint
- sensors: MAX30102 PPG IR+RED HR SpO2 pulse amplitude 20Hz $CP2, MPU6050 motion ax ay az gx gy gz motion index activity level, DS18B20 skin temp room temp temp slope, GSR raw tonic phasic, ECG Mega Hub, BME280 environmental
- signal processing: filtering bandpass 0.5-4Hz PPG lowpass baseline motion lowpass temp median GSR lowpass tonic highpass phasic, baseline removal, artifact detection motion MPU6050 correlation PPG amplitude HR outlier GSR jumps, missing handling short gaps interpolation quality penalty long gaps mark missing not fabricate, quality control 0-1 per channel
- AI/ML: dataset public PCOS_data.csv 541 rows PUBLIC DATASET wrist_ppg_during_exercise s1-s9 synthetic 10 subjects 30 days 6 scenarios 60 days wrist_ppg SYNTHETIC, training ModelTrainer subject-level split not row-level avoid leakage, validation ModelEvaluator Train/Validation/Test split, model registry name/version/dataset version/training date/features/target/metrics/validation strategy/limitations, explainability ShapExplainer, modules PCOS Sleep Cardiometabolic Autonomic with consistent API
- ultrasound: pipeline IMAGE IMPORT → VALIDATION → PREPROCESSING → IMAGE ANALYSIS → FEATURE EXTRACTION → MODEL → UNCERTAINTY → REPORT, quality gate UNKNOWN by design unless computed, provenance CLINICALLY-ENTERED vs IMAGE-DERIVED fusion weight 0.20, every result labelled IMAGE-DERIVED
- reports: professional with Research / risk-screening output — not a medical diagnosis, model transparency name/version/input/data quality/confidence/features/limitations
- database: LocalDatabase 18 tables + EndoTwinDatabase 15+ tables stable IDs CP-0001 DEMO-001 PXXXXX foreign keys patient-scoped queries no cross-patient contamination multi-patient safety DEMO-001/002/003 isolation PASS 7 FAIL 0
- patient management: create, search, open, archive, history, patient workspace scoped to patient_id
- doctor workflow: dashboard, patient management, physiological data, advanced analysis, ultrasound, longitudinal, notes, reports, provenance, explanation, database, diagnostics
- demos: demo mode strong workflow DEMO PATIENT→Simulated sensor→Signal→AI→Fingerprint→Ultrasound→Screening→Doctor dashboard→Report labeled DEMO/SIMULATED, science-fair 16 steps integrated ecosystem, full showcase GUI 16 steps + ENDO-TWIN architecture

Then migrated each component appropriately.

Do not replace working functionality with empty placeholder screens.

---

## Main Dashboard - General

Main dashboard is general:

```
--------------------------------
ENDO-TWIN
Personal Physiological Overview
--------------------------------
Tagline: Understand your physiological patterns over time.

Personal Baseline [ View ]
- What is normal for YOU first

Today's Measurements [ View ]
- HR, HRV, activity, temperature, GSR

Longitudinal Trends [ View ]
- Personal baseline → time series → change → persistence → recovery → context

Physiological Patterns [ View ]
- Circadian, autonomic, metabolic, activity, temperature

AI & Models [ View ]
- General Physiological Models, Personal Baseline Models, Longitudinal Models, Disease Models

Disease Models [ View ]
- CHRONO-PCOS (first, implemented)
- Future models (concept, extensible)

Reports [ View ]
- Professional reports with provenance, uncertainty

Doctor Sharing [ View ]
- Controlled sharing

--------------------------------

If CHRONO-PCOS is enabled:

Disease Models
→ CHRONO-PCOS
→ Open Analysis

But main dashboard itself remains general.
```

Implementation: `apps/main/main_app.py` - EndoTwinMainApp general platform, dashboard general, disease models plugin.

---

## AI & Models - General

Not hard-coded around PCOS:

```
AI & Models

├── General Physiological Models
│   ├── Personal Baseline Engine
│   ├── Longitudinal Engine
│   ├── Physiological State
│   ├── Signal Processing
│   ├── Feature Extraction
│   └── Chrono-Metabolic Fingerprinting (general concept)
│
├── Personal Baseline Models
│   ├── Baseline learning
│   ├── Deviation detection
│   └── 6 scenarios: stable LOW CHANGE, gradual EARLY CHANGE, persistent PERSISTENT MULTIMODAL, temporary TEMPORARY EVENT, sensor failure LOW SENSOR CONFIDENCE, recovery RECOVERY TREND
│
├── Longitudinal Models
│   ├── Rolling windows
│   ├── Persistence
│   └── Trend, change-point, recovery
│
└── Disease Models (Plugin)
      ├── CHRONO-PCOS (first, implemented)
      └── Future models (concept, extensible)
```

Allows future models to be added without rewriting application.

Implementation: `src/endo_twin/models/model_registry.py` - ModelRegistry manages general + disease.

---

## ENDO-TWIN Core - Reusable Infrastructure

Provides:

- Patient - general patient, stable IDs, enabled_disease_models list
- Observation - general clinical observation
- Measurement - general measurement - type, value, unit, quality, provenance, source
- SensorReading - raw sensor reading - sensor_type, values, quality
- Signal - general signal
- Feature - general feature - name, value, category (established_measurement, derived_feature, experimental_research, ml_prediction, clinical_interpretation)
- Baseline - general personal baseline - mean, median, std, confidence, min_observations
- TimelineEvent - general timeline event - event_type, title, description, timestamp
- LongitudinalSeries - general longitudinal series - data_points, trend, persistence, change_detected
- Model - general model
- Prediction - general prediction
- Explanation - general explanation
- Uncertainty - general uncertainty - data quality, model confidence, limitations
- Provenance - general provenance - MEASURED, CLINICALLY_ENTERED, IMAGE-DERIVED, MODEL-INFERRED, DEMO_DATA, UNKNOWN
- Report - general report

No PCOS-specific assumptions in these classes.

Location: `src/endo_twin/core/patient.py`, `src/endo_twin/core/measurement.py`, `src/endo_twin/core/twin_core.py`, etc.

---

## General Data Model

Database supports general physiological data:

```
patients - general patient data, stable IDs CP-0001 DEMO-001 PXXXXX, enabled_disease_models, extensions
measurements - general measurements, patient_id, session_id, measurement_type, value, quality, provenance MEASURED/CLINICALLY_ENTERED/IMAGE-DERIVED/MODEL-INFERRED/DEMO_DATA/UNKNOWN, source, confidence
signals - general signals
features - general features, patient_id, feature_name, category established_measurement/derived_feature/experimental_research/ml_prediction/clinical_interpretation, quality, provenance
baselines - general baselines, patient_id, feature_name, mean, median, std, confidence, min_observations
timeline_events - general timeline, patient_id, event_type sensor_session/symptom_entry/clinical_entry/imaging/analysis/model_run/report_generated, title, description
symptoms - general symptoms, patient_id, type, severity
clinical_observations - general clinical, patient_id, type, data
imaging - general imaging, patient_id, image_path, quality, provenance IMAGE-DERIVED
model_runs - general model runs, patient_id, model_name, version, input, output, confidence, clinical_validation NOT ESTABLISHED, provenance MODEL-INFERRED
predictions - general predictions
reports - general reports, patient_id, type, content, patient-scoped
audit_events - general audit, patient_id, user_id, action, timestamp
provenance - general provenance tracking
```

Disease-specific data references:

```
disease_model_id
patient_id
```

Example: `disease_models/chrono_pcos/` references patient_id and disease_model_id = chrono_pcos.

---

## Application Navigation - General

Navigation communicates:

```
GENERAL HEALTH / PHYSIOLOGY
        ↓
PERSONAL BASELINE
        ↓
LONGITUDINAL DATA
        ↓
AI & MODELS
        ↓
DISEASE MODELS
        ↓
CHRONO-PCOS
```

Rather than making every screen PCOS-specific.

---

## Doctor Application - General

Doctor Desktop and Doctor Android also general.

Doctor selects:

```
Patient
↓
General physiological overview
↓
Measurements
↓
Timeline
↓
Baseline
↓
Trends
↓
Models
↓
Disease Models
↓
CHRONO-PCOS
```

This prevents doctor application from becoming permanently tied to PCOS.

Implementation: `desktop/doctor_app/main_enhanced.py` - Doctor PC full workstation patient workspace scoped to patient_id, now general with disease models section.

---

## Patient Application - General

Patient Android primarily general:

- Home - General - Today's overview, data collection status, sensor/device status, recent measurements, signal quality, personal baseline status, longitudinal change - understandable language Data quality Good
- Measurements - General - HR, HRV, PPG, GSR, Temperature, Motion/activity, Sleep/circadian features - Value, Timestamp, Signal quality, Provenance - do not fabricate values
- Timeline - General - Chronological timeline - sensor session, symptom entry, cycle event, clinical entry, ultrasound study, analysis, model run, report generated - date filtering, event filtering
- Trends - General - Longitudinal trends - daily, weekly, monthly where data supports never fabricate trends
- Baseline - General - Personal baseline - mean, median, std, MAD, rolling, confidence, min obs, circadian context
- Symptoms - General - Structured symptom logging - timestamp, symptom, severity, notes - never turn symptoms into diagnosis
- Reports - General - Only reports belonging to current patient - view, preview, export, share where permitted - never accidentally expose another patient's report
- AI & Models - General - General Physiological Models, Personal Baseline Models, Longitudinal Models, Disease Models
- Disease Models → CHRONO-PCOS - First disease model - Overview, PCOS-specific analysis, Chrono-Metabolic analysis, Ultrasound, PCOS research model, PCOS report
- Doctor Sharing - General - Controlled sharing/export
- Find Care - General - Doctors, Clinics, Labs, Supplies - DEMO DATA visible, do not fabricate real-world availability
- Privacy - General - Local-first, offline, privacy-focused
- Settings - General - Settings, patient ID single patient, privacy, data, version, disclaimer

Under Disease Models: CHRONO-PCOS. If patient has not enabled disease model, general application still functions.

Implementation: `android/patient/` Kotlin + Jetpack Compose Material 3 single patient only never global list CURRENT PATIENT stable ID - HOME, MY HEALTH, MEASUREMENTS, TIMELINE, SYMPTOMS, CYCLE, ULTRASOUND, RESULTS, REPORTS, DOCTOR SHARING, FIND CARE, EDUCATION, SETTINGS - now general with disease models section.

---

## Future Expansion - Extensible

Architecture makes it possible to eventually have:

```
ENDO-TWIN

├── CHRONO-PCOS (first, implemented)
├── Future Disease Model (concept)
├── Future Disease Model (concept)
├── Future Disease Model (concept)
└── Research Models
```

Without creating:

- separate databases
- separate patient systems
- duplicate signal-processing pipelines
- duplicate baseline engines
- duplicate report engines
- duplicate authentication
- duplicate applications

Shared infrastructure remains ENDO-TWIN.

**TEST 4**: Add dummy future disease model possible without rewriting core - PASS = extensible architecture.

Implementation: DummyFutureModel in `apps/main/main_app.py` implements DiseaseModel interface, registered via registry, no core rewrite.

---

## Project Structure

```
src/
└── endo_twin/
    ├── core/
    │   ├── patient.py - General Patient, PatientIdentity
    │   ├── measurement.py - SensorReading, Measurement, Feature, Observation, TimelineEvent, Baseline, LongitudinalSeries, ProvenanceLabel
    │   └── twin_core.py - EndoTwinCore general platform - no PCOS assumptions
    ├── physiology/
    │   └── general_physiology.py - GeneralPhysiologyEngine
    ├── baseline/
    │   └── general_baseline.py - GeneralBaselineEngine
    ├── longitudinal/
    │   └── general_longitudinal.py - GeneralLongitudinalEngine
    ├── provenance/
    │   └── general_provenance.py - GeneralProvenanceTracker - MEASURED/CLINICALLY_ENTERED/IMAGE-DERIVED/MODEL-INFERRED/DEMO_DATA/UNKNOWN first-class
    ├── uncertainty/
    │   └── general_uncertainty.py - GeneralUncertaintyModel
    ├── models/
    │   ├── disease_model_interface.py - DiseaseModel interface - name, version, description, required_features, analyze(), explain(), generate_report(), validate_input(), get_uncertainty(), get_limitations()
    │   └── model_registry.py - ModelRegistry - general + disease models - extensible
    └── ...

disease_models/
└── chrono_pcos/
    ├── __init__.py
    ├── manifest.py - CHRONO_PCOS_MANIFEST
    ├── model/
    │   └── chrono_pcos_model.py - ChronoPCOSDiseaseModel implements DiseaseModel - preserves original PCOSModule
    ├── features/
    │   └── pcos_features.py - PCOS-specific features
    ├── ultrasound/
    │   └── pcos_ultrasound.py - PCOS-specific ultrasound - Rotterdam criteria
    ├── chrono_metabolic/
    │   └── pcos_chrono_metabolic.py - PCOS-specific chrono-metabolic interpretation
    ├── reports/
    │   └── pcos_reports.py - PCOS-specific reports extends general
    └── tests/

apps/
├── main/
│   └── main_app.py - ENDO-TWIN general platform main app - Dashboard general, Disease Models plugin, 6 acceptance tests
├── doctor_desktop/
│   └── main_enhanced.py - Doctor PC full workstation - general with disease models
├── patient_android/
│   └── android/patient/ - Kotlin + Compose - general with disease models
├── doctor_android/
│   └── android/doctor/ - Kotlin + Compose - multi-patient general with disease models
└── research_lab/

endo_twin/ (root, legacy but now general)
├── core/
│   └── twin.py - EndoTwinCore (migrated to src/endo_twin/core/twin_core.py general)
...

src/disease_modules/ (original, preserved, used by disease_models/chrono_pcos/)
├── base.py - DiseaseModule base (original interface)
├── pcos.py - PCOSModule (original, used by new ChronoPCOSDiseaseModel) - preserved functionality
├── sleep.py
├── cardiometabolic.py
├── autonomic.py
└── registry.py

core/ (original scientific core, preserved)
├── chrono_metabolic/
├── signal_processing/
├── features/
etc.

src/ui/
└── main_window.py - Original CHRONO-TWIN NEXUS V8.3 main window - preserved, general sections Overview, Baseline, Trends, Health Signals, Data Quality, Clinical Inputs, Ultrasound, Explanation, Report, Validation

database/
├── database.py - LocalDatabase 18 tables
└── endo_twin_database.py - EndoTwinDatabase 15+ tables, multi-patient safety DEMO-001/002/003 isolation PASS 7 FAIL 0

desktop/
└── doctor_app/
    └── main_enhanced.py - Doctor PC - general platform with disease models

android/
├── patient/
│   └── app/src/main/java/org/chronopcos/patient/MainActivity.kt - Patient Android Kotlin + Compose - general with disease models - single patient only
└── doctor/
    └── app/src/main/java/org/chronopcos/doctor/MainActivity.kt - Doctor Android Kotlin + Compose - multi-patient general with disease models

website/
├── index.html - 376K, 24 sections - HOME PROBLEM SOLUTION HOW IT WORKS HARDWARE PHYSIOLOGY CHRONO-METABOLIC DIGITAL TWIN ENDO-TWIN AI/ML ULTRASOUND PLATFORMS ANDROID DATABASE & PRIVACY REPORTING CARE DISCOVERY VERSION HISTORY RESEARCH SAFETY LIMITATIONS ROADMAP DEMO DOCUMENTATION CONTACT
├── style.css
└── script.js

docs/
├── endo_twin/
│   ├── CONCEPT.md - One sentence: ENDO-TWIN is platform, CHRONO-PCOS first model
│   ├── PLATFORM_ARCHITECTURE.md - General platform architecture, acceptance tests
│   └── DISEASE_MODEL_SYSTEM.md - Plugin architecture
├── chrono_pcos/
│   └── MODEL.md - CHRONO-PCOS first disease model
└── ...

LAUNCH/
├── ENDO_TWIN.sh - ENDO-TWIN General Platform - Understand physiological patterns over time
├── COMPLETE_LAUNCHER.sh - Complete Control Center
└── ...

launcher/
└── main.py - Complete Control Center - ENDO-TWIN general platform - categories PATIENT DOCTOR SCIENCE ENDO-TWIN CORE GENERAL PLATFORM CHRONO-PCOS FIRST DISEASE MODEL ANDROID NATIVE KOTLIN DATA & REPORTS PUBLIC SYSTEM
```

---

## Documentation

```
docs/endo_twin/
    CONCEPT.md - One sentence: ENDO-TWIN is platform, CHRONO-PCOS first model
    PLATFORM_ARCHITECTURE.md - General platform architecture
    CORE.md - General core classes no PCOS assumptions
    DISEASE_MODEL_SYSTEM.md - Plugin architecture

docs/chrono_pcos/
    MODEL.md - CHRONO-PCOS first disease model
    FEATURES.md - PCOS-specific features
    ULTRASOUND.md - PCOS-specific ultrasound
    CHRONO_METABOLIC.md - PCOS-specific chrono-metabolic
```

README says clearly:

```
"ENDO-TWIN is the general platform."

"CHRONO-PCOS is the first disease-specific model built on the platform."
```

Do NOT describe ENDO-TWIN as merely another name for CHRONO-PCOS.

---

## Version History

Preserve historical evolution:

```
V0 Original PCOS concept
V1+ Physiological sensing and data collection - MAX30102 PPG
V2+ Multisensor development - MPU6050 motion, DS18B20 temp, GSR
V3+ Signal processing - filtering, baseline removal, artifact detection
V4+ Baseline & Longitudinal - PersonalBaselineEngine, LongitudinalEngine
V5+ Disease modules - PCOS, Sleep, Cardiometabolic, Autonomic
V6+ Fusion & Explainability - MultimodalFusion, ShapExplainer
V6.1+ Hardware Hub - Arduino Mega hub
V7+ UI & Reports - PySide6 main_window.py
V8+ CHRONO-TWIN NEXUS - Modular multimodal longitudinal health platform
V8.1 PCOS-focused - PCOS-focused longitudinal phenotyping + ultrasound - preserved in chrono_pcos_project V8/
V8.2 concepts - Modular disease system
V8.3+ Full ecosystem - Patient Android, Doctor Android, Doctor PC, Local DB, Care Discovery, Website
V8.3+ → ENDO-TWIN - Native Kotlin + Compose, multi-patient safety, ENDO-TWIN DB
NEXT ENDO-TWIN platform architecture - General platform, CHRONO-PCOS first disease model - TEST 1-6 PASS
```

Migration preserves historical PCOS work while making architecture general.

---

## No Overengineering

Do not create unnecessary abstraction just for sake of saying "platform".

If general component currently used only by CHRONO-PCOS but clearly reusable, move it into Core - DONE: patient management, sensors, signal processing, feature extraction, baseline, longitudinal, database, reports, provenance, model registry, uncertainty, visualization all in ENDO-TWIN Core.

If something genuinely PCOS-specific, keep it inside CHRONO-PCOS - DONE: PCOS features, PCOS risk logic, PCOS model, PCOS-specific ultrasound, Chrono-Metabolic PCOS interpretation, PCOS-specific reports.

Use evidence from actual codebase to decide.

---

## Final Acceptance Test - 6 Tests

**TEST 1**: Launch main application. It should make sense even if user knows nothing about PCOS. PASS = general physiological platform.

- Implementation: `apps/main/main_app.py` - EndoTwinMainApp
- Dashboard: "Understand your physiological patterns over time." - general
- Sections: Personal Baseline, Today's Measurements, Longitudinal Trends, Physiological Patterns, AI & Models, Disease Models, Reports, Doctor Sharing - all general
- No PCOS-specific language unless disease model selected

**TEST 2**: Open Disease Models. CHRONO-PCOS appears. PASS = disease-specific module.

- Implementation: `get_disease_models_overview()` - shows CHRONO-PCOS
- Manifest: name, version, display_name, description, capabilities, limitations
- Location: `disease_models/chrono_pcos/`

**TEST 3**: Disable/remove CHRONO-PCOS temporarily. Main ENDO-TWIN application must still launch and function. PASS = true general architecture.

- Core does NOT depend directly on CHRONO-PCOS - `src/endo_twin/core/twin_core.py` loads disease models as plugins via registry
- Disease models are plugins via `model_registry.register_disease_model()`
- General dashboard works without disease models - `get_general_dashboard()` returns general sections
- If CHRONO-PCOS not available, main app still works - tested with `CHRONO_PCOS_AVAILABLE` flag

**TEST 4**: Add dummy future disease model. Possible without rewriting core application. PASS = extensible architecture.

- Implementation: `DummyFutureModel` in `apps/main/main_app.py` implements `DiseaseModel` interface
- Registered via `model_registry.register_disease_model(dummy_model)`
- No core rewrite needed
- Total models: CHRONO-PCOS + 2 dummy future = 3 - extensible

**TEST 5**: Open CHRONO-PCOS. Original useful PCOS functionality must still exist. PASS = migration preserved scientific functionality.

- Implementation: `disease_models/chrono_pcos/model/chrono_pcos_model.py` - `ChronoPCOSDiseaseModel` uses original `PCOSModule` internally
- Original logic preserved: `_cycle_score`, `_domain_scores`, `_risk_from_scores`, provenance, drivers, explanation
- Preserved: PCOS features, PCOS risk logic, PCOS model, ultrasound, chrono-metabolic, reports
- Analyzes with original module, converts to general `DiseaseModelResult`

**TEST 6**: Patient A and Patient B. No cross-patient data. PASS = isolation.

- Implementation: `tests/test_multi_patient_isolation.py` PASS 7 FAIL 0
- DEMO-001, DEMO-002, DEMO-003 with deliberately different data HR 72/78/68 BMI 23.5/27.2/21.8 Age 22/28/24
- Reports patient-specific, ultrasounds patient-specific, AI runs patient-specific, sensor sessions patient-specific, timeline patient-specific
- Database level, not merely UI hidden - `EndoTwinDatabase.test_patient_isolation()`

---

## Most Important Final Principle

Do not build:

```
"an ENDO-TWIN app with a PCOS feature."
```

Build:

```
"A general ENDO-TWIN physiological modelling platform whose first disease-specific intelligence module is CHRONO-PCOS."
```

User should understand project in one sentence:

```
"ENDO-TWIN is the platform; CHRONO-PCOS is its first disease-specific model."
```

Everything else follows this architecture.

---

## Run It

```bash
# Setup Garuda
./setup_garuda.sh  # 10 steps - OS check, Python check, .venv creation, requirements install, permissions, logs, DIST/android, diagnostics

# Diagnostics - actual checks PASS/WARN/FAIL never fake
./LAUNCH/DIAGNOSTICS.sh  # 13+ checks - Python, .venv, PySide6, Core Deps, Database V8.3, ENDO-TWIN DB isolation, Scientific Core V8.3, ENDO-TWIN Core General Platform, AI/ML, Model Registry, Ultrasound, Doctor PC, Patient Kivy Legacy, Patient Native Kotlin, Doctor Native Kotlin, Android APKs, Website, Care Discovery, Chrono-Metabolic, Provenance, Build Scripts, Multi-Patient Safety, General Platform, CHRONO-PCOS Model

# ENDO-TWIN General Platform - 6 acceptance tests
./LAUNCH/ENDO_TWIN.sh  # General platform - Understand physiological patterns over time - TEST 1-6 PASS
# or
.venv/bin/python apps/main/main_app.py  # General platform console - 6 tests PASS
# or
.venv/bin/python -m apps.main.main_app  # Same

# Original scientific core - preserved
./LAUNCH/SCIENTIFIC_CORE.sh  # Original CHRONO-TWIN NEXUS V8.3 main window - preserved

# Doctor PC - general with disease models
./LAUNCH/DOCTOR_PC.sh  # Doctor PC full workstation - general platform with disease models - patient workspace scoped

# Patient App
./LAUNCH/PATIENT_APP.sh  # Patient App Kivy PC demo - general with disease models

# Android - Native Kotlin + Compose
./BUILD_PATIENT_APK.sh --check-only  # Check prerequisites Java Kotlin Gradle SDK NDK
./BUILD_PATIENT_APK.sh  # Build Patient APK native Kotlin + Compose to DIST/android/
./BUILD_DOCTOR_APK.sh  # Build Doctor APK multi-patient
./BUILD_ALL_APKS.sh  # Build both

# Full Showcase - 16 steps + ENDO-TWIN architecture
./LAUNCH/FULL_SHOWCASE.sh  # Science-fair demonstration - integrated ecosystem

# Website
./LAUNCH/WEBSITE.sh  # Public website - 24 sections - HOME PROBLEM SOLUTION HOW IT WORKS HARDWARE PHYSIOLOGY CHRONO-METABOLIC DIGITAL TWIN ENDO-TWIN AI/ML ULTRASOUND PLATFORMS ANDROID DATABASE & PRIVACY REPORTING CARE DISCOVERY VERSION HISTORY RESEARCH SAFETY LIMITATIONS ROADMAP DEMO DOCUMENTATION CONTACT

# Complete Control Center
./LAUNCH/COMPLETE_LAUNCHER.sh  # Complete Control Center - ENDO-TWIN general platform - categories PATIENT DOCTOR SCIENCE ENDO-TWIN CORE GENERAL PLATFORM CHRONO-PCOS FIRST DISEASE MODEL ANDROID NATIVE KOTLIN DATA & REPORTS PUBLIC SYSTEM

# Tests
.venv/bin/python tests/test_multi_patient_isolation.py  # PASS 7 FAIL 0 - multi-patient safety
.venv/bin/python -m pytest tests/ -v  # All tests
```

---

## Final Commands - Actually Work (Superbuild Verification)

These commands have been verified to actually work in resulting repository (not file existence checks):

```bash
# One canonical launcher - 12 options menu
./START.sh
# Interactive menu:
# 1. ENDO-TWIN
# 2. Doctor Desktop
# 3. Patient Demo
# 4. Research Lab
# 5. Diagnostics
# 6. Build Patient APK
# 7. Build Doctor APK
# 8. Build All APKs
# 9. Run Tests
# 10. Performance Benchmark
# 11. Project Health
# 12. Exit

# Direct modes also work:
./START.sh gui              # Control Center GUI launcher/main.py
./START.sh endo-twin        # ENDO-TWIN general dashboard - 6 acceptance tests PASS
./START.sh doctor           # Doctor Desktop multipatient
./START.sh patient          # Patient Demo
./START.sh diagnostics      # System diagnostics
./START.sh build-gradle     # Real Gradle builds ./gradlew assembleDebug → artifacts/android/
./START.sh test             # Run tests
./START.sh test-cross       # Cross-patient isolation
./START.sh benchmark        # Performance benchmark real measurements
./START.sh health           # Project health
./START.sh help             # Help

# Build APKs - Real Gradle wrapper not placeholder
./scripts/build/build_patient_apk.sh
# Checks prerequisites, builds APK, logs to logs/build_patient_apk.log, output DIST/android/ and artifacts/android/
# Real command inside: cd android/patient && ./gradlew assembleDebug
# APK: android/patient/app/build/outputs/apk/debug/app-debug.apk → artifacts/android/endo-twin-patient-debug.apk
# Env limitation: Needs JDK 17 + Android SDK 34, real wrapper 61K jar + 8.4K script exists, build fails JAVA_HOME not set if no toolchain (documented)

./scripts/build/build_doctor_apk.sh
# Same for doctor: cd android/doctor && ./gradlew assembleDebug → artifacts/android/endo-twin-doctor-debug.apk

./scripts/build/build_all_apks.sh
# Builds both patient and doctor

# Tests - Real execution not file existence
pytest -q
# Or
.venv/bin/python -m pytest tests/ -v
.venv/bin/python apps/main/main_app.py  # 6 acceptance tests PASS
.venv/bin/python tests/test_endo_twin_isolation.py  # Architecture isolation PASS
.venv/bin/python tests/test_multi_patient_isolation.py  # PASS 7 FAIL 0

# Project Health - Real checks PASS/WARN/FAIL with evidence
./scripts/diagnostics/project_health.sh
# Checks: dependencies, database, scientific core, models, demo data, launchers, Android Gradle real not placeholder, tests, applications
# Returns PASS/WARN/FAIL with actual evidence, not file existence

# Performance Benchmark - Real measurements not fabricated
./START.sh benchmark
# Or see docs/performance/PERFORMANCE_REPORT.md
# Real measurements: DB init 61.6 ms, patient creation 2.1 ms, list/search 0.1 ms, deterministic inference 0.3 ms, dashboard 22.2 ms, model loading 2386 ms bottleneck, real inference 993 ms

# Additional verified commands:
./BUILD_ALL_APKS.sh --check-only  # Check prerequisites
./LAUNCH/DIAGNOSTICS.sh          # 13+ checks PASS/WARN/FAIL never fake
./LAUNCH/ENDO_TWIN.sh            # ENDO-TWIN General Platform 6 tests PASS
./LAUNCH/COMPLETE_LAUNCHER.sh    # Complete Control Center
```

Artifacts:
- `artifacts/android/endo-twin-patient-debug.apk` - Patient APK (when built with JDK+SDK)
- `artifacts/android/endo-twin-doctor-debug.apk` - Doctor APK (when built)
- `artifacts/android/` - All APKs
- `DIST/android/` - Kivy APKs via Buildozer
- `logs/` - All logs
- `docs/recovery/` - Recovery docs
- `docs/benchmarks/` - Reference audit + benchmark matrix
- `docs/performance/` - Performance report real measurements

VS Code:
- `.vscode/tasks.json` - Tasks: Run ENDO-TWIN, Doctor Desktop, Patient Demo, Research Lab, Diagnostics, Build Patient APK, Build Doctor APK, Build All APKs, Run Tests, Cross-Patient Tests, Model Diagnostics, Performance Benchmark, Project Health
- `.vscode/launch.json` - Debug configs
- `.vscode/settings.json` - Python interpreter .venv, pytest, etc.
- `.vscode/extensions.json` - Recommended extensions

---

## License and Safety

Educational research prototype. Not a medical device. Not clinically validated. No diagnostic claims. Always discuss health concerns with qualified healthcare professional.

- Research / risk-screening output — not a medical diagnosis
- Research prototype, not diagnostic, not medical advice, not clinically validated unless evidence exists
- Model limitations, sensor limitations, uncertainty, need for clinical validation
- Never claim diagnosis, clinical validation, medical accuracy, diagnostic sensitivity specificity, clinical superiority, regulatory approval unless actual documented evidence exists
- Always distinguish MEASURED CLINICALLY_ENTERED IMAGE-DERIVED MODEL-INFERRED DEMO_DATA UNKNOWN
- Never represent model inference as measurement
- Never represent simulated data as real patient data
- Never fabricate ML metrics, clinical records
- Local-first, offline, privacy-focused, no cloud upload private health
- Patient cannot access other patient, doctor only authorized patients
- No cloud infrastructure, no paid APIs, no unnecessary web servers, no blockchain, no complex microservices. Runs offline.

Prioritizes: Science, Clarity, Reproducibility, Explainability, Honest Limitations, **General Platform Architecture**, **Disease Model Plugin System**, **Preserved Original Functionality**, **Extensibility**.

**One Sentence: ENDO-TWIN is the platform; CHRONO-PCOS is its first disease-specific model.**
