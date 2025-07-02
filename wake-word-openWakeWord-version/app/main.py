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

def detect_supported_sample_rate():
    """Detectar automáticamente la frecuencia de muestreo soportada por el sistema (como Porcupine)"""
    print("🔍 Detectando frecuencia de audio compatible...")
    
    # Probar diferentes frecuencias en orden de preferencia
    sample_rates = [16000, 44100, 48000, 22050, 8000]
    
    for rate in sample_rates:
        try:
            print(f"   Probando {rate} Hz...")
            
            # Crear stream de prueba muy breve (igual que Porcupine)
            test_stream = sd.RawInputStream(
                samplerate=rate,
                blocksize=512,
                dtype='int16',
                channels=1
            )
            
            with test_stream:
                # Si llega aquí, la configuración funciona
                print(f"✅ Frecuencia compatible encontrada: {rate} Hz")
                return rate
                
        except Exception as e:
            print(f"   ❌ {rate} Hz no compatible: {e}")
            continue
    
    # Si nada funciona, usar fallback
    print("⚠️ Usando frecuencia por defecto: 16000 Hz")
    return 16000

# Detectar la mejor frecuencia de muestreo automáticamente
DETECTED_SAMPLE_RATE = detect_supported_sample_rate()
DETECTED_CHUNK_SIZE = 512 if DETECTED_SAMPLE_RATE == 16000 else int(512 * (DETECTED_SAMPLE_RATE / 16000))

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

