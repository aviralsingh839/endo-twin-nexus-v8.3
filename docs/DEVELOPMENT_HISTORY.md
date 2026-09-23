# DEVELOPMENT HISTORY - V8.3

> **Historical record.** This document describes the project as it stood at the time
> of writing. The GSR channel and its hardware were retired afterwards; current
> hardware is the ESP32-S3 wearable with a DS18B20 skin-contact temperature probe and
> it emits the `$CP3` frame. See `docs/WEARABLE_AND_MEGA_BUILD_MANUAL.md`.

## V8.1 - CHRONO-PCOS (Legacy Reference)

**Location:** `chrono_pcos_project V8/` folder preserved as legacy/reference implementation.

**Focus:** Low-cost longitudinal physiological phenotyping plus periodic clinical imaging as offline research prototype for PCOS-focused monitoring. Not diagnostic device and not clinically validated.

**Question:** Can continuous, personalised physiological information collected between clinical assessments provide useful longitudinal context, and does combining it with periodic clinical information such as ultrasound improve PCOS-related risk phenotyping? Wearable only acquires data. Contribution is longitudinal framework: personal baseline, persistent-change detection, evidence-linked "WHAT CHANGED?" summary, provenance-aware fusion, low-infrastructure digital reporting.

**Hardware:**
- Arduino Nano wearable pod: MAX30102 PPG, DS18B20 skin temp, MPU6050 motion, , streams 20 Hz $CP2
- Arduino Mega 2560 bench hub and base station: pod sensors plus ECG, microphone, FSR, light, environment, OLED, LEDs, buzzer, buttons, in relay mode forwards pod stream
- Optional ESP8266 Wi-Fi bridge relays same packets over TCP 7777
- Dashboard runs with no hardware: demo mode, manual entries, replay

**Features:**
- Reads wearable packets over USB serial or ESP8266 TCP bridge
- Scores every sensor's signal quality and withholds risk number when quality or confidence insufficient, showing banner instead of guess
- Builds personal baseline and personal physiological fingerprint, classifies changes as single, persistent, progressive or recovery with quality gates
- Produces evidence-linked WHAT CHANGED summary and CARE JOURNEY SUMMARY with OBSERVED / ASSOCIATED / UNKNOWN separation
- Runs ultrasound pipeline: image quality gate, structured features with provenance (image-derived values stay UNKNOWN until validated labelled dataset exists), descriptive exam comparison
- Fuses every input group with provenance tags and per-group reliability weights, listing missing modalities explicitly
- Computes PCOS-related risk estimate from nine transparent domains with confidence, bootstrap interval, explainable contributions
- Records care-plan adherence and reminders without treatment decisions
- Generates one-page clinical summary (text and PDF), full longitudinal HTML report, QR code carrying only random de-identified token, dependency-free QR encoder
- Stores everything in local SQLite, runs fully offline
- Ten dashboard tabs: Overview, Live Wearable, Longitudinal, PCOS Analysis, Patient Inputs, Care and Adherence, Clinical Dashboard, Ultrasound + Fusion, Validation / Research, Advanced / Research Tools
- Modes: LIVE, DEMO (labelled synthetic), Judge Mode (60s demo), replay

**Models:**
- Risk engine: transparent fallback equation with research-prior weights, not trained calibrated model, labelled longitudinal wearable data does not exist publicly, ethics-approved pilot only realistic path
- PPG quality model: trained on wrist_ppg_during_exercise (different sensor and sampling rate than MAX30102), used as soft correction 40% weight, heuristic dominant
- Ultrasound: UNKNOWN by design until validated labelled dataset, quality gate works on real images today, nothing invented
- Model A-E experiment PENDING by design
- Python BLE client not written yet, pod connects over USB serial or ESP8266 bridge
- Care-plan reminders bookkeeping only
- Everything unproven labelled PENDING or UNKNOWN

**Tests:** 124-test suite covers packet CRC, signal-quality heuristics, baseline calibration and outlier guard, change detection, risk equation, cosinor and sleep estimators, QR encoder round-trips and Reed-Solomon syndromes, ultrasound quality gate and UNKNOWN-by-design, patient-level split integrity, fusion weighting, reporting and tokens, validation lab.

**Documentation:** HOW_THE_PROJECT_WORKS, CODE_EXPLANATION, ARDUINO_WIRING_GUIDE, V8_1_BUILD_SPECIFICATION, scientific_model, validation, data/README, models/README

