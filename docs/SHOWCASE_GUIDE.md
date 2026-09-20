# Showcase Guide - CHRONO-PCOS V8.3+ Full Demonstration

## Overview

Science-fair demonstration polished end-to-end 17 steps integrated ecosystem not unrelated apps.

Sense • Model • Predict • Personalize • Connect

Research / risk-screening output — not a medical diagnosis

## Launch

```bash
./LAUNCH/FULL_SHOWCASE.sh
# Or
./FULL_SHOWCASE.sh
# Or
python demo/full_showcase.py
# Or via Control Center
./COMPLETE_LAUNCHER.sh → Full Showcase card → OPEN
```

GUI: PySide6 1450x950 polished with NEXT/SKIP/EXIT non-blocking, console fallback if PySide6 missing.

## 16 Steps Demo

### Step 1: Project Overview

CHRONO-PCOS V8.3+ - Class 11 Research Innovation

Sense • Model • Predict • Personalize • Connect

What is: Local-first multimodal AI-assisted PCOS/PCOD risk pre-screening research ecosystem

- Sensing: MAX30102 PPG HR HRV, MPU6050 motion, DS18B20 temp, GSR, ECG, BME280
- Signal Processing: Filtering, baseline removal, artifact detection, quality control, feature extraction
- Chrono-Metabolic Fingerprinting: Circadian, autonomic, variability, activity, temp, metabolic, longitudinal, baseline calibration, distinguishing established/derived/experimental/ML/clinical, explainability
- AI/ML: PCOS, Sleep, Cardiometabolic, Autonomic risk signals only, confidence, limitations, NOT ESTABLISHED clinical validation, model transparency name/version/input/data quality/confidence/features/limitations never hide uncertainty
- Ultrasound: Loading, preprocessing, quality checks, segmentation, inference, visualization, confidence, training, evaluation, storage, no invented accuracy, state if insufficient, quality gate UNKNOWN by design provenance CLINICALLY-ENTERED vs IMAGE-DERIVED fusion weight 0.20
- Patient App: Dashboard status/sensor/recent/quality/cycle/sessions/notifications, Profile minimal basic/questionnaire/cycle/symptoms, Measurements guided PPG/HR/HRV/GSR/motion/temp/quality graceful failure, Symptoms structured, Cycle tracking dates/length/irregularity/symptoms/notes not diagnosis, Results understandable language Data quality Good not raw unless advanced, Reports, Doctor Sharing controlled export local-first, accessibility large readable multilingual-ready offline-first Kivy SQLite Buildozer
- Doctor PC: Dashboard overview/recent/quality/pending/longitudinal, Patient Management create/search/open/archive/history, Physiological raw/filtered PPG/HR/HRV/GSR/motion/temp/quality/artifacts visualization time-series, Advanced Analysis circadian/autonomic/metabolic/fingerprint/multimodal/AI distinguishing categories explainability, Ultrasound all V8.3 caps, Longitudinal comparison, Notes, Reports professional with disclaimer Research / risk-screening output — not a medical diagnosis
- Doctor Android: Mobile companion patient list/search/profiles/recent/trends/screening/ultrasound/reports/notes/follow-up not duplicate full PC
- Local DB: SQLite 18 tables patients/profiles/symptoms/cycles/sensor_sessions/PPG/HRV/GSR/motion/temp/quality/ultrasound/model_results/analysis_results/reports/doctor_notes/providers/supplies/audit/access no upload private health to public website default no cloud portability controlled export/import/backup/restore/encrypted package deliberate not automatic
- Care Discovery: FIND CARE map/list distance/specialty/address/hours/services/contact/directions OSM no API key offline-first verification verified/pending/unverified/demo never falsely label demo clearly marked separate from private records Example Nearby ABC Women's Clinic 1.2km Gynecology Verified [View][Directions] Supply discovery sensor accessories/monitoring/menstrual/general no prescription sales no auto medication
- Public Website: Home tagline What is Problem How it Works flow Sensors→Signal→Feature→Baseline→Longitudinal→Multimodal→Fingerprint→Screening→Doctor Review Technology Arduino/PPG/HR/HRV/GSR/motion/temp/ultrasound/AI/signal Patient App Doctor App Care Discovery Research hypothesis/methodology Benefits without unsupported claims Safety limitations Privacy local-first role offline Docs links 25 docs Footer Design serious modern scientific clean typography diagrams accessible colors responsive mobile strong identity avoid excessive animations/fake claims/stock AI doctor/100% accurate/fake hospital branding

