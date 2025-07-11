"""
Gestión de configuración centralizada para el asistente PuertoCho.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Obtener la ruta base del proyecto (directorio que contiene 'app')
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

def load_env_variables():
    """Cargar variables de entorno desde archivo .env si existe"""
    try:
        from dotenv import load_dotenv
        
        # Buscar .env en diferentes ubicaciones
        env_locations = [
            PROJECT_ROOT / '.env',
            PROJECT_ROOT.parent / '.env',
            Path.cwd() / '.env'
        ]
        
        for env_file in env_locations:
            if env_file.exists():
                load_dotenv(env_file)
                print(f"✅ Variables cargadas desde {env_file}")
                return True
        
        print("ℹ️  No se encontró archivo .env, usando variables de entorno del sistema")
        return False
        
    except ImportError:
        print("ℹ️  python-dotenv no instalado, usando variables de entorno del sistema")
        return False

class Config:
    """Configuración centralizada del asistente"""
    
    def __init__(self):
        # Cargar variables de entorno
        load_env_variables()
        
        # Configuración de Porcupine
        self.porcupine_access_key = os.getenv('PORCUPINE_ACCESS_KEY')
        
        # URLs de servicios
        self.assistant_chat_url = os.getenv(
            'ASSISTANT_CHAT_URL', 
            'http://192.168.1.88:8080/api/assistant/chat'
        )
        self.transcription_service_url = os.getenv(
            'TRANSCRIPTION_SERVICE_URL', 
            'http://192.168.1.88:5000/transcribe'
        )
        self.backend_websocket_url = os.getenv(
            'BACKEND_WEBSOCKET_URL',
            'ws://localhost:8765/ws'
        )
        
        # Configuración de GPIO
        self.button_pin = int(os.getenv('BUTTON_PIN', 22))
        self.led_idle_pin = int(os.getenv('LED_IDLE_PIN', 17))
        self.led_record_pin = int(os.getenv('LED_RECORD_PIN', 27))
        
        # Configuración de audio
        self.porcupine_rate = 16000
        self.channels = 1
        self.chunk_size = 512
        self.frame_length = self.chunk_size
        self.audio_device_index = self._detect_audio_device()  # Detectar dispositivo automáticamente
        
        # Rutas de archivos
        self.commands_file = PROJECT_ROOT / 'app' / 'commands.json'
        self.model_file = PROJECT_ROOT / 'app' / 'Puerto-ocho_es_raspberry-pi_v3_0_0.ppn'
        self.params_file = PROJECT_ROOT / 'app' / 'porcupine_params_es.pv'
        
        # Validar configuración crítica
        self._validate_config()
    
    def _validate_config(self):
        """Validar configuración crítica"""
        if not self.porcupine_access_key:
            raise ValueError(
                "❌ ERROR: PORCUPINE_ACCESS_KEY no configurada. "
                "Configúrala en el archivo .env o como variable de entorno."
            )
        
        # Verificar archivos críticos
        critical_files = {
            'commands.json': self.commands_file,
            'modelo personalizado': self.model_file,
            'parámetros': self.params_file
        }
        
        for file_desc, file_path in critical_files.items():
            if not file_path.exists():
                print(f"⚠️  Archivo {file_desc} no encontrado: {file_path}")
    
    def _detect_audio_device(self) -> int:
        """Detectar automáticamente el dispositivo de audio correcto"""
        try:
            import sounddevice as sd
            
            # Primero intentar usar la variable de entorno si está definida
            env_device = os.getenv('AUDIO_DEVICE_INDEX')
            if env_device is not None:
                try:
                    device_index = int(env_device)
                    # Verificar que el dispositivo existe y tiene entrada
                    devices = sd.query_devices()
                    if device_index < len(devices) and devices[device_index]['max_input_channels'] > 0:
                        print(f"🎵 Usando dispositivo de audio configurado: {device_index}")
                        return device_index
                except ValueError:
                    pass
            
            # Si no hay variable de entorno o no funciona, buscar automáticamente
            devices = sd.query_devices()
            print("🔍 Detectando dispositivos de audio...")
            
            # Buscar dispositivos con entrada (micrófonos)
            input_devices = []
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    input_devices.append((i, device))
                    print(f"  {i}: {device['name']} (INPUT: {device['max_input_channels']} canales)")
            
            if not input_devices:
                print("⚠️ No se encontraron dispositivos de entrada, usando default")
                return None  # Usar default
            
            # En lugar de probar cada dispositivo, usar el primero disponible
            # Esto evita conflictos de acceso al dispositivo
            device_index, device = input_devices[0]
            print(f"✅ Usando primer dispositivo disponible: {device_index} - {device['name']}")
            return device_index
            
        except ImportError:
            print("⚠️ sounddevice no disponible, usando default")
            return None
        except Exception as e:
            print(f"⚠️ Error detectando audio: {e}, usando default")
            return None

    def get_project_root(self) -> Path:
        """Obtener la ruta raíz del proyecto"""
        return PROJECT_ROOT
    
    def test_audio_device(self):
        """Probar el dispositivo de audio específico"""
        try:
            import sounddevice as sd
            device_text = f"por defecto" if self.audio_device_index is None else f"{self.audio_device_index}"
            print(f"🔧 Probando dispositivo de audio {device_text}...")
            
            # Verificar que el dispositivo existe
            devices = sd.query_devices()
            if self.audio_device_index is not None and self.audio_device_index >= len(devices):
                print(f"❌ El dispositivo {self.audio_device_index} no existe")
                return False
            
            if self.audio_device_index is not None:
                device = devices[self.audio_device_index]
                print(f"📱 Dispositivo: {device['name']}")
                print(f"🎤 Canales de entrada: {device['max_input_channels']}")
                print(f"🔊 Canales de salida: {device['max_output_channels']}")
                
                if device['max_input_channels'] == 0:
                    print("❌ El dispositivo no tiene canales de entrada")
                    return False
            else:
                print("📱 Usando dispositivo por defecto del sistema")
            
            # Probar grabación rápida
            try:
                with sd.RawInputStream(
                    samplerate=44100,
                    blocksize=512,
                    dtype='int16',
                    channels=1,
                    device=self.audio_device_index
                ) as stream:
                    data = stream.read(512)
                    print("✅ Prueba de grabación exitosa")
                    return True
            except Exception as e:
                print(f"❌ Error en prueba de grabación: {e}")
                return False
                
        except ImportError:
            print("⚠️ sounddevice no disponible para probar audio")
            return False

    def list_audio_devices(self):
        """Listar dispositivos de audio disponibles"""
        try:
            import sounddevice as sd
            print("🎵 Dispositivos de audio disponibles:")
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                device_type = []
                if device['max_input_channels'] > 0:
                    device_type.append("INPUT")
                if device['max_output_channels'] > 0:
                    device_type.append("OUTPUT")
                print(f"  {i}: {device['name']} ({', '.join(device_type)})")
            return devices
        except ImportError:
            print("⚠️ sounddevice no disponible para listar dispositivos")
            return []

    def detect_supported_sample_rate(self) -> int:
        """Detectar qué tasa de muestreo soporta el dispositivo"""
        try:
            import sounddevice as sd
            
            # Tasas comunes en orden de preferencia
            rates_to_try = [16000, 44100, 48000, 22050, 8000]
            
            device_text = f"por defecto" if self.audio_device_index is None else f"{self.audio_device_index}"
            
            for rate in rates_to_try:
                try:
                    # Probar si la tasa funciona con el dispositivo específico
                    test_stream = sd.RawInputStream(
                        samplerate=rate,
                        blocksize=512,
                        dtype='int16',
                        channels=1,
                        device=self.audio_device_index
                    )
                    test_stream.close()
                    print(f"✅ Tasa de audio soportada detectada: {rate} Hz (device {device_text})")
                    return rate
                except Exception as e:
                    print(f"⚠️ Tasa {rate} Hz no soportada: {e}")
                    continue
            
            # Si ninguna funciona, usar 44100 como fallback
            print("⚠️ Usando 44100 Hz como fallback")
            return 44100
            
        except ImportError:
            print("⚠️ sounddevice no disponible, usando 16000 Hz")
            return 16000

    def validate(self) -> bool:
        """Validar configuración completa"""
        try:
            self._validate_config()
            return True
        except Exception as e:
            print(f"❌ Validación fallida: {e}")
            return False
    
    def get_assistant_endpoint(self) -> str:
        """Obtener endpoint del asistente"""
        return self.assistant_chat_url
    
    def get_audio_config(self) -> str:
        """Obtener configuración de audio como string"""
        sample_rate = self.detect_supported_sample_rate()
        device_text = f"device {self.audio_device_index}" if self.audio_device_index is not None else "default device"
        return f"{sample_rate} Hz ({device_text})"

# Instancia global de configuración
config = Config()
