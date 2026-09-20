#!/usr/bin/env bash
set -euo pipefail

# CHRONO-PCOS V8.3+ - Setup (Garuda/Linux generic)
# Wrapper for setup_garuda.sh for compatibility

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
BASE_NAME="$(basename "$SCRIPT_DIR")"
if [[ "$BASE_NAME" == "LAUNCH" || "$BASE_NAME" == "launchers" || "$BASE_NAME" == "launcher" ]]; then
    PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
fi

cd "$PROJECT_ROOT"

echo "CHRONO-PCOS V8.3+ - SETUP.sh"
echo "This is a wrapper for setup_garuda.sh"
echo "Project Root: $PROJECT_ROOT"
echo ""

if [[ -f "$PROJECT_ROOT/setup_garuda.sh" ]]; then
    exec bash "$PROJECT_ROOT/setup_garuda.sh"
else
    echo "setup_garuda.sh not found at $PROJECT_ROOT/setup_garuda.sh"
    exit 1
fi
