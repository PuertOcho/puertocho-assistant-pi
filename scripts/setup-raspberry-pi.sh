#!/bin/bash

# PuertoCho Assistant - Script de Configuración para Raspberry Pi
# Este script configura automáticamente una Raspberry Pi para el modo kiosko

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Verificar que se ejecuta en Raspberry Pi
check_raspberry_pi() {
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        warning "Este script está diseñado para Raspberry Pi"
        read -p "¿Continuar de todas formas? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Verificar permisos de sudo
check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        error "Este script requiere permisos de sudo"
        exit 1
    fi
}

# Función para crear backup de archivos de configuración
backup_config() {
    local file=$1
    if [ -f "$file" ]; then
        log "Creando backup de $file"
        sudo cp "$file" "${file}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
}

# Actualizar sistema
update_system() {
    log "Actualizando sistema..."
    sudo apt update
    sudo apt upgrade -y
}

# Instalar dependencias necesarias
install_dependencies() {
    log "Instalando dependencias necesarias..."
    
    # Verificar si ya tiene entorno gráfico
    if ! command -v startx &> /dev/null; then
        log "Instalando entorno gráfico..."
        sudo apt install -y xorg lightdm lxde-core
    else
        info "Entorno gráfico ya instalado"
    fi
    
    # Instalar herramientas adicionales
    sudo apt install -y \
        chromium-browser \
        xinput-calibrator \
        x11-xserver-utils \
        unclutter \
        git \
        curl
}

# Configurar Docker si no está instalado
install_docker() {
    if ! command -v docker &> /dev/null; then
        log "Instalando Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
        
        log "Instalando Docker Compose..."
        sudo pip3 install docker-compose
    else
        info "Docker ya está instalado"
    fi
}

# Configurar auto-login
configure_autologin() {
    log "Configurando auto-login..."
    
    backup_config "/etc/lightdm/lightdm.conf"
    
    # Configurar lightdm para auto-login
    sudo tee /etc/lightdm/lightdm.conf > /dev/null <<EOF
[Seat:*]
autologin-user=$USER
autologin-user-timeout=0
user-session=LXDE-pi
EOF
}

# Configurar X11 para Docker
configure_x11() {
    log "Configurando X11 para Docker..."
    
    # Añadir xhost al .bashrc si no existe
    if ! grep -q "xhost +local:docker" ~/.bashrc; then
        echo "# Permitir Docker acceso a X11" >> ~/.bashrc
        echo "xhost +local:docker" >> ~/.bashrc
    fi
    
    # Configurar autostart para deshabilitar screensaver
    mkdir -p ~/.config/lxsession/LXDE-pi
    
    cat > ~/.config/lxsession/LXDE-pi/autostart <<EOF
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash
@point-rpi

# Deshabilitar screensaver y power management
@xset s off
@xset -dpms
@xset s noblank

# Permitir Docker acceso a X11
@sh -c 'sleep 5 && xhost +local:docker'
EOF
}

# Configurar GPU split para mejor rendimiento
configure_gpu() {
    log "Configurando GPU split..."
    
    backup_config "/boot/config.txt"
    
    # Verificar si ya está configurado
    if ! grep -q "gpu_mem=" /boot/config.txt; then
        echo "" | sudo tee -a /boot/config.txt
        echo "# GPU Memory Split para mejor rendimiento gráfico" | sudo tee -a /boot/config.txt
        echo "gpu_mem=128" | sudo tee -a /boot/config.txt
    fi
}

# Configurar resolución de pantalla
configure_display() {
    log "Configurando resolución de pantalla..."
    
    echo ""
    echo "Selecciona la configuración de pantalla:"
    echo "1) 1920x1080 (HDMI estándar)"
    echo "2) 1024x600 (Pantalla táctil común)"
    echo "3) Auto-detectar"
    echo "4) Saltar configuración"
    
    read -p "Opción (1-4): " choice
    
    case $choice in
        1)
            if ! grep -q "hdmi_group=2" /boot/config.txt; then
                echo "" | sudo tee -a /boot/config.txt
                echo "# Configuración de pantalla 1920x1080" | sudo tee -a /boot/config.txt
                echo "hdmi_group=2" | sudo tee -a /boot/config.txt
                echo "hdmi_mode=82" | sudo tee -a /boot/config.txt
            fi
            ;;
        2)
            if ! grep -q "hdmi_cvt=1024 600" /boot/config.txt; then
                echo "" | sudo tee -a /boot/config.txt
                echo "# Configuración de pantalla 1024x600" | sudo tee -a /boot/config.txt
                echo "hdmi_cvt=1024 600 60 6 0 0 0" | sudo tee -a /boot/config.txt
                echo "hdmi_group=2" | sudo tee -a /boot/config.txt
                echo "hdmi_mode=87" | sudo tee -a /boot/config.txt
            fi
            ;;
        3)
            info "Auto-detectar seleccionado"
            ;;
        4)
            info "Saltando configuración de pantalla"
            ;;
        *)
            warning "Opción inválida, saltando configuración"
            ;;
    esac
}

