# HARDWARE BUILD GUIDE - V8.3

## Overview

Two boards, both documented:

- **Arduino Nano wearable pod**: MAX30102 PPG, DS18B20 skin temperature, MPU6050 motion, optional GSR. Streams 20 Hz $CP2 packets.
- **Arduino Mega 2560 bench hub and base station**: pod sensors plus ECG, microphone, FSR, light and environment sensors, OLED, LEDs, buzzer and buttons. In relay mode forwards pod stream to PC.
- Optional **ESP8266 Wi-Fi bridge** relays same packets over TCP port 7777.

Dashboard runs with no hardware: demo mode, manual entries, replay, scenarios all exercise same longitudinal engine.

Firmware lives in `hardware/arduino/`: `chrono_pcos_mega_firmware` (bench hub), `chrono_pcos_nano_pod` (wearable pod), `chrono_pcos_esp8266_bridge` (Wi-Fi relay).

Preserved from V8.1, still works in V8.3.

---

## Bill of Materials

### Nano Pod (Primary Wearable)

- Arduino Nano (ATmega328P)
- MAX30102 PPG sensor (I2C, 3.3V, SDA A4, SCL A5)
- MPU6050 IMU (I2C, same bus, address 0x68)
- DS18B20 skin temperature (D2, OneWire, 4.7k pull-up to 5V)
- GSR module (optional, A0)
- LEDs: Green D8, Yellow D9, Red D10 via 220 ohm
- Buzzer D6
- Power: 3.7V LiPo + TP4056 charger + 5V boost, or USB phone charger (never mains when on body)
- Enclosure: small 3D printed pod, wrist/upper arm strap

### Mega Hub (Expanded Lab)

- Arduino Mega 2560
- All pod sensors plus:
  - ECG module (AD8232, A1)
  - Microphone (MAX4466, A2, plus RMS and pitch estimation)
  - FSR pressure sensor (A3, for finger pressure correction)
  - Light sensor (BH1750 I2C or LDR A4)
  - BME280 environment (I2C, room temp, humidity, pressure)
  - OLED 128x64 I2C (0x3C)
  - LEDs, buzzer, buttons (D22-33)
- Power: 5V 2A supply for bench use

### ESP8266 Bridge (Optional)

- ESP8266 NodeMCU
- Connects to Nano TX (via level shifter) and forwards to TCP 7777
- Allows wireless pod → PC

---

## Wiring - Nano Pod

```
MAX30102:
  VIN → 3.3V (or 5V if module has regulator)
  GND → GND
  SDA → A4
  SCL → A5
  INT → not connected

MPU6050:
  VCC → 5V (or 3.3V)
  GND → GND
  SDA → A4 (same bus)
  SCL → A5 (same bus)
  AD0 → GND (address 0x68)

DS18B20:
  VCC → 5V
  GND → GND
  DATA → D2 with 4.7k pull-up to 5V

GSR (optional):
  VCC → 5V
  GND → GND
  SIG → A0

LEDs:
  Green → D8 → 220Ω → GND
  Yellow → D9 → 220Ω → GND
  Red → D10 → 220Ω → GND

Buzzer:
  + → D6
  - → GND
```

**Calibrate IMU:** Rest board flat and still for first ~1.3s, mean becomes zero offset.

---

## Wiring - Mega Hub

See legacy `chrono_pcos_project V8/docs/ARDUINO_WIRING_GUIDE.md` for full Mega wiring - preserved.

Key:

- Same pod sensors on same pins where possible
- ECG AD8232: OUTPUT A1, LO- D30, LO+ D31, 3.3V, GND
- Mic: A2
- FSR: A3 with 10k divider
- BME280: I2C SDA 20, SCL 21
- OLED: I2C same bus
- Buttons: D22-25 with pull-ups

---

## Firmware Upload

**Libraries needed (Arduino Library Manager):**
- SparkFun MAX3010x Pulse and Proximity Sensor Library
- Adafruit MPU6050
- Adafruit Unified Sensor
- OneWire
- DallasTemperature
- Adafruit BME280
- Adafruit GFX + SSD1306 (for OLED)

