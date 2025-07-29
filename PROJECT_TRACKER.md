# PuertoCho Assistant - Project Tracker

## 🏛️ Arquitectura del Sistema

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  HARDWARE       │━━━━▶│  BACKEND LOCAL  │━━━━▶│ BACKEND REMOTO  │
│  (Raspberry Pi) │◀━━━━│  (Gateway)      │◀━━━━│ (Procesamiento) │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Arquitectura seleccionada: Hardware → Backend Local → Backend Remoto**

### Componentes del Sistema:
- **Hardware (puertocho-assistant-hardware)**: Gestión de dispositivos físicos, captura de audio, LEDs, botones
- **Backend Local (puertocho-assistant-backend)**: Gateway, buffer, gestión de estado, API
- **Frontend (puertocho-assistant-web-view)**: Interfaz de usuario para monitoreo y control
- **Backend Remoto**: Procesamiento de IA y servicios en la nube

## 🎯 Tareas para Conectar Hardware y Backend

### 📡 FASE 1: API HTTP en Hardware (Hito 9)

- [ ] **HW-API-01**: Configurar FastAPI en `app/api/http_server.py`
  - Implementar estructura base del servidor
  - Configurar CORS y middlewares necesarios
  - Integrar con el StateManager existente

- [ ] **HW-API-02**: Implementar endpoints básicos de estado y salud
  - `GET /health` - Estado del servicio hardware
  - `GET /state` - Obtener estado actual del StateManager
  - `POST /state` - Cambiar estado manualmente (para testing)

- [ ] **HW-API-03**: Implementar endpoints de gestión de audio
  - `GET /audio/capture` - Obtener último archivo de audio capturado
  - `GET /audio/status` - Estado de audio, VAD y grabación
  - `POST /audio/send` - Endpoint para enviar audio al backend local

- [ ] **HW-API-04**: Implementar endpoints de control de hardware
  - `POST /led/pattern` - Cambiar patrón LED manualmente
  - `GET /metrics` - Métricas del sistema (CPU, memoria, eventos)
  - `POST /button/simulate` - Simular eventos de botón para testing

- [ ] **HW-API-05**: Configurar documentación y testing
  - Añadir documentación OpenAPI/Swagger
  - Implementar middleware de logging
  - Crear tests básicos de endpoints

### 🔌 FASE 2: Cliente WebSocket en Hardware (Hito 10)

- [ ] **HW-WS-01**: Implementar cliente WebSocket en `app/api/websocket_client.py`
  - Conexión al backend local en puerto definido
  - Sistema de reconexión automática con backoff exponencial
  - Manejo de errores y timeouts

- [ ] **HW-WS-02**: Implementar emisión de eventos desde hardware
  - Audio capturado (envío automático cuando VAD termina)
  - Cambios de estado del StateManager
  - Eventos de botón (corto/largo)
  - Métricas de hardware en tiempo real

- [ ] **HW-WS-03**: Implementar recepción de comandos desde backend
  - Cambios de configuración remotos
  - Control de patrones LED
  - Activación manual del sistema
  - Comandos de calibración

- [ ] **HW-WS-04**: Integrar WebSocket con StateManager
  - Notificaciones automáticas de cambios de estado
  - Queue de mensajes para conexiones intermitentes
  - Heartbeat y keep-alive

### 🖥️ FASE 3: Reimplementación del Backend Local

- [ ] **BE-CORE-01**: Configurar estructura base del proyecto backend
  - Limpiar código obsoleto del backend actual
  - Configurar FastAPI como framework principal
  - Sistema de logging centralizado y estructurado
  - Gestión de configuración con variables de entorno

- [ ] **BE-CORE-02**: Implementar StateManager central para el backend
  - Gestión del estado actual del sistema completo
  - Sincronización entre hardware, frontend y backend remoto
  - Persistencia temporal de estados importantes

- [ ] **BE-API-01**: Implementar endpoints para recibir datos del hardware
  - `POST /hardware/audio` - Recibir y procesar audio capturado
  - `POST /hardware/status` - Actualizar estado del hardware
  - `POST /hardware/events` - Recibir eventos (botón, NFC, etc.)
  - `GET /hardware/config` - Configuración para el hardware

