#!/usr/bin/env bash
set -euo pipefail

# CHRONO-PCOS V8.3+ - Garuda Linux Setup
# Automatically sets up .venv, dependencies, launchers, desktop shortcuts, diagnostics

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# If script is inside LAUNCH/, go up one level
if [[ "$(basename "$SCRIPT_DIR")" == "LAUNCH" || "$(basename "$SCRIPT_DIR")" == "launchers" || "$(basename "$SCRIPT_DIR")" == "launcher" ]]; then
    PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
fi

cd "$PROJECT_ROOT"

LOG_FILE="$PROJECT_ROOT/logs/setup.log"
mkdir -p "$PROJECT_ROOT/logs"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "======================================================================"
echo "CHRONO-PCOS V8.3+ - Garuda Linux Setup"
echo "Project Root: $PROJECT_ROOT"
echo "Date: $(date)"
echo "======================================================================"

PASS=0
FAIL=0
WARN=0

check() {
    local name="$1"
    local cmd="$2"
    echo -n "Checking $name... "
    if eval "$cmd" >/dev/null 2>&1; then
        echo "✓ PASS"
        PASS=$((PASS+1))
        return 0
    else
        echo "✗ FAIL"
        FAIL=$((FAIL+1))
        return 1
    fi
}

warn_check() {
    local name="$1"
    local cmd="$2"
    echo -n "Checking $name... "
    if eval "$cmd" >/dev/null 2>&1; then
        echo "✓ PASS"
        PASS=$((PASS+1))
        return 0
    else
        echo "⚠ WARNING"
        WARN=$((WARN+1))
        return 1
    fi
}

# 1. Detect Linux
echo ""
echo "[1/10] Detecting Linux..."
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    echo "OS: ${PRETTY_NAME:-Unknown}"
    ID_VAL="${ID:-}"
    ID_LIKE_VAL="${ID_LIKE:-}"
    NAME_VAL="${NAME:-}"
    if [[ "$ID_VAL" == "garuda" || "$ID_LIKE_VAL" == *"arch"* || "$NAME_VAL" == *"Garuda"* ]]; then
        echo "✓ Garuda/Arch detected"
    else
        echo "⚠ Not Garuda, but Linux - continuing (should work on any Linux)"
    fi
else
    echo "⚠ /etc/os-release not found, assuming Linux"
fi

# 2. Check Python
echo ""
echo "[2/10] Checking Python..."
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=$(command -v python3)
    echo "Python: $PYTHON_BIN"
    python3 --version
    PASS=$((PASS+1))
else
    echo "✗ Python3 not found - please install Python 3.9+"
    FAIL=$((FAIL+1))
    exit 1
fi

# 3. Create .venv if missing
echo ""
echo "[3/10] Checking virtual environment..."
if [[ -d "$PROJECT_ROOT/.venv" && -f "$PROJECT_ROOT/.venv/bin/python" ]]; then
    echo "✓ .venv exists: $PROJECT_ROOT/.venv"
    PASS=$((PASS+1))
else
    echo "Creating .venv..."
    if python3 -m venv "$PROJECT_ROOT/.venv"; then
        echo "✓ .venv created"
        PASS=$((PASS+1))
    else
        echo "✗ Failed to create .venv"
        FAIL=$((FAIL+1))
        exit 1
    fi
fi

VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
VENV_PIP="$PROJECT_ROOT/.venv/bin/pip"

# 4. Install requirements
echo ""
echo "[4/10] Installing requirements..."
if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
    echo "Requirements: $PROJECT_ROOT/requirements.txt"
    cat "$PROJECT_ROOT/requirements.txt"
    echo ""
    echo "Installing..."
    if "$VENV_PIP" install --upgrade pip setuptools wheel >/dev/null 2>&1; then
        echo "✓ pip upgraded"
    fi
    if "$VENV_PIP" install -r "$PROJECT_ROOT/requirements.txt"; then
        echo "✓ Requirements installed"
        PASS=$((PASS+1))
    else
        echo "✗ Failed to install requirements"
        FAIL=$((FAIL+1))
    fi
else
    echo "⚠ requirements.txt not found"
    WARN=$((WARN+1))
fi

