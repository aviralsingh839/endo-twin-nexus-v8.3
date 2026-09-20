# 09 - Patient Android App - V8.3+

## Overview
Kivy-based, offline-first, local SQLite, accessibility-friendly, simplicity low complexity clear explanations large readable accessibility-friendly multilingual-ready offline-first.

## Technology
- Kivy (Python) -> APK via Buildozer
- Local SQLite via LocalDatabase
- No cloud upload default
- Works without internet

## Sections

### Dashboard
- Data collection status: ready/collecting/no data
- Sensor status: connected/disconnected/demo mode
- Recent measurements: HR, HRV, temp, activity
- Quality: Good/Moderate/Poor understandable language not raw technical unless advanced
- Cycle: current cycle info
- Previous screening sessions: list
- Notifications: simple

### Patient Profile
- Basic profile: age, BMI, anonymous_id - minimal data collection no unnecessary personal info
- Questionnaire: PCOS-related questionnaire USER-ENTERED label
- Cycle: usual length, irregularity USER-ENTERED
- Symptoms: minimal
- All USER-ENTERED label, not diagnosis

### Measurements
- Sensor connection: USB/BLE, connect button, status
- Guided measurement: step-by-step PPG, HR, HRV, GSR, motion, temp, quality
- PPG waveform visualization if available
- Gracefully handle sensor unavailable/disconnected/noisy/missing/invalid/serial failure/partial

### Symptoms
- Structured symptom logging: type, severity 0-10, notes
- Not diagnosis, logged timestamp USER-ENTERED

### Cycle Tracking
- Dates: start, end, length
- Length: days
- Irregularity: regular/irregular/unknown
- Symptoms: associated symptoms
- Notes: free text
- Do not interpret as diagnosis

### Results
- Understandable language: Data quality Good not raw technical unless advanced mode
- Screening result: research analysis complete discuss with clinician if symptomatic
- Disclaimer: This is a research / risk-screening output — not a medical diagnosis
- Model transparency: model name/version, input data, quality, confidence, features, limitations via advanced

### Reports
- View appropriate reports, professional but patient-friendly, disclaimer

### Doctor Sharing
- Controlled sharing/export of selected info, local-first default without cloud
- Deliberate sharing not automatic upload
- Export package encrypted if available, audit logged
- Patient-to-doctor deliberate controlled

### Find Care
- Nearby doctors, clinics, labs, supplies
- Map/list, distance, specialty, address, opening hours, services, contact, directions, verification status
- Provider directory separate from private records
- OSM directions https://www.openstreetmap.org/directions?from=&to= no API key offline-first
- Example Nearby ABC Women's Clinic 1.2km Gynecology Verified [View][Directions]
- Verification statuses verified/pending/unverified/demo never falsely label

### Supply Discovery
- Separate section sensor accessories/monitoring equipment/menstrual-care/general supplies
- No prescription-drug sales, no auto medication, no treatment decisions

## Accessibility
Large readable fonts, clear buttons, simple navigation tabs, multilingual-ready, offline-first.

## Security
Local auth role PATIENT, own data only, cannot access other patient, controlled export, audit logging.

## Demo Mode
Simulated sensor data labeled DEMO/SIMULATED, entire workflow without physical sensors, clearly labeled.

## Why Kivy?
Python codebase reuse, free/open-source, offline SQLite, APK via Buildozer, appropriate for Class 11 project.
