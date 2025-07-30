"""
Gateway API Endpoints for PuertoCho Assistant Backend
====================================================

Endpoints que actúan como gateway entre frontend, hardware y backend remoto.
Reemplaza el api_v1.py anterior con nueva funcionalidad gateway.
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from datetime import datetime

from core.state_manager import get_state_manager, BackendState
from services.audio_processor import get_audio_processor
from clients.hardware_client import get_hardware_client


# Router para endpoints de gateway
router = APIRouter()
logger = logging.getLogger("gateway_api")


# ===============================================
# ENDPOINTS PARA RECIBIR DATOS DEL HARDWARE
# ===============================================

@router.post("/hardware/audio")
async def receive_audio_from_hardware(audio: UploadFile = File(...)):
    """
    Recibe archivo de audio enviado desde el hardware.
    
    El hardware puede enviar audio aquí directamente o podemos
    obtenerlo de su API. Este endpoint es para compatibilidad futura.
    """
    try:
        logger.info(f"📥 Received audio from hardware: {audio.filename}")
        
        # Leer contenido del archivo
        audio_content = await audio.read()
        
        # Crear información del audio
        audio_info = {
            "filename": audio.filename,
            "size_bytes": len(audio_content),
            "content_type": audio.content_type,
            "received_at": datetime.now().isoformat()
        }
        
        # Procesar con AudioProcessor
        audio_processor = get_audio_processor()
        result = await audio_processor.process_audio_from_hardware(audio_info)
        
        # Actualizar estado del backend
        state_manager = get_state_manager()
        await state_manager.set_backend_state(BackendState.PROCESSING_AUDIO)
        
        return JSONResponse(
            content={
                "status": "success",
                "message": "Audio received and queued for processing",
                "audio_info": audio_info,
                "processing_result": result
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to receive audio from hardware: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process audio: {str(e)}"
        )


@router.post("/hardware/status")
async def receive_hardware_status(status: Dict[str, Any] = Body(...)):
    """
    Recibe actualizaciones de estado del hardware.
    
    En la nueva arquitectura, obtenemos el estado directamente
    del hardware, pero este endpoint permite push notifications.
    """
    try:
        logger.info(f"📡 Hardware status update received: {status}")
        
        # Procesar evento de hardware
        state_manager = get_state_manager()
        await state_manager.handle_hardware_event({
            "type": "status_update",
            "status": status,
            "received_at": datetime.now().isoformat()
        })
        
        return JSONResponse(
            content={
                "status": "received",
                "message": "Hardware status updated"
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to process hardware status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process hardware status: {str(e)}"
        )


@router.post("/hardware/events")
async def receive_hardware_event(event: Dict[str, Any] = Body(...)):
    """
    Recibe eventos del hardware (botón, audio capturado, etc.).
    """
    try:
        event_type = event.get("type", "unknown")
        logger.info(f"📡 Hardware event received: {event_type}")
        
        # Agregar timestamp si no existe
        if "timestamp" not in event:
            event["timestamp"] = datetime.now().isoformat()
        
        # Procesar evento
        state_manager = get_state_manager()
        await state_manager.handle_hardware_event(event)
        
        return JSONResponse(
            content={
                "status": "processed",
                "event_type": event_type,
                "message": "Hardware event processed"
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to process hardware event: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process hardware event: {str(e)}"
        )


# ===============================================
# ENDPOINTS PARA COMUNICACIÓN CON FRONTEND
# ===============================================

@router.get("/state")
async def get_unified_state():
    """
    Obtener estado unificado del sistema completo.
    
    Combina estado del hardware, backend local y remoto.
    """
    try:
        state_manager = get_state_manager()
        unified_state = state_manager.get_unified_state()
        
        return JSONResponse(
            content={
                "status": "success",
                "state": unified_state
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get unified state: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system state: {str(e)}"
        )


@router.post("/control/hardware")
async def send_command_to_hardware(command: Dict[str, Any] = Body(...)):
    """
    Enviar comando al hardware desde el frontend.
    
    Tipos de comandos soportados:
    - led_pattern: Cambiar patrón de LED
    - state_change: Cambiar estado del hardware
    - button_simulate: Simular pulsación de botón
    """
    try:
        command_type = command.get("type")
        if not command_type:
            raise HTTPException(
                status_code=400,
                detail="Command type is required"
            )
        
        logger.info(f"🎮 Sending command to hardware: {command_type}")
        
        # Enviar comando al hardware
        state_manager = get_state_manager()
        result = await state_manager.send_command_to_hardware(command)
        
        return JSONResponse(
            content={
                "status": "success",
                "command_type": command_type,
                "result": result,
                "message": "Command sent to hardware"
            },
            status_code=200
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to send command to hardware: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send command: {str(e)}"
        )


@router.get("/history")
async def get_interaction_history():
    """
    Obtener historial de interacciones.
    
    TODO: Implementar almacenamiento de historial
    """
    try:
        # Por ahora retornamos información de la cola de audio
        audio_processor = get_audio_processor()
        queue_status = audio_processor.get_queue_status()
        
        return JSONResponse(
            content={
                "status": "success",
                "history": {
                    "audio_queue": queue_status,
                    "note": "Full history implementation pending"
                }
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get history: {str(e)}"
        )


@router.get("/metrics")
async def get_system_metrics():
    """
    Obtener métricas del sistema completo.
    
    Combina métricas del hardware, backend local y remoto.
    """
    try:
        state_manager = get_state_manager()
        audio_processor = get_audio_processor()
        
        # Obtener métricas del hardware
        try:
            hardware_metrics = await state_manager.get_hardware_metrics()
        except Exception as e:
            hardware_metrics = {"error": str(e), "available": False}
        
        # Métricas del backend local
        backend_metrics = {
            "backend_state": state_manager.backend_state.value,
            "last_hardware_sync": state_manager.last_hardware_sync,
            "hardware_connected": state_manager.backend_state not in [
                BackendState.CONNECTING_HARDWARE,
                BackendState.HARDWARE_DISCONNECTED
            ]
        }
        
        # Métricas del procesador de audio
        audio_metrics = audio_processor.get_queue_status()
        
        unified_metrics = {
            "timestamp": datetime.now().isoformat(),
            "hardware": hardware_metrics,
            "backend": backend_metrics,
            "audio_processing": audio_metrics
        }
        
        return JSONResponse(
            content={
                "status": "success",
                "metrics": unified_metrics
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metrics: {str(e)}"
        )


# ===============================================
# ENDPOINTS DE CONFIGURACIÓN
# ===============================================

@router.get("/hardware/config")
async def get_hardware_config():
    """
    Obtener configuración que el hardware debe usar.
    
    TODO: Implementar sistema de configuración
    """
    try:
        # Configuración básica por ahora
        config = {
            "backend_url": "http://backend:8000",
            "sync_interval": 30,
            "audio_auto_send": True,
            "log_level": "INFO"
        }
        
        return JSONResponse(
            content={
                "status": "success",
                "config": config
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get hardware config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get hardware config: {str(e)}"
        )


@router.post("/config/update")
async def update_system_config(config: Dict[str, Any] = Body(...)):
    """
    Actualizar configuración del sistema.
    
    TODO: Implementar gestión de configuración
    """
    try:
        logger.info(f"⚙️ Configuration update requested: {config}")
        
        # Por ahora solo logeamos la configuración
        # En el futuro se implementará persistencia y aplicación
        
        return JSONResponse(
            content={
                "status": "success",
                "message": "Configuration update received (implementation pending)",
                "config": config
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to update config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update config: {str(e)}"
        )


# ===============================================
# ENDPOINTS DE COMPATIBILIDAD (CÓDIGO ANTERIOR)
# ===============================================

@router.post("/audio/process")
async def process_audio_legacy(audio: UploadFile = File(...)):
    """
    Compatibilidad con código anterior.
    Redirige al nuevo endpoint de audio del hardware.
    """
    logger.info("📎 Legacy audio processing endpoint called, redirecting...")
    return await receive_audio_from_hardware(audio)
