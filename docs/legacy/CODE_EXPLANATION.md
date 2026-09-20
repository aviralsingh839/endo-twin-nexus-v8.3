# Code Explanation: Every Part of CHRONO-PCOS V8.1, Written for the Judge Session

This document walks through the code I wrote, in the order I would explain it
at the table: the runtime model, the Python pipeline module by module with the
actual formulas and constants, the Arduino firmware, the test suite, and then a
judge question bank with the exact file and function to open for each answer.

Line counts below are approximate and refer to the checked-in files.

---

## 1. Repository layout and what each folder owns

```text
chrono_pcos_project V8/
  src/app.py                 entry point: argument parsing, QApplication, MainWindow
  src/config.py              every constant: rates, thresholds, paths, UserProfile
  src/data_models.py         SensorSample, FeatureVector, RiskResult, CircadianMetrics
  src/serial_io/             bytes -> SensorSample: parser, serial thread, TCP thread, LED helper
  src/signal_processing/     one streaming processor per sensor (ppg, hrv, spo2, imu, temp, gsr, ecg, filters)
  src/features/              realtime_features fuses processors; circadian_features; sleep_features
  src/models/                the analytical core: baseline, change, fingerprint, risk, fusion,
                             ultrasound CV, care plan, clinical record, reports, what-changed, ...
  src/validation/            the scientific-validation lab: sqi + withhold layer, agreement,
                             calibration, leakage, LOSOCV, ablation, repeatability, prospective, report
  src/utils/                 history_store (SQLite), quality, qr_encoder, report, replay, storage, math
  src/ui/                    main_window + one file per tab + widgets (gauges, radar, plots, theme)
  arduino/                   mega firmware, nano pod firmware, esp8266 bridge, ecg and insole node sketches
  scripts/                   offline training workflows for the optional joblib models
  tests/                     124 pytest tests
  docs/                      the documentation set, including this file
```

Total Python is roughly 14,000 lines including tests; firmware is about 1,000
lines across five sketches.

## 2. Runtime model: threads, timers, signals

`src/app.py` parses `--demo`, `--port`, `--net`, adds the project root to
`sys.path` so the file also runs from an IDE, then creates the Qt application
and one `MainWindow`.

`MainWindow.__init__` (src/ui/main_window.py) builds the ten tabs and starts
two Qt timers:

| Timer | Period | Job |
|---|---|---|
| feature_timer | 1000 ms | pull the latest FeatureVector, update cards, plots, baseline UI, logs |
| circadian_timer | 60000 ms | re-run CircadianAnalyzer over stored history and push the rhythm metrics into the extractor |

Risk recomputation happens inside the feature tick but is rate-limited to every
2 s by `RISK_UPDATE_INTERVAL_S`, and the UI history window is 180 s.

Data acquisition is a plain Python thread, not a Qt thread:

- `ArduinoReader._run` opens pyserial at 115200, waits 1.8 s for the board
  reset, then loops `readline()` and emits the Qt signal `sample_received` for
  every parsed `SensorSample`. On any exception it closes, emits
  `state_changed("reconnecting")`, backs off 3 s (`RECONNECT_RETRY_S`) in
  100 ms slices so stop() stays responsive, and retries forever until stopped.
  A silent line for 6 s (`STALE_DATA_TIMEOUT_S`) raises `_SerialStaleError`,
  which is the unplugged-cable case.
- `NetworkReader` is the same design over a TCP socket for the ESP8266 bridge.
- Demo mode swaps in `src/utils/demo_stream.py`, a synthetic generator whose
  samples carry `source="demo"`; the mode badge and every export respect that.

The main thread never blocks on I/O. Samples arrive through signals, the 1 s
timer computes features, and widgets only ever read the latest feature vector.
That separation is why the UI stays smooth at 20 Hz input.

## 3. Core data structures (src/data_models.py)

