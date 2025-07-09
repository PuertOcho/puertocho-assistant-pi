# PuertoCho Assistant - Web Dashboard

Dashboard web para el asistente de voz PuertoCho, desarrollado con Svelte y optimizado para Raspberry Pi.

## Características

- 🎛️ Dashboard en tiempo real del estado del asistente
- 📱 Interfaz responsive para móvil y escritorio  
- 🔌 Conexión WebSocket para actualizaciones en tiempo real
- 🐳 Completamente dockerizado para fácil despliegue
- ⚡ Optimizado para Raspberry Pi con arquitectura ARM

## Desarrollo Local

### Requisitos previos
- Node.js 18+ 
- npm o yarn
- Docker (opcional pero recomendado)

### Instalación
```bash
# Instalar dependencias
npm install

# Ejecutar en modo desarrollo
npm run dev:host

# Acceder a http://localhost:3000
```

### Scripts disponibles
```bash
npm run dev          # Servidor de desarrollo local
npm run dev:host     # Servidor de desarrollo accesible desde la red
npm run build        # Construir para producción
npm run preview      # Previsualizar build de producción
npm run check        # Verificación de tipos TypeScript
```

## Despliegue con Docker

### Desarrollo
```bash
# Construir y ejecutar en modo desarrollo
docker-compose up puertocho-web-dev
```

### Producción
```bash
# Construir y ejecutar en modo producción
docker-compose up puertocho-web-dashboard -d
```

### Comandos Docker individuales
```bash
# Construir imagen
npm run docker:build

# Ejecutar contenedor
npm run docker:run
```

## Configuración

Las siguientes variables de entorno pueden configurarse:

- `VITE_BACKEND_URL`: URL del backend del asistente (default: http://localhost:8000)
- `VITE_WEBSOCKET_URL`: URL del WebSocket (default: ws://localhost:8000/ws)

## Arquitectura

```
┌─────────────────────────────────────────┐
│           Raspberry Pi                  │
│                                         │
│  ┌─────────────────┐ ┌─────────────────┐│
│  │   Backend       │ │   Frontend      ││
│  │   Python        │ │   Svelte        ││
│  │   + FastAPI     │ │   + nginx       ││
│  │   Puerto: 8000  │ │   Puerto: 3000  ││
│  └─────────────────┘ └─────────────────┘│
│           │                   │          │
│           └───── WebSocket ───┘          │
└─────────────────────────────────────────┘
```

## Estructura del Proyecto

```
src/
├── lib/           # Componentes reutilizables
├── routes/        # Páginas de la aplicación
└── app.html       # Template HTML principal

static/            # Archivos estáticos
docker-compose.yml # Configuración Docker
Dockerfile         # Imagen Docker para producción
nginx.conf         # Configuración del servidor web
```

## Estado del Desarrollo

Ver `PROJECT_TRACKER.md` para el estado actual de las tareas y roadmap del proyecto.
