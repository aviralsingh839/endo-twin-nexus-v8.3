# ENDO-TWIN NEXUS V8.7 — ESP8266 + Mega Connection

## Active topology

### Wearable
ESP8266 → USB Serial → Desktop

or

ESP8266 → Wi-Fi TCP port 7777 → Android / desktop TCP client

### Bench/lab
Arduino Mega 2560 → USB Serial → Desktop

The Mega and ESP8266 are independent CP2 producers.

## ESP8266 network

- SoftAP SSID: `ENDO-TWIN-ESP8266`
- Password: `endotwin8266`
- TCP port: `7777`
- Default SoftAP address: normally `192.168.4.1`; confirm from serial output.

ESP8266 has no BLE. Android therefore uses a TCP socket instead of the previous ESP32 BLE contract.

## Legacy

The previous ESP32 wearable and old ESP8266 bridge are preserved under `hardware/legacy/`.
