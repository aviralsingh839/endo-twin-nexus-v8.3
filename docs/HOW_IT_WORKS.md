# HOW IT WORKS - CHRONO-TWIN NEXUS V8.3

## Complete Journey

```
SENSOR
→ SIGNAL
→ FEATURE
→ BASELINE
→ LONGITUDINAL CHANGE
→ SHARED REPRESENTATION
→ DISEASE MODULE
→ FUSION
→ EXPLANATION
→ REPORT
```

---

## 1. SENSOR

**Wearable Pod (Nano):**
- Generic Analog Pulse Sensor PPG (single-channel analog waveform): single analog pulse waveform, 50 Hz, pulse waveform, HR, HRV, pulse amplitude, SpO2 unavailable with analog pulse sensor
- MPU6050 IMU: ax, ay, az, gx, gy, gz, 50 Hz, motion index, activity level
- DS18B20: skin temperature, 1 Hz
- Optional GSR: galvanic skin response, 10 Hz
- Streams 20 Hz `$CP2` packets: `$CP2,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc`

**Mega Hub:**
- All pod sensors + ECG (periodic checkpoints), microphone, FSR, light, BME280 environment, OLED, LEDs, buzzer, buttons
- In relay mode forwards pod stream

**Quality at Source:**
- Status bits: PPG finger absent, PPG saturated, MPU error, DS18B20 error, GSR saturated, I2C error, low quality, ECG leads off, etc.

---

## 2. SIGNAL → Quality Control

Every reading gets quality metadata:
```json
{
  "value": 72,
  "quality": 0.91,
  "source": "Generic Analog Pulse Sensor",
  "timestamp": "...",
  "artifact": false,
  "artifact_type": null,
  "reason": ""
}
```

**Detects:**
- Missing data (None, NaN)
- Impossible values (HR 35-210, temp 20-42°C skin, GSR 0-1023, IR 0-262143)
- Flatline (5+ identical values)
- Excessive noise (z > 5)
- Motion artifacts (motion_index > 1.5)
- Packet corruption (XOR CRC mismatch)
- Stale data (>6s old)

**Result:**
- Bad data must not silently become model input
- Low quality lowers confidence, does not crash app
- Critical failure (2+ critical sensors failed) triggers banner

---

## 3. FEATURE

**Signal Processing:**
- PPG: DC blocker (r=0.97), exponential smoother (alpha=0.35), peak detection with refractory period (60/MAX_HR), HRV time domain (RMSSD, SDNN, pNN50)
- IMU: motion index, activity level, low_activity_risk
- GSR: tonic, phasic per minute
- Temperature: skin_temp, slope per min
- ECG: HR, RMSSD, quality (when available)

**FeatureVector (real-time):**
- hr_bpm, resting_hr_bpm, rmssd_ms, sdnn_ms, pnn50, pulse amplitude
- motion_index, activity_level, low_activity_risk
- skin_temp_c, temp_slope
- gsr_tonic, gsr_phasic
- stress_index, acute_stress, chronic_stress, autonomic_imbalance
- sleep_status, sleep_probability, sleep_duration_h, sleep_regularity, circadian_stability, circadian_disruption
- signal_quality, baseline_completeness, baseline_available, zscores
- quality_per_feature, shared_features

**Quality = mean over PRESENT sensors only** - optional channels never drag score down when absent.

---

## 4. BASELINE - What is Normal for THIS Person

**Improvements over V8.1:**
- mean, median, std, MAD, p05, p95, p25, p75, count, min_obs_days
- rolling median, rolling std (14-day window, EWMA alpha=0.05)
- confidence (count, days, quality)
- last_updated
- hour_of_day_mean, day_of_week_mean (circadian context)

**Capture:**
- Needs min 60 samples, 5 min calm data, good quality (>0.5)
- Outlier guard: |z| > 3.5 does NOT move baseline
- Saves to `data/baselines/personal_baseline_v8_3.json`

**Comparison:**
```
CURRENT VALUE vs PERSONAL BASELINE
Example: HRV baseline 62 ms, current 48 ms, deviation -22.6%
But NOT immediately pathological - consider duration, repeated obs, quality, context, other features
```

