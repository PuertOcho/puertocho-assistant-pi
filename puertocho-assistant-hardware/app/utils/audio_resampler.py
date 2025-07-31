#!/usr/bin/env python3
"""
AudioResampler - Clase wrapper para resampling de audio optimizado.

Esta clase encapsula las funciones de resampling existentes en audio_resampling.py
añadiendo cache, procesamiento por chunks y una API más limpia para uso en
los componentes core.
"""

import numpy as np
import time
from typing import Dict, Tuple, Optional, Union
from dataclasses import dataclass
from utils.logger import logger, log_performance_metric
from utils.audio_resampling import (
    simple_resample,
    convert_stereo_to_mono,
    normalize_audio,
    prepare_audio_for_processing,
    prepare_for_vad,
    prepare_for_wake_word,
    prepare_for_porcupine
)


@dataclass
class ResamplerConfig:
    """Configuración para una operación de resampling específica"""
    input_rate: int
    output_rate: int
    target_dtype: type = np.float32
    frame_length: Optional[int] = None  # Para casos como Porcupine
    
    def __post_init__(self):
        """Validación de la configuración"""
        if self.input_rate <= 0 or self.output_rate <= 0:
            raise ValueError("Sample rates must be positive")
        if self.frame_length is not None and self.frame_length <= 0:
            raise ValueError("Frame length must be positive")
    
    def get_cache_key(self) -> str:
        """Genera una clave única para el cache"""
        return f"{self.input_rate}_{self.output_rate}_{self.target_dtype.__name__}_{self.frame_length}"


