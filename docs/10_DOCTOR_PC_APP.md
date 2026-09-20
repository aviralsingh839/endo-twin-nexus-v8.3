# 10 - Doctor PC App - V8.3+

## Overview
Doctor PC = full workstation, preserves src/ui/main_window.py, enhanced with modular architecture.

## Technology
- PySide6, PyQtGraph (preserve V8.3)
- LocalDatabase
- No cloud upload default
- Offline-first core

## Sections

### Dashboard
- Patient overview: total patients, recent assessments
- Recent assessments: last sessions
- Data quality: good/moderate/poor summary
- Pending reviews: sessions needing review
- Longitudinal views: trends

### Patient Management
- Create: create_patient anonymous_id age BMI
- Search: search_patients query
- Open: get_patient, patient history
- Archive: mark archived
- Patient history: sessions, symptoms, cycles, reports, notes
- Only authorized patients for doctor role

### Physiological Data
- Raw/filtered PPG: waveform, quality
- HR: time-series, mean
- HRV: RMSSD, SDNN, pNN50, quality
- GSR: tonic/phasic, quality
- Motion: activity, quality
- Temp: skin temp, room temp, slope, quality
- Quality: overall, per channel
- Artifacts: detected, details motion artifact at 12:03 baseline drift at 12:05
- Visualization: time-series pyqtgraph

### Advanced Analysis
- Circadian: pattern moderate disruption, category experimental_research, explainability HR/HRV circadian variation
- Autonomic: signal moderate dysregulation, category derived_feature, explainability RMSSD parasympathetic
- Metabolic: signal experimental, category experimental_research, limitations not clinical metabolic measurement
- Fingerprint: chrono-metabolic fingerprint components with provenance
- Multimodal: fusion output research risk signal confidence quality
- AI/ML outputs: PCOSModule v8.3.0 pcos_associated_risk low confidence 0.75 quality 0.85 clinical validation NOT ESTABLISHED
- Distinguish established/derived/experimental/ML/clinical, explainability

### Ultrasound
- All V8.3 capabilities: loading, preprocessing, quality checks, segmentation, inference, visualization, confidence, training, evaluation, storage
- Do not invent accuracy, state if insufficient, never fabricate percentages
- Quality gate UNKNOWN by design, provenance CLINICALLY-ENTERED vs IMAGE-DERIVED, fusion weight 0.20

### Longitudinal
- Comparison: compare sessions, trends HR, HRV, activity, temp, baseline deviation

### Doctor Notes
- Notes input/view: add_doctor_note, get_doctor_notes, patient_id, doctor_id, note_text, timestamp
- Follow-up information

### Reports
- Professional reports with "Research / risk-screening output — not a medical diagnosis."
- Model transparency: name/version/input/data quality/confidence/features/limitations, never hide uncertainty/manufacture confidence/training results
- Generated via ReportGenerator

## Role System
- DOCTOR: authorized patients only, review, analysis, notes, reports
- ADMIN: prototype manage provider directory, system config, demo data, verification

## Security
Local auth, role separation, encrypted storage prototype Fernet, controlled export, audit logging, minimal collection, no cloud upload, doctor only authorized patients.

## Why PySide6?
Preserve V8.3 src/ui/main_window.py, free/open-source, ordinary hardware performance, Do NOT introduce Dash/Plotly/Flask/Electron/browser dashboard unless architectural reason not replacing existing.
