# Scientific Model Notes (V8.1, as implemented)

## Boundary

This project estimates an educational PCOS-related risk tendency. It does not
diagnose PCOS. Hormone-like values in the app are model-estimated illustrations
and never enter the headline score. Ultrasound-derived anatomical values are
UNKNOWN until a validated labelled dataset exists. Every formula below is
quoted from the source file that implements it.

## Physiological pathways the model leans on

All statements are association-level, consistent with current PCOS research.

### Sleep and circadian disruption, HPA load, glucose regulation

Poor sleep and circadian misalignment are associated with increased
sympathetic and HPA-axis load and with worse glucose regulation. In PCOS
research, circadian disruption has been associated with reduced sleep
efficiency, altered melatonin timing and elevated evening cortisol. The model
uses rhythm *stability* (cosinor fit quality and regularity of activity, sleep
and light), never a claim about cortisol itself.

### Insulin resistance, hyperinsulinaemia and androgen tendency

Insulin resistance raises insulin demand; hyperinsulinaemia is associated with
increased ovarian androgen production and reduced hepatic SHBG, raising free
androgen tendency. The model's metabolic domain is a tendency proxy built from
manual glucose, BMI, blood pressure, sleep, stress, circadian disruption and
activity. It is not a measurement of insulin.

### Autonomic balance

Vagal activity modulates beat-to-beat intervals; low resting RMSSD is
associated in research with stress load and autonomic imbalance, and PCOS
cohorts report autonomic tendency differences. The autonomic domain uses HR,
HRV and GSR features.

### Progesterone and temperature

After ovulation, progesterone is thermogenic and raises basal temperature by a
few tenths of a degree through the luteal phase. Skin temperature is noisier
than core or basal temperature, so the model uses only the *rhythm* of skin
temperature as a circadian-domain input and reports limited confidence. It is
not an ovulation test.

### Activity and inflammation proxy

Low activity and adiposity feed insulin resistance and inflammation tendency.
The model uses IMU-derived inactivity directly and an inflammation proxy only
inside the metabolic domain, labelled as a proxy.

## Core mathematics

### Logistic transform

sigmoid(x) = 1 / (1 + exp(-x)); every 0-100 score in the project is
100*sigmoid(linear combination of z-scores or normalised inputs).

### Signal-level formulas (src/signal_processing)

- HR: 60 / median(clean IBI). Clean IBI: within [60/210, 60/35] s, then within
  25% of the median.
- RMSSD = sqrt(mean(diff(IBI)^2)) * 1000; SDNN = std(IBI, ddof=1) * 1000;
  pNN50 = 100 * mean(|diff| > 50 ms).
- SpO2 (educational): r = (red_AC/red_DC)/(ir_AC/ir_DC); SpO2 = 110 - 25*r,
  clamped 70-100.
- Motion index = RMS(|a| - 1g) + 0.3*RMS(jerk) + 0.002*RMS(gyro);
  activity = clamp((motion - 0.02)/0.40*100).
- Temperature slope: linear fit over 5 min in C/min; stability = clamp(1 - std/0.5).
- GSR phasic rate: first differences above median + 4*MAD, per minute;
  tonic z against the personal resting baseline (scale 80).
- PPG quality heuristic = clamp(0.55*amp + 0.30*saturation + 0.15*motion),
  amp = clamp((p95-p5 - 100)/1500), zero when DC < 5000 counts; blended 60/40
  with the trained wrist-PPG quality model when its joblib file exists.

### Sleep, stress, metabolic, circadian (src/models, src/features)

- Sleep probability = sigmoid(-1.8*motion_z - 0.7*hr_z + 0.9*rmssd_z
  + 0.4*temp_stable - 0.4*gsr_z + 0.6*time_prior), time_prior 1 between 22:00
  and 07:00, sharpened 70/30 by a user-entered sleep window.
- Acute stress = 100*sigmoid(0.9*hr_z - 1.1*rmssd_z + 0.9*phasic_z + 0.5*gsr_z
  - 0.5*max(motion_z, 0) + 0.3*temp_drop_z), multiplied by 0.65 when activity
  exceeds 45 (exercise gate). Autonomic imbalance =
  100*sigmoid(-1.0*rmssd_z + 0.5*hr_z + 0.4*gsr_z). Stress index =
  0.65*acute + 0.35*chronic.