Safety: Research prototype not replacement avoid definitive diagnosis/meds/treatment orders/unsupported claims encourage professional consult

### Step 2: Problem Statement

PCOS challenges: irregular cycles, hyperandrogenism, polycystic ovaries, metabolic, 70% undiagnosed, Rotterdam criteria requires 2/3 clinical+ultrasound+biochemical, longitudinal importance, affordability, privacy, accessibility, offline-first

### Step 3: Hardware - Actual Sensors

- MAX30102 PPG IR+RED HR HRV what/why/signal/limitations/implemented MEASURED
- MPU6050 accelerometer+gyroscope motion activity what/why/signal/limitations/implemented MEASURED
- DS18B20 temperature skin temp what/why/signal/limitations/implemented MEASURED skin not core affected environment
- GSR galvanic skin response tonic/phasic what/why/signal/limitations/implemented MEASURED+DERIVED
- ECG heart electrical what/why/signal/limitations/implemented PROPOSED
- BME280 environmental what/why/signal/limitations/implemented PROPOSED

Each with what measured, why relevant to PCOS/chrono-metabolic, signal characteristics, limitations, implemented status

### Step 4: Physiology

- HR bpm MEASURED source MAX30102 quality 0.91
- HRV RMSSD SDNN pNN50 DERIVED source PPG-derived limitations PPG less accurate than ECG quality 0.85
- Motion ax_g ay_g az_g gx_dps gy_dps gz_dps motion_index activity_level MEASURED source MPU6050 quality 0.8 limitations wrist not whole-body
- Temp skin temp C room temp slope MEASURED+DERIVED source DS18B20 quality 0.88 limitations skin not core affected environment
- GSR tonic lowpass phasic highpass MEASURED+DERIVED source GSR
- Sleep duration/timing/regularity day/night activity MODEL-INFERRED source HR/HRV 24h pattern + activity limitations not polysomnography
- Autonomic HRV+GSR EXPERIMENTAL
- Metabolic multimodal HR HRV activity temp GSR hypothesized EXPERIMENTAL not clinical

### Step 5: Signal Processing

Pipeline: SENSOR → TRANSPORT → PARSING → QUALITY CONTROL → FILTERING → ARTIFACT DETECTION → FEATURE EXTRACTION → TIMESTAMPED STORAGE → PERSONAL BASELINE → LONGITUDINAL CHANGE → RISK LOGIC → MULTIMODAL FUSION → EXPLANATION → REPORT/UI

- Filtering: bandpass 0.5-4Hz PPG lowpass baseline motion lowpass temp median GSR lowpass tonic highpass phasic
- Baseline removal: PPG drift GSR tonic/phasic temp baseline
- Artifact detection: motion MPU6050 correlation PPG amplitude HR outlier GSR jumps quality 0-1 per channel source labeling
- Missing handling: short gaps interpolation quality penalty long gaps mark missing not fabricate
- Quality: overall 0-1 per channel ppg motion temp reason codes
- Feature extraction: established MEASURED HR bpm MAX30102 skin temp C DS18B20 motion MPU6050 GSR raw derived HRV RMSSD SDNN pNN50 resting HR GSR tonic lowpass phasic highpass activity level classified temp slope derivative pulse amplitude SpO2 IR/RED ratio experimental circadian sleep-wake estimation HR/HRV 24h pattern model-inferred limitations not polysomnography autonomic HRV+GSR metabolic multimodal chrono-metabolic fingerprint longitudinal trend personal baseline deviation
- Gracefully handle sensor unavailable/disconnected/noisy/missing/invalid/serial failure/partial

### Step 6: Chrono-Metabolic Fingerprinting

Major section:

- Circadian: HR/HRV 24h pattern circadian disruption
- Autonomic: HRV+GSR autonomic regulation
- Variability: HRV RMSSD SDNN pNN50 variability
- Activity: motion activity level day/night
- Temp: skin temp slope circadian
- Metabolic: multimodal HR HRV activity temp GSR hypothesized metabolic regulation experimental not clinical
- Longitudinal: baseline mean median std MAD rolling confidence min obs circadian context learns what is normal for individual first 6 scenarios stable baseline LOW CHANGE SIGNAL gradual deviation EARLY CHANGE SIGNAL persistent deviation PERSISTENT MULTIMODAL SIGNAL temporary disturbance TEMPORARY EVENT sensor failure LOW SENSOR CONFIDENCE recovery RECOVERY TREND
- Baseline: personal baseline mean median std MAD rolling confidence min obs circadian context
- Multisystem: chrono-metabolic fingerprint combination circadian autonomic variability activity temp metabolic longitudinal experimental research not diagnosis
- Provenance: MEASURED CLINICALLY ENTERED IMAGE-DERIVED MODEL-INFERRED UNKNOWN
- Implementation: ChronoMetabolicFingerprint engine

### Step 7: Digital Twin

Computational representation not perfect simulation, 7 steps: Sensors→Signal→Features→Baseline→Longitudinal→Fingerprint→Screening

### Step 8: AI/ML

Data/Features/Training/Validation/Registry/Explainability distinction Data vs Model vs Inference vs Clinical

- Data: public PCOS_data.csv 541 rows PUBLIC DATASET wrist_ppg_during_exercise s1-s9 synthetic 10 subjects 30 days 6 scenarios 60 days wrist_ppg SYNTHETIC clearly labelled SYNTHETIC never label synthetic as clinical never mix REAL/SYNTHETIC silently clinical USER-ENTERED age BMI cycle info glucose BP if entered ultrasound structured features with provenance labeling REAL/SYNTHETIC/SIMULATED/PUBLIC DATASET/USER-ENTERED/MEASURED/CLINICALLY ENTERED/IMAGE-DERIVED/MODEL-INFERRED/UNKNOWN never mix silently
- Features: established MEASURED derived EXPERIMENTAL
- Training: ModelTrainer input features quality scores dataset public 541 rows synthetic cohort 10 subjects 30 days 6 scenarios 60 days split subject-level not row-level avoid leakage validation 12 categories engineering vs clinical separation no fabricated accuracy state if insufficient metrics accuracy precision recall F1 AUC classification MAE regression never fabricate percentages
- Validation: ModelEvaluator metrics Train/Validation/Test split leakage detection subject-level validation where appropriate avoid data leakage longitudinal subjects split at SUBJECT level clearly separate ENGINEERING VALIDATION implemented from CLINICAL VALIDATION NOT ESTABLISHED
- Registry: model name version dataset version training date features target metrics validation strategy limitations model approval rollback inference uncertainty ModelTrainer ModelEvaluator MultimodalFusion ShapExplainer
- Explainability: ShapExplainer feature drivers SHAP values understandable language why system generated signal drivers baseline deviations trends model name version dataset version training date features target metrics validation strategy limitations never hide uncertainty manufacture confidence training results never invent model metrics if no trained model exists show Model not trained rather than fake accuracy confidence model output not clinical certainty quality scores 0-1 per channel artifact flags reason codes limitations model transparency
- Modules: PCOSModule v8.3.0 pcos_associated_risk low/moderate/high NOT diagnosis confidence 0.75 data quality 0.85 clinical validation NOT ESTABLISHED SleepModule circadian_disruption_pattern moderate confidence 0.68 CardiometabolicModule cardiometabolic_risk_signal moderate never claims diabetes/hypertension/CVD diagnosis AutonomicModule autonomic_regulation_signal moderate explainable estimator separating ACUTE SIGNAL from PERSISTENT LONGITUDINAL CHANGE not mental-health diagnosis each with consistent API name version required_features optional_features predict explain confidence limitations returns structured research signals never DISEASE DETECTED
- Safety: research/prototype risk-screening NOT diagnosis distinguish screening/research vs diagnosis patient language understandable Data quality Good not raw unless advanced model transparency name/version/input/data quality/confidence/features/limitations never hide uncertainty/manufacture confidence medical safety research/prototype not replacement avoid definitive diagnosis/medication prescriptions/treatment as orders/unsupported claims/fabricated stats encourage professional consultation

### Step 9: Ultrasound

Pipeline 11 steps quality gate UNKNOWN by design provenance CLINICALLY-ENTERED vs IMAGE-DERIVED

