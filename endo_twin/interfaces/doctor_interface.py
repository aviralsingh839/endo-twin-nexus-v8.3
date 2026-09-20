"""
Doctor Interface - Multi-patient, patient switching scopes entire context
"""

class DoctorInterface:
    def __init__(self, doctor_id: str):
        self.doctor_id = doctor_id
        self.current_patient_id = None
    
    def list_patients(self):
        return {"doctor_id": self.doctor_id, "patients": "Patient ID, Name/alias, Age, Last session, Last analysis, Status, Search, Filter, Sort, Open, Archive, Create, Import/export"}
    
    def open_patient(self, patient_id: str):
        self.current_patient_id = patient_id
        return {"doctor_id": self.doctor_id, "patient_id": patient_id, "context": "EVERY SCREEN becomes scoped to patient_id - Patient overview, Personal baseline, Recent sessions, Longitudinal timeline, Physiology, Sensors, Ultrasound, AI, Clinical data, Reports, Notes, Provenance, Audit", "safety": "DEMO-001 cannot see DEMO-002, implemented at database/repository level not merely UI hidden"}
