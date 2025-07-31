import webrtcvad
import numpy as np
import collections
from typing import Optional, Callable
import io
import wave
from utils.audio_resampler import AudioResampler
from utils.logger import HardwareLogger, log_audio_event

class VADHandler:
    """
    Voice Activity Detection handler using WebRTC VAD.
    Captura audio durante el habla y notifica cuando termina.
    """
    def __init__(self, 
                 sample_rate=16000, 
                 input_sample_rate=44100,
                 frame_duration=30, 
                 aggressiveness=3, 
                 silence_timeout=1.5,
                 on_voice_start=None, 
                 on_voice_end=None):
        self.vad = webrtcvad.Vad(aggressiveness)
        self.sample_rate = sample_rate  # VAD requiere 16kHz
        self.input_sample_rate = input_sample_rate  # Audio viene a 44.1kHz
        self.frame_duration = frame_duration  # ms
        # Para VAD, frame_size es en samples, no bytes
        self.frame_samples = int(sample_rate * frame_duration / 1000)
        self.frame_size = self.frame_samples * 2  # bytes (16bit mono)
        self.silence_timeout = silence_timeout  # seconds
        self.on_voice_start = on_voice_start
        self.on_voice_end = on_voice_end
        
        # AudioResampler para manejo centralizado
        self.resampler = AudioResampler(cache_size=3)
        
        self._in_speech = False
        self._last_voice_time = None
        self._pre_buffer = collections.deque(maxlen=10)  # Pre-buffer para incluir audio antes del habla
        self.logger = HardwareLogger("vad_handler")
        
        self.logger.info(f"VADHandler initialized: target_sr={sample_rate}, input_sr={input_sample_rate}, "
                        f"frame_duration={frame_duration}ms, aggressiveness={aggressiveness}, "
                        f"silence_timeout={silence_timeout}s")
        
        log_audio_event("vad_handler_initialized", {
            "target_sample_rate": sample_rate,
            "input_sample_rate": input_sample_rate,
            "frame_duration": frame_duration,
            "aggressiveness": aggressiveness,
            "silence_timeout": silence_timeout
        })

    def process_audio_chunk(self, audio_data, timestamp=None):
        """
        Procesa un chunk de audio para detección de actividad de voz.
        Solo detecta inicio/fin de voz, no captura audio.
        """
        import time
        
        # Usar AudioResampler para preparar audio para VAD
        if isinstance(audio_data, np.ndarray):
            try:
                # Preparar audio para VAD usando AudioResampler
                vad_audio = self.resampler.prepare_for_vad(audio_data, self.input_sample_rate)
                
                # Convertir de float32 a int16 para VAD
                if vad_audio.dtype == np.float32:
                    vad_audio = np.clip(vad_audio, -1.0, 1.0)
                    audio_int16 = (vad_audio * 32767).astype(np.int16)
                else:
                    audio_int16 = vad_audio.astype(np.int16)
                
                audio_bytes_converted = audio_int16.tobytes()
            except Exception as e:
                self.logger.error(f"Error preparing audio for VAD: {e}")
                return
        else:
            self.logger.error("Audio data must be numpy array")
            return
        
        now = timestamp or time.time()
        
        # Procesar frames para VAD
        frames_processed = 0
        voice_detected_in_chunk = False
        
        for i in range(0, len(audio_bytes_converted), self.frame_size):
            frame = audio_bytes_converted[i:i+self.frame_size]
            if len(frame) < self.frame_size:
                # Pad el último frame si es necesario
                frame = frame + b'\x00' * (self.frame_size - len(frame))
            
            try:
                is_speech = self.vad.is_speech(frame, self.sample_rate)
                frames_processed += 1
                
                if is_speech:
                    voice_detected_in_chunk = True
                    
                    if not self._in_speech:
                        # Inicio del habla
                        self._in_speech = True
                        self._last_voice_time = now
                        self.logger.info("🎤 Voice start detected")
                        if self.on_voice_start:
                            self.on_voice_start(now)
                    else:
                        self._last_voice_time = now
                        
                else:
                    if self._in_speech:
                        # Verificar si el silencio ha durado suficiente
                        if self._last_voice_time and (now - self._last_voice_time) > self.silence_timeout:
                            self._in_speech = False
                            self.logger.info(f"🔇 Voice end detected after {self.silence_timeout}s silence")
                            
                            if self.on_voice_end:
                                self.on_voice_end(now)
                            
            except Exception as e:
                self.logger.error(f"Error in VAD processing frame {frames_processed}: {e}")
                continue
        
        # Log de debug cada cierto tiempo
        if frames_processed > 0:
            if voice_detected_in_chunk:
                self.logger.debug(f"Processed {frames_processed} frames, voice detected")
            elif not self._in_speech:
                self.logger.debug(f"Processed {frames_processed} frames, no speech detected")

    def set_aggressiveness(self, level):
        """Configura el nivel de agresividad del VAD"""
        self.vad.set_mode(level)
        self.logger.info(f"VAD aggressiveness set to {level}")

    def set_silence_timeout(self, timeout):
        """Configura el timeout de silencio"""
        self.silence_timeout = timeout
        self.logger.info(f"VAD silence timeout set to {timeout}s")

    def reset(self):
        """Resetea el estado del VAD"""
        self._in_speech = False
        self._last_voice_time = None
        self._pre_buffer.clear()
        self.logger.debug("VAD handler reset")
    
    def get_stats(self):
        """Obtiene estadísticas del VAD y AudioResampler"""
        return {
            "is_in_speech": self._in_speech,
            "last_voice_time": self._last_voice_time,
            "silence_timeout": self.silence_timeout,
            "sample_rate": self.sample_rate,
            "input_sample_rate": self.input_sample_rate,
            "frame_duration": self.frame_duration,
            "resampler_stats": self.resampler.get_performance_stats(),
            "resampler_cache": self.resampler.get_cache_info()
        }
