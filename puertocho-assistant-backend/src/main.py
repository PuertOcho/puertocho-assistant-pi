"""
PuertoCho Assistant Backend Gateway
==================================

Backend Gateway que actúa como intermediario entre el hardware funcional,
el frontend web y los servicios remotos de procesamiento.

Nueva arquitectura:
- Cliente HTTP del hardware (puerto 8080)
- Servidor WebSocket para frontend en tiempo real
- Buffer de audio para backend remoto
- StateManager que replica estado del hardware
"""

import asyncio
import os
import logging
import signal
import sys
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Imports locales
from middleware.logging import LoggingMiddleware, setup_logging
from core.websocket_manager import websocket_manager
from core.state_manager import init_state_manager, close_state_manager, get_state_manager
from clients.hardware_client import init_hardware_client, close_hardware_client, get_hardware_client
from clients.remote_backend_client import init_remote_client, close_remote_client
from services.audio_processor import init_audio_processor, close_audio_processor, get_audio_processor
from api.gateway_endpoints import router as gateway_router


# Configurar logging
backend_logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestionar ciclo de vida de la aplicación.
    Inicializa y limpia recursos al iniciar/cerrar.
    """
    backend_logger.info("🚀 Starting PuertoCho Backend Gateway...")
    
    try:
        # 1. Inicializar cliente hardware
        backend_logger.info("🔌 Initializing hardware client...")
        hardware_base_url = os.getenv("HARDWARE_BASE_URL", "http://localhost:8080")
        hardware_client = init_hardware_client(hardware_base_url)
        
        # Esperar a que el hardware esté disponible
        backend_logger.info(f"⏳ Waiting for hardware to be available at {hardware_base_url}...")
        if await hardware_client.wait_for_hardware(max_wait_time=60.0):
            backend_logger.info("✅ Hardware is available!")
        else:
            backend_logger.warning("⚠️ Hardware not available, continuing anyway...")
        
        # 2. Inicializar state manager
        backend_logger.info("📊 Initializing state manager...")
        state_manager = init_state_manager(websocket_manager)
        await state_manager.start()
        
        # 3. Inicializar cliente remoto (Epic 4)
        backend_logger.info("🌐 Initializing remote backend client...")
        try:
            remote_client = await init_remote_client()
            backend_logger.info("✅ Remote backend client initialized!")
        except Exception as e:
            backend_logger.warning(f"⚠️ Remote backend client failed to initialize: {e}")
            backend_logger.warning("Continuing without remote backend connectivity...")
        
        # 4. Inicializar audio processor (Epic 4)
        backend_logger.info("🎙️ Initializing audio processor...")
        audio_processor = init_audio_processor(websocket_manager)
        await audio_processor.start()
        backend_logger.info("🎙️ Audio processor configured for remote backend processing")
        
        backend_logger.info("✅ Backend Gateway startup complete!")
        
        yield  # Aplicación ejecutándose
        
    except Exception as e:
        backend_logger.error(f"❌ Failed to start backend gateway: {e}")
        sys.exit(1)
    
    finally:
        # Cleanup al cerrar
        backend_logger.info("🛑 Shutting down Backend Gateway...")
        
        try:
            await close_audio_processor()
            await close_remote_client()
            await close_state_manager()
            await close_hardware_client()
            backend_logger.info("✅ Backend Gateway shutdown complete")
        except Exception as e:
            backend_logger.error(f"❌ Error during shutdown: {e}")


# Crear aplicación FastAPI
app = FastAPI(
    title="PuertoCho Backend Gateway",
    description="Gateway entre hardware, frontend y backend remoto",
    version="2.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar middleware de logging
app.add_middleware(LoggingMiddleware)

# Incluir rutas de la API
app.include_router(gateway_router, prefix="/api/v1")


# ===============================================
# ENDPOINTS BÁSICOS
# ===============================================

@app.get("/")
def read_root():
    """Endpoint raíz con información del servicio"""
    return {
        "service": "PuertoCho Backend Gateway",
        "version": "2.0.0",
        "status": "online",
        "description": "Gateway entre hardware, frontend y backend remoto"
    }


@app.get("/health")
async def health_check():
    """Health check completo del sistema"""
    try:
        # Verificar estado del hardware
        hardware_error = None  # Inicializar variable para evitar UnboundLocalError
        try:
            hardware_client = get_hardware_client()
            hardware_health = await hardware_client.get_health()
            hardware_available = hardware_health.get("status") == "healthy"
        except Exception as e:
            hardware_available = False
            hardware_error = str(e)
        
        # Verificar estado del state manager
        try:
            state_manager = get_state_manager()
            backend_state = state_manager.backend_state.value
            state_manager_ok = True
        except Exception as e:
            backend_state = "error"
            state_manager_ok = False
        
        # Estado general
        overall_status = "ok" if hardware_available and state_manager_ok else "degraded"
        
        health_info = {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "hardware": {
                    "available": hardware_available,
                    "status": "ok" if hardware_available else "error"
                },
                "state_manager": {
                    "available": state_manager_ok,
                    "current_state": backend_state
                },
                "websocket": {
                    "active_connections": websocket_manager.get_connection_count()
                }
            }
        }
        
        if not hardware_available and hardware_error:
            health_info["components"]["hardware"]["error"] = hardware_error
        
        return health_info
        
    except Exception as e:
        backend_logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# ===============================================
# WEBSOCKET PARA FRONTEND
# ===============================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Endpoint WebSocket para comunicación en tiempo real con frontend.
    """
    connection_id = await websocket_manager.connect(websocket)
    
    try:
        # Enviar estado inicial al cliente recién conectado
        try:
            state_manager = get_state_manager()
            unified_state = state_manager.get_unified_state()
            
            await websocket.send_json({
                "type": "initial_state",
                "payload": unified_state
            })
            
            # Enviar información de conexión
            await websocket.send_json({
                "type": "connection_info",
                "payload": {
                    "connection_id": connection_id,
                    "message": "Connected to PuertoCho Backend Gateway"
                }
            })
            
        except Exception as e:
            backend_logger.error(f"❌ Error sending initial state: {e}")
        
        # Loop principal del WebSocket
        while True:
            try:
                # Recibir mensajes del cliente
                data = await websocket.receive_json()
                message_type = data.get("type", "unknown")
                
                backend_logger.info(f"📡 WebSocket message from {connection_id}: {message_type}")
                
                # Procesar diferentes tipos de mensajes
                if message_type == "manual_activation":
                    await handle_manual_activation(data)
                elif message_type == "hardware_command":
                    await handle_hardware_command(data)
                elif message_type == "get_state":
                    await handle_get_state_request(websocket, connection_id)
                elif message_type == "audio_captured":
                    await handle_audio_captured(data)
                elif message_type == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": data.get("timestamp")})
                else:
                    backend_logger.warning(f"⚠️ Unknown WebSocket message type: {message_type}")
                    
            except WebSocketDisconnect:
                backend_logger.info(f"🔌 WebSocket client {connection_id} disconnected normally")
                break
            except Exception as e:
                backend_logger.error(f"❌ Error in WebSocket {connection_id}: {e}")
                break
    
    except WebSocketDisconnect:
        backend_logger.info(f"🔌 WebSocket client {connection_id} disconnected")
    except Exception as e:
        backend_logger.error(f"❌ WebSocket error for {connection_id}: {e}")
    finally:
        websocket_manager.disconnect(websocket)


