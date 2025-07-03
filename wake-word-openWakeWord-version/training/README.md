# 🧠 Entrenamiento del Modelo "Puertocho"

Este directorio contiene todos los scripts y configuraciones necesarios para entrenar un modelo openWakeWord personalizado para la palabra "Puertocho".

## 🎯 Objetivo

Entrenar un modelo de wake word específico que elimine las detecciones múltiples observadas con modelos genéricos y proporcione una palabra de activación única.

## 📁 Estructura del Proyecto

```
training/
├── scripts/                          # Scripts de entrenamiento
│   ├── setup_gcloud.sh              # 🚀 Configurar Google Cloud T4
│   ├── setup_training_env.sh        # 🧠 Configurar entorno en Cloud
│   ├── generate_positive_samples.py # 🗣️ Generar muestras "Puertocho"
│   ├── download_negative_data.py    # 📥 Descargar datos negativos
│   ├── train_puertocho_model.py     # 🧠 Script principal entrenamiento
│   └── run_full_training_pipeline.sh # 🚀 Pipeline completo
├── configs/
│   └── training_config.yaml         # ⚙️ Configuración de entrenamiento
├── data/                            # Datos de entrenamiento (generado)
│   ├── positive/                    # Muestras "Puertocho"
│   └── negative/                    # Muestras ruido/otras palabras
├── models/                          # Modelos entrenados (generado)
├── logs/                            # Logs de entrenamiento (generado)
└── README.md                        # Esta documentación
```

## 🚀 Inicio Rápido

### **Opción 1: Pipeline Automático (Recomendado)**

```bash
# En la instancia Google Cloud T4
cd ~/puertocho-training
./scripts/run_full_training_pipeline.sh
```

Este script ejecuta automáticamente todo el proceso:
1. ✅ Verificación de prerrequisitos
2. 📊 Generación de 2000 muestras positivas
3. 📥 Descarga y procesamiento de datos negativos
4. ⚖️ Análisis de balance de datos
5. 🧠 Entrenamiento del modelo (3-6 horas)
6. 🎯 Validación y resumen final

### **Opción 2: Paso a Paso**

#### **1. Configurar Google Cloud T4**
```bash
# En tu máquina local
./scripts/setup_gcloud.sh tu-project-id
```

#### **2. Conectar y configurar entorno**
```bash
# Conectar a la instancia
gcloud compute ssh puertocho-training --zone=us-central1-a

# Configurar entorno
bash setup_training_env.sh
```

#### **3. Subir scripts de entrenamiento**
```bash
# En tu máquina local
gcloud compute scp --recurse training/ puertocho-training:~/puertocho-training/ --zone=us-central1-a
```

#### **4. Generar datos positivos**
```bash
# En la instancia Cloud
python3 scripts/generate_positive_samples.py 2000
```

#### **5. Descargar datos negativos**
```bash
python3 scripts/download_negative_data.py
```

#### **6. Entrenar modelo**
```bash
python3 scripts/train_puertocho_model.py configs/training_config.yaml
```

## ⚙️ Configuración

### **Archivo de Configuración Principal**
`configs/training_config.yaml` contiene toda la configuración:

```yaml
model:
  name: "puertocho_v1"
  sample_rate: 16000
  frame_length: 1280

training:
  batch_size: 8          # Optimizado para T4
  learning_rate: 1e-4
  epochs: 100
  early_stopping_patience: 10

data:
  target_fpr: 0.5       # False positives por hora
  target_fnr: 0.05      # False negatives máximo
```

### **Variables de Entorno**
```bash
export CUDA_VISIBLE_DEVICES=0
export PYTHONPATH=$PYTHONPATH:~/puertocho-training
```

## 📊 Datos de Entrenamiento

### **Datos Positivos (Generados)**
- **Cantidad**: ~2000 muestras
- **Frases**: "Puertocho", "Hola Puertocho", "Oye Puertocho", etc.
- **Variaciones**: Velocidad, tono, ruido, voces
- **Métodos TTS**: espeak, Festival, gTTS

### **Datos Negativos (Descargados/Generados)**
- **Common Voice español**: ~8000 muestras
- **Ruido sintético**: ~5000 muestras (blanco, rosa, marrón)
- **Palabras similares**: ~280 muestras ("Puerto", "Ocho", etc.)
- **Total**: ~13000+ muestras negativas

### **Balance de Datos**
- **Ratio recomendado**: 4:1 a 6:1 (negativo:positivo)
- **Ratio actual**: ~6.5:1
- **Validación**: 20% de cada tipo

## 🧠 Proceso de Entrenamiento

### **Arquitectura del Modelo**
- **Tipo**: 1D CNN con características mel-spectrogram
- **Input**: 1280 frames @ 16kHz (80ms)
- **Features**: 32 bandas mel
- **Output**: Probabilidad binaria (Puertocho vs No-Puertocho)

### **Optimización**
- **Optimizador**: AdamW con weight decay
- **Loss**: Binary Cross Entropy con logits
- **Scheduler**: OneCycle con warmup
- **AMP**: Automatic Mixed Precision (T4)
- **Gradient Clipping**: Norm = 1.0

### **Métricas Objetivo**
- **Accuracy**: > 95%
- **False Positive Rate**: < 0.5/hora
- **False Negative Rate**: < 5%
- **F1 Score**: > 0.9

## 📈 Monitoreo

### **Durante el Entrenamiento**
```bash
# Monitor de sistema
./monitor_training.sh

# TensorBoard
tensorboard --logdir logs/tensorboard --host 0.0.0.0 --port 6006

# Logs en tiempo real
tail -f logs/training.log
```