- `SensorSample`: one decoded packet. Fields: timestamps (`timestamp_s` from
  the PC clock, `ms` from board millis), `ir`, `red`, accel and gyro in g and
  deg/s, `temp_c`, `gsr_raw`, `lux`, plus optional `ecg_raw`, `mic_*`,
  `fsr_raw`, `temp1_c`, environment fields, `buttons`, `status`, `source`.
- `FeatureVector`: one row per second of derived physiology: HR, SpO2, RMSSD,
  SDNN, pNN50, pulse amplitude, motion and activity, skin temp and slope, GSR
  tonic/phasic/z, sleep probabilities, circadian stability and disruption,
  stress trio, metabolic outputs, signal quality, baseline availability and
  z-scores. Defaults are neutral (50 for percentages, None for absent), so a
  missing channel is visibly absent rather than silently zero.
- `RiskResult`: risk percent, CI low/high, confidence, category, the nine
  domain scores, sorted contributions, the explanation sentence, and hormone
  estimates carried for the research-only illustration.

## 4. Serial layer (src/serial_io)

`packet_parser.py`:

- `xor_crc_ascii`: XOR of every payload character, masked to 8 bits; the
  firmware prints it as two hex digits. `_verify_crc` recomputes and rejects
  mismatches with both values in the error, which is how I debugged a loose
  jumper wire once.
- `_parse_cp` expects exactly 15 comma fields, `_parse_cp2` exactly 25. Each
  numeric conversion is wrapped so a bad field raises `PacketParseError`
  instead of crashing the reader thread.
- `decode_status_flags` maps the 12 status bits to human strings for the
  diagnostics panel.

`led_controller.py`: `set_risk_state` maps risk and confidence to G/Y/R with
the rule confidence under 35 forces yellow, and only sends a command when the
state actually changes, so the serial line is not spammed.

## 5. Signal processing (src/signal_processing)

### filters.py
Three stateful primitives used everywhere: `MovingAverage`,
`ExponentialSmoother` (y = a*x + (1-a)*y), and `DCBlocker`
(y[n] = x[n] - x[n-1] + r*y[n-1], a one-pole high-pass that removes the DC
light level from the pulse wave). Plus `robust_detrend` and `rolling_rms`.

### ppg.py (PPGProcessor, ~120 lines)
- `add_sample`: primes the DC blocker with the first sample so the filter has
  no start-up step transient (this fixed a bug where peaks were blind for the
  first ~20 s), then DC-blocks with r=0.97 and smooths with alpha=0.35 into a
  180 s deque.
- `_detect_peaks` over the last 20 s: subtract median, noise = std, threshold =
  max(median + 0.45*noise, 60th percentile), skip a 2 s warm-up, then local
  maxima with a refractory period of 60/MAX_HR_BPM (210 bpm). A higher peak
  inside the refractory window replaces the previous one.
- Interval cleaning: keep IBI within [60/210, 60/35] s, then drop intervals
  more than 25% from the median.
- `features`: HRV from `hrv.py`, SpO2 from `spo2.py`, pulse amplitude =
  (p95 - p5)/median over the last 12 s, and quality = 0.7*ppg_quality +
  0.3*spo2_quality.

### hrv.py
`clean_ibi_seconds` plus `hrv_time_domain`: RMSSD = sqrt(mean(diff^2))*1000,
SDNN = std(ddof=1)*1000, pNN50 = fraction of |diff| > 50 ms, mean HR =
60/median(IBI). `HRVBuffer` also rejects a new interval that jumps more than
35% from the previous one.

### spo2.py
Ratio-of-ratios r = (red_AC/red_DC)/(ir_AC/ir_DC) with AC from (p95-p5)/2 and
DC from the median; SpO2 = 110 - 25*r clamped to 70..100, quality peaks near
r=0.7. The docstring says plainly that this is an educational approximation,
not a pulse-oximeter algorithm.

### imu.py
Vector magnitude and gyro magnitude per sample; over 10 s:
motion_index = RMS(acc - 1g) + 0.3*RMS(jerk) + 0.002*RMS(gyro);
activity_level = clamp((motion_index - 0.02)/0.40*100); low_activity_risk =
100 - activity.

