# APPLICATION ARCHITECTURE

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED

## Applications

- ENDO-TWIN Desktop: apps/main/main_app.py general dashboard, launcher/main.py Control Center
- Doctor Desktop: desktop/doctor_app/ + launcher/doctor_pc.py, multipatient workstation
- Patient Android: android/patient_app/ Kivy + android/patient/ Native Kotlin Compose
- Doctor Android: android/doctor_app/ Kivy + android/doctor/ Native Kotlin Compose
- Research Lab: apps/research_lab/ + science/
- Diagnostics: launcher/diagnostics.py + scripts/diagnostics/project_health.sh

## Navigation

General: Overview, Measurements, Signals, Personal Baseline, Longitudinal Trends, Sleep & Circadian, Activity, Autonomic Patterns, Metabolic Context, AI & Models, Disease Models → CHRONO-PCOS, Reports, Data & Provenance, Settings

Doctor: Patients, Overview, Measurements, Signals, Timeline, Baseline, Trends, AI/Models, Disease Models, Ultrasound, Reports, Notes, Provenance, Audit, selected patient always visible

Patient: Home, My Health, Measurements, Signals, Baseline, Trends, Timeline, Symptoms, Cycle, AI & Models, CHRONO-PCOS, Reports, Doctor Sharing, Data & Privacy, Settings, patient only own data

## Architecture Pattern

Python: PySide6, scientific core
Kotlin: Jetpack Compose, Material 3, Room, DataStore
Compose UI → ViewModel → Use Case → Repository → Data Source

Local-first, offline-first, no cloud.

See docs/benchmarks/REFERENCE_REPOSITORY_AUDIT.md for reference patterns from nowinandroid, heartwood, health-companion.
