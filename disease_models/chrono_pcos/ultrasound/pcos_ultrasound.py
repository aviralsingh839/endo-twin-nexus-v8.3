"""
CHRONO-PCOS Ultrasound - PCOS-specific ultrasound analysis

General imaging belongs in ENDO-TWIN Core.
PCOS-specific ultrasound interpretation belongs here.

Pipeline: IMAGE IMPORT → VALIDATION → PREPROCESSING → IMAGE ANALYSIS → FEATURE EXTRACTION → MODEL → UNCERTAINTY → REPORT
Every result labelled IMAGE-DERIVED
Quality gate UNKNOWN by design unless computed
Provenance CLINICALLY-ENTERED vs IMAGE-DERIVED fusion weight 0.20
"""

from typing import Dict, List, Optional, Any
from pathlib import Path

class PCOSUltrasound:
    """PCOS-specific ultrasound analysis"""
    
    @staticmethod
    def analyze_for_pcos(ultrasound_study: Dict) -> Dict[str, Any]:
        """
        Analyze ultrasound for PCOS-related features
        
        Rotterdam criteria: polycystic ovaries on ultrasound requires clinical evaluation
        Not diagnosis by wearable alone
        """
        image_path = ultrasound_study.get("image_path", "")
        quality = ultrasound_study.get("quality", "UNKNOWN")
        
        # Quality gate - UNKNOWN by design unless computed
        if quality == "UNKNOWN" or quality is None:
            return {
                "pcos_relevant": "UNKNOWN",
                "cyst_count": "UNKNOWN",
                "cyst_size_mm": "UNKNOWN",
                "ovarian_volume_cc": "UNKNOWN",
                "morphology": "UNKNOWN",
                "quality": "UNKNOWN",
                "provenance": "IMAGE-DERIVED",
                "confidence": None,
                "limitations": "Quality gate UNKNOWN by design unless computed, inference requires trained model, if insufficient state insufficient never fabricate percentages",
                "disclaimer": "Ultrasound analysis research, not diagnosis, Rotterdam requires ultrasound + clinical"
            }
        
        # If quality available, extract features (if model available)
        cyst_size = ultrasound_study.get("cyst_size_mm")
        volume = ultrasound_study.get("volume_cc")
        morphology = ultrasound_study.get("morphology")
        
        return {
            "pcos_relevant": True if cyst_size and cyst_size < 10 else "UNKNOWN",
            "cyst_count": ultrasound_study.get("cyst_count", "UNKNOWN"),
            "cyst_size_mm": cyst_size or "UNKNOWN",
            "ovarian_volume_cc": volume or "UNKNOWN",
            "morphology": morphology or "UNKNOWN",
            "quality": quality,
            "provenance": "IMAGE-DERIVED",
            "source": "IMAGE-DERIVED",
            "confidence": ultrasound_study.get("confidence"),
            "limitations": "Engineering validation only, clinical validation NOT ESTABLISHED, small datasets",
            "fusion_weight": 0.20,
            "provenance_distinction": "CLINICALLY-ENTERED vs IMAGE-DERIVED",
            "disclaimer": "Ultrasound analysis research, not diagnosis, requires clinical evaluation"
        }
    
    @staticmethod
    def get_pcos_ultrasound_definitions() -> List[Dict]:
        return [
            {
                "name": "cyst_size_mm",
                "display_name": "Cyst Size",
                "description": "Cyst size in mm - PCOS may have many small cysts <10mm",
                "unit": "mm",
                "category": "pcos_specific",
                "provenance": "IMAGE-DERIVED",
                "quality_gate": "UNKNOWN by design unless computed",
                "limitations": "Requires validated model, if insufficient state insufficient"
            },
            {
                "name": "ovarian_volume_cc",
                "display_name": "Ovarian Volume",
                "description": "Ovarian volume in cc - PCOS may have enlarged ovaries",
                "unit": "cc",
                "category": "pcos_specific",
                "provenance": "IMAGE-DERIVED",
                "quality_gate": "UNKNOWN by design unless computed"
            },
            {
                "name": "cyst_count",
                "display_name": "Cyst Count",
                "description": "Number of cysts - Rotterdam: >=12 follicles 2-9mm or volume >10cc",
                "category": "pcos_specific",
                "provenance": "IMAGE-DERIVED",
                "limitations": "Rotterdam criteria requires clinician"
            }
        ]
