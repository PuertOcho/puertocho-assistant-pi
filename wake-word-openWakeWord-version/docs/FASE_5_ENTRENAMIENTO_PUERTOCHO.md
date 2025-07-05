# 🧠 Fase 5: Entrenamiento del Modelo Personalizado "Puertocho"

## 🎯 **Objetivo**

Entrenar un modelo openWakeWord personalizado para la palabra "Puertocho" que elimine definitivamente las detecciones múltiples y false positives observados con modelos genéricos.

## 📊 **Estado Actual vs Objetivo**

### ❌ **Problema Actual (openWakeWord genérico)**
```
🎯 Wake word detectada: 'alexa' (score: 0.669)
🎯 Wake word detectada: 'alexa' (score: 0.995)  ← 8s después  
🎯 Wake word detectada: 'alexa' (score: 0.771)  ← Otra vez
```

### ✅ **Objetivo con "Puertocho" personalizado**
```
🎯 Wake word detectada: 'puertocho' (score: 0.85)
👂 Listo para nueva wake word...
[Sin detecciones múltiples - threshold optimizado para palabra específica]
```

## 🔧 **Estrategia de Entrenamiento**

### **Opción 1: Google Cloud GPU T4 (Recomendada)**
Basada en experiencia exitosa con ChatterboxTTS y Porcupine.

**Ventajas:**
- ✅ Control total del entorno
- ✅ GPU T4 optimizada para ML
- ✅ Sin limitaciones de tiempo
- ✅ Costo predecible (~$10-15)

### **Opción 2: Google Colab (Alternativa)**
Solo si la Opción 1 no está disponible.

**Limitaciones:**
- ⚠️ Sesiones de 12h máximo
- ⚠️ Puede desconectarse
- ⚠️ GPU compartida

## 📝 **Plan de Ejecución Detallado**

### **Paso 1: Preparación del Dataset**

#### **1.1 Datos Positivos ("Puertocho")**
```bash
# Generar ~2000 variaciones usando TTS
"Puertocho"
"Hola Puertocho"  
"Oye Puertocho"
"Hey Puertocho"
"Activa Puertocho"
```

**Variaciones necesarias:**
- 🗣️ **Voces**: Masculina, femenina, diferentes acentos
- 🎚️ **Velocidades**: Lenta, normal, rápida
- 🔊 **Volúmenes**: Bajo, normal, alto
- 🎭 **Estilos**: Formal, casual, susurro

#### **1.2 Datos Negativos (Ruido)**
```bash
# Descargar dataset de ruido (~30,000 horas)
- Conversaciones en español
- Ruido ambiente
- Música
- TV/Radio
- Palabras similares: "Puerto", "Ocho", "Macho", etc.
```

### **Paso 2: Configuración del Entorno Cloud**

#### **2.1 Google Cloud Setup**
```bash
# Crear instancia optimizada
gcloud compute instances create puertocho-training \
    --zone=us-central1-a \
    --machine-type=n1-standard-4 \
    --accelerator=type=nvidia-tesla-t4,count=1 \
    --image-family=pytorch-latest-gpu \
    --image-project=deeplearning-platform-release \
    --boot-disk-size=100GB \
    --metadata="install-nvidia-driver=True"
```

#### **2.2 Dependencias**
```bash
# En la instancia Cloud
pip install openwakeword[training]
pip install torch torchaudio
pip install numpy scipy librosa
pip install wandb  # Para monitoreo
pip install tqdm
```

### **Paso 3: Generación de Datos Sintéticos**

#### **3.1 Script de TTS**
```python
import pyttsx3
import os
from pathlib import Path

def generate_puertocho_samples():
    """Generar muestras sintéticas de 'Puertocho'"""
    
    # Configurar TTS
    engine = pyttsx3.init()
    
    # Diferentes voces y configuraciones
    voices = engine.getProperty('voices')
    rates = [150, 180, 220]  # Velocidades
    volumes = [0.7, 0.9, 1.0]  # Volúmenes
    
    phrases = [
        "Puertocho",
        "Hola Puertocho", 
        "Oye Puertocho",
        "Hey Puertocho"
    ]
    
    output_dir = Path("positive_samples")
    output_dir.mkdir(exist_ok=True)
    
    sample_count = 0
    for phrase in phrases:
        for voice in voices[:2]:  # Usar 2 voces
            for rate in rates:
                for volume in volumes:
                    # Configurar voz
                    engine.setProperty('voice', voice.id)
                    engine.setProperty('rate', rate)
                    engine.setProperty('volume', volume)
                    
                    # Generar archivo
                    filename = f"puertocho_{sample_count:04d}.wav"
                    filepath = output_dir / filename
                    
                    engine.save_to_file(phrase, str(filepath))
                    engine.runAndWait()
                    
                    sample_count += 1
                    if sample_count >= 2000:
                        return
    
    print(f"Generadas {sample_count} muestras positivas")
```

#### **3.2 Descarga de Datos Negativos**
```bash
# Usar dataset Common Voice en español
wget https://mozilla-common-voice-datasets.s3.dualstack.us-west-2.amazonaws.com/cv-corpus-13.0-2023-03-09/cv-corpus-13.0-2023-03-09-es.tar.gz

# Extraer y procesar
tar -xzf cv-corpus-13.0-2023-03-09-es.tar.gz
```

