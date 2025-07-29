"""
HTTP Server for PuertoCho Assistant Hardware Service
Provides REST API endpoints for hardware control and monitoring
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import uvicorn
import psutil
import os
import glob
from datetime import datetime
from pathlib import Path

# Importar el StateManager existente
from core.state_manager import StateManager, AssistantState

class StateChangeRequest(BaseModel):
    """Modelo para cambiar estado manualmente"""
    state: str

class AudioSendRequest(BaseModel):
    """Modelo para enviar audio al backend local"""
    backend_url: Optional[str] = None
    compress: bool = True

class HTTPServer:
    """
    Servidor HTTP para la API REST del hardware.
    Proporciona endpoints para control y monitoreo del hardware.
    """
    
    def __init__(self, state_manager: StateManager, port: int = 8080):
        self.state_manager = state_manager
        self.port = port
        self.logger = logging.getLogger("http_server")
        
        # Crear la app FastAPI
        self.app = FastAPI(
            title="PuertoCho Hardware API",
            description="REST API for hardware control and monitoring",
            version="1.0.0",
            docs_url="/docs",  # Swagger UI
            redoc_url="/redoc"  # ReDoc
        )
        
        # Configurar CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # En producción, especificar orígenes permitidos
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Registrar endpoints
        self._register_endpoints()
    
    def _register_endpoints(self):
        """Registrar todos los endpoints de la API"""
        
        @self.app.get("/health", 
                     summary="Health Check",
                     description="Verificar el estado del servicio hardware")
        async def health_check():
            """Estado del servicio hardware"""
            return {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "service": "puertocho-hardware",
                "version": "1.0.0",
                "hardware_state": self.state_manager.state.name
            }
        
        @self.app.get("/state", 
                     summary="Get Current State",
                     description="Obtener el estado actual del StateManager")
        async def get_state():
            """Obtener estado actual del StateManager"""
            listening_duration = None
            if self.state_manager.listening_start_time:
                listening_duration = datetime.now().timestamp() - self.state_manager.listening_start_time
            
            return {
                "state": self.state_manager.state.name,
                "timestamp": datetime.now().isoformat(),
                "listening_start_time": self.state_manager.listening_start_time,
                "listening_duration_seconds": listening_duration
            }
        
        @self.app.post("/state", 
                      summary="Change State",
                      description="Cambiar estado manualmente (para testing)")
        async def change_state(request: StateChangeRequest):
            """Cambiar estado manualmente (para testing)"""
            try:
                # Validar que el estado existe
                new_state = AssistantState[request.state.upper()]
                
                # Cambiar estado
                old_state = self.state_manager.state.name
                self.state_manager.set_state(new_state)
                
                self.logger.info(f"Manual state change: {old_state} -> {new_state.name}")
                
                return {
                    "success": True,
                    "old_state": old_state,
                    "new_state": new_state.name,
                    "timestamp": datetime.now().isoformat()
                }
                
            except KeyError:
                valid_states = [state.name for state in AssistantState]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": f"Invalid state: {request.state}",
                        "valid_states": valid_states
                    }
                )
            except Exception as e:
                self.logger.error(f"Error changing state: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error changing state: {str(e)}"
                )

        # ========================
        # ENDPOINTS DE GESTIÓN DE AUDIO (HW-API-03)
        # ========================
        
        @self.app.get("/audio/capture",
                     summary="Get Latest Captured Audio",
                     description="Obtener el último archivo de audio capturado por VAD")
        async def get_latest_captured_audio():
            """Obtener último archivo de audio capturado"""
            try:
                captured_dir = Path("/app/captured_audio")
                if not captured_dir.exists():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No captured audio directory found"
                    )
                
                # Buscar archivos WAV ordenados por fecha de modificación
                audio_files = list(captured_dir.glob("captured_*.wav"))
                
                if not audio_files:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No captured audio files found"
                    )
                
                # Obtener el más reciente
                latest_file = max(audio_files, key=lambda f: f.stat().st_mtime)
                
                # Información del archivo
                file_info = {
                    "filename": latest_file.name,
                    "path": str(latest_file),
                    "size_bytes": latest_file.stat().st_size,
                    "created_at": datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat(),
                    "download_url": f"/audio/download/{latest_file.name}"
                }
                
                return {
                    "success": True,
                    "latest_audio": file_info,
                    "total_files": len(audio_files),
                    "timestamp": datetime.now().isoformat()
                }
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error getting captured audio: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error retrieving captured audio: {str(e)}"
                )
        
        @self.app.get("/audio/download/{filename}",
                     summary="Download Audio File",
                     description="Descargar un archivo de audio específico")
        async def download_audio_file(filename: str):
            """Descargar archivo de audio específico"""
            try:
                # Validar filename para seguridad
                if not filename.endswith('.wav') or '..' in filename or '/' in filename:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid filename"
                    )
                
                file_path = Path("/app/captured_audio") / filename
                
                if not file_path.exists():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Audio file not found: {filename}"
                    )
                
                return FileResponse(
                    path=str(file_path),
                    media_type="audio/wav",
                    filename=filename
                )
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error downloading audio file: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error downloading audio file: {str(e)}"
                )
        
        @self.app.get("/audio/status",
                     summary="Get Audio Status",
                     description="Estado del audio, VAD y grabación")
        async def get_audio_status():
            """Estado de audio, VAD y grabación"""
            try:
                # Información básica del estado
                audio_status = {
                    "hardware_state": self.state_manager.state.name,
                    "is_listening": self.state_manager.state == AssistantState.LISTENING,
                    "vad_enabled": self.state_manager.vad_handler is not None,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Información del VAD si está disponible
                if self.state_manager.vad_handler:
                    vad_info = {
                        "sample_rate": self.state_manager.vad_handler.sample_rate,
                        "input_sample_rate": self.state_manager.vad_handler.input_sample_rate,
                        "frame_duration": self.state_manager.vad_handler.frame_duration,
                        "silence_timeout": self.state_manager.vad_handler.silence_timeout,
                        "in_speech": self.state_manager.vad_handler._in_speech,
                    }
                    audio_status["vad"] = vad_info
                
                # Estadísticas de archivos capturados
                captured_dir = Path("/app/captured_audio")
                if captured_dir.exists():
                    audio_files = list(captured_dir.glob("captured_*.wav"))
                    total_size = sum(f.stat().st_size for f in audio_files)
                    
                    audio_status["captured_files"] = {
                        "count": len(audio_files),
                        "total_size_bytes": total_size,
                        "total_size_mb": round(total_size / (1024 * 1024), 2)
                    }
                else:
                    audio_status["captured_files"] = {
                        "count": 0,
                        "total_size_bytes": 0,
                        "total_size_mb": 0
                    }
                
                # Información de tiempo de escucha
                if self.state_manager.listening_start_time:
                    listening_duration = datetime.now().timestamp() - self.state_manager.listening_start_time
                    audio_status["listening_duration_seconds"] = round(listening_duration, 2)
                
                return {
                    "success": True,
                    "audio_status": audio_status
                }
                
            except Exception as e:
                self.logger.error(f"Error getting audio status: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error getting audio status: {str(e)}"
                )
        
        @self.app.post("/audio/send",
                      summary="Send Audio to Backend",
                      description="Enviar último audio capturado al backend local")
        async def send_audio_to_backend(request: AudioSendRequest):
            """Endpoint para enviar audio al backend local"""
            try:
                # Obtener último archivo de audio
                captured_dir = Path("/app/captured_audio")
                if not captured_dir.exists():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No captured audio directory found"
                    )
                
                audio_files = list(captured_dir.glob("captured_*.wav"))
                if not audio_files:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No captured audio files to send"
                    )
                
                latest_file = max(audio_files, key=lambda f: f.stat().st_mtime)
                
                # TODO: Implementar envío real al backend en próximas iteraciones
                # Por ahora, simular el envío
                backend_url = request.backend_url or os.getenv("BACKEND_URL", "http://localhost:8765")
                
                return {
                    "success": True,
                    "message": "Audio send endpoint ready (implementation pending)",
                    "file_info": {
                        "filename": latest_file.name,
                        "size_bytes": latest_file.stat().st_size,
                        "target_backend": backend_url,
                        "compress": request.compress
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error sending audio to backend: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error sending audio to backend: {str(e)}"
                )

    def start(self):
        """Iniciar el servidor HTTP"""
        self.logger.info(f"🌐 Starting HTTP server on port {self.port}")
        self.logger.info(f"📖 API documentation available at: http://0.0.0.0:{self.port}/docs")
        uvicorn.run(self.app, host="0.0.0.0", port=self.port, log_level="info")

    def start_async(self, host: str = "0.0.0.0"):
        """
        Iniciar el servidor de forma asíncrona (para integración con otros servicios)
        Devuelve la configuración para uvicorn
        """
        return {
            "app": self.app,
            "host": host,
            "port": self.port,
            "log_level": "info"
        }
