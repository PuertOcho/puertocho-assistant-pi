# Epic 4 – Integración Backend Local ↔ Backend Remoto y Reproducción de Audio

## 📋 Objetivo
Implementar la comunicación completa entre Backend Local y Backend Remoto para procesamiento de audio con IA/LLM, y habilitar la reproducción de respuestas de audio en el hardware.

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐     HTTP/WS    ┌─────────────────┐     HTTP/Auth   ┌─────────────────┐
│   HARDWARE      │◄──────────────►│  BACKEND LOCAL  │◄───────────────►│ BACKEND REMOTO  │
│ (Puerto 8080)   │                │ (Puerto 8000)   │                 │ (Puerto 10002)  │
│ - Captura audio │                │ - Orquestador   │                 │ - Procesamiento │
│ - Reproduce     │                │ - Auth Manager  │                 │ - IA/LLM        │
│   respuestas    │                │ - Client HTTP   │                 │ - TTS/STT       │
└─────────────────┘                └─────────────────┘                 └─────────────────┘
```

## 🔐 Credenciales Backend Remoto
- **URL**: `http://192.168.1.88:10002`
- **Email**: `service@puertocho.local`
- **Password**: `servicepass123`
- **Endpoint Conversacional**: `/api/v1/conversation/process/audio`

---

## 📦 Paso 1: Preparación del Entorno

### 1.1 Verificar Estado Actual
```bash
# Verificar que el sistema actual funciona
cd /home/puertocho/puertocho-assistant-pi
docker-compose ps
docker-compose logs --tail=20 backend hardware

# Verificar estructura de directorios
ls -la puertocho-assistant-backend/src/
ls -la puertocho-assistant-backend/src/services/
ls -la puertocho-assistant-backend/src/clients/
ls -la puertocho-assistant-hardware/src/
```

### 1.2 Crear Backup
```bash
# Crear backup completo antes de cambios
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
cp -r puertocho-assistant-backend/src $BACKUP_DIR/backend_src
cp -r puertocho-assistant-hardware/src $BACKUP_DIR/hardware_src
cp .env $BACKUP_DIR/.env.backup
cp docker-compose.yml $BACKUP_DIR/docker-compose.yml.backup
echo "✅ Backup creado en: $BACKUP_DIR"
```

### 1.3 Crear Directorios Necesarios
```bash
# Crear estructura de directorios si no existe
mkdir -p puertocho-assistant-backend/src/clients
mkdir -p puertocho-assistant-backend/src/services
mkdir -p puertocho-assistant-backend/audio_verification
mkdir -p logs
```

---

## 📝 Paso 2: Configuración de Variables de Entorno

### 2.1 Actualizar archivo .env
```bash
# Añadir al final del archivo .env existente
cat >> .env << 'EOF'

# ============================================
# EPIC 4 - INTEGRACIÓN BACKEND REMOTO
# ============================================

# Control de Features (IMPORTANTE: Empezar con false)
USE_REMOTE_BACKEND=false
USE_REMOTE_AUDIO_PROCESSOR=false

# Backend Remoto - Configuración
REMOTE_BACKEND_URL=http://192.168.1.88:10002
REMOTE_BACKEND_EMAIL=service@puertocho.local
REMOTE_BACKEND_PASSWORD=servicepass123
REMOTE_BACKEND_TIMEOUT=60.0
REMOTE_BACKEND_RETRY_ATTEMPTS=3
REMOTE_BACKEND_RETRY_DELAY=2.0

# Configuración Conversacional
REMOTE_BACKEND_CONVERSATION_PATH=/api/v1/conversation/process/audio
REMOTE_BACKEND_LANGUAGE=es
REMOTE_BACKEND_API_MODE=conversation
CONVERSATION_DEFAULT_USER_ID=service@puertocho.local
CONVERSATION_SESSION_STRATEGY=sticky-per-device
DEVICE_ID=puertocho-rpi-01

# Audio Verification
AUDIO_VERIFICATION_ENABLED=true
AUDIO_VERIFICATION_DAYS=7
AUDIO_VERIFICATION_MAX_FILES=100

# Audio Output Configuration
AUDIO_OUTPUT_DEVICE_INDEX=0
AUDIO_OUTPUT_SAMPLE_RATE=44100
EOF

echo "✅ Variables de entorno añadidas a .env"
```

