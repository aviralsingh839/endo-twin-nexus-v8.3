# ENDO-TWIN V8.4 Wearable Hardware Analysis - Shoulder + Forearm Mount

## Overview
User-specified final hardware:
- **ESP32-S3** main controller
- **BME280** (room temp + humidity + pressure) - shoulder mount
- **MPU6050 / MPU2060** (accel + gyro) - shoulder mount (MPU2060 is same family, driver compatible)
- **BH1750** (ambient light lux) - shoulder mount
- **Analog Pulse Sensor** (generic 3-pin pulse module, S signal) - inner forearm mount
- **DS18B20** (skin temperature) - inner forearm mount
- Optional **GSR** (galvanic skin response)

## Wiring Map (User Confirmed)
```
All I2C devices share bus:
  SDA -> GPIO8
  SCL -> GPIO9
  VCC -> 3V3
  GND -> GND

Devices on I2C bus:
  - MPU6050/2060 ADDR 0x68 (or 0x69 if AD0 high)
  - BME280 ADDR 0x76 (default) / 0x77 alternate
  - BH1750 ADDR 0x23 (default) / 0x5C alternate

Forearm sensors:
  - Analog Pulse Sensor:
      S (signal) -> GPIO40 (ADC1_CH0 on ESP32-S3, 12-bit)
      VCC -> 3V3 (check module rating, most support 3.3-5V)
      GND -> GND
  - DS18B20:
      DATA -> GPIO6 with 4.7k pull-up to 3V3
      VCC -> 3V3
      GND -> GND

Optional:
  - GSR -> GPIO5 (ADC)
  - Status LED -> GPIO2
```

## Mounting Rationale

### Shoulder Mount (Environmental + Motion Context)
- **MPU6050/2060**: Shoulder is more stable than wrist, less high-frequency motion artifact, good for posture, activity, step detection, circadian movement. Bias calibration on startup (200 samples).
- **BME280**: Measures ambient environment (room temperature, humidity, pressure). Shoulder placement avoids direct skin heating, gives true room context. Important for chrono-metabolic analysis (environment influences physiology).
- **BH1750**: Ambient light lux at shoulder approximates eye-level exposure, useful for circadian disruption analysis (light regularity). Forearm would be shadowed by body.

### Inner Forearm Mount (Vascular + Thermal Window)
- **Analog Pulse Sensor**: Inner forearm has superficial vasculature, less tendon interference than wrist, good signal when light pressure applied. Requires consistent contact, avoid over-tightening.
- **DS18B20**: Skin temperature at inner forearm correlates with peripheral perfusion, close to pulse sensor for multimodal fusion (HR + skin temp + GSR).

## Firmware V8.4 Architecture

### Libraries
- `Wire` - I2C with 400kHz fast mode, SDA=8 SCL=9
- `Adafruit_MPU6050` + `Adafruit_Sensor` - motion
- `Adafruit_BME280` - env temp/hum/press (forced mode, auto-detect 0x76/0x77)
- `BH1750` - lux (continuous high-res mode, auto-detect 0x23/0x5C)
- `OneWire` + `DallasTemperature` - DS18B20 non-blocking
- `BLEDevice` - dual output BLE + Serial

### Timing (Smooth Dashboard)
- Pulse read: 20ms (50Hz) -> raw ADC 0..4095
- IMU read: 20ms (50Hz) -> exponential smoothing alpha=0.35 for dashboard smoothness
- GSR read: 100ms (10Hz)
- DS18B20 read: 1000ms (1Hz) non-blocking (request + read)
- BME280+BH1750 read: 1000ms (1Hz)
- Packet publish: 50ms (20Hz) -> smooth 20fps live dashboard

### Packet Format $CP2 (Compatible)
```
$CP2,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc
```
- ms: millis()
- ir: pulseRaw (0..4095) - analog pulse waveform
- red: -1 (no optical channel)
- ax,ay,az: g (bias-corrected, smoothed)
- gx,gy,gz: deg/s (bias-corrected, smoothed)
- temp0: DS18B20 skin temp C (forearm) or nan
- temp1: nan (reserved)
- gsr: raw ADC
- mic/ecg/fsr: -1/0 placeholders
- lux: BH1750 lux
- roomT: BME280 temp C
- hum: BME280 humidity %
- press: BME280 pressure hPa
- buttons: 0
- status: bitmask
- crc: XOR of payload before last comma

### Status Bits (V8.4)
- 0: PPG/pulse absent (pulseRaw<20)
- 1: PPG saturated (pulseRaw>4075)
- 2: MPU6050/2060 error
- 3: DS18B20 error
- 4: GSR saturated
- 5: I2C bus error
- 6: Low signal quality (multiple sensors missing)
- 7: ECG off (unused)
- 8: BME280 error
- 9: OLED error (unused)
- 10: MIC low (unused)
- 11: FSR artifact (unused)
- 12: ANALOG_PULSE active (always 1)
- 13: ANALOG_PULSE invalid ADC
- 14: BH1750 error
- 15: Reserved

