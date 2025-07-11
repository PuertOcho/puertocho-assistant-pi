# PROJECT TRACKER - PuertoCho Assistant Ecosystem

Este es el tracker centralizado para coordinar el desarrollo simultáneo de todos los microservicios del ecosistema PuertoCho Assistant.

## Arquitectura del Ecosistema

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                PuertoCho Assistant                                 │
│                                                                                     │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────────────────┐  │
│  │   Web Dashboard  │◄──►│   Backend API    │◄──►│     Wake-Word Services      │  │
│  │     (Svelte)     │    │    (FastAPI)     │    │  - Porcupine (primary)      │  │
│  │                  │    │                  │    │                              │  │
│  │  Port: 3000/80   │    │   Port: 8765     │    │   Port: 8080 (porcupine)    │  │
│  └──────────────────┘    └──────────────────┘    └──────────────────────────────┘  │
│                                                                                     │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────────────────┐  │
│  │   QML Desktop    │    │   STT/NLU        │    │    Hardware Integration     │  │
│  │    (Optional)    │    │   Services       │    │  - GPIO (LEDs, buttons)     │  │
│  │                  │    │   (Future)       │    │  - Audio I/O                │  │
│  └──────────────────┘    └──────────────────┘    └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Estado Global del Proyecto

### 🟢 COMPLETADO
- **Backend API**: MVP funcional con WebSockets ✅
- **Web Dashboard**: Interfaz reactiva conectada ✅
- **Wake-Word (Porcupine)**: Integración básica ✅
- **Comunicación**: Protocolo WebSocket definido ✅
- **Containerización**: Docker setup básico ✅

### 🟡 EN PROGRESO
- **Wake-Word Personalizado**: Entrenamiento modelo "Puertocho"
- **Integración Backend-WakeWord**: Conexión en tiempo real
- **Optimización**: Performance y robustez

### 🔴 PENDIENTE
- **STT/NLU Integration**: Servicios de comprensión
- **Hardware GPIO**: LEDs y botones físicos
- **Producción**: Deployment y monitoring

---

## FASE 1: FUNDACIÓN COMPLETA ✅ COMPLETADA

### 1.1 Backend API (puertocho-assistant-backend) ✅
- [x] Estructura de proyecto Python con FastAPI
- [x] Servidor WebSocket en puerto 8765
- [x] Protocolo de comunicación JSON definido
- [x] Endpoints de simulación para testing
- [x] Health check endpoint
- [x] Containerización con Docker

### 1.2 Web Dashboard (puertocho-assistant-web-view) ✅
- [x] Proyecto Svelte con Vite
- [x] Componentes UI (StatusIndicator, CommandHistory)
- [x] Conexión WebSocket reactiva
- [x] Stores para estado y comandos
- [x] Botón de activación manual
- [x] Containerización con Docker

### 1.3 Wake-Word Base (wake-word-porcupine-version) ✅
- [x] Instalación de Porcupine
- [x] Configuración de access key
- [x] Modelo "Puerto-ocho" personalizado
- [x] Captura de audio en tiempo real
- [x] Detección básica de wake word
- [x] Sistema de comandos integrado

---

## FASE 2: INTEGRACIÓN INTERMEDIA 🟡 EN PROGRESO

### 2.1 Conexión Backend ↔ Wake-Word Services
- [ ] **Tarea 2.1.1: Análisis de APIs Existentes**
  - [ ] Revisar protocolo de comunicación de wake-word-porcupine-version
  - [ ] Decidir arquitectura de comunicación (HTTP, WebSocket, IPC)
  - [ ] Documentar especificación de integración

- [ ] **Tarea 2.1.2: Cliente Wake-Word en Backend**
  - [ ] Implementar cliente para Porcupine
  - [ ] Manejar eventos de detección de wake-word
  - [ ] Propagar cambios de estado al dashboard

- [ ] **Tarea 2.1.3: Máquina de Estados**
  - [ ] Implementar estados: `idle` → `listening` → `processing` → `idle`
  - [ ] Manejar activación manual desde dashboard
  - [ ] Manejar activación automática por wake-word
  - [ ] Broadcast de cambios de estado

### 2.2 Modelo Personalizado "Puertocho"
- [ ] **Tarea 2.2.1: Optimización del Modelo Existente**
  - [ ] Evaluar rendimiento del modelo actual "Puerto-ocho"
  - [ ] Ajustar threshold específico para diferentes entornos
  - [ ] Optimizar configuración de Porcupine
  - [ ] Documentar configuración óptima

