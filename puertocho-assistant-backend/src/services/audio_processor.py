"""
Audio Processor Service for PuertoCho Assistant Backend
======================================================

Servicio para procesar audio recibido del hardware y enviarlo al backend remoto.
Maneja buffer, cola de peticiones y procesamiento cuando el remoto está disponible.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import tempfile
import os

from clients.hardware_client import get_hardware_client


class AudioProcessor:
    """
    Procesador de audio que gestiona el flujo desde hardware hacia backend remoto.
    
    Responsabilidades:
    - Recibir audio del hardware
    - Mantener buffer/cola cuando backend remoto no está disponible
    - Enviar audio al backend remoto cuando esté disponible
    - Procesar respuestas del backend remoto
    - Notificar resultados al frontend
    """
    
    def __init__(self, websocket_manager=None):
        self.logger = logging.getLogger("audio_processor")
        self.websocket_manager = websocket_manager
        
        # Buffer y cola de audio
        self.audio_queue: asyncio.Queue = asyncio.Queue()
        self.processing_queue: List[Dict[str, Any]] = []
        
        # Estado del procesador
        self.is_processing = False
        self.remote_available = False
        
        # Configuración
        self.max_queue_size = 10
        self.temp_dir = Path(tempfile.gettempdir()) / "puertocho_audio_buffer"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Tasks
        self._processing_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Iniciar el procesador de audio"""
        self.logger.info("🎙️ Starting Audio Processor...")
        
        self._running = True
        self._processing_task = asyncio.create_task(self._processing_loop())
        
        self.logger.info("✅ Audio Processor started")
    
    async def stop(self):
        """Detener el procesador de audio"""
        self.logger.info("🛑 Stopping Audio Processor...")
        
        self._running = False
        
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        # Limpiar archivos temporales
        await self._cleanup_temp_files()
        
        self.logger.info("✅ Audio Processor stopped")
    
    # ===============================================
    # PROCESAMIENTO DE AUDIO DEL HARDWARE
    # ===============================================
    
    async def process_audio_from_hardware(self, audio_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesar audio recibido del hardware.
        
        Args:
            audio_info: Información del audio desde hardware
            
        Returns:
            Resultado del procesamiento
        """
        try:
            self.logger.info("🎙️ Processing audio from hardware...")
            
            # Obtener información del último audio capturado
            hardware_client = get_hardware_client()
            latest_audio = await hardware_client.get_latest_audio()
            
            if not latest_audio.get("success"):
                raise Exception("No audio available from hardware")
            
            audio_file_info = latest_audio["latest_audio"]
            filename = audio_file_info["filename"]
            
            # Descargar archivo de audio
            self.logger.info(f"📥 Downloading audio file: {filename}")
            audio_data = await hardware_client.download_audio(filename)
            
            # Crear entrada para procesamiento
            processing_entry = {
                "id": f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "filename": filename,
                "size_bytes": len(audio_data),
                "received_at": datetime.now().isoformat(),
                "status": "pending",
                "metadata": audio_file_info
            }
            
            # Guardar audio en buffer temporal
            temp_file_path = await self._save_to_temp_buffer(processing_entry["id"], audio_data)
            processing_entry["temp_path"] = str(temp_file_path)
            
            # Agregar a cola de procesamiento
            await self._add_to_processing_queue(processing_entry)
            
            # Notificar al frontend
            if self.websocket_manager:
                await self.websocket_manager.broadcast_audio_processing({
                    "action": "audio_received",
                    "audio_id": processing_entry["id"],
                    "filename": filename,
                    "size_bytes": len(audio_data),
                    "queue_size": len(self.processing_queue)
                })
            
            return {
                "success": True,
                "audio_id": processing_entry["id"],
                "status": "queued_for_processing",
                "queue_position": len(self.processing_queue)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to process audio from hardware: {e}")
            
            if self.websocket_manager:
                await self.websocket_manager.broadcast_error(
                    f"Audio processing failed: {str(e)}"
                )
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _save_to_temp_buffer(self, audio_id: str, audio_data: bytes) -> Path:
        """Guardar audio en buffer temporal"""
        temp_file_path = self.temp_dir / f"{audio_id}.wav"
        
        with open(temp_file_path, "wb") as f:
            f.write(audio_data)
        
        self.logger.debug(f"💾 Audio saved to temp buffer: {temp_file_path}")
        return temp_file_path
    
    async def _add_to_processing_queue(self, entry: Dict[str, Any]):
        """Agregar entrada a la cola de procesamiento"""
        # Verificar límite de cola
        if len(self.processing_queue) >= self.max_queue_size:
            # Remover la entrada más antigua
            oldest_entry = self.processing_queue.pop(0)
            await self._cleanup_temp_file(oldest_entry.get("temp_path"))
            self.logger.warning(f"⚠️ Queue full, removed oldest entry: {oldest_entry.get('id')}")
        
        self.processing_queue.append(entry)
        self.logger.info(f"📋 Added to processing queue: {entry['id']} (queue size: {len(self.processing_queue)})")
    
    # ===============================================
    # LOOP DE PROCESAMIENTO
    # ===============================================
    
    async def _processing_loop(self):
        """Loop principal de procesamiento de audio"""
        self.logger.info("🔄 Starting audio processing loop...")
        
        while self._running:
            try:
                # Procesar cola si hay elementos
                if self.processing_queue and not self.is_processing:
                    await self._process_next_in_queue()
                
                # Esperar un poco antes del siguiente ciclo
                await asyncio.sleep(1.0)
                
            except asyncio.CancelledError:
                self.logger.info("🔄 Audio processing loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"❌ Error in audio processing loop: {e}")
                await asyncio.sleep(5.0)  # Esperar más tiempo en caso de error
    
    async def _process_next_in_queue(self):
        """Procesar siguiente elemento en la cola"""
        if not self.processing_queue:
            return
        
        self.is_processing = True
        entry = self.processing_queue[0]  # Procesar FIFO
        
        try:
            self.logger.info(f"🎯 Processing audio: {entry['id']}")
            
            # Marcar como en procesamiento
            entry["status"] = "processing"
            entry["processing_started_at"] = datetime.now().isoformat()
            
            # Notificar inicio de procesamiento
            if self.websocket_manager:
                await self.websocket_manager.broadcast_audio_processing({
                    "action": "processing_started",
                    "audio_id": entry["id"]
                })
            
            # Intentar enviar al backend remoto
            if self.remote_available:
                result = await self._send_to_remote_backend(entry)
                if result["success"]:
                    entry["status"] = "completed"
                    entry["completed_at"] = datetime.now().isoformat()
                    entry["result"] = result
                    
                    # Remover de cola y limpiar archivo temporal
                    self.processing_queue.remove(entry)
                    await self._cleanup_temp_file(entry.get("temp_path"))
                    
                    self.logger.info(f"✅ Audio processing completed: {entry['id']}")
                    
                    # Notificar resultado
                    if self.websocket_manager:
                        await self.websocket_manager.broadcast_audio_processing({
                            "action": "processing_completed",
                            "audio_id": entry["id"],
                            "result": result
                        })
                else:
                    # Falló el envío, marcar como pendiente
                    entry["status"] = "pending"
                    self.logger.warning(f"⚠️ Failed to send to remote, keeping in queue: {entry['id']}")
            else:
                # Backend remoto no disponible, mantener en cola
                entry["status"] = "pending"
                self.logger.debug(f"⏳ Remote backend not available, keeping in queue: {entry['id']}")
                
        except Exception as e:
            self.logger.error(f"❌ Error processing audio {entry['id']}: {e}")
            entry["status"] = "error"
            entry["error"] = str(e)
            
            if self.websocket_manager:
                await self.websocket_manager.broadcast_error(
                    f"Audio processing error: {str(e)}",
                    {"audio_id": entry["id"]}
                )
        
        finally:
            self.is_processing = False
    
    async def _send_to_remote_backend(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enviar audio al backend remoto para procesamiento.
        
        Por ahora es un placeholder - en el futuro se implementará
        la comunicación real con el backend remoto.
        """
        try:
            # TODO: Implementar cliente para backend remoto
            self.logger.info(f"📡 Sending to remote backend: {entry['id']}")
            
            # Simular procesamiento remoto
            await asyncio.sleep(2.0)
            
            # Respuesta simulada
            simulated_response = {
                "success": True,
                "transcription": "Comando simulado desde audio",
                "intent": "unknown",
                "confidence": 0.85,
                "processing_time_ms": 2000
            }
            
            self.logger.info(f"✅ Remote backend response: {simulated_response}")
            
            # Notificar respuesta al frontend
            if self.websocket_manager:
                await self.websocket_manager.broadcast_remote_response({
                    "audio_id": entry["id"],
                    "transcription": simulated_response["transcription"],
                    "intent": simulated_response["intent"],
                    "confidence": simulated_response["confidence"]
                })
            
            return simulated_response
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send to remote backend: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ===============================================
    # GESTIÓN DEL BACKEND REMOTO
    # ===============================================
    
    def set_remote_availability(self, available: bool):
        """Establecer disponibilidad del backend remoto"""
        if self.remote_available != available:
            self.remote_available = available
            status = "available" if available else "unavailable"
            self.logger.info(f"🌐 Remote backend is now {status}")
            
            if available and self.processing_queue:
                self.logger.info(f"🔄 Remote backend available, {len(self.processing_queue)} items in queue")
    
    # ===============================================
    # LIMPIEZA Y UTILIDADES
    # ===============================================
    
    async def _cleanup_temp_file(self, file_path: Optional[str]):
        """Limpiar archivo temporal"""
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                self.logger.debug(f"🗑️ Cleaned up temp file: {file_path}")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to cleanup temp file {file_path}: {e}")
    
    async def _cleanup_temp_files(self):
        """Limpiar todos los archivos temporales"""
        try:
            for entry in self.processing_queue:
                await self._cleanup_temp_file(entry.get("temp_path"))
            
            # Limpiar directorio temporal
            for file_path in self.temp_dir.glob("*.wav"):
                try:
                    file_path.unlink()
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to cleanup {file_path}: {e}")
                    
            self.logger.info("🗑️ Temp files cleaned up")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error during temp files cleanup: {e}")
    
    # ===============================================
    # INFORMACIÓN Y ESTADÍSTICAS
    # ===============================================
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Obtener estado de la cola de procesamiento"""
        return {
            "queue_size": len(self.processing_queue),
            "is_processing": self.is_processing,
            "remote_available": self.remote_available,
            "max_queue_size": self.max_queue_size,
            "items": [
                {
                    "id": entry["id"],
                    "status": entry["status"],
                    "received_at": entry["received_at"],
                    "size_bytes": entry["size_bytes"]
                }
                for entry in self.processing_queue
            ]
        }


# Instancia singleton
audio_processor: Optional[AudioProcessor] = None


def get_audio_processor() -> AudioProcessor:
    """Obtener instancia del procesador de audio"""
    global audio_processor
    if audio_processor is None:
        raise Exception("AudioProcessor not initialized. Call init_audio_processor() first.")
    return audio_processor


def init_audio_processor(websocket_manager=None) -> AudioProcessor:
    """Inicializar procesador de audio"""
    global audio_processor
    audio_processor = AudioProcessor(websocket_manager)
    return audio_processor


async def close_audio_processor():
    """Cerrar procesador de audio"""
    global audio_processor
    if audio_processor:
        await audio_processor.stop()
        audio_processor = None