### Error Handling
- I2C bus: try both addresses for each sensor, mark error bit if not found
- DS18B20: non-blocking, check -40..85C range
- BME280: check nan and valid ranges
- BH1750: check 0..100k lux
- Pulse: check ADC range 0..4095, mark invalid if <=5 or >=4090
- IMU: bias calibration on startup, exponential smoothing for smoothness
- BLE: auto-advertise on disconnect, dual output ensures desktop always gets data via Serial even if BLE fails

### Commands via Serial/BLE
- PING -> $ACK,PONG
- WHOAMI -> ENDO-TWIN-ESP32-S3-SHOULDER-FOREARM-V8.4
- STATUS -> $STAT,MPU:x BME:x BH:x DS18:x PULSE:x GSR:x ST:0x...
- CALIB -> re-calibrate IMU bias
- I2CSCAN -> scan I2C bus

## Desktop Software V8.4

### Packet Parser
- Supports $CP2 25 fields with CRC XOR
- Decodes analog pulse: ir field = ADC waveform, red=-1
- Decodes env: lux, roomT, hum, press
- Decodes status flags + hardware health dict for live dashboard
- Functions:
  - `decode_status_flags(status)` -> list of human-readable flags
  - `decode_hardware_health(status)` -> dict of sensor OK booleans

### Quality Control
- Thresholds: HR 35-210, skin temp 20-42C, room temp -20..80C, hum 0..100%, press 300..1100hPa, lux 0..120k, pulse ADC 0..4095, accel max 8g
- Checks: missing, impossible, flatline, noise (z-score), stale
- Per-channel quality 0..1, overall quality mean of present sensors

### Feature Extraction
- PPG: analog pulse waveform -> HR, HRV (RMSSD, SDNN, pNN50), pulse amplitude, quality (motion-aware)
- IMU: motion_index, activity_level, low_activity_risk
- GSR: tonic, phasic per min
- Temp: skin_temp, temp_slope, stability
- Env: room_temp, humidity, pressure, lux stored in _env_history for trends
- Sleep: heuristic based on time + motion + HR
- Stress: HRV + HR based
- Baseline: learns personal normal, z-scores

### Live Dashboard Smooth (V8.4 New)
- **Timers**:
  - feature_timer 80ms (12.5Hz) -> feature extraction
  - smooth_plot_timer 50ms (20fps) -> ring buffer plot refresh
  - risk_timer 1500ms -> disease modules
  - stats_timer 500ms -> packet rate, CRC errors

- **Ring Buffers** (deque):
  - pulse: 2000 samples (40s @50Hz)
  - imu: 1000 samples (20s @50Hz)
  - skin_temp: 500 samples (500s @1Hz)
  - env: 500 samples (500s @1Hz)

- **SmoothLivePlot Widget**:
  - PyQtGraph, anti-aliased, glow pen
  - Downsamples to max 800 points for performance
  - X = seconds ago (negative), Y = value
  - 6 plots: pulse waveform (8s), accel magnitude (10s), gyro magnitude (10s), skin temp (30s), room temp (60s), lux (60s)

- **HardwareStatusCard**:
  - Shows each sensor OK/FAIL with color (green/red)
  - Wiring reminder: SDA8 SCL9 VCC3V3 GND GND Pulse40 DS18-6
  - Tooltip with detailed flags

- **EnvPanel**:
  - Room temp, humidity, pressure, lux, skin temp, pulse raw
  - Updates from live SensorSample

- **LiveStatsPanel**:
  - Rate Hz, CRC errors, latency ms, packet count, mount info

- **Vital Cards** (12):
  - HR (Pulse GPIO40), HRV, Skin Temp DS18 Forearm, Room Temp BME280 Shoulder, Humidity, Pressure, Lux, Activity MPU6050, GSR, Stress, Sleep, Signal Quality
  - Smooth value updates, color state

- **Preserved Logic**:
  - Baseline tab: capture, details, comparison
  - Trends tab: HR, HRV trends + longitudinal text
  - Health Signals: PCOS, Sleep, Cardiometabolic, Autonomic + future modules
  - Data Quality: sensor quality metadata + gauge
  - Clinical Inputs: age, BMI, BP, glucose, cycle
  - Ultrasound, Explanation, Report, Validation

## Analysis: Previous UI vs V8.4

### Previous UI (V8.3)
- Header: brand + search + port + connect + demo + stop + Wi-Fi + scenario + clock
- Sidebar: Overview, Baseline, Trends, Health Signals, Data Quality, Clinical Inputs, Ultrasound, Explanation, Report, Validation
- Overview: risk gauge + status box + vital cards (9) + shared features + health signals summary
- Plots: only trend plots (HR, HRV) at 1Hz, not smooth
- No env data, no hardware health panel, no live waveform
- Demo stream: optical PPG (MAX30102) with IR+RED, not analog