**Status:**
- normal (|z| < 1.5)
- mild_deviation (1.5-2.5)
- moderate_deviation (2.5-3.5)
- significant_deviation (>3.5)

**Is Stable When:** days_covered >= 3 and confidence >= 0.5

---

## 5. LONGITUDINAL CHANGE - Heart of V8.3

**Implements:**
- Rolling windows: short 24h, medium 72h, long 168h (7 days)
- Persistence detection: trailing consecutive out-of-band points >=3
- Trend detection: slope per day over recent 12 points, direction increasing/decreasing/stable, strength via R^2
- Change-point detection: CUSUM-like, rolling mean comparison, shift >2*std
- Recovery detection: max_z_early > alert and latest_z < 0.5*max_early → recovery_progress 0..1
- Missing-data handling: insufficient data → missing kind, not normal
- Confidence scoring: base 0.30 + 0.12*min(persistence,6) + 0.15*min(n/60,1) * quality_factor * baseline_factor

**Kinds:**
- normal: within personal range
- single: one abnormal reading
- persistent: sustained offset held for several points
- progressive: trend still moving away from baseline
- recovery: previously deviated, now returning
- insufficient: apparent deviation but quality too low
- missing: insufficient data

**Concept:**
```
ONE ABNORMAL READING → weak signal
REPEATED CHANGE → stronger signal
MULTIPLE RELATED FEATURES CHANGING → multimodal signal
PERSISTENT CHANGE + GOOD DATA QUALITY → higher-confidence research signal
```

**Overall:**
- Alerts when persistent/progressive
- Multimodal when >=2 metrics changing
- Recovery when previously abnormal returns

---

## 6. SHARED PHYSIOLOGICAL REPRESENTATION

**Common feature layer disease modules consume:**

```python
shared_features = {
  heart_rate,
  resting_heart_rate,
  hrv_rmssd,
  hrv_sdnn,
  activity_level,
  motion_index,
  low_activity_risk,
  sleep_duration_h,
  sleep_regularity,
  sleep_timing_h,
  sleep_probability,
  circadian_stability,
  circadian_disruption,
  day_night_activity_ratio,
  skin_temp_c,
  temperature_trend_c_per_day,
  temperature_rhythm_disruption,
  gsr_tonic,
  stress_index,
  autonomic_imbalance,
  recovery_score,
  baseline_deviations: {hr_bpm: z, rmssd: z, ...},
  trend_features: {hr_24h_change_pct, ...},
  sensor_quality: {hr: q, hrv: q, ...},
  overall_quality,
  provenance
}
```

**Avoids duplicating signal-processing code in every disease model.**

**Built from:**
- FeatureVector + baseline_engine + history
- Trends: last 24h vs previous 24h
- Day/night ratio: day activity / night activity
- Recovery score: 0.6*HRV + 0.4*HR inverse

---

## 7. DISEASE MODULE

**Consistent API:**

```python
class DiseaseModule:
  name
  version
  required_features: List[str]
  optional_features: List[str]
  predict(shared, clinical, ultrasound, history) -> DiseaseModuleResult
  explain(result) -> str
  confidence(shared, result) -> float  # based on coverage + quality
  limitations() -> str
```

**Returns structured:**

```json
{
  "module": "sleep",
  "signal": "circadian_deviation",
  "level": "moderate",
  "confidence": 0.72,
  "data_quality": 0.85,
  "clinical_status": "research_only",
  "clinical_validation": "NOT ESTABLISHED",
  "drivers": [{"domain": "sleep_regularity", "score": 65, "description": "..."}],
  "explanation": "...",
  "provenance": {"wearable": 0.6, "longitudinal": 0.3},
  "limitations": "Research-only...",
  "extra": {}
}
```

**Never returns "DISEASE DETECTED"**

---

## 8. MULTIMODAL FUSION

**Combines:**
- wearable physiology (MEASURED)
- longitudinal changes (MODEL-INFERRED)
- clinical variables (PATIENT-REPORTED)
- ultrasound features (CLINICALLY-ENTERED or IMAGE-DERIVED)
- manually entered measurements (USER-ENTERED)

**Preserves provenance - WHERE DID INFO COME FROM?**

