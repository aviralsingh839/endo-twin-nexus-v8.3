# How CHRONO-PCOS V8.1 Works: Features, Body Physiology and Mastery Guide

This document explains the whole project in one place: what it is, what every
part does, why the body produces the signals we measure, and how to learn the
system well enough to explain any part of it on stage. It is written for me and
for anyone who inherits the project, so it stays practical rather than
marketing-flavoured.

Companion documents:

- `docs/CODE_EXPLANATION.md` for the line-by-line code walkthrough and the
  judge question bank.
- `docs/ARDUINO_WIRING_GUIDE.md` for the Mega and Nano hardware.
- `docs/V8_1_BUILD_SPECIFICATION.md` for the engineering specification.
- `docs/scientific_model.md` and `docs/validation.md` for the mathematics and
  the validation plan.

---

## 1. What the project is, in one paragraph

CHRONO-PCOS V8.1 is an offline research prototype that watches a person's
physiology continuously between clinic visits with a cheap wearable (pulse
waveform, skin temperature, motion, optional skin conductance), learns that
person's own baseline, detects changes that persist for hours or days, and then
combines that longitudinal picture with periodic clinical information (cycle
and symptom logs, blood pressure, glucose, and ultrasound images passed through
a quality gate) into one explainable, uncertainty-aware PCOS-related risk
estimate. It never diagnoses. Every number carries a provenance label and a
confidence, and when the data is too weak the system shows "no reliable
estimate" instead of a number.

The research question it serves: does information collected *between* visits,
fused with periodic clinical information, improve PCOS-related risk
phenotyping compared with a single-visit snapshot? The wearable is only the
acquisition device. The contribution is the longitudinal framework.

---

## 2. The whole system on one page

```text
   WEARABLE POD (Arduino Nano)          BENCH HUB (Arduino Mega)
   PPG + skin temp + motion (+GSR)      same sensors + ECG, mic, FSR,
   20 Hz $CP2 packets                   light, environment, OLED, LEDs
              |                                  |
              +-------------- or ---------------+
                             |  USB serial, or ESP8266 TCP bridge
                             v
                 PACKET PARSER + CRC CHECK  (src/serial_io)
                             v
        SIGNAL PROCESSORS -> FEATURE VECTOR  (src/signal_processing,
        HR, HRV, SpO2, motion, temp slope,     src/features)
        GSR tonic/phasic, sleep probability
                             v
        SIGNAL QUALITY + WITHHOLD LAYER  (src/validation/sqi,
        too weak => "NO RELIABLE ESTIMATE"   src/utils/quality)
                             v
        PERSONAL BASELINE -> CHANGE DETECTOR -> FINGERPRINT
        (src/models/personalization, change_detector, fingerprint)
                             v
        RISK ENGINE + CI + CONFIDENCE + CONTRIBUTORS
        (src/models/risk_engine)
                             v
     DASHBOARD TABS 01-10  +  LOCAL SQLite HISTORY  (src/ui, src/utils/history_store)
                             v
     REPORTS: one-page clinical summary, full HTML report,
     QR token, weekly text/PDF, WHAT CHANGED summary
     (src/models/longitudinal_report, src/utils/qr_encoder, report)

     PLUS the clinical layer:
     patient inputs, care plan and adherence, clinical dashboard,
     ultrasound CV with quality gate, provenance-aware fusion
     (src/models/care_plan, clinical_record, ultrasound_cv, fusion)
```

Everything runs on one laptop with no internet. The database is a local SQLite
file that the app creates on first run and never syncs anywhere.

---

## 3. What the hardware measures and why the body produces it

This section is the "functioning of the body" part. Each signal is followed by
the physiology that makes it useful, and by the limits of what it can
support.

### 3.1 Photoplethysmogram (PPG), MAX30102, red + infrared light

Every heartbeat pushes a volume of blood into the arteries. In the skin's
microvasculature that volume pulse changes how much light is absorbed, so a
LED-and-photodiode pair on the skin sees a small periodic wave at heart rate.
From that wave the software extracts heart rate (peak-to-peak intervals),
pulse amplitude (how strong the volume pulse is) and an educational SpO2
estimate from the red-to-infrared amplitude ratio.

