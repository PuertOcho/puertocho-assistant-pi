# TODO List - Puertocho Assistant Hardware

## Pendientes

### 1. Guardar audios en puertocho-assistant-backend para comprobar que se está enviando correctamente

- [x] **1.1 Implementar almacenamiento temporal en AudioProcessor**
  - [x] Crear directorio `/app/audio_verification` en backend
  - [x] Modificar `process_audio_from_hardware()` para guardar copia permanente
  - [x] Añadir configuración para habilitar/deshabilitar guardado de verificación
  - [x] Implementar limpieza automática de archivos antiguos
  
  **Decisiones de implementación:**
  - **Formato de nombre**: `verification_YYYYMMDD_HHMMSS_microsec_original_filename.wav`
  - **Retención**: 7 días por defecto o máximo 100 archivos (configurable)
  - **Estado por defecto**: Habilitado para debugging/development
  - **Variables de entorno**:
    - `AUDIO_VERIFICATION_ENABLED=true` (habilitar/deshabilitar)
    - `AUDIO_VERIFICATION_DAYS=7` (días de retención)
    - `AUDIO_VERIFICATION_MAX_FILES=100` (máximo archivos)
  - **Directorio**: `/app/audio_verification` (dentro del contenedor)
  - **Limpieza**: Al inicio del servicio y cada hora durante operación
  
  **✅ IMPLEMENTADO:** 
  - ✅ Configuración por variables de entorno añadida al docker-compose.yml
  - ✅ Directorio de verificación creado automáticamente al iniciar
  - ✅ Guardado automático de copia de verificación en `process_audio_from_hardware()`
  - ✅ Limpieza automática por edad (días) y cantidad máxima de archivos
  - ✅ Tarea periódica de limpieza cada hora
  - ✅ Logging detallado de todas las operaciones de verificación
  - ✅ Información de verificación incluida en `get_queue_status()`

- [x] **1.2 Mejorar logging de audio en backend**
  - [x] Añadir logs detallados en `gateway_endpoints.py` endpoint `/hardware/audio`
  - [x] Verificar metadatos del audio recibido (sample_rate, channels, duration)
  - [x] Registrar timestamp de recepción y procesamiento
  - [x] Implementar métricas de calidad del audio
  
  **✅ IMPLEMENTADO:**
  - ✅ Logging detallado en endpoint `/hardware/audio` con timestamps precisos
  - ✅ Análisis completo de metadatos de audio (formato, sample_rate, channels, bits_per_sample)
  - ✅ Métricas de calidad con validaciones de integridad
  - ✅ Sistema de puntuación de calidad y recomendaciones
  - ✅ Medición de tiempos de procesamiento en todas las etapas
  - ✅ Logging mejorado en `AudioProcessor` con métricas detalladas
  - ✅ Nuevos endpoints de verificación: `/audio/verification/status`, `/audio/verification/files`, `/audio/processing/history`
  - ✅ Validación de integridad de archivos de audio
  - ✅ Estadísticas de rendimiento y uso de espacio en disco

### 2. Preparar una primera interfaz gráfica con las nuevas implementaciones del backend

- [x] **2.1 Actualizar conexión WebSocket en web-view**
  - [x] Crear servicio WebSocket para conectar con backend (puerto 8000)
  - [x] Implementar manejo de mensajes de audio procesado
  - [x] Añadir store para estado de procesamiento de audio
  - [x] Integrar con `assistantStore.ts` existente

- [x] **2.2 Crear componentes de visualización de audio**
  - [x] Componente `AudioProcessor.svelte` para mostrar estado de procesamiento
  - [x] Componente `AudioHistory.svelte` para lista de audios procesados
  - [x] Componente `AudioPlayer.svelte` para reproducir audios guardados
  - [x] Visualizador de volumen en tiempo real

- [x] **2.3 Integrar con la interfaz existente**
  - [x] Añadir sección de audio a `+page.svelte`
  - [x] Actualizar `StatusIndicator.svelte` para incluir estado de audio
  - [x] Mejorar `CommandHistory.svelte` para mostrar audios asociados
  - [x] Implementar notificaciones de estado de procesamiento

