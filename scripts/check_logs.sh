#!/bin/bash

# Script para verificar los logs de los servicios del ecosistema PuertoCho Assistant
# Autor: PuertoCho Assistant Team
# Fecha: $(date +"%Y-%m-%d")

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar encabezados
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Función para mostrar información
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# Función para mostrar advertencias
print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Función para mostrar errores
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para verificar si Docker está disponible
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado o no está disponible en el PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
        print_error "Ni docker-compose ni docker compose están disponibles"
        exit 1
    fi
}

# Función para verificar si los servicios están ejecutándose
check_services() {
    print_header "VERIFICANDO ESTADO DE LOS SERVICIOS"
    
    # Verificar usando docker compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi
    
    # Mostrar estado de todos los servicios
    echo -e "${BLUE}Estado de los contenedores:${NC}"
    $COMPOSE_CMD ps
    
    # Verificar servicios específicos
    local services=("puertocho-backend" "puertocho-web-dashboard" "puertocho-hardware")
    
    for service in "${services[@]}"; do
        if $COMPOSE_CMD ps | grep -q "$service.*Up"; then
            print_info "✅ $service está ejecutándose"
        else
            print_warning "⚠️  $service no está ejecutándose"
        fi
    done
}

# Función para mostrar logs de un servicio específico
show_service_logs() {
    local service=$1
    local lines=${2:-50}
    
    print_header "LOGS DE $service (últimas $lines líneas)"
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi
    
    if $COMPOSE_CMD ps | grep -q "$service.*Up"; then
        $COMPOSE_CMD logs --tail="$lines" "$service"
    else
        print_warning "El servicio $service no está ejecutándose"
    fi
}

# Función para mostrar logs en tiempo real
show_realtime_logs() {
    local service=$1
    
    print_header "LOGS EN TIEMPO REAL DE $service"
    print_info "Presiona Ctrl+C para salir"
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi
    
    if $COMPOSE_CMD ps | grep -q "$service.*Up"; then
        $COMPOSE_CMD logs -f "$service"
    else
        print_warning "El servicio $service no está ejecutándose"
    fi
}

# Función para mostrar logs de todos los servicios
show_all_logs() {
    local lines=${1:-50}
    
    print_header "LOGS DE TODOS LOS SERVICIOS"
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi
    
    $COMPOSE_CMD logs --tail="$lines"
}

# Función para mostrar logs agregados en tiempo real
show_realtime_all_logs() {
    print_header "LOGS EN TIEMPO REAL DE TODOS LOS SERVICIOS"
    print_info "Presiona Ctrl+C para salir"
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi
    
    $COMPOSE_CMD logs -f
}

# Función para buscar errores en los logs
search_errors() {
    local service=${1:-"all"}
    local lines=${2:-100}
    
    print_header "BÚSQUEDA DE ERRORES EN LOS LOGS"
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi
    
    if [ "$service" == "all" ]; then
        print_info "Buscando errores en todos los servicios (últimas $lines líneas)..."
        $COMPOSE_CMD logs --tail="$lines" | grep -i -E "(error|exception|failed|traceback)" --color=always || print_info "No se encontraron errores"
    else
        print_info "Buscando errores en $service (últimas $lines líneas)..."
        $COMPOSE_CMD logs --tail="$lines" "$service" | grep -i -E "(error|exception|failed|traceback)" --color=always || print_info "No se encontraron errores en $service"
    fi
}

# Función para mostrar estadísticas de los servicios
show_service_stats() {
    print_header "ESTADÍSTICAS DE LOS SERVICIOS"
    
    # Mostrar uso de recursos
    echo -e "${BLUE}Uso de recursos de los contenedores:${NC}"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
    
    # Mostrar puertos expuestos
    echo -e "\n${BLUE}Puertos expuestos:${NC}"
    docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -E "(puertocho|puerto)"
}

# Función para mostrar ayuda
show_help() {
    echo -e "${BLUE}PuertoCho Assistant - Verificador de Logs${NC}"
    echo -e "${BLUE}===========================================${NC}"
    echo ""
    echo "Uso: $0 [OPCIÓN] [ARGUMENTOS]"
    echo ""
    echo "Opciones:"
    echo "  status                    - Mostrar estado de todos los servicios"
    echo "  logs [servicio] [líneas]  - Mostrar logs de un servicio específico"
    echo "  logs-all [líneas]         - Mostrar logs de todos los servicios"
    echo "  follow [servicio]         - Mostrar logs en tiempo real de un servicio"
    echo "  follow-all                - Mostrar logs en tiempo real de todos los servicios"
    echo "  errors [servicio] [líneas] - Buscar errores en los logs"
    echo "  stats                     - Mostrar estadísticas de recursos"
    echo "  help                      - Mostrar esta ayuda"
    echo ""
    echo "Servicios disponibles:"
    echo "  - puertocho-backend       - Backend API (FastAPI)"
    echo "  - puertocho-web-dashboard - Dashboard Web (Svelte)"
    echo "  - puertocho-hardware      - Servicio de Hardware (Wake-word)"
    echo ""
    echo "Ejemplos:"
    echo "  $0 status"
    echo "  $0 logs puertocho-backend 100"
    echo "  $0 follow puertocho-hardware"
    echo "  $0 errors all 200"
    echo "  $0 stats"
}

# Función principal
main() {
    # Verificar dependencias
    check_docker
    
    # Cambiar al directorio del proyecto
    cd "$(dirname "$0")/.."
    
    case "${1:-help}" in
        "status")
            check_services
            ;;
        "logs")
            if [ -z "$2" ]; then
                print_error "Debes especificar un servicio"
                echo "Servicios disponibles: puertocho-backend, puertocho-web-dashboard, puertocho-hardware"
                exit 1
            fi
            show_service_logs "$2" "${3:-50}"
            ;;
        "logs-all")
            show_all_logs "${2:-50}"
            ;;
        "follow")
            if [ -z "$2" ]; then
                print_error "Debes especificar un servicio"
                echo "Servicios disponibles: puertocho-backend, puertocho-web-dashboard, puertocho-hardware"
                exit 1
            fi
            show_realtime_logs "$2"
            ;;
        "follow-all")
            show_realtime_all_logs
            ;;
        "errors")
            search_errors "${2:-all}" "${3:-100}"
            ;;
        "stats")
            show_service_stats
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            print_error "Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@"
