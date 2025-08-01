# 📋 TODO: Mejoras en el módulo Core

## 🎯 Objetivo General
Refactorizar las clases del módulo `core` para que cada una se dedique exclusivamente a su responsabilidad específica, eliminando duplicación de código y reduciendo el acoplamiento entre componentes.

## 📦 Mejoras por Componente

### 1. **AudioManager** (`audio_manager.py`)
#### 🔧 Cambios necesarios:
- **Implementar reproducción de audio**
  - Añadir método `play_audio()` para reproducción síncrona
  - Añadir método `play_audio_async()` para reproducción asíncrona con callback
  - Implementar control de volumen de reproducción

- **Añadir monitoreo de niveles**
  - Implementar `get_recording_level()` para obtener nivel de volumen actual
  - Útil para feedback visual en LEDs

- **Gestión de buffers centralizada**
  - Añadir `buffer_audio()` para acumular audio temporalmente
  - Añadir `get_buffered_audio()` para recuperar audio acumulado
  - Añadir `clear_buffer()` para limpiar buffers

#### ✅ Resultado esperado:
- AudioManager será el único responsable de toda E/S de audio
- Otros componentes no necesitarán manejar streams de audio directamente
- Facilitará testing al poder mockear un único componente

### 2. **WakeWordDetector** (`wake_word_detector.py`)
#### 🔧 Cambios necesarios:
- **Eliminar lógica de resampling interna**
  - Remover buffers de audio internos (`audio_buffer_left/right`)
  - Delegar resampling a `AudioResampler` dedicado
  - Simplificar `process_audio_chunk()` para solo detectar

- **Mejorar manejo de eventos**
  - Usar callbacks más específicos para diferentes tipos de detección
  - Añadir métricas de confianza en la detección

#### ✅ Resultado esperado:
- Clase enfocada únicamente en detección de wake words
- Código más simple y mantenible
- Resampling reutilizable por otros componentes

### 3. **VADHandler** (`vad_handler.py`)
#### 🔧 Cambios necesarios:
- **Eliminar captura de audio**
  - Remover `_audio_buffer` interno
  - Eliminar métodos `save_captured_audio()` y `on_audio_captured()`
  - Solo detectar inicio/fin de voz, no capturar

- **Mejorar callbacks de eventos**
  - Callbacks deben incluir timestamps precisos
  - Añadir callback para niveles de confianza VAD
  - Incluir duración de segmentos de voz

#### ✅ Resultado esperado:
- VAD solo detecta actividad de voz, no maneja audio
- Reduce memoria al no duplicar buffers de audio
- Más flexible al no imponer formato de captura

### 4. **StateManager** (`state_manager.py`)
#### 🔧 Cambios necesarios:
- **Eliminar comunicación WebSocket directa**
  - Remover referencia a `websocket_client`
  - Usar callbacks/eventos para notificar cambios de estado
  - Main.py manejará la comunicación externa

- **Simplificar manejo de audio**
  - No procesar audio directamente, solo coordinar
  - Delegar captura a AudioManager
  - Usar callbacks para notificar cuando audio está listo

- **Mejorar coordinación de componentes**
  - Añadir método `register_component()` para registrar componentes
  - Implementar patrón Observer para notificaciones
  - Centralizar lógica de transiciones de estado

#### ✅ Resultado esperado:
- StateManager actúa como coordinador puro
- No conoce detalles de implementación de otros componentes
- Facilita añadir nuevos estados y transiciones

### 5. **ButtonHandler** (`button_handler.py`)
#### 🔧 Cambios necesarios:
- **Añadir consulta de estado**
  - Implementar `is_pressed()` para obtener estado actual
  - Útil para lógica condicional en otros componentes

- **Mejorar sistema de callbacks**
  - Añadir `register_state_callback()` para cambios de estado
  - Soportar múltiples listeners con prioridades
  - Añadir callbacks para eventos específicos (doble click, etc.)

#### ✅ Resultado esperado:
- API más completa para interacción con botón
- Facilita implementar gestos complejos
- Mejor integración con StateManager

