# WEARABLE BUILD - ENDO-TWIN V8.7

## Primary wearable: ESP32

The project now uses an ESP32 DevKit as the body-worn controller. **No Arduino Nano is required.**

### Core BOM

- ESP32 DevKit board
- Generic Analog Pulse Sensor PPG (single-channel analog waveform) sensor
- MPU6050 IMU
- DS18B20 temperature sensor + 4.7k resistor
- GSR module (optional)
- 3.7V Li-ion/LiPo battery + suitable protected charging solution
- insulated wires, small enclosure, wrist strap

### Firmware

`hardware/esp32/endo_twin_wearable/endo_twin_wearable.ino`

The ESP32 samples PPG/IMU at 50 Hz, GSR at 10 Hz, temperature at 1 Hz, and publishes a $CP2 packet every 50 ms. BLE is used for Android; USB serial is retained for PC bring-up and diagnostics.

### Android connection

The wearable advertises as **ENDO-TWIN-ESP32**. Android should scan for the documented service UUID, connect, enable notifications on the data characteristic, and feed complete newline-delimited $CP2 messages into the same validation path used by wired serial. The command characteristic supports PING/WHOAMI and future device-control commands.

### Bench fallback

Use `hardware/arduino/endo_twin_uno_bench/endo_twin_uno_bench.ino` with an Arduino UNO for desk testing. The existing Mega firmware remains the expanded bench/hub platform.

### Bring-up order

Flash → verify USB $CP2 → validate parser/CRC → verify BLE advertising → verify Android notification stream → calibrate IMU at rest → validate each sensor independently → only then assemble the body-worn enclosure.

### Safety

Research/educational prototype only. Do not interpret outputs as a diagnosis. Never power a body-worn prototype directly from mains.


## V8.8 Analog Pulse Sensor migration

The current wearable build can use the generic analog Pulse Sensor module shown in the project hardware reference image instead of the MAX3010x optical PPG. The module is a single-channel analog pulse waveform source: SIG connects to an ADC-capable GPIO, VCC to the sensor's supported supply, and GND to common ground. ENDO-TWIN keeps the existing $CP2 transport so the rest of the desktop/BLE pipeline remains compatible. The primary waveform is carried in the existing `ir` slot for transport compatibility and is explicitly marked as `ANALOG_PULSE`/status bit 12. The `red` field is `-1` because there is no optical red channel.

The processing layer continues to support heart-rate and pulse-timing/HRV-style analysis from the waveform, with motion-aware quality scoring. It must not estimate SpO2 from this single-channel analog sensor. This hardware is suitable for an educational research prototype, not for diagnosis or clinical measurement.
