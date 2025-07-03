#!/usr/bin/env python3
"""
🎤 Generador de Muestras Positivas "Puertocho" usando Azure TTS
Utiliza el servicio Azure TTS desplegado para generar muestras de alta calidad
"""

import os
import sys
import random
import requests
import numpy as np
import soundfile as sf
import librosa
from tqdm import tqdm
import time
import json
import io
from pathlib import Path

# Configuración del servicio Azure TTS
AZURE_TTS_URL = "https://azure-tts.antoniopuerto.com"
SAMPLE_RATE = 16000  # openWakeWord requiere 16kHz
TARGET_DURATION = 1.5  # Duración objetivo en segundos

# Frases base para generar variaciones
BASE_PHRASES = [
    "Puertocho",
    "Puerto ocho",
    "Hola Puertocho", 
    "Oye Puertocho",
    "Hey Puertocho",
    "Escucha Puertocho",
    "Eh Puertocho",
    "Hola Puerto ocho",
    "Oye Puerto ocho"
]

# Voces españolas disponibles (femeninas y masculinas)
SPANISH_VOICES = {
    "es-ES": [
        "Abril", "Elvira", "Esperanza", "Montserrat", "Candela", 
        "Vega", "Ximena", "Paloma", "Triana", "Vera",
        "Dario", "Gilberto", "Liberto", "Rodrigo", "Alvaro", "Pablo"
    ],
    "es-MX": ["Beatriz", "Candela", "Carlota", "Cecilio", "Gerardo", "Jorge", "Larissa", "Liberto", "Luciano", "Montserrat", "Nuria", "Pelayo", "Renata", "Yago"],
    "es-AR": ["Elena", "Tomas"],
    "es-CO": ["Gonzalo", "Salome"],
    "es-PE": ["Alex", "Camila"],
    "es-CL": ["Catalina", "Lorenzo"],
    "es-UY": ["Mateo", "Valentina"]
}

def get_available_voices():
    """Obtener voces disponibles del servicio Azure TTS"""
    try:
        response = requests.get(f"{AZURE_TTS_URL}/voices", timeout=10)
        if response.status_code == 200:
            voices_data = response.json()
            voices_by_language = voices_data.get("voices_by_language", {})
            
            # Lista negra de voces que Azure no soporta en la región (detectado por 400)
            unsupported = {"Lola", "Nia", "Tania", "Mar", "Sol"}

            # Convertir formato de Azure TTS a formato simple
            simple_voices = {}
            for lang, voice_data in voices_by_language.items():
                if isinstance(voice_data, dict):
                    # Combinar y filtrar
                    all_voices = [v for v in (voice_data.get("female", []) + voice_data.get("male", [])) if v not in unsupported]
                    if all_voices:
                        simple_voices[lang] = all_voices
                else:
                    # A veces voice_data puede ser lista; filtrar igualmente
                    filtered = [v for v in voice_data if v not in unsupported]
                    if filtered:
                        simple_voices[lang] = filtered
            
            return simple_voices
        else:
            print(f"⚠️ Error obteniendo voces: {response.status_code}")
            return SPANISH_VOICES
    except Exception as e:
        print(f"⚠️ Error conectando con Azure TTS: {e}")
        print("🔄 Usando voces predefinidas...")
        return SPANISH_VOICES

def generate_phrase_variations(base_phrases, num_variations=500):
    """Generar variaciones de las frases base (con un máximo de **un** prefijo)."""

    variations: list[str] = []

    # Prefijos permitidos (con espacio final)
    prefix_words = ["Eh", "Oye", "Hey", "Escucha", "Ven", "Mira", "Hola"]
    prefixes = [w + " " for w in prefix_words]

    for _ in range(num_variations):
        phrase = random.choice(base_phrases)

        # ¿La frase ya contiene prefijo?
        first_word = phrase.split()[0].strip().capitalize()
        has_prefix = first_word in prefix_words

        # Si no tiene prefijo, agregar uno con cierta probabilidad
        if not has_prefix and random.random() < 0.4:
            phrase = random.choice(prefixes) + phrase

        variations.append(phrase.strip())

    # Pesar las frases base simples para que aparezcan más (30 repeticiones)
    variations.extend(base_phrases * 30)

    # Devolver únicas
    return list(set(variations))

