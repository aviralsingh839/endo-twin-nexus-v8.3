# ENDO-TWIN NEXUS — V9 Wearable Build

Use the single current build manual:
`docs/WEARABLE_AND_MEGA_BUILD_MANUAL.md`

## Active controller

**Adafruit Feather ESP32-S3 2MB PSRAM**

## V9 pin map

| Function | Feather pin |
|---|---|
| I2C SDA | SDA / GPIO3 |
| I2C SCL | SCL / GPIO4 |
| Analog PPG | A5 / GPIO8 |
| GSR analog output | D5 / GPIO5 |
| DS18B20 DATA | D6 / GPIO6 + 4.7k pull-up to 3.3V |
| Status LED | onboard `LED_BUILTIN` |

All I2C modules share SDA/SCL:
- MPU6050: 0x68/0x69
- BME280: 0x76/0x77
- BH1750: 0x23/0x5C

The V9 firmware sends CP3 at 115200 over USB and can also provide Wi-Fi/TCP on port 7777.

**Important:** GPIO21/22 and GPIO34 are not the V9 Feather wiring. Move the sensor wires to the pins above before testing the updated firmware.
