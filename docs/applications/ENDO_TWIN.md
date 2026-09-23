# ENDO-TWIN DESKTOP - GENERAL PLATFORM

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED

## Purpose

General disease-neutral platform for physiological data acquisition, baseline modelling, longitudinal tracking, multimodal fusion, research risk signals.

Not PCOS-specific. Disease models are plugins.

## Architecture

- Core: src/endo_twin/ general
- Disease models: disease_models/chrono_pcos/ PCOS-specific
- App: apps/main/main_app.py + launcher/main.py Control Center
- Entry: START.sh option 1 Endo-Twin Dashboard, option 2 General Analysis Engine

## Navigation

- Overview: What is happening, what changed, data quality, measured vs derived vs model-inferred vs needs attention
- Measurements: HR, HRV, Temp, SpO2, Activity
- Signals: PPG raw filtered quality, ECG, IMU, Temp
- Personal Baseline: Rolling mean median MAD confidence drift missingness time-of-day
- Longitudinal Trends: Hourly daily weekly monthly cycle, 6 scenarios stable low change gradual early change persistent multimodal temporary event sensor failure low confidence recovery trend
- Sleep & Circadian: Sleep timing activity timing temperature rhythm regularity
- Activity: MPU6050 motion activity level
- Autonomic Patterns: HR HRV recovery stress-response
- Metabolic Context: Glucose where available activity sleep temp clinical observations
- AI & Models: Model registry name version input data quality confidence features limitations, real artifacts 17M+5.1M, deterministic 0.3ms real 993ms
- Disease Models → CHRONO-PCOS: Plugin, pcos_associated_risk low/moderate/high NOT diagnosis confidence data quality clinical validation NOT ESTABLISHED
- Reports: Research risk-screening not diagnosis
- Data & Provenance: MEASURED CLINICALLY_ENTERED DERIVED IMAGE-DERIVED MODEL-INFERRED DEMO SIMULATED UNKNOWN visible
- Settings

## Design System

- Scientific premium calm modern fast trustworthy
- Midnight ocean medical-tech scientific medical premium
- Inter font, typography spacing cards charts progressive disclosure responsive accessible
- Empty/loading/error states, accessibility-friendly, large readable, multilingual-ready
- Offline-first core offline demo local no cloud, demo labeled never clinical
- Error explicit, graceful handle sensor unavailable/disconnected/noisy/missing/invalid/serial failure/partial

## Tests

- TEST1 general dashboard no PCOS knowledge PASS
- TEST3 main without disease model dashboard works general sections PASS true general architecture
- TEST4 extensibility dummy future models Future Cardio/Sleep total 3 PASS can add without rewriting core
- TEST5 preserves original functionality signal pcos_associated_risk level low PASS migration preserved
- TEST6 isolation PASS 7 FAIL 0 no cross-contamination

## Performance

- Dashboard 22.2 ms fast, import 267.9 ms, DB 61.6 ms
- See docs/performance/PERFORMANCE_REPORT.md