class AudioResampler:
    """
    Wrapper para operaciones de resampling de audio con cache y optimizaciones.
    
    Esta clase encapsula las funciones optimizadas de audio_resampling.py
    añadiendo:
    - Cache de configuraciones frecuentes
    - Procesamiento por chunks eficiente
    - Métricas de rendimiento
    - API unificada para todos los casos de uso
    """
    
    def __init__(self, cache_size: int = 10):
        """
        Inicializa el AudioResampler.
        
        Args:
            cache_size: Número máximo de configuraciones en cache
        """
        self.cache_size = cache_size
        self._config_cache: Dict[str, ResamplerConfig] = {}
        self._performance_stats: Dict[str, Dict] = {}
        
        # Configuraciones predefinidas comunes
        self._setup_common_configs()
        
        logger.info(f"AudioResampler initialized with cache size: {cache_size}")
    
    def _setup_common_configs(self) -> None:
        """Configura las configuraciones más comunes para cache"""
        common_configs = [
            # VAD: 44.1kHz -> 16kHz, float32
            ResamplerConfig(44100, 16000, np.float32),
            # Wake Word: 44.1kHz -> 16kHz, float32
            ResamplerConfig(44100, 16000, np.float32, 512),  # Porcupine frame
            # Audio de alta calidad: mantenimiento
            ResamplerConfig(44100, 44100, np.float32),
            # Compatibilidad común: 48kHz -> 16kHz
            ResamplerConfig(48000, 16000, np.float32),
        ]
        
        for config in common_configs:
            self._add_to_cache(config)
    
    def _add_to_cache(self, config: ResamplerConfig) -> None:
        """Añade una configuración al cache"""
        cache_key = config.get_cache_key()
        
        # Si el cache está lleno, remover el más antiguo (FIFO simple)
        if len(self._config_cache) >= self.cache_size:
            oldest_key = next(iter(self._config_cache))
            del self._config_cache[oldest_key]
            logger.debug(f"Removed oldest config from cache: {oldest_key}")
        
        self._config_cache[cache_key] = config
        self._performance_stats[cache_key] = {
            "total_calls": 0,
            "total_samples_processed": 0,
            "total_time_ms": 0.0,
            "avg_time_per_sample": 0.0
        }
        
        logger.debug(f"Added config to cache: {cache_key}")
    
    def _get_or_create_config(self, input_rate: int, output_rate: int, 
                             target_dtype: type = np.float32, 
                             frame_length: Optional[int] = None) -> ResamplerConfig:
        """Obtiene una configuración del cache o la crea"""
        config = ResamplerConfig(input_rate, output_rate, target_dtype, frame_length)
        cache_key = config.get_cache_key()
        
        if cache_key not in self._config_cache:
            self._add_to_cache(config)
        
        return self._config_cache[cache_key]
    
    def _update_performance_stats(self, cache_key: str, samples_processed: int, 
                                 processing_time_ms: float) -> None:
        """Actualiza las estadísticas de rendimiento"""
        if cache_key in self._performance_stats:
            stats = self._performance_stats[cache_key]
            stats["total_calls"] += 1
            stats["total_samples_processed"] += samples_processed
            stats["total_time_ms"] += processing_time_ms
            
            if stats["total_samples_processed"] > 0:
                stats["avg_time_per_sample"] = stats["total_time_ms"] / stats["total_samples_processed"]
    
    def resample(self, audio: np.ndarray, input_rate: int, output_rate: int, 
                target_dtype: type = np.float32) -> np.ndarray:
        """
        Resamplea audio usando la función optimizada subyacente.
        
        Args:
            audio: Array de audio a resamplear
            input_rate: Sample rate de entrada
            output_rate: Sample rate objetivo
            target_dtype: Tipo de dato objetivo
            
        Returns:
            Audio resampleado
        """
        config = self._get_or_create_config(input_rate, output_rate, target_dtype)
        cache_key = config.get_cache_key()
        
        start_time = time.perf_counter()
        
        try:
            # Usar función optimizada existente
            result = simple_resample(audio, input_rate, output_rate)
            
            # Normalizar al tipo objetivo si es necesario
            if result.dtype != target_dtype:
                result = normalize_audio(result, target_dtype)
            
            processing_time_ms = (time.perf_counter() - start_time) * 1000
            self._update_performance_stats(cache_key, len(audio), processing_time_ms)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in resample: {e}")
            raise
    
    def process_chunk(self, audio: np.ndarray, input_rate: int, output_rate: int,
                     target_dtype: type = np.float32, 
                     convert_stereo: bool = True) -> np.ndarray:
        """
        Procesa un chunk de audio completo: conversión estéreo->mono, normalización y resampling.
        
        Args:
            audio: Chunk de audio (puede ser estéreo o mono)
            input_rate: Sample rate de entrada
            output_rate: Sample rate objetivo
            target_dtype: Tipo de dato objetivo
            convert_stereo: Si convertir de estéreo a mono automáticamente
            
        Returns:
            Audio procesado
        """
        config = self._get_or_create_config(input_rate, output_rate, target_dtype)
        cache_key = config.get_cache_key()
        
        start_time = time.perf_counter()
        
        try:
            # Usar función todo-en-uno optimizada existente
            result = prepare_audio_for_processing(audio, input_rate, output_rate, target_dtype)
            
            processing_time_ms = (time.perf_counter() - start_time) * 1000
            self._update_performance_stats(cache_key, len(audio), processing_time_ms)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in process_chunk: {e}")
            raise
    
    def prepare_for_vad(self, audio: np.ndarray, input_rate: int = 44100) -> np.ndarray:
        """
        Prepara audio para VAD usando función optimizada existente.
        
        Args:
            audio: Audio de entrada
            input_rate: Sample rate de entrada
            
        Returns:
            Audio preparado para VAD (mono, float32, 16kHz)
        """
        config = self._get_or_create_config(input_rate, 16000, np.float32)
        cache_key = config.get_cache_key()
        
        start_time = time.perf_counter()
        
        try:
            result = prepare_for_vad(audio, input_rate)
            
            processing_time_ms = (time.perf_counter() - start_time) * 1000
            self._update_performance_stats(cache_key, len(audio), processing_time_ms)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in prepare_for_vad: {e}")
            raise
    
    def prepare_for_wake_word(self, audio: np.ndarray, input_rate: int = 44100) -> np.ndarray:
        """
        Prepara audio para wake word detection usando función optimizada existente.
        
        Args:
            audio: Audio de entrada
            input_rate: Sample rate de entrada
            
        Returns:
            Audio preparado para wake word (mono, float32, 16kHz)
        """
        config = self._get_or_create_config(input_rate, 16000, np.float32)
        cache_key = config.get_cache_key()
        
        start_time = time.perf_counter()
        
        try:
            result = prepare_for_wake_word(audio, input_rate)
            
            processing_time_ms = (time.perf_counter() - start_time) * 1000
            self._update_performance_stats(cache_key, len(audio), processing_time_ms)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in prepare_for_wake_word: {e}")
            raise
    
    def prepare_for_porcupine(self, audio: np.ndarray, input_rate: int = 44100, 
                             frame_length: int = 512) -> np.ndarray:
        """
        Prepara audio para Porcupine usando función optimizada existente.
        
        Args:
            audio: Audio de entrada
            input_rate: Sample rate de entrada
            frame_length: Longitud exacta del frame requerido
            
        Returns:
            Audio preparado para Porcupine (mono, int16, 16kHz, frame exacto)
        """
        config = self._get_or_create_config(input_rate, 16000, np.int16, frame_length)
        cache_key = config.get_cache_key()
        
        start_time = time.perf_counter()
        
        try:
            result = prepare_for_porcupine(audio, input_rate, frame_length)
            
            processing_time_ms = (time.perf_counter() - start_time) * 1000
            self._update_performance_stats(cache_key, len(audio), processing_time_ms)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in prepare_for_porcupine: {e}")
            raise
    
    def get_performance_stats(self) -> Dict[str, Dict]:
        """
        Obtiene estadísticas de rendimiento de todas las configuraciones.
        
        Returns:
            Dict con estadísticas por configuración
        """
        return self._performance_stats.copy()
    
    def log_performance_metrics(self) -> None:
        """Envía métricas de rendimiento al sistema de logging"""
        for cache_key, stats in self._performance_stats.items():
            if stats["total_calls"] > 0:
                log_performance_metric(
                    f"resampler_avg_time_per_sample_{cache_key}",
                    stats["avg_time_per_sample"],
                    "ms"
                )
                log_performance_metric(
                    f"resampler_total_samples_{cache_key}",
                    stats["total_samples_processed"],
                    "samples"
                )
    
    def clear_cache(self) -> None:
        """Limpia el cache de configuraciones (mantiene las comunes)"""
        self._config_cache.clear()
        self._performance_stats.clear()
        self._setup_common_configs()
        logger.info("AudioResampler cache cleared and common configs restored")
    
    def get_cache_info(self) -> Dict[str, Union[int, list]]:
        """
        Obtiene información sobre el estado del cache.
        
        Returns:
            Dict con información del cache
        """
        return {
            "cache_size": len(self._config_cache),
            "max_cache_size": self.cache_size,
            "cached_configs": list(self._config_cache.keys()),
            "total_configurations_used": len(self._performance_stats)
        }


