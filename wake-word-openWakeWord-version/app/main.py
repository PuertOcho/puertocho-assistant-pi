#!/usr/bin/env python3
"""
🎤 Asistente de Voz Puertocho con openWakeWord
Detección de wake words usando openWakeWord en lugar de Porcupine
"""

import os
import json
import time
import queue
import requests
import sounddevice as sd
import numpy as np
import RPi.GPIO as GPIO
import webrtcvad
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
TRANSCRIPTION_SERVICE_URL = os.getenv('TRANSCRIPTION_SERVICE_URL', 'http://localhost:5000/transcribe')
BUTTON_PIN = int(os.getenv('BUTTON_PIN', 22))
LED_IDLE = int(os.getenv('LED_IDLE_PIN', 17))
LED_RECORD = int(os.getenv('LED_RECORD_PIN', 27))

# Configuración openWakeWord
OPENWAKEWORD_MODEL_PATHS = os.getenv('OPENWAKEWORD_MODEL_PATHS', 'alexa,hey_mycroft').split(',')
OPENWAKEWORD_THRESHOLD = float(os.getenv('OPENWAKEWORD_THRESHOLD', 0.5))
OPENWAKEWORD_VAD_THRESHOLD = float(os.getenv('OPENWAKEWORD_VAD_THRESHOLD', 0.0))
OPENWAKEWORD_ENABLE_SPEEX_NS = os.getenv('OPENWAKEWORD_ENABLE_SPEEX_NS', 'false').lower() == 'true'
OPENWAKEWORD_INFERENCE_FRAMEWORK = os.getenv('OPENWAKEWORD_INFERENCE_FRAMEWORK', 'onnx')

# Configuración de audio
AUDIO_SAMPLE_RATE = int(os.getenv('AUDIO_SAMPLE_RATE', 16000))
AUDIO_CHANNELS = int(os.getenv('AUDIO_CHANNELS', 1))
AUDIO_CHUNK_SIZE = int(os.getenv('AUDIO_CHUNK_SIZE', 1280))  # 80ms @ 16kHz

# Estados del asistente
class AssistantState:
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"

