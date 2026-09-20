# RUNNING - ENDO-TWIN V8.3+

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED

## One Launcher

```bash
./START.sh
```

Interactive menu 12 options.

## Modes

```bash
./START.sh menu          # Interactive menu (default)
./START.sh gui           # Control Center GUI launcher/main.py
./START.sh endo-twin     # ENDO-TWIN general dashboard apps/main/main_app.py
./START.sh doctor        # Doctor Desktop desktop/doctor_app/ + LAUNCH/DOCTOR_PC.sh
./START.sh patient       # Patient Demo android/patient_app/main.py PC demo
./START.sh doctor-android # Doctor Android demo android/doctor_app/main.py
./START.sh research      # Research Lab signal processing training evaluation
./START.sh diagnostics   # Diagnostics launcher/diagnostics.py
./START.sh build-patient # Build Patient APK BUILD_PATIENT_APK.sh
./START.sh build-doctor  # Build Doctor APK BUILD_DOCTOR_APK.sh
./START.sh build         # Build All APKs BUILD_ALL_APKS.sh
./START.sh build-gradle  # Real Gradle builds ./gradlew assembleDebug → artifacts/android/
./START.sh test          # pytest -q + acceptance tests
./START.sh test-cross    # Cross-patient isolation tests
./START.sh benchmark     # Performance benchmark docs/performance/PERFORMANCE_REPORT.md
./START.sh health        # Project health scripts/diagnostics/project_health.sh
./START.sh demo          # Full showcase 17 steps demo/full_showcase.py
./START.sh help          # Help
```

## Applications

### ENDO-TWIN Desktop

General personalized physiological modelling platform, disease-neutral.

Sections: Overview, Measurements, Signals, Personal Baseline, Longitudinal Trends, Sleep & Circadian, Activity, Autonomic Patterns, Metabolic Context, AI & Models, Disease Models → CHRONO-PCOS, Reports, Data & Provenance, Settings

Tagline: Understand your physiological patterns over time. (or Understand physiological patterns over time) - no PCOS knowledge needed TEST1 PASS

Works without disease model TEST3 PASS - true general architecture.

### Doctor Desktop

Multipatient workstation.

Workflow: Doctor → Patient Registry → Search/Filter → Patient Selection → Patient Workspace

Workspace: Overview, Measurements, Signals, Quality, Baseline, Trends, Timeline, Sleep, Activity, Autonomic, Metabolic context, AI/Models, CHRONO-PCOS, Ultrasound, Reports, Notes, Provenance, Audit

Selected patient identity always obvious, multipatient implemented database/repository layer not just UI.

Per-doctor scoping: each doctor sees only assigned patients.

### Patient Android

Independently usable.

Sections: Home, My Health, Measurements, Signals, Baseline, Trends, Timeline, Symptoms, Cycle, AI & Models, CHRONO-PCOS, Reports, Doctor Sharing, Data & Privacy, Settings

Patient can only access own data, no doctor patient registry.

Kivy: android/patient_app/main.py TabbedPanel Dashboard/Profile/Measurements/Symptoms/Cycle/Results/Find Care large readable accessibility-friendly low complexity clear explanations

Native: android/patient/ Kotlin Compose MainActivity.kt PatientHomeScreen.kt Material 3 health-data UI cards sparkline

### Doctor Android

Mobile companion patient list/search/profiles/recent/trends/screening/ultrasound/reports/notes/follow-up, not duplicate full PC.

Kivy: android/doctor_app/main.py

Native: android/doctor/ Kotlin Compose

### Research Lab

Signal processing, training, evaluation, validation.

Science: datasets, signal_processing, training, evaluation, validation

Models: registry/production/experimental/metadata

### Diagnostics

System diagnostics checks env, models, DB, sensors.

Project health: scripts/diagnostics/project_health.sh checks dependencies, database, scientific core, models, demo data, launchers, Android Gradle, tests, applications - real execution not file existence, returns PASS/WARN/FAIL with evidence.

## Database

Local-first SQLite.

Tables: patients, patient_identity, observations, measurements, signals, sensor_sessions, features, baselines, timeline_events, symptoms, cycles, clinical_observations, ultrasound_studies, ultrasound_features, model_versions, model_runs, predictions, reports, providers, doctor_notes, audit_events, provenance_records

DEMO-001,002,003 intentionally different data HR 72/78/68, isolation PASS 7 FAIL 0, no cross-contamination.

## Models

Real artifacts: pcos_risk_model.joblib 17M 37 features 541 rows ROC AUC 0.9594, ppg_quality_model.joblib 5.1M 15 features ROC AUC 0.624 honest low educational artifact.

Real adapter: disease_models/chrono_pcos/model/real_pcos_model_adapter.py pipeline input→validation→prep→preprocessing→inference→calibration→uncertainty→explanation→provenance, honest uncertainty, no fabricated confidence.

Deterministic research logic: src/disease_modules/pcos.py CYCLE_W 1.20 etc sigmoid research risk signal wearable+clinical, confidence from coverage+quality not hard-coded.

## Performance

Fast: DB init 61 ms, patient creation 2 ms, list/search 0.1 ms, deterministic inference 0.3 ms, dashboard 22 ms.

Bottleneck: Model loading 2386 ms, real inference 993 ms due to VotingClassifier 17M - optimize via background preload, caching, array not DataFrame, lazy deterministic first.

See docs/performance/PERFORMANCE_REPORT.md for real measurements not fabricated.

## UI/UX

Scientific Premium Calm Modern Fast Clear Trustworthy.

Midnight ocean medical-tech deep navy layered panels cyan→indigo→pink, Inter font clean typography, pyqtgraph scientific diagrams, QGroupBox clear sections, accessible colors WCAG AA, responsive QSS, strong identity, no excessive animations/fake claims/stock AI doctor/100% accurate/fake hospital branding.

Patient simple friendly large readable, doctor dense analytical, researcher technical exploratory.

Shared design system: typography, icon language, spacing, semantic colors, chart language, terminology, status indicators, animation principles.

See src/ui/theme_v83_premium.py for premium theme dark/light.

## Offline-First

Core works without internet: records/sensor/signal/AI/ultrasound/reports/DB

Internet optional: provider directory/map/updates/controlled sync

No cloud, local-first SQLite, no upload private health to public website, portability controlled export/import/backup/restore/encrypted package deliberate not automatic, graceful handling sensor unavailable.

## Safety

Research / risk-screening output — not a medical diagnosis. Requires clinical evaluation. Rotterdam criteria for PCOS diagnosis requires qualified healthcare professional. Research prototype not replacement for professional medical evaluation, avoid definitive diagnosis medication prescriptions treatment as orders unsupported claims fabricated stats encourage professional consultation.

## Demo Mode

Strong workflow DEMO PATIENT→Simulated sensor→Signal→AI→Fingerprint→Ultrasound→Screening→Doctor dashboard→Report labeled DEMO/SIMULATED.

Science-fair 17 steps integrated ecosystem not unrelated apps: demo/full_showcase.py

DEMO DATA clearly labeled, separate from private records, never present simulated as clinical evidence.
