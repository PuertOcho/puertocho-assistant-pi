#!/usr/bin/env python3
"""
Audio resampling utilities for PuertoCho Assistant Hardware Service.

Este módulo proporciona funciones de resampling de audio optimizadas
para ARM64/Raspberry Pi, evitando dependencias pesadas como scipy/librosa.
"""

import numpy as np
import logging
from typing import Union, Tuple

logger = logging.getLogger(__name__)

def simple_resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """
    Resampling simple usando interpolación lineal con numpy.
    
    Esta función es compatible con ARM64 y no requiere dependencias pesadas
    como scipy o librosa. Usa interpolación lineal que es suficiente para
    las necesidades de audio del proyecto.
    
    Args:
        audio: Array de audio a resamplear (mono, formato float32)
        orig_sr: Sample rate original
        target_sr: Sample rate objetivo
        
    Returns:
        Array de audio resampleado al target_sr
        
    Example:
        >>> audio_16k = simple_resample(audio_44k, 44100, 16000)
    """
    if orig_sr == target_sr:
        return audio
    
    # Calcular el factor de resampling
    ratio = target_sr / orig_sr
    
    # Calcular la nueva longitud
    new_length = int(len(audio) * ratio)
    
    if new_length == 0:
        logger.warning(f"Resampling resulted in 0 length array. Original: {len(audio)}, ratio: {ratio}")
        return np.array([], dtype=audio.dtype)
    
    # Crear índices para interpolación
    old_indices = np.linspace(0, len(audio) - 1, new_length)
    
    # Interpolar usando numpy
    resampled = np.interp(old_indices, np.arange(len(audio)), audio)
    
    return resampled.astype(audio.dtype)

def resample_for_vad(audio: np.ndarray, input_sr: int = 44100, target_sr: int = 16000) -> np.ndarray:
    """
    Resamplea audio específicamente para Voice Activity Detection (WebRTC VAD).
    
    WebRTC VAD requiere audio a 16kHz. Esta función es un wrapper especializado
    para este caso de uso común.
    
    Args:
        audio: Array de audio mono (float32)
        input_sr: Sample rate de entrada (default: 44100)
        target_sr: Sample rate objetivo (default: 16000)
        
    Returns:
        Audio resampleado a 16kHz para VAD
    """
    if not isinstance(audio, np.ndarray):
        raise TypeError("Audio debe ser numpy array")
    
    if audio.dtype != np.float32:
        logger.warning(f"Audio type is {audio.dtype}, converting to float32")
        audio = audio.astype(np.float32)
    
    return simple_resample(audio, input_sr, target_sr)

def resample_for_wake_word(audio: np.ndarray, input_sr: int = 44100, target_sr: int = 16000) -> np.ndarray:
    """
    Resamplea audio específicamente para Wake Word Detection (Porcupine).
    
    Porcupine requiere audio a 16kHz. Esta función es un wrapper especializado
    para este caso de uso común.
    
    Args:
        audio: Array de audio mono (float32)
        input_sr: Sample rate de entrada (default: 44100)
        target_sr: Sample rate objetivo (default: 16000)
        
    Returns:
        Audio resampleado a 16kHz para Porcupine
    """
    if not isinstance(audio, np.ndarray):
        raise TypeError("Audio debe ser numpy array")
    
    if audio.dtype != np.float32:
        logger.warning(f"Audio type is {audio.dtype}, converting to float32")
        audio = audio.astype(np.float32)
    
    return simple_resample(audio, input_sr, target_sr)

def convert_stereo_to_mono(stereo_audio: np.ndarray) -> np.ndarray:
    """
    Convierte audio estéreo a mono promediando ambos canales.
    
    Args:
        stereo_audio: Array de audio estéreo shape [samples, 2] o [samples*2]
        
    Returns:
        Audio mono shape [samples]
    """
    if len(stereo_audio.shape) == 2:
        # Audio con shape [samples, 2]
        return np.mean(stereo_audio, axis=1, dtype=stereo_audio.dtype)
    elif len(stereo_audio.shape) == 1 and len(stereo_audio) % 2 == 0:
        # Audio interleaved [L, R, L, R, ...]
        return np.mean(stereo_audio.reshape(-1, 2), axis=1, dtype=stereo_audio.dtype)
    else:
        # Ya es mono o formato desconocido
        return stereo_audio

