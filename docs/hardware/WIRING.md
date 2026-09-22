# ENDO-TWIN NEXUS V8.7 — Wiring

## ESP8266 primary wearable — NodeMCU 1.0 / ESP-12E

| Module | ESP8266 connection |
|---|---|
| MAX30102 | SDA D1/GPIO5, SCL D2/GPIO4 |
| MPU6050 | SDA D1/GPIO5, SCL D2/GPIO4 |
| DS18B20 | DATA D6/GPIO12 + 4.7 kΩ pull-up to 3.3 V |
| GSR / EDA | analog output A0 |
| Status LED | D4/GPIO2 |

MAX30102 and MPU6050 share the I2C bus. Do not feed incompatible 5 V signals into ESP8266 GPIO. NodeMCU pin labels differ from raw GPIO numbers; D1=GPIO5, D2=GPIO4, D4=GPIO2 and D6=GPIO12. citeturn0search7

### ESP8266 network

On boot the active firmware starts:
- SSID: `ENDO-TWIN-ESP8266`
- password: `endotwin8266`
- TCP port: `7777`

Desktop can use USB serial. Android connects to the ESP8266 IP over TCP. The default SoftAP address is normally `192.168.4.1`; confirm the address from the ESP8266 serial log before relying on it.

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

## Canonical protocol

```
$CP2,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc
```

CRC is XOR of every payload character before the final comma, including `$`, represented as two hexadecimal digits. Unsupported extended channels remain explicit missing-data placeholders.

## Test

1. Flash the active ESP8266 or Mega firmware.
2. For desktop, connect USB and use Auto-detect USB.
3. For Android, join `ENDO-TWIN-ESP8266` and connect to TCP port 7777.
4. Confirm roughly 20 CP2 packets/s.
5. Confirm CRC validation.
6. Use Prototype Lab to inspect PPG, IMU, temperature and GSR.
