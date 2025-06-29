# 🎤 WORKFLOW: CURSOR + REMOTE-SSH + ASISTENTE PUERTOCHO

**Fecha:** 29 de Junio 2025  
**IDE:** Cursor con Remote-SSH  
**Proyecto:** Asistente de Voz Puertocho (openWakeWord)

---

## 🚀 CONFIGURACIÓN INICIAL

### **1. Ejecutar script de configuración:**
```bash
./setup_remote_ssh.sh
```

### **2. En Cursor:**
1. `Ctrl+Shift+P` → `Remote-SSH: Connect to Host`
2. Seleccionar `pi-puertocho` o `puertochopi.local`
3. Abrir carpeta: `/home/puertocho/puertocho-assistant-pi`

---

## 💻 WORKFLOW DE DESARROLLO

### **🔧 Configuración del entorno (primera vez):**
```bash
# En el terminal integrado de Cursor (conectado a la Pi):
cd /home/puertocho/puertocho-assistant-pi/wake-word-openWakeWord-version

# Instalar dependencias
python3 instalar_asistente.py

# Verificar configuración
python3 verificar_configuracion.py
```

### **⚙️ Configuración personalizada:**
```bash
# Editar variables de entorno
cp env.example .env
# Editar .env con las configuraciones específicas
```

### **🎯 Desarrollo típico:**

#### **A. Editando código Python:**
- `app/main.py` - Lógica principal del asistente
- `app/commands.json` - Comandos de voz
- Editas directamente en Cursor, cambios se aplican instantáneamente

#### **B. Testing en tiempo real:**
```bash
# Terminal integrado en Cursor:
python3 ejecutar_asistente.py

# O con Docker:
docker-compose up --build

# Ver logs en tiempo real:
docker-compose logs -f
```

#### **C. Debugging:**
- Breakpoints en Python funcionan directamente
- Variables de entorno se ven en tiempo real
- Output del GPIO/audio visible inmediatamente

---

## 🎤 COMANDOS ESPECÍFICOS PARA EL ASISTENTE

### **Testing del wake word:**
```bash
# Probar detección con diferentes umbrales
export OPENWAKEWORD_THRESHOLD=0.3  # Más sensible
python3 app/main.py

# Verificar modelos disponibles
python3 -c "import openwakeword; print(openwakeword.utils.get_pretrained_model_paths())"
```

### **Ajustes de audio:**
```bash
# Verificar dispositivos de audio
python3 -c "import sounddevice as sd; print(sd.query_devices())"

# Probar captura de audio
python3 -c "
import sounddevice as sd
import numpy as np
print('Grabando 3 segundos...')
audio = sd.rec(int(3 * 16000), samplerate=16000, channels=1)
sd.wait()
print(f'Audio capturado: {audio.shape}, Max: {np.max(np.abs(audio))}')
"
```

### **Control de GPIO:**
```bash
# Probar LEDs directamente
python3 -c "
import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)  # LED verde
GPIO.output(17, GPIO.HIGH)
time.sleep(1)
GPIO.output(17, GPIO.LOW)
GPIO.cleanup()
print('LED test completado')
"
```

---

## 📋 COMANDOS DE VOZ PARA TESTING

Después de activar con **"Alexa"** o **"Hey Mycroft"**:

### **Comandos LED:**
- "enciende luz verde" / "enciende led verde"
- "apaga luz verde" / "apaga led verde"  
- "enciende luz rojo" / "enciende led rojo"
- "apaga luz rojo" / "apaga led rojo"

### **Verificar reconocimiento:**
```bash
# Monitorear logs para ver transcripciones
tail -f /var/log/syslog | grep "Transcripción"
```

---

## 🔧 TROUBLESHOOTING REMOTO

### **Problema: Conexión SSH perdida**
```bash
# Desde Ubuntu - reconectar
ssh pi-puertocho
# O directamente:
ssh puertocho@puertochopi.local

# En Cursor: Ctrl+Shift+P → "Remote-SSH: Reload Window"
```

### **Problema: Permisos GPIO**
```bash
# En la Pi:
sudo usermod -a -G gpio puertocho
# Reiniciar sesión SSH
```

### **Problema: openWakeWord no responde**
```bash
# Verificar procesos
ps aux | grep python
pkill -f "python.*main.py"

# Reiniciar con debug
OPENWAKEWORD_THRESHOLD=0.3 python3 app/main.py --debug
```

### **Problema: Audio no funciona**
```bash
# Verificar ALSA
arecord -l
aplay -l

# Test de micrófono
arecord -d 3 -f cd test.wav && aplay test.wav
```

---

## 🚀 OPTIMIZACIONES PARA DESARROLLO

### **1. Auto-restart del servicio:**
```bash
# Crear script de auto-restart
cat > restart_assistant.sh << 'EOF'
#!/bin/bash
while true; do
    python3 app/main.py
    echo "Asistente crasheó, reiniciando en 2 segundos..."
    sleep 2
done
EOF
chmod +x restart_assistant.sh
```

### **2. Sincronización de código:**
```bash
# Desde Ubuntu (si trabajas offline ocasionalmente):
rsync -av --exclude='.git' ./ puertocho@puertochopi.local:/home/puertocho/puertocho-assistant-pi/
```

### **3. Backup automático:**
```bash
# En la Pi - crontab -e:
0 2 * * * cd /home/puertocho/puertocho-assistant-pi && git add . && git commit -m "auto: $(date)" && git push
```

---

## 📊 MÉTRICAS DE DESARROLLO

### **Latencia típica:**
- Wake word detection: ~100-200ms
- Voice command processing: ~500ms-2s
- GPIO response: <10ms

### **Uso de recursos:**
```bash
# Monitorear CPU/RAM
htop

# Específico para Python
ps aux | grep python | awk '{print $3, $4, $11}'
```

---

## 🎯 PRÓXIMOS DESARROLLOS

Con este setup puedes trabajar fácilmente en:

1. **Nuevos comandos de voz** - Editar `commands.json`
2. **Mejoras de wake word** - Ajustar parámetros en `.env`
3. **Integración con IA** - Usar Cursor AI mientras desarrollas
4. **Modelo personalizado** - Preparación para Fase 5
5. **Testing A/B** - Probar diferentes configuraciones rápidamente

---

## ✅ VENTAJAS DE ESTE WORKFLOW

- ✅ **Edición nativa**: Como si fuera local
- ✅ **AI integrado**: Cursor AI funciona remotamente  
- ✅ **Testing inmediato**: Cambios se aplican al instante
- ✅ **Hardware real**: GPIO, audio, sensores funcionan
- ✅ **Git nativo**: Control de versiones desde la Pi
- ✅ **Terminal integrado**: Comandos directos en la Pi
- ✅ **Debugging completo**: Breakpoints, variables, logs

**¡Perfecto para desarrollar tu Asistente de Voz! 🎤🚀** 