### **Paso 4: Entrenamiento del Modelo**

#### **4.1 Configuración de Entrenamiento**
```python
# training_config.yaml
model:
  name: "puertocho_v1"
  architecture: "mel_stft_1d_cnn"
  
training:
  batch_size: 8  # Optimizado para T4
  learning_rate: 1e-4
  epochs: 100
  early_stopping_patience: 10
  
data:
  sample_rate: 16000
  frame_length: 1280  # 80ms
  positive_samples_dir: "./positive_samples"
  negative_samples_dir: "./negative_samples"
  
optimization:
  target_fpr: 0.5  # False positives por hora
  target_fnr: 0.05  # 5% false negatives máximo
```

#### **4.2 Script de Entrenamiento**
```python
import openwakeword.train as oww_train

# Configurar entrenamiento
config = oww_train.load_config("training_config.yaml")

# Preparar datasets
train_loader, val_loader = oww_train.prepare_datasets(config)

# Entrenar modelo
model = oww_train.train_model(
    config=config,
    train_loader=train_loader,
    val_loader=val_loader,
    device="cuda"  # GPU T4
)

# Exportar modelo entrenado
oww_train.export_model(model, "puertocho_v1.onnx")
```

### **Paso 5: Validación y Pruebas**

#### **5.1 Métricas Objetivo**
```python
# Validar rendimiento
test_results = oww_train.evaluate_model(
    model_path="puertocho_v1.onnx",
    test_dataset=test_loader
)

print(f"Accuracy: {test_results['accuracy']:.3f}")
print(f"False Positive Rate: {test_results['fpr']:.3f}/hora")
print(f"False Negative Rate: {test_results['fnr']:.3f}")

# Objetivos:
# - Accuracy > 0.95
# - FPR < 0.5/hora
# - FNR < 0.05
```

#### **5.2 Prueba en Raspberry Pi**
```bash
# Copiar modelo entrenado
scp puertocho_v1.onnx pi@raspberry:/home/pi/checkpoints/

# Actualizar configuración
echo "OPENWAKEWORD_MODEL_PATHS=/app/checkpoints/puertocho_v1.onnx" >> .env
echo "OPENWAKEWORD_THRESHOLD=0.75" >> .env  # Threshold optimizado
```

### **Paso 6: Integración y Optimización**

#### **6.1 Actualizar main.py**
```python
# En _setup_openwakeword()
model_paths_env = os.getenv('OPENWAKEWORD_MODEL_PATHS', '').strip()

if model_paths_env and 'puertocho' in model_paths_env:
    # Usar modelo personalizado
    model_kwargs['wakeword_models'] = [model_paths_env]
    print(f"🧠 Usando modelo personalizado: {model_paths_env}")
else:
    # Fallback a modelos preentrenados
    print("🧠 Usando modelos preentrenados")
```

#### **6.2 Configuración Optimizada**
```bash
# .env para modelo Puertocho
OPENWAKEWORD_MODEL_PATHS=checkpoints/puertocho_v1.onnx
OPENWAKEWORD_THRESHOLD=0.75  # Más alto para menos false positives
OPENWAKEWORD_VAD_THRESHOLD=0.2  # Activar VAD para filtrar ruido
OPENWAKEWORD_ENABLE_SPEEX_NS=true  # Supresión de ruido
```

## 📊 **Cronograma Estimado**

| Fase | Duración | Descripción |
|------|----------|-------------|
| **Setup Cloud** | 1-2 horas | Configurar instancia T4 |
| **Generación TTS** | 2-3 horas | Crear 2000 muestras positivas |
| **Dataset Negativo** | 1-2 horas | Descargar y procesar Common Voice |
| **Entrenamiento** | 3-6 horas | Entrenar modelo en GPU T4 |
| **Validación** | 1 hora | Probar métricas |
| **Integración** | 1 hora | Integrar en Raspberry Pi |
| ****TOTAL** | **9-15 horas** | **Proyecto completo** |

## 💰 **Costo Estimado**

### **Google Cloud T4**
- **Instancia**: n1-standard-4 = $0.15/hora
- **GPU T4**: $0.35/hora  
- **Almacenamiento**: 100GB = $10/mes
- **Total**: ~$12-15 para proyecto completo

### **Beneficio vs Costo**
- ✅ **Elimina detecciones múltiples** definitivamente
- ✅ **Wake word personalizada** exclusiva
- ✅ **Threshold optimizado** para caso específico
- ✅ **Solución permanente** vs parches temporales

## 🚀 **Próximos Pasos**

1. **Decidir plataforma**: ¿Google Cloud T4 o Colab?
2. **Configurar entorno** de entrenamiento
3. **Generar datasets** (positivos + negativos)
4. **Entrenar modelo** "Puertocho"
5. **Validar y optimizar** threshold
6. **Integrar en RPi** y probar

## ❓ **¿Listo para comenzar?**

El modelo personalizado "Puertocho" resolverá definitivamente el problema de detecciones múltiples y proporcionará una wake word única para tu asistente.

¿Prefieres empezar con **Google Cloud T4** (más control) o **Google Colab** (gratis pero limitado)? 