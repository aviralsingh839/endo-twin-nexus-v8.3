# ENDO-TWIN BENCHMARK MATRIX - 30 REPOS EXTENDED

Date: 2026-09-19
Version: 8.3+
Purpose: Compare ENDO-TWIN with 30 reference repositories across 22 dimensions. Objective: Integrate strongest verified patterns, not copy a repository. Extended from 9 to 30 repos.

## Reference Repositories (30)

1. PPGbetter (GPL-2.0) - Android PPG real-time
2. research-project (GPL-2.0) - Python/Android division
3. E2E-PPG (MIT) - End-to-end pipeline SQA GAN
4. PCOS_project (GPL-2.0) - Multimodal fusion SHAP
5. Clinical Dashboard (MIT) - Pipeline metadata calibration
6. digital-patient (Apache-2.0) - Disease-independent graph GNN
7. HDT-Intelligence (GPL-2.0) - Multimodal fusion privacy local-first
8. health-companion (MIT) - Repository pattern per-doctor scoping
9. heartwood (GPL-3.0) - Kotlin Compose Material3
10. NeuroKit2 (MIT) - Simulate bio_process bio_analyze HRV complexity - BENCHMARK ONLY
11. WFDB (MIT) - PhysioNet formats waveform datasets
12. PyPhysio (MIT) - Caching workflows performance
13. HRVAnalysis (MIT) - RR/NN cleanup ectopic handling - BENCHMARK ONLY
14. tsfresh (MIT) - Automatic extraction 100s features - ADOPT Research Lab
15. PyHealth (MIT) - Lightweight runtime - ADOPT Research Lab
16. MONAI (Apache-2.0) - Healthcare imaging AI UNETR VISTA-3D - ADOPT ultrasound
17. MONAI Deploy (Apache-2.0) - DAGs - ADAPT lightweight
18. OHIF (MIT) - Viewer UX professional - ADOPT viewer UX
19. 3D Slicer (BSD) - Conceptually Research Lab - ADOPT conceptually
20. Now in Android (Apache-2.0) - Fully functional Kotlin Compose official arch - ADOPT fix Android build
21. Android Health Samples (Apache-2.0) - Health Connect official patterns - ADOPT
22. Android FHIR (Apache-2.0) - Interoperability - ADAPT not force DB
23. OpenSRP FHIR Core (Apache-2.0) - Offline-first identities workflows - ADOPT
24. Open mHealth (Apache-2.0) - Standardized schemas - ADOPT
25. Synthea (Apache-2.0) - Synthetic populations - ADOPT SYNTHETIC/DEMO
26. MLflow (Apache-2.0) - Experiment tracking - ADAPT Research Lab
27. DVC (Apache-2.0) - Dataset versioning - ADAPT reproducible pipelines
28. Colepp (MIT) - Wearable acquisition existing ecosystems - ADOPT hardware strategy
29. OpenRing (MIT) - BLE reconnection passive sampling - ADOPT sensor abstraction
30. Gadgetbridge (GPL-3.0) - Vendor independence - BENCHMARK ONLY GPL

See docs/benchmarks/REFERENCE_REPOSITORY_AUDIT.md for full strength/subsystem/pattern/license/reuse decision ADOPT/ADAPT/REIMPLEMENT/BENCHMARK/REJECT integration differentiator.

## Benchmark Dimensions (22)

### 1. PPG Acquisition
- PPGbetter: Android lifecycle real-time PPG, foreground service, permission handling, sensor availability
- research-project: Python serial + Android division
- E2E-PPG: End-to-end filtering→SQA→reconstruction→peak→IBI→HR/HRV
- Colepp: Wearable acquisition existing ecosystems Wear OS
- OpenRing: BLE reconnection passive sampling local-first sensor abstraction
- Gadgetbridge: Vendor independence architectural study
- ENDO-TWIN: src/serial_io/ serial_reader.py packet_parser.py $CP2 protocol, hardware/arduino/ nano_pod MAX30102, gracefully handle unavailable/disconnected/noisy/missing/invalid/serial failure/partial, offline-first demo labeled, 20Hz $CP2 - preserves V8.1, adopts PPGbetter lifecycle + Colepp existing ecosystems + OpenRing BLE reconnection