- [ ] **BE-API-02**: Implementar endpoints para comunicación con frontend
  - `GET /state` - Estado actual del sistema completo
  - `POST /control` - Comandos de control desde la UI
  - `GET /history` - Historial de interacciones
  - `GET /metrics` - Métricas del sistema completo

- [ ] **BE-WS-01**: Implementar servidor WebSocket dual
  - Servidor WebSocket para conexión con hardware
  - Servidor WebSocket para conexión con frontend
  - Distribución inteligente de mensajes entre conexiones
  - Gestión de múltiples clientes frontend

### 🌐 FASE 4: Comunicación con Backend Remoto

- [ ] **BE-REMOTE-01**: Implementar cliente HTTP/REST para backend remoto
  - Autenticación segura y manejo de tokens
  - Gestión de errores, timeouts y reintentos
  - Configuración de endpoints remotos por variables de entorno

- [ ] **BE-REMOTE-02**: Implementar envío de audio para procesamiento
  - Compresión de audio antes del envío
  - Formato estandarizado de peticiones con metadatos
  - Manejo de archivos grandes con streaming

- [ ] **BE-REMOTE-03**: Implementar recepción y procesamiento de respuestas
  - Procesamiento de texto para TTS
  - Interpretación de comandos de acción
  - Manejo de metadatos y contexto de conversación

- [ ] **BE-REMOTE-04**: Implementar buffer y cola de peticiones
  - Buffer local cuando el backend remoto no está disponible
  - Cola de peticiones con prioridades
  - Sincronización cuando se restablece la conexión

### 🔗 FASE 5: Integración y Pruebas

- [ ] **INT-01**: Pruebas de integración hardware → backend local
  - Validar transmisión correcta de audio
  - Verificar sincronización de estados en tiempo real
  - Pruebas de latencia y rendimiento

- [ ] **INT-02**: Pruebas de integración backend local → backend remoto
  - Validar procesamiento de audio remoto
  - Verificar manejo correcto de respuestas
  - Pruebas de fallos y recuperación

- [ ] **INT-03**: Pruebas de flujo completo end-to-end
  - Wake word → grabación → procesamiento → respuesta
  - Medición de latencia total del sistema
  - Pruebas de stress con múltiples interacciones

- [ ] **INT-04**: Configuración de Docker Compose actualizada
  - Actualizar docker-compose.yml para la nueva arquitectura
  - Configurar redes y volúmenes necesarios
  - Variables de entorno para cada servicio

## 📊 Métricas de Éxito

- **Latencia hardware → backend local**: < 200ms
- **Reconexión WebSocket**: < 5 segundos
- **Latencia end-to-end**: < 3 segundos
- **Pérdida de paquetes**: < 0.1% en condiciones normales
- **Disponibilidad del sistema**: > 99% uptime

## 🚀 Plan de Ejecución

### Sprint 1: Base API Hardware (1-2 semanas)
- Tareas HW-API-01 a HW-API-05
- Establecer comunicación HTTP básica

### Sprint 2: WebSocket Hardware (1 semana)  
- Tareas HW-WS-01 a HW-WS-04
- Comunicación en tiempo real hardware → backend

### Sprint 3: Backend Local (2 semanas)
- Tareas BE-CORE-01 a BE-WS-01
- Gateway funcional entre hardware y remoto

### Sprint 4: Integración Remota (1-2 semanas)
- Tareas BE-REMOTE-01 a BE-REMOTE-04
- Conexión completa con backend de IA

### Sprint 5: Testing e Integración (1 semana)
- Tareas INT-01 a INT-04
- Sistema completo funcionando

## 📝 Notas Técnicas

- **Puerto Backend Local**: 8000 (HTTP) / 8001 (WebSocket)
- **Puerto Hardware**: 8080 (HTTP) / 8081 (WebSocket)
- **Formato de Audio**: WAV, 16kHz, mono para transmisión
- **Protocolo WebSocket**: JSON para todos los mensajes
- **Autenticación**: API Keys para backend remoto