"""
PuertoCho Assistant Backend API
==============================

Backend API que actúa como intermediario entre el dashboard web
y los servicios de wake-word del asistente PuertoCho.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.core.state_manager import state_manager
from src.core.websocket_manager import websocket_manager
from src.api_v1 import router as api_v1_router

# Inyectar el websocket_manager en el state_manager
state_manager.set_websocket_manager(websocket_manager)

app = FastAPI(
    title="PuertoCho Assistant Backend",
    description="Servidor central que actúa como Gateway y Orquestador.",
    version="2.0.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir las rutas de la API v1
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"service": "PuertoCho Backend", "status": "online"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        # Enviar estado inicial al cliente recién conectado
        await websocket.send_json({
            "type": "status_update",
            "payload": {"status": state_manager.get_assistant_status()}
        })
        await websocket.send_json({
            "type": "hardware_status_update",
            "payload": state_manager.get_hardware_status()
        })
        
        while True:
            # El backend principalmente emite, pero puede recibir mensajes
            # para acciones como la activación manual.
            data = await websocket.receive_json()
            if data.get("type") == "manual_activation":
                print("Activación manual recibida desde el cliente.")
                # Aquí se podría simular el flujo que iniciaría el hardware
                await state_manager.set_assistant_status("listening")
                # Simular fin de escucha tras un tiempo
                import asyncio
                await asyncio.sleep(3)
                await state_manager.set_assistant_status("idle")

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        print(f"Error en WebSocket: {e}")
        websocket_manager.disconnect(websocket)

def start():
    """Inicia el servidor FastAPI."""
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
