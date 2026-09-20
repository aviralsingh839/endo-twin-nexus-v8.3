#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# If inside LAUNCH/ or launchers/ or launcher/, go up one level
BASE_NAME="$(basename "$SCRIPT_DIR")"
if [[ "$BASE_NAME" == "launchers" || "$BASE_NAME" == "LAUNCH" || "$BASE_NAME" == "launcher" ]]; then
    PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
fi

cd "$PROJECT_ROOT"
mkdir -p "$PROJECT_ROOT/logs"

VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
LOG_FILE="$PROJECT_ROOT/logs/launcher.log"

echo "$(date): Launching COMPLETE_LAUNCHER - Control Center" | tee -a "$LOG_FILE"

# Check .venv
if [[ ! -f "$VENV_PYTHON" ]]; then
    echo "CHRONO-PCOS environment not found at $VENV_PYTHON" | tee -a "$LOG_FILE"
    if command -v kdialog >/dev/null 2>&1; then
        kdialog --error "CHRONO-PCOS environment is not installed.\n\nPlease run:\n  ./setup_garuda.sh\n\nOr double-click setup_garuda.sh in file manager" 2>/dev/null || true
    elif command -v zenity >/dev/null 2>&1; then
        zenity --error --text="CHRONO-PCOS environment not installed.\n\nPlease run setup_garuda.sh" 2>/dev/null || true
    else
        echo "CHRONO-PCOS environment is not installed. Please run: ./setup_garuda.sh"
    fi
    # Offer to run setup automatically
    if [[ -f "$PROJECT_ROOT/setup_garuda.sh" ]]; then
        echo "Attempting to run setup_garuda.sh automatically..." | tee -a "$LOG_FILE"
        bash "$PROJECT_ROOT/setup_garuda.sh" 2>&1 | tee -a "$LOG_FILE" || true
        if [[ -f "$VENV_PYTHON" ]]; then
            echo ".venv now exists, continuing to launch Control Center..." | tee -a "$LOG_FILE"
        else
            exit 1
        fi
    else
        exit 1
    fi
fi

# Launch Control Center GUI
echo "Launching Control Center GUI: launcher/main.py" | tee -a "$LOG_FILE"
cd "$PROJECT_ROOT"
exec "$VENV_PYTHON" "$PROJECT_ROOT/launcher/main.py" 2>&1 | tee -a "$LOG_FILE"