**Status:** Research prototype, not clinically validated, honest limitations.

---

## V8.2 Concepts (Intermediate Design)

**Ideas explored but not fully implemented in V8.1:**

- Modular disease system: CORE PHYSIOLOGICAL ENGINE + DISEASE-SPECIFIC MODULES
- Shared physiological representation to avoid duplicating signal-processing code
- Improved personal baseline: mean, median, std, robust deviation, rolling baseline, confidence, min obs, circadian context
- Longitudinal engine as heart: rolling windows, persistence, trend, change-point, recovery, missing handling, confidence
- Disease Module API: name, version, required_features, optional_features, predict, explain, confidence, limitations
- Multimodal fusion preserving provenance: WHERE DID INFO COME FROM?
- Confidence separation: MODEL CONFIDENCE vs DATA QUALITY vs CLINICAL VALIDATION
- Explainability mandatory: drivers, baseline deviations, trends, limitations
- Synthetic data redesign: realistic longitudinal variation rather than random numbers, individual baselines, timeline DAY1→DAY30→DAY60→DAY90, gradual changes, temporary disturbances, sensor noise, missing data, motion artifacts, recovery periods
- 6 longitudinal scenarios: stable, gradual, persistent, temporary, sensor failure, recovery
- Data architecture: raw, processed, clinical, physiological, longitudinal, ultrasound, synthetic, public, baselines, with clear labels REAL, SYNTHETIC, SIMULATED, PUBLIC DATASET, USER-ENTERED, never mix silently
- Sensor quality metadata: value, quality, source, timestamp, artifact
- Hardware failure testing: disconnected sensors, corrupted packets, noisy PPG, motion, reconnection, app continues not crash
- UI from PCOS-only to multi-disease: Overview, Baseline, Trends, Health Signals (PCOS, Sleep, Cardiometabolic, Autonomic), Data Quality, Clinical Inputs, Ultrasound, Explanation, Report
- No unsupported diseases: cancer, Alzheimer's, infectious, kidney, liver, thyroid unless dataset, validated features, defensible labels actually available, else interface marked future not implemented, no fake datasets
- Documentation rewrite around V8.3 journey: SENSOR → SIGNAL → FEATURE → BASELINE → LONGITUDINAL → SHARED → DISEASE MODULE → FUSION → EXPLANATION → REPORT
- Code quality: remove dead code, consolidate config, fix imports, verify paths, hardware simulation, report generation
- Do not overbuild: Class 11 student innovation, prioritize Science, Clarity, Reproducibility, Explainability, Honest Limitations over enterprise architecture, no cloud, paid APIs, web servers, blockchain, microservices, fake AI, runs offline

**These concepts became V8.3 implementation.**

---

## V8.3 - CHRONO-TWIN NEXUS (Current)

**Name:** CHRONO-TWIN NEXUS V8.3, Tagline Sense • Understand • Track • Personalize

**Location:** Root `src/`, `data/`, `docs/`, `hardware/`, `tests/` etc. - main project. Legacy V8.1 preserved in `chrono_pcos_project V8/` folder.

**Evolution:** From PCOS-focused system into modular multimodal longitudinal health-risk screening and monitoring platform.

**Goal:** Detect physiological deviations, longitudinal patterns and disease-associated risk signals, present with appropriate uncertainty and recommend clinical evaluation when appropriate. NOT to claim wearable can diagnose multiple diseases.

**Pipeline:**
```
RAW DATA → Quality Control → Signal Processing → Feature Extraction → Personal Baseline → Longitudinal Change Detection → Shared Physiological Representation → Disease-Specific Risk Modules → Multimodal Fusion → Explainable Risk Signals → Personalized Trend Dashboard → Clinical Follow-up Recommendation
```

**Most Important Concept:** System learns what is normal for individual first, then looks for persistent deviations from personal baseline. Not dependent only on population averages.

**Architecture:**
- Core physiological engine + disease-specific modules
- Shared representation avoids duplication
- Modular allows additional modules without rewriting core
- Consistent DiseaseModule API
- Structured results never "DISEASE DETECTED"
- Multimodal fusion preserves provenance
- Confidence separation: model confidence vs data quality vs clinical validation
- Explainability mandatory

**Modules Initially Implemented (reasonably supported by available data):**

