# 🛠️ Scripts Directory - Context Index

## 📋 Descripción General
Esta carpeta contiene scripts utilitarios y de prueba para el servicio de hardware de PuertoCho Assistant. Los scripts están diseñados para facilitar el desarrollo, debugging y verificación de componentes específicos.

## 📁 Archivos de Script

### `test_audio_manager.py` 🎙️
**Propósito**: Script interactivo para pruebas rápidas y debugging del `AudioManager` en tiempo real.

**Características principales**:
- **Interface interactiva** con menú de opciones
- **Visualización en tiempo real** del nivel de audio con barras gráficas
- **Listado detallado** de todos los dispositivos de audio disponibles
- **Búsqueda automática** del dispositivo configurado
- **Análisis estadístico** de las muestras de audio capturadas
- **Manejo robusto de errores** con mensajes informativos

**Funcionalidades disponibles**:

#### 1. **Prueba Completa** (Opción 1)
- Muestra configuración actual de audio desde `config.py`
- Lista todos los dispositivos de audio (entrada y salida)
- Inicializa `AudioManager` con configuración automática
- Realiza grabación de 3 segundos con visualización en tiempo real
- Proporciona estadísticas de audio (RMS promedio, máximo, mínimo)
- Detecta si el micrófono está funcionando correctamente

#### 2. **Solo Listado de Dispositivos** (Opción 2)
- Lista completa de dispositivos de audio del sistema
- Información detallada: nombre, canales de entrada/salida
- Búsqueda del dispositivo configurado por nombre
- Ideal para debugging de configuración de hardware

**Visualización de Audio**:
```
Volume: |████████████░░░░░░░░| 0.234
```
- **Barras dinámicas**: Representación visual del nivel de audio
- **Valores RMS**: Medición numérica del volumen
- **Actualización en tiempo real**: Feedback inmediato del micrófono

**Uso**:
```bash
cd puertocho-assistant-hardware/app
python scripts/test_audio_manager.py
# o directamente:
./scripts/test_audio_manager.py
```

**Casos de uso típicos**:
1. **Verificación inicial** del hardware de audio en nueva instalación
2. **Debugging** de problemas de configuración de dispositivos
3. **Calibración** de niveles de audio y sensibilidad
4. **Validación** después de cambios en configuración
5. **Demostración** de funcionalidad a stakeholders

**Dependencias**:
- `numpy`: Para cálculos de análisis de audio
- `time`: Para temporización de grabaciones
- `pathlib`: Para manejo de rutas
- `../core/audio_manager`: Clase principal a probar
- `../config`: Configuración del sistema
- `../utils/logger`: Sistema de logging

**Outputs del Script**:

### Información de Configuración
```
📋 Configuración de audio:
   Sample Rate: 16000 Hz
   Channels: 2
   Chunk Size: 1024
   Device Name: seeed-voicecard
   Buffer Size: 4096
```

### Listado de Dispositivos
```
🎤 Dispositivos de audio disponibles:
   Dispositivos de entrada encontrados: 3
   [0] HDA Intel PCH: ALC662 rev3 Analog - Canales: 2
   [1] seeed-voicecard: - bcm2835-i2s-wm8960-hifi - Canales: 2
   [2] USB Audio Device: USB Audio - Canales: 1
```

### Estadísticas de Grabación
```
📊 Estadísticas de audio:
   Muestras capturadas: 150
   RMS promedio: 0.0234
   RMS máximo: 0.1567
   RMS mínimo: 0.0012
   ✅ Audio detectado correctamente
```

## 🎯 Diferencias con Tests Unitarios

### `test_audio_manager.py` (Script)
- **Propósito**: Debugging interactivo y verificación rápida
- **Interface**: Menú interactivo para usuario
- **Feedback**: Visual en tiempo real con barras de progreso
- **Duración**: Grabaciones cortas para pruebas rápidas
- **Salida**: Información formateada para humanos
- **Uso**: Desarrollo, debugging, demos

### `tests/test_audio.py` (Tests Unitarios)
- **Propósito**: Validación automatizada y CI/CD
- **Interface**: Framework de testing automatizado
- **Feedback**: Reports estructurados pass/fail
- **Duración**: Tests optimizados para velocidad
- **Salida**: Logs estructurados y métricas
- **Uso**: CI/CD, regression testing, validación automática