**✅ IMPLEMENTADO:**
- ✅ WebSocket service actualizado para conectar correctamente al backend (puerto 8000)
- ✅ Store expandido con tipos TypeScript para audio processing
- ✅ Manejo completo de mensajes WebSocket: unified_state_update, audio_processing, hardware_event
- ✅ Componentes modulares: AudioProcessor, AudioHistory, AudioPlayer
- ✅ Dashboard con layout responsive de 2 columnas (comandos + audio)
- ✅ StatusIndicator mejorado con información de audio y queue
- ✅ AudioApiService para comunicación con endpoints del backend

**🚀 MEJORAS DE ESCALABILIDAD IMPLEMENTADAS:**
- ✅ **audioStore.ts**: Store separado y modular para audio con actions y auto-sync
- ✅ **appConfig.ts**: Sistema de configuración centralizado con overrides por entorno
- ✅ **errorHandling.ts**: Sistema robusto de manejo de errores y logging
- ✅ **performanceMonitor**: Monitoreo de rendimiento integrado
- ✅ **Arquitectura modular**: Separación clara de responsabilidades
- ✅ **TypeScript interfaces**: Contratos bien definidos entre componentes
- ✅ **Auto-recovery**: Recuperación automática de errores de red/WebSocket
- ✅ **Configuración por entorno**: Support para development/production
- ✅ **Error boundaries**: Manejo graceful de errores en UI
- ✅ **Performance tracking**: Métricas de rendimiento para debugging
  
  **✅ IMPLEMENTADO:**
  - ✅ WebSocket service actualizado para conectar al puerto 8000 del backend
  - ✅ Store expandido con tipos para audio processing (AudioProcessingState, AudioFile)
  - ✅ Manejo completo de mensajes WebSocket: unified_state_update, audio_processing, hardware_event
  - ✅ Componente AudioProcessor con estado en tiempo real, métricas y progreso visual
  - ✅ Componente AudioHistory con lista de archivos, controles de reproducción y descarga
  - ✅ Componente AudioPlayer con controles completos, barra de progreso y volumen
  - ✅ Dashboard con layout de 2 columnas: comandos + audio processing
  - ✅ StatusIndicator actualizado con estado de audio y queue length
  - ✅ Servicio audioApiService.ts para comunicación con endpoints del backend
  - ✅ Interfaz responsive con adaptación móvil
  - ✅ Integración completa con el sistema de estados unificado del backend

### 3. Modo kiosko y táctil para puertocho-assistant-web-view ✅

- [x] **3.1 Configuración de arranque automático**
  - [x] Crear script de inicio que lance en modo fullscreen
  - [x] Configurar autostart en Raspberry Pi
  - [x] Añadir parámetros de línea de comandos para kiosko
  - [x] Implementar detección automática de pantalla táctil

- [x] **3.2 Optimización para pantalla táctil**
  - [x] Aumentar tamaño de botones y elementos interactivos
  - [x] Implementar gestos táctiles (swipe, tap, long press)
  - [x] Añadir feedback visual para interacciones táctiles
  - [x] Optimizar layout para resoluciones de pantalla pequeñas

- [x] **3.3 Configuración del sistema**
  - [x] Crear dockerfile con configuración de kiosko
  - [x] Añadir variables de entorno para modo kiosko
  - [x] Configurar nginx para servir en modo fullscreen
  - [x] Implementar script de reinicio automático en caso de error

**✅ IMPLEMENTADO:**
- ✅ **Scripts de kiosko**: `kiosk-launcher.sh` y `kiosk-control.sh` para gestión completa del modo kiosko
- ✅ **Docker configurado**: Dockerfile con todas las dependencias X11, chromium y supervisor
- ✅ **Supervisor**: Gestión de procesos nginx + kiosk con reinicio automático
- ✅ **Variables de entorno**: Sistema completo de configuración (KIOSK_MODE, DISPLAY, resolución)
- ✅ **X11 integrado**: Montaje correcto de socket X11 para acceso desde contenedor
- ✅ **Auto-arranque**: Configuración permanente de DISPLAY y xhost en .bashrc
- ✅ **Interface responsive**: Dashboard adaptado automáticamente a resoluciones de pantalla pequeñas
- ✅ **Gestión de errores**: Sistema robusto de recuperación automática ante fallos
- ✅ **Logging completo**: Sistema de logs detallado para depuración y monitoreo
- ✅ **Configuración persistente**: Archivo .env con todas las variables del kiosko configuradas
- ✅ **Pantalla completa**: Chromium lanzado en modo fullscreen sin bordes ni barras
- ✅ **Compatibilidad Raspberry Pi**: Funcionamiento verificado en hardware real con pantalla táctil

