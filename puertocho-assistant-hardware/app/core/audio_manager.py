"""
Módulo para la gestión de audio, incluyendo grabación y reproducción.

Este módulo define la clase AudioManager, que encapsula la lógica para interactuar
con los dispositivos de audio del sistema utilizando la librería sounddevice.
Permite la enumeración de dispositivos, la selección de un dispositivo de entrada
y la gestión de flujos de audio para grabación.
"""

import sounddevice as sd
import numpy as np
import logging
from typing import Optional, Dict, Any
from config import config

# Configuración del logger
logger = logging.getLogger(__name__)

class AudioManager:
    """
    Gestiona la grabación y reproducción de audio.
    """

    def __init__(self, input_device_index: Optional[int] = None):
        """
        Inicializa el AudioManager usando la configuración desde config.py.

        Args:
            input_device_index (Optional[int]): El índice del dispositivo de entrada a utilizar.
                                                Si es None, se detectará automáticamente por nombre.
        """
        # Usar configuración desde config.py
        self.sample_rate = config.audio.sample_rate
        self.channels = config.audio.channels
        self.chunk_size = config.audio.chunk_size
        self.buffer_size = config.audio.buffer_size
        self.device_name = config.audio.device_name
        
        # Si no se especifica un dispositivo, buscar por nombre
        if input_device_index is None:
            input_device_index = self._find_device_by_name(self.device_name)
        
        self.input_device_index = input_device_index
        self.stream = None
        self.is_recording = False

        self._validate_device()

    def _find_device_by_name(self, device_name: str) -> Optional[int]:
        """
        Busca un dispositivo de audio por nombre.
        
        Args:
            device_name (str): Nombre del dispositivo a buscar.
            
        Returns:
            Optional[int]: Índice del dispositivo encontrado o None.
        """
        try:
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                if device_name.lower() in device['name'].lower() and device['max_input_channels'] > 0:
                    logger.info(f"Dispositivo encontrado: {device['name']} (índice: {i})")
                    return i
            
            logger.warning(f"Dispositivo '{device_name}' no encontrado, usando dispositivo por defecto")
            return None
        except Exception as e:
            logger.error(f"Error al buscar dispositivo por nombre: {e}")
            return None

    def _validate_device(self):
        """
        Valida que el dispositivo de entrada seleccionado es válido.
        """
        try:
            if self.input_device_index is not None:
                sd.check_input_settings(device=self.input_device_index, channels=self.channels, samplerate=self.sample_rate)
            else:
                sd.check_input_settings(channels=self.channels, samplerate=self.sample_rate)
            logger.info(f"Dispositivo de audio de entrada validado correctamente (Índice: {self.input_device_index}).")
        except sd.PortAudioError as e:
            logger.error(f"Error al validar el dispositivo de audio: {e}")
            raise

    @staticmethod
    def list_audio_devices() -> Dict[str, Any]:
        """
        Lista los dispositivos de audio disponibles en el sistema.

        Returns:
            Dict[str, Any]: Un diccionario con los dispositivos de entrada y salida.
        """
        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            output_devices = [d for d in devices if d['max_output_channels'] > 0]
            
            return {
                "input_devices": input_devices,
                "output_devices": output_devices,
                "all_devices": devices
            }
        except Exception as e:
            logger.error(f"No se pudieron listar los dispositivos de audio: {e}")
            return {}

    def start_recording(self, callback):
        """
        Inicia la grabación de audio.

        Args:
            callback (function): La función a la que se llamará con cada bloque de audio grabado.
                                 Debe aceptar dos argumentos: (indata, frames).
        """
        if self.is_recording:
            logger.warning("La grabación ya está en curso.")
            return

        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                device=self.input_device_index,
                channels=self.channels,
                blocksize=self.chunk_size,
                callback=lambda indata, frames, time, status: callback(indata, frames, status)
            )
            self.stream.start()
            self.is_recording = True
            logger.info("Grabación iniciada.")
        except Exception as e:
            logger.error(f"Error al iniciar la grabación: {e}")
            self.stream = None

    def stop_recording(self):
        """
        Detiene la grabación de audio.
        """
        if not self.is_recording or not self.stream:
            logger.warning("No hay ninguna grabación en curso para detener.")
            return

        try:
            self.stream.stop()
            self.stream.close()
            self.is_recording = False
            logger.info("Grabación detenida.")
        except Exception as e:
            logger.error(f"Error al detener la grabación: {e}")
        finally:
            self.stream = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_recording:
            self.stop_recording()

if __name__ == '__main__':
    # Ejemplo de uso y prueba del módulo
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    from config import config
    
    logging.basicConfig(level=logging.INFO)
    
    print("Configuración de audio:")
    print(f"  Sample Rate: {config.audio.sample_rate}")
    print(f"  Channels: {config.audio.channels}")
    print(f"  Chunk Size: {config.audio.chunk_size}")
    print(f"  Device Name: {config.audio.device_name}")
    
    print("\nDispositivos de audio disponibles:")
    devices_info = AudioManager.list_audio_devices()
    if devices_info:
        for i, device in enumerate(devices_info.get("all_devices", [])):
            print(f"  {i}: {device['name']}")

    try:
        # Usar configuración automática
        manager = AudioManager()

        # Callback simple para imprimir información del audio
        def audio_callback(indata: np.ndarray, frames: int, status):
            if status:
                print(f"Estado del stream: {status}")
            volume_norm = np.linalg.norm(indata) * 10
            print(f"|{'=' * int(volume_norm)}{' ' * (50 - int(volume_norm))}|")

        print("\nIniciando grabación por 5 segundos...")
        manager.start_recording(callback=audio_callback)
        sd.sleep(5000) # Grabar durante 5 segundos
        manager.stop_recording()
        print("\nGrabación finalizada.")

    except Exception as e:
        logger.error(f"No se pudo ejecutar el ejemplo: {e}")