### 6. **LEDController** (`led_controller.py`)
#### 🔧 Cambios necesarios:
- **Añadir feedback de audio**
  - Implementar `pulse_with_audio_level()` para visualizar niveles
  - Sincronizar animaciones con eventos de audio

- **Mejorar sistema de animaciones**
  - Hacer animaciones interrumpibles
  - Añadir transiciones suaves entre estados
  - Implementar cola de animaciones

- **Optimizar rendimiento**
  - Reducir uso de CPU en animaciones
  - Implementar cache de patrones comunes

#### ✅ Resultado esperado:
- Feedback visual más rico y responsivo
- Menor consumo de recursos
- Animaciones más fluidas

## 🔄 Mejoras Adicionales Identificadas - ACTUALIZADAS

### 13. **Optimizar integración entre componentes existentes**
#### 🔧 Cambios de integración necesarios:
- **AudioManager + CircularAudioBuffer**
  - Reemplazar buffers internos con `CircularAudioBuffer` y `DualChannelBuffer`
  - Usar estadísticas del buffer para métricas de rendimiento
  - Implementar triggers automáticos basados en nivel de llenado

- **WakeWordDetector + AudioResampler**
  - Eliminar lógica de resampling interna y delegar a `utils/audio_resampling.py`
  - Usar `prepare_for_porcupine()` para preparación específica
  - Implementar cache de audio procesado para evitar reprocesamiento

- **LEDController + APA102**
  - Migrar a usar `APA102` como driver base
  - Aprovechar optimizaciones SPI existentes
  - Implementar patrones avanzados sobre la base existente

- **Todos los componentes + HardwareLogger**
  - Migrar todos los `logging.getLogger()` a `HardwareLogger`
  - Usar funciones especializadas por evento
  - Implementar contexto de estado en logs para mejor debugging

#### ✅ Beneficios:
- Reduce duplicación de código significativamente
- Aprovecha optimizaciones ARM64 existentes
- Mejora consistencia en logging y métricas
- Facilita mantenimiento al centralizar funcionalidades

### 8. **Aprovechar CircularAudioBuffer existente** (`utils/audio_buffer.py`) ✅ IMPLEMENTADO
#### 🔧 Integración necesaria:
- **Integrar en AudioManager**
  - Usar `CircularAudioBuffer` como buffer principal en AudioManager
  - Implementar `DualChannelBuffer` para manejo estéreo nativo
  - Aprovechar funciones de estadísticas para monitoreo

- **Mejorar funcionalidad existente**
  - Añadir triggers automáticos cuando buffer alcanza nivel específico
  - Implementar buffer overflow protection
  - Añadir métricas de latencia y rendimiento

#### ✅ Beneficios actuales:
- ✅ Buffer circular thread-safe completamente implementado
- ✅ Soporte para dual-channel especializado para wake word
- ✅ Sistema de estadísticas robusto
- ✅ Manejo eficiente de memoria con wrap-around

### 9. **Aprovechar HardwareLogger existente** (`utils/logger.py`) ✅ IMPLEMENTADO
#### 🔧 Integración necesaria:
- **Estandarizar en todos los componentes**
  - Migrar todos los loggers a usar `HardwareLogger`
  - Usar funciones especializadas (`log_audio_event`, `log_wake_word_event`, etc.)
  - Implementar contexto de estado en logs

- **Añadir métricas de rendimiento**
  - Expandir `log_performance_metric()` para cubrir todos los componentes
  - Implementar dashboard de logs en tiempo real
  - Añadir alertas automáticas por umbral de métricas

#### ✅ Beneficios actuales:
- ✅ Logging estructurado en JSON
- ✅ Funciones especializadas por componente
- ✅ Rotación automática de archivos
- ✅ Métricas de rendimiento integradas

### 10. **Optimizar APA102 LED Driver** (`utils/apa102.py`) ✅ IMPLEMENTADO
#### 🔧 Mejoras necesarias:
- **Integrar con LEDController**
  - Usar `APA102` como driver base en `LEDController`
  - Implementar patrones de animación sobre la clase existente
  - Añadir efectos sincronizados con audio usando buffer circular

- **Optimizar rendimiento**
  - Cache de patrones de colores frecuentes
  - Batching de operaciones SPI para mejor rendimiento
  - Implementar interpolación suave entre estados

