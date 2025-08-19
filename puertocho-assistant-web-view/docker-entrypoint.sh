#!/bin/bash
###############################################################################
# Docker Entrypoint for PuertoCho Assistant Web Dashboard
# Supports hot-reload mode and kiosk mode
###############################################################################

set -euo pipefail

# Default values
KIOSK_MODE=${KIOSK_MODE:-false}
HOT_RELOAD_ENABLED=${HOT_RELOAD_ENABLED:-false}
KIOSK_RESOLUTION=${KIOSK_RESOLUTION:-1920x1080}
DASHBOARD_URL=${DASHBOARD_URL:-http://localhost:3000}
KIOSK_BROWSER=${KIOSK_BROWSER:-chromium-browser}

echo "=== PuertoCho Assistant Web Dashboard Starting ==="
echo "Hot Reload Enabled: $HOT_RELOAD_ENABLED"
echo "Kiosk Mode: $KIOSK_MODE"
echo "Dashboard URL: $DASHBOARD_URL"
echo "Resolution: $KIOSK_RESOLUTION"

# Ensure log directories exist
mkdir -p /var/log/supervisor /var/log/kiosk

# Function to start development server with hot reload
start_dev_server() {
    echo "Starting Vite development server with hot reload..."
    cd /app
    
    # Ensure dependencies are installed
    if [ ! -d "node_modules" ] || [ ! -f "package-lock.json" ]; then
        echo "Installing dependencies..."
        npm install
    fi
    
    # Check if we should run in kiosk mode alongside development server
    if [ "$KIOSK_MODE" = "true" ]; then
        echo "Starting development server with KIOSK MODE"
        
        # Set up environment for supervisor
        export KIOSK_MODE
        export KIOSK_RESOLUTION
        export DASHBOARD_URL
        export KIOSK_BROWSER
        export DISPLAY
        
        # Start Vite dev server in background
        npm run dev:host &
        DEV_SERVER_PID=$!
        
        # Wait a bit for dev server to start
        sleep 5
        
        # Start kiosk browser via supervisor
        exec supervisord -c /etc/supervisor/conf.d/puertocho-kiosk.conf
    else
        echo "Starting development server in NORMAL MODE"
        # Start Vite dev server
        exec npm run dev:host
    fi
}

# Function to build and serve production
start_production() {
    echo "Starting production build process..."
    
    # Check if build directory exists, if not try to build
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
    
    # Set up environment for supervisor
    export KIOSK_MODE
    export KIOSK_RESOLUTION
    export DASHBOARD_URL
    export KIOSK_BROWSER
    export DISPLAY
    export HOT_RELOAD_ENABLED
    
    # Check if we should run in kiosk mode
    if [ "$KIOSK_MODE" = "true" ]; then
        echo "Starting nginx with KIOSK MODE"
        
        # Start with supervisor (nginx + kiosk)
        # The control script will handle nginx startup based on HOT_RELOAD_ENABLED
        exec supervisord -c /etc/supervisor/conf.d/puertocho-kiosk.conf
    else
        echo "Starting nginx in NORMAL MODE"
        exec nginx -g "daemon off;"
    fi
}

# Main execution logic
if [ "$HOT_RELOAD_ENABLED" = "true" ]; then
    start_dev_server
else
    start_production
fi
