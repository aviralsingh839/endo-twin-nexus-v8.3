package org.chronopcos.patient.data.database

import androidx.room.*

/**
 * ENDO-TWIN Patient Database - Local-first SQLite, Room
 * All patient-specific records must contain patient_id
 * Stable IDs, foreign keys, no cross-patient contamination
 * Patient app only sees its own patient data - single patient
 */

@Entity(tableName = "patients")
data class PatientEntity(
    @PrimaryKey val patientId: String, // Stable ID CP-0001, DEMO-001
    val anonymousId: String,
    val displayName: String? = null,
    val ageYears: Double? = null,
    val bmi: Double? = null,
    val isDemo: Boolean = false,
    val createdAt: Long,
    val updatedAt: Long
)

@Entity(
    tableName = "measurements",
    foreignKeys = [ForeignKey(entity = PatientEntity::class, parentColumns = ["patientId"], childColumns = ["patientId"], onDelete = ForeignKey.CASCADE)],
    indices = [Index("patientId")]
)
data class MeasurementEntity(
    @PrimaryKey val measurementId: String,
    val patientId: String, // Must contain patient_id
    val type: String,
    val value: Double,
    val unit: String,
    val timestamp: Long,
    val quality: Double,
    val provenance: String,
    val source: String,
    val isDemo: Boolean = false,
    val createdAt: Long
)

@Entity(
    tableName = "timeline",
    foreignKeys = [ForeignKey(entity = PatientEntity::class, parentColumns = ["patientId"], childColumns = ["patientId"], onDelete = ForeignKey.CASCADE)],
    indices = [Index("patientId")]
)
data class TimelineEntity(
    @PrimaryKey val timelineId: String,
    val patientId: String,
    val eventType: String,
    val eventDate: Long,
    val title: String,
    val description: String,
    val provenance: String,
    val isDemo: Boolean = false,
    val createdAt: Long
)

@Entity(
    tableName = "reports",
    foreignKeys = [ForeignKey(entity = PatientEntity::class, parentColumns = ["patientId"], childColumns = ["patientId"], onDelete = ForeignKey.CASCADE)],
    indices = [Index("patientId")]
)
data class ReportEntity(
    @PrimaryKey val reportId: String,
    val patientId: String, // Reports patient-specific
    val reportType: String,
    val contentText: String,
    val createdAt: Long,
    val isDemo: Boolean = false
)

@Dao
interface PatientDao {
    @Query("SELECT * FROM patients WHERE patientId = :patientId LIMIT 1")
    suspend fun getPatient(patientId: String): PatientEntity?

    @Query("SELECT * FROM patients LIMIT 1")
    suspend fun getCurrentPatient(): PatientEntity? // Patient app only ONE patient

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPatient(patient: PatientEntity)

    @Query("SELECT * FROM measurements WHERE patientId = :patientId ORDER BY timestamp DESC")
    suspend fun getMeasurements(patientId: String): List<MeasurementEntity>

    @Query("SELECT * FROM timeline WHERE patientId = :patientId ORDER BY eventDate DESC")
    suspend fun getTimeline(patientId: String): List<TimelineEntity>

    @Query("SELECT * FROM reports WHERE patientId = :patientId ORDER BY createdAt DESC")
    suspend fun getReports(patientId: String): List<ReportEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMeasurement(measurement: MeasurementEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTimelineEvent(event: TimelineEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertReport(report: ReportEntity)
}

@Database(
    entities = [PatientEntity::class, MeasurementEntity::class, TimelineEntity::class, ReportEntity::class],
    version = 1,
    exportSchema = false
)
abstract class PatientDatabase : RoomDatabase() {
    abstract fun patientDao(): PatientDao
}
