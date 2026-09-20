# CHRONO-PCOS V8.1 Wiring Guide: Arduino Mega 2560 + Arduino Nano

This is the complete hardware guide for the build I actually use: an **Arduino
Mega 2560** as the bench hub / base station and an **Arduino Nano** as the
wearable pod that stays on the body. It covers every wire, both firmware
sketches, the packet protocol, power, testing and troubleshooting.

The hardware is the data-collection layer only. All analysis, scoring and
reporting happens in the Python dashboard (see `docs/HOW_THE_PROJECT_WORKS.md`).
Nothing in this guide or in the firmware diagnoses anything; the system is an
educational research prototype.

---

## 1. The two boards and what each one does

| Board | Role in my build | Why this board |
|---|---|---|
| Arduino Mega 2560 | Bench hub and base station. Runs all bench sensors (PPG, IMU, temperature, GSR, ECG, microphone, FSR, light, environment), drives the OLED, LEDs, buzzer and buttons, and talks to the PC over USB. | 54 digital pins, 16 analog inputs, 4 UARTs. The full sensor set does not fit on a smaller board. |
| Arduino Nano | Wearable pod. Carries only the three continuous signals (PPG, skin temperature, motion) plus optional GSR, and streams them at 20 Hz. | Same ATmega328P as an UNO in a small board that can be strapped to the wrist or forearm. Cheap enough to leave on the body. |

The Nano is electrically an UNO, so any UNO wiring note applies to it: I2C is on
**A4 (SDA) and A5 (SCL)**, and the OneWire temperature bus is on **D2**. The Mega
is different: its I2C is on **pin 20 (SDA) and pin 21 (SCL)**, never A4/A5.

There are three ways to run the system, in increasing order of hardware:

1. **Mega only** (bench demo). Everything wired to the Mega, dashboard on the
   Mega's USB port. This is what I use at the exhibition table.
2. **Nano pod only** (wearable demo). The pod plugged straight into the laptop
   USB, dashboard on the Nano's COM port.
3. **Nano pod + Mega base station** (my full build). The pod is tethered to the
   Mega over two wires, and the Mega relays the pod stream to the PC. The Mega
   keeps its OLED, LEDs, buzzer and buttons as the table-side interface.

All three feed the exact same `$CP2` packet into the same parser, so the
dashboard cannot tell them apart.

---

## 2. Pin map: Arduino Mega 2560 (bench hub)

Firmware: `arduino/chrono_pcos_mega_firmware/chrono_pcos_mega_firmware.ino`

| Module | Module pin | Mega pin | Notes |
|---|---|---|---|
| MAX30102 PPG | VCC | 3.3V | Prefer 3.3V; check your breakout before using 5V |
| MAX30102 PPG | GND | GND | Common ground rail |
| MAX30102 PPG | SDA | 20 (SDA) | I2C address usually 0x57 |
| MAX30102 PPG | SCL | 21 (SCL) | |
| MPU6050 | VCC | 5V | GY-521 boards accept 5V |
| MPU6050 | GND | GND | |
| MPU6050 | SDA / SCL | 20 / 21 | Address 0x68 (AD0 to GND) |
| BH1750 light | VCC / GND | 3.3V or 5V / GND | Circadian light exposure |
| BH1750 light | SDA / SCL | 20 / 21 | Address 0x23 |
| BME280 environment | VCC / GND | 3.3V or 5V / GND | Room temperature, humidity, pressure |
| BME280 environment | SDA / SCL | 20 / 21 | Address 0x76 or 0x77 |
| SSD1306 OLED | VCC / GND | 5V or 3.3V / GND | 0.96 inch I2C display |
| SSD1306 OLED | SDA / SCL | 20 / 21 | Address 0x3C |
| DS18B20 wrist | VCC / GND / DATA | 5V / GND / D2 | OneWire bus |
| DS18B20 fingertip | VCC / GND / DATA | 5V / GND / D2 | Second sensor on the same bus |
| Pull-up resistor | 4.7k | D2 to 5V | One resistor for the whole OneWire bus |
| GSR module | VCC / GND / AO | 5V / GND / A0 | Stress and autonomic arousal |
| MAX4466 microphone | VCC / GND / OUT | 5V / GND / A1 | Experimental voice proxy |
| AD8232 ECG | 3.3V / GND | 3.3V / GND | Never 5V |
| AD8232 ECG | OUTPUT | A2 | Beat timing and HRV reference |
| AD8232 ECG | LO+ / LO- | D11 / D12 | Lead-off detection |
| AD8232 ECG | SDN | not connected | |
| FSR pressure | leg 1 / leg 2 | 5V / A3 | With 10k from A3 to GND (voltage divider) |
| Mode button | both sides | D3 and GND | INPUT_PULLUP, pressed reads LOW |
| Baseline button | both sides | D4 and GND | Starts a baseline capture idea on the bench |
| Post button | both sides | D5 and GND | Post-meal / post-challenge marker |
| Buzzer | + / - | D6 / GND | Active buzzer module; transistor if high current |
| Green LED | anode via 220 ohm | D8 | Good signal, low estimate |
| Yellow LED | anode via 220 ohm | D9 | Medium or low confidence |
| Red LED | anode via 220 ohm | D10 | High estimate or sensor error |
| All LED cathodes | cathode | GND | |
| USB-B cable | to PC | USB port | The dashboard connection |