- [ ] **Tarea 2.2.2: Entrenamiento Adicional (Opcional)**
  - [ ] Evaluar necesidad de modelo adicional con Porcupine Console
  - [ ] Generar datos de entrenamiento si es necesario
  - [ ] Entrenar modelo complementario si se requiere
  - [ ] Integrar modelos múltiples

- [ ] **Tarea 2.2.3: Validación y Testing**
  - [ ] Probar en diferentes condiciones de ruido
  - [ ] Validar false-accept rate (<0.5/hora)
  - [ ] Validar false-reject rate (<5%)
  - [ ] Documentar proceso de configuración

### 2.3 Robustez y Optimización
- [ ] **Tarea 2.3.1: Configuración Avanzada**
  - [ ] Ajustar umbral de activación por entorno
  - [ ] Configurar sensibilidad de Porcupine
  - [ ] Optimizar configuración de audio
  - [ ] Implementar configuración dinámica

- [ ] **Tarea 2.3.2: Performance en Raspberry Pi**
  - [ ] Medir latencia y consumo de recursos
  - [ ] Optimizar uso de CPU y memoria
  - [ ] Configurar parámetros de audio óptimos
  - [ ] Implementar monitoreo de rendimiento

---

## FASE 3: FUNCIONALIDADES AVANZADAS 🔴 PENDIENTE

### 3.1 Procesamiento de Comandos
- [ ] **Tarea 3.1.1: Integración STT (Speech-to-Text)**
  - [ ] Evaluar servicios STT (Google, Azure, local)
  - [ ] Implementar cliente STT en backend## FASE 3: FUNCIONALIDADES AVANZADAS 🔴 PENDIENTE

  - [ ] Manejar transcripción de audio post wake-word
  - [ ] Implementar fallback entre servicios

- [ ] **Tarea 3.1.2: Integración NLU (Natural Language Understanding)**
  - [ ] Definir intents y entities para comandos
  - [ ] Implementar procesador de comandos
  - [ ] Integrar con servicios NLU o implementar local
  - [ ] Registrar comandos procesados

- [ ] **Tarea 3.1.3: Sistema de Comandos**
  - [ ] Definir comandos básicos del asistente
  - [ ] Implementar ejecutor de comandos
  - [ ] Integrar con servicios externos (IoT, APIs)
  - [ ] Manejar respuestas y feedback

### 3.2 Hardware Integration
- [ ] **Tarea 3.2.1: GPIO Integration**
  - [ ] Integrar LEDs de estado (idle, listening, processing)
  - [ ] Implementar botón físico de activación
  - [ ] Manejar interrupciones de hardware
  - [ ] Sincronizar estado hardware con dashboard

- [ ] **Tarea 3.2.2: Audio I/O Optimization**
  - [ ] Configurar dispositivos de audio óptimos
  - [ ] Implementar cancelación de eco
  - [ ] Optimizar latencia de audio
  - [ ] Manejar múltiples dispositivos de audio

### 3.3 QML Desktop Interface (Opcional)
- [ ] **Tarea 3.3.1: Aplicación QML**
  - [ ] Completar interfaz desktop con Qt/QML
  - [ ] Integrar con backend via WebSocket
  - [ ] Sincronizar estado con web dashboard
  - [ ] Packaging para distribución

---

## FASE 4: PRODUCCIÓN Y DEPLOYMENT 🔴 PENDIENTE

### 4.1 Orquestación y Configuración
- [x] **Tarea 4.1.1: Docker Compose Master**
  - [x] Crear docker-compose.yml en raíz del proyecto
  - [x] Orquestar todos los servicios (backend, web, wake-word)
  - [x] Configurar redes y volúmenes
  - [x] Definir dependencias entre servicios

- [ ] **Tarea 4.1.2: Configuración Centralizada**
  - [ ] Sistema de configuración unificado
  - [ ] Variables de entorno por servicio
  - [ ] Configuración de URLs y puertos
  - [ ] Secrets management

- [ ] **Tarea 4.1.3: Scripts de Deployment**
  - [ ] Script de instalación para Raspberry Pi
  - [ ] Script de actualización automática
  - [ ] Script de backup y restore
  - [ ] Documentación de deployment

### 4.2 Monitoring y Logging
- [ ] **Tarea 4.2.1: Logging Estructurado**
  - [ ] Implementar logging consistente en todos los servicios
  - [ ] Configurar niveles de log
  - [ ] Centralizaar logs con agregador
  - [ ] Implementar rotación de logs

- [ ] **Tarea 4.2.2: Health Checks y Monitoring**
  - [ ] Health checks para todos los servicios
  - [ ] Métricas de performance
  - [ ] Alertas automáticas
  - [ ] Dashboard de monitoring