What it supports: resting heart rate, heart-rate variability, sleep and wake
detection, pulse amplitude trends. What it cannot support: blood pressure,
hormones, or any diagnosis. Motion destroys the wave, which is why the IMU
exists and why the quality layer downgrades moving windows.

### 3.2 Heart-rate variability (HRV) from the pulse intervals

The interval between beats is not constant. Breathing and vagal (parasympathetic)
activity speed the heart up and slow it down every few seconds. RMSSD, the root
mean square of successive interval differences, tracks that fast vagal
component; SDNN tracks total variability. Low RMSSD at rest is associated in
research with stress load, poor recovery and autonomic imbalance. PCOS research
reports autonomic tendency differences, always as association, never as a
cause or a test.

### 3.3 Skin temperature, DS18B20

Core body temperature runs on a circadian rhythm of roughly a degree, lowest in
the early morning hours and highest in the evening, and skin temperature
follows it with its own offset from peripheral blood flow. Two more effects
matter here: after ovulation, progesterone is thermogenic and raises basal
temperature by a few tenths of a degree for the luteal phase, and stress or
illness shifts the rhythm. The project uses the *rhythm* (how well a 24-hour
cosine fits the temperature series) as a circadian-domain input, and the
luteal-shift idea only as background physiology, never as an ovulation test.

### 3.4 Motion, MPU6050 accelerometer and gyro

The magnitude of dynamic acceleration tells activity level and restlessness.
Three jobs: activity and inactivity scoring, sleep restlessness, and gating the
PPG (a moving window is a low-quality window). The firmware removes the gravity
bias at start-up so only movement remains.

### 3.5 Galvanic skin response (GSR), optional

Sweat glands are driven by the sympathetic nervous system. Even invisible
changes in sweat conductance change skin resistance, so a slow tonic level plus
quick phasic spikes track arousal. The dashboard keeps the person's own tonic
baseline and counts phasic responses per minute. Modules differ electrically,
so raw ADC counts are used and interpreted only relative to that person's
baseline.

### 3.6 Light (BH1750), environment (BME280), voice (MAX4466), pressure (FSR), ECG (AD8232)

Light exposure pattern is a circadian entrainment cue: bright days and dark
nights stabilise the rhythm, and the circadian analyzer uses the day-night lux
contrast as one small term. Room temperature and humidity are context for the
skin-temperature channel. The microphone feeds an experimental voice proxy that
stays behind the Advanced tab. The FSR is not a biological signal at all: it
measures how hard the finger presses on the PPG window, so the software can
blame pressure instead of physiology when the pulse amplitude collapses. The
AD8232 ECG gives a clean electrical heartbeat reference for periodic
checkpoints, used to validate PPG-derived heart rate and HRV.

### 3.7 The physiology behind the score, stated carefully

PCOS is a heterogeneous endocrine-metabolic condition. The Rotterdam view needs
two of three: irregular or absent ovulation, clinical or biochemical
hyperandrogenism, and polycystic ovarian morphology on ultrasound, with other
causes excluded. The mechanisms the project leans on are all association-level:

- Insulin resistance raises insulin demand; high insulin is associated with
  increased ovarian androgen production and lower hepatic SHBG, raising free
  androgen tendency.
- Sleep loss and circadian disruption are associated with HPA-axis load and
  worse glucose regulation.
- Sympathetic dominance and low HRV accompany chronic stress states that
  co-occur with metabolic disturbance.
- Adiposity and low activity feed inflammation and insulin resistance.
- Irregular cycle length and long gaps between periods are the strongest
  practical, patient-reportable signals, which is why cycle input carries the
  largest weight in the score.

None of this is measured by a sensor. The wearable measures physiology that is
*associated* with these mechanisms (sleep, rhythm, autonomic tone, activity),
and the score says so on screen: it is a research tendency estimate, not a
hormone measurement and not a diagnosis.

