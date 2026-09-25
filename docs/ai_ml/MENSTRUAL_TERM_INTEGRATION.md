# Menstrual-term integration — ENDO-TWIN NEXUS

Date: 2026-09-25

## Source analysis

The handwritten research note supplied for this iteration contains a section on
symptoms reported around periods and a comparison of similar versus
dissimilar observations.

Only clearly legible, domain-relevant phrases were normalized. Ambiguous
phrases were excluded rather than guessed.

Normalized terminology includes:
- higher flow during initial days
- lower back pain
- lower abdominal/pelvic pain
- 5–6 day bleeding duration
- food cravings
- irritability
- sleep-cycle change
- feeling uneasy
- white discharge
- usual lifestyle / no alteration
- mental-health disturbance

Implementation:
disease_models/chrono_pcos/features/menstrual_terms.py

## Why these terms are not directly added to the current PCOS classifier

The current real clinical PCOS model was trained on 37 clinical variables.
Its feature schema does not contain this menstrual-context vocabulary. Adding
new terms at inference time without retraining on matching labelled examples
would create feature mismatch and invalidate the model input contract.

Therefore the terms are implemented as a research feature schema first.

- menstrual_context_v1: normalized term observations
- menstrual_context_comparison_v1: similar-vs-dissimilar descriptive comparison
- model_ready: false until a future labelled patient-level dataset exists
- unknown/ambiguous language is retained as unmapped text rather than guessed

## Training

The existing PCOS clinical training script remains the source of truth for the
37-feature clinical baseline. CI now retrains that model from the repository's
public CSV and verifies the resulting joblib bundle on every pull request.

The workflow does not pretend that handwritten terms are labelled training data.

To train the current clinical baseline locally:

python "chrono_pcos_project V8/scripts/train_pcos_risk_model.py" --csv data/public/PCOS_data.csv --out "chrono_pcos_project V8/models/pcos_risk_model.joblib"

Patient-level grouped cross-validation and the existing pregnancy-screen
leakage exclusions are preserved.

## Doctor workstation changes

The Doctor PC entry point now stays on the enhanced workstation rather than
silently jumping to the legacy src/ui/main_window.py.

The workstation data services are database-backed:
- patient history reads sessions, symptoms, cycles, reports, and notes
- session viewer reads PPG/HRV/GSR/motion/temperature/quality tables
- longitudinal comparison uses supplied database sessions
- archive actually updates the local patient record
- authorized doctor access is checked before opening/archiving/history
- absent data returns UNKNOWN / NOT_RUN rather than fabricated example values

This removes the main mock-data paths that previously displayed static HR, HRV,
temperature, confidence, artifact counts, and longitudinal values.

## Safety / scope

This is a research and risk-screening prototype, not a diagnostic system.
Menstrual terms are observations and vocabulary features; they are not
diagnostic criteria by themselves. No model metric or confidence is created
from the handwritten note.
