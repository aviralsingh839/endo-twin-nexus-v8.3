#!/usr/bin/env bash
# Builds the two bench firmware targets that the desktop/live path uses.
#
# The third active firmware, hardware/esp8266/endo_twin_sensor_pod, is not built
# here: it needs the esp8266:esp8266 core and the I2Cdevlib "MPU6050" library
# instead of "Adafruit MPU6050". Install those and add a compile line if you want
# it in the same run.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")/../.." && pwd)"
command -v arduino-cli >/dev/null || { echo "ERROR: arduino-cli is required."; exit 1; }

arduino-cli core update-index
arduino-cli core install arduino:avr
arduino-cli core install esp32:esp32

LIBS=(
  "SparkFun MAX3010x Pulse and Proximity Sensor Library"
  "Adafruit MPU6050"
  "Adafruit Unified Sensor"
  "OneWire"                 # DS18B20 skin-temperature probe
  "DallasTemperature"       # DS18B20 skin-temperature probe
  "BH1750"                  # ambient light
  "Adafruit BME280 Library" # room temperature / humidity / pressure
  "Adafruit GFX Library"    # Mega lab OLED
  "Adafruit SSD1306"        # Mega lab OLED
)
for lib in "${LIBS[@]}"; do
  arduino-cli lib install "$lib"
done

OUT="$ROOT/DIST/firmware-v8.7"
mkdir -p "$OUT/mega" "$OUT/esp32s3"

arduino-cli compile --fqbn esp32:esp32:esp32s3 --export-binaries --output-dir "$OUT/esp32s3" "$ROOT/hardware/esp32s3/endo_twin_wearable"

arduino-cli compile --fqbn arduino:avr:mega --export-binaries --output-dir "$OUT/mega" "$ROOT/hardware/arduino/endo_twin_mega_lab"

echo "Firmware build complete:"
echo "  ESP32-S3 wearable: $OUT/esp32s3"
echo "  Arduino Mega lab: $OUT/mega"
