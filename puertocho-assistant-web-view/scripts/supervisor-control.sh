#!/bin/bash
###############################################################################
# Supervisor Control Script - Dynamically enable/disable nginx
# Enables nginx only when NOT in hot reload mode
###############################################################################

# Wait for supervisor to be ready
sleep 2

# Use the correct socket path
SOCKET_PATH="/var/run/supervisor.sock"

# Check if we should start nginx
if [ "${HOT_RELOAD_ENABLED:-false}" = "false" ]; then
    echo "Hot reload disabled - starting nginx"
    supervisorctl -s unix://$SOCKET_PATH start nginx
else
    echo "Hot reload enabled - nginx disabled (Vite handles serving)"
    supervisorctl -s unix://$SOCKET_PATH stop nginx 2>/dev/null || true
fi

# Always ensure kiosk starts if requested
if [ "${KIOSK_MODE:-false}" = "true" ]; then
    echo "Ensuring kiosk is running"
    supervisorctl -s unix://$SOCKET_PATH start kiosk
fi