### 2.2 Actualizar docker-compose.yml
```yaml
# Buscar la sección del servicio 'backend' y añadir estas variables de entorno
# NO reemplazar el archivo completo, solo añadir las variables

  backend:
    # ...configuración existente...
    environment:
      # ...variables existentes...
      
      # Epic 4 - Control de Features
      - USE_REMOTE_BACKEND=${USE_REMOTE_BACKEND:-false}
      - USE_REMOTE_AUDIO_PROCESSOR=${USE_REMOTE_AUDIO_PROCESSOR:-false}
      
      # Epic 4 - Remote Backend Configuration
      - REMOTE_BACKEND_URL=${REMOTE_BACKEND_URL:-http://192.168.1.88:10002}
      - REMOTE_BACKEND_EMAIL=${REMOTE_BACKEND_EMAIL:-service@puertocho.local}
      - REMOTE_BACKEND_PASSWORD=${REMOTE_BACKEND_PASSWORD:-servicepass123}
      - REMOTE_BACKEND_TIMEOUT=${REMOTE_BACKEND_TIMEOUT:-60.0}
      - REMOTE_BACKEND_RETRY_ATTEMPTS=${REMOTE_BACKEND_RETRY_ATTEMPTS:-3}
      - REMOTE_BACKEND_RETRY_DELAY=${REMOTE_BACKEND_RETRY_DELAY:-2.0}
      
      # Epic 4 - Conversation Configuration
      - REMOTE_BACKEND_CONVERSATION_PATH=${REMOTE_BACKEND_CONVERSATION_PATH:-/api/v1/conversation/process/audio}
      - REMOTE_BACKEND_LANGUAGE=${REMOTE_BACKEND_LANGUAGE:-es}
      - REMOTE_BACKEND_API_MODE=${REMOTE_BACKEND_API_MODE:-conversation}
      - CONVERSATION_DEFAULT_USER_ID=${CONVERSATION_DEFAULT_USER_ID:-service@puertocho.local}
      - CONVERSATION_SESSION_STRATEGY=${CONVERSATION_SESSION_STRATEGY:-sticky-per-device}
      - DEVICE_ID=${DEVICE_ID:-puertocho-rpi-01}
      
      # Epic 4 - Audio Verification
      - AUDIO_VERIFICATION_ENABLED=${AUDIO_VERIFICATION_ENABLED:-true}
      - AUDIO_VERIFICATION_DAYS=${AUDIO_VERIFICATION_DAYS:-7}
      - AUDIO_VERIFICATION_MAX_FILES=${AUDIO_VERIFICATION_MAX_FILES:-100}
    
    volumes:
      # ...volúmenes existentes...
      - ./puertocho-assistant-backend/audio_verification:/app/audio_verification
      - ./logs:/app/logs

  hardware:
    # ...configuración existente...
    environment:
      # ...variables existentes...
      
      # Epic 4 - Audio Output Configuration
      - AUDIO_OUTPUT_DEVICE_INDEX=${AUDIO_OUTPUT_DEVICE_INDEX:-0}
      - AUDIO_OUTPUT_SAMPLE_RATE=${AUDIO_OUTPUT_SAMPLE_RATE:-44100}
```

---

## 💻 Paso 3: Implementación del Cliente de Backend Remoto

### 3.1 Crear remote_backend_client.py
```bash
# Crear el archivo del cliente remoto
cat > puertocho-assistant-backend/src/clients/remote_backend_client.py << 'EOF'
# Copiar aquí el contenido COMPLETO del archivo remote_backend_client.py proporcionado
# Este es un archivo NUEVO, no reemplaza nada existente
EOF
```

### 3.2 Verificar la creación
```bash
# Verificar que el archivo se creó correctamente
ls -la puertocho-assistant-backend/src/clients/remote_backend_client.py
head -20 puertocho-assistant-backend/src/clients/remote_backend_client.py
```

---

## 🎙️ Paso 4: Implementación del Procesador de Audio

### 4.1 Verificar si existe un procesador actual
```bash
# Buscar referencias a procesamiento de audio existente
find puertocho-assistant-backend/src -name "*audio*processor*.py" 2>/dev/null
grep -r "AudioProcessor" puertocho-assistant-backend/src/ --include="*.py" 2>/dev/null || echo "No se encontró AudioProcessor existente"
```

### 4.2 Crear audio_processor.py
```bash
# Si NO existe un procesador de audio, crear uno nuevo
cat > puertocho-assistant-backend/src/services/audio_processor.py << 'EOF'
# Copiar aquí el contenido COMPLETO del archivo audio_processor.py proporcionado
EOF
```