### V8.4 Improvements (Revert + Smooth)
- **Reverted**: kept previous UI shell (header, sidebar, tabs, baseline/trends/health signals logic) - no rewrite, just enhanced
- **Smooth**: added 20fps ring-buffer plots, 50ms timer, exponential smoothing in firmware, downsampling for performance
- **Hardware**: added BME280 + BH1750 support, updated wiring to SDA8 SCL9 Pulse40 DS18-6 as user specified
- **Mounting**: documented shoulder vs forearm rationale
- **Live**: hardware health card, env panel, live stats (rate, CRC, latency)
- **Vitals**: expanded from 9 to 12 cards including room temp, humidity, pressure, lux
- **Demo**: new 50Hz analog pulse simulation (base 1850 + sine + dicrotic notch + noise), env slow drift, motion phases
- **Firmware**: 20Hz packet, 400kHz I2C, auto-detect addresses, non-blocking DS18B20, bias calibration, status bits for each sensor

## Testing Checklist

### Firmware
- [ ] I2C scan finds MPU6050 0x68/0x69, BME280 0x76/0x77, BH1750 0x23/0x5C
- [ ] Pulse raw varies 1500-2200 with finger, stable when no finger
- [ ] DS18B20 reads 32-34C on forearm, nan if disconnected
- [ ] BME280 reads room temp ~25C, hum 40-60%, press 1000-1020hPa
- [ ] BH1750 reads 1-1000 lux depending on light
- [ ] Packet $CP2 at 20Hz, CRC valid, status bits correct
- [ ] BLE advertises ENDO-TWIN-S3, notifies packets
- [ ] Commands PING, WHOAMI, STATUS, CALIB, I2CSCAN work

### Desktop
- [ ] Connect serial /dev/ttyACM0 115200 -> live dashboard smooth
- [ ] Demo V8.4 -> 50Hz smooth waveforms
- [ ] Hardware health shows OK for all sensors
- [ ] Env panel shows BME280+BH1750 live
- [ ] Vital cards update smoothly
- [ ] Pulse waveform plot 8s history smooth
- [ ] Packet rate ~20Hz, CRC errors 0
- [ ] Baseline capture works
- [ ] Trends, Health Signals, Data Quality tabs preserved

## Safety & Limitations
- Educational research prototype, NOT medical device
- Analog pulse sensor does NOT provide SpO2 - do not fabricate
- BME280/BH1750 environmental data is for context, not diagnosis
- All risk signals are research-only, require clinical validation
- No cloud upload, local-first, privacy-focused
- Disclaimer on every report

## Future Extensions
- Add second DS18B20 for room vs skin differential
- Add GSR for stress (already optional)
- Add BME280 altitude for activity context
- Add BH1750 light regularity for circadian
- Add MPU6050 step count, posture detection
- Add pulse sensor HRV validation against ECG

## Files Changed V8.4
- `hardware/esp32/endo_twin_wearable/endo_twin_wearable.ino` - full rewrite for SDA8 SCL9 Pulse40 DS18-6 + BME280+BH1750+MPU6050
- `src/serial_io/packet_parser.py` - status bits for BME280/BH1750, hardware health
- `src/utils/demo_stream.py` - 50Hz analog pulse + env simulation
- `src/core/quality_control.py` - thresholds for hum/press/lux
- `src/core/feature_extraction.py` - env channels + quality
- `src/ui/main_window.py` - smooth live dashboard 20fps, hardware status, env panel, 12 vital cards, 6 live plots, preserved previous logic

## Wiring Diagram (Text)

```
ESP32-S3 DevKit
+-------------------+
| 3V3  ------------+----> BME280 VCC, MPU6050 VCC, BH1750 VCC, Pulse VCC, DS18B20 VCC, GSR VCC
| GND  ------------+----> All GND
| GPIO8 (SDA) -----+----> BME280 SDA, MPU6050 SDA, BH1750 SDA
| GPIO9 (SCL) -----+----> BME280 SCL, MPU6050 SCL, BH1750 SCL
| GPIO40 (ADC) ----+----> Pulse Sensor S
| GPIO6  ---------+-----> DS18B20 DATA (4.7k pull-up to 3V3)
| GPIO5 (ADC) ----+----> GSR (optional)
| GPIO2 ----------+----> Status LED
+-------------------+

Shoulder strap:
  [MPU6050 breakout] + [BME280 breakout] + [BH1750 breakout] on shared I2C bus
  Mount with soft strap, sensor windows exposed

Forearm band:
  [Pulse Sensor] + [DS18B20] on inner forearm
  Pulse: light pressure, not over tendon
  DS18B20: skin contact with medical tape, insulated from air
```

## References
- MPU6050 datasheet: accel +-4g, gyro +-500dps, DLPF 21Hz
- BME280 datasheet: temp +-1C, hum +-3%, press +-1hPa
- BH1750 datasheet: lux 1-65535, high-res mode 1 lux
- DS18B20 datasheet: 12-bit 0.0625C, -55..125C
- Analog Pulse Sensor: 3.3-5V, ADC output 0..VCC, requires amplification/filtering in software
- ESP32-S3: ADC1 12-bit, attenuation 11dB for 0..3.3V, GPIO40 is ADC1_CH0