**Example PCOS signal:**
```
40% clinical variables
25% longitudinal physiology
20% ultrasound-derived features
15% metabolic information
```
Values only used if actually generated by implemented model, not hard-coded fake percentages.

**Group weights:**
```
weight = mean quality of present values in group * coverage (fraction present)
Missing groups get zero weight, cannot drag estimate down, but absence visible and lowers overall confidence
```

**Separates:**
- MODEL CONFIDENCE (based on coverage + quality)
- DATA QUALITY (mean quality of present features)
- CLINICAL VALIDATION (NOT ESTABLISHED for all V8.3 modules)

**FusionResult:**
- overall_signals: elevated/high modules
- confidence_breakdown: model_confidence, data_quality, clinical_validation, fusion_coverage, fusion_quality
- explanation: primary signal + quality + validation + not diagnosis
- recommendations: improve quality, discuss with clinician, module-specific lifestyle

---

## 9. EXPLANATION ENGINE

**Every risk signal explains main contributing factors:**

```
Persistent change detected
Drivers:
- resting HR increased from personal baseline (+18%, |z|=2.8)
- HRV decreased from baseline (-35%, |z|=2.5)
- sleep regularity decreased (45% vs baseline 85%)
- activity decreased (-25%)

These changes are not specific to one disease and should not be interpreted as a diagnosis.
Data quality: 0.85, Persistence: 3.2, Confidence: 0.72
```

**Explains:**
- Shared features (core vitals, sleep/circadian, stress/autonomic, baseline deviations, trends)
- Longitudinal (per-metric phrase, trend direction, multimodal, recovery)
- Disease module (module, signal, level, confidence, drivers, baseline deviations, limitations)
- Fusion (provenance, elevated signals, recommendations)

---

## 10. REPORT

**Includes:**
- Subject ID (anonymous)
- Observation period
- Sensor data available
- Data quality
- Personal baseline (median, p05-p95, std, confidence, days)
- Longitudinal changes
- Disease-module signals
- Contributing factors
- Ultrasound if available
- Clinical inputs if available
- Limitations
- Recommended next step: "Discuss relevant findings with qualified healthcare professional"

**No medical diagnosis**

**Formats:**
- Text in UI
- Save to file
- Future: PDF, HTML longitudinal report

---

## 11. Why This Matters

**Traditional:** RAW DATA → DISEASE MODEL → DISEASE SCORE (population averages, single reading, black box)

**V8.3:** RAW DATA → QUALITY CONTROL → SIGNAL PROCESSING → FEATURE EXTRACTION → PERSONAL BASELINE → LONGITUDINAL CHANGE → SHARED REPRESENTATION → DISEASE MODULES → FUSION → EXPLANATION → REPORT (personal, persistent, explainable, honest)

**Judge Pitch (2-3 min):**
1. Wearable collects signals
2. System cleans and checks quality
3. Builds personal baseline
4. Compares new against baseline
5. Looks for persistent changes, not one abnormal reading
6. Shared representation feeds several research modules
7. Clinical and ultrasound add context
8. Fusion combines evidence with provenance
9. Explains which factors produced signal
10. Final result is research-oriented signal, NOT diagnosis

**Innovation:** "We are not trying to make one sensor diagnose every disease. We are building one longitudinal physiological framework that can learn an individual's baseline and support multiple disease-specific research modules."


## V8.8 Analog Pulse Sensor migration

The current wearable build can use the generic analog Pulse Sensor module shown in the project hardware reference image instead of the MAX3010x optical PPG. The module is a single-channel analog pulse waveform source: SIG connects to an ADC-capable GPIO, VCC to the sensor's supported supply, and GND to common ground. ENDO-TWIN keeps the existing $CP2 transport so the rest of the desktop/BLE pipeline remains compatible. The primary waveform is carried in the existing `ir` slot for transport compatibility and is explicitly marked as `ANALOG_PULSE`/status bit 12. The `red` field is `-1` because there is no optical red channel.

The processing layer continues to support heart-rate and pulse-timing/HRV-style analysis from the waveform, with motion-aware quality scoring. It must not estimate SpO2 from this single-channel analog sensor. This hardware is suitable for an educational research prototype, not for diagnosis or clinical measurement.