### temperature.py
Rejects readings outside 15..45 C; baseline drifts as an EWMA
(0.999/0.001) toward the median; `features` returns the latest value, a
polyfit slope in C/min over 5 min, and stability = clamp(1 - std/0.5).

### gsr.py
Baseline EWMA (0.995/0.005) toward the 20th percentile; tonic = median of the
last 60 s; phasic events counted as first differences above median + 4*MAD,
reported per minute; z against the personal resting baseline with scale 80.

### ecg.py
DC block r=0.985 + smoothing 0.45, automatic polarity flip when the negative
excursion dominates, R-peaks above the 92nd percentile with the same
refractory rule, quality = 0.8*(clean/total intervals) + 0.2, then HRV on the
cleaned intervals. Used as the reference channel, never for diagnosis.

## 6. Feature fusion and the higher estimators (src/features, src/models)

### realtime_features.py (RealtimeFeatureExtractor)
Owns one instance of every processor plus the sleep, stress, metabolic and
voice estimators and the BaselineManager. `add_sample` fans the sample out;
`compute()` builds the FeatureVector per second. Key decisions in code:

- ECG beat timing replaces PPG HR/HRV only when `ecg_quality > 0.55`.
- Signal quality is the mean over *present* sensors only, so an absent optional
  channel can never drag the score down; then it is blended 0.7/0.3 with the
  completeness score from `utils.quality.completeness_score`.
- Circadian metrics are injected by the 60 s main-window timer; until then the
  neutral defaults stand, and the code comment says they are placeholders, not
  measurements.
- Baseline: after 300 s of calm data with mean quality >= 0.5 the extractor
  auto-captures once; manual capture is always available; z-scores per metric
  are exposed once a baseline exists.

### sleep_model.py
Logistic formula on z-scores:
x = -1.8*motion_z - 0.7*hr_z + 0.9*rmssd_z + 0.4*temp_stable - 0.4*gsr_z + 0.6*time_prior,
with time_prior = 1 between 22:00 and 07:00, sharpened 70/30 by a user-entered
sleep window. Deep and REM probabilities use their own logistic terms with
early-night and late-night indicators.

### stress_model.py
acute = 100*sigmoid(0.9*hr_z - 1.1*rmssd_z + 0.9*phasic_z + 0.5*gsr_z
- 0.5*max(motion_z,0) + 0.3*temp_drop_z); a motion gate multiplies by 0.65 when
activity > 45 (exercise is not stress); chronic blends slowly; autonomic
imbalance = 100*sigmoid(-1.0*rmssd_z + 0.5*hr_z + 0.4*gsr_z); stress_index =
0.65*acute + 0.35*chronic.

### metabolic_model.py
Glucose risk uses context-dependent logistic curves (fasting centred at 100,
2-hour at 140, random at 160 mg/dL). Insulin-resistance tendency:
ir = 100*sigmoid(-2.0 + 0.025*(glucose-90) + 0.045*(BMI-23) + 0.004*bp_risk
+ 0.008*sleep_risk + 0.007*stress + 0.005*circadian_disruption
- 0.006*activity). Metabolic-syndrome proxy is a weighted sum (glucose 0.28,
BMI 0.20, BP 0.18, inactivity 0.12, sleep 0.12, stress 0.10). Inflammation is
another small logistic on HR, temperature elevation, sleep, glucose, stress.

### circadian_features.py (CircadianAnalyzer)
Cosinor fit per channel: least squares of y against [1, cos(w t), sin(w t)]
with w = 2*pi/24 h, and R2 = 1 - SS_res/SS_tot. Stability =
100*(0.20*hr_R2 + 0.10*hrv_R2 + 0.25*temp_R2 + 0.10*gsr_R2 +
0.15*activity_regularity + 0.15*sleep_regularity + 0.05*light_regularity),
where activity regularity is 1 - CV of the hourly activity profile and light
regularity is the day-night lux contrast scaled by 500 lux. Disruption =
100 - stability. Needs at least 60 feature rows; otherwise neutral 50.

