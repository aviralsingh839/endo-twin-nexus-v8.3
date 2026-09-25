# 01 - Project Overview - CHRONO-PCOS V8.3+

## What is CHRONO-PCOS?
Local-first multimodal AI-assisted PCOS/PCOD risk pre-screening research ecosystem combining physiological sensing, signal processing, multimodal analysis, AI/ML, ultrasound, longitudinal tracking, patient accessibility, doctor review, local storage, care discovery, educational resources.

Tagline: Sense • Model • Predict • Personalize • Connect

## What it IS
- Research prototype for physiological signal research
- Risk pre-screening tool (not diagnosis)
- Educational demonstration of chrono-metabolic fingerprinting
- Local-first, offline-capable ecosystem
- Patient + Doctor + Care Discovery + Public Website integrated

## What it IS NOT
- Not a medical device
- Not a diagnostic tool (Rotterdam criteria required, requires clinician)
- Not a replacement for professional medical evaluation
- Not claiming to diagnose PCOS, only research risk signals

## Architecture
Sensors (Generic Analog Pulse Sensor PPG (single-channel analog waveform), MPU6050 motion, DS18B20 temp, GSR) → Signal Processing → Feature Extraction → Baseline Calibration → Disease Modules (risk signals only) → Fusion → Chrono-Metabolic Fingerprint → Screening Results (not diagnosis) → Reporting → Local DB → Patient/Doctor Apps/Care Discovery/Website

## Components
- Patient Android App (Kivy, offline-first)
- Doctor Android App (mobile review)
- Doctor PC App (PySide6, preserves V8.3 src/ui/main_window.py)
- Local Database (SQLite 18 tables, no cloud upload)
- Analysis Engine (signal processing, AI/ML, ultrasound, chrono-metabolic)
- Care Discovery (FIND CARE map/list, providers, supplies, OSM directions)
- Public Website (serious modern scientific, no private records)
- Demo Mode (entire workflow without sensors, labeled DEMO/SIMULATED)

## Scientific Foundation
- PPG-derived HR/HRV (established/derived)
- GSR/EDA (established)
- Motion activity (established)
- Skin temp (established)
- Chrono-metabolic fingerprint (experimental research)
- ML predictions (risk signals, not diagnosis, confidence, limitations)

## Safety
Research/prototype, not replacement for professional consultation, avoid definitive diagnosis, prescriptions, treatment orders, unsupported claims, fabricated stats.

## Why?
Class 11 research innovation: physiological sensing, signal processing, AI/ML, local-first privacy, patient accessibility, doctor review, scientific honesty (limitations, provenance, explainability).

## Version History
V8.1 - Wrist PPG + disease modules
V8.3 - Ultrasound + improved architecture
V8.3+ - Full patient-doctor ecosystem, local DB, care discovery, website, Android apps

## Branding
Primary: CHRONO-PCOS V8.3+
Historical: CHRONO-TWIN NEXUS V8.3 (keep in old notes)


## V8.8 Analog Pulse Sensor migration

The current wearable build can use the generic analog Pulse Sensor module shown in the project hardware reference image instead of the MAX3010x optical PPG. The module is a single-channel analog pulse waveform source: SIG connects to an ADC-capable GPIO, VCC to the sensor's supported supply, and GND to common ground. ENDO-TWIN keeps the existing $CP2 transport so the rest of the desktop/BLE pipeline remains compatible. The primary waveform is carried in the existing `ir` slot for transport compatibility and is explicitly marked as `ANALOG_PULSE`/status bit 12. The `red` field is `-1` because there is no optical red channel.

The processing layer continues to support heart-rate and pulse-timing/HRV-style analysis from the waveform, with motion-aware quality scoring. It must not estimate SpO2 from this single-channel analog sensor. This hardware is suitable for an educational research prototype, not for diagnosis or clinical measurement.
