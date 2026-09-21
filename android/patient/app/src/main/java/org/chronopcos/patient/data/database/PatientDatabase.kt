package org.chronopcos.patient.data.database

import android.content.Context
import androidx.room.*
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

/**
 * ENDO-TWIN Patient Database - local-first Room database.
 * Sensor transport stores raw payloads locally before board-specific parsing.
 * All records remain patient-scoped.
 */

@Entity(tableName = "patients")
data class PatientEntity(
    @PrimaryKey val patientId: String,
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
    foreignKeys = [ForeignKey(
        entity = PatientEntity::class,
        parentColumns = ["patientId"],
        childColumns = ["patientId"],
        onDelete = ForeignKey.CASCADE
    )],
    indices = [Index("patientId")]
)
data class MeasurementEntity(
    @PrimaryKey val measurementId: String,
    val patientId: String,
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
    foreignKeys = [ForeignKey(
        entity = PatientEntity::class,
        parentColumns = ["patientId"],
        childColumns = ["patientId"],
        onDelete = ForeignKey.CASCADE
    )],
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
    foreignKeys = [ForeignKey(
        entity = PatientEntity::class,
        parentColumns = ["patientId"],
        childColumns = ["patientId"],
        onDelete = ForeignKey.CASCADE
    )],
    indices = [Index("patientId")]
)
data class ReportEntity(
    @PrimaryKey val reportId: String,
    val patientId: String,
    val reportType: String,
    val contentText: String,
    val createdAt: Long,
    val isDemo: Boolean = false
)

@Entity(
    tableName = "wearable_sessions",
    foreignKeys = [ForeignKey(
        entity = PatientEntity::class,
        parentColumns = ["patientId"],
        childColumns = ["patientId"],
        onDelete = ForeignKey.CASCADE
    )],
    indices = [Index("patientId")]
)
data class WearableSessionEntity(
    @PrimaryKey val sessionId: String,
    val patientId: String,
    val deviceId: String?,
    val transport: String,
    val startedAt: Long,
    val endedAt: Long? = null,
    val state: String = "ACTIVE",
    val isDemo: Boolean = false
)

@Entity(
    tableName = "wearable_events",
    foreignKeys = [ForeignKey(
        entity = PatientEntity::class,
        parentColumns = ["patientId"],
        childColumns = ["patientId"],
        onDelete = ForeignKey.CASCADE
    )],
    indices = [Index("patientId"), Index("sessionId")]
)
data class WearableEventEntity(
    @PrimaryKey val eventId: String,
    val patientId: String,
    val sessionId: String?,
    val timestamp: Long,
    val eventType: String,
    val detail: String,
    val isDemo: Boolean = false
)

@Entity(
    tableName = "raw_wearable_packets",
    foreignKeys = [ForeignKey(
        entity = PatientEntity::class,
        parentColumns = ["patientId"],
        childColumns = ["patientId"],
        onDelete = ForeignKey.CASCADE
    )],
    indices = [Index("patientId"), Index("sessionId"), Index("timestamp")]
)
data class RawWearablePacketEntity(
    @PrimaryKey val packetId: String,
    val patientId: String,
    val sessionId: String?,
    val timestamp: Long,
    val payloadBase64: String,
    val transport: String,
    val quality: Double? = null,
    val isDemo: Boolean = false
)

@Dao
interface PatientDao {
    @Query("SELECT * FROM patients WHERE patientId = :patientId LIMIT 1")
    suspend fun getPatient(patientId: String): PatientEntity?

    @Query("SELECT * FROM patients LIMIT 1")
    suspend fun getCurrentPatient(): PatientEntity?

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

@Dao
interface WearableDao {
    @Query("SELECT * FROM wearable_sessions WHERE patientId = :patientId ORDER BY startedAt DESC")
    suspend fun getSessions(patientId: String): List<WearableSessionEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSession(session: WearableSessionEntity)