1. Image Import: image path format size check metadata label REAL/SYNTHETIC/DEMO
2. Image Preview: preview metadata shape
3. Image Metadata: path shape quality check pending source label
4. Preprocessing: resize normalize denoise
5. Region/Structure Analysis: cyst detection morphology volume if model available
6. Feature Extraction: cyst size mm volume cc morphology quality source confidence provenance
7. Model Inference: requires trained model if insufficient state insufficient never fabricate percentages confidence None unless computed model accuracy not established without validation dataset
8. Result Visualization: overlay confidence map image-derived features
9. Uncertainty: confidence None unless computed quality score UNKNOWN by design unless computed limitations never hard-code fake confidence percentages
10. Provenance: source image → preprocessing → detected features → quality → uncertainty CLINICALLY-ENTERED vs IMAGE-DERIVED distinction fusion weight 0.20
11. Export/Report: storage ultrasound_records table patient_id image_path cyst_size_mm volume_cc morphology quality source confidence notes created_at label REAL/SYNTHETIC/DEMO report with IMAGE-DERIVED label

Quality gate UNKNOWN by design unless computed provenance CLINICALLY-ENTERED vs IMAGE-DERIVED fusion weight 0.20 If insufficient training data state insufficient never fabricate percentages Inference requires trained model if not available state insufficient Do not claim clinically validated unless actually is If existing model exists use it if not build infrastructure without fabricating performance Safety ultrasound analysis research not diagnosis requires clinical evaluation Rotterdam requires ultrasound + clinical

### Step 10: Patient App

Dashboard status/sensor/recent/quality/cycle/sessions/notifications Profile minimal basic/questionnaire/cycle/symptoms Measurements guided PPG/HR/HRV/GSR/motion/temp/quality graceful failure Symptoms structured Cycle tracking dates/length/irregularity/symptoms/notes not diagnosis Results understandable language Data quality Good not raw unless advanced Reports Doctor Sharing controlled export local-first accessibility large readable multilingual-ready offline-first Kivy SQLite Buildozer

Expected APK DIST/android/CHRONO_PCOS_Patient.apk source android/patient_app/main.py buildozer.spec build scripts BUILD_PATIENT_APK.sh status honest APK not built PC demo Kivy

### Step 11: Doctor PC + Android

Doctor PC complete technical interface Dashboard overview/recent/quality/pending/longitudinal Patient Management create/search/open/archive/history Physiological raw/filtered PPG/HR/HRV/GSR/motion/temp/quality/artifacts visualization time-series Advanced Analysis circadian/autonomic/metabolic/fingerprint/multimodal/AI distinguishing categories explainability Ultrasound all V8.3 caps Longitudinal comparison Notes Reports professional with disclaimer Research / risk-screening output — not a medical diagnosis

Doctor Android mobile companion patient list/search/profiles/recent/trends/screening/ultrasound/reports/notes/follow-up not duplicate full PC

### Step 12: Local DB + Portability

Local DB SQLite 18 tables patients/profiles/symptoms/cycles/sensor_sessions/PPG/HRV/GSR/motion/temp/quality/ultrasound/model_results/analysis_results/reports/doctor_notes/providers/supplies/audit/access No upload private health to public website default no cloud Portability controlled export/import/backup/restore/encrypted package deliberate not automatic

### Step 13: Care Discovery FIND CARE

Map/list distance/specialty/address/hours/services/contact/directions OSM no API key offline-first verification verified/pending/unverified/demo never falsely label demo clearly marked separate from private records Example Nearby ABC Women's Clinic 1.2km Gynecology Verified [View][Directions] Supply discovery sensor accessories/monitoring/menstrual/general no prescription sales no auto medication Provider verification statuses verified/pending/unverified/demo never falsely label real doctor/clinic verified prototype allow demo clearly marked Provider-directory separate from private records

Example: Nearby ABC Women's Clinic 1.2km Gynecology Verified [View][Directions] - 4 demo providers 5 supplies demo clearly marked

### Step 14: Public Website

Home tagline What is Problem How it Works flow Sensors→Signal→Feature→Baseline→Longitudinal→Multimodal→Fingerprint→Screening→Doctor Review Technology Arduino/PPG/HR/HRV/GSR/motion/temp/ultrasound/AI/signal Patient App Doctor App Care Discovery Research hypothesis/methodology Benefits without unsupported claims Safety limitations Privacy local-first role offline Docs links 25 docs Footer Design serious modern scientific clean typography diagrams accessible colors responsive mobile strong identity avoid excessive animations/fake claims/stock AI doctor/100% accurate/fake hospital branding

