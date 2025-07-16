
# PuertoCho Assistant - Hardware Client

Este módulo (`puertocho-assistant-hardware`) es el componente de hardware dedicado del ecosistema PuertoCho Assistant. Está diseñado para ejecutarse en una Raspberry Pi equipada con un **ReSpeaker 2-Mic Pi HAT V1.0**.

## 🚀 Visión General

El propósito principal de este servicio es actuar como un cliente ligero y eficiente que gestiona todas las interacciones de hardware. Sus responsabilidades clave son:

1.  **Detección de Wake Word**: Escucha continuamente la palabra de activación ("Puerto Ocho") utilizando el motor `Porcupine`.
2.  **Captura de Audio**: Una vez activado, graba el comando de voz del usuario.
3.  **Comunicación con el Backend**: Envía el audio capturado al `puertocho-assistant-backend` para su procesamiento (NLU, ejecución de acciones, etc.).
4.  **Feedback de Hardware**: Proporciona feedback visual al usuario a través de los LEDs RGB integrados en el ReSpeaker HAT y gestiona la entrada del botón físico.
5.  **Reporte de Estado**: Informa su estado operativo al backend para que pueda ser monitorizado, por ejemplo, desde `puertocho-assistant-web-view`.

## 🏗️ Arquitectura del Módulo (`app/`)

La lógica principal reside en la carpeta `app/`, que sigue una estructura limpia para separar responsabilidades.

### `main.py` / `main_modular.py`
-   **Propósito**: Es el punto de entrada de la aplicación.
-   **Funcionamiento**: Inicializa la clase `PuertoChoApp`, que a su vez instancia y ejecuta el `HardwareClient`. Configura los manejadores de señales para una terminación limpia del programa.

### `config.py`
-   **Propósito**: Actúa como el centro de configuración de la aplicación.
-   **Funcionamiento**:
    -   Carga variables de entorno desde un archivo `.env` ubicado en la raíz del proyecto.
    -   Define y valida todas las configuraciones críticas: `PORCUPINE_ACCESS_KEY`, URLs de los servicios de backend, pines GPIO, y rutas a archivos de modelos.
    -   Implementa la **detección automática del dispositivo de audio**, buscando específicamente el hardware ReSpeaker (`seeed-voicecard`).
    -   Proporciona métodos para obtener la configuración de audio y validar el entorno.

### `core/hardware_client.py`
-   **Propósito**: Es el corazón del servicio. Contiene toda la lógica operativa.
-   **Funcionamiento**:
    -   **Inicialización**: Prepara todos los componentes de hardware: GPIO, Porcupine, VAD (Voice Activity Detection) y el stream de audio con `sounddevice`.
    -   **Gestión de Estado**: Mantiene el estado actual del asistente (`IDLE`, `LISTENING`, `PROCESSING`, `ERROR`) y lo comunica al `led_controller`.
    -   **Bucle Principal**: En un bucle asíncrono, procesa el audio de la cola, lo analiza con Porcupine para detectar la wake word y gestiona la pulsación del botón físico.
    -   **Manejo de Comandos**: Al detectar la activación, orquesta el proceso de:
        1.  Cambiar al estado `LISTENING`.
        2.  Grabar el audio del usuario hasta detectar un silencio (`_record_until_silence`).
        3.  Cambiar al estado `PROCESSING`.
        4.  Empaquetar el audio en formato WAV en memoria.
        5.  Enviar el audio al backend (`_send_audio_to_backend`).
        6.  Volver al estado `IDLE`.

### `utils/`
Este paquete contiene módulos de utilidad que soportan al `hardware_client`.

-   **`led_controller.py`**:
    -   **Propósito**: Abstrae el control de los 3 LEDs RGB (APA102) integrados en el ReSpeaker HAT.
    -   **Funcionamiento**: Implementa patrones de animación para cada estado del asistente (`idle`, `wakeup`, `listening`, `thinking`, `speaking`, `error`), inspirados en asistentes como Google Home. Se ejecuta en un hilo separado para no bloquear el proceso principal.
-   **`apa102.py`**:
    -   **Propósito**: Driver de bajo nivel para comunicarse con los LEDs APA102 a través de la interfaz SPI de la Raspberry Pi.
-   **`logging_config.py`**:
    -   **Propósito**: Configuración centralizada del logging para mantener un formato consistente en toda la aplicación.

## 🔌 Conectividad con Otros Módulos

