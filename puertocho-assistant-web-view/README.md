# PuertoCho Assistant - Web Dashboard

Dashboard web en Svelte con soporte para hot-reload y modo kiosk.

## Configuración

### Variables de entorno principales

```bash
# Hot-reload (desarrollo)
HOT_RELOAD_ENABLED=true    # true/false - Habilita servidor de desarrollo Vite

# Kiosk (pantalla completa)
KIOSK_MODE=true           # true/false - Habilita modo kiosk con navegador
KIOSK_RESOLUTION=800x480  # Resolución de pantalla
DISPLAY=:0                # Display X11

# Configuración de HMR
VITE_HMR_PORT=24678
CHOKIDAR_USEPOLLING=true
CHOKIDAR_INTERVAL=1000
```

## Modos de operación

### 1. Desarrollo con hot-reload (sin kiosk)
```bash
HOT_RELOAD_ENABLED=true
KIOSK_MODE=false
```
- Inicia servidor Vite en puerto 3000
- Cambios en código se reflejan automáticamente
- Accesible en navegador normal

### 2. Desarrollo con hot-reload + kiosk
```bash
HOT_RELOAD_ENABLED=true
KIOSK_MODE=true
```
- Inicia servidor Vite en puerto 3000
- Abre navegador Chromium en modo kiosk
- Cambios en código se reflejan en la pantalla kiosk

### 3. Producción sin kiosk
```bash
HOT_RELOAD_ENABLED=false
KIOSK_MODE=false
```
- Construye aplicación estática
- Sirve con nginx en puerto 3000

### 4. Producción con kiosk
```bash
HOT_RELOAD_ENABLED=false
KIOSK_MODE=true
```
- Construye aplicación estática
- Sirve con nginx + abre navegador en modo kiosk

## Arquitectura

- **docker-entrypoint.sh**: Punto de entrada principal
- **supervisor.conf**: Gestiona nginx y kiosk browser
- **kiosk-launcher.sh**: Lanza navegador en modo kiosk
- **supervisor-control.sh**: Controla dinámicamente nginx según configuración

## Puertos

- **3000**: Puerto principal del dashboard
- **24678**: Puerto HMR para hot-reload

## Volúmenes importantes

- `./src:/app/src`: Código fuente (para hot-reload)
- `./static:/app/static`: Archivos estáticos
- `/tmp/.X11-unix:/tmp/.X11-unix:rw`: Socket X11 (para kiosk)

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
