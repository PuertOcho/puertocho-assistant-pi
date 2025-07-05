import os
import json
import time
import queue
import requests
import sounddevice as sd
import numpy as np
import RPi.GPIO as GPIO
import webrtcvad
import pvporcupine
import threading
import wave
import io
import sys
import logging
from typing import Optional

# Configurar logging para mejor visibilidad
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Guardar referencia al print original antes de reemplazarlo
_original_print = print

# Forzar que todos los prints se muestren inmediatamente
def print_flush(*args, **kwargs):
    """Print con flush automático para logs en tiempo real"""
    _original_print(*args, **kwargs)
    sys.stdout.flush()

# Reemplazar print estándar
print = print_flush

# Cargar variables de entorno desde .env si existe
try:
    from dotenv import load_dotenv
    # Buscar .env en el directorio actual y en el directorio padre
    for env_file in ['.env', '../.env']:
        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"✅ Variables cargadas desde {env_file}")
            break
    else:
        print("ℹ️  No se encontró archivo .env, usando variables de entorno del sistema")
except ImportError:
    print("ℹ️  python-dotenv no instalado, usando variables de entorno del sistema")

# Configuración desde variables de entorno
PORCUPINE_ACCESS_KEY = os.getenv('PORCUPINE_ACCESS_KEY')  # NECESARIO: Obtener de la consola de Picovoice

# NUEVO: Endpoint del asistente conversacional
ASSISTANT_CHAT_URL = os.getenv('ASSISTANT_CHAT_URL', 'http://192.168.1.88:8080/api/assistant/chat')

# FALLBACK: Servicio de transcripción directo (para compatibilidad)
TRANSCRIPTION_SERVICE_URL = os.getenv('TRANSCRIPTION_SERVICE_URL', 'http://192.168.1.88:5000/transcribe')

# Configuración de GPIO
BUTTON_PIN = int(os.getenv('BUTTON_PIN', 22))
LED_IDLE = int(os.getenv('LED_IDLE_PIN', 17))
LED_RECORD = int(os.getenv('LED_RECORD_PIN', 27))

# Configuración de audio con detección automática de tasas soportadas
PORCUPINE_RATE = 16000      # Tasa requerida por Porcupine
CHANNELS = 1

# Detectar tasa de muestreo soportada
def detect_supported_sample_rate():
    """Detectar qué tasa de muestreo soporta el dispositivo"""
    import sounddevice as sd
    
    # Tasas comunes en orden de preferencia
    rates_to_try = [16000, 44100, 48000, 22050, 8000]
    
    for rate in rates_to_try:
        try:
            # Probar si la tasa funciona
            test_stream = sd.RawInputStream(
                samplerate=rate,
                blocksize=512,
                dtype='int16',
                channels=1
            )
            test_stream.close()
            print(f"✅ Tasa de audio soportada detectada: {rate} Hz")
            return rate
        except Exception as e:
            print(f"⚠️ Tasa {rate} Hz no soportada: {e}")
            continue
    
    # Si ninguna funciona, usar 44100 como fallback
    print("⚠️ Usando 44100 Hz como fallback")
    return 44100

# Detectar la mejor tasa de muestreo
CAPTURE_RATE = detect_supported_sample_rate()
CHUNK = 512 if CAPTURE_RATE == 16000 else int(512 * (CAPTURE_RATE / 16000))
FRAME_LENGTH = CHUNK

