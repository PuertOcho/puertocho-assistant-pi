#!/bin/bash
# 🧠 Configurar entorno de entrenamiento para modelo "Puertocho"
# Ejecutar DENTRO de la instancia Google Cloud T4

set -e

echo "🧠 Configurando entorno de entrenamiento 'Puertocho'"
echo "=================================================="

# Verificar que estamos en la instancia correcta
if ! nvidia-smi &> /dev/null; then
    echo "❌ ERROR: No se detecta GPU NVIDIA"
    echo "💡 Asegúrate de estar en la instancia Cloud con GPU T4"
    exit 1
fi

# Mostrar información de GPU
echo "🎮 GPU detectada:"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits

# 1. Actualizar sistema
echo "🔄 Actualizando sistema..."
sudo apt-get update -y
sudo apt-get upgrade -y

# 2. Instalar dependencias del sistema
echo "📦 Instalando dependencias del sistema..."
sudo apt-get install -y \
    wget \
    curl \
    git \
    unzip \
    htop \
    tree \
    vim \
    tmux \
    ffmpeg \
    sox \
    libsox-fmt-all \
    espeak \
    espeak-data \
    libespeak1 \
    libespeak-dev \
    festival \
    festvox-kallpc16k

# 3. Verificar Python y pip
echo "🐍 Verificando Python..."
python3 --version
pip3 --version

# 4. Actualizar pip
echo "📦 Actualizando pip..."
pip3 install --upgrade pip setuptools wheel

# 5. Instalar PyTorch con soporte CUDA
echo "🔥 Instalando PyTorch con CUDA..."
pip3 install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# 6. Verificar instalación de PyTorch
echo "🔍 Verificando PyTorch + CUDA..."
python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA disponible: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"No disponible\"}')"

# 7. Instalar openWakeWord con dependencias de entrenamiento
echo "🎯 Instalando openWakeWord..."
pip3 install openwakeword[train]

# 8. Instalar dependencias adicionales para entrenamiento
echo "📦 Instalando dependencias de entrenamiento..."
pip3 install \
    numpy==1.24.3 \
    scipy \
    librosa \
    soundfile \
    matplotlib \
    seaborn \
    pandas \
    jupyter \
    jupyterlab \
    wandb \
    tqdm \
    pyyaml \
    tensorboard \
    sklearn \
    onnx \
    onnxruntime \
    pydub \
    webrtcvad \
    speechrecognition \
    pyttsx3 \
    gTTS \
    requests

# 9. Instalar TTS en español
echo "🗣️ Configurando TTS en español..."
# Configurar Festival con voces en español
sudo apt-get install -y festvox-ellpc11k

# 10. Crear estructura de directorios
echo "📁 Creando estructura de directorios..."
mkdir -p ~/puertocho-training/{data,models,logs,scripts,configs,results}
mkdir -p ~/puertocho-training/data/{positive,negative,validation}

# 11. Configurar Jupyter Lab
echo "🔬 Configurando Jupyter Lab..."
jupyter lab --generate-config

# Configurar Jupyter para acceso remoto
cat >> ~/.jupyter/jupyter_lab_config.py << EOF
c.ServerApp.ip = '0.0.0.0'
c.ServerApp.port = 8080
c.ServerApp.open_browser = False
c.ServerApp.allow_remote_access = True
c.ServerApp.token = ''
c.ServerApp.password = ''
EOF

# 12. Configurar variables de entorno
echo "🔧 Configurando variables de entorno..."
cat >> ~/.bashrc << EOF

# Configuración para entrenamiento Puertocho
export CUDA_VISIBLE_DEVICES=0
export PYTHONPATH=\$PYTHONPATH:~/puertocho-training
export OMP_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false

# Aliases útiles
alias gpu='nvidia-smi'
alias logs='tail -f ~/puertocho-training/logs/training.log'
alias tb='tensorboard --logdir ~/puertocho-training/logs --host 0.0.0.0 --port 6006'

EOF

# 13. Crear script de inicio rápido
echo "🚀 Creando script de inicio rápido..."
cat > ~/start_training.sh << 'EOF'
#!/bin/bash
echo "🧠 Iniciando entorno de entrenamiento Puertocho"
echo "================================================"

# Activar entorno
source ~/.bashrc

# Mostrar información del sistema
echo "💻 Sistema:"
echo "   CPU: $(nproc) cores"
echo "   RAM: $(free -h | awk '/^Mem:/ {print $2}')"
echo "   GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader)"
echo "   CUDA: $(python3 -c 'import torch; print(torch.version.cuda)')"
echo ""

# Cambiar al directorio de trabajo
cd ~/puertocho-training

echo "🔗 Enlaces útiles:"
echo "   Jupyter Lab: http://$(curl -s ifconfig.me):8080"
echo "   TensorBoard: http://$(curl -s ifconfig.me):6006"
echo ""

echo "✅ Entorno listo para entrenar modelo 'Puertocho'"
EOF

chmod +x ~/start_training.sh

# 14. Crear script de monitoreo
cat > ~/monitor_training.sh << 'EOF'
#!/bin/bash
# Monitor continuo del entrenamiento

while true; do
    clear
    echo "🔍 Monitor de Entrenamiento - $(date)"
    echo "================================================"
    
    # GPU
    echo "🎮 GPU:"
    nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits | \
    awk -F, '{printf "   Uso: %s%% | RAM: %s/%s MB | Temp: %s°C\n", $1, $2, $3, $4}'
    
    # CPU y RAM
    echo ""
    echo "💻 Sistema:"
    echo "   CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)% | RAM: $(free | awk '/Mem:/ {printf "%.1f%%", $3/$2 * 100.0}')"
    
    # Procesos de entrenamiento
    echo ""
    echo "🧠 Procesos Python:"
    ps aux | grep python | grep -v grep | awk '{print "   PID:"$2" CPU:"$3"% RAM:"$4"% "$11$12$13}'
    
    sleep 5
done
EOF

chmod +x ~/monitor_training.sh

# 15. Abrir puertos en firewall (si es necesario)
echo "🔓 Configurando firewall..."
sudo ufw allow 8080  # Jupyter
sudo ufw allow 6006  # TensorBoard

echo ""
echo "✅ Entorno de entrenamiento configurado correctamente!"
echo "=================================================="
echo "🚀 Para comenzar:"
echo "   bash ~/start_training.sh"
echo ""
echo "🔗 Servicios:"
echo "   Jupyter Lab: http://$(curl -s ifconfig.me):8080"
echo "   TensorBoard: http://$(curl -s ifconfig.me):6006"
echo ""
echo "📊 Monitoreo:"
echo "   bash ~/monitor_training.sh"
echo ""
echo "💡 Próximo paso: Subir scripts de entrenamiento y datos" 