Structure: HOME hero Sense•Model•Predict•Personalize with architecture preview PROBLEM PCOS challenges longitudinal importance HOW IT WORKS interactive flow Sensors→Signal→Quality→Features→Baseline→Longitudinal→AI→Ultrasound→Fusion→Explanation→Patient/Doctor with MEASURED/CLINICALLY-ENTERED/IMAGE-DERIVED/MODEL-INFERRED/UNKNOWN labels HARDWARE actual sensors MAX30102/MPU6050/DS18B20/GSR/ECG/BME280 with what/why/signal/limitations/implemented PHYSIOLOGY HR/HRV/motion/temp/GSR/sleep/autonomic/metabolic CHRONO-METABOLIC major section circadian/autonomic/metabolic/temporal/baseline/multisystem with provenance DIGITAL TWIN computational representation not simulation AI/ML Data/Features/Training/Validation/Registry/Explainability distinction Data vs Model vs Inference vs Clinical ULTRASOUND pipeline 11 steps quality gate UNKNOWN by design provenance CLINICALLY-ENTERED vs IMAGE-DERIVED PLATFORMS Patient/Doctor detailed sections ANDROID APK build workflow DATABASE 18 tables local-first REPORTING professional with disclaimer CARE DISCOVERY FIND CARE demo providers TIMELINE V0-V8.3+ interactive with IMPLEMENTED/PROPOSED/CONCEPT SAFETY research prototype disclaimer ROADMAP CHRONO-PCOS→ENDO-TWIN NEXUS DEMO 16 steps DOCS 25+2

Design: serious modern scientific clean typography diagrams accessible colors responsive mobile strong identity avoid excessive animations/fake claims/stock AI doctor/100% accurate/fake hospital branding

### Step 15: Reporting + Safety + Privacy

Professional reports with disclaimer Research / risk-screening output — not a medical diagnosis Model transparency name/version/input/data quality/confidence/features/limitations never hide uncertainty Safety research prototype not replacement avoid definitive diagnosis/meds/treatment orders/unsupported claims encourage professional consult Privacy local-first role offline

### Step 16: Timeline + Roadmap

V0-V8.3+ 13 items with IMPLEMENTED/PROPOSED/CONCEPT distinguishing actual changes V0 Concept V1 Arduino PPG V2 HR/HRV V3 GSR/Motion/Temp V4 Quality/Artifact/Baseline V5 AI/ML PCOS module V6 Ultrasound V7 Chrono-metabolic V8 Patient/Doctor apps V8.1 Complete Control Center V8.3+ Polished scientific website APK build workflow Android Build Guide SETUP.sh BUILD scripts polished launcher no clipped text

Roadmap: CHRONO-PCOS→Clinical→Digital Twin→ENDO-TWIN NEXUS future research not implemented mark as Future research never add unsupported modules cancer Alzheimer infectious kidney liver thyroid without dataset

## GUI Behavior

- NEXT button: next step
- SKIP button: skip to next category
- EXIT button: exit showcase
- Non-blocking, polished, scroll area, WordWrap, min sizes, responsive
- Each step shows real operations, actual checks, never fake
- DEMO/SIMULATED labeled, never label synthetic as clinical
- Console fallback if PySide6 missing

## Science-Fair Demonstration

Polished end-to-end 17 steps integrated ecosystem not unrelated apps share common terminology/data model/scientific foundation/identity/UI/safety language

One coherent digital health research ecosystem not collection random apps/mockups/disconnected demos

## Testing

Run:

```bash
./LAUNCH/FULL_SHOWCASE.sh
# Or
python demo/full_showcase.py
```

Should show 16 steps all PASS including Reports 26c6a816 disclaimer

Check logs/ for showcase log

## Safety

Research prototype not medical diagnosis, local-first offline privacy-focused, no cloud upload, no prescription sales, no treatment decisions, encourage professional consultation.

## Next Steps

- Run showcase
- Read docs/ARCHITECTURE.md
- Read docs/INSTALLATION.md
- Visit website via LAUNCH/WEBSITE.sh
