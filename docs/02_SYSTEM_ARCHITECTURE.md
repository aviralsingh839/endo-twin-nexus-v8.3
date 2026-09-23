# 02 - System Architecture - V8.3+

## Overview
Preserves ALL V8.3 functionality, adds modular layers.

## Layers
1. Hardware: S3 wearable pod (MAX30102, MPU6050, DS18B20 skin temp), Mega hub (ECG, mic, FSR, BME280, OLED)
2. Serial: $CP3 packet CRC XOR 20Hz, PacketParser, SerialManager, reconnection
3. Signal Processing: Filtering, BaselineRemoval, ArtifactDetection, QualityControl
4. Feature Extraction: RealtimeFeatureExtractor HR, HRV RMSSD/SDNN/pNN50, , motion, temp
5. Baseline Calibration: Personal baseline, longitudinal
6. Disease Modules: PCOS, Sleep, Cardiometabolic, Autonomic - risk signals only
7. Fusion: MultimodalFusion
8. Chrono-Metabolic: circadian, autonomic, variability, activity, temp, metabolic, longitudinal - distinguishes established/derived/experimental/ML/clinical
9. Screening Results: research / risk-screening — not diagnosis
10. Reporting: professional reports with disclaimer
11. Local Data Layer: SQLite 18 tables, LocalDatabase, auth, CRUD, access control, export/import, backup, audit
12. Data/Sync Layer: Controlled export/import/backup/restore/encrypted package, deliberate sharing not automatic
13. Application Layer: Patient Android, Doctor Android, Doctor PC (preserves src/ui/main_window.py), Provider Network, Website

## Data Flow
Sensors → Serial → Signal Processing → Features → Baseline → Modules → Fusion → Fingerprint → Screening → Report → DB → Apps

## Preservation
- src/core/* preserved
- src/disease_modules/* preserved
- src/fusion/*, explainability/*, signal_processing/*, serial_io/*, utils/*, ui/main_window.py, config, data_models preserved

## New Modular Core
core/signal_processing wrappers src/signal_processing
core/sensors wrappers serial_io
core/features wrappers feature_extraction
core/analysis wrappers disease_modules, fusion, chrono-metabolic
core/ai wrappers training, evaluation
core/ultrasound preserves ultrasound pipeline
core/chrono_metabolic new fingerprint engine with provenance

## Offline-First
Core works without internet: patient records, sensor collection, signal processing, AI inference, ultrasound, reports, historical, local DB
Internet optional: provider directory, map tiles, updates, controlled sync

## Security
Local auth, role separation PATIENT/DOCTOR/ADMIN, encrypted storage prototype Fernet, controlled export, audit logging, minimal collection, no cloud upload, patient cannot access other patient, doctor only authorized.

## Performance
Ordinary hardware, avoid heavy cloud/APIs/proprietary/unnecessary frameworks. Prefer Python, PySide6, PyQtGraph, NumPy, Pandas, PySerial. Do NOT introduce Dash/Plotly/Flask/Electron unless architectural reason not replacing existing. Android Kivy offline SQLite APK via Buildozer.
