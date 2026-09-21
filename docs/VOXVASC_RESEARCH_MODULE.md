# VoxVasc Research Module

## Purpose

VoxVasc is an optional experimental voice-acoustic modality within CHRONO-PCOS. It is intended for research exploration of voice-derived physiological features alongside the broader ENDO-TWIN representation.

## Current implementation

The active implementation lives in:
- src/models/voice_vasc_model.py
- src/ui/voice_vasc_tab.py

The original prototype files remain under chrono_pcos_project V8/ for historical traceability.

## Acquisition

The current desktop UI supports WAV input. A consistent sustained-vowel protocol should be used for research comparisons, such as a short sustained “aaa” recording in a quiet environment with consistent microphone placement.

## Features

The current implementation extracts:
- fundamental-frequency / pitch estimate
- microphone RMS energy
- an experimental low-pitch acoustic proxy index

Jitter is not currently estimated and is explicitly unavailable.

## Interpretation boundary

VoxVasc is not:
- a testosterone measurement
- an androgen assay
- a vascular measurement
- a PCOS diagnostic test
- a clinically validated probability
- a substitute for clinical inputs, physiological sensors, or validated imaging

The experimental index is deliberately not represented as a medical probability and is not allowed to override measured or clinically entered evidence.

## Provenance

Audio-derived features must be labelled as voice/acoustic derived data. Failed pitch extraction or insufficient audio remains UNKNOWN / UNAVAILABLE.

## Future work

Before any research fusion weight is introduced, the project needs a defined dataset, participant-level splits, reproducible preprocessing, confounder analysis, validation protocol, uncertainty analysis, and independent evaluation. No clinical performance claim should be added without such evidence.