- Insulin-resistance tendency = 100*sigmoid(-2.0 + 0.025*(glucose - 90)
  + 0.045*(BMI - 23) + 0.004*bp_risk + 0.008*sleep_risk + 0.007*stress
  + 0.005*circadian_disruption - 0.006*activity).
- Circadian stability = 100*(0.20*hr_R2 + 0.10*hrv_R2 + 0.25*temp_R2
  + 0.10*gsr_R2 + 0.15*activity_regularity + 0.15*sleep_regularity
  + 0.05*light_regularity), each R2 from a 24 h cosinor least-squares fit;
  disruption = 100 - stability.

### Personal baseline and change (src/models/personalization, change_detector)

- Baseline per metric: median, MAD, mean, std, p05, p95 from a calibration
  window of at least 60 samples (default 300 s).
- Robust scale = max(1.4826*MAD, 0.02*|median|); robust z = (x - median)/scale.
- Gradual update: EWMA alpha 0.05 on rolling median/MAD (600-point window);
  observations whose rolling median is more than 3.5 scale units from the
  baseline are rejected.
- Change classes: |z| < 2 normal; |z| > 3 deviation; 3+ consecutive out-of-band
  points persistent; slope at least 1 scale unit per day away progressive;
  return into band recovery; window quality under 0.5 insufficient (no alert).

### Headline risk (src/models/risk_engine)

Nine domain scores d in 0-100 (cycle, metabolic, glucose, bp,
stress_autonomic, sleep, circadian, temperature_rhythm, low_activity):

z = -3.0 + 1.20*cycle/100 + 0.90*metabolic/100 + 0.60*autonomic/100
  + 0.50*sleep/100 + 0.50*circadian/100 + 0.35*temperature/100
  + 0.35*glucose/100 + 0.30*activity/100 + 0.20*bp/100
risk = clamp(100*sigmoid(z), 0, 100)

Cycle score from self-report only: |length - 28|/20*100, plus 60 for reported
irregularity (10 if reported regular), plus (days_since_last_period - 35)/25*100
above 35 days; neutral 15 when nothing is reported.

Interval: 250 bootstrap draws, each domain perturbed by N(0, sigma) with
sigma = 5 + (1 - signal_quality)*14; CI = 5th and 95th percentiles.

Confidence = 100*(0.30*data_quality + 0.20*baseline_available +
0.20*clamp(1 - CI_width/80) + 0.20*feature_completeness +
0.10*cycle_completeness).

Categories: <25 low, <50 watch, <75 elevated, else high.

### Withhold layer (src/validation/sqi)

The risk number is withheld when overall SQI < 0.40, or confidence < 25, or CI
width > 65, or HRV is missing. The UI shows a banner instead.

### Fusion (src/models/fusion)

Group weight = coverage * mean quality of present values in the group; missing
groups get weight 0 and are listed as missing. Provenance classes: MEASURED,
PATIENT-REPORTED, CLINICALLY-ENTERED, IMAGE-DERIVED, MODEL-INFERRED, UNKNOWN.

### Ultrasound gate (src/models/ultrasound_cv)

Accept only if the image decodes, width >= 320, height >= 240 and the blur
score (gradient-magnitude variance on a downscaled grayscale image) >= 1.5.
Otherwise the fixed verdict "ULTRASOUND QUALITY INSUFFICIENT FOR ANALYSIS".
Image-derived anatomy stays UNKNOWN with confidence 0.0 until a validated,
labelled, patient-grouped dataset exists; clinician entries pass through with
CLINICALLY-ENTERED provenance.

## Model inventory and status

| Model | Artifact | Status |
|---|---|---|
| Clinical-variable PCOS risk baseline | models/pcos_risk_model.joblib | Trained on the bundled public cohort, patient-level 5-fold CV ROC-AUC 0.959 on that cohort; research reference, not the live engine |
| PPG motion-artifact quality | models/ppg_quality_model.joblib | Trained on wrist-PPG-during-exercise, subject-level CV AUC about 0.62; blended at 40% into the heuristic |
| Live risk engine | none | Transparent fallback equation (above), labelled FALLBACK in the Evidence Center |
| Stress and sleep estimators | none | Transparent formulas only; the optional joblib blends were removed in the V8.1 cleanup |
| Ultrasound feature extractor | none | PENDING DATA by design |

## Validation display

The Validation tab and the weekly report show signal quality, feature
completeness, model agreement, CI width and the contributors that moved the
estimate, so a reader can always see how much of the number is data and how
much is model.