- [ ] **Tarea 4.2.3: Error Handling y Recovery**
  - [ ] Manejo de errores robusto
  - [ ] Auto-recovery de servicios
  - [ ] Fallback entre servicios
  - [ ] Graceful shutdown

### 4.3 Documentación y Testing
- [ ] **Tarea 4.3.1: Testing Integral**
  - [ ] Tests unitarios por servicio
  - [ ] Tests de integración inter-servicios
  - [ ] Tests end-to-end
  - [ ] Performance testing

- [ ] **Tarea 4.3.2: Documentación Final**
  - [ ] Documentación de arquitectura
  - [ ] Guías de usuario
  - [ ] Troubleshooting guide
  - [ ] API documentation

---

## DEPENDENCIAS ENTRE SERVICIOS

### Críticas (Bloquean desarrollo)
- **Backend ← Wake-Word**: Sin integración, no hay detección automática
- **Web Dashboard ← Backend**: Sin backend, no hay interfaz funcional
- **Modelo Personalizado ← Entrenamiento**: Sin modelo, no hay wake-word "Puertocho"

### Importantes (Afectan funcionalidad)
- **STT/NLU ← Backend**: Sin procesamiento, no hay comprensión de comandos
- **Hardware GPIO ← Backend**: Sin integración, no hay indicadores físicos
- **Monitoring ← Todos**: Sin monitoreo, difícil debugging en producción

### Opcionales (Mejoran experiencia)
- **QML Desktop ← Backend**: Interfaz alternativa
- **Configuración Avanzada**: Ajustes finos de Porcupine
- **Cloud Services ← Local**: Backup y mejoras

---

## CONFIGURACIÓN DE DESARROLLO

### Puertos Reservados
- **3000**: Web Dashboard (desarrollo)
- **80**: Web Dashboard (producción)
- **8765**: Backend API (WebSocket)
- **8080**: Wake-Word Porcupine

### Variables de Entorno Globales
```bash
# Backend
BACKEND_HOST=localhost
BACKEND_PORT=8765
BACKEND_LOG_LEVEL=INFO

# Wake-Word Services
WAKEWORD_SERVICE_URL=http://localhost:8080
WAKEWORD_THRESHOLD=0.5
PORCUPINE_ACCESS_KEY=your_access_key_here

# Web Dashboard
VITE_BACKEND_WS_URL=ws://localhost:8765/ws
VITE_BACKEND_HTTP_URL=http://localhost:8765

# Hardware (Raspberry Pi)
GPIO_ENABLED=true
AUDIO_DEVICE_INDEX=0
```

### Comandos de Desarrollo
```bash
# Iniciar todo el ecosistema
docker-compose up -d

# Desarrollo individual
cd puertocho-assistant-backend && python -m uvicorn src.main:app --reload --port 8765
cd puertocho-assistant-web-view && npm run dev
cd wake-word-porcupine-version && python app/main.py

# Testing
make test-all
make test-integration
```

---

## ROADMAP TEMPORAL

### Sprint 1 (Semana 1-2): Integración Básica
- [ ] Backend ↔ Wake-Word Porcupine
- [ ] Estados de transición automática
- [ ] Logging integrado

### Sprint 2 (Semana 3-4): Modelo Personalizado
- [ ] Optimización "Puerto-ocho"
- [ ] Configuración dinámica
- [ ] Validación y testing

### Sprint 3 (Semana 5-6): Robustez
- [ ] Performance optimization
- [ ] Hardware GPIO integration
- [ ] Error handling

### Sprint 4 (Semana 7-8): Producción
- [ ] Docker compose master
- [ ] Deployment scripts
- [ ] Monitoring y logging

---

## NOTAS Y DECISIONES

### Decisiones Técnicas
- **Framework Backend**: FastAPI (WebSocket nativo, async)
- **Framework Frontend**: Svelte (ligero, reactivo)
- **Wake-Word**: Porcupine (modelo personalizado "Puerto-ocho")
- **Containerización**: Docker (portabilidad multi-arquitectura)

### Consideraciones de Hardware
- **Target Platform**: Raspberry Pi 4+ (4GB RAM mínimo)
- **Audio**: USB microphone + speakers/headphones
- **GPIO**: LEDs para estado, botón para activación manual
- **Storage**: 32GB SD card mínimo

### Próximas Decisiones Pendientes
- [ ] Servicio STT: ¿Local (Whisper) o Cloud (Google/Azure)?
- [ ] Servicio NLU: ¿Local (spaCy) o Cloud (Dialogflow)?
- [ ] Base de datos: ¿SQLite local o PostgreSQL?
- [ ] Monitoreo: ¿Prometheus/Grafana o solución cloud?

---

*Último update: 11 Julio 2025*  
*Mantenido por: Equipo PuertoCho Assistant*
