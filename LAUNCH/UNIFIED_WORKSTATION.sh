#!/usr/bin/env bash
# ENDO-TWIN NEXUS — Unified Workstation (web UI: Patient + Doctor in one console)
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
BASE_NAME="$(basename "$SCRIPT_DIR")"
if [[ "$BASE_NAME" == "launchers" || "$BASE_NAME" == "LAUNCH" || "$BASE_NAME" == "launcher" ]]; then
    PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
fi

cd "$PROJECT_ROOT"
mkdir -p "$PROJECT_ROOT/logs"
LOG_FILE="$PROJECT_ROOT/logs/workstation.log"
PORT="${1:-${ENDOTWIN_PORT:-8787}}"

echo "$(date): Launching UNIFIED WORKSTATION on port $PORT" | tee -a "$LOG_FILE"

PY="$(command -v python3 || command -v python || true)"
if [[ -z "$PY" ]]; then
    echo "ERROR: python3 not found in PATH" | tee -a "$LOG_FILE"
    exit 1
fi

exec "$PY" "$PROJECT_ROOT/workstation/serve.py" --port "$PORT" --host "${ENDOTWIN_HOST:-0.0.0.0}" 2>&1 | tee -a "$LOG_FILE"
