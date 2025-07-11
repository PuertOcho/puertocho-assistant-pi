# 🎙️ PuertoCho Assistant - Raspberry Pi 4

**🆕 VERSIÓN MODULAR**: Sistema completo de asistente de voz para Raspberry Pi 4 con arquitectura modular, backend WebSocket, interfaz web y wake word personalizado.

## 🎯 Descripción

PuertoCho Assistant es un asistente de voz inteligente que combina:
- **🎤 Detección de Wake Word**: "Hola Puertocho" con Porcupine
- **🌐 Backend WebSocket**: FastAPI con comunicación en tiempo real
- **📱 Interfaz Web**: Dashboard Svelte para monitoreo
- **🏠 Control GPIO**: LEDs y botones en Raspberry Pi
- **🧠 Procesamiento Local**: Transcripción y respuestas locales
- **🔧 Arquitectura Modular**: Código organizado y mantenible

## 🏗️ Arquitectura del Sistema

```
📦 PuertoCho Assistant
├── 🎤 wake-word-porcupine-version/     # Asistente de voz (MODULAR)
│   ├── app/
│   │   ├── core/assistant.py          # 🧠 Lógica principal
│   │   ├── api/client.py              # 🌐 Cliente WebSocket
│   │   ├── utils/logging_config.py    # 📝 Logging estructurado
│   │   └── config.py                  # ⚙️ Configuración centralizada
│   └── main.py                        # 🚀 Punto de entrada
├── 🌐 puertocho-assistant-backend/     # Backend WebSocket
└── 📱 puertocho-assistant-web-view/    # Interfaz web
```

## ✨ Características Principales

### 🎤 Asistente de Voz Modular
- **Wake Word Personalizado**: "Hola Puertocho" u "Oye Puertocho"
- **Arquitectura Modular**: Código limpio y mantenible
- **Detección de Silencio**: Termina automáticamente la grabación
- **Control GPIO**: LEDs indicadores y botón de activación manual
- **Transcripción Local**: Procesamiento rápido y privado

### 🌐 Backend WebSocket
- **FastAPI**: API moderna y performante
- **Comunicación en Tiempo Real**: WebSocket para updates instantáneos
- **Arquitectura Escalable**: Preparado para múltiples clientes
- **Logging Estructurado**: Trazabilidad completa

### 📱 Interfaz Web
- **Dashboard Svelte**: Interfaz moderna y responsive
- **Monitoreo en Tiempo Real**: Estado del asistente en vivo
- **Control Remoto**: Activación y configuración desde web
- **Historial de Comandos**: Seguimiento de actividad

## 🚀 Instalación Rápida

### Prerrequisitos
- Raspberry Pi 4 con Raspberry Pi OS
- Docker y Docker Compose
- Micrófono y LEDs conectados
- Acceso a Picovoice Console para API Key

### 1. Clonar el Repositorio
```bash
git clone <tu-repositorio>
cd puertocho-assistant-pi
```

### 2. Configurar Variables de Entorno
```bash
cp .env.example .env
nano .env
```

Configura tu `PORCUPINE_ACCESS_KEY` y otras variables necesarias.

### 3. Ejecutar el Sistema Completo
```bash
# Construir y ejecutar todos los servicios
docker compose up --build

# Ejecutar en background
docker compose up -d --build
```

### 4. Acceder a la Interfaz Web
- **Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8765

## 🔧 Configuración

### Variables de Entorno Principales
```env
# Porcupine (Obligatorio)
PORCUPINE_ACCESS_KEY=tu_access_key_aqui

# GPIO (Raspberry Pi)
BUTTON_PIN=22
LED_IDLE_PIN=17
LED_RECORD_PIN=27

# URLs de servicios
BACKEND_WEBSOCKET_URL=ws://localhost:8765/ws
VITE_BACKEND_WS_URL=ws://localhost:8765/ws
```

### Hardware Requerido
- **Raspberry Pi 4**: Con GPIO habilitado
- **Micrófono**: Conexión USB o jack 3.5mm
- **LED Verde**: GPIO 17 (estado listo)
- **LED Rojo**: GPIO 27 (estado grabando)
- **Botón**: GPIO 22 (activación manual)
- **Resistencias**: 220Ω para LEDs

## 📊 Servicios del Sistema

