#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
BASE_NAME="$(basename "$SCRIPT_DIR")"
if [[ "$BASE_NAME" == "launchers" || "$BASE_NAME" == "LAUNCH" || "$BASE_NAME" == "launcher" ]]; then
    PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
fi
cd "$PROJECT_ROOT"
mkdir -p "$PROJECT_ROOT/logs"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
LOG_FILE="$PROJECT_ROOT/logs/doctor_android.log"
echo "$(date): Launching DOCTOR_ANDROID" | tee -a "$LOG_FILE"
if [[ ! -f "$VENV_PYTHON" ]]; then
    echo "Environment not found" | tee -a "$LOG_FILE"
    exit 1
fi
APK_FOUND=$(find "$PROJECT_ROOT/android/doctor_app" -name "*.apk" 2>/dev/null | head -1)
if [[ -n "$APK_FOUND" ]]; then
    echo "APK found: $APK_FOUND" | tee -a "$LOG_FILE"
else
    echo "No APK built yet - PC demo available" | tee -a "$LOG_FILE"
fi
cd "$PROJECT_ROOT"
exec "$VENV_PYTHON" -m android.doctor_app.main 2>&1 | tee -a "$LOG_FILE"