    @Query("UPDATE wearable_sessions SET endedAt = :endedAt, state = :state WHERE sessionId = :sessionId AND patientId = :patientId")
    suspend fun closeSession(sessionId: String, patientId: String, endedAt: Long, state: String)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertEvent(event: WearableEventEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPacket(packet: RawWearablePacketEntity)

    @Query("SELECT COUNT(*) FROM raw_wearable_packets WHERE sessionId = :sessionId")
    suspend fun packetCount(sessionId: String): Int

    @Query("SELECT * FROM wearable_events WHERE patientId = :patientId ORDER BY timestamp")
    suspend fun getEvents(patientId: String): List<WearableEventEntity>

    @Query("SELECT * FROM raw_wearable_packets WHERE patientId = :patientId ORDER BY timestamp")
    suspend fun getPackets(patientId: String): List<RawWearablePacketEntity>
}

@Database(
    entities = [
        PatientEntity,
        MeasurementEntity,
        TimelineEntity,
        ReportEntity,
        WearableSessionEntity,
        WearableEventEntity,
        RawWearablePacketEntity
    ],
    version = 2,
    exportSchema = false
)
abstract class PatientDatabase : RoomDatabase() {
    abstract fun patientDao(): PatientDao
    abstract fun wearableDao(): WearableDao

    companion object {
        @Volatile private var INSTANCE: PatientDatabase? = null

        private val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS wearable_sessions (" +
                        "sessionId TEXT NOT NULL PRIMARY KEY, " +
                        "patientId TEXT NOT NULL, " +
                        "deviceId TEXT, transport TEXT NOT NULL, " +
                        "startedAt INTEGER NOT NULL, endedAt INTEGER, " +
                        "state TEXT NOT NULL, isDemo INTEGER NOT NULL, " +
                        "FOREIGN KEY(patientId) REFERENCES patients(patientId) ON DELETE CASCADE)"
                )
                db.execSQL("CREATE INDEX IF NOT EXISTS index_wearable_sessions_patientId ON wearable_sessions(patientId)")
                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS wearable_events (" +
                        "eventId TEXT NOT NULL PRIMARY KEY, patientId TEXT NOT NULL, sessionId TEXT, " +
                        "timestamp INTEGER NOT NULL, eventType TEXT NOT NULL, detail TEXT NOT NULL, isDemo INTEGER NOT NULL, " +
                        "FOREIGN KEY(patientId) REFERENCES patients(patientId) ON DELETE CASCADE)"
                )
                db.execSQL("CREATE INDEX IF NOT EXISTS index_wearable_events_patientId ON wearable_events(patientId)")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_wearable_events_sessionId ON wearable_events(sessionId)")
                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS raw_wearable_packets (" +
                        "packetId TEXT NOT NULL PRIMARY KEY, patientId TEXT NOT NULL, sessionId TEXT, " +
                        "timestamp INTEGER NOT NULL, payloadBase64 TEXT NOT NULL, transport TEXT NOT NULL, " +
                        "quality REAL, isDemo INTEGER NOT NULL, " +
                        "FOREIGN KEY(patientId) REFERENCES patients(patientId) ON DELETE CASCADE)"
                )
                db.execSQL("CREATE INDEX IF NOT EXISTS index_raw_wearable_packets_patientId ON raw_wearable_packets(patientId)")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_raw_wearable_packets_sessionId ON raw_wearable_packets(sessionId)")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_raw_wearable_packets_timestamp ON raw_wearable_packets(timestamp)")
            }
        }

        fun getInstance(context: Context): PatientDatabase =
            INSTANCE ?: synchronized(this) {
                INSTANCE ?: Room.databaseBuilder(
                    context.applicationContext,
                    PatientDatabase::class.java,
                    "endo_twin_patient.db"
                ).addMigrations(MIGRATION_1_2).build().also { INSTANCE = it }
            }
    }
}
