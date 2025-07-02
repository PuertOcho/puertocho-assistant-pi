# 🎤 Asistente de Voz Puertocho con openWakeWord

Asistente de voz inteligente para Raspberry Pi que utiliza openWakeWord para detección de palabras de activación y un servicio de transcripción para ejecutar comandos por voz.

## 🌟 Características

- **🧠 Detección avanzada de wake words** usando openWakeWord
- **🔘 Activación dual**: Por voz ("Alexa", "Hey Mycroft") o botón físico
- **💡 Control GPIO**: LEDs indicadores y botón de activación manual
- **🎙️ Procesamiento de audio en tiempo real** (16kHz, frames de 80ms)
- **🤖 Transcripción de comandos** via servicio REST
- **⚙️ Configuración flexible** por variables de entorno
- **🐳 Despliegue con Docker** listo para producción
- **🧪 Suite completa de tests** unitarios e integración

## 📁 Estructura del Proyecto

```
wake-word-openWakeWord-version/
├── app/
│   ├── main.py              # Aplicación principal
│   ├── commands.json        # Comandos configurables
│   ├── requirements.txt     # Dependencias Python
│   ├── test_simple.py       # Tests unitarios
│   └── test_voice_assistant.py  # Tests avanzados
├── scripts/
│   └── verify_system.py     # Script de verificación del sistema
├── docs/                    # Documentación adicional
├── docker-compose.yml       # Configuración Docker Compose
├── Dockerfile              # Imagen Docker
├── env.example             # Variables de entorno de ejemplo
├── PROJECT_TRACKER.md      # Seguimiento del desarrollo
└── README.md              # Este archivo
```

## 🚀 Instalación Rápida

### Opción 1: Docker (Recomendado)

```bash
# 1. Clonar y configurar
git clone <repo-url>
cd wake-word-openWakeWord-version

# 2. Configurar variables de entorno
cp env.example .env
# Editar .env según necesidades

# 3. Ejecutar con Docker
docker compose up --build
```

### Opción 2: Instalación Nativa

```bash
# 1. Instalar dependencias del sistema (Ubuntu/Debian)
sudo apt update
sudo apt install -y libsndfile1 libasound2-dev libspeexdsp-dev python3-pip

# 2. Instalar dependencias Python
cd app/
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp ../env.example ../.env
# Editar .env según necesidades

# 4. Ejecutar
python main.py
```

## ⚙️ Configuración

### Variables de Entorno

Crear archivo `.env` basado en `env.example`:

```bash
# Servicio de transcripción
TRANSCRIPTION_SERVICE_URL=http://localhost:5000/transcribe

# Configuración GPIO
BUTTON_PIN=22              # Pin del botón de activación
LED_IDLE_PIN=17           # LED verde (listo)
LED_RECORD_PIN=27         # LED rojo (escuchando)

# openWakeWord
OPENWAKEWORD_THRESHOLD=0.4               # Umbral de detección
OPENWAKEWORD_VAD_THRESHOLD=0.0           # Voice Activity Detection
OPENWAKEWORD_ENABLE_SPEEX_NS=false       # Supresión de ruido
OPENWAKEWORD_INFERENCE_FRAMEWORK=onnx    # Motor de inferencia
OPENWAKEWORD_MODEL_PATHS=                # Modelos específicos (vacío = todos)

# Audio
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1
AUDIO_CHUNK_SIZE=1280

# Modo de operación
MODE=HYBRID               # HYBRID | GPIO_ONLY
```

### Comandos Personalizados

Editar `app/commands.json` para añadir comandos:

```json
{
  "enciende luz verde": {"pin": 17, "state": "HIGH"},
  "apaga luz verde": {"pin": 17, "state": "LOW"},
  "enciende luz rojo": {"pin": 27, "state": "HIGH"},
  "apaga luz rojo": {"pin": 27, "state": "LOW"},
  "tu comando aquí": {"pin": 18, "state": "HIGH"}
}
```

## 🎮 Uso

### Activación por Voz

1. **Ejecutar el asistente**:
   ```bash
   python app/main.py
   ```

2. **Decir wake word**:
   - "Alexa"
   - "Hey Mycroft" 
   - "Hey Jarvis"

3. **Dar comando**:
   - "Enciende luz verde"
   - "Apaga luz rojo"
   - Cualquier comando configurado en `commands.json`

### Activación Manual

- **Presionar botón** conectado al GPIO 22
- Hablar comando tras activación

### Indicadores LED

- 🟢 **LED Verde (GPIO 17)**: Sistema listo
- 🔴 **LED Rojo (GPIO 27)**: Escuchando/procesando comando

## 🧪 Testing y Verificación

### Tests Unitarios

```bash
# Tests básicos (sin dependencias)
cd app/
python test_simple.py

# Tests completos (requiere dependencias instaladas)
python test_voice_assistant.py
```

### Verificación del Sistema

```bash
# Verificación completa del sistema
python scripts/verify_system.py
```

