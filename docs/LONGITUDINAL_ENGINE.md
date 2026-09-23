# LONGITUDINAL ENGINE - V8.3 (Heart of System)

## Philosophy

**The system learns what is normal for an individual first, then looks for persistent deviations from that personal baseline.**

Do not make system dependent only on population averages.

**Concept:**
```
ONE ABNORMAL READING → weak signal
REPEATED CHANGE → stronger signal
MULTIPLE RELATED FEATURES CHANGING → multimodal signal
PERSISTENT CHANGE + GOOD DATA QUALITY → higher-confidence research signal
```

## Implements

- Rolling windows: short 24h, medium 72h, long 168h (7 days)
- Persistence detection: trailing consecutive out-of-band points >=3, persistence hours
- Trend detection: slope per day over recent 12 points, direction increasing/decreasing/stable, strength via R^2
- Change-point detection: CUSUM-like, rolling mean comparison, shift >2*std
- Recovery detection: max_z_early > alert and latest_z < 0.5*max_early → recovery_progress 0..1
- Missing-data handling: insufficient data → missing kind, not normal
- Confidence scoring: base 0.30 + 0.12*min(persistence,6) + 0.15*min(n/60,1) * quality_factor (0.8+0.2*mean_q) * baseline_factor (0.5+0.5*baseline_conf) → min 0.95

## Metrics Tracked

Default: hr_bpm, resting_hr_bpm, rmssd_ms, skin_temp_c, activity_level, sleep_duration_h, circadian_stability_index, stress_index

## Baseline Reference

If personal baseline available: median and std from baseline, confidence from baseline
Else: earliest stable quarter of series (never whole window, so drifted series cannot hide own drift) - median and robust MAD scale

Robust scale: MAD *1.4826, floor 0.02*|median|

## Series Extraction

From FeatureVector history: ts, vals, q (signal_quality)
Filters None, non-finite, conversion errors

## Persistence

Trailing consecutive |z| > Z_NORMAL (2.0) from end of series
Counts points and hours (timestamp difference)

## Quality Gate

Mean quality over window and tail quality (recent out-of-band) must >=0.5, else insufficient
Tail quality = mean quality of last persistence points (min 1)

## Trend Analysis

Tail_n = min(slope_window 12, n)
x_hours = (tail_ts - tail_ts[0])/3600
slope_per_hour via polyfit, *24 → per day
Direction: >0.8 increasing, <-0.8 decreasing, else stable
Strength: corr^2

## Change-Point Detection

Window = max(5, n//4)
For i in window to n-window step window:
  before = values[i-window:i], after = values[i:i+window]
  If |mean_after - mean_before| >2*std_before → change point at timestamp i

## Recovery Detection

If len(z) <6: no recovery
Half = n//2, max_z_early = max(|z|[:half]), latest_z = |z|[-1]
If max_z_early > Z_ALERT (3.0) and latest_z <0.5*max_z_early → recovering, progress 1 - latest/max_early

## Classification

```
if recovering and max_z_recent > alert: recovery
elif z_latest <= Z_NORMAL:
  if max_z_recent > alert: recovery
  else normal
elif not quality_ok: insufficient
else:
  direction = 1 if latest>median else -1
  moving_away = slope_per_day * direction >0
  if persistence >= persist_points and moving_away and |slope|>=progressive_slope: progressive
  elif persistence >= persist_points: persistent
  else single
```

## Finalize

Alerts = persistent, progressive, recovery, single
Insufficient = insufficient
If alerts: overall deviation, contributors list, summary with change detected, multimodal if >=2 metrics, persistence_score mean persistence, confidence_breakdown persistence/data_quality/n_metrics
If insufficient: insufficient_quality, summary improve sensor contact
Else if recovery_metrics: recovery, recovery_detected True, summary returning toward baseline
Else normal, no persistent change

## Example Report

```
per_metric:
  hr_bpm: kind persistent, latest 78 vs baseline 68 (+14%, |z|=2.8), slope +0.15/day, persistence 12 pts (~36h), confidence 0.75, trend increasing strength 0.68, change_points [ts1, ts2]
overall_kind: deviation
summary: Change detected: hr_bpm +14% from baseline, persistent (12 points); rmssd_ms -25% from baseline, persistent (10 points). Research pattern detection - not diagnosis.
contributors: ["hr_bpm (persistent, +14%)", "rmssd_ms (persistent, -25%)"]
data_quality: 0.85
n_windows: 200
multimodal_signal: True
multimodal_metrics: ["hr_bpm", "rmssd_ms"]
persistence_score: 11.0
recovery_detected: False
confidence_breakdown: {persistence: 0.8, data_quality: 0.85, n_metrics: 0.22}
```

## Testing Scenarios

- Stable baseline: persistence low, overall normal/recovery → LOW CHANGE SIGNAL
- Gradual: deviation, persistence >0 → EARLY CHANGE SIGNAL
- Persistent: deviation, multimodal True, persistence high → PERSISTENT MULTIMODAL SIGNAL
- Temporary: recovery after brief disturbance → TEMPORARY EVENT
- Sensor failure: quality low, not interpreted as physiological → LOW SENSOR CONFIDENCE
- Recovery: recovery_detected True → RECOVERY TREND

## Why Heart?

All disease modules consume longitudinal report or shared features derived from it. Single reading never triggers high-confidence signal. Persistent multimodal with good quality does.

## Backward Compatibility

Alias ChangeDetector = LongitudinalEngine, so V8.1 code still works.