Este servicio no funciona de forma aislada. Su principal objetivo es conectar el hardware físico con el cerebro del asistente (`backend`).

### Con `puertocho-assistant-backend`

La comunicación se realiza a través de una API REST. El `hardware_client` consume dos endpoints principales del backend:

1.  **`POST /api/v1/audio/process`**:
    -   **Cuándo se usa**: Después de que el usuario dice un comando y este es grabado.
    -   **Qué envía**: Un `multipart/form-data` que contiene el audio grabado como un archivo `audio.wav`.
    -   **Qué espera**: Una respuesta JSON del backend confirmando que el audio fue recibido y está siendo procesado.
    -   **Robustez**: Incluye sistema de reintentos automáticos configurables para manejar errores de red.

2.  **`POST /api/v1/hardware/status`**:
    -   **Cuándo se usa**: Al iniciar la aplicación y periódicamente cada 60 segundos (configurable).
    -   **Qué envía**: Un objeto JSON con el estado actual de los componentes de hardware. Ejemplo:
        ```json
        {
            "microphone_ok": true,
            "gpio_ok": true,
            "porcupine_ok": true,
            "vad_ok": true,
            "rgb_leds_ok": true,
            "state": "idle",
            "audio_config": "16000 Hz (ReSpeaker 2-Mic Pi HAT V1.0 - device 2)"
        }
        ```
    -   **Propósito**: Permite al backend (y a otros servicios a través de él) conocer la salud y el estado del cliente de hardware en tiempo real.
    -   **Robustez**: Incluye manejo de errores y reintentos para garantizar que el backend esté siempre informado del estado del hardware.

### Con `puertocho-assistant-web-view`

La conexión es **indirecta**. El `hardware_client` no se comunica directamente con la interfaz web. El flujo es el siguiente:

1.  `hardware-client` envía su estado al `backend`.
2.  `web-view` solicita el estado del hardware al `backend`.
3.  El `backend` sirve la información que recibió previamente del `hardware-client`.

De esta manera, la `web-view` puede mostrar un dashboard con el estado en tiempo real del hardware de la Raspberry Pi.

## ⚙️ Configuración

La configuración se gestiona a través de un archivo `.env` en la raíz del proyecto. Las variables más importantes para este módulo son:

-   `PORCUPINE_ACCESS_KEY`: Clave de API de Picovoice para usar Porcupine. **(Obligatoria)**
-   `BACKEND_URL`: La URL base del servicio `puertocho-assistant-backend` (ej. `http://localhost:8000`).
-   `BACKEND_TIMEOUT`: Tiempo de espera para requests HTTP al backend (por defecto 30 segundos).
-   `BACKEND_RETRY_ATTEMPTS`: Número de intentos para requests fallidos (por defecto 3).
-   `BACKEND_RETRY_DELAY`: Delay entre reintentos (por defecto 1.0 segundos).
-   `HARDWARE_STATUS_INTERVAL`: Intervalo para envío periódico de estado del hardware (por defecto 60 segundos).
-   `BUTTON_PIN`: El pin GPIO para el botón físico (por defecto `17` para el ReSpeaker).
-   `LED_RGB_ENABLED`: `true` o `false` para habilitar/deshabilitar los LEDs RGB.
-   `LED_RGB_BRIGHTNESS`: Brillo de los LEDs (1-31).
-   `AUDIO_DEVICE_INDEX`: Permite forzar un índice de dispositivo de audio específico, aunque por defecto se autodetecta.

## 🚦 Estados de los LEDs RGB

Los LEDs integrados proporcionan feedback visual sobre el estado del asistente:

-   **Idle**: Luz azul muy tenue y estática. El asistente está en espera.
-   **Wakeup**: Animación de "despertar" con los colores base. Ocurre al detectar la wake word.
-   **Listening**: Luz constante con los colores base. El asistente está grabando el comando.
-   **Thinking**: Los colores rotan. El asistente ha enviado el audio y está esperando respuesta.
-   **Speaking**: Efecto de pulsación. El asistente está reproduciendo una respuesta de audio (TTS).
-   **Error**: Parpadeo en color rojo. Ha ocurrido un error en alguna parte del proceso.
-   **Off**: LEDs apagados.

## 🚀 Uso

Este servicio está diseñado para ser ejecutado como un contenedor de Docker a través del `docker-compose.yml` principal del proyecto. La configuración de Docker se encarga de mapear los dispositivos necesarios (`/dev/snd`, `/dev/gpiomem`, `/dev/spidev*`) dentro del contenedor.