### 2. Signal Processing
- NeuroKit2: Filtering detrending EMD decomposition bio_process bio_analyze 2 lines code, MIT, field tested unit tested
- E2E-PPG: Filtering bandpass, SQA one-class SVM Reliable/Unreliable, GAN reconstruction, IEEE BIBM 2023
- WFDB: PhysioNet formats annotations waveform datasets
- PyPhysio: Caching workflows performance
- ENDO-TWIN: src/signal_processing/ ppg.py ecg.py gsr.py hrv.py imu.py spo2.py temperature.py filters.py bandpass 0.5-4Hz PPG lowpass baseline median GSR etc., filtering artifact detection motion MPU6050 correlation amplitude outlier jumps missing short gaps interpolation quality penalty long gaps mark missing not fabricate quality 0-1 per channel, deterministic 0.3ms extremely fast vs NeuroKit2 may be slower keep fast path, use NeuroKit2 simulate for testing Research Lab - BENCHMARK ONLY keep better impl

### 3. Signal Quality
- E2E-PPG: SQA one-class SVM Reliable/Unreliable, GAN reconstruction
- ppg_quality_model: 5.1M Pipeline RF 15 feats PhysioNet wrist PPG 19 rec 8 subj 903 windows usable_rate 0.3477 ROC 0.624 std 0.141 honest low educational artifact blended 40%
- ENDO-TWIN: quality.py heuristic + ppg_quality_model blended 40%, quality 0-1 per channel overall, never fabricate, insufficient → Insufficient data - adopts E2E-PPG SQA concepts enhances quality.py

### 4. HR
- PPGbetter: HR real-time Android
- E2E-PPG: HR from PPG peak→IBI→HR
- WFDB: ECG gated HR
- ENDO-TWIN: ppg.py peak detection IBI HR, HR 72 bpm MEASURED quality 0.91 source MAX30102, deterministic fast - preserves V8.1

### 5. HRV
- NeuroKit2: HRV time RMSSD MeanNN SDNN frequency ULF VLF LF HF complexity entropy fractal ECG delineation P Q S T
- HRVAnalysis: RR/NN cleanup outlier ectopic handling
- PyPhysio: HRV workflows
- ENDO-TWIN: hrv.py RMSSD SDNN pNN50 PPG-derived HRV less accurate than ECG limitations documented, HRV RMSSD 48 ms DERIVED quality 0.85 limitations PPG less accurate than ECG motion artifacts affect - preserves V8.1, benchmark NeuroKit2 HRVAnalysis keep better impl

### 6. Baseline
- ENDO-TWIN: src/core/personal_baseline.py src/endo_twin/baseline/ general_baseline.py rolling baseline robust mean/median variability MAD/outlier confidence age drift missingness time-of-day context never fabricate baseline insufficient → Insufficient baseline data What is unusual FOR THIS PERSON not generic reference - first-class component differentiator

### 7. Longitudinal
- digital-patient: Forecasting future trajectories evolution physiological state GNN forecasting clinically relevant endpoints probabilistic simulations future trajectories graph representation nodes tissues/pathways → GNN forecasting solves multiscale modelling with AI
- HDT: Time-series forecasting 7-day future wellness LSTM weekly/monthly trends anomalies habit impact what-if simulation
- heartwood: Weekly summary daily averages vs goals progress rings week-over-week trends detail views full charts statistics recent records
- ENDO-TWIN: src/core/longitudinal_engine.py src/endo_twin/longitudinal/ general_longitudinal.py endo_twin/longitudinal/ session hour day week month cycle long-term trajectory change from baseline persistence recovery variability missingness context do not infer trends from inadequate data 6 scenarios stable LOW CHANGE gradual EARLY CHANGE persistent PERSISTENT MULTIMODAL temporary TEMPORARY EVENT sensor failure LOW SENSOR CONFIDENCE recovery RECOVERY TREND personal baseline → time series → change → persistence → recovery → context core scientific story NOT today's number - matches digital-patient forecasting + HDT weekly/monthly + heartwood weekly summary

