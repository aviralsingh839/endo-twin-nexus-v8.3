# V8.4 Wiring - ESP32-S3 Shoulder + Forearm Wearable

## User Final Wiring (Confirmed)

### I2C Bus Shared - Shoulder Mount
```
ESP32-S3          -> All I2C Devices
GPIO8 (SDA)       -> BME280 SDA, MPU6050/2060 SDA, BH1750 SDA
GPIO9 (SCL)       -> BME280 SCL, MPU6050/2060 SCL, BH1750 SCL
3V3               -> BME280 VCC, MPU6050 VCC, BH1750 VCC
GND               -> BME280 GND, MPU6050 GND, BH1750 GND
```

**I2C Addresses (auto-detect):**
- MPU6050/2060: 0x68 (AD0 low) or 0x69 (AD0 high) - GY-521 board
- BME280: 0x76 (default) or 0x77 (SDO high)
- BH1750: 0x23 (default) or 0x5C (ADDR high)

### Forearm Mount - Pulse + Skin Temp
```
Analog Pulse Sensor (generic 3-pin):
  S (signal) -> GPIO40 (ADC1_CH0, 12-bit, 0..4095)
  VCC        -> 3V3 (check module: most 3.3-5V tolerant)
  GND        -> GND

DS18B20 (TO-92 or waterproof):
  DATA       -> GPIO6 with 4.7kΩ pull-up to 3V3
  VCC        -> 3V3
  GND        -> GND

Optional GSR:
  Signal     -> GPIO5 (ADC)
  VCC        -> 3V3
  GND        -> GND
```

### Power & Status
```
Status LED -> GPIO2 (onboard LED many S3 boards)
```

## Physical Mounting

### Shoulder (Left or Right, user preference)
- Use soft elastic strap or sewn pocket
- Orientation: MPU6050 arrow forward, BME280/BH1750 window outward
- Keep BME280 away from direct skin heat (air gap)
- BH1750 lens exposed to ambient light
- I2C wires: short (<15cm), twisted SDA+SCL, 3V3+GND twisted

### Forearm (Inner Forearm, non-dominant)
- Pulse sensor: light pressure, not over tendon, inner wrist/forearm vascular area
- DS18B20: skin contact with medical tape, small foam insulation over top to reduce air influence
- Both on same elastic band, 2-3cm apart
- Wires routed along arm to shoulder unit (flexible silicone wire)

## ESP32-S3 Specific Notes
- GPIO40 is ADC1_CH0, input only? On S3 it's ADC capable, check board variant. If not, use GPIO1-10 ADC1.
- ADC attenuation: 11dB for 0..3.3V range (pulse sensor outputs ~0.3-2.5V)
- AnalogReadResolution 12-bit (0..4095)
- I2C: GPIO8/9 are default I2C on many S3 DevKitC, but can be any. User specified 8/9.
- OneWire: GPIO6 needs 4.7k pull-up, use parasite power? No, use external VCC.
- BLE: ESP32-S3 has BLE 5.0, name ENDO-TWIN-S3

## Bill of Materials V8.4
- 1x ESP32-S3 DevKitC (N8R8 or similar)
- 1x MPU6050 or MPU2060 breakout (GY-521)
- 1x BME280 breakout (3.3V, I2C)
- 1x BH1750 breakout (GY-302)
- 1x Analog Pulse Sensor (PulseSensor.com generic or Keyes)
- 1x DS18B20 (waterproof or TO-92)
- 1x 4.7kΩ resistor (DS18B20 pull-up)
- Optional: GSR sensor (2 electrodes)
- Wires, elastic straps, medical tape

## Firmware Flash
- Board: ESP32S3 Dev Module
- USB CDC On Boot: Enabled
- Flash Mode: QIO, 80MHz
- Partition: Default 4MB with spiffs
- Upload Speed: 921600
- Libraries: Adafruit MPU6050, Adafruit BME280, BH1750, OneWire, DallasTemperature, BLE

## Testing
1. I2C scan: should find 3 devices (0x68, 0x76, 0x23)
2. Serial 115200: packets $CP2 at 20Hz
3. Pulse: 1500-2200 raw with finger, <50 without
4. DS18B20: 32-34C on skin
5. BME280: room temp 22-28C, hum 35-65%, press 1000-1020hPa
6. BH1750: 1-1000 lux

## Safety
- 3V3 only, no 5V to ESP32-S3 GPIOs
- Pulse sensor VCC: if module is 5V only, use level shifter or voltage divider for S
- DS18B20 VCC 3V3
- Educational prototype only, not medical device
