# Project Tracker: PuertoCho Assistant - Backend API

Este documento sirve como backlog para el desarrollo del backend del asistente PuertoCho que conecta el dashboard web con los servicios de wake-word.

## Objetivo del Proyecto

Crear un backend API que actúe como intermediario entre:
- El dashboard web (frontend Svelte)
- Los servicios de wake-word existentes (`wake-word-openWakeWord-version` y `wake-word-porcupine-version`)
- Otros microservicios del ecosistema PuertoCho

## Fase 1: Fundación del Backend (MVP) ✅ COMPLETADA

El objetivo es tener un servidor WebSocket funcional que pueda comunicarse con el dashboard web.

-   [x] **Tarea 1: Inicializar Proyecto Backend** ✅
    -   [x] Crear estructura de proyecto Python (FastAPI + WebSockets)
    -   [x] Configurar `requirements.txt` con dependencias básicas
    -   [x] Crear `Dockerfile` para containerización
    -   [x] Crear `docker-compose.yml` para desarrollo local
    -   [x] Configurar estructura de carpetas (`src/`, `tests/`, etc.)

-   [x] **Tarea 2: Implementar Servidor WebSocket Básico** ✅
    -   [x] Configurar FastAPI con soporte para WebSockets
    -   [x] Implementar endpoint WebSocket en `/ws` en puerto 8765
    -   [x] Manejar conexión/desconexión de clientes
    -   [x] Implementar broadcast de mensajes a todos los clientes conectados

-   [x] **Tarea 3: Definir Protocolo de Comunicación** ✅
    -   [x] Documentar formato de mensajes JSON entre frontend y backend
    -   [x] Implementar manejo de mensaje `manual_activation`
    -   [x] Implementar envío de `status_update` (`idle`, `listening`, `processing`, `error`)
    -   [x] Implementar envío de `command_log` con timestamp y comando

-   [x] **Tarea 4: Validación Inicial con Frontend** ✅
    -   [x] Probar conexión WebSocket desde el dashboard web
    -   [x] Validar envío y recepción de mensajes
    -   [x] Verificar que el estado se actualiza correctamente en la UI

### Estado Actual del MVP
- ✅ Backend ejecutándose en `http://localhost:8765`
- ✅ WebSocket funcional en `ws://localhost:8765/ws`
- ✅ Dashboard web conectado y funcionando
- ✅ Comunicación bidireccional establecida
- ✅ Endpoints de simulación para testing (`/simulate/command`, `/simulate/status`)
- ✅ Health check endpoint (`/health`)

## Fase 2: Integración con Servicios Wake-Word

Una vez que el backend básico funcione, lo conectaremos con los servicios de wake-word.

-   [ ] **Tarea 5: Análisis de Servicios Existentes**
    -   [ ] Revisar API/protocolo de `wake-word-porcupine-version`
    -   [ ] Decidir cuál usar como principal y cuál como fallback

-   [ ] **Tarea 6: Cliente para Servicios Wake-Word**
    -   [ ] Implementar cliente HTTP/WebSocket para comunicarse con el servicio de wake-word
    -   [ ] Manejar eventos de detección de wake-word
    -   [ ] Manejar cambios de estado del servicio de wake-word

-   [ ] **Tarea 7: Lógica de Estado del Asistente**
    -   [ ] Implementar máquina de estados (`idle` → `listening` → `processing` → `idle`)
    -   [ ] Manejar activación manual desde el dashboard
    -   [ ] Manejar activación automática por wake-word
    -   [ ] Propagar cambios de estado al dashboard web

## Fase 3: Funcionalidades Avanzadas

-   [ ] **Tarea 8: Procesamiento de Comandos**
    -   [ ] Integrar con servicios de STT (Speech-to-Text)
    -   [ ] Integrar con servicios de NLU (Natural Language Understanding)
    -   [ ] Registrar comandos procesados y enviarlos al dashboard

-   [ ] **Tarea 9: Configuración y Administración**
    -   [ ] Endpoint REST para configuración del backend
    -   [ ] Soporte para cambiar URL de servicios wake-word
    -   [ ] Logging estructurado y métricas

-   [ ] **Tarea 10: Producción y Deployment**
    -   [ ] Optimizar Dockerfile para producción
    -   [ ] Documentación de despliegue
    -   [ ] Health checks y monitoring
    -   [ ] Integración con docker-compose del proyecto principal

## Arquitectura Propuesta

```
Dashboard Web (Svelte) ←→ WebSocket ←→ Backend API (FastAPI)
                                            ↓
                                    Wake-Word Service
                                            ↓
                                    STT/NLU Services
```

## Tecnologías

- **Framework**: FastAPI (Python)
- **WebSockets**: nativo de FastAPI
- **Containerización**: Docker + docker-compose
- **Testing**: pytest
- **Logging**: structlog o loguru
