# CHRONO-METABOLIC FINGERPRINTING - ENDO-TWIN V8.3+

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED

## Preserve Original Concept

Domains:

Circadian:
- sleep timing
- activity timing
- temperature rhythm
- regularity

Autonomic:
- HR
- HRV
- recovery
- stress-response indicators

Metabolic context:
- glucose where available
- activity
- sleep
- temperature
- clinical observations

Coordination:
Analyze temporal relationships between these dimensions.

Clearly identify: OBSERVED, DERIVED, MODEL-INFERRED, EXPERIMENTAL

## Implementation

- disease_models/chrono_pcos/chrono_metabolic/pcos_chrono_metabolic.py, src/core/chrono_metabolic (if exists)
- Combines circadian autonomic variability activity temp metabolic longitudinal into fingerprint with provenance explainability
- Distinguishes established/derived/experimental/ML/clinical, explainability
- Experimental research not diagnosis

## Example

- Circadian: moderate disruption experimental_research q=0.9 explainability HR/HRV circadian variation
- Autonomic: moderate dysregulation derived_feature q=0.9 explainability RMSSD parasympathetic
- Metabolic: experimental signal experimental_research q=0.8 limitations not clinical metabolic measurement
- Fingerprint: Version 8.3+ components circadian_rhythm experimental_research q=0.9 autonomic_regulation derived_feature q=0.9 metabolic_signal experimental_research q=0.8 provenance V8.3+ chrono-metabolic engine distinguishes established/derived/experimental/ML/clinical disclaimer Research / experimental chrono-metabolic fingerprint - not a medical diagnosis requires clinical evaluation

## Benchmark

- Digital Patient: Graph representation nodes tissues/pathways → GNN forecasting endpoints, graph representation solves multiscale modelling with AI
- HDT: Multimodal sensing physiological/context fusion, emotion+context+behavior fusion, lab+wearable+lifestyle fusion
- Our: Circadian + autonomic + variability + activity + temp + metabolic + longitudinal → fingerprint with provenance explainability - matches multimodal fusion

## Safety

- Experimental research not diagnosis
- Clearly distinguish OBSERVED DERIVED MODEL-INFERRED EXPERIMENTAL
- Do not turn hypotheses into established medical claims
- Disclaimer: Research / experimental chrono-metabolic fingerprint - not a medical diagnosis requires clinical evaluation