### **URLs de Monitoreo**
- **Jupyter Lab**: `http://EXTERNAL_IP:8080`
- **TensorBoard**: `http://EXTERNAL_IP:6006`

## 🎯 Resultados Esperados

### **Archivos Generados**
```
models/
├── puertocho_v1_best.pth      # Mejor modelo PyTorch
├── puertocho_v1.onnx          # Modelo para inferencia
└── puertocho_v1_epoch_*.pth   # Checkpoints por época

logs/
├── training.log               # Log principal
├── training_history_*.json    # Métricas de entrenamiento
└── tensorboard/               # Logs TensorBoard
```

### **Métricas Típicas**
```
Época 45/100:
├── Train Loss: 0.023456
├── Train Acc: 98.2%
├── Val Loss: 0.034567
└── Val Acc: 96.8%

Early stopping: Sin mejora en 10 épocas
Mejor modelo: Época 45 (Val Loss: 0.034567)
```

## 🚀 Deployment

### **1. Descargar Modelo**
```bash
# Desde la instancia Cloud a tu máquina
gcloud compute scp puertocho-training:~/puertocho-training/models/puertocho_v1.onnx . --zone=us-central1-a
```

### **2. Subir a Raspberry Pi**
```bash
# A la Raspberry Pi
scp puertocho_v1.onnx pi@raspberry:/home/pi/puertocho-assistant-pi/wake-word-openWakeWord-version/checkpoints/
```

### **3. Actualizar Configuración**
```bash
# En la Raspberry Pi
echo "OPENWAKEWORD_MODEL_PATHS=/app/checkpoints/puertocho_v1.onnx" >> .env
echo "OPENWAKEWORD_THRESHOLD=0.75" >> .env
echo "OPENWAKEWORD_VAD_THRESHOLD=0.2" >> .env
```

### **4. Probar el Modelo**
```bash
# Reconstruir y probar
docker compose up --build
```

## 🔧 Troubleshooting

### **Problemas Comunes**

#### **Error de Memoria GPU**
```bash
# Reducir batch size
sed -i 's/batch_size: 8/batch_size: 4/' configs/training_config.yaml
```

#### **Datos Insuficientes**
```bash
# Generar más muestras positivas
python3 scripts/generate_positive_samples.py 4000

# O más ruido sintético
# Editar download_negative_data.py línea: generate_synthetic_noise(10000)
```

#### **Convergencia Lenta**
```bash
# Aumentar learning rate
sed -i 's/learning_rate: 1e-4/learning_rate: 3e-4/' configs/training_config.yaml
```

#### **Overfitting**
```bash
# Aumentar dropout
sed -i 's/dropout: 0.3/dropout: 0.5/' configs/training_config.yaml
```

### **Logs de Debug**
```bash
# Ver logs completos
less logs/training_$(date +%Y%m%d)*.log

# Últimas líneas de error
tail -50 logs/training.log

# Métricas de sistema
cat /proc/meminfo | grep Mem
nvidia-smi
```

## 💰 Gestión de Costos

### **Estimación de Costos**
- **Instancia n1-standard-4**: $0.15/hora
- **GPU T4**: $0.35/hora
- **Almacenamiento 100GB**: ~$10/mes
- **Total entrenamiento**: ~$12-15

### **Optimización de Costos**
```bash
# Parar instancia cuando no se use
gcloud compute instances stop puertocho-training --zone=us-central1-a

# Reanudar cuando necesites
gcloud compute instances start puertocho-training --zone=us-central1-a

# Eliminar al finalizar
gcloud compute instances delete puertocho-training --zone=us-central1-a
```

## 📝 Notas Importantes

### **Antes de Entrenar**
- ✅ Verificar cuota de GPU T4 en Google Cloud
- ✅ Tener al menos $20 en créditos
- ✅ Configurar firewall para puertos 8080 y 6006
- ✅ Hacer backup de configuraciones importantes

### **Durante el Entrenamiento**
- 🔄 Monitorear GPU utilization (>80%)
- 📊 Verificar que loss disminuye
- ⏰ Entrenamiento típico: 3-6 horas
- 💾 Checkpoints se guardan automáticamente

### **Después del Entrenamiento**
- 📤 Descargar modelo .onnx inmediatamente
- 🗑️ Limpiar datos temporales grandes
- 💰 Parar/eliminar instancia Cloud
- 🧪 Probar modelo en Raspberry Pi

## 🆘 Soporte

### **Si algo sale mal:**
1. 📋 Revisar logs completos
2. 🔍 Verificar espacio en disco
3. 💾 Verificar memoria GPU
4. 🌐 Verificar conectividad de red
5. 📖 Consultar documentación openWakeWord

### **Recursos Adicionales**
- [openWakeWord Documentation](https://github.com/dscripka/openWakeWord)
- [Google Cloud GPU Guide](https://cloud.google.com/compute/docs/gpus)
- [PyTorch Mixed Precision](https://pytorch.org/docs/stable/amp.html)

---

## 🎉 ¡Éxito!

Si todo va bien, tendrás un modelo **"Puertocho"** personalizado que:
- ✅ Elimina detecciones múltiples
- ✅ Responde solo a "Puertocho"
- ✅ Tiene threshold optimizado (0.75)
- ✅ Reduce false positives <0.5/hora
- ✅ Mantiene false negatives <5%

**¡Tu asistente de voz será único y funcionará perfectamente!** 🚀 