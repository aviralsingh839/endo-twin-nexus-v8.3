# 15 - Public Website - V8.3+

## Overview
Public website structure Home tagline, What is, Problem, How it Works flow Sensors→Signal Processing→Feature Extraction→Multimodal AI→Chrono-Metabolic Fingerprinting→Risk Screening→Doctor Review, Technology Arduino/PPG/HR/HRV/GSR/motion/temp/ultrasound/AI/signal processing, Patient App, Doctor App, Care Discovery, Research hypothesis/methodology, Benefits without unsupported claims, Safety limitations, Privacy local-first, Documentation links to 25 docs.

## Structure
- Home: tagline Sense•Model•Predict•Personalize•Connect, subtitle research ecosystem, disclaimer Research Prototype Not Medical Diagnosis, CTA Learn More View Apps GitHub, architecture preview Sensors→...→Doctor Review
- What is: What it IS (research prototype, risk pre-screening, educational, local-first, patient+doctor+care+website) and What it IS NOT (not medical device, not diagnostic, not replacement, not claiming diagnose)
- Problem: PCOS/PCOD challenges, need for accessible research tools, not diagnosis
- How it Works: flow-diagram 9 steps icons Sensors Signal Processing Feature Extraction Personal Baseline Longitudinal Multimodal AI Chrono-Metabolic Fingerprinting Risk Screening Doctor Review
- Technology: 3 cards Arduino (Nano pod generic analog Pulse Sensor MPU6050 DS18B20 GSR 20Hz $CP2, Mega hub ECG mic FSR BME280 OLED), Signal Processing (filtering baseline artifact quality missing handling feature extraction baseline calibration), AI/ML (PCOSModule SleepModule CardiometabolicModule AutonomicModule fusion chrono-metabolic fingerprint model transparency no fake confidence)
- Patient App: dashboard/profile/measurements/symptoms/cycle/results/reports/sharing/find care Kivy offline SQLite APK Buildozer accessibility large readable multilingual-ready offline-first local-first
- Doctor App: Doctor PC (dashboard/patient management/physiological data/advanced analysis/ultrasound/longitudinal/notes/reports professional dense PySide6 PyQtGraph) Doctor Android mobile companion patient list/search/profiles/recent measurements/trends/screening results/ultrasound/reports/notes/follow-up not duplicate full PC
- Care Discovery: Nearby example provider cards demo View Directions Contact, verification status verified/pending/unverified/demo never falsely label, OSM directions no API key offline-first, provider directory separate from private records
- Supply Discovery: sensor accessories/monitoring equipment/menstrual-care/general supplies no prescription sales no auto medication no treatment decisions
- Research: hypothesis chrono-metabolic fingerprint may show research signals related to PCOS-associated patterns, methodology physiological sensing signal processing multimodal AI, benefits without unsupported claims educational research accessible local-first privacy
- Safety: warning box limitations list research/prototype not replacement avoid definitive diagnosis/medication prescriptions/treatment as orders/unsupported claims/fabricated stats encourage professional consultation Rotterdam required
- Privacy: local-first tables offline optional services role system PATIENT own data DOCTOR authorized ADMIN provider directory encrypted storage prototype audit logging minimal collection no cloud upload patient cannot access other patient
- Documentation: links to 25 docs 01_PROJECT_OVERVIEW to 25_RESEARCH_METHODOLOGY explain WHAT and WHY
- Footer: Class 11 Research Innovation Project, GitHub, disclaimer research prototype not medical device

## Design
Serious modern scientific avoid excessive animations/fake claims/stock AI doctor/exaggerated promises/100% accurate/fake hospital branding, use clean typography/scientific diagrams/clear sections/accessible colors/responsive/mobile/strong identity.

## Files
- website/index.html: full V8.3+ public site responsive meta nav logo CHRONO-PCOS V8.3+ hero tagline disclaimer CTA architecture preview sections footer
- website/style.css: serious modern scientific/health-technology CSS variables primary #0f172a secondary #1e293b accent #0ea5e9 text #0f172a bg #ffffff bg-alt #f8fafc border #e2e8f0, no excessive animations, clean typography, responsive, mobile support
- website/script.js: minimal JS smooth scrolling nav links, no fake medical claims, console logs research prototype not medical device

## Why?
Public info, no private records, scientific honest, educational, no fake hospital branding.
