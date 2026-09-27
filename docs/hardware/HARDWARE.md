# ENDO-TWIN NEXUS — Hardware Architecture

## Active architecture

| Controller | Role | Active |
|---|---|---|
| **Adafruit Feather ESP32-S3 2MB PSRAM** | **Primary wireless wearable** | YES |
| **Arduino Mega 2560** | Bench / lab / expanded controller | YES |
| ESP8266 | Superseded wearable implementation | Legacy |
| ESP32 original wearable | Historical implementation | Legacy |
| Arduino Nano | Historical implementation | Legacy |

## ESP32-S3 wearable

Firmware:
`hardware/esp32s3/endo_twin_wearable/endo_twin_wearable.ino`

Sensors:
- Analog Pulse Sensor / PPG: **A5 / GPIO8 / ADC1**
- GSR/EDA module analog output: **D5 / GPIO5 / ADC1**
- DS18B20: **D6 / GPIO6**
- MPU6050: I2C on **SDA GPIO3 / SCL GPIO4**
- BME280: I2C on **SDA GPIO3 / SCL GPIO4**
- BH1750: I2C on **SDA GPIO3 / SCL GPIO4**

Expected I2C addresses:
- MPU6050: 0x68 or 0x69
- BME280: 0x76 or 0x77
- BH1750: 0x23 or 0x5C

Transport:
- USB serial 115200
- Wi-Fi SoftAP `ENDO-TWIN-S3`
- password `endotwins3`
- TCP port 7777
- V9 packet: `$CP3,ms,ppg_raw,gsr_raw,ax,ay,az,gx,gy,gz,skinT,roomT,hum,press,lux,status,crc`

The V9 firmware uses the Feather's native I2C pins instead of generic ESP32 DevKit pins. The single analog PPG channel is used for pulse/HR/HRV research features; conventional SpO2 is not computed from one analog channel.
## Mega hub

Firmware:
`hardware/arduino/endo_twin_mega_lab/endo_twin_mega_lab.ino`

The Mega remains the separate bench/lab controller for expanded experiments.

## Unified build guide

Physical assembly, dimensions, wiring, sensor placement, GSR safety, wearable enclosure and Mega box assembly:

`docs/WEARABLE_AND_MEGA_BUILD_MANUAL.md`

## Safety

Research/educational prototype only. Verify sensor voltage compatibility, battery isolation, body-contact safety, wiring, placement and calibration before testing on a person.
