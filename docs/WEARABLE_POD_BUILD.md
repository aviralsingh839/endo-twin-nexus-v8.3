# WEARABLE POD BUILD - V8.3

## Primary Wearable - Arduino Nano Pod

Preserved from V8.1, primary wearable implementation in V8.3.

### Components

- Arduino Nano (ATmega328P)
- MAX30102 PPG (I2C, SDA A4, SCL A5, 3.3V)
- MPU6050 IMU (I2C same bus, address 0x68, 5V)
- DS18B20 skin temperature (D2, OneWire, 4.7k pull-up)
- Optional GSR (A0)
- LEDs Green D8, Yellow D9, Red D10 via 220Ω
- Buzzer D6
- Power: 3.7V LiPo + TP4056 + boost, or USB charger
- Enclosure: small 3D printed pod, wrist strap

### Wiring

See HARDWARE_BUILD_GUIDE.md

### Firmware

`hardware/arduino/chrono_pcos_nano_pod/chrono_pcos_nano_pod.ino`

- Samples PPG 50 Hz, IMU 50 Hz, GSR 10 Hz, Temp 1 Hz
- Sends packet 20 Hz `$CP2` at 115200 baud
- Channels not present sent as placeholders (-1 analog, nan environment) so dashboard reads pod like Mega
- Two connection methods:
  1. Pod → PC: Nano USB straight to laptop, dashboard --port <nano port>
  2. Pod → Mega → PC: Nano D1 TX → Mega D19 RX1, common GND, power Nano from charger, Mega firmware RELAY_POD_SERIAL1=1, dashboard connects to Mega only

### Commands

Dashboard sends on same serial:
- LED,G / LED,Y / LED,R
- BEEP
- PING → $ACK,PONG,00

### Testing

- Serial Monitor 115200, 20 Hz $CP2 lines
- Finger on MAX30102: ir >5000
- Move: motion index
- Warm: temp

### V8.3 Integration

- Quality control: ir <5000 → quality 0, artifact low_amplitude, finger absent
- Feature extraction: PPG → HR, HRV, SpO2 educational, pulse amplitude
- Baseline: learns personal RHR, HRV, temp, GSR, activity
- Longitudinal: detects persistent changes
- Shared features: feeds all disease modules
- Missing sensors: gracefully handled, does not crash
