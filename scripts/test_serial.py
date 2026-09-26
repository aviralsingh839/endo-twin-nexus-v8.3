#!/usr/bin/env python3
"""
Test serial $CP2 packets directly, bypassing dashboard.
Usage: python3 scripts/test_serial.py /dev/ttyACM0
"""
import sys, time
import serial
from src.serial_io.packet_parser import PacketParser

port = sys.argv[1] if len(sys.argv)>1 else "/dev/ttyACM0"
baud = 115200
print(f"Opening {port} @ {baud}...")
try:
    ser = serial.Serial(port, baud, timeout=1)
except Exception as e:
    print(f"Failed to open {port}: {e}")
    print("Check: ls /dev/ttyACM* ; sudo chmod 666 /dev/ttyACM0 ; dmesg | tail")
    sys.exit(1)

time.sleep(2) # wait for ESP32 reset
parser = PacketParser(require_crc=True)
count=0
crc_err=0
print("Waiting for $CP2 packets... (Ctrl+C to stop)")
print("If nothing appears in 5 sec, firmware not sending. Check USB CDC On Boot Enabled and flash V8.4.")
start=time.time()
while True:
    try:
        line = ser.readline().decode('ascii', errors='ignore').strip()
        if not line:
            if time.time()-start > 6 and count==0:
                print("[WARN] No data for 6 sec - ESP32 silent. Check firmware flash, USB CDC On Boot, cable.")
                start=time.time()
            continue
        print(f"RAW: {line}")
        if line.startswith("$CP2,"):
            try:
                sample = parser.parse(line)
                count+=1
                print(f"  -> OK: pulse={sample.ir} skin={sample.temp_c:.2f} room={sample.room_temp_c} lux={sample.lux} status={sample.status}")
            except Exception as e:
                crc_err+=1
                print(f"  -> PARSE ERR: {e}")
        elif line.startswith("$STAT") or line.startswith("$ACK") or "ENDO-TWIN" in line or "I2C" in line:
            print(f"  -> INFO: {line}")
    except KeyboardInterrupt:
        print(f"\nDone. Packets OK: {count}, CRC errors: {crc_err}")
        break
    except Exception as e:
        print(f"Read error: {e}")
        time.sleep(0.5)
