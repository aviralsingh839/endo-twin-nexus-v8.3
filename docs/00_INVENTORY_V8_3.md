# V8.3 Inventory - Audit

## Python Modules

### Core (src/core/)
- quality_control.py: SensorQualityControl, checks missing/impossible/flatline/noise/stale, overall_quality, has_critical_failure
- personal_baseline.py: MetricStats, PersonalBaseline, PersonalBaselineEngine (BaselineManager alias), capture_from_features, zscore, robust_zscore, deviation_percent, compare, compare_current_vs_baseline, update_observation EWMA, save/load
- longitudinal_engine.py: MetricLongitudinal, LongitudinalReport, LongitudinalEngine (ChangeDetector alias), rolling windows, persistence, trend, change-point, recovery, missing handling, confidence
- shared_features.py: SharedPhysiologicalFeatures, SharedFeatureExtractor, trends, day/night ratio, recovery score
- feature_extraction.py: RealtimeFeatureExtractor, profile, baseline_engine, quality_control, signal processors, feature_history, sleep estimate, stress estimate, FSR correction, shared features

### Disease Modules (src/disease_modules/)
- base.py: DiseaseModule abstract base, name, version, required_features, optional_features, predict, explain, confidence, limitations
- pcos.py: PCOSModule, domain weights, cycle_score, domain_scores, risk_from_scores, provenance breakdown
- sleep.py: SleepModule, duration, regularity, circadian, recovery assessments
- cardiometabolic.py: CardiometabolicModule, RHR, HRV, activity, metabolic clinical, baseline deviations
- autonomic.py: AutonomicModule, HRV, GSR, stress, acute vs persistent separation
- registry.py: ModuleInfo, DiseaseModuleRegistry, GLOBAL_REGISTRY, enabled modules, future modules

### Fusion (src/fusion/)
- multimodal_fusion.py: FusionFeature, FusionContext, FusionResult, FusionEngine, provenance labels, group weights, overall_quality, coverage, provenance_summary, build, fuse

### Explainability (src/explainability/)
- explanation_engine.py: ExplanationEngine, explain_longitudinal, explain_module, explain_fusion, explain_shared_features, generate_report_explanation

### Signal Processing (src/signal_processing/)
- ppg.py: PPGProcessor, DCBlocker, ExponentialSmoother, peak detection, HRV time domain, SpO2 (unavailable with analog pulse sensor), waveform
- imu.py: IMUProcessor, motion_index, activity_level, low_activity_risk
- gsr.py: GSRProcessor, tonic, phasic
- temperature.py: TemperatureProcessor, skin_temp, slope
- ecg.py: ECGProcessor, HR, RMSSD, quality
- filters.py: DCBlocker, ExponentialSmoother
- hrv.py: hrv_time_domain
- SpO2.py: estimate_SpO2

### Serial IO (src/serial_io/)
- packet_parser.py: PacketParser, XOR CRC, $CP and $CP2 support, decode_status_flags
- arduino_reader.py: ArduinoReader thread, USB serial
- network_reader.py: NetworkReader, ESP8266 TCP bridge
- led_controller.py: LEDController

### Utils (src/utils/)
- synthetic.py: SyntheticSubjectProfile, generate_subject_timeline (6 scenarios), generate_synthetic_cohort, generate_scenario_dataset, generate_week legacy
- history_store.py: HistoryStore, SQLite, sessions, features, clinical, ultrasound, care plan, reports
- demo_stream.py: DemoSensorStream
- quality.py: ppg_quality, completeness_score, ppg_window_features, heuristic + trained model blended
- math_utils.py: sigmoid, clamp, safe_mean, safe_std, zscore, rescale_0_100
- replay.py: FeatureReplay
- report.py: report generation
- qr_encoder.py: dependency-free QR encoder
- logger.py, storage.py

### UI (src/ui/)
- main_window.py: MainWindow, 10 tabs Overview, Baseline, Trends, Health Signals, Data Quality, Clinical Inputs, Ultrasound, Explanation, Report, Validation, header with port, demo, scenario loading, timers for features and risk
- theme.py: DARK_QSS, colors
- gauges.py: GaugeWidget
- vital_cards.py: VitalCard
- live_plots.py: TimeSeriesPlot

### Config & Data Models
- config.py: APP_VERSION 8.3.0, APP_NAME CHRONO-TWIN NEXUS, TAGLINE, PROJECT_ROOT, DATA_DIR, MODEL_DIR, SERIAL_BAUD, timeouts, baseline constants, sampling targets, HR limits, quality thresholds, risk thresholds, longitudinal windows, enabled/future modules, data labels, provenance labels, UserProfile
- data_models.py: SensorQuality, SensorSample, FeatureVector, SharedPhysiologicalFeatures, HormoneEstimate, RiskResult, DiseaseModuleResult, SleepMetrics, CircadianMetrics

