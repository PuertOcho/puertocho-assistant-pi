"""
Módulo para la gestión de audio, incluyendo grabación y reproducción.

Este módulo define la clase AudioManager, que encapsula la lógica para interactuar
con los dispositivos de audio del sistema utilizando la librería sounddevice.
Permite la enumeración de dispositivos, la selección de un dispositivo de entrada
y la gestión de flujos de audio para grabación.
"""

import sounddevice as sd
import numpy as np
import time
from typing import Optional, Dict, Any, Callable, List
from config import config
from utils.logger import HardwareLogger, log_audio_event, log_performance_metric
from utils.audio_buffer import CircularAudioBuffer, DualChannelBuffer

# Configuración del logger
logger = HardwareLogger("audio_manager")

class AudioManager:
    """
    Gestiona la grabación y reproducción de audio con buffers centralizados.
    
    Características principales:
    - Buffer circular continuo para monitoreo
    - Buffer dinámico para captura de voz completa  
    - Soporte dual-channel para alta calidad (44.1kHz)
    - API retrocompatible con callbacks existentes
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
        
        # Buffer circular continuo (3 segundos por defecto)
        self.continuous_buffer_duration = 3.0
        
        # Inicializar buffers según configuración
        if self.channels == 2:
            self.continuous_buffer = DualChannelBuffer(
                self.continuous_buffer_duration, 
                self.sample_rate
            )
        else:
            self.continuous_buffer = CircularAudioBuffer(
                self.continuous_buffer_duration,
                self.sample_rate,
                self.channels
            )
        
        # Buffer dinámico para captura de voz completa
        self.dynamic_audio_chunks: List[np.ndarray] = []
        self.is_capturing_voice = False
        self.capture_start_time = None
        
        # Callback externo para retrocompatibilidad
        self.external_callback: Optional[Callable] = None
        
        # Métricas de rendimiento
        self.last_level_calculation = 0
        self.current_audio_level = 0.0

        self._validate_device()
        
        log_audio_event("audio_manager_initialized", {
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "buffer_duration": self.continuous_buffer_duration,
            "buffer_type": "DualChannelBuffer" if self.channels == 2 else "CircularAudioBuffer"
        })

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

        # Guardar callback externo para retrocompatibilidad
        self.external_callback = callback

        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                device=self.input_device_index,
                channels=self.channels,
                blocksize=self.chunk_size,
                callback=self._internal_audio_callback
            )
            self.stream.start()
            self.is_recording = True
            logger.info("Grabación iniciada.")
            log_audio_event("recording_started", {
                "sample_rate": self.sample_rate,
                "channels": self.channels,
                "chunk_size": self.chunk_size
            })
        except Exception as e:
            logger.error(f"Error al iniciar la grabación: {e}")
            self.stream = None

    def _internal_audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """
        Callback interno que maneja buffers y llama al callback externo.
        
        Args:
            indata: Datos de audio de entrada
            frames: Número de frames
            time_info: Información temporal
            status: Estado del stream
        """
        if status:
            logger.warning(f"Estado del stream de audio: {status}")
        
        # Convertir a float32 para consistencia
        audio_data = indata.astype(np.float32)
        
        # Escribir al buffer circular continuo
        if self.channels == 2:
            self.continuous_buffer.write_stereo(audio_data)
        else:
            self.continuous_buffer.write(audio_data.flatten())
        
        # Si estamos capturando voz dinámicamente, añadir al buffer dinámico
        if self.is_capturing_voice:
            self.dynamic_audio_chunks.append(audio_data.copy())
        
        # Calcular nivel de audio para monitoreo
        self._update_audio_level(audio_data)
        
        # Llamar al callback externo para retrocompatibilidad
        if self.external_callback:
            self.external_callback(indata, frames, status)
    
    def _update_audio_level(self, audio_data: np.ndarray):
        """
        Actualiza el nivel de audio actual para monitoreo.
        
        Args:
            audio_data: Datos de audio para calcular nivel
        """
        current_time = time.time()
        
        # Calcular nivel cada 100ms para evitar overhead
        if current_time - self.last_level_calculation > 0.1:
            if len(audio_data.shape) > 1:
                # Audio multicanal - usar RMS promedio
                self.current_audio_level = np.sqrt(np.mean(audio_data ** 2))
            else:
                # Audio mono - usar RMS directo
                self.current_audio_level = np.sqrt(np.mean(audio_data ** 2))
            
            self.last_level_calculation = current_time

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

    # =============================================================================
    # NUEVOS MÉTODOS - GESTIÓN DE BUFFERS CENTRALIZADA
    # =============================================================================
    
    def start_voice_capture(self):
        """
        Inicia la captura dinámica de voz completa.
        Se almacenarán todos los chunks hasta stop_voice_capture().
        """
        if not self.is_recording:
            logger.warning("Debe estar grabando para iniciar captura de voz")
            return False
        
        self.is_capturing_voice = True
        self.capture_start_time = time.time()
        self.dynamic_audio_chunks.clear()
        
        log_audio_event("voice_capture_started", {
            "timestamp": self.capture_start_time
        })
        return True
    
    def stop_voice_capture(self) -> Optional[np.ndarray]:
        """
        Detiene la captura de voz y retorna el audio completo.
        
        Returns:
            Optional[np.ndarray]: Audio capturado completo o None si no había captura activa
        """
        if not self.is_capturing_voice:
            logger.warning("No hay captura de voz activa")
            return None
        
        self.is_capturing_voice = False
        capture_duration = time.time() - self.capture_start_time if self.capture_start_time else 0
        
        if not self.dynamic_audio_chunks:
            logger.warning("No se capturó audio durante la sesión de voz")
            return None
        
        # Concatenar todos los chunks capturados
        complete_audio = np.concatenate(self.dynamic_audio_chunks, axis=0)
        
        log_audio_event("voice_capture_completed", {
            "duration_seconds": capture_duration,
            "samples_captured": len(complete_audio),
            "audio_size_mb": complete_audio.nbytes / (1024 * 1024)
        })
        
        # Limpiar buffer dinámico
        self.dynamic_audio_chunks.clear()
        
        return complete_audio
    
    def get_buffered_audio(self, seconds: float = None, samples: int = None) -> Optional[np.ndarray]:
        """
        Recupera audio del buffer circular continuo.
        
        Args:
            seconds (float, optional): Segundos de audio a recuperar
            samples (int, optional): Número específico de muestras (tiene prioridad sobre seconds)
            
        Returns:
            Optional[np.ndarray]: Audio recuperado o None si no hay suficientes datos
        """
        if samples is not None:
            if self.channels == 2:
                # Para DualChannelBuffer, devolver ambos canales combinados
                left_data = self.continuous_buffer.read_latest_mono('left', samples)
                right_data = self.continuous_buffer.read_latest_mono('right', samples)
                
                if left_data is not None and right_data is not None:
                    # Combinar canales: intercalar L,R,L,R...
                    stereo_data = np.zeros((len(left_data), 2), dtype=np.float32)
                    stereo_data[:, 0] = left_data
                    stereo_data[:, 1] = right_data
                    return stereo_data
                return None
            else:
                return self.continuous_buffer.read_latest(samples)
        
        elif seconds is not None:
            if self.channels == 2:
                return self._get_stereo_seconds(seconds)
            else:
                return self.continuous_buffer.read_latest_seconds(seconds)
        
        else:
            logger.warning("Debe especificar 'seconds' o 'samples' para get_buffered_audio")
            return None
    
    def _get_stereo_seconds(self, seconds: float) -> Optional[np.ndarray]:
        """
        Helper para obtener audio estéreo por duración.
        
        Args:
            seconds: Segundos de audio a obtener
            
        Returns:
            Audio estéreo combinado o None
        """
        left_data = self.continuous_buffer.read_latest_mono_seconds('left', seconds)
        right_data = self.continuous_buffer.read_latest_mono_seconds('right', seconds)
        
        if left_data is not None and right_data is not None:
            stereo_data = np.zeros((len(left_data), 2), dtype=np.float32)
            stereo_data[:, 0] = left_data
            stereo_data[:, 1] = right_data
            return stereo_data
        return None
    
    def clear_buffer(self):
        """
        Limpia todos los buffers de audio.
        """
        self.continuous_buffer.clear()
        self.dynamic_audio_chunks.clear()
        self.is_capturing_voice = False
        self.capture_start_time = None
        
        log_audio_event("buffers_cleared", {
            "timestamp": time.time()
        })
    
    def get_recording_level(self) -> float:
        """
        Obtiene el nivel de volumen actual de grabación.
        Útil para feedback visual en LEDs.
        
        Returns:
            float: Nivel RMS normalizado (0.0 - 1.0)
        """
        return min(1.0, self.current_audio_level * 10)  # Escalar para mejor visualización
    
    def get_buffer_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de los buffers de audio.
        
        Returns:
            Dict con estadísticas detalladas
        """
        if self.channels == 2:
            continuous_stats = self.continuous_buffer.get_combined_stats()
        else:
            continuous_stats = self.continuous_buffer.get_stats()
        
        return {
            "continuous_buffer": continuous_stats,
            "dynamic_capture": {
                "is_capturing": self.is_capturing_voice,
                "chunks_count": len(self.dynamic_audio_chunks),
                "capture_start_time": self.capture_start_time
            },
            "current_audio_level": self.current_audio_level,
            "is_recording": self.is_recording
        }
    
    def is_buffer_ready(self) -> bool:
        """
        Verifica si el buffer continuo está listo para procesamiento.
        
        Returns:
            bool: True si hay suficientes datos en el buffer
        """
        if self.channels == 2:
            return self.continuous_buffer.are_both_ready()
        else:
            return self.continuous_buffer.is_ready()

    # =============================================================================
    # MÉTODOS DE REPRODUCCIÓN (Pendientes para fases posteriores)
    # =============================================================================
    
    def play_audio(self, audio_data: np.ndarray) -> bool:
        """
        Reproduce audio de forma síncrona.
        
        Args:
            audio_data: Datos de audio a reproducir
            
        Returns:
            bool: True si la reproducción fue exitosa
        """
        # TODO: Implementar en fases posteriores
        logger.warning("play_audio() no implementado aún - pendiente para fases posteriores")
        return False
    
    def play_audio_async(self, audio_data: np.ndarray, callback: Callable = None) -> bool:
        """
        Reproduce audio de forma asíncrona con callback opcional.
        
        Args:
            audio_data: Datos de audio a reproducir
            callback: Función a llamar cuando termine la reproducción
            
        Returns:
            bool: True si se inició la reproducción
        """
        # TODO: Implementar en fases posteriores  
        logger.warning("play_audio_async() no implementado aún - pendiente para fases posteriores")
        return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_recording:
            self.stop_recording()

