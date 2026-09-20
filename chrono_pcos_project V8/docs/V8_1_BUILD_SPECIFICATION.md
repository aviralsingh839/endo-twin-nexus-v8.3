# CHRONO-PCOS V8.1 Build Specification

Periodic clinical imaging plus continuous low-cost physiological monitoring,
personal baseline, longitudinal change detection, cycle and symptom context,
provenance-aware multimodal fusion, patient support, clinician-facing
longitudinal reporting and low-infrastructure deployment. Research prototype.
Not a diagnostic device. Not clinically validated. Every unproven component is
labelled PENDING or UNKNOWN in the code, the interface and this document.

## 1. Scope of this release

V8.1 sits on the working V6.2 longitudinal core and adds the periodic clinical
imaging and fusion layer:

1. `src/utils/qr_encoder.py`: dependency-free QR codec (byte mode, versions 1
   to 3, EC levels L and M, Reed-Solomon error correction, mask penalty
   selection, PNG and SVG output).
2. `src/models/ultrasound_cv.py`: ultrasound image pipeline with a hard quality
   gate, provenance-tagged structured features and descriptive exam comparison.
3. `src/models/fusion.py`: provenance-aware multimodal fusion context with
   per-group reliability weights and explicit missing-modality reporting.
4. `src/models/longitudinal_report.py`: one-page clinical summary (text and
   PDF, single page enforced) and the full longitudinal HTML report.
5. `src/ui/ultrasound_fusion_tab.py`: the Ultrasound + Fusion tab.
6. `src/utils/history_store.py`: `ultrasound_images` and `report_tokens`
   tables, token issue and resolve, image logging.
7. `src/validation/longitudinal_experiment.py`: Model A-E, adding Model D
   (clinical + cycle + longitudinal + ultrasound-derived) and Model E (full
   multimodal).
8. `src/ui/clinical_tab.py` and `src/ui/main_window.py`: QR report access in
   the clinical dashboard, the new tab 08, renumbered tabs 09 and 10, V8
   branding.
9. `tests/test_v8_1.py`: 20 tests for the above.

Nothing working was removed. Hardware support in this release covers the
Arduino Mega 2560 bench hub, the Arduino Nano wearable pod (including pod to
Mega relay mode) and the ESP8266 TCP bridge; see
`docs/ARDUINO_WIRING_GUIDE.md`.

## 2. Architecture

```text
WEARABLE POD (Nano) / BENCH HUB (Mega) / ESP8266 BRIDGE
        |  $CP2 packets, 20 Hz, CRC checked
        v
PACKET PARSER -> SIGNAL PROCESSORS -> FEATURE VECTOR (1 Hz)
        v
SIGNAL QUALITY + WITHHOLD LAYER  (SQI < 0.40 / conf < 25 / CI > 65 / no HRV => withhold)
        v
PERSONAL BASELINE -> CHANGE DETECTOR -> PERSONAL FINGERPRINT
        v
RISK ENGINE (transparent fallback, nine domains, bootstrap CI, confidence)
        v
LONGITUDINAL SUMMARIES: WHAT CHANGED, CARE JOURNEY, 7-day profile
        v
CLINICAL LAYER: patient inputs, care plan and adherence, visits and notes,
report history and compare
        v
ULTRASOUND CV: quality gate -> structured features (provenance) -> exam compare
        v
MULTIMODAL FUSION: provenance tags, group weights, missing modalities
        v
REPORTING: one-page summary, full HTML report, QR token, weekly text/PDF
        v
LOCAL SQLite (offline first) + DASHBOARD TABS 01-10
```

## 3. Design rules enforced in code

- Provenance everywhere: MEASURED, PATIENT-REPORTED, CLINICALLY-ENTERED,
  IMAGE-DERIVED, MODEL-INFERRED, UNKNOWN. Nothing is presented as a measurement
  unless its tag says so.
- Withholding over guessing: the decision layer in `src/validation/sqi.py`
  refuses to display a risk number when data quality, confidence or interval
  width fails, or when HRV is missing.
- No invented data: no ultrasound dataset is included or invented; image-
  derived anatomy returns UNKNOWN with confidence 0.0 until a validated
  labelled patient-grouped dataset exists. The schema and split validator
  (`UltrasoundDataset`) documents exactly what a legitimate dataset must
  contain and rejects image-level splits.
- No causation language: outputs say "temporally associated with"; the care
  journey separates OBSERVED, ASSOCIATED and UNKNOWN.
- Hormone values never enter the headline score; they remain an illustration
  behind the Advanced tab.
- Offline first: local SQLite, no cloud dependency, QR encoder without third-
  party packages.
- Treatment decisions never made: the care plan is bookkeeping with reminders.

## 4. Dataset and privacy rules

- Public development data kept in `data/public/`: the Kaggle PCOS cohort (CSV
  and the original xlsx) for the clinical-variable baseline model, and the
  PhysioNet wrist-PPG-during-exercise database for the PPG quality model. The
  PhysioNet page has been withdrawn, so the local copy is the only source; it
  is used for signal-quality research only, never as wearable accuracy.
- Runtime state (database, calibration files, training audit, assistant
  config) is gitignored and stays on the machine that produced it.
- Report QR payloads are random de-identified tokens that resolve locally and
  expire; no personal information is encoded.
- Exports are explicit user actions; demo rows are flagged and excluded from
  real analysis.
- Any future human data collection requires consent, oversight and
  institutional approval before the first sample.

## 5. Known weaknesses

1. No validated longitudinal wearable-plus-ultrasound dataset: the central
   research question is untested. Everything dependent on it is PENDING.
2. The live risk engine is a transparent fallback equation with research-prior
   weights, not a trained calibrated model.
3. No Python BLE client yet; the pod connects over USB serial or the ESP8266
   bridge. A wireless BLE pod remains a design milestone.
4. QR optical scanning has not been tested across phone models; encoder
   self-tests (round-trips and Reed-Solomon syndromes) pass.
5. Firmware packet rate is 20 Hz while some processors assume up to 50 Hz;
   documented, not hidden.
6. User versus clinician role separation is conceptual on a single machine,
   not authenticated.
7. Ultrasound feature extraction awaits data; the plain UNKNOWN state is
   correct but unproven.

## 6. Experiments required before any clinical usefulness claim

1. Ethics-approved pilot (about 20-30 participants, 8-12 weeks) with wearable,
   cycle and symptom logs and periodic clinical assessment including ultrasound
   where clinically indicated.
2. Model A-E comparison on pilot data with patient-level splits: AUROC, AUPRC,
   sensitivity, specificity, F1 and calibration with confidence intervals per
   model.
3. Ultrasound feature pipeline validation on collected labelled images,
   testing Model D against Model C.
4. Per-sensor ablation (PPG, plus temperature, plus IMU, plus GSR) to justify
   the hardware list.
5. QR interoperability on several phone models.
6. Calibration and uncertainty audit with reliability diagrams and interval
   coverage.

Until these produce real results, every claim stays NOT YET VALIDATED.

## 7. Documentation index

- `docs/HOW_THE_PROJECT_WORKS.md`: system, features, physiology, mastery plan.
- `docs/CODE_EXPLANATION.md`: code walkthrough and judge kit.
- `docs/ARDUINO_WIRING_GUIDE.md`: Mega and Nano hardware, firmware, protocol.
- `docs/scientific_model.md`: every formula as implemented.
- `docs/validation.md`: current checks and the pending validation plan.
- `README.md`: entry point, run instructions, current status.

*End of specification. Nothing here claims clinical accuracy, real patient
data, real ultrasound images or validated performance that has not been
demonstrated.*