class VoiceAssistant:
    def __init__(self):
        self.state = AssistantState.IDLE
        self.should_stop = False
        self.button_pressed = False
        self.last_button_time = 0
        self.last_button_state = GPIO.HIGH
        
        # Buffer para acumular audio
        self.audio_buffer = queue.Queue()
        
        # Cargar comandos
        self._load_commands()
        
        # Inicializar GPIO
        self._setup_gpio()
        
        # Inicializar VAD si está configurado
        if OPENWAKEWORD_VAD_THRESHOLD > 0:
            self.vad = webrtcvad.Vad(2)  # Agresividad media
            print(f"✅ VAD inicializado con threshold: {OPENWAKEWORD_VAD_THRESHOLD}")
        else:
            self.vad = None
            print("ℹ️  VAD deshabilitado")
        
        # Inicializar openWakeWord
        self._setup_openwakeword()
        
        # Verificar servicio de transcripción
        self._verify_transcription_service()
        
        # Iniciar hilo para monitorear botón
        self.button_thread = threading.Thread(target=self._monitor_button, daemon=True)
        self.button_thread.start()
        
        print("✅ Asistente inicializado correctamente")
        self._show_configuration()

    def _load_commands(self):
        """Cargar comandos desde JSON"""
        try:
            with open('commands.json') as f:
                self.commands = json.load(f)
            print(f"✅ Comandos cargados: {len(self.commands)} comandos disponibles")
        except FileNotFoundError:
            # Crear comandos básicos por defecto
            self.commands = {
                "enciende luz verde": {"pin": LED_IDLE, "state": "HIGH"},
                "apaga luz verde": {"pin": LED_IDLE, "state": "LOW"},
                "enciende luz rojo": {"pin": LED_RECORD, "state": "HIGH"},
                "apaga luz rojo": {"pin": LED_RECORD, "state": "LOW"}
            }
            # Guardar comandos por defecto
            with open('commands.json', 'w') as f:
                json.dump(self.commands, f, indent=2)
            print(f"✅ Comandos por defecto creados: {len(self.commands)} comandos")

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
        
        # Configurar modo de numeración
        GPIO.setmode(GPIO.BCM)
        
        # Configurar pines
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(LED_IDLE, GPIO.OUT)
        GPIO.setup(LED_RECORD, GPIO.OUT)
        
        # Estado inicial: LED verde encendido (listo)
        GPIO.output(LED_IDLE, GPIO.HIGH)
        GPIO.output(LED_RECORD, GPIO.LOW)
        
        print(f"✅ GPIO configurado - Botón: {BUTTON_PIN}, LED Verde: {LED_IDLE}, LED Rojo: {LED_RECORD}")

    def _monitor_button(self):
        """Monitorear botón GPIO en hilo separado"""
        while not self.should_stop:
            try:
                current_state = GPIO.input(BUTTON_PIN)
                
                # Detectar presión del botón (flanco descendente con debounce)
                if self.last_button_state == GPIO.HIGH and current_state == GPIO.LOW:
                    current_time = time.time()
                    if current_time - self.last_button_time > 0.3:  # Debounce 300ms
                        print("🔘 Botón presionado - Activación manual")
                        self.button_pressed = True
                        self.last_button_time = current_time
                
                self.last_button_state = current_state
                time.sleep(0.1)  # Polling cada 100ms
                
            except Exception as e:
                print(f"⚠️ Error monitoreando botón: {e}")
                time.sleep(1)

    def _setup_openwakeword(self):
        """Configurar openWakeWord con modelos específicos"""
        
        # TEMPORAL: Saltamos openWakeWord completamente por ahora
        print("🔧 Modo de prueba: saltando openWakeWord - funcionará solo con botón GPIO")
        self.oww_model = None
        self.active_models = []
        return
        
        # Verificar si debemos intentar usar modelos de audio
        mode = os.getenv('MODE', '').upper()
        if mode == 'GPIO_ONLY':
            print("🔧 Modo GPIO_ONLY activado - saltando inicialización de openWakeWord")
            self.oww_model = None
            self.active_models = []
            return
        
        try:
            import openwakeword
            from openwakeword.model import Model
            
            print("🔄 Inicializando openWakeWord...")
            
            # Verificar si los modelos están especificados y no vacíos
            model_paths = os.getenv('OPENWAKEWORD_MODEL_PATHS', 'alexa,hey_mycroft').strip()
            if not model_paths:
                print("🔧 OPENWAKEWORD_MODEL_PATHS vacío - funcionará solo con botón GPIO")
                self.oww_model = None
                self.active_models = []
                return
            
            # Descargar modelos preentrenados si es necesario
            try:
                print("📥 Descargando modelos preentrenados...")
                openwakeword.utils.download_models()
                print("✅ Modelos descargados correctamente")
            except Exception as e:
                print(f"⚠️ Error descargando modelos: {e}")
                print("🔄 Continuando sin modelos de audio - solo botón GPIO")
                self.oww_model = None
                self.active_models = []
                return
            
            # Configurar parámetros del modelo
            model_kwargs = {
                'inference_framework': OPENWAKEWORD_INFERENCE_FRAMEWORK
            }
            
            # Añadir VAD si está habilitado
            if OPENWAKEWORD_VAD_THRESHOLD > 0:
                model_kwargs['vad_threshold'] = OPENWAKEWORD_VAD_THRESHOLD
            
            # Añadir supresión de ruido Speex si está habilitado
            if OPENWAKEWORD_ENABLE_SPEEX_NS:
                model_kwargs['enable_speex_noise_suppression'] = True
                print("✅ Supresión de ruido Speex habilitada")
            
            # Inicializar modelo con modelos específicos o todos
            try:
                if OPENWAKEWORD_MODEL_PATHS and OPENWAKEWORD_MODEL_PATHS != ['']:
                    # Filtrar modelos vacíos
                    models = [m.strip() for m in OPENWAKEWORD_MODEL_PATHS if m.strip()]
                    if models:
                        model_kwargs['wakeword_models'] = models
                        print(f"🔄 Intentando cargar modelos específicos: {models}")
                    else:
                        print("✅ Usando todos los modelos preentrenados")
                else:
                    print("✅ Usando todos los modelos preentrenados")
                
                # Crear modelo
                self.oww_model = Model(**model_kwargs)
                
                # Obtener lista de modelos activos
                self.active_models = list(self.oww_model.prediction_buffer.keys())
                print(f"✅ openWakeWord inicializado con {len(self.active_models)} modelos")
                if self.active_models:
                    print(f"🎯 Modelos activos: {', '.join(self.active_models)}")
                else:
                    print("⚠️ No se cargaron modelos - funcionará solo con botón GPIO")
                print(f"🎚️ Umbral de activación: {OPENWAKEWORD_THRESHOLD}")
                
            except Exception as model_error:
                print(f"⚠️ Error cargando modelos: {model_error}")
                print("🔄 Continuando sin modelos de audio - solo botón GPIO")
                self.oww_model = None
                self.active_models = []
                
        except ImportError:
            print("⚠️ openWakeWord no está disponible - funcionará solo con botón GPIO")
            self.oww_model = None
            self.active_models = []
        except Exception as e:
            print(f"⚠️ Error general con openWakeWord: {e}")
            print("🔄 Continuando sin modelos de audio - solo botón GPIO")
            self.oww_model = None
            self.active_models = []

    def _verify_transcription_service(self):
        """Verificar que el servicio de transcripción esté disponible"""
        try:
            print("🔄 Verificando servicio de transcripción...")
            response = requests.get(TRANSCRIPTION_SERVICE_URL.replace('/transcribe', '/health'), timeout=5)
            print("✅ Servicio de transcripción disponible")
        except requests.exceptions.RequestException:
            try:
                # Crear un archivo de audio de prueba muy pequeño
                test_audio = b'\x00' * 1000
                buffer = io.BytesIO()
                with wave.open(buffer, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(16000)
                    wav_file.writeframes(test_audio)
                
                files = {'audio': ('test.wav', buffer.getvalue(), 'audio/wav')}
                response = requests.post(TRANSCRIPTION_SERVICE_URL, files=files, timeout=10)
                print("✅ Servicio de transcripción disponible y funcionando")
            except Exception as e:
                print(f"⚠️ Warning: No se pudo verificar el servicio de transcripción: {e}")
                print(f"💡 Asegúrate de que el servicio esté ejecutándose en {TRANSCRIPTION_SERVICE_URL}")

    def _show_configuration(self):
        """Mostrar configuración actual"""
        print("\n📋 CONFIGURACIÓN ACTUAL:")
        print(f"🎤 Audio: {AUDIO_SAMPLE_RATE}Hz, {AUDIO_CHANNELS} canal, chunks de {AUDIO_CHUNK_SIZE} samples")
        
        if self.active_models:
            print(f"🧠 Modelos activos: {', '.join(self.active_models)}")
            print(f"🎚️ Umbral: {OPENWAKEWORD_THRESHOLD}")
            print(f"🔊 VAD: {'Habilitado' if OPENWAKEWORD_VAD_THRESHOLD > 0 else 'Deshabilitado'}")
            print(f"🔇 Speex NS: {'Habilitado' if OPENWAKEWORD_ENABLE_SPEEX_NS else 'Deshabilitado'}")
        else:
            print("🧠 Modelos de audio: No disponibles")
            print("🔘 Modo de funcionamiento: Solo botón GPIO")
            
        print(f"🔴 LED Rojo (GPIO {LED_RECORD}): Escuchando")
        print(f"🟢 LED Verde (GPIO {LED_IDLE}): Listo")
        print(f"🔘 Botón (GPIO {BUTTON_PIN}): Activación manual")
        print(f"🤖 Transcripción: {TRANSCRIPTION_SERVICE_URL}")
        
        if not self.active_models:
            print("\n💡 INSTRUCCIONES:")
            print("   • Presiona el botón GPIO 22 para activar el asistente")
            print("   • El LED verde indica que está listo")
            print("   • El LED rojo indica que está escuchando comandos")

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

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback para captura de audio"""
        if status:
            if 'input overflow' in str(status):
                if not hasattr(self, '_last_overflow_time') or time.time() - self._last_overflow_time > 5:
                    print(f"⚠️ Audio overflow detectado")
                    self._last_overflow_time = time.time()
            else:
                print(f"⚠️ Status audio: {status}")
        
        # Agregar audio a la cola
        if self.audio_buffer.qsize() < 10:
            self.audio_buffer.put(indata.copy())
        else:
            # Descartar datos antiguos si la cola está llena
            try:
                self.audio_buffer.get_nowait()
                self.audio_buffer.put(indata.copy())
            except queue.Empty:
                pass

    def _process_audio_for_wakeword(self):
        """Procesar audio para detectar wake words"""
        while not self.should_stop:
            try:
                # Verificar activación manual del botón siempre
                if self.button_pressed:
                    print("🔘 Activación manual detectada")
                    self.button_pressed = False
                    self._handle_wakeword_detected("manual_button", 1.0)
                    continue
                
                # Si no hay modelos de audio, solo manejar botón
                if not self.oww_model or not self.active_models:
                    time.sleep(0.1)
                    continue
                
                # Obtener chunk de audio si hay modelos disponibles
                try:
                    audio_chunk = self.audio_buffer.get(timeout=0.1)
                    
                    # Convertir a formato requerido (mono, int16)
                    if audio_chunk.ndim > 1:
                        audio_chunk = audio_chunk[:, 0]  # Tomar solo el primer canal
                    
                    # Convertir a int16 si es necesario
                    if audio_chunk.dtype != np.int16:
                        audio_chunk = (audio_chunk * 32767).astype(np.int16)
                    
                    # Ejecutar predicción con openWakeWord
                    prediction = self.oww_model.predict(audio_chunk)
                    
                    # Verificar si algún modelo supera el umbral
                    for model_name, score in prediction.items():
                        if score > OPENWAKEWORD_THRESHOLD:
                            print(f"🎯 Wake word detectada: '{model_name}' (score: {score:.3f})")
                            self._handle_wakeword_detected(model_name, score)
                            break
                            
                except queue.Empty:
                    continue
                except Exception as audio_error:
                    # Si hay error con audio, continuar solo con botón
                    print(f"⚠️ Error procesando audio (continuando con botón): {audio_error}")
                    time.sleep(0.1)
                    continue
                    
            except Exception as e:
                print(f"⚠️ Error general en procesamiento: {e}")
                time.sleep(0.1)

    def _handle_wakeword_detected(self, model_name: str, score: float):
        """Manejar detección de wake word"""
        print(f"🎉 Wake word '{model_name}' detectada con score {score:.3f}")
        self._set_state(AssistantState.LISTENING)
        
        # Grabar comando de voz
        self._handle_voice_command()
        
        # Volver al estado idle
        self._set_state(AssistantState.IDLE)

    def _handle_voice_command(self):
        """Grabar y procesar comando de voz"""
        try:
            print("🎤 Grabando comando...")
            
            # Limpiar buffer de audio
            while not self.audio_buffer.empty():
                self.audio_buffer.get()
            
            # Grabar por tiempo limitado o hasta silencio
            frames = []
            silence_count = 0
            max_silence_frames = 40  # ~0.8 segundos de silencio
            max_recording_time = 5  # 5 segundos máximo
            
            start_time = time.time()
            
            while time.time() - start_time < max_recording_time:
                try:
                    audio_chunk = self.audio_buffer.get(timeout=0.1)
                    frames.append(audio_chunk)
                    
                    # Detectar silencio si VAD está disponible
                    if self.vad:
                        # Convertir a formato para VAD
                        if audio_chunk.ndim > 1:
                            audio_chunk = audio_chunk[:, 0]
                        if audio_chunk.dtype != np.int16:
                            audio_chunk = (audio_chunk * 32767).astype(np.int16)
                        
                        # VAD requiere frames de 10, 20 o 30ms
                        frame_size = 320  # 20ms @ 16kHz
                        if len(audio_chunk) >= frame_size:
                            is_speech = self.vad.is_speech(audio_chunk[:frame_size].tobytes(), AUDIO_SAMPLE_RATE)
                            if not is_speech:
                                silence_count += 1
                            else:
                                silence_count = 0
                            
                            if silence_count > max_silence_frames:
                                print("🔇 Silencio detectado, finalizando grabación")
                                break
                    
                except queue.Empty:
                    silence_count += 1
                    if silence_count > max_silence_frames:
                        break
            
            if frames:
                # Concatenar audio grabado
                audio_data = np.concatenate(frames)
                if audio_data.ndim > 1:
                    audio_data = audio_data[:, 0]
                
                # Crear archivo WAV
                wav_bytes = self._create_wav_file(audio_data)
                
                # Enviar a transcripción
                self._set_state(AssistantState.PROCESSING)
                transcription = self._send_to_transcription_service(wav_bytes)
                
                if transcription:
                    print(f"🗣️  Transcripción: '{transcription}'")
                    self._execute_command(transcription)
                else:
                    print("❌ No se pudo transcribir el audio")
            else:
                print("❌ No se grabó audio")
                
        except Exception as e:
            print(f"❌ Error procesando comando de voz: {e}")

    def _create_wav_file(self, audio_data: np.ndarray) -> bytes:
        """Crear archivo WAV en memoria"""
        if audio_data.dtype != np.int16:
            audio_data = (audio_data * 32767).astype(np.int16)
        
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(AUDIO_CHANNELS)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(AUDIO_SAMPLE_RATE)
            wav_file.writeframes(audio_data.tobytes())
        
        return buffer.getvalue()

    def _send_to_transcription_service(self, wav_bytes: bytes) -> Optional[str]:
        """Enviar audio al servicio de transcripción"""
        try:
            files = {'audio': ('command.wav', wav_bytes, 'audio/wav')}
            response = requests.post(TRANSCRIPTION_SERVICE_URL, files=files, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('transcription', '').strip().lower()
            else:
                print(f"❌ Error del servicio de transcripción: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error enviando audio a transcripción: {e}")
            return None

    def _execute_command(self, text: str):
        """Ejecutar comando basado en transcripción"""
        text = text.lower().strip()
        
        if text in self.commands:
            cmd = self.commands[text]
            pin = cmd['pin']
            state = GPIO.HIGH if cmd['state'] == 'HIGH' else GPIO.LOW
            
            try:
                GPIO.output(pin, state)
                print(f"✅ Comando ejecutado: '{text}' → GPIO {pin} = {cmd['state']}")
            except Exception as e:
                print(f"❌ Error ejecutando comando: {e}")
        else:
            print(f"❓ Comando no reconocido: '{text}'")
            print(f"💡 Comandos disponibles: {list(self.commands.keys())}")

    def run(self):
        """Ejecutar el asistente de voz"""
        try:
            print("\n🚀 Iniciando asistente de voz...")
            self._set_state(AssistantState.IDLE)
            
            # Iniciar hilo de procesamiento de audio/botón
            audio_thread = threading.Thread(target=self._process_audio_for_wakeword, daemon=True)
            audio_thread.start()
            
            # Verificar si tenemos modelos de audio
            if self.active_models:
                print("🎧 Verificando dispositivos de audio...")
                try:
                    devices = sd.query_devices()
                    print(f"📋 Dispositivos de audio encontrados: {len(devices)}")
                    
                    # Buscar dispositivo de entrada por defecto
                    default_input = sd.default.device[0] if sd.default.device[0] is not None else 0
                    print(f"🎤 Dispositivo de entrada por defecto: {default_input}")
                    
                    # Verificar si el dispositivo soporta la configuración deseada
                    try:
                        sd.check_input_settings(
                            device=default_input,
                            channels=AUDIO_CHANNELS,
                            samplerate=AUDIO_SAMPLE_RATE,
                            dtype='float32'
                        )
                        print(f"✅ Configuración de audio verificada: {AUDIO_SAMPLE_RATE}Hz, {AUDIO_CHANNELS} canal")
                    except Exception as e:
                        print(f"⚠️ Configuración no soportada: {e}")
                        print("🔄 Probando configuraciones alternativas...")
                        
                        # Intentar con diferentes frecuencias de muestreo
                        sample_rates = [16000, 44100, 48000, 22050, 8000]
                        working_rate = None
                        
                        for rate in sample_rates:
                            try:
                                sd.check_input_settings(
                                    device=default_input,
                                    channels=AUDIO_CHANNELS,
                                    samplerate=rate,
                                    dtype='float32'
                                )
                                working_rate = rate
                                print(f"✅ Configuración alternativa encontrada: {rate}Hz")
                                break
                            except:
                                continue
                        
                        if working_rate:
                            global AUDIO_SAMPLE_RATE
                            AUDIO_SAMPLE_RATE = working_rate
                            print(f"🔧 Usando frecuencia de muestreo: {AUDIO_SAMPLE_RATE}Hz")
                        else:
                            print("❌ No se encontró configuración de audio compatible")
                            print("🔄 Funcionando solo con botón GPIO")
                            raise RuntimeError("No hay configuración de audio compatible")
                            
                except Exception as e:
                    print(f"⚠️ Error verificando audio: {e}")
                    print("🔄 Funcionando solo con botón GPIO")
                
                # Iniciar captura de audio con configuración verificada
                try:
                    with sd.InputStream(
                        channels=AUDIO_CHANNELS,
                        samplerate=AUDIO_SAMPLE_RATE,
                        dtype='float32',
                        blocksize=AUDIO_CHUNK_SIZE,
                        callback=self._audio_callback,
                        device=default_input
                    ):
                        print("🎧 Captura de audio iniciada")
                        print("👂 Escuchando wake words y botón GPIO...")
                        print("💡 Presiona Ctrl+C para detener")
                        
                        # Loop principal con audio
                        while not self.should_stop:
                            time.sleep(0.1)
                            
                except Exception as audio_error:
                    print(f"❌ Error específico de audio: {audio_error}")
                    print("🔧 Funcionando solo con botón GPIO...")
                    
                    # Modo sin audio: solo botón GPIO
                    print("🔘 Funcionando solo con botón GPIO (sin audio)")
                    print("💡 Presiona el botón GPIO 22 para activar el asistente")
                    print("💡 Presiona Ctrl+C para detener")
                    
                    while not self.should_stop:
                        time.sleep(0.1)
            else:
                # Modo sin modelos de audio: solo botón GPIO
                print("🔘 Funcionando solo con botón GPIO (sin modelos de audio)")
                print("💡 Presiona el botón GPIO 22 para activar el asistente")
                print("💡 Presiona Ctrl+C para detener")
                
                while not self.should_stop:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo asistente...")
        except Exception as e:
            print(f"❌ Error en el bucle principal: {e}")
        finally:
            self._cleanup()

    def _cleanup(self):
        """Limpiar recursos al salir"""
        print("🧹 Limpiando recursos...")
        self.should_stop = True
        
        try:
            # Apagar LEDs
            GPIO.output(LED_IDLE, GPIO.LOW)
            GPIO.output(LED_RECORD, GPIO.LOW)
            # Limpiar GPIO
            GPIO.cleanup()
            print("✅ GPIO limpiado")
        except:
            pass

def main():
    """Función principal"""
    try:
        assistant = VoiceAssistant()
        assistant.run()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