def synthesize_audio_azure(text, language="es-ES", voice=None, speed=1.0):
    """Sintetizar audio usando Azure TTS"""
    try:
        # Seleccionar voz aleatoria si no se especifica
        if voice is None:
            available_voices = get_available_voices()
            if language in available_voices and available_voices[language]:
                voice = random.choice(available_voices[language])
            else:
                voice = "Abril"  # Fallback
        
        # Preparar datos para la API
        payload = {
            "text": text,
            "language": language,
            "voice": voice,
            "speed": speed
        }
        
        # Realizar petición
        response = requests.post(
            f"{AZURE_TTS_URL}/synthesize",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.content, voice
        else:
            print(f"⚠️ Error Azure TTS ({response.status_code}): {response.text}")
            return None, voice
            
    except Exception as e:
        print(f"⚠️ Error sintetizando '{text}': {str(e)}")
        return None, voice

def process_audio(audio_data, target_sr=16000, target_duration=1.5):
    """Procesar audio: resample y ajustar duración"""
    try:
        # Cargar audio desde bytes
        audio, sr = sf.read(io.BytesIO(audio_data))
        
        # Resample a 16kHz si es necesario
        if sr != target_sr:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
            sr = target_sr
        
        # Normalizar audio
        if len(audio) > 0:
            audio = audio / (np.max(np.abs(audio)) + 1e-8)
        
        # Ajustar duración
        target_samples = int(target_duration * sr)
        
        if len(audio) > target_samples:
            # Truncar desde el centro
            start = (len(audio) - target_samples) // 2
            audio = audio[start:start + target_samples]
        elif len(audio) < target_samples:
            # Pad con silencio
            padding = target_samples - len(audio)
            pad_start = padding // 2
            pad_end = padding - pad_start
            audio = np.pad(audio, (pad_start, pad_end), mode='constant', constant_values=0)
        
        return audio, sr
        
    except Exception as e:
        print(f"⚠️ Error procesando audio: {e}")
        return None, target_sr

def apply_audio_augmentation(audio, sr):
    """Aplicar aumentación de datos al audio"""
    try:
        # Copia para no modificar original
        augmented = audio.copy()
        
        # 1. Cambio de velocidad (ocasional)
        if random.random() < 0.3:
            speed_factor = random.uniform(0.9, 1.1)
            augmented = librosa.effects.time_stretch(augmented, rate=speed_factor)
        
        # 2. Cambio de tono (ocasional)
        if random.random() < 0.3:
            pitch_shift = random.uniform(-2, 2)  # semitonos
            augmented = librosa.effects.pitch_shift(augmented, sr=sr, n_steps=pitch_shift)
        
        # 3. Añadir ruido muy suave (ocasional)
        if random.random() < 0.4:
            noise_level = random.uniform(0.001, 0.005)
            noise = np.random.normal(0, noise_level, len(augmented))
            augmented = augmented + noise
        
        # 4. Normalizar después de augmentación
        if len(augmented) > 0:
            augmented = augmented / (np.max(np.abs(augmented)) + 1e-8)
        
        return augmented
        
    except Exception as e:
        print(f"⚠️ Error en augmentación: {e}")
        return audio

def generate_positive_samples(output_dir="data/positive", num_samples=2000):
    """Generar muestras positivas usando Azure TTS"""
    
    print("🎤 Generador de Muestras Positivas 'Puertocho' - Azure TTS")
    print("=" * 60)
    
    # Crear directorio de salida
    os.makedirs(output_dir, exist_ok=True)
    
    # Verificar conexión con Azure TTS
    print("🔍 Verificando conexión con Azure TTS...")
    try:
        response = requests.get(f"{AZURE_TTS_URL}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Azure TTS conectado - {health_data.get('region', 'N/A')}")
        else:
            print("❌ Error conectando con Azure TTS")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False
    
    # Obtener voces disponibles
    print("🎭 Obteniendo voces disponibles...")
    available_voices = get_available_voices()
    total_voices = sum(len(voices) for voices in available_voices.values())
    print(f"✅ {total_voices} voces disponibles en {len(available_voices)} idiomas")
    
    # Generar variaciones de frases
    print("📝 Generando variaciones de frases...")
    phrase_variations = generate_phrase_variations(BASE_PHRASES, num_samples)
    print(f"✅ {len(phrase_variations)} variaciones de frases generadas")
    
    # Configuración
    print(f"\n🎯 Configuración:")
    print(f"   Directorio salida: {output_dir}")
    print(f"   Muestras objetivo: {num_samples}")
    print(f"   Sample rate: {SAMPLE_RATE} Hz")
    print(f"   Duración objetivo: {TARGET_DURATION}s")
    print(f"   Endpoint Azure: {AZURE_TTS_URL}")
    
    # Generar muestras
    print(f"\n🚀 Generando {num_samples} muestras...")
    
    successful_samples = 0
    failed_samples = 0
    
    with tqdm(total=num_samples, desc="Generando muestras") as pbar:
        for i in range(num_samples):
            try:
                # Seleccionar frase y configuración
                phrase = random.choice(phrase_variations)
                
                # Solo usar idiomas españoles disponibles
                spanish_languages = [lang for lang in available_voices.keys() if lang.startswith('es-')]
                language = random.choice(spanish_languages)
                
                # Variación de velocidad (0.7–1.6) según preferencia del usuario
                speed = random.uniform(0.7, 1.6)
                
                # Sintetizar con Azure TTS
                audio_data, voice_used = synthesize_audio_azure(
                    phrase, language=language, speed=speed
                )
                
                if audio_data is None:
                    failed_samples += 1
                    pbar.update(1)
                    continue
                
                # Procesar audio
                audio, sr = process_audio(audio_data, SAMPLE_RATE, TARGET_DURATION)
                
                if audio is None:
                    failed_samples += 1
                    pbar.update(1)
                    continue
                
                # Aplicar augmentación ocasional
                if random.random() < 0.5:  # 50% de las muestras
                    audio = apply_audio_augmentation(audio, sr)
                
                # Guardar archivo con velocidad en el nombre
                speed_str = f"{speed:.1f}x".replace(".", "_")
                filename = f"puertocho_{i:05d}_{language}_{voice_used}_{speed_str}.wav"
                filepath = os.path.join(output_dir, filename)
                
                sf.write(filepath, audio, sr)
                successful_samples += 1
                
                # Pequeña pausa para no sobrecargar el servicio
                if i % 10 == 0:
                    time.sleep(0.1)
                
            except Exception as e:
                print(f"\n⚠️ Error generando muestra {i}: {e}")
                failed_samples += 1
            
            pbar.update(1)
    
    # Resumen final
    print(f"\n📊 Generación completada:")
    print(f"   ✅ Muestras exitosas: {successful_samples}")
    print(f"   ❌ Muestras fallidas: {failed_samples}")
    print(f"   📁 Directorio: {output_dir}")
    print(f"   🎯 Tasa de éxito: {successful_samples/num_samples*100:.1f}%")
    
    # Verificar archivos generados
    wav_files = list(Path(output_dir).glob("*.wav"))
    print(f"   📄 Archivos WAV: {len(wav_files)}")
    
    if len(wav_files) > 0:
        # Mostrar estadísticas de un archivo de ejemplo
        sample_file = str(wav_files[0])
        sample_audio, sample_sr = sf.read(sample_file)
        duration = len(sample_audio) / sample_sr
        print(f"   📏 Ejemplo - Duración: {duration:.2f}s, SR: {sample_sr}Hz")
    
    return successful_samples > 0

if __name__ == "__main__":
    # Número de muestras desde argumentos o default
    num_samples = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "data/positive"
    
    success = generate_positive_samples(output_dir, num_samples)
    
    if success:
        print("\n🎉 ¡Generación completada exitosamente!")
        sys.exit(0)
    else:
        print("\n❌ Error en la generación")
        sys.exit(1) 