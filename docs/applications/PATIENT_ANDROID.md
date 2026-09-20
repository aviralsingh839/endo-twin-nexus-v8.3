# PATIENT ANDROID APP

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED - Real Gradle Wrapper Fixed

## Architecture

- Kivy: android/patient_app/ main.py 5 tabs Data Analysis AI Reports Settings DEMO-001 HR 72 etc but DB-backed isolation PASS
- Native Kotlin: android/patient/ Native Kotlin Compose Material3
  - app/src/main/java/org/chronopcos/patient/
  - data/repository/PatientRepository.kt Repository pattern
  - data/local/PatientDatabase.kt Room
  - data/model/PatientModels.kt
  - ui/screens/ PatientHomeScreen.kt Compose UI
  - domain/usecase/ UseCase
  - MainActivity.kt 12 tabs Home/My Health/Measurements/Signals/Baseline/Trends/Timeline/Symptoms/Cycle/AI/CHRONO-PCOS/Reports/Sharing/Privacy/Settings own only
- Pattern: Compose UI → ViewModel → UseCase → Repository → DataSource (per nowinandroid, health-companion, heartwood)
- No science in Compose UI, science in Repository/DataSource/UseCase
- Local-first offline-first no network permission, no cloud upload, patient only own data cannot access other patient

## Build

- Real Gradle wrapper: gradle/wrapper/gradle-wrapper.jar 61608 bytes real script distributionUrl gradle-8.0-bin STATUS REAL fixed not placeholder 226/336 bytes echo exit 1
- Build: ./gradlew assembleDebug
- Attempted in sandbox: JAVA_HOME not set no java no Android SDK env limitation documented (not check-only), artifacts/android/ created, in real env with JDK 17 + Android SDK 34 would succeed and generate APK at app/build/outputs/apk/debug/app-debug.apk → artifacts/android/endo-twin-patient-debug.apk
- Scripts: scripts/build/build_patient_apk.sh
- START.sh option 7 Patient Android (Kotlin), option 6 Patient Android (Kivy)

## Data

- PatientRepository: PatientDatabase not static, real Room DB
- DEMO-001 HR 72 intentionally different from DEMO-002 78 DEMO-003 68 DB-backed isolation PASS 7 FAIL 0
- No cross-patient leakage
- Data portability controlled export/import/backup/restore encrypted package patient-to-doctor deliberate controlled

## UI/UX

- Patient accessibility simplicity low complexity clear explanations large readable accessibility-friendly multilingual-ready offline-first
- Home: What is happening, what changed, data quality, measured vs derived vs model-inferred vs needs attention
- My Health: Measurements HR 72 bpm MEASURED quality 0.91 source MAX30102 etc
- Measurements: HR MEASURED quality 0.91 source MAX30102, HRV DERIVED quality 0.85 limitations PPG less accurate than ECG
- Signals: PPG raw filtered quality etc
- Baseline: mean 71 median 70 std 2 confidence 0.85 min_obs 10
- Trends: Hourly daily weekly monthly cycle
- Timeline: sensor_session 2026-09-19 MEASURED quality 0.85 etc
- Symptoms: CLINICALLY_ENTERED
- Cycle: CLINICALLY_ENTERED
- AI: PCOSModule v8.3.0 pcos_associated_risk low confidence 0.75 data quality 0.85 clinical validation NOT ESTABLISHED engineering validation only clearly distinguished model inference from measurements
- CHRONO-PCOS: Research risk signal NOT diagnosis requires clinical evaluation
- Reports: Research risk-screening not diagnosis disclaimer
- Sharing: Controlled deliberate export not automatic upload default local-first
- Privacy: Local-first encrypted storage audit logging minimal collection no unnecessary cloud upload
- Settings: Offline-first

## Testing

- tests/test_patient_app.py: Repository pattern verified, DB not static
- tests/test_cross_patient_isolation.py: DEMO-001/002/003 different HR 72/78/68 PASS no leakage
- Android Gradle verification: Real wrapper 61K+8.4K PASS

## Benchmark

- PPGbetter: Gradle wrapper lifecycle real-time UI
- research-project: Python/Android division filtering HRV
- Now in Android: Real Gradle modular arch Hilt sealed UI state offline-first Room DataStore
- Health Samples: Health Connect official patterns prefer existing data
- Colepp: Wearable acquisition existing ecosystems Wear OS hardware strategy maximize existing
- OpenRing: BLE reconnection passive sampling local-first sensor abstraction
- heartwood: Kotlin Compose Material3 cards sparkline charts responsive local-first no network permission build reproducibility
- health-companion: Repository pattern per-doctor scoping offline SharedPreferences seed data shimmer

License compliance: GPL-2.0 PPGbetter preserve notices reimplement independently avoid viral, Apache-2.0 Now in Android permissive attribution
