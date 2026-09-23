# SCIENTIFIC CORE - ENDO-TWIN V8.3+

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED

## Preserve Original Science

Preserve and recover strongest implementation of:

- PPG acquisition
- PPG filtering
- Artifact handling
- Signal quality
- HR
- HRV
- Motion/activity
- Temperature (DS18B20 skin-contact probe)
- Sensor communication
- Streaming
- Feature extraction
- Personal baseline
- Longitudinal analysis
- Sleep/circadian analysis
- Chrono-metabolic analysis
- Multimodal fusion
- Ultrasound processing
- PCOS modelling
- Reports
- Model artifacts
- Datasets
- Database functionality
- Hardware/Arduino functionality

Do NOT replace scientifically meaningful working component with simplified placeholder merely because new version is cleaner. Refactor and migrate.

## Current Implementation

### PPG Acquisition

- Hardware: MAX30102/PPG, Arduino Nano pod + Mega hub in arduino/
- Serial: serial_io/arduino_reader.py packet_parser.py led_controller.py network_reader.py
- Streaming: demo_stream.py replay.py synthetic.py
- Quality: quality.py blends heuristic + ppg_quality_model.joblib 5.1M 15 features PhysioNet 19 rec 8 subj 903 windows ROC AUC 0.624 honest low educational artifact blended 40% weight
- Reconnection handling, graceful failure sensor unavailable/disconnected/noisy/missing/invalid/serial failure/partial

### Signal Processing

- src/signal_processing/ ppg.py ecg.py hrv.py imu.py spo2.py temperature.py filters.py
- Filtering, baseline removal, artifact detection, quality control, missing handling, 20Hz $CP3 CRC XOR
- End-to-end pipeline: filtering → SQA → reconstruction → peak detection → IBI → HR/HRV - benchmarked against E2E-PPG and research-project, not replaced without evidence
- HR: 72 bpm MEASURED quality 0.91 source MAX30102 PPG
- HRV: RMSSD SDNN pNN50 48 ms DERIVED quality 0.85 source PPG-derived limitations PPG less accurate than ECG motion artifacts affect

### Feature Extraction

- src/core/feature_extraction.py, shared_features.py, quality_control.py
- Established MEASURED HR temp motion, derived HRV RMSSD/SDNN/pNN50, experimental circadian autonomic metabolic
- Distinguishes established/derived/experimental/ML/clinical, explainability

### Personal Baseline

- src/core/personal_baseline.py, src/endo_twin/baseline/general_baseline.py
- First-class component: rolling baseline, robust statistics mean/median variability MAD/outlier handling baseline confidence baseline age drift missingness time-of-day context
- Never fabricate baseline, when insufficient Insufficient baseline data

### Longitudinal Engine

- src/core/longitudinal_engine.py, src/endo_twin/longitudinal/general_longitudinal.py, endo_twin/longitudinal/longitudinal_engine.py
- Session-level hourly daily weekly monthly cycle-level, meaningful deviations not isolated numbers, 6 scenarios stable LOW CHANGE gradual EARLY CHANGE persistent PERSISTENT MULTIMODAL temporary TEMPORARY EVENT sensor failure LOW SENSOR CONFIDENCE recovery RECOVERY TREND
- Core scientific story NOT today's number, it is personal baseline → time series → change → persistence → recovery → context
- Do not generate trends from insufficient observations

### Chrono-Metabolic Fingerprinting

- disease_models/chrono_pcos/chrono_metabolic/pcos_chrono_metabolic.py, src/core/chrono_metabolic (if exists), docs/08_CHRONO_METABOLIC.md
- Domains: Circadian sleep timing activity timing temp rhythm regularity, Autonomic HR HRV recovery stress-response, Metabolic context glucose activity sleep temp observations, Coordination relationships between domains
- Clearly distinguish OBSERVED DERIVED MODEL-INFERRED EXPERIMENTAL, do not turn hypotheses into established medical claims
- Experimental research not diagnosis

### Multimodal Fusion

- src/fusion/multimodal_fusion.py
- Combines circadian autonomic variability activity temp metabolic longitudinal into fingerprint with provenance explainability

