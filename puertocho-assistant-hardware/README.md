# ReSpeaker 2-Mic Pi HAT V1.0 - Hardware Client

Este directorio contiene el cliente de hardware simplificado para el ReSpeaker 2-Mic Pi HAT V1.0.

## 🎯 Características

- **Captura de audio**: Grabación continua con procesamiento de chunks
- **Wake Word Detection**: Usando Porcupine para detectar la palabra clave
- **Control de LEDs RGB**: Control de los 3 LEDs APA102 integrados
- **Gestión de estado**: Estados visuales (idle, listening, thinking, speaking, error)
- **Botón integrado**: Detección del botón en GPIO17
- **Arquitectura simplificada**: Sin dependencias de servicios externos

## 🛠️ Instalación Rápida

```bash
# Ejecutar script de instalación
chmod +x setup_respeaker.sh
./setup_respeaker.sh

# Activar entorno virtual
source venv/bin/activate
```

## 🎮 Pruebas

### Probar LEDs RGB
```bash
# Probar estados del asistente
./test_leds.py --test states

# Probar colores básicos
./test_leds.py --test colors

# Probar LEDs individuales
./test_leds.py --test individual

# Probar efectos
./test_leds.py --test breathing
./test_leds.py --test rotation

# Probar todo
./test_leds.py --test all
```

### Probar Audio
```bash
# Listar dispositivos de audio
aplay -l

# Grabar audio (5 segundos)
arecord -D hw:1,0 -f S16_LE -r 44100 -c 2 -d 5 test.wav

# Reproducir audio
aplay -D hw:1,0 test.wav

# Probar micrófono para wake word (formato Porcupine)
arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 -d 5 test_mono.wav
```

## 📁 Estructura del Proyecto

```
puertocho-assistant-hardware/
├── app/
│   ├── hardware_client.py      # Cliente principal
│   ├── config.py               # Configuración
│   └── utils/
│       ├── apa102.py           # Driver APA102 LEDs
│       ├── led_controller.py   # Controlador de LEDs
│       └── logging_config.py   # Configuración de logs
├── test_leds.py                # Script de prueba LEDs
├── setup_respeaker.sh          # Script de instalación
└── README.md                   # Este archivo
```

## 🔧 Configuración

### GPIO Pins (ReSpeaker 2-Mic Pi HAT V1.0)
- **Botón**: GPIO17
- **LEDs disponibles**: GPIO12, GPIO13 (externos)
- **LEDs RGB integrados**: SPI (MOSI, SCLK)
- **I2C**: GPIO2 (SDA), GPIO3 (SCL)
- **UART**: GPIO14 (TX), GPIO15 (RX)

### Audio
- **Dispositivo**: `hw:1,0` (ReSpeaker)
- **Formato óptimo**: S16_LE, 44100Hz, estéreo
- **Formato Wake Word**: S16_LE, 16000Hz, mono

## 🎨 Control de LEDs

### Estados del Asistente
- **Idle**: Azul suave pulsante
- **Listening**: Verde sólido
- **Thinking**: Amarillo rotativo
- **Speaking**: Cyan pulsante
- **Error**: Rojo parpadeante

### Uso Programático
```python
from utils.led_controller import get_led_controller

# Crear controlador
led_controller = get_led_controller(brightness=10)

# Cambiar estado
led_controller.set_state('listening')

# Control directo
led_controller.write([255, 0, 0] * 3)  # Rojo en los 3 LEDs

# Apagar
led_controller.off()
```

## Hardware Compatible

### ReSpeaker 2-Mic Pi HAT V1.0
- **Modelo**: keyestudio ReSpeaker 2-Mic Pi HAT V1.0
- **Documentación**: Ver `docs/respeaker-2mic-hat-v1.md`
- **Características**:
  - 2 micrófonos estéreo (Mic L y Mic R)
  - Codec WM8960 para audio de alta calidad
  - 3 LEDs APA102 RGB integrados
  - Botón de usuario en GPIO17
  - Conectores Grove para expansión (I2C y GPIO12/13)
  - Salida de audio: Jack 3.5mm y conector XH2.54-2P

### Configuración de pines:
- **Botón integrado**: GPIO17 (configurado por defecto)
- **LEDs externos**: GPIO12 y GPIO13 (conectores Grove)
- **I2C disponible**: GPIO2 (SDA), GPIO3 (SCL)

## Configuración de Audio

El módulo ReSpeaker utiliza el codec WM8960 y requiere la instalación de drivers específicos. Ver documentación detallada en `docs/respeaker-2mic-hat-v1.md`.

### Configuración recomendada:
```bash
# Parámetros óptimos para ReSpeaker 2-Mic Pi HAT V1.0
# Grabación con alta calidad
arecord -D "plughw:X,0" -f S16_LE -r 44100 -c 2 -d 5 grabacion.wav

# Reproducción
aplay -D "plughw:X,0" grabacion.wav

# Para Porcupine (wake word detection)
arecord -D "plughw:X,0" -f S16_LE -r 16000 -c 1 -d 5 wake_word.wav
```

*Nota: X es el número del dispositivo de audio, detectado automáticamente por el sistema.*
*   **Flujo de comunicación**:
    1.  Primero, envía el audio grabado al **Servicio de Transcripción** para convertir la voz a texto.
    2.  Luego, envía el texto ya transcrito al **Servicio de Chat del Asistente**.
    3.  Este modo permite conversaciones contextuales y respuestas complejas. Si el servicio de chat devuelve una URL de audio con una respuesta sintetizada (TTS), este servicio de wake-word se encarga de descargarla y reproducirla.

```
┌───────────────────────────┐      ┌───────────────────────────┐      ┌────────────────────────┐
│ Wake-Word Service         │      │ Transcription Service     │      │ Assistant Chat Service │
│ (Este proyecto)           │      │ (Externo)                 │      │ (Externo)              │
├───────────────────────────┤      ├───────────────────────────┤      ├────────────────────────┤
│ 1. Graba audio            │      │                           │      │                        │
│ 2. Envía audio.wav        ├─────►│ 3. Transcribe a texto     │      │                        │
│                           │      │ 4. Devuelve texto         │◄─────┤                        │
│ 5. Recibe texto           │      │                           │      │                        │
│ 6. Envía texto            │      │                           ├─────►│ 7. Procesa conversación  │
│                           │      │                           │      │ 8. Devuelve respuesta  │
│ 9. Recibe y reproduce     │◄─────│                           │◄─────┤                        │
└───────────────────────────┘      └───────────────────────────┘      └────────────────────────┘
```

### Modo 2: Fallback (Comandos Locales)

Este modo se activa si el servicio de chat no está disponible, pero sí el de transcripción.

*   **Endpoint de destino**: `TRANSCRIPTION_SERVICE_URL` (configurable).
*   **Flujo de comunicación**:
    1.  Envía el audio grabado directamente al **Servicio de Transcripción**.
    2.  Recibe el texto transcrito y busca una coincidencia exacta en su archivo local `commands.json`.
    3.  Si encuentra una coincidencia, ejecuta la acción asociada (ej. encender/apagar un LED conectado a un pin GPIO).
*   Este modo es más limitado, no tiene memoria conversacional y solo responde a un conjunto predefinido de comandos.