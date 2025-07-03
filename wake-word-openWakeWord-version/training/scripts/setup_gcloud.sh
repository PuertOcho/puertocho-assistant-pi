#!/bin/bash
# 🚀 Setup Google Cloud T4 para entrenamiento del modelo "Puertocho"
# Basado en experiencia exitosa previa

set -e

echo "🚀 Configurando Google Cloud T4 para entrenamiento 'Puertocho'"
echo "=================================================="

# Variables de configuración
PROJECT_ID="${1:-puertocho-assistant}"  # Cambiar por tu project ID
INSTANCE_NAME="puertocho-training"
ZONE="us-central1-a"
MACHINE_TYPE="n1-standard-4"
GPU_TYPE="nvidia-tesla-t4"
GPU_COUNT="1"
DISK_SIZE="100GB"

echo "📋 Configuración:"
echo "   Project: $PROJECT_ID"
echo "   Instance: $INSTANCE_NAME"
echo "   Zone: $ZONE"
echo "   Machine: $MACHINE_TYPE"
echo "   GPU: $GPU_TYPE x$GPU_COUNT"
echo "   Disk: $DISK_SIZE"
echo ""

# 1. Verificar que gcloud esté instalado y configurado
if ! command -v gcloud &> /dev/null; then
    echo "❌ ERROR: gcloud no está instalado"
    echo "💡 Instala desde: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# 2. Verificar autenticación
echo "🔐 Verificando autenticación..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "❌ ERROR: No hay cuenta autenticada"
    echo "💡 Ejecuta: gcloud auth login"
    exit 1
fi

# 3. Configurar proyecto por defecto
echo "🔧 Configurando proyecto..."
gcloud config set project "$PROJECT_ID"

# 4. Habilitar APIs necesarias
echo "🔌 Habilitando APIs necesarias..."
gcloud services enable compute.googleapis.com
gcloud services enable ml.googleapis.com

# 5. Verificar cuotas de GPU T4
echo "🔍 Verificando disponibilidad de GPU T4 en $ZONE..."
QUOTA_INFO=$(gcloud compute project-info describe --format="value(quotas[?metric:'NVIDIA_T4_GPUS'].limit)" 2>/dev/null || echo "0")

if [ "$QUOTA_INFO" = "0" ] || [ -z "$QUOTA_INFO" ]; then
    echo "⚠️  WARNING: Puede que necesites solicitar cuota para GPU T4"
    echo "💡 Ve a: https://console.cloud.google.com/iam-admin/quotas"
    echo "🔍 Busca: 'GPUs (all regions)' y 'NVIDIA T4 GPUs'"
    echo ""
    read -p "¿Continuar de todas formas? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 6. Crear instancia con GPU T4
echo "🏗️  Creando instancia $INSTANCE_NAME..."

# Comando para crear la instancia
gcloud compute instances create "$INSTANCE_NAME" \
    --zone="$ZONE" \
    --machine-type="$MACHINE_TYPE" \
    --accelerator="type=$GPU_TYPE,count=$GPU_COUNT" \
    --image-family="pytorch-latest-gpu" \
    --image-project="deeplearning-platform-release" \
    --boot-disk-size="$DISK_SIZE" \
    --boot-disk-type="pd-standard" \
    --metadata="install-nvidia-driver=True" \
    --maintenance-policy="TERMINATE" \
    --provisioning-model="STANDARD" \
    --scopes="https://www.googleapis.com/auth/cloud-platform"

# 7. Esperar a que la instancia esté lista
echo "⏳ Esperando a que la instancia esté lista..."
gcloud compute instances wait-until-running "$INSTANCE_NAME" --zone="$ZONE"

# 8. Obtener IP externa
EXTERNAL_IP=$(gcloud compute instances describe "$INSTANCE_NAME" --zone="$ZONE" --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

echo ""
echo "✅ Instancia creada correctamente!"
echo "=================================================="
echo "🌐 IP Externa: $EXTERNAL_IP"
echo "🔗 SSH: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
echo "💻 Jupyter: http://$EXTERNAL_IP:8080 (cuando esté configurado)"
echo ""
echo "🚀 Próximos pasos:"
echo "   1. Conectar: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
echo "   2. Ejecutar: bash setup_training_env.sh"
echo "   3. Subir datos de entrenamiento"
echo ""
echo "💰 Costo estimado: ~\$0.50/hora (\$12-15 total)"
echo "🛑 Para detener: gcloud compute instances stop $INSTANCE_NAME --zone=$ZONE"
echo "🗑️  Para eliminar: gcloud compute instances delete $INSTANCE_NAME --zone=$ZONE" 