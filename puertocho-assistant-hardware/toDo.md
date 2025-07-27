# PuertoCho Assistant Hardware - Hitos del Proyecto

## 📋 Resumen del Proyecto

El servicio `puertocho-assistant-hardware` es responsable de manejar todo el hardware de la Raspberry Pi, incluyendo:
- **Grabación de audio** con el módulo ReSpeaker 2-Mic Pi HAT V1.0
- **Control de LEDs RGB** APA102 para indicar estados del asistente
- **Detección de botón** en GPIO17 para activación manual
- **Módulo NFC** por I2C para lectura/escritura de etiquetas
- **Wake word detection** con Porcupine
- **Detección de silencio** para parar grabación automáticamente
- **Comunicación HTTP/WebSocket** con el backend

## 🏛️ Arquitectura del Sistema

Para asegurar la mantenibilidad y escalabilidad del proyecto, se ha decidido adoptar una arquitectura basada en una **Máquina de Estados Centralizada (`StateManager`)**.

- **`StateManager`**: Orquesta el flujo de la aplicación. Gestiona los estados (`IDLE`, `LISTENING`, `PROCESSING`, etc.) y coordina las acciones entre los diferentes módulos de hardware.
- **`AudioManager`**: Provee un flujo de audio constante. No conoce el estado de la aplicación, simplemente emite los datos del micrófono.
- **Módulos de Hardware (`ButtonHandler`, `WakeWordDetector`, `VADHandler`, `LEDController`)**: Actúan como componentes desacoplados.
    - Notifican eventos al `StateManager` (ej: "botón presionado", "wake word detectado").
    - Reciben comandos del `StateManager` (ej: "cambiar patrón de LED").

Esta arquitectura promueve el bajo acoplamiento y la alta cohesión, facilitando las pruebas y futuras modificaciones. La implementación de los hitos se realizará siguiendo este patrón.

## 🎯 Hitos del Proyecto

### Hito 1: Configuración Base del Contenedor
- [x] **1.1** Configurar `Dockerfile` con imagen base Python 3.9+ para ARM64
- [x] **1.2** Instalar dependencias del sistema (audio, I2C, GPIO)
- [x] **1.3** Configurar privilegios y acceso a hardware (privileged: true)
- [x] **1.4** Configurar variables de entorno en archivo `.env`
- [x] **1.5** Crear estructura de directorios del proyecto
- [x] **1.6** Configurar logging y manejo de errores básico

### Hito 2: Configuración de Audio y ReSpeaker
- [x] **2.1** Configurar driver del ReSpeaker 2-Mic Pi HAT V1.0
- [x] **2.2** Implementar detección automática de dispositivos de audio
- [x] **2.2.1** Ejecutar script para verificar la detección de audio
- [x] **2.3** Crear clase `AudioManager` para grabación/reproducción
- [x] **2.4** Implementar configuración de audio (sample rate, channels, formato)
- [x] **2.5** Añadir pruebas de audio para verificar funcionamiento
  - [x] **2.5.1** Tests unitarios completos (`test_audio.py`)
  - [x] **2.5.2** Script interactivo (`test_audio_manager.py`)
  - [x] **2.5.3** Guardado de audio en archivos WAV
  - [x] **2.5.4** Reproducción de audio guardado

### Hito 3: Control de LEDs RGB (APA102)
- [x] **3.1** Implementar clase `LEDController` para manejar LEDs APA102
- [x] **3.2** Configurar comunicación SPI para LEDs RGB
- [x] **3.3** Crear patrones de LED para diferentes estados:
  - Disponible (azul pulsante)
  - Escuchando (verde sólido)
  - Procesando (amarillo giratorio)
  - Error (rojo parpadeante)
- [x] **3.4** Implementar transiciones suaves entre estados
- [x] **3.5** Añadir control de brillo adaptativo
- [x] **3.6** Crear scripts de prueba para cada patrón

