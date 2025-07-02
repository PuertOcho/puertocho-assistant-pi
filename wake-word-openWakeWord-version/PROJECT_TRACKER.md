# PROJECT_TRACKER.md

## Fase 1: Preparación del entorno ✅ COMPLETADA
- [x] Añadir `openwakeword` y dependencias a `requirements.txt`
- [x] Instalar dependencias del sistema necesarias (ej: `libsndfile1`, `libasound2`, `libsndfile-dev`, `libspeexdsp-dev` si se usa supresión de ruido)
- [x] Configurar variables de entorno específicas para openWakeWord
- [x] Documentar instalación y dependencias en el README

## Fase 2: Integración básica de openWakeWord ✅ COMPLETADA
- [x] Descargar modelos preentrenados de openWakeWord (`openwakeword.utils.download_models()`)
- [x] Crear clase/módulo para inicializar y gestionar el modelo de wake word
- [x] Implementar captura de audio en tiempo real (usar `sounddevice`, frames de 80ms multiples)
- [x] Integrar la predicción del modelo sobre frames de audio (16kHz, 16bit PCM)
- [x] Implementar sistema de buffering de audio eficiente
- [x] Probar detección básica de wake word y log de activaciones

## Fase 3: Integración con lógica del asistente ✅ COMPLETADA
- [x] Adaptar la lógica de activación (sustituir Porcupine por openWakeWord en el flujo principal)
- [x] Integrar con el sistema de comandos (ejecución tras detección de wake word)
- [x] Mantener compatibilidad con LEDs y botón físico (GPIO)
- [x] Implementar gestión de estados (IDLE, LISTENING, PROCESSING)
- [x] Añadir tests de integración para la activación y flujo de comandos

## Fase 4: Optimización y robustez
- [ ] **Configuración de parámetros avanzados:**
  - [ ] Ajustar umbral de activación (threshold) según entorno
  - [ ] Configurar VAD (Voice Activity Detection) con `vad_threshold`
  - [ ] Implementar supresión de ruido Speex (`enable_speex_noise_suppression=True`)
- [ ] **Optimización de rendimiento:**
  - [ ] Medir latencia y consumo de CPU/RAM en Raspberry Pi
  - [ ] Optimizar tamaño de frames (multiples de 80ms para eficiencia)
  - [ ] Configurar inference framework (ONNX vs TFLite según hardware)
- [ ] Permitir selección/cambio de modelo de wake word (personalización)
- [ ] Implementar fallback a modelos preentrenados si falla el personalizado

## Fase 5: Entrenamiento de modelo personalizado "Puertocho"
- [ ] **Preparación del entorno de entrenamiento:**
  - [ ] **OPCIÓN RECOMENDADA: Google Cloud GPU T4** (basado en experiencia previa exitosa)
    - [ ] Configurar instancia con GPU T4 (similar a docs/FASE_3_IMPLEMENTACION_CLOUD.md)
    - [ ] Adaptar scripts de setup para openWakeWord en lugar de ChatterboxTTS
    - [ ] Configurar entorno: Python 3.11+, PyTorch, openWakeWord dependencies
    - [ ] Costo estimado: $10-15 para entrenamiento completo
  - [ ] **OPCIÓN ALTERNATIVA: Google Colab** (gratuito pero con limitaciones)
    - [ ] Usar notebook oficial de openWakeWord
    - [ ] Considerar limitaciones de tiempo (12h) y sesiones cortadas
- [ ] **Preparación de datos:**
  - [ ] Generar datos sintéticos positivos usando TTS
    - [ ] "Puertocho"
    - [ ] "Hola Puertocho" 
    - [ ] "Oye Puertocho"
    - [ ] Variaciones con diferentes voces y acentos (mínimo varios miles)
  - [ ] Generar/descargar datos negativos (~30,000 horas recomendadas)
  - [ ] Subir dataset a Cloud Storage si usas Google Cloud
- [ ] **Entrenamiento:**
  - [ ] **Si usas Google Cloud T4:**
    - [ ] Adaptar scripts de entrenamiento existentes (train_spanish_*.py → train_puertocho_*.py)
    - [ ] Configurar Wandb para monitoreo (modo offline funcional)
    - [ ] Usar configuración optimizada para T4: batch_size=8, learning_rate=1e-4
  - [ ] **Si usas Google Colab:**
    - [ ] Usar notebook oficial de openWakeWord para entrenamiento
    - [ ] Configurar parámetros de entrenamiento (épocas, batch size, etc.)
  - [ ] Entrenar modelo (tiempo estimado: <1 hora)
  - [ ] Validar rendimiento del modelo entrenado
