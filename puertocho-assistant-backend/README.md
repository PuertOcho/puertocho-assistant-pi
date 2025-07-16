# PuertoCho Assistant Backend

## Descripción General

Este servicio es el **sistema nervioso central** del Asistente PuertoCho. Actúa como un **Gateway y Orquestador**, gestionando el estado del asistente y coordinando la comunicación entre el cliente de hardware (`puertocho-assistant-hardware`), la interfaz de usuario (`puertocho-assistant-web-view`), y los futuros servicios de procesamiento (NLU, TTS, etc.).

Su función principal es centralizar la lógica de estado (`idle`, `listening`, `processing`, `error`) y distribuir esta información a todos los componentes conectados, asegurando una experiencia de usuario coherente.

## Arquitectura y Comunicación

El backend está diseñado en torno a una **API REST** para la comunicación con el hardware y un servidor **WebSocket** para la comunicación en tiempo real con la interfaz web.

```
┌──────────────────────┐     HTTP POST     ┌───────────────────┐     WebSocket     ┌───────────────────┐
│  Hardware Service    ├──────────────────►│   Backend API     │◄──────────────────►│   Web Dashboard   │
│ (Envía audio/estado) │                   │    (Gateway)      │                   │  (Muestra estado) │
└──────────────────────┘                   └───────────────────┘                   └───────────────────┘
                                                     │
                                                     ▼
                                          (Futuro) Servicios Externos
                                             (STT, NLU, Chat, etc.)
```

El flujo de comunicación es el siguiente:
1.  El **Hardware Service** detecta la palabra de activación, graba un comando de voz y lo envía al endpoint `POST /api/v1/audio/process`.
2.  El **Backend API** recibe el audio:
    a. Cambia el estado del asistente a `processing`.
    b. Notifica este cambio a todos los clientes **Web Dashboard** conectados vía WebSocket.
    c. (Futuro) Envía el audio a un servicio de STT/NLU.
    d. Recibe el resultado, lo registra y lo envía al Web Dashboard.
    e. Vuelve al estado `idle` y lo notifica.
3.  Paralelamente, el **Hardware Service** envía su estado (micrófono OK, etc.) al endpoint `POST /api/v1/hardware/status`, y el backend lo retransmite a los dashboards.

## API de Comunicación

### Endpoints REST (Prefijo: `/api/v1`)

-   `POST /audio/process`:
    -   **Descripción**: Recibe un archivo de audio del servicio de hardware para su procesamiento.
    -   **Body**: `multipart/form-data` con un campo `audio` que contiene el archivo `.wav`.
    -   **Respuesta**: JSON con el estado del procesamiento y la transcripción (simulada por ahora).

-   `POST /hardware/status`:
    -   **Descripción**: Recibe un objeto JSON con el estado actual del hardware.
    -   **Body**: Objeto JSON con el estado del hardware (ej. `{"microphone_ok": true, "state": "idle"}`).
    -   **Respuesta**: JSON confirmando la recepción.

### WebSocket

-   **URL**: `ws://<host>:8000/ws`
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
