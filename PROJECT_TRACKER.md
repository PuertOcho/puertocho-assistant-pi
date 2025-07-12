# PROJECT TRACKER - PuertoCho Assistant Ecosystem

## Arquitectura del Ecosistema (Visión v2)

El sistema se rediseña para que el Backend API actúe como un **Gateway y Orquestador Central**. El servicio de Hardware se comunica exclusivamente con el Backend.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                PuertoCho Assistant                                     │
│                                                                                        │
│  ┌────────────────────┐      ┌──────────────────┐      ┌────────────────────────────┐  │
│  │  Hardware Service  │─────►│   Backend API    │◄────►│       Web Dashboard        │  │
│  │ (Raspberry Pi)     │ HTTP │    (Gateway)     │ WebSocket │         (Svelte)         │  │
│  └────────────────────┘      ├──────────────────┤      └────────────────────────────┘  │
│                              │ - Orquestación   │                                        │
│                              │ - Gestión Estado │      ┌────────────────────────────┐  │
│                              │ - API Gateway    │─────►│     Servicios Externos     │  │
│                              └──────────────────┘      │  - STT, NLU, Chat, etc.    │  │
│                                                        └────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## FASE 1: FUNDACIÓN ✅ COMPLETADA

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

## FASE 2: RE-ARQUITECTURA Y ORQUESTACIÓN 🟡 EN PROGRESO

*Objetivo: Implementar el patrón API Gateway y centralizar la lógica en el backend.*

### 2.1 Backend como Gateway
- [ ] **Tarea 2.1.1**: Crear un endpoint REST en el backend (`POST /api/v1/audio/process`) que acepte un archivo de audio.
- [ ] **Tarea 2.1.2**: Implementar la lógica de orquestación en el backend:
  - [ ] Recibir audio del servicio de hardware.
  - [ ] Actualizar y transmitir estado a `processing` vía WebSocket.
  - [ ] Llamar a servicios externos (STT/NLU) con el audio/texto.
  - [ ] Recibir la respuesta final y registrar el comando.
  - [ ] Actualizar y transmitir estado a `idle` vía WebSocket.
- [ ] **Tarea 2.1.3**: Crear un endpoint (`POST /api/v1/hardware/status`) para que el servicio de hardware informe su estado (ej. micrófono OK, GPIO conectado).

### 2.2 Simplificación del Servicio de Hardware
- [ ] **Tarea 2.2.1**: Renombrar `wake-word-porcupine-version` a `puertocho-assistant-hardware`.
- [ ] **Tarea 2.2.2**: Refactorizar el servicio de hardware para eliminar toda la lógica de llamadas a servicios externos (STT/NLU).
- [ ] **Tarea 2.2.3**: Implementar un cliente HTTP para que, tras grabar el audio, lo envíe únicamente al endpoint `/api/v1/audio/process` del backend.
- [ ] **Tarea 2.2.4**: Implementar el envío periódico o por eventos del estado del hardware al endpoint `/api/v1/hardware/status` del backend.

---

## FASE 3: EXPERIENCIA DE USUARIO AVANZADA 🔴 PENDIENTE

*Objetivo: Mejorar radicalmente la interfaz de usuario y la inteligencia conversacional.*

### 3.1 Overhaul de la Interfaz (Web Dashboard)
- [ ] **Tarea 3.1.1**: Implementar navegación por pestañas (Home, Configuración, etc.).
- [ ] **Tarea 3.1.2**: Crear componente "Asistente Virtual" que muestre visualmente los estados (callado, escuchando, hablando, procesando).
- [ ] **Tarea 3.1.3**: Crear tarjeta "Skills/MCPs" con iconos para activar/desactivar módulos de backend.
- [ ] **Tarea 3.1.4**: Crear tarjeta "Dispositivo Objetivo" para seleccionar dónde se ejecutan las acciones.
- [ ] **Tarea 3.1.5**: Crear tarjeta "Contexto" que muestre información relevante que el asistente está usando (localización, etc.).
- [ ] **Tarea 3.1.6**: Integrar la visualización del estado del hardware recibido desde el backend.

### 3.2 Inteligencia Conversacional
- [ ] **Tarea 3.2.1**: Diseñar una máquina de estados de diálogo en el backend.
- [ ] **Tarea 3.2.2**: Integrar con un servicio NLU para detectar "intents" y "entities".
- [ ] **Tarea 3.2.3**: Implementar la lógica de "slot-filling": si un comando requiere un parámetro que no fue proporcionado, el asistente debe preguntar por él.
- [ ] **Tarea 3.2.4**: Implementar la capacidad del backend para generar respuestas de voz (TTS) y enviarlas al servicio de hardware para su reproducción.

---

## FASE 4: INTEGRACIÓN FÍSICA Y PRODUCCIÓN 🔴 PENDIENTE

*Objetivo: Asegurar que el sistema funcione de manera robusta en el hardware final.*

### 4.1 Despliegue en Raspberry Pi
- [ ] **Tarea 4.1.1**: Validar el funcionamiento de todos los servicios en la arquitectura ARM de la Raspberry Pi.
- [ ] **Tarea 4.1.2**: Probar y optimizar la interacción con el hardware real (micrófono, LEDs, botón).
- [ ] **Tarea 4.1.3**: Crear scripts de despliegue y configuración específicos para la Raspberry Pi.

### 4.2 Optimización y Monitorización
- [ ] **Tarea 4.2.1**: Medir y optimizar el consumo de CPU y memoria en la Raspberry Pi.
- [ ] **Tarea 4.2.2**: Implementar un sistema de logging y monitorización centralizado para el entorno de producción.
- [ ] **Tarea 4.2.3**: Realizar pruebas de estrés y de largo plazo para asegurar la estabilidad.