---

## 4. The software pipeline, stage by stage

1. **Acquisition.** `ArduinoReader` (or `NetworkReader` for the Wi-Fi bridge)
   runs a background thread that reads lines from the serial port, reconnects
   with a 3-second backoff if the cable drops, and raises a stale-link error
   after 6 silent seconds. Demo mode replaces this thread with a synthetic
   stream that is labelled DEMO everywhere and excluded from exports.
2. **Parsing and integrity.** `PacketParser` checks the prefix, the field
   count and the XOR CRC, and converts the line into a `SensorSample`.
   Corrupt lines are dropped and counted, not guessed.
3. **Signal processing.** `PPGProcessor` DC-blocks and smooths the IR wave,
   detects peaks with a refractory period, cleans the interval series with a
   median filter, and computes HR, RMSSD, SDNN, pNN50, SpO2 and pulse
   amplitude. `IMUProcessor`, `TemperatureProcessor`, `GSRProcessor` and
   `ECGProcessor` do the same job for their channels.
4. **Feature fusion.** `RealtimeFeatureExtractor` merges the processors into
   one `FeatureVector` per second, prefers ECG beat timing when ECG quality is
   above 0.55, runs the sleep estimator, the stress estimator and the metabolic
   estimators, and asks `CircadianAnalyzer` (every 60 s) for cosinor rhythm
   stability.
5. **Quality and withholding.** Per-sensor SQI plus a completeness score give
   an overall signal quality. The decision layer in `src/validation/sqi.py`
   withholds the risk number when overall SQI is below 0.40, confidence below
   25, the 90% interval wider than 65 points, or HRV missing entirely. The UI
   shows a banner instead of a fake number.
6. **Personal baseline.** After 5 minutes of calm good-quality data (or a
   manual capture), `BaselineManager` stores median, MAD, mean, std and the
   5th/95th percentiles per metric. Later observations update it gradually with
   an outlier guard at 3.5 scale units, so one bad minute never redefines what
   is normal for this person.
7. **Change detection and fingerprint.** `ChangeDetector` classifies each
   metric as normal, single, persistent (3+ out-of-band points), progressive
   (slope at least 1 scale unit per day away from baseline) or recovery, each
   with a quality gate. `FingerprintEngine` presents that as the personal
   physiological fingerprint: baseline with spread, current value, deviation in
   robust SD, persistence in points and hours, slope per day, trend label.
8. **Risk estimate.** `RiskEngine` combines nine domain scores (cycle,
   metabolic, glucose, BP, stress/autonomic, sleep, circadian, temperature
   rhythm, low activity) in a transparent logistic equation with published-in-
   code weights, then bootstraps a 90% interval (250 draws, noise scaled by
   signal quality) and computes confidence from data quality, baseline
   availability, interval width, feature completeness and cycle information.
   Hormone-twin values never enter this score.
9. **Longitudinal summary.** `WhatChangedEngine` turns the change report plus
   the local history (cycle, symptoms, BP, glucose, adherence) into
   evidence-linked statements, each with the exact numbers behind it and
   "temporally associated with" wording only.
10. **Clinical layer.** Care plan and adherence bookkeeping, clinical visits
    and notes, report history and comparison, and the V8.1 imaging layer:
    ultrasound images go through a quality gate (decodable, at least 320x240,
    sharpness above threshold) and then produce structured features that are
    CLINICALLY-ENTERED when a clinician typed them and UNKNOWN otherwise,
    because no validated labelled ultrasound dataset exists in this project.
    `FusionEngine` then tags every input with a provenance class and computes
    per-group reliability weights, listing missing modalities explicitly.
11. **Reporting.** A one-page clinical summary (text and PDF, hard-limited to
    one page), a full longitudinal HTML report, and a QR code whose payload is
    only a random de-identified token that resolves locally. The QR encoder is
    written from scratch with Reed-Solomon error correction and no
    dependencies.
