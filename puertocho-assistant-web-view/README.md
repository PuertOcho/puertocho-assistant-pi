# PuertoCho Assistant - Web Dashboard

## Descripción General

Este proyecto es la cara visible del Asistente PuertoCho. Es un dashboard web interactivo, construido con Svelte, que permite a los usuarios visualizar el estado del asistente en tiempo real y controlar algunas de sus funciones. Su principal objetivo es proporcionar una retroalimentación visual clara y una forma de interacción manual con el sistema.

## Arquitectura y Comunicación

El dashboard es una aplicación de una sola página (SPA) que se comunica directamente con el **PuertoCho Assistant Backend** a través de una conexión WebSocket persistente. Esta arquitectura permite que el backend empuje actualizaciones de estado al dashboard instantáneamente, sin que el cliente necesite preguntar (polling).

```
Dashboard Web (Svelte) ←───── WebSocket (ws://.../ws) ─────→ Backend API
(Este proyecto)
```

El flujo de comunicación es el siguiente:
1.  Al cargar la aplicación en el navegador, el servicio `websocketService.ts` establece una conexión con el endpoint `ws://localhost:8765/ws` del backend.
2.  El dashboard se suscribe a los mensajes del backend para actualizar la interfaz de usuario.
3.  Cuando el usuario realiza una acción, como presionar el botón de "Activación Manual", el dashboard envía un mensaje JSON específico al backend.
4.  El backend procesa la solicitud y notifica a todos los clientes (incluido este) sobre cualquier cambio de estado o nuevo comando registrado.

## API de Comunicación (WebSocket)

La comunicación se basa en un intercambio de mensajes JSON tipados.

### Mensajes que el Dashboard Escucha (del Backend)

Estos mensajes actualizan la UI en tiempo real.

```json
{
  "type": "status_update",
  "payload": { "status": "idle|listening|processing|error" }
}
```
- **Reacción**: Al recibir este mensaje, el `assistantStore` se actualiza, y los componentes de Svelte que dependen de él (como el `StatusIndicator.svelte`) cambian su apariencia visual para reflejar el nuevo estado.

```json
{
  "type": "command_log",
  "payload": { "command": "...", "timestamp": "..." }
}
```
- **Reacción**: Este mensaje añade el comando recibido al historial. El componente `CommandHistory.svelte` muestra la lista actualizada de comandos.

### Mensajes que el Dashboard Envía (al Backend)

Estos mensajes inician acciones en el asistente.

```json
{
  "type": "manual_activation"
}
```
- **Acción**: Se envía cuando el usuario hace clic en el componente `ManualActivation.svelte`, solicitando al backend que inicie el ciclo de escucha del asistente.
