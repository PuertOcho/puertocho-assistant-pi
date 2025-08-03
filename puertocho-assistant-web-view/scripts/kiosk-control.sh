#!/bin/bash
###############################################################################
# Kiosk Control Script for PuertoCho Assistant
# Provides control commands for the kiosk mode
###############################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIOSK_LAUNCHER="$SCRIPT_DIR/kiosk-launcher.sh"
LOG_FILE="/var/log/kiosk-control.log"
PID_FILE="/var/run/kiosk-launcher.pid"
SERVICE_NAME="puertocho-kiosk"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [KIOSK-CTRL] $1" | tee -a "$LOG_FILE"
}

# Check if kiosk is running
is_kiosk_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Start kiosk
start_kiosk() {
    if is_kiosk_running; then
        log "Kiosk is already running"
        return 0
    fi
    
    log "Starting kiosk launcher..."
    
    # Check if we're in a Docker environment
    if [ -f /.dockerenv ]; then
        log "Running in Docker container"
        # In Docker, we need to ensure X11 forwarding is set up
        export DISPLAY=${DISPLAY:-:0}
    fi
    
    # Start the launcher in background
    nohup "$KIOSK_LAUNCHER" > "$LOG_FILE" 2>&1 &
    local launcher_pid=$!
    
    # Give it a moment to start
    sleep 3
    
    if ps -p "$launcher_pid" > /dev/null 2>&1; then
        log "Kiosk launcher started successfully with PID: $launcher_pid"
        return 0
    else
        log "ERROR: Failed to start kiosk launcher"
        return 1
    fi
}

# Stop kiosk
stop_kiosk() {
    log "Stopping kiosk..."
    
    # Kill the launcher script
    pkill -f "kiosk-launcher.sh" || true
    
    # Kill browsers
    pkill -f "chromium-browser" || true
    pkill -f "chromium" || true
    pkill -f "firefox" || true
    
    # Clean up PID file
    rm -f "$PID_FILE"
    
    log "Kiosk stopped"
}

# Restart kiosk
restart_kiosk() {
    log "Restarting kiosk..."
    stop_kiosk
    sleep 2
    start_kiosk
}

# Get kiosk status
status_kiosk() {
    if is_kiosk_running; then
        local pid=$(cat "$PID_FILE")
        echo "✅ Kiosk is running (PID: $pid)"
        
        # Check if browser is also running
        if pgrep -f "chromium" > /dev/null; then
            echo "✅ Browser is active"
        else
            echo "⚠️  Browser is not running"
        fi
        
        return 0
    else
        echo "❌ Kiosk is not running"
        return 1
    fi
}

# Show logs
show_logs() {
    local lines=${1:-50}
    if [ -f "$LOG_FILE" ]; then
        echo "=== Last $lines lines of kiosk log ==="
        tail -n "$lines" "$LOG_FILE"
    else
        echo "No log file found at $LOG_FILE"
    fi
}

# Enable autostart (systemd service)
enable_autostart() {
    log "Setting up autostart service..."
    
    local service_file="/etc/systemd/system/$SERVICE_NAME.service"
    
    # Create systemd service
    sudo tee "$service_file" > /dev/null << EOF
[Unit]
Description=PuertoCho Assistant Kiosk Mode
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=forking
User=$(whoami)
Group=$(id -gn)
Environment=DISPLAY=:0
ExecStart=$SCRIPT_DIR/kiosk-control.sh start
ExecStop=$SCRIPT_DIR/kiosk-control.sh stop
ExecReload=$SCRIPT_DIR/kiosk-control.sh restart
Restart=always
RestartSec=10

[Install]
WantedBy=graphical-session.target
EOF

    # Enable and start service
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
    
    log "Autostart service enabled. Use 'sudo systemctl start $SERVICE_NAME' to start."
}

# Disable autostart
disable_autostart() {
    log "Disabling autostart service..."
    
    sudo systemctl stop "$SERVICE_NAME" || true
    sudo systemctl disable "$SERVICE_NAME" || true
    sudo rm -f "/etc/systemd/system/$SERVICE_NAME.service"
    sudo systemctl daemon-reload
    
    log "Autostart service disabled"
}

# Display usage
usage() {
    cat << EOF
PuertoCho Assistant Kiosk Control

Usage: $0 {start|stop|restart|status|logs|enable-autostart|disable-autostart}

Commands:
    start              Start the kiosk mode
    stop               Stop the kiosk mode
    restart            Restart the kiosk mode
    status             Show current status
    logs [lines]       Show log entries (default: 50 lines)
    enable-autostart   Enable automatic startup on boot
    disable-autostart  Disable automatic startup on boot

Environment Variables:
    KIOSK_RESOLUTION   Display resolution (default: 1920x1080)
    DASHBOARD_URL      Dashboard URL (default: http://localhost:3000)
    KIOSK_BROWSER      Browser command (default: chromium-browser)
    KIOSK_FORCE_TOUCH  Force touch mode (set to any value)

Examples:
    $0 start                    # Start kiosk mode
    $0 logs 100                 # Show last 100 log lines
    KIOSK_RESOLUTION=1024x768 $0 start  # Start with specific resolution

EOF
}

# Main command processing
case "${1:-}" in
    start)
        start_kiosk
        ;;
    stop)
        stop_kiosk
        ;;
    restart)
        restart_kiosk
        ;;
    status)
        status_kiosk
        ;;
    logs)
        show_logs "${2:-50}"
        ;;
    enable-autostart)
        enable_autostart
        ;;
    disable-autostart)
        disable_autostart
        ;;
    *)
        usage
        exit 1
        ;;
esac