12. **Storage.** Everything lands in the local SQLite database: sessions,
    per-10-second features, calibrations, anomalies, quality and error logs,
    BP/glucose/weight, symptoms, cycle entries, ultrasound observations and
    images, medications and adherence, goals, appointments, notes, visits,
    reports and report tokens.

---

## 5. The ten dashboard tabs

| Tab | What it shows | Where it comes from |
|---|---|---|
| 01 Overview | Headline risk with confidence, CI, data quality and coverage; top contributors; personal baseline; risk trend; what changed since last assessment | risk engine + change report |
| 02 Live Wearable | Connection state, per-sensor cards, live PPG waveform, withheld banner | serial reader + processors |
| 03 Longitudinal | Baseline, change-point analysis, personal fingerprint, 7-day profile and trajectory | personalization, change detector, fingerprint, multi_day |
| 04 PCOS Analysis | Risk summary, model input status including ultrasound, contributors, domain radar, transparency box of measured vs derived vs not measured | risk engine + fusion |
| 05 Patient Inputs | Cycle day and length, irregularity, symptoms, BP, glucose, weight, manual wearable-style readings | history store |
| 06 Care and Adherence | Medication plan, taken/skipped/snoozed log, adherence percent, lifestyle goals, appointment reminders | care plan manager |
| 07 Clinical Dashboard | What changed since last visit, patient overview, report history and compare, ultrasound entries and notes, care journey, QR report access, Model A-E research panel | clinical record + reports |
| 08 Ultrasound + Fusion | Image import, quality gate verdict, structured features with provenance, exam comparison, fusion context with group weights and missing modalities, one-page summary, HTML report, QR token | ultrasound_cv + fusion + longitudinal_report |
| 09 Validation / Research | SQI, agreement, calibration, leakage checks, ablation, leave-one-subject-out, prospective mode, repeatability, validation report | src/validation |
| 10 Advanced / Research Tools | Sleep and circadian view, hormone illustration (excluded from the score), metabolic challenge, VoxVasc, what-if lab, research lab, assistant, evidence center, diagnostics, digital twin timeline, recommendations and alerts, equipment and protocol notes | experimental modules |

Modes: LIVE (real hardware), DEMO (labelled synthetic stream), Judge Mode
(a scripted ~2 minute demonstration on labelled synthetic data including the
clinical record, report and QR flow), and replay of recorded sessions. The
header badge always says which one is active.

---

## 6. Limits, stated the way I say them on stage

1. No diagnosis, ever. Diagnosis needs a clinician and accepted criteria.
2. No sensor measures hormones. Hormone-like values are illustration only and
   sit behind the Advanced tab with zero effect on the score.
3. The live risk engine is a transparent fallback equation with research-prior
   weights, not a trained calibrated model. Labelled longitudinal wearable data
   does not publicly exist; an ethics-approved pilot is the only realistic route.
4. Ultrasound image-derived features are UNKNOWN by design until a validated,
   labelled, patient-grouped dataset exists. The quality gate runs today; the
   anatomy extractor waits for data. Nothing is invented.
5. The Model A-E experiment (does longitudinal or ultrasound information add
   value?) is PENDING by design.
6. No cyst-rupture prediction exists or is claimed.
7. Care-plan reminders are bookkeeping; the app never changes, starts, stops or
   prescribes treatment.
8. The Python BLE client is not written yet, so the pod connects over USB
   serial or the ESP8266 TCP bridge.

---

## 7. How to master this project

### 7.1 A two-week study plan

Week 1, signal path:

1. Day 1: read `src/config.py` and `src/data_models.py`. Know every constant
   and the fields of `SensorSample` and `FeatureVector`.
2. Day 2: run the Mega or Nano firmware, watch `$CP2` lines, then read
   `src/serial_io/packet_parser.py` and `arduino_reader.py`. Break the CRC on
   purpose (edit one digit in a saved line and feed it through the parser in a
   Python shell) and watch it reject.
3. Day 3: read `src/signal_processing/ppg.py` with a recorded 30-second window
   in hand; plot the filtered wave and the detected peaks yourself.
