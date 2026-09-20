# ORIGINAL PROJECT INVENTORY - V8.3

Date: 2026-09-19
Branch: arena/01a0ab67-chrono-pcos-v8-1
Commit: afe6315 (architectural correction)
Purpose: Inspect entire V8.3 project first, create inventory of Python modules/UI components/ML/AI/ultrasound/signal-processing/sensor interfaces/database/reports/training scripts/config/demo/docs/tests/dependencies, map dependencies, identify reusable/refactor/unchanged.

ABSOLUTE: every working V8.3 feature must remain unless compelling technical reason, do not silently delete.

## 1. Project Root Structure

- `chrono_pcos_project V8/` - Original V8 project (preserved)
  - `models/pcos_risk_model.joblib` 17M REAL
  - `models/ppg_quality_model.joblib` 5.1M REAL
  - `src/` original source
  - `arduino/` Nano pod + Mega hub
  - `data/` public datasets
  - `docs/` original docs
  - `tests/`

- `src/` - Core reusable modules (V8.1 -> V8.3)
  - `config.py` - System config
  - `data_models.py` - Patient, measurement models
  - `app.py` - Main app
  - `core/` - Feature extraction, longitudinal, baseline, quality, shared_features
  - `disease_modules/` - PCOS, autonomic, cardiometabolic, sleep, base, registry
  - `endo_twin/` - General ENDO-TWIN architecture (core, baseline, longitudinal, models, physiology, provenance, uncertainty, ai, data, explainability, features, fusion, signals)
  - `explainability/` - Explanation engine
  - `fusion/` - Multimodal fusion
  - `serial_io/` - Arduino reader, packet parser, LED controller, network reader
  - `signal_processing/` - PPG, ECG, GSR, HRV, IMU, SpO2, temperature, filters
  - `ui/` - Main window, live plots, gauges, vital cards, theme
  - `utils/` - Quality, history_store, logger, math_utils, demo_stream, replay, report, storage, synthetic, qr_encoder
  - `validation/`

- `disease_models/chrono_pcos/` - CHRONO-PCOS specific
  - `manifest.py` - Model manifest
  - `model/chrono_pcos_model.py` - Deterministic research logic (wearable+clinical)
  - `model/real_pcos_model_adapter.py` - REAL adapter for pcos_risk_model.joblib (NEW)
  - `features/pcos_features.py`
  - `chrono_metabolic/pcos_chrono_metabolic.py`
  - `ultrasound/pcos_ultrasound.py`
  - `reports/pcos_reports.py`
  - `tests/`

- `android/` - Android projects
  - `patient_app/` - Kivy Patient App (main.py, buildozer.spec) - TabbedPanel Dashboard/Profile/Measurements/Symptoms/Cycle/Results/Find Care
  - `doctor_app/` - Kivy Doctor App (main.py, buildozer.spec) - patient list/search/profiles/recent/trends/screening/ultrasound/reports/notes
  - `patient/` - Native Kotlin Compose Patient (gradle) - app/build.gradle.kts, settings.gradle.kts, MainActivity.kt, data/database, model, repository, ui/screens, navigation
  - `doctor/` - Native Kotlin Compose Doctor (gradle) - similar
  - `patient/gradlew` and `doctor/gradlew` - Previously placeholders, NOW REAL (61K jar + 8.4K script)

- `apps/` - New modular apps (ENDO-TWIN architecture)
  - `main/main_app.py` - General dashboard ENDO-TWIN tagline Understand physiological patterns over time (no PCOS-specific knowledge needed) - TEST1 PASS
  - `doctor_desktop/`, `patient_android/`, `doctor_android/`, `research_lab/` - stubs for extensibility

- `desktop/doctor_app/` - Doctor PC app
  - `patient_management.py`
  - Other modules

- `database/` - Local DB
  - `database.py` - Original DB
  - `endo_twin_database.py` - ENDO-TWIN DB with DEMO_DATA (DEMO-001,002,003) clearly labeled
  - `security.py` - Security

- `launcher/` - Control Center GUI
  - `main.py` - Complete Launcher Control Center
  - `diagnostics.py` - Diagnostics
  - `ai_ml.py`, `care_finder.py`, `chrono_metabolic.py`, `database.py`, `doctor_pc.py`, `patient_app.py`, `signal_processing.py`, `ultrasound.py`

