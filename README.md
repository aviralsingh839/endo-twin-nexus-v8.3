# ENDO-TWIN V8.6 — Current Operating Path

ENDO-TWIN is the personalized physiological modelling platform; CHRONO-PCOS is its first disease-specific research module.

## Start
```bash
./START.sh
```

## Workstations
```bash
./START.sh doctor
./START.sh patient-pc
```

Both workstations ask for **DEMO MODE** or **LIVE SENSOR MODE** before the main interface opens. The selected mode is fixed for that run.

## Live sensor path
LIVE SENSOR MODE accepts CRC-checked Arduino $CP/$CP2 packets and runs the existing PPG, HRV, IMU, GSR and temperature processing pipeline. Poor-quality pulse data can suppress HR/HRV, and SpO2 is withheld by a stricter quality gate.

## Doctor review
The Doctor Workstation includes:
**Command Center · Patient Registry · Live Signals · CHRONO-PCOS · Ultrasound · Reports · Mobile Link**

DEMO MODE contains named synthetic review cases with condition/module, synthetic tier, research-risk value, quality and driver text. These are demonstration values, not diagnoses, patient severity assessments or validation metrics.

## Android
```bash
./setup_android.sh
./build_apks.sh all
```

## Mobile connection
Doctor Workstation → Mobile Link → endpoint + 6-digit code.
Patient Android → Connect → Pair → Send latest session.

The current Android transport is deliberately DEMO_DATA. See the application and live-processing guides for the evidence and security boundaries.

---

# ENDO-TWIN — Personalized Physiological Modelling Platform
### **Sense • Model • Predict • Personalize • Connect**

> **One Sentence: ENDO-TWIN is the platform; CHRONO-PCOS is its first disease-specific model.**
> **Research Prototype — Not a Medical Device — Not Clinically Validated — Not a Diagnosis**

The historical architecture and preserved PCOS work remain documented below. The current V8.6 workstation experience adds a mode-safe live acquisition surface without turning research signals into clinical claims.