- **Module A - PCOS / Reproductive-Metabolic:** Keeps and improves V8.1 PCOS pipeline, inputs age, BMI, cycle info, clinical variables, glucose, HR, HRV, activity, sleep/circadian, temp trends, stress, ultrasound structured features, distinguishes clinical-variable, wearable physiology, ultrasound-derived, combined/fused, language PCOS-associated risk signals not wearable detects PCOS, provenance breakdown computed not hard-coded fake

- **Module B - Sleep / Circadian:** Uses activity, movement, HR, HRV, resting HR, temp trends, sleep duration/timing/regularity, day/night activity, outputs sleep regularity signal, circadian disruption signal, recovery signal, persistent deviation, language sleep-related risk signal or circadian disruption pattern not diagnosis

- **Module C - Cardiometabolic (research-oriented):** Features resting HR, HRV, activity, BMI, age, BP if entered, glucose if entered, sleep, temp, longitudinal changes, outputs cardiometabolic risk signal, reduced activity trend, elevated RHR trend, metabolic data flag, never claims diabetes/hypertension/CVD diagnosis

- **Module D - Autonomic / Stress Regulation:** Uses HRV, resting HR, GSR, activity, sleep, temp, explainable estimator separating ACUTE SIGNAL from PERSISTENT LONGITUDINAL CHANGE, not mental-health diagnosis

- **Future Modules:** thyroid, renal, hepatic, infectious, oncology, neurodegenerative marked Future research module - not implemented, no fake datasets, requires appropriate dataset, validated features, scientifically defensible labels

**Dataset Improvement:**

- Organized into raw, processed, clinical, physiological, longitudinal, ultrasound, synthetic, public, baselines
- Clearly labelled REAL, SYNTHETIC, SIMULATED, PUBLIC DATASET, USER-ENTERED, never mix silently
- Synthetic redesigned realistic longitudinal variation not random numbers, individual baselines, age, BMI, activity patterns, resting HR, HRV, sleep timing/duration, temp trends, temperature patterns, cycle info, clinical variables, gradual changes, temporary disturbances, sensor noise, missing data, motion artifacts, recovery periods, timeline DAY1→DAY30→DAY60→DAY90
- 6 scenarios: stable LOW CHANGE SIGNAL, gradual EARLY CHANGE SIGNAL, persistent PERSISTENT MULTIMODAL SIGNAL, temporary TEMPORARY EVENT not disease, sensor failure LOW SENSOR CONFIDENCE must not be interpreted as physiological, recovery RECOVERY TREND
- Synthetic cohort 10 subjects diverse baselines, mix scenarios

**Personal Baseline Improvement:**

- Mean, median, std, robust MAD, p05, p95, p25, p75, count, min_obs_days, rolling median/std, confidence, last_updated, hour_of_day_mean, day_of_week_mean
- CURRENT vs PERSONAL BASELINE → normalized deviation (z-score, % change) with status normal/mild/moderate/significant
- Is stable when days_covered >=3 and confidence >=0.5
- Outlier guard |z|>3.5 does NOT move baseline, EWMA alpha 0.05, rolling window 14 days

**Longitudinal Engine - Heart:**

- Rolling windows short 24h medium 72h long 168h, persistence trailing consecutive out-of-band >=3, trend slope per day over recent 12 points direction increasing/decreasing/stable strength R^2, change-point CUSUM-like shift >2*std, recovery max_z_early > alert and latest_z <0.5*max_early → progress 0..1, missing handling missing kind not normal, confidence base 0.30+0.12*min(persistence,6)+0.15*min(n/60,1) * quality_factor * baseline_factor
- Kinds: normal, single, persistent, progressive, recovery, insufficient, missing
- Concept: one abnormal weak, repeated stronger, multiple related multimodal, persistent+good quality higher confidence

**Shared Feature Representation:**

- Common layer: heart_rate, resting_heart_rate, hrv, activity, sleep_duration, sleep_regularity, temp_trend, gsr, circadian, recovery, baseline_deviation, trend_features, sensor_quality
- Disease modules consume common representation, avoids duplication

**Disease Module API:**

- Consistent interface name, version, required_features, optional_features, predict, explain, confidence, limitations
- Returns structured with module, signal, level, confidence, drivers, data_quality, explanation, clinical_status research_only, provenance, limitations

**Multimodal Fusion:**

