# ENDO-TWIN 48-Hour Wearable Research Protocol

## Purpose

Evaluate the ENDO-TWIN research pipeline on one participant over approximately 48 hours while preserving the distinction between real observations, derived features, research-model outputs and missing data.

This is a research-prototype procedure, not a diagnostic protocol.

## Participant workflow

1. Create an anonymous participant in the Doctor Desktop Patients workspace.
2. Start a 48-hour research study.
3. Register/identify the prototype wearable.
4. Start a wear episode.
5. Connect the wearable transport.
6. Allow normal daily activity to be recorded.
7. Before bathing/showering, use **Remove for bathing**.
8. The current wear episode is closed and a `WEARABLE_REMOVED_BATHING` event is stored.
9. Do not generate measurements during the removal gap.
10. After bathing, reconnect the wearable and start a new wear episode.
11. Repeat this lifecycle whenever the device is removed.
12. At the end of approximately 48 hours, end the study.
13. Export the complete patient package.
14. Import the package into the Doctor Desktop if acquisition occurred on Android.

## Data lifecycle

Wearable -> BLE / USB / Wi-Fi transport -> raw packet -> validation -> local storage -> board-specific decoder -> signal quality -> feature extraction -> personal baseline -> longitudinal context -> research modules -> explanation -> report.

Raw packets are retained on the phone until the exact board/protocol decoder is configured. The desktop database can accept those packets during synchronization.

## Local database boundary

The Android patient app stores its own local Room database.

The Doctor Desktop stores its own local SQLite database.

Synchronization is deliberate and patient-scoped through an exported package. There is no automatic cloud upload in this workflow.

## Removal and missing data

A bathing interval is a real missing-data interval. It is not a zero-value interval and must not be interpolated into an apparent measurement history without an explicit quality penalty and provenance.

## Two-day analysis

A two-day study can be used to:
- inspect acquisition quality
- characterize short-term physiological patterns
- initialize/update a personal baseline
- exercise longitudinal and multimodal software
- produce a research-only screening signal when the actual model inputs are available

A two-day wearable record must not be presented as proof of clinical diagnostic accuracy for PCOS or another disease.

## Personalization / self-learning

The automatic self-learning layer updates the participant-specific baseline from valid observations.

Disease-model retraining is separate. A disease model is not silently rewritten from one participant's data. Candidate training requires explicit research labels, participant-level split/leakage checks and independent validation before promotion.

## Recommended data review after the study

Review:
- total wear-session duration
- removal/reconnection events
- raw packet count
- per-channel quality
- missing intervals
- feature coverage
- personal baseline completeness
- longitudinal change
- model input availability
- model version and limitations
- provenance of every reported value