### App Entry
- app.py: argparse --demo, --port, --net, --scenario, QApplication, MainWindow

## UI Components

- 10 tabs in MainWindow: Overview, Baseline, Trends, Health Signals (4 modules + future), Data Quality, Clinical Inputs, Ultrasound, Explanation, Report, Validation
- Header: port combo, refresh, connect wearable, demo mode, stop, WiFi bridge, load scenario
- Vital cards: HR, HRV, temp, activity, GSR, stress, sleep, quality, recovery
- Gauges: overall research signal, data quality
- Plots: HR trend, HRV trend
- Text areas: shared features, longitudinal, module results, quality, clinical, ultrasound, explanation, report, validation
- Spin boxes: age, BMI, BP, glucose, cycle day, length, irregular combo, cyst size

## ML/AI Models

- PCOS risk: transparent fallback equation with research priors, sigmoid, bootstrap CI, confidence breakdown
- Sleep: formula-based wearable sleep estimation (time prior 22-07 high, motion, HR, RMSSD, GSR, temp)
- Stress: formula-based (HR z, RMSSD z, motion z, temp drop z, phasic GSR, GSR z, motion gate)
- PPG quality: heuristic (amplitude, saturation, motion penalty) + trained model (wrist_ppg_during_exercise) blended 60/40, features list 15, target |PPG HR - ECG HR| <=5 bpm
- Legacy: pcos_risk_model.joblib (17MB) and ppg_quality_model.joblib (5MB) in chrono_pcos_project V8/models/, reference only

## Ultrasound Modules

- Pipeline: image loading, preprocessing, quality checks, segmentation/analysis where implemented, model inference, visualization, confidence, training pipeline, evaluation, result storage
- Quality gate first, structured features with provenance (UNKNOWN by design until validated labelled dataset)
- Provenance: source image → preprocessing → detected features → quality → uncertainty
- If cannot be reliably extracted: UNKNOWN, never invented
- Structured features: cyst_size_mm, volume_cc, morphology
- Source: CLINICALLY-ENTERED or IMAGE-DERIVED
- Fusion integration: ultrasound group, weight 0.20 if present
- UI: ultrasound tab with spinbox for cyst size, add clinically-entered

## Signal Processing Modules

- PPG, IMU, GSR, temperature, ECG, filters, HRV, SpO2 (unavailable with analog pulse sensor)
- Quality control per channel
- Feature extraction streaming
- Baseline calibration
- Demo mode and scenario loading

## Sensor Interfaces

- Arduino Nano/ESP32 wearable pod: Generic Analog Pulse Sensor PPG (single-channel analog waveform), MPU6050 IMU, DS18B20 temp, optional GSR, 20 Hz $CP2 packets, 115200 baud, XOR CRC, status bits
- Mega hub: pod sensors + ECG, mic, FSR, light, BME280, OLED, LEDs, buzzer, buttons, relay mode
- ESP8266 bridge: Wi-Fi relay TCP 7777
- Packet parser: $CP and $CP2, CRC verification, error handling
- Readers: ArduinoReader thread, NetworkReader thread, DemoSensorStream, FeatureReplay
- Reconnection policy: RECONNECT_RETRY_S 3.0, STALE_DATA_TIMEOUT_S 6.0

## Database/Storage Logic

- HistoryStore: SQLite, tables for sessions, features, clinical, ultrasound, care plan, reports, patient info
- Data organization: raw, processed, clinical, physiological, longitudinal, ultrasound, synthetic, public, baselines
- Labels: REAL, SYNTHETIC, SIMULATED, PUBLIC DATASET, USER-ENTERED
- Baselines: JSON files in data/baselines/, personal_baseline_v8_3.json, calibration_history_v8_3.json, gitignored
- Raw exports: CSV in data/raw/, gitignored
- Training audit: JSONL in data/training_audit.jsonl, gitignored
- Reports: text files, save dialog

## Reports

- Text report in UI with sections: subject ID anonymous, observation period, sensor data available, data quality, personal baseline, longitudinal changes, disease signals, contributing factors, ultrasound if available, clinical inputs, limitations, recommendation to discuss with clinician
- No medical diagnosis
- Save to file
- Future: PDF, HTML longitudinal report

## Training Scripts

- scripts/generate_synthetic_dataset.py: generates 6 scenarios and cohort
- scripts/dataset_links.py: prints links for optional datasets (WESAD, BIDSleep, MESA, MMASH, mcPHASES, NHANES)
- Legacy: train_pcos_risk_model.py, train_ppg_quality_model.py in chrono_pcos_project V8/scripts/

