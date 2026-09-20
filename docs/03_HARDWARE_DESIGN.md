# 03 - Hardware Design - V8.3+

## Wearable Pod (Nano)
- MCU: Arduino Nano
- Sensors: MAX30102 PPG (HR, SpO2, pulse amplitude), MPU6050 (ax,ay,az,gx,gy,gz, motion index), DS18B20 (skin temp), GSR (raw, tonic, phasic)
- Sampling: 20Hz
- Protocol: $CP2 packet, CRC XOR, fields ir, red, hr, spo2, gsr, ax,ay,az, etc.
- Power: LiPo + charging
- Wiring: See WEARABLE_POD_BUILD.md, HARDWARE_BUILD_GUIDE.md
- Firmware: Arduino sketch, 20Hz loop, $CP2 generation

## Lab Hub (Mega)
- MCU: Arduino Mega 2560
- Sensors: ECG (AD8232), mic (MAX4466), FSR, BME280 (room temp/humidity/pressure), OLED, relay mode
- Purpose: Expanded lab validation, not required for patient app
- See MEGA_HUB_BUILD.md

## Sensor Specifications
- MAX30102: PPG IR+RED, HR bpm, SpO2 %, pulse amplitude, quality - established
- MPU6050: accelerometer + gyroscope, motion index, activity level - established
- DS18B20: skin temp C, room temp C, temp slope - established
- GSR: galvanic skin response, tonic/phasic - established

## Quality Considerations
- PPG quality affected by motion, pressure, skin tone, ambient light
- HRV from PPG less accurate than ECG
- Skin temp not core temp, affected by environment
- GSR affected by sweat, electrode contact

## Failure Handling
- Sensor unavailable: graceful handling, notify, demo mode
- Disconnected: reconnection logic, SerialManager
- Noisy: artifact detection, quality control
- Missing: interpolation not fabrication
- Invalid: validation, discard invalid
- Serial failure: retry, fallback

## Why This Hardware?
Low cost, accessible for Class 11, wrist-worn PPG research common, open-source libraries, reproducible.

## Future Research (Not Implemented Without Dataset)
Cancer, Alzheimer, infectious, kidney, liver, thyroid - marked as future research, no unsupported modules.
