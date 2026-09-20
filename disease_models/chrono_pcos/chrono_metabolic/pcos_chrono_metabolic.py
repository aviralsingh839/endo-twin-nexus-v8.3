"""
CHRONO-PCOS Chrono-Metabolic - PCOS-specific interpretation

General chrono-metabolic fingerprinting belongs in ENDO-TWIN Core (core/chrono_metabolic/).
PCOS-specific interpretation belongs here.

General: circadian, autonomic, variability, activity, temp, metabolic, longitudinal
PCOS-specific: how these patterns relate to PCOS research signals
"""

from typing import Dict, List, Optional, Any

class PCOSChronoMetabolic:
    """PCOS-specific chrono-metabolic interpretation"""
    
    @staticmethod
    def interpret_for_pcos(general_fingerprint: Dict, clinical_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Interpret general chrono-metabolic fingerprint for PCOS research
        
        General fingerprint: circadian + autonomic + variability + activity + temp + metabolic + longitudinal
        PCOS interpretation: how these relate to PCOS-associated patterns - experimental research, not diagnosis
        """
        
        circadian = general_fingerprint.get("circadian", {})
        autonomic = general_fingerprint.get("autonomic", {})
        metabolic = general_fingerprint.get("metabolic", {})
        longitudinal = general_fingerprint.get("longitudinal", {})
        
        # PCOS-specific interpretation - experimental research
        pcos_signals = []
        
        # Circadian disruption may be associated with PCOS - research hypothesis
        if circadian.get("disruption", 0) > 50:
            pcos_signals.append({
                "domain": "circadian",
                "signal": "circadian_disruption_may_be_associated_with_pcos_research",
                "value": circadian.get("disruption"),
                "provenance": "MODEL-INFERRED",
                "category": "experimental_research",
                "limitations": "Research hypothesis, not clinical, sleep-wake from wrist PPG model-inferred not polysomnography"
            })
        
        # Autonomic dysregulation
        if autonomic.get("dysregulation", 0) > 50:
            pcos_signals.append({
                "domain": "autonomic",
                "signal": "autonomic_dysregulation_research_signal",
                "value": autonomic.get("dysregulation"),
                "provenance": "MODEL-INFERRED",
                "category": "experimental_research",
                "explainability": "RMSSD reflects parasympathetic activity, lower values may indicate autonomic dysregulation research signal"
            })
        
        # Metabolic context
        if metabolic.get("risk_signal", 0) > 50:
            pcos_signals.append({
                "domain": "metabolic",
                "signal": "metabolic_context_may_relate_to_pcos_research",
                "value": metabolic.get("risk_signal"),
                "provenance": "MODEL-INFERRED",
                "category": "experimental_research",
                "limitations": "Experimental research signal not clinical metabolic measurement, not diabetes diagnosis"
            })
        
        # Longitudinal - persistent deviation
        if longitudinal.get("persistent_deviation", False):
            pcos_signals.append({
                "domain": "longitudinal",
                "signal": "persistent_deviation_from_personal_baseline",
                "value": longitudinal.get("deviation_score", 0),
                "provenance": "MODEL-INFERRED",
                "category": "experimental_research",
                "description": "Personal baseline → time series → change → persistence → recovery → context"
            })
        
        return {
            "general_fingerprint": general_fingerprint,
            "pcos_interpretation": {
                "signals": pcos_signals,
                "count": len(pcos_signals),
                "description": "Chrono-metabolic patterns interpreted for PCOS research - experimental, not diagnosis",
                "conceptual_flow": "Circadian + Autonomic + Metabolic context + Longitudinal patterns → Chrono-Metabolic representation → PCOS research interpretation",
                "provenance": "MODEL-INFERRED from MEASURED",
                "category": "pcos_specific + experimental_research",
                "limitations": "Experimental research, not diagnosis, requires validation, chrono-metabolic fingerprint experimental",
                "disclaimer": "Research / experimental chrono-metabolic fingerprint - not a medical diagnosis, requires clinical evaluation"
            },
            "general_note": "General chrono-metabolic fingerprinting belongs in ENDO-TWIN Core, PCOS interpretation belongs in CHRONO-PCOS disease model"
        }
    
    @staticmethod
    def get_pcos_chrono_metabolic_definitions() -> List[Dict]:
        return [
            {
                "name": "circadian_pcos",
                "display_name": "Circadian PCOS Research Signal",
                "description": "Circadian disruption may be associated with PCOS - research hypothesis",
                "category": "pcos_specific + experimental_research",
                "provenance": "MODEL-INFERRED",
                "limitations": "Sleep-wake from wrist PPG model-inferred not polysomnography"
            },
            {
                "name": "autonomic_pcos",
                "display_name": "Autonomic PCOS Research Signal",
                "description": "Autonomic dysregulation research signal - HRV RMSSD + GSR",
                "category": "pcos_specific + experimental_research",
                "provenance": "MODEL-INFERRED",
                "explainability": "RMSSD reflects parasympathetic"
            },
            {
                "name": "metabolic_pcos",
                "display_name": "Metabolic PCOS Context",
                "description": "Metabolic context may relate to PCOS - multimodal HR, HRV, activity, temp, GSR hypothesized",
                "category": "pcos_specific + experimental_research",
                "provenance": "MODEL-INFERRED",
                "limitations": "Experimental, not clinical metabolic measurement"
            }
        ]
