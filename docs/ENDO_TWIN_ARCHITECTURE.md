# ENDO-TWIN Architecture - CHRONO-PCOS V8.3+ → ENDO-TWIN

## Overview

ENDO-TWIN is a research framework / prototype for personalized physiological modelling.

CHRONO-PCOS should become the first major disease-specific implementation running on an ENDO-TWIN-ready architecture.

DO NOT claim ENDO-TWIN is already a clinically validated universal human digital twin.

It is a research framework / prototype.

```
                 ENDO-TWIN CORE
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
  DATA LAYER     TWIN ENGINE      AI/ML LAYER
        |              |              |
        +--------------+--------------+
                       |
              DISEASE-SPECIFIC MODELS
                       |
                  CHRONO-PCOS
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
   PATIENT        DOCTOR         RESEARCH
   PLATFORM       PLATFORM       PLATFORM
```

## Core Concept

What a digital twin is: computational representation of physiological state.

What ENDO-TWIN means in this project: research framework for personalized physiological modelling, NOT perfect simulation of human.

Flow: data → features → baseline → longitudinal state → multimodal model → inference → uncertainty

Clearly state: It is computational representation, NOT perfect simulation of human.

## Architecture Layers

### DATA LAYER

Core entities:

- patients - stable IDs like CP-0001, DEMO-001, anonymous_id PXXXXX, display_name, age, BMI, created_at, updated_at, is_archived, foreign key user_id
- sensor_sessions - session_id, patient_id, source, start_at, end_at, sample_count, data_quality, notes, label REAL/SIMULATED/DEMO/DEMO_DATA, created_at, foreign key patient_id
- measurements - measurement_id, patient_id, session_id, measurement_type hr/hrv/ppg/temperature/motion/sleep/activity/circadian/autonomic/metabolic, value, value_json, unit, timestamp, quality 0-1, provenance MEASURED/CLINICALLY_ENTERED/IMAGE_DERIVED/MODEL_INFERRED/DEMO_DATA/UNKNOWN, source MAX30102/DS18B20/MPU6050/USER-ENTERED, confidence None unless computed, limitations, is_demo, created_at, foreign keys patient_id, session_id
- features - feature_id, patient_id, session_id, measurement_id, feature_name, feature_value, feature_json, category established_measurement/derived_feature/experimental_research/ml_prediction/clinical_interpretation, quality, provenance, source, confidence, limitations, explainability, is_demo, created_at, foreign keys
- clinical_records - record_id, patient_id, record_type, data_json, provenance CLINICALLY_ENTERED, source USER-ENTERED, label USER-ENTERED, is_demo, created_at, updated_at, foreign key patient_id
- symptoms - symptom_id, patient_id, symptom_type, severity, notes, logged_at, label USER-ENTERED, foreign key patient_id
- cycle_events - event_id, patient_id, event_type cycle_start/cycle_end/ovulation/symptom/note, event_date, cycle_length_days, irregularity, symptoms_json, notes, provenance CLINICALLY_ENTERED, is_demo, created_at, foreign key patient_id
- ultrasound_studies - study_id, patient_id, study_date, image_path, image_metadata_json, quality, quality_details_json, provenance IMAGE_DERIVED, source, confidence None unless computed, is_demo, label REAL/SYNTHETIC/DEMO, created_at, foreign key patient_id
- ultrasound_features - feature_id, patient_id, study_id, feature_name, feature_value, feature_json, unit, quality, provenance IMAGE_DERIVED, source, confidence, limitations, is_demo, created_at, foreign keys patient_id, study_id
- model_runs - run_id, patient_id, session_id, model_name PCOSModule v8.3.0, model_version, input_features_json, output_json pcos_associated_risk low/moderate/high NOT diagnosis, confidence None unless computed, data_quality, clinical_validation NOT ESTABLISHED, provenance MODEL_INFERRED, explainability_json, limitations, is_demo, created_at, foreign keys
- model_versions - version_id, model_name, model_version, model_type disease_specific/general/experimental, description, capabilities_json, limitations, dataset_version, training_date, features_json, target, metrics_json, validation_strategy, provenance MODEL_INFERRED, is_approved, created_at, UNIQUE(model_name, model_version)
- reports - report_id, patient_id, session_id, report_type, content_text, file_path, created_at, created_by, label REAL/DEMO_DATA, foreign key patient_id
- notes - doctor_notes - note_id, patient_id, doctor_id, note_text, created_at, updated_at, is_private, foreign keys patient_id, doctor_id
- providers - care discovery separate from private health data - provider_id, name, type doctor/clinic/lab/supply, specialty, address, latitude, longitude, distance_km, opening_hours, services_json, contact_info, verification_status verified/pending/unverified/demo, is_demo, created_at, updated_at - 4 demo clearly marked demo
- supplies - supply_id, name, category sensor/accessory/monitoring/menstrual/general, description, provider_id, price, availability, image_path, created_at, foreign key provider_id - 5 supplies, no prescription sales
- audit_events - event_id, user_id, patient_id, event_type, action, details_json, timestamp, ip_address, is_demo, foreign keys user_id, patient_id - audit history
- personal_baseline - baseline_id, patient_id, feature_name, baseline_period_start, baseline_period_end, mean_value, median_value, std_value, mad_value, rolling_json, confidence, min_observations, circadian_context_json, provenance, is_demo, created_at, updated_at, foreign key patient_id, UNIQUE(patient_id, feature_name)
- longitudinal_timeline - timeline_id, patient_id, event_type sensor_session/symptom_entry/cycle_event/clinical_entry/ultrasound_study/analysis/model_run/report_generated, event_id, event_date, title, description, provenance, data_json, is_demo, created_at, foreign key patient_id

