# Sensor Testing Guide

## Individual test mode
The test harness should expose:
[ ] MAX30102
[ ] MPU6050
[ ] GSR
[ ] DS18B20
[ ] ECG
[ ] Serial communication
[ ] Database
[ ] Signal processing

## Acceptance behavior
A sensor test must say PASS, WARN or FAIL with evidence. A missing/disconnected sensor must produce an explicit unavailable state.

## Failure matrix
- disconnected → DEVICE_UNAVAILABLE
- loose wire → unstable/low-quality signal where detectable
- zero/flatline → FLATLINE
- noisy → LOW_SIGNAL_QUALITY
- motion → MOTION_ARTIFACT
- corrupt packet → PACKET_INVALID
- missing packet → DATA_GAP
- wrong sample rate → SAMPLE_RATE_MISMATCH
- serial drop → SERIAL_DISCONNECTED
- reconnect → SERIAL_RECONNECTED
- unavailable sensor → DEVICE_UNAVAILABLE
- invalid value → VALUE_INVALID

No failure mode may silently generate a plausible value.