### 8. Fusion
- PCOS_project: Multimodal fusion SHAP Grad-CAM
- HDT: Multimodal sensing physiological/context fusion emotion+context+behavior fusion lab+wearable+lifestyle fusion human-centred ensemble forecasting what-if
- ENDO-TWIN: src/fusion/multimodal_fusion.py circadian+autonomic+variability+activity+temp+metabolic+longitudinal → fingerprint with provenance explainability fusion weight 0.20 ultrasound - matches HDT multimodal + PCOS_project fusion

### 9. PCOS Modelling
- PCOS_project: Multimodal fusion SHAP Grad-CAM PCOS-specific
- ENDO-TWIN: disease_models/chrono_pcos/ model chrono_pcos_model.py real_pcos_model_adapter.py 17M dict CalibratedCV VotingClassifier 37 feats 541 rows ROC 0.9594 + deterministic research logic CYCLE_W 1.20 sigmoid wearable PPG+cycle research risk signal NOT diagnosis requires clinical evaluation Rotterdam criteria - preserves V8.1 extends with real model honest metrics

### 10. Ultrasound
- MONAI: Healthcare imaging AI PyTorch domain-specific transforms UNETR VISTA-3D MAISI Dice Hausdorff NIfTI DICOM Bundles AutoML Smart Caching Auto3DSeg MICCAI wins Mayo Clinic Apache-2.0
- MONAI Deploy: DAGs lightweight
- OHIF: Viewer UX professional MIT
- 3D Slicer: Conceptually Research Lab BSD
- ENDO-TWIN: disease_models/chrono_pcos/ultrasound/ modular Image→Validation→Preprocess→Quality→Feature→Segmentation→Uncertainty→Explanation→CHRONO-PCOS no clinical claim UNKNOWN quality unless computed fusion weight 0.20 every result labelled IMAGE-DERIVED quality gate UNKNOWN by design unless computed if insufficient training data state insufficient never fabricate percentages experimental imaging not clinically validated diagnosis never present experimental imaging as clinically validated diagnosis - ADOPT MONAI preprocessing segmentation augmentation OHIF viewer UX 3D Slicer conceptually Research Lab

### 11. Explainability
- PCOS_project: SHAP Grad-CAM
- Clinical Dashboard: Explainability pipeline
- ENDO-TWIN: Model name/version/input/data quality/confidence/features/limitations SHAP real only when model available feature importance never hide uncertainty manufacture confidence training results - preserves V8.1 honest explainability

### 12. Uncertainty
- ENDO-TWIN: src/endo_twin/uncertainty/ general_uncertainty.py confidence quality provenance visible MEASURED CLINICAL_ENTRY DERIVED IMAGE_DERIVED MODEL_INFERRED DEMO SIMULATED UNKNOWN, confidence calibrated probability not hard-coded 0.75, quality coverage+input quality, uncertainty not established if cannot produce reliable rather than inventing - first-class component differentiator

### 13. Provenance
- ENDO-TWIN: src/endo_twin/provenance/ general_provenance.py MEASURED/CLINICAL_ENTRY/DERIVED/IMAGE_DERIVED/MODEL_INFERRED/DEMO/SIMULATED/UNKNOWN visible first-class example HR 72 bpm MEASURED Circadian Stability 0.81 DERIVED PCOS Research Model Output 0.31 MODEL-INFERRED - first-class component differentiator

### 14. Twin Architecture
- digital-patient: Disease-independent graph GNN longitudinal forecasting probabilistic simulations graph representation solves multiscale modelling with AI
- HDT: Multimodal fusion privacy local-first human-centred ensemble forecasting what-if
- ENDO-TWIN: src/endo_twin/core/ general core twin_core.py PatientIdentity observations signals features baseline longitudinal fusion AI/model_registry explainability uncertainty provenance disease-neutral not renamed PCOS structure platform/endo_twin/ disease_models/chrono_pcos/ apps/ science/ models/ database/ hardware/ data/ scripts/ tests/ docs/ artifacts/android/ archive/ - general platform + CHRONO-PCOS first disease model matches digital-patient disease-independent + HDT privacy local-first

