package org.chronopcos.patient.ble

import android.Manifest
import android.bluetooth.*
import android.bluetooth.le.*
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.content.ContextCompat
import java.nio.charset.Charset
import java.util.UUID

object EndoTwinBleContract {
    val serviceUuid: UUID = UUID.fromString("7f300001-6c12-4f70-9e6b-8e9f7b8b1001")
    val notifyUuid: UUID = UUID.fromString("7f300002-6c12-4f70-9e6b-8e9f7b8b1001")
    val commandUuid: UUID = UUID.fromString("7f300003-6c12-4f70-9e6b-8e9f7b8b1001")
    const val DEVICE_NAME = "ENDO-TWIN-ESP32"
}

data class Cp2AndroidSample(
    val raw: String,
    val ms: Long,
    val ir: Long,
    val red: Long,
    val ax: Double,
    val ay: Double,
    val az: Double,
    val gx: Double,
    val gy: Double,
    val gz: Double,
    val temp0: Double?,
    val temp1: Double?,
    val gsr: Int,
    val status: Int,
    val crcValid: Boolean = true
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
                nullableDouble(parts[10]),nullableDouble(parts[11]),parts[12].toInt(),
                parts[23].toInt())
        } catch(_:Exception) { null }
    }
}

class EndoTwinBleClient(private val context: Context) {
    enum class State { IDLE, SCANNING, CONNECTING, CONNECTED, DISCONNECTED, ERROR }
    var state: State = State.IDLE
        private set
    var onState: ((State) -> Unit)? = null
    var onDevice: ((String) -> Unit)? = null
    var onSample: ((Cp2AndroidSample) -> Unit)? = null
    var onRawPacket: ((String) -> Unit)? = null
    var onError: ((String) -> Unit)? = null

    private val manager= context.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
    private val adapter: BluetoothAdapter? get()=manager.adapter
    private val parser=Cp2AndroidParser()
    private var scanner: BluetoothLeScanner?=null
    private var gatt: BluetoothGatt?=null
    private val frameBuffer=StringBuilder()

    private fun emit(s:State){state=s;onState?.invoke(s)}
    private fun canScan():Boolean =
        Build.VERSION.SDK_INT < 31 || ContextCompat.checkSelfPermission(context,Manifest.permission.BLUETOOTH_SCAN)==PackageManager.PERMISSION_GRANTED
    private fun canConnect():Boolean =
        Build.VERSION.SDK_INT < 31 || ContextCompat.checkSelfPermission(context,Manifest.permission.BLUETOOTH_CONNECT)==PackageManager.PERMISSION_GRANTED

    fun scan() {
        if (!canScan()) { emit(State.ERROR); onError?.invoke("Bluetooth scan permission required"); return }
        val a=adapter ?: run { emit(State.ERROR); onError?.invoke("Bluetooth unavailable"); return }
        if (!a.isEnabled) { emit(State.ERROR); onError?.invoke("Bluetooth is disabled"); return }
        scanner=a.bluetoothLeScanner
        frameBuffer.clear()
        emit(State.SCANNING)
        val settings=ScanSettings.Builder().setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY).build()
        val filter=ScanFilter.Builder().setServiceUuid(ParcelUuid(EndoTwinBleContract.serviceUuid)).build()
        scanner?.startScan(listOf(filter),settings,scanCallback)
    }

    fun stopScan() {
        if (!canScan()) return
        scanner?.stopScan(scanCallback)
        if (state==State.SCANNING) emit(State.IDLE)
    }

    fun connect(device: BluetoothDevice) {
        if (!canConnect()) { emit(State.ERROR); onError?.invoke("Bluetooth connect permission required"); return }
        stopScan()
        emit(State.CONNECTING)
        gatt?.close()
        gatt=device.connectGatt(context,false,gattCallback,BluetoothDevice.TRANSPORT_LE)
    }

    fun disconnect() {
        if (canConnect()) gatt?.disconnect()
        gatt?.close();gatt=null;emit(State.DISCONNECTED)
    }

    fun ping()=writeCommand("PING")
    fun whoAmI()=writeCommand("WHOAMI")

    private fun writeCommand(command:String) {
        val g=gatt ?: return
        if (!canConnect()) { onError?.invoke("Bluetooth connect permission required"); return }
        val svc=g.getService(EndoTwinBleContract.serviceUuid) ?: return
        val c=svc.getCharacteristic(EndoTwinBleContract.commandUuid) ?: return
        c.writeType=BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT
        c.value=(command+"\\n").toByteArray(Charsets.UTF_8)
        g.writeCharacteristic(c)
    }

    private val scanCallback=object:ScanCallback(){
        override fun onScanResult(type:Int,result:ScanResult){
            val d=result.device
            val advertised=d.name ?: result.scanRecord?.deviceName ?: ""
            if (advertised==EndoTwinBleContract.DEVICE_NAME || result.scanRecord?.serviceUuids?.any{it.uuid==EndoTwinBleContract.serviceUuid}==true) {
                onDevice?.invoke(advertised.ifBlank{d.address})
            }
        }
        override fun onScanFailed(errorCode:Int){emit(State.ERROR);onError?.invoke("BLE scan failed: $errorCode")}
    }

    private val gattCallback=object:BluetoothGattCallback(){
        override fun onConnectionStateChange(g:BluetoothGatt,status:Int,newState:Int){
            if (status!=BluetoothGatt.GATT_SUCCESS || newState!=BluetoothProfile.STATE_CONNECTED){
                g.close();if(gatt===g)gatt=null;emit(State.DISCONNECTED);return
            }
            emit(State.CONNECTED);g.discoverServices()
        }
        override fun onServicesDiscovered(g:BluetoothGatt,status:Int){
            if(status!=BluetoothGatt.GATT_SUCCESS){emit(State.ERROR);onError?.invoke("GATT service discovery failed");return}
            val svc=g.getService(EndoTwinBleContract.serviceUuid)
            val c=svc?.getCharacteristic(EndoTwinBleContract.notifyUuid)
            if(c==null){emit(State.ERROR);onError?.invoke("ENDO-TWIN notify characteristic not found");return}
            g.setCharacteristicNotification(c,true)
            c.getDescriptor(UUID.fromString("00002902-0000-1000-8000-00805f9b34fb"))?.value=BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                ?.also{g.writeDescriptor(c.getDescriptor(UUID.fromString("00002902-0000-1000-8000-00805f9b34fb"))!!)}
        }
        @Deprecated("Legacy callback kept for API compatibility")
        override fun onCharacteristicChanged(g:BluetoothGatt,c:BluetoothGattCharacteristic){consume(c.value)}
        override fun onCharacteristicChanged(g:BluetoothGatt,c:BluetoothGattCharacteristic,value:ByteArray){consume(value)}
    }

    private fun consume(bytes:ByteArray){
        frameBuffer.append(bytes.toString(Charset.forName("UTF-8")))
        while(true){
            val idx=frameBuffer.indexOf("\\n")
            if(idx<0) break
            val frame=frameBuffer.substring(0,idx).trim()
            frameBuffer.delete(0,idx+1)
            if(frame.length>4096){frameBuffer.clear();onError?.invoke("CP2 frame exceeded safety limit");break}
            onRawPacket?.invoke(frame)
            parser.parse(frame)?.let{onSample?.invoke(it)} ?: if(frame.startsWith("$CP2,")) onError?.invoke("Invalid CP2/CRC")
        }
    }
}
