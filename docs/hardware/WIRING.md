# ENDO-TWIN NEXUS — Current Wiring

The complete physical construction, enclosure dimensions, sensor placement, GSR finger-electrode assembly, and Mega hub assembly are documented in:

**docs/WEARABLE_AND_MEGA_BUILD_MANUAL.md**

## ESP32-S3 primary wearable

| Module | Connection |
|---|---|
| MAX30102 | SDA GPIO8, SCL GPIO9 |
| MPU6050 | SDA GPIO8, SCL GPIO9 |
| BME280 | SDA GPIO8, SCL GPIO9 |
| BH1750 | SDA GPIO8, SCL GPIO9 |
| GSR module AO | GPIO4 / ADC |
| Status LED | GPIO2 through 220 Ω resistor |
| I2C VCC | 3.3 V-compatible supply |
| Common ground | ESP32-S3 GND |

The four I2C devices share the same bus. The wearable uses Wi-Fi/TCP on port 7777.

## GSR finger electrodes

The electrodes connect to the **GSR module**, not directly to the ESP32 GPIO. The GSR module analog output goes to GPIO4.

Recommended prototype: index-finger electrode + middle-finger electrode, with approximately 20–30 mm center-to-center spacing when the fingers are relaxed.

Use a battery-powered isolated setup for body-contact testing and follow the GSR module's electrical limits.

## Arduino Mega 2560 lab controller

| Module | Mega connection |
|---|---|
| I2C | SDA D20, SCL D21 |
| DS18B20 | D2 |
| GSR | A0 |
| MAX4466 | A1 |
| AD8232 OUT | A2 |
| FSR | A3 |
| ECG LO+ / LO− | D11 / D12 |
| Buttons | D3/D4/D5 |
| LEDs | D8/D9/D10 |
| Buzzer | D6 |

For the complete enclosure/box assembly, use the unified manual above.