### 4.3 Si ya existe un procesador, crear uno paralelo
```bash
# Si YA existe, crear remote_audio_processor.py para no colisionar
# Cambiar el nombre de la clase a RemoteAudioProcessor
cat > puertocho-assistant-backend/src/services/remote_audio_processor.py << 'EOF'
# Copiar el contenido de audio_processor.py pero:
# 1. Renombrar class AudioProcessor a class RemoteAudioProcessor
# 2. Ajustar las funciones globales para usar el nuevo nombre
EOF
```

---

## 🔌 Paso 5: Integración con el Sistema Existente

### 5.1 Actualizar main.py con inicialización condicional
```python
# puertocho-assistant-backend/src/main.py
# AÑADIR estas importaciones al inicio (si no existen)
import os
from typing import Optional

# BUSCAR la función startup_event() y AÑADIR este código AL FINAL de la función
@app.on_event("startup")
async def startup_event():
    # ...código existente NO MODIFICAR...
    
    # === INICIO INTEGRACIÓN EPIC 4 ===
    logger.info("🔄 Checking Epic 4 remote backend configuration...")
    
    # Verificar si debemos usar el backend remoto
    use_remote_backend = os.getenv("USE_REMOTE_BACKEND", "false").lower() == "true"
    use_audio_processor = os.getenv("USE_REMOTE_AUDIO_PROCESSOR", "false").lower() == "true"
    
    logger.info(f"📋 Epic 4 Configuration: USE_REMOTE_BACKEND={use_remote_backend}, USE_REMOTE_AUDIO_PROCESSOR={use_audio_processor}")
    
    if use_remote_backend:
        try:
            from clients.remote_backend_client import init_remote_client
            await init_remote_client()
            logger.info("✅ Remote Backend Client initialized successfully")
        except ImportError as e:
            logger.error(f"❌ Remote Backend Client not found: {e}")
            logger.warning("⚠️ Continuing without remote backend support")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Remote Backend Client: {e}")
            logger.warning("⚠️ System will run in offline mode")
    
    if use_audio_processor:
        try:
            from services.audio_processor import init_audio_processor
            # Obtener websocket_manager si existe
            ws_manager = globals().get('websocket_manager', None)
            audio_processor = init_audio_processor(ws_manager)
            await audio_processor.start()
            logger.info("✅ Audio Processor initialized successfully")
        except ImportError as e:
            logger.error(f"❌ Audio Processor not found: {e}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Audio Processor: {e}")
    # === FIN INTEGRACIÓN EPIC 4 ===

# BUSCAR la función shutdown_event() y AÑADIR este código AL FINAL
@app.on_event("shutdown")
async def shutdown_event():
    # ...código existente NO MODIFICAR...
    
    # === INICIO CLEANUP EPIC 4 ===
    logger.info("🔄 Cleaning up Epic 4 components...")
    
    # Cerrar Audio Processor si está activo
    try:
        from services.audio_processor import close_audio_processor
        await close_audio_processor()
        logger.info("✅ Audio Processor closed")
    except ImportError:
        pass  # No estaba importado
    except Exception as e:
        logger.warning(f"⚠️ Error closing Audio Processor: {e}")
    
    # Cerrar Remote Backend Client si está activo
    try:
        from clients.remote_backend_client import close_remote_client
        await close_remote_client()
        logger.info("✅ Remote Backend Client closed")
    except ImportError:
        pass  # No estaba importado
    except Exception as e:
        logger.warning(f"⚠️ Error closing Remote Backend Client: {e}")
    # === FIN CLEANUP EPIC 4 ===
```

### 5.2 Actualizar gateway_endpoints.py
```python
# puertocho-assistant-backend/src/api/v1/gateway_endpoints.py
# MODIFICAR el endpoint /hardware/audio existente

# AÑADIR imports al inicio del archivo (si no existen)
import os
from datetime import datetime

# BUSCAR el endpoint @router.post("/hardware/audio") y MODIFICAR
@router.post("/hardware/audio")
async def receive_hardware_audio(request: Request):
    """Recibir audio desde el hardware para procesamiento"""
    try:
        # ...código existente de validación y procesamiento inicial...
        # NO BORRAR el código existente
        
        # === INICIO INTEGRACIÓN EPIC 4 ===
        # Verificar si debemos usar el procesador remoto
        use_remote_processor = os.getenv("USE_REMOTE_AUDIO_PROCESSOR", "false").lower() == "true"
        
        if use_remote_processor:
            logger.info("🔄 Epic 4: Using remote audio processor")
            try:
                from services.audio_processor import get_audio_processor
                processor = get_audio_processor()
                
                # Preparar información para el procesador
                audio_info = {
                    "filename": filename if 'filename' in locals() else "audio.wav",
                    "received_at": datetime.now().isoformat(),
                    "audio_metrics": audio_metrics if 'audio_metrics' in locals() else {}
                }
                
                # Procesar con el sistema remoto
                logger.info(f"📡 Sending audio to remote processor: {audio_info['filename']}")
                result = await processor.process_audio_from_hardware(audio_info)
                
                if result.get("success"):
                    logger.info(f"✅ Remote processing successful: {result.get('audio_id')}")
                    return result
                else:
                    logger.warning(f"⚠️ Remote processing failed: {result.get('error')}")
                    logger.info("📍 Falling back to local processing")
                    
            except ImportError as e:
                logger.debug(f"Remote audio processor not available: {e}")
            except Exception as e:
                logger.error(f"❌ Error in remote audio processor: {e}")
                logger.info("📍 Falling back to local processing")
        # === FIN INTEGRACIÓN EPIC 4 ===
        
        # ...resto del código existente para procesamiento local...
        # MANTENER todo el código actual aquí
        
    except Exception as e:
        # ...manejo de errores existente...
```

