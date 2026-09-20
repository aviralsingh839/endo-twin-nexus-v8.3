# WIRING - ENDO-TWIN V8.3+

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED - Preserved V8.1

## Nano Pod Wiring

- MAX30102 PPG: I2C SDA A4 SCL A5 3.3V GND
- MPU6050 IMU: I2C SDA A4 SCL A5 3.3V GND (shared I2C)
- DS18B20 Temp: OneWire D2 3.3V GND 4.7k pullup
- GSR: Analog A0 3.3V GND
- Serial: USB Serial 115200 baud $CP2 protocol

## Mega Hub Wiring

- Arduino Mega aggregation
- Serial to Nano Pod
- USB to PC

## Protocol

- $CP2 packets: qr_encoder.py packet_parser.py
- Format: $CP2,hr,spo2,ax,ay,az,gx,gy,gz,temp,gsr*checksum
- Example: $CP2,72,98,0.1,0.2,0.9,0.01,0.02,0.03,32.5,512*AB
- Validation: Checksum, range checks, missing handling

## Safety

- 3.3V sensors not 5V
- I2C shared bus MAX30102 + MPU6050 different addresses
- OneWire DS18B20 D2 with pullup
- Analog GSR A0
- Gracefully handle sensor unavailable/disconnected/noisy/missing/invalid/serial failure/partial
- Never fabricate data when sensor unavailable show Sensor unavailable

## Demo Mode

- Entire workflow without physical sensors DEMO/SIMULATED DATA labeled
- demo/demo_flow.py + demo/full_showcase.py 17 steps integrated ecosystem
- Synthetic 10 subjects 30 days 6 scenarios 60 days wrist_ppg SYNTHETIC clearly labelled