### 4. Reproducir el audio recibido desde hardware como respuesta ✅

**OBJETIVO**: Implementar comunicación completa con Backend Remoto y reproducción de respuestas de audio.

**ARQUITECTURA**:
```
┌─────────────────┐     HTTP/WS    ┌─────────────────┐     HTTP/Auth   ┌─────────────────┐
│   HARDWARE      │◄──────────────►│  BACKEND LOCAL  │◄───────────────►│ BACKEND REMOTO  │
│ (Puerto 8080)   │                │ (Puerto 8000)   │                 │ (Puerto 10002)  │
│ - Captura audio │                │ - Orquestador   │                 │ - Procesamiento │
│ - Reproduce     │                │ - Auth Manager  │                 │ - IA/LLM        │
│   respuestas    │                │ - Client HTTP   │                 │ - TTS/STT       │
└─────────────────┘                └─────────────────┘                 └─────────────────┘
        ▲                                  ▲
        │ WebSocket                        │ WebSocket
        │                                  ▼
        │                          ┌─────────────────┐
        └──────────────────────────│    WEB VIEW     │
                                   │ (Puerto 3000)   │
                                   │ - Control UI    │
                                   │ - Monitoreo     │
                                   └─────────────────┘
```

**CREDENCIALES BACKEND REMOTO**:
- **URL**: `http://192.168.1.88:10002`
- **Email**: `service@puertocho.local`
- **Password**: `servicepass123`

- [x] **4.1 Implementar Cliente de Backend Remoto**
  - [x] Crear `RemoteBackendClient` en `puertocho-assistant-backend/src/clients/remote_backend_client.py`
  - [x] Implementar autenticación automática con auto-renovación de tokens
  - [x] Añadir método `send_audio_for_processing()` con manejo de multipart/form-data
  - [x] Integrar manejo de errores y reintentos
  - [x] Añadir configuración por variables de entorno
  
  **✅ IMPLEMENTADO:**
  - ✅ **RemoteBackendClient**: Cliente completo con autenticación JWT y auto-renovación
  - ✅ **Variables de entorno**: Configuración completa en docker-compose.yml
  - ✅ **Multipart upload**: Soporte para envío de audio con metadata y contexto
  - ✅ **Error handling**: Reintentos automáticos y manejo robusto de errores
  - ✅ **Health check**: Endpoint `/remote/status` para verificar conectividad
  - ✅ **Lifecycle management**: Inicialización automática en startup del backend
  - ✅ **Timeout configuration**: Configuración extendida para audio (60s por defecto)
  - ✅ **Token management**: Renovación automática 5 minutos antes de expiración
  - ✅ **Testing endpoint**: `/remote/test-auth` para diagnóstico de autenticación

- [x] **4.2 Rediseñar IntentManagerMS con LLM-RAG y Arquitectura MoE**
  - *Objetivo*: Implementación completamente nueva de intentmanagerms usando arquitectura LLM-RAG + Mixture of Experts (MoE) para clasificación de intenciones escalable, conversación multivuelta inteligente y soporte nativo MCP.

- [x] **4.3 Actualizar AudioProcessor para Backend Remoto**
  - [x] Modificar `_send_to_remote_backend()` en `audio_processor.py`
  - [x] Implementar manejo de respuestas por tipo: `audio`, `text`, `action`
  - [x] Añadir método `_handle_audio_response()` para coordinar reproducción
  - [x] Integrar con `HardwareClient` para envío de audio a reproductor
  - [x] Actualizar flujo de WebSocket para notificar respuestas

