#!/bin/bash
# 📊 Script de Monitoreo del Entrenamiento Puertocho
# Supervisa el progreso y muestra métricas en tiempo real

echo "🔍 MONITOR DE ENTRENAMIENTO PUERTOCHO"
echo "======================================"
echo "Fecha/Hora: $(date)"
echo ""

# Función para mostrar estado de proceso
check_process() {
    local process_name="$1"
    local pid=$(pgrep -f "$process_name")
    if [ -n "$pid" ]; then
        echo "✅ Proceso activo: $process_name (PID: $pid)"
        local cpu=$(ps -p $pid -o %cpu --no-headers | tr -d ' ')
        local mem=$(ps -p $pid -o %mem --no-headers | tr -d ' ')
        echo "   📊 CPU: ${cpu}% | RAM: ${mem}%"
        return 0
    else
        echo "❌ Proceso inactivo: $process_name"
        return 1
    fi
}

# Función para mostrar estado de GPU
check_gpu() {
    echo "🖥️  ESTADO DE GPU:"
    nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits | while IFS=',' read name util mem_used mem_total temp; do
        echo "   GPU: $name"
        echo "   Utilización: ${util}%"
        echo "   Memoria: ${mem_used}MB / ${mem_total}MB ($(echo "$mem_used * 100 / $mem_total" | bc)%)"
        echo "   Temperatura: ${temp}°C"
    done
    echo ""
}

# Función para mostrar logs recientes
check_logs() {
    local log_dir="$1"
    echo "📝 LOGS RECIENTES ($log_dir):"
    if [ -d "$log_dir" ]; then
        if [ -f "$log_dir/training.log" ]; then
            echo "   Últimas 5 líneas:"
            tail -5 "$log_dir/training.log" | sed 's/^/   /'
        elif [ -f "$log_dir/test_training.log" ]; then
            echo "   Últimas 5 líneas (test):"
            tail -5 "$log_dir/test_training.log" | sed 's/^/   /'
        else
            echo "   ⚠️  Sin archivos de log específicos"
            local latest_log=$(find "$log_dir" -name "*.log" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
            if [ -n "$latest_log" ]; then
                echo "   Último log encontrado: $(basename "$latest_log")"
                tail -3 "$latest_log" | sed 's/^/   /'
            fi
        fi
    else
        echo "   ❌ Directorio de logs no existe"
    fi
    echo ""
}

# Función para mostrar archivos generados
check_outputs() {
    echo "📁 ARCHIVOS GENERADOS:"
    for dir in "test_models" "test_logs" "models" "logs"; do
        if [ -d "$dir" ]; then
            local count=$(find "$dir" -type f | wc -l)
            echo "   $dir/: $count archivos"
            if [ $count -gt 0 ]; then
                find "$dir" -type f -printf '   - %f (%s bytes)\n' | head -3
                if [ $count -gt 3 ]; then
                    echo "   ... y $(($count - 3)) más"
                fi
            fi
        fi
    done
    echo ""
}

# Función para mostrar métricas del sistema
check_system() {
    echo "🖥️  MÉTRICAS DEL SISTEMA:"
    echo "   Carga del sistema: $(uptime | awk -F'load average:' '{print $2}')"
    echo "   Memoria libre: $(free -h | awk '/^Mem:/ {print $7}') / $(free -h | awk '/^Mem:/ {print $2}')"
    echo "   Espacio en disco: $(df -h /home | awk 'NR==2 {print $4}') disponible"
    echo ""
}

# Mostrar información del proceso de entrenamiento
echo "🎯 ESTADO DEL ENTRENAMIENTO:"
if check_process "train_puertocho_model.py"; then
    echo ""
    check_gpu
    check_logs "test_logs"
    check_logs "logs"
    check_outputs
    check_system
    
    echo "⏱️  TIEMPO DE EJECUCIÓN:"
    local start_time=$(stat -c %Y logs/training.log 2>/dev/null || stat -c %Y test_logs/ 2>/dev/null || echo $(date +%s))
    local current_time=$(date +%s)
    local elapsed=$((current_time - start_time))
    local hours=$((elapsed / 3600))
    local minutes=$(((elapsed % 3600) / 60))
    local seconds=$((elapsed % 60))
    echo "   Tiempo transcurrido: ${hours}h ${minutes}m ${seconds}s"
    
else
    echo ""
    echo "🔍 VERIFICANDO ESTADO:"
    check_logs "test_logs"
    check_logs "logs"
    check_outputs
    
    # Verificar si hay errores recientes
    if [ -f "test_logs/training.log" ] || [ -f "logs/training.log" ]; then
        echo "🚨 POSIBLES ERRORES:"
        grep -i "error\|traceback\|exception" test_logs/*.log logs/*.log 2>/dev/null | tail -3 | sed 's/^/   /'
        echo ""
    fi
fi

echo "💡 Para monitoreo continuo, ejecuta:"
echo "   watch -n 30 './monitor_training.sh'"
echo ""
echo "🔄 Última actualización: $(date)" 