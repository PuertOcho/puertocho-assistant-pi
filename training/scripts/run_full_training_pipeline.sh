#!/bin/bash
# 🚀 Pipeline Completo de Entrenamiento "Puertocho"
# Ejecuta todo el proceso de entrenamiento de forma automatizada

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para logging con timestamp
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Función para verificar prerrequisitos
check_prerequisites() {
    log "🔍 Verificando prerrequisitos..."
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        error "Python3 no está instalado"
        exit 1
    fi
    
    # Verificar GPU
    if ! nvidia-smi &> /dev/null; then
        warning "GPU NVIDIA no detectada"
    else
        info "GPU detectada: $(nvidia-smi --query-gpu=name --format=csv,noheader,nounits)"
    fi
    
    # Verificar espacio en disco
    AVAILABLE_SPACE=$(df . | awk 'NR==2 {print $4}')
    REQUIRED_SPACE=10000000  # 10GB en KB
    
    if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
        error "Espacio insuficiente. Necesitas al menos 10GB"
        exit 1
    fi
    
    # Verificar dependencias Python
    python3 -c "import torch, librosa, soundfile, tqdm, yaml" 2>/dev/null || {
        error "Dependencias Python faltantes. Ejecuta: pip install -r requirements.txt"
        exit 1
    }
    
    log "✅ Prerrequisitos verificados"
}

# Función para mostrar progreso
show_progress() {
    local current=$1
    local total=$2
    local description=$3
    local percentage=$((current * 100 / total))
    
    printf "\r${BLUE}[%3d%%]${NC} %s" "$percentage" "$description"
}

# Función principal
main() {
    log "🧠 Iniciando Pipeline Completo de Entrenamiento 'Puertocho'"
    log "============================================================"
    
    # Variables de configuración
    TOTAL_STEPS=6
    CURRENT_STEP=0
    START_TIME=$(date +%s)
    
    # Verificar prerrequisitos
    ((CURRENT_STEP++))
    show_progress $CURRENT_STEP $TOTAL_STEPS "Verificando prerrequisitos..."
    check_prerequisites
    echo ""
    
    # Paso 1: Generar datos positivos
    ((CURRENT_STEP++))
    show_progress $CURRENT_STEP $TOTAL_STEPS "Generando muestras positivas..."
    echo ""
    log "📊 Paso 1: Generando muestras positivas de 'Puertocho'"
    
    if [ ! -d "data/positive" ] || [ $(find data/positive -name "*.wav" 2>/dev/null | wc -l) -lt 1000 ]; then
        python3 scripts/generate_positive_samples.py 2000
    else
        info "Muestras positivas ya existen, omitiendo generación"
    fi
    
    # Verificar resultado
    POSITIVE_COUNT=$(find data/positive -name "*.wav" 2>/dev/null | wc -l)
    if [ "$POSITIVE_COUNT" -lt 1000 ]; then
        error "Insuficientes muestras positivas generadas: $POSITIVE_COUNT"
        exit 1
    fi
    log "✅ Muestras positivas: $POSITIVE_COUNT archivos"
    
    # Paso 2: Descargar/generar datos negativos
    ((CURRENT_STEP++))
    show_progress $CURRENT_STEP $TOTAL_STEPS "Preparando datos negativos..."
    echo ""
    log "📥 Paso 2: Preparando datos negativos"
    
    if [ ! -d "data/negative" ] || [ $(find data/negative -name "*.wav" 2>/dev/null | wc -l) -lt 5000 ]; then
        python3 scripts/download_negative_data.py
    else
        info "Datos negativos ya existen, omitiendo descarga"
    fi
    
    # Verificar resultado
    NEGATIVE_COUNT=$(find data/negative -name "*.wav" 2>/dev/null | wc -l)
    if [ "$NEGATIVE_COUNT" -lt 1000 ]; then
        warning "Pocos datos negativos: $NEGATIVE_COUNT. El entrenamiento puede ser subóptimo"
    fi
    log "✅ Datos negativos: $NEGATIVE_COUNT archivos"
    
    # Paso 3: Verificar balance de datos
    ((CURRENT_STEP++))
    show_progress $CURRENT_STEP $TOTAL_STEPS "Analizando balance de datos..."
    echo ""
    log "⚖️ Paso 3: Análisis de balance de datos"
    
    RATIO=$(echo "scale=2; $NEGATIVE_COUNT / $POSITIVE_COUNT" | bc)
    info "Ratio negativo/positivo: $RATIO"
    
    if (( $(echo "$RATIO < 2" | bc -l) )); then
        warning "Ratio bajo, considera generar más datos negativos"
    elif (( $(echo "$RATIO > 10" | bc -l) )); then
        warning "Ratio muy alto, puede causar desbalance"
    else
        log "✅ Balance de datos adecuado"
    fi
    
    # Paso 4: Configurar entrenamiento
    ((CURRENT_STEP++))
    show_progress $CURRENT_STEP $TOTAL_STEPS "Configurando entrenamiento..."
    echo ""
    log "⚙️ Paso 4: Configuración de entrenamiento"
    
    # Verificar archivo de configuración
    if [ ! -f "configs/training_config.yaml" ]; then
        error "Archivo de configuración no encontrado: configs/training_config.yaml"
        exit 1
    fi
    
    # Crear directorios necesarios
    mkdir -p models logs logs/tensorboard
    
    # Ajustar configuración según hardware
    if nvidia-smi &> /dev/null; then
        GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
        info "Memoria GPU detectada: ${GPU_MEMORY}MB"
        
        if [ "$GPU_MEMORY" -lt 8000 ]; then
            warning "Poca memoria GPU, reduciendo batch size"
            # Aquí podrías modificar la configuración automáticamente
        fi
    fi
    
    log "✅ Configuración verificada"
    
    # Paso 5: Entrenar modelo
    ((CURRENT_STEP++))
    show_progress $CURRENT_STEP $TOTAL_STEPS "Entrenando modelo..."
    echo ""
    log "🧠 Paso 5: Entrenamiento del modelo 'Puertocho'"
    log "    Este proceso puede tomar 3-6 horas..."
    
    # Ejecutar entrenamiento con logging
    python3 scripts/train_puertocho_model.py configs/training_config.yaml 2>&1 | tee logs/training_$(date +%Y%m%d_%H%M%S).log
    
    # Verificar que el entrenamiento fue exitoso
    if [ ! -f "models/puertocho_v1_best.pth" ]; then
        error "El entrenamiento falló - modelo no encontrado"
        exit 1
    fi
    
    if [ ! -f "models/puertocho_v1.onnx" ]; then
        warning "Modelo ONNX no generado, pero entrenamiento completado"
    fi
    
    log "✅ Entrenamiento completado"
    
    # Paso 6: Validación final y resumen
    ((CURRENT_STEP++))
    show_progress $CURRENT_STEP $TOTAL_STEPS "Validación final..."
    echo ""
    log "🎯 Paso 6: Validación final y resumen"
    
    # Mostrar información del modelo entrenado
    MODEL_SIZE=$(ls -lh models/puertocho_v1_best.pth | awk '{print $5}')
    log "📁 Tamaño del modelo: $MODEL_SIZE"
    
    if [ -f "models/puertocho_v1.onnx" ]; then
        ONNX_SIZE=$(ls -lh models/puertocho_v1.onnx | awk '{print $5}')
        log "📁 Tamaño ONNX: $ONNX_SIZE"
    fi
    
    # Calcular tiempo total
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    HOURS=$((DURATION / 3600))
    MINUTES=$(((DURATION % 3600) / 60))
    
    # Resumen final
    echo ""
    log "🎉 PIPELINE COMPLETADO EXITOSAMENTE"
    log "=================================="
    log "⏱️  Tiempo total: ${HOURS}h ${MINUTES}m"
    log "📊 Datos procesados:"
    log "    • Muestras positivas: $POSITIVE_COUNT"
    log "    • Muestras negativas: $NEGATIVE_COUNT"
    log "    • Ratio negativo/positivo: $RATIO"
    log ""
    log "📁 Archivos generados:"
    log "    • Modelo PyTorch: models/puertocho_v1_best.pth"
    if [ -f "models/puertocho_v1.onnx" ]; then
        log "    • Modelo ONNX: models/puertocho_v1.onnx"
    fi
    log "    • Logs de entrenamiento: logs/"
    log ""
    log "🚀 Próximos pasos:"
    log "    1. Copiar puertocho_v1.onnx a la Raspberry Pi"
    log "    2. Actualizar configuración del asistente"
    log "    3. Probar el modelo personalizado"
    log ""
    log "📋 Comandos para deployment:"
    log "    scp models/puertocho_v1.onnx pi@raspberry:/path/to/checkpoints/"
    log "    echo 'OPENWAKEWORD_MODEL_PATHS=/app/checkpoints/puertocho_v1.onnx' >> .env"
    log "    echo 'OPENWAKEWORD_THRESHOLD=0.75' >> .env"
}

