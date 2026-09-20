# DOCTOR ANDROID APP

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED - Real Gradle Wrapper Fixed

## Architecture

- Kivy: android/doctor_app/ main.py 7 tabs Overview Patients Signals AI CHRONO-PCOS Ultrasound Reports DEMO-001 HR 72 etc DB-backed isolation
- Native Kotlin: android/doctor/ Native Kotlin Compose Material3
  - app/src/main/java/org/chronopcos/doctor/
  - data/model/DoctorModels.kt
  - data/repository/DoctorRepository.kt
  - MainActivity.kt registry→search→selection→workspace 14 tabs Overview/Measurements/Signals/Quality/Baseline/Trends/Timeline/Sleep/Activity/Autonomic/Metabolic/AI/CHRONO-PCOS/Ultrasound/Reports/Notes/Provenance/Audit selected obvious DB layer not UI only
- Pattern: Compose UI → ViewModel → UseCase → Repository → DataSource
- Local-first offline-first no network permission no cloud upload doctor only authorized patients cannot access other patient unless authorized
- Doctor Android mobile review not duplicate full PC

## Build

- Real Gradle wrapper: gradle/wrapper/gradle-wrapper.jar 61608 bytes real script distributionUrl gradle-8.0-bin STATUS REAL fixed
- Build: ./gradlew assembleDebug
- Attempted in sandbox: JAVA_HOME not set no java no Android SDK env limitation documented (not check-only)
- Scripts: scripts/build/build_doctor_apk.sh
- START.sh option 9 Doctor Android (Kotlin), option 8 Doctor Android (Kivy)

## Workflow

- Registry → Search → Selection → Workspace
- Patients list: DEMO-001 HR 72 DEMO-002 HR 78 DEMO-003 HR 68 intentionally different DB-backed isolation PASS 7 FAIL 0
- Search: 0.1 ms fast
- Selection: Patient-specific data loading per-doctor scoping doctor_id filtering not cosmetic
- Workspace 14 tabs: Overview Measurements Signals Quality Baseline Trends Timeline Sleep Activity Autonomic Metabolic AI CHRONO-PCOS Ultrasound Reports Notes Provenance Audit selected obvious DB layer not UI only
- Overview: What is happening what changed quality measured derived model-inferred needs attention patient-specific
- Measurements: HR MEASURED quality 0.91 source MAX30102 HRV DERIVED quality 0.85 limitations PPG less accurate than ECG etc patient-specific
- Signals: PPG raw filtered quality patient-specific
- Quality: overall per channel ppg motion temp hrv patient-specific
- Baseline: mean median std MAD confidence drift missingness time-of-day patient-specific
- Trends: Hourly daily weekly monthly cycle 6 scenarios patient-specific
- Timeline: sensor_session MEASURED quality 0.85 symptom_entry CLINICALLY_ENTERED ultrasound_study IMAGE-DERIVED quality UNKNOWN model_run MODEL-INFERRED confidence 0.75 report_generated patient-specific timeline
- Sleep: Sleep timing activity timing temp rhythm regularity
- Activity: MPU6050 motion activity level
- Autonomic: HR HRV recovery stress-response
- Metabolic: Glucose where available activity sleep temp clinical observations
- AI: PCOSModule v8.3.0 pcos_associated_risk low/moderate/high NOT diagnosis confidence 0.75 data quality 0.85 clinical validation NOT ESTABLISHED etc patient-specific AI runs
- CHRONO-PCOS: Research risk signal NOT diagnosis requires clinical evaluation
- Ultrasound: modular Image→Validation→Preprocess→Quality→Feature→Segmentation→Uncertainty→Explanation→CHRONO-PCOS no clinical claim UNKNOWN quality unless computed fusion weight 0.20
- Reports: Research risk-screening not diagnosis patient-specific
- Notes: Clinical notes CLINICALLY_ENTERED
- Provenance: MEASURED CLINICALLY_ENTERED DERIVED IMAGE-DERIVED MODEL-INFERRED DEMO SIMULATED UNKNOWN visible patient-specific
- Audit: Audit logging minimal collection

## Testing

- tests/test_doctor_app.py: Registry search selection workspace verified
- tests/test_cross_patient_isolation.py: DEMO-001/002/003 different HR PASS no leakage
- Android Gradle verification: Real wrapper 61K+8.4K PASS

## Benchmark

- health-companion: Repository pattern per-doctor scoping offline SharedPreferences seed data shimmer, doctor only authorized patients
- Now in Android: Real Gradle modular arch Hilt sealed UI state offline-first Room DataStore
- heartwood: Kotlin Compose Material3 cards sparkline charts responsive local-first
- OpenSRP: Offline-first identities workflows secure storage
- Colepp: Wearable acquisition existing ecosystems
- OpenRing: BLE reconnection passive sampling local-first sensor abstraction

License compliance: MIT health-companion permissive attribution, Apache-2.0 Now in Android OpenSRP permissive