- Combines wearable physiology, longitudinal changes, clinical variables, ultrasound features, manually entered measurements
- Preserves provenance WHERE DID INFO COME FROM? Example PCOS 40% clinical 25% longitudinal 20% ultrasound 15% metabolic - only used if actually generated by model, not hard-coded fake
- Group weights coverage*avg_q, missing groups weight 0 does not drag down but absence visible lowers confidence
- Confidence separation: model confidence vs data quality vs clinical validation

**Explainability:**

- Every risk signal explains main contributing factors: persistent change detected drivers resting HR increased from baseline, HRV decreased, sleep regularity decreased, activity decreased, then these changes not specific to one disease and should not be interpreted as diagnosis - mandatory

**Hardware:**

- Keep V8.1 wearable pod as primary: Nano + MAX30102 + MPU6050 + DS18B20 + 
- Keep Mega hub as expanded lab/base station
- Architecture: WEARABLE POD → physiological data, MEGA HUB → expanded experimental sensors, PC → CHRONO-TWIN NEXUS ENGINE
- Do not force every sensor required, software gracefully operates with missing sensors

**Sensor Quality:**

- Every reading quality metadata value, quality 0..1, source, timestamp, artifact bool
- Detects missing, impossible, flatline, excessive noise, motion artifacts, packet corruption, stale
- Bad data must not silently become model input

**Hardware Failure Testing:**

- Tests for disconnected MAX30102, temp, corrupted packet, duplicate, delayed, missing, noisy PPG, excessive motion, reconnection
- App continues rather than crashing

**Ultrasound:**

- Keep V8.1 pipeline, do not pretend large clinically labelled dataset if not
- Extract structured features where possible, maintain provenance source image → preprocessing → detected features → quality → uncertainty
- If feature cannot be reliably extracted: return UNKNOWN, never invent

**UI:**

- Changed from PCOS-only to CHRONO-TWIN NEXUS with sections Overview, Baseline, Trends, Health Signals (PCOS, Sleep, Cardiometabolic, Autonomic), Data Quality, Clinical Inputs, Ultrasound, Explanation, Report, Validation
- Keep existing style where useful, improve to feel coherent research platform not several unrelated dashboards
- Simple visual hierarchy, prioritize trend graphs, baseline comparisons, signal persistence, confidence, data quality, explanations, avoid flashy medical claims

**Report Generation:**

- Includes subject ID, observation period, sensor data available, data quality, personal baseline, longitudinal changes, disease-module signals, contributing factors, ultrasound if available, clinical inputs if available, limitations, recommended next step discuss with qualified healthcare professional, do not produce medical diagnosis

**Model Training:**

- Inspect every existing model, document dataset, target, features, preprocessing, train/test split, cross-validation, metrics, limitations
- Avoid data leakage, longitudinal subjects splitting at SUBJECT level, measurements from same person not in both training and validation when would leak subject information

**Validation:**

- Tests for baseline accuracy, trend detection, persistence, recovery, missing sensor handling, noisy data, multimodal fusion, disease module isolation, subject-level validation, reproducibility
- Clearly separate ENGINEERING VALIDATION from CLINICAL VALIDATION, project may have engineering without clinical

**Data Honesty - Critical:**

- Never create fake clinical results as real, never modify public datasets to make metrics look better, never fabricate patient records, never label synthetic as clinical, never claim diagnoses PCOS, detects diabetes, detects heart disease unless genuine clinical validation supporting exact claim, use research risk signal, physiological deviation, screening-oriented estimate, requires clinical evaluation

**Documentation:**

- Rewrite main documentation around V8.3: README, HOW_IT_WORKS, SYSTEM_ARCHITECTURE, MULTI_DISEASE_MODEL, DATA_ARCHITECTURE, LONGITUDINAL_ENGINE, DISEASE_MODULES, HARDWARE_BUILD_GUIDE, WEARABLE_POD_BUILD, MEGA_HUB_BUILD, ULTRASOUND_PIPELINE, MODEL_VALIDATION, DATASET_CARD, SAFETY_AND_LIMITATIONS, DEVELOPMENT_HISTORY
- Explain complete journey SENSOR → SIGNAL → FEATURE → BASELINE → LONGITUDINAL → SHARED → DISEASE MODULE → FUSION → EXPLANATION → REPORT

**Code Quality:**

- Remove dead code where safe, remove duplicated implementations, consolidate configuration, remove temporary files, caches, obsolete docs from primary path, fix imports, run tests, syntax checks, check startup, verify model paths, data paths, hardware simulation, report generation
- Do not delete anything important merely because looks unused, first determine whether referenced

