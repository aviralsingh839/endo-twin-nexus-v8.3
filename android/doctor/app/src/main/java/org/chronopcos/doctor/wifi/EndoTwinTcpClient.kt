package org.chronopcos.doctor.wifi

import android.content.Context
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.PrintWriter
import java.net.InetSocketAddress
import java.net.Socket

/**
 * One decoded frame from the ESP32-S3 pod.
 *
 * CP3 is the current format; CP2 is still accepted so recordings made before the
 * GSR hardware was retired keep parsing. The only difference is that CP2 carries a
 * `gsr` field this pod no longer measures.
 */
data class Cp2AndroidSample(
    val raw: String, val ms: Long, val ir: Long, val red: Long,
    val ax: Double, val ay: Double, val az: Double, val gx: Double, val gy: Double, val gz: Double,
    val temp0: Double?, val temp1: Double?, val status: Int, val crcValid: Boolean = true,
    val format: String = "CP3", val gsr: Int? = null
)

class Cp2AndroidParser {
    /** Returns a decoded frame, or null when the line is not a valid CP3/CP2 frame. */
    fun parse(line: String): Cp2AndroidSample? {
        val raw=line.trim()
        val cp3 = raw.startsWith("\$CP3,")
        val cp2 = raw.startsWith("\$CP2,")
        if (!cp3 && !cp2) return null
        val parts=raw.split(",")
        // CP3: tag + 22 data fields + crc. CP2 adds the retired gsr field.
        if (parts.size != if (cp3) 24 else 25) return null
        val received=parts.last().toIntOrNull(16) ?: return null
        val payload=parts.dropLast(1).joinToString(",")
        var crc=0
        for (c in payload) crc=crc xor c.code
        if ((crc and 0xFF)!=received) return null
        fun nullableDouble(s:String)=s.toDoubleOrNull()?.takeIf { it.isFinite() }
        // CP2 places the mic/ECG/FSR/status fields one position later than CP3.
        val shift = if (cp3) 0 else 1
        return try {
            Cp2AndroidSample(raw,parts[1].toLong(),parts[2].toLong(),parts[3].toLong(),
                parts[4].toDouble(),parts[5].toDouble(),parts[6].toDouble(),
                parts[7].toDouble(),parts[8].toDouble(),parts[9].toDouble(),
                nullableDouble(parts[10]),nullableDouble(parts[11]),
                parts[22+shift].toInt(), format = if (cp3) "CP3" else "CP2",
                gsr = if (cp2) parts[12].toIntOrNull() else null)
        } catch(_:Exception) { null }
    }
}

class EndoTwinTcpClient(private val context: Context) {
    enum class State { IDLE, CONNECTING, CONNECTED, DISCONNECTED, ERROR }
    var state: State = State.IDLE
        private set
    var onState: ((State) -> Unit)? = null
    var onDevice: ((String) -> Unit)? = null
    var onSample: ((Cp2AndroidSample) -> Unit)? = null
    var onRawPacket: ((String) -> Unit)? = null
    var onError: ((String) -> Unit)? = null

    private var socket: Socket? = null
    private var writer: PrintWriter? = null
    private var job: Job? = null
    private val scope=CoroutineScope(Dispatchers.IO)
    private val parser=Cp2AndroidParser()

    private fun emit(s:State)=scope.launch(Dispatchers.Main){ state=s; onState?.invoke(s) }
    private fun error(message:String)=scope.launch(Dispatchers.Main){ onError?.invoke(message); state=State.ERROR; onState?.invoke(State.ERROR) }

    fun connect(host:String, port:Int=7777) {
        disconnect()
        emit(State.CONNECTING)
        job=scope.launch {
            try {
                val s=Socket()
                s.connect(InetSocketAddress(host.trim(),port),5000)
                socket=s
                writer=PrintWriter(s.getOutputStream(),true)
                withContext(Dispatchers.Main){ onDevice?.invoke("$host:$port") }
                withContext(Dispatchers.Main){ state=State.CONNECTED; onState?.invoke(State.CONNECTED) }
                val reader=BufferedReader(InputStreamReader(s.getInputStream(),Charsets.UTF_8))
                while (true) {
                    val line=reader.readLine() ?: break
                    val frame=line.trim()
                    if(frame.length>4096){ error("CP2 frame exceeded safety limit"); break }
                    withContext(Dispatchers.Main){ onRawPacket?.invoke(frame) }
                    val sample = parser.parse(frame)
                    if (sample != null) {
                        withContext(Dispatchers.Main) { onSample?.invoke(sample) }
                    } else if (frame.startsWith("\$CP2,")) {
                        error("Invalid CP2/CRC")
                    }
                }
                withContext(Dispatchers.Main){ state=State.DISCONNECTED; onState?.invoke(State.DISCONNECTED) }
            } catch (e:Exception) {
                error("ESP sensor pod connection failed: ${e.message ?: e.javaClass.simpleName}")
            } finally {
                try { socket?.close() } catch(_:Exception) {}
                socket=null; writer=null
            }
        }
    }

    fun disconnect() {
        job?.cancel(); job=null
        try { socket?.close() } catch(_:Exception) {}
        socket=null; writer=null
        state=State.DISCONNECTED
        onState?.invoke(State.DISCONNECTED)
    }

    fun ping()=writeCommand("PING")
    fun whoAmI()=writeCommand("WHOAMI")
    private fun writeCommand(command:String) {
        writer?.println(command) ?: onError?.invoke("ESP sensor pod TCP link is not connected")
    }
}
