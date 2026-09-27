# ENDO-TWIN NEXUS V9 — Desktop Wearable

## Primary wearable

ESP32-S3 + low-cost analog Pulse Sensor + GSR + MPU6050.

### Pin map

| Function | ESP32-S3 pin |
|---|---:|
| Analog Pulse Sensor output | GPIO4 |
| GSR analog output | GPIO34 |
| I²C SDA | GPIO21 |
| I²C SCL | GPIO22 |
| Status LED | GPIO2 |

I²C devices are optional:
- MPU6050 at 0x68/0x69
- BME280 at 0x76/0x77
- BH1750 at 0x23/0x5C

The analog Pulse Sensor is a single-channel PPG source. The workstation derives pulse rate and quality-gated pulse-variability features; it does not claim SpO₂ from this channel.

## Packet protocol

USB Serial and Wi-Fi TCP 7777 use the same CP3 frame:

`$CP3,ms,ppg_raw,gsr_raw,ax,ay,az,gx,gy,gz,roomT,hum,press,lux,status,crc`

CRC is the XOR of every character in the payload before the final comma.

## Raw-data calibration

The desktop performs a separate calibration layer so acquisition values remain auditable.

**Offset calibration**
- accelerometer X/Y bias
- accelerometer Z resting-gravity error
- gyroscope X/Y/Z zero offsets

**Baseline-relative calibration**
- analog PPG
- GSR

**Reference capture without silent unit changes**
- BME280 temperature / humidity / pressure
- BH1750 lux

The calibration page shows channel readiness, baseline/scale estimates and calibration status. A manual reset is available from the Patient Workspace.

This is engineering calibration, not traceable metrology or clinical calibration.

## Desktop workflow

1. Start the desktop workstation.
2. Choose DEMO, USB sensor mode, or ESP32 Wi-Fi mode.
3. Wear the pod with stable finger contact on the Pulse Sensor and GSR electrodes.
4. Keep the pod still for the first few seconds so IMU offsets can stabilize.
5. The workstation streams the calibrated analog waveform and updates signal quality.
6. Patient context and longitudinal data remain separate from the raw sensor layer.

## PCOS / PMOS complication context

The new **PCOS / PMOS Complication Context** workspace separates:
- measured/entered metabolic context
- blood-pressure context
- lipid-data gaps
- menstrual/endometrial context
- sleep/autonomic wearable context
- androgenic/dermatologic clinical-data gaps
- wellbeing/validated-screening data gaps

The page is intentionally a context/surveillance surface. It does not convert wearable readings into a diagnostic probability and does not replace clinical assessment.

## Architecture note

The workstation now avoids the previous duplicate-sample path: the Session owns streaming feature extraction, while the UI consumes its emitted sample/feature signals.

Android application code is not part of this wearable-focused implementation.
