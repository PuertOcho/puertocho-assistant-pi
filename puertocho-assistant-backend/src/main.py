"""
PuertoCho Assistant Backend API
==============================

Backend API que actúa como intermediario entre el dashboard web
y los servicios de wake-word del asistente PuertoCho.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
import asyncio
from typing import Set
import structlog
import io
from pathlib import Path

# Configurar logging estructurado
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Crear aplicación FastAPI
app = FastAPI(
    title="PuertoCho Assistant Backend",
    description="Backend API para el dashboard web del asistente PuertoCho",
    version="1.0.0"
)

# Configurar CORS para permitir conexiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manager para conexiones WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("Cliente WebSocket conectado", 
                   client_count=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info("Cliente WebSocket desconectado", 
                   client_count=len(self.active_connections))

    async def broadcast(self, message: dict):
        """Enviar mensaje a todos los clientes conectados"""
        if self.active_connections:
            message_str = json.dumps(message)
            disconnected = set()
            
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_str)
                except Exception as e:
                    logger.warning("Error enviando mensaje a cliente", error=str(e))
                    disconnected.add(connection)
            
            # Remover conexiones muertas
            for connection in disconnected:
                self.disconnect(connection)

manager = ConnectionManager()

# Estado del asistente
class AssistantState:
    def __init__(self):
        self.status = "idle"  # idle, listening, processing, error
        self.commands = []

    async def set_status(self, new_status: str):
        if self.status != new_status:
            self.status = new_status
            logger.info("Estado del asistente cambiado", status=new_status)
            await manager.broadcast({
                "type": "status_update",
                "payload": {"status": new_status}
            })

    async def add_command(self, command: str):
        import time
        command_entry = {
            "command": command,
            "timestamp": int(time.time() * 1000)  # Timestamp en milisegundos
        }
        self.commands.append(command_entry)
        logger.info("Comando registrado", command=command)
        await manager.broadcast({
            "type": "command_log",
            "payload": command_entry
        })

assistant_state = AssistantState()

@app.get("/")
async def root():
    """Endpoint de salud básico"""
    return {
        "message": "PuertoCho Assistant Backend API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "connections": len(manager.active_connections),
        "assistant_status": assistant_state.status
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint principal de WebSocket"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Recibir mensaje del cliente
            data = await websocket.receive_text()
            message = json.loads(data)
            
            logger.info("Mensaje recibido", message=message)
            
            # Manejar diferentes tipos de mensajes
            if message.get("type") == "manual_activation":
                logger.info("Activación manual solicitada")
                await handle_manual_activation()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("Error en WebSocket", error=str(e))
        manager.disconnect(websocket)

async def handle_manual_activation():
    """Manejar activación manual del asistente"""
    logger.info("Procesando activación manual")
    
    # Simular el flujo del asistente
    await assistant_state.set_status("listening")
    await asyncio.sleep(2)  # Simular tiempo de escucha
    
    await assistant_state.set_status("processing")
    await asyncio.sleep(1)  # Simular procesamiento
    
    # Simular comando reconocido
    await assistant_state.add_command("Activación manual desde dashboard")
    
    await assistant_state.set_status("idle")

# Endpoint para simular comandos (útil para testing)
@app.post("/simulate/command")
async def simulate_command(command: str):
    """Simular un comando para testing"""
    await assistant_state.add_command(command)
    return {"message": f"Comando simulado: {command}"}

@app.post("/simulate/status")
async def simulate_status(status: str):
    """Simular cambio de estado para testing"""
    await assistant_state.set_status(status)
    return {"message": f"Estado cambiado a: {status}"}

# Nuevos endpoints para la arquitectura Gateway
@app.post("/api/v1/audio/process")
async def process_audio(audio: UploadFile = File(...)):
    """
    Procesar audio recibido del servicio de hardware.
    Este endpoint actúa como orquestador central para el procesamiento de comandos de voz.
    """
    try:
        logger.info("Procesando audio recibido", filename=audio.filename, content_type=audio.content_type)
        
        # Validar que el archivo es de audio
        if not audio.content_type or not audio.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="El archivo debe ser de audio")
        
        # Cambiar estado a processing
        await assistant_state.set_status("processing")
        
        # Leer el contenido del archivo
        audio_content = await audio.read()
        audio_size = len(audio_content)
        
        logger.info("Audio recibido", size_bytes=audio_size)
        
        # TODO: Aquí irá la lógica de orquestación:
        # 1. Llamar al servicio de transcripción (STT)
        # 2. Llamar al servicio de NLU/Chat
        # 3. Procesar la respuesta
        
        # Por ahora, simulamos el procesamiento
        await asyncio.sleep(1)
        
        # Simular un comando procesado
        command_text = f"Comando de audio procesado ({audio_size} bytes)"
        await assistant_state.add_command(command_text)
        
        # Volver al estado idle
        await assistant_state.set_status("idle")
        
        return {
            "success": True,
            "message": "Audio procesado exitosamente",
            "audio_size": audio_size,
            "command": command_text
        }
        
    except Exception as e:
        logger.error("Error procesando audio", error=str(e))
        await assistant_state.set_status("error")
        raise HTTPException(status_code=500, detail=f"Error procesando audio: {str(e)}")

@app.post("/api/v1/hardware/status")
async def update_hardware_status(status_data: dict):
    """
    Recibir actualizaciones de estado del servicio de hardware.
    """
    try:
        logger.info("Estado del hardware recibido", status_data=status_data)
        
        # TODO: Almacenar y procesar el estado del hardware
        # Por ahora, simplemente lo registramos
        
        # Broadcast del estado del hardware a los clientes conectados
        await manager.broadcast({
            "type": "hardware_status",
            "payload": status_data
        })
        
        return {
            "success": True,
            "message": "Estado del hardware actualizado"
        }
        
    except Exception as e:
        logger.error("Error actualizando estado del hardware", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error actualizando estado del hardware: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="info")
