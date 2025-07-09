#!/bin/bash

# Script de compilación para PuertoCho Assistant Dashboard
# Uso: ./build.sh [release|debug|clean]

set -e  # Salir si hay errores

PROJECT_NAME="PuertoChoAssistantView"
BUILD_DIR="build"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con color
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  PuertoCho Assistant Builder${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Verificar dependencias
check_dependencies() {
    print_message "Verificando dependencias..."
    
    if ! command -v cmake &> /dev/null; then
        print_error "CMake no está instalado. Instálalo con: sudo apt install cmake"
        exit 1
    fi
    
    if ! command -v make &> /dev/null; then
        print_error "Make no está instalado. Instálalo con: sudo apt install build-essential"
        exit 1
    fi
    
    # Verificar Qt6
    if ! dpkg -l | grep -q qt6-base-dev; then
        print_warning "Qt6 puede no estar instalado. Para instalarlo:"
        echo "sudo apt install qt6-base-dev qt6-declarative-dev qt6-tools-dev"
    fi
    
    print_message "Dependencias verificadas ✓"
}

# Función de limpieza
clean_build() {
    print_message "Limpiando archivos de compilación..."
    if [ -d "$BUILD_DIR" ]; then
        rm -rf "$BUILD_DIR"
        print_message "Directorio build eliminado ✓"
    else
        print_message "No hay nada que limpiar ✓"
    fi
}

# Función de compilación
build_project() {
    BUILD_TYPE=${1:-Release}
    
    print_message "Iniciando compilación en modo $BUILD_TYPE..."
    
    # Crear directorio de build
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"
    
    # Configurar con CMake
    print_message "Configurando proyecto con CMake..."
    if cmake .. -DCMAKE_BUILD_TYPE="$BUILD_TYPE"; then
        print_message "Configuración completada ✓"
    else
        print_error "Error en la configuración de CMake"
        exit 1
    fi
    
    # Compilar
    print_message "Compilando proyecto..."
    if make -j$(nproc); then
        print_message "Compilación completada ✓"
    else
        print_error "Error en la compilación"
        exit 1
    fi
    
    cd "$SCRIPT_DIR"
    
    print_message "¡Proyecto compilado exitosamente!"
    print_message "Ejecutable disponible en: $BUILD_DIR/$PROJECT_NAME"
}

# Función para ejecutar la aplicación
run_application() {
    if [ -f "$BUILD_DIR/$PROJECT_NAME" ]; then
        print_message "Ejecutando $PROJECT_NAME..."
        cd "$BUILD_DIR"
        ./"$PROJECT_NAME"
    else
        print_error "El ejecutable no existe. Compila primero con: ./build.sh"
        exit 1
    fi
}

# Información del sistema
show_system_info() {
    print_message "Información del sistema:"
    echo "  - OS: $(uname -s) $(uname -r)"
    echo "  - Arquitectura: $(uname -m)"
    echo "  - Procesador: $(nproc) cores"
    
    if command -v qmake6 &> /dev/null; then
        echo "  - Qt6: $(qmake6 -query QT_VERSION)"
    else
        echo "  - Qt6: No encontrado"
    fi
    
    if [ -f /proc/device-tree/model ]; then
        echo "  - Modelo: $(cat /proc/device-tree/model 2>/dev/null | tr -d '\0')"
    fi
}

# Función de ayuda
show_help() {
    echo "Uso: $0 [OPCIÓN]"
    echo ""
    echo "Opciones:"
    echo "  release    Compilar en modo Release (por defecto)"
    echo "  debug      Compilar en modo Debug"
    echo "  clean      Limpiar archivos de compilación"
    echo "  run        Ejecutar la aplicación"
    echo "  info       Mostrar información del sistema"
    echo "  help       Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0                # Compilar en modo Release"
    echo "  $0 debug          # Compilar en modo Debug"
    echo "  $0 clean          # Limpiar y compilar"
    echo "  $0 run            # Ejecutar la aplicación"
}

# Script principal
main() {
    print_header
    
    case "${1:-release}" in
        "release")
            check_dependencies
            build_project "Release"
            ;;
        "debug")
            check_dependencies
            build_project "Debug"
            ;;
        "clean")
            clean_build
            check_dependencies
            build_project "Release"
            ;;
        "run")
            run_application
            ;;
        "info")
            show_system_info
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar script principal
main "$@" 