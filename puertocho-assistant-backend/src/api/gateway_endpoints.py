"""
Gateway API Endpoints for PuertoCho Assistant Backend
====================================================

Endpoints que actúan como gateway entre frontend, hardware y backend remoto.
Reemplaza el api_v1.py anterior con nueva funcionalidad gateway.
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
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
    reception_timestamp = datetime.now()
    processing_start = None
    
    try:
        # Logging detallado de recepción
        logger.info(f"📥 Audio reception started from hardware")
        logger.info(f"📄 Filename: {audio.filename}")
        logger.info(f"📅 Reception timestamp: {reception_timestamp.isoformat()}")
        
        # Leer contenido del archivo
        audio_content = await audio.read()
        
        # Validar que realmente sea un archivo de audio
        if not audio.content_type or not audio.content_type.startswith('audio/'):
            logger.warning(f"⚠️ Unexpected content type: {audio.content_type}")
        
        # Logging de metadatos del archivo
        logger.info(f"📊 Audio file size: {len(audio_content)} bytes ({len(audio_content)/1024:.2f} KB)")
        logger.info(f"🏷️ Content type: {audio.content_type}")
        
        # Validar tamaño del archivo
        if len(audio_content) == 0:
            logger.error("❌ Received empty audio file")
            raise HTTPException(status_code=400, detail="Empty audio file received")
        
        # Estimar metadatos básicos del audio (asumiendo WAV estándar)
        audio_metrics = _analyze_audio_basic_metrics(audio_content, audio.filename)
        logger.info(f"🎵 Estimated audio metrics: {audio_metrics}")
        
        # Crear información del audio con metadatos extendidos
        audio_info = {
            "filename": audio.filename,
            "size_bytes": len(audio_content),
            "content_type": audio.content_type,
            "received_at": reception_timestamp.isoformat(),
            "reception_endpoint": "/hardware/audio",
            "audio_metrics": audio_metrics
        }
        
        # Marcar inicio de procesamiento
        processing_start = datetime.now()
        logger.info(f"⚡ Starting audio processing at: {processing_start.isoformat()}")
        
        # Procesar con AudioProcessor
        audio_processor = get_audio_processor()
        result = await audio_processor.process_audio_from_hardware(audio_info)
        
        # Calcular tiempo de procesamiento
        processing_end = datetime.now()
        processing_duration = (processing_end - processing_start).total_seconds()
        logger.info(f"⏱️ Audio processing completed in {processing_duration:.3f} seconds")
        
        # Logging del resultado del procesamiento
        if result.get("success"):
            logger.info(f"✅ Audio processing successful - ID: {result.get('audio_id')}")
            logger.info(f"📍 Queue position: {result.get('queue_position')}")
        else:
            logger.error(f"❌ Audio processing failed: {result.get('error')}")
        
        # Actualizar estado del backend
        state_manager = get_state_manager()
        await state_manager.set_backend_state(BackendState.PROCESSING_AUDIO)
        
        # Respuesta con información extendida
        response_data = {
            "status": "success",
            "message": "Audio received and queued for processing",
            "audio_info": audio_info,
            "processing_result": result,
            "timing": {
                "received_at": reception_timestamp.isoformat(),
                "processing_started_at": processing_start.isoformat(),
                "processing_completed_at": processing_end.isoformat(),
                "total_processing_time_seconds": processing_duration
            }
        }
        
        logger.info(f"📤 Sending successful response for audio: {audio.filename}")
        
        return JSONResponse(
            content=response_data,
            status_code=200
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions without logging as errors
        raise
    except Exception as e:
        processing_end = datetime.now() if processing_start else reception_timestamp
        total_time = (processing_end - reception_timestamp).total_seconds()
        
        logger.error(f"❌ Failed to receive audio from hardware: {e}")
        logger.error(f"💥 Error occurred after {total_time:.3f} seconds")
        logger.error(f"📄 Failed file: {audio.filename if audio else 'unknown'}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process audio: {str(e)}"
        )


def _analyze_audio_basic_metrics(audio_content: bytes, filename: str) -> Dict[str, Any]:
    """
    Analiza métricas básicas del audio sin librerías externas.
    
    Para WAV files, podemos extraer información básica del header.
    Incluye validaciones de calidad básicas.
    """
    metrics = {
        "file_extension": filename.split('.')[-1].lower() if '.' in filename else "unknown",
        "size_bytes": len(audio_content),
        "size_kb": len(audio_content) / 1024,
        "estimated_format": "unknown",
        "quality_indicators": {}
    }
    
    try:
        # Para archivos WAV, intentar leer el header básico
        if audio_content.startswith(b'RIFF') and len(audio_content) > 12 and audio_content[8:12] == b'WAVE':
            metrics["estimated_format"] = "wav"
            
            # Validar estructura básica WAV
            quality_issues = []
            
            # Verificar tamaño mínimo del header WAV
            if len(audio_content) < 44:
                quality_issues.append("WAV file too small (incomplete header)")
                metrics["quality_indicators"]["issues"] = quality_issues
                return metrics
            
            try:
                # Extraer información del header WAV
                # Sample rate está en bytes 24-27 (little endian)
                sample_rate = int.from_bytes(audio_content[24:28], byteorder='little')
                # Channels está en bytes 22-23 (little endian)
                channels = int.from_bytes(audio_content[22:24], byteorder='little')
                # Bits per sample está en bytes 34-35 (little endian)
                bits_per_sample = int.from_bytes(audio_content[34:36], byteorder='little')
                # Byte rate está en bytes 28-31 (little endian)
                byte_rate = int.from_bytes(audio_content[28:32], byteorder='little')
                # Block align está en bytes 32-33 (little endian)
                block_align = int.from_bytes(audio_content[32:34], byteorder='little')
                
                # Calcular duración estimada
                data_size = len(audio_content) - 44  # Restar header
                duration_seconds = data_size / byte_rate if byte_rate > 0 else None
                
                metrics.update({
                    "sample_rate_hz": sample_rate,
                    "channels": channels,
                    "bits_per_sample": bits_per_sample,
                    "byte_rate": byte_rate,
                    "block_align": block_align,
                    "data_size_bytes": data_size,
                    "estimated_duration_seconds": duration_seconds
                })
                
                # Validaciones de calidad
                quality_score = 100  # Empezar con puntuación perfecta
                
                # Verificar sample rate válido
                if sample_rate < 8000:
                    quality_issues.append("Very low sample rate (< 8kHz)")
                    quality_score -= 20
                elif sample_rate < 16000:
                    quality_issues.append("Low sample rate (< 16kHz)")
                    quality_score -= 10
                elif sample_rate > 48000:
                    quality_issues.append("Unusually high sample rate (> 48kHz)")
                    quality_score -= 5
                
                # Verificar channels válidos
                if channels < 1 or channels > 2:
                    quality_issues.append(f"Unusual channel count: {channels}")
                    quality_score -= 15
                
                # Verificar bits per sample
                if bits_per_sample < 16:
                    quality_issues.append("Low bit depth (< 16 bits)")
                    quality_score -= 15
                elif bits_per_sample > 32:
                    quality_issues.append("Unusually high bit depth (> 32 bits)")
                    quality_score -= 5
                
                # Verificar duración
                if duration_seconds is not None:
                    if duration_seconds < 0.1:
                        quality_issues.append("Very short duration (< 0.1s)")
                        quality_score -= 25
                    elif duration_seconds < 1.0:
                        quality_issues.append("Short duration (< 1s)")
                        quality_score -= 10
                    elif duration_seconds > 60:
                        quality_issues.append("Very long duration (> 60s)")
                        quality_score -= 5
                
                # Verificar coherencia de datos
                expected_byte_rate = sample_rate * channels * (bits_per_sample // 8)
                if abs(byte_rate - expected_byte_rate) > expected_byte_rate * 0.01:  # 1% tolerance
                    quality_issues.append("Byte rate doesn't match other parameters")
                    quality_score -= 10
                
                expected_block_align = channels * (bits_per_sample // 8)
                if block_align != expected_block_align:
                    quality_issues.append("Block align doesn't match other parameters")
                    quality_score -= 10
                
                # Análisis de tamaño de archivo
                expected_size = duration_seconds * byte_rate if duration_seconds else 0
                size_difference = abs(data_size - expected_size) / expected_size if expected_size > 0 else 0
                if size_difference > 0.05:  # 5% tolerance
                    quality_issues.append(f"File size doesn't match expected size (diff: {size_difference*100:.1f}%)")
                    quality_score -= 15
                
                metrics["quality_indicators"] = {
                    "quality_score": max(0, quality_score),
                    "issues": quality_issues,
                    "is_high_quality": quality_score >= 80,
                    "is_acceptable": quality_score >= 60,
                    "recommendations": _generate_audio_recommendations(metrics, quality_issues)
                }
                
            except Exception as header_error:
                quality_issues.append(f"Error parsing WAV header: {str(header_error)}")
                metrics["quality_indicators"] = {
                    "quality_score": 0,
                    "issues": quality_issues,
                    "is_high_quality": False,
                    "is_acceptable": False
                }
        
        elif audio_content.startswith(b'ID3') or audio_content.startswith(b'\xff\xfb'):
            metrics["estimated_format"] = "mp3"
            # Para MP3, análisis básico limitado
            quality_issues = ["MP3 format - limited analysis available"]
            metrics["quality_indicators"] = {
                "quality_score": 50,  # Puntuación neutral para MP3
                "issues": quality_issues,
                "is_high_quality": False,
                "is_acceptable": True
            }
        
        else:
            quality_issues = ["Unrecognized audio format"]
            metrics["quality_indicators"] = {
                "quality_score": 0,
                "issues": quality_issues,
                "is_high_quality": False,
                "is_acceptable": False
            }
        
        # Validaciones generales independientes del formato
        general_issues = []
        if len(audio_content) == 0:
            general_issues.append("Empty file")
        elif len(audio_content) < 1024:  # 1KB
            general_issues.append("Very small file size")
        elif len(audio_content) > 50 * 1024 * 1024:  # 50MB
            general_issues.append("Very large file size")
        
        if general_issues:
            existing_issues = metrics["quality_indicators"].get("issues", [])
            metrics["quality_indicators"]["issues"] = existing_issues + general_issues
            
    except Exception as e:
        # Si falla el análisis, no es crítico
        metrics["analysis_error"] = str(e)
        metrics["quality_indicators"] = {
            "quality_score": 0,
            "issues": [f"Analysis failed: {str(e)}"],
            "is_high_quality": False,
            "is_acceptable": False
        }
    
    return metrics


def _generate_audio_recommendations(metrics: Dict[str, Any], issues: List[str]) -> List[str]:
    """
    Generar recomendaciones basadas en los problemas encontrados en el audio.
    """
    recommendations = []
    
    # Recomendaciones basadas en sample rate
    if metrics.get("sample_rate_hz", 0) < 16000:
        recommendations.append("Consider increasing sample rate to at least 16kHz for better speech quality")
    
    # Recomendaciones basadas en bits per sample
    if metrics.get("bits_per_sample", 0) < 16:
        recommendations.append("Use at least 16-bit depth for acceptable audio quality")
    
    # Recomendaciones basadas en duración
    duration = metrics.get("estimated_duration_seconds", 0)
    if duration and duration < 1:
        recommendations.append("Very short audio clips may not contain enough information")
    elif duration and duration > 30:
        recommendations.append("Consider breaking long audio into shorter segments")
    
    # Recomendaciones basadas en tamaño
    if metrics.get("size_bytes", 0) > 10 * 1024 * 1024:  # 10MB
        recommendations.append("Large file size - consider compression or shorter duration")
    
    # Recomendaciones generales
    if any("coherence" in issue.lower() or "match" in issue.lower() for issue in issues):
        recommendations.append("Audio file may be corrupted - verify recording settings")
    
    return recommendations


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
# ENDPOINTS DE VERIFICACIÓN Y DEBUGGING
# ===============================================

@router.get("/audio/verification/status")
async def get_audio_verification_status():
    """
    Obtener estado de los archivos de verificación de audio.
    
    Útil para verificar que los audios se están recibiendo y guardando correctamente.
    """
    try:
        logger.info("🔍 Getting audio verification status...")
        
        audio_processor = get_audio_processor()
        
        # Obtener información de archivos de verificación
        verification_info = await audio_processor.get_verification_files_info()
        
        # Obtener estado de la cola de procesamiento
        queue_status = audio_processor.get_queue_status()
        
        return JSONResponse(
            content={
                "status": "success",
                "verification": verification_info,
                "processing_queue": queue_status,
                "timestamp": datetime.now().isoformat()
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get verification status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get verification status: {str(e)}"
        )


@router.get("/audio/verification/files")
async def list_verification_files():
    """
    Listar archivos de verificación disponibles.
    """
    try:
        logger.info("📋 Listing audio verification files...")
        
        audio_processor = get_audio_processor()
        files_list = await audio_processor.list_verification_files()
        
        return JSONResponse(
            content={
                "status": "success",
                "files": files_list,
                "total_files": len(files_list),
                "timestamp": datetime.now().isoformat()
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to list verification files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list verification files: {str(e)}"
        )


@router.get("/audio/processing/history")
async def get_audio_processing_history():
    """
    Obtener historial detallado de procesamiento de audio.
    
    Incluye métricas de rendimiento, errores y estadísticas.
    """
    try:
        logger.info("📊 Getting audio processing history...")
        
        audio_processor = get_audio_processor()
        
        # Obtener estadísticas detalladas
        processing_stats = audio_processor.get_processing_statistics()
        queue_status = audio_processor.get_queue_status()
        
        history = {
            "current_queue": queue_status,
            "statistics": processing_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        return JSONResponse(
            content={
                "status": "success",
                "history": history
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get processing history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get processing history: {str(e)}"
        )


# ===============================================
# ENDPOINTS DEL CLIENTE REMOTO
# ===============================================

@router.get("/remote/status")
async def get_remote_backend_status():
    """
    Verificar estado del cliente de backend remoto.
    
    Returns:
        Dict con información de estado, autenticación y conectividad
    """
    try:
        from clients.remote_backend_client import get_remote_client
        
        remote_client = get_remote_client()
        health_status = await remote_client.health_check()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "remote_backend": health_status
        }
        
    except RuntimeError as e:
        # Cliente no inicializado
        return {
            "success": False,
            "error": str(e),
            "remote_backend": {
                "status": "not_initialized",
                "authenticated": False
            }
        }
    except Exception as e:
        logger.error(f"❌ Failed to get remote backend status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get remote backend status: {str(e)}"
        )


@router.post("/remote/test-auth")
async def test_remote_authentication():
    """
    Probar autenticación con backend remoto.
    
    Útil para testing y diagnóstico de problemas de conexión.
    """
    try:
        from clients.remote_backend_client import get_remote_client
        
        remote_client = get_remote_client()
        
        # Forzar nueva autenticación
        success = await remote_client._authenticate()
        
        if success:
            return {
                "success": True,
                "message": "Authentication successful",
                "timestamp": datetime.now().isoformat(),
                "token_expires_at": remote_client.token_expires_at.isoformat() if remote_client.token_expires_at else None
            }
        else:
            return {
                "success": False,
                "message": "Authentication failed",
                "timestamp": datetime.now().isoformat()
            }
            
    except RuntimeError as e:
        # Cliente no inicializado
        raise HTTPException(
            status_code=503,
            detail=f"Remote client not initialized: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Failed to test remote authentication: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to test remote authentication: {str(e)}"
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
