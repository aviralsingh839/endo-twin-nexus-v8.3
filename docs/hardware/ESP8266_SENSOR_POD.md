# ENDO-TWIN ESP8266 Sensor Pod

## Purpose

The ESP8266 can be used as the low-cost Wi-Fi sensor controller for the ENDO-TWIN research prototype. It is a direct sensor-pod option, not merely a replacement name for the ESP32-S3.

Firmware:

`hardware/esp8266/endo_twin_sensor_pod/endo_twin_sensor_pod.ino`

The pod emits the same newline-delimited **$CP3** data contract already consumed by the desktop and Android network paths (the host parser also still accepts legacy `$CP2`).

## Supported prototype sensors

| Sensor | ESP8266 connection | CP3 fields |
|---|---|---|
| MAX30102 | I2C | `ir`, `red` |
| MPU6050 | I2C | `ax..gz` |
| BME280 | I2C | `roomT`, `hum`, `press` |
| DS18B20 | D5 | `temp0` (skin contact) |
| (previous GSR input) | A0 | retired - pin left free |

The firmware leaves channels that are not physically connected as explicit placeholders. It does not fabricate ECG, microphone, FSR or light values.

## NodeMCU ESP8266 wiring

### I2C

- D2 / GPIO4 → SDA
- D1 / GPIO5 → SCL
- 3.3 V → sensor VCC where supported
- GND → common ground

MAX30102, MPU6050 and BME280 share the I2C bus.

### DS18B20

- D5 / GPIO14 → DATA
- 3.3 V → VCC
- GND → GND
- Use the normal 4.7 kΩ DATA-to-3.3 V pull-up.

### Retired analog input

A0 was the GSR input. That channel has been retired - the firmware no longer reads A0,
and the pin is left free. If you ever attach a new analog module, check the exact NodeMCU
board's ADC divider specification first and do not feed a voltage above the A0 limit.

## Network

The default firmware creates:

- SSID: `ENDO-TWIN-POD`
- Password: `endotwin123`
- IP: `192.168.4.1`
- TCP port: `7777`

The password is a prototype default and must be changed before any non-lab deployment.

The Android/desktop client connects to:

`192.168.4.1:7777`

## Device commands

TCP commands currently supported:

- `PING` → `$ACK,PONG,00`
- `WHOAMI` → `ENDO-TWIN-ESP8266-SENSOR-POD`

## $CP3 contract

The firmware sends one packet approximately every 50 ms:

`$CP3,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc`

CRC is the XOR of every character in the payload before the final comma. The existing ENDO-TWIN packet parser validates this CRC.

The ESP8266 pod therefore uses the same downstream path:

`ESP8266 → TCP → CP3 parser → quality control → signal processing → feature extraction → workstation/apps`

## Status flags

The firmware uses the existing status-bit convention where applicable:

- bit 0 — PPG finger absent
- bit 1 — PPG saturated / PPG unavailable
- bit 2 — MPU6050 error
- bit 3 — DS18B20 error
- bit 5 — I2C error
- bit 8 — BME280 error

These flags are engineering/prototype quality indicators, not clinical measurements.

## Build

Install the ESP8266 Arduino core and these libraries:

- ESP8266WiFi
- Adafruit BME280
- OneWire
- DallasTemperature
- SparkFun MAX3010x Sensor Library
- MPU6050 library compatible with `MPU6050.h`

Then select an ESP8266 board such as NodeMCU 1.0 (ESP-12E Module), flash at 115200 baud, and open the serial monitor.

## Bring-up sequence

1. Power the ESP8266 from a stable USB supply.
2. Open serial at 115200.
3. Confirm `ENDO-TWIN ESP8266 SENSOR POD`.
4. Confirm the AP address is `192.168.4.1`.
5. Connect a laptop/phone to `ENDO-TWIN-POD`.
6. Connect a TCP client to port 7777.
7. Confirm `$CP3` lines arrive.
8. Check CRC with the existing ENDO-TWIN parser.
9. Test each sensor independently.
10. Test the complete sensor set.
11. Only after signal quality is acceptable, use the live workstation mode.

## ESP8266 vs ESP32-S3

ESP8266 is now supported as a low-cost prototype pod option.

ESP32-S3 remains useful when the design requires substantially more GPIO, Bluetooth/BLE, local processing or additional peripherals.

The application protocol should remain board-neutral: **device identity may change, but the validated $CP3 contract should not** (the $CP2
layout stays accepted for old recordings).

## Research boundary

This is a research/engineering prototype. Sensor readings can be affected by wiring, placement, motion, environmental conditions, ADC limits and sensor quality. The device does not provide a medical diagnosis and does not establish clinical accuracy.
