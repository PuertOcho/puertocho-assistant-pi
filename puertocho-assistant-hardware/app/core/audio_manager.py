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
import os
import sys
import threading
import base64
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
        
        # Si no se especifica un dispositivo, buscar por nombre o usar índice configurado
        if input_device_index is None:
            if config.audio.device_index is not None:
                input_device_index = config.audio.device_index
                logger.info(f"Usando índice de dispositivo configurado: {input_device_index}")
            else:
                input_device_index = self._find_device_by_name(self.device_name)
        
        self.input_device_index = input_device_index
        self.stream = None
        self.is_recording = False
        
        # Configuración de salida de audio para reproducción
        self.output_device_index = int(os.getenv("AUDIO_OUTPUT_DEVICE_INDEX", "0"))
        self.output_sample_rate = int(os.getenv("AUDIO_OUTPUT_SAMPLE_RATE", "44100"))
        self.audio_volume_percent = float(os.getenv("AUDIO_VOLUME_PERCENT", "30.0"))
        self.audio_volume_db = float(os.getenv("AUDIO_VOLUME_DB", "-20.0"))
        self.aplay_device = os.getenv("AUDIO_APLAY_DEVICE", "hw:0,0")
        
        # Buffer circular continuo (3 segundos por defecto)
        self.continuous_buffer_duration = 3.0
        
        # Inicializar atributos básicos antes de validación
        self.dynamic_audio_chunks: List[np.ndarray] = []
        self.is_capturing_voice = False
        self.capture_start_time = None
        self.external_callback: Optional[Callable] = None
        self.last_level_calculation = 0
        self.current_audio_level = 0.0
        
        # Inicializar estadísticas de rendimiento
        self.performance_stats = {
            'total_callbacks': 0,
            'overflow_count': 0,
            'last_stats_log': time.time(),
            'callback_times': []
        }
        
        # Validar y ajustar configuración antes de crear buffers
        self._validate_device()
        
        # Verificar dispositivo de salida
        self._validate_output_device()
        
        # Inicializar buffers según configuración validada
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
        
        log_audio_event("audio_manager_initialized", {
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "buffer_duration": self.continuous_buffer_duration,
            "buffer_type": "DualChannelBuffer" if self.channels == 2 else "CircularAudioBuffer",
            "config": {
                "chunk_size": self.chunk_size,
                "buffer_size": self.buffer_size,
                "device_name": self.device_name,
                "device_index": self.input_device_index,
                "theoretical_latency_ms": (self.chunk_size / self.sample_rate) * 1000
            }
        })
        
        # Log configuración inicial para optimización
        logger.info(f"🎵 AudioManager configurado: {self.sample_rate}Hz, {self.channels}ch, "
                   f"chunk={self.chunk_size} (latencia teórica: {(self.chunk_size / self.sample_rate) * 1000:.1f}ms)")

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
            
            # Prioridad de búsqueda para dispositivos conocidos
            priority_devices = [
                "array",      # ReSpeaker device - tiene 2 canales
                "seeed",
                "capture_in", 
                "duplex",
                "pulse",
                "default"
            ]
            
            # Primero buscar dispositivos con entrada disponible
            input_devices = [d for i, d in enumerate(devices) if d['max_input_channels'] > 0]
            
            logger.info(f"Dispositivos de entrada disponibles: {len(input_devices)}")
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    logger.info(f"  {i}: {device['name']} (canales: {device['max_input_channels']})")
            
            # Buscar por prioridad
            for priority_name in priority_devices:
                for i, device in enumerate(devices):
                    if (priority_name.lower() in device['name'].lower() and 
                        device['max_input_channels'] > 0):
                        logger.info(f"Dispositivo encontrado por prioridad: {device['name']} (índice: {i})")
                        return i
            
            # Si no encuentra ninguno por prioridad, buscar el solicitado
            for i, device in enumerate(devices):
                if device_name.lower() in device['name'].lower() and device['max_input_channels'] > 0:
                    logger.info(f"Dispositivo encontrado: {device['name']} (índice: {i})")
                    return i
            
            # Si no encuentra nada, usar el primer dispositivo con entrada
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    logger.warning(f"Usando primer dispositivo de entrada disponible: {device['name']} (índice: {i})")
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
        original_channels = self.channels
        original_sample_rate = self.sample_rate
        
        # Lista de dispositivos para probar en orden de prioridad
        devices_to_try = []
        
        if self.input_device_index is not None:
            devices_to_try.append(self.input_device_index)
        
        # Agregar dispositivos de prioridad detectados
        try:
            devices = sd.query_devices()
            priority_devices = ["array", "seeed", "capture_in", "duplex", "pulse", "default"]
            
            for priority_name in priority_devices:
                for i, device in enumerate(devices):
                    if (priority_name.lower() in device['name'].lower() and 
                        device['max_input_channels'] > 0 and 
                        i not in devices_to_try):
                        devices_to_try.append(i)
                        logger.info(f"Agregando dispositivo de prioridad para probar: {device['name']} (índice: {i})")
        except Exception as e:
            logger.warning(f"Error al obtener lista de dispositivos: {e}")
        
        # Probar dispositivos en orden
        for device_index in devices_to_try:
            try:
                logger.info(f"Probando dispositivo índice {device_index}...")
                sd.check_input_settings(
                    device=device_index, 
                    channels=self.channels, 
                    samplerate=self.sample_rate
                )
                self.input_device_index = device_index
                logger.info(f"Dispositivo {device_index} validado correctamente con {self.channels}ch@{self.sample_rate}Hz")
                return  # Éxito - salir
            except sd.PortAudioError as e:
                logger.warning(f"Dispositivo índice {device_index} falló: {e}")
                continue
        
        # Si ningún dispositivo funcionó con la configuración original, probar configuración reducida
        logger.error("Ningún dispositivo funcionó con configuración original")
        logger.info("Intentando con configuración reducida (mono, 16kHz)...")
        
        for device_index in devices_to_try:
            try:
                logger.info(f"Probando dispositivo {device_index} con configuración reducida...")
                sd.check_input_settings(device=device_index, channels=1, samplerate=16000)
                self.input_device_index = device_index
                logger.warning("Solo configuración básica disponible - ajustando parámetros")
                self.channels = 1
                self.sample_rate = 16000
                break
            except sd.PortAudioError as e:
                logger.warning(f"Dispositivo {device_index} falló incluso con configuración reducida: {e}")
                continue
        else:
            # Si llegamos aquí, nada funcionó
            logger.error("Ningún dispositivo funcionó, ni siquiera con configuración básica")
            raise Exception("No se pudo encontrar un dispositivo de audio válido")
        
        # Si los parámetros cambiaron, necesitamos recrear los buffers
        if (self.channels != original_channels or 
            self.sample_rate != original_sample_rate):
            logger.info(f"Recreando buffers: {original_channels}ch@{original_sample_rate}Hz -> {self.channels}ch@{self.sample_rate}Hz")
            self._recreate_buffers()
    
    def _validate_output_device(self):
        """Validar dispositivo de salida de audio"""
        try:
            devices = sd.query_devices()
            if self.output_device_index < len(devices):
                output_dev = devices[self.output_device_index]
                if output_dev['max_output_channels'] > 0:
                    logger.info(f"🔊 Output device: [{self.output_device_index}] {output_dev['name']}")
                    logger.info(f"🔊 APLAY device: {self.aplay_device}")
                    logger.info(f"🔊 Volume: {self.audio_volume_percent}% ({self.audio_volume_db}dB)")
                else:
                    logger.warning(f"⚠️ Device {self.output_device_index} has no output channels")
                    self.output_device_index = None
            else:
                logger.warning(f"⚠️ Output device {self.output_device_index} not found")
                self.output_device_index = None
        except Exception as e:
            logger.error(f"❌ Error validating output device: {e}")
            self.output_device_index = None
    
    def _recreate_buffers(self):
        """
        Recrea los buffers cuando cambia la configuración de audio.
        """
        # Inicializar buffers según configuración actualizada
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
        
        # Limpiar buffer dinámico también
        self.dynamic_audio_chunks.clear()
        self.is_capturing_voice = False
        
        log_audio_event("buffers_recreated", {
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "buffer_type": "DualChannelBuffer" if self.channels == 2 else "CircularAudioBuffer"
        })

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
            # Calcular latencia basada en chunk_size
            latency_ms = (self.chunk_size / self.sample_rate) * 1000
            
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                device=self.input_device_index,
                channels=self.channels,
                blocksize=self.chunk_size,
                callback=self._internal_audio_callback,
                latency='low'  # Solicitar baja latencia
            )
            self.stream.start()
            self.is_recording = True
            
            # Log información detallada para optimización
            logger.info(f"Grabación iniciada - Latencia teórica: {latency_ms:.1f}ms")
            log_audio_event("recording_started", {
                "sample_rate": self.sample_rate,
                "channels": self.channels,
                "chunk_size": self.chunk_size,
                "buffer_size": self.buffer_size,
                "theoretical_latency_ms": latency_ms,
                "device_index": self.input_device_index
            })
        except Exception as e:
            logger.error(f"Error al iniciar la grabación: {e}")
            self.stream = None

    def _internal_audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """
        Callback interno que maneja buffers y llama al callback externo.
        Optimizado para mínima latencia.
        
        Args:
            indata: Datos de audio de entrada
            frames: Número de frames
            time_info: Información temporal
            status: Estado del stream
        """
        callback_start = time.time()
        
        # Actualizar estadísticas
        self.performance_stats['total_callbacks'] += 1
        
        if status:
            self.performance_stats['overflow_count'] += 1
            
            # Log detallado cada 100 overflows para diagnóstico
            if self.performance_stats['overflow_count'] % 100 == 0:
                current_latency = (frames / self.sample_rate) * 1000
                logger.warning(f"Estado del stream de audio: {status} (#{self.performance_stats['overflow_count']}) - "
                             f"Latencia actual: {current_latency:.1f}ms, "
                             f"Frames: {frames}, Chunk: {self.chunk_size}")
        
        # Optimización: copiar datos una sola vez
        audio_data = indata.astype(np.float32, copy=False)
        
        # Escribir al buffer circular continuo - operación crítica
        try:
            if self.channels == 2:
                self.continuous_buffer.write_stereo(audio_data)
            else:
                self.continuous_buffer.write(audio_data.flatten())
        except Exception:
            pass  # Silenciar errores para no bloquear el callback
        
        # Si estamos capturando voz dinámicamente - operación rápida
        if self.is_capturing_voice:
            self.dynamic_audio_chunks.append(audio_data.copy())
        
        # Llamar al callback externo para retrocompatibilidad
        if self.external_callback:
            try:
                self.external_callback(indata, frames, status)
            except Exception:
                pass  # No permitir que errores del callback externo bloqueen el audio
        
        # Registrar tiempo de callback y estadísticas periódicas
        callback_duration = time.time() - callback_start
        self.performance_stats['callback_times'].append(callback_duration)
        
        # Mantener solo las últimas 1000 mediciones
        if len(self.performance_stats['callback_times']) > 1000:
            self.performance_stats['callback_times'] = self.performance_stats['callback_times'][-1000:]
        
        # Log estadísticas cada 30 segundos
        current_time = time.time()
        if current_time - self.performance_stats['last_stats_log'] > 30.0:
            self._log_performance_stats()
            self.performance_stats['last_stats_log'] = current_time
    
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
    
    def _log_performance_stats(self):
        """
        Registra estadísticas de rendimiento del audio para optimización.
        """
        if not self.performance_stats['callback_times']:
            return
        
        # Calcular estadísticas de tiempo de callback
        callback_times = self.performance_stats['callback_times']
        avg_callback_time = np.mean(callback_times) * 1000  # en ms
        max_callback_time = np.max(callback_times) * 1000   # en ms
        min_callback_time = np.min(callback_times) * 1000   # en ms
        p95_callback_time = np.percentile(callback_times, 95) * 1000  # en ms
        
        # Calcular tasa de overflow
        total_callbacks = self.performance_stats['total_callbacks']
        overflow_rate = (self.performance_stats['overflow_count'] / total_callbacks * 100) if total_callbacks > 0 else 0
        
        # Latencia teórica vs real
        theoretical_latency = (self.chunk_size / self.sample_rate) * 1000
        
        # Estadísticas del buffer
        buffer_stats = {}
        if hasattr(self, 'continuous_buffer'):
            try:
                if hasattr(self.continuous_buffer, 'get_buffer_fill_percentage'):
                    buffer_stats['buffer_fill_pct'] = self.continuous_buffer.get_buffer_fill_percentage()
                if hasattr(self.continuous_buffer, 'buffer_size'):
                    buffer_stats['buffer_size'] = getattr(self.continuous_buffer, 'buffer_size', 'unknown')
            except Exception:
                pass
        
        log_audio_event("audio_performance_stats", {
            "config": {
                "sample_rate": self.sample_rate,
                "channels": self.channels,
                "chunk_size": self.chunk_size,
                "buffer_size": self.buffer_size,
                "theoretical_latency_ms": round(theoretical_latency, 2)
            },
            "performance": {
                "total_callbacks": total_callbacks,
                "overflow_count": self.performance_stats['overflow_count'],
                "overflow_rate_pct": round(overflow_rate, 2),
                "avg_callback_time_ms": round(avg_callback_time, 3),
                "max_callback_time_ms": round(max_callback_time, 3),
                "min_callback_time_ms": round(min_callback_time, 3),
                "p95_callback_time_ms": round(p95_callback_time, 3)
            },
            "buffer_stats": buffer_stats,
            "recommendations": self._get_optimization_recommendations(overflow_rate, avg_callback_time, theoretical_latency)
        })
        
        # Reset parcial de estadísticas para la siguiente ventana
        self.performance_stats['callback_times'] = []

    def _get_optimization_recommendations(self, overflow_rate: float, avg_callback_time: float, theoretical_latency: float) -> List[str]:
        """
        Genera recomendaciones de optimización basadas en las estadísticas.
        
        Args:
            overflow_rate: Porcentaje de overflows
            avg_callback_time: Tiempo promedio de callback en ms
            theoretical_latency: Latencia teórica en ms
            
        Returns:
            Lista de recomendaciones
        """
        recommendations = []
        
        # Recomendaciones basadas en overflow rate
        if overflow_rate > 5.0:
            recommendations.append("🔴 Alto rate de overflow (>5%) - Considerar aumentar AUDIO_CHUNK_SIZE")
            
            if self.chunk_size < 2048:
                recommendations.append(f"📈 Probar AUDIO_CHUNK_SIZE={self.chunk_size * 2} (latencia: {(self.chunk_size * 2 / self.sample_rate) * 1000:.1f}ms)")
            
            if theoretical_latency < 50:
                recommendations.append("⚡ Latencia muy baja, considerar balance latencia/estabilidad")
        
        elif overflow_rate > 1.0:
            recommendations.append("🟡 Overflow rate moderado (1-5%) - Monitorear")
        
        elif overflow_rate < 0.1:
            recommendations.append("🟢 Overflow rate excelente (<0.1%)")
            
            if theoretical_latency > 100:
                recommendations.append(f"📉 Latencia alta, considerar AUDIO_CHUNK_SIZE={max(512, self.chunk_size // 2)}")
        
        # Recomendaciones basadas en tiempo de callback
        if avg_callback_time > theoretical_latency * 0.8:
            recommendations.append("⚠️ Tiempo de callback alto vs latencia teórica - Optimizar procesamiento")
        
        # Recomendaciones específicas para 48kHz
        if self.sample_rate == 48000:
            if self.chunk_size < 1024:
                recommendations.append("🎵 Para 48kHz considerar AUDIO_CHUNK_SIZE >= 1024")
            elif overflow_rate > 3.0 and self.chunk_size < 2048:
                recommendations.append("🎵 Para 48kHz con overflows, probar AUDIO_CHUNK_SIZE=2048")
        
        return recommendations

    def get_audio_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas detalladas del audio para optimización.
        
        Returns:
            Dict con estadísticas del audio
        """
        stats = {
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "chunk_size": self.chunk_size,
            "buffer_size": self.buffer_size,
            "theoretical_latency_ms": (self.chunk_size / self.sample_rate) * 1000,
            "is_recording": self.is_recording,
            "overflow_count": getattr(self, '_overflow_count', 0),
            "device_index": self.input_device_index,
            "device_name": self.device_name
        }
        
        if hasattr(self, 'stream') and self.stream:
            try:
                # Obtener información del stream actual
                stats.update({
                    "stream_active": self.stream.active,
                    "stream_stopped": self.stream.stopped,
                    "actual_latency": self.stream.latency
                })
            except Exception:
                pass
        
        return stats

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
    
    def play_audio(self, audio_data: np.ndarray, sample_rate: int = None) -> bool:
        """
        Reproduce audio de forma síncrona con control de volumen.
        
        Args:
            audio_data: Datos de audio a reproducir
            sample_rate: Tasa de muestreo (usa default si None)
            
        Returns:
            bool: True si la reproducción fue exitosa
        """
        try:
            if sample_rate is None:
                sample_rate = self.output_sample_rate
            
            # Normalizar audio
            if audio_data.dtype == np.int16:
                audio_float = audio_data.astype(np.float32) / 32768.0
            elif audio_data.dtype == np.float64:
                audio_float = audio_data.astype(np.float32)
            elif audio_data.dtype == np.float32:
                audio_float = audio_data
            else:
                audio_float = audio_data.astype(np.float32)
            
            # Aplicar control de volumen (convertir porcentaje a factor multiplicador)
            volume_factor = self.audio_volume_percent / 100.0
            audio_float = audio_float * volume_factor
            
            # Asegurar rango [-1, 1]
            max_val = np.abs(audio_float).max()
            if max_val > 1.0:
                logger.warning(f"⚠️ Audio clipping detected after volume adjustment, normalizing...")
                audio_float = audio_float / max_val
            
            duration = len(audio_float) / sample_rate
            logger.info(f"🎵 Playing audio: {duration:.2f}s @ {sample_rate}Hz, volume: {self.audio_volume_percent}%")
            
            # Reproducir usando sounddevice con dispositivo configurado
            try:
                # Usar dispositivo por índice (sounddevice funciona mejor con índices)
                sd.play(audio_float, samplerate=sample_rate, device=self.output_device_index)
                sd.wait()  # Esperar a que termine
                logger.info(f"✅ Audio playback completed on device {self.output_device_index}")
                return True
            except Exception as sd_error:
                logger.error(f"❌ Sounddevice playback failed on device {self.output_device_index}: {sd_error}")
                
                # Fallback: probar con dispositivo por defecto
                try:
                    sd.play(audio_float, samplerate=sample_rate)  # Sin especificar device
                    sd.wait()
                    logger.info(f"✅ Audio playback completed on default device")
                    return True
                except Exception as fallback_error:
                    logger.error(f"❌ Default device playback also failed: {fallback_error}")
                    return False
            
        except Exception as e:
            logger.error(f"❌ Error playing audio: {e}")
            return False
    
    def set_volume(self, volume_percent: float) -> bool:
        """
        Cambiar el volumen de reproducción.
        
        Args:
            volume_percent: Volumen en porcentaje (0-100)
            
        Returns:
            bool: True si se cambió exitosamente
        """
        try:
            if not 0 <= volume_percent <= 100:
                logger.warning(f"⚠️ Volume {volume_percent}% out of range, clamping to 0-100%")
                volume_percent = max(0, min(100, volume_percent))
            
            old_volume = self.audio_volume_percent
            self.audio_volume_percent = volume_percent
            
            # Calcular dB aproximado (logarítmico)
            if volume_percent > 0:
                self.audio_volume_db = 20 * np.log10(volume_percent / 100.0)
            else:
                self.audio_volume_db = -60.0  # Silencio
            
            # Configurar volumen del hardware usando amixer
            self._set_hardware_volume(volume_percent)
            
            logger.info(f"🔊 Volume changed: {old_volume}% → {volume_percent}% ({self.audio_volume_db:.1f}dB)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting volume: {e}")
            return False
    
    def _set_hardware_volume(self, volume_percent: float):
        """
        Configurar el volumen del hardware usando amixer
        
        Args:
            volume_percent: Volumen en porcentaje (0-100)
        """
        try:
            import subprocess
            
            # Para la tarjeta bcm2835 Headphones (card 0)
            # Intentar configurar el volumen principal
            commands_to_try = [
                ['amixer', '-c', '0', 'sset', 'PCM', f'{int(volume_percent)}%'],
                ['amixer', '-c', '0', 'sset', 'Master', f'{int(volume_percent)}%'],
                ['amixer', '-c', '0', 'sset', 'Headphone', f'{int(volume_percent)}%'],
                ['amixer', 'sset', 'PCM', f'{int(volume_percent)}%'],
                ['amixer', 'sset', 'Master', f'{int(volume_percent)}%']
            ]
            
            for cmd in commands_to_try:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        logger.info(f"🔊 Hardware volume set with: {' '.join(cmd)}")
                        return
                    else:
                        logger.debug(f"Command failed: {' '.join(cmd)} - {result.stderr}")
                except subprocess.TimeoutExpired:
                    logger.warning(f"Timeout running: {' '.join(cmd)}")
                except Exception as e:
                    logger.debug(f"Error with command {' '.join(cmd)}: {e}")
            
            logger.warning("⚠️ Could not set hardware volume with any amixer command")
            
        except Exception as e:
            logger.error(f"❌ Error setting hardware volume: {e}")
    
    def get_volume(self) -> Dict[str, float]:
        """
        Obtener información actual del volumen.
        
        Returns:
            Dict con información del volumen
        """
        # También intentar obtener el volumen del hardware
        hardware_volume = self._get_hardware_volume()
        
        result = {
            "volume_percent": self.audio_volume_percent,
            "volume_db": self.audio_volume_db,
            "volume_factor": self.audio_volume_percent / 100.0
        }
        
        if hardware_volume is not None:
            result["hardware_volume_percent"] = hardware_volume
        
        return result
    
    def _get_hardware_volume(self) -> Optional[float]:
        """
        Obtener el volumen actual del hardware usando amixer
        
        Returns:
            Volumen en porcentaje o None si no se pudo obtener
        """
        try:
            import subprocess
            import re
            
            commands_to_try = [
                ['amixer', '-c', '0', 'sget', 'PCM'],
                ['amixer', '-c', '0', 'sget', 'Master'],
                ['amixer', '-c', '0', 'sget', 'Headphone'],
                ['amixer', 'sget', 'PCM'],
                ['amixer', 'sget', 'Master']
            ]
            
            for cmd in commands_to_try:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        # Buscar patrón como [75%] en la salida
                        match = re.search(r'\[(\d+)%\]', result.stdout)
                        if match:
                            return float(match.group(1))
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Error getting hardware volume: {e}")
            return None
    
    def play_audio_base64(self, audio_base64: str, sample_rate: int = None) -> bool:
        """
        Reproducir audio desde string Base64
        
        Args:
            audio_base64: Audio en formato Base64
            sample_rate: Sample rate (opcional)
            
        Returns:
            True si la reproducción fue exitosa
        """
        try:
            # Decodificar Base64
            audio_bytes = base64.b64decode(audio_base64)
            
            # Convertir bytes a numpy array (asumiendo PCM 16-bit)
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # Reproducir
            return self.play_audio(audio_array, sample_rate)
            
        except Exception as e:
            logger.error(f"❌ Error decoding/playing base64 audio: {e}")
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
        try:
            def play_thread():
                success = self.play_audio(audio_data)
                if callback:
                    callback(success)
            
            thread = threading.Thread(target=play_thread, daemon=True)
            thread.start()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error starting async audio playback: {e}")
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