Este script verifica:
- ✅ Dependencias del sistema y Python
- ✅ Dispositivos de audio disponibles
- ✅ Acceso a GPIO en Raspberry Pi
- ✅ Modelos de openWakeWord
- ✅ Servicio de transcripción
- ✅ Tests funcionales

## 🔧 Solución de Problemas

### Audio No Funciona

```bash
# Verificar dispositivos de audio
python -c "import sounddevice as sd; print(sd.query_devices())"

# Configurar dispositivo específico en .env
echo "ALSA_CARD=1" >> .env
echo "ALSA_DEVICE=0" >> .env
```

### GPIO No Accesible

```bash
# Añadir usuario al grupo gpio
sudo usermod -a -G gpio $USER

# Verificar permisos
ls -la /dev/gpiomem
```

### openWakeWord No Detecta

```bash
# Verificar modelos descargados
python -c "import openwakeword; openwakeword.utils.download_models()"

# Ajustar umbral en .env
echo "OPENWAKEWORD_THRESHOLD=0.3" >> .env
```

### Servicio de Transcripción

```bash
# Verificar conectividad
curl http://localhost:5000/health

# Cambiar URL en .env
echo "TRANSCRIPTION_SERVICE_URL=http://tu-servidor:5000/transcribe" >> .env
```

## 🐳 Docker

### Variables de Entorno Docker

```yaml
# docker-compose.yml
environment:
  - TRANSCRIPTION_SERVICE_URL=http://host.docker.internal:5000/transcribe
  - OPENWAKEWORD_THRESHOLD=0.4
  - MODE=HYBRID
```

### Permisos Docker

El contenedor necesita acceso privilegiado para:
- **Audio**: `/dev/snd`
- **GPIO**: `/dev/gpiomem`
- **Red**: `host` mode para mejor rendimiento de audio

### Logs

```bash
# Ver logs del contenedor
docker compose logs -f puertocho-assistant

# Debug interactivo
docker compose exec puertocho-assistant bash
```

## 📊 Rendimiento

### Requisitos Mínimos

- **Raspberry Pi 3B+** o superior
- **1GB RAM** disponible
- **CPU**: 20-30% para procesamiento de audio
- **Audio**: Micrófono USB o HAT compatible

### Optimización

1. **Usar ONNX** como framework de inferencia (por defecto)
2. **Ajustar chunk size** según CPU disponible
3. **Habilitar Speex NS** solo si hay mucho ruido
4. **Monitorear VAD threshold** para evitar falsos positivos

## 🔄 Estados del Sistema

| Estado | LED Verde | LED Rojo | Descripción |
|--------|-----------|----------|-------------|
| **IDLE** | 🟢 ON | ⚫ OFF | Listo para wake word |
| **LISTENING** | ⚫ OFF | 🔴 ON | Grabando comando |
| **PROCESSING** | ⚫ OFF | 🔴 Parpadeo | Enviando a transcripción |

## 🛣️ Roadmap

### ✅ Completado (Fases 1-3)
- Integración openWakeWord
- Control GPIO y LEDs
- Pipeline completo de comandos
- Tests y validación

### 🔄 En Desarrollo (Fase 4)
- Optimización de rendimiento
- Métricas de latencia y CPU
- Configuración avanzada de parámetros

### 🔮 Futuro (Fases 5-7)
- Modelo personalizado "Puertocho"
- Validación exhaustiva (FAR/FRR)
- Soporte multi-idioma
- Integración con servicios cloud

## 🤝 Contribuir

1. **Fork** del repositorio
2. **Crear rama** para nueva característica
3. **Añadir tests** para funcionalidad nueva
4. **Ejecutar verificación**: `python scripts/verify_system.py`
5. **Enviar Pull Request**

### Estructura de Commits

```
tipo(scope): descripción

feat(audio): añadir soporte para VAD
fix(gpio): corregir configuración de LEDs
test(core): añadir tests para comandos
docs(readme): actualizar instalación
```

## 📄 Licencia

Este proyecto está bajo licencia MIT. Ver archivo `LICENSE` para detalles.

## 🆘 Soporte

### Issues Comunes

- **Audio crackling**: Reducir `AUDIO_CHUNK_SIZE` a 640
- **Alta latencia**: Usar `MODE=GPIO_ONLY` temporalmente
- **False positives**: Aumentar `OPENWAKEWORD_THRESHOLD`
- **No detecta susurros**: Reducir `OPENWAKEWORD_VAD_THRESHOLD`

### Contacto

- 📧 **Issues**: [GitHub Issues](link-to-issues)
- 📚 **Docs**: Ver `docs/` para documentación técnica
- 🔧 **Debug**: Ejecutar `scripts/verify_system.py`

---

## 🙏 Agradecimientos

- **openWakeWord**: Por el excelente framework de detección
- **Raspberry Pi Foundation**: Por el hardware increíble
- **Comunidad OpenSource**: Por las librerías utilizadas

---

⭐ **Si este proyecto te resulta útil, ¡dale una estrella!** ⭐
