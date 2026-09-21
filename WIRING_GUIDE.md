# ENDO-TWIN Wiring Guide

## Important variant rule
Exact pin labels vary between breakout boards. The repository therefore records the interface class first and requires the exact board variant to be confirmed before a pin-by-pin assembly is frozen.

### MAX30102 — I2C
- VIN/VCC → verified supply compatible with the exact breakout
- GND → controller GND
- SDA → controller I2C SDA
- SCL → controller I2C SCL
- INT → optional GPIO if the firmware uses interrupt-driven acquisition

### MPU6050 — I2C
- VCC → verified supply compatible with the exact breakout
- GND → controller GND
- SDA → controller I2C SDA
- SCL → controller I2C SCL
- INT → optional GPIO if interrupt use is implemented

### DS18B20 — 1-Wire
- VDD → verified supply
- GND → controller GND
- DATA → chosen digital GPIO
- Pull-up resistor → DATA to VDD at the value required by the probe/bus implementation

### GSR
- VCC → module-rated supply
- GND → controller GND
- ANALOG OUT → controller ADC input

### ECG
- VCC/GND/OUTPUT → exactly according to the identified ECG breakout module documentation.
- Do not substitute a guessed pinout.

## I2C note
MAX30102 and MPU6050 can normally share one I2C bus when addresses do not conflict, but the actual addresses and voltage compatibility must be checked for the exact breakout boards.
