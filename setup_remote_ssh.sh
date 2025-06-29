#!/bin/bash
# ============================================
# CONFIGURACIÓN AUTOMÁTICA REMOTE-SSH CURSOR
# Para Asistente de Voz Puertocho
# ============================================

echo "🚀 CONFIGURANDO REMOTE-SSH PARA CURSOR..."
echo "============================================"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para verificar comando
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✅ $1 encontrado${NC}"
        return 0
    else
        echo -e "${RED}❌ $1 no encontrado${NC}"
        return 1
    fi
}

# PASO 1: Verificar herramientas
echo -e "${BLUE}📦 VERIFICANDO HERRAMIENTAS...${NC}"
check_command "cursor" || { echo "Instala Cursor primero"; exit 1; }
check_command "ssh" || { echo "SSH no disponible"; exit 1; }

# PASO 2: Verificar claves SSH
echo -e "${BLUE}🔑 VERIFICANDO CLAVES SSH...${NC}"
if [ -f ~/.ssh/id_ed25519 ]; then
    echo -e "${GREEN}✅ Clave SSH encontrada${NC}"
else
    echo -e "${YELLOW}⚠️  Generando clave SSH...${NC}"
    ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
fi

# PASO 3: Configuración específica para puertochopi.local
echo -e "${BLUE}🌐 CONFIGURACIÓN DE RED...${NC}"
PI_HOST="puertochopi.local"
PI_USER="puertocho"
echo -e "${GREEN}✅ Usando configuración predefinida:${NC}"
echo "   Host: $PI_HOST"
echo "   Usuario: $PI_USER"
echo ""

# PASO 4: Configuración SSH ya está actualizada
echo -e "${BLUE}📝 VERIFICANDO CONFIGURACIÓN SSH...${NC}"
if grep -q "puertochopi.local" ~/.ssh/config; then
    echo -e "${GREEN}✅ Configuración SSH actualizada correctamente${NC}"
else
    echo -e "${RED}❌ Error en configuración SSH${NC}"
    exit 1
fi

# PASO 5: Probar conexión
echo -e "${BLUE}🔗 PROBANDO CONEXIÓN...${NC}"
echo "Probando conexión SSH a $PI_USER@$PI_HOST..."

if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no $PI_USER@$PI_HOST "echo 'Conexión exitosa'" 2>/dev/null; then
    echo -e "${GREEN}✅ Conexión SSH exitosa${NC}"
else
    echo -e "${YELLOW}⚠️  Primera conexión - copiando clave SSH...${NC}"
    echo "Ingresa la contraseña '$PI_USER' (1212) cuando se solicite:"
    ssh-copy-id $PI_USER@$PI_HOST
    
    # Verificar nuevamente
    if ssh -o ConnectTimeout=5 $PI_USER@$PI_HOST "echo 'Conexión exitosa'" 2>/dev/null; then
        echo -e "${GREEN}✅ Conexión SSH configurada correctamente${NC}"
    else
        echo -e "${RED}❌ Error en la conexión. Verifica:${NC}"
        echo "   - La Pi está encendida y en la red"
        echo "   - SSH está habilitado en la Pi"
        echo "   - El hostname puertochopi.local resuelve correctamente"
        echo "   - La contraseña es: 1212"
        exit 1
    fi
fi

# PASO 6: Verificar proyecto en la Pi
echo -e "${BLUE}📁 VERIFICANDO PROYECTO EN LA PI...${NC}"
PROJECT_PATH="/home/$PI_USER/puertocho-assistant-pi"

if ssh $PI_USER@$PI_HOST "[ -d '$PROJECT_PATH' ]"; then
    echo -e "${GREEN}✅ Proyecto encontrado en: $PROJECT_PATH${NC}"
else
    echo -e "${YELLOW}⚠️  Creando directorio del proyecto...${NC}"
    ssh $PI_USER@$PI_HOST "mkdir -p $PROJECT_PATH"
    echo -e "${GREEN}✅ Directorio creado: $PROJECT_PATH${NC}"
fi

# PASO 7: Instrucciones finales
echo -e "${GREEN}"
echo "============================================"
echo "🎉 ¡CONFIGURACIÓN COMPLETADA!"
echo "============================================"
echo -e "${NC}"
echo -e "${BLUE}📋 PRÓXIMOS PASOS:${NC}"
echo "1. Abre Cursor"
echo "2. Presiona Ctrl+Shift+P"
echo "3. Escribe 'Remote-SSH: Connect to Host'"
echo "4. Selecciona 'pi-puertocho' o 'puertochopi.local'"
echo "5. Instala extensión Remote-SSH si aparece el prompt"
echo "6. Abre carpeta: $PROJECT_PATH"
echo ""
echo -e "${BLUE}🔧 COMANDOS ÚTILES:${NC}"
echo "# Conectar por terminal:"
echo "ssh pi-puertocho"
echo "# O directamente:"
echo "ssh $PI_USER@$PI_HOST"
echo ""
echo "# Sincronizar código:"
echo "rsync -av ./ $PI_USER@$PI_HOST:$PROJECT_PATH/"
echo ""
echo -e "${YELLOW}⚠️  RECUERDA:${NC}"
echo "- La Pi debe estar encendida y conectada a la red"
echo "- Hostname: $PI_HOST (no necesitas IP fija)"
echo "- Usuario: $PI_USER / Contraseña: 1212"

# Opción para abrir Cursor directamente
echo ""
echo -n "¿Quieres abrir Cursor ahora? (y/n): "
read -r OPEN_CURSOR

if [[ $OPEN_CURSOR =~ ^[Yy]$ ]]; then
    echo "Abriendo Cursor..."
    cursor &
fi

echo -e "${GREEN}✅ ¡Listo para desarrollar!${NC}" 