| Servicio | Puerto | Descripción |
|----------|---------|-------------|
| **Backend WebSocket** | 8765 | API principal y comunicación en tiempo real |
| **Interfaz Web** | 3000 | Dashboard de monitoreo y control |
| **Asistente de Voz** | - | Procesamiento de voz y control GPIO |

## 🎯 Uso

### Activación por Voz
1. Di **"Hola Puertocho"** u **"Oye Puertocho"**
2. Espera a que se encienda el LED rojo
3. Habla tu comando
4. El sistema detecta silencio y procesa el comando

### Activación Manual
- Presiona el **botón** (GPIO 22) para activar
- Presiona nuevamente para cancelar durante la grabación

### Comandos Disponibles
- "enciende luz verde"
- "apaga luz verde"
- "enciende luz roja"
- "apaga luz roja"
- Personalizable en `wake-word-porcupine-version/app/commands.json`

## 🔍 Monitoreo

### Logs en Tiempo Real
```bash
# Ver logs del asistente
docker compose logs -f puertocho-assistant

# Ver logs del backend
docker compose logs -f puertocho-backend

# Ver logs de todos los servicios
docker compose logs -f
```

### Dashboard Web
- **Estado del Sistema**: Conectividad y health checks
- **Historial de Comandos**: Últimos comandos ejecutados
- **Métricas**: Estadísticas de uso
- **Configuración**: Ajustes remotos

## 🛠️ Desarrollo

### Arquitectura Modular
El sistema usa una arquitectura modular que facilita el desarrollo y mantenimiento:

```
wake-word-porcupine-version/app/
├── core/
│   └── assistant.py      # Lógica principal del asistente
├── api/
│   └── client.py         # Cliente WebSocket
├── utils/
│   └── logging_config.py # Configuración de logging
├── config.py             # Configuración centralizada
├── main.py               # Punto de entrada
└── main_modular.py       # Implementación modular
```

### Extensibilidad
- **Nuevos Módulos**: Fácil agregar funcionalidades
- **Plugins**: Sistema preparado para plugins
- **APIs**: Integración con servicios externos
- **Sensores**: Soporte para hardware adicional

## 🐛 Solución de Problemas

### Problemas Comunes
1. **Error de API Key**: Verificar `PORCUPINE_ACCESS_KEY` en `.env`
2. **GPIO no funciona**: Asegurar `privileged: true` en Docker
3. **Audio no detectado**: Verificar conexión del micrófono
4. **Servicios no conectan**: Verificar puertos y URLs

### Diagnóstico
```bash
# Verificar estado de servicios
docker compose ps

# Verificar logs específicos
docker compose logs puertocho-assistant

# Verificar configuración
docker compose config
```

## 📚 Documentación Adicional

- **[Configuración Avanzada](wake-word-porcupine-version/README.md)**: Detalles del asistente de voz
- **[Arquitectura Modular](wake-word-porcupine-version/README_MODULAR.md)**: Documentación técnica
- **[Notas de Migración](wake-word-porcupine-version/MIGRATION_NOTES.md)**: Proceso de modernización

## 🎯 Roadmap

### Próximas Características
- [ ] **Sistema de Plugins**: Carga dinámica de funcionalidades
- [ ] **API REST**: Endpoints HTTP para control remoto
- [ ] **Base de Datos**: Persistencia de configuración
- [ ] **Sensores IoT**: Integración con hardware adicional
- [ ] **Reconocimiento de Voz Mejorado**: Múltiples idiomas
- [ ] **Interface Móvil**: App para smartphones

### Mejoras Técnicas
- [ ] **Testing Automatizado**: Unit tests para cada módulo
- [ ] **CI/CD**: Pipeline de integración continua
- [ ] **Métricas**: Monitoring de performance
- [ ] **Documentación API**: Docs auto-generadas

## 🤝 Contribución

¡Las contribuciones son bienvenidas! La arquitectura modular facilita el desarrollo colaborativo:

1. Fork el proyecto
2. Crear rama para nueva funcionalidad
3. Hacer cambios en el módulo apropiado
4. Añadir tests si es necesario
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- **Picovoice**: Por Porcupine Wake Word Engine
- **FastAPI**: Por el excelente framework web
- **Svelte**: Por la interfaz de usuario moderna
- **Docker**: Por facilitar el deployment

---

**¡Creado con ❤️ para la comunidad de makers y entusiastas de IoT!**