## 7. The longitudinal core

### personalization.py (BaselineManager)
`capture_from_features` needs 60 samples; per metric it stores median, p05,
p95, mean, std, count and MAD. `update_observation` blends rolling
median/MAD windows in with alpha=0.05 over a 600-point window and refuses to
move the baseline when the rolling median is more than 3.5 scale units away
(the outlier guard). Baselines persist to data/baselines/personal_baseline.json
on this machine only; that path is gitignored.

### change_detector.py
Per metric: robust scale = max(1.4826*MAD, 2% of |median|); z of the latest
value; slope per day from a 12-point fit; persistence counted in consecutive
out-of-band points and hours. Classification: |z| < 2 normal, |z| > 3 a real
deviation, 3+ persistent points makes it persistent, slope >= 1 scale unit per
day away makes it progressive, return into band after a deviation is recovery,
and any deviation with mean window quality under 0.5 becomes
insufficient_quality with no alert. The report never assigns causes.

### fingerprint.py
Per metric it reports baseline median and spread, current value, signed
deviation in robust SD, persistence points and hours, slope per day, and a
trend label (stable/elevated/reduced/recovering/insufficient) with a colour.
It reuses ChangeDetector so the fingerprint and the change report can never
disagree.

### what_changed.py
Builds ChangedItem records from five sources (physiology change report, cycle
history, symptom log, adherence, model estimate). Each item carries the exact
evidence string with numbers, a direction and a confidence, and the renderer
appends the standing disclaimer that these are temporal associations, not
causes.

### risk_engine.py
Nine domain scores, each 0..100 (see HOW_THE_PROJECT_WORKS.md for what feeds
each). The headline is a logistic equation in log-odds:

z = -3.0 + 1.20*cycle + 0.90*metabolic + 0.60*autonomic + 0.50*sleep
  + 0.50*circadian + 0.35*temperature + 0.35*glucose + 0.30*activity
  + 0.20*bp   (all domains divided by 100 first)
risk = 100*sigmoid(z)

Cycle score comes only from self-reported length, irregularity and days since
last period, and returns the neutral 15 when nothing is known so absence of
data never pretends to be regularity. `_bootstrap_ci` draws 250 noisy copies of
the domain vector with sigma = 5 + (1 - quality)*14 and takes the 5th and 95th
percentiles. `_confidence` = 100*(0.30*data_quality + 0.20*baseline +
0.20*ci_score + 0.20*feature_completeness + 0.10*cycle_completeness).
Categories: under 25 low, under 50 watch, under 75 elevated, above high.
`_contributions` sorts weight*score so the UI can say why the number moved.

### src/validation/sqi.py: the withhold layer
Per-sensor SQI objects with grade good/fair/poor/missing, then the decision
layer: withhold when overall SQI < 0.40, or confidence < 25, or CI width > 65,
or HRV is missing entirely. This is the code behind the "NO RELIABLE ESTIMATE"
banner, and it is the single most important safety mechanism in the project.

## 8. The V8.1 clinical-imaging and fusion layer

### ultrasound_cv.py
- Provenance vocabulary: MEASURED, PATIENT-REPORTED, CLINICALLY-ENTERED,
  IMAGE-DERIVED, MODEL-INFERRED, UNKNOWN.
- `assess_quality`: decodable (PIL), width >= 320, height >= 240, blur score
  (variance of the gradient magnitude on a downscaled grayscale image) >= 1.5.
  Failure returns the fixed sentence "ULTRASOUND QUALITY INSUFFICIENT FOR
  ANALYSIS" plus the reasons.
- `extract_features`: clinician entries pass through as CLINICALLY-ENTERED with
  their confidence; image-derived anatomy stays UNKNOWN with confidence 0.0
  because no validated labelled patient-grouped dataset exists here. The code
  says this in the returned notes, not only in the docs.
