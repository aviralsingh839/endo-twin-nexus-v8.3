# ENDO-TWIN NEXUS — V9 Wearable Build

Use the single current build manual:
`docs/WEARABLE_AND_MEGA_BUILD_MANUAL.md`

## Active controller

**Adafruit Feather ESP32-S3 2MB PSRAM**

## V9 pin map

| Function | Feather pin |
|---|---|
| I2C SDA | GPIO8 |
| I2C SCL | GPIO9 |
| Analog PPG | GPIO4 |
| GSR analog output | GPIO5 |
| DS18B20 DATA | GPIO6 + 4.7k pull-up to 3.3V |
| Status LED | onboard `LED_BUILTIN` |

All I2C modules share SDA/SCL:
- MPU6050: 0x68/0x69
- BME280: 0x76/0x77
- BH1750: 0x23/0x5C

The V9 firmware sends CP3 at 115200 over USB and can also provide Wi-Fi/TCP on port 7777.

**V9 wiring used by this project:** I2C SDA=GPIO8, SCL=GPIO9, analog PPG=GPIO4, GSR=GPIO5, DS18B20=GPIO6. Use this exact map for the current firmware.
