# LIMITATIONS - ENDO-TWIN V8.3+

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED - Honest limitations

## Scientific Honesty

Never claim clinical validation diagnosis guaranteed accuracy superiority medical efficacy real patient performance unless actual evidence supports it.

Clearly distinguish OBSERVED DERIVED MODEL-INFERRED EXPERIMENTAL DEMO SIMULATED

## Current Limitations

### Engineering Validation Only

- Clinical validation NOT ESTABLISHED
- Research prototype, not medical device, not replacement for professional medical evaluation
- Engineering validation only

### Sensors

- PPG-derived HRV less accurate than ECG, motion artifacts affect
- Skin temp not core temp, affected environment, DS18B20 skin temp room temp temp slope
- Wrist activity not whole-body calorimetry, MPU6050 motion ax ay az gx gy gz motion index activity level
- , affected environment
- MAX30102 PPG IR+RED HR SpO2 pulse amplitude 20Hz $CP3
- Quality affected by motion, pressure, skin tone
- Gracefully handle sensor unavailable/disconnected/noisy/missing/invalid/serial failure/partial

### Models

- pcos_risk_model.joblib 17M dict CalibratedClassifierCV VotingClassifier 37 features target PCOS Y/N meta dataset PCOS_data_without_infertility.xlsx 541 rows leaky dropped Pregnant/Abortions/HCG CV 5-fold stratified-group patient-level CV ROC AUC 0.9594 AP 0.9324 notes synthetic excluded - GOOD methodology but sample 541 small, requires lab values FSH LH etc. not wearable alone, distribution may have selection bias, CV only no separate test set may be optimistic
- ppg_quality_model.joblib 5.1M Pipeline RF 15 features PhysioNet wrist PPG 19 rec 8 subj 903 windows usable_rate 0.3477 window 10s label |PPG HR - ECG HR|<=5 bpm CV GroupKFold by subject ROC AUC 0.624 std 0.141 AP 0.5043 keep_rate_0_5 0.2835 top_features zero_cross_rate/hr_bpm/ibi_cv/dom_peak_diff/band_power notes educational artifact wrist PPG sensor differs from MAX30102 blended at 40% weight - HONEST low metrics, small sample 19 rec 8 subj, performance low 0.624 barely above random 0.5 std 0.141 high unstable, usable_rate low 34% wrist PPG during exercise very noisy, sensor mismatch wrist vs MAX30102 different characteristics may not transfer, label quality heuristic not gold standard
- Deterministic research logic src/disease_modules/pcos.py CYCLE_W 1.20 etc sigmoid research risk signal wearable+clinical not real joblib, research priors not clinical model, when lab values unavailable
- Never display fabricated confidence number, if model cannot produce reliable uncertainty show Uncertainty not established rather than inventing one
- No fake AI - real models with honest metrics not 100% accuracy claims

### Data

- Small datasets 541 rows, synthetic excluded honest, synthetic 10 subjects 30 days 6 scenarios 60 days wrist_ppg SYNTHETIC clearly labelled SYNTHETIC never label synthetic as clinical never mix REAL/SYNTHETIC silently never fabricate patient records
- PhysioNet Wrist PPG During Exercise retained locally 19 rec 8 subj 903 windows usable_rate 0.3477
- DEMO-001,002,003 intentionally different data HR 72/78/68 clearly labeled DEMO_DATA separate from private records

### Ultrasound

- Quality gate UNKNOWN by design unless computed, provenance CLINICALLY-ENTERED vs IMAGE-DERIVED fusion weight 0.20, every result labelled IMAGE-DERIVED
- If insufficient training data state insufficient never fabricate percentages, inference requires trained model if not available state insufficient
- Experimental imaging not clinically validated diagnosis, never present experimental imaging as clinically validated diagnosis
- Benchmark against MONAI, use OHIF/3D Slicer as UX/workflow references, keep experimental imaging clearly labelled

### Clinical

- Research / risk-screening output — not a medical diagnosis, requires clinical evaluation, Rotterdam criteria for PCOS diagnosis requires qualified healthcare professional, PCOS diagnosis requires clinical evaluation using Rotterdam criteria oligo-anovulation hyperandrogenism polycystic ovaries by qualified professional, wearable physiology alone cannot diagnose PCOS, ultrasound features UNKNOWN by design until validated labelled dataset exists, model not clinically validated
- Never claim diagnosis, clinical validation, medical accuracy, diagnostic sensitivity/specificity, clinical superiority, regulatory approval unless actual documented evidence exists
- Encourage professional consultation, no medication prescriptions no treatment as orders

### Performance

- Model loading 2386 ms bottleneck due to 17M VotingClassifier 500+400 trees CalibratedClassifierCV cv=3, real inference 993 ms moderate, deterministic 0.3 ms extremely fast, dashboard 22 ms fast, DB init 61 ms fast
- Optimize via background preload caching array not DataFrame lazy deterministic first, target after optimization Import <200 ms DB <50 ms Model loading <500 ms background cached Real inference <500 ms
- See docs/performance/PERFORMANCE_REPORT.md real measurements not fabricated

### Android

- Real Gradle wrapper 61K jar + 8.4K script fixed not placeholder, attempted ./gradlew assembleDebug for real fails JAVA_HOME not set no java no Android SDK env limitation documented (not check-only), artifacts/android/ created, in real env with JDK 17 + Android SDK 34 would succeed and generate APK at app/build/outputs/apk/debug/app-debug.apk → artifacts/android/endo-twin-patient-debug.apk
- No device/emulator in sandbox, installation tested where possible limitation documented

### Privacy

- Local-first offline-first no cloud, no upload private health to public website default without cloud, encrypted storage Fernet if available else PROTOTYPE_ENCRYPTED labeled, controlled export, audit logging, minimal collection, no cloud upload, patient cannot access other patient doctor only authorized, role system PATIENT own data/measurements/results/manage/share DOCTOR authorized/review/analysis/notes/reports ADMIN provider directory/system config/demo data/verification
- No secrets in source, .env.example with no real secrets, .env not committed

## Safety

- Research prototype not replacement for professional medical evaluation
- Avoid definitive diagnosis medication prescriptions treatment as orders unsupported claims fabricated stats
- Encourage professional consultation
- Disclaimer Research / risk-screening output — not a medical diagnosis on every report
- See docs/SAFETY_AND_LIMITATIONS.md

## Honest Metrics

- pcos_risk_model ROC AUC 0.9594 AP 0.9324 - not 100%, realistic
- ppg_quality_model ROC AUC 0.624 std 0.141 AP 0.5043 keep_rate_0_5 0.2835 usable_rate 0.3477 - honest low, educational artifact
- Never fabricate ML metrics, clinical records
- If model cannot produce reliable uncertainty show Uncertainty not established rather than inventing one
- Never hide uncertainty manufacture confidence training results never invent model metrics if no trained model exists show Model not trained rather than fake accuracy
