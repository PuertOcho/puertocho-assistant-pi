# 🌐 GUÍA COMPLETA - FASE 3: INFRAESTRUCTURA CLOUD

## 📋 **ESTADO ACTUAL**
✅ **Cuenta Google Cloud creada**  
✅ **Tarjeta verificada**  
✅ **Créditos $300 disponibles**

---

## 🎯 **OBJETIVO FASE 3**
Configurar la infraestructura completa en Google Cloud Platform para entrenar el modelo Chatterbox TTS Español con dataset de 482K muestras (840h de audio) usando GPU A100.

---

## ⚡ **PRERREQUISITOS**

### 1. Instalar Google Cloud SDK
```bash
# Para Ubuntu/Debian
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
sudo apt-get update && sudo apt-get install google-cloud-cli

# Verificar instalación
gcloud version
```

### 2. Autenticarse en Google Cloud
```bash
# Login con tu cuenta
gcloud auth login

# Configurar credenciales por defecto para aplicaciones
gcloud auth application-default login
```

---

## 🚀 **EJECUCIÓN PASO A PASO**

### **PASO 1: Configurar APIs y Proyecto** (15 minutos)
```bash
# Hacer ejecutable el script
chmod +x setup_gcp_apis.sh

# Ejecutar configuración de APIs
./setup_gcp_apis.sh
```

**¿Qué hace este script?**
- ✅ Crea proyecto `chatterbox-spanish-tts`
- ✅ Vincula facturación automáticamente  
- ✅ Activa 8 APIs necesarias (Compute, Storage, etc.)
- ✅ Verifica cuotas GPU disponibles
- ⚠️ **SI FALLA**: Verifica que tienes cuota para GPUs A100

### **PASO 2: Solicitar Cuota GPU A100** (5-60 minutos)
```bash
# Verificar cuota actual
gcloud compute project-info describe --format="table(quotas.metric,quotas.limit)" | grep A100

# Si no tienes cuota, solicitarla:
# 1. Ve a: https://console.cloud.google.com/iam-admin/quotas
# 2. Busca: "NVIDIA A100 GPUs"
# 3. Región: "us-central1"
# 4. Solicita: 1 GPU mínimo
# 5. Justificación: "Entrenamiento modelo TTS español académico"
```

**⏰ Tiempo de aprobación:**
- Con créditos gratuitos: 5-15 minutos
- Cuenta nueva: hasta 24-48 horas

### **PASO 3: Crear Instancia GPU A100** (10 minutos)
```bash
# Solo ejecutar DESPUÉS de tener cuota A100 aprobada
chmod +x setup_gpu_instance.sh
./setup_gpu_instance.sh
```

**¿Qué hace este script?**
- 🎮 Crea instancia `a2-highgpu-1g` (1x A100, 12 vCPU, 85GB RAM)
- 💾 Configura disco SSD de 500GB para datos
- 🔧 Instala drivers NVIDIA automáticamente
- 📦 Configura entorno PyTorch optimizado
- 💰 Costo: ~$3/hora ($72/día)

### **PASO 4: Subir Dataset a Cloud Storage** (30-120 minutos)
```bash
# Ejecutar desde directorio raíz del proyecto
chmod +x setup_cloud_storage.sh
./setup_cloud_storage.sh
```

**¿Qué sube este script?**
- 📊 Dataset completo (482K muestras, 840h)
- 🧠 Tokenizer español BPE (8K tokens)
- 💻 Código fuente del proyecto
- 📜 Scripts de entrenamiento
- 📋 Metadata del proyecto

**⏰ Tiempo estimado de subida:**
- Tokenizer: 2-5 minutos
- Dataset completo: 30-90 minutos (según conexión)
- Código fuente: 1-2 minutos

---

## 🔗 **CONECTAR Y VERIFICAR**

### **Conectar a la Instancia GPU**
```bash
# SSH básico
gcloud compute ssh chatterbox-tts-gpu --zone=us-central1-a

# Con túnel para Jupyter
gcloud compute ssh chatterbox-tts-gpu --zone=us-central1-a -- -L 8888:localhost:8888

# Con túnel para TensorBoard
gcloud compute ssh chatterbox-tts-gpu --zone=us-central1-a -- -L 6006:localhost:6006
```

### **Verificar GPU en la Instancia**
```bash
# Verificar GPU disponible
nvidia-smi

# Verificar PyTorch + CUDA
python3 -c "import torch; print(f'CUDA disponible: {torch.cuda.is_available()}'); print(f'GPUs: {torch.cuda.device_count()}')"
```

