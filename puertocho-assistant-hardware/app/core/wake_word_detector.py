#!/usr/bin/env python3
"""
Wake Word Detector usando Porcupine con soporte para dual-microphone.

Este módulo implementa la detección de wake word "Puerto-ocho" procesando
audio de ambos micrófonos en paralelo para mejorar la precisión de detección.
"""

import os
import threading
import time
from typing import Optional, Callable, Dict, Any, List
import numpy as np
import pvporcupine
from dataclasses import dataclass

from config import config
from utils.logger import logger, log_hardware_event
from utils.audio_buffer import DualChannelBuffer
from utils.audio_resampling import simple_resample, prepare_for_wake_word, prepare_for_porcupine


@dataclass
class WakeWordEvent:
    """Evento de detección de wake word"""
    timestamp: float
    channel: str  # 'left' o 'right'
    keyword_index: int
    confidence: float = 0.0  # Para futuras versiones de Porcupine


class WakeWordDetector:
    """
    Detector de wake word usando Porcupine con soporte dual-microphone.
    
    Procesa audio de ambos canales (izquierdo/derecho) en paralelo,
    detectando el wake word "Puerto-ocho" en cualquiera de ellos.
    """

    def __init__(self, on_wake_word: Optional[Callable[[WakeWordEvent], None]] = None):
        """
        Inicializa el detector de wake word.
        
        Args:
            on_wake_word: Callback que se ejecuta cuando se detecta wake word
        """
        self.on_wake_word = on_wake_word
        self.is_running = False
        self._processing_threads: List[threading.Thread] = []
        self._stop_event = threading.Event()
        
        # Configuración
        self.access_key = config.wake_word.access_key
        self.model_path = config.wake_word.model_path
        self.params_path = config.wake_word.params_path
        self.sensitivity = config.wake_word.sensitivity
        self.process_both_channels = config.wake_word.process_both_channels
        self.require_both_channels = config.wake_word.require_both_channels
        
        # Configuración de resampling
        self.input_sample_rate = config.audio.sample_rate  # 44100 Hz
        self.target_sample_rate = 16000  # Porcupine requiere 16kHz
        self.resample_ratio = self.target_sample_rate / self.input_sample_rate
        
        # Buffers de audio para resampling (uno por canal)
        self.audio_buffer_left = np.array([], dtype=np.float32)
        self.audio_buffer_right = np.array([], dtype=np.float32)
        
        # Buffer de audio original (mantener para compatibilidad)
        self.audio_buffer = DualChannelBuffer(
            duration_seconds=config.wake_word.buffer_duration_seconds,
            sample_rate=config.audio.sample_rate
        )
        
        # Instancias de Porcupine (una por canal si es necesario)
        self._porcupine_left: Optional[pvporcupine.Porcupine] = None
        self._porcupine_right: Optional[pvporcupine.Porcupine] = None
        
        # Control de detección
        self._last_detection_time = 0
        self._detection_cooldown = 2.0  # Evitar detecciones múltiples
        
        # Estadísticas
        self._stats = {
            "total_detections": 0,
            "left_channel_detections": 0,
            "right_channel_detections": 0,
            "processing_errors": 0,
            "last_detection_time": None,
            "processing_started": None
        }
        
        self._initialize_porcupine()
        
        logger.info(f"WakeWordDetector initialized successfully")
        logger.info(f"Resampling: {self.input_sample_rate}Hz -> {self.target_sample_rate}Hz (ratio: {self.resample_ratio:.4f})")

    def _initialize_porcupine(self) -> None:
        """Inicializa las instancias de Porcupine."""
        try:
            # Validar archivos necesarios
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Modelo no encontrado: {self.model_path}")
            
            if not os.path.exists(self.params_path):
                raise FileNotFoundError(f"Parámetros no encontrados: {self.params_path}")
            
            if not self.access_key:
                raise ValueError("PORCUPINE_ACCESS_KEY no configurado")
            
            # Crear instancia para canal izquierdo (siempre)
            self._porcupine_left = pvporcupine.create(
                access_key=self.access_key,
                keyword_paths=[self.model_path],
                model_path=self.params_path,
                sensitivities=[self.sensitivity]
            )
            
            # Crear instancia para canal derecho si se requiere procesamiento dual
            if self.process_both_channels:
                self._porcupine_right = pvporcupine.create(
                    access_key=self.access_key,
                    keyword_paths=[self.model_path],
                    model_path=self.params_path,
                    sensitivities=[self.sensitivity]
                )
            
            # Validar frame length
            expected_frame_length = self._porcupine_left.frame_length
            logger.info(f"Porcupine frame length: {expected_frame_length}")
            
            log_hardware_event("wake_word_detector_initialized", {
                "model_path": self.model_path,
                "sensitivity": self.sensitivity,
                "dual_channel": self.process_both_channels,
                "frame_length": expected_frame_length
            })
            
        except Exception as e:
            logger.error(f"Error al inicializar Porcupine: {e}")
            self._cleanup_porcupine()
            raise

    def _cleanup_porcupine(self) -> None:
        """Limpia las instancias de Porcupine."""
        if self._porcupine_left:
            self._porcupine_left.delete()
            self._porcupine_left = None
        
        if self._porcupine_right:
            self._porcupine_right.delete()
            self._porcupine_right = None

    def process_audio_chunk(self, audio_data: np.ndarray) -> None:
        """
        Procesa un chunk de audio estéreo con resampling.
        Usa funciones centralizadas de audio_resampling.
        
        Args:
            audio_data: Array de audio estéreo (shape: [samples, 2] o [samples*2])
        """
        if not self.is_running or self._porcupine_left is None:
            return
        
        try:
            # Usar función centralizada para convertir a mono (sin resampling aún)
            from utils.audio_resampling import convert_stereo_to_mono, normalize_audio
            
            # Convertir a mono si es estéreo
            if len(audio_data.shape) == 2 and audio_data.shape[1] == 2:
                mono_audio = convert_stereo_to_mono(audio_data)
            elif len(audio_data.shape) == 1 and len(audio_data) % 2 == 0:
                mono_audio = convert_stereo_to_mono(audio_data)
            else:
                mono_audio = audio_data
            
            # Normalizar a float32
            mono_audio = normalize_audio(mono_audio, np.float32)
            
            # Agregar al buffer SIN resampling
            self.audio_buffer_left = np.concatenate([self.audio_buffer_left, mono_audio])
            
            # Calcular cuántas muestras del audio original necesitamos para obtener frame_length después del resampling
            # Si frame_length = 512 (a 16kHz) y tenemos 44.1kHz, necesitamos: 512 * (44100/16000) = ~1411 samples
            samples_needed_original = int(self._porcupine_left.frame_length * self.input_sample_rate / self.target_sample_rate)
            
            # Procesar mientras tengamos suficientes muestras del audio original
            while len(self.audio_buffer_left) >= samples_needed_original:
                # Extraer chunk del audio original
                chunk_original = self.audio_buffer_left[:samples_needed_original]
                self.audio_buffer_left = self.audio_buffer_left[samples_needed_original:]
                
                # Usar función centralizada para preparar audio para Porcupine
                pcm = prepare_for_porcupine(chunk_original, self.input_sample_rate, self._porcupine_left.frame_length)
                
                # Verificar que tenemos exactamente frame_length samples
                if len(pcm) != self._porcupine_left.frame_length:
                    logger.warning(f"Frame length mismatch: expected {self._porcupine_left.frame_length}, got {len(pcm)}")
                    continue
                
                # Procesar con Porcupine
                result = self._porcupine_left.process(pcm)
                
                # Si se detectó wake word
                if result >= 0:
                    timestamp = time.time()
                    
                    # Verificar cooldown para evitar detecciones múltiples
                    if timestamp - self._last_detection_time > self._detection_cooldown:
                        logger.info(f"🔥 Wake word detected! Channel: left, Index: {result}")
                        
                        # Ejecutar callback
                        if self.on_wake_word:
                            wake_word_event = WakeWordEvent(
                                timestamp=timestamp,
                                channel="left",
                                keyword_index=result
                            )
                            self.on_wake_word(wake_word_event)
                        
                        # Actualizar estadísticas
                        self._stats["total_detections"] += 1
                        self._stats["left_channel_detections"] += 1
                        self._stats["last_detection_time"] = timestamp
                        self._last_detection_time = timestamp
                        
                        # Log del evento
                        log_hardware_event("wake_word_detected", {
                            "channel": "left",
                            "keyword_index": result,
                            "timestamp": timestamp,
                            "total_detections": self._stats["total_detections"]
                        })
            
        except Exception as e:
            logger.error(f"Error procesando chunk de audio: {e}")
            self._stats["processing_errors"] += 1

    def _process_channel(self, channel: str, porcupine: pvporcupine.Porcupine) -> None:
        """
        Procesa un canal específico en un hilo separado con resampling.
        
        Args:
            channel: 'left' o 'right'
            porcupine: Instancia de Porcupine para este canal
        """
        logger.info(f"Iniciando procesamiento del canal {channel} con resampling")
        frame_length = porcupine.frame_length
        
        # Seleccionar el buffer apropiado
        if channel == "left":
            audio_buffer = self.audio_buffer_left
        else:
            audio_buffer = self.audio_buffer_right
        
        while not self._stop_event.is_set():
            try:
                # Calcular cuántas muestras del audio original necesitamos para obtener frame_length después del resampling
                samples_needed_original = int(frame_length * self.input_sample_rate / self.target_sample_rate)
                
                if len(audio_buffer) < samples_needed_original:
                    time.sleep(0.01)  # Esperar más datos
                    continue
                
                # Extraer chunk del audio original para procesar
                chunk_original = audio_buffer[:samples_needed_original]
                
                # Actualizar el buffer (esto es un poco ineficiente, pero funcional)
                if channel == "left":
                    self.audio_buffer_left = self.audio_buffer_left[samples_needed_original:]
                    audio_buffer = self.audio_buffer_left
                else:
                    self.audio_buffer_right = self.audio_buffer_right[samples_needed_original:]
                    audio_buffer = self.audio_buffer_right
                
                # Usar función centralizada para preparar audio para Porcupine
                pcm = prepare_for_porcupine(chunk_original, self.input_sample_rate, frame_length)
                
                # Verificar que tenemos exactamente frame_length samples
                if len(pcm) != frame_length:
                    logger.warning(f"Frame length mismatch for {channel}: expected {frame_length}, got {len(pcm)}")
                    continue
                
                # Procesar con Porcupine
                keyword_index = porcupine.process(pcm)
                
                # Si se detectó wake word
                if keyword_index >= 0:
                    current_time = time.time()
                    
                    # Verificar cooldown para evitar detecciones múltiples
                    if current_time - self._last_detection_time > self._detection_cooldown:
                        self._handle_wake_word_detected(channel, keyword_index, current_time)
                        self._last_detection_time = current_time
                
                # Pequeña pausa para no saturar CPU
                time.sleep(0.005)  # 5ms
                
            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error(f"Error en procesamiento del canal {channel}: {e}")
                    self._stats["processing_errors"] += 1
                    time.sleep(0.1)  # Pausa más larga en caso de error
        
        logger.info(f"Procesamiento del canal {channel} finalizado")

    def _handle_wake_word_detected(self, channel: str, keyword_index: int, timestamp: float) -> None:
        """
        Maneja la detección de wake word.
        
        Args:
            channel: Canal donde se detectó ('left' o 'right')
            keyword_index: Índice del keyword detectado
            timestamp: Timestamp de la detección
        """
        # Actualizar estadísticas
        self._stats["total_detections"] += 1
        self._stats["last_detection_time"] = timestamp
        
        if channel == "left":
            self._stats["left_channel_detections"] += 1
        else:
            self._stats["right_channel_detections"] += 1
        
        # Crear evento de wake word
        wake_word_event = WakeWordEvent(
            timestamp=timestamp,
            channel=channel,
            keyword_index=keyword_index
        )
        
        # Log del evento
        log_hardware_event("wake_word_detected", {
            "channel": channel,
            "keyword_index": keyword_index,
            "timestamp": timestamp,
            "total_detections": self._stats["total_detections"]
        })
        
        logger.info(f"Wake word detectado en canal {channel} (detección #{self._stats['total_detections']})")
        
        # Ejecutar callback si está configurado
        if self.on_wake_word:
            try:
                self.on_wake_word(wake_word_event)
            except Exception as e:
                logger.error(f"Error en callback de wake word: {e}")

    def start(self) -> None:
        """Inicia el procesamiento de wake word."""
        if self.is_running:
            logger.warning("WakeWordDetector ya está ejecutándose")
            return
        
        if not self._porcupine_left:
            raise RuntimeError("Porcupine no está inicializado")
        
        logger.info("Iniciando WakeWordDetector...")
        self.is_running = True
        self._stop_event.clear()
        self._stats["processing_started"] = time.time()
        
        # Limpiar buffers
        self.audio_buffer.clear()
        self.audio_buffer_left = np.array([], dtype=np.float32)
        self.audio_buffer_right = np.array([], dtype=np.float32)
        
        log_hardware_event("wake_word_detector_started", {
            "dual_channel": self.process_both_channels,
            "processing_mode": "callback_based"
        })
        
        logger.info("WakeWordDetector iniciado (modo callback directo)")

    def stop(self) -> None:
        """Detiene el procesamiento de wake word."""
        if not self.is_running:
            return
        
        logger.info("Deteniendo WakeWordDetector...")
        self.is_running = False
        self._stop_event.set()
        
        log_hardware_event("wake_word_detector_stopped", {
            "total_detections": self._stats["total_detections"],
            "processing_errors": self._stats["processing_errors"]
        })
        
        logger.info("WakeWordDetector detenido")

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del detector.
        
        Returns:
            Dict con estadísticas de funcionamiento
        """
        stats = self._stats.copy()
        stats["is_running"] = self.is_running
        stats["buffer_stats"] = self.audio_buffer.get_combined_stats()
        stats["config"] = {
            "sensitivity": self.sensitivity,
            "dual_channel": self.process_both_channels,
            "require_both": self.require_both_channels,
            "cooldown_seconds": self._detection_cooldown
        }
        return stats

    def set_sensitivity(self, sensitivity: float) -> None:
        """
        Actualiza la sensibilidad del detector.
        
        Args:
            sensitivity: Nueva sensibilidad (0.0 - 1.0)
        """
        if not 0.0 <= sensitivity <= 1.0:
            raise ValueError("Sensibilidad debe estar entre 0.0 y 1.0")
        
        was_running = self.is_running
        if was_running:
            self.stop()
        
        self.sensitivity = sensitivity
        
        # Reinicializar Porcupine con nueva sensibilidad
        self._cleanup_porcupine()
        self._initialize_porcupine()
        
        if was_running:
            self.start()
        
        logger.info(f"Sensibilidad actualizada a {sensitivity}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        self._cleanup_porcupine()


# Función de conveniencia para testing
def test_wake_word_detector():
    """Función de prueba básica."""
    def on_detection(event: WakeWordEvent):
        print(f"🎙️ Wake word detectado en canal {event.channel} a las {event.timestamp}")
    
    detector = WakeWordDetector(on_wake_word=on_detection)
    
    try:
        detector.start()
        print("Detector iniciado. Presiona Ctrl+C para parar...")
        
        while True:
            time.sleep(1)
            stats = detector.get_stats()
            if stats["buffer_stats"]["both_ready"]:
                print(f"Buffer listo - Detecciones: {stats['total_detections']}")
    
    except KeyboardInterrupt:
        print("\nDeteniendo detector...")
    finally:
        detector.stop()


if __name__ == "__main__":
    test_wake_word_detector()
