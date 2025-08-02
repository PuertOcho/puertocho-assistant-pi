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

- [ ] **1.2 Mejorar logging de audio en backend**
  - [ ] Añadir logs detallados en `gateway_endpoints.py` endpoint `/hardware/audio`
  - [ ] Verificar metadatos del audio recibido (sample_rate, channels, duration)
  - [ ] Registrar timestamp de recepción y procesamiento
  - [ ] Implementar métricas de calidad del audio

- [ ] **1.3 Verificar transmisión WebSocket**
  - [ ] Confirmar que `_send_captured_audio_to_backend()` en hardware funciona correctamente
  - [ ] Validar formato base64 y metadatos enviados
  - [ ] Verificar que WebSocketManager recibe y procesa correctamente
  - [ ] Añadir endpoint para verificar archivos recibidos

### 2. Preparar una primera interfaz gráfica con las nuevas implementaciones del backend

- [ ] **2.1 Actualizar conexión WebSocket en web-view**
  - [ ] Crear servicio WebSocket para conectar con backend (puerto 8000)
  - [ ] Implementar manejo de mensajes de audio procesado
  - [ ] Añadir store para estado de procesamiento de audio
  - [ ] Integrar con `assistantStore.ts` existente

- [ ] **2.2 Crear componentes de visualización de audio**
  - [ ] Componente `AudioProcessor.svelte` para mostrar estado de procesamiento
  - [ ] Componente `AudioHistory.svelte` para lista de audios procesados
  - [ ] Componente `AudioPlayer.svelte` para reproducir audios guardados
  - [ ] Visualizador de volumen en tiempo real

- [ ] **2.3 Integrar con la interfaz existente**
  - [ ] Añadir sección de audio a `+page.svelte`
  - [ ] Actualizar `StatusIndicator.svelte` para incluir estado de audio
  - [ ] Mejorar `CommandHistory.svelte` para mostrar audios asociados
  - [ ] Implementar notificaciones de estado de procesamiento

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