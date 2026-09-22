package org.chronopcos.patient.study
import android.app.*
import android.content.Intent
import android.os.IBinder
import android.content.pm.ServiceInfo
import androidx.core.app.NotificationCompat
import androidx.room.Room
import kotlinx.coroutines.*
import org.chronopcos.patient.data.database.*
import org.chronopcos.patient.wifi.Cp2AndroidParser
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.InetSocketAddress
import java.net.Socket
import java.util.UUID

class PublicStudyService : Service() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var job: Job? = null
    private val parser = Cp2AndroidParser()
    private var db: PatientDatabase? = null

    override fun onCreate() {
        super.onCreate()
        db = Room.databaseBuilder(applicationContext, PatientDatabase::class.java, "endo_twin_patient.db")
            .addMigrations(org.chronopcos.patient.data.database.MIGRATION_2_3).build()
        getSystemService(NotificationManager::class.java).createNotificationChannel(
            NotificationChannel(CHANNEL_ID, "ENDO-TWIN public study", NotificationManager.IMPORTANCE_LOW)
        )
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val host = intent?.getStringExtra(EXTRA_HOST) ?: "192.168.4.1"
        val port = intent?.getIntExtra(EXTRA_PORT, 7777) ?: 7777
        val patientId = intent?.getStringExtra(EXTRA_PATIENT_ID) ?: "PUBLIC-PARTICIPANT"
        val studyId = intent?.getStringExtra(EXTRA_STUDY_ID) ?: "STUDY-" + UUID.randomUUID().toString().take(8)
        if (android.os.Build.VERSION.SDK_INT >= 29) startForeground(NOTIFICATION_ID, notification("3-day study recorder • connecting"), ServiceInfo.FOREGROUND_SERVICE_TYPE_CONNECTED_DEVICE) else startForeground(NOTIFICATION_ID, notification("3-day study recorder • connecting"))
        job?.cancel()
        job = scope.launch { runRecorder(host, port, patientId, studyId) }
        return START_STICKY
    }

    private suspend fun runRecorder(host: String, port: Int, patientId: String, studyId: String) {
        while (isActive) {
            try {
                Socket().use { socket ->
                    socket.connect(InetSocketAddress(host, port), 5000)
                    socket.soTimeout = 15000
                    updateNotification("3-day study recorder • connected")
                    val reader = BufferedReader(InputStreamReader(socket.getInputStream(), Charsets.UTF_8))
                    while (isActive) {
                        val line = reader.readLine() ?: break
                        if (line.length > 4096) continue
                        val frame = line.trim()
                        parser.parse(frame)?.let { sample ->
                            db?.patientDao()?.insertRawPacket(
                                RawSensorPacketEntity(
                                    packetId = studyId + "-" + UUID.randomUUID().toString(),
                                    patientId = patientId,
                                    transport = "wifi-tcp",
                                    payload = frame,
                                    receivedAt = System.currentTimeMillis(),
                                    crcValid = sample.crcValid,
                                    isDemo = false
                                )
                            )
                        }
                    }
                }
            } catch (_: Exception) {
                updateNotification("3-day study recorder • reconnecting")
            }
            delay(5000)
        }
    }

    private fun notification(text: String): Notification =
        NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_menu_info_details)
            .setContentTitle("ENDO-TWIN • Public 3-Day Test")
            .setContentText(text).setOngoing(true).setOnlyAlertOnce(true).build()

    private fun updateNotification(text: String) {
        getSystemService(NotificationManager::class.java).notify(NOTIFICATION_ID, notification(text))
    }

    override fun onDestroy() {
        job?.cancel(); scope.cancel(); db?.close(); super.onDestroy()
    }
    override fun onBind(intent: Intent?): IBinder? = null

    companion object {
        const val EXTRA_HOST = "host"
        const val EXTRA_PORT = "port"
        const val EXTRA_PATIENT_ID = "patient_id"
        const val EXTRA_STUDY_ID = "study_id"
        const val NOTIFICATION_ID = 7301
        const val CHANNEL_ID = "endo_twin_public_study"
    }
}
