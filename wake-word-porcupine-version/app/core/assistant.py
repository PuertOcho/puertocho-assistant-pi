"""
Lógica principal del asistente de voz PuertoCho.
"""

import asyncio
import json
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

from ..config import config
from ..utils.logging_config import get_logger
from ..api.client import BackendClient

logger = get_logger('assistant')

class AssistantState:
    """Estados del asistente"""
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

class VoiceAssistant:
    """Asistente de voz principal"""
    
    def __init__(self):
        self.state = AssistantState.IDLE
        self.audio_queue = queue.Queue()
        self.should_stop = False
        self.button_pressed = False
        self.last_button_time = 0
        self.last_button_state = GPIO.HIGH if GPIO_AVAILABLE else True
        
        # Buffer para acumular audio para Porcupine (512 frames exactos)
        self.audio_buffer = np.array([], dtype=np.int16)
        self.target_frame_length = 512  # Porcupine requiere exactamente 512 frames
        
        # Gestión de sesión conversacional
        self.session_id = None
        self.use_assistant_api = True  # Preferir API del asistente
        
        # Detectar tasa de muestreo soportada
        self.capture_rate = config.detect_supported_sample_rate()
        self.chunk_size = 512 if self.capture_rate == 16000 else int(512 * (self.capture_rate / 16000))
        
        # Cliente del backend
        self.backend_client = BackendClient(config.backend_websocket_url)
        self.backend_client.set_message_callback(self._handle_backend_message)
        
        # Inicialización
        self._verify_dependencies()
        self._load_commands()
        self._setup_gpio()
        self._setup_vad()
        self._setup_porcupine()
        self._verify_services()
        
        # Iniciar hilo para monitorear botón
        if GPIO_AVAILABLE:
            self.button_thread = threading.Thread(target=self._monitor_button, daemon=True)
            self.button_thread.start()
        
        logger.info("✅ Asistente inicializado correctamente")
        self._print_configuration()
    
    def _verify_dependencies(self):
        """Verificar dependencias críticas"""
        if not PORCUPINE_AVAILABLE:
            raise RuntimeError("❌ Porcupine no disponible - instala pvporcupine")
        
        if not AUDIO_AVAILABLE:
            raise RuntimeError("❌ Audio no disponible - instala sounddevice")
        
        if not config.porcupine_access_key:
            raise ValueError("❌ PORCUPINE_ACCESS_KEY no configurada")
    
    def _load_commands(self):
        """Cargar comandos desde archivo JSON"""
        try:
            with open(config.commands_file) as f:
                self.commands = json.load(f)
            logger.info(f"✅ Comandos cargados desde {config.commands_file}")
        except Exception as e:
            logger.warning(f"⚠️ No se pudieron cargar comandos: {e}")
            self.commands = {}
    
    def _setup_gpio(self):
        """Configurar pines GPIO con cleanup robusto"""
        if not GPIO_AVAILABLE:
            logger.warning("GPIO no disponible - LEDs y botón deshabilitados")
            return
        
        logger.info("🔧 Configurando GPIO...")
        
        # Deshabilitar advertencias de GPIO
        GPIO.setwarnings(False)
        
        # Cleanup inicial para liberar cualquier configuración previa
        try:
            GPIO.cleanup()
        except:
            pass
        
        # Configurar modo GPIO
        GPIO.setmode(GPIO.BCM)
        
        try:
            # Configurar pines
            GPIO.setup(config.led_idle_pin, GPIO.OUT)
            GPIO.setup(config.led_record_pin, GPIO.OUT)
            GPIO.setup(config.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Estado inicial: LED verde encendido
            GPIO.output(config.led_idle_pin, GPIO.HIGH)
            GPIO.output(config.led_record_pin, GPIO.LOW)
            
            logger.info("✅ GPIO configurado correctamente")
            
        except Exception as e:
            logger.warning(f"⚠️ Warning configurando GPIO: {e}")
    
    def _setup_vad(self):
        """Inicializar VAD (Voice Activity Detection)"""
        if VAD_AVAILABLE:
            self.vad = webrtcvad.Vad(2)  # Agresividad media
            logger.info("✅ VAD inicializado")
        else:
            self.vad = None
            logger.warning("⚠️ VAD no disponible")
    
    def _setup_porcupine(self):
        """Inicializar Porcupine con modelo personalizado"""
        logger.info("🔧 Inicializando Porcupine...")
        
        try:
            # Método 1: Intentar con modelo personalizado y parámetros en español
            if config.model_file.exists() and config.params_file.exists():
                try:
                    self.porcupine = pvporcupine.create(
                        access_key=config.porcupine_access_key,
                        keyword_paths=[str(config.model_file)],
                        model_path=str(config.params_file)
                    )
                    logger.info(f"✅ Porcupine inicializado con modelo personalizado")
                    logger.info(f"🎯 Wake words: Hola Puertocho, Oye Puertocho")
                    return
                except Exception as e:
                    logger.warning(f"⚠️ Error con modelo personalizado: {e}")
            
            # Método 2: Solo modelo personalizado sin parámetros
            if config.model_file.exists():
                try:
                    self.porcupine = pvporcupine.create(
                        access_key=config.porcupine_access_key,
                        keyword_paths=[str(config.model_file)]
                    )
                    logger.info(f"✅ Porcupine inicializado con modelo personalizado (sin parámetros)")
                    return
                except Exception as e:
                    logger.warning(f"⚠️ Error con modelo personalizado sin parámetros: {e}")
            
            # Método 3: Fallback a keywords genéricos en inglés
            logger.info("🔄 Usando keywords genéricos como fallback...")
            self.porcupine = pvporcupine.create(
                access_key=config.porcupine_access_key,
                keywords=['hey google', 'alexa']  # Keywords genéricos
            )
            logger.info("✅ Porcupine inicializado con keywords genéricos (hey google, alexa)")
            logger.warning("💡 NOTA: Usar 'Hey Google' o 'Alexa' para activar el asistente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Porcupine: {e}")
            raise RuntimeError("No se pudo inicializar Porcupine con ninguna configuración")
    
    def _verify_services(self):
        """Verificar que los servicios estén disponibles"""
        logger.info("🔄 Verificando servicios disponibles...")
        
        # 1. Intentar verificar el asistente conversacional (prioritario)
        try:
            health_url = config.assistant_chat_url.replace('/chat', '/health')
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                logger.info("✅ Asistente conversacional disponible")
                self.use_assistant_api = True
                return
        except Exception as e:
            logger.warning(f"⚠️ Asistente conversacional no disponible: {e}")
        
        # 2. Fallback: Verificar servicio de transcripción directo
        try:
            logger.info("🔄 Intentando con servicio de transcripción directo...")
            health_url = config.transcription_service_url.replace('/transcribe', '/health')
            response = requests.get(health_url, timeout=5)
            logger.info("✅ Servicio de transcripción directo disponible")
            self.use_assistant_api = False
        except Exception as e:
            logger.warning(f"⚠️ Servicio de transcripción no disponible: {e}")
            self.use_assistant_api = False
    
    def _print_configuration(self):
        """Imprimir configuración actual"""
        logger.info("=" * 60)
        logger.info("🎤 CONFIGURACIÓN DEL ASISTENTE")
        logger.info("=" * 60)
        
        # Wake words
        if hasattr(self, 'porcupine'):
            if hasattr(self.porcupine, '_keyword_paths') and self.porcupine._keyword_paths:
                logger.info(f"🎯 Wake words: Hola Puertocho, Oye Puertocho (modelo personalizado)")
            else:
                logger.info(f"🎯 Wake words: Hey Google, Alexa (keywords genéricos)")
        
        # GPIO
        if GPIO_AVAILABLE:
            logger.info(f"🔴 LED Rojo (GPIO {config.led_record_pin}): Escuchando")
            logger.info(f"🟢 LED Verde (GPIO {config.led_idle_pin}): Listo")
            logger.info(f"🔘 Botón (GPIO {config.button_pin}): Activación manual")
        
        # Servicio activo
        if self.use_assistant_api:
            logger.info(f"🤖 Asistente: {config.assistant_chat_url}")
            logger.info("🎯 Modo: Conversacional multivuelta con slot-filling")
        else:
            logger.info(f"🤖 Transcripción: {config.transcription_service_url}")
            logger.info("🎯 Modo: Comandos directos (fallback)")
        
        # Audio
        if self.capture_rate == config.porcupine_rate:
            logger.info(f"🎤 Audio: {self.capture_rate} Hz (directo, sin resample)")
        else:
            logger.info(f"🎤 Audio: {self.capture_rate} Hz → {config.porcupine_rate} Hz (con resample)")
        
        logger.info("=" * 60)
    
    async def start(self):
        """Iniciar el asistente"""
        logger.info("🚀 Iniciando asistente de voz...")
        
        # Conectar al backend
        try:
            await self.backend_client.connect()
        except Exception as e:
            logger.warning(f"⚠️ No se pudo conectar al backend: {e}")
        
        # Cambiar estado a idle
        await self._set_state(AssistantState.IDLE)
        
        # Iniciar bucle principal
        await self._main_loop()
    
    async def stop(self):
        """Detener el asistente"""
        logger.info("🛑 Deteniendo asistente...")
        
        self.should_stop = True
        
        # Desconectar del backend
        await self.backend_client.disconnect()
        
        # Cleanup GPIO
        if GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
            except:
                pass
        
        # Cleanup Porcupine
        if hasattr(self, 'porcupine'):
            self.porcupine.delete()
        
        logger.info("✅ Asistente detenido")
    
    async def _set_state(self, new_state: str):
        """Cambiar estado del asistente"""
        if self.state != new_state:
            self.state = new_state
            logger.info(f"Estado cambiado: {new_state}")
            
            # Actualizar LEDs
            self._update_leds()
            
            # Enviar actualización al backend
            try:
                await self.backend_client.send_status_update(new_state)
            except Exception as e:
                logger.warning(f"Error enviando estado al backend: {e}")
    
    def _update_leds(self):
        """Actualizar LEDs según el estado"""
        if not GPIO_AVAILABLE:
            return
        
        try:
            if self.state == AssistantState.IDLE:
                GPIO.output(config.led_idle_pin, GPIO.HIGH)
                GPIO.output(config.led_record_pin, GPIO.LOW)
            elif self.state == AssistantState.LISTENING:
                GPIO.output(config.led_idle_pin, GPIO.LOW)
                GPIO.output(config.led_record_pin, GPIO.HIGH)
            elif self.state == AssistantState.PROCESSING:
                # Parpadeo alternado
                GPIO.output(config.led_idle_pin, GPIO.LOW)
                GPIO.output(config.led_record_pin, GPIO.LOW)
            else:  # ERROR
                # Ambos LEDs encendidos
                GPIO.output(config.led_idle_pin, GPIO.HIGH)
                GPIO.output(config.led_record_pin, GPIO.HIGH)
        except Exception as e:
            logger.warning(f"Error actualizando LEDs: {e}")
    
    async def _handle_backend_message(self, message: Dict[str, Any]):
        """Manejar mensajes del backend"""
        message_type = message.get("type")
        
        if message_type == "manual_activation":
            logger.info("🔘 Activación manual desde backend")
            await self._handle_manual_activation()
        else:
            logger.debug(f"Mensaje no manejado del backend: {message}")
    
    async def _handle_manual_activation(self):
        """Manejar activación manual"""
        if self.state != AssistantState.IDLE:
            logger.warning("Asistente ocupado, ignorando activación manual")
            return
        
        logger.info("🔘 Procesando activación manual...")
        
        await self._set_state(AssistantState.LISTENING)
        
        # Grabar audio
        raw_audio = await self._record_audio()
        
        if raw_audio:
            await self._set_state(AssistantState.PROCESSING)
            
            # Procesar audio
            response = await self._process_audio(raw_audio)
            
            if response:
                # Enviar comando al backend
                try:
                    await self.backend_client.send_command_log(f"Activación manual: {response}")
                except Exception as e:
                    logger.warning(f"Error enviando comando al backend: {e}")
        
        await self._set_state(AssistantState.IDLE)
    
    async def _main_loop(self):
        """Bucle principal del asistente"""
        logger.info("🎯 Escuchando wake words...")
        
        # Configurar stream de audio
        if not AUDIO_AVAILABLE:
            logger.error("❌ Audio no disponible")
            return
        
        try:
            stream = sd.RawInputStream(
                samplerate=self.capture_rate,
                blocksize=self.chunk_size,
                dtype='int16',
                channels=config.channels,
                callback=self._audio_callback
            )
            
            with stream:
                while not self.should_stop:
                    await asyncio.sleep(0.1)  # Pequeña pausa para no saturar CPU
                    
                    # Procesar audio acumulado para Porcupine
                    if len(self.audio_buffer) >= self.target_frame_length:
                        frames_to_process = self.audio_buffer[:self.target_frame_length]
                        self.audio_buffer = self.audio_buffer[self.target_frame_length:]
                        
                        # Procesar con Porcupine
                        keyword_index = self.porcupine.process(frames_to_process)
                        
                        if keyword_index >= 0:
                            logger.info("🎯 Wake word detectada!")
                            
                            # Enviar notificación al backend
                            try:
                                await self.backend_client.send_wake_word_detected("puertocho")
                            except Exception as e:
                                logger.warning(f"Error enviando wake word al backend: {e}")
                            
                            # Procesar comando
                            await self._handle_wake_word_detected()
                    
        except Exception as e:
            logger.error(f"❌ Error en bucle principal: {e}")
            await self._set_state(AssistantState.ERROR)
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback para audio en tiempo real"""
        if status:
            logger.warning(f"Estado de audio: {status}")
        
        # Convertir a numpy array
        audio_data = np.frombuffer(indata, dtype=np.int16)
        
        # Resample si es necesario
        if self.capture_rate != config.porcupine_rate:
            audio_data = simple_resample(audio_data, self.capture_rate, config.porcupine_rate)
        
        # Añadir al buffer
        self.audio_buffer = np.append(self.audio_buffer, audio_data)
    
    async def _handle_wake_word_detected(self):
        """Manejar detección de wake word"""
        if self.state != AssistantState.IDLE:
            logger.warning("Asistente ocupado, ignorando wake word")
            return
        
        await self._set_state(AssistantState.LISTENING)
        
        # Pequeña pausa para que el usuario empiece a hablar
        await asyncio.sleep(0.5)
        
        # Grabar audio
        raw_audio = await self._record_audio()
        
        if raw_audio:
            await self._set_state(AssistantState.PROCESSING)
            
            # Procesar audio
            response = await self._process_audio(raw_audio)
            
            if response:
                # Enviar comando al backend
                try:
                    await self.backend_client.send_command_log(response)
                except Exception as e:
                    logger.warning(f"Error enviando comando al backend: {e}")
        
        await self._set_state(AssistantState.IDLE)
    
    async def _record_audio(self) -> Optional[bytes]:
        """Grabar audio del usuario"""
        logger.info("🎤 Grabando audio del usuario...")
        
        frames = []
        silence_count = 0
        max_silence_frames = 30  # ~3 segundos de silencio
        
        try:
            # Usar queue para capturar audio
            audio_queue = queue.Queue()
            
            def audio_callback(indata, frames, time, status):
                audio_queue.put(bytes(indata))
            
            with sd.RawInputStream(
                samplerate=self.capture_rate,
                blocksize=self.chunk_size,
                dtype='int16',
                channels=config.channels,
                callback=audio_callback
            ):
                for _ in range(200):  # Máximo ~20 segundos
                    try:
                        frame = audio_queue.get(timeout=0.1)
                        frames.append(frame)
                        
                        # Detectar silencio con VAD si está disponible
                        if self.vad and len(frame) >= 320:  # VAD necesita al menos 10ms de audio
                            # Resample para VAD (necesita 16kHz)
                            if self.capture_rate != 16000:
                                audio_16k = simple_resample(
                                    np.frombuffer(frame, dtype=np.int16),
                                    self.capture_rate,
                                    16000
                                )
                                frame_16k = audio_16k.tobytes()
                            else:
                                frame_16k = frame
                            
                            # VAD necesita exactamente 320 bytes (160 samples * 2 bytes)
                            if len(frame_16k) >= 320:
                                if self.vad.is_speech(frame_16k[:320], 16000):
                                    silence_count = 0
                                else:
                                    silence_count += 1
                            else:
                                silence_count += 1
                        else:
                            silence_count += 1
                        
                        # Si detectamos silencio prolongado, terminar
                        if silence_count > max_silence_frames:
                            break
                    
                    except queue.Empty:
                        silence_count += 1
                        if silence_count > max_silence_frames:
                            break
            
            logger.info(f"🎤 Grabación terminada ({len(frames)} frames)")
            return b''.join(frames)
            
        except Exception as e:
            logger.error(f"❌ Error grabando audio: {e}")
            return None
    
    async def _process_audio(self, raw_audio: bytes) -> Optional[str]:
        """Procesar audio grabado"""
        if not raw_audio:
            return None
        
        try:
            # Crear archivo WAV
            wav_bytes = self._create_wav_file(raw_audio)
            
            # Enviar a servicio según configuración
            if self.use_assistant_api:
                return await self._send_to_assistant(wav_bytes)
            else:
                return await self._send_to_transcription_service(wav_bytes)
                
        except Exception as e:
            logger.error(f"❌ Error procesando audio: {e}")
            return None
    
    def _create_wav_file(self, raw_audio: bytes) -> bytes:
        """Crear archivo WAV desde audio raw"""
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(config.channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.capture_rate)
            wav_file.writeframes(raw_audio)
        return buffer.getvalue()
    
    async def _send_to_assistant(self, wav_bytes: bytes) -> Optional[str]:
        """Enviar audio al asistente conversacional"""
        # Esta función será implementada según la API específica
        logger.info("🤖 Procesando con asistente conversacional...")
        # TODO: Implementar integración con API del asistente
        return "Comando procesado por asistente conversacional"
    
    async def _send_to_transcription_service(self, wav_bytes: bytes) -> Optional[str]:
        """Enviar audio al servicio de transcripción"""
        # Esta función será implementada según la API específica
        logger.info("📝 Procesando con servicio de transcripción...")
        # TODO: Implementar integración con servicio de transcripción
        return "Comando transcrito"
    
    def _monitor_button(self):
        """Monitorear botón usando polling en lugar de interrupciones"""
        if not GPIO_AVAILABLE:
            return
        
        logger.info("🔘 Iniciando monitoreo de botón...")
        
        while not self.should_stop:
            try:
                current_state = GPIO.input(config.button_pin)
                
                # Detectar flanco descendente (botón presionado)
                if self.last_button_state == GPIO.HIGH and current_state == GPIO.LOW:
                    current_time = time.time()
                    
                    # Debounce: ignorar si es muy pronto desde la última pulsación
                    if current_time - self.last_button_time > 0.5:
                        logger.info("🔘 Botón presionado")
                        self.button_pressed = True
                        self.last_button_time = current_time
                        
                        # Crear tarea asíncrona para manejar activación manual
                        asyncio.create_task(self._handle_manual_activation())
                
                self.last_button_state = current_state
                time.sleep(0.1)  # Polling cada 100ms
                
            except Exception as e:
                logger.error(f"❌ Error monitoreando botón: {e}")
                time.sleep(1)
