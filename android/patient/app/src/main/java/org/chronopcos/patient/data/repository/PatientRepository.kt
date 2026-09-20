package org.chronopcos.patient.data.repository

import org.chronopcos.patient.data.database.PatientDao
import org.chronopcos.patient.data.model.*

/**
 * Patient Repository - Single patient only
 * Patient must NEVER see global list of all patients
 * Represents CURRENT PATIENT with stable patient ID
 * Clean interface between Android app ↔ data/repository ↔ CHRONO-PCOS data architecture
 */

class PatientRepository(
    private val patientDao: PatientDao
) {
    // Current patient - stable ID
    private var currentPatientId: String = "DEMO-001" // Default demo, would be set from DataStore in real app

    fun getCurrentPatientId(): String = currentPatientId

    fun setCurrentPatientId(patientId: String) {
        currentPatientId = patientId
    }

    suspend fun getCurrentPatient(): PatientIdentity? {
        val entity = patientDao.getCurrentPatient() ?: patientDao.getPatient(currentPatientId)
        return entity?.let {
            PatientIdentity(
                patientId = it.patientId,
                anonymousId = it.anonymousId,
                displayName = it.displayName,
                ageYears = it.ageYears,
                bmi = it.bmi,
                isDemo = it.isDemo,
                label = if (it.isDemo) "DEMO_DATA" else "USER-ENTERED"
            )
        }
    }

    suspend fun getMeasurements(): List<PhysiologicalMeasurement> {
        val entities = patientDao.getMeasurements(currentPatientId)
        return entities.map {
            PhysiologicalMeasurement(
                measurementId = it.measurementId,
                patientId = it.patientId,
                type = it.type,
                value = it.value,
                unit = it.unit,
                timestamp = it.timestamp,
                quality = it.quality,
                provenance = try { ProvenanceLabel.valueOf(it.provenance) } catch (e: Exception) { ProvenanceLabel.UNKNOWN },
                source = it.source,
                isDemo = it.isDemo
            )
        }
    }

    suspend fun getTimeline(): List<TimelineEvent> {
        val entities = patientDao.getTimeline(currentPatientId)
        return entities.map {
            TimelineEvent(
                timelineId = it.timelineId,
                patientId = it.patientId,
                eventType = it.eventType,
                eventDate = it.eventDate,
                title = it.title,
                description = it.description,
                provenance = try { ProvenanceLabel.valueOf(it.provenance) } catch (e: Exception) { ProvenanceLabel.UNKNOWN },
                isDemo = it.isDemo
            )
        }
    }

    suspend fun getReports(): List<Report> {
        val entities = patientDao.getReports(currentPatientId)
        return entities.map {
            Report(
                reportId = it.reportId,
                patientId = it.patientId,
                reportType = it.reportType,
                contentText = it.contentText,
                createdAt = it.createdAt,
                isDemo = it.isDemo
            )
        }
    }

    fun getDemoProviders(): List<Provider> {
        return listOf(
            Provider(
                providerId = "demo_doc_001",
                name = "Dr. Priya Sharma (Demo)",
                type = "doctor",
                specialty = "Gynecology",
                address = "123 Health Street, Ghaziabad, UP 201001",
                distanceKm = 1.2,
                openingHours = "Mon-Sat 9AM-6PM",
                services = listOf("PCOS Consultation", "Gynecology", "Ultrasound"),
                contactInfo = "demo@example.com | +91 90000 00001",
                verificationStatus = "demo",
                isDemo = true
            ),
            Provider(
                providerId = "demo_clinic_001",
                name = "ABC Women's Clinic (Demo)",
                type = "clinic",
                specialty = "Gynecology & Obstetrics",
                address = "456 Care Avenue, Ghaziabad, UP 201002",
                distanceKm = 2.1,
                openingHours = "Mon-Sun 8AM-8PM",
                services = listOf("Gynecology", "Ultrasound", "Lab Tests", "PCOS Screening"),
                contactInfo = "clinic-demo@example.com | +91 90000 00002",
                verificationStatus = "demo",
                isDemo = true
            )
        )
    }

    fun getPersonalBaseline(): List<PersonalBaseline> {
        // Would query personal_baseline table in real implementation
        return listOf(
            PersonalBaseline(
                baselineId = "baseline_hr",
                patientId = currentPatientId,
                featureName = "hr",
                meanValue = 71.0,
                medianValue = 70.0,
                stdValue = 2.0,
                confidence = 0.85,
                minObservations = 10,
                provenance = ProvenanceLabel.MEASURED
            )
        )
    }

    fun getChronoMetabolicComponents(): List<ChronoMetabolicComponent> {
        return listOf(
            ChronoMetabolicComponent(
                name = "circadian_rhythm",
                value = "moderate disruption - model-inferred",
                category = "experimental_research",
                quality = 0.85,
                source = "PPG-derived sleep-wake estimation, model-inferred",
                limitations = "Sleep-wake from wrist PPG is model-inferred, not polysomnography, requires validation",
                explainability = "Estimated from HR/HRV circadian variation, 24h pattern analysis"
            ),
            ChronoMetabolicComponent(
                name = "autonomic_regulation",
                value = "RMSSD 48 ms - parasympathetic activity",
                category = "derived_feature",
                quality = 0.85,
                source = "PPG-derived HRV, time-domain RMSSD",
                limitations = "PPG-derived HRV less accurate than ECG, motion artifacts affect",
                explainability = "RMSSD reflects parasympathetic activity, lower values may indicate autonomic dysregulation research signal"
            )
        )
    }
}
