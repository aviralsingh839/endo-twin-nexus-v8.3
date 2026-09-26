# Troubleshooting: Live Dashboard Shows No Input (Rate 0.0 Hz)

Your screenshot shows:
- `Rate: 0.0 Hz`, `Packets: 0`, `Latency: ~28076 ms`, `Mode: LIVE SERIAL /dev/ttyACM0`
- Vital cards `--`, waveforms empty
- This means **no valid $CP2 packet received** via serial.

## Quick Fix Checklist

### 1. Test UI Without Hardware (should work immediately)
Click **Demo V8.4** button in header.
- Expected: Rate ~50Hz, pulse waveform, vitals, env data, 6 smooth plots.
- If Demo works, UI code is OK, problem is hardware/serial.
- If Demo also shows 0 Hz, reinstall: `pip install pyqtgraph numpy PySide6`

### 2. Check Port Exists and Permissions (Linux)
```bash
ls -l /dev/ttyACM* /dev/ttyUSB*
# Should show /dev/ttyACM0 or /dev/ttyUSB0
dmesg | tail -30
# Look for "cp210x" or "ch340" or "USB ACM device"

# Permission fix
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/ttyACM0
# Then logout/login or new terminal
```

### 3. Check Raw Serial Data (bypass dashboard)
```bash
# Install miniterm
python3 -m pip install pyserial

# Try cat
cat /dev/ttyACM0
# or
python3 -m serial.tools.miniterm /dev/ttyACM0 115200

# Expected output (20Hz):
# $CP2,12345,1850,-1,0.01,0.02,1.00,0.1,0.2,0.3,32.50,nan,450,0,0.00,0.0,-1,-1,180.5,25.3,48.2,1008.5,0,4096,41
# If you see nothing, firmware not flashed or ESP32-S3 not in CDC mode
```

### 4. Flash V8.4 Firmware (Critical)
Your ESP32-S3 must have V8.4 firmware with SDA=8 SCL=9 Pulse=40 DS18=6.

**Arduino IDE:**
- Board: ESP32S3 Dev Module
- USB CDC On Boot: Enabled
- Flash Mode: QIO 80MHz
- Partition: Default 4MB with spiffs
- Upload Speed: 921600
- Port: /dev/ttyACM0
- Libraries needed: Adafruit MPU6050, Adafruit BME280, BH1750, OneWire, DallasTemperature, ESP32 BLE
- Open `hardware/esp32/endo_twin_wearable/endo_twin_wearable.ino` and Upload

**Verify after flash, open Serial Monitor 115200:**
```
=== ENDO-TWIN S3 Wearable V8.4 ===
Wiring: SDA=8 SCL=9 Pulse=40 DS18=6 GSR=5
[I2C] scanning SDA=8 SCL=9 @100k...
  I2C 0x68 found
  I2C 0x76 found
  I2C 0x23 found
[MPU] OK at 0x68
[BME280] OK at 0x76
[BH1750] OK at 0x23
[DS18B20] 1 device(s) found
[SYS] ready - 20Hz packet @ 115200 baud
$CP2,...
```

If you see:
- `I2C WARNING: no devices found` -> Check SDA=8 SCL=9 wiring, VCC=3V3, GND, pull-ups (BME280/MPU/BH boards have pull-ups usually)
- `MPU not found` -> Check MPU VCC 3V3, GND, AD0=GND for 0x68, SDA=8 SCL=9
- `BME280 not found` -> Check BME280 wiring, 3V3, some boards need SDO=GND for 0x76
- `BH1750 not found` -> Check BH1750 wiring, lens not covered
- `DS18B20 not found` -> Check DATA=GPIO6 with 4.7k pull-up to 3V3

**Even if sensors fail, firmware still publishes $CP2 at 20Hz with nan for missing values and status bits set. So you should always see packets.**

### 5. Check Wiring Again (Your Final Map)
```
All I2C:
  SDA -> 8
  SCL -> 9
  VCC -> 3V3
  GND -> GND

Forearm:
  Pulse S -> 40
  DS18 DATA -> 6 + 4.7k to 3V3
```

Common mistakes:
- SDA/SCL swapped
- Using GPIO8/9 but board's default I2C is 21/22 - our firmware forces Wire.begin(8,9) so must wire to 8/9
- Pulse sensor VCC 5V module feeding 5V into GPIO40 (should be 3V3 module or divider)
- DS18B20 without pull-up -> no data
- ESP32-S3 GPIO40 not ADC capable on your variant -> try GPIO4 or GPIO5

### 6. Dashboard Debug Console (New in this fix)
After updating, overview tab has **Serial Debug** box at top:
- Shows `[STATE]` connected/reconnecting
- Shows `[ERR]` crc mismatch, parse errors
- If you see `reconnecting` every 6s -> serial silent, check firmware + cable
- If you see `crc mismatch` -> baud mismatch or corrupted packets, check 115200

### 7. Refresh Ports Button
Click **Refresh** then check dropdown:
- Should list `/dev/ttyACM0`, `/dev/ttyUSB0`, etc.
- Select correct one, then **Connect S3**

### 8. Try Different USB Cable / Port
- Some cables are power-only, no data
- Try USB2 port, not USB3 hub
- Press BOOT + RESET on ESP32-S3 to enter download mode, then flash

### 9. If Still No Data, Run This Test Script
```bash
.venv/bin/python - << 'PY'
import serial, time
port="/dev/ttyACM0"
ser=serial.Serial(port,115200,timeout=1)
time.sleep(2)
for _ in range(100):
    line=ser.readline().decode(errors='ignore').strip()
    if line:
        print(line)
PY
```

If this prints $CP2 lines, parser should work. If not, firmware issue.

### 10. Final: Use Demo Mode for Development
Until hardware is ready, use **Demo V8.4** button:
- Simulates shoulder: MPU6050 motion, BME280 25C/48%/1008hPa, BH1750 180 lux
- Simulates forearm: analog pulse 1850 ADC + sine wave, DS18B20 32.8C
- 50Hz smooth, tests all 12 vital cards + 6 waveforms + hardware health + env panel

## What Was Fixed in Code (This Update)
- Added Serial Debug console to overview
- Added packet stats reset on connect
- Added error/state logging to debug console
- Added I2C scan with timeout (was hanging if no devices)
- Added Wire.setTimeOut(50ms) to avoid hang
- Added auto-detect with retries for MPU/BME/BH
- Firmware now always publishes at 20Hz even if all sensors fail (nan + status bits)

Update locally:
```bash
git fetch origin
git checkout arena/01a0dc15-endo-twin-nexus-v8-3
git pull origin arena/01a0dc15-endo-twin-nexus-v8-3
```