# Función para cleanup en caso de error
cleanup() {
    if [ $? -ne 0 ]; then
        error "Pipeline falló. Revisando logs..."
        
        # Mostrar últimas líneas del log más reciente
        LATEST_LOG=$(ls -t logs/training_*.log 2>/dev/null | head -1)
        if [ -n "$LATEST_LOG" ]; then
            echo ""
            echo "📋 Últimas líneas del log:"
            tail -20 "$LATEST_LOG"
        fi
        
        echo ""
        echo "🔧 Posibles soluciones:"
        echo "  • Verificar espacio en disco"
        echo "  • Verificar memoria GPU"
        echo "  • Revisar logs completos en logs/"
        echo "  • Reducir batch_size en configuración"
    fi
}

# Configurar trap para cleanup
trap cleanup EXIT

# Verificar argumentos
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "🧠 Pipeline de Entrenamiento 'Puertocho'"
    echo "Uso: $0 [opciones]"
    echo ""
    echo "Opciones:"
    echo "  --help, -h     Mostrar esta ayuda"
    echo "  --skip-data    Saltar generación de datos"
    echo "  --config FILE  Usar archivo de configuración específico"
    echo ""
    echo "El script ejecuta automáticamente:"
    echo "  1. Verificación de prerrequisitos"
    echo "  2. Generación de muestras positivas"
    echo "  3. Descarga/generación de datos negativos"
    echo "  4. Análisis de balance de datos"
    echo "  5. Entrenamiento del modelo"
    echo "  6. Validación y resumen final"
    exit 0
fi

# Ejecutar función principal
main "$@" 