- `LAUNCH/` - Shell launchers for Garuda Linux
  - `DIAGNOSTICS.sh`, `COMPLETE_LAUNCHER.sh`, `PATIENT_ANDROID.sh`, `DOCTOR_ANDROID.sh`, `DOCTOR_PC.sh`, etc.
  - All launchers check .venv and log to logs/

- `demo/` - Demo mode
  - `full_showcase.py` - 17 steps integrated ecosystem
  - `demo_flow.py` - Demo flow

- `reports/` - Reporting
  - `report_generator.py`

- `website/` - Public website (if exists)

- `provider_network/` - Care discovery

- `docs/` - 25 docs required
  - `01_PROJECT_OVERVIEW.md` to `25_RESEARCH_METHODOLOGY.md` - WHAT and WHY
  - Additional: ANDROID_BUILD_GUIDE.md, ARCHITECTURE.md, etc.
  - `recovery/` - This recovery docs (NEW)
  - `ai_ml/MODEL_DIAGNOSTIC_REPORT.md` (NEW)

- `tests/` - Testing
  - DB/sensor/signal/artifact/missing/reconnection/permissions/report/import/export/Android UI/PC UI/AI/ultrasound + failures

- `scripts/` - Scripts
  - `dataset_links.py`, `generate_synthetic_dataset.py`
  - `run.sh`, `build.sh`, `diagnostics.sh` (NEW)
  - `run/gui.sh, patient.sh, doctor.sh, build.sh` (NEW)
  - `build/android.sh, gradle.sh` (NEW)
  - `diagnostics/run.sh, android.sh` (NEW)

- Root launchers
  - `START.sh` (NEW canonical)
  - `COMPLETE_LAUNCHER.sh`, `BUILD_ALL_APKS.sh`, `BUILD_PATIENT_APK.sh`, `BUILD_DOCTOR_APK.sh`, `ENDO_TWIN.sh`, `SETUP.sh`, `setup_garuda.sh`

- `artifacts/android/` - APK output (NEW, attempted builds)
- `DIST/android/` - APK output for Kivy builds
- `logs/` - Logs

## 2. Python Modules (151 files)

Core:
- src/config.py
- src/data_models.py
- src/app.py
- src/core/feature_extraction.py
- src/core/longitudinal_engine.py
- src/core/personal_baseline.py
- src/core/quality_control.py
- src/core/shared_features.py
- src/disease_modules/base.py
- src/disease_modules/pcos.py - Deterministic research logic (CYCLE_W 1.20 etc sigmoid) - NOT real joblib, research risk signal wearable+clinical
- src/disease_modules/autonomic.py
- src/disease_modules/cardiometabolic.py
- src/disease_modules/sleep.py
- src/disease_modules/registry.py
- src/endo_twin/core/patient.py, measurement.py, twin_core.py
- src/endo_twin/models/disease_model_interface.py, model_registry.py
- src/endo_twin/baseline/general_baseline.py
- src/endo_twin/longitudinal/general_longitudinal.py
- src/endo_twin/physiology/general_physiology.py
- src/endo_twin/provenance/general_provenance.py
- src/endo_twin/uncertainty/general_uncertainty.py - Contains example pcos_risk 0.75 (DEMO, not real path)
- src/signal_processing/ppg.py, ecg.py, gsr.py, hrv.py, imu.py, spo2.py, temperature.py, filters.py
- src/serial_io/arduino_reader.py, packet_parser.py, led_controller.py, network_reader.py
- src/ui/main_window.py, live_plots.py, gauges.py, vital_cards.py, theme.py
- src/utils/quality.py - Blends heuristic + ppg_quality_model 40% weight
- src/utils/history_store.py, logger.py, math_utils.py, demo_stream.py, replay.py, report.py, storage.py, synthetic.py, qr_encoder.py
- src/explainability/explanation_engine.py
- src/fusion/multimodal_fusion.py
- disease_models/chrono_pcos/model/chrono_pcos_model.py
- disease_models/chrono_pcos/model/real_pcos_model_adapter.py (NEW) - Real inference pipeline
- disease_models/chrono_pcos/features/pcos_features.py
- disease_models/chrono_pcos/chrono_metabolic/pcos_chrono_metabolic.py
- disease_models/chrono_pcos/ultrasound/pcos_ultrasound.py
- disease_models/chrono_pcos/reports/pcos_reports.py
- launcher/main.py, diagnostics.py, etc.
- apps/main/main_app.py - General dashboard ENDO-TWIN
- database/endo_twin_database.py - DEMO_DATA

