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
LOG_FILE="$PROJECT_ROOT/logs/ultrasound.log"
echo "$(date): Launching ULTRASOUND" | tee -a "$LOG_FILE"
if [[ ! -f "$VENV_PYTHON" ]]; then
    echo "CHRONO-PCOS environment not found at $VENV_PYTHON" | tee -a "$LOG_FILE"
    exit 1
fi
cd "$PROJECT_ROOT"
exec "$VENV_PYTHON" "$PROJECT_ROOT/launcher/ultrasound.py" 2>&1 | tee -a "$LOG_FILE"
