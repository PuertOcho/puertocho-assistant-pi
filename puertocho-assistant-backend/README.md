# PuertoCho Assistant Backend Local

## ⚠️ Estado del Proyecto: REIMPLEMENTACIÓN NECESARIA

Este servicio está siendo **completamente reimplementado** para alinearse con la nueva arquitectura del hardware que ya cuenta con un HTTP Server robusto y funcional.

### 📋 Situación Actual

**❌ Backend Actual (Obsoleto)**:
- Simula estados en lugar de obtenerlos del hardware real
- No tiene cliente HTTP para comunicarse con hardware:8080
- WebSocket simplificado sin manejo robusto
- Procesamiento hardcodeado sin backend remoto

**✅ Hardware Funcional**:
- HTTP Server con 14 endpoints operativos
- StateManager robusto con estados bien definidos
- API completa documentada con OpenAPI/Swagger
- Tests completos (14/14 passing)

### 🎯 Nueva Arquitectura Backend Local

El backend local debe funcionar como **Gateway** entre hardware funcional y servicios remotos:

```
┌─────────────────┐     HTTP     ┌─────────────────┐     HTTP/WS     ┌─────────────────┐
│                 │─────────────▶│                 │────────────────▶│                 │
│  HARDWARE       │              │  BACKEND LOCAL  │                 │ BACKEND REMOTO  │
│  (Puerto 8080)  │◀─────────────│  (Puerto 8000)  │◀────────────────│ (Procesamiento) │
│                 │              │                 │                 │                 │
└─────────────────┘              └─────────────────┘                 └─────────────────┘
        │                                │                                    │
        │                                │                                    │
        ▼                                ▼                                    ▼
 📱 HTTP API                     🌐 Gateway                         🤖 IA/STT/TTS
 📡 StateManager                📊 Métricas                        ☁️ Cloud Services
 🎙️ Audio/VAD                  🔄 Buffer                          📈 Analytics
```

### 🔄 Plan de Reimplementación

**Ver archivo detallado**: [`REIMPLEMENTATION_PLAN.md`](./REIMPLEMENTATION_PLAN.md)

#### Responsabilidades del Nuevo Backend:

1. **🔗 Cliente del Hardware**: Consumir API del hardware (puerto 8080)
2. **📡 Servidor WebSocket**: Servir frontend en tiempo real  
3. **🎙️ Procesador de Audio**: Buffer y envío a backend remoto
4. **📊 Agregador de Estados**: Combinar hardware + backend + remoto
5. **🔄 Buffer Inteligente**: Cola cuando backend remoto no disponible

## 📋 Elementos Reutilizables del Backend Actual

### ✅ Mantener
- `Dockerfile.alternative` (Alpine optimizado)
- `requirements.txt` (dependencias básicas)
- Estructura FastAPI + uvicorn
- Middleware CORS básico

### 🔄 Actualizar Completamente
- `src/main.py` → Gateway principal
- `src/core/state_manager.py` → Cliente del hardware  
- `src/core/websocket_manager.py` → WebSocket robusto
- `src/api_v1.py` → Endpoints de gateway

### ➕ Añadir Nuevo
- `src/clients/hardware_client.py` → Cliente HTTP hardware:8080
- `src/services/audio_processor.py` → Buffer y cola de audio
- `src/services/remote_client.py` → Cliente backend remoto
- `src/middleware/logging.py` → Logging estructurado

## 🚀 Próximos Pasos

1. **📋 Revisar Plan Detallado**: [`REIMPLEMENTATION_PLAN.md`](./REIMPLEMENTATION_PLAN.md)
2. **🧹 Limpiar Código Actual**: Mantener elementos reutilizables
3. **🔌 Implementar Cliente Hardware**: Consumir API puerto 8080
4. **📊 StateManager Gateway**: Replicar estado del hardware  
5. **🎙️ Pipeline de Audio**: Buffer → Backend remoto
6. **🧪 Tests de Integración**: Hardware ↔ Backend funcional

## 📖 API Actual (OBSOLETA)

> ⚠️ **La API actual será reemplazada completamente**

### Endpoints REST (Serán Eliminados)

-   `POST /audio/process`: Simula procesamiento (será reemplazado)
-   `POST /hardware/status`: Recibe estado simulado (será cliente activo)

### WebSocket (Será Actualizado)

-   **URL Actual**: `ws://<host>:8000/ws` (se mantendrá para frontend)
-   **Cambios**: Transmitirá datos reales del hardware en lugar de simulaciones
-   **Descripción**: Canal principal para la comunicación en tiempo real con la interfaz web.

#### Mensajes del Backend hacia el Cliente
El backend envía mensajes para notificar al frontend sobre cambios de estado o eventos.

-   **`status_update`**: Informa sobre el estado del asistente.
    ```json
    {
      "type": "status_update",
      "payload": { "status": "idle|listening|processing|error" }
    }
    ```

-   **`hardware_status_update`**: Informa sobre el estado del hardware.
    ```json
    {
      "type": "hardware_status_update",
      "payload": { "microphone_ok": true, "state": "idle", ... }
    }
    ```

-   **`command_log`**: Envía un comando procesado para el historial.
    ```json
    {
      "type": "command_log",
      "payload": { "command": "...", "timestamp": 1234567890 }
    }
    ```