## 3. UI Components

- Patient Android Kivy: TabbedPanel Dashboard/Profile/Measurements/Symptoms/Cycle/Results/Find Care, large readable, accessibility-friendly
- Doctor Android Kivy: patient list/search/profiles/recent/trends/screening/ultrasound/reports/notes/follow-up
- Patient Native Kotlin: MainActivity.kt, PatientHomeScreen.kt, PatientNavigation.kt, components, database, repository
- Doctor Native Kotlin: similar
- Doctor PC: PySide6/PyQtGraph main_window.py, live_plots, gauges, vital_cards, patient_management.py
- Launcher Control Center: main.py GUI with buttons for all modules
- Theme: theme.py consistent identity

## 4. ML/AI Models

REAL:
- pcos_risk_model.joblib 17M dict CalibratedClassifierCV VotingClassifier lr+rf+et 37 features PCOS Y/N meta dataset PCOS_data_without_infertility.xlsx 541 rows leaky dropped Pregnant/Abortions/HCG CV 5-fold stratified-group patient-level ROC AUC 0.9594 AP 0.9324 notes synthetic excluded - GOOD methodology
- ppg_quality_model.joblib 5.1M dict Pipeline median+StandardScaler+RandomForest 15 features PhysioNet Wrist PPG 19 rec 8 subj 903 windows usable_rate 0.3477 window 10s label |PPG HR - ECG HR|<=5 bpm CV GroupKFold by subject ROC AUC 0.624 std 0.141 AP 0.5043 keep_rate_0_5 0.2835 top_features zero_cross_rate/hr_bpm/ibi_cv/dom_peak_diff/band_power notes educational artifact wrist differs MAX30102 blended 40% weight - HONEST low metrics

DETERMINISTIC RESEARCH LOGIC:
- src/disease_modules/pcos.py - CYCLE_W 1.20 METABOLIC_W 0.90 etc INTERCEPT -3.0 CYCLE_NEUTRAL 15.0 sigmoid - research risk signal wearable+clinical, NOT joblib, preserved separate purpose

ADAPTER:
- disease_models/chrono_pcos/model/real_pcos_model_adapter.py - Implements required pipeline model input→schema validation→feature preparation→preprocessing→real inference→raw→calibration→uncertainty→explanation→provenance with honest uncertainty, no fabricated confidence, model transparency

## 5. Signal Processing

- PPG: ppg.py - filtering, peak detection, HR, HRV, quality
- ECG: ecg.py
- GSR: gsr.py
- HRV: hrv.py - RMSSD, etc.
- IMU: imu.py - MPU6050 motion
- SpO2: spo2.py - MAX30102
- Temperature: temperature.py - DS18B20
- Filters: filters.py - baseline calibration, filtering
- Quality: quality.py - ppg_quality heuristic + model blended 40%, artifact handling, missing handling, reconnection
- Core: feature_extraction.py, quality_control.py, shared_features.py, personal_baseline.py, longitudinal_engine.py

## 6. Sensor Interfaces

- Arduino Nano pod + Mega hub - arduino/
- MAX30102/PPG, HR, HRV, GSR, MPU6050, DS18B20
- Serial: arduino_reader.py, packet_parser.py, network_reader.py, led_controller.py
- Reconnection handling, graceful failure sensor unavailable/disconnected/noisy/missing/invalid/serial failure/partial

## 7. Database

- SQLite tables: patients/profiles/symptoms/cycles/sensor_sessions/PPG/HRV/GSR/motion/temp/quality/ultrasound/model_results/analysis_results/reports/doctor_notes/providers/supplies/audit/access
- database.py, endo_twin_database.py, security.py
- Local-first, no upload private health to public website, default no cloud
- Portability: controlled export/import/backup/restore/encrypted package deliberate not automatic
- DEMO_DATA: DEMO-001,002,003 clearly labeled DEMO_DATA

## 8. Reports

- report_generator.py, pcos_reports.py
- Professional with disclaimer "Research / risk-screening output — not a medical diagnosis."
- Understandable language Data quality Good not raw unless advanced

## 9. Training Scripts

- scripts/generate_synthetic_dataset.py, dataset_links.py
- chrono_pcos_project V8 original training (models created)
- No retraining needed, use existing real artifacts

## 10. Config

- src/config.py
- build.gradle.kts, settings.gradle.kts for Android
- buildozer.spec for Kivy
- requirements.txt

