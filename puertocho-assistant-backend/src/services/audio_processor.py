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
import json
import base64

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
        
        # Config conversación (Epic4)
        self.default_language = os.getenv("REMOTE_BACKEND_LANGUAGE", "es")
        self.default_user_id = os.getenv("CONVERSATION_DEFAULT_USER_ID", os.getenv("REMOTE_BACKEND_EMAIL", "service@puertocho.local"))
        self.session_strategy = os.getenv("CONVERSATION_SESSION_STRATEGY", "sticky-per-device")
        self.forced_session_id = os.getenv("CONVERSATION_SESSION_ID")
        self.device_id = os.getenv("DEVICE_ID")
        
        # Tasks
        self._processing_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._remote_monitor_task: Optional[asyncio.Task] = None
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
        
        # Iniciar monitor de disponibilidad del backend remoto
        self._remote_monitor_task = asyncio.create_task(self._monitor_remote_availability())
        
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
        
        if self._remote_monitor_task:
            self._remote_monitor_task.cancel()
            try:
                await self._remote_monitor_task
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
        processing_start = datetime.now()
        audio_id = None
        
        try:
            self.logger.info("🎙️ Processing audio from hardware...")
            
            # Logging de métricas de entrada si están disponibles
            if "audio_metrics" in audio_info:
                metrics = audio_info["audio_metrics"]
                self.logger.info(f"🎵 Audio metrics - Format: {metrics.get('estimated_format')}, "
                               f"Size: {metrics.get('size_bytes')} bytes, "
                               f"Channels: {metrics.get('channels')}, "
                               f"Sample Rate: {metrics.get('sample_rate_hz')} Hz")
                
                if metrics.get('estimated_duration_seconds'):
                    self.logger.info(f"⏱️ Estimated duration: {metrics['estimated_duration_seconds']:.2f} seconds")
            
            # Obtener información del último audio capturado
            self.logger.info("🔗 Connecting to hardware client...")
            hardware_client = get_hardware_client()
            
            hardware_fetch_start = datetime.now()
            latest_audio = await hardware_client.get_latest_audio()
            hardware_fetch_duration = (datetime.now() - hardware_fetch_start).total_seconds()
            
            self.logger.info(f"📡 Hardware fetch completed in {hardware_fetch_duration:.3f} seconds")
            
            if not latest_audio.get("success"):
                error_msg = f"No audio available from hardware: {latest_audio}"
                self.logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
            
            audio_file_info = latest_audio["latest_audio"]
            filename = audio_file_info["filename"]
            
            self.logger.info(f"📄 Hardware audio file info: {audio_file_info}")
            
            # Descargar archivo de audio
            download_start = datetime.now()
            self.logger.info(f"📥 Downloading audio file: {filename}")
            audio_data = await hardware_client.download_audio(filename)
            download_duration = (datetime.now() - download_start).total_seconds()
            
            # Validar descarga
            if not audio_data:
                raise Exception(f"Downloaded audio data is empty for file: {filename}")
            
            download_size_kb = len(audio_data) / 1024
            download_speed_kbps = download_size_kb / download_duration if download_duration > 0 else 0
            
            self.logger.info(f"📦 Download completed: {len(audio_data)} bytes ({download_size_kb:.2f} KB) "
                           f"in {download_duration:.3f} seconds ({download_speed_kbps:.2f} KB/s)")
            
            # Validar integridad básica del audio
            integrity_check = self._validate_audio_integrity(audio_data, filename)
            self.logger.info(f"🔍 Audio integrity check: {integrity_check}")
            
            # Crear entrada para procesamiento con información extendida
            audio_id = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            processing_entry = {
                "id": audio_id,
                "filename": filename,
                "original_filename": audio_info.get("filename", filename),
                "size_bytes": len(audio_data),
                "received_at": audio_info.get("received_at", datetime.now().isoformat()),
                "processing_started_at": processing_start.isoformat(),
                "status": "pending",
                "metadata": audio_file_info,
                "source_info": audio_info,
                "integrity_check": integrity_check,
                "timing": {
                    "hardware_fetch_seconds": hardware_fetch_duration,
                    "download_seconds": download_duration,
                    "download_speed_kbps": download_speed_kbps
                }
            }
            
            self.logger.info(f"🆔 Created processing entry with ID: {audio_id}")
            
            # Guardar audio en buffer temporal
            temp_save_start = datetime.now()
            temp_file_path = await self._save_to_temp_buffer(processing_entry["id"], audio_data)
            temp_save_duration = (datetime.now() - temp_save_start).total_seconds()
            
            processing_entry["temp_path"] = str(temp_file_path)
            processing_entry["timing"]["temp_save_seconds"] = temp_save_duration
            
            self.logger.info(f"💾 Temporary file saved in {temp_save_duration:.3f} seconds: {temp_file_path}")
            
            # Guardar copia de verificación si está habilitado
            verification_path = None
            if self.verification_enabled:
                verification_start = datetime.now()
                verification_path = await self._save_verification_copy(
                    processing_entry["id"], 
                    filename, 
                    audio_data
                )
                verification_duration = (datetime.now() - verification_start).total_seconds()
                
                processing_entry["verification_path"] = str(verification_path)
                processing_entry["timing"]["verification_save_seconds"] = verification_duration
                
                self.logger.info(f"🔍 Verification copy saved in {verification_duration:.3f} seconds: {verification_path}")
            
            # Agregar a cola de procesamiento
            queue_add_start = datetime.now()
            await self._add_to_processing_queue(processing_entry)
            queue_add_duration = (datetime.now() - queue_add_start).total_seconds()
            
            current_queue_size = len(self.processing_queue)
            self.logger.info(f"📋 Added to processing queue in {queue_add_duration:.3f} seconds. "
                           f"Queue size: {current_queue_size}/{self.max_queue_size}")
            
            # Calcular tiempo total de procesamiento hasta aquí
            total_processing_time = (datetime.now() - processing_start).total_seconds()
            
            # Notificar al frontend
            if self.websocket_manager:
                notification_start = datetime.now()
                await self.websocket_manager.broadcast_audio_processing({
                    "action": "audio_received",
                    "audio_id": processing_entry["id"],
                    "filename": filename,
                    "size_bytes": len(audio_data),
                    "queue_size": current_queue_size,
                    "processing_time_seconds": total_processing_time
                })
                notification_duration = (datetime.now() - notification_start).total_seconds()
                self.logger.info(f"📡 Frontend notification sent in {notification_duration:.3f} seconds")
            
            # Resultado exitoso con métricas detalladas
            result = {
                "success": True,
                "audio_id": processing_entry["id"],
                "status": "queued_for_processing",
                "queue_position": current_queue_size,
                "processing_metrics": {
                    "total_processing_time_seconds": total_processing_time,
                    "hardware_fetch_seconds": hardware_fetch_duration,
                    "download_seconds": download_duration,
                    "temp_save_seconds": temp_save_duration,
                    "verification_save_seconds": verification_duration if verification_path else 0,
                    "queue_add_seconds": queue_add_duration
                }
            }
            
            self.logger.info(f"✅ Audio processing completed successfully in {total_processing_time:.3f} seconds - ID: {audio_id}")
            return result
            
        except Exception as e:
            total_error_time = (datetime.now() - processing_start).total_seconds()
            
            self.logger.error(f"❌ Failed to process audio from hardware: {e}")
            self.logger.error(f"💥 Error occurred after {total_error_time:.3f} seconds")
            self.logger.error(f"🆔 Failed audio ID: {audio_id or 'not assigned'}")
            
            if self.websocket_manager:
                try:
                    await self.websocket_manager.broadcast_error(
                        f"Audio processing failed: {str(e)}"
                    )
                except Exception as notify_error:
                    self.logger.error(f"📡 Failed to send error notification: {notify_error}")
            
            return {
                "success": False,
                "error": str(e),
                "audio_id": audio_id,
                "error_after_seconds": total_error_time
            }
    
    def _validate_audio_integrity(self, audio_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Valida la integridad básica del archivo de audio.
        
        Args:
            audio_data: Datos del audio
            filename: Nombre del archivo
            
        Returns:
            Resultado de la validación
        """
        validation = {
            "is_valid": False,
            "format_detected": "unknown",
            "issues": []
        }
        
        try:
            # Verificar que no esté vacío
            if len(audio_data) == 0:
                validation["issues"].append("Audio data is empty")
                return validation
            
            # Verificar formato WAV
            if audio_data.startswith(b'RIFF') and len(audio_data) > 8 and audio_data[8:12] == b'WAVE':
                validation["format_detected"] = "wav"
                
                # Verificar tamaño mínimo para header WAV
                if len(audio_data) < 44:
                    validation["issues"].append("WAV file too small (missing header)")
                else:
                    validation["is_valid"] = True
                    
            # Verificar formato MP3
            elif audio_data.startswith(b'ID3') or audio_data.startswith(b'\xff\xfb'):
                validation["format_detected"] = "mp3"
                validation["is_valid"] = True
                
            else:
                validation["issues"].append("Unrecognized audio format")
            
            # Verificar extensión vs contenido
            file_ext = filename.split('.')[-1].lower() if '.' in filename else ""
            if file_ext and validation["format_detected"] != "unknown":
                if file_ext != validation["format_detected"]:
                    validation["issues"].append(f"Extension '{file_ext}' doesn't match detected format '{validation['format_detected']}'")
            
        except Exception as e:
            validation["issues"].append(f"Validation error: {str(e)}")
        
        return validation
    
    async def _save_to_temp_buffer(self, audio_id: str, audio_data: bytes) -> Path:
        """Guardar audio en buffer temporal con logging detallado"""
        temp_file_path = self.temp_dir / f"{audio_id}.wav"
        
        try:
            # Verificar que el directorio temporal existe
            self.temp_dir.mkdir(exist_ok=True)
            
            # Escribir archivo con medición de tiempo
            write_start = datetime.now()
            with open(temp_file_path, "wb") as f:
                f.write(audio_data)
            write_duration = (datetime.now() - write_start).total_seconds()
            
            # Verificar que el archivo se escribió correctamente
            if not temp_file_path.exists():
                raise Exception(f"Temp file was not created: {temp_file_path}")
            
            written_size = temp_file_path.stat().st_size
            if written_size != len(audio_data):
                raise Exception(f"Size mismatch: expected {len(audio_data)}, written {written_size}")
            
            write_speed_kbps = (len(audio_data) / 1024) / write_duration if write_duration > 0 else 0
            
            self.logger.debug(f"💾 Audio saved to temp buffer: {temp_file_path}")
            self.logger.debug(f"📏 Write performance: {len(audio_data)} bytes in {write_duration:.3f}s ({write_speed_kbps:.2f} KB/s)")
            
            return temp_file_path
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save audio to temp buffer: {e}")
            self.logger.error(f"📁 Temp directory: {self.temp_dir}")
            self.logger.error(f"📄 Target file: {temp_file_path}")
            raise
    
    async def _add_to_processing_queue(self, entry: Dict[str, Any]):
        """Agregar entrada a la cola de procesamiento con logging mejorado"""
        entry_id = entry.get('id', 'unknown')
        queue_size_before = len(self.processing_queue)
        
        try:
            # Verificar límite de cola
            if queue_size_before >= self.max_queue_size:
                # Remover la entrada más antigua
                oldest_entry = self.processing_queue.pop(0)
                oldest_id = oldest_entry.get('id', 'unknown')
                
                # Cleanup del archivo temporal
                temp_path = oldest_entry.get("temp_path")
                if temp_path:
                    try:
                        await self._cleanup_temp_file(temp_path)
                        self.logger.warning(f"🧹 Cleaned up temp file for removed entry: {temp_path}")
                    except Exception as cleanup_error:
                        self.logger.error(f"❌ Failed to cleanup temp file {temp_path}: {cleanup_error}")
                
                self.logger.warning(f"⚠️ Queue full ({self.max_queue_size}), removed oldest entry: {oldest_id}")
            
            # Agregar nueva entrada
            self.processing_queue.append(entry)
            queue_size_after = len(self.processing_queue)
            
            self.logger.info(f"📋 Added to processing queue: {entry_id}")
            self.logger.info(f"📊 Queue stats: {queue_size_before} → {queue_size_after}/{self.max_queue_size}")
            
            # Log información adicional de la entrada
            if 'size_bytes' in entry:
                size_kb = entry['size_bytes'] / 1024
                self.logger.debug(f"📦 Entry size: {size_kb:.2f} KB")
            
            if 'filename' in entry:
                self.logger.debug(f"📄 Entry filename: {entry['filename']}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to add entry to processing queue: {e}")
            self.logger.error(f"🆔 Entry ID: {entry_id}")
            raise
    
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
        Enviar audio al backend remoto para procesamiento conversacional.
        """
        try:
            # Importar el cliente remoto
            from clients.remote_backend_client import get_remote_client
            
            entry_id = entry.get('id', 'unknown')
            self.logger.info(f"📡 Sending audio {entry_id} to remote backend...")
            
            # Obtener cliente remoto
            remote_client = get_remote_client()
            
            # Leer datos de audio
            audio_file_path = entry.get('temp_file_path')
            if not audio_file_path or not os.path.exists(audio_file_path):
                raise ValueError(f"Audio file not found: {audio_file_path}")
            
            with open(audio_file_path, 'rb') as f:
                audio_data = f.read()
            
            # Preparar parámetros conversacionales
            session_id = self._resolve_session_id()
            user_id = self.default_user_id
            language = self.default_language
            metadata = entry.get('metadata', {})
            
            self.logger.info(f"�️ Conversation params - Session: {session_id}, User: {user_id}, Lang: {language}")
            
            # Enviar al backend remoto
            response = await remote_client.send_audio_for_conversation(
                audio_data=audio_data,
                session_id=session_id,
                user_id=user_id,
                language=language,
                metadata_json=json.dumps(metadata),
                generate_audio_response=True
            )
            
            if response.get("success"):
                self.logger.info(f"✅ Remote backend processed audio {entry_id}")
                
                # Log de respuesta
                if response.get("text"):
                    self.logger.info(f"📝 Transcription: {response['text'][:100]}...")
                
                # Procesar respuesta de audio si existe
                audio_response_data = None
                if response.get("audioResponse"):
                    try:
                        audio_response_data = base64.b64decode(response["audioResponse"])
                        self.logger.info(f"🔊 Audio response received: {len(audio_response_data)} bytes")
                        
                        # Enviar audio al hardware para reproducción
                        await self._send_audio_to_hardware(audio_response_data)
                        
                    except Exception as e:
                        self.logger.error(f"❌ Error processing audio response: {e}")
                
                # Notificar respuesta al frontend
                if self.websocket_manager:
                    await self.websocket_manager.broadcast_remote_response({
                        "audio_id": entry_id,
                        "transcription": response.get("text", ""),
                        "intent": response.get("intent", "unknown"),
                        "confidence": response.get("confidence", 0.0),
                        "has_audio_response": bool(audio_response_data),
                        "response_duration": response.get("audioDuration", 0.0)
                    })
                
                return {
                    "success": True,
                    "transcription": response.get("text", ""),
                    "intent": response.get("intent", "unknown"),
                    "confidence": response.get("confidence", 0.0),
                    "has_audio_response": bool(audio_response_data),
                    "processing_time_ms": response.get("processingTime", 0)
                }
            else:
                error_msg = response.get("error", "Unknown remote backend error")
                self.logger.error(f"❌ Remote backend failed for {entry_id}: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
                
        except Exception as e:
            self.logger.error(f"❌ Failed to send audio {entry.get('id', 'unknown')} to remote backend: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _resolve_session_id(self) -> str:
        """Resolver sessionId según estrategia sticky-per-device"""
        if self.forced_session_id:
            return self.forced_session_id
        if self.device_id:
            return f"device-{self.device_id}"
        return f"device-{self._get_hostname()}"
    
    def _get_hostname(self) -> str:
        try:
            import socket
            return socket.gethostname()
        except Exception:
            return "unknown"
    
    async def _send_audio_to_hardware(self, audio_data: bytes):
        """
        Enviar audio al hardware para reproducción.
        """
        try:
            hardware_client = get_hardware_client()
            
            # Codificar audio en base64 para envío
            audio_b64 = base64.b64encode(audio_data).decode()
            
            # Enviar al hardware
            response = await hardware_client.play_audio({
                "audio_data": audio_b64,
                "format": "wav",
                "sample_rate": 22050  # Asumimos 22050 por defecto para TTS
            })
            
            if response.get("success"):
                self.logger.info("🔊 Audio sent to hardware for playback")
            else:
                self.logger.error(f"❌ Failed to send audio to hardware: {response.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"❌ Error sending audio to hardware: {e}")
    
    async def _monitor_remote_availability(self):
        """
        Monitoriza periódicamente el estado del backend remoto y
        actualiza remote_available. Se considera 'available' si el
        cliente remoto está autenticado y funcionando correctamente.
        """
        self.logger.info("🌐 Starting remote availability monitor...")
        initial_log_done = False

        while self._running:
            try:
                # Verificar disponibilidad cada 30 segundos
                await asyncio.sleep(30)
                
                if not self._running:
                    break
                
                # Verificar si el cliente remoto está disponible
                try:
                    from clients.remote_backend_client import get_remote_client
                    remote_client = get_remote_client()
                    
                    # Verificar autenticación
                    if remote_client.is_authenticated:
                        if not self.remote_available:
                            self.set_remote_availability(True)
                    else:
                        if self.remote_available:
                            self.set_remote_availability(False)
                            
                except Exception as e:
                    if not initial_log_done:
                        self.logger.warning(f"🌐 Remote client not available yet: {e}")
                        initial_log_done = True
                    if self.remote_available:
                        self.set_remote_availability(False)
                        
            except asyncio.CancelledError:
                self.logger.info("🛑 Remote availability monitor cancelled")
                break
            except Exception as e:
                self.logger.error(f"❌ Error in remote availability monitor: {e}")
                await asyncio.sleep(30)
    
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
    # MÉTODOS DE VERIFICACIÓN Y DEBUGGING
    # ===============================================
    
    async def get_verification_files_info(self) -> Dict[str, Any]:
        """
        Obtener información detallada de los archivos de verificación.
        """
        if not self.verification_enabled:
            return {
                "enabled": False,
                "message": "Audio verification is disabled"
            }
        
        try:
            if not self.verification_dir.exists():
                self.verification_dir.mkdir(exist_ok=True)
            
            verification_files = list(self.verification_dir.glob("verification_*.wav"))
            verification_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            files_info = []
            total_size = 0
            
            for file_path in verification_files:
                stat = file_path.stat()
                file_info = {
                    "filename": file_path.name,
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "age_hours": (datetime.now().timestamp() - stat.st_mtime) / 3600
                }
                files_info.append(file_info)
                total_size += stat.st_size
            
            return {
                "enabled": True,
                "directory": str(self.verification_dir),
                "total_files": len(files_info),
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "retention_days": self.verification_days,
                "max_files": self.verification_max_files,
                "files": files_info[:10],  # Solo los 10 más recientes para evitar respuestas muy grandes
                "showing_latest": min(10, len(files_info))
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting verification files info: {e}")
            return {
                "enabled": True,
                "error": str(e)
            }
    
    async def list_verification_files(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Listar archivos de verificación con información detallada.
        
        Args:
            limit: Número máximo de archivos a retornar
        """
        if not self.verification_enabled or not self.verification_dir.exists():
            return []
        
        try:
            verification_files = list(self.verification_dir.glob("verification_*.wav"))
            verification_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            files_list = []
            
            for file_path in verification_files[:limit]:
                stat = file_path.stat()
                
                # Intentar extraer información del nombre del archivo
                filename_parts = file_path.stem.split('_')
                original_info = {}
                if len(filename_parts) >= 6:  # verification_YYYYMMDD_HHMMSS_microsec_original_filename
                    try:
                        date_part = filename_parts[1]
                        time_part = filename_parts[2]
                        original_info = {
                            "capture_date": f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}",
                            "capture_time": f"{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}",
                            "original_filename": "_".join(filename_parts[4:])
                        }
                    except (IndexError, ValueError):
                        pass
                
                file_info = {
                    "filename": file_path.name,
                    "full_path": str(file_path),
                    "size_bytes": stat.st_size,
                    "size_kb": stat.st_size / 1024,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "age_hours": (datetime.now().timestamp() - stat.st_mtime) / 3600,
                    **original_info
                }
                
                files_list.append(file_info)
            
            return files_list
            
        except Exception as e:
            self.logger.error(f"❌ Error listing verification files: {e}")
            return []
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        Obtener estadísticas detalladas de procesamiento.
        """
        try:
            # Estadísticas básicas de la cola
            queue_stats = {
                "current_queue_size": len(self.processing_queue),
                "max_queue_size": self.max_queue_size,
                "is_processing": self.is_processing,
                "remote_available": self.remote_available
            }
            
            # Análisis de la cola actual
            if self.processing_queue:
                sizes = [entry.get("size_bytes", 0) for entry in self.processing_queue]
                queue_analysis = {
                    "total_queue_size_bytes": sum(sizes),
                    "average_file_size_bytes": sum(sizes) / len(sizes),
                    "min_file_size_bytes": min(sizes) if sizes else 0,
                    "max_file_size_bytes": max(sizes) if sizes else 0,
                    "oldest_entry_age_seconds": self._calculate_entry_age(self.processing_queue[0]) if self.processing_queue else 0,
                    "newest_entry_age_seconds": self._calculate_entry_age(self.processing_queue[-1]) if self.processing_queue else 0
                }
            else:
                queue_analysis = {
                    "total_queue_size_bytes": 0,
                    "average_file_size_bytes": 0,
                    "min_file_size_bytes": 0,
                    "max_file_size_bytes": 0,
                    "oldest_entry_age_seconds": 0,
                    "newest_entry_age_seconds": 0
                }
            
            # Información de directorios
            temp_dir_stats = self._get_directory_stats(self.temp_dir)
            verification_dir_stats = self._get_directory_stats(self.verification_dir) if self.verification_enabled else {}
            
            return {
                "queue": queue_stats,
                "queue_analysis": queue_analysis,
                "directories": {
                    "temp": temp_dir_stats,
                    "verification": verification_dir_stats
                },
                "configuration": {
                    "verification_enabled": self.verification_enabled,
                    "verification_retention_days": self.verification_days if self.verification_enabled else None,
                    "verification_max_files": self.verification_max_files if self.verification_enabled else None
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting processing statistics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _calculate_entry_age(self, entry: Dict[str, Any]) -> float:
        """Calcular la edad de una entrada en segundos"""
        try:
            received_at = datetime.fromisoformat(entry.get("received_at", datetime.now().isoformat()))
            return (datetime.now() - received_at).total_seconds()
        except Exception:
            return 0.0
    
    def _get_directory_stats(self, directory: Path) -> Dict[str, Any]:
        """Obtener estadísticas de un directorio"""
        try:
            if not directory.exists():
                return {"exists": False}
            
            files = list(directory.glob("*"))
            if not files:
                return {"exists": True, "file_count": 0, "total_size_bytes": 0}
            
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            
            return {
                "exists": True,
                "path": str(directory),
                "file_count": len([f for f in files if f.is_file()]),
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "free_space_bytes": self._get_free_space(directory)
            }
            
        except Exception as e:
            return {"exists": True, "error": str(e)}
    
    def _get_free_space(self, directory: Path) -> int:
        """Obtener espacio libre en el directorio"""
        try:
            import shutil
            total, used, free = shutil.disk_usage(directory)
            return free
        except Exception:
            return -1

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