**Upload:**

- Nano Pod: Board "Arduino Nano", Processor "ATmega328P", Port, Upload `chrono_pcos_nano_pod.ino`, Baud 115200, 20 Hz packets
- Mega Hub: Board "Arduino Mega 2560", Port, Upload `chrono_pcos_mega_firmware.ino`, set RELAY_POD_SERIAL1 1 if using pod → mega → PC relay (Nano TX D1 → Mega RX1 D19, common GND, power Nano from charger)
- ESP8266 Bridge: Board "NodeMCU 1.0", Upload `chrono_pcos_esp8266_bridge.ino`, connects to WiFi, TCP 7777

**Commands accepted on same serial (sent by dashboard):**
- LED,G / LED,Y / LED,R
- BEEP (120 ms tone)
- PING → $ACK,PONG,00

---

## Packet Protocol

**Enhanced $CP2 (20 Hz, 115200 baud):**
```
$CP2,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc
```

- ms: Arduino millis
- ir, red: PPG raw (0-262143, 18-bit)
- ax,ay,az: g, gx,gy,gz: dps
- temp0: skin temp °C, temp1: extra temp or nan
- gsr: raw 0-1023
- micRaw, micRms, micPitch: microphone
- ecg: raw or -1 if absent
- fsr: raw or -1
- lux: light or -1
- roomT, hum, press: BME280 or nan
- buttons: bitmask
- status: bitmask (PPG absent, saturated, MPU error, DS18B20 error, GSR saturated, I2C error, low quality, ECG leads off, BME280 error, OLED error, mic low, FSR artifact)
- crc: XOR of all chars in payload before final comma, hex 2 digits

**Legacy $CP:** older 15-field version still supported by parser.

**CRC:** XOR all characters in payload before final comma.

**Parser:** `src/serial_io/packet_parser.py` handles both, verifies CRC, raises PacketParseError on bad prefix, too few fields, invalid CRC, numeric conversion failed.

---

## Power and Safety

- Educational physiological monitoring only, not diagnostic medical device
- Keep pod on battery or laptop's own USB when on person, never mains
- LiPo: use protected cell, TP4056 charger, 5V boost, fuse
- Clean sensors with alcohol, not water
- If skin irritation, remove
- No medical decisions from this hardware alone

---

## Testing

**Pod:**
- Upload, open Serial Monitor 115200, should see $CP2 lines at 20 Hz
- Cover MAX30102 with finger: ir should rise >5000, status bit PPG absent clears
- Move: motion_index rises
- Warm finger: temp rises

**Mega Hub:**
- Same, plus ECG: connect leads, check ecg_raw and quality
- Relay mode: Nano TX → Mega RX1, Mega USB to PC, dashboard connects to Mega only, should see pod data

**Dashboard:**
- Connect wearable button → live plots
- Demo mode → synthetic stream, clearly labelled
- Scenario load → 6 scenarios
- Disconnect sensor: should show low quality, not crash, banner instead of guess

---

## Software Gracefully Handles Missing Sensors

- If MAX30102 disconnected: ir=0, quality 0, artifact missing, overall quality low, prediction withheld, banner
- If temp disconnected: temp_c None, quality 0, does not drag other sensors down (mean over PRESENT only)
- If GSR absent: optional channel, never drags score down
- Packet corruption: CRC mismatch → PacketParseError, packet discarded, app continues
- Duplicate packet: timestamp same, handled
- Delayed packet: stale >6s → artifact stale, quality 0.2
- Missing packet: no sample, history gap, longitudinal handles missing
- Noisy PPG: quality heuristic + trained model blended 60/40, noisy → quality low
- Excessive motion: motion_index >1.5 → quality penalty
- Reconnection: quality recovers

All tested in `tests/test_hardware_failures.py` and `tests/test_sensor_quality.py`

---

## V8.3 Preservation

- V8.1 Nano pod firmware kept, still works
- V8.1 Mega hub firmware kept, still works
- V8.1 ESP8266 bridge kept
- No force every sensor required - software gracefully operates with missing sensors
- New quality control and longitudinal engine work with whatever sensors present
