#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
PY="${PYTHON:-python3}"

echo "ENDO-TWIN V9 ready check"
echo "Root: $ROOT"
echo

files="hardware/esp32s3/endo_twin_wearable/endo_twin_wearable.ino
desktop/workstation_runtime.py
desktop/unified_workstation.py
desktop/patient_app/main.py
desktop/doctor_app/main_enhanced.py
src/serial_io/packet_parser.py
src/serial_io/arduino_reader.py
src/serial_io/network_reader.py
src/personal_twin/profile_store.py
src/personal_twin/adaptive_model.py
src/personal_twin/baseline_store.py
src/personal_twin/baseline_capture.py
src/personal_twin/self_learning_app.py"

while IFS= read -r f; do
  [ -n "$f" ] || continue
  test -f "$ROOT/$f" || { echo "MISSING: $f"; exit 1; }
done <<< "$files"
echo "[OK] Required V9 files exist"

"$PY" -m py_compile \
  "$ROOT/desktop/workstation_runtime.py" \
  "$ROOT/desktop/unified_workstation.py" \
  "$ROOT/desktop/patient_app/main.py" \
  "$ROOT/desktop/doctor_app/main_enhanced.py" \
  "$ROOT/src/serial_io/packet_parser.py" \
  "$ROOT/src/serial_io/arduino_reader.py" \
  "$ROOT/src/serial_io/network_reader.py" \
  "$ROOT/src/personal_twin/profile_store.py" \
  "$ROOT/src/personal_twin/adaptive_model.py" \
  "$ROOT/src/personal_twin/baseline_store.py" \
  "$ROOT/src/personal_twin/baseline_capture.py" \
  "$ROOT/src/personal_twin/self_learning_app.py"
echo "[OK] Python syntax checks"

grep -q '\$CP3' "$ROOT/hardware/esp32s3/endo_twin_wearable/endo_twin_wearable.ino"
grep -q 'PPG_NEW_PERSON' "$ROOT/hardware/esp32s3/endo_twin_wearable/endo_twin_wearable.ino"
grep -q '\$PCAL' "$ROOT/hardware/esp32s3/endo_twin_wearable/endo_twin_wearable.ino"
grep -q 'ST_LOW_QUALITY' "$ROOT/hardware/esp32s3/endo_twin_wearable/endo_twin_wearable.ino"
echo "[OK] V9 CP3 + personal PPG calibration markers"

grep -q 'feature_ready.emit' "$ROOT/desktop/unified_workstation.py"
grep -q 'PersonalAdaptiveModel' "$ROOT/desktop/unified_workstation.py"
grep -q 'BaselineCapture' "$ROOT/desktop/unified_workstation.py"
echo "[OK] Unified workstation live-feature + Personal Twin wiring"

grep -q 'BaselineCapture' "$ROOT/desktop/patient_app/main.py"
grep -q 'self.personal_model.observe' "$ROOT/desktop/patient_app/main.py"
grep -q 'self.session.features_updated.connect' "$ROOT/desktop/patient_app/main.py"
echo "[OK] Patient Desktop learning wiring"

grep -q 'self.personal_model.observe' "$ROOT/desktop/doctor_app/main_enhanced.py"
grep -q 'PersonalAdaptiveModel' "$ROOT/desktop/doctor_app/main_enhanced.py"
echo "[OK] Doctor Desktop learning wiring"

echo
echo "V9 ready check passed."
echo "Run './START.sh self-learning' for Personal Twin."
echo "Run './START.sh patient' for Patient Desktop."
echo "Run './START.sh doctor' for Doctor Desktop."
echo "Run './START.sh unified' for Unified Workstation."
