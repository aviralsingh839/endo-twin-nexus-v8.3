package org.chronopcos.patient.ble

import android.content.Context

/**
 * Compatibility surface for the legacy BLE recorder.
 *
 * The current patient workflow uses Wi-Fi/TCP through EndoTwinTcpClient.
 * This class keeps the legacy recorder source buildable without claiming
 * that a BLE transport is implemented in the current branch.
 */
data class EndoTwinBleSample(
    val ir: Long = 0L,
    val red: Long = 0L,
    val ax: Double = 0.0,
    val ay: Double = 0.0,
    val az: Double = 0.0,
    val gx: Double = 0.0,
    val gy: Double = 0.0,
    val gz: Double = 0.0
)

class EndoTwinBleClient(@Suppress("UNUSED_PARAMETER") context: Context) {
    var onSample: ((EndoTwinBleSample) -> Unit)? = null

    fun disconnect() {
        // BLE transport is not active in the current Wi-Fi/TCP patient workflow.
    }
}
