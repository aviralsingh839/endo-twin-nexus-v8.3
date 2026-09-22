# ENDO-TWIN NEXUS V8.7 — Wiring

## ESP32 primary wearable

| Module | ESP32 connection |
|---|---|
| MAX30102 | SDA GPIO21, SCL GPIO22 |
| MPU6050 | SDA GPIO21, SCL GPIO22 |
| DS18B20 | DATA GPIO18 + 4.7 kΩ pull-up to 3.3 V |
| GSR / EDA | analog output GPIO34 |
| Status LED | GPIO2 through appropriate resistor |

MAX30102 and MPU6050 share the I2C bus. Do not feed a 5 V signal into ESP32 GPIO.

### Wearable power

Use a suitable regulated, battery-powered ESP32 supply for body-worn operation. Keep the body-worn circuit isolated from mains. Do not connect unsafe chargers, exposed mains wiring or incompatible sensor outputs to the body-worn assembly.

## Arduino Mega bench/lab controller

| Module | Mega connection |
|---|---|
| MAX30102 | SDA D20, SCL D21 |
| MPU6050 | SDA D20, SCL D21 |
| DS18B20 | DATA D2 + 4.7 kΩ pull-up |
| GSR | A0 |
| MAX4466 | A1 optional |
| AD8232 | OUT A2; LO+ D11; LO− D12 optional |
| FSR | A3 optional |
| BH1750/BME280/OLED | I2C D20/D21 |
| Buttons | D3/D4/D5 to GND, INPUT_PULLUP |
| LEDs | D8/D9/D10 through 220 Ω |
| Buzzer | D6 |

The Mega is intended for bench testing and expanded sensor experiments. It connects directly to the PC by USB and does not require Nano or ESP8266 hardware.

## Canonical protocol

```
$CP2,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc
```

CRC is XOR of every payload character before the final comma, including `$`, represented as two hexadecimal digits.

ESP32 fills unsupported extended channels with explicit missing-data placeholders (`-1` or `nan`). It never fabricates sensor measurements.

## USB test

1. Flash the appropriate active firmware.
2. Connect ESP32 or Mega by USB.
3. Select the discovered serial device in LIVE SENSOR MODE.
4. Confirm approximately 20 CP2 packets/s.
5. Confirm CRC passes.
6. Use Prototype Lab to inspect PPG, IMU, temperature, GSR and optional channels.
