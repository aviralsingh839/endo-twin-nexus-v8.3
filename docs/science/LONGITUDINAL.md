# LONGITUDINAL MODELLING - ENDO-TWIN V8.3+

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED

## Temporal Priority

Support: session, hour, day, week, month, cycle, long-term trajectory

Include: change from baseline, persistence, recovery, variability, missingness, context

Do not infer trends from inadequate data.

## Implementation

- src/core/longitudinal_engine.py, src/endo_twin/longitudinal/general_longitudinal.py, endo_twin/longitudinal/longitudinal_engine.py
- Session-level hourly daily weekly monthly cycle-level, meaningful deviations not isolated numbers, 6 scenarios stable LOW CHANGE gradual EARLY CHANGE persistent PERSISTENT MULTIMODAL temporary TEMPORARY EVENT sensor failure LOW SENSOR CONFIDENCE recovery RECOVERY TREND
- Core scientific story NOT today's number, it is personal baseline → time series → change → persistence → recovery → context
- Daily, weekly, monthly longitudinal where data supports never fabricate trends
- Personal baseline → time series → change → persistence → recovery → context

## Example

- HR: 70 → 72 → 71 bpm stable baseline LOW CHANGE SIGNAL
- HRV RMSSD: 50 → 48 → 45 ms gradual deviation EARLY CHANGE SIGNAL
- Activity: 40% → 35% → 30% persistent deviation PERSISTENT MULTIMODAL SIGNAL

## Benchmark

- Digital Patient: Forecasting future trajectories evolution physiological state, GNN forecasting clinically relevant endpoints, probabilistic simulations future trajectories
- HDT: Time-series forecasting 7-day future wellness LSTM, weekly/monthly trends anomalies habit impact, what-if simulation
- Heartwood: Weekly summary daily averages vs goals progress rings week-over-week trends, detail views full charts statistics recent records

Our implementation matches: personal baseline → time series → change → persistence → recovery → context, similar forecasting and weekly summary.

## Performance

- Part of core 22.2 ms fast
- Rolling windows incremental, not recompute entire history