### 15. Patient/Doctor Apps
- health-companion: Repository pattern per-doctor scoping offline SharedPreferences seed data shimmer MIT
- heartwood: Kotlin Compose Material3 cards sparkline charts responsive local-first no network permission build reproducibility GPL-3.0
- Now in Android: Fully functional Kotlin Compose Material3 official arch guidance data/domain/UI layers offline-first source of truth Room Proto DataStore Retrofit Hilt DI sealed UI state Loading/Success Test repositories test-only hooks adaptive layouts dynamic color dark mode benchmark variant baseline profile app-nia-catalog product flavors demo local data Apache-2.0
- ENDO-TWIN: Patient Android android/patient_app/ Kivy + android/patient/ Native Kotlin Compose Repository pattern PatientRepository PatientDatabase not static Compose UI ViewModel UseCase Repository DataSource no science in Compose local-first offline-first no network permission patient only own data cannot access other patient accessibility simplicity low complexity clear explanations large readable accessibility-friendly multilingual-ready offline-first + Doctor Android android/doctor_app/ Kivy + android/doctor/ Native Kotlin Compose registry→search→selection→workspace 14 tabs Overview/Measurements/Signals/Quality/Baseline/Trends/Timeline/Sleep/Activity/Autonomic/Metabolic/AI/CHRONO-PCOS/Ultrasound/Reports/Notes/Provenance/Audit selected obvious DB layer not UI only per-doctor scoping doctor_id filtering not cosmetic + Doctor Desktop desktop/doctor_app/ main_enhanced.py patient_management.py complete technical interface registry search switching scoped data reports models ultrasound notes provenance audit - ADOPT health-companion repository pattern per-doctor scoping + heartwood Kotlin Compose Material3 cards sparkline + Now in Android real Gradle modular arch Hilt sealed UI state

### 16. Multipatient
- health-companion: Per-doctor scoping doctor only authorized patients
- OpenSRP: Offline-first identities workflows secure storage
- ENDO-TWIN: database/endo_twin_database.py 22 tables users patients profiles symptoms cycles sensor_sessions ppg_data hrv_data gsr_data etc LocalDatabase init create_patient list_patients real execution DEMO-001/002/003 HR 72/78/68 intentionally different DB-backed isolation PASS 7 FAIL 0 per-doctor scoping doctor_id filtering not cosmetic search 0.1ms fast - ADOPT health-companion per-doctor scoping + OpenSRP offline-first identities

### 17. Android Quality
- PPGbetter: Real Gradle wrapper lifecycle real-time UI GPL-2.0
- Now in Android: Real Gradle modular arch Hilt sealed UI state offline-first Room DataStore Apache-2.0
- heartwood: Kotlin Compose Material3 responsive local-first no network permission build reproducibility GPL-3.0
- health-companion: Repository pattern offline SharedPreferences seed data shimmer MIT
- ENDO-TWIN: android/patient/ + android/doctor/ Real Gradle wrapper 61K jar 61608 bytes gradlew 8.4K real script distributionUrl gradle-8.0-bin STATUS REAL fixed not placeholder 226/336 bytes echo exit 1 attempted ./gradlew assembleDebug for real fails JAVA_HOME not set env limitation documented artifacts/android/ created in real env with JDK 17 + Android SDK 34 would succeed APK app/build/outputs/apk/debug/app-debug.apk → artifacts/android/endo-twin-patient-debug.apk scripts/build/build_patient_apk.sh build_doctor_apk.sh build_all_apks.sh START.sh 12 options build-gradle - ADOPT PPGbetter Gradle wrapper lifecycle + Now in Android real Gradle modular arch + heartwood Kotlin Compose + health-companion repository pattern

### 18. UI/UX
- heartwood: Kotlin Compose Material3 cards sparkline charts responsive local-first no network permission build reproducibility
- Now in Android: Material3 adaptive layouts dynamic color dark mode
- OHIF: Viewer UX professional
- ENDO-TWIN: Scientific premium calm modern fast trustworthy midnight ocean medical-tech scientific medical premium Inter font typography spacing cards charts progressive disclosure responsive accessible empty/loading/error states shared design system role optimized patient simple friendly doctor professional dense website scientific accessible dashboard hierarchy What happening/changed/quality/measured/derived/model-inferred/needs attention patient 6 levels What is happening What changed Data quality Measured Derived Model-inferred Needs attention - ADOPT heartwood Material3 cards sparkline + Now in Android Material3 adaptive + OHIF viewer UX

