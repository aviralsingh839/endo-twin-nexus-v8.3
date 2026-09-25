# WIRING - ENDO-TWIN V8.7

## ESP32 primary wearable

| Device | ESP32 connection |
|---|---|
| Generic Analog Pulse Sensor SDA | GPIO21 |
| Generic Analog Pulse Sensor SCL | GPIO22 |
| MPU6050 SDA | GPIO21 |
| MPU6050 SCL | GPIO22 |
| DS18B20 data | GPIO18 + 4.7k pull-up to 3.3V |
| GSR analog | GPIO34 (ADC1 input) |
| Status LED | GPIO2 (optional) |
| Ground | Common GND |

Generic Analog Pulse Sensor and MPU6050 are on the same I2C bus and must use compatible 3.3V logic. Check your breakout board before powering it; do not assume a 5V-only sensor input is safe.

## Arduino UNO bench

Generic Analog Pulse Sensor/MPU6050: SDA=A4, SCL=A5. DS18B20: D2 with 4.7k pull-up. GSR: A0. USB serial: 115200.

## Arduino Mega bench/hub

Generic Analog Pulse Sensor/MPU6050: SDA=20, SCL=21. DS18B20: D2. GSR=A0. The existing Mega firmware can additionally host ECG, microphone, FSR, environmental sensors, OLED and buttons.

## ESP32 BLE contract

Service UUID: `7f300001-6c12-4f70-9e6b-8e9f7b8b1001`\nNotify UUID: `7f300002-6c12-4f70-9e6b-8e9f7b8b1001`\nCommand UUID: `7f300003-6c12-4f70-9e6b-8e9f7b8b1001`

The data characteristic sends one complete $CP2 line per notification. USB serial uses the same line format.

## Testing

1. Flash ESP32 and open serial at 115200.
2. Confirm device advertises as `ENDO-TWIN-ESP32`.
3. Send `WHOAMI` and check the identity response.
4. With no finger on Generic Analog Pulse Sensor, the packet should carry the PPG-absent status bit rather than fake a signal.
5. Place a finger gently on Generic Analog Pulse Sensor and observe IR/RED values.
6. Move the IMU and observe acceleration/gyro fields.
7. Touch/warm the DS18B20 and observe temperature changes.
8. Verify GSR changes only when its sensor is correctly wired.
9. Validate the resulting lines with the existing Python `PacketParser` tests before enabling any research-model pipeline.

## Safety

Never place an unverified powered prototype on a person. Use insulated wiring, current-limited battery power, and no direct mains connection.


## V8.8 Analog Pulse Sensor migration

The current wearable build can use the generic analog Pulse Sensor module shown in the project hardware reference image instead of the MAX3010x optical PPG. The module is a single-channel analog pulse waveform source: SIG connects to an ADC-capable GPIO, VCC to the sensor's supported supply, and GND to common ground. ENDO-TWIN keeps the existing $CP2 transport so the rest of the desktop/BLE pipeline remains compatible. The primary waveform is carried in the existing `ir` slot for transport compatibility and is explicitly marked as `ANALOG_PULSE`/status bit 12. The `red` field is `-1` because there is no optical red channel.

The processing layer continues to support heart-rate and pulse-timing/HRV-style analysis from the waveform, with motion-aware quality scoring. It must not estimate SpO2 from this single-channel analog sensor. This hardware is suitable for an educational research prototype, not for diagnosis or clinical measurement.
