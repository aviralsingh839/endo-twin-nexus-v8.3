"""Local-first SQLite database for V8.3+ ecosystem.

Tables:
- patients
- profiles
- symptoms
- cycles
- sensor_sessions
- ppg, hr, hrv, gsr, motion, temperature
- sensor_quality
- ultrasound_records
- model_results
- analysis_results
- reports
- doctor_notes
- providers (care discovery)
- supplies
- audit_records
- users (auth, roles)

Local-first, no cloud upload of private health data.
"""
from __future__ import annotations

import json
import sqlite3
import time
import hashlib
import secrets
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.config import DATA_DIR


class LocalDatabase:
    """Robust local database architecture."""

    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path) if db_path else DATA_DIR / "chrono_twin_nexus_v8_3_plus.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        self._seed_demo_providers()

    def _init_schema(self):
        cur = self.conn.cursor()

        # Users - auth, roles
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('patient','doctor','admin')),
            created_at REAL NOT NULL,
            last_login REAL,
            is_active INTEGER DEFAULT 1
        )
        """)

        # Patients
        cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY,
            user_id TEXT,
            anonymous_id TEXT UNIQUE NOT NULL,
            display_name TEXT,
            age_years REAL,
            bmi REAL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            is_archived INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
        """)

        # Profiles - basic profile information, questionnaire
        cur.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            profile_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            data_json TEXT NOT NULL,
            label TEXT NOT NULL DEFAULT 'USER-ENTERED',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
        """)

        # Symptoms - structured symptom logging
        cur.execute("""
        CREATE TABLE IF NOT EXISTS symptoms (
            symptom_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            symptom_type TEXT NOT NULL,
            severity INTEGER,
            notes TEXT,
            logged_at REAL NOT NULL,
            label TEXT NOT NULL DEFAULT 'USER-ENTERED',
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
        """)

        # Cycles - cycle tracking
        cur.execute("""
        CREATE TABLE IF NOT EXISTS cycles (
            cycle_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            start_date REAL NOT NULL,
            end_date REAL,
            cycle_length_days INTEGER,
            usual_length_days INTEGER,
            irregularity TEXT,
            symptoms_json TEXT,
            notes TEXT,
            logged_at REAL NOT NULL,
            label TEXT NOT NULL DEFAULT 'USER-ENTERED',
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
        """)

        # Sensor sessions
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_sessions (
            session_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            source TEXT NOT NULL,
            start_at REAL NOT NULL,
            end_at REAL,
            sample_count INTEGER DEFAULT 0,
            data_quality REAL,
            notes TEXT,
            label TEXT NOT NULL,
            created_at REAL NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
        """)

        # Sensor data - PPG
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ppg_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp_s REAL NOT NULL,
            ir INTEGER,
            red INTEGER,
            hr_bpm REAL,
            spo2_pct REAL,
            pulse_amplitude REAL,
            quality REAL,
            label TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sensor_sessions(session_id)
        )
        """)

        # HR, HRV
        cur.execute("""
        CREATE TABLE IF NOT EXISTS hrv_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp_s REAL NOT NULL,
            hr_bpm REAL,
            resting_hr_bpm REAL,
            rmssd_ms REAL,
            sdnn_ms REAL,
            pnn50_pct REAL,
            quality REAL,
            label TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sensor_sessions(session_id)
        )
        """)

        # GSR
        cur.execute("""
        CREATE TABLE IF NOT EXISTS gsr_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp_s REAL NOT NULL,
            gsr_raw INTEGER,
            gsr_tonic REAL,
            gsr_phasic_per_min REAL,
            quality REAL,
            label TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sensor_sessions(session_id)
        )
        """)

        # Motion
        cur.execute("""
        CREATE TABLE IF NOT EXISTS motion_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp_s REAL NOT NULL,
            ax_g REAL, ay_g REAL, az_g REAL,
            gx_dps REAL, gy_dps REAL, gz_dps REAL,
            motion_index REAL,
            activity_level REAL,
            quality REAL,
            label TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sensor_sessions(session_id)
        )
        """)

        # Temperature
        cur.execute("""
        CREATE TABLE IF NOT EXISTS temperature_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp_s REAL NOT NULL,
            skin_temp_c REAL,
            room_temp_c REAL,
            temp_slope_c_per_min REAL,
            quality REAL,
            label TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sensor_sessions(session_id)
        )
        """)

        # Sensor quality
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_quality (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp_s REAL NOT NULL,
            channel TEXT NOT NULL,
            value REAL,
            quality REAL,
            source TEXT,
            artifact INTEGER,
            artifact_type TEXT,
            reason TEXT,
            label TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sensor_sessions(session_id)
        )
        """)

        # Ultrasound records
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ultrasound_records (
            record_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            image_path TEXT,
            cyst_size_mm REAL,
            volume_cc REAL,
            morphology TEXT,
            quality REAL,
            source TEXT NOT NULL,
            confidence REAL,
            notes TEXT,
            created_at REAL NOT NULL,
            label TEXT NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
        """)

        # Model results
        cur.execute("""
        CREATE TABLE IF NOT EXISTS model_results (
            result_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            session_id TEXT,
            module_name TEXT NOT NULL,
            module_version TEXT NOT NULL,
            signal TEXT NOT NULL,
            level TEXT NOT NULL,
            confidence REAL,
            data_quality REAL,
            clinical_validation TEXT,
            drivers_json TEXT,
            explanation TEXT,
            provenance_json TEXT,
            limitations TEXT,
            extra_json TEXT,
            created_at REAL NOT NULL,
            label TEXT NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
        """)

        # Analysis results - chrono-metabolic fingerprint
        cur.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            analysis_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            session_id TEXT,
            fingerprint_json TEXT NOT NULL,
            circadian_json TEXT,
            autonomic_json TEXT,
            metabolic_json TEXT,
            longitudinal_json TEXT,
            created_at REAL NOT NULL,
            label TEXT NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
        """)

        # Reports
        cur.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            report_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            session_id TEXT,
            report_type TEXT NOT NULL,
            content_text TEXT NOT NULL,
            file_path TEXT,
            created_at REAL NOT NULL,
            created_by TEXT,
            label TEXT NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
        """)

        # Doctor notes
        cur.execute("""
        CREATE TABLE IF NOT EXISTS doctor_notes (
            note_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            doctor_id TEXT NOT NULL,
            note_text TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            is_private INTEGER DEFAULT 0,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY(doctor_id) REFERENCES users(user_id)
        )
        """)

        # Wearable lifecycle / local synchronization
    # Providers - care discovery (separate from patient health data)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS providers (
            provider_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('doctor','clinic','lab','supply')),
            specialty TEXT,
            address TEXT,
            latitude REAL,
            longitude REAL,
            distance_km REAL,
            opening_hours TEXT,
            services_json TEXT,
            contact_info TEXT,
            verification_status TEXT NOT NULL CHECK(verification_status IN ('verified','pending','unverified','demo')),
            is_demo INTEGER DEFAULT 0,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
        """)

        # Supplies - health monitoring supplies
        cur.execute("""
        CREATE TABLE IF NOT EXISTS supplies (
            supply_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            provider_id TEXT,
            price REAL,
            availability TEXT,
            image_path TEXT,
            created_at REAL NOT NULL,
            FOREIGN KEY(provider_id) REFERENCES providers(provider_id)
        )
        """)

        # Audit records
        cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_records (
            audit_id TEXT PRIMARY KEY,
            user_id TEXT,
            patient_id TEXT,
            action TEXT NOT NULL,
            details_json TEXT,
            timestamp REAL NOT NULL,
            ip_address TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
        """)

        # Patient-doctor access - authorization
        cur.execute("""
        CREATE TABLE IF NOT EXISTS patient_doctor_access (
            access_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            doctor_id TEXT NOT NULL,
            granted_at REAL NOT NULL,
            granted_by TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY(doctor_id) REFERENCES users(user_id)
        )
        """)

        # Wearable lifecycle, synchronization and personalized-learning metadata.
        cur.execute("""
        CREATE TABLE IF NOT EXISTS research_studies (
            study_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            started_at REAL NOT NULL,
            target_end_at REAL NOT NULL,
            ended_at REAL,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            protocol_json TEXT,
            label TEXT NOT NULL DEFAULT 'REAL',
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
        """)
        cur.execute("""CREATE INDEX IF NOT EXISTS idx_research_studies_patient ON research_studies(patient_id, started_at)""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS wearable_devices (
            device_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            device_type TEXT NOT NULL,
            transport TEXT NOT NULL,
            firmware_version TEXT,
            state TEXT NOT NULL DEFAULT 'NOT_CONNECTED',
            first_seen REAL NOT NULL,
            last_seen REAL,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS wearable_events (
            event_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            session_id TEXT,
            timestamp REAL NOT NULL,
            event_type TEXT NOT NULL,
            detail_json TEXT,
            label TEXT NOT NULL DEFAULT 'REAL',
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY(session_id) REFERENCES sensor_sessions(session_id)
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_wearable_packets (
            packet_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            session_id TEXT,
            timestamp REAL NOT NULL,
            payload_base64 TEXT NOT NULL,
            transport TEXT NOT NULL,
            quality REAL,
            label TEXT NOT NULL DEFAULT 'REAL',
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY(session_id) REFERENCES sensor_sessions(session_id)
        )
        """)
        cur.execute("""CREATE INDEX IF NOT EXISTS idx_raw_wearable_packets_patient_ts ON raw_wearable_packets(patient_id, timestamp)""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS feature_vectors (
            feature_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            session_id TEXT,
            timestamp_s REAL NOT NULL,
            data_json TEXT NOT NULL,
            source TEXT NOT NULL,
            algorithm_version TEXT,
            label TEXT NOT NULL DEFAULT 'REAL',
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY(session_id) REFERENCES sensor_sessions(session_id)
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS personal_baselines (
            baseline_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            feature_name TEXT NOT NULL,
            median_value REAL,
            mean_value REAL,
            std_value REAL,
            mad_value REAL,
            sample_count INTEGER NOT NULL DEFAULT 0,
            days_covered REAL NOT NULL DEFAULT 0,
            confidence REAL NOT NULL DEFAULT 0,
            algorithm_version TEXT NOT NULL,
            updated_at REAL NOT NULL,
            UNIQUE(patient_id, feature_name),
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS research_labels (
            label_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            target TEXT NOT NULL,
            label_value TEXT NOT NULL,
            source TEXT NOT NULL,
            entered_by TEXT,
            timestamp REAL NOT NULL,
            notes TEXT,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
        """)
        cur.execute("""CREATE INDEX IF NOT EXISTS idx_research_labels_target ON research_labels(target, timestamp)""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS learning_runs (
            run_id TEXT PRIMARY KEY,
            patient_id TEXT,
            model_name TEXT NOT NULL,
            base_model_version TEXT,
            mode TEXT NOT NULL,
            started_at REAL NOT NULL,
            completed_at REAL,
            status TEXT NOT NULL,
            input_sessions_json TEXT,
            metrics_json TEXT,
            limitations TEXT,
            label TEXT NOT NULL DEFAULT 'RESEARCH',
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
        """)
        self._ensure_column(self.conn, "features", "extra_json", "TEXT")
        self._ensure_column(self.conn, "sensor_sessions", "participant_id", "TEXT")
        self._ensure_column(self.conn, "sensor_sessions", "study_id", "TEXT")

        cur.execute("""CREATE INDEX IF NOT EXISTS idx_feature_vectors_patient_ts ON feature_vectors(patient_id, timestamp_s)""")
        cur.execute("""CREATE INDEX IF NOT EXISTS idx_wearable_events_patient_ts ON wearable_events(patient_id, timestamp)""")
        cur.execute("""CREATE INDEX IF NOT EXISTS idx_learning_runs_patient_ts ON learning_runs(patient_id, started_at)""")

        self.conn.commit()


    def register_wearable(self, patient_id: str, device_id: str, device_type: str, transport: str, firmware_version: Optional[str] = None) -> str:
        now = time.time()
        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO wearable_devices(device_id, patient_id, device_type, transport, firmware_version, state, first_seen, last_seen)
        VALUES (?, ?, ?, ?, ?, 'NOT_CONNECTED', ?, ?)
        ON CONFLICT(device_id) DO UPDATE SET
            patient_id=excluded.patient_id,
            device_type=excluded.device_type,
            transport=excluded.transport,
            firmware_version=excluded.firmware_version,
            last_seen=excluded.last_seen
        """, (device_id, patient_id, device_type, transport, firmware_version, now, now))
        self.conn.commit()
        return device_id

    def set_wearable_state(self, patient_id: str, device_id: str, state: str, reason: str = '') -> bool:
        allowed = {'NOT_CONNECTED', 'CONNECTED', 'WORN', 'REMOVED', 'RECONNECTING', 'ERROR', 'CHARGING'}
        state = state.upper()
        if state not in allowed:
            raise ValueError(f'Unsupported wearable state: {state}')
        now = time.time()
        cur = self.conn.cursor()
        cur.execute(
            'UPDATE wearable_devices SET state=?, last_seen=? WHERE device_id=? AND patient_id=?',
            (state, now, device_id, patient_id),
        )
        changed = cur.rowcount > 0
        self.conn.commit()
        if changed:
            self.record_wearable_event(patient_id, None, 'WEARABLE_STATE', {'device_id': device_id, 'state': state, 'reason': reason})
        return changed

    def record_wearable_event(self, patient_id: str, session_id: Optional[str], event_type: str, detail: Optional[Dict[str, Any]] = None, label: str = 'REAL') -> str:
        event_id = str(uuid.uuid4())
        self.conn.execute(
            'INSERT INTO wearable_events(event_id, patient_id, session_id, timestamp, event_type, detail_json, label) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (event_id, patient_id, session_id, time.time(), event_type, json.dumps(detail or {}, sort_keys=True), label),
        )
        self.conn.commit()
        return event_id

    def save_sensor_sample(self, patient_id: str, session_id: str, sample: Any, feature_vector: Optional[Any] = None, label: str = 'REAL') -> None:
        """Persist one raw wearable sample plus derived feature vector.

        The raw channels remain separate from derived features so the doctor
        workstation can inspect acquisition quality and provenance independently.
        """
        if not self.get_session(session_id, patient_id=patient_id):
            raise ValueError('Patient-scoped sensor session not found')
        ts = float(getattr(sample, 'timestamp_s', time.time()))
        quality = float(getattr(sample, 'ppg_quality', 0.0))
        fv = feature_vector
        self.conn.execute(
            'INSERT INTO ppg_data(session_id,timestamp_s,ir,red,hr_bpm,spo2_pct,pulse_amplitude,quality,label) VALUES (?,?,?,?,?,?,?,?,?)',
            (session_id, ts, getattr(sample, 'ir', None), getattr(sample, 'red', None), getattr(fv, 'hr_bpm', None), getattr(fv, 'spo2_pct', None), getattr(fv, 'ppg_pulse_amplitude_corrected', None) or getattr(fv, 'ppg_pulse_amplitude', None), quality, label),
        )
        self.conn.execute(
            'INSERT INTO hrv_data(session_id,timestamp_s,hr_bpm,resting_hr_bpm,rmssd_ms,sdnn_ms,pnn50_pct,quality,label) VALUES (?,?,?,?,?,?,?,?,?)',
            (session_id, ts, getattr(fv, 'hr_bpm', None), getattr(fv, 'resting_hr_bpm', None), getattr(fv, 'rmssd_ms', None), getattr(fv, 'sdnn_ms', None), getattr(fv, 'pnn50_pct', None), quality, label),
        )
        self.conn.execute(
            'INSERT INTO gsr_data(session_id,timestamp_s,gsr_raw,gsr_tonic,gsr_phasic_per_min,quality,label) VALUES (?,?,?,?,?,?,?)',
            (session_id, ts, getattr(sample, 'gsr_raw', None), getattr(fv, 'gsr_tonic', None), getattr(fv, 'gsr_phasic_per_min', None), quality, label),
        )
        self.conn.execute(
            'INSERT INTO motion_data(session_id,timestamp_s,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps,motion_index,activity_level,quality,label) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
            (session_id, ts, getattr(sample, 'ax_g', None), getattr(sample, 'ay_g', None), getattr(sample, 'az_g', None), getattr(sample, 'gx_dps', None), getattr(sample, 'gy_dps', None), getattr(sample, 'gz_dps', None), getattr(fv, 'motion_index', None), getattr(fv, 'activity_level', None), quality, label),
        )
        self.conn.execute(
            'INSERT INTO temperature_data(session_id,timestamp_s,skin_temp_c,room_temp_c,temp_slope_c_per_min,quality,label) VALUES (?,?,?,?,?,?,?)',
            (session_id, ts, getattr(sample, 'temp_c', None), getattr(sample, 'room_temp_c', None), getattr(fv, 'temp_slope_c_per_min', None), quality, label),
        )
        if fv is not None:
            self.conn.execute(
                'INSERT INTO feature_vectors(feature_id,patient_id,session_id,timestamp_s,data_json,source,algorithm_version,label) VALUES (?,?,?,?,?,?,?,?)',
                (str(uuid.uuid4()), patient_id, session_id, ts, json.dumps(fv.as_dict(), default=str, sort_keys=True), getattr(sample, 'source', 'wearable'), 'realtime-feature-extractor', label),
            )
        self.update_session_observation_count(session_id, quality)
        self.conn.commit()

    def update_session_observation_count(self, session_id: str, data_quality: Optional[float] = None) -> None:
        cur = self.conn.cursor()
        cur.execute(
            'UPDATE sensor_sessions SET sample_count=COALESCE(sample_count,0)+1, data_quality=COALESCE(?, data_quality) WHERE session_id=?',
            (data_quality, session_id),
        )
        self.conn.commit()

    def close_sensor_session(self, patient_id: str, session_id: str, notes: Optional[str] = None) -> bool:
        cur = self.conn.cursor()
        cur.execute(
            'UPDATE sensor_sessions SET end_at=?, notes=COALESCE(?, notes) WHERE session_id=? AND patient_id=?',
            (time.time(), notes, session_id, patient_id),
        )
        changed = cur.rowcount > 0
        self.conn.commit()
        if changed:
            self.record_wearable_event(patient_id, session_id, 'SESSION_ENDED', {'notes': notes or ''})
        return changed

    def save_raw_wearable_packet(self, patient_id: str, session_id: Optional[str], payload_base64: str, transport: str = 'BLE', quality: Optional[float] = None, label: str = 'REAL') -> str:
        packet_id = str(uuid.uuid4())
        self.conn.execute(
            'INSERT INTO raw_wearable_packets(packet_id, patient_id, session_id, timestamp, payload_base64, transport, quality, label) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (packet_id, patient_id, session_id, time.time(), payload_base64, transport, quality, label),
        )
        self.conn.commit()
        return packet_id

    def save_feature_vector(self, patient_id: str, session_id: Optional[str], feature_vector: Any, source: str = 'wearable', algorithm_version: Optional[str] = None, label: str = 'REAL') -> str:
        data = feature_vector.as_dict() if hasattr(feature_vector, 'as_dict') else dict(feature_vector)
        feature_id = str(uuid.uuid4())
        self.conn.execute(
            'INSERT INTO feature_vectors(feature_id, patient_id, session_id, timestamp_s, data_json, source, algorithm_version, label) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (feature_id, patient_id, session_id, float(data.get('timestamp_s', time.time())), json.dumps(data, default=str, sort_keys=True), source, algorithm_version, label),
        )
        self.conn.commit()
        return feature_id

    def save_personal_baseline(self, patient_id: str, feature_name: str, stats: Dict[str, Any], algorithm_version: str) -> str:
        baseline_id = str(uuid.uuid4())
        self.conn.execute("""
        INSERT INTO personal_baselines(baseline_id, patient_id, feature_name, median_value, mean_value, std_value, mad_value, sample_count, days_covered, confidence, algorithm_version, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(patient_id, feature_name) DO UPDATE SET
            median_value=excluded.median_value, mean_value=excluded.mean_value,
            std_value=excluded.std_value, mad_value=excluded.mad_value,
            sample_count=excluded.sample_count, days_covered=excluded.days_covered,
            confidence=excluded.confidence, algorithm_version=excluded.algorithm_version,
            updated_at=excluded.updated_at
        """, (
            baseline_id, patient_id, feature_name, stats.get('median'), stats.get('mean'),
            stats.get('std'), stats.get('mad'), int(stats.get('sample_count', 0)),
            float(stats.get('days_covered', 0)), float(stats.get('confidence', 0)),
            algorithm_version, time.time()
        ))
        self.conn.commit()
        row = self.conn.execute('SELECT baseline_id FROM personal_baselines WHERE patient_id=? AND feature_name=?', (patient_id, feature_name)).fetchone()
        return str(row[0])

    def record_research_label(self, patient_id: str, target: str, label_value: str, source: str, entered_by: Optional[str] = None, notes: str = '') -> str:
        label_id = str(uuid.uuid4())
        self.conn.execute(
            'INSERT INTO research_labels(label_id, patient_id, target, label_value, source, entered_by, timestamp, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (label_id, patient_id, target, label_value, source, entered_by, time.time(), notes),
        )
        self.conn.commit()
        self._log_audit(entered_by, patient_id, 'record_research_label', {'target': target, 'source': source})
        return label_id

    def list_research_labels(self, target: Optional[str] = None) -> List[Dict]:
        if target:
            rows = self.conn.execute('SELECT * FROM research_labels WHERE target=? ORDER BY timestamp DESC', (target,)).fetchall()
        else:
            rows = self.conn.execute('SELECT * FROM research_labels ORDER BY timestamp DESC').fetchall()
        return [dict(r) for r in rows]

    def record_learning_run(self, patient_id: Optional[str], model_name: str, base_model_version: Optional[str], mode: str, status: str, input_sessions: Optional[List[str]] = None, metrics: Optional[Dict] = None, limitations: str = '') -> str:
        run_id = str(uuid.uuid4())
        self.conn.execute(
            'INSERT INTO learning_runs(run_id, patient_id, model_name, base_model_version, mode, started_at, completed_at, status, input_sessions_json, metrics_json, limitations, label) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (run_id, patient_id, model_name, base_model_version, mode, time.time(), time.time(), status, json.dumps(input_sessions or []), json.dumps(metrics or {}, sort_keys=True), limitations, 'RESEARCH'),
        )
        self.conn.commit()
        return run_id

    def list_wearable_events(self, patient_id: str, limit: int = 500) -> List[Dict]:
        rows = self.conn.execute('SELECT * FROM wearable_events WHERE patient_id=? ORDER BY timestamp DESC LIMIT ?', (patient_id, limit)).fetchall()
        return [dict(r) for r in rows]

    def list_feature_vectors(self, patient_id: str, limit: int = 5000) -> List[Dict]:
        rows = self.conn.execute('SELECT * FROM feature_vectors WHERE patient_id=? ORDER BY timestamp_s DESC LIMIT ?', (patient_id, limit)).fetchall()
        return [dict(r) for r in rows]

    def _seed_demo_providers(self):
        """Seed demo providers for prototype - clearly marked demo."""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM providers")
        if cur.fetchone()["cnt"] > 0:
            return

        demo_providers = [
            {
                "provider_id": "demo_doc_001",
                "name": "Dr. Priya Sharma (Demo)",
                "type": "doctor",
                "specialty": "Gynecology",
                "address": "123 Health Street, Ghaziabad, UP 201001",
                "latitude": 28.6692,
                "longitude": 77.4538,
                "distance_km": 1.2,
                "opening_hours": "Mon-Sat 9AM-6PM",
                "services_json": json.dumps(["PCOS Consultation", "Gynecology", "Ultrasound"]),
                "contact_info": "demo@example.com | +91 90000 00001",
                "verification_status": "demo",
                "is_demo": 1,
            },
            {
                "provider_id": "demo_clinic_001",
                "name": "ABC Women's Clinic (Demo)",
                "type": "clinic",
                "specialty": "Gynecology & Obstetrics",
                "address": "456 Care Avenue, Ghaziabad, UP 201002",
                "latitude": 28.6750,
                "longitude": 77.4600,
                "distance_km": 2.1,
                "opening_hours": "Mon-Sun 8AM-8PM",
                "services_json": json.dumps(["Gynecology", "Ultrasound", "Lab Tests", "PCOS Screening"]),
                "contact_info": "clinic-demo@example.com | +91 90000 00002",
                "verification_status": "demo",
                "is_demo": 1,
            },
            {
                "provider_id": "demo_lab_001",
                "name": "City Diagnostic Lab (Demo)",
                "type": "lab",
                "specialty": "Pathology",
                "address": "789 Lab Road, Ghaziabad, UP 201003",
                "latitude": 28.6800,
                "longitude": 77.4700,
                "distance_km": 3.5,
                "opening_hours": "Mon-Sat 7AM-7PM",
                "services_json": json.dumps(["Hormone Tests", "Blood Tests", "Ultrasound"]),
                "contact_info": "lab-demo@example.com | +91 90000 00003",
                "verification_status": "demo",
                "is_demo": 1,
            },
            {
                "provider_id": "demo_supply_001",
                "name": "Health Monitoring Supplies (Demo)",
                "type": "supply",
                "specialty": "Medical Supplies",
                "address": "321 Supply Street, Ghaziabad, UP 201004",
                "latitude": 28.6650,
                "longitude": 77.4400,
                "distance_km": 0.8,
                "opening_hours": "Mon-Sat 9AM-9PM",
                "services_json": json.dumps(["Sensor Accessories", "Monitoring Equipment", "Menstrual Care"]),
                "contact_info": "supply-demo@example.com | +91 90000 00004",
                "verification_status": "demo",
                "is_demo": 1,
            },
        ]

        for p in demo_providers:
            cur.execute("""
            INSERT OR IGNORE INTO providers 
            (provider_id, name, type, specialty, address, latitude, longitude, distance_km, 
             opening_hours, services_json, contact_info, verification_status, is_demo, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p["provider_id"], p["name"], p["type"], p["specialty"], p["address"],
                p["latitude"], p["longitude"], p["distance_km"], p["opening_hours"],
                p["services_json"], p["contact_info"], p["verification_status"], p["is_demo"],
                time.time(), time.time()
            ))

        # Demo supplies
        demo_supplies = [
            {"supply_id": "supply_001", "name": "MAX30102 Sensor Module", "category": "sensor", "description": "PPG sensor for heart rate and SpO2", "provider_id": "demo_supply_001", "price": 450.0, "availability": "In Stock"},
            {"supply_id": "supply_002", "name": "MPU6050 Motion Sensor", "category": "sensor", "description": "Motion and activity tracking", "provider_id": "demo_supply_001", "price": 250.0, "availability": "In Stock"},
            {"supply_id": "supply_003", "name": "DS18B20 Temperature Sensor", "category": "sensor", "description": "Skin temperature monitoring", "provider_id": "demo_supply_001", "price": 150.0, "availability": "In Stock"},
            {"supply_id": "supply_004", "name": "Wrist Band for Pod", "category": "accessory", "description": "Comfortable wrist strap for wearable pod", "provider_id": "demo_supply_001", "price": 200.0, "availability": "In Stock"},
            {"supply_id": "supply_005", "name": "Menstrual Care Kit (Demo)", "category": "menstrual", "description": "Demo product - educational", "provider_id": "demo_supply_001", "price": 300.0, "availability": "In Stock"},
        ]

        for s in demo_supplies:
            cur.execute("""
            INSERT OR IGNORE INTO supplies (supply_id, name, category, description, provider_id, price, availability, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (s["supply_id"], s["name"], s["category"], s["description"], s["provider_id"], s["price"], s["availability"], time.time()))

        self.conn.commit()

    # User management
    def create_user(self, username: str, password: str, role: str) -> str:
        user_id = str(uuid.uuid4())
        password_hash = self._hash_password(password)
        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO users (user_id, username, password_hash, role, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, password_hash, role, time.time()))
        self.conn.commit()
        self._log_audit(user_id, None, "create_user", {"username": username, "role": role})
        return user_id

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND is_active=1", (username,))
        row = cur.fetchone()
        if row and not self._verify_password(password, row["password_hash"]):
            row = None
        if row:
            cur.execute("UPDATE users SET last_login=? WHERE user_id=?", (time.time(), row["user_id"]))
            self.conn.commit()
            self._log_audit(row["user_id"], None, "login", {"username": username})
            return dict(row)
        return None

    @staticmethod
    def _hash_password(password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
        return "pbkdf2_sha256$200000$" + salt.hex() + "$" + digest.hex()

    @staticmethod
    def _verify_password(password: str, stored: str) -> bool:
        if stored.startswith("pbkdf2_sha256$"):
            try:
                _, rounds, salt_hex, digest_hex = stored.split("$", 3)
                digest = hashlib.pbkdf2_hmac(
                    "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(rounds)
                )
                return secrets.compare_digest(digest.hex(), digest_hex)
            except (ValueError, TypeError):
                return False
        legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return secrets.compare_digest(legacy, stored)

    # Patient management
    def create_patient(self, user_id: Optional[str] = None, display_name: Optional[str] = None, age_years: Optional[float] = None, bmi: Optional[float] = None, anonymous_id: Optional[str] = None, patient_id: Optional[str] = None) -> str:
        patient_id = patient_id or str(uuid.uuid4())
        if anonymous_id is None:
            # Ensure unique anonymous_id with uuid fallback if collision
            for _ in range(5):
                candidate = f"P{int(time.time()*1000) % 100000:05d}{uuid.uuid4().hex[:2]}"
                cur = self.conn.cursor()
                cur.execute("SELECT 1 FROM patients WHERE anonymous_id=?", (candidate,))
                if not cur.fetchone():
                    anonymous_id = candidate
                    break
            if anonymous_id is None:
                anonymous_id = f"P{uuid.uuid4().hex[:8]}"
        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO patients (patient_id, user_id, anonymous_id, display_name, age_years, bmi, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (patient_id, user_id, anonymous_id, display_name, age_years, bmi, time.time(), time.time()))
        self.conn.commit()
        self._log_audit(user_id, patient_id, "create_patient", {"anonymous_id": anonymous_id})
        return patient_id

    def get_patient(self, patient_id: str) -> Optional[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM patients WHERE patient_id=?", (patient_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def list_patients(self, doctor_id: Optional[str] = None, include_archived: bool = False) -> List[Dict]:
        cur = self.conn.cursor()
        if doctor_id:
            # Only authorized patients for doctor
            cur.execute("""
            SELECT p.* FROM patients p
            JOIN patient_doctor_access a ON p.patient_id = a.patient_id
            WHERE a.doctor_id=? AND a.is_active=1 AND (p.is_archived=0 OR ?)
            """, (doctor_id, 1 if include_archived else 0))
        else:
            if include_archived:
                cur.execute("SELECT * FROM patients")
            else:
                cur.execute("SELECT * FROM patients WHERE is_archived=0")
        return [dict(row) for row in cur.fetchall()]

    def archive_patient(self, patient_id: str, archived: bool = True, user_id: Optional[str] = None) -> bool:
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE patients SET is_archived=?, updated_at=? WHERE patient_id=?",
            (1 if archived else 0, time.time(), patient_id),
        )
        changed = cur.rowcount > 0
        self.conn.commit()
        if changed:
            self._log_audit(
                user_id, patient_id,
                "archive_patient" if archived else "unarchive_patient",
                {"archived": archived},
            )
        return changed

    def list_sessions(self, patient_id: str) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM sensor_sessions WHERE patient_id=? ORDER BY start_at DESC",
            (patient_id,),
        )
        return [dict(row) for row in cur.fetchall()]

    def get_session(self, session_id: str, patient_id: Optional[str] = None) -> Optional[Dict]:
        cur = self.conn.cursor()
        if patient_id is None:
            cur.execute("SELECT * FROM sensor_sessions WHERE session_id=?", (session_id,))
        else:
            cur.execute(
                "SELECT * FROM sensor_sessions WHERE session_id=? AND patient_id=?",
                (session_id, patient_id),
            )
        row = cur.fetchone()
        return dict(row) if row else None

    def search_patients(self, query: str) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("""
        SELECT * FROM patients 
        WHERE anonymous_id LIKE ? OR display_name LIKE ?
        """, (f"%{query}%", f"%{query}%"))
        return [dict(row) for row in cur.fetchall()]

    # Symptoms
    def log_symptom(self, patient_id: str, symptom_type: str, severity: Optional[int] = None, notes: Optional[str] = None) -> str:
        symptom_id = str(uuid.uuid4())
        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO symptoms (symptom_id, patient_id, symptom_type, severity, notes, logged_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (symptom_id, patient_id, symptom_type, severity, notes, time.time()))
        self.conn.commit()
        return symptom_id

    # Cycles
    def log_cycle(self, patient_id: str, start_date: float, cycle_length: Optional[int] = None, irregularity: Optional[str] = None, notes: Optional[str] = None) -> str:
        cycle_id = str(uuid.uuid4())
        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO cycles (cycle_id, patient_id, start_date, cycle_length_days, irregularity, notes, logged_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cycle_id, patient_id, start_date, cycle_length, irregularity, notes, time.time()))
        self.conn.commit()
        return cycle_id

    # Sensor sessions
    def start_study(self, patient_id: str, duration_hours: float = 48.0, protocol: Optional[Dict[str, Any]] = None, label: str = "REAL") -> str:
        study_id = str(uuid.uuid4())
        now = time.time()
        self.conn.execute(
            'INSERT INTO research_studies(study_id, patient_id, started_at, target_end_at, protocol_json, label) VALUES (?, ?, ?, ?, ?, ?)',
            (study_id, patient_id, now, now + float(duration_hours) * 3600.0, json.dumps(protocol or {}, sort_keys=True), label),
        )
        self.conn.commit()
        self.record_wearable_event(patient_id, None, 'STUDY_STARTED', {'study_id': study_id, 'duration_hours': duration_hours}, label=label)
        return study_id

    def get_active_study(self, patient_id: str) -> Optional[Dict]:
        row = self.conn.execute(
            "SELECT * FROM research_studies WHERE patient_id=? AND status='ACTIVE' ORDER BY started_at DESC LIMIT 1",
            (patient_id,),
        ).fetchone()
        return dict(row) if row else None

    def end_study(self, patient_id: str, study_id: str, status: str = "COMPLETED") -> bool:
        cur = self.conn.cursor()
        cur.execute(
            'UPDATE research_studies SET ended_at=?, status=? WHERE study_id=? AND patient_id=?',
            (time.time(), status, study_id, patient_id),
        )
        changed = cur.rowcount > 0
        self.conn.commit()
        if changed:
            self.record_wearable_event(patient_id, None, 'STUDY_ENDED', {'study_id': study_id, 'status': status})
        return changed

    def create_session(self, patient_id: str, source: str, label: str, notes: Optional[str] = None, study_id: Optional[str] = None) -> str:
        session_id = str(uuid.uuid4())
        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO sensor_sessions (session_id, patient_id, study_id, source, start_at, label, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, patient_id, study_id, source, time.time(), label, notes, time.time()))
        self.conn.commit()
        if study_id:
            self.record_wearable_event(patient_id, session_id, 'SESSION_STARTED', {'study_id': study_id, 'label': label}, label=label)
        return session_id

    # Providers - care discovery
    def list_providers(self, provider_type: Optional[str] = None, verified_only: bool = False) -> List[Dict]:
        cur = self.conn.cursor()
        query = "SELECT * FROM providers WHERE 1=1"
        params = []
        if provider_type:
            query += " AND type=?"
            params.append(provider_type)
        if verified_only:
            query += " AND verification_status='verified'"
        query += " ORDER BY distance_km ASC"
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]

    def search_providers(self, query: str) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("""
        SELECT * FROM providers 
        WHERE name LIKE ? OR specialty LIKE ? OR address LIKE ?
        ORDER BY distance_km ASC
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        return [dict(row) for row in cur.fetchall()]

    def get_nearby_providers(self, latitude: float, longitude: float, radius_km: float = 10.0) -> List[Dict]:
        # Simple distance calculation for demo - in real app use haversine
        cur = self.conn.cursor()
        cur.execute("""
        SELECT * FROM providers 
        WHERE distance_km <= ?
        ORDER BY distance_km ASC
        """, (radius_km,))
        return [dict(row) for row in cur.fetchall()]

    # Supplies
    def list_supplies(self, category: Optional[str] = None) -> List[Dict]:
        cur = self.conn.cursor()
        if category:
            cur.execute("SELECT * FROM supplies WHERE category=?", (category,))
        else:
            cur.execute("SELECT * FROM supplies")
        return [dict(row) for row in cur.fetchall()]

    # Reports
    def create_report(self, patient_id: str, report_type: str, content_text: str, created_by: Optional[str] = None, label: str = "REAL") -> str:
        report_id = str(uuid.uuid4())
        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO reports (report_id, patient_id, report_type, content_text, created_at, created_by, label)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (report_id, patient_id, report_type, content_text, time.time(), created_by, label))
        self.conn.commit()
        return report_id

    # Doctor notes
    def add_doctor_note(self, patient_id: str, doctor_id: str, note_text: str) -> str:
        note_id = str(uuid.uuid4())
        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO doctor_notes (note_id, patient_id, doctor_id, note_text, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (note_id, patient_id, doctor_id, note_text, time.time(), time.time()))
        self.conn.commit()
        self._log_audit(doctor_id, patient_id, "add_doctor_note", {"note_id": note_id})
        return note_id

    def get_doctor_notes(self, patient_id: str) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM doctor_notes WHERE patient_id=? ORDER BY created_at DESC", (patient_id,))
        return [dict(row) for row in cur.fetchall()]

    # Access control
    def grant_access(self, patient_id: str, doctor_id: str, granted_by: str) -> str:
        access_id = str(uuid.uuid4())
        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO patient_doctor_access (access_id, patient_id, doctor_id, granted_at, granted_by)
        VALUES (?, ?, ?, ?, ?)
        """, (access_id, patient_id, doctor_id, time.time(), granted_by))
        self.conn.commit()
        self._log_audit(granted_by, patient_id, "grant_access", {"doctor_id": doctor_id})
        return access_id

    def check_access(self, patient_id: str, doctor_id: str) -> bool:
        cur = self.conn.cursor()
        cur.execute("""
        SELECT * FROM patient_doctor_access 
        WHERE patient_id=? AND doctor_id=? AND is_active=1
        """, (patient_id, doctor_id))
        return cur.fetchone() is not None

    # Audit
    def _log_audit(self, user_id: Optional[str], patient_id: Optional[str], action: str, details: Optional[Dict] = None):
        audit_id = str(uuid.uuid4())
        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO audit_records (audit_id, user_id, patient_id, action, details_json, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (audit_id, user_id, patient_id, action, json.dumps(details) if details else None, time.time()))
        self.conn.commit()

    # Export/Import
    def export_patient_data(self, patient_id: str) -> Dict:
        """Export a complete patient-scoped local package for phone → doctor sync."""
        patient = self.get_patient(patient_id)
        if not patient:
            return {}
        cur = self.conn.cursor()
        package = {'schema_version': '1.1', 'exported_at': time.time(), 'label': 'EXPORTED_PACKAGE', 'patient': patient}

        for key, table, where, params in [
            ('research_studies', 'research_studies', 'patient_id=?', (patient_id,)),
            ('research_labels', 'research_labels', 'patient_id=?', (patient_id,)),
            ('profiles', 'profiles', 'patient_id=?', (patient_id,)),
            ('symptoms', 'symptoms', 'patient_id=?', (patient_id,)),
            ('cycles', 'cycles', 'patient_id=?', (patient_id,)),
            ('sessions', 'sensor_sessions', 'patient_id=?', (patient_id,)),
            ('wearable_devices', 'wearable_devices', 'patient_id=?', (patient_id,)),
            ('wearable_events', 'wearable_events', 'patient_id=?', (patient_id,)),
            ('feature_vectors', 'feature_vectors', 'patient_id=?', (patient_id,)),
            ('raw_wearable_packets', 'raw_wearable_packets', 'patient_id=?', (patient_id,)),
            ('reports', 'reports', 'patient_id=?', (patient_id,)),
            ('doctor_notes', 'doctor_notes', 'patient_id=?', (patient_id,)),
            ('personal_baselines', 'personal_baselines', 'patient_id=?', (patient_id,)),
            ('learning_runs', 'learning_runs', 'patient_id=?', (patient_id,)),
            ('model_results', 'model_results', 'patient_id=?', (patient_id,)),
            ('analysis_results', 'analysis_results', 'patient_id=?', (patient_id,)),
        ]:
            cur.execute(f'SELECT * FROM {table} WHERE {where}', params)
            package[key] = [dict(r) for r in cur.fetchall()]

        session_ids = [r['session_id'] for r in package['sessions']]
        placeholders = ','.join('?' for _ in session_ids)
        if session_ids:
            for key, table in [('ppg_data', 'ppg_data'), ('hrv_data', 'hrv_data'), ('gsr_data', 'gsr_data'), ('motion_data', 'motion_data'), ('temperature_data', 'temperature_data'), ('sensor_quality', 'sensor_quality')]:
                cur.execute(f'SELECT * FROM {table} WHERE session_id IN ({placeholders})', tuple(session_ids))
                package[key] = [dict(r) for r in cur.fetchall()]
        else:
            for key in ('ppg_data','hrv_data','gsr_data','motion_data','temperature_data','sensor_quality'):
                package[key] = []

        package['note'] = 'Complete local patient research package. DEMO_DATA/REAL labels are preserved. Wear/removal/reconnection gaps are events, never silently filled.'
        return package

    def import_patient_data(self, data: Dict) -> str:
        """Merge a patient-scoped package while preserving stable IDs and provenance."""
        patient_data = data.get('patient') or {}
        if not patient_data or not patient_data.get('patient_id'):
            raise ValueError('No stable patient identity in package')

        patient_id = str(patient_data['patient_id'])
        existing = self.get_patient(patient_id)
        if not existing:
            anon = patient_data.get('anonymous_id') or f'P{uuid.uuid4().hex[:8]}'
            clash = self.conn.execute('SELECT patient_id FROM patients WHERE anonymous_id=?', (anon,)).fetchone()
            if clash and clash[0] != patient_id:
                anon = f'{anon}-SYNC-{uuid.uuid4().hex[:4]}'
            self.create_patient(
                user_id=patient_data.get('user_id'), display_name=patient_data.get('display_name'),
                age_years=patient_data.get('age_years'), bmi=patient_data.get('bmi'),
                anonymous_id=anon, patient_id=patient_id
            )

        merge_tables = [
            ('research_studies','study_id'), ('research_labels','label_id'),
            ('profiles','profile_id'), ('symptoms','symptom_id'), ('cycles','cycle_id'),
            ('sessions','session_id'), ('wearable_devices','device_id'), ('wearable_events','event_id'),
            ('feature_vectors','feature_id'), ('raw_wearable_packets','packet_id'), ('reports','report_id'), ('doctor_notes','note_id'),
            ('personal_baselines','baseline_id'), ('learning_runs','run_id'),
            ('model_results','result_id'), ('analysis_results','analysis_id'),
        ]
        for key, pk in merge_tables:
            rows = data.get(key) or []
            if not rows:
                continue
            for row in rows:
                # Preserve the primary key for stable synchronization except where
                # the table has a unique composite key and a regenerated UUID is safer.
                columns = list(row.keys())
                values = [row[col] for col in columns]
                qs = ','.join('?' for _ in columns)
                self.conn.execute(f'INSERT OR IGNORE INTO {self._validate_identifier(key)} ({",".join(columns)}) VALUES ({qs})', values)

        for key in ('ppg_data','hrv_data','gsr_data','motion_data','temperature_data','sensor_quality'):
            for row in data.get(key) or []:
                columns = list(row.keys())
                values = [row[col] for col in columns]
                qs = ','.join('?' for _ in columns)
                self.conn.execute(f'INSERT OR IGNORE INTO {self._validate_identifier(key)} ({",".join(columns)}) VALUES ({qs})', values)

        self.conn.commit()
        self._log_audit(None, patient_id, 'import_patient_data', {'source_label': data.get('label'), 'schema_version': data.get('schema_version')})
        return patient_id

    @staticmethod
    def _validate_identifier(identifier: str) -> str:
        allowed = {'profiles','symptoms','cycles','sensor_sessions','wearable_devices','wearable_events','feature_vectors','reports','doctor_notes','personal_baselines','learning_runs','model_results','analysis_results','ppg_data','hrv_data','gsr_data','motion_data','temperature_data','sensor_quality','raw_wearable_packets'}
        if identifier not in allowed:
            raise ValueError(f'Unsupported table: {identifier}')
        return identifier

    def backup_database(self, backup_path: Path) -> Path:
        """Backup database file."""
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        # SQLite backup
        backup_conn = sqlite3.connect(str(backup_path))
        self.conn.backup(backup_conn)
        backup_conn.close()

        return backup_path

    def close(self):
        self.conn.close()
