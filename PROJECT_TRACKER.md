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

### 📡 FASE 1: API HTTP en Hardware (Hito 9) ✅ COMPLETADO

- [x] **HW-API-01**: Configurar FastAPI en `app/api/http_server.py` ✅
  - Implementar estructura base del servidor
  - Configurar CORS y middlewares necesarios
  - Integrar con el StateManager existente

- [x] **HW-API-02**: Implementar endpoints básicos de estado y salud ✅
  - `GET /health` - Estado del servicio hardware
  - `GET /state` - Obtener estado actual del StateManager
  - `POST /state` - Cambiar estado manualmente (para testing)

- [x] **HW-API-03**: Implementar endpoints de gestión de audio ✅
  - `GET /audio/capture` - Obtener último archivo de audio capturado
  - `GET /audio/status` - Estado de audio, VAD y grabación
  - `POST /audio/send` - Endpoint para enviar audio al backend local
  - `GET /audio/download/{filename}` - Descargar archivos de audio específicos

- [x] **HW-API-04**: Implementar endpoints de control de hardware ✅
  - `POST /led/pattern` - Cambiar patrón LED manualmente
  - `GET /metrics` - Métricas del sistema (CPU, memoria, eventos)
  - `POST /button/simulate` - Simular eventos de botón para testing

- [x] **HW-API-05**: Configurar documentación y testing ✅
  - Añadir documentación OpenAPI/Swagger
  - Implementar middleware de logging con request IDs
  - Crear tests completos de endpoints (14/14 tests passing)
  - Configurar CORS para desarrollo
  - Manejo robusto de errores HTTP

**Estado**: ✅ **COMPLETADO** - 14 endpoints funcionales, documentación OpenAPI, tests completos

### 🔧 EVALUACIÓN POST-FASE 1: Estado del Backend Actual

Tras completar exitosamente la Fase 1 del hardware, hemos identificado que el **backend local actual está desactualizado** y no se alinea con la nueva arquitectura del hardware. El backend actual:

**❌ Problemas Identificados:**
- Simula estados en lugar de recibir datos reales del hardware
- No tiene endpoints para recibir audio desde hardware (puerto 8080)
- WebSocket simple sin manejo robusto de reconexión
- Estado hardcodeado sin sincronización real con hardware
- Falta de cliente HTTP para comunicarse con hardware
- No maneja la cola de audio ni buffer para backend remoto

**✅ Elementos Reutilizables:**
- Estructura FastAPI básica
- WebSocket manager para frontend
- Middleware CORS
- Dockerfile Alpine base

**🎯 Decisión**: Reimplementar backend local siguiendo el patrón exitoso del hardware

### �️ FASE 2: Reimplementación del Backend Local (Hito 10) 🔄 EN PROGRESO

**Objetivo**: Desarrollar un backend local que funcione como gateway real entre hardware (puerto 8080) y servicios remotos.

- [ ] **BE-CORE-01**: Limpiar y reestructurar código base existente
  - Mantener Dockerfile Alpine y requirements.txt básicos
  - Preservar estructura FastAPI + WebSocket para frontend
  - Eliminar simulaciones y estados hardcodeados
  - Configurar logging estructurado con request IDs (siguiendo patrón hardware)

- [ ] **BE-CORE-02**: Implementar StateManager central para backend
  - Gestión unificada del estado hardware + backend + frontend
  - Sincronización bidireccional con hardware (puerto 8080)
  - Persistencia temporal de estados importantes
  - Manejo de inconsistencias y recuperación de fallos

- [ ] **BE-API-01**: Implementar endpoints para recibir datos del hardware ✅ Patrón definido
  - `POST /hardware/audio` - Recibir archivos de audio capturados por VAD
  - `POST /hardware/status` - Actualizar estado del hardware en tiempo real
  - `POST /hardware/events` - Recibir eventos (botón, wake word, errores)
  - `GET /hardware/config` - Configuración que el hardware debe usar

