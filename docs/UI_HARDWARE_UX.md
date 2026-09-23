# ENDO-TWIN NEXUS Hardware UX

## Device types

- ESP8266 Sensor Pod — low-cost Wi-Fi/TCP sensor pod.
- ESP32-S3 Sensor Pod — higher-capability Wi-Fi/TCP sensor pod.
- Arduino Mega Lab Controller — bench/lab controller over USB serial.

## ESP8266 setup workflow

Discover/enter endpoint → Connect → WHOAMI → PING → CP3 validation → sensor inventory → signal quality → Ready.

## Sensor matrix

MAX30102, MPU6050, BME280/BME680, DS18B20 skin probe, ECG, FSR, microphone and light should expose Present, Connected, Streaming, Signal Quality, Last Value and Error.

Unsupported/unwired channels must render UNAVAILABLE, not zero and not synthetic physiology.

## Failure UX

Connection loss must show endpoint, last successful packet/timestamp, actual error and retry action. Build failure must show command, failed step and real log location.

## Protocol

The existing CP3 parser remains canonical. Hardware UI does not duplicate packet decoding.
