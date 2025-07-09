# PuertoCho Assistant Backend

Backend API que actúa como intermediario entre el dashboard web y los servicios de wake-word del asistente PuertoCho.

## Características

- ✅ Servidor WebSocket en el puerto 8765
- ✅ API REST con FastAPI
- ✅ Gestión de estado del asistente en tiempo real
- ✅ Broadcast de mensajes a múltiples clientes
- ✅ Logging estructurado
- ✅ Containerizado con Docker

## Desarrollo Local

### Con Docker (Recomendado)

```bash
# Construir y ejecutar
docker-compose up --build

# Solo ejecutar (si ya está construido)
docker-compose up
```

### Sin Docker

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
python src/main.py
```

## API

### WebSocket
- **URL**: `ws://localhost:8765/ws`
- **Protocolo**: JSON

#### Mensajes de entrada (desde frontend):
```json
{
  "type": "manual_activation"
}
```

#### Mensajes de salida (hacia frontend):
```json
{
  "type": "status_update",
  "payload": {
    "status": "idle|listening|processing|error"
  }
}

{
  "type": "command_log",
  "payload": {
    "command": "texto del comando",
    "timestamp": 1234567890123
  }
}
```

### REST Endpoints

- `GET /` - Información básica
- `GET /health` - Health check
- `POST /simulate/command` - Simular comando (testing)
- `POST /simulate/status` - Simular cambio de estado (testing)

## Arquitectura

```
Dashboard Web ←→ WebSocket (puerto 8765) ←→ Backend API
                                              ↓
                                         [Futuros servicios]
```
