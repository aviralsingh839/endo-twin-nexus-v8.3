"""
ENDO-TWIN CORE - Research Framework for Personalized Physiological Modelling

CHRONO-PCOS is the first disease-specific implementation running on ENDO-TWIN-ready architecture.

This is NOT a clinically validated universal human digital twin.
It is a research framework / prototype for personalized physiological modelling.

Architecture:
ENDO-TWIN CORE
  |
  +-- DATA LAYER (patients, sensor_sessions, measurements, features, clinical, ultrasound, models, reports, audit)
  +-- TWIN ENGINE (identity, physiology, baseline, longitudinal, provenance, uncertainty)
  +-- AI/ML LAYER (models, registry, training, inference, explainability)

DISEASE-SPECIFIC MODELS:
  CHRONO-PCOS (first implementation)
  Future: other endocrine/metabolic research modules

Common infrastructure:
- patient identity
- personal baseline
- longitudinal timeline
- physiological state
- multimodal data
- provenance MEASURED/CLINICALLY ENTERED/IMAGE-DERIVED/MODEL-INFERRED/DEMO/UNKNOWN
- uncertainty
- model registry + versioning
- reports
- audit history
- patient/doctor access
- future disease-specific models
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if sys.path[0] != str(PROJECT_ROOT):
    if str(PROJECT_ROOT) in sys.path:
        sys.path.remove(str(PROJECT_ROOT))
    sys.path.insert(0, str(PROJECT_ROOT))
src_path = str(PROJECT_ROOT / "src")
if src_path in sys.path:
    sys.path.remove(src_path)

from .twin import EndoTwinCore

__all__ = ['EndoTwinCore']