- `compare_exams`: rows only for fields present on both sides; direction
  labels increased/decreased/stable/changed with a 0.5 mm dead band.
- `UltrasoundDataset`: schema validator (patient_id, image_path, label,
  exam_date required) and `patient_split`, which splits patients, never
  images, and returns PENDING when there is no data. It exists to make the
  correct future experiment impossible to get wrong.

### fusion.py
Seven groups (clinical, wearable, longitudinal, metabolic, ecg, ultrasound,
adherence). Each FusionFeature carries value, provenance, quality and source.
`group_weights` = coverage * mean quality per group; missing groups get weight
0 and appear in `missing_groups()`. `provenance_summary` and `summary_text`
produce the transparency panel on tab 08.

### longitudinal_report.py and qr_encoder.py
The one-page summary builder enforces a single page by trimming sections in a
fixed priority order; the HTML report assembles timeline, cycle, symptom,
adherence and ultrasound sections. `qr_encoder.py` is a from-scratch byte-mode
QR codec (versions 1 to 3, EC levels L and M): GF(256) tables, Reed-Solomon
generator polynomials, block interleaving, mask penalty scoring and PNG/SVG
rendering with no third-party dependency. The report token in the QR payload
is a random de-identified string that resolves locally through
`history_store.resolve_report_token`.

### care_plan.py, clinical_record.py, multi_day.py
Care plan stores medications, goals, appointments and the taken/skipped/snoozed
log; adherence percent uses cadence doses-per-day; gap analysis emits only
"potential care-plan gap" wording. Clinical record handles visits, notes,
saved reports and `compare_reports` (improved/worsened/stable/uncertain per
metric). Multi-day distils the features table into DaySummary rows and linear
trajectories per metric for the 7-day profile.

## 9. Storage (src/utils/history_store.py)

One SQLite file with 22 tables: sessions, features, calibrations, anomalies,
quality_log, error_log, events, bp_readings, glucose_readings, weight_readings,
symptoms, menstrual_cycle, ultrasound_observations, care_medications,
medication_log, care_goals, appointments, clinical_notes, visits, reports,
ultrasound_images, report_tokens. `_ensure_column` migrates older databases
without losing rows. Demo rows carry a source flag and are excluded from real
analysis and exports. The database file itself is gitignored because it is
whoever's machine it runs on.

## 10. UI (src/ui)

`main_window.py` (~1700 lines) is the orchestrator: it builds tabs 01 to 10,
owns the reader/extractor/risk engine, wires the timers, and implements the
mode logic (LIVE/DEMO/Judge/replay), baseline capture wizard, weekly report
text and PDF, JSON/CSV export and the care-reminder tick. Each other file is
one tab or widget: vital cards, live plots, gauges, radar, fingerprint widget,
circadian clock, sleep view, hormone panel, what-if lab, research lab,
validation tab, ultrasound+fusion tab, clinical tab, care tab, patient inputs,
assistant, evidence center, diagnostics, timeline, theme. The assistant
(`models/assistant.py`) answers from live data with a local grounded rule
engine; an external LLM endpoint is optional, off by default, and configured
only through environment variables or a gitignored local config.

## 11. Firmware (arduino/)

### chrono_pcos_mega_firmware.ino (bench hub)
- Non-blocking scheduler: each sensor group has its own period (PPG 20 ms, IMU
  20 ms, analog 20 ms, temperature 1 s, environment 1 s, microphone 100 ms,
  OLED 500 ms, packet 50 ms) checked against millis(), so nothing uses delay()
  in the loop.
- `setupPPG` configures the MAX30105 library (4x averaging, red+IR, 100 Hz,
  411 us pulse, 18-bit); `setupMPU` sets 4 g / 500 dps / 21 Hz bandwidth;
  `calibrateIMU` averages 160 still samples into bias offsets.
- `readMicFeatures` takes 256 samples at ~4 kHz with delayMicroseconds and
  returns RMS and a zero-crossing pitch estimate, rejected outside 60..400 Hz.
