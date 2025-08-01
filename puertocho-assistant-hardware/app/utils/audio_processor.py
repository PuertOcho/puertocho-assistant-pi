#!/usr/bin/env python3
"""
AudioProcessor - Sistema unificado de procesamiento de audio.

Este módulo combina y coordina todas las funcionalidades de procesamiento de audio:
- Resampling optimizado (AudioResampler)
- Buffering circular (CircularAudioBuffer)  
- Análisis de niveles y espectro
- Pipelines configurables de procesamiento

Proporciona una API única y coherente para todo el procesamiento de audio del sistema.
"""

import numpy as np
import time
import threading
from typing import Dict, List, Optional, Callable, Tuple, Union
from dataclasses import dataclass
from enum import Enum

# Imports de componentes existentes
from .audio_resampler import AudioResampler
from .audio_buffer import CircularAudioBuffer, DualChannelBuffer
from .logger import logger, log_performance_metric


class ProcessingStage(Enum):
    """Etapas disponibles en el pipeline de procesamiento."""
    RESAMPLE = "resample"
    BUFFER = "buffer"  
    FILTER = "filter"
    ANALYZE = "analyze"
    DETECT = "detect"


@dataclass
class AudioSpectrum:
    """Datos del análisis de espectro de audio."""
    frequencies: np.ndarray
    magnitudes: np.ndarray
    peak_frequency: float
    peak_magnitude: float
    timestamp: float


@dataclass
class AudioLevel:
    """Información de niveles de audio."""
    rms: float
    peak: float
    average: float
    timestamp: float
    channel: int = 0


@dataclass
class ProcessingConfig:
    """Configuración para pipeline de procesamiento."""
    input_sample_rate: int
    output_sample_rate: int
    buffer_duration: float = 2.0
    enable_filtering: bool = False
    enable_analysis: bool = False
    chunk_size: int = 1024
    channels: int = 1