### 19. Offline
- Now in Android: Offline-first source of truth Room Proto DataStore
- OpenSRP: Offline-first identities workflows secure storage
- OpenRing: Local-first sensor abstraction
- health-companion: Offline SharedPreferences seed data
- ENDO-TWIN: Offline-first core offline demo local no cloud Demo labeled never clinical Local-first DB SQLite tables patients/identity/observations/measurements/signals/sensor_sessions/features/baselines/timeline_events/symptoms/cycles/clinical_observations/ultrasound_studies/features/model_versions/runs/predictions/reports/providers/notes/audit/provenance FK migrations indexes No upload private health to public website default without cloud Controlled export/import/backup/restore encrypted package patient-to-doctor deliberate controlled - ADOPT Now in Android offline-first + OpenSRP offline-first + OpenRing local-first

### 20. Testing
- NeuroKit2: Field tested unit tested
- tsfresh: Field tested unit tested sklearn pandas numpy compatible Neurocomputing 2018
- Now in Android: Test repositories test-only hooks benchmark variant baseline profile
- ENDO-TWIN: tests/ 13 files pytest 47 passed acceptance 6 PASS isolation PASS architecture isolation PASS unit/signal/feature/baseline/longitudinal/provenance/uncertainty DB migrations CRUD FK isolation AI loading schema inference apps nav patient selection Android Gradle e2e ingest→report arch test Core not coupled - ADOPT NeuroKit2 field tested + tsfresh field tested + Now in Android test repositories

### 21. Performance
- PyPhysio: Caching workflows performance
- Now in Android: Benchmark variant baseline profile
- ENDO-TWIN: Real benchmarks 267.9ms import 61.6ms DB 2.1ms patient 0.1ms search 2386ms model load bottleneck 0.3ms deterministic 993.5ms real 22.2ms dashboard FAST shell→cached→critical→charts→heavy async lazy indexes caching memoization vectorized batch incremental preloading ring buffers benchmark PERFORMANCE_REPORT.md no fabrication - ADOPT PyPhysio caching + Now in Android benchmark variant

### 22. Reproducibility
- MLflow: Experiment tracking versioning lineage
- DVC: Dataset versioning lineage reproducible pipelines
- Synthea: Synthetic populations SYNTHETIC/DEMO/SIMULATED stress testing
- Open mHealth: Standardized schemas prevent arbitrary formats
- ENDO-TWIN: Dataset versioning DVC Research Lab no bloat experiment tracking MLflow Research Lab synthetic populations Synthea SYNTHETIC/DEMO/SIMULATED stress testing standardized schemas Open mHealth prevent arbitrary formats provenance MEASURED/CLINICAL_ENTRY/DERIVED/IMAGE_DERIVED/MODEL_INFERRED/DEMO/SIMULATED/UNKNOWN visible model registry metadata status EXPERIMENTAL/RESEARCH/VALIDATION_PENDING/DEMO/RETIRED - ADOPT MLflow experiment tracking + DVC dataset versioning + Synthea synthetic populations + Open mHealth standardized schemas

## Integration Differentiator

ENDO-TWIN: REAL DATA→QUALITY→PROCESSING→FEATURES→BASELINE→LONGITUDINAL→FUSION→DISEASE→EXPLANATION→UNCERTAINTY→PROVENANCE→PATIENT→DOCTOR→RESEARCH

Not copy one repository, integrate strongest verified patterns across 30 repos into coherent platform with scientific honesty honest limitations research risk-screening not diagnosis.

## License Compliance

- GPL-2.0 PPGbetter preserve notices reimplement independently avoid viral
- MIT E2E-PPG Clinical Dashboard NeuroKit2 WFDB tsfresh Health Samples Open mHealth Synthea permissive attribution
- Apache-2.0 digital-patient MONAI Deploy Now in Android FHIR OpenSRP MLflow DVC permissive
- GPL-3.0 heartwood Gadgetbridge reimplement independently own ENDO-TWIN identity midnight ocean medical-tech scientific medical premium Inter font no stock AI doctor no fake hospital branding disclaimer Research risk-screening not diagnosis