async def handle_manual_activation(data: dict):
    """Manejar activación manual desde el frontend"""
    try:
        backend_logger.info("🎮 Manual activation triggered from frontend")
        
        state_manager = get_state_manager()
        
        # Enviar comando al hardware para cambiar a estado listening
        command = {
            "type": "state_change",
            "state": "LISTENING"
        }
        
        result = await state_manager.send_command_to_hardware(command)
        backend_logger.info(f"✅ Manual activation sent to hardware: {result}")
        
    except Exception as e:
        backend_logger.error(f"❌ Failed to handle manual activation: {e}")


async def handle_hardware_command(data: dict):
    """Manejar comando hacia hardware desde frontend"""
    try:
        command_type = data.get("command_type")
        hardware_client = get_hardware_client()
        
        backend_logger.info(f"🎮 Hardware command from frontend: {command_type}")
        
        if command_type == "set_led_pattern":
            # Usar la API HTTP del hardware directamente
            pattern = data.get("pattern", "idle")
            response = await hardware_client.post("/led/pattern", json={
                "pattern_type": pattern,
                "color": data.get("color"),
                "brightness": data.get("brightness")
            })
            
        elif command_type == "activate_listening":
            # Cambiar estado a LISTENING vía HTTP
            response = await hardware_client.post("/state", json={"state": "LISTENING"})
            
        elif command_type == "simulate_button":
            # Simular evento de botón
            response = await hardware_client.post("/button/simulate", json={
                "event_type": data.get("button_type", "short"),
                "duration": data.get("duration")
            })
            
        else:
            backend_logger.warning(f"Unknown command type: {command_type}")
            response = {"success": False, "error": "Unknown command type"}
        
        # Notificar resultado al frontend
        await websocket_manager.broadcast({
            "type": "hardware_command_result",
            "payload": {
                "command_type": command_type,
                "success": response.get("success", False),
                "result": response
            }
        })
        
    except Exception as e:
        backend_logger.error(f"❌ Error handling hardware command: {e}")
        await websocket_manager.broadcast_error(str(e))


async def handle_get_state_request(websocket: WebSocket, connection_id: str):
    """Manejar solicitud de estado actual"""
    try:
        state_manager = get_state_manager()
        unified_state = state_manager.get_unified_state()
        
        await websocket.send_json({
            "type": "current_state",
            "payload": unified_state
        })
        
    except Exception as e:
        backend_logger.error(f"❌ Failed to send state to {connection_id}: {e}")


async def handle_audio_captured(data: dict):
    """Manejar audio capturado desde hardware"""
    try:
        backend_logger.info("🎙️ Audio captured event received from hardware")
        
        # Obtener el AudioProcessor
        audio_processor = get_audio_processor()
        
        # Procesar el audio desde hardware
        result = await audio_processor.process_audio_from_hardware(data)
        
        backend_logger.info(f"✅ Audio processing initiated: {result}")
        
    except Exception as e:
        backend_logger.error(f"❌ Failed to handle audio captured: {e}")


# ===============================================
# GESTIÓN DE SEÑALES PARA SHUTDOWN GRACEFUL
# ===============================================

def signal_handler(signum, frame):
    """Manejar señales de shutdown"""
    signal_name = signal.Signals(signum).name
    backend_logger.info(f"🛑 Received {signal_name}, shutting down gracefully...")
    
    # FastAPI con lifespan se encarga del cleanup automáticamente
    sys.exit(0)


# Registrar manejadores de señales
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ===============================================
# FUNCIÓN PRINCIPAL
# ===============================================

def start():
    """
    Función principal para iniciar el servidor.
    """
    backend_logger.info("🚀 Starting PuertoCho Backend Gateway Server...")
    
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disabled para producción
            log_level="info",
            access_log=False  # Usamos nuestro middleware de logging
        )
    except Exception as e:
        backend_logger.error(f"❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    start()
