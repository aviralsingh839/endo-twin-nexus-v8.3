# HARDWARE BUILD GUIDE - ENDO-TWIN V8.7

## Overview

- **ESP32 DevKit: primary wearable controller. Arduino Nano is not required.**
- **Arduino UNO: bench/prototype validation** for Generic Analog Pulse Sensor + MPU6050 + DS18B20 + optional GSR.
- **Arduino Mega 2560: expanded laboratory/hub platform** for ECG, microphone, FSR, environment sensors, OLED, buttons and other extensions.
- **ESP32 BLE → Android** is the preferred wearable transport; USB serial at 115200 remains available for PC diagnostics.
- The canonical data contract remains newline-delimited **$CP2** with XOR CRC.

### Active firmware

- Wearable: `hardware/esp32/endo_twin_wearable/endo_twin_wearable.ino`
- UNO bench: `hardware/arduino/endo_twin_uno_bench/endo_twin_uno_bench.ino`
- Mega bench/hub: `hardware/arduino/chrono_pcos_mega_firmware/chrono_pcos_mega_firmware.ino`
- `hardware/arduino/chrono_pcos_nano_pod/` and `hardware/arduino/chrono_pcos_esp8266_bridge/` are retained as legacy references only and are not required for the current build.

---

## Bill of Materials

### ESP32 wearable

- ESP32 DevKit
- Generic Analog Pulse Sensor PPG (single-channel analog waveform)
- MPU6050 IMU
- DS18B20 + 4.7k resistor
- GSR module (optional)
- Battery/power-bank solution suitable for isolated body-worn prototype use
- Insulated wire, perfboard/breadboard for bench bring-up, enclosure and strap

### UNO bench

- Arduino UNO
- Same Generic Analog Pulse Sensor, MPU6050, DS18B20 and optional GSR
- USB cable
- Breadboard/jumper wires

### Mega expanded lab

Use the existing Mega firmware for ECG (AD8232), microphone, FSR, BH1750, BME280, OLED, LEDs, buzzer and buttons.

---

## ESP32 wiring

```
Generic Analog Pulse Sensor:
  SIG     -> PULSE_PIN (ADC-capable GPIO; choose the correct pin for your ESP32/ESP32-S3)
  VCC     -> the module's supported supply voltage
  GND     -> GND

MPU6050:
  VCC     -> compatible supply for your breakout
  GND     -> GND
  SDA     -> GPIO21
  SCL     -> GPIO22
  AD0     -> GND for address 0x68

DS18B20:
  VCC     -> 3.3V
  GND     -> GND
  DATA    -> GPIO18
  4.7k resistor between DATA and 3.3V

GSR:
  SIG     -> GPIO34
  VCC/GND -> according to your GSR module specification

Optional status LED:
  GPIO2 -> resistor -> LED -> GND
```

**Important:** breakout-board voltage handling varies. Do not assume a sensor marked "5V" or "VIN" is safe to connect directly to an ESP32 GPIO. Keep ESP32 GPIO signals at 3.3V levels.

---

## UNO bench wiring

```
Analog Pulse Sensor: SIG -> A1 (or another analog-capable input); MPU6050: SDA=A4, SCL=A5
DS18B20:          DATA=D2, 4.7k pull-up to 5V
GSR:              SIG=A0
USB serial:       115200 baud
```

The UNO is for desk testing and validation, not the body-worn controller.

---

## Firmware upload

### ESP32

Install the ESP32 board package in Arduino IDE, select your exact ESP32 board, then upload:

`hardware/esp32/endo_twin_wearable/endo_twin_wearable.ino`

Libraries:
- Adafruit MPU6050
- Adafruit Unified Sensor
- OneWire
- DallasTemperature
- BLE support from the Arduino-ESP32 core

### UNO

Select Arduino UNO and upload:

`hardware/arduino/endo_twin_uno_bench/endo_twin_uno_bench.ino`

### Mega

Select Arduino Mega 2560 and use the existing:

`hardware/arduino/chrono_pcos_mega_firmware/chrono_pcos_mega_firmware.ino`

---

## ESP32 BLE interface

Device name: **ENDO-TWIN-PULSE**

Service:
`7f300001-6c12-4f70-9e6b-8e9f7b8b1001`

Notify characteristic:
`7f300002-6c12-4f70-9e6b-8e9f7b8b1001`

Command characteristic:
`7f300003-6c12-4f70-9e6b-8e9f7b8b1001`

The notify characteristic sends complete $CP2 lines. Android should preserve the same parser, CRC validation, provenance and missing-data semantics used by the desktop pipeline.

---

## Bring-up and testing

1. Flash ESP32.
2. Open USB serial at 115200 and verify $CP2 lines.
3. Confirm the device advertises as **ENDO-TWIN-ESP32**.
4. Send `WHOAMI` over USB and verify the identity response.
5. With no finger on Generic Analog Pulse Sensor, verify the PPG-absent status bit instead of fabricated signal.
6. Place a finger gently on the Generic Analog Pulse Sensor and verify IR/RED change.
7. Move the MPU6050 and verify accelerometer/gyro fields.
8. Verify DS18B20 temperature changes.
9. Verify GSR only after its module is wired correctly.
10. Validate packets with the existing `PacketParser` and CRC tests.
11. Connect Android over BLE and verify notification streaming.
12. Only after bench validation, package the electronics into the body-worn enclosure.

---

## Protocol

```
$CP2,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc
```

ESP32/UNO do not provide every extended channel, so absent channels are sent as explicit placeholders. Real records must never be silently filled with synthetic measurements.

---

## Power and safety

- Educational/research prototype only; not a diagnostic medical device.
- Never connect a body-worn prototype directly to mains.
- Use a protected battery/power solution and electrically isolated testing.
- Insulate exposed conductors and strain-relieve sensor wiring.
- Remove the prototype if skin irritation or heating occurs.
- Do not base medical decisions on this hardware alone.


## V8.8 Analog Pulse Sensor migration

The current wearable build can use the generic analog Pulse Sensor module shown in the project hardware reference image instead of the MAX3010x optical PPG. The module is a single-channel analog pulse waveform source: SIG connects to an ADC-capable GPIO, VCC to the sensor's supported supply, and GND to common ground. ENDO-TWIN keeps the existing $CP2 transport so the rest of the desktop/BLE pipeline remains compatible. The primary waveform is carried in the existing `ir` slot for transport compatibility and is explicitly marked as `ANALOG_PULSE`/status bit 12. The `red` field is `-1` because there is no optical red channel.

The processing layer continues to support heart-rate and pulse-timing/HRV-style analysis from the waveform, with motion-aware quality scoring. It must not estimate SpO2 from this single-channel analog sensor. This hardware is suitable for an educational research prototype, not for diagnosis or clinical measurement.
