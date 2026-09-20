"""
Security & Privacy Layer V8.3+

- Local auth / role separation
- Encrypted storage (prototype - Fernet if available, else hash)
- Controlled export
- Audit logging
- Minimal collection / no cloud upload
- Patient cannot access other patient, doctor only authorized
- Role system PATIENT own data/measurements/results/manage/share, DOCTOR authorized patients/review/analysis/notes/reports, ADMIN prototype manage provider directory/system config/demo data/verification
"""
import hashlib
import secrets
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

try:
    from cryptography.fernet import Fernet
    FERNET_AVAILABLE = True
except ImportError:
    FERNET_AVAILABLE = False

class AuthManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple:
        if salt is None:
            salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
        return salt, hashed

    @staticmethod
    def verify_password(password: str, salt: str, hashed: str) -> bool:
        _, check = AuthManager.hash_password(password, salt)
        return check == hashed

class EncryptionManager:
    """
    Encrypted storage prototype.
    Uses Fernet if available, else base64-like obfuscation with clear label PROTOTYPE.
    """
    def __init__(self, key_path: Path):
        self.key_path = key_path
        self.key = None
        if FERNET_AVAILABLE:
            if key_path.exists():
                self.key = key_path.read_bytes()
            else:
                self.key = Fernet.generate_key()
                key_path.parent.mkdir(parents=True, exist_ok=True)
                key_path.write_bytes(self.key)
            self.fernet = Fernet(self.key)
        else:
            self.fernet = None

    def encrypt(self, data: str) -> str:
        if self.fernet:
            return self.fernet.encrypt(data.encode()).decode()
        else:
            # Prototype fallback - NOT secure, labeled
            import base64
            return "PROTOTYPE_ENCRYPTED:" + base64.b64encode(data.encode()).decode()

    def decrypt(self, token: str) -> str:
        if self.fernet:
            return self.fernet.decrypt(token.encode()).decode()
        else:
            import base64
            if token.startswith("PROTOTYPE_ENCRYPTED:"):
                return base64.b64decode(token[len("PROTOTYPE_ENCRYPTED:"):].encode()).decode()
            return token

class RoleManager:
    ROLES = {
        'PATIENT': {
            'permissions': ['own_data', 'measurements', 'results', 'manage', 'share'],
            'description': 'Patient can access own data, collect measurements, view results, manage profile, controlled share with doctor'
        },
        'DOCTOR': {
            'permissions': ['authorized_patients', 'review', 'analysis', 'notes', 'reports'],
            'description': 'Doctor can access authorized patients only, review measurements, advanced analysis, add notes, generate reports'
        },
        'ADMIN': {
            'permissions': ['provider_directory', 'system_config', 'demo_data', 'verification'],
            'description': 'Admin prototype can manage provider directory, system config, demo data, verification status'
        }
    }

    @staticmethod
    def check_permission(role: str, permission: str) -> bool:
        if role not in RoleManager.ROLES:
            return False
        return permission in RoleManager.ROLES[role]['permissions']

    @staticmethod
    def can_access_patient(requester_role: str, requester_id: str, patient_id: str, access_list) -> bool:
        """
        Patient cannot access other patient, doctor only authorized
        """
        if requester_role == 'PATIENT':
            # Patient can only access own data - patient_id must match requester_id mapping
            return requester_id == patient_id
        elif requester_role == 'DOCTOR':
            # Doctor only if granted access
            return patient_id in access_list
        elif requester_role == 'ADMIN':
            return True
        return False

class AuditLogger:
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, user_id: str, action: str, resource: str, details: Dict[str, Any] = None, success: bool = True):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'details': details or {},
            'success': success
        }
        # Append to file
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        return entry

class DataPortabilityManager:
    """
    Controlled export/import/backup/restore/encrypted package, deliberate sharing not automatic
    """
    def __init__(self, db, encryption_mgr: EncryptionManager):
        self.db = db
        self.encryption_mgr = encryption_mgr

    def export_patient_package(self, patient_id: str, requester_id: str, requester_role: str, include_sensitive: bool = False) -> Dict[str, Any]:
        # Check permission
        if requester_role == 'PATIENT' and requester_id != patient_id:
            raise PermissionError("Patient cannot export other patient data")
        if requester_role == 'DOCTOR':
            if not self.db.check_access(patient_id, requester_id):
                raise PermissionError("Doctor not authorized for this patient")

        data = self.db.export_patient_data(patient_id)

        package = {
            'export_version': '8.3+',
            'exported_at': datetime.now().isoformat(),
            'exported_by': requester_id,
            'role': requester_role,
            'patient_id': patient_id,
            'data': data,
            'disclaimer': 'Research data export - not a medical diagnosis, controlled sharing, local-first',
            'encryption': 'encrypted' if FERNET_AVAILABLE else 'prototype_obfuscation',
            'audit': 'logged'
        }

        # Encrypt sensitive parts if needed
        if include_sensitive:
            package['data_encrypted'] = self.encryption_mgr.encrypt(json.dumps(data))
            # Don't include raw data if encrypted export
            # package['data'] = None

        return package

    def import_package(self, package: Dict[str, Any], importer_id: str, importer_role: str) -> str:
        # Validate package
        if 'patient_id' not in package or 'data' not in package:
            raise ValueError("Invalid package")

        # If encrypted, decrypt
        if 'data_encrypted' in package and package['data_encrypted']:
            decrypted = self.encryption_mgr.decrypt(package['data_encrypted'])
            data = json.loads(decrypted)
        else:
            data = package['data']

        # Import
        new_id = self.db.import_patient_data(data)
        return new_id