4. Day 4: read `hrv.py`, `spo2.py`, `imu.py`, `temperature.py`, `gsr.py`.
   Recompute RMSSD by hand from eight intervals to feel the formula.
5. Day 5: read `src/utils/quality.py` and `src/validation/sqi.py`. Force a
   low-quality state (lift your finger) and watch the withhold banner.

Week 2, intelligence path:

6. Day 6: `personalization.py` and `change_detector.py`. Capture a real
   baseline, then move somewhere warm and watch the temperature metric drift
   into "persistent".
7. Day 7: `risk_engine.py`. Reproduce one risk number by hand from the nine
   domain scores and the weight table.
8. Day 8: `fingerprint.py`, `what_changed.py`, `multi_day.py`.
9. Day 9: `ultrasound_cv.py`, `fusion.py`, `longitudinal_report.py`,
   `qr_encoder.py`. Feed a blurred image and a tiny image and read the gate's
   reasons.
10. Day 10: `src/validation/*` and the test suite. Run
    `python -m pytest tests/ -q` (124 tests) and read any test that fails if
    you change something.

### 7.2 The code map to keep in your head

| Folder | Role | First file to read |
|---|---|---|
| src/serial_io | bytes in, samples out, reconnects | packet_parser.py |
| src/signal_processing | one processor per sensor | ppg.py |
| src/features | per-second feature fusion, circadian, sleep | realtime_features.py |
| src/models | baseline, change, risk, fusion, imaging, care, reports | risk_engine.py |
| src/validation | quality gates and the scientific validation lab | sqi.py |
| src/utils | database, QR, reports, quality, replay, synthetic | history_store.py |
| src/ui | the ten tabs and all widgets | main_window.py |
| arduino | firmware for Mega, Nano pod, bridge, optional nodes | chrono_pcos_mega_firmware.ino |
| scripts | training workflows for the optional joblib models | train_pcos_risk_model.py |
| tests | 124 tests, one file per feature generation | test_v8_1.py |

### 7.3 Concepts you must be able to explain without notes

XOR CRC; DC blocker and exponential smoothing; peak detection with refractory
period; RMSSD, SDNN, pNN50; median absolute deviation and robust z-scores;
cosinor fit and its R-squared; logistic (sigmoid) transform and why weights
are additive in log-odds; bootstrap interval; provenance labels; patient-level
splitting and why image-level splits leak; Reed-Solomon error correction in the
QR encoder; the difference between association and causation.

### 7.4 Experiments to run on yourself before the exhibition

- Capture a baseline, then drink something warm and watch the temperature
  domain move while the score barely moves (weights).
- Unplug one sensor mid-session and confirm confidence drops while missing
  channels never drag quality down.
- Feed the ultrasound gate a phone photo, a 100x100 crop and a motion-blurred
  image; read the three different verdicts.
- Generate the QR, scan it with a phone, and confirm the payload is only the
  token.
- Kill the USB cable for 20 seconds and watch the reconnect and the gap
  handling.

Being able to do these live, and to say what each result means and does not
mean, is what "mastering" the project means in front of a judge.

---

## 8. Running the system

```text
pip install -r requirements.txt

python -m src.app --demo                 # synthetic stream, clearly labelled
python -m src.app --port COM5            # live from a board (or /dev/ttyACM0)
python -m src.app --net 192.168.4.1:7777 # live over the ESP8266 bridge
python -m pytest tests/ -q               # 124 tests
```

Windows users can double-click `run_demo_windows.bat` or
`run_arduino_windows.bat`; Linux and macOS users have the `.sh` equivalents.
The Judge Mode button in the header runs the scripted demonstration.

---

## 9. Safety and ethics in one place

Educational physiological monitoring only. No diagnosis, no treatment
decisions, no hormone measurement, no anatomy from images without validated
data. Body-connected circuits run from battery or laptop USB. ECG only with
consent, battery power, and never on people with implanted cardiac devices. No
glucose challenges on visitors. Any human data collection requires consent,
adult or clinician oversight and institutional approval. All data stays on the
local machine, exports are explicit, and report QR tokens carry no personal
information.