---

## 🔊 Paso 6: Implementación de Reproducción de Audio en Hardware

### 6.1 Verificar dispositivos de audio disponibles
```bash
# Crear script de verificación
cat > check_audio_devices.sh << 'EOF'
#!/bin/bash
echo "🔊 Verificando dispositivos de audio"
echo "===================================="

# En el host
echo -e "\n📍 Dispositivos en el HOST:"
echo "Salida:"
aplay -l 2>/dev/null || echo "aplay no disponible"
echo -e "\nCaptura:"
arecord -l 2>/dev/null || echo "arecord no disponible"

# En el contenedor de hardware
echo -e "\n📍 Dispositivos en CONTENEDOR hardware:"
docker exec puertocho-hardware python3 -c "
import sounddevice as sd
print('\\nDispositivos de entrada:')
for i, dev in enumerate(sd.query_devices()):
    if dev['max_input_channels'] > 0:
        print(f'  [{i}] {dev[\"name\"]} - {dev[\"max_input_channels\"]} ch')
print('\\nDispositivos de salida:')
for i, dev in enumerate(sd.query_devices()):
    if dev['max_output_channels'] > 0:
        print(f'  [{i}] {dev[\"name\"]} - {dev[\"max_output_channels\"]} ch')
print(f'\\nDispositivo por defecto: {sd.default.device}')
" 2>/dev/null || echo "Error verificando dispositivos en contenedor"
EOF

chmod +x check_audio_devices.sh
./check_audio_devices.sh
```

### 6.2 Actualizar audio_manager.py en Hardware
```python
# puertocho-assistant-hardware/src/audio_manager.py
# AÑADIR este método a la clase AudioManager existente

import sounddevice as sd
import numpy as np
import base64

class AudioManager:
    # ...código existente...
    
    def __init__(self):
        # ...código existente de __init__...
        
        # Añadir configuración de dispositivo de salida
        self.output_device_index = int(os.getenv("AUDIO_OUTPUT_DEVICE_INDEX", "0"))
        self.output_sample_rate = int(os.getenv("AUDIO_OUTPUT_SAMPLE_RATE", "44100"))
        
        # Verificar dispositivo de salida
        try:
            devices = sd.query_devices()
            if self.output_device_index < len(devices):
                output_dev = devices[self.output_device_index]
                if output_dev['max_output_channels'] > 0:
                    logger.info(f"🔊 Output device configured: [{self.output_device_index}] {output_dev['name']}")
                else:
                    logger.warning(f"⚠️ Device {self.output_device_index} has no output channels, using default")
                    self.output_device_index = None
            else:
                logger.warning(f"⚠️ Output device index {self.output_device_index} not found, using default")
                self.output_device_index = None
        except Exception as e:
            logger.error(f"❌ Error configuring output device: {e}")
            self.output_device_index = None
    
    async def play_audio_array(self, audio_array: np.ndarray, sample_rate: int = None) -> bool:
        """
        Reproducir un array de audio numpy
        
        Args:
            audio_array: Audio data as numpy array
            sample_rate: Sample rate for playback (usa default si no se especifica)
            
        Returns:
            True if playback successful
        """
        try:
            if sample_rate is None:
                sample_rate = self.output_sample_rate
            
            # Log información del audio
            duration = len(audio_array) / sample_rate
            logger.info(f"🎵 Playing audio: {duration:.2f} seconds @ {sample_rate}Hz")
            
            # Normalizar audio según el tipo de datos
            if audio_array.dtype == np.int16:
                # Convertir int16 a float32 normalizado
                audio_float = audio_array.astype(np.float32) / 32768.0
            elif audio_array.dtype == np.float64:
                # Convertir float64 a float32
                audio_float = audio_array.astype(np.float32)
            elif audio_array.dtype == np.float32:
                audio_float = audio_array
            else:
                # Intentar conversión genérica
                audio_float = audio_array.astype(np.float32)
            
            # Asegurar que está en el rango [-1, 1]
            max_val = np.abs(audio_float).max()
            if max_val > 1.0:
                logger.warning(f"⚠️ Audio clipping detected (max={max_val:.2f}), normalizing...")
                audio_float = audio_float / max_val
            
            # Reproducir audio
            device = self.output_device_index if self.output_device_index is not None else None
            
            logger.debug(f"🔊 Using device: {device}")
            sd.play(audio_float, samplerate=sample_rate, device=device)
            
            # Esperar a que termine la reproducción
            sd.wait()
            
            logger.info(f"✅ Audio playback completed successfully")
            return True
            
        except sd.PortAudioError as e:
            logger.error(f"❌ PortAudio error playing audio: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error playing audio: {e}")
            return False
    
    async def play_audio_base64(self, audio_base64: str, sample_rate: int = None) -> bool:
        """
        Reproducir audio desde string Base64
        
        Args:
            audio_base64: Audio en formato Base64
            sample_rate: Sample rate (opcional)
            
        Returns:
            True si la reproducción fue exitosa
        """
        try:
            # Decodificar Base64
            audio_bytes = base64.b64decode(audio_base64)
            
            # Convertir bytes a numpy array (asumiendo PCM 16-bit)
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # Reproducir
            return await self.play_audio_array(audio_array, sample_rate)
            
        except Exception as e:
            logger.error(f"❌ Error decoding/playing base64 audio: {e}")
            return False
```