## 🔧 Configuración y Personalización

### Variables de Entorno Soportadas
```bash
# Configuración de audio
AUDIO_DEVICE_NAME="seeed-voicecard"
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=2
AUDIO_CHUNK_SIZE=1024

# Configuración de logging
HARDWARE_LOG_LEVEL=INFO
DEBUG_MODE=false
```

### Personalización del Script
El script puede modificarse para:
- **Duración de grabación**: Cambiar los 3 segundos por defecto
- **Umbrales de detección**: Ajustar niveles mínimos de audio
- **Visualización**: Modificar el formato de las barras de volumen
- **Estadísticas**: Añadir métricas adicionales (FFT, frecuencias, etc.)

## 🚨 Troubleshooting

### Errores Comunes y Soluciones

#### 1. "No se encontró config.py"
```bash
❌ No se encontró config.py en el directorio actual
   Ejecute este script desde el directorio: puertocho-assistant-hardware/app/
```
**Solución**: Ejecutar desde el directorio correcto o ajustar `sys.path`

#### 2. "No se pudieron listar dispositivos de audio"
```bash
❌ No se pudieron obtener dispositivos de audio
```
**Causas posibles**:
- Drivers de audio no instalados
- Hardware desconectado
- Permisos insuficientes
- PulseAudio/ALSA no configurado

#### 3. "Nivel de audio muy bajo"
```bash
⚠️  Nivel de audio muy bajo (posible problema de micrófono)
```
**Soluciones**:
- Verificar conexión física del micrófono
- Ajustar niveles de volumen del sistema
- Revisar configuración de ALSA/PulseAudio
- Comprobar que el dispositivo correcto está seleccionado

#### 4. "Error al importar módulos"
```bash
❌ Error al importar módulos: No module named 'core.audio_manager'
```
**Solución**: Verificar estructura de directorios y que todos los archivos existan

## 📊 Métricas y Análisis

### Interpretación de Valores RMS
- **0.000 - 0.010**: Silencio o ruido de fondo muy bajo
- **0.010 - 0.050**: Habla suave o ruido de fondo normal
- **0.050 - 0.200**: Habla normal o música suave
- **0.200 - 0.500**: Habla fuerte o música moderada
- **0.500+**: Audio muy fuerte (posible saturación)

### Indicadores de Salud del Sistema
- **Muestras capturadas > 0**: Hardware funcionando
- **RMS máximo > 0.01**: Micrófono detectando audio
- **Variación en RMS**: Respuesta dinámica del micrófono
- **Sin errores de status**: Stream de audio estable

## 🔮 Extensiones Futuras

### Funcionalidades Planificadas
1. **Análisis de frecuencias**: FFT para análisis espectral
2. **Calibración automática**: Ajuste automático de niveles
3. **Tests de latencia**: Medición de latencia de captura
4. **Grabación a archivo**: Guardar muestras para análisis posterior
5. **Comparación de dispositivos**: Benchmark entre múltiples dispositivos
6. **Interface web**: Dashboard web para monitoreo remoto

### Integration con Otros Componentes
- **LED Controller**: Visualización de audio en LEDs
- **Wake Word Detector**: Verificación de sensibilidad
- **WebSocket Client**: Streaming en tiempo real al backend
- **NFC Manager**: Configuración de audio vía NFC

## 📝 Notas para Desarrolladores

### Añadir Nuevas Funcionalidades
1. **Nuevas opciones de menú**: Añadir en la función `main()`
2. **Nuevas métricas**: Extender las funciones de análisis
3. **Visualización personalizada**: Modificar las funciones de display
4. **Export de datos**: Añadir funciones de guardado

### Best Practices
- **Manejo de errores robusto**: Catch y explain todos los errores
- **Cleanup de recursos**: Siempre cerrar streams de audio
- **Feedback visual**: Proporcionar feedback inmediato al usuario
- **Documentación inline**: Comentarios claros en código complejo
- **Configuración flexible**: Usar variables de entorno cuando sea posible
