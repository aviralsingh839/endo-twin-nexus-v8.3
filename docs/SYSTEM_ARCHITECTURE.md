# SYSTEM ARCHITECTURE - V8.3

## Overview

```
                SENSOR DATA (Nano Pod, Mega Hub, Demo, Scenario)
                     │
                     ▼
            QUALITY CONTROL (value, quality, source, timestamp, artifact)
                     │ Detects missing, impossible, flatline, noise, motion, corruption, stale
                     ▼
           SIGNAL PROCESSING (PPG, IMU, GSR, Temp, ECG)
                     │ Filtering, peak detection, HRV, motion index, etc.
                     ▼
         FEATURE EXTRACTION (FeatureVector, 0-100 normalized where appropriate)
                     │
                     ▼
          PERSONAL BASELINE (mean, median, std, MAD, p05/p95, rolling, confidence, circadian)
                     │ Learns what is normal for individual
                     ▼
         LONGITUDINAL ENGINE (rolling windows, persistence, trend, change-point, recovery)
                     │ Heart of V8.3 - distinguishes single vs persistent vs progressive vs recovery
                     ▼
      SHARED PHYSIOLOGICAL FEATURES (common representation, avoids duplication)
                     │
      ┌──────────────┼──────────────┐
      │              │              │
      ▼              ▼              ▼
   PCOS/S          SLEEP       CARDIOMETABOLIC
   MODULE          MODULE          MODULE
      │              │              │
      │         AUTONOMIC          │
      │         MODULE             │
      └──────────────┼──────────────┘
                     ▼
             MULTIMODAL FUSION (preserves provenance, group weights, coverage)
                     │
                     ▼
             EXPLANATION ENGINE (drivers, baseline deviations, trends, limitations)
                     │
                     ▼
          RISK SIGNALS + TRENDS (research-only, with uncertainty)
                     │
                     ▼
          DASHBOARD + REPORT (Overview, Baseline, Trends, Health Signals, Quality, Clinical, Ultrasound, Explanation, Report)
```

---

## Core Modules

### 1. Quality Control (`src/core/quality_control.py`)
- `SensorQualityControl` class
- Methods: `check_missing, check_impossible, check_flatline, check_noise, check_stale, evaluate, evaluate_sample, overall_quality, has_critical_failure`
- Thresholds: HR 35-210, skin temp 20-42°C, GSR 0-1023, IR 0-262143, motion 8g, stale 6s

### 2. Personal Baseline (`src/core/personal_baseline.py`)
- `MetricStats`: median, mean, std, mad, p05, p95, p25, p75, count, min_obs_days, rolling_median, rolling_std, confidence, hour_of_day_mean, day_of_week_mean
- `PersonalBaseline`: captured_at, duration_s, samples, days_covered, quality, confidence, stats, version
- `PersonalBaselineEngine`: capture_from_features, zscore, robust_zscore, deviation_percent, compare, compare_current_vs_baseline, update_observation (EWMA), save/load
- Backward compat alias: `BaselineManager`

### 3. Longitudinal Engine (`src/core/longitudinal_engine.py`)
- `MetricLongitudinal`: metric, kind, latest_value, baseline_median, z_latest, abs_change, pct_change, slope_per_day, persistence_points/hours, confidence, quality_ok, n_points, trend_direction/strength, is_recovering, recovery_progress, change_points
- `LongitudinalReport`: per_metric, overall_kind, summary, contributors, data_quality, n_windows, multimodal_signal, multimodal_metrics, persistence_score, recovery_detected, confidence_breakdown
- `LongitudinalEngine`: _series, _baseline_ref, _detect_change_points (CUSUM-like), _trend_analysis (slope + R^2), _recovery_detection, evaluate, _classify, _finalize
- Alias: `ChangeDetector`

### 4. Shared Features (`src/core/shared_features.py`)
- `SharedPhysiologicalFeatures`: heart_rate, resting_heart_rate, hrv_rmssd/sdnn, activity_level, motion_index, low_activity_risk, sleep_duration_h, sleep_regularity, sleep_timing_h, sleep_probability, circadian_stability/disruption, day_night_ratio, skin_temp_c, temperature_trend, temperature_rhythm_disruption, gsr_tonic, stress_index, autonomic_imbalance, recovery_score, baseline_deviations, trend_features, sensor_quality, overall_quality, provenance
- `SharedFeatureExtractor`: extract, _compute_trends (24h vs prev 24h), _day_night_ratio, _recovery_score