# Estados del asistente
class AssistantState:
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"

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
    def __init__(self):
        self.state = AssistantState.IDLE
        self.audio_queue = queue.Queue()
        self.should_stop = False
        self.button_pressed = False
        self.last_button_time = 0
        self.last_button_state = GPIO.HIGH  # Estado anterior del botón
        
        # Buffer para acumular audio para Porcupine (512 frames exactos)
        self.audio_buffer = np.array([], dtype=np.int16)
        self.target_frame_length = 512  # Porcupine requiere exactamente 512 frames
        
        # NUEVO: Gestión de sesión conversacional
        self.session_id = None
        self.use_assistant_api = True  # Preferir API del asistente
        # Indica si se está usando un modelo de wake word personalizado (español)
        self.custom_keywords = False
        
        # Verificar API Keys
        self._verify_api_keys()
        
        # Cargar comandos
        with open('commands.json') as f:
            self.commands = json.load(f)
        
        # Inicializar GPIO
        self._setup_gpio()
        
        # Inicializar VAD (para 16kHz después de resample)
        self.vad = webrtcvad.Vad(2)  # Agresividad media
        
        # Inicializar Porcupine con modelo personalizado
        self._setup_porcupine()
        
        # Verificar servicios disponibles
        self._verify_services()
        
        # Iniciar hilo para monitorear botón
        self.button_thread = threading.Thread(target=self._monitor_button, daemon=True)
        self.button_thread.start()
        
        print("✅ Asistente inicializado correctamente")
        
        # Mostrar wake words según la configuración real
        if self.custom_keywords:
            print("🎯 Wake words: Hola Puertocho, Oye Puertocho (modelo personalizado)")
        else:
            print("🎯 Wake words: Hey Google, Alexa (keywords genéricos)")
        
        print(f"🔴 LED Rojo (GPIO {LED_RECORD}): Escuchando")
        print(f"🟢 LED Verde (GPIO {LED_IDLE}): Listo")
        print(f"🔘 Botón (GPIO {BUTTON_PIN}): Activación manual")
        
        # Mostrar servicio activo
        if self.use_assistant_api:
            print(f"🤖 Asistente: {ASSISTANT_CHAT_URL}")
            print("🎯 Modo: Conversacional multivuelta con slot-filling")
        else:
            print(f"🤖 Transcripción: {TRANSCRIPTION_SERVICE_URL}")
            print("🎯 Modo: Comandos directos (fallback)")
            
        if CAPTURE_RATE == PORCUPINE_RATE:
            print(f"🎤 Audio: {CAPTURE_RATE} Hz (directo, sin resample)")
        else:
            print(f"🎤 Audio: {CAPTURE_RATE} Hz → {PORCUPINE_RATE} Hz (con resample)")

    def _verify_api_keys(self):
        """Verificar que las API keys estén configuradas"""
        if not PORCUPINE_ACCESS_KEY:
            raise ValueError("❌ ERROR: Necesitas configurar PORCUPINE_ACCESS_KEY en docker-compose.yml")

    def _setup_gpio(self):
        """Configurar pines GPIO con cleanup robusto"""
        print("🔧 Configurando GPIO...")
        
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
            GPIO.setup(LED_IDLE, GPIO.OUT)
            GPIO.setup(LED_RECORD, GPIO.OUT)
            GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Estado inicial: LED verde encendido
            GPIO.output(LED_IDLE, GPIO.HIGH)
            GPIO.output(LED_RECORD, GPIO.LOW)
            
            print("✅ GPIO configurado correctamente")
            
        except Exception as e:
            print(f"⚠️ Warning configurando GPIO: {e}")
            # Continuar de todas formas, algunos errores son esperados en Docker

    def _monitor_button(self):
        """Monitorear botón usando polling en lugar de interrupciones"""
        print("🔘 Iniciando monitoreo de botón...")
        
        while not self.should_stop:
            try:
                current_state = GPIO.input(BUTTON_PIN)
                
                # Detectar flanco descendente (botón presionado)
                if self.last_button_state == GPIO.HIGH and current_state == GPIO.LOW:
                    current_time = time.time()
                    if current_time - self.last_button_time > 0.3:  # Debouncing
                        self.button_pressed = True
                        self.last_button_time = current_time
                        print("🔘 Botón presionado")
                
                self.last_button_state = current_state
                time.sleep(0.05)  # Revisar cada 50ms
                
            except Exception as e:
                print(f"⚠️ Error monitoreando botón: {e}")
                time.sleep(0.1)

    def _setup_porcupine(self):
        """Configurar Porcupine con modelo personalizado en español"""
        try:
            # Usar el modelo personalizado con modelo en español
            model_path = "Puerto-ocho_es_raspberry-pi_v3_0_0.ppn"
            
            # Intentar configurar Porcupine con modelo en español
            print("🔄 Intentando configurar Porcupine con modelo en español...")
            
            # Método 1: Intentar usar modelo en español si está disponible
            try:
                # Descargar modelo en español automáticamente
                spanish_model_url = "https://github.com/Picovoice/porcupine/raw/master/lib/common/porcupine_params_es.pv"
                spanish_model_path = "porcupine_params_es.pv"
                
                # Descargar si no existe
                if not os.path.exists(spanish_model_path):
                    print("📥 Descargando modelo base en español...")
                    response = requests.get(spanish_model_url, timeout=30)
                    response.raise_for_status()
                    with open(spanish_model_path, 'wb') as f:
                        f.write(response.content)
                    print("✅ Modelo en español descargado")
                
                self.porcupine = pvporcupine.create(
                    access_key=PORCUPINE_ACCESS_KEY,
                    keyword_paths=[model_path],
                    model_path=spanish_model_path
                )
                self.custom_keywords = True  # Confirmamos uso de modelo personalizado
                print(f"✅ Porcupine inicializado con modelo personalizado en español: {model_path}")
                return
                
            except Exception as e:
                print(f"⚠️ Error con modelo en español: {e}")
                
            # Método 2: Intentar sin especificar modelo (usando el modelo por defecto)
            print("🔄 Intentando con modelo por defecto...")
            try:
                self.porcupine = pvporcupine.create(
                    access_key=PORCUPINE_ACCESS_KEY,
                    keyword_paths=[model_path]
                )
                self.custom_keywords = True  # Modelo personalizado por defecto
                print(f"✅ Porcupine inicializado con modelo por defecto: {model_path}")
                return
            except Exception as e:
                print(f"⚠️ Error con modelo por defecto: {e}")
                
            # Método 3: Fallback a keywords genéricos en inglés
            print("🔄 Usando keywords genéricos como fallback...")
            try:
                self.porcupine = pvporcupine.create(
                    access_key=PORCUPINE_ACCESS_KEY,
                    keywords=['hey google', 'alexa']  # Keywords genéricos
                )
                self.custom_keywords = False  # Usando keywords genéricos
                print("✅ Porcupine inicializado con keywords genéricos (hey google, alexa)")
                print("💡 NOTA: Usar 'Hey Google' o 'Alexa' para activar el asistente")
                return
            except Exception as e:
                print(f"❌ Error con keywords genéricos: {e}")
                
        except Exception as e:
            print(f"❌ Error general inicializando Porcupine: {e}")
            
        # Si todo falla, lanzar error
        raise RuntimeError("No se pudo inicializar Porcupine con ninguna configuración")

    def _download_spanish_model(self):
        """Descargar modelo base en español para Porcupine"""
        spanish_model_path = "porcupine_params_es.pv"
        
        if os.path.exists(spanish_model_path):
            return spanish_model_path
            
        try:
            print("📥 Descargando modelo base en español...")
            
            # URLs posibles para el modelo en español
            urls = [
                "https://github.com/Picovoice/porcupine/raw/master/lib/common/porcupine_params_es.pv",
                "https://github.com/Picovoice/porcupine/raw/main/lib/common/porcupine_params_es.pv"
            ]
            
            for url in urls:
                try:
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    
                    with open(spanish_model_path, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"✅ Modelo en español descargado desde: {url}")
                    return spanish_model_path
                    
                except Exception as e:
                    print(f"⚠️ Error descargando desde {url}: {e}")
                    continue
            
            raise Exception("No se pudo descargar el modelo en español desde ninguna URL")
            
        except Exception as e:
            print(f"❌ Error descargando modelo en español: {e}")
            return None

    def _verify_services(self):
        """Verificar que los servicios estén disponibles"""
        print("🔄 Verificando servicios disponibles...")
        
        # 1. Intentar verificar el asistente conversacional (prioritario)
        try:
            health_url = ASSISTANT_CHAT_URL.replace('/chat', '/health')
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                print("✅ Asistente conversacional disponible")
                print(f"🤖 Endpoint: {ASSISTANT_CHAT_URL}")
                self.use_assistant_api = True
                return
        except Exception as e:
            print(f"⚠️ Asistente conversacional no disponible: {e}")
        
        # 2. Fallback: Verificar servicio de transcripción directo
        try:
            print("🔄 Intentando con servicio de transcripción directo...")
            response = requests.get(TRANSCRIPTION_SERVICE_URL.replace('/transcribe', '/health'), timeout=5)
            print("✅ Servicio de transcripción directo disponible")
            print(f"🤖 Endpoint: {TRANSCRIPTION_SERVICE_URL}")
            self.use_assistant_api = False
        except requests.exceptions.RequestException:
            # Si no hay endpoint de health, intentar con el endpoint principal
            try:
                # Crear un archivo de audio de prueba muy pequeño para verificar
                test_audio = b'\x00' * 1000  # Audio silencioso de prueba
                buffer = io.BytesIO()
                with wave.open(buffer, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(16000)
                    wav_file.writeframes(test_audio)
                
                files = {'audio': ('test.wav', buffer.getvalue(), 'audio/wav')}
                response = requests.post(TRANSCRIPTION_SERVICE_URL, files=files, timeout=10)
                print("✅ Servicio de transcripción directo funcionando")
                print(f"🤖 Endpoint: {TRANSCRIPTION_SERVICE_URL}")
                self.use_assistant_api = False
            except Exception as e:
                print(f"⚠️ Warning: Ningún servicio disponible: {e}")
                print(f"💡 Asegúrate de tener ejecutándose:")
                print(f"   - Asistente: {ASSISTANT_CHAT_URL}")
                print(f"   - O transcripción: {TRANSCRIPTION_SERVICE_URL}")
                self.use_assistant_api = False

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback para captura de audio con manejo mejorado de overflow"""
        if status:
            if 'input overflow' in str(status):
                # Solo mostrar overflow ocasionalmente para no llenar logs
                if not hasattr(self, '_last_overflow_time') or time.time() - self._last_overflow_time > 5:
                    print(f"⚠️ Audio overflow detectado - considera reducir la carga del sistema")
                    self._last_overflow_time = time.time()
            else:
                print(f"⚠️ Status audio: {status}")
        
        # Agregar audio a la cola solo si no está llena
        if self.audio_queue.qsize() < 10:  # Limitar tamaño de cola
            self.audio_queue.put(bytes(indata))
        else:
            # Si la cola está llena, descartar datos antiguos
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.put(bytes(indata))
            except queue.Empty:
                pass

    def _set_state(self, new_state: str):
        """Cambiar estado del asistente y LEDs"""
        self.state = new_state
        try:
            if new_state == AssistantState.IDLE:
                GPIO.output(LED_IDLE, GPIO.HIGH)
                GPIO.output(LED_RECORD, GPIO.LOW)
            elif new_state == AssistantState.LISTENING:
                GPIO.output(LED_IDLE, GPIO.LOW)
                GPIO.output(LED_RECORD, GPIO.HIGH)
            elif new_state == AssistantState.PROCESSING:
                # Parpadear LED rojo durante procesamiento
                GPIO.output(LED_IDLE, GPIO.LOW)
                self._blink_led(LED_RECORD, 0.2, 3)
        except Exception as e:
            print(f"⚠️ Error controlando LEDs: {e}")

    def _blink_led(self, pin: int, interval: float, times: int):
        """Hacer parpadear un LED"""
        try:
            for _ in range(times):
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(interval)
                GPIO.output(pin, GPIO.LOW)
                time.sleep(interval)
        except Exception as e:
            print(f"⚠️ Error parpadeando LED: {e}")

    def _record_until_silence(self) -> bytes:
        """Grabar audio hasta detectar silencio prolongado"""
        print("🎤 Grabando audio...")
        frames = []
        silence_count = 0
        max_silence_frames = 40  # ~0.8 segundos de silencio (más rápido)
        
        # Limpiar cola de audio
        while not self.audio_queue.empty():
            self.audio_queue.get()
        
        start_time = time.time()
        max_recording_time = 10  # 10 segundos máximo
        
        while time.time() - start_time < max_recording_time:
            try:
                # Obtener datos de audio con timeout
                data = self.audio_queue.get(timeout=0.1)
                frames.append(data)
                
                # Convertir a numpy array
                audio_chunk = np.frombuffer(data, dtype=np.int16)
                
                # Resample para VAD si es necesario
                if CAPTURE_RATE != PORCUPINE_RATE:
                    resampled_pcm = simple_resample(audio_chunk, CAPTURE_RATE, PORCUPINE_RATE)
                else:
                    resampled_pcm = audio_chunk
                
                # Verificar si es voz usando VAD (requiere 16kHz)
                if len(resampled_pcm) >= 320:  # 20ms a 16kHz
                    vad_data = resampled_pcm[:320].astype(np.int16).tobytes()
                    is_speech = self.vad.is_speech(vad_data, PORCUPINE_RATE)
                    if is_speech:
                        silence_count = 0
                    else:
                        silence_count += 1
                    
                    # Si detectamos silencio prolongado, terminar
                    if silence_count > max_silence_frames:
                        break
                
                # Verificar si se presionó el botón para cancelar
                if self.button_pressed:
                    self.button_pressed = False
                    print("🔘 Grabación cancelada por botón")
                    return b''
                    
            except queue.Empty:
                silence_count += 1
                if silence_count > max_silence_frames:
                    break
        
        print(f"🎤 Grabación terminada ({len(frames)} frames)")
        return b''.join(frames)

    def _create_wav_file(self, raw_audio: bytes) -> bytes:
        """Crear archivo WAV desde audio raw"""
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(CAPTURE_RATE)  # Tasa de captura detectada
            wav_file.writeframes(raw_audio)
        return buffer.getvalue()

    def _send_to_assistant(self, wav_bytes: bytes) -> Optional[str]:
        """Enviar audio al asistente conversacional (NUEVO)"""
        if not wav_bytes:
            return None
            
        try:
            print("🤖 Procesando con asistente conversacional...")
            
            # PASO 1: Transcribir el audio primero
            text = self._send_to_transcription_service(wav_bytes)
            if not text:
                print("❌ No se pudo transcribir el audio para el asistente")
                return None
            
            print(f"📝 Texto transcrito: '{text}'")
            
            # PASO 2: Enviar texto al asistente conversacional
            payload = {
                'message': text,
                'sessionId': self.session_id,
                'generateAudio': True,  # Solicitar audio TTS de respuesta
                'language': 'es',
                'voice': 'es_female',
                'deviceContext': self._get_device_context()  # NUEVO: Contexto del dispositivo
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Enviar petición POST al asistente conversacional
            response = requests.post(
                ASSISTANT_CHAT_URL,
                json=payload,
                headers=headers,
                timeout=30  # Timeout de 30 segundos
            )
            
            # Verificar respuesta
            response.raise_for_status()
            
            # Obtener respuesta del asistente
            result = response.json()
            
            if result.get('success', False):
                assistant_message = result.get('message', '').strip()
                self.session_id = result.get('sessionId')  # Actualizar sessionId
                
                # Información adicional disponible
                audio_url = result.get('audioUrl')
                tts_service = result.get('ttsService')
                conversation_state = result.get('conversationState', 'unknown')
                extracted_entities = result.get('extractedEntities', {})
                missing_entities = result.get('missingEntities', {})
                suggested_action = result.get('suggestedAction')
                metadata = result.get('metadata', {})
                
                print(f"🤖 Asistente: '{assistant_message}'")
                print(f"🔄 Estado conversación: {conversation_state}")
                
                if extracted_entities:
                    print(f"📝 Entidades extraídas: {extracted_entities}")
                if missing_entities:
                    print(f"❓ Entidades faltantes: {missing_entities}")
                if suggested_action:
                    print(f"💡 Acción sugerida: {suggested_action}")
                
                if audio_url:
                    print(f"🔊 Audio TTS disponible: {audio_url}")
                    # Reproducir audio TTS si está disponible
                    self._play_tts_audio(audio_url)
                if tts_service:
                    print(f"🎵 Servicio TTS usado: {tts_service}")
                
                return assistant_message
            else:
                error_msg = result.get('error', 'Error desconocido')
                print(f"❌ Error del asistente: {error_msg}")
                return None
            
        except requests.exceptions.Timeout:
            print("❌ Timeout esperando respuesta del asistente")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión con asistente: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Error decodificando respuesta JSON del asistente: {e}")
            return None
        except Exception as e:
            print(f"❌ Error enviando al asistente: {e}")
            return None

    def _send_to_transcription_service(self, wav_bytes: bytes) -> Optional[str]:
        """Enviar audio al servicio de transcripción HTTP local (FALLBACK)"""
        if not wav_bytes:
            return None
            
        try:
            print("🤖 Enviando audio al servicio de transcripción...")
            
            # Preparar archivo para envío
            files = {'audio': ('audio.wav', wav_bytes, 'audio/wav')}
            
            # Enviar petición POST al servicio de transcripción
            response = requests.post(
                TRANSCRIPTION_SERVICE_URL,
                files=files,
                timeout=30  # Timeout de 30 segundos para transcripción
            )
            
            # Verificar respuesta
            response.raise_for_status()
            
            # Obtener transcripción del JSON de respuesta
            result = response.json()
            text = result.get('transcription', '').strip()
            
            print(f"📝 Transcripción: '{text}'")
            return text
            
        except requests.exceptions.Timeout:
            print("❌ Timeout esperando respuesta del servicio de transcripción")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión con servicio de transcripción: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Error decodificando respuesta JSON: {e}")
            return None
        except Exception as e:
            print(f"❌ Error enviando al servicio de transcripción: {e}")
            return None

    def _play_tts_audio(self, audio_url: str):
        """Reproducir audio TTS desde URL"""
        try:
            print(f"🔊 Reproduciendo audio TTS: {audio_url}")
            
            # Descargar el audio
            response = requests.get(audio_url, timeout=10)
            response.raise_for_status()
            
            # Guardar temporalmente
            temp_audio_path = "/tmp/tts_response.wav"
            with open(temp_audio_path, 'wb') as f:
                f.write(response.content)
            
            # Reproducir usando comandos del sistema (más compatible)
            import subprocess
            try:
                # Intentar con aplay (ALSA)
                subprocess.run(['aplay', temp_audio_path], 
                             check=True, capture_output=True)
                print("✅ Audio reproducido exitosamente")
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    # Fallback: mpg123 o mpv
                    subprocess.run(['mpv', '--no-video', temp_audio_path], 
                                 check=True, capture_output=True)
                    print("✅ Audio reproducido con mpv")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print("⚠️ No se pudo reproducir audio: instala aplay o mpv")
            
            # Limpiar archivo temporal
            try:
                import os
                os.remove(temp_audio_path)
            except:
                pass
                
        except Exception as e:
            print(f"⚠️ Error reproduciendo audio TTS: {e}")

    def _get_device_context(self):
        """Obtener contexto del dispositivo para enviar al asistente"""
        try:
            import datetime
            import platform
            
            context = {
                'deviceType': 'raspberry_pi',
                'location': 'Casa Principal',  # Configurable en el futuro
                'room': 'Salón',  # Configurable en el futuro
                'timeZone': 'Europe/Madrid',  # Configurable
                'isNightMode': self._is_night_mode(),
                'capabilities': {
                    'hasAudio': 'true',
                    'hasGPIO': 'true',
                    'hasLEDs': 'true',
                    'hasMicrophone': 'true',
                    'platform': platform.system(),
                    'pythonVersion': platform.python_version()
                },
                'sensors': {}  # Para futuras extensiones
            }
            
            # Agregar información de temperatura si está disponible
            try:
                # En el futuro se puede leer de sensores reales
                context['temperature'] = None
                context['humidity'] = None
            except:
                pass
                
            return context
            
        except Exception as e:
            print(f"⚠️ Error obteniendo contexto del dispositivo: {e}")
            return {
                'deviceType': 'raspberry_pi',
                'capabilities': {'hasAudio': 'true'}
            }

    def _is_night_mode(self):
        """Determinar si es modo nocturno basado en la hora"""
        try:
            import datetime
            current_hour = datetime.datetime.now().hour
            # Considerar modo nocturno entre 22:00 y 7:00
            return current_hour >= 22 or current_hour <= 7
        except:
            return False

    def _execute_command(self, text: str):
        """Ejecutar comando basado en el texto"""
        command = self.commands.get(text.lower())
        if command:
            pin = command['pin']
            state = command['state']
            gpio_state = GPIO.HIGH if state == 'on' else GPIO.LOW
            try:
                GPIO.output(pin, gpio_state)
                print(f"✅ Ejecutando: '{text}' -> GPIO {pin} = {state}")
            except Exception as e:
                print(f"❌ Error ejecutando comando: {e}")
        else:
            print(f"❓ Comando no reconocido: '{text}'")
            print(f"💡 Comandos disponibles: {list(self.commands.keys())}")

    def run(self):
        """Ejecutar el asistente principal"""
        print("🚀 Iniciando asistente de voz...")
        
        try:
            with sd.RawInputStream(
                samplerate=CAPTURE_RATE,  # Tasa detectada automáticamente
                blocksize=FRAME_LENGTH,   # Buffer ajustado según tasa
                dtype='int16', 
                channels=CHANNELS, 
                callback=self._audio_callback
            ):
                # Mostrar mensaje apropiado según la configuración
                if self.custom_keywords:
                    print("👂 Esperando wake word 'Hola Puertocho' o 'Oye Puertocho'...")
                else:
                    print("👂 Esperando wake word 'Hey Google' o 'Alexa'...")
                    
                # Mostrar información sobre la tasa de audio
                if CAPTURE_RATE == PORCUPINE_RATE:
                    print(f"🎵 Audio optimizado: {CAPTURE_RATE} Hz directo")
                else:
                    print(f"🎵 Audio: {CAPTURE_RATE} Hz → resample → {PORCUPINE_RATE} Hz")
                
                # Limpiar buffer de audio al iniciar
                self.audio_buffer = np.array([], dtype=np.int16)
                print("🔄 Buffer de audio inicializado")
                    
                self._set_state(AssistantState.IDLE)
                
                while not self.should_stop:
                    try:
                        # Obtener audio para detección de wake word
                        audio_data = self.audio_queue.get(timeout=0.1)
                        pcm = np.frombuffer(audio_data, dtype=np.int16)
                        
                        # Resample si es necesario
                        if CAPTURE_RATE != PORCUPINE_RATE:
                            resampled_pcm = simple_resample(pcm, CAPTURE_RATE, PORCUPINE_RATE)
                        else:
                            resampled_pcm = pcm
                        
                        # Acumular audio en buffer
                        self.audio_buffer = np.concatenate([self.audio_buffer, resampled_pcm])
                        
                        # Limitar el tamaño del buffer para evitar que crezca indefinidamente
                        max_buffer_size = self.target_frame_length * 10  # Máximo 10 frames
                        if len(self.audio_buffer) > max_buffer_size:
                            self.audio_buffer = self.audio_buffer[-max_buffer_size:]
                        
                        # Procesar frames completos de 512 muestras
                        while len(self.audio_buffer) >= self.target_frame_length:
                            # Extraer exactamente 512 frames
                            frame = self.audio_buffer[:self.target_frame_length]
                            self.audio_buffer = self.audio_buffer[self.target_frame_length:]
                            
                            # Procesar con Porcupine
                            keyword_index = self.porcupine.process(frame.astype(np.int16))
                            
                            # Si se detectó wake word, salir del bucle interno
                            if keyword_index >= 0:
                                break
                        else:
                            # No se detectó wake word en ningún frame
                            keyword_index = -1
                        
                        # Verificar wake word o botón
                        if keyword_index >= 0:
                            print("🎯 Wake word detectado!")
                            self._handle_voice_command()
                        elif self.button_pressed:
                            self.button_pressed = False
                            print("🔘 Activación manual")
                            self._handle_voice_command()
                            
                    except queue.Empty:
                        continue
                    except Exception as e:
                        if "Invalid frame length" in str(e):
                            print(f"⚠️ Error de frame length: {e}")
                            print(f"🔧 Buffer actual: {len(self.audio_buffer)} muestras")
                            # Limpiar buffer y continuar
                            self.audio_buffer = np.array([], dtype=np.int16)
                        else:
                            print(f"❌ Error en loop principal: {e}")
                        time.sleep(0.1)
                        
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo asistente...")
        except Exception as e:
            print(f"❌ Error fatal: {e}")
        finally:
            self._cleanup()

    def _handle_voice_command(self):
        """Manejar comando de voz completo"""
        self._set_state(AssistantState.LISTENING)
        
        # Grabar audio
        raw_audio = self._record_until_silence()
        
        if raw_audio:
            self._set_state(AssistantState.PROCESSING)
            
            # Convertir a WAV
            wav_bytes = self._create_wav_file(raw_audio)
            
            # NUEVO: Usar asistente conversacional o fallback a transcripción
            if self.use_assistant_api:
                # Usar API del asistente conversacional
                assistant_response = self._send_to_assistant(wav_bytes)
                
                if assistant_response:
                    print(f"✅ Respuesta del asistente: '{assistant_response}'")
                    # El asistente ya procesó todo (transcripción + acción + respuesta)
                    # No necesitamos hacer nada más, solo mostrar la respuesta
                else:
                    print("❌ No se pudo procesar con el asistente")
            else:
                # Fallback: Usar transcripción directa + comandos locales
                text = self._send_to_transcription_service(wav_bytes)
                
                if text:
                    # Ejecutar comando usando la lógica local
                    self._execute_command(text)
                else:
                    print("❌ No se pudo transcribir el audio")
        
        # Volver al estado idle
        time.sleep(1)
        self._set_state(AssistantState.IDLE)
        print("👂 Esperando wake word...")

    def _cleanup(self):
        """Limpiar recursos"""
        print("🧹 Limpiando recursos...")
        self.should_stop = True
        
        # Esperar a que termine el hilo del botón
        if hasattr(self, 'button_thread') and self.button_thread.is_alive():
            self.button_thread.join(timeout=1)
        
        # Limpiar GPIO
        try:
            GPIO.cleanup()
        except Exception as e:
            print(f"⚠️ Warning limpiando GPIO: {e}")
        
        # Limpiar Porcupine
        if hasattr(self, 'porcupine'):
            try:
                self.porcupine.delete()
            except Exception as e:
                print(f"⚠️ Warning limpiando Porcupine: {e}")
        
        print("🧹 Recursos liberados")

def main():
    """Función principal"""
    assistant = VoiceAssistant()
    assistant.run()

if __name__ == '__main__':
    main()
