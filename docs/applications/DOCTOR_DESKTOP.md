# ENDO-TWIN V8.6 — Doctor Desktop

Launch:
```bash
./START.sh doctor
```

Startup mode is chosen before the workstation opens:
**DEMO MODE** or **LIVE SENSOR MODE**.

Doctor surface:
**Command Center · Patient Registry · Live Signals · CHRONO-PCOS · Ultrasound · Reports · Mobile Link**

DEMO MODE contains named synthetic review cases. The registry can filter by condition/module and sort by research priority, research risk or condition. Tier, risk and drivers are clearly labelled synthetic UI data.

LIVE SENSOR MODE uses CRC-checked Arduino packets and the existing PPG/HRV/IMU/temperature processing chain. Live patient records are not given fabricated disease risk.

Doctor mobile bridge: **7777**.


## Patient creation + Prototype Lab

The Doctor Workstation now supports **+ Add Patient** from the Patients screen. A local patient record can be created with an optional display name, anonymous ID, age and BMI. Missing fields remain absent/UNKNOWN; creating a patient does not automatically run a disease model.

The sidebar also includes **Prototype Lab**. In LIVE SENSOR MODE it observes the same CRC-checked Arduino stream used by the workstation and shows:
- packet count and observed packet rate;
- PPG/HR quality state;
- IMU motion/activity;
- DS18B20 temperature;
- skin-probe status (contact, status bit 3);
- AD8232 lead-off/raw state;
- FSR, microphone and environment channel status when present;
- firmware status flags;
- a 15-second engineering acceptance test;
- exportable test report.

A module marked PASS means the software received/processsed data during the engineering test. It does not establish sensor calibration, medical accuracy or clinical validity.
