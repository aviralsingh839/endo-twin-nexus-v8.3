# ENDO-TWIN NEXUS V8.7 — ESP8266 Wearable Build

The **ESP8266 is the primary wearable**. Arduino Mega remains the separate bench/lab controller.

## Bill of materials

- NodeMCU 1.0 / ESP-12E ESP8266 development board
- MAX30102
- MPU6050
- DS18B20
- GSR module
- status LED + resistor
- breadboard / prototype wiring
- suitable regulated battery supply for body-worn testing

## Firmware

`hardware/esp8266/endo_twin_wearable/endo_twin_wearable.ino`

Required libraries:
- SparkFun MAX3010x Pulse and Proximity Sensor Library
- Adafruit MPU6050
- Adafruit Unified Sensor
- OneWire
- DallasTemperature
- ESP8266 Arduino core

The ESP8266 Arduino platform is installed through Boards Manager or the documented ESP8266 core package. citeturn0search0

## Wiring

- MAX30102 SDA → D1/GPIO5, SCL → D2/GPIO4
- MPU6050 SDA → D1/GPIO5, SCL → D2/GPIO4
- DS18B20 DATA → D6/GPIO12, 4.7 kΩ to 3.3 V
- GSR analog output → A0
- status LED → D4/GPIO2

## Network

The firmware starts the `ENDO-TWIN-ESP8266` Wi-Fi access point and TCP server on port 7777. Android connects over TCP. Desktop may use USB serial.

## Flash

Use Arduino CLI with an ESP8266 NodeMCU target such as `esp8266:esp8266:nodemcuv2`. The repository build helper compiles the canonical firmware.

## Validation

At 115200 baud, the serial monitor should show the SoftAP IP and TCP server status. A working device produces newline-terminated:

```
$CP2,...,<CRC>
$CP2,...,<CRC>
```

Send `PING` or `WHOAMI` over USB/TCP and verify the corresponding ACK. The ESP8266 reports `ENDO-TWIN-ESP8266`.

## Physical test sequence

1. Verify I2C wiring and sensor voltage compatibility.
2. Verify MAX30102 IR readings.
3. Verify MPU6050 movement.
4. Verify DS18B20 temperature.
5. Verify GSR ADC values.
6. Confirm CRC-valid CP2 packets.
7. Join the ESP8266 AP from Android and connect to TCP 7777.
8. Run the Prototype Lab acceptance test.