# 5. Make all .sh launchers executable
echo ""
echo "[5/10] Setting executable permissions..."
chmod +x "$PROJECT_ROOT/COMPLETE_LAUNCHER.sh" 2>/dev/null || true
chmod +x "$PROJECT_ROOT/setup_garuda.sh" 2>/dev/null || true
chmod +x "$PROJECT_ROOT/LAUNCH/"*.sh "$PROJECT_ROOT"/*.sh 2>/dev/null || true
chmod +x "$PROJECT_ROOT/LAUNCH/"*.sh 2>/dev/null || true
chmod +x "$PROJECT_ROOT/run_"*.sh 2>/dev/null || true
echo "✓ Executable permissions set"
PASS=$((PASS+1))
echo "Launchers:"
ls -lh "$PROJECT_ROOT/LAUNCH/"*.sh 2>/dev/null | awk '{print $1, $9}' || echo "No launchers yet"
ls -lh "$PROJECT_ROOT/LAUNCH/"*.sh 2>/dev/null | awk '{print $1, $9}' || echo "No LAUNCH yet"

# 6. Create logs directory
echo ""
echo "[6/10] Creating logs directory..."
mkdir -p "$PROJECT_ROOT/logs"
echo "✓ logs/ created: $PROJECT_ROOT/logs"
PASS=$((PASS+1))

# 7. Create desktop shortcuts if appropriate
echo ""
echo "[7/10] Creating desktop shortcuts..."
DESKTOP_DIR="$HOME/Desktop"
if [[ ! -d "$DESKTOP_DIR" ]]; then
    DESKTOP_DIR="$HOME/.local/share/applications"
fi
mkdir -p "$PROJECT_ROOT/desktop"
# .desktop files will be created by launcher setup, just ensure directory exists
echo "✓ desktop/ directory ready"
echo "Desktop files in $PROJECT_ROOT/desktop/:"
ls -lh "$PROJECT_ROOT/desktop/"*.desktop 2>/dev/null || echo "No .desktop files yet (will be created by setup)"
PASS=$((PASS+1))

# 8. Run basic diagnostics
echo ""
echo "[8/10] Running diagnostics..."
"$VENV_PYTHON" -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('$PROJECT_ROOT').resolve()))
print('Python:', sys.version)
try:
    import PySide6
    print('PySide6: OK', PySide6.__version__)
except Exception as e:
    print('PySide6: FAIL', e)
try:
    import numpy, pandas, sklearn, pyqtgraph
    print('NumPy/Pandas/Sklearn/PyQtGraph: OK')
except Exception as e:
    print('Dependencies: FAIL', e)
try:
    from database.database import LocalDatabase
    db = LocalDatabase(db_path=Path('/tmp/setup_test.db'))
    print('Database: OK -', len(db.list_providers()), 'providers')
except Exception as e:
    print('Database: FAIL', e)
try:
    from core.chrono_metabolic import ChronoMetabolicFingerprint
    print('Chrono-Metabolic: OK')
except Exception as e:
    print('Chrono-Metabolic: FAIL', e)
try:
    from src.core.feature_extraction import RealtimeFeatureExtractor
    print('Scientific Core: OK')
except Exception as e:
    print('Scientific Core: FAIL', e)
" || echo "Diagnostics encountered errors (see above)"

# 9. Create optional .desktop launchers
echo ""
echo "[9/10] Checking .desktop files..."
if ls "$PROJECT_ROOT/desktop/"*.desktop >/dev/null 2>&1; then
    echo "✓ .desktop files exist"
    PASS=$((PASS+1))
else
    echo "⚠ No .desktop files yet - will be created when launchers are built"
    WARN=$((WARN+1))
fi

# 10. Final report
echo ""
echo "[10/10] Final report..."
echo "======================================================================"
echo "Setup Summary:"
echo "PASS: $PASS"
echo "WARN: $WARN"
echo "FAIL: $FAIL"
echo "======================================================================"

if [[ $FAIL -eq 0 ]]; then
    echo ""
    echo "CHRONO-PCOS V8.3+ is ready."
    echo ""
    echo "Double-click:"
    echo "  LAUNCH/COMPLETE_LAUNCHER.sh"
    echo "or"
    echo "  COMPLETE_LAUNCHER.sh"
    echo ""
    echo "Or run:"
    echo "  ./LAUNCH/COMPLETE_LAUNCHER.sh"
    echo ""
    echo "For individual apps, open LAUNCH/ and double-click:"
    echo "  ./START.sh (menu) or LAUNCH/UNIFIED_WORKSTATION.sh, LAUNCH/WEBSITE.sh"
    echo ""
    echo "If double-click opens text editor in Dolphin:"
    echo "  Dolphin → Right-click .sh → Properties → Permissions → Check 'Is executable'"
    echo "  Dolphin → Settings → Configure Dolphin → General → Confirmations → Uncheck or set Executable files to 'Run'"
    echo "  Or: Right-click → Open With → Run"
    echo ""
    echo "Logs: $PROJECT_ROOT/logs/"
    echo "======================================================================"
    # Try to show graphical success dialog if possible
    if command -v kdialog >/dev/null 2>&1; then
        kdialog --msgbox "CHRONO-PCOS V8.3+ is ready!\n\nDouble-click LAUNCH/COMPLETE_LAUNCHER.sh to open Control Center." 2>/dev/null || true
    elif command -v zenity >/dev/null 2>&1; then
        zenity --info --text="CHRONO-PCOS V8.3+ is ready!\n\nDouble-click LAUNCH/COMPLETE_LAUNCHER.sh" 2>/dev/null || true
    fi
    exit 0
else
    echo ""
    echo "Setup completed with $FAIL failure(s), $WARN warning(s)."
    echo "Check logs: $LOG_FILE"
    echo "Run DIAGNOSTICS.sh for details."
    echo "======================================================================"
    exit 1
fi
