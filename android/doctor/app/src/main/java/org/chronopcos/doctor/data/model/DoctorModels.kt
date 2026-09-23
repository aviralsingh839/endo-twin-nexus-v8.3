package org.chronopcos.doctor.data.model

/**
 * ENDO-TWIN Doctor Models - Multi-patient application
 * Doctor sees Patient ID, Name/alias, Age, Last session, Last analysis, Status
 * Search, Filter, Sort, Open, Archive, Create, Import/export
 * Opening patient CP-0001 must switch entire context to CP-0001
 * Tabs: OVERVIEW, TIMELINE, PHYSIOLOGY, SENSORS, ULTRASOUND, AI/MODELS, CLINICAL DATA, REPORTS, NOTES, PROVENANCE, AUDIT
 * Everything displayed must belong to that patient
 * DEMO-001 cannot see DEMO-002 - implemented at database level not merely UI hidden
 */

enum class ProvenanceLabel {
    MEASURED,
    CLINICALLY_ENTERED,
    IMAGE_DERIVED,
    MODEL_INFERRED,
    DEMO_DATA,
    UNKNOWN
}

data class PatientListItem(
    val patientId: String, // Stable ID CP-0001, DEMO-001
    val anonymousId: String,
    val displayName: String?,
    val ageYears: Double?,
    val lastSession: Long?,
    val lastAnalysis: Long?,
    val dataStatus: String,
    val isDemo: Boolean = false
)

data class PatientProfile(
    val patientId: String,
    val anonymousId: String,
    val displayName: String?,
    val ageYears: Double?,
    val bmi: Double?,
    val isDemo: Boolean,
    val overview: String,
    val personalBaseline: String,
    val recentSessions: List<String>,
    val longitudinalTimeline: String
)

data class PhysiologicalData(
    val patientId: String, // Must contain patient_id
    val hr: String, // HR 72 bpm MEASURED quality 0.91 source MAX30102
    val hrv: String, // HRV RMSSD 48 ms DERIVED quality 0.85 limitations PPG less accurate than ECG
    val ppg: String,
    val temperature: String,
    val motion: String,
    val quality: Double,
    val provenance: ProvenanceLabel,
    val isDemo: Boolean = false
)

data class UltrasoundStudy(
    val studyId: String,
    val patientId: String, // Must belong to exactly one patient - ultrasounds patient-specific
    val studyDate: Long,
    val imagePath: String?,
    val quality: Double?,
    val provenance: ProvenanceLabel = ProvenanceLabel.IMAGE_DERIVED,
    val confidence: Double? = null, // None unless computed
    val isDemo: Boolean = false,
    val label: String = "REAL"
)

data class ModelRun(
    val runId: String,
    val patientId: String, // AI runs patient-specific
    val modelName: String, // PCOSModule v8.3.0
    val modelVersion: String,
    val output: String, // pcos_associated_risk low/moderate/high NOT diagnosis
    val confidence: Double?,
    val dataQuality: Double,
    val clinicalValidation: String = "NOT ESTABLISHED",
    val provenance: ProvenanceLabel = ProvenanceLabel.MODEL_INFERRED,
    val explainability: String,
    val limitations: String,
    val isDemo: Boolean = false,
    val createdAt: Long
)

data class Report(
    val reportId: String,
    val patientId: String, // Reports patient-specific
    val reportType: String,
    val contentText: String,
    val createdAt: Long,
    val isDemo: Boolean = false
)

data class DoctorNote(
    val noteId: String,
    val patientId: String, // Must contain patient_id
    val doctorId: String,
    val noteText: String,
    val createdAt: Long
)

data class TimelineEvent(
    val timelineId: String,
    val patientId: String, // Timeline patient-specific
    val eventType: String,
    val eventDate: Long,
    val title: String,
    val description: String,
    val provenance: ProvenanceLabel,
    val isDemo: Boolean = false
)

data class AuditEvent(
    val eventId: String,
    val userId: String?,
    val patientId: String?,
    val action: String,
    val timestamp: Long,
    val isDemo: Boolean = false
)
