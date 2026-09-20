# 11 - Doctor Android App - V8.3+

## Overview
Doctor Android = mobile companion, review and monitoring, not duplicate every PC feature.
PC = full workstation, Android = mobile review and monitoring interface.

## Technology
- Kivy, offline-first, local SQLite, authorized patients only
- APK via Buildozer

## Sections (Mobile Review)

### Patient List
- Patient list: only authorized patients for doctor
- Patient search: search authorized patients
- Open patient: basic info

### Patient Profiles
- Basic info: anonymous_id, age, BMI USER-ENTERED
- Questionnaire, cycle, symptoms - minimal data

### Recent Measurements
- HR: 72 bpm MEASURED quality 0.91
- HRV RMSSD: 48 ms MEASURED quality 0.85
- Skin Temp: 32.5°C MEASURED quality 0.88
- Activity: 35% MEASURED
- Sleep Regularity: 75% MODEL-INFERRED

### Trends
- Longitudinal changes: HR trend, HRV trend, activity trend

### Screening Results
- Research only: Research / risk-screening output — not a medical diagnosis
- Model name/version, input data, quality, confidence, features, limitations
- PCOS Module v8.3.0 pcos_associated_risk low confidence 0.75 data quality 0.85 clinical validation NOT ESTABLISHED
- Sleep Module, Cardiometabolic, Autonomic

### Ultrasound Results
- Image, quality, features, provenance CLINICALLY-ENTERED vs IMAGE-DERIVED
- No fabricated accuracy

### Reports
- Professional research/clinical-review style, not medical diagnosis
- View reports

### Notes
- Doctor notes, follow-up information
- Add note, view notes

## Why Not Duplicate PC?
Mobile limited screen, review not full analysis, offline-first, battery efficient.

## Security
Local auth DOCTOR role, only authorized patients, audit logging.

## Demo
Console demo if Kivy not available.
