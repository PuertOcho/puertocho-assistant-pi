#!/usr/bin/env python3
"""
Buffer circular thread-safe para procesamiento de audio en tiempo real.

Este módulo implementa un buffer circular optimizado para manejar flujos de audio
continuos con acceso concurrente desde múltiples hilos.
"""

import threading
import numpy as np
from typing import Optional, Tuple
import time
from utils.logger import logger


class CircularAudioBuffer:
    """
    Buffer circular thread-safe para audio.
    
    Diseñado para mantener una cantidad fija de segundos de audio en memoria,
    permitiendo escritura continua y lectura de chunks para procesamiento.
    """

    def __init__(self, duration_seconds: float, sample_rate: int, channels: int = 1):
        """
        Inicializa el buffer circular.
        
        Args:
            duration_seconds (float): Duración del buffer en segundos
            sample_rate (int): Frecuencia de muestreo del audio
            channels (int): Número de canales de audio
        """
        self.duration_seconds = duration_seconds
        self.sample_rate = sample_rate
        self.channels = channels
        
        # Calcular tamaño del buffer
        self.buffer_size = int(duration_seconds * sample_rate * channels)
        
        # Buffer principal
        self.buffer = np.zeros(self.buffer_size, dtype=np.float32)
        
        # Control de posiciones
        self.write_pos = 0
        self.lock = threading.RLock()
        
        # Estadísticas
        self.total_samples_written = 0
        self.last_write_time = None
        
        logger.info(f"CircularAudioBuffer initialized: {duration_seconds}s, "
                   f"{sample_rate}Hz, {channels}ch, buffer_size={self.buffer_size}")

    def write(self, data: np.ndarray) -> None:
        """
        Escribe datos de audio al buffer circular.
        
        Args:
            data (np.ndarray): Datos de audio a escribir
        """
        if data.size == 0:
            return
            
        # Asegurar que data sea float32
        if data.dtype != np.float32:
            data = data.astype(np.float32)
        
        # Si es multicanal, aplanar los datos
        if len(data.shape) > 1:
            data = data.flatten()
        
        with self.lock:
            data_length = len(data)
            
            # Si los datos son más grandes que el buffer, tomar solo los últimos
            if data_length > self.buffer_size:
                data = data[-self.buffer_size:]
                data_length = self.buffer_size
            
            # Calcular posiciones de escritura
            end_pos = self.write_pos + data_length
            
            if end_pos <= self.buffer_size:
                # Escritura simple, sin wrap-around
                self.buffer[self.write_pos:end_pos] = data
            else:
                # Escritura con wrap-around
                first_part_size = self.buffer_size - self.write_pos
                self.buffer[self.write_pos:] = data[:first_part_size]
                self.buffer[:end_pos - self.buffer_size] = data[first_part_size:]
            
            # Actualizar posición de escritura
            self.write_pos = end_pos % self.buffer_size
            
            # Actualizar estadísticas
            self.total_samples_written += data_length
            self.last_write_time = time.time()

    def read_latest(self, num_samples: int) -> Optional[np.ndarray]:
        """
        Lee las últimas N muestras del buffer.
        
        Args:
            num_samples (int): Número de muestras a leer
            
        Returns:
            Optional[np.ndarray]: Array con las muestras o None si no hay suficientes datos
        """
        if num_samples <= 0 or num_samples > self.buffer_size:
            return None
            
        with self.lock:
            # Verificar que tenemos suficientes datos
            if self.total_samples_written < num_samples:
                return None
            
            # Calcular posición de inicio de lectura
            start_pos = (self.write_pos - num_samples) % self.buffer_size
            
            if start_pos + num_samples <= self.buffer_size:
                # Lectura simple, sin wrap-around
                return self.buffer[start_pos:start_pos + num_samples].copy()
            else:
                # Lectura con wrap-around
                first_part_size = self.buffer_size - start_pos
                result = np.zeros(num_samples, dtype=np.float32)
                result[:first_part_size] = self.buffer[start_pos:]
                result[first_part_size:] = self.buffer[:num_samples - first_part_size]
                return result

    def read_latest_seconds(self, seconds: float) -> Optional[np.ndarray]:
        """
        Lee los últimos N segundos de audio del buffer.
        
        Args:
            seconds (float): Segundos de audio a leer
            
        Returns:
            Optional[np.ndarray]: Array con las muestras o None si no hay suficientes datos
        """
        num_samples = int(seconds * self.sample_rate * self.channels)
        return self.read_latest(num_samples)

    def get_channel_data(self, data: np.ndarray, channel: int) -> np.ndarray:
        """
        Extrae datos de un canal específico de audio multicanal.
        
        Args:
            data (np.ndarray): Datos de audio multicanal
            channel (int): Índice del canal (0=izquierdo, 1=derecho)
            
        Returns:
            np.ndarray: Datos del canal especificado
        """
        if self.channels == 1:
            return data
        
        # Reshape para separar canales
        if len(data.shape) == 1:
            data = data.reshape(-1, self.channels)
        
        if channel >= self.channels:
            raise ValueError(f"Canal {channel} no disponible. Canales disponibles: {self.channels}")
        
        return data[:, channel].flatten()

    def is_ready(self) -> bool:
        """
        Verifica si el buffer tiene datos suficientes para procesamiento.
        
        Returns:
            bool: True si el buffer está listo para ser leído
        """
        with self.lock:
            return self.total_samples_written >= self.buffer_size

    def get_stats(self) -> dict:
        """
        Obtiene estadísticas del buffer.
        
        Returns:
            dict: Diccionario con estadísticas del buffer
        """
        with self.lock:
            return {
                "buffer_size": self.buffer_size,
                "duration_seconds": self.duration_seconds,
                "sample_rate": self.sample_rate,
                "channels": self.channels,
                "total_samples_written": self.total_samples_written,
                "current_fill_percentage": min(100.0, (self.total_samples_written / self.buffer_size) * 100),
                "last_write_time": self.last_write_time,
                "is_ready": self.is_ready()
            }

    def clear(self) -> None:
        """
        Limpia el buffer y reinicia las posiciones.
        """
        with self.lock:
            self.buffer.fill(0)
            self.write_pos = 0
            self.total_samples_written = 0
            self.last_write_time = None
            logger.debug("CircularAudioBuffer cleared")


