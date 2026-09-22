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

@Entity(tableName = "public_studies")
data class PublicStudyEntity(
    @PrimaryKey val studyId: String,
    val participantId: String,
    val startedAt: Long,
    val plannedEndAt: Long,
    val endedAt: Long? = null,
    val consentAcknowledged: Boolean = false,
    val status: String = "ACTIVE"
)

@Entity(tableName = "raw_sensor_packets")
data class RawSensorPacketEntity(
    @PrimaryKey val packetId: String,
    val patientId: String,
    val transport: String,
    val payload: String,
    val receivedAt: Long,
    val crcValid: Boolean,
    val isDemo: Boolean = false
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

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertRawPacket(packet: RawSensorPacketEntity)

    @Query("SELECT * FROM raw_sensor_packets WHERE patientId = :patientId ORDER BY receivedAt DESC")
    suspend fun getRawPackets(patientId: String): List<RawSensorPacketEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPublicStudy(study: PublicStudyEntity)

    @Query("SELECT * FROM public_studies ORDER BY startedAt DESC LIMIT 1")
    suspend fun getLatestPublicStudy(): PublicStudyEntity?

    @Query("UPDATE public_studies SET endedAt=:endedAt, status=:status WHERE studyId=:studyId")
    suspend fun finishPublicStudy(studyId: String, endedAt: Long, status: String)

    @Query("SELECT COUNT(*) FROM raw_sensor_packets WHERE patientId=:patientId AND receivedAt BETWEEN :from AND :to")
    suspend fun countRawPackets(patientId: String, from: Long, to: Long): Int

    @Query("SELECT COUNT(*) FROM raw_sensor_packets WHERE patientId=:patientId AND receivedAt BETWEEN :from AND :to AND crcValid=1")
    suspend fun countValidPackets(patientId: String, from: Long, to: Long): Int

    @Query("SELECT MIN(receivedAt) FROM raw_sensor_packets WHERE patientId=:patientId AND receivedAt BETWEEN :from AND :to")
    suspend fun firstPacketAt(patientId: String, from: Long, to: Long): Long?

    @Query("SELECT MAX(receivedAt) FROM raw_sensor_packets WHERE patientId=:patientId AND receivedAt BETWEEN :from AND :to")
    suspend fun lastPacketAt(patientId: String, from: Long, to: Long): Long?
}

@Database(
    entities = [PatientEntity::class, MeasurementEntity::class, TimelineEntity::class, ReportEntity::class, RawSensorPacketEntity::class, PublicStudyEntity::class],
    version = 3,
    exportSchema = false
)
abstract class PatientDatabase : RoomDatabase() {

    abstract fun patientDao(): PatientDao
}
