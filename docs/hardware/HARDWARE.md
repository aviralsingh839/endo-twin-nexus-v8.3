# HARDWARE - ENDO-TWIN V8.7

## Active architecture

- **ESP32 = primary wearable controller**. Arduino Nano is no longer required.
- **Arduino UNO = bench/prototype validation controller** for the same core sensors.
- **Arduino Mega 2560 = extended bench/hub controller** when ECG, microphone, FSR, BME280, OLED and other expansion sensors are needed.
- **MAX30102 + MPU6050 share I2C on the ESP32 (GPIO21/22). DS18B20 uses GPIO18. GSR uses ADC GPIO34.**
- **BLE is the preferred ESP32 → Android transport; USB serial at 115200 remains available for desktop diagnostics.**
- The canonical data contract remains newline-delimited **$CP2** with XOR CRC. Missing channels stay explicit placeholders; no synthetic values are inserted into real sessions.

## Active files

- Wearable: `hardware/esp32/endo_twin_wearable/endo_twin_wearable.ino`
- UNO bench: `hardware/arduino/endo_twin_uno_bench/endo_twin_uno_bench.ino`
- Mega bench/hub: `hardware/arduino/chrono_pcos_mega_firmware/chrono_pcos_mega_firmware.ino`
- Former Nano firmware is retained only as a **legacy reference** and must not be presented as the required wearable.

## Data flow

`ESP32 sensors → $CP2 → BLE/USB → packet_parser.py → quality control → signal processing → feature extraction → longitudinal fusion → research models/UI`

## Safety

Educational/research prototype only; not a diagnostic medical device. For body-worn operation use battery power or an electrically isolated supply and keep mains power away from the body.