def normalize_audio(audio: np.ndarray, target_dtype: type = np.float32) -> np.ndarray:
    """
    Normaliza audio a un rango específico según el tipo de dato.
    
    Args:
        audio: Array de audio a normalizar
        target_dtype: Tipo de dato objetivo (np.float32, np.int16, etc.)
        
    Returns:
        Audio normalizado al tipo especificado
    """
    if target_dtype == np.float32:
        if audio.dtype == np.int16:
            return audio.astype(np.float32) / 32767.0
        elif audio.dtype == np.int32:
            return audio.astype(np.float32) / 2147483647.0
        else:
            # Ya es float, asegurar rango [-1, 1]
            return np.clip(audio.astype(np.float32), -1.0, 1.0)
    
    elif target_dtype == np.int16:
        if audio.dtype in [np.float32, np.float64]:
            # Asegurar rango [-1, 1] y convertir
            clipped = np.clip(audio, -1.0, 1.0)
            return (clipped * 32767).astype(np.int16)
        else:
            return audio.astype(np.int16)
    
    else:
        return audio.astype(target_dtype)

def prepare_audio_for_processing(
    audio: np.ndarray, 
    input_sr: int, 
    target_sr: int, 
    target_dtype: type = np.float32
) -> np.ndarray:
    """
    Función todo-en-uno para preparar audio para procesamiento.
    
    Convierte de estéreo a mono, normaliza, y resamplea en un solo paso.
    
    Args:
        audio: Audio de entrada (puede ser estéreo o mono)
        input_sr: Sample rate de entrada
        target_sr: Sample rate objetivo
        target_dtype: Tipo de dato objetivo
        
    Returns:
        Audio preparado: mono, normalizado, y resampleado
    """
    # Convertir a mono si es necesario
    if len(audio.shape) == 2:
        audio = convert_stereo_to_mono(audio)
    
    # Normalizar
    audio = normalize_audio(audio, target_dtype)
    
    # Resamplear si es necesario
    if input_sr != target_sr:
        audio = simple_resample(audio, input_sr, target_sr)
    
    return audio

# Funciones de conveniencia para casos de uso comunes
def prepare_for_vad(audio: np.ndarray, input_sr: int = 44100) -> np.ndarray:
    """Prepara audio para VAD: mono, float32, 16kHz"""
    return prepare_audio_for_processing(audio, input_sr, 16000, np.float32)

def prepare_for_wake_word(audio: np.ndarray, input_sr: int = 44100) -> np.ndarray:
    """Prepara audio para wake word: mono, float32, 16kHz"""
    return prepare_audio_for_processing(audio, input_sr, 16000, np.float32)

def prepare_for_porcupine(audio: np.ndarray, input_sr: int = 44100, frame_length: int = 512) -> np.ndarray:
    """
    Prepara audio específicamente para Porcupine: mono, int16, 16kHz, frame exacto.
    
    Args:
        audio: Audio de entrada
        input_sr: Sample rate de entrada
        frame_length: Longitud exacta del frame requerido por Porcupine
        
    Returns:
        Audio preparado como int16 con longitud exacta
    """
    # Preparar audio básico
    prepared = prepare_audio_for_processing(audio, input_sr, 16000, np.float32)
    
    # Ajustar longitud exacta
    if len(prepared) < frame_length:
        # Pad con ceros
        prepared = np.pad(prepared, (0, frame_length - len(prepared)))
    elif len(prepared) > frame_length:
        # Truncar
        prepared = prepared[:frame_length]
    
    # Convertir a int16 para Porcupine
    return normalize_audio(prepared, np.int16)

# Testing y debugging
if __name__ == "__main__":
    # Tests básicos
    print("Testing audio resampling utilities...")
    
    # Test 1: Resampling simple
    test_audio = np.random.randn(44100).astype(np.float32)  # 1 segundo a 44.1kHz
    resampled = simple_resample(test_audio, 44100, 16000)
    print(f"Original: {len(test_audio)} samples @ 44.1kHz")
    print(f"Resampled: {len(resampled)} samples @ 16kHz")
    print(f"Expected: ~{int(44100 * 16000 / 44100)} samples")
    
    # Test 2: Estéreo a mono
    stereo = np.random.randn(1000, 2).astype(np.float32)
    mono = convert_stereo_to_mono(stereo)
    print(f"Stereo shape: {stereo.shape} -> Mono shape: {mono.shape}")
    
    # Test 3: Preparación completa
    prepared = prepare_for_vad(stereo, 44100)
    print(f"Prepared for VAD: {prepared.shape}, dtype: {prepared.dtype}")
    
    print("All tests completed!")
