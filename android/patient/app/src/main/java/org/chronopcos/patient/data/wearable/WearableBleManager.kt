package org.chronopcos.patient.data.wearable

import android.Manifest
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothGattDescriptor
import java.util.UUID
import android.bluetooth.BluetoothManager
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.content.ContextCompat

data class WearableDeviceSummary(
    val name: String,
    val address: String,
)

class WearableBleManager(private val context: Context) {
    private val bluetoothManager =
        context.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
    private val adapter: BluetoothAdapter?
        get() = bluetoothManager.adapter

    private val scanner
        get() = adapter?.bluetoothLeScanner

    private var scanCallback: ScanCallback? = null
    private var gatt: BluetoothGatt? = null

    fun isSupported(): Boolean = adapter != null && context.packageManager.hasSystemFeature(
        PackageManager.FEATURE_BLUETOOTH_LE
    )

    fun isEnabled(): Boolean = adapter?.isEnabled == true

    fun missingPermissions(): Array<String> {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            buildList {
                if (ContextCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_SCAN) != PackageManager.PERMISSION_GRANTED) {
                    add(Manifest.permission.BLUETOOTH_SCAN)
                }
                if (ContextCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) {
                    add(Manifest.permission.BLUETOOTH_CONNECT)
                }
            }.toTypedArray()
        } else {
            buildList {
                if (ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
                    add(Manifest.permission.ACCESS_FINE_LOCATION)
                }
            }.toTypedArray()
        }
    }

    fun startScan(
        onDevice: (WearableDeviceSummary) -> Unit,
        onError: (String) -> Unit
    ) {
        if (!isSupported()) {
            onError("Bluetooth LE is not supported on this phone.")
            return
        }
        if (!isEnabled()) {
            onError("Bluetooth is disabled.")
            return
        }
        if (missingPermissions().isNotEmpty()) {
            onError("Bluetooth permission is required.")
            return
        }

        stopScan()
        val callback = object : ScanCallback() {
            override fun onScanResult(callbackType: Int, result: ScanResult) {
                val device = result.device
                val name = result.scanRecord?.deviceName ?: device.name ?: "Unnamed wearable"
                onDevice(WearableDeviceSummary(name, device.address))
            }

            override fun onScanFailed(errorCode: Int) {
                onError("BLE scan failed: code $errorCode")
            }
        }
        scanCallback = callback
        try {
            scanner?.startScan(callback)
        } catch (security: SecurityException) {
            onError("Bluetooth permission was not granted.")
        }
    }

    fun stopScan() {
        val callback = scanCallback ?: return
        try {
            scanner?.stopScan(callback)
        } catch (_: SecurityException) {
            // Permission may have been revoked while the screen was open.
        }
        scanCallback = null
    }

    fun connect(
        address: String,
        onState: (String) -> Unit,
        onBytes: (ByteArray) -> Unit,
    ) {
        if (missingPermissions().isNotEmpty()) {
            onState("PERMISSION_REQUIRED")
            return
        }

        stopScan()
        try {
            val device: BluetoothDevice = adapter?.getRemoteDevice(address)
                ?: run {
                    onState("DEVICE_NOT_FOUND")
                    return
                }
            gatt?.close()
            onState("CONNECTING")
            gatt = device.connectGatt(context, false, object : BluetoothGattCallback() {
                override fun onConnectionStateChange(
                    g: BluetoothGatt,
                    status: Int,
                    newState: Int
                ) {
                    val state = if (newState == BluetoothGatt.STATE_CONNECTED) "CONNECTED"
                    else if (newState == BluetoothGatt.STATE_DISCONNECTED) "DISCONNECTED"
                    else "CONNECTING"
                    onState("$state:$status")
                    if (newState == BluetoothGatt.STATE_CONNECTED) {
                        try {
                            g.discoverServices()
                        } catch (_: SecurityException) {
                            onState("PERMISSION_REQUIRED")
                        }
                    }
                }

                override fun onServicesDiscovered(g: BluetoothGatt, status: Int) {
                    if (status != BluetoothGatt.GATT_SUCCESS) {
                        onState("SERVICE_DISCOVERY_FAILED:$status")
                        return
                    }

                    val notifyCharacteristics = g.services
                        .flatMap { it.characteristics }
                        .filter { characteristic ->
                            val props = characteristic.properties
                            props and BluetoothGattCharacteristic.PROPERTY_NOTIFY != 0 ||
                                props and BluetoothGattCharacteristic.PROPERTY_INDICATE != 0
                        }

                    if (notifyCharacteristics.isEmpty()) {
                        onState("CONNECTED_NO_NOTIFY_CHARACTERISTIC")
                        return
                    }

                    val characteristic = notifyCharacteristics.first()
                    try {
                        if (!g.setCharacteristicNotification(characteristic, true)) {
                            onState("NOTIFICATION_SETUP_FAILED")
                            return
                        }
                        val cccd = characteristic.getDescriptor(
                            UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")
                        )
                        if (cccd != null) {
                            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                                val result = g.writeDescriptor(
                                    cccd,
                                    BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                                )
                                if (result != BluetoothGatt.GATT_SUCCESS) {
                                    onState("CCCD_WRITE_FAILED:$result")
                                    return
                                }
                            } else {
                                @Suppress("DEPRECATION")
                                cccd.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                                @Suppress("DEPRECATION")
                                if (!g.writeDescriptor(cccd)) {
                                    onState("CCCD_WRITE_FAILED")
                                    return
                                }
                            }
                        }
                        onState(
                            "READY:" + characteristic.serviceUuid + ":" + characteristic.uuid
                        )
                    } catch (_: SecurityException) {
                        onState("PERMISSION_REQUIRED")
                    }
                }

                override fun onCharacteristicChanged(
                    g: BluetoothGatt,
                    characteristic: BluetoothGattCharacteristic
                ) {
                    onBytes(characteristic.value ?: ByteArray(0))
                }
            })
        } catch (security: SecurityException) {
            onState("PERMISSION_REQUIRED")
        } catch (exc: IllegalArgumentException) {
            onState("INVALID_DEVICE_ADDRESS")
        }
    }

    fun disconnect() {
        try {
            gatt?.disconnect()
        } catch (_: SecurityException) {
            // Ignore cleanup permission races.
        }
        gatt?.close()
        gatt = null
    }
}
