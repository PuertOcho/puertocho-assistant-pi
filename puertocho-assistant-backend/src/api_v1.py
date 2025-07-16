from fastapi import APIRouter, UploadFile, File, Body
from fastapi.responses import JSONResponse
import asyncio

from .state_manager import state_manager
from .websocket_manager import websocket_manager

router = APIRouter()

@router.post("/audio/process")
async def process_audio(audio: UploadFile = File(...)):
    """
    Recibe un archivo de audio, simula su procesamiento y notifica
    a los clientes WebSocket sobre los cambios de estado.
    """
    # 1. Notificar que estamos procesando
    await state_manager.set_assistant_status("processing")
    
    # Simulación de la llamada a un servicio STT/NLU
    print("Procesando audio recibido...")
    await asyncio.sleep(2)  # Simular tiempo de procesamiento
    
    # 2. Simular resultado y registrarlo
    command_text = "Comando simulado desde audio"
    await websocket_manager.broadcast_command(command_text)
    print(f"Comando simulado: '{command_text}'")
    
    # 3. Volver al estado idle
    await state_manager.set_assistant_status("idle")
    
    return JSONResponse(
        content={"status": "success", "transcription": command_text},
        status_code=200
    )

@router.post("/hardware/status")
async def update_hardware_status(status: dict = Body(...)):
    """
    Recibe y actualiza el estado del hardware y lo notifica
    a los clientes WebSocket.
    """
    await state_manager.set_hardware_status(status)
    return JSONResponse(content={"status": "received"}, status_code=200)
