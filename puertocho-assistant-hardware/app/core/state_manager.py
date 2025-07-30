import logging
from enum import Enum, auto
from typing import Optional, List
import numpy as np
from datetime import datetime
import asyncio

class AssistantState(Enum):
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    SPEAKING = auto()
    ERROR = auto()

class StateManager:
    """
    Orquesta el flujo de la aplicación y gestiona los estados principales.
    Captura audio durante LISTENING y lo prepara para enviar al backend.
    """
    def __init__(self, led_controller=None, vad_handler=None):
        self.state = AssistantState.IDLE
        self.led_controller = led_controller
        self.vad_handler = vad_handler
        self.websocket_client = None  # Se asignará desde main.py
        self.logger = logging.getLogger("state_manager")
        self.captured_audio_buffer: List[np.ndarray] = []
        self.listening_start_time: Optional[float] = None
        self._event_loop = None  # Se asignará desde HardwareService
        
        # Integrar callbacks de VAD si está presente
        if self.vad_handler:
            self.vad_handler.on_voice_start = self.on_voice_start
            self.vad_handler.on_voice_end = self.on_voice_end
            self.vad_handler.on_audio_captured = self.on_audio_captured
            self.logger.info("✅ VAD callbacks successfully connected")
        else:
            self.logger.warning("⚠️ VAD handler not provided")

    def set_state(self, new_state):
        if self.state != new_state:
            self.logger.info(f"State change: {self.state.name} -> {new_state.name}")
            old_state = self.state
            self.state = new_state
            
            # Acciones específicas por transición
            if new_state == AssistantState.LISTENING:
                self.listening_start_time = datetime.now().timestamp()
                self.captured_audio_buffer = []
                if self.vad_handler:
                    self.vad_handler.reset()
                    self.logger.info("🎙️ Started listening for user speech - VAD reset completed")
                else:
                    self.logger.warning("⚠️ VAD handler not available for listening state")
            
            elif old_state == AssistantState.LISTENING and new_state == AssistantState.IDLE:
                self.logger.info("⏹️ Stopped listening, returning to idle")
            
            # Sincronizar LEDs
            if self.led_controller:
                led_state_mapping = {
                    AssistantState.IDLE: "IDLE",
                    AssistantState.LISTENING: "LISTENING", 
                    AssistantState.PROCESSING: "PROCESSING",
                    AssistantState.SPEAKING: "SPEAKING",
                    AssistantState.ERROR: "ERROR"
                }
                led_state = led_state_mapping.get(new_state)
                if led_state:
                    from core.led_controller import LEDState
                    led_enum_value = getattr(LEDState, led_state, LEDState.IDLE)
                    self.led_controller.set_state(led_enum_value)

    def handle_audio_chunk(self, audio_bytes, timestamp=None):
        """
        Recibe audio y lo distribuye según el estado actual.
        """
        if self.state == AssistantState.LISTENING:
            # Capturar todo el audio durante LISTENING
            if isinstance(audio_bytes, np.ndarray):
                self.captured_audio_buffer.append(audio_bytes.copy())
                self.logger.debug(f"📊 Added audio chunk to buffer, total chunks: {len(self.captured_audio_buffer)}")
            
            # Procesar con VAD
            if self.vad_handler:
                self.logger.debug("🔍 Sending audio to VAD handler")
                self.vad_handler.process_audio_chunk(audio_bytes, timestamp)
            else:
                self.logger.warning("⚠️ VAD handler not available")
        
        elif self.state == AssistantState.IDLE:
            # En IDLE no procesamos audio (wake word se maneja en main.py)
            pass

    def on_voice_start(self, timestamp):
        """Callback cuando VAD detecta inicio de voz"""
        self.logger.info(f"🗣️ User started speaking at {timestamp}")
        # Mantenerse en LISTENING para seguir capturando

    def on_voice_end(self, timestamp):
        """Callback cuando VAD detecta fin de voz"""
        self.logger.info(f"🤐 User stopped speaking at {timestamp}")
        # Cambiar a PROCESSING para procesar el audio
        self.set_state(AssistantState.PROCESSING)
        
        # Procesar y enviar audio al backend
        import asyncio
        import threading
        
        try:
            # Usar el event loop almacenado si está disponible
            if self._event_loop and not self._event_loop.is_closed():
                self._event_loop.call_soon_threadsafe(self._schedule_audio_processing_task)
            else:
                # Intentar obtener el event loop actual
                loop = asyncio.get_running_loop()
                loop.call_soon_threadsafe(self._schedule_audio_processing_task)
        except RuntimeError:
            # No hay event loop, usar thread separado
            self.logger.warning("No event loop available, using thread-safe workaround")
            threading.Thread(target=self._process_audio_sync, daemon=True).start()

    def on_audio_captured(self, audio_data: np.ndarray, sample_rate: int):
        """Callback cuando VAD ha capturado audio completo"""
        # Imports necesarios al inicio
        import os
        from datetime import datetime
        
        duration = len(audio_data) / sample_rate
        self.logger.info(f"📼 Received captured audio: {duration:.2f}s at {sample_rate}Hz")
        
        # Guardar para enviar al backend
        self.captured_audio_for_backend = {
            "audio_data": audio_data,
            "sample_rate": sample_rate,
            "duration": duration,
            "timestamp": datetime.now().timestamp()
        }
        
        # Guardar localmente para debug
        os.makedirs("/app/captured_audio", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/app/captured_audio/captured_{timestamp}.wav"
        
        # Guardar usando el audio recibido directamente
        if audio_data is not None and len(audio_data) > 0:
            # Convertir a int16 para WAV
            import io
            import wave
            
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            # Crear WAV en memoria
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_int16.tobytes())
            
            wav_bytes = wav_buffer.getvalue()
            
            # Guardar a archivo para debug
            with open(filename, 'wb') as f:
                f.write(wav_bytes)
            
            self.logger.info(f"💾 Saved captured audio to {filename}")
            # Guardar los bytes WAV para envío al backend
            self.captured_audio_for_backend["wav_bytes"] = wav_bytes
        else:
            self.logger.warning("⚠️ No audio data to save")

    async def _process_audio_and_send_to_backend(self):
        """Procesa y envía el audio capturado al backend"""
        try:
            self.logger.info("🔄 Processing and sending audio to backend...")
            
            if not hasattr(self, 'captured_audio_for_backend') or not self.captured_audio_for_backend:
                self.logger.warning("No captured audio available to send")
                self.set_state(AssistantState.IDLE)
                return
            
            # Verificar si tenemos WebSocket client
            if not self.websocket_client:
                self.logger.error("❌ WebSocket client not available, cannot send audio")
                self.set_state(AssistantState.IDLE)
                return
            
            # Preparar datos para envío
            audio_info = self.captured_audio_for_backend
            
            # Convertir audio a base64 para envío por WebSocket
            import base64
            audio_b64 = base64.b64encode(audio_info["wav_bytes"]).decode('utf-8')
            
            # Crear mensaje para el backend
            message_data = {
                "audio_data": audio_b64,
                "audio_format": "wav",
                "sample_rate": audio_info["sample_rate"],
                "duration": audio_info["duration"],
                "timestamp": audio_info["timestamp"]
            }
            
            # Enviar audio al backend vía WebSocket
            from api.websocket_client import MessageType
            await self.websocket_client.send_message(MessageType.AUDIO_CAPTURED, message_data)
            
            self.logger.info(f"✅ Audio sent to backend: {audio_info['duration']:.2f}s")
            
            # Simular tiempo de procesamiento mientras esperamos respuesta
            await asyncio.sleep(1)
            
        except Exception as e:
            self.logger.error(f"❌ Error processing/sending audio: {e}")
        finally:
            # Volver a IDLE después del procesamiento
            self.set_state(AssistantState.IDLE)

    def _schedule_audio_processing_task(self):
        """Programa la tarea de procesamiento de audio en el event loop"""
        import asyncio
        asyncio.create_task(self._process_audio_and_send_to_backend())

    def _process_audio_sync(self):
        """Versión síncrona del procesamiento de audio"""
        import time
        import asyncio
        self.logger.info("🔄 Processing audio (sync mode)...")
        
        try:
            if hasattr(self, 'captured_audio_for_backend') and self.captured_audio_for_backend:
                audio_info = self.captured_audio_for_backend
                self.logger.info(f"📤 Would send {audio_info['duration']:.2f}s audio to backend")
            else:
                self.logger.warning("No captured audio available")
        except Exception as e:
            self.logger.error(f"Error in sync audio processing: {e}")
        
        time.sleep(1)  # Simular procesamiento
        self.logger.info("✅ Audio processing complete (sync mode)")
        
        # Intentar cambiar estado de forma thread-safe
        try:
            if self._event_loop and not self._event_loop.is_closed():
                self._event_loop.call_soon_threadsafe(self.set_state, AssistantState.IDLE)
            else:
                loop = asyncio.get_running_loop()
                loop.call_soon_threadsafe(self.set_state, AssistantState.IDLE)
        except RuntimeError:
            self.logger.warning("No event loop available for state change, using direct call")
            self.set_state(AssistantState.IDLE)

    async def _simulate_processing(self):
        """Simula procesamiento del audio (mantener para compatibilidad)"""
        import asyncio
        self.logger.info("🔄 Simulating audio processing...")
        await asyncio.sleep(2)  # Simular procesamiento
        self.logger.info("✅ Processing complete")
        self.set_state(AssistantState.IDLE)

    def _schedule_processing_task(self):
        """Programa la tarea de procesamiento en el event loop (mantener para compatibilidad)"""
        import asyncio
        asyncio.create_task(self._simulate_processing())

    def _simulate_processing_sync(self):
        """Versión síncrona de simulación de procesamiento (mantener para compatibilidad)"""
        import time
        import asyncio
        self.logger.info("🔄 Simulating audio processing (sync mode)...")
        time.sleep(2)  # Simular procesamiento
        self.logger.info("✅ Processing complete (sync mode)")
        
        # Intentar cambiar estado de forma thread-safe
        try:
            # Usar el event loop almacenado si está disponible
            if self._event_loop and not self._event_loop.is_closed():
                self._event_loop.call_soon_threadsafe(self.set_state, AssistantState.IDLE)
            else:
                # Intentar obtener el event loop actual
                loop = asyncio.get_running_loop()
                loop.call_soon_threadsafe(self.set_state, AssistantState.IDLE)
        except RuntimeError:
            # Si no hay loop, cambiar directamente (puede no ser thread-safe pero es el fallback)
            self.logger.warning("No event loop available for state change, using direct call")
            self.set_state(AssistantState.IDLE)

    def handle_button_press(self, press_type: str):
        """Maneja eventos de botón"""
        self.logger.info(f"🔘 Button {press_type} press detected")
        
        if press_type == "short":
            if self.state == AssistantState.IDLE:
                # Iniciar escucha manual
                self.set_state(AssistantState.LISTENING)
            elif self.state == AssistantState.LISTENING:
                # Detener escucha manual
                self.set_state(AssistantState.IDLE)
        
        elif press_type == "long":
            # Reiniciar o acción especial
            self.logger.info("Long press - resetting to IDLE")
            self.set_state(AssistantState.IDLE)