## 11. Demo

- demo/full_showcase.py - 17 steps integrated ecosystem
- demo/demo_flow.py
- utils/demo_stream.py, replay.py, synthetic.py
- Strong workflow DEMO PATIENT→Simulated sensor→Signal→AI→Fingerprint→Ultrasound→Screening→Doctor dashboard→Report labeled DEMO/SIMULATED

## 12. Docs

- 25 docs 01-25 plus additional
- ANDROID_BUILD_GUIDE.md explains Kivy vs Native, BUILD scripts, prerequisites, check-only mode
- recovery/ORIGINAL_PROJECT_INVENTORY.md (this), RECOVERY_PLAN.md (next), MODEL_DIAGNOSTIC_REPORT.md

## 13. Tests

- tests/ - DB/sensor/signal/artifact/missing/reconnection/permissions/report/import/export/Android UI/PC UI/AI/ultrasound + failures
- apps/main/main_app.py acceptance tests 6 PASS (general dashboard, 3 models, main without disease model, extensibility dummy future models, preserved original functionality, isolation)

## 14. Dependencies

- Python: PySide6/PyQtGraph/NumPy/Pandas/PySerial, Kivy, Buildozer
- Android Native: Kotlin 1.9.0, Compose BOM 2023.10.01, Room 2.6.1, etc.
- Gradle 8.0, compileSdk 34, minSdk 24, targetSdk 34
- Keep Python/PySide6/PyQtGraph/NumPy/Pandas/PySerial no Dash/Plotly/Flask/Electron unless reason

## 15. Preserved vs Refactor vs Unchanged

- Preserved every V8.3 major/AI/ultrasound/sensor/demo: pcos_risk_model.joblib REAL, ppg_quality_model.joblib REAL, signal processing, sensor interfaces, Arduino Nano/Mega, demo, reports, 25 docs, Android Kivy source, Doctor PC, database, launcher
- Refactor: Android gradlew placeholder → real (61K jar + 8.4K script) + attempt assembleDebug, START.sh canonical launcher, scripts/run/build/diagnostics, real_pcos_model_adapter.py for real inference pipeline
- Unchanged: src/disease_modules/pcos.py deterministic research logic (wearable context), src/endo_twin/ general architecture, database DEMO_DATA, UI theme, etc.

## 16. Issues Found

- Placeholder gradlew: 226/336 bytes echo install SDK exit 1 - MUST be replaced with real - DONE now real 61K jar + 8.4K script, attempted build, fails JAVA_HOME not set (env limitation documented)
- Hard-coded 0.75: Found in general_uncertainty.py, longitudinal_engine.py, endo_twin_database.py, demo, reports, launcher - Classification: A genuinely generated (real adapter), B deterministic research logic (pcos.py confidence from coverage), C demo (DEMO_DATA clearly labeled), D hard-coded placeholder (none in real path) - Real path uses computed confidence 0.5*coverage+0.2*optional+0.3*quality, not 0.75
- Feature mismatch: Real model expects 37 clinical features with lab values, wearable module uses PPG-derived + cycle - Both valid different purposes, keep both with clear distinction
- No fake AI: Real models with honest metrics ROC AUC 0.9594 and 0.624 not 100%

## 17. Acceptance Criteria Status

- Preserve every V8.3 major/AI/ultrasound/sensor/demo: YES
- New ecosystem Patient Android/Doctor Android/Doctor PC/Local DB/export/import/Care/Provider/Supply/Website: Patient Android Kivy+Native exists, Doctor Android Kivy+Native exists, Doctor PC exists, Local DB exists, export/import exists, Care/Provider exists, Website structure exists in docs
- Engineering modular/offline/error/security/role/testing/docs: Modular yes, offline-first yes, error handling yes, security local auth/role separation, role system PATIENT/DOCTOR/ADMIN, testing 6 PASS, docs 25+ exist
- Scientific integrity no fabricated AI/accuracy/false claims clear screening vs diagnosis limitations explainable: Real models honest metrics, no 100% claims, disclaimer Research risk-screening not diagnosis, explainability real drivers, uncertainty honest

## 18. Next Steps

- RECOVERY_PLAN.md - Staged phases 1-10
- Fix hard-coded inference removal from real path (already computed, ensure no placeholder in real inference)
- Architecture test ENDO-TWIN core no direct PCOS import
- UI redesign scientific+medical+premium
- Final recovery report