Relationships:

```
patients
 ↓
sensor_sessions
 ↓
measurements
 ↓
features

patients
 ↓
ultrasound_studies
 ↓
ultrasound_features

patients
 ↓
model_runs

patients
 ↓
reports

patients
 ↓
clinical_records
```

All patient-specific records must contain patient_id.

Do not rely only on UI state for patient separation - implemented at database/repository level.

Use stable IDs like CP-0001, DEMO-001, anonymous_id PXXXXX.

Use foreign keys where appropriate.

### TWIN ENGINE

- identity - PatientIdentity - stable IDs, patient-scoped queries, no cross-patient contamination, DEMO-001 DEMO-002 DEMO-003 with deliberately different data, generate_patient_id prefix CP, get_identity patient_id scoped, create_demo_patients
- physiology - PhysiologicalState - physiological representation, NOT perfect simulation, computational representation data → features → baseline → longitudinal state → multimodal model → inference → uncertainty, measurements HR MEASURED quality 0.91 source MAX30102, HRV DERIVED quality 0.85 limitations PPG less accurate than ECG, temperature MEASURED quality 0.88 source DS18B20 limitations skin not core, motion MEASURED quality 0.8 source MPU6050 limitations wrist not whole-body, skin temperature MEASURED source DS18B20 probe (skin contact) motion
- baseline - PersonalBaselineEngine - personal baseline architecture, shows baseline period, baseline values/features, current period, deviation, trend, signal quality, clearly distinguish population reference, personal baseline, model inference, scenarios stable LOW CHANGE SIGNAL gradual EARLY CHANGE SIGNAL persistent PERSISTENT MULTIMODAL SIGNAL temporary TEMPORARY EVENT sensor failure LOW SENSOR CONFIDENCE recovery RECOVERY TREND, baseline mean median std MAD rolling confidence min_obs circadian_context
- longitudinal - LongitudinalEngine - core scientific story is NOT today's number, it is personal baseline → time series → change → persistence → recovery → context, visualizations daily weekly monthly longitudinal where data supports never fabricate trends, timeline chronological sensor session symptom entry cycle event clinical entry ultrasound study analysis model run report generated, date filtering event filtering session details, analysis baseline_deviation persistence recovery context
- provenance - ProvenanceTracker, ProvenanceLabel - make provenance first-class architecture, every important data object should indicate MEASURED/CLINICALLY_ENTERED/IMAGE-DERIVED/MODEL-INFERRED/DEMO_DATA/UNKNOWN, appears in Doctor PC, Doctor Android, Patient Android where appropriate, Reports, AI/ML, Ultrasound, Database metadata, MEASURED directly measured HR temp motion , CLINICALLY_ENTERED USER-ENTERED age BMI cycle symptoms glucose BP, IMAGE_DERIVED cyst size volume morphology from ultrasound image quality UNKNOWN by design unless computed provenance CLINICALLY-ENTERED vs IMAGE-DERIVED fusion weight 0.20, MODEL_INFERRED sleep regularity circadian disruption HRV derived risk signals, DEMO_DATA demo providers demo patients synthetic clearly labelled, UNKNOWN if cannot reliably extract return UNKNOWN never invent, safety never fabricate measurements diagnoses clinical validation medical certainty clearly distinguish never mix never represent model inference as measurement never represent simulated data as real patient data
- uncertainty - UncertaintyModel - model transparency, confidence, limitations, never hide uncertainty, confidence model output not clinical certainty quality scores 0-1 per channel artifact flags reason codes limitations model transparency, data_quality overall 0.85 per_channel ppg 0.91 motion 0.8 temp 0.88 reason_codes Motion artifact at 12:03 Baseline drift at 12:05 artifact_flags 2, model_confidence pcos_risk 0.75 sleep_disruption 0.68 note model output not clinical certainty, quality_gate UNKNOWN by design unless computed for ultrasound, limitations engineering validation only clinical validation NOT ESTABLISHED PPG-derived HRV less accurate than ECG etc, model_transparency name version dataset version training date features target metrics validation strategy limitations, safety research prototype not replacement

