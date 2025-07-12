# Wake-Word Service (Porcupine Version)

## Descripción General

Este servicio es el oído del Asistente PuertoCho. Su responsabilidad es escuchar constantemente en el entorno físico a través de un micrófono para detectar una palabra de activación específica ("wake word"). Una vez detectada, graba el comando de voz del usuario y lo delega a otros servicios para su procesamiento. Interactúa directamente con el hardware de la Raspberry Pi para controlar LEDs de estado y leer un botón de activación manual.

## Arquitectura y Funcionamiento

El servicio opera en un bucle continuo con los siguientes pasos:

1.  **Inicialización**: Carga la configuración, incluyendo las URLs de los servicios externos y las claves de API para el motor de wake word (Porcupine). Inicializa los pines GPIO para los LEDs (estado "preparado" y "escuchando") y el botón de activación manual.
2.  **Detección de Wake Word**: Entra en un estado de escucha activa (`idle`), procesando el audio del micrófono en tiempo real con Porcupine. El LED de estado "preparado" (verde) permanece encendido.
3.  **Activación**: Al detectar la palabra clave ("Hola Puertocho" o "Oye Puertocho") o al recibir una pulsación del botón físico, el servicio transiciona:
    *   Cambia su estado interno a `listening`.
    *   Apaga el LED "preparado" y enciende el LED "escuchando" (rojo).
4.  **Grabación del Comando**: Graba el audio del usuario hasta que detecta un periodo de silencio. Utiliza `webrtcvad` (Voice Activity Detection) para determinar de forma inteligente el final del habla del usuario.
5.  **Delegación del Comando**: Una vez finalizada la grabación, cambia su estado a `processing`. El audio grabado se encapsula en un archivo `.wav` y se envía a un servicio externo para su interpretación.
6.  **Vuelta al Estado Inicial**: Tras completar el ciclo, vuelve a su estado `idle` para esperar la siguiente palabra de activación.

## Comunicación con Otros Servicios

Este servicio no procesa el lenguaje natural directamente; su función es actuar como un sensor de voz y delegar esa tarea. La comunicación se realiza a través de **peticiones HTTP POST**.

El servicio tiene dos modos de operación, que se seleccionan automáticamente al inicio dependiendo de los servicios que encuentre disponibles en la red:

### Modo 1: Conversacional (Preferido)

Este modo se activa si el **Servicio de Chat del Asistente** está disponible.

*   **Endpoint de destino**: `ASSISTANT_CHAT_URL` (configurable).
*   **Flujo de comunicación**:
    1.  Primero, envía el audio grabado al **Servicio de Transcripción** para convertir la voz a texto.
    2.  Luego, envía el texto ya transcrito al **Servicio de Chat del Asistente**.
    3.  Este modo permite conversaciones contextuales y respuestas complejas. Si el servicio de chat devuelve una URL de audio con una respuesta sintetizada (TTS), este servicio de wake-word se encarga de descargarla y reproducirla.

```
┌───────────────────────────┐      ┌───────────────────────────┐      ┌────────────────────────┐
│ Wake-Word Service         │      │ Transcription Service     │      │ Assistant Chat Service │
│ (Este proyecto)           │      │ (Externo)                 │      │ (Externo)              │
├───────────────────────────┤      ├───────────────────────────┤      ├────────────────────────┤
│ 1. Graba audio            │      │                           │      │                        │
│ 2. Envía audio.wav        ├─────►│ 3. Transcribe a texto     │      │                        │
│                           │      │ 4. Devuelve texto         │◄─────┤                        │
│ 5. Recibe texto           │      │                           │      │                        │
│ 6. Envía texto            │      │                           ├─────►│ 7. Procesa conversación  │
│                           │      │                           │      │ 8. Devuelve respuesta  │
│ 9. Recibe y reproduce     │◄─────│                           │◄─────┤                        │
└───────────────────────────┘      └───────────────────────────┘      └────────────────────────┘
```

### Modo 2: Fallback (Comandos Locales)

Este modo se activa si el servicio de chat no está disponible, pero sí el de transcripción.

*   **Endpoint de destino**: `TRANSCRIPTION_SERVICE_URL` (configurable).
*   **Flujo de comunicación**:
    1.  Envía el audio grabado directamente al **Servicio de Transcripción**.
    2.  Recibe el texto transcrito y busca una coincidencia exacta en su archivo local `commands.json`.
    3.  Si encuentra una coincidencia, ejecuta la acción asociada (ej. encender/apagar un LED conectado a un pin GPIO).
*   Este modo es más limitado, no tiene memoria conversacional y solo responde a un conjunto predefinido de comandos.