- [x] **4.3 Estructura de Datos Escalable para Comunicación Backend Local ↔ Remoto**
  - [x] Diseñar protocolo multipart/form-data para comunicación flexible entre puertocho-assistant-backend y backend remoto
  - [x] Implementar estructura con campos obligatorios: audio binario (bytes WAV) y metadata con timestamp ISO
  - [x] Añadir soporte para campos opcionales: context con ubicación, temperatura, configuración de dispositivo, etc.
  - [x] Asegurar escalabilidad: Usar diccionarios JSON que permitan añadir keys futuras sin romper compatibilidad
  - [x] Mapear context opcional con DeviceContext de intentmanagerms (location→room, temperature→temperature, etc.)
  - [x] Integrar obtención dinámica de context desde hardware status o configuración local
  - [x] Actualizar remote_backend_client.py para enviar estructura completa al backend remoto
  - [x] Documentar estructura con ejemplos de payload en README.md
  - [x] Implementar validación opcional con schemas (Pydantic) para metadata y context
  - [x] Añadir variables de entorno para habilitar/deshabilitar envío de datos opcionales (ENABLE_CONTEXT=true)

- [x] **4.4 Implementar Reproducción en Hardware**
  - [x] Crear endpoint `/audio/play` en `http_server.py`
  - [x] Añadir método `play_response_audio()` en `audio_manager.py`
  - [x] Implementar decodificación de audio Base64 y conversión a numpy
  - [x] Manejar reproducción con chunks y control de stream
  - [x] Añadir estado `SPEAKING` al `StateManager`

- [x] **4.5 Integrar Cliente Hardware en Backend**
  - [x] Añadir método `play_audio_response()` en `hardware_client.py`
  - [x] Implementar serialización Base64 para envío de audio
  - [x] Manejar metadata y contexto de respuesta
  - [x] Coordinar con WebSocket para notificaciones en tiempo real

- [x] **4.6 Actualizar Variables de Entorno y Configuración**
  - [x] Añadir variables `REMOTE_BACKEND_*` al `docker-compose.yml`
  - [x] Configurar credenciales: URL, usuario, password
  - [x] Actualizar `main.py` para inicializar cliente remoto
  - [x] Implementar gestión de ciclo de vida (startup/shutdown)

- [x] **4.7 Testing de Flujo Completo**
  - [x] Probar autenticación con Backend Remoto
  - [x] Validar envío de audio con metadata y context opcionales
  - [x] Verificar recepción y reproducción de respuestas
  - [x] Testing de latencia y calidad de audio
  - [x] Pruebas de recuperación ante errores de red
  - [x] Testing de escalabilidad: añadir campos nuevos sin romper compatibilidad

**FLUJO IMPLEMENTADO**:
1. **Hardware** captura audio → envía a **Backend Local**
2. **Backend Local** autentica con **Backend Remoto** → envía audio
3. **Backend Remoto** procesa → devuelve respuesta (audio/texto/acción)
4. **Backend Local** recibe respuesta → coordina reproducción en **Hardware**
5. **Hardware** reproduce audio → notifica finalización
6. **Web View** muestra estado en tiempo real durante todo el proceso

---

### 5. Mejoras en la vista de puertocho-assistant-web-view

**OBJETIVO**: Rediseñar completamente la interfaz con una estructura de 3 secciones para una mejor experiencia de usuario.

**NUEVA ARQUITECTURA DE VISTA**:
```
┌──────────┬───────────────────────────────────────────────────────────────────────────┐
│          │                           COLUMNA SUPERIOR (7% alto)                      │
│          │ Audio Wave │ Controles Audio │ Estado Asistente │ Estado Conexión Server │
│ COLUMNA  ├───────────────────────────────────────────────────────────────────────────┤
│ IZQDA    │                                                                           │
│ (10%)    │                           VISTA PRINCIPAL                                 │
│          │                           (90% ancho, 93% alto)                          │
│ • Home   │                                                                           │
│ • Config │  HOME: Botones 5xN (izq.) + Chat (der.)                                 │
│ • ...    │  CONFIG: Configuración voz, volumen, modelo                              │
│ (scroll) │  Otras vistas según icono activo                                        │
│          │                                                                           │
└──────────┴───────────────────────────────────────────────────────────────────────────┘
```