### 6.3 Añadir endpoint de reproducción en Hardware
```python
# puertocho-assistant-hardware/src/http_server.py
# AÑADIR este nuevo endpoint

from fastapi import Request
from fastapi.responses import JSONResponse
import base64

@app.post("/audio/play")
async def play_audio(request: Request):
    """
    Endpoint para reproducir audio recibido del backend
    """
    try:
        # Parsear datos JSON
        data = await request.json()
        
        # Extraer audio y metadata
        audio_base64 = data.get("audio")
        metadata = data.get("metadata", {})
        
        if not audio_base64:
            logger.error("❌ No audio data provided in request")
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "No audio data provided"}
            )
        
        # Log metadata
        logger.info(f"📥 Received audio for playback: {metadata}")
        
        # Obtener sample rate de metadata o usar default
        sample_rate = metadata.get("sample_rate", 44100)
        
        # Obtener audio manager
        audio_manager = get_audio_manager()
        
        # Cambiar estado a SPEAKING
        state_manager = get_state_manager()
        previous_state = state_manager.get_state()
        await state_manager.set_state("SPEAKING")
        logger.info(f"🔄 State changed: {previous_state} → SPEAKING")
        
        # Reproducir audio
        success = await audio_manager.play_audio_base64(audio_base64, sample_rate)
        
        # Restaurar estado anterior o ir a LISTENING
        if success:
            new_state = "LISTENING" if previous_state in ["LISTENING", "PROCESSING"] else "IDLE"
            await state_manager.set_state(new_state)
            logger.info(f"🔄 State changed: SPEAKING → {new_state}")
        else:
            await state_manager.set_state("ERROR")
            logger.error("🔄 State changed: SPEAKING → ERROR")
        
        # Calcular duración estimada para respuesta
        try:
            audio_bytes = base64.b64decode(audio_base64)
            audio_length = len(audio_bytes) / 2  # Asumiendo 16-bit audio
            duration = audio_length / sample_rate
        except:
            duration = 0
        
        return JSONResponse(content={
            "success": success,
            "duration": duration,
            "state": state_manager.get_state()
        })
        
    except Exception as e:
        logger.error(f"❌ Error in /audio/play endpoint: {e}", exc_info=True)
        
        # Intentar restaurar estado
        try:
            state_manager = get_state_manager()
            await state_manager.set_state("ERROR")
        except:
            pass
        
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# AÑADIR también un endpoint de test para verificar que funciona
@app.get("/audio/test-beep")
async def test_beep():
    """
    Generar y reproducir un beep de prueba
    """
    try:
        import numpy as np
        
        # Generar tono de 440Hz por 0.5 segundos
        sample_rate = 44100
        duration = 0.5
        frequency = 440
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_array = np.sin(2 * np.pi * frequency * t)
        audio_array = (audio_array * 32767).astype(np.int16)
        
        # Reproducir
        audio_manager = get_audio_manager()
        success = await audio_manager.play_audio_array(audio_array, sample_rate)
        
        return JSONResponse(content={
            "success": success,
            "message": f"Played {frequency}Hz tone for {duration}s"
        })
        
    except Exception as e:
        logger.error(f"❌ Error in test beep: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
```

