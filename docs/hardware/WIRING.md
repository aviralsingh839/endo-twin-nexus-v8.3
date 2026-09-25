# WIRING - ENDO-TWIN V8.7

## ESP32 primary wearable

| Device | ESP32 connection |
|---|---|
| Analog Pulse Sensor SIG | ADC-capable GPIO configured as `PULSE_PIN` (current firmware default GPIO4; choose another ADC GPIO if your exact ESP32/ESP32-S3 board requires it) |
| Analog Pulse Sensor VCC | 3.3V or the module's specified supply |
| Analog Pulse Sensor GND | Common GND |
| MPU6050 SDA | GPIO21 (or board-specific SDA) |
| MPU6050 SCL | GPIO22 (or board-specific SCL) |
| DS18B20 data | GPIO18 + 4.7k pull-up to 3.3V |
| GSR analog | GPIO5 (or another ADC-capable GPIO) |
| Status LED | GPIO2 (optional) |

The analog pulse module is **not I2C**. Only the MPU6050 uses the I2C bus. Connect the pulse sensor's **SIG** line to an ADC-capable input and keep its signal within the ESP32 ADC voltage range. Check the breakout's supply requirement before connecting power.

## Arduino UNO bench


Analog Pulse Sensor: SIG to an analog-capable A0/A1/A2 input; MPU6050: SDA=A4, SCL=A5. DS18B20: D2 with 4.7k pull-up. GSR: A0. USB serial: 115200.

## Arduino Mega bench/hub

Analog Pulse Sensor: SIG to an analog-capable Mega analog input (for example A4/A5); MPU6050: SDA=20, SCL=21. DS18B20: D2. GSR=A0. The existing Mega firmware can additionally host ECG, microphone, FSR, environmental sensors, OLED and buttons.

## ESP32 BLE contract

Service UUID: `7f300001-6c12-4f70-9e6b-8e9f7b8b1001`\nNotify UUID: `7f300002-6c12-4f70-9e6b-8e9f7b8b1001`\nCommand UUID: `7f300003-6c12-4f70-9e6b-8e9f7b8b1001`

The data characteristic sends one complete $CP2 line per notification. USB serial uses the same line format.

## Testing

1. Flash ESP32 and open serial at 115200.
2. Confirm device advertises as `ENDO-TWIN-PULSE`.
3. Send `WHOAMI` and check the identity response.
4. With no finger/contact on the analog Pulse Sensor, the waveform should become low/invalid and the quality gate should avoid producing a trusted HR value.
5. Place a finger gently on the analog Pulse Sensor and observe the single ADC waveform in the live PPG plot.
6. Move the IMU and observe acceleration/gyro fields.
7. Touch/warm the DS18B20 and observe temperature changes.
8. Verify GSR changes only when its sensor is correctly wired.
9. Validate the resulting lines with the existing Python `PacketParser` tests before enabling any research-model pipeline.

## Safety

Never place an unverified powered prototype on a person. Use insulated wiring, current-limited battery power, and no direct mains connection.


## V8.8 Analog Pulse Sensor migration

The current wearable build can use the generic analog Pulse Sensor module shown in the project hardware reference image instead of the MAX3010x optical PPG. The module is a single-channel analog pulse waveform source: SIG connects to an ADC-capable GPIO, VCC to the sensor's supported supply, and GND to common ground. ENDO-TWIN keeps the existing $CP2 transport so the rest of the desktop/BLE pipeline remains compatible. The primary waveform is carried in the existing `ir` slot for transport compatibility and is explicitly marked as `ANALOG_PULSE`/status bit 12. The `red` field is `-1` because there is no optical red channel.

The processing layer continues to support heart-rate and pulse-timing/HRV-style analysis from the waveform, with motion-aware quality scoring. It must not estimate SpO2 from this single-channel analog sensor. This hardware is suitable for an educational research prototype, not for diagnosis or clinical measurement.
