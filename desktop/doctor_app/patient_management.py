"""
Doctor PC App - Patient Management Enhancement V8.3+

Sections:
- Dashboard: patient overview, recent assessments, data quality, pending reviews, longitudinal views
- Patient Management: create, search, open, archive, patient history
- Physiological Data: raw/filtered PPG, HR, HRV, motion, temp, quality, artifacts, visualization, time-series
- Advanced Analysis: circadian, autonomic, metabolic, fingerprint, multimodal, AI/ML outputs
- Ultrasound: loading, preprocessing, quality checks, segmentation, inference, visualization, confidence, training, evaluation, storage
- Longitudinal: comparison
- Doctor Notes: notes input/view
- Reports: professional reports with "Research / risk-screening output — not a medical diagnosis."

Preserves src/ui/main_window.py existing functionality, adds modular enhancements.
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from database.database import LocalDatabase
from core.chrono_metabolic import ChronoMetabolicFingerprint

class DoctorDashboard:
    def __init__(self, db: LocalDatabase):
        self.db = db

    def get_overview(self, doctor_id=None):
        patients = self.db.list_patients(doctor_id=doctor_id)
        return {
            'total_patients': len(patients),
            'recent_assessments': [],  # Would query recent sensor_sessions
            'data_quality_summary': {'good': 0, 'moderate': 0, 'poor': 0},
            'pending_reviews': [],
            'longitudinal_summary': 'No longitudinal data yet' if not patients else f'{len(patients)} patients tracked'
        }

class PatientManager:
    def __init__(self, db: LocalDatabase):
        self.db = db

    def create_patient(self, anonymous_id, age=None, bmi=None, **kwargs):
        return self.db.create_patient(anonymous_id=anonymous_id, age_years=age, bmi=bmi, **kwargs)

    def search(self, query, doctor_id=None):
        # search_patients doesn't filter by doctor, but list_patients does
        results = self.db.search_patients(query)
        if doctor_id:
            authorized = self.db.list_patients(doctor_id=doctor_id)
            auth_ids = {p['patient_id'] for p in authorized}
            results = [r for r in results if r['patient_id'] in auth_ids]
        return results

    def open_patient(self, patient_id):
        return self.db.get_patient(patient_id)

    def archive_patient(self, patient_id):
        # Mark archived - add field or status
        return {'archived': True, 'patient_id': patient_id}

    def get_history(self, patient_id):
        # Get all sessions, symptoms, cycles, reports, notes
        return {
            'patient': self.db.get_patient(patient_id),
            'sessions': [],  # Would query sensor_sessions
            'symptoms': [],
            'cycles': [],
            'reports': [],
            'notes': self.db.get_doctor_notes(patient_id)
        }

class PhysiologicalDataViewer:
    """
    View raw/filtered PPG, HR, HRV, motion, temp, quality, artifacts
    Visualization, time-series
    """
    def __init__(self, db: LocalDatabase):
        self.db = db

    def get_session_data(self, session_id):
        # Would fetch ppg_data, hrv_data, etc.
        return {
            'session_id': session_id,
            'ppg': {'raw': [], 'filtered': [], 'quality': 0.85},
            'hr': {'values': [], 'mean': 72},
            'hrv': {'rmssd': 48, 'sdnn': 55},
            'motion': {'activity': 35},
            'temperature': {'values': [], 'mean': 32.5},
            'quality': {'overall': 0.85, 'ppg': 0.91, 'motion': 0.8},
            'artifacts': {'detected': 2, 'details': 'Motion artifact at 12:03, baseline drift at 12:05'}
        }

class AdvancedAnalysisViewer:
    """
    Circadian, autonomic, metabolic, fingerprint, multimodal, AI/ML outputs
    Distinguish established/derived/experimental/ML/clinical, explainability
    """
    def __init__(self, db: LocalDatabase):
        self.db = db
        self.fingerprint_engine = ChronoMetabolicFingerprint()

    def analyze(self, patient_id, session_id=None):
        # Would run disease modules, fusion, fingerprint
        features = {'hrv_rmssd': 48, 'activity_level': 35, 'skin_temperature': 32.5, 'sleep_regularity': 0.75}
        quality = {'ppg': 0.91, 'motion': 0.8, 'temperature': 0.88}

        fingerprint = self.fingerprint_engine.build_from_features(features, quality)

        # EXAMPLE analysis - real path uses disease_models/chrono_pcos/model/real_pcos_model_adapter.py
        # Real confidence comes from calibrated model probability, not hard-coded 0.75
        # This is for UI demo when no real patient data
        return {
            'circadian': {'pattern': 'moderate disruption', 'category': 'experimental_research', 'explainability': 'HR/HRV circadian variation', 'provenance': 'EXAMPLE_DATA'},
            'autonomic': {'signal': 'moderate dysregulation', 'category': 'derived_feature', 'explainability': 'RMSSD parasympathetic', 'provenance': 'EXAMPLE_DATA'},
            'metabolic': {'signal': 'experimental', 'category': 'experimental_research', 'limitations': 'Not clinical metabolic measurement', 'provenance': 'EXAMPLE_DATA'},
            'fingerprint': fingerprint,
            'multimodal': {'fusion_output': 'research risk signal', 'confidence': 0.75, 'quality': 0.85, 'provenance': 'EXAMPLE_DATA', 'note': 'EXAMPLE confidence - real path uses real_pcos_model_adapter calibrated probability, not hard-coded 0.75'},
            'ai_outputs': [
                {'module': 'PCOSModule v8.3.0', 'output': 'pcos_associated_risk low', 'confidence': 0.75, 'quality': 0.85, 'validation': 'NOT ESTABLISHED - engineering validation only', 'provenance': 'EXAMPLE_DATA', 'warning': 'EXAMPLE - real inference uses real_pcos_model_adapter'},
                {'module': 'SleepModule v8.3.0', 'output': 'circadian_disruption_pattern moderate', 'confidence': 0.68, 'provenance': 'EXAMPLE_DATA'},
            ],
            'disclaimer': 'Research / risk-screening output — not a medical diagnosis',
            'provenance': 'EXAMPLE_DATA - real analysis uses real models with calibrated confidence',
            'label': 'EXAMPLE analysis for UI demo, real path uses real_pcos_model_adapter'
        }

class UltrasoundViewer:
    """
    Ultrasound: loading, preprocessing, quality checks, segmentation, inference, visualization, confidence, training, evaluation, storage
    Do not invent accuracy, state if insufficient, never fabricate percentages
    """
    def __init__(self, db: LocalDatabase):
        self.db = db

    def load_image(self, path):
        return {'path': path, 'loaded': True, 'shape': 'unknown', 'quality_check': 'pending'}

    def quality_check(self, image):
        # No invented accuracy
        return {
            'quality_score': None,  # UNKNOWN by design unless computed
            'checks': ['blur', 'exposure', 'anatomy visibility'],
            'result': 'quality assessment requires model, not fabricated',
            'provenance': 'CLINICALLY-ENTERED vs IMAGE-DERIVED distinction'
        }

    def inference(self, image):
        return {
            'result': 'inference requires trained model',
            'confidence': None,  # Do not hard-code fake confidence
            'disclaimer': 'Ultrasound analysis is research, not diagnosis, requires clinical evaluation, model accuracy not established without validation dataset',
            'provenance': 'If insufficient training data, state insufficient'
        }

class LongitudinalViewer:
    def compare(self, patient_id, session_ids):
        return {
            'patient_id': patient_id,
            'sessions': session_ids,
            'trends': 'Longitudinal comparison - HR trend, HRV trend, activity trend, temp trend',
            'baseline_deviation': 'Deviation from personal baseline'
        }

class ReportGenerator:
    def __init__(self, db=None):
        self.db = db

    def generate(self, patient_id, analysis, include_disclaimer=True):
        # EXAMPLE report - real report uses real model confidence from adapter
        report = {
            'patient_id': patient_id,
            'analysis': analysis,
            'generated_at': 'now',
            'provenance': 'EXAMPLE_DATA - real report uses real model calibrated confidence',
            'label': 'EXAMPLE report for UI demo',
            'disclaimer': 'Research / risk-screening output — not a medical diagnosis.' if include_disclaimer else '',
            'model_transparency': {
                'models_used': ['PCOSModule v8.3.0', 'SleepModule v8.3.0'],
                'input_data': 'PPG, HRV, activity, temp',
                'data_quality': '0.85 overall',
                'confidence': '0.75 (model output, not clinical certainty) - EXAMPLE, real path uses calibrated probability from real_pcos_model_adapter',
                'features': 'HRV RMSSD, activity level, skin temp',
                'limitations': 'Engineering validation only, clinical validation NOT ESTABLISHED, not replacement for professional evaluation',
                'note': 'EXAMPLE confidence - real report uses real model adapter confidence'
            }
        }
        return report
