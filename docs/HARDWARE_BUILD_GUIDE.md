# ENDO-TWIN NEXUS — Hardware Build Guide

The complete current physical assembly guide is:

`docs/WEARABLE_AND_MEGA_BUILD_MANUAL.md`

It covers the ESP32-S3 wearable, sensor placement, dimensions, wiring, skin-temperature probe, Mega hub and validation procedure.


## ESP8266 Sensor Pod

A low-cost ESP8266 direct sensor-pod build is now supported alongside the ESP32-S3 option.

- Firmware: `hardware/esp8266/endo_twin_sensor_pod/endo_twin_sensor_pod.ino`
- Detailed wiring, bring-up and protocol: `docs/hardware/ESP8266_SENSOR_POD.md`
- Transport: Wi-Fi TCP on port 7777
- Protocol: newline-delimited `$CP3` with XOR CRC
- Typical sensors: MAX30102, MPU6050, BME280 and DS18B20 (skin contact)
- Unavailable channels remain explicit placeholders; no physiology is fabricated.

ESP8266 has fewer GPIO/ADC resources and no BLE, so ESP32-S3 remains preferable when additional peripherals, BLE or more local processing are required.