# Instancia global para uso conveniente
global_resampler = AudioResampler()

# Funciones de conveniencia que usan la instancia global
def resample_audio(audio: np.ndarray, input_rate: int, output_rate: int, 
                  target_dtype: type = np.float32) -> np.ndarray:
    """Función de conveniencia para resampling simple"""
    return global_resampler.resample(audio, input_rate, output_rate, target_dtype)

def process_audio_chunk(audio: np.ndarray, input_rate: int, output_rate: int,
                       target_dtype: type = np.float32) -> np.ndarray:
    """Función de conveniencia para procesamiento completo de chunk"""
    return global_resampler.process_chunk(audio, input_rate, output_rate, target_dtype)


# Testing
if __name__ == "__main__":
    # Tests básicos de la clase AudioResampler
    print("Testing AudioResampler...")
    
    resampler = AudioResampler(cache_size=5)
    
    # Test 1: Resampling básico
    test_audio = np.random.randn(44100).astype(np.float32)  # 1 segundo a 44.1kHz
    resampled = resampler.resample(test_audio, 44100, 16000)
    print(f"Test 1 - Resampling: {len(test_audio)} -> {len(resampled)} samples")
    
    # Test 2: Preparación para VAD
    vad_audio = resampler.prepare_for_vad(test_audio, 44100)
    print(f"Test 2 - VAD prep: {vad_audio.shape}, dtype: {vad_audio.dtype}")
    
    # Test 3: Preparación para Porcupine
    porcupine_audio = resampler.prepare_for_porcupine(test_audio, 44100, 512)
    print(f"Test 3 - Porcupine prep: {porcupine_audio.shape}, dtype: {porcupine_audio.dtype}")
    
    # Test 4: Cache info
    cache_info = resampler.get_cache_info()
    print(f"Test 4 - Cache info: {cache_info}")
    
    # Test 5: Performance stats
    perf_stats = resampler.get_performance_stats()
    print(f"Test 5 - Performance stats keys: {list(perf_stats.keys())}")
    
    print("All tests completed!")
