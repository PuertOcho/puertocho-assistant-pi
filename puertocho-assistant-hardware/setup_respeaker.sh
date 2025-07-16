#!/bin/bash
# Script de instalación rápida para ReSpeaker 2-Mic Pi HAT V1.0

echo "🚀 Configurando ReSpeaker 2-Mic Pi HAT V1.0..."

# Actualizar sistema
echo "📦 Actualizando sistema..."
sudo apt update
sudo apt upgrade -y

# Instalar dependencias de audio
echo "🔊 Instalando dependencias de audio..."
sudo apt install -y alsa-utils pulseaudio pulseaudio-utils
sudo apt install -y libasound2-plugins

# Instalar Python y dependencias
echo "🐍 Instalando Python y dependencias..."
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y python3-spidev python3-rpi.gpio

# Crear entorno virtual
echo "🔧 Creando entorno virtual..."
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias Python
echo "📚 Instalando dependencias Python..."
pip install --upgrade pip
pip install requests numpy pvporcupine pyaudio

# Configurar audio
echo "🎤 Configurando audio..."
# Crear archivo de configuración ALSA
sudo tee /home/pi/.asoundrc << EOF
pcm.!default {
    type plug
    slave.pcm "hw:1,0"
}

ctl.!default {
    type hw
    card 1
}
EOF

# Verificar dispositivos de audio
echo "🔍 Verificando dispositivos de audio..."
aplay -l | grep -i respeaker

# Hacer script ejecutable
chmod +x test_leds.py

echo "✅ Instalación completada"
echo ""
echo "🎮 Para probar los LEDs:"
echo "   ./test_leds.py --test states"
echo ""
echo "🎤 Para probar audio:"
echo "   arecord -D hw:1,0 -f S16_LE -r 44100 -c 2 -d 5 test.wav"
echo "   aplay -D hw:1,0 test.wav"
echo ""
echo "🔧 Para activar el entorno virtual:"
echo "   source venv/bin/activate"
