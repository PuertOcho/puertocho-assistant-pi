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
    
    def get_project_root(self) -> Path:
        """Obtener la ruta raíz del proyecto"""
        return PROJECT_ROOT
    
    def detect_supported_sample_rate(self) -> int:
        """Detectar qué tasa de muestreo soporta el dispositivo"""
        try:
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
            
        except ImportError:
            print("⚠️ sounddevice no disponible, usando 16000 Hz")
            return 16000

# Instancia global de configuración
config = Config()
