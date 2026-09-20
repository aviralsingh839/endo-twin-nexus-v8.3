"""
CHRONO-PCOS Features - PCOS-specific features

General features belong in ENDO-TWIN Core (src/endo_twin/features/)
PCOS-specific features belong here.

Examples:
- cycle_length, cycle_irregularity, cycle history
- PCOS-related symptoms: irregular_cycle, weight_gain, hirsutism, acne
- PCOS risk factors: BMI, age, etc. combined with physiological signals
- Chrono-metabolic PCOS interpretation
"""

from typing import Dict, List, Optional, Any

class PCOSFeatures:
    """PCOS-specific features - extends general physiological features"""
    
    @staticmethod
    def extract_cycle_features(cycle_events: List[Dict]) -> Dict[str, Any]:
        """Extract PCOS-relevant cycle features"""
        if not cycle_events:
            return {"cycle_length": None, "irregularity": "unknown", "is_pcos_relevant": False}
        
        lengths = [e.get("cycle_length_days") for e in cycle_events if e.get("cycle_length_days")]
        if not lengths:
            return {"cycle_length": None, "irregularity": "unknown", "is_pcos_relevant": False}
        
        avg_length = sum(lengths) / len(lengths)
        # Irregular if varies >7 days or length <21 or >35
        irregular = len(set(lengths)) > 2 or avg_length < 21 or avg_length > 35
        
        return {
            "cycle_length": avg_length,
            "cycle_length_history": lengths,
            "irregularity": "irregular" if irregular else "regular",
            "is_pcos_relevant": irregular or avg_length > 35,
            "provenance": "CLINICALLY_ENTERED",
            "category": "pcos_specific",
            "description": "Cycle length and irregularity - Rotterdam criteria requires clinical evaluation"
        }
    
    @staticmethod
    def extract_symptom_features(symptoms: List[Dict]) -> Dict[str, Any]:
        """Extract PCOS-relevant symptoms"""
        pcos_symptoms = ["irregular_cycle", "weight_gain", "hirsutism", "acne", "hair_loss", "infertility"]
        found = []
        for symptom in symptoms:
            symptom_type = symptom.get("symptom_type", symptom.get("type", ""))
            if symptom_type in pcos_symptoms:
                found.append(symptom_type)
        
        return {
            "pcos_symptoms_found": found,
            "count": len(found),
            "is_pcos_relevant": len(found) >= 2,
            "provenance": "CLINICALLY_ENTERED",
            "category": "pcos_specific",
            "description": "PCOS-related symptoms - not diagnosis, requires clinical evaluation"
        }
    
    @staticmethod
    def get_pcos_feature_definitions() -> List[Dict]:
        """Get definitions of PCOS-specific features"""
        return [
            {
                "name": "cycle_length",
                "display_name": "Cycle Length",
                "description": "Average cycle length in days - PCOS may have >35 days or irregular",
                "unit": "days",
                "category": "pcos_specific",
                "provenance": "CLINICALLY_ENTERED",
                "limitations": "USER-ENTERED, not MEASURED, requires clinical evaluation"
            },
            {
                "name": "cycle_irregularity",
                "display_name": "Cycle Irregularity",
                "description": "Regular vs irregular cycles",
                "category": "pcos_specific",
                "provenance": "CLINICALLY_ENTERED",
                "limitations": "Subjective, requires history"
            },
            {
                "name": "pcos_symptoms",
                "display_name": "PCOS Symptoms",
                "description": "Irregular cycle, weight gain, hirsutism, acne, etc.",
                "category": "pcos_specific",
                "provenance": "CLINICALLY_ENTERED",
                "limitations": "Symptoms alone not diagnostic"
            },
            {
                "name": "chrono_metabolic_pcos",
                "display_name": "Chrono-Metabolic PCOS Interpretation",
                "description": "Circadian + autonomic + metabolic + longitudinal patterns interpreted for PCOS research - experimental",
                "category": "pcos_specific",
                "provenance": "MODEL-INFERRED",
                "limitations": "Experimental research, not diagnosis, requires validation"
            }
        ]