class AudioProcessor:
    """
    Procesador unificado de audio que combina todas las funcionalidades.
    
    Maneja resampling, buffering, filtrado, análisis y detección en un pipeline
    configurable y optimizado.
    """

    def __init__(self, config: ProcessingConfig):
        """
        Inicializa el procesador de audio.
        
        Args:
            config: Configuración del procesamiento
        """
        self.config = config
        self._setup_components()
        self._setup_pipeline()
        
        # Estado del procesamiento
        self._is_running = False
        self._processing_thread = None
        self._callbacks = {}
        self._metrics = {}
        
        logger.info(f"AudioProcessor inicializado con config: {config}")

    def _setup_components(self):
        """Configura los componentes individuales."""
        # AudioResampler para conversión de sample rate
        self.resampler = AudioResampler()
        
        # Buffer circular principal
        self.main_buffer = CircularAudioBuffer(
            duration_seconds=self.config.buffer_duration,
            sample_rate=self.config.output_sample_rate,
            channels=self.config.channels
        )
        
        # Buffer adicional para procesamiento dual-channel si es necesario
        if self.config.channels == 2:
            self.dual_buffer = DualChannelBuffer(
                duration_seconds=self.config.buffer_duration,
                sample_rate=self.config.output_sample_rate
            )
        else:
            self.dual_buffer = None
            
        # Cache para análisis de espectro
        self._spectrum_cache = {}
        self._level_cache = {}

    def _setup_pipeline(self):
        """Configura el pipeline de procesamiento."""
        self.pipeline_stages = [ProcessingStage.RESAMPLE, ProcessingStage.BUFFER]
        
        if self.config.enable_filtering:
            self.pipeline_stages.append(ProcessingStage.FILTER)
            
        if self.config.enable_analysis:
            self.pipeline_stages.append(ProcessingStage.ANALYZE)

    def process_chunk(self, audio_chunk: np.ndarray) -> Optional[np.ndarray]:
        """
        Procesa un chunk de audio a través del pipeline completo.
        
        Args:
            audio_chunk: Chunk de audio a procesar
            
        Returns:
            Audio procesado o None si hay error
        """
        start_time = time.time()
        
        try:
            processed_audio = audio_chunk
            
            # Ejecutar pipeline
            for stage in self.pipeline_stages:
                processed_audio = self._execute_stage(stage, processed_audio)
                if processed_audio is None:
                    return None
            
            # Métricas de rendimiento
            processing_time = (time.time() - start_time) * 1000  # ms
            log_performance_metric("audio_processing_time", processing_time, "ms")
            
            return processed_audio
            
        except Exception as e:
            logger.error(f"Error en procesamiento de audio: {e}")
            return None

    def _execute_stage(self, stage: ProcessingStage, audio: np.ndarray) -> Optional[np.ndarray]:
        """Ejecuta una etapa específica del pipeline."""
        try:
            if stage == ProcessingStage.RESAMPLE:
                if self.config.input_sample_rate != self.config.output_sample_rate:
                    return self.resampler.resample(
                        audio, 
                        self.config.input_sample_rate, 
                        self.config.output_sample_rate
                    )
                return audio
                
            elif stage == ProcessingStage.BUFFER:
                self.main_buffer.write(audio)
                return audio
                
            elif stage == ProcessingStage.FILTER:
                return self._apply_filters(audio)
                
            elif stage == ProcessingStage.ANALYZE:
                self._analyze_audio(audio)
                return audio
                
            else:
                logger.warning(f"Etapa desconocida: {stage}")
                return audio
                
        except Exception as e:
            logger.error(f"Error en etapa {stage}: {e}")
            return None

    def _apply_filters(self, audio: np.ndarray) -> np.ndarray:
        """
        Aplica filtros de audio (noise reduction, EQ, etc.).
        
        Args:
            audio: Audio a filtrar
            
        Returns:
            Audio filtrado
        """
        # TODO: Implementar filtros avanzados
        # Por ahora solo aplicamos normalización básica
        if len(audio) > 0:
            max_val = np.max(np.abs(audio))
            if max_val > 0:
                return audio / max_val * 0.8  # Normalizar a 80%
        return audio

    def _analyze_audio(self, audio: np.ndarray):
        """
        Realiza análisis de espectro y niveles del audio.
        
        Args:
            audio: Audio a analizar
        """
        if len(audio) == 0:
            return
            
        timestamp = time.time()
        
        # Análisis de niveles
        level = self._calculate_audio_level(audio, timestamp)
        self._level_cache[timestamp] = level
        
        # Análisis de espectro (cada cierto tiempo para no sobrecargar)
        if timestamp - self._metrics.get('last_spectrum_time', 0) > 0.1:  # 100ms
            spectrum = self._calculate_spectrum(audio, timestamp)
            self._spectrum_cache[timestamp] = spectrum
            self._metrics['last_spectrum_time'] = timestamp
            
        # Limpiar cache antiguo
        self._cleanup_caches(timestamp)

    def _calculate_audio_level(self, audio: np.ndarray, timestamp: float) -> AudioLevel:
        """Calcula niveles de audio (RMS, peak, average)."""
        rms = np.sqrt(np.mean(audio ** 2))
        peak = np.max(np.abs(audio))
        average = np.mean(np.abs(audio))
        
        return AudioLevel(
            rms=float(rms),
            peak=float(peak), 
            average=float(average),
            timestamp=timestamp
        )

    def _calculate_spectrum(self, audio: np.ndarray, timestamp: float) -> AudioSpectrum:
        """Calcula análisis de espectro usando FFT."""
        # FFT simple para análisis de espectro
        fft = np.fft.rfft(audio)
        magnitudes = np.abs(fft)
        frequencies = np.fft.rfftfreq(len(audio), 1/self.config.output_sample_rate)
        
        # Encontrar pico
        peak_idx = np.argmax(magnitudes)
        peak_freq = frequencies[peak_idx]
        peak_mag = magnitudes[peak_idx]
        
        return AudioSpectrum(
            frequencies=frequencies,
            magnitudes=magnitudes,
            peak_frequency=float(peak_freq),
            peak_magnitude=float(peak_mag),
            timestamp=timestamp
        )

    def _cleanup_caches(self, current_time: float):
        """Limpia cache antiguo para evitar uso excesivo de memoria."""
        max_age = 5.0  # 5 segundos
        
        # Limpiar cache de niveles
        old_keys = [k for k in self._level_cache.keys() if current_time - k > max_age]
        for key in old_keys:
            del self._level_cache[key]
            
        # Limpiar cache de espectro
        old_keys = [k for k in self._spectrum_cache.keys() if current_time - k > max_age]
        for key in old_keys:
            del self._spectrum_cache[key]

    def get_current_level(self) -> Optional[AudioLevel]:
        """Obtiene el nivel de audio más reciente."""
        if not self._level_cache:
            return None
        latest_time = max(self._level_cache.keys())
        return self._level_cache[latest_time]

    def get_current_spectrum(self) -> Optional[AudioSpectrum]:
        """Obtiene el análisis de espectro más reciente."""
        if not self._spectrum_cache:
            return None
        latest_time = max(self._spectrum_cache.keys())
        return self._spectrum_cache[latest_time]

    def get_buffered_audio(self, duration_seconds: float) -> Optional[np.ndarray]:
        """
        Obtiene audio del buffer circular.
        
        Args:
            duration_seconds: Duración de audio a obtener
            
        Returns:
            Array de audio o None si no hay suficientes datos
        """
        return self.main_buffer.read_last_seconds(duration_seconds)

    def clear_buffers(self):
        """Limpia todos los buffers de audio."""
        self.main_buffer.clear()
        if self.dual_buffer:
            self.dual_buffer.clear()
        self._level_cache.clear()
        self._spectrum_cache.clear()
        logger.info("Buffers de audio limpiados")

    def register_callback(self, event_type: str, callback: Callable):
        """
        Registra callback para eventos específicos.
        
        Args:
            event_type: Tipo de evento ('level_change', 'spectrum_update', etc.)
            callback: Función a llamar
        """
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)

    def _notify_callbacks(self, event_type: str, data):
        """Notifica a callbacks registrados."""
        if event_type in self._callbacks:
            for callback in self._callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error en callback {event_type}: {e}")

    def get_metrics(self) -> Dict:
        """Obtiene métricas de rendimiento del procesador."""
        buffer_stats = self.main_buffer.get_stats()
        
        return {
            'buffer_stats': buffer_stats,
            'total_samples_processed': self.main_buffer.total_samples_written,
            'cache_sizes': {
                'levels': len(self._level_cache),
                'spectrum': len(self._spectrum_cache)
            },
            'pipeline_stages': [stage.value for stage in self.pipeline_stages],
            'config': {
                'input_sr': self.config.input_sample_rate,
                'output_sr': self.config.output_sample_rate,
                'buffer_duration': self.config.buffer_duration,
                'channels': self.config.channels
            }
        }

    def start_continuous_processing(self):
        """Inicia procesamiento continuo en hilo separado."""
        if self._is_running:
            return
            
        self._is_running = True
        self._processing_thread = threading.Thread(target=self._processing_loop)
        self._processing_thread.start()
        logger.info("Procesamiento continuo iniciado")

    def stop_continuous_processing(self):
        """Detiene el procesamiento continuo."""
        self._is_running = False
        if self._processing_thread:
            self._processing_thread.join()
        logger.info("Procesamiento continuo detenido")

    def _processing_loop(self):
        """Loop principal de procesamiento continuo."""
        while self._is_running:
            try:
                # Procesar análisis periódicos
                current_level = self.get_current_level()
                if current_level:
                    self._notify_callbacks('level_update', current_level)
                    
                current_spectrum = self.get_current_spectrum()
                if current_spectrum:
                    self._notify_callbacks('spectrum_update', current_spectrum)
                    
                time.sleep(0.05)  # 50ms de sleep
                
            except Exception as e:
                logger.error(f"Error en loop de procesamiento: {e}")
                time.sleep(0.1)


class AudioProcessorFactory:
    """Factory para crear instancias de AudioProcessor con configuraciones predefinidas."""
    
    @staticmethod
    def create_for_wake_word() -> AudioProcessor:
        """Crea procesador optimizado para detección de wake word."""
        config = ProcessingConfig(
            input_sample_rate=48000,
            output_sample_rate=16000,
            buffer_duration=2.0,
            enable_filtering=True,
            enable_analysis=False,
            channels=1
        )
        return AudioProcessor(config)
    
    @staticmethod  
    def create_for_recording() -> AudioProcessor:
        """Crea procesador optimizado para grabación de audio."""
        config = ProcessingConfig(
            input_sample_rate=48000,
            output_sample_rate=48000,
            buffer_duration=10.0,
            enable_filtering=True,
            enable_analysis=True,
            channels=1
        )
        return AudioProcessor(config)
    
    @staticmethod
    def create_for_playback() -> AudioProcessor:
        """Crea procesador optimizado para reproducción."""
        config = ProcessingConfig(
            input_sample_rate=44100,
            output_sample_rate=48000, 
            buffer_duration=1.0,
            enable_filtering=False,
            enable_analysis=True,
            channels=1
        )
        return AudioProcessor(config)
