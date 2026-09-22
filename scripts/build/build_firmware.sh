#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")/../.." && pwd)"
command -v arduino-cli >/dev/null || { echo "ERROR: arduino-cli is required."; exit 1; }

arduino-cli core update-index
arduino-cli core install arduino:avr
arduino-cli core install esp32:esp32

for lib in   "SparkFun MAX3010x Pulse and Proximity Sensor Library"   "Adafruit MPU6050"   "Adafruit Unified Sensor"   "BH1750"   "Adafruit BME280 Library"   "Adafruit GFX Library"   "Adafruit SSD1306"; do
  arduino-cli lib install "$lib"
done

OUT="$ROOT/DIST/firmware-v8.7"
mkdir -p "$OUT/mega" "$OUT/esp32s3"

arduino-cli compile --fqbn esp32:esp32:esp32s3 --export-binaries   --output-dir "$OUT/esp32s3"   "$ROOT/hardware/esp32s3/endo_twin_wearable"

arduino-cli compile --fqbn arduino:avr:mega --export-binaries   --output-dir "$OUT/mega"   "$ROOT/hardware/arduino/endo_twin_mega_lab"

echo "Firmware build complete:"
echo "  ESP32-S3 wearable: $OUT/esp32s3"
echo "  Arduino Mega lab: $OUT/mega"