Block view:

```text
                        ARDUINO MEGA 2560
      +---------------------------------------------------+
 I2C  | 20 SDA -- MAX30102, MPU6050, BH1750, BME280, OLED  |
 BUS  | 21 SCL ------------------------------------------  |
      |                                                    |
 TEMP | D2 ---- DS18B20 wrist + DS18B20 fingertip          |
      |         4.7k pull-up from D2 to 5V                 |
      |                                                    |
 ANAL | A0 GSR    A1 microphone    A2 ECG    A3 FSR        |
      |                                                    |
 DIGI | D3 D4 D5 buttons   D6 buzzer   D8 D9 D10 LEDs      |
      | D11 ECG LO+   D12 ECG LO-                          |
      |                                                    |
 UART | Serial  (USB)  -> Python dashboard                 |
      | Serial1 (D19 RX / D18 TX) -> Nano pod in relay mode|
      +---------------------------------------------------+
```

---

## 3. Pin map: Arduino Nano (wearable pod)

Firmware: `arduino/chrono_pcos_nano_pod/chrono_pcos_nano_pod.ino`

| Module | Module pin | Nano pin | Notes |
|---|---|---|---|
| MAX30102 PPG | VCC | 3.3V | PPG is the pod's main signal |
| MAX30102 PPG | GND | GND | |
| MAX30102 PPG | SDA | A4 | Nano I2C is A4/A5 |
| MAX30102 PPG | SCL | A5 | |
| MPU6050 | VCC | 5V or 3.3V | Per your breakout |
| MPU6050 | GND | GND | |
| MPU6050 | SDA / SCL | A4 / A5 | Same bus as the PPG |
| MPU6050 | AD0 | GND | Keeps address 0x68 |
| DS18B20 | VCC / GND / DATA | 5V or 3.3V / GND / D2 | Tape the probe to skin, insulated from air |
| Pull-up resistor | 4.7k | D2 to VCC of the probe | Required |
| GSR module (optional) | VCC / GND / AO | 5V / GND / A0 | Two electrodes on the palm or fingers |
| Status LEDs (optional) | via 220 ohm | D8 / D9 / D10 | Handy while bench testing the pod |
| Buzzer (optional) | + / - | D6 / GND | Only for bench testing |
| TX (for relay) | D1 | to Mega D19 (RX1) | Only in base-station configuration |
| GND | GND | to Mega GND | Common ground with the Mega |

The pod sketch sends unused `$CP2` channels as fixed placeholders (mic and
environment fields as `nan`, ECG and FSR as `-1`), so the dashboard treats a pod
stream exactly like a Mega stream.

---

## 4. The three configurations, wired

### 4.1 Mega only (bench demo)

```text
sensors --> Mega --USB-B--> laptop --> python -m src.app --port <mega port>
```

Mega firmware with `RELAY_POD_SERIAL1 0` (the default). The Mega samples
everything itself and prints `$CP2` lines at 20 Hz on its USB port.

### 4.2 Nano pod only (wearable demo)

```text
pod (Nano) --USB-mini--> laptop --> python -m src.app --port <nano port>
```

