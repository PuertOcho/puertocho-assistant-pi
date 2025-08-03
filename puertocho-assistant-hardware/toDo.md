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

### 3. Modo kiosko y táctil para puertocho-assistant-web-view

- [ ] **3.1 Configuración de arranque automático**
  - [ ] Crear script de inicio que lance en modo fullscreen
  - [ ] Configurar autostart en Raspberry Pi
  - [ ] Añadir parámetros de línea de comandos para kiosko
  - [ ] Implementar detección automática de pantalla táctil

- [ ] **3.2 Optimización para pantalla táctil**
  - [ ] Aumentar tamaño de botones y elementos interactivos
  - [ ] Implementar gestos táctiles (swipe, tap, long press)
  - [ ] Añadir feedback visual para interacciones táctiles
  - [ ] Optimizar layout para resoluciones de pantalla pequeñas

- [ ] **3.3 Configuración del sistema**
  - [ ] Crear dockerfile con configuración de kiosko
  - [ ] Añadir variables de entorno para modo kiosko
  - [ ] Configurar nginx para servir en modo fullscreen
  - [ ] Implementar script de reinicio automático en caso de error

### 4. Reproducir el audio recibido desde hardware como respuesta

- [ ] **4.1 Implementar reproducción en AudioManager (hardware)**
  - [ ] Añadir método `play_response_audio()` en `audio_manager.py`
  - [ ] Integrar con sistema de eventos existente
  - [ ] Manejar cola de reproducción para múltiples respuestas
  - [ ] Implementar control de volumen

- [ ] **4.2 Configurar recepción de respuestas desde backend**
  - [ ] Crear endpoint en hardware para recibir audio de respuesta
  - [ ] Modificar WebSocket client para manejar respuestas de audio
  - [ ] Implementar deserialización de audio base64
  - [ ] Añadir validación de formato de audio recibido

- [ ] **4.3 Integración con flujo de estados**
  - [ ] Modificar StateManager para estado `PLAYING_RESPONSE`
  - [ ] Actualizar LED patterns para indicar reproducción
  - [ ] Implementar timeout para respuestas largas
  - [ ] Añadir manejo de interrupciones durante reproducción

- [ ] **4.4 Testing y validación**
  - [ ] Crear tests para ciclo completo: captura → envío → respuesta → reproducción
  - [ ] Validar latencia total del sistema
  - [ ] Testing de calidad de audio (pérdida en compresión/transmisión)
  - [ ] Pruebas de estabilidad con múltiples ciclos

## Completadas

<!-- Las tareas completadas se moverán aquí -->