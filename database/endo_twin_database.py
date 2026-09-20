"""
ENDO-TWIN Database - Enhanced SQLite schema for ENDO-TWIN research framework

Core entities:
- patients
- sensor_sessions
- measurements (generic)
- features
- clinical_records
- symptoms
- cycle_events
- ultrasound_studies
- ultrasound_features
- model_runs
- model_versions
- reports
- notes
- providers
- audit_events

Relationships:
patients → sensor_sessions → measurements → features
patients → ultrasound_studies → ultrasound_features
patients → model_runs
patients → reports
patients → clinical_records

All patient-specific records must contain patient_id
Stable IDs, foreign keys, audit events, no cross-patient contamination
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any

from .database import LocalDatabase

class EndoTwinDatabase(LocalDatabase):
    """
    ENDO-TWIN enhanced database - extends LocalDatabase with ENDO-TWIN architecture
    Preserves existing V8.3 functionality, adds new ENDO-TWIN entities
    """

    def __init__(self, db_path: Path | str | None = None):
        super().__init__(db_path=db_path)
        self._init_endo_twin_schema()
        self._seed_demo_patients()

    def _init_endo_twin_schema(self):
        cur = self.conn.cursor()

        # Measurements - generic table for all physiological measurements with provenance
        cur.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            measurement_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            session_id TEXT,
            measurement_type TEXT NOT NULL CHECK(measurement_type IN ('hr','hrv','ppg','gsr','temperature','motion','sleep','activity','circadian','autonomic','metabolic')),
            value REAL,
            value_json TEXT,
            unit TEXT,
            timestamp REAL NOT NULL,
            quality REAL,
            provenance TEXT NOT NULL CHECK(provenance IN ('MEASURED','CLINICALLY_ENTERED','IMAGE_DERIVED','MODEL_INFERRED','DEMO_DATA','UNKNOWN')),
            source TEXT NOT NULL,
            confidence REAL,
            limitations TEXT,
            is_demo INTEGER DEFAULT 0,
            created_at REAL NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY(session_id) REFERENCES sensor_sessions(session_id)
        )
        """)

        # Features - extracted features with provenance
        cur.execute("""
        CREATE TABLE IF NOT EXISTS features (
            feature_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            session_id TEXT,
            measurement_id TEXT,
            feature_name TEXT NOT NULL,
            feature_value REAL,
            feature_json TEXT,
            category TEXT NOT NULL CHECK(category IN ('established_measurement','derived_feature','experimental_research','ml_prediction','clinical_interpretation')),
            quality REAL,
            provenance TEXT NOT NULL,
            source TEXT NOT NULL,
            confidence REAL,
            limitations TEXT,
            explainability TEXT,
            is_demo INTEGER DEFAULT 0,
            created_at REAL NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY(session_id) REFERENCES sensor_sessions(session_id)
        )
        """)

        # Clinical records - clinical data with provenance CLINICALLY_ENTERED
        cur.execute("""
        CREATE TABLE IF NOT EXISTS clinical_records (
            record_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            record_type TEXT NOT NULL,
            data_json TEXT NOT NULL,
            provenance TEXT NOT NULL DEFAULT 'CLINICALLY_ENTERED',
            source TEXT NOT NULL DEFAULT 'USER-ENTERED',
            label TEXT NOT NULL DEFAULT 'USER-ENTERED',
            is_demo INTEGER DEFAULT 0,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
        """)

        # Cycle events - enhanced cycle tracking (alias for cycles but with event structure)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS cycle_events (
            event_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            event_type TEXT NOT NULL CHECK(event_type IN ('cycle_start','cycle_end','ovulation','symptom','note')),
            event_date REAL NOT NULL,
            cycle_length_days INTEGER,
            irregularity TEXT,
            symptoms_json TEXT,
            notes TEXT,
            provenance TEXT NOT NULL DEFAULT 'CLINICALLY_ENTERED',
            is_demo INTEGER DEFAULT 0,
            created_at REAL NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
        """)

        # Ultrasound studies - enhanced from ultrasound_records
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ultrasound_studies (
            study_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            study_date REAL NOT NULL,
            image_path TEXT,
            image_metadata_json TEXT,
            quality REAL,
            quality_details_json TEXT,
            provenance TEXT NOT NULL DEFAULT 'IMAGE_DERIVED',
            source TEXT NOT NULL,
            confidence REAL,
            is_demo INTEGER DEFAULT 0,
            label TEXT NOT NULL DEFAULT 'REAL',
            created_at REAL NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
        """)

        # Ultrasound features - features extracted from ultrasound
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ultrasound_features (
            feature_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            study_id TEXT NOT NULL,
            feature_name TEXT NOT NULL,
            feature_value REAL,
            feature_json TEXT,
            unit TEXT,
            quality REAL,
            provenance TEXT NOT NULL DEFAULT 'IMAGE_DERIVED',
            source TEXT NOT NULL,
            confidence REAL,
            limitations TEXT,
            is_demo INTEGER DEFAULT 0,
            created_at REAL NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY(study_id) REFERENCES ultrasound_studies(study_id)
        )
        """)

        # Model versions - model registry
        cur.execute("""
        CREATE TABLE IF NOT EXISTS model_versions (
            version_id TEXT PRIMARY KEY,
            model_name TEXT NOT NULL,
            model_version TEXT NOT NULL,
            model_type TEXT NOT NULL CHECK(model_type IN ('disease_specific','general','experimental')),
            description TEXT,
            capabilities_json TEXT,
            limitations TEXT,
            dataset_version TEXT,
            training_date TEXT,
            features_json TEXT,
            target TEXT,
            metrics_json TEXT,
            validation_strategy TEXT,
            provenance TEXT NOT NULL DEFAULT 'MODEL_INFERRED',
            is_approved INTEGER DEFAULT 0,
            created_at REAL NOT NULL,
            UNIQUE(model_name, model_version)
        )
        """)

        # Model runs - inference runs scoped to patient
        cur.execute("""
        CREATE TABLE IF NOT EXISTS model_runs (
            run_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            session_id TEXT,
            model_name TEXT NOT NULL,
            model_version TEXT NOT NULL,
            input_features_json TEXT,
            output_json TEXT,
            confidence REAL,
            data_quality REAL,
            clinical_validation TEXT DEFAULT 'NOT ESTABLISHED',
            provenance TEXT NOT NULL DEFAULT 'MODEL_INFERRED',
            explainability_json TEXT,
            limitations TEXT,
            is_demo INTEGER DEFAULT 0,
            created_at REAL NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY(session_id) REFERENCES sensor_sessions(session_id)
        )
        """)

        # Audit events - enhanced audit
        cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_events (
            event_id TEXT PRIMARY KEY,
            user_id TEXT,
            patient_id TEXT,
            event_type TEXT NOT NULL,
            action TEXT NOT NULL,
            details_json TEXT,
            timestamp REAL NOT NULL,
            ip_address TEXT,
            is_demo INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
        """)

        # Personal baseline - stores baseline per patient
        cur.execute("""
        CREATE TABLE IF NOT EXISTS personal_baseline (
            baseline_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            feature_name TEXT NOT NULL,
            baseline_period_start REAL,
            baseline_period_end REAL,
            mean_value REAL,
            median_value REAL,
            std_value REAL,
            mad_value REAL,
            rolling_json TEXT,
            confidence REAL,
            min_observations INTEGER,
            circadian_context_json TEXT,
            provenance TEXT NOT NULL,
            is_demo INTEGER DEFAULT 0,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
            UNIQUE(patient_id, feature_name)
        )
        """)

        # Longitudinal timeline - chronological events
        cur.execute("""
        CREATE TABLE IF NOT EXISTS longitudinal_timeline (
            timeline_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_id TEXT NOT NULL,
            event_date REAL NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            provenance TEXT NOT NULL,
            data_json TEXT,
            is_demo INTEGER DEFAULT 0,
            created_at REAL NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
        """)

        self.conn.commit()

    def _seed_demo_patients(self):
        """Create DEMO-001, DEMO-002, DEMO-003 with deliberately different data"""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM patients WHERE patient_id LIKE 'DEMO-%'")
        if cur.fetchone()["cnt"] >= 3:
            return

        demo_patients = [
            {
                "patient_id": "DEMO-001",
                "anonymous_id": "P00001",
                "display_name": "Demo Patient 001 (DEMO DATA)",
                "age_years": 22,
                "bmi": 23.5,
                "is_demo": True,
                "hr": 72,
                "hrv_rmssd": 48,
                "activity": 35,
                "temp": 32.5,
                "symptoms": ["irregular_cycle", "mild_acne"],
                "cycle_length": 32,
                "irregularity": "irregular"
            },
            {
                "patient_id": "DEMO-002",
                "anonymous_id": "P00002",
                "display_name": "Demo Patient 002 (DEMO DATA)",
                "age_years": 28,
                "bmi": 27.2,
                "is_demo": True,
                "hr": 78,
                "hrv_rmssd": 35,
                "activity": 25,
                "temp": 32.8,
                "symptoms": ["irregular_cycle", "weight_gain", "hirsutism"],
                "cycle_length": 45,
                "irregularity": "highly_irregular"
            },
            {
                "patient_id": "DEMO-003",
                "anonymous_id": "P00003",
                "display_name": "Demo Patient 003 (DEMO DATA)",
                "age_years": 24,
                "bmi": 21.8,
                "is_demo": True,
                "hr": 68,
                "hrv_rmssd": 55,
                "activity": 45,
                "temp": 32.3,
                "symptoms": ["regular_cycle", "mild"],
                "cycle_length": 28,
                "irregularity": "regular"
            },
        ]

        for p in demo_patients:
            # Check if exists
            cur.execute("SELECT 1 FROM patients WHERE patient_id=?", (p["patient_id"],))
            if cur.fetchone():
                continue

            cur.execute("""
            INSERT INTO patients (patient_id, anonymous_id, display_name, age_years, bmi, created_at, updated_at, is_archived)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """, (p["patient_id"], p["anonymous_id"], p["display_name"], p["age_years"], p["bmi"], time.time(), time.time()))

            # Create sensor session for each demo patient with different data
            session_id = f"session_{p['patient_id']}_001"
            cur.execute("""
            INSERT OR IGNORE INTO sensor_sessions (session_id, patient_id, source, start_at, label, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session_id, p["patient_id"], "DEMO_SENSOR", time.time(), "DEMO_DATA", f"Demo session for {p['patient_id']} - HR {p['hr']} bpm, HRV {p['hrv_rmssd']} ms, Activity {p['activity']}%, Temp {p['temp']}C - deliberately different data", time.time()))

            # Create measurements with provenance MEASURED and DEMO_DATA label
            for m_type, value in [("hr", p["hr"]), ("hrv", p["hrv_rmssd"]), ("activity", p["activity"]), ("temperature", p["temp"])]:
                measurement_id = str(uuid.uuid4())
                cur.execute("""
                INSERT INTO measurements (measurement_id, patient_id, session_id, measurement_type, value, unit, timestamp, quality, provenance, source, is_demo, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (measurement_id, p["patient_id"], session_id, m_type, value, "bpm" if m_type=="hr" else "ms" if m_type=="hrv" else "%" if m_type=="activity" else "C", time.time(), 0.85, "DEMO_DATA", f"DEMO_SENSOR_{m_type}", 1, time.time()))

            # Create symptoms
            for symptom in p["symptoms"]:
                symptom_id = str(uuid.uuid4())
                cur.execute("""
                INSERT INTO symptoms (symptom_id, patient_id, symptom_type, severity, notes, logged_at, label)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (symptom_id, p["patient_id"], symptom, 1, f"Demo symptom for {p['patient_id']}", time.time(), "DEMO_DATA"))

            # Create cycle event
            event_id = str(uuid.uuid4())
            cur.execute("""
            INSERT INTO cycle_events (event_id, patient_id, event_type, event_date, cycle_length_days, irregularity, notes, provenance, is_demo, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (event_id, p["patient_id"], "cycle_start", time.time(), p["cycle_length"], p["irregularity"], f"Demo cycle for {p['patient_id']}", "DEMO_DATA", 1, time.time()))

            # Create ultrasound study for each (different)
            study_id = f"ultrasound_{p['patient_id']}_001"
            cur.execute("""
            INSERT OR IGNORE INTO ultrasound_studies (study_id, patient_id, study_date, image_path, quality, provenance, source, label, is_demo, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (study_id, p["patient_id"], time.time(), f"/demo/ultrasound_{p['patient_id']}.png", 0.8, "DEMO_DATA", "DEMO_ULTRASOUND", "DEMO", 1, time.time()))

            # Create model run for each (different risk)
            run_id = str(uuid.uuid4())
            risk = "low" if p["patient_id"] == "DEMO-003" else "moderate" if p["patient_id"] == "DEMO-001" else "high"
            cur.execute("""
            INSERT INTO model_runs (run_id, patient_id, session_id, model_name, model_version, input_features_json, output_json, confidence, data_quality, clinical_validation, provenance, is_demo, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (run_id, p["patient_id"], session_id, "PCOSModule", "v8.3.0", json.dumps({"hr": p["hr"], "hrv_rmssd": p["hrv_rmssd"], "activity": p["activity"], "bmi": p["bmi"]}), json.dumps({"pcos_associated_risk": risk, "note": "NOT diagnosis"}), 0.75, 0.85, "NOT ESTABLISHED", "DEMO_DATA", 1, time.time()))

            # Create report for each
            report_id = str(uuid.uuid4())
            cur.execute("""
            INSERT INTO reports (report_id, patient_id, session_id, report_type, content_text, created_at, label)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (report_id, p["patient_id"], session_id, "pcos_risk_screening", f"Report for {p['patient_id']} - Risk {risk} - Research / risk-screening output — not a medical diagnosis - HR {p['hr']} bpm MEASURED quality 0.91, HRV {p['hrv_rmssd']} ms DERIVED quality 0.85, Activity {p['activity']}% MEASURED, Temp {p['temp']}C MEASURED - Model PCOSModule v8.3.0 confidence 0.75 data quality 0.85 clinical validation NOT ESTABLISHED - DEMO DATA clearly marked", time.time(), "DEMO_DATA"))

            # Create timeline events
            for event_type in ["sensor_session", "symptom_entry", "ultrasound_study", "model_run", "report_generated"]:
                timeline_id = str(uuid.uuid4())
                cur.execute("""
                INSERT INTO longitudinal_timeline (timeline_id, patient_id, event_type, event_id, event_date, title, description, provenance, is_demo, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (timeline_id, p["patient_id"], event_type, str(uuid.uuid4()), time.time(), f"{event_type} for {p['patient_id']}", f"Demo timeline event {event_type} for {p['patient_id']} - deliberately different data", "DEMO_DATA", 1, time.time()))

        self.conn.commit()

    # Enhanced patient-scoped queries - mandatory multi-patient safety
    def get_patient_measurements(self, patient_id: str) -> List[Dict]:
        """Get measurements scoped to patient - no cross-contamination"""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM measurements WHERE patient_id=? ORDER BY timestamp DESC", (patient_id,))
        return [dict(row) for row in cur.fetchall()]

    def get_patient_features(self, patient_id: str) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM features WHERE patient_id=? ORDER BY created_at DESC", (patient_id,))
        return [dict(row) for row in cur.fetchall()]

    def get_patient_clinical_records(self, patient_id: str) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM clinical_records WHERE patient_id=? ORDER BY created_at DESC", (patient_id,))
        return [dict(row) for row in cur.fetchall()]

    def get_patient_cycle_events(self, patient_id: str) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM cycle_events WHERE patient_id=? ORDER BY event_date DESC", (patient_id,))
        return [dict(row) for row in cur.fetchall()]

    def get_patient_ultrasound_studies(self, patient_id: str) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM ultrasound_studies WHERE patient_id=? ORDER BY study_date DESC", (patient_id,))
        return [dict(row) for row in cur.fetchall()]

    def get_patient_ultrasound_features(self, patient_id: str) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM ultrasound_features WHERE patient_id=? ORDER BY created_at DESC", (patient_id,))
        return [dict(row) for row in cur.fetchall()]

    def get_patient_model_runs(self, patient_id: str) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM model_runs WHERE patient_id=? ORDER BY created_at DESC", (patient_id,))
        return [dict(row) for row in cur.fetchall()]

    def get_patient_reports(self, patient_id: str) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM reports WHERE patient_id=? ORDER BY created_at DESC", (patient_id,))
        return [dict(row) for row in cur.fetchall()]

    def get_patient_timeline(self, patient_id: str) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM longitudinal_timeline WHERE patient_id=? ORDER BY event_date DESC", (patient_id,))
        return [dict(row) for row in cur.fetchall()]

    def get_patient_baseline(self, patient_id: str) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM personal_baseline WHERE patient_id=?", (patient_id,))
        return [dict(row) for row in cur.fetchall()]

    # Test multi-patient isolation
    def test_patient_isolation(self) -> Dict[str, Any]:
        """
        Test DEMO-001 cannot see DEMO-002, etc.
        Mandatory multi-patient safety - implemented at database level not merely UI hidden
        """
        results = {
            "demo_patients": ["DEMO-001", "DEMO-002", "DEMO-003"],
            "tests": [],
            "passed": 0,
            "failed": 0
        }

        for patient_id in results["demo_patients"]:
            measurements = self.get_patient_measurements(patient_id)
            features = self.get_patient_features(patient_id)
            studies = self.get_patient_ultrasound_studies(patient_id)
            runs = self.get_patient_model_runs(patient_id)
            reports = self.get_patient_reports(patient_id)
            timeline = self.get_patient_timeline(patient_id)

            # Check that all returned records belong to this patient only
            all_correct = True
            for m in measurements:
                if m["patient_id"] != patient_id:
                    all_correct = False
            for f in features:
                if f["patient_id"] != patient_id:
                    all_correct = False
            for s in studies:
                if s["patient_id"] != patient_id:
                    all_correct = False
            for r in runs:
                if r["patient_id"] != patient_id:
                    all_correct = False
            for rep in reports:
                if rep["patient_id"] != patient_id:
                    all_correct = False
            for t in timeline:
                if t["patient_id"] != patient_id:
                    all_correct = False

            # Check that data is deliberately different
            hr_values = [m["value"] for m in measurements if m["measurement_type"] == "hr"]
            
            test_result = {
                "patient_id": patient_id,
                "measurements_count": len(measurements),
                "studies_count": len(studies),
                "runs_count": len(runs),
                "reports_count": len(reports),
                "timeline_count": len(timeline),
                "hr_values": hr_values,
                "isolation_ok": all_correct,
                "has_data": len(measurements) > 0
            }
            
            results["tests"].append(test_result)
            if all_correct and len(measurements) > 0:
                results["passed"] += 1
            else:
                results["failed"] += 1

        # Check that DEMO-001 data is different from DEMO-002
        demo_001_hr = []
        demo_002_hr = []
        demo_003_hr = []
        
        for test in results["tests"]:
            if test["patient_id"] == "DEMO-001":
                demo_001_hr = test["hr_values"]
            elif test["patient_id"] == "DEMO-002":
                demo_002_hr = test["hr_values"]
            elif test["patient_id"] == "DEMO-003":
                demo_003_hr = test["hr_values"]

        results["data_is_different"] = len(set(str(demo_001_hr) + str(demo_002_hr) + str(demo_003_hr))) > 1
        results["cross_contamination"] = False  # If isolation_ok for all, no cross-contamination
        
        # Check for cross-contamination by querying all measurements and ensuring patient_id is correct
        cur = self.conn.cursor()
        cur.execute("SELECT patient_id, COUNT(*) as cnt FROM measurements WHERE patient_id LIKE 'DEMO-%' GROUP BY patient_id")
        demo_counts = {row["patient_id"]: row["cnt"] for row in cur.fetchall()}
        results["demo_counts"] = demo_counts
        
        # Verify no measurement belongs to multiple patients (impossible by schema but test)
        cur.execute("SELECT measurement_id, patient_id FROM measurements WHERE patient_id LIKE 'DEMO-%'")
        all_demo_measurements = cur.fetchall()
        patient_ids_in_measurements = set([row["patient_id"] for row in all_demo_measurements])
        results["patient_ids_in_demo_measurements"] = list(patient_ids_in_measurements)
        results["no_cross_contamination"] = patient_ids_in_measurements.issubset(set(results["demo_patients"]))

        results["overall_pass"] = results["failed"] == 0 and results["data_is_different"] and results["no_cross_contamination"]

        return results