No firmware change: the Nano has a single UART and the USB chip sits on the
same pins, so plugging in the USB cable is the same serial line.

### 4.3 Nano pod + Mega base station (relay)

```text
pod (Nano) ---D1/TX---> Mega D19/RX1          Nano powered by a USB
             GND -------> GND                 phone charger (5V)
                        Mega --USB-B--> laptop (relay firmware)
```

Steps:

1. In `chrono_pcos_mega_firmware.ino` set `#define RELAY_POD_SERIAL1 1`.
2. Wire Nano D1 to Mega D19, and Nano GND to Mega GND. Two wires only.
3. Power the Nano from its own USB charger, not from the laptop, so the Nano's
   USB chip does not fight the Mega for the serial line.
4. Upload both sketches. The Mega now forwards every pod line to its USB port
   unchanged, forwards dashboard commands (LED, BEEP, PING) back to the pod,
   and shows a `POD RELAY lines:<n>` counter on its OLED.
5. On the laptop connect to the **Mega** port only. The dashboard sees one
   clean stream.

If you forget step 1, the Mega keeps printing its own packets as well and the
dashboard receives two interleaved streams. That is the most common relay
mistake; the fix is the one-line define.

---

## 5. I2C bus rules

All I2C sensors share two wires plus ground. On the Mega those wires are pins
20 and 21; on the Nano they are A4 and A5.

| Module | Usual address |
|---|---|
| MAX30102 | 0x57 |
| MPU6050 | 0x68 (0x69 with AD0 high) |
| BH1750 | 0x23 (or 0x5C) |
| BME280 | 0x76 (or 0x77) |
| SSD1306 | 0x3C (or 0x3D) |

Rules that save hours:

- No two devices may share an address on one bus. The set above is conflict
  free. A DS3231 RTC would collide with the MPU6050 at 0x68; I do not use one.
- Two MAX30102 sensors would collide; that needs a TCA9548A multiplexer. The
  build uses one PPG sensor per board.
- Keep I2C wires short (under about 30 cm). Long I2C runs are the usual cause
  of "sensor not found" on a breadboard.
- Both boards are 5V logic. Most hobby breakouts contain their own regulator
  and level shifting and work directly. If a breakout is documented as
  3.3V-only with no level shifting, put a bidirectional I2C level converter
  between board and sensor.

---

## 6. OneWire temperature wiring

```text
VCC (5V or 3.3V) ----+----------- DS18B20 red (VDD)
                     |
                   4.7k
                     |
D2 ------------------+----------- DS18B20 yellow/white (DATA)

GND ----------------------------- DS18B20 black (GND)
```

One 4.7k pull-up serves the whole bus. A second DS18B20 joins the same three
nodes; the firmware reads index 0 as `temp0` (wrist) and index 1 as `temp1`
(fingertip). If the dashboard shows `-127.00` or `nan` for temperature, the bus
has no pull-up, the data wire is on the wrong pin, or the probe is reversed.

Placement:

| Probe | Site | What it feeds |
|---|---|---|
| DS18B20 #1 | Inner wrist or forearm, taped, insulated from air with a small foam pad | Skin temperature rhythm, circadian domain |
| DS18B20 #2 (Mega build) | Fingertip next to the PPG window | Perfusion context for the PPG |

---

## 7. Analog circuits

**GSR (A0).** Module VCC to 5V, GND to GND, AO to A0. Two electrodes on the
palm or on two fingers of one hand. Readings are module-specific raw ADC
counts; the dashboard tracks the person's own baseline instead of assuming
microsiemens, which is why raw values are acceptable here.

**FSR finger pressure (A3, Mega build).** Voltage divider:

```text
5V --- FSR ---+--- A3
              |
            10k
              |
             GND
```

The FSR sits under the finger that rests on the PPG window. High readings mean
the finger is pressing hard enough to squeeze the pulse out of the signal, and
the signal-quality layer marks the window accordingly.

**AD8232 ECG (A2, Mega build).** 3.3V to 3.3V, GND to GND, OUTPUT to A2, LO+ to
D11, LO- to D12, SDN left open. Electrodes: RA below the right clavicle, LA
below the left clavicle, RL on the lower right ribs. This channel is used for
beat timing and HRV reference only. Safety rules are in section 12.