### **Sincronizar Datos desde Cloud Storage**
```bash
# Conectar por SSH y ejecutar:
mkdir -p /data/datasets /data/tokenizer

# Descargar tokenizer (crítico)
gsutil -m rsync -r gs://chatterbox-tts-dataset/tokenizer/ /data/tokenizer/

# Descargar subset del dataset para pruebas
gsutil -m rsync -r gs://chatterbox-tts-dataset/datasets/spanish_subset/ /data/datasets/

# Verificar descarga
ls -la /data/tokenizer/
ls -la /data/datasets/
```

---

## 💰 **GESTIÓN DE COSTOS**

### **Costos Estimados Fase 3:**
- 🎮 **GPU A100**: $3.00/hora ($72/día)
- 💾 **Storage**: $1.00/mes (50GB)
- 🌐 **Transferencia**: $0.50 (subida inicial)
- **Total estimado**: $75-150 para completar entrenamiento

### **IMPORTANTE - Gestión de Instancia:**
```bash
# ⚠️ APAGAR cuando no uses (ahorra $$)
gcloud compute instances stop chatterbox-tts-gpu --zone=us-central1-a

# ✅ ENCENDER cuando necesites
gcloud compute instances start chatterbox-tts-gpu --zone=us-central1-a

# 📊 Ver costos actuales
gcloud billing budgets list
```

---

## 🔍 **VERIFICACIÓN FINAL**

### **Checklist Fase 3 Completa:**
- [ ] ✅ Proyecto `chatterbox-spanish-tts` creado
- [ ] ✅ 8 APIs activadas correctamente
- [ ] ✅ Cuota GPU A100 aprobada
- [ ] ✅ Instancia GPU creada y funcionando
- [ ] ✅ Dataset subido a Cloud Storage (gs://chatterbox-tts-dataset)
- [ ] ✅ SSH funcionando a la instancia
- [ ] ✅ GPU verificada con `nvidia-smi`
- [ ] ✅ PyTorch + CUDA funcionando
- [ ] ✅ Datos sincronizados en `/data/`

### **Comando de Verificación Completa:**
```bash
# Ejecutar este script en la instancia GPU
cat << 'EOF' > verify_setup.sh
#!/bin/bash
echo "🔍 VERIFICACIÓN ENTORNO ENTRENAMIENTO"
echo "===================================="
echo "🎮 GPU:"
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv
echo ""
echo "🐍 Python/PyTorch:"
python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.version.cuda}'); print(f'GPUs: {torch.cuda.device_count()}')"
echo ""
echo "💾 Espacio en disco:"
df -h /data
echo ""
echo "📊 Tokenizer:"
ls -la /data/tokenizer/
echo ""
echo "📁 Dataset:"
find /data/datasets -name "*.wav" | wc -l
echo "archivos de audio encontrados"
echo ""
echo "✅ ¡Entorno listo para entrenamiento!"
EOF

chmod +x verify_setup.sh
./verify_setup.sh
```

---

## 📊 **PRÓXIMOS PASOS - FASE 4**

Con la Fase 3 completada, estás listo para:

1. **🔄 FASE 4.1**: Crear scripts de entrenamiento
2. **🔄 FASE 4.2**: Configurar hyperparámetros
3. **🔄 FASE 4.3**: Entrenar modelo (1-2 semanas)
4. **🔄 FASE 4.4**: Validación y optimización

---

## 🆘 **TROUBLESHOOTING**

### **Error: Cuota GPU insuficiente**
```bash
# Verificar cuota actual
gcloud compute project-info describe --format="table(quotas.metric,quotas.limit)" | grep -i gpu
# Solicitar aumento en: https://console.cloud.google.com/iam-admin/quotas
```

### **Error: Falló subida a Cloud Storage**
```bash
# Verificar permisos
gsutil iam get gs://chatterbox-tts-dataset
# Reintentar subida específica
gsutil -m rsync -r ./directorio_problema gs://chatterbox-tts-dataset/destino/
```

### **Error: No se puede conectar por SSH**
```bash
# Verificar estado de la instancia
gcloud compute instances list --filter="name=chatterbox-tts-gpu"
# Reiniciar si es necesario
gcloud compute instances reset chatterbox-tts-gpu --zone=us-central1-a
```

---

## 🎉 **¡FELICITACIONES!**

Si completaste todos los pasos, tienes:
- ✅ **Infraestructura cloud profesional**
- ✅ **GPU A100 optimizada para entrenamiento**
- ✅ **Dataset de 840h listo en la nube**
- ✅ **Entorno PyTorch configurado**

**🚀 ¡Listo para entrenar el mejor TTS español del mundo!** 