#### ✅ Beneficios actuales:
- ✅ Driver SPI optimizado para APA102
- ✅ Soporte para múltiples formatos de color
- ✅ Base sólida para efectos complejos

### 11. **Implementar EventBus** (`utils/event_bus.py`)
#### 🔧 Implementación necesaria:
```python
class EventBus:
    """Sistema centralizado de eventos"""
    def publish(self, event_type, data):
        # Publicar evento a suscriptores
        pass
    
    def subscribe(self, event_type, callback):
        # Suscribir callback a tipo de evento
        pass
```

#### ✅ Beneficios:
- Desacopla componentes completamente
- Facilita debugging al centralizar eventos
- Permite añadir nuevos componentes sin modificar existentes
- Se integra con HardwareLogger existente

### 12. **Crear AudioProcessor unificado** (`utils/audio_processor.py`)
#### 🔧 Nueva implementación necesaria:
- **Combinar funcionalidades existentes**
  - Integrar `AudioResampler`, `CircularAudioBuffer` y funciones de `audio_resampling.py`
  - Crear API unificada para todo el procesamiento de audio
  - Implementar pipelines configurables (resample -> buffer -> detect)

- **Añadir nuevas capacidades**
  - Filtrado de audio (noise reduction, EQ)
  - Análisis de espectro en tiempo real
  - Detección de niveles de ruido ambiente

#### ✅ Beneficios esperados:
- API única para todo el procesamiento de audio
- Aprovecha código optimizado existente
- Facilita añadir nuevos algoritmos de procesamiento

## 🔄 Mejoras Adicionales Identificadas - ACTUALIZADAS
#### 🔧 Cambios necesarios:
- Estandarizar formato de logs entre componentes
- Añadir contexto a cada log (estado actual, componente origen)
- Implementar métricas de rendimiento por componente
- Crear dashboard de salud del sistema

#### ✅ Beneficios:
- Debugging más eficiente
- Identificación rápida de cuellos de botella
- Mejor monitoreo en producción

## 📅 Orden de Implementación Sugerido - ACTUALIZADO CON PRIORIDADES CRÍTICAS

0. **Fase 0 - Reparación Crítica** (Prioridad CRÍTICA) 🚨 **INMEDIATO**
   - [ ] **Corregir bug en health check del backend** (5 minutos)
     - Inicializar variable `hardware_error` correctamente
     - Probar endpoint `/health` funciona
   
   - [ ] **Implementar endpoint WebSocket en backend** (30 minutos)
     - Añadir `@app.websocket("/ws")` en main.py
     - Verificar configuración uvicorn para WebSockets
     - Probar conexión básica hardware -> backend
   
   - [ ] **Implementar captura post-wake word** (1-2 horas)
     - Buffer persistente para audio post-wake word
     - Envío via WebSocket al backend
     - Timeout para fin de mensaje

1. **Fase 1 - Integración de Utils existentes** (Prioridad Alta) ✅ **COMPLETADA**
   - [x] Crear clase wrapper `AudioResampler` sobre funciones existentes ✅ COMPLETADO
   - [x] Integrar `CircularAudioBuffer` en AudioManager ✅ COMPLETADO
   - [x] Migrar todos los componentes a usar `HardwareLogger` ✅ COMPLETADO
   - [x] Integrar `APA102` como driver base en LEDController ✅ COMPLETADO

2. **Fase 2 - Refactorización Core** (Prioridad Alta) ✅ **COMPLETADA**
   - [x] Refactorizar WakeWordDetector para usar AudioResampler ✅ COMPLETADO
   - [x] Simplificar VADHandler (eliminar captura, usar buffer centralizado) ✅ COMPLETADO
   - [x] Refactorizar StateManager (eliminar WebSocket directo) ✅ COMPLETADO
   - [x] Implementar EventBus básico ✅ COMPLETADO

3. **Fase 3 - Nuevas funcionalidades** (Prioridad Media) ✅ **COMPLETADA**
   - [x] Crear AudioProcessor unificado ✅ COMPLETADO
   - [x] Mejorar ButtonHandler con nuevos callbacks ✅ COMPLETADO
   - [x] Implementar feedback de audio en LEDs ✅ COMPLETADO
   - [x] Añadir transiciones suaves y animaciones interrumpibles ✅ COMPLETADO

