# 07 - Ultrasound Module - V8.3+

## Overview
Preserves V8.3 ultrasound pipeline, no invented accuracy.

## Pipeline
1. Loading: image path, format check, size check
2. Preprocessing: resize, normalize, denoise
3. Quality Checks: blur, exposure, anatomy visibility, quality score UNKNOWN by design unless computed, provenance CLINICALLY-ENTERED vs IMAGE-DERIVED
4. Segmentation: cyst detection, morphology, if model available
5. Inference: requires trained model, if insufficient training data state insufficient, never fabricate percentages, confidence None unless computed
6. Visualization: overlay, confidence map
7. Storage: ultrasound_records table, patient_id, image_path, cyst_size_mm, volume_cc, morphology, quality, source, confidence, label

## Quality Gate
UNKNOWN by design, provenance distinction.

## Training
If training: need clinical ultrasound dataset, not synthetic as clinical, never label synthetic as clinical, never fabricate patient records.

## Evaluation
- If model exists: evaluate on held-out clinical data
- If not: state model accuracy not established
- No 100% accurate claims

## Storage
- Local SQLite ultrasound_records
- Image path, not BLOB for performance
- Label REAL vs SYNTHETIC

## Safety
Ultrasound analysis is research, not diagnosis, requires clinical evaluation, Rotterdam criteria requires ultrasound + clinical.

## Why?
Scientific integrity, avoid fake medical claims.