## Configuration Files

- src/config.py: version, paths, serial, baseline, sampling, HR limits, quality thresholds, risk thresholds, longitudinal windows, enabled/future modules, data labels, provenance, UserProfile
- requirements.txt: PySide6, pyqtgraph, numpy, pandas, scikit-learn, pyserial, joblib, pytest
- .gitignore: __pycache__, *.pyc, .venv, venv, data/*.db, data/raw/, data/baselines/, etc., models/*.joblib
- data/ai_config.example.json: template for optional assistant config
- data/README.md: data architecture
- models/README.md: model documentation

## Demo Mode

- DemoSensorStream: synthetic data, clearly labelled SIMULATED
- Scenario loading: 6 scenarios from data/synthetic/scenarios/, load via dialog or --scenario arg
- Synthetic cohort: 10 subjects in data/synthetic/cohort/
- Modes in UI: NO STREAM, LIVE SERIAL, LIVE NETWORK, DEMO SYNTHETIC, SCENARIO

## Documentation

- README.md: V8.3 main, tagline, what it is, architecture, disease modules, data architecture, hardware, sensor quality, ultrasound, UI, reports, model training, validation, data honesty, run instructions, documentation list, demonstration story, acceptance checklist, version history
- docs/HOW_IT_WORKS.md: complete journey SENSOR→SIGNAL→FEATURE→BASELINE→LONGITUDINAL→SHARED→DISEASE MODULE→FUSION→EXPLANATION→REPORT
- docs/SYSTEM_ARCHITECTURE.md: modular architecture diagram, core modules, disease modules, fusion, explainability, signal processing, serial IO, utils, UI, data, hardware, extensibility, config, entry point
- docs/MULTI_DISEASE_MODEL.md: philosophy, architecture, Disease Module API, implemented modules A-D details, future modules, why modular, confidence separation, testing isolation, provenance, limitations honesty
- docs/DATA_ARCHITECTURE.md: organization, labeling, public datasets, synthetic data improvements, scenarios, clinical/physiological/longitudinal/ultrasound/baselines/raw, data honesty, subject-level validation, reproducibility, training audit, model files, usage
- docs/LONGITUDINAL_ENGINE.md: philosophy, implements, metrics tracked, baseline reference, series extraction, persistence, quality gate, trend analysis, change-point detection, recovery detection, classification, finalize, example report, testing scenarios, why heart, backward compat
- docs/DISEASE_MODULES.md: Module A-D details, future modules, Module API, confidence separation, explainability mandatory
- docs/HARDWARE_BUILD_GUIDE.md: overview, BOM Nano pod and Mega hub and ESP8266 bridge, wiring Nano pod and Mega hub, firmware upload, libraries, packet protocol, power and safety, testing, software gracefully handles missing sensors, V8.3 preservation
- docs/WEARABLE_POD_BUILD.md: primary wearable Nano pod, components, wiring, firmware, commands, testing, V8.3 integration
- docs/MEGA_HUB_BUILD.md: expanded lab Mega hub, components, wiring, firmware, testing, architecture, when to use, preservation
- docs/ULTRASOUND_PIPELINE.md: overview, provenance, quality gate, structured features, provenance labels, current status V8.3, fusion integration, PCOS module integration, safety, testing, future work, data storage, UI
- docs/MODEL_VALIDATION.md: engineering vs clinical, engineering validation 12 tests, clinical validation NOT ESTABLISHED, model training documentation, avoid data leakage, validation tab, running tests, safety
- docs/DATASET_CARD.md: public datasets PCOS_data.csv, PCOS_infertility.csv, wrist_ppg, synthetic cohort and scenarios, demo stream, clinical, physiological, longitudinal, ultrasound, baselines, raw, data honesty, training audit, model files, reproducibility, limitations, usage
- docs/SAFETY_AND_LIMITATIONS.md: medical safety note, safety, limitations engineering/models/data/clinical validation, language rules, data honesty, confidence separation, report limitations, future modules, code quality, do not overbuild, final checklist, most important requirement
- docs/DEVELOPMENT_HISTORY.md: V8.1 legacy reference, V8.2 concepts, V8.3 current, file mapping V8.1→V8.3, branding, author
- docs/README.md: list of docs
- docs/legacy/: V8.1 docs preserved

## Tests

- tests/test_baseline.py: baseline accuracy, comparison, min obs
- tests/test_longitudinal.py: stable LOW CHANGE, gradual EARLY CHANGE, persistent MULTIMODAL, temporary TEMPORARY, recovery RECOVERY
- tests/test_sensor_quality.py: missing, impossible, flatline, overall quality, critical failure, noisy
- tests/test_disease_modules.py: module API, isolation, provenance, future not implemented, no diagnostic claims
- tests/test_fusion.py: provenance, combines modules, missing sensors no crash
- tests/test_hardware_failures.py: packet parser corrupted, disconnected sensors, noisy PPG, excessive motion, reconnection, missing not physiological
- tests/test_validation.py: subject-level validation, reproducibility, data honesty labels, no fake clinical, ultrasound provenance
- Legacy: chrono_pcos_project V8/tests/ 124 tests

## Dependencies

- Python
- PySide6 >=6.6
- pyqtgraph >=0.13
- numpy >=1.24
- pandas >=2.0
- scikit-learn >=1.3
- pyserial >=3.5
- joblib >=1.3
- pytest >=7.0
- Optional: scipy, wfdb

## Dependency Mapping

- app.py → MainWindow → RealtimeFeatureExtractor → signal_processing, quality_control, personal_baseline, shared_features → FeatureVector → disease_modules → fusion → explainability → reports
- MainWindow → ArduinoReader/NetworkReader/DemoSensorStream → packet_parser → SensorSample → RealtimeFeatureExtractor
- HistoryStore → SQLite → sessions, features, clinical, ultrasound
- Synthetic → FeatureVector → baseline → longitudinal → shared → disease modules
- UI theme, gauges, vital_cards, live_plots reused across tabs

## What Can Be Reused

- All core modules: quality_control, personal_baseline, longitudinal_engine, shared_features, feature_extraction
- All disease modules: base, pcos, sleep, cardiometabolic, autonomic, registry
- Fusion and explainability
- Signal processing: ppg, imu, gsr, temperature, ecg, filters, hrv, SpO2
- Serial IO: packet_parser, arduino_reader, network_reader, led_controller
- Utils: synthetic, history_store, demo_stream, quality, math_utils, replay, report, qr_encoder, logger, storage
- UI: theme, gauges, vital_cards, live_plots, main_window (as base for doctor PC app)
- Config and data_models
- Hardware firmware: Nano pod, Mega hub, ESP8266 bridge
- Data: public PCOS datasets, synthetic scenarios and cohort
- Tests: all V8.3 tests
- Documentation: all V8.3 docs

## What Needs Refactoring

- Database: need to extend HistoryStore for patients, profiles, symptoms, cycles, provider directory, audit records, role separation
- Desktop: need to split into patient management, doctor notes, advanced analysis, longitudinal comparison
- New modules: provider_network for care discovery, supply discovery
- Android: need to create patient and doctor apps (Kivy-based, offline-first, local SQLite, role separation)
- Website: need to create public website (static HTML/CSS/JS, responsive, serious design, no private records)
- Security: need local authentication, role separation, encrypted storage, audit logging, minimal data collection
- Reports: need professional research/clinical-review style reports
- Docs: need 25 docs for V8.3+

## What Must Remain Unchanged

- Core scientific modules: signal processing, baseline, longitudinal, shared features, disease modules API, fusion, explainability
- Hardware firmware: Nano pod and Mega hub packet protocol $CP2, CRC, status bits
- Data honesty: labels REAL, SYNTHETIC, PUBLIC, USER-ENTERED, no fake clinical data, no diagnostic claims
- Offline-first: SQLite local, no cloud upload of private health data
- Safety language: research/prototype risk-screening, not diagnosis, limitations, encourage professional consultation
- Demo mode: simulated data clearly labelled
- Existing V8.3 features: all major features preserved

## Conclusion

V8.3 is complete modular multimodal longitudinal health platform with 4 disease modules, personal baseline, longitudinal engine, shared representation, fusion, explainability, sensor quality, hardware handling, synthetic data with 6 scenarios, tests, documentation, hardware preserved.

Ready for expansion to V8.3+ ecosystem: patient Android, doctor Android, doctor PC, local database, care discovery, supply discovery, public website, while preserving all existing functionality.


## V8.8 Analog Pulse Sensor migration

The current wearable build can use the generic analog Pulse Sensor module shown in the project hardware reference image instead of the MAX3010x optical PPG. The module is a single-channel analog pulse waveform source: SIG connects to an ADC-capable GPIO, VCC to the sensor's supported supply, and GND to common ground. ENDO-TWIN keeps the existing $CP2 transport so the rest of the desktop/BLE pipeline remains compatible. The primary waveform is carried in the existing `ir` slot for transport compatibility and is explicitly marked as `ANALOG_PULSE`/status bit 12. The `red` field is `-1` because there is no optical red channel.

The processing layer continues to support heart-rate and pulse-timing/HRV-style analysis from the waveform, with motion-aware quality scoring. It must not estimate SpO2 from this single-channel analog sensor. This hardware is suitable for an educational research prototype, not for diagnosis or clinical measurement.
