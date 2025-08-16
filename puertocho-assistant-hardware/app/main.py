#!/usr/bin/env python3
"""
🎙️ PuertoCho Voice Assistant - Hardware Service (Refactored)
Main entry point usando StateManager y EventBus refactorizados
"""

import asyncio
import sys
import signal
import time
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import config, validate_config
from utils.logger import logger, log_hardware_event

from core.led_controller import LEDController, LEDState
from core.state_manager import StateManager, AssistantState, create_state_manager_with_adapters
from core.event_bus import EventBus, EventType, EventMixin, event_handler
from core.vad_handler import VADHandler


class HardwareService(EventMixin):
    """
    Servicio principal refactorizado con EventBus y StateManager desacoplados.
    
    Responsabilidades:
    - Coordinación de componentes
    - Manejo de WebSocket (delegado desde StateManager)
    - Gestión del ciclo de vida del servicio
    """
    
    def __init__(self):
        self.running = False
        self.tasks = []
        # Inicializar el main_loop como None, se asignará en start()
        self.main_loop = None
        
        # Inicializar EventBus primero
        self.event_bus = EventBus(async_processing=True, max_queue_size=1000)
        
        # Inicializar EventMixin con el EventBus
        super().__init__(self.event_bus)
        
        # Componentes
        self.components = {}
        
        logger.info("HardwareService initialized with EventBus")

    async def start(self):
        """Start the hardware service"""
        try:
            # Asignar el event loop principal actual
            self.main_loop = asyncio.get_running_loop()
            
            # Validate configuration
            validate_config()
            log_hardware_event("service_starting", {"config_valid": True})
            
            # Initialize components
            await self._initialize_components()
            
            # Start main service loop
            self.running = True
            log_hardware_event("service_started", {"status": "ready"})
            
            # Notificar que el servicio está listo
            self.publish_event(EventType.COMPONENT_READY, {
                "component": "HardwareService",
                "components_count": len(self.components)
            })
            
            # Keep service running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Failed to start hardware service: {e}")
            self.publish_event(EventType.SYSTEM_ERROR, {
                "error": str(e),
                "phase": "startup"
            })
            raise
    
    async def stop(self):
        """Stop the hardware service"""
        log_hardware_event("service_stopping")
        self.running = False
        
        # Notificar shutdown
        self.publish_event(EventType.SHUTDOWN_REQUESTED, {
            "source": "HardwareService"
        })
        
        # Stop HTTP server
        if 'http_server_task' in self.components:
            self.components['http_server_task'].cancel()
        
        # Stop WebSocket client
        if 'websocket_client' in self.components:
            await self.components['websocket_client'].stop()
        
        # Stop components in reverse order
        if 'audio_manager' in self.components:
            self.components['audio_manager'].stop_recording()
            
        if 'wake_word_detector' in self.components:
            self.components['wake_word_detector'].stop()
            
        if 'led_controller' in self.components:
            self.components['led_controller'].set_state(LEDState.OFF)
            self.components['led_controller'].stop_animation()
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Shutdown EventBus
        self.event_bus.shutdown()
        
        log_hardware_event("service_stopped")
    
    async def _initialize_components(self):
        """Initialize hardware components with EventBus integration"""
        log_hardware_event("initializing_components")

        # 1. LED Controller
        self.components['led_controller'] = LEDController()
        self.components['led_controller'].start_animation()
        self.components['led_controller'].set_state(LEDState.IDLE)
        log_hardware_event("led_controller_initialized", {
            "num_leds": self.components['led_controller'].num_leds,
            "brightness": self.components['led_controller'].brightness
        })

        # 2. VAD Handler con callbacks configurados
        self.components['vad_handler'] = VADHandler(
            sample_rate=16000,  # WebRTC VAD requiere 16kHz
            input_sample_rate=config.audio.sample_rate,  # Audio del ReSpeaker (44.1kHz)
            frame_duration=config.vad.frame_duration,
            aggressiveness=config.vad.mode,
            silence_timeout=config.vad.silence_timeout
        )
        
        # Configurar callbacks del VAD
        self.components['vad_handler'].on_voice_start = self._on_voice_start_detected
        self.components['vad_handler'].on_voice_end = self._on_voice_end_detected
        
        log_hardware_event("vad_handler_initialized", {
            "target_sample_rate": 16000,
            "input_sample_rate": config.audio.sample_rate,
            "frame_duration": config.vad.frame_duration,
            "aggressiveness": config.vad.mode,
            "silence_timeout": config.vad.silence_timeout
        })

        # 3. StateManager refactorizado con adaptadores
        self.components['state_manager'] = create_state_manager_with_adapters(
            led_controller=self.components['led_controller'],
            vad_handler=self.components['vad_handler']
        )
        
        # Registrar callbacks para manejar cambios de estado
        self.components['state_manager'].register_state_callback(
            AssistantState.LISTENING, 
            self._on_listening_state_entered
        )
        self.components['state_manager'].register_state_callback(
            AssistantState.PROCESSING,
            self._on_processing_state_entered
        )
        
        log_hardware_event("state_manager_initialized", {
            "has_led_controller": self.components['led_controller'] is not None,
            "has_vad_handler": self.components['vad_handler'] is not None,
            "initial_state": self.components['state_manager'].get_current_state().name
        })

        # 4. Audio Manager
        from core.audio_manager import AudioManager
        self.components['audio_manager'] = AudioManager()
        log_hardware_event("audio_manager_initialized", {
            "sample_rate": config.audio.sample_rate,
            "channels": config.audio.channels,
            "device_name": config.audio.device_name
        })

        # 5. Wake Word Detector con callback refactorizado
        from core.wake_word_detector import WakeWordDetector
        self.components['wake_word_detector'] = WakeWordDetector(
            on_wake_word=self._on_wake_word_detected
        )
        self.components['wake_word_detector'].start()
        log_hardware_event("wake_word_detector_initialized", {
            "model_path": config.wake_word.model_path,
            "sensitivity": config.wake_word.sensitivity
        })

        # 6. Start audio recording con callback centralizado
        self.components['audio_manager'].start_recording(self._audio_callback)
        log_hardware_event("audio_recording_started")

        # 7. HTTP Server
        from api.http_server import HTTPServer
        self.components['http_server'] = HTTPServer(
            state_manager=self.components['state_manager'],
            audio_manager=self.components['audio_manager'],
            port=8080
        )
        
        # Start HTTP server asynchronously
        import uvicorn
        server_config = self.components['http_server'].start_async()
        self.components['http_server_task'] = asyncio.create_task(
            uvicorn.Server(uvicorn.Config(**server_config)).serve()
        )
        self.tasks.append(self.components['http_server_task'])
        
        log_hardware_event("http_server_initialized", {
            "port": 8080,
            "docs_url": "http://localhost:8080/docs"
        })
        
        # 8. WebSocket Client (ahora manejado por HardwareService)
        from api.websocket_client import WebSocketClient
        self.components['websocket_client'] = WebSocketClient(
            ws_url=config.backend.ws_url,
            reconnect_interval=5.0,
            max_reconnect_attempts=0  # Infinite reconnection attempts
        )
        
        # Start WebSocket connection
        self.components['websocket_task'] = asyncio.create_task(
            self.components['websocket_client'].start()
        )
        self.tasks.append(self.components['websocket_task'])
        
        log_hardware_event("websocket_client_initialized", {
            "backend_url": config.backend.ws_url
        })

        log_hardware_event("components_initialized")
    
    def _audio_callback(self, audio_data, frames, status):
        """
        Callback centralizado para procesar chunks de audio.
        Distribuye audio según el estado actual.
        """
        current_state = self.components['state_manager'].get_current_state()
        
        # Publicar evento de audio disponible
        self.publish_event(EventType.AUDIO_CHUNK_READY, {
            "size": len(audio_data) if hasattr(audio_data, '__len__') else 'unknown',
            "current_state": current_state.name,
            "frames": frames
        })
        
        # Distribución por estado
        if current_state == AssistantState.IDLE:
            # Solo wake word detection
            self.components['wake_word_detector'].process_audio_chunk(audio_data)
            
        elif current_state == AssistantState.LISTENING:
            # Wake word + VAD processing
            self.components['wake_word_detector'].process_audio_chunk(audio_data)
            
            # En LISTENING, también procesar VAD (ahora via callbacks)
            self.components['vad_handler'].process_audio_chunk(audio_data)
            
        # En otros estados, solo wake word para permitir interrupciones
        else:
            self.components['wake_word_detector'].process_audio_chunk(audio_data)
    
    def _on_voice_start_detected(self, timestamp):
        """Callback cuando el VAD detecta inicio de voz"""
        logger.info("🎤 Voice start detected by VAD")
        
        # Publicar evento de inicio de voz
        self.publish_event(EventType.VOICE_ACTIVITY_START, {
            "timestamp": timestamp,
            "current_state": self.components['state_manager'].get_current_state().name
        })
    
    def _on_voice_end_detected(self, timestamp):
        """Callback cuando el VAD detecta fin de voz"""
        logger.info("🔇 Voice end detected by VAD")
        logger.debug(f"DEBUG: Voice end timestamp: {timestamp}")
        
        # Cambiar a estado PROCESSING solo si estamos en LISTENING
        current_state = self.components['state_manager'].get_current_state()
        logger.debug(f"DEBUG: Current state: {current_state}")
        
        if current_state == AssistantState.LISTENING:
            
            # NUEVA FUNCIONALIDAD: Capturar audio completo y enviarlo al backend
            captured_audio = None
            logger.debug("DEBUG: Checking if audio_manager is available for capturing...")
            
            if 'audio_manager' in self.components:
                logger.debug("DEBUG: Calling stop_voice_capture()...")
                try:
                    captured_audio = self.components['audio_manager'].stop_voice_capture()
                    logger.debug(f"DEBUG: stop_voice_capture() returned: {captured_audio is not None}")
                    
                    if captured_audio is not None:
                        logger.info(f"🎙️ Captured {len(captured_audio)} audio samples")
                        
                        # Enviar audio al backend via WebSocket usando el event loop principal
                        try:
                            if self.main_loop and self.main_loop.is_running():
                                logger.debug("DEBUG: Scheduling audio send task...")
                                # Programar desde cualquier hilo usando call_soon_threadsafe
                                asyncio.run_coroutine_threadsafe(
                                    self._send_captured_audio_to_backend(captured_audio, timestamp), 
                                    self.main_loop
                                )
                                logger.debug("DEBUG: Audio send task scheduled successfully")
                            else:
                                logger.warning("Main event loop not available for sending audio")
                        except Exception as e:
                            logger.error(f"Failed to schedule audio sending: {e}")
                    else:
                        logger.warning("⚠️ No audio was captured during voice session")
                except Exception as e:
                    logger.error(f"ERROR calling stop_voice_capture(): {e}")
            else:
                logger.warning("⚠️ Audio manager not available for capturing")
            
            self.components['state_manager'].set_state(
                AssistantState.PROCESSING,
                {
                    "reason": "voice_end_detected", 
                    "timestamp": timestamp,
                    "audio_captured": captured_audio is not None,
                    "audio_samples": len(captured_audio) if captured_audio is not None else 0
                }
            )
            
            # Publicar evento de fin de voz
            self.publish_event(EventType.VOICE_ACTIVITY_END, {
                "timestamp": timestamp,
                "current_state": current_state.name,
                "audio_captured": captured_audio is not None
            })

    async def _send_captured_audio_to_backend(self, audio_data, voice_end_timestamp):
        """
        Envía el audio capturado al backend via WebSocket.
        
        Args:
            audio_data (np.ndarray): Audio capturado
            voice_end_timestamp (float): Timestamp del fin de voz
        """
        try:
            import base64
            import numpy as np
            import wave
            from pathlib import Path
            from datetime import datetime
            
            # NUEVO: Guardar copia local para verificación
            await self._save_audio_copy_for_verification(audio_data, voice_end_timestamp)
            
            # Convertir numpy array a bytes
            if isinstance(audio_data, np.ndarray):
                # Asegurar que está en formato int16 para mejor compresión
                if audio_data.dtype != np.int16:
                    # Normalizar y convertir a int16
                    audio_normalized = np.clip(audio_data, -1.0, 1.0)
                    audio_int16 = (audio_normalized * 32767).astype(np.int16)
                else:
                    audio_int16 = audio_data
                
                # Convertir a bytes y luego a base64
                audio_bytes = audio_int16.tobytes()
                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                
                # Preparar metadata del audio
                audio_metadata = {
                    "sample_rate": self.components['audio_manager'].sample_rate,
                    "channels": self.components['audio_manager'].channels,
                    "samples": len(audio_int16),
                    "duration_seconds": len(audio_int16) / self.components['audio_manager'].sample_rate,
                    "format": "int16",
                    "voice_end_timestamp": voice_end_timestamp
                }
                
                # Enviar via WebSocket
                if 'websocket_client' in self.components:
                    from api.websocket_client import MessageType
                    
                    success = await self.components['websocket_client'].send_message(
                        MessageType.AUDIO_CAPTURED,
                        {
                            "audio_data": audio_base64,
                            "metadata": audio_metadata,
                            "capture_session": {
                                "start_timestamp": self.components['audio_manager'].capture_start_time,
                                "end_timestamp": voice_end_timestamp,
                                "wake_word_detected": True
                            }
                        }
                    )
                    
                    if success:
                        logger.info(f"✅ Audio sent to backend: {audio_metadata['duration_seconds']:.2f}s, {len(audio_base64)} bytes")
                        log_hardware_event("audio_sent_to_backend", {
                            "duration_seconds": audio_metadata['duration_seconds'],
                            "size_bytes": len(audio_base64),
                            "sample_rate": audio_metadata['sample_rate'],
                            "channels": audio_metadata['channels']
                        })
                    else:
                        logger.error("❌ Failed to send audio to backend")
                        log_hardware_event("audio_send_failed", {
                            "reason": "websocket_send_failed",
                            "audio_duration": audio_metadata['duration_seconds']
                        })
                else:
                    logger.error("❌ WebSocket client not available")
                    log_hardware_event("audio_send_failed", {
                        "reason": "websocket_client_unavailable"
                    })
                    
            else:
                logger.error("❌ Invalid audio data format")
                log_hardware_event("audio_send_failed", {
                    "reason": "invalid_audio_format",
                    "data_type": type(audio_data).__name__
                })
                
        except Exception as e:
            logger.error(f"❌ Error sending audio to backend: {e}")
            log_hardware_event("audio_send_failed", {
                "reason": "exception",
                "error": str(e)
            })
            self.publish_event(EventType.VOICE_ACTIVITY_END, {
                "timestamp": timestamp,
                "previous_state": current_state.name
            })
            
            # Programar retorno a IDLE usando el event loop principal
            try:
                if self.main_loop and self.main_loop.is_running():
                    # Programar desde cualquier hilo usando run_coroutine_threadsafe
                    asyncio.run_coroutine_threadsafe(self._return_to_idle_after_processing(), self.main_loop)
                else:
                    logger.warning("Main event loop not available for return to idle")
            except Exception as e:
                logger.warning(f"Could not schedule return to idle: {e}")
        else:
            logger.debug(f"Voice end detected but not in LISTENING state (current: {current_state.name})")
    
    async def _save_audio_copy_for_verification(self, audio_data, voice_end_timestamp):
        """
        Guarda una copia local del audio capturado para verificación.
        
        Args:
            audio_data (np.ndarray): Audio capturado
            voice_end_timestamp (float): Timestamp del fin de voz
        """
        try:
            from pathlib import Path
            from datetime import datetime
            import wave
            import numpy as np
            
            # Crear directorio de audio capturado
            captured_audio_dir = Path("/app/captured_audio")
            captured_audio_dir.mkdir(exist_ok=True)
            
            # Generar nombre de archivo con timestamp
            timestamp_str = datetime.fromtimestamp(voice_end_timestamp).strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"captured_voice_{timestamp_str}.wav"
            filepath = captured_audio_dir / filename
            
            # Convertir audio para guardado
            if audio_data.dtype != np.int16:
                # Normalizar y convertir a int16
                audio_normalized = np.clip(audio_data, -1.0, 1.0)
                audio_int16 = (audio_normalized * 32767).astype(np.int16)
            else:
                audio_int16 = audio_data
            
            # Guardar como archivo WAV
            sample_rate = self.components['audio_manager'].sample_rate
            channels = self.components['audio_manager'].channels
            
            with wave.open(str(filepath), 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(2)  # 2 bytes = 16 bits
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_int16.tobytes())
            
            duration_seconds = len(audio_int16) / (sample_rate * channels)
            file_size_kb = filepath.stat().st_size / 1024
            
            logger.info(f"💾 Audio copy saved: {filename}")
            logger.info(f"   📁 Path: {filepath}")
            logger.info(f"   ⏱️  Duration: {duration_seconds:.2f}s")
            logger.info(f"   📊 Size: {file_size_kb:.1f} KB")
            logger.info(f"   🎵 Format: {sample_rate}Hz, {channels}ch, 16-bit")
            
            log_hardware_event("audio_copy_saved", {
                "filename": filename,
                "path": str(filepath),
                "duration_seconds": duration_seconds,
                "size_kb": file_size_kb,
                "sample_rate": sample_rate,
                "channels": channels
            })
            
        except Exception as e:
            logger.error(f"❌ Error saving audio copy: {e}")
    
    async def _return_to_idle_after_processing(self, delay_seconds: float = 3.0):
        """Vuelve al estado IDLE después de un delay (simulando procesamiento)"""
        await asyncio.sleep(delay_seconds)
        
        # Solo cambiar a IDLE si sigue en PROCESSING
        if self.components['state_manager'].is_in_state(AssistantState.PROCESSING):
            logger.info("🔄 Returning to IDLE after processing timeout")
            self.components['state_manager'].set_state(
                AssistantState.IDLE,
                {"reason": "processing_completed"}
            )
    
    def _process_vad_audio(self, audio_data):
        """
        Método legacy - ya no se usa, el VAD funciona via callbacks.
        Mantenido por compatibilidad temporal.
        """
        # Este método ya no se usa, el VAD funciona via callbacks
        pass
    
    def _on_wake_word_detected(self, event):
        """Callback refactorizado para wake word detection"""
        logger.info("🚨 _on_wake_word_detected() function ENTRY")
        logger.info(f"🎙️ Wake word detected on channel {event.channel}!")
        
        # NUEVA FUNCIONALIDAD: Iniciar captura de audio post-wake word
        capture_started = False
        logger.info("INFO: Checking if audio_manager is available...")
        
        if 'audio_manager' in self.components:
            logger.info("INFO: audio_manager found, calling start_voice_capture()...")
            try:
                capture_started = self.components['audio_manager'].start_voice_capture()
                logger.info(f"INFO: start_voice_capture() returned: {capture_started}")
                
                if capture_started:
                    logger.info("🎤 Started voice capture after wake word detection")
                else:
                    logger.warning("⚠️ Failed to start voice capture")
            except Exception as e:
                logger.error(f"ERROR calling start_voice_capture(): {e}")
        else:
            logger.warning("⚠️ Audio manager not available for voice capture")
        
        logger.info("🚨 _on_wake_word_detected() function BEFORE state change")
        
        # Cambiar a estado LISTENING usando StateManager
        self.components['state_manager'].set_state(
            AssistantState.LISTENING,
            {
                "wake_word_channel": event.channel,
                "wake_word_index": event.keyword_index,
                "detection_timestamp": event.timestamp,
                "voice_capture_started": capture_started
            }
        )

        logger.info("🚨 _on_wake_word_detected() function AFTER state change")

        # Publicar evento
        self.publish_event(EventType.WAKE_WORD_DETECTED, {
            "channel": event.channel,
            "keyword_index": event.keyword_index,
            "timestamp": event.timestamp
        })

        log_hardware_event("wake_word_detected", {
            "channel": event.channel,
            "keyword_index": event.keyword_index,
            "timestamp": event.timestamp
        })
        
        logger.info("🚨 _on_wake_word_detected() function EXIT")
    
    def _on_listening_state_entered(self, event):
        """Callback cuando entra en estado LISTENING"""
        logger.info("📝 Entered LISTENING state - preparing for voice capture")
        
        # Reset VAD para nueva captura
        if 'vad_handler' in self.components:
            self.components['vad_handler'].reset()
        
        # NUEVA FUNCIONALIDAD: Programar timeout para captura de voz
        # En caso de que VAD no detecte fin de voz, forzar fin después de timeout
        try:
            if self.main_loop and self.main_loop.is_running():
                # Timeout de 30 segundos para captura de voz
                asyncio.run_coroutine_threadsafe(
                    self._voice_capture_timeout(30.0), 
                    self.main_loop
                )
            else:
                logger.warning("Main event loop not available for voice capture timeout")
        except Exception as e:
            logger.warning(f"Could not schedule voice capture timeout: {e}")
        
        # Publicar evento
        self.publish_event(EventType.VOICE_ACTIVITY_START, {
            "previous_state": event.previous_state.name,
            "context": event.context
        })
    
    def _on_processing_state_entered(self, event):
        """Callback cuando entra en estado PROCESSING"""
        logger.info("⚙️ Entered PROCESSING state - waiting for backend response")
        
        # Programar timeout para volver a IDLE si no hay respuesta
        # Usar el event loop principal guardado en self.main_loop
        try:
            if self.main_loop and self.main_loop.is_running():
                # Programar desde cualquier hilo usando call_soon_threadsafe
                asyncio.run_coroutine_threadsafe(self._processing_timeout(), self.main_loop)
            else:
                logger.warning("Main event loop not available for processing timeout")
        except Exception as e:
            logger.warning(f"Could not schedule processing timeout: {e}")
    
    async def _processing_timeout(self, timeout_seconds: float = 10.0):
        """Timeout para estado PROCESSING"""
        await asyncio.sleep(timeout_seconds)
        
        # Si sigue en PROCESSING, volver a IDLE
        if self.components['state_manager'].is_in_state(AssistantState.PROCESSING):
            logger.warning("Processing timeout reached, returning to IDLE")
            self.components['state_manager'].set_state(
                AssistantState.IDLE,
                {"reason": "processing_timeout"}
            )

    async def _voice_capture_timeout(self, timeout_seconds: float = 30.0):
        """
        Timeout para captura de voz cuando VAD no detecta fin.
        
        Args:
            timeout_seconds: Tiempo máximo de espera antes de forzar fin de captura
        """
        await asyncio.sleep(timeout_seconds)
        
        # Si sigue en LISTENING, forzar fin de captura
        current_state = self.components['state_manager'].get_current_state()
        if current_state == AssistantState.LISTENING:
            logger.warning(f"Voice capture timeout reached ({timeout_seconds}s), forcing end of capture")
            
            # Simular detección de fin de voz con timestamp actual
            self._on_voice_end_detected(time.time())
            
            log_hardware_event("voice_capture_timeout", {
                "timeout_seconds": timeout_seconds,
                "forced_end": True
            })
    
    # Event handlers usando decorador
    @event_handler(EventType.WEBSOCKET_CONNECTED)
    def _on_websocket_connected(self, event):
        """Handler para conexión WebSocket"""
        logger.info("🔗 WebSocket connected to backend")
        log_hardware_event("websocket_connected", {"backend_url": event.data.get("url")})
    
    @event_handler(EventType.WEBSOCKET_DISCONNECTED)
    def _on_websocket_disconnected(self, event):
        """Handler para desconexión WebSocket"""
        logger.warning("🔌 WebSocket disconnected from backend")
        log_hardware_event("websocket_disconnected", {"reason": event.data.get("reason")})
    
    @event_handler(EventType.MESSAGE_FROM_BACKEND)
    def _on_message_from_backend(self, event):
        """Handler para mensajes del backend"""
        message_type = event.data.get("type", "unknown")
        logger.info(f"📥 Message from backend: {message_type}")
        
        if message_type == "response":
            # Respuesta del backend, cambiar a SPEAKING o IDLE
            self.components['state_manager'].set_state(
                AssistantState.IDLE,  # Por ahora, directo a IDLE
                {"reason": "backend_response", "response_type": message_type}
            )
    
    @event_handler(EventType.SYSTEM_ERROR)
    def _on_system_error(self, event):
        """Handler para errores del sistema"""
        error_msg = event.data.get("error", "Unknown error")
        context = event.data.get("context", "")
        
        logger.error(f"💥 System error: {error_msg} (context: {context})")
        
        # En caso de error crítico, volver a IDLE
        if self.components['state_manager'].get_current_state() != AssistantState.IDLE:
            self.components['state_manager'].set_state(
                AssistantState.IDLE,
                {"reason": "system_error", "error": error_msg}
            )


def setup_signal_handlers(service: HardwareService):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(service.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main function"""
    logger.info("Starting PuertoCho Assistant Hardware Service (Refactored)")
    
    service = HardwareService()
    setup_signal_handlers(service)
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Service failed: {e}")
        sys.exit(1)
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