### AI/ML LAYER

- models - ChronoPCOSModel - first disease-specific implementation on ENDO-TWIN architecture, NOT clinically validated universal human digital twin, capabilities pcos_risk_signal NOT diagnosis circadian_analysis autonomic_analysis metabolic_context longitudinal_tracking, safety research prototype not clinically validated not diagnostic requires clinical evaluation engineering validation only never claim diagnosis clinical validation medical accuracy diagnostic sensitivity specificity clinical superiority regulatory approval unless actual documented evidence exists
- registry - ModelRegistry, ModelVersion - model name version dataset version training date features target metrics validation strategy limitations model approval rollback inference uncertainty, register_model name version type disease_specific/general/experimental description capabilities limitations provenance dataset_version features target metrics, get_model name version, list_models, approve_model name version, rollback_model name to_version, get_registry_info, safety never invent metrics if no trained model exists show Model not trained rather than fake accuracy never hide uncertainty manufacture confidence training results

## Common Infrastructure

- patient identity - stable IDs, patient-scoped queries, no cross-patient contamination
- personal baseline - learns what is normal for individual first, baseline period, baseline values/features, current period, deviation, trend, signal quality, clearly distinguish population reference personal baseline model inference
- longitudinal timeline - chronological, daily weekly monthly longitudinal where data supports never fabricate trends, personal baseline → time series → change → persistence → recovery → context
- physiological state - computational representation not perfect simulation, data → features → baseline → longitudinal state → multimodal model → inference → uncertainty
- multimodal data - HR, HRV, PPG, temperature, motion, sleep, activity, circadian, autonomic, metabolic, ultrasound
- provenance - MEASURED CLINICALLY_ENTERED IMAGE-DERIVED MODEL-INFERRED DEMO_DATA UNKNOWN first-class
- uncertainty - confidence model output not clinical certainty, quality scores 0-1, artifact flags, reason codes, limitations, model transparency
- model registry + versioning - model name version dataset version training date features target metrics validation strategy limitations model approval rollback inference uncertainty
- reports - professional, patient/session ID, date/time, measurements, signal quality, longitudinal trends, ultrasound information, model outputs, uncertainty, provenance, limitations, safety disclaimer, separate MEASURED CLINICAL IMAGE-DERIVED MODEL-INFERRED, patient-scoped
- audit history - audit_events patient_id user_id action timestamp patient-scoped audit history
- patient/doctor access - patient_doctor_access access_id patient_id doctor_id granted_at granted_by is_active, check_access patient_id doctor_id, grant_access patient_id doctor_id granted_by, patient cannot access other patient, doctor only authorized patients
- future disease-specific models - CHRONO-PCOS is first, future validated models may eventually exist but do not create fake models

## Disease-Specific Models

CHRONO-PCOS - first major disease-specific implementation running on ENDO-TWIN-ready architecture

```
CHRONO-PCOS
     |
     |
ENDO-TWIN CORE
     |
Disease-specific
    models
     |
CHRONO-PCOS
     |
future validated models
```

Suggested architecture:

```
endo_twin/
    core/
        __init__.py - EndoTwinCore
        twin.py - Central orchestrator
    identity/
        patient_identity.py - PatientIdentity, PatientIdentityRecord
    physiology/
        physiological_state.py - PhysiologicalState, PhysiologicalMeasurement
    baseline/
        personal_baseline.py - PersonalBaselineEngine
    longitudinal/
        longitudinal_engine.py - LongitudinalEngine
    provenance/
        provenance.py - ProvenanceTracker, ProvenanceLabel, ProvenanceRecord
    uncertainty/
        uncertainty.py - UncertaintyModel
    models/
        chrono_pcos.py - ChronoPCOSModel - first disease-specific
    registry/
        model_registry.py - ModelRegistry, ModelVersion
    interfaces/
        patient_interface.py - PatientInterface - single patient only
        doctor_interface.py - DoctorInterface - multi-patient
```

