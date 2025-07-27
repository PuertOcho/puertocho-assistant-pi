#!/usr/bin/env python3
"""
Test simplificado de Porcupine usando nuestro AudioManager pero con la lógica del demo oficial.
"""

import os
import sys
import time
import numpy as np
from datetime import datetime

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pvporcupine
from config import config
from core.audio_manager import AudioManager
from utils.logger import logger


def simple_resample(audio, orig_sr, target_sr):
    """
    Resampling simple usando interpolación lineal.
    """
    if orig_sr == target_sr:
        return audio
    
    # Calcular el factor de resampling
    ratio = target_sr / orig_sr
    
    # Calcular la nueva longitud
    new_length = int(len(audio) * ratio)
    
    # Crear índices para interpolación
    old_indices = np.linspace(0, len(audio) - 1, new_length)
    
    # Interpolar
    resampled = np.interp(old_indices, np.arange(len(audio)), audio)
    
    return resampled


class SimpleWakeWordTest:
    """Test simple que usa AudioManager con lógica del demo oficial."""
    
    def __init__(self):
        self.access_key = config.wake_word.access_key
        self.model_path = config.wake_word.model_path
        self.params_path = config.wake_word.params_path
        self.sensitivity = config.wake_word.sensitivity
        
        self.porcupine = None
        self.audio_manager = None
        self.is_running = False
        
        self.detection_count = 0
        self.frame_count = 0
        
        # Configuración de resampling
        self.input_sample_rate = config.audio.sample_rate  # 44100 Hz
        self.target_sample_rate = 16000  # Porcupine requiere 16kHz
        self.resample_ratio = self.target_sample_rate / self.input_sample_rate
        
        # Buffer para acumular muestras hasta tener exactamente frame_length después del resampling
        self.audio_buffer = np.array([], dtype=np.float32)
        
        print(f"🔄 Resampling configurado: {self.input_sample_rate}Hz -> {self.target_sample_rate}Hz")
        print(f"   Ratio: {self.resample_ratio:.4f}")
        
    def initialize(self):
        """Inicializa Porcupine y AudioManager."""
        print(f"Access Key: {self.access_key[:20]}...")
        print(f"Model Path: {self.model_path}")
        print(f"Params Path: {self.params_path}")
        print(f"Sensitivity: {self.sensitivity}")
        
        # Verificar archivos
        if not os.path.exists(self.model_path):
            print(f"❌ ERROR: Modelo no encontrado: {self.model_path}")
            return False
        
        if not os.path.exists(self.params_path):
            print(f"❌ ERROR: Parámetros no encontrados: {self.params_path}")
            return False
        
        try:
            # Crear Porcupine (igual que el demo oficial)
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keyword_paths=[self.model_path],
                model_path=self.params_path,
                sensitivities=[self.sensitivity]
            )
            
            print(f"✅ Porcupine inicializado correctamente")
            print(f"   Version: {self.porcupine.version}")
            print(f"   Frame length: {self.porcupine.frame_length}")
            print(f"   Sample rate: {self.porcupine.sample_rate}")
            
            # Crear AudioManager
            self.audio_manager = AudioManager()
            print(f"✅ AudioManager inicializado")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en inicialización: {e}")
            return False
    
    def audio_callback(self, audio_data: np.ndarray, frames: int, status):
        """
        Callback de audio que procesa cada chunk con resampling.
        """
        if not self.is_running or self.porcupine is None:
            return
        
        try:
            # El audio viene como estéreo [samples, 2], convertir a mono
            if len(audio_data.shape) == 2:
                # Convertir a mono promediando ambos canales
                mono_audio = np.mean(audio_data, axis=1, dtype=np.float32)
            else:
                mono_audio = audio_data.astype(np.float32)
            
            # Normalizar si no está normalizado
            if mono_audio.dtype == np.int16:
                mono_audio = mono_audio / 32767.0
            
            # Agregar al buffer
            self.audio_buffer = np.concatenate([self.audio_buffer, mono_audio])
            
            # Procesar mientras tengamos suficientes muestras
            while len(self.audio_buffer) >= int(self.porcupine.frame_length / self.resample_ratio):
                # Calcular cuántas muestras necesitamos del audio original para obtener frame_length después del resampling
                samples_needed = int(self.porcupine.frame_length / self.resample_ratio)
                
                # Extraer chunk para procesar
                chunk = self.audio_buffer[:samples_needed]
                self.audio_buffer = self.audio_buffer[samples_needed:]
                
                # Hacer resampling usando nuestra función simple
                resampled = simple_resample(chunk, self.input_sample_rate, self.target_sample_rate)
                
                # Asegurar que tenemos exactamente frame_length samples
                if len(resampled) < self.porcupine.frame_length:
                    # Pad con ceros si es muy corto
                    resampled = np.pad(resampled, (0, self.porcupine.frame_length - len(resampled)))
                elif len(resampled) > self.porcupine.frame_length:
                    # Truncar si es muy largo
                    resampled = resampled[:self.porcupine.frame_length]
                
                # Convertir a int16 como requiere Porcupine
                pcm = (resampled * 32767).astype(np.int16)
                
                # Asegurar que tenemos exactamente frame_length samples
                if len(pcm) != self.porcupine.frame_length:
                    continue
                
                self.frame_count += 1
                
                # Procesar con Porcupine
                result = self.porcupine.process(pcm)
                
                # Si se detectó wake word
                if result >= 0:
                    self.detection_count += 1
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"🔥 [{timestamp}] Wake word detectado! (#{self.detection_count})")
                    print(f"   Keyword index: {result}")
                    print(f"   Frame: {self.frame_count}")
                    print(f"   Input: {self.input_sample_rate}Hz -> Resampled: {self.target_sample_rate}Hz")
                    print(f"   PCM shape: {pcm.shape}, range: [{pcm.min()}, {pcm.max()}]")
                
                # Mostrar progreso cada 5 segundos (aproximadamente)
                if self.frame_count % 156 == 0:  # 16000/512 * 5 ≈ 156 frames
                    print(f"📊 Frames procesados: {self.frame_count}, Detecciones: {self.detection_count}")
                    print(f"   Audio stats: min={pcm.min()}, max={pcm.max()}, mean={pcm.mean():.1f}")
                    print(f"   Buffer size: {len(self.audio_buffer)} samples")
        
        except Exception as e:
            print(f"❌ Error procesando audio: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """Ejecuta el test principal."""
        if not self.initialize():
            return
        
        print(f"\n🎙️ Iniciando detección de 'Puerto-ocho'...")
        print(f"   Sensibilidad: {self.sensitivity}")
        print(f"   Frame length: {self.porcupine.frame_length}")
        print(f"   Presiona Ctrl+C para salir\n")
        
        self.is_running = True
        
        try:
            # Iniciar AudioManager con nuestro callback
            self.audio_manager.start_recording(self.audio_callback)
            
            print("🎧 AudioManager iniciado, escuchando...")
            
            # Mantener el programa corriendo
            while True:
                time.sleep(1)
        
        except KeyboardInterrupt:
            print(f"\n🛑 Deteniendo...")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpia recursos."""
        self.is_running = False
        
        if self.audio_manager:
            self.audio_manager.stop_recording()
        
        if self.porcupine:
            self.porcupine.delete()
        
        print(f"\n📈 Resultados finales:")
        print(f"   Frames procesados: {self.frame_count}")
        print(f"   Total detecciones: {self.detection_count}")


def main():
    """Función principal."""
    test = SimpleWakeWordTest()
    test.run()


if __name__ == "__main__":
    main()