---

## 🧪 Paso 7: Scripts de Testing y Monitoreo

### 7.1 Script de Test Progresivo
```bash
cat > test_epic4_integration.sh << 'EOF'
#!/bin/bash

echo "🧪 Epic 4 - Test de Integración Progresiva"
echo "=========================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Función para verificar resultado
check_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
        exit 1
    fi
}

# Test 1: Sistema base funcionando
echo -e "\n${YELLOW}Test 1: Verificando sistema base${NC}"
curl -s http://localhost:8000/health > /dev/null 2>&1
check_result "Backend local respondiendo"

curl -s http://localhost:8080/status > /dev/null 2>&1
check_result "Hardware respondiendo"

# Test 2: Audio output en hardware
echo -e "\n${YELLOW}Test 2: Probando reproducción de audio${NC}"
echo "Generando beep de prueba..."
BEEP_RESULT=$(curl -s http://localhost:8080/audio/test-beep)
echo "$BEEP_RESULT" | grep -q '"success":true'
check_result "Reproducción de audio funcionando"

# Test 3: Activar cliente remoto
echo -e "\n${YELLOW}Test 3: Activando cliente remoto${NC}"
sed -i 's/USE_REMOTE_BACKEND=false/USE_REMOTE_BACKEND=true/' .env
docker-compose up -d backend
sleep 5

# Verificar conexión con backend remoto
REMOTE_STATUS=$(curl -s http://localhost:8000/api/v1/remote/status 2>/dev/null)
echo "$REMOTE_STATUS" | grep -q "authenticated"
check_result "Cliente remoto autenticado"

# Test 4: Activar procesador de audio
echo -e "\n${YELLOW}Test 4: Activando procesador de audio remoto${NC}"
sed -i 's/USE_REMOTE_AUDIO_PROCESSOR=false/USE_REMOTE_AUDIO_PROCESSOR=true/' .env
docker-compose up -d backend
sleep 5

# Verificar estado del procesador
QUEUE_STATUS=$(curl -s http://localhost:8000/api/v1/audio/queue/status 2>/dev/null)
echo "$QUEUE_STATUS" | grep -q "queue_size"
check_result "Procesador de audio activo"

# Test 5: Flujo completo con audio real
echo -e "\n${YELLOW}Test 5: Probando flujo completo${NC}"

# Generar audio de prueba si no existe
if [ ! -f test_audio.wav ]; then
    echo "Generando archivo de audio de prueba..."
    sox -n -r 44100 -c 1 test_audio.wav synth 2 sine 440 2>/dev/null || {
        echo -e "${YELLOW}⚠️ sox no disponible, usando archivo alternativo${NC}"
        # Crear un WAV mínimo válido
        echo "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAAB9AAACABAAZGF0YQAAAAA=" | base64 -d > test_audio.wav
    }
fi

# Enviar audio al backend
echo "Enviando audio al backend..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/hardware/audio \
  -F "audio=@test_audio.wav" \
  -F "metadata={\"test\": true}")

echo "$RESPONSE" | grep -q "success"
check_result "Audio procesado correctamente"

echo -e "\n${GREEN}✅ Todos los tests pasaron exitosamente${NC}"
echo -e "${YELLOW}Sistema Epic 4 listo para uso${NC}"
EOF

chmod +x test_epic4_integration.sh
```