4. **Fase 4 - Comunicación Backend-Hardware** (Prioridad Alta) 🚨 **CRÍTICO**
   - [ ] **Corregir conexión WebSocket entre hardware y backend**
     - Error: `[Errno 111] Connect call failed ('127.0.0.1', 8000)`
     - Backend responde en puerto 8000 pero WebSocket no está disponible
     - Verificar endpoint `/ws` en backend gateway
   
   - [ ] **Corregir bug en health check del backend**
     - Error: `cannot access local variable 'hardware_error' where it is not associated with a value`
     - Línea 136 en `/puertocho-assistant-backend/src/main.py`
   
   - [ ] **Implementar endpoint WebSocket en backend**
     - Verificar que `@app.websocket("/ws")` esté implementado
     - Asegurar que maneja eventos del hardware correctamente
   
   - [ ] **Corregir captura de audio post-wake word**
     - Audio se pierde después de detectar wake word
     - Implementar buffer persistente para captura completa
     - Enviar audio capturado al backend via WebSocket

5. **Fase 5 - Optimización y Métricas** (Prioridad Baja)
   - [ ] Optimizar rendimiento usando cache en resampling
   - [ ] Implementar dashboard de métricas en tiempo real
   - [ ] Añadir alertas automáticas por umbral
   - [ ] Performance tuning específico para Raspberry Pi
   - [ ] Resolver warnings de audio overflow (`input overflow`)

## 🚨 Problemas Críticos Identificados - NUEVA SECCIÓN

### **PROBLEMA 1: Conexión WebSocket Backend-Hardware FALLIDA**
#### 🔴 Estado: CRÍTICO - Sistema no funcional
#### 📊 Evidencia de logs:
```
{"timestamp": "2025-08-01T07:25:21.809042Z", "level": "ERROR", "logger": "api.websocket_client", "message": "WebSocket connection failed: Multiple exceptions: [Errno 111] Connect call failed ('::1', 8000, 0, 0), [Errno 111] Connect call failed ('127.0.0.1', 8000)", "module": "logger", "function": "_log", "line": 144, "thread": 4155846672, "process": 1}
```

#### 🔧 Causas identificadas:
1. **Backend responde en puerto 8000 pero WebSocket endpoint no está disponible**
   - `curl http://localhost:8000/health` funciona 
   - `ws://localhost:8000/ws` falla con conexión rechazada

2. **Posible falta de endpoint WebSocket en backend**
   - Verificar que `@app.websocket("/ws")` esté implementado en `main.py`
   - Verificar que el endpoint maneje eventos del hardware

#### ✅ Soluciones requeridas:
- [ ] Implementar endpoint WebSocket `/ws` en backend
- [ ] Verificar configuración de uvicorn para WebSockets
- [ ] Probar conexión WebSocket manualmente
- [ ] Implementar reconexión robusta en hardware

### **PROBLEMA 2: Bug en Health Check del Backend**
#### 🔴 Estado: CRÍTICO - Impide monitoreo
#### 📊 Evidencia:
```json
{"detail":"Health check failed: cannot access local variable 'hardware_error' where it is not associated with a value"}
```

#### 🔧 Causa identificada:
- Variable `hardware_error` no inicializada en todas las rutas del código
- Línea 136 en `/puertocho-assistant-backend/src/main.py`

#### ✅ Solución requerida:
- [ ] Inicializar `hardware_error = None` antes del try/catch
- [ ] Usar variable en respuesta de error solo si está definida

### **PROBLEMA 3: Audio se pierde después de Wake Word**
#### 🔴 Estado: FUNCIONALIDAD CRÍTICA FALTANTE
#### 📊 Comportamiento actual:
- Wake word se detecta correctamente
- Audio posterior no se captura/envía al backend
- Buffer se limpia sin guardar el mensaje

#### 🔧 Causas posibles:
1. **Falta de buffer persistente post-wake word**
2. **Sin envío de audio capturado via WebSocket**
3. **StateManager no coordina captura completa**

