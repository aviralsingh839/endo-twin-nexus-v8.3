# Disease Model System - Plugin Architecture

## Overview

ENDO-TWIN is general platform, CHRONO-PCOS is first disease-specific model.

Disease models are plugins that implement `DiseaseModel` interface.

Core does NOT depend directly on CHRONO-PCOS.

## Interface

```python
class DiseaseModel:
    name: str
    version: str
    display_name: str
    description: str
    required_features: List[str]
    
    def validate_input(features, clinical_data, imaging_data) -> {valid, missing, warnings, quality}
    def analyze(features, clinical_data, imaging_data, longitudinal_data, baseline_data, patient_id) -> DiseaseModelResult
    def explain(result) -> str
    def generate_report(result, include_disclaimer) -> Dict
    def get_uncertainty(result) -> Dict
    def get_limitations() -> str
```

## Implementation

### Location

```
disease_models/
└── chrono_pcos/
    ├── __init__.py
    ├── manifest.py - CHRONO_PCOS_MANIFEST
    ├── model/
    │   └── chrono_pcos_model.py - ChronoPCOSDiseaseModel implements DiseaseModel
    ├── features/
    │   └── pcos_features.py - PCOS-specific features
    ├── ultrasound/
    │   └── pcos_ultrasound.py - PCOS-specific ultrasound
    ├── chrono_metabolic/
    │   └── pcos_chrono_metabolic.py - PCOS-specific chrono-metabolic interpretation
    ├── reports/
    │   └── pcos_reports.py - PCOS-specific reports
    └── tests/
```

### Manifest

```python
CHRONO_PCOS_MANIFEST = DiseaseModelManifest(
    name="chrono_pcos",
    version="8.3+",
    display_name="CHRONO-PCOS",
    description="PCOS/PCOD risk pre-screening research module - first disease-specific implementation on ENDO-TWIN platform",
    category=Endocrine,
    required_features=["heart_rate", "hrv_rmssd", "activity_level", "skin_temp_c"],
    capabilities=["pcos_risk_signal", "circadian_analysis", "autonomic_analysis", "metabolic_context", ...],
    limitations="Research-only, not diagnostic, Rotterdam criteria requires clinician",
    clinical_validation="NOT ESTABLISHED"
)
```

### Model

```python
class ChronoPCOSDiseaseModel(DiseaseModel):
    @property
    def manifest(self) -> DiseaseModelManifest:
        return CHRONO_PCOS_MANIFEST
    
    def validate_input(...) -> {valid, missing, warnings, quality}
    def analyze(...) -> DiseaseModelResult
```

Preserves original functionality from `src/disease_modules/pcos.py`:

- Original PCOSModule used internally
- Cycle score, domain scores, risk from scores
- Provenance, drivers, explanation
- Converted to general DiseaseModelResult

## Registry

```python
from src.endo_twin.models.model_registry import get_global_registry

registry = get_global_registry()

# Register disease model
registry.register_disease_model(chrono_pcos_model)

# List disease models
registry.list_disease_models()  # [CHRONO-PCOS, Future Model A, Future Model B]

# Analyze with specific model
result = registry.analyze_with_disease_model("chrono_pcos", features, clinical_data, imaging_data, patient_id)

# Get registry info for UI
registry.get_registry_info()
# {
#   "general_models": [...],
#   "disease_models": [{"name": "chrono_pcos", "display_name": "CHRONO-PCOS", ...}],
#   "summary": {"total_general": 6, "total_disease": 3, "first_disease_model": "CHRONO-PCOS"}
# }
```

## General vs PCOS-Specific Separation

### GENERAL (ENDO-TWIN Core)

- patient management
- sensors
- signal acquisition
- signal processing
- feature extraction
- baseline
- longitudinal analysis
- database
- reports
- provenance
- model registry
- uncertainty
- visualization

Location: `src/endo_twin/core/`, `src/endo_twin/physiology/`, `src/endo_twin/baseline/`, etc.

Classes: Patient, Observation, Measurement, SensorReading, Signal, Feature, Baseline, TimelineEvent, LongitudinalSeries, Model, Prediction, Explanation, Uncertainty, Provenance, Report

No PCOS-specific assumptions.

### PCOS-SPECIFIC (CHRONO-PCOS)

- PCOS features: cycle_length, cycle_irregularity, pcos_symptoms, chrono_metabolic_pcos
- PCOS risk logic: cycle score, domain scores, risk from scores
- PCOS model: ChronoPCOSDiseaseModel
- PCOS-specific ultrasound: cyst_size_mm, ovarian_volume_cc, cyst_count - Rotterdam criteria
- Chrono-Metabolic PCOS interpretation: circadian, autonomic, metabolic patterns interpreted for PCOS research
- PCOS-specific reports: extends general report with PCOS analysis

Location: `disease_models/chrono_pcos/`

## Future Models - Extensibility

### TEST 4: Add dummy future disease model possible without rewriting core

```python
from src.endo_twin.models.disease_model_interface import DiseaseModel, DiseaseModelManifest, DiseaseModelCategory

class DummyFutureModel(DiseaseModel):
    @property
    def manifest(self):
        return DiseaseModelManifest(
            name="future_cardio",
            version="0.1.0",
            display_name="Future Cardio Model",
            description="Future cardiometabolic research model - CONCEPT",
            category=DiseaseModelCategory.CARDIOMETABOLIC,
            required_features=["heart_rate"],
            capabilities=["research_signal"],
            limitations="Dummy future model - not implemented"
        )
    
    def validate_input(self, features, clinical_data=None, imaging_data=None):
        return {"valid": True, "missing": [], "warnings": ["Dummy"], "quality": 0.5}
    
    def analyze(self, features, clinical_data=None, imaging_data=None, longitudinal_data=None, baseline_data=None, patient_id="unknown"):
        return DiseaseModelResult(...)

# Register without rewriting core
registry.register_disease_model(DummyFutureModel())
```

No core rewrite needed. Extensible architecture.

## Acceptance Tests

**TEST 2**: Open Disease Models. CHRONO-PCOS appears. PASS = disease-specific module.

**TEST 3**: Disable/remove CHRONO-PCOS temporarily. Main ENDO-TWIN application must still launch and function. PASS = true general architecture.

- Core does NOT depend directly on CHRONO-PCOS
- Disease models are plugins via registry
- General dashboard works without disease models

**TEST 4**: Add dummy future disease model. Possible without rewriting core. PASS = extensible architecture.

- DummyFutureModel implements DiseaseModel interface
- Registered via registry
- No core rewrite

**TEST 5**: Open CHRONO-PCOS. Original useful PCOS functionality must still exist. PASS = migration preserved scientific functionality.

- ChronoPCOSDiseaseModel uses original PCOSModule internally
- Preserved: PCOS features, risk logic, model, ultrasound, chrono-metabolic, reports

## One Sentence

**ENDO-TWIN is the platform; CHRONO-PCOS is its first disease-specific model.**
