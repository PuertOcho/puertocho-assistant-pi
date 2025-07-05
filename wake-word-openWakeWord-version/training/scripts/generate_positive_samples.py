#!/usr/bin/env python3
"""
🗣️ Generador de Muestras Positivas para "Puertocho"
Genera ~2000 variaciones usando múltiples métodos TTS
"""

import os
import sys
import time
import random
import subprocess
from pathlib import Path
from typing import List, Dict
import numpy as np
import librosa
import soundfile as sf
from tqdm import tqdm

# Intentar importar gTTS
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("⚠️ gTTS no disponible, usando solo métodos locales")

class PuertochoDataGenerator:
    def __init__(self, output_dir: str = "data/positive"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuración de audio
        self.sample_rate = 16000
        self.target_duration = 1.5  # segundos
        self.target_samples = int(self.sample_rate * self.target_duration)
        
        # Frases base para "Puertocho"
        self.base_phrases = [
            "Puertocho",
            "Hola Puertocho", 
            "Oye Puertocho",
            "Hey Puertocho",
            "Activa Puertocho",
            "Puertocho despierta",
            "Puertocho ayuda",
        ]
        
        # Configuraciones de velocidad y tono
        self.speed_variations = [0.8, 0.9, 1.0, 1.1, 1.2]
        self.pitch_variations = [0.9, 0.95, 1.0, 1.05, 1.1]
        
        print(f"🎯 Configuración:")
        print(f"   Directorio: {self.output_dir}")
        print(f"   Sample rate: {self.sample_rate} Hz")
        print(f"   Duración objetivo: {self.target_duration}s")
        print(f"   Frases base: {len(self.base_phrases)}")

    def normalize_audio(self, audio: np.ndarray, target_db: float = -20.0) -> np.ndarray:
        """Normalizar audio a un nivel específico"""
        if len(audio) == 0:
            return audio
            
        # Calcular RMS
        rms = np.sqrt(np.mean(audio**2))
        if rms == 0:
            return audio
            
        # Convertir dB objetivo a amplitud
        target_rms = 10**(target_db/20)
        
        # Normalizar
        normalized = audio * (target_rms / rms)
        
        # Evitar clipping
        max_val = np.max(np.abs(normalized))
        if max_val > 1.0:
            normalized = normalized / max_val * 0.95
            
        return normalized

    def adjust_duration(self, audio: np.ndarray) -> np.ndarray:
        """Ajustar duración del audio"""
        current_length = len(audio)
        
        if current_length > self.target_samples:
            # Recortar desde el centro
            start = (current_length - self.target_samples) // 2
            return audio[start:start + self.target_samples]
        elif current_length < self.target_samples:
            # Rellenar con silencio
            padding = self.target_samples - current_length
            left_pad = padding // 2
            right_pad = padding - left_pad
            return np.pad(audio, (left_pad, right_pad), mode='constant')
        else:
            return audio

    def add_noise(self, audio: np.ndarray, noise_level: float = 0.005) -> np.ndarray:
        """Añadir ruido blanco sutil"""
        noise = np.random.normal(0, noise_level, len(audio))
        return audio + noise

    def change_pitch(self, audio: np.ndarray, pitch_factor: float) -> np.ndarray:
        """Cambiar tono del audio usando librosa"""
        try:
            # Cambiar pitch manteniendo la duración
            n_steps = 12 * np.log2(pitch_factor)
            return librosa.effects.pitch_shift(audio, sr=self.sample_rate, n_steps=n_steps)
        except Exception as e:
            print(f"⚠️ Error cambiando pitch: {e}")
            return audio

    def change_speed(self, audio: np.ndarray, speed_factor: float) -> np.ndarray:
        """Cambiar velocidad del audio"""
        try:
            # Cambiar velocidad y luego ajustar duración
            stretched = librosa.effects.time_stretch(audio, rate=speed_factor)
            return self.adjust_duration(stretched)
        except Exception as e:
            print(f"⚠️ Error cambiando velocidad: {e}")
            return self.adjust_duration(audio)

    def generate_with_espeak(self, text: str, voice: str = "es") -> np.ndarray:
        """Generar audio usando espeak"""
        try:
            # Crear archivo temporal
            temp_file = f"/tmp/temp_espeak_{random.randint(1000,9999)}.wav"
            
            # Generar audio con espeak
            cmd = [
                "espeak", 
                "-v", voice,
                "-s", "150",  # velocidad
                "-w", temp_file,
                text
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return np.array([])
            
            # Cargar audio
            audio, sr = librosa.load(temp_file, sr=self.sample_rate)
            
            # Limpiar archivo temporal
            os.remove(temp_file)
            
            return audio
            
        except Exception as e:
            print(f"⚠️ Error con espeak: {e}")
            return np.array([])

    def generate_with_festival(self, text: str) -> np.ndarray:
        """Generar audio usando Festival"""
        try:
            # Crear archivo temporal
            temp_file = f"/tmp/temp_festival_{random.randint(1000,9999)}.wav"
            
            # Generar audio con Festival
            cmd = f'echo "{text}" | festival --tts --otype riff --o {temp_file}'
            
            result = subprocess.run(cmd, shell=True, capture_output=True)
            if result.returncode != 0 or not os.path.exists(temp_file):
                return np.array([])
            
            # Cargar audio
            audio, sr = librosa.load(temp_file, sr=self.sample_rate)
            
            # Limpiar archivo temporal
            os.remove(temp_file)
            
            return audio
            
        except Exception as e:
            print(f"⚠️ Error con Festival: {e}")
            return np.array([])

    def generate_with_gtts(self, text: str, lang: str = "es") -> np.ndarray:
        """Generar audio usando gTTS (Google Text-to-Speech)"""
        if not GTTS_AVAILABLE:
            return np.array([])
            
        try:
            # Crear archivo temporal
            temp_file = f"/tmp/temp_gtts_{random.randint(1000,9999)}.mp3"
            
            # Generar audio con gTTS
            tts = gTTS(text=text, lang=lang)
            tts.save(temp_file)
            
            # Cargar y convertir de MP3 a WAV
            audio, sr = librosa.load(temp_file, sr=self.sample_rate)
            
            # Limpiar archivo temporal
            os.remove(temp_file)
            
            return audio
            
        except Exception as e:
            print(f"⚠️ Error con gTTS: {e}")
            return np.array([])

    def generate_sample(self, phrase: str, method: str, sample_id: int) -> bool:
        """Generar una muestra individual"""
        try:
            # Generar audio base según el método
            if method == "espeak":
                audio = self.generate_with_espeak(phrase)
            elif method == "festival":
                audio = self.generate_with_festival(phrase)
            elif method == "gtts":
                audio = self.generate_with_gtts(phrase)
            else:
                return False
            
            if len(audio) == 0:
                return False
            
            # Aplicar variaciones aleatorias
            speed_factor = random.choice(self.speed_variations)
            pitch_factor = random.choice(self.pitch_variations)
            noise_level = random.uniform(0.001, 0.01)
            
            # Procesar audio
            audio = self.change_speed(audio, speed_factor)
            audio = self.change_pitch(audio, pitch_factor)
            audio = self.add_noise(audio, noise_level)
            audio = self.normalize_audio(audio)
            audio = self.adjust_duration(audio)
            
            # Guardar archivo
            filename = f"puertocho_{sample_id:04d}_{method}_{phrase.replace(' ', '_').lower()}.wav"
            filepath = self.output_dir / filename
            
            sf.write(filepath, audio, self.sample_rate)
            
            return True
            
        except Exception as e:
            print(f"⚠️ Error generando muestra {sample_id}: {e}")
            return False

    def generate_dataset(self, target_samples: int = 2000) -> None:
        """Generar dataset completo"""
        print(f"🚀 Generando {target_samples} muestras de 'Puertocho'...")
        
        # Métodos TTS disponibles
        methods = ["espeak"]
        
        # Verificar qué métodos están disponibles
        if self.test_festival():
            methods.append("festival")
        if GTTS_AVAILABLE:
            methods.append("gtts")
        
        print(f"🔧 Métodos TTS disponibles: {methods}")
        
        samples_generated = 0
        sample_id = 1
        
        progress_bar = tqdm(total=target_samples, desc="Generando muestras")
        
        while samples_generated < target_samples:
            # Seleccionar frase y método aleatoriamente
            phrase = random.choice(self.base_phrases)
            method = random.choice(methods)
            
            # Generar muestra
            if self.generate_sample(phrase, method, sample_id):
                samples_generated += 1
                progress_bar.update(1)
            
            sample_id += 1
            
            # Evitar bucle infinito
            if sample_id > target_samples * 3:
                break
        
        progress_bar.close()
        
        print(f"✅ Generadas {samples_generated} muestras en {self.output_dir}")
        print(f"📊 Distribución:")
        
        # Mostrar estadísticas
        for method in methods:
            count = len(list(self.output_dir.glob(f"*_{method}_*.wav")))
            print(f"   {method}: {count} muestras")

    def test_festival(self) -> bool:
        """Probar si Festival está disponible"""
        try:
            result = subprocess.run(["festival", "--version"], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def validate_samples(self) -> None:
        """Validar las muestras generadas"""
        print("🔍 Validando muestras generadas...")
        
        audio_files = list(self.output_dir.glob("*.wav"))
        valid_samples = 0
        total_duration = 0
        
        for audio_file in tqdm(audio_files, desc="Validando"):
            try:
                audio, sr = librosa.load(audio_file, sr=None)
                duration = len(audio) / sr
                
                # Verificar duración y contenido
                if 0.5 <= duration <= 3.0 and len(audio) > 0:
                    valid_samples += 1
                    total_duration += duration
                else:
                    print(f"⚠️ Muestra inválida: {audio_file.name} (duración: {duration:.2f}s)")
                    
            except Exception as e:
                print(f"❌ Error cargando {audio_file.name}: {e}")
        
        print(f"✅ Validación completada:")
        print(f"   Muestras válidas: {valid_samples}/{len(audio_files)}")
        print(f"   Duración total: {total_duration:.1f}s")
        print(f"   Duración promedio: {total_duration/valid_samples:.2f}s")

def main():
    """Función principal"""
    print("🗣️ Generador de Muestras Positivas 'Puertocho'")
    print("=" * 50)
    
    # Crear generador
    generator = PuertochoDataGenerator()
    
    # Generar dataset
    target_samples = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    generator.generate_dataset(target_samples)
    
    # Validar muestras
    generator.validate_samples()
    
    print("\n🎯 Muestras positivas generadas correctamente!")
    print("💡 Próximo paso: Descargar datos negativos")

if __name__ == "__main__":
    main() 