- `makeStatus` ORs twelve fault bits (finger absent, saturation, sensor errors,
  lead-off, pressure artifact).
- `sendPacket` formats `$CP2` with dtostrf/snprintf, appends the XOR CRC as two
  hex digits.
- `handleCommand` accepts LED,G/Y/R, BEEP and PING from the dashboard.
- `RELAY_POD_SERIAL1` (default 0) turns the Mega into a base station: it
  forwards every Nano pod line from Serial1 to USB, forwards dashboard
  commands back to the pod, counts relayed lines on the OLED and suppresses its
  own packet so the PC sees exactly one stream.

### chrono_pcos_nano_pod.ino (wearable pod)
Same architecture trimmed to the pod sensor set (MAX30102, MPU6050, DS18B20,
optional GSR on A0, I2C on A4/A5). It emits the full `$CP2` frame with
placeholder values for channels the pod does not have, so the dashboard code
path is identical for pod and hub. One UART, so the same sketch serves
pod-to-PC and pod-to-Mega wiring.

### chrono_pcos_esp8266_bridge.ino
A transparent byte relay: joins your Wi-Fi or falls back to a soft AP
(CHRONO-PCOS-BRIDGE), runs a TCP server on 7777, forwards Serial1 bytes to the
client and client bytes back to Serial1, so LED and BEEP commands still work
wirelessly.

### Older sketches
Earlier revisions carried a minimal UNO sketch and ESP32 reference nodes for
ECG checkpoints and the FSR insole. None of them run on the Mega or the Nano,
so the V8.1 cleanup removed them; the packet parser still accepts the old
15-field `$CP` frame for replaying earlier recordings.

## 12. Scripts and models

`scripts/train_pcos_risk_model.py` trains the clinical-variable baseline model
from the bundled public Kaggle cohort with patient-level 5-fold CV (ROC-AUC
0.959 on that cohort; it is a model-development result and never presented as
wearable accuracy). `train_ppg_quality_model.py` trains the motion-artifact
quality model from the PhysioNet wrist-PPG-during-exercise database
(subject-level CV AUC about 0.62, used at 40% weight as a soft correction in
`utils.quality.ppg_quality`). The sleep and stress estimators are pure
formulas; no other trained artifact ships with the project.

## 13. Tests: 124 of them

| File | Tests | What it pins down |
|---|---|---|
| test_packet_parser | 1 | CRC acceptance/rejection, field counts |
| test_quality | 4 | PPG quality heuristic and model blend behaviour |
| test_risk_engine | 2 | domain math, category boundaries |
| test_personalization | 3 | baseline capture, gradual update, outlier guard |
| test_anomaly_detector | 2 | anomaly flags |
| test_circadian_and_sleep | 2 | cosinor and sleep estimator ranges |
| test_composite_and_synthetic | 2 | composite scores and synthetic week |
| test_history_store | 3 | schema, logging, tokens |
| test_multi_day | 1 | daily summaries and trajectories |
| test_assistant | 18 | grounded answers, context, LLM fallback off by default |
| test_v5_evidence | 11 | evidence center and model status labels |
| test_v5_master | 9 | change detector, gradual baseline, timeline, manual tables |
| test_v6 | 13 | risk engine redesign, tab structure, demo/live separation |
| test_v6_2 | 12 | fingerprint, what-changed, care plan, clinical record |
| test_v8_1 | 20 | QR round-trips and Reed-Solomon syndromes, ultrasound gate, UNKNOWN-by-design features, patient-level split, fusion weights, one-page report, token expiry |
| test_validation | 19 | SQI, agreement, calibration, leakage, LOSOCV, repeatability |
| test_whatif | 2 | counterfactual engine |

Run them with `python -m pytest tests/ -q`. They use temporary databases
(`tmp_path`), never the real one.

---

## 14. Judge session kit

### 14.1 Thirty-second pitch

