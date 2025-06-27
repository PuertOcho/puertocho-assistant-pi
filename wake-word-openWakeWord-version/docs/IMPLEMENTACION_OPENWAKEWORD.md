# 🎤 IMPLEMENTACIÓN OPENWAKEWORD

**Fecha:** 25 de Enero 2025  
**Estado:** ✅ **FASE 1 Y 2 COMPLETADAS**  
**Progreso:** Implementación básica funcional

---

## 📋 RESUMEN EJECUTIVO

Se ha completado exitosamente la migración del **Asistente de Voz Puertocho** desde **Porcupine** a **openWakeWord**, eliminando la dependencia de API keys y proporcionando una solución completamente offline con capacidades de entrenamiento de modelos personalizados.

### 🏆 **LOGROS PRINCIPALES**
- ✅ **Migración completa**: De Porcupine a openWakeWord
- ✅ **Sin API keys**: Funciona completamente offline
- ✅ **Modelos preentrenados**: Alexa, Hey Mycroft disponibles
- ✅ **Configuración flexible**: Variables de entorno configurables
- ✅ **Scripts adaptados**: Instalador, verificador y ejecutor actualizados
- ✅ **Docker funcional**: Contenedor construye y ejecuta correctamente

---

## 🔄 CAMBIOS REALIZADOS

### **1. Dependencias actualizadas**
```txt
# app/requirements.txt
openwakeword        # Biblioteca principal
sounddevice         # Captura de audio
numpy              # Procesamiento numérico
python-dotenv      # Variables de entorno
requests           # Comunicación HTTP
RPi.GPIO           # Control de GPIO
webrtcvad          # Detección de actividad de voz
```

### **2. Variables de entorno nuevas**
```env
# Configuración openWakeWord
OPENWAKEWORD_MODEL_PATHS=alexa,hey_mycroft  # Modelos a usar
OPENWAKEWORD_THRESHOLD=0.5                  # Umbral de activación
OPENWAKEWORD_VAD_THRESHOLD=0.0             # VAD (0.0=deshabilitado)
OPENWAKEWORD_ENABLE_SPEEX_NS=false         # Supresión de ruido
OPENWAKEWORD_INFERENCE_FRAMEWORK=onnx      # Motor de inferencia

# Configuración de audio
AUDIO_SAMPLE_RATE=16000                    # Frecuencia requerida
AUDIO_CHANNELS=1                           # Mono
AUDIO_CHUNK_SIZE=1280                      # 80ms @ 16kHz
```

### **3. Arquitectura del sistema**
```
openWakeWord Pipeline:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Audio Capture   │    │ openWakeWord    │    │ Voice Commands  │
│ (sounddevice)   │───▶│ Detection       │───▶│ Processing      │
│ 16kHz, 16bit    │    │ (ONNX/TFLite)   │    │ (Transcription) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **4. Scripts actualizados**
- **`instalar_asistente.py`**: Instala openWakeWord automáticamente
- **`verificar_configuracion.py`**: Verifica modelos openWakeWord
- **`ejecutar_asistente.py`**: Documentación actualizada
- **`app/main.py`**: Lógica principal con openWakeWord

---

## 🚀 CONFIGURACIÓN Y USO

### **Instalación automática**
```bash
python3 instalar_asistente.py
```

**El instalador:**
1. Instala openWakeWord automáticamente
2. Descarga modelos preentrenados
3. Crea archivo .env con configuración por defecto
4. Verifica la configuración
5. Ejecuta el asistente en Docker

### **Wake words disponibles**
- **'Alexa'** (modelo alexa)
- **'Hey Mycroft'** (modelo hey_mycroft)
- **Modelos adicionales**: hey_jarvis, timers, weather
- **Modelo personalizado**: 'Puertocho' (próximamente)

### **Comandos de voz**
Después de activar con wake word:
- "enciende luz verde" / "enciende led verde"
- "apaga luz verde" / "apaga led verde"
- "enciende luz rojo" / "enciende led rojo"
- "apaga luz rojo" / "apaga led rojo"

---

## ⚙️ CONFIGURACIÓN AVANZADA

### **Modelos personalizados**
```env
# Usar solo modelo específico
OPENWAKEWORD_MODEL_PATHS=alexa

# Usar múltiples modelos
OPENWAKEWORD_MODEL_PATHS=alexa,hey_mycroft,hey_jarvis

# Usar modelo personalizado (cuando esté disponible)
OPENWAKEWORD_MODEL_PATHS=checkpoints/puertocho.onnx
```

### **Ajuste de sensibilidad**
```env
# Más sensible (más detecciones, posibles falsos positivos)
OPENWAKEWORD_THRESHOLD=0.3

