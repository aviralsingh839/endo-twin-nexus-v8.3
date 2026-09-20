# ENDO-TWIN V8.6 — Workstations, Modes & Connection

## Startup mode
Doctor Workstation and Patient Workstation use a startup-only mode chooser:
- **DEMO MODE** — synthetic stream; values are explicitly labelled DEMO_DATA.
- **LIVE SENSOR MODE** — Arduino USB serial; CRC-checked $CP/$CP2 packets are decoded and processed.

The selected mode is fixed for the run. There is no in-app Demo/Live toggle, which prevents accidental mixing of synthetic and live records.

## Live processing path
Arduino packet → CRC validation → decode → PPG filtering/peak detection → HR/HRV cleaning → quality-gated SpO2 estimate → IMU motion/activity → GSR tonic/phasic → temperature validity/trend → channel quality → visible quality gate → workstation.

The firmware can sample the MAX30102 internally at 100 Hz, while the PC receives approximately 20 packets/s from the canonical firmware. The workstation therefore uses 20 Hz for its desktop PPG/IMU packet processor.

## Doctor Workstation
`./START.sh doctor`

Modules:
**Command Center · Patient Registry · Live Signals · CHRONO-PCOS · Ultrasound · Reports · Mobile Link**

DEMO MODE includes named synthetic cases with condition/module, synthetic tier, research-risk value, data quality and example drivers. These are UI demonstration values, not diagnoses, patient severity assessments or validation results.

LIVE SENSOR MODE displays only local patient records and live processed observations. Disease-model outputs are not fabricated when clinical context is missing.

Doctor mobile bridge: **7777**.

## Patient Workstation
`./START.sh patient-pc`

Single-patient surface:
**Overview · My Health · Measurements · Timeline · Connect · Reports**

Patient bridge: **7778**.

## Mobile connection
Doctor → Mobile Link → copy endpoint + six-digit code.
Patient Android → Connect → enter endpoint/code → Pair → Send latest session.

The existing Android transport remains DEMO_DATA until a validated real-device ingestion path is implemented.

## Research boundary
Live processing is actual signal-processing code, but it is not clinical validation. Sensor placement, calibration, hardware differences, motion artifacts and independent reference comparison all affect measurement validity. CHRONO-PCOS remains a research model and must not be presented as a diagnosis.