### 7.2 Script de Monitoreo en Tiempo Real
```bash
cat > monitor_epic4.sh << 'EOF'
#!/bin/bash

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

while true; do
    clear
    echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     EPIC 4 - MONITOR DE INTEGRACIÓN         ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"
    
    # Timestamp
    echo -e "\n⏰ $(date '+%Y-%m-%d %H:%M:%S')"
    
    # Estado de Features
    echo -e "\n${YELLOW}📊 CONFIGURACIÓN:${NC}"
    USE_REMOTE=$(grep "^USE_REMOTE_BACKEND=" .env | cut -d'=' -f2)
    USE_PROCESSOR=$(grep "^USE_REMOTE_AUDIO_PROCESSOR=" .env | cut -d'=' -f2)
    
    if [ "$USE_REMOTE" = "true" ]; then
        echo -e "  Backend Remoto: ${GREEN}ACTIVO${NC}"
    else
        echo -e "  Backend Remoto: ${RED}INACTIVO${NC}"
    fi
    
    if [ "$USE_PROCESSOR" = "true" ]; then
        echo -e "  Procesador Audio: ${GREEN}ACTIVO${NC}"
    else
        echo -e "  Procesador Audio: ${RED}INACTIVO${NC}"
    fi
    
    # Estado del Sistema
    echo -e "\n${YELLOW}🖥️ ESTADO DEL SISTEMA:${NC}"
    
    # Backend Local
    BACKEND_HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null | jq -r '.status' 2>/dev/null)
    if [ "$BACKEND_HEALTH" = "healthy" ]; then
        echo -e "  Backend Local: ${GREEN}✓ Healthy${NC}"
    else
        echo -e "  Backend Local: ${RED}✗ Offline${NC}"
    fi
    
    # Hardware
    HW_STATE=$(curl -s http://localhost:8080/status 2>/dev/null | jq -r '.state' 2>/dev/null)
    if [ -n "$HW_STATE" ]; then
        echo -e "  Hardware: ${GREEN}✓ $HW_STATE${NC}"
    else
        echo -e "  Hardware: ${RED}✗ Offline${NC}"
    fi
    
    # Backend Remoto (si está activo)
    if [ "$USE_REMOTE" = "true" ]; then
        echo -e "\n${YELLOW}🌐 BACKEND REMOTO:${NC}"
        REMOTE_DATA=$(curl -s http://localhost:8000/api/v1/remote/status 2>/dev/null)
        if [ -n "$REMOTE_DATA" ]; then
            AUTHENTICATED=$(echo "$REMOTE_DATA" | jq -r '.remote_backend.authenticated' 2>/dev/null)
            STATUS=$(echo "$REMOTE_DATA" | jq -r '.remote_backend.status' 2>/dev/null)
            
            if [ "$AUTHENTICATED" = "true" ]; then
                echo -e "  Autenticación: ${GREEN}✓${NC}"
            else
                echo -e "  Autenticación: ${RED}✗${NC}"
            fi
            echo -e "  Estado: $STATUS"
        else
            echo -e "  ${RED}No disponible${NC}"
        fi
    fi
    
    # Cola de Audio (si está activa)
    if [ "$USE_PROCESSOR" = "true" ]; then
        echo -e "\n${YELLOW}📋 COLA DE PROCESAMIENTO:${NC}"
        QUEUE_DATA=$(curl -s http://localhost:8000/api/v1/audio/queue/status 2>/dev/null)
        if [ -n "$QUEUE_DATA" ]; then
            QUEUE_SIZE=$(echo "$QUEUE_DATA" | jq -r '.queue_size' 2>/dev/null)
            MAX_SIZE=$(echo "$QUEUE_DATA" | jq -r '.max_queue_size' 2>/dev/null)
            IS_PROCESSING=$(echo "$QUEUE_DATA" | jq -r '.is_processing' 2>/dev/null)
            REMOTE_AVAILABLE=$(echo "$QUEUE_DATA" | jq -r '.remote_available' 2>/dev/null)
            
            echo -e "  Items en cola: $QUEUE_SIZE/$MAX_SIZE"
            
            if [ "$IS_PROCESSING" = "true" ]; then
                echo -e "  Procesando: ${GREEN}✓${NC}"
            else
                echo -e "  Procesando: ${YELLOW}En espera${NC}"
            fi
            
            if [ "$REMOTE_AVAILABLE" = "true" ]; then
                echo -e "  Backend disponible: ${GREEN}✓${NC}"
            else
                echo -e "  Backend disponible: ${RED}✗${NC}"
            fi
            
            # Archivos de verificación
            VERIFICATION_COUNT=$(echo "$QUEUE_DATA" | jq -r '.verification_files_count' 2>/dev/null)
            if [ -n "$VERIFICATION_COUNT" ] && [ "$VERIFICATION_COUNT" != "null" ]; then
                echo -e "  Archivos verificación: $VERIFICATION_COUNT"
            fi
        else
            echo -e "  ${RED}No disponible${NC}"
        fi
    fi
    
    # Logs recientes
    echo -e "\n${YELLOW}📜 LOGS RECIENTES:${NC}"
    docker-compose logs --tail=3 backend 2>/dev/null | grep -E "(ERROR|WARNING|Epic 4)" | tail -3
    
    echo -e "\n${BLUE}Presiona Ctrl+C para salir | Actualización en 5s${NC}"
    sleep 5
done
EOF

chmod +x monitor_epic4.sh
```

