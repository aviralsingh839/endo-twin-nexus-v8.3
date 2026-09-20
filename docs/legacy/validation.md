# Validation Plan and Current Status (V8.1)

Validation in this project has two halves: the checks that run on every session
inside the app (signal quality, agreement, withholding), and the scientific
validation laboratory in `src/validation/` that answers "how would we prove
this works" with code that is ready for real data. Everything that needs
labelled human data is PENDING, and the interface says so.

## 1. What runs today, on every session

| Check | Where | What it does |
|---|---|---|
| Per-sensor signal quality | src/utils/quality.py, src/validation/sqi.py | PPG amplitude, saturation, motion penalty; ECG interval cleanliness; presence checks; completeness score |
| Withhold layer | src/validation/sqi.py | Refuses to show the risk number below SQI 0.40, confidence 25, CI width 65, or without HRV |
| Packet integrity | src/serial_io/packet_parser.py | Field counts and XOR CRC on every line; corrupt lines dropped and counted |
| Baseline integrity | src/models/personalization.py | Minimum 60 samples, quality gate, 3.5-scale outlier guard on updates |
| Change gating | src/models/change_detector.py | Persistence, slope and quality gates before any statement is shown |
| Ultrasound quality gate | src/models/ultrasound_cv.py | Decodability, resolution and blur checks before any feature work |
| Provenance accounting | src/models/fusion.py | Every value tagged MEASURED / PATIENT-REPORTED / CLINICALLY-ENTERED / IMAGE-DERIVED / MODEL-INFERRED / UNKNOWN with quality and source |
| Test suite | tests/ | 124 tests including QR round-trips, Reed-Solomon syndromes, split integrity and the withholding behaviours above |

## 2. Sensor validation protocol (bench, no human subjects needed)

| Measurement | Reference | Acceptance I use at the table |
|---|---|---|
| Heart rate | Finger-counted pulse and a commercial pulse oximeter at rest | Within about 3 bpm at rest |
| SpO2 estimate | Commercial pulse oximeter | Labelled educational; compare but never present as medical |
| Skin temperature | Digital thermometer against the probe in still air | Within about 0.5 C after settling |
| Motion index | Quiet rest vs walking vs shaking | Clear separation of the three states |
| GSR | Rest vs mental arithmetic | Visible tonic rise or phasic bursts on myself only |
| ECG checkpoint | PPG-derived HR in the same window | Within about 3 bpm, quality above 0.5 |
| Sleep estimate | Sleep diary over several nights | Direction-level agreement only |

These are bench checks of the acquisition chain. They validate sensors, not the
risk model.

## 3. The validation laboratory (src/validation)

| Module | Purpose |
|---|---|
| sqi.py | Signal quality indices and the confidence-based decision layer |
| agreement.py | Reference-device agreement (Bland-Altman style comparison of dashboard values against a reference device) |
| calibration.py | Brier score, expected calibration error, reliability diagrams for any connected model |
| leakage.py | Detects feature/label leakage and train-test overlap, including time-based leakage |
| losocv.py | Leave-one-subject-out cross-validation harness |
| ablation.py | Per-modality ablation: how much each sensor group contributes to the estimate |
| repeatability.py | Repeated-measurement reproducibility on the same subject |
| prospective.py | Prospective mode: score now, compare against later reference labels |
| longitudinal_experiment.py | The Model A-E comparison: A snapshot clinical only, B clinical + cycle, C + longitudinal wearable, D + ultrasound-derived, E full multimodal |
| store.py | Structured ground-truth and reference-data capture with provenance |
| versioning.py | Reproducible model-state snapshots so a result can be traced to exact code and weights |
| report.py | Assembles all of the above into one validation report |

The laboratory is wired and unit-tested on synthetic data. Its outputs on real
human data do not exist yet.

## 4. Model validation that is defined but PENDING

| Model | Dataset needed | Method defined in code |
|---|---|---|
| Clinical-variable risk baseline | Bundled public Kaggle cohort (already run) | Patient-level 5-fold CV; ROC-AUC 0.959, AP 0.932 on that cohort; reported as a development result only |
| PPG quality | PhysioNet wrist-PPG-during-exercise (already run) | Subject-level CV; AUC about 0.62; used at 40% weight |
| Stress | WESAD | Leave-one-subject-out or stratified CV |
| Sleep | BIDSleep or MESA epoch exports | Epoch accuracy, F1, Cohen's kappa |
| Hormone priors | mcPHASES, MMASH, NHANES | MAE/RMSE where direct labels exist, otherwise uncertainty only |
| Live risk engine | Labelled longitudinal wearable + PCOS data (does not exist publicly) | Model A-E with patient-level splits; AUROC, AUPRC, sensitivity, specificity, F1, calibration with CIs |
| Ultrasound features | Validated, labelled, patient-grouped ultrasound images (not included, none invented) | Patient-level train/validation/test; feature value over Model C tested by Model D vs C |

## 5. Rules I will not break

- Train, validation and test splits happen at patient level; one patient's
  images or rows never appear in two partitions. The schema validator enforces
  this for any future ultrasound dataset.
- Synthetic and demo rows are excluded from real analysis and exports.
- No accuracy number is quoted unless it was measured on the stated dataset
  with the stated protocol; the model status registry records which is which.
- Temporal association is never written as causation in any output string.
- Any human data collection requires consent, adult or clinician oversight and
  institutional approval before the first sample.

## 6. The experiment that would move this from prototype to evidence

1. Ethics-approved pilot, roughly 20-30 participants over 8-12 weeks: wearable
   plus cycle and symptom logs plus periodic clinical assessment with ultrasound
   where clinically indicated.
2. Model A-E on the pilot data with patient-level splits and full metrics with
   confidence intervals.
3. Ultrasound feature validation on the collected labelled images.
4. Per-sensor ablation to justify the hardware list.
5. QR interoperability on several phone models and a calibration audit with
   reliability diagrams.

Until steps 2 to 4 produce real results, every claim in this project stays
labelled NOT YET VALIDATED, and the interface keeps saying so.
