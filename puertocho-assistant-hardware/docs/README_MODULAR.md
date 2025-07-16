# PuertoCho Assistant - Estructura Modular

## 📋 Descripción

El asistente PuertoCho ha sido refactorizado a una estructura modular que separa las responsabilidades y mejora la mantenibilidad del código.

## 🏗️ Estructura Modular

```
wake-word-porcupine-version/
├── app/
│   ├── main_modular.py          # Punto de entrada modular
│   ├── config.py                # Configuración centralizada
│   ├── core/
│   │   ├── __init__.py
│   │   └── assistant.py         # Lógica principal del asistente
│   ├── api/
│   │   ├── __init__.py
│   │   └── client.py            # Cliente para comunicación con backend
│   ├── utils/
│   │   ├── __init__.py
│   │   └── logging_config.py    # Configuración de logging
│   └── ...
├── migrate_to_modular.py        # Script de migración
└── README_MODULAR.md            # Este archivo
```

## 🎯 Beneficios de la Estructura Modular

### ✅ Organización Mejorada
- **Separación clara de responsabilidades**: Cada módulo tiene una función específica
- **Código más legible**: Archivos más pequeños y enfocados
- **Navegación más fácil**: Encontrar funcionalidades específicas

### ✅ Mantenibilidad
- **Modificaciones aisladas**: Cambios en un módulo no afectan otros
- **Testing más sencillo**: Cada módulo puede probarse independientemente
- **Debug más eficiente**: Problemas localizados en módulos específicos

### ✅ Extensibilidad
- **Nuevas funcionalidades**: Agregar módulos sin modificar código existente
- **Integración de servicios**: Fácil conexión con nuevos backends
- **Configuración flexible**: Centralizada y adaptable

### ✅ Robustez
- **Manejo de errores**: Mejor control de excepciones por módulo
- **Logging estructurado**: Trazabilidad mejorada
- **Recuperación de fallos**: Aislamiento de problemas

## 📦 Módulos Principales

### 1. `core/assistant.py`
**Responsabilidad**: Lógica principal del asistente de voz

**Características**:
- Detección de wake words con Porcupine
- Grabación y procesamiento de audio
- Integración con servicios de transcripción
- Control de GPIO (LEDs, botones)
- Manejo de estados del asistente

**Clases principales**:
- `VoiceAssistant`: Clase principal del asistente
- `AssistantState`: Estados del asistente (IDLE, LISTENING, PROCESSING)

### 2. `api/client.py`
**Responsabilidad**: Comunicación con el backend

**Características**:
- Cliente WebSocket para comunicación en tiempo real
- Manejo de reconexiones automáticas
- Callbacks para eventos de conexión
- Protocolo de mensajes estructurado

**Clases principales**:
- `BackendClient`: Cliente para comunicación WebSocket

### 3. `utils/logging_config.py`
**Responsabilidad**: Configuración de logging

**Características**:
- Configuración centralizada de logs
- Diferentes niveles de logging
- Formateo consistente
- Rotación de archivos de log

### 4. `config.py`
**Responsabilidad**: Configuración centralizada

**Características**:
- Gestión de variables de entorno
- Configuración de audio automática
- Validación de parámetros
- Detección de dispositivos

**Clases principales**:
- `Config`: Configuración centralizada del sistema

### 5. `main_modular.py`
**Responsabilidad**: Punto de entrada y orquestación

**Características**:
- Inicialización ordenada de componentes
- Manejo de señales del sistema
- Bucle principal de la aplicación
- Limpieza de recursos

**Clases principales**:
- `PuertoChoApp`: Aplicación principal

## 🚀 Uso

### Ejecución Normal
```bash
# Opción 1: Usar directamente el punto de entrada modular
python main_modular.py

# Opción 2: Usar el main.py que redirige automáticamente
python main.py
```

### Migración desde Versión Monolítica
```bash
# Verificar estado de la estructura modular
python migrate_to_modular.py check

# Migrar automáticamente
python migrate_to_modular.py migrate
```

## 🔧 Configuración

### Variables de Entorno
La configuración se gestiona principalmente a través de variables de entorno:

```bash
# Configuración esencial
PORCUPINE_ACCESS_KEY=your_access_key_here

# URLs de servicios
ASSISTANT_CHAT_URL=http://localhost:8765/api/assistant/chat
TRANSCRIPTION_SERVICE_URL=http://localhost:5000/transcribe
BACKEND_WEBSOCKET_URL=ws://localhost:8765/ws

# GPIO (Raspberry Pi)
BUTTON_PIN=22
LED_IDLE_PIN=17
LED_RECORD_PIN=27

# Audio
AUDIO_DEVICE_INDEX=0  # Opcional, se detecta automáticamente
```

### Archivos de Configuración
- `.env`: Variables de entorno (se carga automáticamente)
- `commands.json`: Comandos de voz reconocidos
- `Puerto-ocho_es_raspberry-pi_v3_0_0.ppn`: Modelo personalizado de Porcupine

## 🐛 Troubleshooting

### Problemas Comunes

1. **Error de importación de módulos**
   ```bash
   # Verificar que todos los archivos __init__.py existen
   python migrate_to_modular.py check
   ```

2. **Configuración incompleta**
   ```bash
   # Verificar variables de entorno
   python -c "from config import Config; c = Config(); print('Config OK' if c.validate() else 'Config ERROR')"
   ```

3. **Problemas de audio**
   ```bash
   # Listar dispositivos disponibles
   python -c "from config import Config; Config().list_audio_devices()"
   ```

### Logs y Debug
```bash
# Ejecutar con logging detallado
PYTHONUNBUFFERED=1 python main_modular.py

# Verificar logs específicos de cada módulo
# Los logs incluyen el nombre del módulo para facilitar el debug
```

## 🔄 Migración Gradual

### Paso 1: Verificar Estado Actual
```bash
python migrate_to_modular.py check
```

### Paso 2: Hacer Backup
El script de migración automáticamente hace backup del `main.py` original.

### Paso 3: Migrar
```bash
python migrate_to_modular.py migrate
```

### Paso 4: Verificar Funcionamiento
```bash
python main_modular.py
```

### Paso 5: Rollback (si es necesario)
```bash
# Restaurar versión original
cp app/main_original_backup.py app/main.py
```

## 📈 Desarrollo Futuro

### Extensiones Planificadas
- **Plugins dinámicos**: Sistema de plugins para funcionalidades adicionales
- **API REST**: Endpoint HTTP para control remoto
- **Interface web**: Dashboard web para monitoreo
- **Sensores IoT**: Integración con sensores de temperatura, movimiento, etc.
- **Base de datos**: Persistencia de conversaciones y configuraciones

### Contribuciones
La estructura modular facilita las contribuciones:
- Cada módulo puede desarrollarse independientemente
- Tests unitarios por módulo
- Documentación específica por funcionalidad
- Menor probabilidad de conflictos en el código

## 📚 Documentación Adicional

- `docs/CONFIGURACION_ENV.md`: Configuración detallada de variables de entorno
- `docs/INICIO_RAPIDO.md`: Guía de inicio rápido
- `docs/REFACTORING_SUMMARY.md`: Resumen técnico del refactoring

## ⚠️ Compatibilidad

- **Python**: 3.8+
- **Raspberry Pi**: Todas las versiones con GPIO
- **Docker**: Compatible con la imagen actual
- **Dependencias**: Mismas que la versión monolítica

La estructura modular mantiene **100% de compatibilidad** con la funcionalidad existente, solo mejora la organización del código.