- [ ] **Integración del modelo personalizado:**
  - [ ] Descargar modelo `.onnx` o `.tflite` entrenado
  - [ ] Integrar en checkpoints del proyecto
  - [ ] Probar detección con el modelo personalizado
  - [ ] Ajustar threshold específico para "Puertocho"
- [ ] **Documentación del proceso:**
  - [ ] Documentar proceso de entrenamiento paso a paso
  - [ ] Crear guía para futuras wake words personalizadas
  - [ ] Documentar troubleshooting y recomendaciones

## Fase 6: Validación y despliegue
- [ ] **Testing exhaustivo:**
  - [ ] Probar en diferentes condiciones de ruido
  - [ ] Validar false-accept rate (<0.5/hora objetivo)
  - [ ] Validar false-reject rate (<5% objetivo)
  - [ ] Probar susurros y diferentes velocidades de habla
- [ ] **Optimización para producción:**
  - [ ] Validar funcionamiento en Raspberry Pi y otros entornos
  - [ ] Configurar logging y monitoreo de rendimiento
  - [ ] Implementar recuperación ante errores
- [ ] **Documentación final:**
  - [ ] Documentar troubleshooting y recomendaciones
  - [ ] Actualizar scripts de instalación y verificación para openWakeWord
  - [ ] Crear guía de usuario final

## Fase 7: Mejoras avanzadas (opcional)
- [ ] **Modelos verifier para voces específicas:**
  - [ ] Entrenar modelo de segunda etapa para reconocer voz del usuario
  - [ ] Reducir false-accepts de otras voces
- [ ] **Soporte multilenguaje:**
  - [ ] Investigar TTS en español para datos sintéticos
  - [ ] Experimentar con modelos base en otros idiomas
- [ ] **Integración con servicios cloud:**
  - [ ] Backup a servicios de transcripción remotos
  - [ ] Telemetría y mejora continua

---

## Notas técnicas y mejores prácticas

### **Configuración recomendada openWakeWord:**
```python
from openwakeword.model import Model

# Configuración optimizada para Raspberry Pi
model = Model(
    wakeword_models=["checkpoints/puertocho.onnx"],  # Tu modelo personalizado
    inference_framework="onnx",  # Más eficiente en RPi
    vad_threshold=0.5,  # Ajustar según entorno
    enable_speex_noise_suppression=True  # Para ambientes ruidosos
)
```

### **Parámetros de audio recomendados:**
- **Frecuencia de muestreo:** 16kHz (requerido)
- **Resolución:** 16-bit PCM
- **Canales:** Mono (1 canal)
- **Frame size:** Múltiplos de 80ms (1280 samples @ 16kHz)
- **Buffer size:** 3-5 frames para latencia vs eficiencia

### **Thresholds típicos por modelo:**
- Modelos preentrenados: 0.5 (default)
- Modelos personalizados: 0.3-0.8 (ajustar según pruebas)
- Ambientes ruidosos: threshold más alto
- Requisitos de baja latencia: threshold más bajo

---

## Recursos y enlaces
- [Repositorio oficial openWakeWord](https://github.com/dscripka/openWakeWord)
- [Ejemplo de uso básico](https://github.com/dscripka/openWakeWord#usage)
- [Recomendaciones de uso y parámetros](https://github.com/dscripka/openWakeWord#recommendations-for-usage)
- [Entrenamiento de modelos personalizados](https://github.com/dscripka/openWakeWord#training-new-models)
- [Notebook de entrenamiento en Colab](https://github.com/dscripka/openWakeWord/blob/main/notebooks/)
- [Repositorio de generación de datos sintéticos](https://github.com/dscripka/synthetic_speech_dataset_generation)
- [Modelos de la comunidad Home Assistant](https://github.com/fwartner/home-assistant-wakewords-collection)

---

Este archivo debe actualizarse conforme avance el desarrollo, marcando tareas completadas y añadiendo nuevas según necesidades del proyecto. 