**MAX4466 microphone (A1, Mega build).** VCC 5V, GND, OUT to A1. Experimental
voice proxy; the firmware computes RMS and a zero-crossing pitch estimate over
256 samples.

---

## 8. Digital I/O: buttons, LEDs, buzzer

Buttons: one side to D3 / D4 / D5, other side to GND. The firmware sets
`INPUT_PULLUP`, so an unpressed button reads HIGH and a pressed button reads
LOW. No external resistors needed.

LEDs: anode through a 220 ohm resistor to D8 (green), D9 (yellow), D10 (red);
cathodes to GND. The dashboard drives them with `LED,G`, `LED,Y`, `LED,R`
commands over the same serial line, and forces yellow whenever confidence is
below 35 so a weak-data state can never look like a green "all clear".

Buzzer: D6 to the module's +, GND to -. `tone(D6, 2200, 120)` gives a short
beep; the dashboard sends `BEEP`.

---

## 9. Power

Bench rig:

- Power the Mega from the laptop USB-B cable. That is enough for the whole
  breadboard if you keep the OLED and buzzer counts modest.
- Build two breadboard rails: `5V` and `GND` from the Mega, plus a separate
  `3.3V` rail for sensors that prefer 3.3V. Never feed high-current modules
  from the 3.3V pin.
- Keep one common ground for everything, including the Nano in relay mode and
  any ESP8266 bridge.

Pod:

- For a tethered exhibition demo, power the Nano from its USB cable (laptop or
  a 5V phone charger). Simplest and safest.
- For an untethered trial: 3.7V Li-ion cell to a TP4056 charger board, TP4056
  output to a slide switch, switch to a 3.3V LDO (HT7333 or similar), and the
  LDO output to the Nano VIN only if the Nano's own regulator is used, or to
  the 5V pin if you bypass it. Measure the rail with a multimeter before
  strapping anything to a person. Never connect raw cell voltage to a sensor.
- The pod draws a few tens of mA with the PPG and IMU running; budget battery
  life by measurement on your own hardware, not by calculation.

Wireless alternative: the ESP8266 bridge
(`arduino/chrono_pcos_esp8266_bridge/chrono_pcos_esp8266_bridge.ino`) relays
the Mega's serial bytes over TCP port 7777. Wire Mega D18 (TX1) to the ESP RX
and Mega D19 (RX1) to the ESP TX with common ground, then start the dashboard
with `python -m src.app --net 192.168.4.1:7777`. In relay-pod mode Serial1 is
already used by the pod, so use the bridge either in the Mega-only
configuration or with the pod connected directly to the PC.

---

## 10. Sensor placement on the body

| Sensor | Site | Reason |
|---|---|---|
| MAX30102 (+ FSR on the bench) | Fingertip for demos; forearm or wrist window for wear trials | Clean pulse waveform, least motion |
| DS18B20 #1 | Inner wrist or forearm | Skin temperature rhythm |
| MPU6050 | On the pod body, strap to wrist or upper arm | Activity, restlessness, motion gating of the PPG |
| GSR electrodes | Palm, or index and middle finger of one hand | Sympathetic sweat response |
| AD8232 electrodes | Chest triangle (RA, LA, RL) | Beat timing reference, bench only |
| BH1750 | Facing ambient light on the bench rig | Circadian light exposure |
| MAX4466 | Near the collar on the bench rig | Experimental voice proxy |

For wear trials the pod sits on the ventral forearm about 5 cm below the elbow
crease, PPG window against the skin, temperature probe a couple of centimetres
away under the same strap. Upper-arm medial side is the alternative if the
forearm site picks up too much motion.

---

## 11. Firmware, upload and first serial check

Libraries (Arduino IDE Library Manager):

- SparkFun MAX3010x Pulse and Proximity Sensor Library
- Adafruit MPU6050
- Adafruit Unified Sensor
- OneWire
- DallasTemperature
- For the Mega build only: BH1750, Adafruit BME280, Adafruit GFX, Adafruit SSD1306
- For the ESP8266 bridge only: the ESP8266 board package

Board settings in the IDE:

| Sketch | Board entry | Processor | Port |
|---|---|---|---|
| chrono_pcos_mega_firmware | Arduino Mega or Mega 2560 | ATmega2560 | the Mega's COM port |
| chrono_pcos_nano_pod | Arduino Nano | ATmega328P | the Nano's COM port |
| chrono_pcos_esp8266_bridge | Generic ESP8266 module | | the ESP's COM port |

Upload order and checks:

1. Upload the sketch with only the board connected. Open the Serial Monitor at
   **115200 baud**. You should see `$CP2,...` lines 20 times a second (Mega and
   Nano), each ending in a two-digit hex CRC.
2. Cover the MAX30102 window with a fingertip: `ir` should jump from near zero
   to tens of thousands and visibly pulse.
3. Wave the board: the acceleration fields move. Rest it: they settle near 0,
   0, 1 after the start-up bias calibration (the first ~1.3 s, keep the board
   still).
4. Hold the DS18B20 probe: `temp0` drifts towards skin temperature within a
   few seconds. A stuck `-127.00` means the OneWire bus is wrong.
5. Squeeze the GSR electrodes: the `gsr` field moves slowly.
6. Type `PING` and send: the board answers `$ACK,PONG,00`. Type `LED,R`: the red
   LED lights. This proves the command path the dashboard uses.
7. Only now start the dashboard: `python -m src.app --port <port>` and watch
   the Live Wearable tab fill in.

The CRC is the XOR of every character before the final comma, printed as two
hex digits. The parser recomputes it and drops any line that disagrees, so a
noisy cable shows up as parse errors in the status bar instead of corrupted
numbers in the score.

---

## 12. The packet protocol

`$CP2` (Mega and Nano pod), 25 fields, 20 Hz:

| # | Field | Unit | Source |
|---|---|---|---|
| 1 | ms | ms | board millis() |
| 2 | ir | ADC counts | MAX30102 IR |
| 3 | red | ADC counts | MAX30102 red |
| 4-6 | ax, ay, az | g | MPU6050 accel, bias removed |
| 7-9 | gx, gy, gz | deg/s | MPU6050 gyro, bias removed |
| 10 | temp0 | degC | DS18B20 wrist |
| 11 | temp1 | degC | DS18B20 fingertip (nan on the pod) |
| 12 | gsr | raw ADC | GSR module |
| 13 | micRaw | raw ADC | microphone last sample |
| 14 | micRms | counts | microphone RMS over 256 samples |
| 15 | micPitch | Hz | zero-crossing pitch estimate |
| 16 | ecg | raw ADC | AD8232 output |
| 17 | fsr | raw ADC | finger pressure divider |
| 18 | lux | lux | BH1750 |
| 19 | roomT | degC | BME280 |
| 20 | hum | % | BME280 |
| 21 | press | hPa | BME280 |
| 22 | buttons | bitmask | bit0 mode, bit1 baseline, bit2 post |
| 23 | status | bitmask | see below |
| 24 | crc | hex | XOR of the payload |

Status bits (value = 1 shifted by the bit number):

| Bit | Meaning |
|---|---|
| 0 | PPG finger absent (IR below 5000) |
| 1 | PPG saturated |
| 2 | MPU6050 error |
| 3 | DS18B20 error |
| 4 | GSR saturated |
| 5 | I2C error |
| 6 | Low signal quality |
| 7 | ECG leads off |
| 8 | BME280 error |
| 9 | OLED error |
| 10 | Microphone signal too low |
| 11 | FSR pressure artifact |

The parser also accepts the older 15-field `$CP` frame, so sessions recorded
with earlier firmware can still be replayed.

Commands the dashboard sends back on the same line: `LED,G`, `LED,Y`, `LED,R`,
`BEEP`, `PING`.

---

## 13. Bill of materials

Prices are rough Indian retail ranges seen on Robu.in, Robocraze and similar
stores. They move around; confirm in the cart before ordering, and skip
anything you already own.

Core (both configurations):

