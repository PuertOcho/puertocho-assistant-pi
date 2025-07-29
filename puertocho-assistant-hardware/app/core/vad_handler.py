import webrtcvad
import numpy as np
import collections
import logging
from typing import Optional, Callable
import io
import wave
from utils.audio_resampling import prepare_for_vad

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
                 on_voice_end=None,
                 on_audio_captured=None):
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
        self.on_audio_captured = on_audio_captured
        
        self._in_speech = False
        self._last_voice_time = None
        self._audio_buffer = []  # Buffer para capturar el audio completo
        self._pre_buffer = collections.deque(maxlen=10)  # Pre-buffer para incluir audio antes del habla
        self.logger = logging.getLogger("vad_handler")
        
        self.logger.info(f"VADHandler initialized: target_sr={sample_rate}, input_sr={input_sample_rate}, "
                        f"frame_duration={frame_duration}ms, aggressiveness={aggressiveness}, "
                        f"silence_timeout={silence_timeout}s")

    def process_audio_chunk(self, audio_data, timestamp=None):
        """
        Procesa un chunk de audio (numpy array estéreo float32).
        Convierte a formato requerido por WebRTC VAD y captura audio.
        """
        import time
        
        # Convertir numpy array a mono y resamplear
        if isinstance(audio_data, np.ndarray):
            # Usar función centralizada para preparar audio para VAD
            mono_audio = prepare_for_vad(audio_data, self.input_sample_rate)
            
            # Guardar audio original para captura (antes de convertir a int16)
            audio_for_capture = mono_audio.copy()
            
            # Convertir de float32 a int16 para VAD
            if mono_audio.dtype == np.float32:
                mono_audio = np.clip(mono_audio, -1.0, 1.0)
                audio_int16 = (mono_audio * 32767).astype(np.int16)
            else:
                audio_int16 = mono_audio.astype(np.int16)
            
            audio_bytes_converted = audio_int16.tobytes()
        else:
            self.logger.error("Audio data must be numpy array")
            return
        
        now = timestamp or time.time()
        
        # Agregar al pre-buffer (para capturar un poco antes del inicio del habla)
        self._pre_buffer.append(audio_for_capture)
        
        # Procesar frames para VAD
        frames_processed = 0
        for i in range(0, len(audio_bytes_converted), self.frame_size):
            frame = audio_bytes_converted[i:i+self.frame_size]
            if len(frame) < self.frame_size:
                # Pad el último frame si es necesario
                frame = frame + b'\x00' * (self.frame_size - len(frame))
            
            try:
                is_speech = self.vad.is_speech(frame, self.sample_rate)
                frames_processed += 1
                
                if is_speech:
                    if not self._in_speech:
                        # Inicio del habla
                        self._in_speech = True
                        self._last_voice_time = now
                        # Incluir pre-buffer en la captura
                        self._audio_buffer = list(self._pre_buffer)
                        self.logger.info("🎤 Voice start detected")
                        if self.on_voice_start:
                            self.on_voice_start(now)
                    else:
                        self._last_voice_time = now
                    
                    # Capturar audio durante el habla
                    start_idx = i // 2  # Convertir bytes a samples
                    end_idx = min((i + self.frame_size) // 2, len(audio_for_capture))
                    self._audio_buffer.append(audio_for_capture[start_idx:end_idx])
                    
                else:
                    if self._in_speech:
                        # Seguir capturando durante el silencio (por si es una pausa)
                        start_idx = i // 2
                        end_idx = min((i + self.frame_size) // 2, len(audio_for_capture))
                        self._audio_buffer.append(audio_for_capture[start_idx:end_idx])
                        
                        # Verificar si el silencio ha durado suficiente
                        if self._last_voice_time and (now - self._last_voice_time) > self.silence_timeout:
                            self._in_speech = False
                            self.logger.info(f"🔇 Voice end detected after {self.silence_timeout}s silence")
                            
                            # Concatenar todo el audio capturado
                            if self._audio_buffer:
                                captured_audio = np.concatenate(self._audio_buffer)
                                self.logger.info(f"📼 Captured {len(captured_audio)/self.sample_rate:.2f}s of audio")
                                
                                # Notificar con el audio capturado
                                if self.on_voice_end:
                                    self.on_voice_end(now)
                                if self.on_audio_captured:
                                    self.on_audio_captured(captured_audio, self.sample_rate)
                                
                                # Limpiar buffer
                                self._audio_buffer = []
                            
            except Exception as e:
                self.logger.error(f"Error in VAD processing frame {frames_processed}: {e}")
                continue
        
        # Log de debug cada cierto tiempo
        if frames_processed > 0 and not self._in_speech:
            self.logger.debug(f"Processed {frames_processed} frames, no speech detected")

    def save_captured_audio(self, filename: str) -> Optional[bytes]:
        """
        Guarda el audio capturado en un archivo WAV y retorna los bytes.
        """
        if not self._audio_buffer:
            return None
        
        captured_audio = np.concatenate(self._audio_buffer)
        
        # Convertir a int16 para WAV
        audio_int16 = (captured_audio * 32767).astype(np.int16)
        
        # Crear WAV en memoria
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        # Guardar a archivo si se especifica
        if filename:
            with open(filename, 'wb') as f:
                f.write(wav_buffer.getvalue())
        
        return wav_buffer.getvalue()

    def set_aggressiveness(self, level):
        self.vad.set_mode(level)

    def set_silence_timeout(self, timeout):
        self.silence_timeout = timeout

    def reset(self):
        """Resetea el estado del VAD"""
        self._in_speech = False
        self._last_voice_time = None
        self._audio_buffer = []
        self._pre_buffer.clear()
        self.logger.debug("VAD handler reset")
