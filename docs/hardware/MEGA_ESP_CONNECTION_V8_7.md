# ENDO-TWIN NEXUS V8.7 — Mega + ESP8266 wiring

## Recommended topology

PC --USB--> Mega 2560

Mega D18 / TX1 --[5V to 3.3V level shift]--> ESP8266 RX0 / GPIO3
Mega D19 / RX1 <----------------------------- ESP8266 TX0 / GPIO1
Mega GND ----------------------------------- ESP GND

ESP8266 --Wi-Fi TCP 7777--> Unified Workstation

The Mega is the sensor hub. The ESP8266 is only a network transport bridge. The Mega emits the same CP2 packet to USB Serial and Serial1, so the workstation can use either transport.

### Mega sensor pins

| Module | Mega connection |
|---|---|
| MAX30102 | I2C SDA D20, SCL D21 |
| MPU6050 | I2C SDA D20, SCL D21 |
| BME280/BH1750/OLED | I2C SDA D20, SCL D21 |
| DS18B20 | DATA D2 + 4.7 kΩ pull-up to the sensor supply |
| GSR/EDA | AO A0 |
| MAX4466 | AO A1 optional |
| AD8232 | OUT A2, LO+ D11, LO− D12 optional |
| FSR | AO A3 optional |
| Buttons | D3/D4/D5 to GND, INPUT_PULLUP |
| LEDs | D8/D9/D10 through 220 Ω |
| Buzzer | D6 |

### Safety-critical UART rule

The Mega is 5 V logic; ESP8266 UART is 3.3 V logic. Never wire Mega D18/TX1 directly to ESP RX0. Use a 5V-to-3.3V level shifter or suitable divider. ESP TX0 to Mega RX1 is normally a 3.3V-high signal into a 5V AVR input.

Do not power an ESP8266 module directly from the Mega 5V pin unless the specific ESP board explicitly provides its own regulated 5V input. Prefer the board's regulated supply and adequate current headroom.

UART0 is also the common ESP8266 programming UART. Disconnect the Mega TX/RX pair while flashing the ESP8266, then reconnect after programming.

## V8.7 performance changes

The Mega uses 400 kHz I2C, 10-bit non-blocking DS18B20 conversion, an incremental microphone sampler, and a fixed 20 Hz CP2 transport cadence. The PC recomputes features at 2 Hz rather than forcing the UI to redraw for every packet. The ESP bridge uses UART0 for data, UART1 TX-only for debug, TCP no-delay and immediate byte forwarding.

This is intended to reduce stalls and jitter; it does not make the sensor data clinically validated.