### 5. Feature Extraction (`src/core/feature_extraction.py`)
- `RealtimeFeatureExtractor`: profile, baseline_engine, quality_control, shared_extractor, signal processors (PPG, IMU, GSR, Temp, ECG), last_feature, feature_history, sleep_onset/wake, circadian_metrics, set_profile, set_sleep_window, capture_baseline, add_sample, compute, ppg_waveform, history_arrays

---

## Disease Modules (`src/disease_modules/`)

### Base (`base.py`)
- Abstract `DiseaseModule`: name, version, required_features, optional_features, predict, explain, confidence (coverage + quality), limitations, _level_from_score (low/moderate/elevated/high), _check_data_quality

### PCOS (`pcos.py`)
- Domain weights: CYCLE_W 1.20, METABOLIC_W 0.90, AUTONOMIC_W 0.60, SLEEP_W 0.50, CIRCADIAN_W 0.50, TEMPERATURE_W 0.35, GLUCOSE_W 0.35, ACTIVITY_W 0.30, BP_W 0.20, INTERCEPT -3.0
- Methods: _cycle_score (self-reported only), _domain_scores, _risk_from_scores (sigmoid)
- Provenance breakdown: clinical, wearable, longitudinal, ultrasound, metabolic

### Sleep (`sleep.py`)
- Assesses duration, regularity, circadian, recovery
- Signal map: sleep_regularity_deviation, circadian_disruption_pattern, sleep_duration_deviation, reduced_recovery_signal, persistent_*

### Cardiometabolic (`cardiometabolic.py`)
- Assesses resting HR, HRV, activity, clinical metabolic, baseline deviations
- Signals: reduced_activity_trend, elevated_resting_hr_trend, metabolic_data_flag, cardiometabolic_risk_signal

### Autonomic (`autonomic.py`)
- Assesses HRV, GSR, stress_index, acute vs persistent separation
- Signals: acute_autonomic_signal, persistent_autonomic_deviation, intermittent_stress_pattern, autonomic_regulation_signal

### Registry (`registry.py`)
- `ModuleInfo`: name, version, status, description, cls
- `DiseaseModuleRegistry`: register, get, get_module_class, create, list_implemented, list_future, list_all, summary
- Global `GLOBAL_REGISTRY`
- Enabled by default: pcos, sleep, cardiometabolic, autonomic
- Future: thyroid, renal, hepatic, infectious, oncology, neurodegenerative - marked not implemented

---

## Fusion (`src/fusion/multimodal_fusion.py`)

- `FusionFeature`: key, label, value, group, provenance, quality, source, unit
- `FusionContext`: built_at, features, by_group, get, present_groups, missing_groups, group_weights (coverage * avg quality), overall_quality, coverage, provenance_summary, summary_text
- `FusionResult`: timestamp, context, module_results, overall_signals, confidence_breakdown (model_confidence, data_quality, clinical_validation, fusion_coverage, fusion_quality), data_quality, clinical_validation, explanation, recommendations, as_dict
- `FusionEngine`: add_clinical, add_wearable, add_longitudinal, add_metabolic, add_ultrasound, build, fuse

**Provenance Labels:**
- MEASURED, PATIENT-REPORTED, CLINICALLY-ENTERED, IMAGE-DERIVED, MODEL-INFERRED, UNKNOWN

**Group Order:**
- clinical, wearable, longitudinal, metabolic, ecg, ultrasound, adherence

---

## Explainability (`src/explainability/explanation_engine.py`)

- `ExplanationEngine`: explain_longitudinal, explain_module, explain_fusion, explain_shared_features, generate_report_explanation

---

## Signal Processing (`src/signal_processing/`)

Reused from V8.1, improved:

- `ppg.py`: PPGProcessor with DC blocker, smoother, peak detection, HRV
- `imu.py`: IMUProcessor motion_index, activity_level
- `gsr.py`: GSRProcessor tonic, phasic
- `temperature.py`: TemperatureProcessor skin_temp, slope
- `ecg.py`: ECGProcessor HR, RMSSD, quality
- `filters.py`: DCBlocker, ExponentialSmoother
- `hrv.py`: hrv_time_domain
- `spo2.py`: estimate_spo2 (educational)

---

## Serial IO (`src/serial_io/`)

- `packet_parser.py`: PacketParser with XOR CRC, supports $CP and $CP2, decode_status_flags
- `arduino_reader.py`: ArduinoReader thread for USB serial
- `network_reader.py`: NetworkReader for ESP8266 TCP bridge
- `led_controller.py`: LED feedback

---

## Utils (`src/utils/`)

- `synthetic.py`: SyntheticSubjectProfile, generate_subject_timeline (6 scenarios), generate_synthetic_cohort, generate_scenario_dataset, generate_week (legacy compat)
- `history_store.py`: SQLite storage for sessions, features, clinical, ultrasound
- `demo_stream.py`: DemoSensorStream synthetic
- `quality.py`: ppg_quality, completeness_score
- `math_utils.py`: sigmoid, clamp, safe_mean, zscore, rescale_0_100
- `replay.py`: FeatureReplay
- `report.py`: report generation
- `qr_encoder.py`: dependency-free QR encoder

---

## UI (`src/ui/`)

- `main_window.py`: MainWindow with 10 tabs - Overview, Baseline, Trends, Health Signals (4 modules + future), Data Quality, Clinical Inputs, Ultrasound, Explanation, Report, Validation
- `theme.py`: DARK_QSS, colors
- `gauges.py`: GaugeWidget
- `vital_cards.py`: VitalCard
- `live_plots.py`: TimeSeriesPlot

Preserves V8.1 hardware: Nano pod and Mega hub.

---

## Data (`data/`)

Organized with clear labels: REAL, SYNTHETIC, PUBLIC DATASET, USER-ENTERED

- `raw/`: raw exports, gitignored
- `processed/`: processed features
- `clinical/`: clinical variables
- `physiological/`: wearable features
- `longitudinal/`: timelines
- `ultrasound/`: ultrasound
- `synthetic/`: synthetic cohort + 6 scenarios
- `public/`: PCOS_data.csv, PCOS_infertility.csv, wrist_ppg
- `baselines/`: personal baselines, gitignored

---

## Hardware (`hardware/arduino/`)

- `chrono_pcos_nano_pod`: wearable pod firmware
- `chrono_pcos_mega_firmware`: bench hub firmware
- `chrono_pcos_esp8266_bridge`: Wi-Fi bridge

---

## Extensibility

To add new disease module:

1. Create `src/disease_modules/new_module.py` inheriting `DiseaseModule`
2. Implement required properties and `predict()`
3. Register in `registry.py`
4. No core engine rewrite needed
5. UI automatically shows new module in Health Signals tab if implemented

Future modules must have:
- Appropriate dataset
- Validated features
- Scientifically defensible target labels
- Otherwise marked "Future research module - not implemented" and no fake data

---

## Configuration (`src/config.py`)

- APP_VERSION 8.3.0, APP_NAME CHRONO-TWIN NEXUS, TAGLINE Sense • Understand • Track • Personalize
- PROJECT_ROOT, DATA_DIR, MODEL_DIR, LOG_DIR
- SERIAL_BAUD 115200, timeouts, Wi-Fi port 7777
- Baseline: capture 300s, min 60 samples, min days 3, rolling 14 days, confidence min obs 30
- Sampling: PPG 50Hz, IMU 50Hz, GSR 10Hz, Temp 1Hz
- HR limits 35-210 bpm
- Quality thresholds
- Risk thresholds low 25, medium 50, high 75
- Longitudinal windows short 24h, medium 72h, long 168h
- Enabled modules, future modules
- Data labels, provenance labels
- UserProfile with clinical fields

---

## Entry Point (`src/app.py`)

- Argparse: --demo, --port, --net, --scenario
- QApplication, MainWindow, exec
