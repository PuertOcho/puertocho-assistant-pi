#!/usr/bin/env python3
"""
📥 Descargador de Datos Negativos para entrenamiento "Puertocho"
Descarga Common Voice español y otros datasets de ruido
"""

import os
import sys
import requests
import tarfile
import zipfile
import random
from pathlib import Path
from typing import List
import librosa
import soundfile as sf
import numpy as np
from tqdm import tqdm
import subprocess

class NegativeDataDownloader:
    def __init__(self, output_dir: str = "data/negative"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuración de audio
        self.sample_rate = 16000
        self.target_duration = 1.5  # segundos
        self.target_samples = int(self.sample_rate * self.target_duration)
        
        print(f"📥 Configuración descarga datos negativos:")
        print(f"   Directorio: {self.output_dir}")
        print(f"   Sample rate: {self.sample_rate} Hz")
        print(f"   Duración objetivo: {self.target_duration}s")

    def download_file(self, url: str, filename: str) -> bool:
        """Descargar archivo con barra de progreso"""
        filepath = self.output_dir / filename
        
        if filepath.exists():
            print(f"✅ {filename} ya existe")
            return True
        
        try:
            print(f"📥 Descargando {filename}...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            
            print(f"✅ {filename} descargado correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error descargando {filename}: {e}")
            return False

    def extract_archive(self, archive_path: Path, extract_to: Path = None) -> bool:
        """Extraer archivo comprimido"""
        if extract_to is None:
            extract_to = self.output_dir
            
        try:
            print(f"📦 Extrayendo {archive_path.name}...")
            
            if archive_path.suffix == '.gz' and archive_path.stem.endswith('.tar'):
                # Archivo tar.gz
                with tarfile.open(archive_path, 'r:gz') as tar:
                    tar.extractall(extract_to)
            elif archive_path.suffix == '.zip':
                # Archivo ZIP
                with zipfile.ZipFile(archive_path, 'r') as zip_file:
                    zip_file.extractall(extract_to)
            else:
                print(f"⚠️ Formato no soportado: {archive_path.suffix}")
                return False
            
            print(f"✅ {archive_path.name} extraído correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error extrayendo {archive_path.name}: {e}")
            return False

    def download_common_voice_es(self) -> bool:
        """Descargar dataset Common Voice en español"""
        print("🗣️ Descargando Common Voice en español...")
        
        # URLs de Common Voice (usar la versión más pequeña para entrenamiento)
        urls = [
            # Versión 13.0 (más reciente, pero grande)
            "https://mozilla-common-voice-datasets.s3.dualstack.us-west-2.amazonaws.com/cv-corpus-13.0-2023-03-09/cv-corpus-13.0-2023-03-09-es.tar.gz",
            # Versión 11.0 (más pequeña)
            "https://mozilla-common-voice-datasets.s3.dualstack.us-west-2.amazonaws.com/cv-corpus-11.0-2022-09-21/cv-corpus-11.0-2022-09-21-es.tar.gz"
        ]
        
        for url in urls:
            filename = url.split('/')[-1]
            if self.download_file(url, filename):
                # Extraer archivo
                archive_path = self.output_dir / filename
                if self.extract_archive(archive_path):
                    return True
        
        return False

    def download_free_sound_datasets(self) -> bool:
        """Descargar datasets de sonidos libres"""
        print("🎵 Descargando datasets de sonidos libres...")
        
        # URLs de datasets pequeños de ruido
        datasets = [
            {
                "name": "Urban Sound 8K (muestra)",
                "url": "https://github.com/karoldvl/ESC-50/archive/refs/heads/master.zip",
                "filename": "esc50.zip"
            }
        ]
        
        success = False
        for dataset in datasets:
            print(f"📥 Descargando {dataset['name']}...")
            if self.download_file(dataset['url'], dataset['filename']):
                archive_path = self.output_dir / dataset['filename']
                if self.extract_archive(archive_path):
                    success = True
        
        return success

    def generate_synthetic_noise(self, num_samples: int = 5000) -> None:
        """Generar ruido sintético como datos negativos"""
        print(f"🔧 Generando {num_samples} muestras de ruido sintético...")
        
        noise_dir = self.output_dir / "synthetic_noise"
        noise_dir.mkdir(exist_ok=True)
        
        noise_types = [
            "white_noise",
            "pink_noise", 
            "brown_noise",
            "silence",
            "low_frequency_hum"
        ]
        
        for i in tqdm(range(num_samples), desc="Generando ruido"):
            noise_type = random.choice(noise_types)
            
            # Generar ruido según el tipo
            if noise_type == "white_noise":
                audio = np.random.normal(0, 0.1, self.target_samples)
            elif noise_type == "pink_noise":
                # Aproximación de ruido rosa
                white = np.random.normal(0, 1, self.target_samples)
                audio = np.cumsum(white) / np.sqrt(len(white))
                audio = audio * 0.1
            elif noise_type == "brown_noise":
                # Ruido marrón (Browniano)
                white = np.random.normal(0, 1, self.target_samples)
                audio = np.cumsum(np.cumsum(white)) 
                audio = audio / np.max(np.abs(audio)) * 0.1
            elif noise_type == "silence":
                audio = np.zeros(self.target_samples)
                # Añadir muy poco ruido para evitar silencio absoluto
                audio += np.random.normal(0, 0.001, self.target_samples)
            elif noise_type == "low_frequency_hum":
                # Zumbido de baja frecuencia (50/60 Hz)
                t = np.linspace(0, self.target_duration, self.target_samples)
                freq = random.choice([50, 60, 100, 120])
                audio = 0.05 * np.sin(2 * np.pi * freq * t)
            
            # Normalizar
            if np.max(np.abs(audio)) > 0:
                audio = audio / np.max(np.abs(audio)) * 0.1
            
            # Guardar
            filename = f"noise_{i:05d}_{noise_type}.wav"
            filepath = noise_dir / filename
            sf.write(filepath, audio, self.sample_rate)

    def process_audio_files(self, source_dir: Path, max_files: int = 10000) -> None:
        """Procesar archivos de audio y convertirlos a formato estándar"""
        print(f"🔄 Procesando archivos de audio desde {source_dir}...")
        
        # Buscar archivos de audio
        audio_extensions = ['.wav', '.mp3', '.flac', '.ogg', '.m4a']
        audio_files = []
        
        for ext in audio_extensions:
            audio_files.extend(source_dir.rglob(f"*{ext}"))
        
        if not audio_files:
            print("⚠️ No se encontraron archivos de audio")
            return
        
        # Limitar número de archivos
        if len(audio_files) > max_files:
            audio_files = random.sample(audio_files, max_files)
        
        processed_dir = self.output_dir / "processed"
        processed_dir.mkdir(exist_ok=True)
        
        processed_count = 0
        
        for audio_file in tqdm(audio_files, desc="Procesando audio"):
            try:
                # Cargar audio
                audio, sr = librosa.load(audio_file, sr=self.sample_rate)
                
                # Dividir en segmentos si es muy largo
                if len(audio) > self.target_samples * 2:
                    # Crear múltiples segmentos
                    num_segments = len(audio) // self.target_samples
                    for i in range(min(num_segments, 5)):  # Max 5 segmentos por archivo
                        start = i * self.target_samples
                        end = start + self.target_samples
                        segment = audio[start:end]
                        
                        # Guardar segmento
                        filename = f"negative_{processed_count:06d}_seg{i}.wav"
                        filepath = processed_dir / filename
                        sf.write(filepath, segment, self.sample_rate)
                        processed_count += 1
                else:
                    # Ajustar duración
                    if len(audio) < self.target_samples:
                        # Rellenar con silencio
                        padding = self.target_samples - len(audio)
                        audio = np.pad(audio, (0, padding), mode='constant')
                    elif len(audio) > self.target_samples:
                        # Recortar
                        audio = audio[:self.target_samples]
                    
                    # Guardar
                    filename = f"negative_{processed_count:06d}.wav"
                    filepath = processed_dir / filename
                    sf.write(filepath, audio, self.sample_rate)
                    processed_count += 1
                
                # Limitar total de archivos procesados
                if processed_count >= max_files:
                    break
                    
            except Exception as e:
                print(f"⚠️ Error procesando {audio_file}: {e}")
                continue
        
        print(f"✅ Procesados {processed_count} archivos de audio")

    def create_similar_words_samples(self) -> None:
        """Crear muestras de palabras similares a 'Puertocho'"""
        print("🔤 Generando muestras de palabras similares...")
        
        similar_words = [
            "Puerto",
            "Ocho", 
            "Macho",
            "Muchacho",
            "Borracho",
            "Sancho",
            "Pancho",
            "Poncho",
            "Mocho",
            "Pocho",
            "Puerto Rico",
            "Puerto Vallarta",
            "Ocho y medio",
            "Mucho gusto"
        ]
        
        similar_dir = self.output_dir / "similar_words"
        similar_dir.mkdir(exist_ok=True)
        
        sample_count = 0
        
        for word in similar_words:
            # Generar múltiples variaciones por palabra
            for i in range(20):  # 20 variaciones por palabra
                try:
                    # Usar espeak para generar audio
                    temp_file = f"/tmp/temp_similar_{random.randint(1000,9999)}.wav"
                    
                    # Variar velocidad y tono
                    speed = random.randint(120, 200)
                    pitch = random.randint(20, 80)
                    
                    cmd = [
                        "espeak", 
                        "-v", "es",
                        "-s", str(speed),
                        "-p", str(pitch),
                        "-w", temp_file,
                        word
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True)
                    if result.returncode == 0 and os.path.exists(temp_file):
                        # Cargar y procesar audio
                        audio, sr = librosa.load(temp_file, sr=self.sample_rate)
                        
                        # Ajustar duración
                        if len(audio) < self.target_samples:
                            padding = self.target_samples - len(audio)
                            audio = np.pad(audio, (0, padding), mode='constant')
                        elif len(audio) > self.target_samples:
                            audio = audio[:self.target_samples]
                        
                        # Guardar
                        safe_word = word.replace(' ', '_').lower()
                        filename = f"similar_{sample_count:04d}_{safe_word}_{i:02d}.wav"
                        filepath = similar_dir / filename
                        sf.write(filepath, audio, self.sample_rate)
                        sample_count += 1
                        
                        # Limpiar archivo temporal
                        os.remove(temp_file)
                
                except Exception as e:
                    print(f"⚠️ Error generando '{word}': {e}")
                    continue
        
        print(f"✅ Generadas {sample_count} muestras de palabras similares")

    def download_and_prepare_negative_data(self) -> None:
        """Función principal para descargar y preparar todos los datos negativos"""
        print("📥 Descargando y preparando datos negativos...")
        
        # 1. Intentar descargar Common Voice
        print("\n1️⃣ Common Voice en español...")
        cv_success = self.download_common_voice_es()
        
        # 2. Generar ruido sintético (siempre funciona)
        print("\n2️⃣ Ruido sintético...")
        self.generate_synthetic_noise(5000)
        
        # 3. Generar palabras similares
        print("\n3️⃣ Palabras similares...")
        self.create_similar_words_samples()
        
        # 4. Procesar archivos descargados
        if cv_success:
            print("\n4️⃣ Procesando Common Voice...")
            cv_dirs = list(self.output_dir.rglob("cv-corpus-*"))
            for cv_dir in cv_dirs:
                clips_dir = cv_dir / "es" / "clips"
                if clips_dir.exists():
                    self.process_audio_files(clips_dir, max_files=8000)
                    break
        
        # 5. Mostrar estadísticas finales
        self.show_dataset_stats()

    def show_dataset_stats(self) -> None:
        """Mostrar estadísticas del dataset negativo"""
        print("\n📊 Estadísticas del dataset negativo:")
        
        total_files = 0
        total_duration = 0
        
        categories = {
            "processed": "Common Voice procesado",
            "synthetic_noise": "Ruido sintético", 
            "similar_words": "Palabras similares"
        }
        
        for folder, description in categories.items():
            folder_path = self.output_dir / folder
            if folder_path.exists():
                files = list(folder_path.glob("*.wav"))
                count = len(files)
                
                # Calcular duración aproximada
                duration = count * self.target_duration
                
                print(f"   {description}: {count} archivos ({duration:.1f}s)")
                total_files += count
                total_duration += duration
        
        print(f"   📊 TOTAL: {total_files} archivos ({total_duration/60:.1f} minutos)")
        
        if total_files < 5000:
            print("⚠️ Pocos datos negativos. Considera generar más ruido sintético.")
        else:
            print("✅ Suficientes datos negativos para entrenamiento")

def main():
    """Función principal"""
    print("📥 Descargador de Datos Negativos 'Puertocho'")
    print("=" * 50)
    
    # Crear descargador
    downloader = NegativeDataDownloader()
    
    # Descargar y preparar datos
    downloader.download_and_prepare_negative_data()
    
    print("\n✅ Datos negativos preparados correctamente!")
    print("💡 Próximo paso: Configurar entrenamiento")

if __name__ == "__main__":
    main() 