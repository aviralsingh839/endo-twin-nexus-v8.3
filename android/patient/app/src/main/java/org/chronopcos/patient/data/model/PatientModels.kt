package org.chronopcos.patient.data.model

/**
 * ENDO-TWIN Patient Models - Single patient only, never global list
 * Patient must NEVER see global list of all patients
 * Represents CURRENT PATIENT with stable patient ID
 * Provenance: MEASURED, CLINICALLY_ENTERED, IMAGE_DERIVED, MODEL_INFERRED, DEMO_DATA, UNKNOWN
 */

enum class ProvenanceLabel {
    MEASURED,              // Directly measured HR, skin temp, motion
    CLINICALLY_ENTERED,    // USER-ENTERED age, BMI, cycle, symptoms
    IMAGE_DERIVED,         // Cyst size, volume, morphology from ultrasound
    MODEL_INFERRED,        // Sleep regularity, circadian disruption, HRV derived, risk signals
    DEMO_DATA,             // Demo providers, demo patients, synthetic
    UNKNOWN                // If cannot reliably extract return UNKNOWN never invent
}

data class PatientIdentity(
    val patientId: String,  // Stable ID like CP-0001, DEMO-001
    val anonymousId: String, // PXXXXX
    val displayName: String? = null,
    val ageYears: Double? = null,
    val bmi: Double? = null,
    val isDemo: Boolean = false,
    val label: String = "USER-ENTERED"
)

data class PhysiologicalMeasurement(
    val measurementId: String,
    val patientId: String,  // Must contain patient_id - no cross-contamination
    val type: String, // hr, hrv, ppg, temperature, motion, sleep, activity
    val value: Double,
    val unit: String,
    val timestamp: Long,
    val quality: Double, // 0-1
    val provenance: ProvenanceLabel,
    val source: String, // MAX30102, DS18B20, MPU6050, USER-ENTERED
    val confidence: Double? = null, // None unless computed, never hard-code fake
    val limitations: String = "",
    val isDemo: Boolean = false
)

data class TimelineEvent(
    val timelineId: String,
    val patientId: String, // Must contain patient_id
    val eventType: String, // sensor_session, symptom_entry, cycle_event, clinical_entry, ultrasound_study, analysis, model_run, report_generated
    val eventDate: Long,
    val title: String,
    val description: String,
    val provenance: ProvenanceLabel,
    val isDemo: Boolean = false
)

data class SymptomEntry(
    val symptomId: String,
    val patientId: String,
    val symptomType: String,
    val severity: Int? = null,
    val notes: String? = null,
    val loggedAt: Long,
    val label: String = "USER-ENTERED"
)

data class CycleEvent(
    val eventId: String,
    val patientId: String,
    val eventType: String, // cycle_start, cycle_end, ovulation, symptom, note
    val eventDate: Long,
    val cycleLengthDays: Int? = null,
    val irregularity: String? = null,
    val notes: String? = null,
    val provenance: ProvenanceLabel = ProvenanceLabel.CLINICALLY_ENTERED,
    val isDemo: Boolean = false
)

data class UltrasoundStudy(
    val studyId: String,
    val patientId: String, // Must belong to exactly one patient
    val studyDate: Long,
    val imagePath: String? = null,
    val quality: Double? = null,
    val provenance: ProvenanceLabel = ProvenanceLabel.IMAGE_DERIVED,
    val source: String = "ULTRASOUND",
    val confidence: Double? = null, // None unless computed
    val isDemo: Boolean = false,
    val label: String = "REAL" // REAL, SYNTHETIC, DEMO
)

data class ModelRun(
    val runId: String,
    val patientId: String, // Must contain patient_id - AI runs patient-specific
    val modelName: String, // PCOSModule v8.3.0
    val modelVersion: String,
    val output: String, // pcos_associated_risk low/moderate/high NOT diagnosis
    val confidence: Double? = null,
    val dataQuality: Double,
    val clinicalValidation: String = "NOT ESTABLISHED",
    val provenance: ProvenanceLabel = ProvenanceLabel.MODEL_INFERRED,
    val explainability: String = "",
    val limitations: String = "Research prototype, not clinically validated",
    val isDemo: Boolean = false,
    val createdAt: Long
)

data class Report(
    val reportId: String,
    val patientId: String, // Must contain patient_id - reports patient-specific, never expose another patient's report
    val reportType: String,
    val contentText: String,
    val createdAt: Long,
    val label: String = "REAL",
    val isDemo: Boolean = false
)

data class Provider(
    val providerId: String,
    val name: String,
    val type: String, // doctor, clinic, lab, supply
    val specialty: String? = null,
    val address: String? = null,
    val distanceKm: Double? = null,
    val openingHours: String? = null,
    val services: List<String> = emptyList(),
    val contactInfo: String? = null,
    val verificationStatus: String, // verified, pending, unverified, demo
    val isDemo: Boolean = false
)

data class PersonalBaseline(
    val baselineId: String,
    val patientId: String,
    val featureName: String,
    val meanValue: Double,
    val medianValue: Double,
    val stdValue: Double,
    val confidence: Double,
    val minObservations: Int,
    val provenance: ProvenanceLabel
)

data class ChronoMetabolicComponent(
    val name: String,
    val value: String,
    val category: String, // established_measurement, derived_feature, experimental_research, ml_prediction
    val quality: Double,
    val source: String,
    val limitations: String,
    val explainability: String
)