if __name__ == '__main__':
    # Ejemplo de uso y prueba del módulo actualizado
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    from config import config
    
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
            # El nivel se calcula internamente ahora
            level = manager.get_recording_level()
            bar_length = int(level * 50)
            print(f"|{'=' * bar_length}{' ' * (50 - bar_length)}| Nivel: {level:.3f}")

        print("\n=== DEMO: Capacidades nuevas del AudioManager ===")
        
        print("\n1. Iniciando grabación con buffer continuo...")
        manager.start_recording(callback=audio_callback)
        sd.sleep(2000)  # Llenar buffer
        
        print("\n2. Testeando buffer continuo...")
        buffer_stats = manager.get_buffer_stats()
        print(f"   Buffer listo: {manager.is_buffer_ready()}")
        print(f"   Estadísticas: {buffer_stats['continuous_buffer']}")
        
        print("\n3. Recuperando últimos 1.5 segundos de audio...")
        recent_audio = manager.get_buffered_audio(seconds=1.5)
        if recent_audio is not None:
            print(f"   Audio recuperado: {recent_audio.shape}, tipo: {recent_audio.dtype}")
        
        print("\n4. Iniciando captura de voz dinámica...")
        manager.start_voice_capture()
        sd.sleep(2000)  # Simular habla
        
        print("\n5. Finalizando captura y obteniendo audio completo...")
        complete_voice = manager.stop_voice_capture()
        if complete_voice is not None:
            print(f"   Voz capturada: {complete_voice.shape}, duración: {len(complete_voice)/config.audio.sample_rate:.2f}s")
        
        print("\n6. Estadísticas finales...")
        final_stats = manager.get_buffer_stats()
        print(f"   Nivel actual: {manager.get_recording_level():.3f}")
        print(f"   Buffer continuo listo: {manager.is_buffer_ready()}")
        
        manager.stop_recording()
        print("\n=== Demo completada exitosamente ===")

    except Exception as e:
        logger.error(f"No se pudo ejecutar el ejemplo: {e}")
        print(f"Error en demo: {e}")
