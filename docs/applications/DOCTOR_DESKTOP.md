# DOCTOR DESKTOP APP

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED

## Purpose

Complete technical interface for clinicians/researchers, not duplicate full PC on Android.

## Architecture

- desktop/doctor_app/ main_enhanced.py + patient_management.py
- launcher/doctor_pc.py
- PySide6 PyQtGraph NumPy Pandas
- START.sh option 3 Doctor Desktop

## Workflow

- Registry → Search → Selection → Workspace
- Patients list: DEMO-001 HR 72 DEMO-002 HR 78 DEMO-003 HR 68 intentionally different DB-backed isolation PASS
- Search: 0.1 ms fast real execution
- Selection: Patient-specific data loading per-doctor scoping doctor_id filtering not cosmetic
- Workspace: Overview Measurements Signals Quality Baseline Trends Timeline Sleep Activity Autonomic Metabolic AI CHRONO-PCOS Ultrasound Reports Notes Provenance Audit selected obvious DB layer not UI only

## Features

- Overview: What is happening what changed quality measured derived model-inferred needs attention patient-specific
- Measurements: HR MEASURED quality 0.91 source MAX30102 HRV DERIVED quality 0.85 limitations PPG less accurate than ECG GSR Temp SpO2 Activity patient-specific
- Signals: PPG raw filtered quality ECG GSR IMU Temp patient-specific
- Quality: overall per channel ppg motion temp hrv patient-specific
- Baseline: mean median std MAD confidence drift missingness time-of-day patient-specific personal baseline first what is unusual for this person not generic reference
- Trends: Hourly daily weekly monthly cycle 6 scenarios stable low change gradual early change persistent multimodal temporary event sensor failure low confidence recovery trend personal baseline → time series → change → persistence → recovery → context core scientific story
- Timeline: sensor_session MEASURED quality 0.85 symptom_entry CLINICALLY_ENTERED ultrasound_study IMAGE-DERIVED quality UNKNOWN model_run MODEL-INFERRED confidence model output report_generated patient-specific timeline
- Sleep: Sleep timing activity timing temp rhythm regularity
- Activity: MPU6050 motion activity level
- Autonomic: HR HRV recovery stress-response
- Metabolic: Glucose where available activity sleep temp clinical observations
- AI: PCOSModule v8.3.0 pcos_associated_risk low/moderate/high NOT diagnosis confidence data quality clinical validation NOT ESTABLISHED engineering validation only input PPG HRV activity temp features HRV RMSSD activity level skin temp limitations small dataset synthetic never hide uncertainty model registry name version dataset version training date features target metrics validation strategy limitations never hide uncertainty manufacture confidence training results - patient-specific AI runs
- CHRONO-PCOS: Research risk signal NOT diagnosis requires clinical evaluation circadian moderate disruption experimental_research q=0.9 autonomic moderate dysregulation derived_feature q=0.9 metabolic experimental signal experimental_research q=0.8 fingerprint version 8.3+ components provenance disclaimer Research experimental not medical diagnosis
- Ultrasound: modular Image→Validation→Preprocess→Quality→Feature→Segmentation→Uncertainty→Explanation→CHRONO-PCOS no clinical claim UNKNOWN quality unless computed fusion weight 0.20 every result labelled IMAGE-DERIVED quality gate UNKNOWN by design unless computed if insufficient training data state insufficient never fabricate percentages experimental imaging not clinically validated diagnosis never present experimental imaging as clinically validated diagnosis
- Reports: Research risk-screening not diagnosis HR 72 bpm MEASURED quality 0.91 HRV 48 ms DERIVED quality 0.85 Activity 35% MEASURED Temp 32.5C MEASURED Model PCOSModule v8.3.0 confidence data quality clinical validation NOT ESTABLISHED DEMO DATA clearly marked disclaimer Research risk-screening output not medical diagnosis requires clinical evaluation patient-specific
- Notes: Clinical notes CLINICALLY_ENTERED provider_id
- Provenance: MEASURED CLINICALLY_ENTERED DERIVED IMAGE-DERIVED MODEL-INFERRED DEMO SIMULATED UNKNOWN visible patient-specific
- Audit: Audit logging minimal collection

## Design System

- Doctor professional dense complete technical interface
- Scientific premium calm modern fast trustworthy midnight ocean medical-tech
- Typography spacing cards charts progressive disclosure responsive accessible empty/loading/error states
- Offline-first core offline demo local no cloud demo labeled never clinical error explicit graceful handle sensor unavailable/disconnected/noisy/missing/invalid/serial failure/partial

## Testing

- tests/test_doctor_desktop.py: Registry search switching scoped data reports models ultrasound notes provenance audit verified
- tests/test_cross_patient_isolation.py: DEMO-001/002/003 different HR PASS no leakage
- tests/test_architecture_isolation.py: Core not coupled to PCOS dynamic importlib PASS

## Performance

- Search 0.1 ms fast, dashboard 22 ms fast
- See docs/performance/PERFORMANCE_REPORT.md

## Benchmark

- health-companion: Repository pattern per-doctor scoping offline SharedPreferences seed data shimmer doctor only authorized patients
- Clinical Dashboard: Pipeline metadata calibration
- Now in Android: Modular arch sealed UI state offline-first
- OHIF: Viewer UX professional - adopt for ultrasound viewer UX