### Hito 4: Detección de Botón y GPIO
- [x] **4.1** Implementar clase `ButtonHandler` para GPIO17
- [x] **4.2** Configurar interrupciones para detección de pulsaciones
- [x] **4.3** Implementar debouncing para evitar falsas activaciones
- [x] **4.4** Manejar pulsación corta y larga
- [x] **4.5** Notificar al StateManager los eventos de botón (corta/larga) a través de un callback
- [x] **4.6** Integrar con el `StateManager` para iniciar/detener la escucha manualmente
- [x] **4.7** Implementar modo simulación para testing sin hardware
- [x] **4.8** Crear script de pruebas completo (`test_button_handler.py`)
- [x] **4.9** Configurar permisos GPIO en contenedor Docker
- [x] **4.10** Validar funcionamiento en hardware real

### Hito 5: Wake Word Detection (Porcupine)
- [x] **5.1** Configurar Porcupine con modelo personalizado "Puerto-ocho"
- [x] **5.2** Implementar clase `WakeWordDetector` que procesa chunks de audio
- [x] **5.2.1** Implementar buffer circular para audio en tiempo real
- [x] **5.3** Optimizar sensibilidad para entorno doméstico
- [x] **5.4** Implementar filtros de audio para mejorar detección
- [x] **5.5** Añadir logging de eventos de wake word
- [x] **5.6** Crear modo de calibración para ajustar sensibilidad
- [x] **5.7** Integrar con `StateManager`: recibirá audio en estado `IDLE` y notificará detecciones

### Hito 6: Detección de Silencio (VAD)
- [ ] **6.1** Implementar Voice Activity Detection con WebRTC VAD
- [ ] **6.2** Configurar umbrales de silencio dinámicos
- [ ] **6.3** Notificar al `StateManager` el inicio y fin del habla para controlar la grabación
- [ ] **6.4** Añadir filtros de ruido de fondo
- [ ] **6.5** Optimizar para diferentes niveles de ruido ambiental
- [ ] **6.6** Crear sistema de calibración automática
- [ ] **6.7** Integrar con `StateManager`: recibirá audio en estado `LISTENING`

### Hito 7: Módulo NFC (I2C)
- [ ] **7.1** Configurar comunicación I2C para módulo NFC
- [ ] **7.2** Implementar clase `NFCManager` para operaciones básicas
- [ ] **7.3** Funcionalidades de lectura:
  - Detectar presencia de etiqueta
  - Leer UID de etiqueta
  - Leer datos NDEF
- [ ] **7.4** Funcionalidades de escritura:
  - Escribir datos NDEF
  - Formatear etiquetas
  - Proteger etiquetas
- [ ] **7.5** Implementar sistema de acciones programables
- [ ] **7.6** Crear interfaz para configurar acciones NFC

### Hito 8: Sistema de Estados del Asistente (StateManager)
- [ ] **8.1** Implementar la clase `StateManager` en `app/core/state_manager.py`.
- [ ] **8.2** Definir los estados principales como un Enum: `IDLE`, `LISTENING`, `PROCESSING`, `SPEAKING`, `ERROR`.
- [ ] **8.3** Implementar el método `handle_audio_chunk` que distribuirá el audio al componente correspondiente según el estado actual (`WakeWordDetector` o `VADHandler`).
- [ ] **8.4** Crear la lógica de transiciones entre estados (ej: `IDLE` -> `LISTENING` al detectar wake word o botón).
- [ ] **8.5** Integrar `LEDController` para que los patrones de LED se sincronicen automáticamente con los cambios de estado.
- [ ] **8.6** Implementar un sistema de callbacks o eventos para que los manejadores de hardware notifiquen al `StateManager`.
- [ ] **8.7** Añadir logging detallado para cada transición de estado y evento recibido.
- [ ] **8.8** Manejar timeouts y recuperación de errores básicos (ej: volver a `IDLE` si algo falla).

