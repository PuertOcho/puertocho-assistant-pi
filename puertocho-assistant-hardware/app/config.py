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
        
        # URLs de servicios - Solo backend
        self.backend_url = os.getenv(
            'BACKEND_URL', 
            'http://localhost:8000'
        )
        self.backend_audio_endpoint = f"{self.backend_url}/api/v1/audio/process"
        self.backend_hardware_status_endpoint = f"{self.backend_url}/api/v1/hardware/status"
        
        # Configuración de GPIO - ReSpeaker 2-Mic Pi HAT V1.0
        # Pines ocupados por el módulo:
        # - Audio: WM8960 codec (I2S)
        # - RGB LEDs: 3 APA102 RGB LEDs (SPI)
        # - Botón: GPIO17 (por defecto en el módulo)
        # - Micrófonos: Mic L y Mic R (estéreo)
        
        # Pines disponibles para expansión:
        # - Grove I2C: GPIO2 (SDA), GPIO3 (SCL) 
        # - Grove GPIO12: GPIO12 y GPIO13
        
        # Configuración del botón integrado del módulo
        self.button_pin = int(os.getenv('BUTTON_PIN', 17))  # Botón integrado del ReSpeaker
        
        # LEDs externos opcionales (no usar los APA102 del módulo por ahora)
        # Estos pueden conectarse a los pines Grove disponibles
        self.led_idle_pin = int(os.getenv('LED_IDLE_PIN', 12))    # Grove GPIO12
        self.led_record_pin = int(os.getenv('LED_RECORD_PIN', 13))  # Grove GPIO13
        
        # Configuración I2C para expansiones futuras
        self.i2c_sda_pin = 2  # Grove I2C SDA
        self.i2c_scl_pin = 3  # Grove I2C SCL
        
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
            
            # Si no hay variable de entorno, buscar automáticamente
            devices = sd.query_devices()
            print("🔍 Detectando dispositivos de audio...")
            
            # Buscar específicamente el ReSpeaker (seeed-voicecard)
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    device_name = device['name'].lower()
                    if 'seeed' in device_name or 'voicecard' in device_name or 'respeaker' in device_name:
                        print(f"✅ ReSpeaker detectado: {i} - {device['name']}")
                        return i
            
            # Si no se encuentra ReSpeaker, buscar dispositivos con entrada
            input_devices = []
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    input_devices.append((i, device))
                    print(f"  {i}: {device['name']} (INPUT: {device['max_input_channels']} canales)")
            
            if not input_devices:
                print("⚠️ No se encontraron dispositivos de entrada, usando default")
                return None  # Usar default
            
            # Usar el primer dispositivo disponible
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
    
    def get_backend_endpoint(self) -> str:
        """Obtener endpoint del backend"""
        return self.backend_url
    
    def get_audio_config(self) -> str:
        """Obtener configuración de audio como string"""
        sample_rate = self.detect_supported_sample_rate()
        device_text = f"device {self.audio_device_index}" if self.audio_device_index is not None else "default device"
        
        # Detectar si es ReSpeaker
        respeaker_info = self.detect_respeaker()
        if respeaker_info:
            return f"{sample_rate} Hz (ReSpeaker {respeaker_info} - device {self.audio_device_index})"
        else:
            return f"{sample_rate} Hz ({device_text})"
    
    def detect_respeaker(self) -> Optional[str]:
        """Detectar si hay un módulo ReSpeaker conectado"""
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            
            for device in devices:
                device_name = device['name'].lower()
                if 'seeed' in device_name or 'voicecard' in device_name:
                    return "2-Mic Pi HAT V1.0"
                elif 'respeaker' in device_name:
                    return "detected"
            
            return None
            
        except ImportError:
            return None
        except Exception:
            return None

# Instancia global de configuración
config = Config()
