# ENDO-TWIN NEXUS — Current Wiring

The complete physical construction, enclosure dimensions, sensor placement, GSR finger-electrode assembly, and Mega hub assembly are documented in:

**docs/WEARABLE_AND_MEGA_BUILD_MANUAL.md**

## ESP32-S3 primary wearable (Adafruit Feather ESP32-S3 2MB PSRAM)

The V9 wearable now uses the board's labeled SDA/SCL pins. On this Feather these are GPIO3/GPIO4. GPIO8 is the board's A5/ADC1 pin and is used for analog PPG; GPIO5 (D5) is used for GSR; GPIO6 (D6) is used for DS18B20.

| Module | Signal | Feather pin |
|---|---|---|
| MPU6050 | SDA | **SDA / GPIO3** |
| MPU6050 | SCL | **SCL / GPIO4** |
| BME280 | SDA | **SDA / GPIO3** |
| BME280 | SCL | **SCL / GPIO4** |
| BH1750 | SDA | **SDA / GPIO3** |
| BH1750 | SCL | **SCL / GPIO4** |
| Analog Pulse Sensor | AO | **A5 / GPIO8 / ADC1** |
| GSR module | AO | **D5 / GPIO5 / ADC1** |
| DS18B20 | DATA | **D6 / GPIO6** |
| Status LED | onboard | `LED_BUILTIN` |

I2C power is supplied through the Feather's I2C power circuit; the V9 firmware explicitly enables `PIN_I2C_POWER` when the board core exposes it.

Expected digital addresses:
- MPU6050: 0x68 or 0x69
- BME280: 0x76 or 0x77
- BH1750: 0x23 or 0x5C
- MAX17048/LC709203 battery monitor: board-dependent 0x36 or 0x0B

The V9 transport is USB serial at 115200 and Wi-Fi SoftAP `ENDO-TWIN-S3` on TCP port 7777. The wire packet is `$CP3`.
## GSR finger electrodes

The electrodes connect to the **GSR module**, not directly to the ESP32 GPIO. The GSR module analog output goes to **D5 / GPIO5 (ADC1)**.

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
