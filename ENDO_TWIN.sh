#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"
mkdir -p logs
LOG_FILE="logs/endo_twin.log"
echo "=== ENDO-TWIN General Platform ===" | tee "$LOG_FILE"
echo "ENDO-TWIN is general platform, CHRONO-PCOS is first disease-specific model" | tee -a "$LOG_FILE"
echo "Understand your physiological patterns over time" | tee -a "$LOG_FILE"
echo "Project root: $PROJECT_ROOT" | tee -a "$LOG_FILE"
echo "Timestamp: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

echo "Using Python: $PYTHON_BIN" | tee -a "$LOG_FILE"
echo "Launching ENDO-TWIN General Platform..." | tee -a "$LOG_FILE"
echo "TEST 1: General dashboard should make sense without PCOS knowledge" | tee -a "$LOG_FILE"
echo "TEST 2: Disease Models should contain CHRONO-PCOS" | tee -a "$LOG_FILE"
echo "TEST 3: Main app works even without disease model" | tee -a "$LOG_FILE"
echo "TEST 4: Dummy future model extensibility" | tee -a "$LOG_FILE"
echo "TEST 5: CHRONO-PCOS preserves original functionality" | tee -a "$LOG_FILE"
echo "TEST 6: Patient isolation DEMO-001/002/003" | tee -a "$LOG_FILE"

# Try general platform first - ENDO-TWIN general platform
if [ -f "$PROJECT_ROOT/apps/main/main_app.py" ]; then
    echo "Found general platform: apps/main/main_app.py - ENDO-TWIN is platform, CHRONO-PCOS first model" | tee -a "$LOG_FILE"
    echo "Launching: $PYTHON_BIN apps/main/main_app.py" | tee -a "$LOG_FILE"
    "$PYTHON_BIN" apps/main/main_app.py 2>&1 | tee -a "$LOG_FILE"
    EXIT_CODE=${PIPESTATUS[0]}
    if [ $EXIT_CODE -eq 0 ]; then
        echo "ENDO-TWIN General Platform closed with code $EXIT_CODE" | tee -a "$LOG_FILE"
        exit 0
    fi
    echo "General platform console closed with $EXIT_CODE, trying GUI if available..." | tee -a "$LOG_FILE"
    # Try with GUI - may need display
    "$PYTHON_BIN" -c "from apps.main.main_app import main; main()" 2>&1 | tee -a "$LOG_FILE"
    EXIT_CODE=${PIPESTATUS[0]}
    echo "General platform GUI closed with $EXIT_CODE" | tee -a "$LOG_FILE"
    exit $EXIT_CODE
fi

# Fallback to original scientific core
if [ -f "$PROJECT_ROOT/src/ui/main_window.py" ]; then
    echo "Fallback to original: src/ui/main_window.py" | tee -a "$LOG_FILE"
    "$PYTHON_BIN" -m src.app --demo 2>&1 | tee -a "$LOG_FILE" || "$PYTHON_BIN" src/app.py --demo 2>&1 | tee -a "$LOG_FILE"
    exit 0
fi

echo "ERROR: No main app found" | tee -a "$LOG_FILE"
if command -v kdialog >/dev/null 2>&1; then
    kdialog --error "ENDO-TWIN General Platform not found. Check logs/endo_twin.log"
elif command -v zenity >/dev/null 2>&1; then
    zenity --error --text="ENDO-TWIN General Platform not found. Check logs/endo_twin.log"
fi
exit 1
