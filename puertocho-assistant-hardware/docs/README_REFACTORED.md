# 🎤 Asistente de Voz PuertoCho - Versión Porcupine

## 📁 Nueva Estructura del Proyecto

El proyecto ha sido refactorizado para una mejor organización y mantenibilidad:

```
wake-word-porcupine-version/
├── app/                           # Aplicación principal
│   ├── __init__.py
│   ├── main.py                    # Archivo original (legacy)
│   ├── main_new.py               # Nuevo punto de entrada
│   ├── config.py                 # Configuración centralizada
│   ├── commands.json             # Comandos del asistente
│   ├── requirements.txt          # Dependencias Python
│   ├── core/                     # Lógica del asistente
│   │   ├── __init__.py
│   │   └── assistant.py          # Clase principal del asistente
│   ├── api/                      # Comunicación con backend
│   │   ├── __init__.py
│   │   └── client.py             # Cliente WebSocket
│   └── utils/                    # Utilidades
│       ├── __init__.py
│       └── logging_config.py     # Configuración de logging
├── scripts/                      # Scripts de utilidad
│   ├── instalar_asistente.py     # Instalación automática
│   ├── ejecutar_asistente.py     # Ejecución del asistente
│   ├── verificar_configuracion.py # Verificación de configuración
│   ├── configurar_access_key.py  # Configuración de Porcupine API Key
│   └── descargar_modelo_espanol.py # Descarga de modelo español
├── docs/                         # Documentación
├── checkpoints/                  # Modelos entrenados
├── .env                          # Variables de entorno
├── docker-compose.yml           # Configuración Docker
├── Dockerfile                   # Imagen Docker
└── README.md                    # Este archivo
```

## 🚀 Inicio Rápido

### 1. Instalación Automática

```bash
# Instalar y configurar todo automáticamente
python3 scripts/instalar_asistente.py
```

### 2. Ejecución Manual

```bash
# Opción 1: Ejecución con logs visibles
python3 scripts/ejecutar_asistente.py

# Opción 2: Ejecución directa de la aplicación refactorizada
cd app && python3 main_new.py
```

### 3. Configuración

```bash
# Configurar Porcupine Access Key interactivamente
python3 scripts/configurar_access_key.py

# Verificar configuración
python3 scripts/verificar_configuracion.py

# Descargar modelo en español (si es necesario)
python3 scripts/descargar_modelo_espanol.py
```

## 🔧 Configuración

### Variables de Entorno (.env)

```bash
# Obligatorio: Access Key de Porcupine
PORCUPINE_ACCESS_KEY=tu_access_key_aqui

# GPIO (Raspberry Pi)
BUTTON_PIN=22
LED_IDLE_PIN=17
LED_RECORD_PIN=27

# Servicios externos
ASSISTANT_CHAT_URL=http://192.168.1.88:8080/api/assistant/chat
TRANSCRIPTION_SERVICE_URL=http://192.168.1.88:5000/transcribe
BACKEND_WEBSOCKET_URL=ws://localhost:8765/ws
```

## 🏗️ Arquitectura Refactorizada

### Separación de Responsabilidades

1. **`app/config.py`**: Gestión centralizada de configuración
   - Carga variables de entorno
   - Validación de configuración crítica
   - Detección automática de hardware

2. **`app/core/assistant.py`**: Lógica principal del asistente
   - Detección de wake words con Porcupine
   - Grabación y procesamiento de audio
   - Gestión de estados (idle, listening, processing)
   - Control de GPIO (LEDs y botón)

3. **`app/api/client.py`**: Comunicación con backend
   - Conexión WebSocket con el backend
   - Envío de estados y comandos
   - Manejo de reconexión automática

4. **`app/utils/logging_config.py`**: Sistema de logging
   - Configuración estructurada de logs
   - Diferentes niveles de verbosidad

### Beneficios de la Refactorización

- ✅ **Modularidad**: Cada componente tiene una responsabilidad específica
- ✅ **Mantenibilidad**: Fácil localización y corrección de errores
- ✅ **Escalabilidad**: Facilita la adición de nuevas funcionalidades
- ✅ **Reutilización**: Componentes reutilizables en otros proyectos
- ✅ **Testing**: Estructura que facilita las pruebas unitarias
- ✅ **Rutas dinámicas**: Todos los scripts funcionan desde cualquier ubicación

## 🔗 Integración con Backend

El asistente refactorizado se conecta automáticamente al backend (`puertocho-assistant-backend`) vía WebSocket:

- Envía actualizaciones de estado en tiempo real
- Transmite comandos reconocidos
- Recibe comandos de activación manual
- Manejo de reconexión automática

## 🎯 Wake Words Soportadas

- **Modelo personalizado**: "Hola Puertocho", "Oye Puertocho"
- **Fallback genérico**: "Hey Google", "Alexa"

## 🔴 LEDs y Controles (Raspberry Pi)

- **LED Verde (GPIO 17)**: Asistente listo (idle)
- **LED Rojo (GPIO 27)**: Escuchando audio
- **Botón (GPIO 22)**: Activación manual

## 📋 Comandos Docker

```bash
# Ver estado
docker compose ps

# Ver logs en tiempo real
docker compose logs -f puertocho-assistant

# Detener
docker compose stop

# Reiniciar
docker compose restart

# Reconstruir
docker compose up --build -d
```

## 🐛 Solución de Problemas

### Error: No se encuentra .env
```bash
# Copiar desde ejemplo
cp env.example .env
# Editar y configurar PORCUPINE_ACCESS_KEY
```

### Error: GPIO no disponible
- Normal en sistemas que no son Raspberry Pi
- Los LEDs y botón se deshabilitarán automáticamente

### Error: Audio no disponible
```bash
# Instalar dependencias de audio
sudo apt-get install portaudio19-dev
pip install sounddevice
```

### Error: Backend no conecta
- Verificar que `puertocho-assistant-backend` esté ejecutándose
- Comprobar la URL en `BACKEND_WEBSOCKET_URL`

## 📖 Documentación Adicional

- Ver `docs/` para documentación técnica detallada
- Consultar `INTEGRATION_SUCCESS.md` para información de integración
- Revisar `PROJECT_TRACKER.md` para seguimiento del desarrollo

## 🤝 Contribuir

Para contribuir al proyecto:

1. Mantener la separación de responsabilidades
2. Usar el sistema de logging estructurado
3. Actualizar rutas dinámicamente (usar `PROJECT_ROOT`)
4. Documentar cambios en este README
