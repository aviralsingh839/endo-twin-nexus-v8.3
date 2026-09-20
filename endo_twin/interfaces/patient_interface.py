"""
Patient Interface - ONE patient only, never global list
"""

class PatientInterface:
    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self.is_single_patient = True  # Must belong to ONE patient
    
    def get_home(self):
        return {"patient_id": self.patient_id, "overview": "Today's overview, data collection status, sensor/device status, recent measurements, signal quality, recent activity, personal baseline status, recent longitudinal change", "disclaimer": "Data quality: Good - understandable language, not raw technical"}
    
    def get_my_health(self):
        return {"patient_id": self.patient_id, "baseline": "Personal baseline", "trends": "Longitudinal trends", "changes": "Recent changes", "measurements": "Available measurements", "completeness": "Data completeness", "model_outputs": "Research-model outputs where appropriate clearly distinguished model inference from measurements"}
