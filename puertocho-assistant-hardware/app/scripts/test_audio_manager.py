#!/usr/bin/env python3
"""
Script de prueba simple para AudioManager
Ejecuta una prueba básica de funcionalidad del AudioManager
"""

import sys
import os
import time
import numpy as np
import wave
from datetime import datetime
from pathlib import Path

# Añadir el directorio de la app al path para imports absolutos
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

# Cambiar al directorio de la app para que los imports funcionen
os.chdir(str(app_dir))

try:
    from core.audio_manager import AudioManager
    from config import config
    from utils.logger import logger
except ImportError as e:
    print(f"❌ Error al importar módulos: {e}")
    print("Asegúrate de estar en el directorio correcto y que todos los archivos existan.")
    print(f"Directorio actual: {os.getcwd()}")
    print(f"App directory: {app_dir}")
    sys.exit(1)

def save_audio_to_file(raw_audio_data, audio_manager):
    """
    Guarda los datos de audio capturados en un archivo WAV.
    
    Args:
        raw_audio_data (list): Lista de arrays de numpy con los datos de audio
        audio_manager (AudioManager): Instancia del AudioManager para obtener configuración
        
    Returns:
        str: Ruta del archivo guardado
    """
    # Crear directorio de audio si no existe
    audio_dir = Path("data/audio_tests")
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    # Generar nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"audio_test_{timestamp}.wav"
    filepath = audio_dir / filename
    
    # Concatenar todos los datos de audio
    if raw_audio_data:
        audio_data = np.concatenate(raw_audio_data, axis=0)
        
        # Normalizar datos al rango de int16
        if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
            # Asegurar que los valores están en el rango [-1, 1]
            audio_data = np.clip(audio_data, -1.0, 1.0)
            # Convertir a int16
            audio_data = (audio_data * 32767).astype(np.int16)
        
        # Guardar como archivo WAV
        with wave.open(str(filepath), 'wb') as wav_file:
            wav_file.setnchannels(audio_manager.channels)
            wav_file.setsampwidth(2)  # 2 bytes = 16 bits
            wav_file.setframerate(audio_manager.sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return str(filepath)
    else:
        raise ValueError("No hay datos de audio para guardar")

def test_audio_basic():
    """Prueba básica del AudioManager"""
    print("🔊 Iniciando prueba básica de AudioManager...")
    
    try:
        # 1. Mostrar configuración
        print(f"\n📋 Configuración de audio:")
        print(f"   Sample Rate: {config.audio.sample_rate} Hz")
        print(f"   Channels: {config.audio.channels}")
        print(f"   Chunk Size: {config.audio.chunk_size}")
        print(f"   Device Name: {config.audio.device_name}")
        print(f"   Buffer Size: {config.audio.buffer_size}")
        
        # 2. Listar dispositivos disponibles
        print(f"\n🎤 Dispositivos de audio disponibles:")
        devices_info = AudioManager.list_audio_devices()
        
        if not devices_info:
            print("   ❌ No se pudieron listar los dispositivos de audio")
            return False
            
        input_devices = devices_info.get("input_devices", [])
        print(f"   Dispositivos de entrada encontrados: {len(input_devices)}")
        
        for i, device in enumerate(input_devices[:5]):  # Mostrar máximo 5
            print(f"   [{i}] {device['name']} - Canales: {device['max_input_channels']}")
        
        # 3. Inicializar AudioManager
        print(f"\n🎛️  Inicializando AudioManager...")
        audio_manager = AudioManager()
        print(f"   ✅ AudioManager inicializado correctamente")
        print(f"   Dispositivo seleccionado: {audio_manager.input_device_index}")
        
        # 4. Test de grabación corta (si hay hardware)
        print(f"\n🎙️  Prueba de grabación (3 segundos)...")
        print(f"   Hable cerca del micrófono o haga ruido...")
        
        audio_samples = []
        raw_audio_data = []  # Para guardar el audio completo
        
        def audio_callback(indata, frames, status):
            if status:
                print(f"   ⚠️  Estado del stream: {status}")
            
            # Guardar datos de audio completos
            raw_audio_data.append(indata.copy())
            
            # Calcular nivel de volumen
            rms = np.sqrt(np.mean(indata**2))
            audio_samples.append(rms)
            
            # Mostrar barra de volumen visual
            volume_bar_length = int(rms * 50)
            volume_bar = "█" * volume_bar_length + "░" * (20 - volume_bar_length)
            print(f"\r   Volume: |{volume_bar}| {rms:.3f}", end="", flush=True)
        
        # Iniciar grabación
        audio_manager.start_recording(audio_callback)
        
        if not audio_manager.is_recording:
            print(f"\n   ❌ No se pudo iniciar la grabación")
            return False
        
        # Grabar por 3 segundos
        time.sleep(3)
        
        # Detener grabación
        audio_manager.stop_recording()
        print(f"\n   ✅ Grabación completada")
        
        # 5. Análisis de los datos capturados
        if audio_samples:
            avg_rms = np.mean(audio_samples)
            max_rms = np.max(audio_samples)
            min_rms = np.min(audio_samples)
            
            print(f"\n📊 Estadísticas de audio:")
            print(f"   Muestras capturadas: {len(audio_samples)}")
            print(f"   RMS promedio: {avg_rms:.4f}")
            print(f"   RMS máximo: {max_rms:.4f}")
            print(f"   RMS mínimo: {min_rms:.4f}")
            
            # Determinar si se detectó audio
            if max_rms > 0.01:  # Umbral básico
                print(f"   ✅ Audio detectado correctamente")
            else:
                print(f"   ⚠️  Nivel de audio muy bajo (posible problema de micrófono)")
            
            # 6. Guardar audio capturado
            if raw_audio_data:
                try:
                    audio_filename = save_audio_to_file(raw_audio_data, audio_manager)
                    print(f"\n💾 Audio guardado:")
                    print(f"   Archivo: {audio_filename}")
                    print(f"   Duración: ~{len(raw_audio_data) * audio_manager.chunk_size / audio_manager.sample_rate:.1f} segundos")
                    
                    # Mostrar información del archivo
                    file_size = os.path.getsize(audio_filename)
                    print(f"   Tamaño: {file_size} bytes ({file_size/1024:.1f} KB)")
                    
                except Exception as e:
                    print(f"\n⚠️  Error al guardar audio: {e}")
                    
        else:
            print(f"   ❌ No se capturaron muestras de audio")
            return False
        
        print(f"\n🎉 Prueba básica completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {e}")
        logger.error(f"Error en test de audio: {e}")
        return False

def test_audio_devices_only():
    """Prueba solo el listado de dispositivos (sin grabación)"""
    print("🔍 Listando dispositivos de audio únicamente...")
    
    try:
        devices_info = AudioManager.list_audio_devices()
        
        if not devices_info:
            print("❌ No se pudieron obtener dispositivos de audio")
            return False
        
        all_devices = devices_info.get("all_devices", [])
        input_devices = devices_info.get("input_devices", [])
        output_devices = devices_info.get("output_devices", [])
        
        print(f"\n📊 Resumen de dispositivos:")
        print(f"   Total: {len(all_devices)}")
        print(f"   Entrada: {len(input_devices)}")
        print(f"   Salida: {len(output_devices)}")
        
        print(f"\n📋 Todos los dispositivos:")
        for i, device in enumerate(all_devices):
            status = []
            if device['max_input_channels'] > 0:
                status.append(f"IN:{device['max_input_channels']}")
            if device['max_output_channels'] > 0:
                status.append(f"OUT:{device['max_output_channels']}")
            
            print(f"   [{i:2}] {device['name']:<30} ({', '.join(status)})")
        
        # Información detallada de dispositivos de entrada
        print(f"\n🎤 Dispositivos de entrada detallados:")
        for i, device in enumerate(input_devices):
            print(f"   [{i}] Nombre: {device['name']}")
            print(f"       Canales de entrada: {device['max_input_channels']}")
            print(f"       Sample rate por defecto: {device['default_samplerate']}")
            if 'hostapi' in device:
                print(f"       Host API: {device['hostapi']}")
            print()
        
        # Buscar el dispositivo configurado
        print(f"\n🔍 Buscando dispositivo configurado: '{config.audio.device_name}'")
        audio_manager = AudioManager()
        found_device = audio_manager._find_device_by_name(config.audio.device_name)
        
        if found_device is not None:
            device = all_devices[found_device]
            print(f"   ✅ Encontrado en índice {found_device}: {device['name']}")
        else:
            print(f"   ⚠️  No encontrado, se usará dispositivo por defecto")
            
            # Sugerir dispositivos candidatos para ReSpeaker
            print(f"\n💡 Dispositivos candidatos para ReSpeaker 2-Mic:")
            for i, device in enumerate(input_devices):
                # ReSpeaker típicamente tiene 2 canales de entrada
                if device['max_input_channels'] == 2:
                    print(f"   🎯 [{i}] {device['name']} - {device['max_input_channels']} canales (CANDIDATO)")
                    print(f"       Para usar este dispositivo, configure: AUDIO_DEVICE_NAME=\"{device['name']}\"")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al listar dispositivos: {e}")
        return False

def test_play_last_audio():
    """Reproduce el último archivo de audio guardado"""
    print("🔊 Reproduciendo último audio guardado...")
    
    try:
        audio_dir = Path("data/audio_tests")
        if not audio_dir.exists():
            print("❌ No se encontró directorio de audio")
            print("💡 Tip: Ejecute primero la opción 1 para grabar y guardar audio")
            return False
        
        # Buscar el archivo más reciente
        audio_files = list(audio_dir.glob("audio_test_*.wav"))
        if not audio_files:
            print("❌ No se encontraron archivos de audio guardados")
            print("💡 Tip: Ejecute primero la opción 1 para grabar y guardar audio")
            return False
        
        # Ordenar por fecha de modificación (más reciente primero)
        latest_file = max(audio_files, key=lambda f: f.stat().st_mtime)
        
        print(f"📁 Archivo: {latest_file.name}")
        print(f"📊 Tamaño: {latest_file.stat().st_size} bytes")
        print(f"🕒 Fecha: {datetime.fromtimestamp(latest_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Mostrar información del archivo WAV
        try:
            with wave.open(str(latest_file), 'rb') as wav_file:
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                frame_rate = wav_file.getframerate()
                frames = wav_file.getnframes()
                duration = frames / frame_rate
                
                print(f"🎵 Información del audio:")
                print(f"   Canales: {channels}")
                print(f"   Sample Rate: {frame_rate} Hz")
                print(f"   Bits: {sample_width * 8}")
                print(f"   Duración: {duration:.2f} segundos")
        except Exception as e:
            print(f"⚠️  Error al leer información del archivo: {e}")
        
        # Intentar reproducir con comando del sistema
        print(f"\n🎧 Intentando reproducir...")
        if os.system("which aplay > /dev/null 2>&1") == 0:
            print("   Usando aplay para reproducir...")
            result = os.system(f"aplay '{latest_file}' 2>/dev/null")
            if result == 0:
                print("   ✅ Reproducción completada")
            else:
                print("   ⚠️  Error durante la reproducción")
        elif os.system("which paplay > /dev/null 2>&1") == 0:
            print("   Usando paplay para reproducir...")
            result = os.system(f"paplay '{latest_file}' 2>/dev/null")
            if result == 0:
                print("   ✅ Reproducción completada")
            else:
                print("   ⚠️  Error durante la reproducción")
        else:
            print("   ⚠️  No se encontró reproductor de audio (aplay/paplay)")
            print(f"   💡 Puedes reproducir manualmente: aplay {latest_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al reproducir audio: {e}")
        return False

def list_saved_audio_files():
    """Lista todos los archivos de audio guardados"""
    print("📂 Archivos de audio guardados...")
    
    try:
        audio_dir = Path("data/audio_tests")
        if not audio_dir.exists():
            print("❌ No se encontró directorio de audio")
            print("💡 Tip: Ejecute primero la opción 1 para grabar y guardar audio")
            return False
        
        audio_files = list(audio_dir.glob("audio_test_*.wav"))
        if not audio_files:
            print("❌ No se encontraron archivos de audio guardados")
            print("💡 Tip: Ejecute primero la opción 1 para grabar y guardar audio")
            return False
        
        # Ordenar por fecha de modificación (más reciente primero)
        audio_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        print(f"\n📊 Encontrados {len(audio_files)} archivos:")
        total_size = 0
        
        for i, file_path in enumerate(audio_files, 1):
            file_size = file_path.stat().st_size
            total_size += file_size
            file_date = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            print(f"   [{i:2}] {file_path.name}")
            print(f"       📊 {file_size} bytes ({file_size/1024:.1f} KB)")
            print(f"       🕒 {file_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Intentar leer información del WAV
            try:
                with wave.open(str(file_path), 'rb') as wav_file:
                    duration = wav_file.getnframes() / wav_file.getframerate()
                    print(f"       ⏱️  {duration:.2f} segundos")
            except:
                pass
            print()
        
        print(f"💾 Tamaño total: {total_size} bytes ({total_size/1024:.1f} KB)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al listar archivos: {e}")
        return False

def main():
    """Función principal con menú en loop"""
    print("=" * 60)
    print("🎙️  PRUEBA DE AUDIOMANAGER - PuertoCho Assistant")
    print("=" * 60)
    
    while True:
        try:
            print("\nSeleccione el tipo de prueba:")
            print("1. Prueba completa (listado + grabación + guardar)")
            print("2. Solo listado de dispositivos")
            print("3. Reproducir último audio guardado")
            print("4. Listar archivos de audio guardados")
            print("5. Salir")
            
            choice = input("\nIngrese su opción (1-5): ").strip()
            
            if choice == "1":
                print("\n" + "="*50)
                success = test_audio_basic()
                if success:
                    print("\n✅ Prueba completa exitosa!")
                else:
                    print("\n❌ La prueba falló.")
                    
            elif choice == "2":
                print("\n" + "="*50)
                success = test_audio_devices_only()
                if success:
                    print("\n✅ Listado completado!")
                else:
                    print("\n❌ Error al listar dispositivos.")
                    
            elif choice == "3":
                print("\n" + "="*50)
                success = test_play_last_audio()
                if success:
                    print("\n✅ Reproducción completada!")
                else:
                    print("\n❌ Error en la reproducción.")
                    
            elif choice == "4":
                print("\n" + "="*50)
                success = list_saved_audio_files()
                if success:
                    print("\n✅ Listado completado!")
                else:
                    print("\n❌ Error al listar archivos.")
                    
            elif choice == "5":
                print("\n👋 Saliendo del script...")
                break
                
            else:
                print("\n❌ Opción inválida. Por favor ingrese un número del 1 al 5.")
                continue
            
            # Pausa antes de volver al menú
            input("\n🔄 Presione ENTER para volver al menú principal...")
                
        except KeyboardInterrupt:
            print("\n\n👋 Script interrumpido por el usuario (Ctrl+C)")
            break
        except Exception as e:
            print(f"\n❌ Error inesperado: {e}")
            input("\n🔄 Presione ENTER para volver al menú principal...")

if __name__ == "__main__":
    main()
