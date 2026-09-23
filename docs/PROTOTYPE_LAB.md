# ENDO-TWIN V8.6.1 — Prototype Lab

## Purpose

The Doctor Workstation Prototype Lab is the bench-validation surface for the ENDO-TWIN hardware prototype.

It answers:

"Is the sensor/module producing data that the software can receive and process?"

It does not answer:

"Is the sensor clinically accurate?"

Those are different validation questions.

## Patient creation

Doctor → Patients → **+ Add Patient**

Fields:
- display name / alias (optional);
- anonymous ID (optional; generated when blank);
- age (optional);
- BMI (optional).

The patient is stored in the local SQLite database. Missing clinical information remains absent/UNKNOWN. Creating a patient does not automatically run CHRONO-PCOS.

## Prototype Lab

Doctor → **Prototype Lab**

The lab observes the same LiveSession used by the workstation.

It exposes:
- current DEMO/LIVE session;
- serial port;
- valid packet count;
- observed packet rate;
- PPG state/quality;
- IMU state and motion;
- temperature validity (skin probe contact);
- ECG raw/lead-off state;
- FSR context;
- microphone state;
- environment state;
- firmware status flags.

## 15-second acceptance test

Select **LIVE SENSOR MODE** at workstation startup.

1. Power the Arduino and connect USB.
2. Confirm the expected serial port.
3. Verify that $CP/$CP3 packets are arriving.
4. Keep the board/IMU stable.
5. Keep a steady finger on MAX30102 during the test.
6. Start **Run 15 s Module Test**.
7. Inspect packet count, signal quality, module states and firmware flags.
8. Export the test report for the experiment log.

A module marked PASS means that the application received/processed data for that channel during the engineering test. It does not prove calibration, accuracy, reference-device agreement, or clinical validity.

## Failure behavior

A useful prototype failure is visible:

- CRC error → packet rejected.
- sensor absent → UNKNOWN/status flag.
- PPG quality poor → HR/HRV may be withheld.
- insufficient clean intervals → HRV UNKNOWN.
- stale stream → reconnect/stale state.
- unsupported anatomy → UNKNOWN.
- missing disease-specific clinical evidence → CHRONO-PCOS does not create a disease-specific result.

No default value should be injected simply to make the UI look complete.

## Suggested bench sequence

Test the modules in this order:

1. I2C bus
2. MAX30102
3. MPU6050
4. DS18B20 skin probe
5. OLED
7. LEDs/buzzer/buttons
8. BME280
9. BH1750
10. MAX4466
11. FSR
12. AD8232

Add one optional module at a time after the core build is stable.

## Model-development handoff

Prototype evidence should eventually be logged as:

raw measurement → quality → derived feature → personal baseline → longitudinal context → clinical/context input → disease-model gate → model result → uncertainty

Do not train a disease model directly from an uncontrolled collection of UI-ready values.

## Safety boundary

The Prototype Lab is an engineering/research instrument.
It is not a medical device and is not clinically validated.