### 7.3 Script de Rollback de Emergencia
```bash
cat > rollback_epic4.sh << 'EOF'
#!/bin/bash

echo "⚠️ ROLLBACK - Desactivando Epic 4"
echo "================================="

# Desactivar features en .env
sed -i 's/USE_REMOTE_BACKEND=true/USE_REMOTE_BACKEND=false/' .env
sed -i 's/USE_REMOTE_AUDIO_PROCESSOR=true/USE_REMOTE_AUDIO_PROCESSOR=false/' .env

# Reiniciar servicios
docker-compose restart backend hardware

echo "✅ Epic 4 desactivado"
echo "Sistema volvió a configuración anterior"
EOF

chmod +x rollback_epic4.sh
```

---

## 🚀 Paso 8: Activación y Verificación

### 8.1 Secuencia de Activación Segura
```bash
# 1. Verificar sistema actual
./check_audio_devices.sh

# 2. Ejecutar tests progresivos
./test_epic4_integration.sh

# 3. Si todos los tests pasan, monitorear
./monitor_epic4.sh

# 4. En caso de problemas
./rollback_epic4.sh
```

### 8.2 Verificación de Logs
```bash
# Ver logs en tiempo real
docker-compose logs -f backend | grep -E "(Epic 4|Remote|Audio)"

# Ver logs de hardware
docker-compose logs -f hardware | grep -E "(play|audio|speaker)"

# Ver archivos de verificación
ls -la puertocho-assistant-backend/audio_verification/
```

---

## 📊 Paso 9: Endpoints de Verificación

### 9.1 Endpoints Disponibles
```bash
# Estado del backend remoto
curl http://localhost:8000/api/v1/remote/status | jq .

# Estado de la cola de audio
curl http://localhost:8000/api/v1/audio/queue/status | jq .

# Archivos de verificación
curl http://localhost:8000/api/v1/audio/verification/status | jq .

# Estadísticas de procesamiento
curl http://localhost:8000/api/v1/audio/processing/statistics | jq .

# Test de autenticación remota
curl http://localhost:8000/api/v1/remote/test-auth | jq .

# Test de beep en hardware
curl http://localhost:8080/audio/test-beep | jq .
```

---

## ✅ Checklist de Verificación Final

- [ ] Variables de entorno configuradas en `.env`
- [ ] Docker-compose actualizado con nuevas variables
- [ ] `remote_backend_client.py` creado en `src/clients/`
- [ ] `audio_processor.py` creado en `src/services/`
- [ ] `main.py` actualizado con inicialización condicional
- [ ] `gateway_endpoints.py` actualizado con integración opcional
- [ ] `audio_manager.py` en hardware actualizado con reproducción
- [ ] Endpoint `/audio/play` añadido en hardware
- [ ] Scripts de testing creados y ejecutables
- [ ] Sistema probado con `USE_REMOTE_*=false` (modo offline)
- [ ] Sistema probado con `USE_REMOTE_*=true` (modo online)
- [ ] Reproducción de audio verificada en hardware
- [ ] Monitoreo funcionando correctamente
- [ ] Logs sin errores críticos
- [ ] Rollback probado y funcionando

---

## 🔧 Troubleshooting

### Problema: No se puede conectar al backend remoto
```bash
# Verificar conectividad
ping 192.168.1.88
curl http://192.168.1.88:10002/health

# Verificar credenciales
curl -X POST http://192.168.1.88:10002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"service@puertocho.local","password":"servicepass123"}'
```

### Problema: No se reproduce audio
```bash
# Verificar dispositivos
./check_audio_devices.sh

# Probar beep directo
curl http://localhost:8080/audio/test-beep

# Verificar permisos de audio
docker exec puertocho-hardware ls -la /dev/snd/
```

### Problema: Sistema lento o no responde
```bash
# Rollback inmediato
./rollback_epic4.sh

# Revisar logs
docker-compose logs --tail=100 backend | grep ERROR

# Reiniciar servicios
docker-compose restart backend hardware
```

---

## 📝 Notas Finales

1. **Activación Gradual**: Siempre activar primero con `USE_REMOTE_*=false` para verificar que no se rompe nada
2. **Monitoreo**: Mantener `monitor_epic4.sh` corriendo durante las primeras horas
3. **Backup**: El backup creado al inicio permite restauración completa si es necesario
4. **Logs**: Guardar logs de la primera ejecución exitosa para referencia
5. **Documentación**: Actualizar este documento con cualquier cambio o problema encontrado

**Versión**: 1.0.0
**Fecha**: $(date +%Y-%m-%d)
**Estado**: LISTO PARA IMPLEMENTACIÓN