### Ultrasound

- disease_models/chrono_pcos/ultrasound/pcos_ultrasound.py, desktop/doctor_app/patient_management.py UltrasoundViewer, launcher/ultrasound.py
- Modular: Image→Validation→Preprocessing→Quality→Feature Extraction→Segmentation/Model→Uncertainty→Explanation→CHRONO-PCOS
- Never present experimental imaging as clinically validated diagnosis, quality gate UNKNOWN by design unless computed, provenance CLINICALLY-ENTERED vs IMAGE-DERIVED fusion weight 0.20, if insufficient training data state insufficient never fabricate percentages

### PCOS Modelling

- Deterministic research logic: src/disease_modules/pcos.py CYCLE_W 1.20 METABOLIC_W 0.90 etc INTERCEPT -3.0 CYCLE_NEUTRAL 15.0 sigmoid research risk signal wearable+clinical, confidence from coverage+quality not hard-coded
- Real model: disease_models/chrono_pcos/model/real_pcos_model_adapter.py REAL adapter pcos_risk_model.joblib 17M 37 features 541 rows ROC AUC 0.9594 patient-level CV, pipeline input→validation→prep→preprocessing→inference→calibration→uncertainty→explanation→provenance
- Keep both with clear distinction: deterministic for wearable context when lab values unavailable, real for clinical context when lab values available
- Language: PCOS-associated physiological and clinical risk signals, never wearable detects PCOS

### Reports

- reports/report_generator.py, disease_models/chrono_pcos/reports/pcos_reports.py
- Professional with disclaimer Research / risk-screening output — not a medical diagnosis, model transparency name/version/input/data quality/confidence/features/limitations, never hide uncertainty/manufacture confidence

### Model Artifacts

- chrono_pcos_project V8/models/pcos_risk_model.joblib 17M REAL dict CalibratedClassifierCV VotingClassifier 37 features target PCOS Y/N meta 541 rows CV ROC AUC 0.9594
- chrono_pcos_project V8/models/ppg_quality_model.joblib 5.1M REAL Pipeline RF 15 features PhysioNet 19 rec 8 subj 903 windows ROC AUC 0.624 honest low educational artifact
- Preserved, not replaced with placeholder

### Datasets

- chrono_pcos_project V8/data/ public datasets PCOS_data_without_infertility.xlsx 541 rows
- data/ demo/synthetic/public
- PhysioNet Wrist PPG During Exercise retained locally 19 rec 8 subj 903 windows
- Never mix REAL/SYNTHETIC silently, never label synthetic as clinical, never fabricate patient records

### Hardware

- hardware/ ESP32-S3 wearable + Mega hub, MAX30102/PPG, HR, HRV, MPU6050, DS18B20 skin probe, wiring docs
- Preserve working V8.1 functionality, Nano pod, Mega hub

## Performance

- Import core 267.9 ms, DB init 61.6 ms, deterministic inference 0.3 ms extremely fast, dashboard 22.2 ms fast, model loading 2386 ms bottleneck background preload
- Use async background workers lazy loading indexes caching memoization vectorized batch incremental preloading ring buffers
- See docs/performance/PERFORMANCE_REPORT.md real measurements not fabricated

## Offline-First

Core works without internet, no unnecessary cloud dependencies, degrade gracefully.

## Provenance & Uncertainty

- Provenance MEASURED CLINICAL_ENTRY DERIVED IMAGE_DERIVED MODEL_INFERRED DEMO SIMULATED UNKNOWN first-class
- Uncertainty honestly represented model_confidence data_quality coverage validation, never hard-code fake confidence percentages, Uncertainty not established if cannot produce reliable

## Limitations

- Engineering validation only, clinical validation NOT ESTABLISHED
- PPG-derived HRV less accurate than ECG, skin temp not core temp, wrist activity not whole-body
- Small datasets 541 rows, synthetic excluded honest
- Research prototype not replacement for professional medical evaluation
- See docs/23_SAFETY_ETHICS.md and docs/ai_ml/MODEL_DIAGNOSTIC_REPORT.md
