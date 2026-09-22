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

data class Cp2AndroidSample(
    val raw: String, val ms: Long, val ir: Long, val red: Long,
    val ax: Double, val ay: Double, val az: Double, val gx: Double, val gy: Double, val gz: Double,
    val temp0: Double?, val temp1: Double?, val gsr: Int, val status: Int, val crcValid: Boolean = true
)

class Cp2AndroidParser {
    fun parse(line: String): Cp2AndroidSample? {
        val raw=line.trim()
        if (!raw.startsWith("$CP2,")) return null
        val parts=raw.split(",")
        if (parts.size!=25) return null
        val received=parts.last().toIntOrNull(16) ?: return null
        val payload=parts.dropLast(1).joinToString(",")
        var crc=0
        for (c in payload) crc=crc xor c.code
        if ((crc and 0xFF)!=received) return null
        fun nullableDouble(s:String)=s.toDoubleOrNull()?.takeIf { it.isFinite() }
        return try {
            Cp2AndroidSample(raw,parts[1].toLong(),parts[2].toLong(),parts[3].toLong(),
                parts[4].toDouble(),parts[5].toDouble(),parts[6].toDouble(),
                parts[7].toDouble(),parts[8].toDouble(),parts[9].toDouble(),
                nullableDouble(parts[10]),nullableDouble(parts[11]),parts[12].toInt(),parts[23].toInt())
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
                    parser.parse(frame)?.let { sample -> withContext(Dispatchers.Main){ onSample?.invoke(sample) } }
                        ?: if(frame.startsWith("$CP2,")) error("Invalid CP2/CRC")
                }
                withContext(Dispatchers.Main){ state=State.DISCONNECTED; onState?.invoke(State.DISCONNECTED) }
            } catch (e:Exception) {
                error("ESP8266 connection failed: \${e.message ?: e.javaClass.simpleName}")
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
        writer?.println(command) ?: onError?.invoke("ESP8266 TCP link is not connected")
    }
}
