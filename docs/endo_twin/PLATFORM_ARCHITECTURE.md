# ENDO-TWIN Platform Architecture - General Platform

## Overview

```
                ENDO-TWIN (General Platform)
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
  DATA LAYER     TWIN ENGINE      AI/ML LAYER
        |              |              |
        +--------------+--------------+
                       |
              DISEASE-SPECIFIC MODELS (Plugin)
                       |
                  CHRONO-PCOS (First Model)
                  Future Model A (Concept)
                  Future Model B (Concept)
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
   PATIENT        DOCTOR         RESEARCH
   PLATFORM       PLATFORM       PLATFORM
```

## General Platform Sections

Main application is general, disease-agnostic:

### Dashboard - General Physiological Overview

```
--------------------------------
ENDO-TWIN
Personal Physiological Overview
--------------------------------
Tagline: Understand your physiological patterns over time.

Personal Baseline [ View ]
- What is normal for YOU first
- mean, median, std, MAD, rolling, confidence, circadian context

Today's Measurements [ View ]
- HR, HRV, activity, temperature, GSR
- MEASURED with quality, source, timestamp

Longitudinal Trends [ View ]
- Personal baseline → time series → change → persistence → recovery → context
- Daily, weekly, monthly

Physiological Patterns [ View ]
- Circadian, autonomic, metabolic, activity, temperature
- Multisystem interaction, chrono-metabolic fingerprinting

AI & Models [ View ]
- General Physiological Models
- Personal Baseline Models
- Longitudinal Models
- Disease Models

Disease Models [ View ]
- CHRONO-PCOS (first, implemented)
- Future models (concept, extensible)

Reports [ View ]
- Professional reports with provenance, uncertainty, limitations

Doctor Sharing [ View ]
- Controlled sharing, deliberate not automatic

--------------------------------
```

If CHRONO-PCOS enabled:

```
Disease Models
→ CHRONO-PCOS
→ Open Analysis - PCOS-specific analysis, chrono-metabolic, ultrasound, report

But main dashboard itself remains general.
```

## Core Classes - No PCOS Assumptions

ENDO-TWIN Core provides reusable infrastructure:

- **Patient**: General patient, stable IDs, enabled_disease_models list, extensions dict
- **Observation**: General clinical observation
- **Measurement**: General measurement - type, value, unit, quality, provenance, source
- **SensorReading**: Raw sensor reading - sensor_type, values, quality
- **Signal**: General signal
- **Feature**: General feature - name, value, category (established_measurement, derived_feature, experimental_research, ml_prediction, clinical_interpretation)
- **Baseline**: General personal baseline - mean, median, std, confidence, min_observations
- **TimelineEvent**: General timeline event - event_type, title, description, timestamp
- **LongitudinalSeries**: General longitudinal series - data_points, trend, persistence, change_detected
- **Model**: General model
- **Prediction**: General prediction
- **Explanation**: General explanation
- **Uncertainty**: General uncertainty - data quality, model confidence, limitations
- **Provenance**: General provenance - MEASURED, CLINICALLY_ENTERED, IMAGE-DERIVED, MODEL-INFERRED, DEMO_DATA, UNKNOWN
- **Report**: General report

No PCOS-specific assumptions in these classes.

## Data Model - General

Database supports general physiological data:

```
patients - general patient data, stable IDs, enabled_disease_models
measurements - general measurements, patient_id, type, value, quality, provenance
signals - general signals
features - general features, category
baselines - general baselines, patient_id, feature_name, mean, median, std, confidence
timeline_events - general timeline, patient_id, event_type, title, description
symptoms - general symptoms, patient_id, type, severity
clinical_observations - general clinical, patient_id, type, data
imaging - general imaging, patient_id, image_path, quality, provenance
model_runs - general model runs, patient_id, model_name, version, input, output, confidence
predictions - general predictions
reports - general reports, patient_id, type, content
audit_events - general audit, patient_id, user_id, action
provenance - general provenance tracking
```