| Item | Qty | Approx. INR |
|---|---|---|
| Arduino Mega 2560 compatible | 1 | 1050 to 1350 |
| Arduino Nano with cable | 1 | 350 to 600 |
| MAX30102 PPG module | 2 (one per board) | 190 to 600 each |
| MPU6050 (GY-521) | 2 | 150 to 170 each |
| DS18B20 waterproof probe | 2 to 3 | 60 to 90 each |
| 4.7k, 10k, 220 ohm resistors | a few each | 5 to 50 |
| Breadboards (830 point) | 2 | 60 to 120 each |
| Jumper wires M-M, M-F | 1 set each | 100 to 150 |
| LEDs green/yellow/red | 3+ | 10 to 30 |
| Active buzzer module | 1 | 25 to 50 |
| Tactile push buttons | 3 | 15 to 40 |
| USB cables (B and mini) | 2 | 25 to 70 each |

Mega-only extras (full bench rig):

| Item | Qty | Approx. INR |
|---|---|---|
| GSR sensor module | 1 | 300 to 1150 |
| AD8232 ECG module + electrodes | 1 | 500 to 1150 |
| FSR (square or round) | 1 | 130 to 380 |
| BH1750 light module | 1 | 99 to 130 |
| BME280 module | 1 | 530 to 780 |
| MAX4466 microphone module | 1 | 99 to 200 |
| SSD1306 0.96 inch OLED | 1 | 160 to 280 |

Pod extras for untethered wear trials:

| Item | Qty | Approx. INR |
|---|---|---|
| Li-ion cell 150 to 250 mAh | 1 | 150 to 300 |
| TP4056 charger board | 1 | 40 to 80 |
| 3.3V LDO (HT7333 or similar) | 1 | 20 to 60 |
| Slide switch | 1 | 10 to 30 |
| Strap or velcro band, foam pad | 1 | 50 to 150 |

A working minimum is Mega + MAX30102 + MPU6050 + DS18B20 + breadboard and
wires, around 1800 to 2500 INR if you own nothing. My full two-board build with
the bench extras lands near 6000 to 8000 INR. Buy in this order if budget is
tight: Mega, MAX30102, MPU6050, DS18B20, Nano, GSR, OLED, then the rest.

---

## 14. Troubleshooting

| Symptom | First things to check |
|---|---|
| Serial Monitor shows garbage characters | Baud rate is not 115200 |
| No `$CP2` lines at all | Wrong board or port selected; cable is charge-only; CH340 driver missing on the Nano |
| `ir` stays near 0 | No finger on the window, or PPG VCC missing; check the I2C address 0x57 |
| `ir` pinned above 250000 | Finger pressed hard or LED current too high; status bit 1 will be set |
| Temperature `-127.00` or `nan` | Missing 4.7k pull-up, DATA on the wrong pin, probe wired backwards |
| Motion values never settle | Board moved during the start-up bias calibration; power cycle and hold it still |
| OLED blank | Address 0x3C vs 0x3D, or the OLED on 5V when it wants 3.3V |
| Dashboard says pyserial missing | `pip install -r requirements.txt` in the project folder |
| Parse errors in the status bar | Loose jumper wires, or two boards writing to one port |
| Two interleaved streams in relay mode | `RELAY_POD_SERIAL1` left at 0 in the Mega sketch |
| Nothing arrives in relay mode | Nano D1 and Mega D19 crossed (TX must go to RX), or missing common GND, or Nano not powered |
| LEDs never change | The dashboard only sends LED commands while a stream is connected |
| GSR stuck at 0 or 1023 | Electrodes not touching skin, or the module's AO wired to the wrong analog pin |

---

## 15. Safety and exhibition rules

- The system estimates a research score. It is not a diagnostic medical
  device, and the firmware and dashboard both say so on screen.
- ECG: laptop on battery while electrodes are on a person, never on visitors
  without consent, never on anyone with a pacemaker or implanted cardiac
  device, never on broken skin.
- Glucose: no finger-prick and no 75 g glucose challenge on visitors. Use a
  normal snack, your own historical readings, or pre-recorded volunteer data.
- Body-worn circuits run from batteries or the laptop's own USB, never from a
  mains adapter.
- Any data collection from people needs consent plus teacher or clinician
  oversight and institutional approval first. The dashboard stores everything
  locally for exactly this reason.
- Clean the PPG window, strap and electrodes between people with isopropyl
  alcohol.

Label every cable and rail at the table, keep a printed copy of sections 2 to
4 in the project file, and rehearse the serial-monitor check in section 11 so
you can prove the data path live if a judge asks.