#### ✅ Soluciones requeridas:
- [ ] Implementar buffer de audio persistente post-wake word
- [ ] Enviar audio capturado al backend via WebSocket
- [ ] Coordinar estados de captura en StateManager
- [ ] Añadir timeout para fin de captura de voz

### **PROBLEMA 4: Warnings de Audio Overflow**
#### 🔶 Estado: DEGRADACIÓN DE RENDIMIENTO
#### 📊 Evidencia (múltiples):
```
{"timestamp": "2025-08-01T07:25:20.785181Z", "level": "WARNING", "logger": "audio_manager", "message": "Estado del stream de audio: input overflow"}
```

#### 🔧 Causas posibles:
1. **Buffer de audio demasiado pequeño**
2. **Procesamiento no optimizado para tiempo real**
3. **Configuración de latencia subóptima**

#### ✅ Soluciones requeridas:
- [ ] Aumentar tamaño de buffer de audio
- [ ] Optimizar procesamiento de audio en tiempo real
- [ ] Ajustar configuración de latencia de PyAudio
- [ ] Implementar dropping inteligente de frames

## 🧪 Testing Requerido

Para cada componente refactorizado:
- [ ] Unit tests para nuevos métodos
- [ ] Integration tests entre componentes
- [ ] Performance tests para operaciones críticas
- [ ] Tests de regresión para funcionalidad existente

## 📝 Notas Importantes - ACTUALIZADAS CON PROBLEMAS CRÍTICOS

- **🚨 PRIORIDAD MÁXIMA**: Solucionar comunicación WebSocket backend-hardware
- **🔧 Bug crítico**: Health check del backend impide monitoreo del sistema
- **🎙️ Funcionalidad faltante**: Captura de audio post-wake word es crítica para el funcionamiento
- **⚡ Optimización audio**: Resolver overflow warnings mejorará estabilidad general

- **Aprovechar código existente**: La carpeta `utils/` contiene implementaciones robustas que deben ser el fundamento de la refactorización
- **Mantener retrocompatibilidad**: Los cambios deben ser incrementales, especialmente al migrar a componentes existentes
- **Documentar cambios**: Actualizar docstrings y README, especialmente para nuevas integraciones
- **Optimizaciones ARM64**: El código en `utils/` ya está optimizado para Raspberry Pi, mantener estas optimizaciones
- **Coordinar con main.py**: Actualizar la inicialización para usar los nuevos componentes integrados
- **Testing exhaustivo**: Probar especialmente las integraciones entre componentes existentes y nuevos

## 💡 Observaciones sobre Utils existentes

### ✅ Fortalezas identificadas:
- **`audio_resampling.py`**: Implementación completa y optimizada para ARM64, con funciones especializadas
- **`audio_buffer.py`**: Buffer circular thread-safe robusto con soporte dual-channel
- **`logger.py`**: Sistema de logging estructurado con métricas especializadas por componente
- **`apa102.py`**: Driver LED optimizado con soporte SPI eficiente

### 🔄 Oportunidades de mejora:
- **Encapsulación**: Algunas funciones podrían beneficiarse de clases wrapper
- **Integración**: Los componentes core aún no aprovechan completamente estas utilidades
- **Cache**: Oportunidades de optimización mediante caching en operaciones frecuentes
- **Documentación**: Algunos componentes necesitan mejor documentación de integración

## 🎯 Próximos Pasos Inmediatos

### Para solucionar INMEDIATAMENTE:

1. **Corregir health check backend** (5 minutos):
   ```bash
   # Editar: /puertocho-assistant-backend/src/main.py línea ~130
   # Añadir: hardware_error = None antes del try
   ```

2. **Verificar endpoint WebSocket** (15 minutos):
   ```bash
   # Verificar que existe @app.websocket("/ws") en main.py
   # Si no existe, implementarlo
   ```

3. **Probar conexión básica** (10 minutos):
   ```bash
   # Reiniciar contenedores después de los fixes
   docker-compose down && docker-compose up -d
   # Verificar logs sin errores de conexión
   ```

4. **Implementar captura post-wake word** (1-2 horas):
   - Modificar StateManager para mantener buffer post-wake word
   - Enviar audio via WebSocket al backend
   - Añadir timeout para fin de captura