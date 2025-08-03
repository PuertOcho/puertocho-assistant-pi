# Configuración de Raspberry Pi para Modo Kiosko

## 📋 Requisitos Previos

- Raspberry Pi con Raspberry Pi OS Desktop (no Lite)
- Pantalla conectada (HDMI o pantalla táctil oficial)
- Docker y Docker Compose instalados
- Usuario con permisos sudo

## 🔧 Configuraciones Necesarias

### 1. Configuración del Sistema X11

#### Verificar si X11 está funcionando:
```bash
# Verificar si el servidor X está corriendo
ps aux | grep -i xorg

# Verificar la variable DISPLAY
echo $DISPLAY

# Test básico de X11
xdpyinfo | head -n 5
```

#### Si no tienes entorno gráfico, instalar:
```bash
sudo apt update
sudo apt install -y xorg lightdm lxde-core
```

### 2. Configuración de Docker para X11

#### Permitir acceso a X11 desde Docker:
```bash
# Permitir conexiones X11 locales
xhost +local:docker

# O de forma más segura, para un usuario específico:
xhost +local:root
```

#### Hacer permanente la configuración:
Añadir al archivo `~/.bashrc` o `~/.profile`:
```bash
echo "xhost +local:docker" >> ~/.bashrc
```

### 3. Configuración de Auto-login (Opcional)

Para que el kiosko arranque automáticamente:

#### Método 1: Configurar auto-login en lightdm
```bash
sudo nano /etc/lightdm/lightdm.conf
```

Añadir o descomentar:
```ini
[Seat:*]
autologin-user=pi
autologin-user-timeout=0
```

#### Método 2: Configurar auto-login en raspi-config
```bash
sudo raspi-config
# Ir a: 1 System Options > S5 Boot / Auto Login > B4 Desktop Autologin
```

### 4. Configuración de Pantalla

#### Para pantalla táctil oficial de Raspberry Pi:
```bash
# Verificar que está detectada
dmesg | grep -i touch

# Configurar orientación si es necesario
echo 'lcd_rotate=2' | sudo tee -a /boot/config.txt  # 180 grados
# O para 90 grados: lcd_rotate=1
```

#### Para configurar resolución:
```bash
sudo nano /boot/config.txt
```

Añadir o modificar:
```ini
# Para 1920x1080
hdmi_group=2
hdmi_mode=82

# Para 1024x600 (pantalla táctil común)
hdmi_cvt=1024 600 60 6 0 0 0
hdmi_group=2
hdmi_mode=87
```

### 5. Configuración del Servicio Kiosko

#### Crear servicio systemd para auto-arranque:
```bash
sudo nano /etc/systemd/system/puertocho-kiosk.service
```

Contenido:
```ini
[Unit]
Description=PuertoCho Assistant Kiosk
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=oneshot
User=pi
Group=pi
WorkingDirectory=/home/pi/puertocho-assistant-pi
Environment=DISPLAY=:0
Environment=KIOSK_MODE=true
Environment=KIOSK_RESOLUTION=1920x1080
ExecStartPre=/usr/bin/xhost +local:docker
ExecStart=/usr/bin/docker compose up -d
RemainAfterExit=yes
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical-session.target
```

#### Habilitar el servicio:
```bash
sudo systemctl enable puertocho-kiosk.service
sudo systemctl daemon-reload
```

### 6. Configuraciones Adicionales de Rendimiento

#### Configurar GPU split para mejor rendimiento gráfico:
```bash
sudo raspi-config
# Ir a: 7 Advanced Options > A3 Memory Split
# Configurar a 128 o 256 MB para la GPU
```

#### O editando directamente:
```bash
echo 'gpu_mem=128' | sudo tee -a /boot/config.txt
```

#### Deshabilitar screensaver del sistema:
```bash
# Crear archivo de configuración X11
mkdir -p ~/.config/lxsession/LXDE-pi
nano ~/.config/lxsession/LXDE-pi/autostart
```

Contenido:
```bash
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash
@point-rpi
# Deshabilitar screensaver
@xset s off
@xset -dpms
@xset s noblank
```

### 7. Variables de Entorno para el Kiosko

#### Crear archivo de configuración:
```bash
nano ~/puertocho-assistant-pi/.env
```

Contenido:
```bash
# Configuración del Kiosko
KIOSK_MODE=true
KIOSK_RESOLUTION=1920x1080
DISPLAY=:0

# Configuración de la aplicación
DASHBOARD_URL=http://localhost:3000
KIOSK_BROWSER=chromium-browser
KIOSK_RESTART_DELAY=5
```

## 🚀 Script de Instalación Automática

Crear un script para automatizar la configuración:

```bash
nano setup-raspberry-pi.sh && chmod +x setup-raspberry-pi.sh
```

El script incluirá todas estas configuraciones automáticamente.

## ✅ Verificación de la Configuración

### Tests después de la configuración:
```bash
# 1. Verificar X11
DISPLAY=:0 xclock  # Debe aparecer un reloj

# 2. Verificar Docker con X11
docker run --rm -e DISPLAY=:0 -v /tmp/.X11-unix:/tmp/.X11-unix jess/firefox --version

# 3. Verificar el servicio
sudo systemctl status puertocho-kiosk.service

# 4. Test del kiosko
cd ~/puertocho-assistant-pi
KIOSK_MODE=true DISPLAY=:0 docker compose up
```

## 🔧 Solución de Problemas Comunes

### Error: "cannot connect to X server"
```bash
# Verificar que X está corriendo
sudo systemctl status lightdm
# Reiniciar si es necesario
sudo systemctl restart lightdm
```

### Error: "No protocol specified"
```bash
# Dar permisos X11 más amplios (temporalmente)
xhost +
```

### Pantalla en negro o resolución incorrecta:
```bash
# Editar configuración de pantalla
sudo nano /boot/config.txt
# Reiniciar
sudo reboot
```

## 📱 Configuración Específica para Pantalla Táctil

Si usas la pantalla táctil oficial de Raspberry Pi:

```bash
# Instalar drivers si es necesario
sudo apt install -y raspberrypi-ui-mods

# Calibrar pantalla táctil
sudo apt install -y xinput-calibrator
xinput_calibrator
```

## 🔄 Reinicio y Verificación Final

```bash
# Reiniciar para aplicar todos los cambios
sudo reboot

# Después del reinicio, verificar que todo funciona:
systemctl status puertocho-kiosk.service
docker ps
```

El modo kiosko debería arrancar automáticamente y mostrar el dashboard de PuertoCho Assistant en pantalla completa.
