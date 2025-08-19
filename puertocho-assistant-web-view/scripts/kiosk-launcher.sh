#!/bin/bash
###############################################################################
# Kiosk Launcher Script for PuertoCho Assistant Web Dashboard
# This script launches the web dashboard in fullscreen kiosk mode
###############################################################################

# Set strict error handling
set -euo pipefail

# Configuration variables
DISPLAY_RESOLUTION=${KIOSK_RESOLUTION:-"1920x1080"}
DASHBOARD_URL=${DASHBOARD_URL:-"http://localhost:3000"}
KIOSK_BROWSER=${KIOSK_BROWSER:-"chromium-browser"}
LOG_FILE="/var/log/kiosk-launcher.log"
PID_FILE="/var/run/kiosk-launcher.pid"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [KIOSK] $1" | tee -a "$LOG_FILE"
}

# Check if running as root (required for some display operations)
check_user() {
    if [[ $EUID -eq 0 ]]; then
        log "WARNING: Running as root. Consider running as a dedicated user."
    fi
}

# Detect if touch screen is available
detect_touchscreen() {
    if [ -n "${KIOSK_FORCE_TOUCH:-}" ]; then
        log "Touch screen mode forced via environment variable"
        return 0
    fi
    
    # Check for touch devices in /dev/input
    if ls /dev/input/event* 2>/dev/null | xargs -I {} sh -c 'cat {} 2>/dev/null' | head -c1 | wc -c | grep -q '^1$' 2>/dev/null; then
        log "Touch screen detected"
        return 0
    else
        log "No touch screen detected, using mouse mode"
        return 1
    fi
}

# Configure display settings
setup_display() {
    log "Setting up display configuration..."
    
    # Set display resolution if specified
    if [ "$DISPLAY_RESOLUTION" != "auto" ]; then
        log "Setting display resolution to $DISPLAY_RESOLUTION"
        if command -v xrandr >/dev/null 2>&1; then
            xrandr --output HDMI-1 --mode "$DISPLAY_RESOLUTION" 2>/dev/null || \
            xrandr --output HDMI-A-1 --mode "$DISPLAY_RESOLUTION" 2>/dev/null || \
            log "WARNING: Could not set resolution $DISPLAY_RESOLUTION"
        else
            log "WARNING: xrandr not available, cannot set resolution"
        fi
    fi
    
    # Disable screen saver and power management
    log "Disabling screen saver and power management"
    xset s off
    xset -dpms
    xset s noblank
    
    # Hide mouse cursor if touch screen is available
    if detect_touchscreen; then
        log "Hiding mouse cursor for touch screen"
        # Use xdotool to hide cursor (alternative to unclutter)
        if command -v xdotool >/dev/null 2>&1; then
            xdotool mousemove 0 0
        fi
    fi
}

# Kill existing browser instances
kill_existing_browsers() {
    log "Terminating existing browser instances..."
    pkill -f "$KIOSK_BROWSER" || true
    pkill -f "chromium" || true
    pkill -f "firefox" || true
    sleep 2
}

# Wait for network connectivity
wait_for_network() {
    log "Waiting for network connectivity..."
    local max_attempts=30
    local attempt=1
    
    while ! curl -s --max-time 5 "$DASHBOARD_URL" > /dev/null; do
        if [ $attempt -ge $max_attempts ]; then
            log "ERROR: Dashboard not available after $max_attempts attempts"
            return 1
        fi
        log "Attempt $attempt/$max_attempts: Dashboard not ready, waiting..."
        sleep 2
        ((attempt++))
    done
    
    log "Dashboard is accessible at $DASHBOARD_URL"
}

# Launch browser in kiosk mode
launch_browser() {
    log "Launching browser in kiosk mode..."
    
    # Browser arguments for kiosk mode
    local browser_args=(
        --kiosk
        --start-fullscreen
        --no-first-run
        --disable-infobars
        --disable-session-crashed-bubble
        --disable-component-update
        --disable-background-timer-throttling
        --disable-renderer-backgrounding
        --disable-backgrounding-occluded-windows
        --disable-features=TranslateUI,VizDisplayCompositor,VizServiceDisplayCompositor
        --disable-extensions
        --disable-dev-shm-usage
        --no-sandbox
        --disable-gpu
        --disable-gpu-sandbox
        --disable-gpu-compositing
        --disable-gpu-rasterization
        --disable-software-rasterizer
        --disable-web-security
        --disable-features=VizServiceDisplayCompositor
        --use-gl=swiftshader-webgl
        --enable-unsafe-swiftshader
        --allow-running-insecure-content
        --ignore-certificate-errors
        --ignore-ssl-errors
        --ignore-certificate-errors-spki-list
        --ignore-certificate-errors-ssl-errors
        --user-data-dir=/tmp/chromium-data
        --app="$DASHBOARD_URL"
    )
    
    # Additional arguments for touch screen
    if detect_touchscreen; then
        browser_args+=(
            --touch-events=enabled
            --enable-pinch
            --force-device-scale-factor=1.0
        )
    fi
    
    # Launch browser with retry mechanism
    local max_retries=3
    local retry=1
    
    while [ $retry -le $max_retries ]; do
        log "Browser launch attempt $retry/$max_retries"
        
        if $KIOSK_BROWSER "${browser_args[@]}" & then
            local browser_pid=$!
            echo $browser_pid > "$PID_FILE"
            log "Browser launched successfully with PID: $browser_pid"
            
            # Monitor browser process
            wait $browser_pid
            local exit_code=$?
            
            log "Browser exited with code: $exit_code"
            
            if [ $exit_code -eq 0 ]; then
                break
            fi
        fi
        
        log "Browser launch failed, retry $retry/$max_retries"
        sleep 5
        ((retry++))
    done
    
    if [ $retry -gt $max_retries ]; then
        log "ERROR: Failed to launch browser after $max_retries attempts"
        return 1
    fi
}

# Cleanup function
cleanup() {
    log "Cleaning up kiosk launcher..."
    kill_existing_browsers
    rm -f "$PID_FILE"
}

# Signal handlers
trap cleanup EXIT
trap cleanup SIGINT
trap cleanup SIGTERM

# Main execution
main() {
    log "=== Starting PuertoCho Assistant Kiosk Launcher ==="
    log "Dashboard URL: $DASHBOARD_URL"
    log "Browser: $KIOSK_BROWSER"
    log "Resolution: $DISPLAY_RESOLUTION"
    
    check_user
    
    # Check if X11 is available
    if [ -z "${DISPLAY:-}" ]; then
        log "ERROR: No DISPLAY environment variable set"
        exit 1
    fi
    
    # Setup display
    setup_display
    
    # Main loop with auto-restart
    while true; do
        log "Starting kiosk session..."
        
        # Wait for network and dashboard
        if ! wait_for_network; then
            log "Network check failed, retrying in 10 seconds..."
            sleep 10
            continue
        fi
        
        # Kill any existing browsers
        kill_existing_browsers
        
        # Launch browser
        if launch_browser; then
            log "Kiosk session completed normally"
        else
            log "Kiosk session failed"
        fi
        
        # Auto-restart delay
        local restart_delay=${KIOSK_RESTART_DELAY:-5}
        log "Restarting in $restart_delay seconds..."
        sleep $restart_delay
    done
}

# Execute main function
main "$@"
