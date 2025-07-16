# 🔑 Configuración con archivo .env

El asistente ahora usa un archivo `.env` para cargar las variables de configuración de manera más sencilla y segura.

## 🚀 Configuración rápida

### 1. Ejecutar el configurador automático
```bash
python3 configurar_access_key.py
```

Este comando es inteligente:
- 🔍 **Detecta** si ya tienes configuración válida
- ❓ **Te pregunta** si quieres mantenerla o cambiarla
- 💾 **Preserva** otras configuraciones existentes
- ✅ **Solo pide** nueva clave si es necesario

**Ejemplo de ejecución con configuración existente:**
```
🔑 Configurador de API Keys - Porcupine
========================================

✅ Ya tienes configuración en .env
🔍 Porcupine ACCESS_KEY actual: niQEyzvVe6DEBZBDvPGE...
❓ ¿Quieres mantener la configuración actual? (S/n): 

✅ Configuración mantenida
🚀 Configuración lista para usar
```

### 2. Verificar configuración
```bash
python3 verificar_configuracion.py
```

### 3. Ejecutar el asistente
```bash
# Método recomendado: Instalador automático (ejecuta en segundo plano)
python3 instalar_asistente.py

# O manualmente en segundo plano
docker compose up -d --build

# Ver logs en tiempo real
docker compose logs -f puertocho-assistant
```

### 🎮 Gestión del asistente
```bash
# Gestor completo con menú interactivo
python3 ejecutar_asistente.py

# Comandos directos
python3 ejecutar_asistente.py start    # Ejecutar en segundo plano
python3 ejecutar_asistente.py logs     # Ver logs
python3 ejecutar_asistente.py stop     # Detener
python3 ejecutar_asistente.py status   # Ver estado
```

## 📝 Configuración manual (opcional)

Si prefieres crear el archivo `.env` manualmente:

### 1. Copiar el archivo de ejemplo
```bash
cp env.example .env
```

### 2. Editar el archivo `.env`
```bash
nano .env
```

Completar con tus valores:
```bash
# Configuración del Asistente de Voz Puertocho

# REQUERIDO: Porcupine ACCESS_KEY para detección de wake word
# Obtener de: https://console.picovoice.ai/
PORCUPINE_ACCESS_KEY=tu_access_key_real_aqui

# Servicio de transcripción HTTP
TRANSCRIPTION_SERVICE_URL=http://localhost:5000/transcribe

# Configuración de GPIO (opcional, tienen valores por defecto)
BUTTON_PIN=22
LED_IDLE_PIN=17
LED_RECORD_PIN=27
```

## 🔒 Ventajas del archivo .env

- **🔐 Seguridad**: Las claves no están en el código
- **✅ Simplicidad**: Un solo archivo para toda la configuración
- **🎯 Flexibilidad**: Fácil cambiar configuración sin tocar docker-compose.yml
- **👥 Colaboración**: Cada desarrollador puede tener su propia configuración

## ⚠️ Importante

- El archivo `.env` está en `.gitignore` por seguridad
- No compartas tu archivo `.env` con nadie (contiene tu ACCESS_KEY)
- Si cambias alguna variable, reinicia el contenedor Docker

## 🆘 Solución de problemas

### ❌ Error: "PORCUPINE_ACCESS_KEY no configurado"
```bash
# Verificar que el archivo .env existe
ls -la .env

# Si no existe, ejecutar:
python3 configurar_access_key.py
```

### ❌ Error: "No se puede conectar al servicio de transcripción"
Asegurate de que tu servicio esté ejecutándose:
```bash
curl -X POST http://localhost:5000/transcribe \
  -F "audio=@test.wav"
```

### 📋 Ver variables cargadas
El asistente muestra al inicio qué archivo .env está usando:
```
✅ Variables cargadas desde .env
``` 