"Most PCOS tools take a snapshot: one visit, one ultrasound, one questionnaire.
My project asks what happens between visits. A low-cost wearable pod on an
Arduino Nano collects pulse waveform, skin temperature and motion at 20 Hz. The
Python dashboard learns my personal baseline, detects changes that persist for
days, and combines that with cycle and symptom logs and periodic clinical
information, including ultrasound images through a quality gate with strict
provenance. The output is an explainable risk tendency with confidence and a
visible withhold state when data is weak. It never diagnoses, and every number
tells you where it came from."

### 14.2 Two-minute demo script

1. Header badge and Overview card: risk, confidence, CI, data quality. Say the
   sentence on screen: research estimate, not a diagnosis. (10 s)
2. Live Wearable: lift and replace your finger on the PPG; show the waveform
   and the quality card react. (20 s)
3. Longitudinal: the fingerprint table with baseline, deviation in SD,
   persistence. (20 s)
4. Ultrasound + Fusion: import a good image (gate passes), then a 100x100 crop
   (gate refuses with reasons) and show UNKNOWN features plus provenance tags
   and missing modalities. (40 s)
5. Reporting: one-page summary, HTML report, QR; scan it and show the payload
   is only a random token. (25 s)
6. Close with the limits sentence: fallback equation, pending validation, no
   diagnosis. (5 s)

### 14.3 Question bank: answer plus where in the code

| Question | Short answer | Open this |
|---|---|---|
| Does it diagnose PCOS? | No; risk tendency plus longitudinal context; diagnosis needs a clinician | risk_engine.py docstring |
| Where does the number come from? | Nine domain scores in one logistic equation with weights in the source | risk_engine.py `_risk_from_scores` |
| Why trust the pulse detection? | DC block, smoothing, refractory peak detection, median IBI cleaning, CRC on every packet | ppg.py, packet_parser.py |
| What happens with bad data? | The decision layer withholds the number; banner instead of a guess | validation/sqi.py |
| How is personalisation done? | 5-minute calibration to median/MAD/percentiles, gradual updates with a 3.5-sigma outlier guard | personalization.py |
| How do you avoid reacting to noise? | Persistence (3+ points), slope, quality gates; single readings never alert | change_detector.py |
| What does the ultrasound module do? | Quality gate then structured features; image-derived anatomy UNKNOWN until a validated dataset exists | ultrasound_cv.py |
| How is leakage avoided? | Patient-level splits only; schema validator enforces it | ultrasound_cv.py `patient_split` |
| Is the QR safe? | Payload is a random token; resolves locally; expires | qr_encoder.py, history_store.py tokens |
| Does it measure hormones? | No; hormone values are illustration only, excluded from the score | risk_engine.py docstring, registry.py |
| Why these weights? | Research priors in a transparent fallback; ablation and a pilot must replace them | risk_engine.py header, validation/ablation.py |
| What is your accuracy? | No wearable accuracy exists yet; the 0.959 AUC is a clinical-variable cohort result, labelled as such | model_status.py, models/README.md |
| Causation vs correlation? | Never claimed; "temporally associated with" only; OBSERVED/ASSOCIATED/UNKNOWN | what_changed.py, care_plan.py |
| Can it run offline? | Fully; local SQLite, no cloud; QR encoder has zero dependencies | history_store.py, qr_encoder.py |
| What breaks first in the field? | Motion artifacts and sensor contact; that is exactly what the quality layer reports | quality.py, sqi.py |
| Biggest weakness? | No validated longitudinal dataset yet; everything unproven is labelled PENDING | V8_1_BUILD_SPECIFICATION.md |

### 14.4 Numbers worth memorising

20 Hz packets; 25 fields; 115200 baud; CRC is an 8-bit XOR; baseline 300 s and
60 samples; withhold thresholds SQI 0.40, confidence 25, CI width 65; change
thresholds |z| 2 and 3 with 3 persistent points; risk categories 25/50/75;
bootstrap 250 draws; 124 tests; 22 database tables; ten tabs; three boards
supported (Mega hub, Nano pod, ESP8266 bridge).
