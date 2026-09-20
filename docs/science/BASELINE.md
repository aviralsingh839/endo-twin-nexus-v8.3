# PERSONAL BASELINE - ENDO-TWIN V8.3+

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED

## First-Class Component

Support: rolling baseline, robust mean/median, variability, MAD/outlier handling, time-of-day context, baseline age, baseline confidence, drift, missingness

System should answer: What is unusual FOR THIS PERSON? not merely Is this value different from generic reference?

Never fabricate baseline. When insufficient: Insufficient baseline data.

## Implementation

- src/core/personal_baseline.py, src/endo_twin/baseline/general_baseline.py
- Mean, median, std, MAD, rolling, confidence, min obs, circadian context
- Learns what is normal for individual first
- Robust statistics

## Example

- HR baseline: mean 71 bpm median 70 std 2 confidence 0.85 min_obs 10
- HRV baseline: mean 48 ms etc.
- Personal baseline first, then deviation detection

## Performance

- Part of ENDO-TWIN core init + dashboard 22.2 ms fast
- Incremental updates, not recompute entire history
