# WIRING - ENDO-TWIN V8.7

## ESP32 primary wearable

| Device | ESP32 connection |
|---|---|
| MAX30102 SDA | GPIO21 |
| MAX30102 SCL | GPIO22 |
| MPU6050 SDA | GPIO21 |
| MPU6050 SCL | GPIO22 |
| DS18B20 data | GPIO18 + 4.7k pull-up to 3.3V |
| GSR analog | GPIO34 (ADC1 input) |
| Status LED | GPIO2 (optional) |
| Ground | Common GND |

MAX30102 and MPU6050 are on the same I2C bus and must use compatible 3.3V logic. Check your breakout board before powering it; do not assume a 5V-only sensor input is safe.

## Arduino UNO bench

MAX30102/MPU6050: SDA=A4, SCL=A5. DS18B20: D2 with 4.7k pull-up. GSR: A0. USB serial: 115200.

## Arduino Mega bench/hub

MAX30102/MPU6050: SDA=20, SCL=21. DS18B20: D2. GSR=A0. The existing Mega firmware can additionally host ECG, microphone, FSR, environmental sensors, OLED and buttons.

## ESP32 BLE contract

Service UUID: `7f300001-6c12-4f70-9e6b-8e9f7b8b1001`\nNotify UUID: `7f300002-6c12-4f70-9e6b-8e9f7b8b1001`\nCommand UUID: `7f300003-6c12-4f70-9e6b-8e9f7b8b1001`

The data characteristic sends one complete $CP2 line per notification. USB serial uses the same line format.

## Testing

1. Flash ESP32 and open serial at 115200.
2. Confirm device advertises as `ENDO-TWIN-ESP32`.
3. Send `WHOAMI` and check the identity response.
4. With no finger on MAX30102, the packet should carry the PPG-absent status bit rather than fake a signal.
5. Place a finger gently on MAX30102 and observe IR/RED values.
6. Move the IMU and observe acceleration/gyro fields.
7. Touch/warm the DS18B20 and observe temperature changes.
8. Verify GSR changes only when its sensor is correctly wired.
9. Validate the resulting lines with the existing Python `PacketParser` tests before enabling any research-model pipeline.

## Safety

Never place an unverified powered prototype on a person. Use insulated wiring, current-limited battery power, and no direct mains connection.
