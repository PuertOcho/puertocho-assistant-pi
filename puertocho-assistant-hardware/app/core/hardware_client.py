"""
Cliente de hardware simplificado para PuertoCho Assistant.
Solo se encarga de capturar audio y enviarlo al backend.
"""

import asyncio
import json
import os
import queue
import threading
import time
import wave
import io
import numpy as np
import requests
from typing import Optional, Dict, Any

# Importaciones condicionales para Raspberry Pi
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("⚠️ RPi.GPIO no disponible - LEDs y botón deshabilitados")

try:
    import pvporcupine
    PORCUPINE_AVAILABLE = True
except ImportError:
    PORCUPINE_AVAILABLE = False
    print("⚠️ Porcupine no disponible")

try:
    import sounddevice as sd
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("⚠️ sounddevice no disponible")

try:
    import webrtcvad
    VAD_AVAILABLE = True
except ImportError:
    VAD_AVAILABLE = False
    print("⚠️ webrtcvad no disponible")

from config import Config
from utils.logging_config import get_logger
from utils.led_controller import get_led_controller

logger = get_logger('hardware_client')

class HardwareState:
    """Estados del hardware"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    ERROR = "error"

def simple_resample(audio_data, original_rate, target_rate):
    """Resample simple usando interpolación lineal con precisión mejorada"""
    if original_rate == target_rate:
        return audio_data
    
    if len(audio_data) == 0:
        return audio_data
    
    # Calcular ratio de resample
    ratio = target_rate / original_rate
    
    # Número de muestras en el audio original y objetivo
    original_length = len(audio_data)
    target_length = int(np.round(original_length * ratio))
    
    if target_length <= 0:
        return np.array([], dtype=audio_data.dtype)
    
    # Crear índices para interpolación
    if target_length == 1:
        indices = np.array([original_length // 2])
    else:
        indices = np.linspace(0, original_length - 1, target_length)
    
    # Interpolar
    resampled = np.interp(indices, np.arange(original_length), audio_data)
    
    return resampled.astype(audio_data.dtype)

class HardwareClient:
    """Cliente de hardware simplificado"""
    
    def __init__(self, config: Config):
        self.config = config
        self.state = HardwareState.IDLE
        self.audio_queue = queue.Queue()
        self.should_stop = False
        self.button_pressed = False
        self.last_button_time = 0
        self.last_button_state = GPIO.HIGH if GPIO_AVAILABLE else True
        
        # Configuración de audio
        self.capture_rate = self.config.detect_supported_sample_rate()
        self.target_frame_length = 512  # Para Porcupine
        self.audio_buffer = np.array([], dtype=np.int16)
        
        # Inicializar componentes
        self.porcupine = None
        self.vad = None
        self.stream = None
        self.gpio_initialized = False
        self.led_controller = get_led_controller(brightness=8)  # LEDs RGB integrados
        
        logger.info(f"Inicializando cliente hardware con rate {self.capture_rate} Hz")
    
    async def initialize(self):
        """Inicializar todos los componentes"""
        try:
            # Inicializar GPIO
            if GPIO_AVAILABLE:
                await self._initialize_gpio()
            
            # Inicializar Porcupine
            if PORCUPINE_AVAILABLE:
                await self._initialize_porcupine()
            
            # Inicializar VAD
            if VAD_AVAILABLE:
                await self._initialize_vad()
            
            # Inicializar stream de audio
            if AUDIO_AVAILABLE:
                await self._initialize_audio_stream()
            
            logger.info("✅ Hardware inicializado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando hardware: {e}")
            raise
    
    async def _initialize_gpio(self):
        """Inicializar GPIO"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.config.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.config.led_idle_pin, GPIO.OUT)
            GPIO.setup(self.config.led_record_pin, GPIO.OUT)
            
            # LEDs iniciales
            GPIO.output(self.config.led_idle_pin, GPIO.HIGH)
            GPIO.output(self.config.led_record_pin, GPIO.LOW)
            
            self.gpio_initialized = True
            logger.info("✅ GPIO inicializado")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando GPIO: {e}")
            raise
    
    async def _initialize_porcupine(self):
        """Inicializar Porcupine"""
        try:
            if not self.config.porcupine_access_key:
                raise ValueError("PORCUPINE_ACCESS_KEY no configurada")
            
            self.porcupine = pvporcupine.create(
                access_key=self.config.porcupine_access_key,
                keyword_paths=[str(self.config.model_file)]
            )
            
            logger.info("✅ Porcupine inicializado")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Porcupine: {e}")
            raise
    
    async def _initialize_vad(self):
        """Inicializar VAD"""
        try:
            self.vad = webrtcvad.Vad(2)  # Agresividad media
            logger.info("✅ VAD inicializado")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando VAD: {e}")
            raise
    
    async def _initialize_audio_stream(self):
        """Inicializar stream de audio"""
        try:
            self.stream = sd.InputStream(
                samplerate=self.capture_rate,
                channels=1,
                dtype=np.int16,
                blocksize=self.config.chunk_size,
                device=self.config.audio_device_index,
                callback=self._audio_callback
            )
            
            logger.info("✅ Stream de audio inicializado")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando stream: {e}")
            raise
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback para procesar audio"""
        if status:
            logger.warning(f"Estado del audio: {status}")
        
        if not self.should_stop:
            self.audio_queue.put(indata.copy())
    
    def _set_state(self, new_state: str):
        """Cambiar estado del hardware"""
        if self.state != new_state:
            logger.info(f"Estado: {self.state} -> {new_state}")
            self.state = new_state
            
            # Actualizar LEDs GPIO externos
            if self.gpio_initialized:
                if new_state == HardwareState.IDLE:
                    GPIO.output(self.config.led_idle_pin, GPIO.HIGH)
                    GPIO.output(self.config.led_record_pin, GPIO.LOW)
                elif new_state == HardwareState.LISTENING:
                    GPIO.output(self.config.led_idle_pin, GPIO.LOW)
                    GPIO.output(self.config.led_record_pin, GPIO.HIGH)
                elif new_state == HardwareState.PROCESSING:
                    GPIO.output(self.config.led_idle_pin, GPIO.LOW)
                    GPIO.output(self.config.led_record_pin, GPIO.LOW)
            
            # Actualizar LEDs RGB integrados
            self.led_controller.set_state(new_state)
    
    def get_wake_words(self) -> list:
        """Obtener lista de wake words"""
        return ["Puerto-ocho"]
    
    async def run(self):
        """Ejecutar bucle principal"""
        try:
            # Iniciar stream de audio
            if self.stream:
                self.stream.start()
                logger.info("🎤 Stream de audio iniciado")
            
            # Enviar estado inicial al backend
            await self._send_hardware_status()
            
            # Bucle principal
            while not self.should_stop:
                await self._process_audio_buffer()
                await asyncio.sleep(0.01)  # 10ms
                
        except Exception as e:
            logger.error(f"❌ Error en bucle principal: {e}")
        finally:
            await self.stop()
    
    async def _process_audio_buffer(self):
        """Procesar buffer de audio para detección de wake word"""
        try:
            # Obtener audio de la cola
            if not self.audio_queue.empty():
                audio_data = self.audio_queue.get_nowait()
                pcm = np.frombuffer(audio_data, dtype=np.int16)
                
                # Resample si es necesario
                if self.capture_rate != 16000:
                    resampled_pcm = simple_resample(pcm, self.capture_rate, 16000)
                else:
                    resampled_pcm = pcm
                
                # Acumular en buffer
                self.audio_buffer = np.concatenate([self.audio_buffer, resampled_pcm])
                
                # Procesar frames completos
                while len(self.audio_buffer) >= self.target_frame_length:
                    frame = self.audio_buffer[:self.target_frame_length]
                    self.audio_buffer = self.audio_buffer[self.target_frame_length:]
                    
                    # Procesar con Porcupine
                    if self.porcupine:
                        keyword_index = self.porcupine.process(frame.astype(np.int16))
                        
                        if keyword_index >= 0:
                            logger.info("🎯 Wake word detectado!")
                            self.led_controller.wakeup()  # Efecto de activación
                            await self._handle_voice_command()
                            return
            
            # Verificar botón
            if self.button_pressed:
                self.button_pressed = False
                logger.info("🔘 Activación manual")
                await self._handle_voice_command()
                
        except queue.Empty:
            pass
        except Exception as e:
            logger.error(f"❌ Error procesando audio: {e}")
    
    async def _handle_voice_command(self):
        """Manejar comando de voz detectado"""
        try:
            self._set_state(HardwareState.LISTENING)
            
            # Grabar audio
            audio_bytes = await self._record_until_silence()
            if not audio_bytes:
                self._set_state(HardwareState.IDLE)
                return
            
            self._set_state(HardwareState.PROCESSING)
            
            # Crear WAV
            wav_bytes = self._create_wav_file(audio_bytes)
            
            # Enviar al backend
            success = await self._send_audio_to_backend(wav_bytes)
            
            if success:
                logger.info("✅ Audio enviado al backend correctamente")
            else:
                logger.error("❌ Error enviando audio al backend")
            
        except Exception as e:
            logger.error(f"❌ Error manejando comando: {e}")
        finally:
            self._set_state(HardwareState.IDLE)
    
    async def _record_until_silence(self) -> bytes:
        """Grabar audio hasta detectar silencio"""
        logger.info("🎤 Grabando audio...")
        frames = []
        silence_count = 0
        max_silence_frames = 40
        
        # Limpiar cola
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        
        # Grabar hasta silencio
        for _ in range(300):  # Máximo 6 segundos
            try:
                audio_data = self.audio_queue.get(timeout=0.1)
                frames.append(audio_data)
                
                # Detección de silencio simple
                pcm = np.frombuffer(audio_data, dtype=np.int16)
                if np.max(np.abs(pcm)) < 500:  # Umbral de silencio
                    silence_count += 1
                    if silence_count >= max_silence_frames:
                        break
                else:
                    silence_count = 0
                    
            except queue.Empty:
                silence_count += 1
                if silence_count >= max_silence_frames:
                    break
        
        if frames:
            logger.info(f"📝 Audio grabado: {len(frames)} frames")
            return b''.join(frames)
        else:
            logger.warning("⚠️ No se grabó audio")
            return b''
    
    def _create_wav_file(self, audio_bytes: bytes) -> bytes:
        """Crear archivo WAV a partir de datos de audio"""
        if not audio_bytes:
            return b''
        
        # Convertir a PCM
        pcm_data = np.frombuffer(audio_bytes, dtype=np.int16)
        
        # Crear archivo WAV en memoria
        wav_buffer = io.BytesIO()
        
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.capture_rate)
            wav_file.writeframes(pcm_data.tobytes())
        
        wav_buffer.seek(0)
        return wav_buffer.read()
    
    async def _send_audio_to_backend(self, wav_bytes: bytes) -> bool:
        """Enviar audio al backend"""
        if not wav_bytes:
            return False
        
        try:
            logger.info("🚀 Enviando audio al backend...")
            
            files = {'audio': ('audio.wav', wav_bytes, 'audio/wav')}
            
            response = requests.post(
                self.config.backend_audio_endpoint,
                files=files,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"✅ Respuesta del backend: {result}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando audio al backend: {e}")
            return False
    
    async def _send_hardware_status(self) -> bool:
        """Enviar estado del hardware al backend"""
        try:
            status = {
                "microphone_ok": AUDIO_AVAILABLE and self.stream is not None,
                "gpio_ok": self.gpio_initialized,
                "porcupine_ok": self.porcupine is not None,
                "vad_ok": self.vad is not None,
                "rgb_leds_ok": self.led_controller.is_enabled(),
                "state": self.state,
                "audio_config": self.config.get_audio_config()
            }
            
            response = requests.post(
                self.config.backend_hardware_status_endpoint,
                json=status,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            response.raise_for_status()
            logger.info("✅ Estado enviado al backend")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando estado al backend: {e}")
            return False
    
    async def stop(self):
        """Detener el cliente"""
        logger.info("🛑 Deteniendo cliente hardware...")
        self.should_stop = True
        
        # Detener stream
        if self.stream:
            self.stream.stop()
            self.stream.close()
        
        # Limpiar Porcupine
        if self.porcupine:
            self.porcupine.delete()
        
        # Limpiar LEDs RGB
        if self.led_controller:
            self.led_controller.cleanup()
        
        # Limpiar GPIO
        if self.gpio_initialized:
            GPIO.cleanup()
        
        logger.info("✅ Cliente hardware detenido")