# Configuración openWakeWord (se cargarán dinámicamente)
OPENWAKEWORD_THRESHOLD = float(os.getenv('OPENWAKEWORD_THRESHOLD', 0.6))
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
        
        # Verificar si debemos intentar usar modelos de audio
        mode = os.getenv('MODE', 'HYBRID').upper()
        if mode == 'GPIO_ONLY':
            print("🔧 Modo GPIO_ONLY activado - funcionará solo con botón GPIO")
            self.oww_model = None
            self.active_models = []
            return
        
        try:
            import openwakeword
            from openwakeword.model import Model
            
            print("🔄 Inicializando openWakeWord...")
            
            # Verificar si los modelos están especificados
            model_paths = os.getenv('OPENWAKEWORD_MODEL_PATHS', '').strip()
            if not model_paths:
                print("🔧 OPENWAKEWORD_MODEL_PATHS vacío - usando todos los modelos preentrenados")
            # Continuar con la inicialización en ambos casos
            
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
            
            # Configurar parámetros del modelo (forzar ONNX para evitar problemas con TFLite)
            model_kwargs = {
                'inference_framework': 'onnx'  # Forzar ONNX debido a incompatibilidad NumPy con TFLite
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
                # Obtener modelos dinámicamente del .env
                model_paths_env = os.getenv('OPENWAKEWORD_MODEL_PATHS', '').strip()
                
                if model_paths_env:
                    # Usar modelos específicos
                    model_paths_list = [m.strip() for m in model_paths_env.split(',') if m.strip()]
                    model_kwargs['wakeword_models'] = model_paths_list
                    print(f"🔄 Intentando cargar modelos específicos: {model_paths_list}")
                else:
                    # Usar todos los modelos preentrenados (no especificar wakeword_models)
                    print("✅ Usando todos los modelos preentrenados disponibles")
                
                # Crear modelo
                self.oww_model = Model(**model_kwargs)
                
                # Obtener lista de modelos activos (verificar en models, no en prediction_buffer)
                self.active_models = list(self.oww_model.models.keys()) if hasattr(self.oww_model, 'models') and self.oww_model.models else []
                print(f"✅ openWakeWord inicializado con {len(self.active_models)} modelos")
                if self.active_models:
                    print(f"🎯 Modelos activos: {', '.join(self.active_models)}")
                    print(f"🎚️ Umbral de activación: {OPENWAKEWORD_THRESHOLD}")
                    print("🎙️ Wake words disponibles:")
                    for model in self.active_models:
                        if model in ['alexa']:
                            print("   • Di 'Alexa' para activar")
                        elif model in ['hey_mycroft']:
                            print("   • Di 'Hey Mycroft' para activar")
                        elif model in ['hey_jarvis']:
                            print("   • Di 'Hey Jarvis' para activar")
                        elif model in ['timer']:
                            print("   • Di comandos de timer para activar")
                        elif model in ['weather']:
                            print("   • Di comandos de clima para activar")
                else:
                    print("⚠️ No se cargaron modelos - funcionará solo con botón GPIO")
                
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
        mode = os.getenv('MODE', 'HYBRID').upper()
        print("\n📋 CONFIGURACIÓN ACTUAL:")
        print(f"🎤 Audio: {AUDIO_SAMPLE_RATE}Hz, {AUDIO_CHANNELS} canal, chunks de {AUDIO_CHUNK_SIZE} samples")
        print(f"⚙️  Modo: {mode}")
        
        if self.active_models:
            print(f"🧠 Modelos activos: {', '.join(self.active_models)}")
            print(f"🎚️ Umbral: {OPENWAKEWORD_THRESHOLD}")
            print(f"🔊 VAD: {'Habilitado' if OPENWAKEWORD_VAD_THRESHOLD > 0 else 'Deshabilitado'}")
            print(f"🔇 Speex NS: {'Habilitado' if OPENWAKEWORD_ENABLE_SPEEX_NS else 'Deshabilitado'}")
            print("🎙️  Wake Words: Habilitadas")
        else:
            print("🧠 Modelos de audio: No disponibles")
            print("🎙️  Wake Words: Deshabilitadas")
            
        print(f"🔴 LED Rojo (GPIO {LED_RECORD}): Escuchando")
        print(f"🟢 LED Verde (GPIO {LED_IDLE}): Listo")
        print(f"🔘 Botón (GPIO {BUTTON_PIN}): Activación manual")
        print(f"🤖 Transcripción: {TRANSCRIPTION_SERVICE_URL}")
        
        print("\n💡 OPCIONES DE ACTIVACIÓN:")
        if self.active_models:
            print("   🎙️  COMANDOS DE VOZ:")
            for model in self.active_models:
                if model == 'alexa':
                    print("      - Di 'Alexa' para activar")
                elif model == 'hey_mycroft':
                    print("      - Di 'Hey Mycroft' para activar") 
                elif model == 'hey_jarvis':
                    print("      - Di 'Hey Jarvis' para activar")
        print("   🔘 ACTIVACIÓN MANUAL:")
        print("      - Presiona el botón GPIO 22")
        print("   📊 INDICADORES:")
        print("      - LED verde: Listo para comandos")
        print("      - LED rojo: Escuchando/procesando")

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

    def _audio_callback_raw(self, indata, frames, time_info, status):
        """Callback simplificado para RawInputStream (igual que Porcupine)"""
        if status:
            if 'input overflow' in str(status):
                # Solo mostrar overflow ocasionalmente
                if not hasattr(self, '_last_overflow_time') or time.time() - self._last_overflow_time > 5:
                    print(f"⚠️ Audio overflow detectado")
                    self._last_overflow_time = time.time()
            else:
                print(f"⚠️ Status audio: {status}")
        
        # Agregar audio raw directamente a la cola (como Porcupine)
        if self.audio_buffer.qsize() < 10:
            self.audio_buffer.put(bytes(indata))
        else:
            # Si la cola está llena, descartar datos antiguos
            try:
                self.audio_buffer.get_nowait()
                self.audio_buffer.put(bytes(indata))
            except queue.Empty:
                pass

    def simple_resample(self, audio_data, original_rate, target_rate):
        """Resample simple usando interpolación lineal (copiado de Porcupine)"""
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

    def _process_audio_for_wakeword(self):
        """Procesar audio para detectar wake words usando el enfoque Porcupine"""
        # Buffer para acumular audio (como Porcupine)
        audio_buffer_raw = np.array([], dtype=np.int16)
        target_frame_length = 1280  # openWakeWord requiere 1280 frames (80ms @ 16kHz)
        
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
                
                # Obtener audio raw de la cola
                try:
                    audio_data = self.audio_buffer.get(timeout=0.1)
                    pcm = np.frombuffer(audio_data, dtype=np.int16)
                    
                    # Resample si es necesario (como Porcupine)
                    if DETECTED_SAMPLE_RATE != 16000:
                        resampled_pcm = self.simple_resample(pcm, DETECTED_SAMPLE_RATE, 16000)
                    else:
                        resampled_pcm = pcm
                    
                    # Acumular audio en buffer
                    audio_buffer_raw = np.concatenate([audio_buffer_raw, resampled_pcm])
                    
                    # Limitar el tamaño del buffer para evitar que crezca indefinidamente
                    max_buffer_size = target_frame_length * 10  # Máximo 10 frames
                    if len(audio_buffer_raw) > max_buffer_size:
                        audio_buffer_raw = audio_buffer_raw[-max_buffer_size:]
                    
                    # Procesar frames completos
                    while len(audio_buffer_raw) >= target_frame_length:
                        # Extraer exactamente el frame requerido
                        frame = audio_buffer_raw[:target_frame_length]
                        audio_buffer_raw = audio_buffer_raw[target_frame_length:]
                        
                        # Ejecutar predicción con openWakeWord
                        prediction = self.oww_model.predict(frame.astype(np.int16))
                        
                        # Debug: mostrar scores ocasionalmente
                        if not hasattr(self, '_last_debug_time'):
                            self._last_debug_time = time.time()
                            self._debug_counter = 0
                        
                        self._debug_counter += 1
                        if time.time() - self._last_debug_time > 30:  # Cada 30 segundos (menos spam)
                            max_score = max(prediction.values()) if prediction else 0
                            if max_score > 0.2:  # Solo mostrar si hay actividad significativa
                                print(f"🔍 Audio activo - alexa={prediction.get('alexa', 0):.3f}, hey_mycroft={prediction.get('hey_mycroft', 0):.3f}")
                            else:
                                print(f"🔍 Sistema funcionando (frames procesados: {self._debug_counter})")
                            self._last_debug_time = time.time()
                            self._debug_counter = 0
                        
                        # Verificar si algún modelo supera el umbral (con cooldown mejorado)
                        current_time = time.time()
                        if not hasattr(self, '_last_detection_time'):
                            self._last_detection_time = 0
                        
                        # Cooldown de 8 segundos entre detecciones (mejorado para evitar detecciones múltiples)
                        if current_time - self._last_detection_time > 8:
                            for model_name, score in prediction.items():
                                if score > OPENWAKEWORD_THRESHOLD:
                                    print(f"🎯 Wake word detectada: '{model_name}' (score: {score:.3f})")
                                    self._last_detection_time = current_time
                                    
                                    # LIMPIAR COMPLETAMENTE todos los buffers
                                    audio_buffer_raw = np.array([], dtype=np.int16)
                                    
                                    # Vaciar cola de audio completamente
                                    while not self.audio_buffer.empty():
                                        try:
                                            self.audio_buffer.get_nowait()
                                        except queue.Empty:
                                            break
                                    
                                    print("🧹 Buffers limpiados - procesando comando...")
                                    self._handle_wakeword_detected(model_name, score)
                                    
                                    # Pausa más larga para permitir que termines de hablar
                                    time.sleep(1.5)
                                    
                                    # Limpiar una vez más después del comando
                                    while not self.audio_buffer.empty():
                                        try:
                                            self.audio_buffer.get_nowait()
                                        except queue.Empty:
                                            break
                                    
                                    print("👂 Listo para nueva wake word...")
                                    break
                            else:
                                continue
                            break  # Salir del while si se detectó wake word
                            
                except queue.Empty:
                    continue
                except Exception as audio_error:
                    print(f"⚠️ Error procesando audio (continuando con botón): {audio_error}")
                    time.sleep(0.1)
                    continue
                    
            except Exception as e:
                print(f"⚠️ Error general en procesamiento: {e}")
                time.sleep(0.1)

    def _handle_wakeword_detected(self, model_name: str, score: float):
        """Manejar detección de wake word con limpieza completa"""
        print(f"🎉 Wake word '{model_name}' detectada con score {score:.3f}")
        self._set_state(AssistantState.LISTENING)
        
        # Pausa adicional para que termine la palabra "Alexa"
        time.sleep(0.3)
        
        # Limpiar cualquier residuo de audio de la wake word
        cleanup_count = 0
        while not self.audio_buffer.empty() and cleanup_count < 50:
            try:
                self.audio_buffer.get_nowait()
                cleanup_count += 1
            except queue.Empty:
                break
        
        if cleanup_count > 0:
            print(f"🧹 Limpiados {cleanup_count} frames residuales de wake word")
        
        # Grabar comando de voz
        self._handle_voice_command()
        
        # Volver al estado idle
        self._set_state(AssistantState.IDLE)
        
        # Limpieza final
        final_cleanup = 0
        while not self.audio_buffer.empty() and final_cleanup < 20:
            try:
                self.audio_buffer.get_nowait()
                final_cleanup += 1
            except queue.Empty:
                break

    def _handle_voice_command(self):
        """Grabar y procesar comando de voz (corregido para arrays raw)"""
        try:
            print("🎤 Grabando comando...")
            
            # Limpiar buffer de audio
            while not self.audio_buffer.empty():
                try:
                    self.audio_buffer.get_nowait()
                except queue.Empty:
                    break
            
            # Esperar un momento para que el buffer se llene de nuevo
            time.sleep(0.2)
            
            # Grabar por tiempo limitado
            raw_frames = []
            max_recording_time = 5  # 5 segundos máximo
            start_time = time.time()
            
            print("📢 Habla ahora...")
            
            while time.time() - start_time < max_recording_time:
                try:
                    # Obtener audio raw como bytes
                    audio_data = self.audio_buffer.get(timeout=0.2)
                    raw_frames.append(audio_data)
                    
                except queue.Empty:
                    # Si no hay audio por un tiempo, terminar grabación
                    break
            
            if raw_frames:
                # Unir todos los frames raw (bytes)
                raw_audio = b''.join(raw_frames)
                
                # Convertir a numpy array
                audio_array = np.frombuffer(raw_audio, dtype=np.int16)
                
                if len(audio_array) > 0:
                    # Crear archivo WAV
                    wav_bytes = self._create_wav_file(audio_array)
                    
                    # Enviar a transcripción
                    self._set_state(AssistantState.PROCESSING)
                    transcription = self._send_to_transcription_service(wav_bytes)
                    
                    if transcription:
                        print(f"🗣️  Transcripción: '{transcription}'")
                        self._execute_command(transcription)
                    else:
                        print("❌ No se pudo transcribir el audio")
                else:
                    print("❌ Audio grabado vacío")
            else:
                print("❌ No se grabó audio")
                
        except Exception as e:
            print(f"❌ Error procesando comando de voz: {e}")
            import traceback
            print(f"🔍 Detalles del error: {traceback.format_exc()}")

    def _create_wav_file(self, audio_data: np.ndarray) -> bytes:
        """Crear archivo WAV en memoria (compatible con RawInputStream)"""
        # Asegurar que sea int16
        if audio_data.dtype != np.int16:
            audio_data = (audio_data * 32767).astype(np.int16)
        
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono (RawInputStream es mono)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(16000)  # Siempre 16000Hz después del resample
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
        """Ejecutar el asistente de voz usando el enfoque exitoso de Porcupine"""
        global AUDIO_SAMPLE_RATE
        try:
            print("\n🚀 Iniciando asistente de voz...")
            self._set_state(AssistantState.IDLE)
            
            # Iniciar hilo de procesamiento de audio/botón usando enfoque Porcupine
            audio_thread = threading.Thread(target=self._process_audio_for_wakeword, daemon=True)
            audio_thread.start()
            print("🔄 Hilo de procesamiento de audio iniciado")
            
            # Verificar si tenemos modelos de audio
            if self.active_models:
                print("🎧 Iniciando captura de audio con enfoque Porcupine...")
                
                try:
                    # Usar RawInputStream como en Porcupine (más simple y funcional)
                    with sd.RawInputStream(
                        samplerate=DETECTED_SAMPLE_RATE,  # Frecuencia detectada automáticamente
                        blocksize=DETECTED_CHUNK_SIZE,    # Blocksize ajustado
                        dtype='int16', 
                        channels=1,
                        callback=self._audio_callback_raw
                    ):
                        print(f"✅ Audio iniciado: {DETECTED_SAMPLE_RATE}Hz, blocksize={DETECTED_CHUNK_SIZE}")
                        if DETECTED_SAMPLE_RATE == 16000:
                            print("🎵 Audio optimizado: 16000 Hz directo (sin resample)")
                        else:
                            print(f"🎵 Audio: {DETECTED_SAMPLE_RATE} Hz → resample → 16000 Hz")
                        
                        print("👂 Escuchando wake words y botón GPIO...")
                        print("💡 Presiona Ctrl+C para detener")
                        
                        # Buffer para audio (igual que Porcupine)
                        self.audio_buffer_raw = np.array([], dtype=np.int16)
                        
                        # Loop principal simplificado 
                        while not self.should_stop:
                            time.sleep(0.1)
                            
                except Exception as audio_error:
                    print(f"❌ Error de audio: {audio_error}")
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
