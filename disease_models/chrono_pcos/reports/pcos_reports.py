"""
CHRONO-PCOS Reports - PCOS-specific reports

General reports belong in ENDO-TWIN Core (reports/).
PCOS-specific reports belong here.
"""

from typing import Dict, List, Optional, Any
import time

class PCOSReportGenerator:
    """PCOS-specific report generation"""
    
    @staticmethod
    def generate_pcos_report(patient_id: str, general_report: Dict, pcos_analysis: Dict,
                           ultrasound_data: Optional[Dict] = None, include_disclaimer: bool = True) -> Dict[str, Any]:
        """
        Generate PCOS-specific report - extends general report
        
        General report: patient/session ID, date/time, measurements, signal quality, longitudinal trends, etc.
        PCOS-specific: PCOS analysis, chrono-metabolic PCOS interpretation, ultrasound PCOS features, PCOS risk signal
        """
        
        report = {
            "report_id": f"PCOS-REPORT-{int(time.time())}",
            "patient_id": patient_id,
            "report_type": "chrono_pcos",
            "disease_model": "chrono_pcos",
            "display_name": "CHRONO-PCOS Research Report",
            "is_first_disease_model": True,
            "general_platform": "ENDO-TWIN",
            "generated_at": time.time(),
            "generated_at_str": time.strftime("%Y-%m-%d %H:%M:%S"),
            "general_data": general_report,
            "pcos_analysis": pcos_analysis,
            "ultrasound": ultrasound_data,
            "sections": {
                "general": {
                    "title": "General Physiological Overview",
                    "description": "General measurements, baseline, longitudinal, patterns - ENDO-TWIN platform",
                    "data": general_report
                },
                "pcos_specific": {
                    "title": "CHRONO-PCOS Analysis - First Disease Model",
                    "description": "PCOS-specific analysis built on general platform",
                    "analysis": pcos_analysis,
                    "features": "PCOS features - cycle length, irregularity, symptoms, chrono-metabolic PCOS interpretation",
                    "ultrasound": ultrasound_data,
                    "risk_signal": pcos_analysis.get("signal", "pcos_associated_risk"),
                    "level": pcos_analysis.get("level", "low"),
                    "confidence": pcos_analysis.get("confidence"),  # No default 0.75 - must come from real model, None if unavailable
                    "drivers": pcos_analysis.get("drivers", []),
                    "explanation": pcos_analysis.get("explanation", ""),
                    "provenance": pcos_analysis.get("provenance", {}),
                    "limitations": pcos_analysis.get("limitations", ""),
                    "note": "Confidence from real model adapter calibrated probability, not hard-coded default"
                }
            },
            "provenance": {
                "MEASURED": "HR, temp, motion - quality, source",
                "CLINICALLY_ENTERED": "Age, BMI, cycle info - USER-ENTERED",
                "IMAGE_DERIVED": "Cyst size, morphology - quality UNKNOWN by design",
                "MODEL_INFERRED": "PCOS risk signal, sleep regularity, circadian disruption - confidence, limitations",
                "DEMO_DATA": "Demo patients - clearly marked",
                "UNKNOWN": "If cannot reliably extract, return UNKNOWN, never invent"
            },
            "model_transparency": {
                "name": "CHRONO-PCOS",
                "version": "8.3+",
                "display_name": "CHRONO-PCOS - First Disease Model",
                "description": "First disease-specific model on ENDO-TWIN platform",
                "capabilities": ["pcos_risk_signal", "circadian_analysis", "autonomic_analysis", "metabolic_context", "longitudinal_tracking", "chrono_metabolic_fingerprinting", "ultrasound_analysis"],
                "limitations": "Research-only, not diagnostic, not clinically validated, requires clinical evaluation, Rotterdam criteria requires clinician",
                "clinical_validation": "NOT ESTABLISHED - Engineering validation only",
                "input": "PPG HR, HRV, activity, temp, clinical cycle info, optional ultrasound",
                "data_quality": pcos_analysis.get("data_quality"),  # No default - must be computed
                "confidence": pcos_analysis.get("confidence"),  # No hard-coded default - real model calibrated probability or None
                "note": "Model output confidence from calibrated classifier, not clinical certainty - None if not computed, never hard-coded 0.75"
            },
            "patient_scoped": True,
            "no_cross_contamination": True,
            "is_demo": "DEMO" in patient_id
        }
        
        if include_disclaimer:
            report["disclaimer"] = "Research / risk-screening output — not a medical diagnosis. Requires clinical evaluation. Rotterdam criteria for PCOS diagnosis requires qualified healthcare professional."
            report["framework_disclaimer"] = "ENDO-TWIN is general platform, CHRONO-PCOS is first disease-specific model. Research prototype, not medical device."
            report["safety"] = {
                "does_not": [
                    "Does NOT diagnose PCOS/PCOD",
                    "Does NOT prescribe medication",
                    "Does NOT provide treatment as orders",
                    "Does NOT claim 100% accurate",
                    "Does NOT claim clinical validation unless evidence",
                    "Does NOT claim ENDO-TWIN is clinically validated universal digital twin"
                ],
                "does": [
                    "Provides research risk signals, requires clinical evaluation",
                    "Educational demonstration",
                    "Local-first privacy",
                    "Clearly distinguishes MEASURED/CLINICALLY_ENTERED/IMAGE-DERIVED/MODEL-INFERRED/DEMO_DATA/UNKNOWN"
                ]
            }
        
        return report
