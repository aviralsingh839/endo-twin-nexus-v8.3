#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# If inside launchers/ or LAUNCH/ or launcher/, project root is parent
BASE_NAME="$(basename "$SCRIPT_DIR")"
if [[ "$BASE_NAME" == "launchers" || "$BASE_NAME" == "LAUNCH" || "$BASE_NAME" == "launcher" ]]; then
    PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
fi

cd "$PROJECT_ROOT"
mkdir -p "$PROJECT_ROOT/logs"

VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
VENV_PIP="$PROJECT_ROOT/.venv/bin/pip"

show_error() {
    local title="$1"
    local msg="$2"
    local log_file="$3"
    echo "ERROR: $title - $msg" | tee -a "$log_file"
    if command -v kdialog >/dev/null 2>&1; then
        kdialog --error "$title

$msg

Log: $log_file" 2>/dev/null || true
    elif command -v zenity >/dev/null 2>&1; then
        zenity --error --title="$title" --text="$msg

Log: $log_file" 2>/dev/null || true
    elif command -v xmessage >/dev/null 2>&1; then
        xmessage -center "$title: $msg" 2>/dev/null || true
    fi
    # Also show in terminal if running in terminal
    echo ""
    echo "======================================================================"
    echo "$title"
    echo "======================================================================"
    echo "$msg"
    echo ""
    echo "Log: $log_file"
    echo "Run DIAGNOSTICS.sh or setup_garuda.sh"
    echo "======================================================================"
}

check_venv() {
    if [[ ! -f "$VENV_PYTHON" ]]; then
        local log="$PROJECT_ROOT/logs/launcher.log"
        show_error "CHRONO-PCOS Environment Not Found" "Virtual environment not found at $VENV_PYTHON

Please run:
  ./setup_garuda.sh

Or from file manager double-click setup_garuda.sh" "$log"
        exit 1
    fi
}


LOG_FILE="$PROJECT_ROOT/logs/website.log"
echo "$(date): Launching WEBSITE" | tee -a "$LOG_FILE"

# Website is static HTML - no venv needed, but check anyway
if [[ -f "$PROJECT_ROOT/.venv/bin/python" ]]; then
    echo ".venv found" >> "$LOG_FILE"
fi

WEBSITE_FILE="$PROJECT_ROOT/website/index.html"

if [[ ! -f "$WEBSITE_FILE" ]]; then
    echo "Website not found: $WEBSITE_FILE" | tee -a "$LOG_FILE"
    if command -v kdialog >/dev/null 2>&1; then
        kdialog --error "Website not found:\n$WEBSITE_FILE" 2>/dev/null || true
    fi
    exit 1
fi

echo "Website is static HTML: $WEBSITE_FILE" | tee -a "$LOG_FILE"
echo "Opening with xdg-open..." | tee -a "$LOG_FILE"

# Try xdg-open (Garuda/Linux standard)
if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$WEBSITE_FILE" 2>&1 | tee -a "$LOG_FILE" &
    echo "Opened with xdg-open" | tee -a "$LOG_FILE"
    # Also try to start simple http server for better experience and open browser
    if command -v python3 >/dev/null 2>&1; then
        echo "Also starting local server at http://localhost:8000..." | tee -a "$LOG_FILE"
        cd "$PROJECT_ROOT/website"
        python3 -m http.server 8000 2>&1 | tee -a "$LOG_FILE" &
        SERVER_PID=$!
        sleep 2
        if command -v xdg-open >/dev/null 2>&1; then
            xdg-open "http://localhost:8000" 2>&1 | tee -a "$LOG_FILE" &
        fi
        echo "Server PID $SERVER_PID running at http://localhost:8000 - Close terminal to stop" | tee -a "$LOG_FILE"
        wait $SERVER_PID 2>/dev/null || true
    fi
elif command -v firefox >/dev/null 2>&1; then
    firefox "$WEBSITE_FILE" &
elif command -v chromium >/dev/null 2>&1; then
    chromium "$WEBSITE_FILE" &
else
    echo "No browser opener found, please open manually: $WEBSITE_FILE" | tee -a "$LOG_FILE"
    if command -v kdialog >/dev/null 2>&1; then
        kdialog --msgbox "Please open manually:\n$WEBSITE_FILE\n\nNo xdg-open found" 2>/dev/null || true
    fi
fi