- [ ] **5.1 Restructurar layout principal**
  - [ ] Crear nuevo componente `ThreeColumnLayout.svelte` para reemplazar la estructura actual
  - [ ] Implementar CSS Grid/Flexbox con proporciones: 10% izquierda, 7% superior, resto principal
  - [ ] Migrar contenido actual a la nueva estructura
  - [ ] Asegurar responsividad para pantallas táctiles y móviles

- [ ] **5.2 Desarrollar columna izquierda (Navegación)**
  - [ ] Crear componente `SideNavigation.svelte` con scroll vertical
  - [ ] Implementar iconos: Home (por defecto), Configuración, y expandibles futuros
  - [ ] Añadir sistema de estado activo/inactivo para iconos
  - [ ] Integrar store para manejo de vista activa (`navigationStore.ts`)

- [ ] **5.3 Desarrollar columna superior (Info en tiempo real)**
  - [ ] Crear componente `TopStatusBar.svelte` con 4 secciones:
    - [ ] **AudioWave**: Visualizador de onda de audio en tiempo real
    - [ ] **AudioControls**: Botones detener/pausar/iniciar grabación
    - [ ] **AssistantStatus**: Estado actual del asistente (idle/listening/processing)
    - [ ] **ConnectionStatus**: Estado conexión backend/hardware con indicadores visuales
  - [ ] Integrar con stores existentes: `assistantStore`, `audioStore`
  - [ ] Añadir animaciones y transiciones suaves

- [ ] **5.4 Implementar Vista Principal - Home**
  - [ ] Crear componente `HomeView.svelte` con layout 50/50:
    - [ ] **Izquierda**: Componente `ButtonMatrix.svelte` - Matriz de botones 5xN configurable
    - [ ] **Derecha**: Componente `ChatInterface.svelte` - Chat en tiempo real
  - [ ] Implementar sistema de botones personalizables (comandos rápidos)
  - [ ] Integrar chat con historial de comandos y respuestas
  - [ ] Añadir configuración de dimensiones de matriz (5xN ajustable)

- [ ] **5.5 Implementar Vista Principal - Configuración**
  - [ ] Crear componente `ConfigView.svelte` con secciones:
    - [ ] **Configuración de Voz**: Velocidad, tono, idioma
    - [ ] **Volumen de Audio**: Controles entrada/salida, niveles
    - [ ] **Modelo del Asistente**: Selección y parámetros IA
    - [ ] **Preferencias UI**: Tema, tamaños, animaciones
  - [ ] Implementar store `configStore.ts` para persistir configuraciones
  - [ ] Añadir validación y guardado automático de cambios

- [ ] **5.6 Sistema de enrutamiento interno**
  - [ ] Crear `viewRouter.ts` para manejar cambios entre vistas principales
  - [ ] Implementar transiciones suaves entre vistas
  - [ ] Añadir historial de navegación y botón "atrás"
  - [ ] Integrar con el store de navegación

- [ ] **5.7 Optimización para pantallas táctiles**
  - [ ] Aumentar área táctil de todos los elementos interactivos (mínimo 44px)
  - [ ] Implementar feedback visual inmediato en toques
  - [ ] Añadir soporte para gestos: swipe para cambiar vistas, tap largo para opciones
  - [ ] Optimizar para resoluciones comunes de Pi con pantalla táctil

- [ ] **5.8 Estados y stores actualizados**
  - [ ] Crear `navigationStore.ts`: Vista activa, historial, configuración navigation
  - [ ] Extender `configStore.ts`: Todas las configuraciones de usuario
  - [ ] Actualizar `assistantStore.ts`: Integrar con nueva estructura
  - [ ] Añadir `uiStore.ts`: Estados de UI, animaciones, preferencias visuales

- [ ] **5.9 Testing y documentación**
  - [ ] Testing en diferentes resoluciones y dispositivos táctiles
  - [ ] Documentar nueva estructura de componentes
  - [ ] Crear guía de uso para la nueva interfaz
  - [ ] Screenshots y videos demostrativos de la nueva UI