Adapt to existing architecture rather than blindly creating exact structure - we have this structure.

## Patient Platform - Native Kotlin + Jetpack Compose

Patient Android must belong to ONE patient, patient must NEVER see global list of all patients, represents CURRENT PATIENT with stable patient ID.

Structure: HOME, MY HEALTH, MEASUREMENTS, TIMELINE, SYMPTOMS, CYCLE, ULTRASOUND, RESULTS, REPORTS, DOCTOR SHARING, FIND CARE, EDUCATION, SETTINGS

HOME: Today's overview, data collection status, sensor/device status, recent measurements, signal quality, recent activity, personal baseline status, recent longitudinal change, understandable language Data quality Good rather than raw technical diagnostics, do not make unsupported medical claims

MY HEALTH: Personal baseline, longitudinal trends, recent changes, available measurements, data completeness, research-model outputs where appropriate, clearly distinguish model inference from measurements

MEASUREMENTS: Display only measurements actually available, HR, HRV, PPG, Temperature, Motion/activity, Sleep/circadian features, Value, Timestamp, Signal quality, Provenance, do not fabricate values

TIMELINE: Chronological timeline, sensor session, symptom entry, cycle event, clinical entry, ultrasound study, analysis, model run, report generated, date filtering, event filtering, session details

SYMPTOMS: Structured symptom logging, timestamp, symptom, severity if supported, notes, never turn symptoms into diagnosis

CYCLE TRACKING: cycle dates, cycle length, irregularity, symptom association, do not make unsupported medical interpretations

ULTRASOUND: Patient-specific ultrasound section, study list, date, image, metadata, analysis, image-derived features, model results, uncertainty, provenance, each study must belong to exactly one patient

RESULTS: Explain results in understandable language, observed measurements, longitudinal changes, model inference, contributing factors, uncertainty, limitations, clear labels MEASURED IMAGE-DERIVED MODEL-INFERRED UNKNOWN

REPORTS: Only reports belonging to current patient, view, preview, export, share where permitted, never accidentally expose another patient's report

DOCTOR SHARING: Controlled sharing/export, allow patient to select what information is shared where appropriate, sharing state visible, privacy-first

FIND CARE: Doctors, Clinics, Labs, Supplies, if using demonstration providers DEMO DATA must be visible, do not fabricate real-world availability

EDUCATION: What HR means, what HRV means, what physiological monitoring means, what longitudinal analysis means, what AI does, what AI does not do, what ultrasound contributes, why this is not a diagnosis

Implementation: Kotlin + Jetpack Compose + Material 3 + Navigation Compose + ViewModel + Repository pattern + Coroutines + Room/SQLite + DataStore + lifecycle-aware components, clean architecture app/ui/navigation/viewmodel/data/database/repository/model/domain/components, do not create one giant MainActivity

## Doctor Platform - Native Kotlin + Jetpack Compose Multi-Patient

Doctor Android must be proper multi-patient application.

MAIN: Dashboard, Patients, Recent Activity, Pending Review, Reports, Settings

Patient List: Patient ID, Name/alias where appropriate, Age if supported, Last session, Last analysis, Status, Search, Filter, Sort, Open, Archive, Create, Import/export

Patient Profile: Opening patient CP-0001 must switch entire context to CP-0001, Tabs OVERVIEW, TIMELINE, PHYSIOLOGY, SENSORS, ULTRASOUND, AI/MODELS, CLINICAL DATA, REPORTS, NOTES, PROVENANCE, AUDIT, Everything displayed must belong to that patient

Multi-Patient Safety: DEMO-001 DEMO-002 DEMO-003 with deliberately different data, Test DEMO-001 cannot see DEMO-002, DEMO-002 cannot see DEMO-001, Reports patient-specific, Ultrasounds patient-specific, AI results patient-specific, Sensor sessions patient-specific, Timeline patient-specific, implemented at database/repository level not merely hidden in UI

Doctor PC must become primary full research/clinical workstation: Dashboard, Patients, Patient Timeline, Physiology, Sensors, Ultrasound, AI/ML, Clinical Data, Reports, Database, Care Discovery, Diagnostics, Settings, Patient Management real patient list Search Patient ID Name/alias Age Last Session Last Analysis Data Status Open, Support Create Search Filter Sort Open Archive Import Export where appropriate, Patient Workspace when patient CP-0001 selected EVERY SCREEN becomes scoped to CP-0001 Patient overview Personal baseline Recent sessions Longitudinal timeline Physiology Sensors Ultrasound AI Clinical data Reports Notes Provenance Audit

## Android Build System - Native Kotlin

