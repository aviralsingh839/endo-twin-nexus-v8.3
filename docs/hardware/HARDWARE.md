# HARDWARE - ENDO-TWIN V8.3+

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED - Preserved V8.1

## Preserved Hardware

- Nano pod: Arduino Nano wearable pod MAX30102 PPG IR+RED HR SpO2 pulse amplitude 20Hz $CP2 MPU6050 motion ax ay az gx gy gz motion index activity level DS18B20 skin temp room temp temp slope GSR raw tonic phasic
- Mega hub: Arduino Mega hub aggregation
- Sensors: MAX30102 PPG, MPU6050 IMU, DS18B20 temperature, GSR
- Communication: Serial $CP2 protocol packet_parser.py qr_encoder.py ecg.py etc.

## Architecture

- hardware/arduino/ nano_pod/ mega_hub/
- src/serial_io/ serial_reader.py packet_parser.py preserved
- src/signal_processing/ ppg.py ecg.py gsr.py hrv.py imu.py spo2.py temperature.py filters.py preserved
- Gracefully handle sensor unavailable/disconnected/noisy/missing/invalid/serial failure/partial
- Offline-first core offline demo local no cloud
- Demo mode entire workflow without physical sensors DEMO/SIMULATED DATA labeled

## Data Flow

```
Nano Pod Sensors
 ↓ $CP2 packets
Serial Reader
 ↓ packet_parser
Validation
 ↓
Signal Processing filtering artifact quality HR HRV motion temp GSR
 ↓
Feature Extraction HR 72 bpm MEASURED quality 0.91 HRV RMSSD 48 ms DERIVED quality 0.85 etc
 ↓
Baseline Longitudinal Fusion Disease Model Prediction Explanation Uncertainty Provenance Report/UI
```

## Benchmark References

- PPGbetter: Real-time PPG acquisition Android lifecycle
- research-project: Python/Android division filtering HRV
- E2E-PPG: End-to-end SQA reconstruction
- Colepp: Wearable acquisition existing ecosystems Wear OS hardware strategy maximize existing real sensor data
- OpenRing: BLE reconnection passive sampling local-first sensor abstraction
- Gadgetbridge: BENCHMARK ONLY GPL architectural study vendor independence

## Performance

- Import core 267.9 ms fast
- Deterministic inference 0.3 ms extremely fast
- Real inference 993 ms moderate
- Dashboard 22 ms fast
- Ring buffers streaming lazy loading async model inference

## Safety

- Research prototype not medical device
- Gracefully handle sensor failures
- Never fabricate data when sensor unavailable
- Demo labeled never clinical