Disease-specific data references:

```
disease_model_id
patient_id
```

Example:

```
disease_models/chrono_pcos/
  - references patient_id and disease_model_id = chrono_pcos
  - pcos-specific features stored with disease_model_id
  - pcos reports reference disease_model_id
```

## Disease Model Interface

Common interface:

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

## AI & Models - General

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
│   └── 6 scenarios
│
├── Longitudinal Models
│   ├── Rolling windows
│   ├── Persistence
│   └── Trend, change-point, recovery
│
└── Disease Models (Plugin)
      ├── CHRONO-PCOS (first, implemented)
      │   ├── Overview
      │   ├── PCOS-specific analysis
      │   ├── Chrono-Metabolic PCOS interpretation
      │   ├── Ultrasound PCOS analysis
      │   ├── PCOS research model
      │   └── PCOS report
      ├── Future Model A (concept, dummy for extensibility test)
      └── Future Model B (concept)
```

This allows future models to be added without rewriting application.

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

## Doctor Application - General

Doctor Desktop and Doctor Android should also be general.

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

## Patient Application - General

Patient Android primarily general:

- Home - General
- Measurements - General
- Timeline - General
- Trends - General
- Baseline - General
- Symptoms - General
- Reports - General
- AI & Models - General
- Disease Models → CHRONO-PCOS
- Doctor Sharing - General
- Find Care - General
- Privacy - General
- Settings - General

Under Disease Models:

```
CHRONO-PCOS
```

If patient has not enabled disease model, general application still functions.

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

## Implementation

### Current Structure (After Migration)

```
src/
└── endo_twin/
    ├── core/
    │   ├── patient.py - General Patient, PatientIdentity
    │   ├── measurement.py - SensorReading, Measurement, Feature, Observation, TimelineEvent, Baseline, LongitudinalSeries, ProvenanceLabel
    │   └── twin_core.py - EndoTwinCore general platform
    ├── physiology/
    │   └── general_physiology.py - GeneralPhysiologyEngine
    ├── baseline/
    │   └── general_baseline.py - GeneralBaselineEngine
    ├── longitudinal/
    │   └── general_longitudinal.py - GeneralLongitudinalEngine
    ├── provenance/
    │   └── general_provenance.py - GeneralProvenanceTracker
    ├── uncertainty/
    │   └── general_uncertainty.py - GeneralUncertaintyModel
    ├── models/
    │   ├── disease_model_interface.py - DiseaseModel interface
    │   └── model_registry.py - ModelRegistry general + disease
    └── ...

disease_models/
└── chrono_pcos/
    ├── __init__.py
    ├── manifest.py - CHRONO_PCOS_MANIFEST
    ├── model/
    │   └── chrono_pcos_model.py - ChronoPCOSDiseaseModel implements DiseaseModel
    ├── features/
    │   └── pcos_features.py - PCOS-specific features
    ├── ultrasound/
    │   └── pcos_ultrasound.py - PCOS-specific ultrasound
    ├── chrono_metabolic/
    │   └── pcos_chrono_metabolic.py - PCOS-specific chrono-metabolic interpretation
    ├── reports/
    │   └── pcos_reports.py - PCOS-specific reports
    └── tests/

apps/
├── main/
│   └── main_app.py - ENDO-TWIN general platform main app
├── doctor_desktop/
├── patient_android/
├── doctor_android/
└── research_lab/

endo_twin/ (root, legacy but now general)
├── core/
│   └── twin.py - EndoTwinCore (to be migrated to src/endo_twin/core/twin_core.py)
...

src/disease_modules/ (original, preserved, used by disease_models/chrono_pcos/)
├── base.py - DiseaseModule base (original interface)
├── pcos.py - PCOSModule (original, used by new ChronoPCOSDiseaseModel)
├── sleep.py
├── cardiometabolic.py
├── autonomic.py
└── registry.py

