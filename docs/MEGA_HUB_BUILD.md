# MEGA HUB BUILD - V8.3

## Expanded Laboratory / Base Station

Preserved from V8.1 as expanded experimental sensors hub in V8.3.

### Components

- Arduino Mega 2560
- Pod sensors: generic analog Pulse Sensor, MPU6050, DS18B20, GSR
- Plus:
  - ECG AD8232 (A1, LO- D30, LO+ D31)
  - Microphone MAX4466 (A2, RMS + pitch)
  - FSR pressure sensor (A3, finger pressure correction)
  - Light sensor BH1750 I2C or LDR A4
  - BME280 environment (I2C SDA 20 SCL 21, room temp, humidity, pressure)
  - OLED 128x64 I2C 0x3C
  - LEDs, buzzer, buttons D22-33
- Power: 5V 2A bench supply

### Wiring

See legacy `chrono_pcos_project V8/docs/ARDUINO_WIRING_GUIDE.md` for full details - preserved.

### Firmware

`hardware/arduino/chrono_pcos_mega_firmware/chrono_pcos_mega_firmware.ino`

- Same packet format $CP2 but with extra channels filled
- Periodic ECG checkpoints
- OLED shows live vitals
- Relay mode: if RELAY_POD_SERIAL1=1, forwards every pod line from Serial1 to USB, so dashboard connects to Mega only

### Testing

- Same as pod plus ECG: connect leads, check ecg_raw, ecg_quality >0.55 uses ECG for HR/HRV instead of PPG
- FSR: press, check fsr_pressure_index, extreme pressure degrades PPG quality
- Mic: check mic_rms, mic_pitch, voice_vasc_score
- BME280: room temp, humidity, pressure

### V8.3 Architecture

```
WEARABLE POD → physiological data (primary)
MEGA HUB → expanded experimental sensors (lab)
PC → CHRONO-TWIN NEXUS ENGINE
```

- Software gracefully operates with missing sensors
- Mega hub not required for core functionality
- Pod alone sufficient for all 4 disease modules (PCOS, Sleep, Cardiometabolic, Autonomic)

### When to Use Mega Hub

- Lab experiments with ECG validation
- FSR pressure correction study
- Environment context (room temp, humidity)
- OLED standalone display
- Relay for pod when PC far

### Preservation

V8.1 Mega hub still works in V8.3, no breaking changes to packet protocol.
