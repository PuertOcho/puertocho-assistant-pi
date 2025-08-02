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
        
        # Configuración de verificación de audio
        self.verification_enabled = os.getenv("AUDIO_VERIFICATION_ENABLED", "true").lower() == "true"
        self.verification_days = int(os.getenv("AUDIO_VERIFICATION_DAYS", "7"))
        self.verification_max_files = int(os.getenv("AUDIO_VERIFICATION_MAX_FILES", "100"))
        self.verification_dir = Path("/app/audio_verification")
        
        if self.verification_enabled:
            self.verification_dir.mkdir(exist_ok=True)
            self.logger.info(f"🔍 Audio verification enabled: {self.verification_dir}")
            self.logger.info(f"📅 Retention: {self.verification_days} days, max {self.verification_max_files} files")
        
        # Tasks
        self._processing_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Iniciar el procesador de audio"""
        self.logger.info("🎙️ Starting Audio Processor...")
        
        self._running = True
        self._processing_task = asyncio.create_task(self._processing_loop())
        
        # Limpieza inicial de archivos de verificación antiguos
        if self.verification_enabled:
            await self._cleanup_old_verification_files()
            # Iniciar tarea de limpieza periódica (cada hora)
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
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
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
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
            
            # Guardar copia de verificación si está habilitado
            verification_path = None
            if self.verification_enabled:
                verification_path = await self._save_verification_copy(
                    processing_entry["id"], 
                    filename, 
                    audio_data
                )
                processing_entry["verification_path"] = str(verification_path)
                self.logger.info(f"🔍 Verification copy saved: {verification_path}")
            
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
    # VERIFICACIÓN DE AUDIO
    # ===============================================
    
    async def _save_verification_copy(self, audio_id: str, original_filename: str, audio_data: bytes) -> Path:
        """
        Guardar copia de verificación del audio.
        
        Args:
            audio_id: ID del audio para procesamiento
            original_filename: Nombre del archivo original del hardware
            audio_data: Datos binarios del audio
            
        Returns:
            Path al archivo de verificación guardado
        """
        try:
            # Crear timestamp con microsegundos para evitar colisiones
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            microsec = now.strftime("%f")[:3]  # Primeros 3 dígitos de microsegundos
            
            # Formato: verification_YYYYMMDD_HHMMSS_microsec_original_filename.wav
            verification_filename = f"verification_{timestamp}_{microsec}_{original_filename}"
            verification_path = self.verification_dir / verification_filename
            
            # Guardar archivo
            with open(verification_path, "wb") as f:
                f.write(audio_data)
            
            self.logger.debug(f"🔍 Verification copy saved: {verification_path} ({len(audio_data)} bytes)")
            
            return verification_path
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save verification copy for {audio_id}: {e}")
            raise
    
    async def _cleanup_old_verification_files(self):
        """
        Limpiar archivos de verificación antiguos basado en:
        - Edad (días configurados)
        - Cantidad máxima de archivos
        """
        if not self.verification_enabled or not self.verification_dir.exists():
            return
        
        try:
            verification_files = list(self.verification_dir.glob("verification_*.wav"))
            
            if not verification_files:
                return
            
            # Ordenar por fecha de modificación (más recientes primero)
            verification_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            current_time = datetime.now().timestamp()
            max_age_seconds = self.verification_days * 24 * 3600
            
            files_removed = 0
            files_kept = 0
            
            for i, file_path in enumerate(verification_files):
                should_remove = False
                reason = ""
                
                # Verificar edad
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    should_remove = True
                    reason = f"older than {self.verification_days} days"
                
                # Verificar límite de cantidad (mantener solo los más recientes)
                elif i >= self.verification_max_files:
                    should_remove = True
                    reason = f"exceeds max files limit ({self.verification_max_files})"
                
                if should_remove:
                    try:
                        file_path.unlink()
                        files_removed += 1
                        self.logger.debug(f"🗑️ Removed verification file: {file_path.name} ({reason})")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Failed to remove {file_path}: {e}")
                else:
                    files_kept += 1
            
            if files_removed > 0 or files_kept > 0:
                self.logger.info(f"🗑️ Verification cleanup: removed {files_removed}, kept {files_kept} files")
                
        except Exception as e:
            self.logger.error(f"❌ Error during verification files cleanup: {e}")
    
    async def _periodic_cleanup(self):
        """Tarea periódica de limpieza de archivos de verificación (cada hora)"""
        while self._running:
            try:
                # Esperar 1 hora
                await asyncio.sleep(3600)  # 3600 segundos = 1 hora
                
                if self._running:  # Verificar que aún estamos corriendo
                    self.logger.debug("🔄 Running periodic verification cleanup...")
                    await self._cleanup_old_verification_files()
                    
            except asyncio.CancelledError:
                self.logger.info("🔄 Periodic cleanup cancelled")
                break
            except Exception as e:
                self.logger.error(f"❌ Error in periodic cleanup: {e}")
                # Continuar con el loop a pesar del error
                await asyncio.sleep(300)  # Esperar 5 minutos antes de reintentar
    
    # ===============================================
    # INFORMACIÓN Y ESTADÍSTICAS
    # ===============================================
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Obtener estado de la cola de procesamiento"""
        verification_stats = {}
        
        if self.verification_enabled and self.verification_dir.exists():
            try:
                verification_files = list(self.verification_dir.glob("verification_*.wav"))
                total_size = sum(f.stat().st_size for f in verification_files)
                verification_stats = {
                    "verification_files_count": len(verification_files),
                    "verification_total_size_bytes": total_size,
                    "verification_directory": str(self.verification_dir)
                }
            except Exception as e:
                verification_stats = {"verification_error": str(e)}
        
        return {
            "queue_size": len(self.processing_queue),
            "is_processing": self.is_processing,
            "remote_available": self.remote_available,
            "max_queue_size": self.max_queue_size,
            "verification_enabled": self.verification_enabled,
            "verification_config": {
                "days_retention": self.verification_days,
                "max_files": self.verification_max_files
            } if self.verification_enabled else None,
            **verification_stats,
            "items": [
                {
                    "id": entry["id"],
                    "status": entry["status"],
                    "received_at": entry["received_at"],
                    "size_bytes": entry["size_bytes"],
                    "has_verification_copy": "verification_path" in entry
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