### Hito 9: API HTTP y Endpoints
- [ ] **9.1** Configurar FastAPI para endpoints HTTP
- [ ] **9.2** Implementar endpoints principales:
  - `GET /health` - Estado del servicio
  - `POST /audio/start` - Iniciar grabación
  - `POST /audio/stop` - Parar grabación
  - `GET /audio/status` - Estado de audio
  - `POST /nfc/read` - Leer etiqueta NFC
  - `POST /nfc/write` - Escribir etiqueta NFC
  - `GET /nfc/status` - Estado NFC
  - `POST /led/pattern` - Cambiar patrón LED
- [ ] **9.3** Implementar autenticación y validación
- [ ] **9.4** Añadir documentación OpenAPI/Swagger
- [ ] **9.5** Implementar rate limiting
- [ ] **9.6** Añadir métricas y monitoreo

### Hito 10: Comunicación WebSocket
- [ ] **10.1** Implementar cliente WebSocket para comunicación en tiempo real
- [ ] **10.2** Eventos a enviar al backend:
  - Audio grabado
  - Cambios de estado
  - Eventos de botón
  - Eventos NFC
  - Métricas de hardware
- [ ] **10.3** Eventos a recibir del backend:
  - Comandos de control
  - Cambios de configuración
  - Patrones LED personalizados
- [ ] **10.4** Implementar reconexión automática
- [ ] **10.5** Añadir heartbeat y keep-alive
- [ ] **10.6** Manejar cola de mensajes para conexiones intermitentes

### Hito 11: Integración con Backend
- [ ] **11.1** Adaptar endpoints del backend para recibir:
  - `/hardware/audio` - Recibir audio grabado
  - `/hardware/status` - Recibir estado del hardware
  - `/hardware/nfc` - Recibir eventos NFC
- [ ] **11.2** Implementar formato de datos estándar
- [ ] **11.3** Añadir compresión de audio para transmisión
- [ ] **11.4** Implementar retry logic para fallos de comunicación
- [ ] **11.5** Crear sistema de configuración remota
- [ ] **11.6** Añadir sincronización de tiempo entre servicios

### Hito 12: Configuración y Persistencia
- [ ] **12.1** Crear archivo de configuración YAML/JSON
- [ ] **12.2** Implementar sistema de configuración por capas:
  - Configuración por defecto
  - Configuración de usuario
  - Variables de entorno
- [ ] **12.3** Persistir configuraciones de calibración
- [ ] **12.4** Implementar backup y restauración de configuración
- [ ] **12.5** Crear interfaz de configuración web
- [ ] **12.6** Añadir validación de configuración

### Hito 13: Monitoreo y Logging
- [ ] **13.1** Implementar logging estructurado (JSON)
- [ ] **13.2** Configurar rotación de logs
- [ ] **13.3** Añadir métricas de rendimiento:
  - Latencia de audio
  - Uso de CPU/RAM
  - Eventos por segundo
- [ ] **13.4** Implementar health checks avanzados
- [ ] **13.5** Crear dashboard de monitoreo
- [ ] **13.6** Añadir alertas por email/webhook

### Hito 14: Testing y Calidad
- [ ] **14.1** Crear tests unitarios para cada componente
- [ ] **14.2** Implementar tests de integración
- [ ] **14.3** Añadir tests de hardware simulado
- [ ] **14.4** Crear suite de tests de rendimiento
- [ ] **14.5** Implementar tests de stress
- [ ] **14.6** Configurar CI/CD para tests automáticos

### Hito 15: Optimización y Producción
- [ ] **15.1** Optimizar uso de memoria y CPU
- [ ] **15.2** Implementar cache para operaciones frecuentes
- [ ] **15.3** Añadir compresión y optimización de datos
- [ ] **15.4** Configurar monitoreo de producción
- [ ] **15.5** Implementar actualizaciones OTA
- [ ] **15.6** Crear documentación de deployment

## 🔧 Tecnologías y Librerías Principales

### Audio
- **sounddevice**: Grabación y reproducción de audio
- **webrtcvad**: Voice Activity Detection
- **numpy**: Procesamiento de señales de audio

### Wake Word
- **pvporcupine**: Detección de wake word
- **Modelo personalizado**: Puerto-ocho_es_raspberry-pi_v3_0_0.ppn