Since Android is now native Kotlin: Create proper Gradle Android projects.

Patient: android/patient/settings.gradle.kts build.gradle.kts app/build.gradle.kts app/src/main/AndroidManifest.xml app/src/main/java/org/chronopcos/patient/MainActivity.kt etc

Doctor: android/doctor/settings.gradle.kts build.gradle.kts app/build.gradle.kts app/src/main/AndroidManifest.xml app/src/main/java/org/chronopcos/doctor/MainActivity.kt etc

Use modern Android tooling compatible with available environment.

Create BUILD_PATIENT_APK.sh BUILD_DOCTOR_APK.sh BUILD_ALL_APKS.sh They must check prerequisites, build, capture logs, report failures, copy APKs to DIST/android/ and dist/android/ For example CHRONO-PCOS-Patient.apk CHRONO-PCOS-Doctor.apk Never fake APK If Android SDK/Gradle cannot be installed in environment explain exactly what missing provide reproducible setup scripts do not claim build success

Current environment: No Android SDK/NDK/Gradle - honest reporting, native Kotlin source preserved, Kivy legacy preserved as fallback, PC demo available, build scripts provide setup instructions, never claim APK exists when not

## Safety

Research prototype, not diagnostic, not medical advice, not clinically validated unless evidence exists, model limitations, sensor limitations, uncertainty, need for clinical validation, never claim diagnosis clinical validation medical accuracy diagnostic sensitivity specificity clinical superiority regulatory approval unless actual documented evidence exists, always distinguish MEASURED CLINICALLY_ENTERED IMAGE-DERIVED MODEL-INFERRED DEMO DATA UNKNOWN, never represent model inference as measurement, never represent simulated data as real patient data, never fabricate ML metrics, never fabricate clinical records

## Testing

Multi-Patient Test Suite: Create DEMO-001 DEMO-002 DEMO-003 with deliberately different data, Test Create Open Edit Switch Analyze Report Ultrasound Timeline Export Then verify No cross-patient contamination This must be automated test wherever possible

Test Complete Launcher opens by double-click, Launcher text never clipped, Desktop launchers work, Patient Desktop works, Doctor PC works, Scientific Core works, AI/ML works or reports unavailable components, Ultrasound works or reports unavailable components, Database works, Reports work, Care Discovery works, Website works, Showcase works, Diagnostics works

ANDROID: Patient Android native Kotlin project exists, Doctor Android native Kotlin project exists, Jetpack Compose UI works, Patient app only sees its own patient data, Doctor app supports multiple patients, Patient switching works, Patient timelines work, Reports patient-specific, Ultrasounds patient-specific, AI runs patient-specific, Provenance visible, Offline mode works where supported, APK builds if toolchain available, APKs placed in dist/android/

DATABASE: Stable patient IDs, foreign keys, patient-scoped queries, audit events, no cross-patient contamination

WEBSITE: Extensive project explanation, Scientific architecture, Hardware, Physiology, Chrono-Metabolic, AI/ML, Ultrasound, Digital Twin, Patient platform, Doctor platform, Version history, Safety, Roadmap, Documentation

ENDO-TWIN: Core architecture documented, Personal baseline supported, Longitudinal state supported, Provenance supported, Uncertainty supported, Model registry architecture supported, CHRONO-PCOS represented as disease-specific module, No unsupported universal-digital-twin claims

## Roadmap

CHRONO-PCOS ↓ ENDO-TWIN CORE ↓ Disease-specific research models ↓ Future validated applications

Do not claim future functionality is already implemented

Future: ENDO-TWIN NEXUS direction, other endocrine research modules - CONCEPT not implemented

## Final Principle

Optimize for COHERENCE, RELIABILITY, SCIENTIFIC INTEGRITY, PATIENT DATA ISOLATION, USABILITY, ACCESSIBILITY, PERFORMANCE, PRIVACY, EXPLAINABILITY, REPRODUCIBILITY, EXTENSIBILITY

Final project must feel like ONE ecosystem, not Python demos + Android demo + website + launcher

```
                CHRONO-PCOS
                     |
                ENDO-TWIN
                     |
      +--------------+--------------+
      |              |              |
   PATIENT         DOCTOR        RESEARCH
      |              |              |
   Android        Android          PC
      |              |              |
      +--------------+--------------+
                     |
               Shared Data Model
                     |
            Scientific Core / AI
                     |
         Ultrasound / Longitudinal
                     |
               Reports / Audit
                     |
                Website / Demo
```

Goal is not to make CHRONO-PCOS LOOK impressive, goal is to make it ACTUALLY impressive