core/ (original scientific core, preserved)
├── chrono_metabolic/
├── signal_processing/
├── features/
etc.

database/
├── database.py - LocalDatabase 18 tables
└── endo_twin_database.py - EndoTwinDatabase 15+ tables, multi-patient safety
```

### Migration Strategy

1. **Audit original PCOS app**: Identify screens, workflows, scientific modules, sensors, signal processing, AI/ML, ultrasound, reports, database, patient management, doctor workflow, demos - DONE, preserved in src/, core/, endo_twin/, database/, etc.

2. **Separate GENERAL from PCOS-SPECIFIC**:
   - GENERAL → ENDO-TWIN Core: patient management, sensors, signal acquisition, signal processing, feature extraction, baseline, longitudinal analysis, database, reports, provenance, model registry, uncertainty, visualization
   - PCOS-SPECIFIC → CHRONO-PCOS: PCOS features, PCOS risk logic, PCOS model, PCOS-specific ultrasound analysis, Chrono-Metabolic PCOS interpretation, PCOS-specific reports - DONE, created disease_models/chrono_pcos/ with model, features, ultrasound, chrono_metabolic, reports

3. **Create general platform**: apps/main/main_app.py - ENDO-TWIN general platform, dashboard general, disease models plugin - DONE

4. **Preserve original functionality**: Original PCOS functionality still exists in src/disease_modules/pcos.py and is used by new disease_models/chrono_pcos/model/chrono_pcos_model.py - TEST 5 PASS

5. **Test extensibility**: Dummy future models registered in apps/main/main_app.py - TEST 4 PASS

6. **Test general app without PCOS**: Main app works even when no disease model selected - TEST 3 PASS

## Acceptance Tests

**TEST 1**: Launch main application. It should make sense even if user knows nothing about PCOS. PASS = general physiological platform.

- Dashboard: "Understand your physiological patterns over time." - general, not PCOS-specific
- Sections: Personal Baseline, Today's Measurements, Longitudinal Trends, Physiological Patterns, AI & Models, Disease Models, Reports, Doctor Sharing - all general

**TEST 2**: Open Disease Models. CHRONO-PCOS appears. PASS = disease-specific module.

- Disease Models overview shows CHRONO-PCOS as first model, plus dummy future models
- CHRONO-PCOS manifest: name, version, display_name, description, capabilities, limitations

**TEST 3**: Disable/remove CHRONO-PCOS temporarily. Main ENDO-TWIN application must still launch and function. PASS = true general architecture.

- Core does NOT depend directly on CHRONO-PCOS
- Disease models are plugins via registry
- General dashboard works without disease models
- General sections: baseline, measurements, timeline, trends, patterns, etc. all work without PCOS

**TEST 4**: Add dummy future disease model. Possible without rewriting core application. PASS = extensible architecture.

- DummyFutureModel class implements DiseaseModel interface
- Registered via model_registry.register_disease_model()
- No core rewrite needed
- Total models: CHRONO-PCOS + 2 dummy future = 3

**TEST 5**: Open CHRONO-PCOS. Original useful PCOS functionality must still exist. PASS = migration preserved scientific functionality.

- ChronoPCOSDiseaseModel uses original PCOSModule internally
- Original logic: cycle score, domain scores, risk from scores, provenance, drivers, explanation
- Preserved: PCOS features, PCOS risk logic, PCOS model, ultrasound, chrono-metabolic, reports
- Analyzes with original module, converts to general DiseaseModelResult

**TEST 6**: Patient A and Patient B. No cross-patient data. PASS = isolation.

- tests/test_multi_patient_isolation.py PASS 7 FAIL 0
- DEMO-001, DEMO-002, DEMO-003 with deliberately different data HR 72/78/68
- Reports patient-specific, ultrasounds patient-specific, AI runs patient-specific, etc.
- Database level, not merely UI hidden

## One Sentence

**ENDO-TWIN is the platform; CHRONO-PCOS is its first disease-specific model.**

Everything else follows this architecture.
