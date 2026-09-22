# ENDO-TWIN NEXUS V8.7 — ESP32 Wearable Build

The **ESP32 is the primary wearable**. This document is the practical build guide for the active wearable.

## Bill of materials

- ESP32 development board
- MAX30102
- MPU6050
- DS18B20
- GSR module
- status LED + resistor
- breadboard / prototype wiring
- suitable regulated battery supply for body-worn testing

The Arduino Mega is a separate bench/lab controller; it is not required for the wearable.

## Firmware

`hardware/esp32/endo_twin_wearable/endo_twin_wearable.ino`

Required Arduino libraries:
- SparkFun MAX3010x Pulse and Proximity Sensor Library
- Adafruit MPU6050
- Adafruit Unified Sensor
- OneWire
- DallasTemperature
- ESP32 BLE support from the Arduino-ESP32 core

## Wiring

- MAX30102 SDA → GPIO21, SCL → GPIO22
- MPU6050 SDA → GPIO21, SCL → GPIO22
- DS18B20 DATA → GPIO18, 4.7 kΩ to 3.3 V
- GSR analog output → GPIO34
- status LED → GPIO2

Check each sensor breakout's allowed logic voltage before connection.

## Flash

Use `arduino-cli compile` / `arduino-cli upload` with an ESP32 target such as `esp32:esp32:esp32`. The repository build helper compiles the canonical firmware.

## Serial validation

115200 baud. A working device produces:

```
$CP2,...,<CRC>
$CP2,...,<CRC>
...
```

Send `PING` and expect `$ACK,PONG,00`. Send `WHOAMI` and expect `$ACK,WHOAMI,ENDO-TWIN-ESP32`.

## BLE validation

Scan for **ENDO-TWIN-ESP32**, filter by service UUID, connect, subscribe to the notify characteristic, then reconstruct newline-terminated CP2 frames from notification chunks. The command characteristic accepts `PING`, `WHOAMI` and LED commands.

## Physical test sequence

1. Verify the I2C bus and sensor breakout voltages.
2. Verify MAX30102 presence; a finger should raise IR readings.
3. Verify MPU6050 movement changes acceleration/gyro values.
4. Verify DS18B20 returns a plausible temperature.
5. Verify GSR produces a changing ADC value.
6. Confirm CRC-valid CP2 packets.
7. Run the Prototype Lab acceptance test.
