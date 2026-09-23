package org.chronopcos.patient.ble

import android.content.Context
import org.chronopcos.patient.data.database.MeasurementEntity
import java.util.UUID

class PatientBleRecorder(context: Context, private val patientId: String) {
    val client = EndoTwinBleClient(context)
    private val sessionId = UUID.randomUUID().toString()
    private val recorded = mutableListOf<MeasurementEntity>()

    init {
        client.onSample = { sample ->
            val now = System.currentTimeMillis()
            val values = listOf(
                Triple("ppg_ir", sample.ir.toDouble(), "raw"),
                Triple("ppg_red", sample.red.toDouble(), "raw"),
                Triple("accel_x", sample.ax, "g"),
                Triple("accel_y", sample.ay, "g"),
                Triple("accel_z", sample.az, "g"),
                Triple("gyro_x", sample.gx, "dps"),
                Triple("gyro_y", sample.gy, "dps"),
                Triple("gyro_z", sample.gz, "dps")
            )
            recorded += values.map { item ->
                val type = item.first; val value = item.second; val unit = item.third
                MeasurementEntity(
                    measurementId = sessionId + "_" + now + "_" + type,
                    patientId = patientId, type = type, value = value, unit = unit,
                    timestamp = now, quality = 1.0, provenance = "MEASURED",
                    source = "ESP32", isDemo = false, createdAt = now
                )
            }
        }
    }

    fun snapshot(): List<MeasurementEntity> = recorded.toList()
}