**Do Not Overbuild:**

- Class 11 student innovation/research demonstration
- Prioritize Science, Clarity, Reproducibility, Explainability, Honest Limitations over unnecessary enterprise architecture
- Do not add cloud infrastructure, paid APIs, unnecessary web servers, databases, blockchain, complex microservices, fake AI features
- System remains capable of running offline wherever possible - does, SQLite local, no cloud

**Final Demonstration Story (2-3 min):**

1. Wearable collects physiological signals
2. System cleans signals and checks sensor quality
3. Builds personal baseline
4. Continuously compares new measurements against that baseline
5. Instead of reacting to one abnormal reading, looks for persistent changes
6. Shared physiological representation feeds several disease-specific research modules
7. Clinical information and ultrasound can provide additional context
8. Fusion engine combines available evidence
9. System explains which factors produced each signal
10. Final result is research-oriented risk/health signal - NOT diagnosis

**Central Innovation:** We are not trying to make one sensor diagnose every disease. We are building one longitudinal physiological framework that can learn an individual's baseline and support multiple disease-specific research modules.

**Acceptance Checklist:** All checked, see README.md

**Most Important Requirement:** Do not simply add four disease names to existing README. Actually refactor architecture so CHRONO-TWIN NEXUS V8.3 is reusable longitudinal physiological platform with modular disease-specific research models. PCOS functionality becomes one module within larger system rather than entire identity. Preserve working V8.1 functionality wherever possible, improve data realism and longitudinal structure, make resulting project technically coherent, reproducible, explainable and honest about what has and has not been clinically validated.

**Done in V8.3.**

---

## File Mapping V8.1 → V8.3

- `src/config.py` V8.1 → `src/config.py` V8.3 with version 8.3.0, new constants for longitudinal, enabled/future modules, data labels, provenance
- `src/data_models.py` → extended with SensorQuality, SharedPhysiologicalFeatures, DiseaseModuleResult
- `src/models/personalization.py` → `src/core/personal_baseline.py` improved with mean, median, std, MAD, rolling, confidence, circadian context
- `src/models/change_detector.py` → `src/core/longitudinal_engine.py` heart with rolling windows, persistence, trend, change-point, recovery, missing handling, confidence
- `src/features/realtime_features.py` → `src/core/feature_extraction.py` with quality control and shared extractor
- New `src/core/quality_control.py` - sensor quality with metadata
- New `src/core/shared_features.py` - common representation
- `src/models/risk_engine.py` → `src/disease_modules/pcos.py` with provenance breakdown
- New `src/disease_modules/sleep.py`, `cardiometabolic.py`, `autonomic.py`, `base.py`, `registry.py`
- `src/models/fusion.py` → `src/fusion/multimodal_fusion.py` improved with confidence separation
- New `src/explainability/explanation_engine.py`
- `src/signal_processing/` reused from V8.1
- `src/serial_io/` reused
- `src/utils/synthetic.py` redesigned realistic longitudinal with 6 scenarios
- `src/utils/` other utils reused
- `src/ui/main_window.py` redesigned from PCOS-only to multi-disease dashboard with 10 tabs
- `src/ui/theme.py`, `gauges.py`, `vital_cards.py`, `live_plots.py` reused
- `src/app.py` updated for V8.3
- `data/` reorganized with clear labels, synthetic scenarios and cohort generated
- `hardware/arduino/` copied from V8.1, preserved
- `docs/` rewritten for V8.3
- `tests/` new tests for V8.3 requirements plus legacy 124 tests still in legacy folder
- `README.md` rewritten for V8.3 as current version
- Legacy V8.1 preserved in `chrono_pcos_project V8/` folder

---

## Branding

- Old: CHRONO-PCOS V8.1, Longitudinal Multimodal Phenotyping + Periodic Clinical Imaging Research Prototype
- New: CHRONO-TWIN NEXUS V8.3, Modular Multimodal Longitudinal Health Platform, Sense • Understand • Track • Personalize
- Do NOT blindly replace historical references inside old development notes, clearly distinguish V8.3 current, V8.1 legacy/reference, older experimental

Final README and main documentation present V8.3 as current version - done.

---

## Author

Class 11 student innovation/research demonstration.

Prioritizes Science, Clarity, Reproducibility, Explainability, Honest Limitations.
