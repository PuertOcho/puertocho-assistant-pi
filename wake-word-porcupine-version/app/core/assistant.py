"""
Lógica principal del asistente de voz PuertoCho.
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

# Import modules using absolute imports
from config import Config
from utils.logging_config import get_logger
# Note: BackendClient import removed to avoid websockets dependency for now

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
    
    def __init__(self, config):
        self.config = config
        self.state = AssistantState.IDLE
        self.audio_queue = queue.Queue()
        self.should_stop = False
        self.button_pressed = False
        self.last_button_time = 0
        self.last_button_state = GPIO.HIGH if GPIO_AVAILABLE else True
        
        # Buffer para acumular audio para Porcupine (512 frames exactos)
        self.audio_buffer = np.array([], dtype=np.int16)
        self.target_frame_length = 512  # Porcupine requiere exactamente 512 frames
        
        # Configuración de audio
        self.capture_rate = self.config.detect_supported_sample_rate()
        self.chunk_size = int(512 * (self.capture_rate / 16000)) if self.capture_rate != 16000 else 512
        
        # Inicialización diferida
        self.porcupine = None
        self.vad = None
        self.commands = {}
        self.session_id = None
        self.use_assistant_api = True
        
        # Hilo para monitorear botón
        self.button_thread = None
    
    async def initialize(self):
        """Inicializar el asistente de forma asíncrona"""
        try:
            # Cargar comandos
            await self._load_commands()
            
            # Configurar GPIO
            self._setup_gpio()
            
            # Inicializar VAD
            self._setup_vad()
            
            # Inicializar Porcupine
            self._setup_porcupine()
            
            # Verificar servicios
            await self._verify_services()
            
            # Iniciar monitoreo de botón
            self._start_button_monitor()
            
            print("✅ Asistente inicializado correctamente")
            
        except Exception as e:
            print(f"❌ Error inicializando asistente: {e}")
            raise
    
    def get_wake_words(self) -> str:
        """Obtener descripción de las wake words activas"""
        if hasattr(self, 'porcupine') and self.porcupine and hasattr(self.porcupine, '_keyword_paths') and self.porcupine._keyword_paths:
            return "Hola Puertocho, Oye Puertocho (modelo personalizado)"
        else:
            return "Hey Google, Alexa (keywords genéricos)"
    
    def stop(self):
        """Detener el asistente"""
        self.should_stop = True
        
        # Detener Porcupine
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None
        
        # Cleanup GPIO
        if GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
            except:
                pass
    
    async def run(self):
        """Ejecutar el bucle principal del asistente"""
        try:
            import sounddevice as sd
            
            print("🚀 Iniciando bucle principal del asistente...")
            
            with sd.RawInputStream(
                samplerate=self.capture_rate,
                blocksize=self.chunk_size,
                dtype='int16',
                channels=1,
                device=self.config.audio_device_index,
                callback=self._audio_callback
            ):
                print(f"👂 Esperando wake word: {self.get_wake_words()}")
                print(f"🎵 Audio: {self.capture_rate} Hz")
                
                self._set_state(AssistantState.IDLE)
                
                while not self.should_stop:
                    try:
                        # Procesar audio para detección de wake word
                        await self._process_audio_buffer()
                        
                        # Pequeña pausa para no sobrecargar CPU
                        await asyncio.sleep(0.01)
                        
                    except Exception as e:
                        print(f"❌ Error en bucle principal: {e}")
                        await asyncio.sleep(1)
                        
        except Exception as e:
            print(f"❌ Error en bucle principal: {e}")
            raise
    
    async def _load_commands(self):
        """Cargar comandos desde archivo JSON"""
        try:
            import json
            with open(self.config.commands_file, 'r') as f:
                self.commands = json.load(f)
            print(f"✅ Comandos cargados: {len(self.commands)}")
        except Exception as e:
            print(f"⚠️ Error cargando comandos: {e}")
            self.commands = {}
    
    async def _verify_services(self):
        """Verificar servicios disponibles"""
        print("🔄 Verificando servicios disponibles...")
        
        try:
            # Verificar asistente conversacional
            health_url = self.config.assistant_chat_url.replace('/chat', '/health')
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                print("✅ Asistente conversacional disponible")
                self.use_assistant_api = True
                return
        except Exception as e:
            print(f"⚠️ Asistente conversacional no disponible: {e}")
        
        # Fallback a transcripción
        try:
            response = requests.get(self.config.transcription_service_url.replace('/transcribe', '/health'), timeout=5)
            print("✅ Servicio de transcripción disponible")
            self.use_assistant_api = False
        except Exception as e:
            print(f"⚠️ Servicios no disponibles: {e}")
            self.use_assistant_api = False
    
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
                            print("🎯 Wake word detectado!")
                            await self._handle_voice_command()
                            return
            
            # Verificar botón
            if self.button_pressed:
                self.button_pressed = False
                print("🔘 Activación manual")
                await self._handle_voice_command()
                
        except queue.Empty:
            pass
        except Exception as e:
            print(f"❌ Error procesando audio: {e}")
    
    async def _handle_voice_command(self):
        """Manejar comando de voz detectado"""
        try:
            self._set_state(AssistantState.LISTENING)
            
            # Grabar audio
            audio_bytes = await self._record_until_silence()
            if not audio_bytes:
                self._set_state(AssistantState.IDLE)
                return
            
            self._set_state(AssistantState.PROCESSING)
            
            # Crear WAV
            wav_bytes = self._create_wav_file(audio_bytes)
            
            # Enviar al servicio apropiado
            if self.use_assistant_api:
                response = await self._send_to_assistant(wav_bytes)
            else:
                response = await self._send_to_transcription_service(wav_bytes)
            
            if response:
                print(f"🤖 Respuesta: {response}")
            
        except Exception as e:
            print(f"❌ Error manejando comando: {e}")
        finally:
            self._set_state(AssistantState.IDLE)
    
    async def _record_until_silence(self) -> bytes:
        """Grabar audio hasta detectar silencio"""
        print("🎤 Grabando audio...")
        frames = []
        silence_count = 0
        max_silence_frames = 40
        
        # Limpiar cola
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        
        start_time = time.time()
        max_recording_time = 10
        
        while time.time() - start_time < max_recording_time:
            try:
                data = self.audio_queue.get(timeout=0.1)
                frames.append(data)
                
                # Detectar silencio usando VAD
                audio_chunk = np.frombuffer(data, dtype=np.int16)
                
                if self.capture_rate != 16000:
                    resampled_pcm = simple_resample(audio_chunk, self.capture_rate, 16000)
                else:
                    resampled_pcm = audio_chunk
                
                if len(resampled_pcm) >= 320:
                    vad_data = resampled_pcm[:320].astype(np.int16).tobytes()
                    is_speech = self.vad.is_speech(vad_data, 16000)
                    
                    if is_speech:
                        silence_count = 0
                    else:
                        silence_count += 1
                    
                    if silence_count > max_silence_frames:
                        break
                
            except queue.Empty:
                silence_count += 1
                if silence_count > max_silence_frames:
                    break
        
        print(f"🎤 Grabación terminada ({len(frames)} frames)")
        return b''.join(frames)
    
    def _setup_gpio(self):
        """Configurar GPIO para LEDs y botón"""
        if not GPIO_AVAILABLE:
            print("⚠️ GPIO no disponible, LEDs y botón deshabilitados")
            return
        
        try:
            print("🔧 Configurando GPIO...")
            
            GPIO.setwarnings(False)
            GPIO.cleanup()
            GPIO.setmode(GPIO.BCM)
            
            # Configurar pines
            GPIO.setup(self.config.led_idle_pin, GPIO.OUT)
            GPIO.setup(self.config.led_record_pin, GPIO.OUT)
            GPIO.setup(self.config.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Estado inicial
            GPIO.output(self.config.led_idle_pin, GPIO.HIGH)
            GPIO.output(self.config.led_record_pin, GPIO.LOW)
            
            print("✅ GPIO configurado correctamente")
            
        except Exception as e:
            print(f"⚠️ Error configurando GPIO: {e}")
    
    def _setup_vad(self):
        """Configurar VAD para detección de voz"""
        try:
            import webrtcvad
            self.vad = webrtcvad.Vad(2)
            print("✅ VAD configurado")
        except ImportError:
            print("⚠️ webrtcvad no disponible, usando detección simple")
            self.vad = None
    
    def _setup_porcupine(self):
        """Configurar Porcupine para detección de wake word"""
        if not PORCUPINE_AVAILABLE:
            print("⚠️ Porcupine no disponible")
            return
        
        try:
            print("🔄 Configurando Porcupine...")
            
            # Intentar con modelo personalizado
            try:
                self.porcupine = pvporcupine.create(
                    access_key=self.config.porcupine_access_key,
                    keyword_paths=[str(self.config.model_file)],
                    model_path=str(self.config.params_file) if self.config.params_file.exists() else None
                )
                print("✅ Porcupine configurado con modelo personalizado")
                return
            except Exception as e:
                print(f"⚠️ Error con modelo personalizado: {e}")
            
            # Fallback a keywords genéricos
            try:
                self.porcupine = pvporcupine.create(
                    access_key=self.config.porcupine_access_key,
                    keywords=['hey google', 'alexa']
                )
                print("✅ Porcupine configurado con keywords genéricos")
                return
            except Exception as e:
                print(f"❌ Error con keywords genéricos: {e}")
                
        except Exception as e:
            print(f"❌ Error configurando Porcupine: {e}")
            raise
    
    def _start_button_monitor(self):
        """Iniciar monitoreo del botón"""
        if not GPIO_AVAILABLE:
            return
        
        def monitor_button():
            while not self.should_stop:
                try:
                    current_state = GPIO.input(self.config.button_pin)
                    
                    if self.last_button_state == GPIO.HIGH and current_state == GPIO.LOW:
                        current_time = time.time()
                        if current_time - self.last_button_time > 0.3:
                            self.button_pressed = True
                            self.last_button_time = current_time
                    
                    self.last_button_state = current_state
                    time.sleep(0.05)
                    
                except Exception as e:
                    print(f"⚠️ Error monitoreando botón: {e}")
                    time.sleep(0.1)
        
        self.button_thread = threading.Thread(target=monitor_button, daemon=True)
        self.button_thread.start()
        print("✅ Monitoreo de botón iniciado")
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback para captura de audio"""
        if status:
            if 'input overflow' in str(status):
                if not hasattr(self, '_last_overflow_time') or time.time() - self._last_overflow_time > 5:
                    print("⚠️ Audio overflow detectado")
                    self._last_overflow_time = time.time()
        
        # Agregar a cola si no está llena
        if self.audio_queue.qsize() < 10:
            self.audio_queue.put(bytes(indata))
        else:
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.put(bytes(indata))
            except queue.Empty:
                pass
    
    def _set_state(self, new_state: str):
        """Cambiar estado del asistente y LEDs"""
        self.state = new_state
        
        if not GPIO_AVAILABLE:
            return
        
        try:
            if new_state == AssistantState.IDLE:
                GPIO.output(self.config.led_idle_pin, GPIO.HIGH)
                GPIO.output(self.config.led_record_pin, GPIO.LOW)
            elif new_state == AssistantState.LISTENING:
                GPIO.output(self.config.led_idle_pin, GPIO.LOW)
                GPIO.output(self.config.led_record_pin, GPIO.HIGH)
            elif new_state == AssistantState.PROCESSING:
                GPIO.output(self.config.led_idle_pin, GPIO.LOW)
                self._blink_led(self.config.led_record_pin, 0.2, 3)
        except Exception as e:
            print(f"⚠️ Error controlando LEDs: {e}")
    
    def _blink_led(self, pin: int, interval: float, times: int):
        """Hacer parpadear un LED"""
        if not GPIO_AVAILABLE:
            return
        
        try:
            for _ in range(times):
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(interval)
                GPIO.output(pin, GPIO.LOW)
                time.sleep(interval)
        except Exception as e:
            print(f"⚠️ Error parpadeando LED: {e}")
    
    def _create_wav_file(self, raw_audio: bytes) -> bytes:
        """Crear archivo WAV desde audio crudo"""
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.capture_rate)
            wav_file.writeframes(raw_audio)
        return buffer.getvalue()
    
    async def _send_to_assistant(self, wav_bytes: bytes) -> Optional[str]:
        """Enviar audio al asistente conversacional"""
        if not wav_bytes:
            return None
        
        try:
            print("🤖 Procesando con asistente conversacional...")
            
            # Primero transcribir
            text = await self._send_to_transcription_service(wav_bytes)
            if not text:
                return None
            
            print(f"📝 Texto transcrito: '{text}'")
            
            # Enviar al asistente
            payload = {
                'message': text,
                'sessionId': self.session_id,
                'generateAudio': True,
                'language': 'es',
                'voice': 'es_female'
            }
            
            response = requests.post(
                self.config.assistant_chat_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('success', False):
                message = result.get('message', '').strip()
                self.session_id = result.get('sessionId')
                
                print(f"🤖 Asistente: '{message}'")
                
                # Reproducir audio si está disponible
                audio_url = result.get('audioUrl')
                if audio_url:
                    await self._play_tts_audio(audio_url)
                
                return message
            else:
                print(f"❌ Error del asistente: {result.get('error', 'Unknown')}")
                return None
                
        except Exception as e:
            print(f"❌ Error enviando al asistente: {e}")
            return None
    
    async def _send_to_transcription_service(self, wav_bytes: bytes) -> Optional[str]:
        """Enviar audio al servicio de transcripción"""
        if not wav_bytes:
            return None
        
        try:
            print("🤖 Transcribiendo audio...")
            
            files = {'audio': ('audio.wav', wav_bytes, 'audio/wav')}
            
            response = requests.post(
                self.config.transcription_service_url,
                files=files,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            text = result.get('transcription', '').strip()
            
            print(f"📝 Transcripción: '{text}'")
            return text
            
        except Exception as e:
            print(f"❌ Error en transcripción: {e}")
            return None
    
    async def _play_tts_audio(self, audio_url: str):
        """Reproducir audio TTS"""
        try:
            print(f"🔊 Reproduciendo audio TTS")
            
            response = requests.get(audio_url, timeout=10)
            response.raise_for_status()
            
            temp_path = "/tmp/tts_response.wav"
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            import subprocess
            try:
                subprocess.run(['aplay', temp_path], check=True, capture_output=True)
                print("✅ Audio reproducido")
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    subprocess.run(['mpv', '--no-video', temp_path], check=True, capture_output=True)
                    print("✅ Audio reproducido con mpv")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print("⚠️ No se pudo reproducir audio")
            
            try:
                os.remove(temp_path)
            except:
                pass
                
        except Exception as e:
            print(f"⚠️ Error reproduciendo audio: {e}")
