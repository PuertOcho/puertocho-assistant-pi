# Project Tracker: PuertoCho Assistant - Web Dashboard

Este documento sirve como backlog para el desarrollo de la interfaz web del asistente PuertoCho.

## Fase 1: Fundación y Conexión (MVP - Producto Mínimo Viable)

El objetivo de esta fase es tener un dashboard funcional de solo lectura que refleje el estado del asistente en tiempo real.

-   [x] **Tarea 1: Inicializar el Proyecto Web con Svelte.**
    -   [x] Configurar un nuevo proyecto Svelte utilizando `vite`.
    -   [x] Estructurar las carpetas iniciales (`src/lib`, `src/routes`, etc.).
    -   [x] Asegurar que el servidor de desarrollo funcione correctamente.
    -   [x] Crear `Dockerfile` para containerizar la aplicación web.
    -   [x] Crear `docker-compose.yml` para orquestar el frontend web y facilitar el desarrollo.

-   [x] **Tarea 2: Diseñar la Interfaz de Usuario (UI) Básica.**
    -   [x] Crear el componente `StatusIndicator.svelte` para mostrar el estado del asistente.
    -   [x] Crear el componente `CommandHistory.svelte` para mostrar los comandos procesados.
    -   [x] Ensamblar los componentes en la vista principal (`+page.svelte`).

-   [x] **Tarea 3: Implementar Conexión en Tiempo Real (WebSocket).**
    -   [x] Crear un servicio o store para gestionar la conexión WebSocket.
    -   [x] Implementar la lógica de conexión, recepción de mensajes y manejo de errores/desconexiones.
    -   [x] Definir stores de Svelte para el estado del asistente y el historial de comandos.

-   [x] **Tarea 4: Vincular la UI con los Datos en Tiempo Real.**
    -   [x] Suscribir los componentes de la UI a los stores para que se actualicen automáticamente.
    -   [x] Asegurar que el estado (`listening`, `processing`, etc.) y los comandos se reflejen en la UI.

-   [x] **Tarea 5: Interactividad Básica (Fase 2).**
    -   [x] Añadir un botón de "activación manual" en la UI.
    -   [x] Implementar la lógica para enviar un mensaje de activación al backend vía WebSocket.

## Fase 3: Mejoras y Refinamiento

-   [ ] **Tarea 6: Estilo y Diseño Visual.**
    -   [ ] Aplicar CSS para que el dashboard sea visualmente atractivo y claro.
    -   [ ] Asegurar que el diseño sea responsive (se vea bien en móvil y escritorio).

-   [ ] **Tarea 7: Configuración.**
    -   [ ] Añadir una página de configuración para, por ejemplo, cambiar la URL del backend.

-   [x] **Tarea 8: Optimización para Producción.**
    -   [x] Configurar el proceso de `build` para generar los archivos estáticos optimizados.
    -   [ ] Documentar cómo servir estos archivos desde el backend de Python.
    -   [x] Optimizar el `Dockerfile` para producción (multi-stage build).
    -   [ ] Crear documentación de despliegue con Docker en Raspberry Pi.
