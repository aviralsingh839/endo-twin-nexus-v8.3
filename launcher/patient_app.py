#!/usr/bin/env python3
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
print("="*70)
print("CHRONO-PCOS Patient App - PC Demo")
print("Research / risk-screening output — not a medical diagnosis")
print("="*70)
try:
    import kivy
    print("Kivy available, launching Patient App GUI...")
    from android.patient_app.main import PatientApp
    PatientApp().run()
except Exception as e:
    print(f"Kivy not available or error: {e}")
    print("Running console demo of Patient App")
    print("="*60)
    print("CHRONO-PCOS Patient App V8.3+ - Console Demo")
    print("Dashboard: data collection status, sensor status, recent measurements, quality, cycle, previous sessions")
    print("Profile: basic info, questionnaire, cycle, symptoms - minimal data")
    print("Measurements: sensor connection, guided measurement, PPG, HR, HRV, GSR, motion, temp, quality")
    print("Symptoms: structured logging")
    print("Cycle Tracking: dates, length, irregularity, symptoms, notes - not diagnosis")
    print("Results: understandable language, Data quality: Good, not raw technical unless advanced")
    print("Reports: view appropriate reports")
    print("Doctor Sharing: controlled sharing/export, local-first")
    print("Find Care: nearby doctors/clinics/labs/supplies with map/list, distance, specialty, address, hours, contact, verification")
    print("="*60)
    print("This is a research / risk-screening output — not a medical diagnosis.")
    print("Local-first, offline, privacy-focused")
    try:
        input("Press Enter to exit...")
    except (EOFError, KeyboardInterrupt):
        print("\nExiting...")