- [ ] **BE-API-02**: Actualizar endpoints para comunicación con frontend
  - `GET /state` - Estado unificado del sistema completo (hardware + backend)
  - `POST /control` - Comandos de control que se envían al hardware
  - `GET /history` - Historial de interacciones y audio procesado
  - `GET /metrics` - Métricas agregadas de hardware + backend + remoto

- [ ] **BE-CLIENT-01**: Implementar cliente HTTP para comunicación con hardware
  - Cliente HTTP robusto para endpoints hardware (puerto 8080)
  - Healthcheck y monitoreo de conexión con hardware
  - Retry logic y manejo de timeouts
  - Configuración por variables de entorno

- [ ] **BE-WS-01**: Actualizar servidor WebSocket para frontend
  - Mantener compatibilidad con frontend existente
  - Transmitir eventos reales desde hardware
  - Comandos de control hacia hardware
  - Distribuir métricas y estados en tiempo real

### 🌐 FASE 3: Comunicación con Backend Remoto (Hito 11)

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

### 🔌 FASE 4: Cliente WebSocket en Hardware (Hito 12) 

**Nota**: Movido después del backend local para aprovechar la nueva implementación

- [ ] **HW-WS-01**: Implementar cliente WebSocket en `app/api/websocket_client.py`
  - Conexión al backend local actualizado (puerto 8000)
  - Sistema de reconexión automática con backoff exponencial
  - Manejo de errores y timeouts siguiendo patrón del HTTP server

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

### 🔗 FASE 5: Integración y Pruebas

- [ ] **INT-01**: Pruebas de integración hardware → backend local
  - Validar comunicación HTTP bidireccional (hardware:8080 ↔ backend:8000)
  - Verificar transmisión correcta de audio desde hardware
  - Validar sincronización de estados en tiempo real
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
  - Healthchecks para todos los servicios

## 📊 Métricas de Éxito

- **Latencia hardware → backend local**: < 200ms (HTTP bidireccional)
- **Reconexión y recuperación**: < 5 segundos ante fallos
- **Latencia end-to-end**: < 3 segundos
- **Pérdida de paquetes**: < 0.1% en condiciones normales
- **Disponibilidad del sistema**: > 99% uptime

## 🚀 Plan de Ejecución Actualizado

### ✅ Sprint 1: Base API Hardware (COMPLETADO)
- ✅ Tareas HW-API-01 a HW-API-05
- ✅ Comunicación HTTP básica establecida
- ✅ 14 endpoints funcionales con documentación
- ✅ Tests completos (14/14 passing)
- ✅ StateManager robusto con estados bien definidos

### 🔄 Sprint 2: Backend Local Gateway (EN PROGRESO)  
- Tareas BE-CORE-01 a BE-WS-01
- Gateway funcional que consume API del hardware
- Comunicación bidireccional hardware ↔ backend

### Sprint 3: Integración Remota (1-2 semanas)
- Tareas BE-REMOTE-01 a BE-REMOTE-04
- Conexión completa con backend de IA

### Sprint 4: WebSocket Hardware (1 semana)
- Tareas HW-WS-01 a HW-WS-04
- Comunicación en tiempo real optimizada

### Sprint 5: Testing e Integración (1 semana)
- Tareas INT-01 a INT-04
- Sistema completo funcionando

## 📝 Notas Técnicas

- **Puerto Backend Local**: 8000 (HTTP + WebSocket para frontend)
- **Puerto Hardware**: 8080 (HTTP API - ya funcional)
- **Comunicación Hardware ↔ Backend**: HTTP RESTful bidireccional
- **Formato de Audio**: WAV, 16kHz, mono para transmisión
- **Protocolo Frontend**: WebSocket JSON para UI en tiempo real
- **Autenticación**: API Keys para backend remoto
- **Logging**: Request IDs y logging estructurado en ambos servicios

### 🔄 Cambios Arquitectónicos Importantes

1. **Prioridad HTTP sobre WebSocket**: El hardware ya tiene HTTP robusto, el backend debe consumirlo
2. **Backend como Cliente**: Backend local debe ser cliente del hardware (no al revés)
3. **Estados Sincronizados**: Hardware mantiene estado principal, backend lo replica
4. **WebSocket Opcional**: Para optimización futura, no bloqueante para MVP