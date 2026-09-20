"""
CHRONO-PCOS - First Disease-Specific Model on ENDO-TWIN Platform

ENDO-TWIN is the general platform.
CHRONO-PCOS is its first disease-specific model.

This module contains PCOS-specific functionality that was previously
mixed with general functionality. General functionality belongs in
ENDO-TWIN Core (src/endo_twin/).

PCOS-Specific:
- PCOS features
- PCOS risk logic
- PCOS model
- PCOS-specific ultrasound analysis
- Chrono-Metabolic PCOS interpretation
- PCOS-specific reports

General (belongs in ENDO-TWIN Core):
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
"""

from .model.chrono_pcos_model import ChronoPCOSDiseaseModel, get_chrono_pcos_model
from .manifest import CHRONO_PCOS_MANIFEST

__all__ = ["ChronoPCOSDiseaseModel", "get_chrono_pcos_model", "CHRONO_PCOS_MANIFEST"]