# Crear servicio systemd para auto-arranque
create_kiosk_service() {
    log "Creando servicio de auto-arranque del kiosko..."
    
    # Obtener directorio actual del proyecto
    PROJECT_DIR=$(pwd)
    
    sudo tee /etc/systemd/system/puertocho-kiosk.service > /dev/null <<EOF
[Unit]
Description=PuertoCho Assistant Kiosk
After=graphical-session.target network.target
Wants=graphical-session.target

[Service]
Type=oneshot
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR
Environment=DISPLAY=:0
Environment=KIOSK_MODE=true
Environment=KIOSK_RESOLUTION=1920x1080
ExecStartPre=/bin/sleep 10
ExecStartPre=/usr/bin/xhost +local:docker
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
RemainAfterExit=yes
StandardOutput=journal
StandardError=journal
Restart=on-failure
RestartSec=30

[Install]
WantedBy=graphical-session.target
EOF

    # Habilitar el servicio
    sudo systemctl enable puertocho-kiosk.service
    sudo systemctl daemon-reload
}

# Crear archivo de configuración .env
create_env_config() {
    log "Creando archivo de configuración..."
    
    if [ ! -f ".env" ]; then
        cat > .env <<EOF
# Configuración del Kiosko PuertoCho Assistant
KIOSK_MODE=true
KIOSK_RESOLUTION=1920x1080
DISPLAY=:0

# URLs de la aplicación
DASHBOARD_URL=http://localhost:3000
VITE_BACKEND_WS_URL=ws://localhost:8000/ws
VITE_BACKEND_HTTP_URL=http://localhost:8000

# Configuración del navegador
KIOSK_BROWSER=chromium-browser
KIOSK_RESTART_DELAY=5
EOF
        info "Archivo .env creado"
    else
        info "Archivo .env ya existe, no se sobrescribe"
    fi
}

# Configurar pantalla táctil si está presente
configure_touchscreen() {
    if [ -f "/proc/device-tree/soc/i2c@7e804000/touchscreen@5d/compatible" ]; then
        log "Pantalla táctil detectada, configurando..."
        
        sudo apt install -y raspberrypi-ui-mods
        
        echo ""
        read -p "¿Quieres calibrar la pantalla táctil ahora? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            xinput_calibrator
        fi
    fi
}

# Verificar configuración
verify_setup() {
    log "Verificando configuración..."
    
    # Verificar Docker
    if docker --version &> /dev/null; then
        info "✓ Docker instalado correctamente"
    else
        error "✗ Docker no está funcionando"
    fi
    
    # Verificar servicio
    if systemctl is-enabled puertocho-kiosk.service &> /dev/null; then
        info "✓ Servicio de auto-arranque habilitado"
    else
        error "✗ Servicio de auto-arranque no habilitado"
    fi
    
    # Verificar archivos de configuración
    if [ -f ".env" ]; then
        info "✓ Archivo de configuración creado"
    else
        warning "✗ Archivo .env no encontrado"
    fi
}

# Función principal
main() {
    echo ""
    echo "================================================"
    echo "  PuertoCho Assistant - Configuración Raspberry Pi"
    echo "================================================"
    echo ""
    
    info "Este script configurará tu Raspberry Pi para el modo kiosko"
    echo ""
    read -p "¿Continuar con la instalación? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
    
    check_raspberry_pi
    check_sudo
    
    log "Iniciando configuración..."
    
    update_system
    install_dependencies
    install_docker
    configure_autologin
    configure_x11
    configure_gpu
    configure_display
    configure_touchscreen
    create_env_config
    create_kiosk_service
    
    verify_setup
    
    echo ""
    echo "================================================"
    log "Configuración completada exitosamente!"
    echo "================================================"
    echo ""
    warning "IMPORTANTE: Es necesario reiniciar para aplicar todos los cambios"
    echo ""
    echo "Después del reinicio, el kiosko se iniciará automáticamente."
    echo "Para controlar el servicio manualmente:"
    echo "  sudo systemctl start puertocho-kiosk.service"
    echo "  sudo systemctl stop puertocho-kiosk.service"
    echo "  sudo systemctl status puertocho-kiosk.service"
    echo ""
    read -p "¿Reiniciar ahora? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Reiniciando en 5 segundos..."
        sleep 5
        sudo reboot
    else
        warning "Recuerda reiniciar manualmente para aplicar los cambios"
    fi
}

# Ejecutar función principal
main "$@"
