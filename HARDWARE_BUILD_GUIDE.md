# ENDO-TWIN Wearable Hardware Build Guide

## Prototype bill of materials

| Component | Qty | Role | Interface / notes |
|---|---:|---|---|
| Arduino controller | 1 | Sensor hub | USB serial to computer; exact board variant must be recorded |
| MAX30102 breakout | 1 | Optical PPG | I2C; verify breakout voltage/pin labeling |
| MPU6050 breakout | 1 | 6-axis motion | I2C; verify breakout voltage/pin labeling |
| DS18B20 probe | 1 | Temperature trend | 1-Wire; requires appropriate pull-up arrangement |
| GSR sensor/module | 1 | Electrodermal activity | Analog or module-specific output; verify variant |
| ECG module | 1 optional | ECG research channel | Module-specific interface and safety constraints |
| Breadboard | 1 | Prototype assembly | Prefer a new, reliable board |
| Dupont/jumper wires | assorted | Connections | Male/female sets as dictated by breakout headers |
| Resistors | assorted | Sensor-specific pull-ups | Value must follow exact module/datasheet configuration |
| USB cable | 1 | Power/data | Match controller connector |

## Assembly sequence
1. Record exact board/module part numbers.
2. Verify supply-voltage requirements from the module documentation.
3. Build and test the controller alone.
4. Add one sensor at a time.
5. Validate raw data before adding another sensor.
6. Label every wire and connector.
7. Add strain relief before wearable mounting.

## Placement
MAX30102: stable optical contact; avoid excessive pressure.
MPU6050: rigid orientation reference on the wearable.
DS18B20: placed according to the intended temperature experiment; do not call it core body temperature without validation.
GSR: electrodes placed consistently; skin contact and pressure must be documented.
ECG: only use a module and electrode arrangement whose electrical safety is understood.

## Troubleshooting
No sensor → power/interface check → bus scan where appropriate → connector check → module-specific test.
Noisy PPG → stabilize contact → reduce motion → inspect signal quality; do not silently smooth into a false measurement.
Missing packets → check cable/serial state → packet counters → reconnect → preserve missing intervals.