class DualChannelBuffer:
    """
    Buffer especializado para audio estéreo que mantiene buffers separados
    para cada canal, optimizado para detección de wake word.
    """

    def __init__(self, duration_seconds: float, sample_rate: int):
        """
        Inicializa el buffer dual canal.
        
        Args:
            duration_seconds (float): Duración del buffer en segundos
            sample_rate (int): Frecuencia de muestreo del audio
        """
        self.duration_seconds = duration_seconds
        self.sample_rate = sample_rate
        
        # Crear buffers para cada canal
        self.left_buffer = CircularAudioBuffer(duration_seconds, sample_rate, channels=1)
        self.right_buffer = CircularAudioBuffer(duration_seconds, sample_rate, channels=1)
        
        logger.info(f"DualChannelBuffer initialized: {duration_seconds}s, {sample_rate}Hz")

    def write_stereo(self, stereo_data: np.ndarray) -> None:
        """
        Escribe datos estéreo separándolos en canales izquierdo y derecho.
        
        Args:
            stereo_data (np.ndarray): Datos de audio estéreo (shape: [samples, 2] o [samples*2])
        """
        if stereo_data.size == 0:
            return
        
        # Convertir a float32 si es necesario
        if stereo_data.dtype != np.float32:
            stereo_data = stereo_data.astype(np.float32)
        
        # Asegurar que tenemos datos estéreo
        if len(stereo_data.shape) == 1:
            # Datos intercalados: [L, R, L, R, ...]
            stereo_data = stereo_data.reshape(-1, 2)
        elif len(stereo_data.shape) == 2 and stereo_data.shape[1] != 2:
            logger.warning(f"Datos de audio con forma inesperada: {stereo_data.shape}")
            return
        
        # Separar canales
        left_channel = stereo_data[:, 0]
        right_channel = stereo_data[:, 1]
        
        # Escribir a buffers separados
        self.left_buffer.write(left_channel)
        self.right_buffer.write(right_channel)

    def read_latest_mono(self, channel: str, num_samples: int) -> Optional[np.ndarray]:
        """
        Lee las últimas N muestras de un canal específico.
        
        Args:
            channel (str): 'left' o 'right'
            num_samples (int): Número de muestras a leer
            
        Returns:
            Optional[np.ndarray]: Array con las muestras o None si no hay suficientes datos
        """
        if channel.lower() == 'left':
            return self.left_buffer.read_latest(num_samples)
        elif channel.lower() == 'right':
            return self.right_buffer.read_latest(num_samples)
        else:
            raise ValueError(f"Canal '{channel}' no válido. Use 'left' o 'right'")

    def read_latest_mono_seconds(self, channel: str, seconds: float) -> Optional[np.ndarray]:
        """
        Lee los últimos N segundos de un canal específico.
        
        Args:
            channel (str): 'left' o 'right'
            seconds (float): Segundos de audio a leer
            
        Returns:
            Optional[np.ndarray]: Array con las muestras o None si no hay suficientes datos
        """
        num_samples = int(seconds * self.sample_rate)
        return self.read_latest_mono(channel, num_samples)

    def are_both_ready(self) -> bool:
        """
        Verifica si ambos canales están listos para procesamiento.
        
        Returns:
            bool: True si ambos buffers están listos
        """
        return self.left_buffer.is_ready() and self.right_buffer.is_ready()

    def get_combined_stats(self) -> dict:
        """
        Obtiene estadísticas combinadas de ambos canales.
        
        Returns:
            dict: Estadísticas de ambos canales
        """
        return {
            "left_channel": self.left_buffer.get_stats(),
            "right_channel": self.right_buffer.get_stats(),
            "both_ready": self.are_both_ready()
        }

    def clear(self) -> None:
        """
        Limpia ambos buffers.
        """
        self.left_buffer.clear()
        self.right_buffer.clear()
        logger.debug("DualChannelBuffer cleared")
