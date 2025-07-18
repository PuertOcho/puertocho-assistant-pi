# 🧪 Tests Directory - Context Index

## 📋 Descripción General
Esta carpeta contiene todos los tests automatizados para el servicio de hardware de PuertoCho Assistant. Los tests están organizados por componente y tipo de funcionalidad.

## 📁 Archivos de Test

### `test_audio.py` 🎙️
**Propósito**: Suite completa de tests unitarios y de integración para la clase `AudioManager`.

**Características principales**:
- **Tests unitarios** con mocks para simulación sin hardware
- **Tests de integración** con hardware real opcional
- **Validación de configuración** desde `config.py`
- **Tests de context manager** (`with` statement)
- **Manejo robusto de errores** y casos edge

**Clases de test incluidas**:
1. **`TestAudioManager`**: Tests básicos de funcionalidad
   - `test_audio_manager_initialization()`: Verificación de inicialización
   - `test_list_audio_devices()`: Listado de dispositivos de audio
   - `test_find_device_by_name()`: Búsqueda de dispositivos por nombre
   - `test_start_stop_recording_mock()`: Grabación simulada con mocks
   - `test_recording_with_real_hardware()`: Grabación real (requiere hardware)
   - `test_context_manager()`: Verificación del context manager

2. **`TestAudioManagerIntegration`**: Tests de integración
   - `test_config_integration()`: Integración con `config.py`

**Uso**:
```bash
cd puertocho-assistant-hardware/app
python tests/test_audio.py
```

**Dependencias**:
- `unittest`: Framework de testing de Python
- `unittest.mock`: Para simulación de componentes
- `numpy`: Para análisis de datos de audio
- `sounddevice`: Para interacción con hardware de audio
- `../core/audio_manager`: Clase bajo test
- `../config`: Configuración del sistema

**Outputs esperados**:
- Reporte detallado de tests ejecutados
- Estadísticas de éxito/fallo
- Información de debug sobre dispositivos de audio
- Métricas de audio capturado (cuando hay hardware)

## 🎯 Propósito de los Tests

### Tests con Mock (Sin Hardware)
- **Ventajas**: Ejecutan siempre, no requieren hardware específico
- **Verifican**: Lógica de código, inicialización, manejo de errores
- **Ideal para**: CI/CD, desarrollo sin hardware, tests rápidos

### Tests con Hardware Real
- **Ventajas**: Verificación completa del stack de audio
- **Verifican**: Comunicación real con dispositivos, latencia, calidad
- **Ideal para**: Validación en dispositivo final, debugging de hardware

## 📊 Métricas Monitoreadas

### Audio Quality Metrics
- **RMS (Root Mean Square)**: Nivel de volumen promedio
- **Peak Levels**: Niveles máximos de audio
- **Sample Rate Accuracy**: Verificación de frecuencia de muestreo
- **Channel Integrity**: Verificación de canales de audio

### Performance Metrics
- **Initialization Time**: Tiempo de inicialización del AudioManager
- **Stream Latency**: Latencia en la captura de audio
- **Error Rate**: Frecuencia de errores de audio
- **Device Detection Speed**: Velocidad de detección de dispositivos

## 🔧 Configuración de Tests

### Variables de Entorno Relevantes
- `AUDIO_DEVICE_NAME`: Dispositivo de audio preferido para tests
- `AUDIO_SAMPLE_RATE`: Frecuencia de muestreo para tests
- `AUDIO_CHANNELS`: Número de canales para tests
- `TEST_MODE`: Activar modo de test (opcional)

### Hardware Requerido (para tests completos)
- **ReSpeaker 2-Mic Pi HAT V1.0**: Dispositivo de audio principal
- **Raspberry Pi**: Plataforma de hardware
- **Conexión de audio**: Micrófono funcional

## 🚨 Troubleshooting

### Errores Comunes
1. **"No audio devices found"**
   - Verificar que el hardware de audio esté conectado
   - Revisar drivers de audio en el sistema
   - Comprobar permisos de acceso a dispositivos

2. **"Device validation failed"**
   - Verificar configuración en `config.py`
   - Comprobar que el dispositivo especificado existe
   - Revisar parámetros de audio (sample rate, channels)

3. **"Recording test skipped"**
   - Normal cuando no hay hardware disponible
   - Tests con mock aún deben pasar
   - Verificar en hardware real para tests completos

## 📝 Notas para Desarrolladores

### Añadir Nuevos Tests
1. Heredar de `unittest.TestCase`
2. Seguir convención de nombres: `test_[funcionalidad]()`
3. Incluir docstrings descriptivos
4. Manejar casos con y sin hardware
5. Limpiar recursos en `tearDown()`

### Best Practices
- **Usar mocks** para tests unitarios
- **Tests reales** solo para validación final
- **Timeouts cortos** para evitar tests lentos
- **Cleanup automático** de recursos de audio
- **Logging informativo** para debugging

### Extensiones Futuras
- Tests de rendimiento con cargas específicas
- Tests de stress con múltiples streams
- Validación de calidad de audio avanzada
- Integration tests con otros componentes (LEDs, NFC)