### Hardware
- **RPi.GPIO**: Control de GPIO y botones
- **spidev**: Comunicación SPI para LEDs APA102
- **I2C**: Comunicación con módulo NFC

### Comunicación
- **fastapi**: API HTTP
- **uvicorn**: Servidor ASGI
- **websockets**: Cliente WebSocket
- **requests**: Cliente HTTP

### Utilidades
- **python-dotenv**: Gestión de variables de entorno
- **asyncio**: Programación asíncrona
- **threading**: Manejo de hilos para hardware

## 📁 Estructura de Archivos Propuesta

```
puertocho-assistant-hardware/
├── Dockerfile
├── requirements.txt
├── .env.example
├── app/
│   ├── main.py                 # Punto de entrada principal
│   ├── config.py               # Configuración centralizada
│   ├── core/
│   │   ├── __init__.py
│   │   ├── audio_manager.py    # Gestión de audio
│   │   ├── led_controller.py   # Control de LEDs
│   │   ├── button_handler.py   # Manejo de botones
│   │   ├── nfc_manager.py      # Gestión NFC
│   │   ├── state_machine.py    # Máquina de estados
│   │   └── wake_word_detector.py # Detección wake word
│   ├── api/
│   │   ├── __init__.py
│   │   ├── http_server.py      # Servidor HTTP
│   │   └── websocket_client.py # Cliente WebSocket
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py           # Logging
│   │   ├── metrics.py          # Métricas
│   │   └── calibration.py      # Calibración
│   └── tests/
│       ├── __init__.py
│       ├── test_audio.py
│       ├── test_led.py
│       ├── test_nfc.py
│       └── test_integration.py
├── scripts/
│   ├── setup.sh               # Script de instalación
│   ├── test_hardware.py       # Pruebas de hardware
│   └── calibrate.py           # Calibración automática
├── docs/
│   ├── README.md
│   ├── API.md
│   └── DEPLOYMENT.md
└── models/
    ├── porcupine_params_es.pv
    └── Puerto-ocho_es_raspberry-pi_v3_0_0.ppn
```

## 🚀 Próximos Pasos

1. **✅ Hito 1**: Configuración base del contenedor - **COMPLETADO**
2. **✅ Hito 2**: Configuración de Audio y ReSpeaker - **COMPLETADO**
3. **✅ Hito 3**: Control de LEDs RGB (APA102) - **COMPLETADO**
4. **✅ Hito 4**: Detección de Botón y GPIO - **COMPLETADO**
5. **🔄 Próximo**: Implementar Hito 5 (Wake Word Detection)
6. **Planificado**: Desarrollar Hitos 6-8 (VAD, NFC, StateManager)
7. **Futuro**: Integrar Hitos 9-11 (API, WebSocket, Backend)
8. **Final**: Finalizar Hitos 12-15 (Configuración, Testing, Producción)

## 📝 Notas Importantes

- ✅ El contenedor debe ejecutarse con `privileged: true` para acceso al hardware
- ✅ Usar `network_mode: host` para comunicación eficiente  
- ✅ Configurar correctamente I2C, SPI y GPIO en el sistema host
- ✅ Permisos GPIO resueltos ejecutando contenedor como root (user: "0:0")
- ✅ ButtonHandler implementado con soporte completo para hardware real y simulación
- 🔄 Considerar latencia y rendimiento en tiempo real para próximos módulos
- 🔄 Implementar manejo robusto de errores de hardware
- 🔄 Documentar todas las configuraciones y calibraciones

### 🎯 Estado Actual del Proyecto
**Hardware Base**: ✅ COMPLETADO (Hitos 1-4)
- Contenedor Docker configurado y funcionando
- Audio ReSpeaker operativo con grabación/reproducción
- LEDs RGB APA102 con patrones dinámicos
- Detección de botón GPIO con eventos y callbacks

**Próximo Objetivo**: 🚀 Wake Word Detection (Hito 5)
- Integrar Porcupine para detección "Puerto-ocho"
- Implementar buffer circular de audio
- Crear sistema de calibración de sensibilidad