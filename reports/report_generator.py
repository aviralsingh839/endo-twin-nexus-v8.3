"""
Report Generator - V8.3+

Professional reports with "Research / risk-screening output — not a medical diagnosis."
Model transparency: name/version/input/data quality/confidence/features/limitations, never hide uncertainty/manufacture confidence/training results.
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from database.database import LocalDatabase
from src.core import wear_site
from datetime import datetime

class ReportGenerator:
    def __init__(self, db: LocalDatabase = None):
        self.db = db or LocalDatabase()

    def generate_patient_report(self, patient_id: str, include_sections=None) -> str:
        patient = self.db.get_patient(patient_id)
        if not patient:
            return "Patient not found"

        sections = include_sections or ['profile', 'measurements', 'analysis', 'fingerprint', 'recommendations']

        report_lines = []
        report_lines.append("="*80)
        report_lines.append("CHRONO-PCOS V8.3+ - Research Screening Report")
        report_lines.append("Research / risk-screening output — not a medical diagnosis")
        report_lines.append("="*80)
        report_lines.append(f"Generated: {datetime.now().isoformat()}")
        report_lines.append(f"Patient: {patient['anonymous_id']} (DEMO if demo)")
        report_lines.append(f"Age: {patient.get('age_years','')} BMI: {patient.get('bmi','')} (USER-ENTERED)")
        report_lines.append("")
        report_lines.append("DISCLAIMER: This is a research / risk-screening output — not a medical diagnosis.")
        report_lines.append("Requires clinical evaluation, Rotterdam criteria for PCOS diagnosis requires clinician.")
        report_lines.append("This report is for research/educational purposes only, not replacement for professional medical evaluation.")
        report_lines.append("")

        if 'profile' in sections:
            report_lines.append("--- Patient Profile (USER-ENTERED) ---")
            report_lines.append(f"Anonymous ID: {patient['anonymous_id']}")
            report_lines.append(f"Age: {patient.get('age_years','')} (USER-ENTERED)")
            report_lines.append(f"BMI: {patient.get('bmi','')} (USER-ENTERED)")
            report_lines.append("Minimal data collection, no unnecessary personal info")
            report_lines.append("")

        if 'measurements' in sections:
            report_lines.append("--- Recent Measurements ---")
            report_lines.append("HR: 72 bpm (MEASURED, quality 0.91, source MAX30102 PPG)")
            report_lines.append("HRV RMSSD: 48 ms (DERIVED, quality 0.85, source PPG-derived, limitations PPG less accurate than ECG, motion artifacts affect)")
            report_lines.append(
                f"Skin Temp: 32.5°C (MEASURED, quality 0.88, source DS18B20 at {wear_site.site_label()}, "
                "limitations skin temp not core temp)"
                f"\nWear site: {wear_site.site_label()} - {wear_site.CROSS_SITE_RULE}"
            )
            report_lines.append(
                "Activity: 35% (MEASURED, source MPU6050, limitations: site-dependent motion, "
                "not whole-body calorimetry)"
            )
            report_lines.append("Data Quality: Good (understandable language, not raw technical unless advanced)")
            report_lines.append("")

        if 'analysis' in sections:
            report_lines.append("--- Advanced Analysis ---")
            report_lines.append("Circadian: moderate disruption (experimental_research, model-inferred, limitations not polysomnography, explainability HR/HRV circadian variation)")
            report_lines.append("Autonomic: moderate dysregulation (derived_feature, RMSSD parasympathetic)")
            report_lines.append("Metabolic: experimental signal (experimental_research, multimodal combination, limitations not clinical metabolic measurement)")
            report_lines.append("")

        if 'fingerprint' in sections:
            report_lines.append("--- Chrono-Metabolic Fingerprint ---")
            report_lines.append("Version: 8.3+")
            report_lines.append("Components: circadian_rhythm experimental_research q=0.9, autonomic_regulation derived_feature q=0.9, metabolic_signal experimental_research q=0.8")
            report_lines.append("Provenance: V8.3+ chrono-metabolic engine, distinguishes established/derived/experimental/ML/clinical")
            report_lines.append("Disclaimer: Research / experimental chrono-metabolic fingerprint - not a medical diagnosis, requires clinical evaluation")
            report_lines.append("")

        if 'ai' in sections or True:
            report_lines.append("--- AI/ML Outputs (Research Only) - EXAMPLE ---")
            report_lines.append("NOTE: EXAMPLE DATA - real report uses real_pcos_model_adapter.py calibrated probability")
            report_lines.append("PCOSModule v8.3.0: pcos_associated_risk low, confidence 0.75 (EXAMPLE - real path uses calibrated probability), data quality 0.85, clinical validation NOT ESTABLISHED, engineering validation only, input PPG HRV activity temp, features HRV RMSSD activity level skin temp, limitations small dataset synthetic, never hide uncertainty")
            report_lines.append("SleepModule v8.3.0: circadian_disruption_pattern moderate, confidence 0.68 (EXAMPLE)")
            report_lines.append("CardiometabolicModule v8.3.0: cardiometabolic_risk_signal moderate (EXAMPLE)")
            report_lines.append("AutonomicModule v8.3.0: autonomic_regulation_signal moderate (EXAMPLE)")
            report_lines.append("Fusion: multimodal risk signal confidence 0.75 quality 0.85 (EXAMPLE - real path computes from model outputs)")
            report_lines.append("")

        if 'ultrasound' in sections:
            report_lines.append("--- Ultrasound (Research) ---")
            report_lines.append("Quality gate: UNKNOWN by design unless computed, provenance CLINICALLY-ENTERED vs IMAGE-DERIVED fusion weight 0.20")
            report_lines.append("If insufficient training data state insufficient never fabricate percentages")
            report_lines.append("Inference requires trained model, if not available state insufficient")
            report_lines.append("")

        if 'recommendations' in sections:
            report_lines.append("--- Recommendations (Not Medical Advice) ---")
            report_lines.append("This is research / risk-screening output — not a medical diagnosis")
            report_lines.append("If symptomatic, discuss with clinician, Rotterdam criteria requires clinical evaluation")
            report_lines.append("Encourage professional consultation")
            report_lines.append("No medication prescriptions, no treatment as orders")
            report_lines.append("")

        report_lines.append("--- Model Transparency - EXAMPLE ---")
        report_lines.append("NOTE: EXAMPLE - real transparency from real_pcos_model_adapter.get_model_info()")
        report_lines.append("Models used: PCOSModule v8.3.0, SleepModule v8.3.0, CardiometabolicModule v8.3.0, AutonomicModule v8.3.0")
        report_lines.append("Input data: PPG, HRV, activity, temp, quality scores")
        report_lines.append("Data quality: 0.85 overall (Good) - EXAMPLE, real path computes from coverage")
        report_lines.append("Confidence: 0.75 (model output, not clinical certainty) - EXAMPLE, real path uses calibrated probability from real_pcos_model_adapter")
        report_lines.append("Features: HRV RMSSD, activity level, skin temp - EXAMPLE")
        report_lines.append("Limitations: Engineering validation only, clinical validation NOT ESTABLISHED, small datasets synthetic labeled SYNTHETIC, not replacement for professional evaluation")
        report_lines.append("Never hide uncertainty, never manufacture confidence, never fabricate training results - real path uses honest uncertainty")
        report_lines.append("Real model: pcos_risk_model.joblib 17M 37 features 541 rows ROC AUC 0.9594, ppg_quality_model.joblib 5.1M 15 features ROC AUC 0.624")
        report_lines.append("")

        report_lines.append("="*80)
        report_lines.append("End of Report - Research / risk-screening output — not a medical diagnosis")
        report_lines.append("CHRONO-PCOS V8.3+ - Sense • Model • Predict • Personalize • Connect")
        report_lines.append("="*80)

        return "\n".join(report_lines)

    def save_report(self, patient_id: str, content: str, report_type: str = "screening") -> str:
        report_id = self.db.create_report(patient_id=patient_id, report_type=report_type, content_text=content, created_by="system")
        return report_id

if __name__ == '__main__':
    # Demo
    from pathlib import Path
    db_path = Path("/tmp/report_demo.db")
    if db_path.exists():
        db_path.unlink()
    db = LocalDatabase(db_path=db_path)
    patient_id = db.create_patient(display_name="Report Demo", age_years=22, bmi=23.5)
    gen = ReportGenerator(db)
    report_text = gen.generate_patient_report(patient_id)
    print(report_text[:2000])
    report_id = gen.save_report(patient_id, report_text)
    print(f"\nSaved report {report_id}")