# Menos sensible (menos detecciones, menos falsos positivos)
OPENWAKEWORD_THRESHOLD=0.7
```

### **Supresión de ruido (recomendado para ambientes ruidosos)**
```env
OPENWAKEWORD_ENABLE_SPEEX_NS=true
OPENWAKEWORD_VAD_THRESHOLD=0.5
```

---

## 🔧 TROUBLESHOOTING

### **Problema: openWakeWord no instalado**
```bash
pip install openwakeword
```

### **Problema: Modelos no se descargan**
```bash
python -c "import openwakeword; openwakeword.utils.download_models()"
```

### **Problema: Wake word no se detecta**
1. Reducir umbral: `OPENWAKEWORD_THRESHOLD=0.3`
2. Verificar micrófono funcionando
3. Probar activación manual con botón GPIO

### **Problema: Muchos falsos positivos**
1. Aumentar umbral: `OPENWAKEWORD_THRESHOLD=0.7`
2. Habilitar VAD: `OPENWAKEWORD_VAD_THRESHOLD=0.5`
3. Habilitar supresión de ruido: `OPENWAKEWORD_ENABLE_SPEEX_NS=true`

---

## 📊 COMPARACIÓN: PORCUPINE VS OPENWAKEWORD

| Característica | Porcupine | openWakeWord |
|----------------|-----------|--------------|
| **Costo** | API key requerida | Gratuito, open source |
| **Offline** | ✅ | ✅ |
| **Modelos preentrenados** | Limitados | Múltiples disponibles |
| **Entrenamiento personalizado** | Requiere licencia | Notebooks gratuitos |
| **Idiomas** | Español disponible | Solo inglés (por ahora) |
| **Supresión de ruido** | No integrada | Speex integrado |
| **VAD** | No integrada | Silero VAD integrado |
| **Flexibilidad** | Limitada | Alta configurabilidad |

---

## 🎯 PRÓXIMOS PASOS (FASES 3-7)

### **Fase 3: Integración con lógica del asistente** ⏳
- [ ] Pruebas exhaustivas en Raspberry Pi
- [ ] Optimización de rendimiento
- [ ] Integración robusta con GPIO
- [ ] Tests de integración

### **Fase 4: Optimización y robustez** ⏳
- [ ] Configuración óptima de parámetros
- [ ] Medición de latencia y CPU
- [ ] Optimización para Raspberry Pi
- [ ] Configuración de inference framework

### **Fase 5: Modelo personalizado "Puertocho"** 📋
- [ ] Preparación de entorno de entrenamiento (Google Cloud T4)
- [ ] Generación de datos sintéticos
- [ ] Entrenamiento del modelo
- [ ] Integración del modelo personalizado

### **Fase 6: Validación y despliegue** 📋
- [ ] Testing en diferentes condiciones
- [ ] Validación de métricas (false-accept/reject)
- [ ] Optimización para producción
- [ ] Documentación final

### **Fase 7: Mejoras avanzadas** 📋
- [ ] Modelos verifier de voz específica
- [ ] Soporte multilenguaje
- [ ] Integración con servicios cloud

---

## 📚 RECURSOS Y DOCUMENTACIÓN

### **Enlaces útiles**
- [Repositorio openWakeWord](https://github.com/dscripka/openWakeWord)
- [Documentación oficial](https://github.com/dscripka/openWakeWord#usage)
- [Notebook de entrenamiento](https://github.com/dscripka/openWakeWord/blob/main/notebooks/)
- [Modelos de la comunidad](https://github.com/fwartner/home-assistant-wakewords-collection)

### **Configuraciones recomendadas**
```python
# Para Raspberry Pi
model = Model(
    wakeword_models=["alexa"],
    inference_framework="onnx",          # Más eficiente en RPi
    vad_threshold=0.5,                   # Reduce falsos positivos
    enable_speex_noise_suppression=True  # Para ambientes ruidosos
)
```

---

## ✅ ESTADO ACTUAL

**✅ COMPLETADO:**
- Migración completa de Porcupine a openWakeWord
- Scripts de instalación y configuración automatizados
- Contenedor Docker funcional
- Documentación básica

**🔄 EN PROGRESO:**
- Pruebas en hardware real (Raspberry Pi)
- Optimización de rendimiento

**📋 PENDIENTE:**
- Entrenamiento de modelo personalizado "Puertocho"
- Testing exhaustivo y validación
- Optimización avanzada

La implementación básica está **funcional y lista para pruebas**. El siguiente paso es la validación en hardware real y la preparación para el entrenamiento del modelo personalizado. 