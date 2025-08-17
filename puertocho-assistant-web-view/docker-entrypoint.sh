#!/bin/bash
###############################################################################
# Docker Entrypoint for PuertoCho Assistant Web Dashboard
# Supports both normal mode and kiosk mode
###############################################################################

set -euo pipefail

# Default values
KIOSK_MODE=${KIOSK_MODE:-false}
KIOSK_RESOLUTION=${KIOSK_RESOLUTION:-1920x1080}
DASHBOARD_URL=${DASHBOARD_URL:-http://localhost:3000}
KIOSK_BROWSER=${KIOSK_BROWSER:-chromium-browser}

echo "=== PuertoCho Assistant Web Dashboard Starting ==="
echo "Kiosk Mode: $KIOSK_MODE"
echo "Dashboard URL: $DASHBOARD_URL"
echo "Resolution: $KIOSK_RESOLUTION"

# Ensure log directories exist
mkdir -p /var/log/supervisor /var/log/kiosk

# Check if build directory exists, if not try to build or serve dev files
if [ ! -d "/usr/share/nginx/html/assets" ] || [ ! -f "/usr/share/nginx/html/index.html" ] || [ "$(ls -A /usr/share/nginx/html)" = "index.html" ]; then
    echo "No production build found, attempting to build..."
    
    if [ -d "/app" ] && [ -f "/app/package.json" ]; then
        cd /app
        echo "Installing dependencies..."
        npm install --production=false || {
            echo "npm install failed, serving placeholder..."
            echo '<!DOCTYPE html><html><head><title>PuertoCho Assistant</title></head><body><h1>Building application...</h1><p>Please wait while the application builds.</p><script>setTimeout(() => location.reload(), 10000);</script></body></html>' > /usr/share/nginx/html/index.html
        }
        
        if [ -f "/app/package.json" ]; then
            echo "Building application..."
            npm run build 2>/dev/null || {
                echo "Build failed, serving development proxy..."
                echo '<!DOCTYPE html><html><head><title>PuertoCho Assistant</title><meta http-equiv="refresh" content="0;url=http://localhost:3000"></head><body><h1>Redirecting to development server...</h1></body></html>' > /usr/share/nginx/html/index.html
            }
            
            if [ -d "/app/build" ]; then
                echo "Copying build files..."
                cp -r /app/build/* /usr/share/nginx/html/
            fi
        fi
    fi
fi

# Set up environment for supervisor
export KIOSK_MODE
export KIOSK_RESOLUTION
export DASHBOARD_URL
export KIOSK_BROWSER
export DISPLAY

# Check if we should run in kiosk mode
if [ "$KIOSK_MODE" = "true" ]; then
    echo "Starting in KIOSK MODE"
    
    # Check if X11 is available for kiosk mode
    if [ -z "${DISPLAY:-}" ]; then
        echo "WARNING: DISPLAY not set, kiosk mode may not work properly"
        echo "Make sure to run with --env DISPLAY=:0 and mount X11 socket"
    fi
    
    # Start with supervisor (nginx + kiosk)
    exec supervisord -c /etc/supervisor/conf.d/puertocho-kiosk.conf
else
    echo "Starting in NORMAL MODE (nginx only)"
    
    # Handle original nginx startup arguments
    if [ "$1" = "nginx" ]; then
        shift
        exec nginx -g "daemon off;" "$@"
    else
        exec "$@"
    fi
fi
