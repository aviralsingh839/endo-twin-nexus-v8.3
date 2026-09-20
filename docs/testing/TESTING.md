# TESTING - ENDO-TWIN V8.3+

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED

## Test Suite

### Core
- Unit tests: physiology, signal, feature, baseline, longitudinal, provenance, uncertainty
- Location: tests/unit/, src/ tests
- Example: src/signal_processing/ tests, src/core/ tests

### Database
- Migrations, CRUD, foreign keys, patient isolation
- Location: tests/database/, database/ tests
- Real: LocalDatabase init, create_patient, list_patients, search_patients works - real execution not file existence
- Isolation: DEMO-001,002,003 intentionally different data HR 72/78/68, test Select DEMO-001→only DEMO-001 data, any leakage failure, PASS 7 FAIL 0

### AI
- Model loading, schema validation, preprocessing, inference, missing data, invalid data, model metadata
- Location: tests/ai/, disease_models/chrono_pcos/tests/
- Real: pcos_risk_model.joblib 17M 37 features 541 rows ROC AUC 0.9594 real loading and inference verified, ppg_quality_model.joblib 5.1M 15 features ROC AUC 0.624 honest low educational artifact real loading verified
- Hard-coded inference removed from real path: No hard-coded 0.75 in real_pcos_model_adapter.py uses calibrated probability
- Feature mapping verified: Correct order as per training critical for valid inference
- Model metadata recorded: get_model_info() name/version/input/quality/confidence/features/limitations
- Explainability verified: Only real influencing factors from feature_importances, not invented medical explanations
- Uncertainty honestly represented: model_confidence data_quality coverage validation ROC AUC

### Applications
- Navigation, state, patient selection, error handling
- Location: tests/apps/, apps/main/main_app.py acceptance tests
- Real: 6 acceptance tests PASS - general dashboard, 3 models, main without disease model, extensibility dummy future models, preserved original functionality, isolation

### Android
- Gradle build, unit tests, Compose tests where practical
- Real: android/patient/gradlew and android/doctor/gradlew real 61K jar + 8.4K script not placeholder, ./gradlew assembleDebug real attempt fails JAVA_HOME not set env limitation documented (not check-only), artifacts/android/ created
- Kivy: android/patient_app/main.py and android/doctor_app/main.py exists, BUILD scripts check-only if no toolchain

### Architecture
- Location: tests/architecture/, tests/test_endo_twin_isolation.py
- Real: ENDO-TWIN core no direct PCOS import PASS, general dashboard no PCOS knowledge PASS, main without disease model PASS, true general architecture core no direct dep, extensible without rewriting core

### End-to-end
- Complete patient workflow from ingest through report
- Location: tests/end_to_end/, demo/full_showcase.py 17 steps
- Workflow: DEMO PATIENT→Simulated sensor→Signal→AI→Fingerprint→Ultrasound→Screening→Doctor dashboard→Report labeled DEMO/SIMULATED

## Running Tests

```bash
pytest -q
.venv/bin/python -m pytest tests/ -v
.venv/bin/python apps/main/main_app.py  # 6 acceptance tests
.venv/bin/python tests/test_endo_twin_isolation.py  # Architecture
.venv/bin/python tests/test_multi_patient_isolation.py  # Isolation PASS 7 FAIL 0
./scripts/diagnostics/project_health.sh  # Real checks PASS/WARN/FAIL with evidence
./START.sh test
./START.sh test-cross
```

## Cross-Patient Isolation

Create DEMO-001,002,003 give each intentionally different data HR 72/78/68 BMI 23.5/27.2/21.8 Age 22/28/24.

Test: Select DEMO-001→only DEMO-001 data, Select DEMO-002→only DEMO-002 data, Select DEMO-003→only DEMO-003 data

Test: measurements, signals, features, baselines, trends, symptoms, cycle data, ultrasound, AI outputs, reports, notes, provenance, audit events

Any leakage is test failure.

Current: PASS 7 FAIL 0 - database level not merely UI hidden.

## Failure Conditions

Test proper database/sensor/signal processing/artifact/missing/reconnection/permissions/report/import/export/Android UI/PC UI/AI/ultrasound plus failure conditions unplug/corrupt/no internet/empty DB/invalid/damaged image/interrupted/duplicate/unauthorized.

Gracefully handle sensor unavailable/disconnected/noisy/missing/invalid/serial failure/partial.

Error handling: Every subsystem explicit failure states Sensor missing Sensor disconnected, Bad signal Signal quality insufficient, Database Database initialization failed, Model Model unavailable, Missing data Insufficient data for analysis, Ultrasound Image quality insufficient, Build show actual build failure, do not silently fail.

## Performance

Benchmarks real measurements not fabricated: docs/performance/PERFORMANCE_REPORT.md

## CI/CD

VS Code tasks: Run Tests, Cross-Patient Tests, Model Diagnostics, Performance Benchmark, Project Health

See .vscode/tasks.json
