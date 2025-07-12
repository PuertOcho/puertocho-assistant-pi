# PuertoCho Assistant Backend

## Descripción General

Este servicio es el sistema nervioso central del Asistente PuertoCho. Actúa como un intermediario inteligente que gestiona el estado del asistente y orquesta la comunicación en tiempo real entre la interfaz de usuario (el dashboard web) y los componentes de procesamiento de voz (como el servicio de wake-word).

Su función principal es centralizar la lógica de estado (`idle`, `listening`, `processing`, `error`) y distribuir esta información a todos los clientes conectados, asegurando que la interfaz de usuario siempre refleje el estado actual del asistente.

## Arquitectura y Comunicación

El backend está diseñado en torno a un servidor WebSocket para la comunicación bidireccional y en tiempo real, y una API REST para tareas síncronas como health checks o simulaciones.

```
Dashboard Web (Cliente) ←───── WebSocket (ws://.../ws) ─────→ Backend API
                                                                  │
                                                                  ↓
                                                    (Futuro) Servicio de Wake-Word
```

El flujo de comunicación es el siguiente:
1.  El **Dashboard Web** establece una conexión persistente con el backend a través de WebSocket.
2.  Cuando ocurre un evento (ej. un usuario presiona el botón de activación manual en el dashboard), el cliente envía un mensaje JSON al backend.
3.  El backend recibe el mensaje, actualiza el estado interno del asistente y, a su vez, notifica a **todos** los clientes conectados sobre este cambio de estado (`status_update`).
4.  Si se procesa un comando, se registra y se envía a los clientes (`command_log`) para que se muestre en el historial.

## API de Comunicación

### WebSocket

- **URL**: `ws://<host>:8765/ws`
- **Descripción**: Es el canal principal para la comunicación asíncrona y en tiempo real.

#### Mensajes del Cliente hacia el Backend
El frontend envía mensajes para iniciar acciones en el asistente.

```json
{
  "type": "manual_activation"
}
```
- **`manual_activation`**: Solicita al backend que inicie el ciclo de escucha del asistente, simulando la detección de la palabra de activación.

#### Mensajes del Backend hacia el Cliente
El backend envía mensajes para notificar al frontend sobre cambios de estado o eventos.

```json
{
  "type": "status_update",
  "payload": {
    "status": "idle|listening|processing|error"
  }
}
```
- **`status_update`**: Informa al dashboard sobre el estado actual del asistente para que la UI pueda reaccionar visualmente (ej. mostrar un ícono de "escuchando").

```json
{
  "type": "command_log",
  "payload": {
    "command": "texto del comando reconocido",
    "timestamp": 1234567890123
  }
}
```
- **`command_log`**: Envía un comando que ha sido procesado para que el dashboard lo muestre en el historial de comandos.

### Endpoints REST

- `GET /`: Endpoint de información básica del servicio.
- `GET /health`: Proporciona un health check para monitorización y diagnóstico.
- `POST /simulate/command`: Permite simular la recepción de un comando. Útil para desarrollo y pruebas.
- `POST /simulate/status`: Permite forzar un cambio de estado en el asistente. Útil para desarrollo y pruebas.
