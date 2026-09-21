"""
Doctor PC App - Patient Management Enhancement V8.3+

Sections:
- Dashboard: patient overview, recent assessments, data quality, pending reviews, longitudinal views
- Patient Management: create, search, open, archive, patient history
- Physiological Data: raw/filtered PPG, HR, HRV, GSR, motion, temp, quality, artifacts, visualization, time-series
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

    def archive_patient(self, patient_id, user_id=None):
        return {
            'archived': self.db.archive_patient(patient_id, archived=True, user_id=user_id),
            'patient_id': patient_id,
        }

    def get_history(self, patient_id):
        cur = self.db.conn.cursor()
        cur.execute("SELECT * FROM symptoms WHERE patient_id=? ORDER BY logged_at DESC", (patient_id,))
        symptoms = [dict(row) for row in cur.fetchall()]
        cur.execute("SELECT * FROM cycles WHERE patient_id=? ORDER BY start_date DESC", (patient_id,))
        cycles = [dict(row) for row in cur.fetchall()]
        cur.execute("SELECT * FROM reports WHERE patient_id=? ORDER BY created_at DESC", (patient_id,))
        reports = [dict(row) for row in cur.fetchall()]
        return {
            'patient': self.db.get_patient(patient_id),
            'sessions': self.db.list_sessions(patient_id),
            'symptoms': symptoms,
            'cycles': cycles,
            'reports': reports,
            'notes': self.db.get_doctor_notes(patient_id)
        }

class PhysiologicalDataViewer:
    """
    View raw/filtered PPG, HR, HRV, GSR, motion, temp, quality, artifacts
    Visualization, time-series
    """
    def __init__(self, db: LocalDatabase):
        self.db = db

    def get_session_data(self, session_id, patient_id=None):
        session = self.db.get_session(session_id, patient_id=patient_id)
        if not session:
            return {'session_id': session_id, 'status': 'SESSION_NOT_FOUND'}
        cur = self.db.conn.cursor()
        out = {'session': session, 'ppg': [], 'hrv': [], 'gsr': [], 'motion': [], 'temperature': [], 'quality': []}
        for key, table in {
            'ppg': 'ppg_data', 'hrv': 'hrv_data', 'gsr': 'gsr_data',
            'motion': 'motion_data', 'temperature': 'temperature_data', 'quality': 'sensor_quality'
        }.items():
            cur.execute(f"SELECT * FROM {table} WHERE session_id=? ORDER BY timestamp_s", (session_id,))
            out[key] = [dict(row) for row in cur.fetchall()]
        out['status'] = 'OK'
        return out

class AdvancedAnalysisViewer:
    """Patient-scoped analysis facade with explicit unavailable states."""
    def __init__(self, db: LocalDatabase):
        self.db = db
        self.fingerprint_engine = ChronoMetabolicFingerprint()

    @staticmethod
    def _insufficient(patient_id, session_id=None, reason="Insufficient data"):
        return {
            'status': 'INSUFFICIENT_DATA',
            'patient_id': patient_id,
            'session_id': session_id,
            'reason': reason,
            'provenance': 'UNKNOWN',
            'circadian': {'status': 'INSUFFICIENT_DATA'},
            'autonomic': {'status': 'INSUFFICIENT_DATA'},
            'metabolic': {'status': 'INSUFFICIENT_DATA'},
            'fingerprint': {'status': 'INSUFFICIENT_DATA', 'components': []},
            'multimodal': {'status': 'INSUFFICIENT_DATA'},
            'ai_outputs': [],
        }

    def analyze(self, patient_id, session_id=None):
        if session_id is None:
            return self._insufficient(patient_id, reason='Select a stored sensor session before analysis')
        data = PhysiologicalDataViewer(self.db).get_session_data(session_id, patient_id=patient_id)
        if data.get('status') != 'OK':
            return self._insufficient(patient_id, session_id, 'Session not found or not patient-scoped')
        counts = {k: len(data.get(k, [])) for k in ('ppg', 'hrv', 'gsr', 'motion', 'temperature')}
        if sum(counts.values()) == 0:
            return self._insufficient(patient_id, session_id, 'No sensor observations are stored for this session')
        return {
            'status': 'DATA_AVAILABLE',
            'patient_id': patient_id,
            'session_id': session_id,
            'sensor_counts': counts,
            'provenance': 'STORED_OBSERVATION',
            'circadian': {'status': 'PENDING_FEATURE_EXTRACTION'},
            'autonomic': {'status': 'PENDING_FEATURE_EXTRACTION'},
            'metabolic': {'status': 'PENDING_FEATURE_EXTRACTION'},
            'fingerprint': {'status': 'PENDING_FEATURE_EXTRACTION', 'components': []},
            'multimodal': {'status': 'PENDING_FUSION'},
            'ai_outputs': [],
            'note': 'Route stored observations through the real feature/fusion/model pipeline; no hard-coded prediction is emitted.',
        }


class LongitudinalViewer:
    """Patient-scoped longitudinal comparison facade.

    This component reports stored observations and explicit unavailable states.
    It does not invent trends, baseline statistics, or model-inferred findings.
    """

    def __init__(self, db=None):
        self.db = db

    def compare(self, patient_id, session_ids):
        if not patient_id:
            return {
                'status': 'INVALID_PATIENT',
                'patient_id': patient_id,
                'session_ids': session_ids or [],
                'trends': [],
                'baseline_deviation': None,
            }

        session_ids = list(session_ids or [])
        if not session_ids:
            return {
                'status': 'INSUFFICIENT_DATA',
                'patient_id': patient_id,
                'session_ids': [],
                'trends': [],
                'baseline_deviation': None,
                'reason': 'No sessions supplied for longitudinal comparison',
            }

        viewer = PhysiologicalDataViewer(self.db) if getattr(self, 'db', None) else None
        # Keep the constructor optional for compatibility with the existing
        # EnhancedDoctorApp, while allowing a database-backed implementation.
        if viewer is None:
            return {
                'status': 'INSUFFICIENT_DATA',
                'patient_id': patient_id,
                'session_ids': session_ids,
                'trends': [],
                'baseline_deviation': None,
                'reason': 'Longitudinal database context is unavailable',
            }

        stored = []
        for session_id in session_ids:
            data = viewer.get_session_data(session_id, patient_id=patient_id)
            if data.get('status') == 'OK':
                stored.append({
                    'session_id': session_id,
                    'counts': {k: len(data.get(k, [])) for k in ('ppg', 'hrv', 'gsr', 'motion', 'temperature')},
                })

        if not stored:
            return {
                'status': 'INSUFFICIENT_DATA',
                'patient_id': patient_id,
                'session_ids': session_ids,
                'trends': [],
                'baseline_deviation': None,
                'reason': 'No patient-scoped stored observations were found',
            }

        return {
            'status': 'DATA_AVAILABLE',
            'patient_id': patient_id,
            'session_ids': session_ids,
            'stored_sessions': stored,
            'trends': [],
            'baseline_deviation': None,
            'note': 'Trend and personal-baseline calculations require the real longitudinal feature pipeline; no synthetic values are emitted.',
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
            'disclaimer': 'Ultrasound analysis is research, not diagnosis, requires clinical evaluation, model accuracy not established',
        }


class ReportGenerator:
    def __init__(self, db=None):
        self.db = db

    def generate(self, patient_id, analysis, include_disclaimer=True):
        status = analysis.get('status', 'UNKNOWN')
        report = {
            'patient_id': patient_id,
            'analysis': analysis,
            'generated_at': 'now',
            'provenance': analysis.get('provenance', 'UNKNOWN'),
            'label': 'REAL' if status == 'DATA_AVAILABLE' else 'INSUFFICIENT_DATA',
            'disclaimer': 'Research / risk-screening output — not a medical diagnosis.' if include_disclaimer else '',
            'model_transparency': {
                'models_used': [],
                'input_data': analysis.get('sensor_counts', {}),
                'data_quality': 'Not computed' if status != 'DATA_AVAILABLE' else 'See stored channel quality',
                'confidence': None,
                'features': [],
                'limitations': 'Model inference is not performed when required inputs are unavailable.',
                'status': status,
                'note': 'No confidence value is invented by the Doctor workstation.',
            },
        }
        return report


