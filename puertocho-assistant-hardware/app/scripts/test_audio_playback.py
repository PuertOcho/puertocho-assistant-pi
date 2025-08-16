#!/usr/bin/env python3
"""
Test script para verificar la funcionalidad de reproducción de audio
"""

import sys
import os
import time
import base64
import tempfile
import subprocess
import requests
import numpy as np
from pathlib import Path

# Añadir el directorio app al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import sounddevice as sd
except ImportError:
    print("❌ sounddevice no disponible")
    sd = None

def print_header():
    """Imprimir encabezado del test"""
    print("🧪 Test de Reproducción de Audio")
    print("=" * 40)

def test_devices():
    """Test 1: Verificar dispositivos de audio"""
    print("\n1️⃣ Verificando dispositivos de audio...")
    
    if not sd:
        print("❌ sounddevice no disponible")
        return False
    
    try:
        devices = sd.query_devices()
        print("Dispositivos de entrada:")
        input_devices = []
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                print(f"  [{i}] {dev['name']} - {dev['max_input_channels']}ch")
                input_devices.append(i)
        
        print("\nDispositivos de salida:")
        output_devices = []
        for i, dev in enumerate(devices):
            if dev['max_output_channels'] > 0:
                print(f"  [{i}] {dev['name']} - {dev['max_output_channels']}ch")
                output_devices.append(i)
        
        if not output_devices:
            print("❌ No hay dispositivos de salida disponibles")
            return False
        
        print(f"✅ Encontrados {len(output_devices)} dispositivos de salida")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando dispositivos: {e}")
        return False

def test_http_server():
    """Test 2: Verificar que el servidor HTTP está respondiendo"""
    print("\n2️⃣ Verificando servidor HTTP...")
    
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor HTTP respondiendo en puerto 8080")
            return True
        else:
            print(f"❌ Servidor HTTP responde con código: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor HTTP en puerto 8080")
        return False
    except Exception as e:
        print(f"❌ Error verificando servidor HTTP: {e}")
        return False

def test_beep():
    """Test 3: Probar beep de prueba"""
    print("\n3️⃣ Probando beep de prueba...")
    
    try:
        response = requests.get("http://localhost:8080/audio/test-beep", timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Beep reproducido exitosamente")
                print(f"   Frecuencia: {result.get('frequency', 'N/A')}Hz")
                print(f"   Duración: {result.get('duration', 'N/A')}s")
                return True
            else:
                print(f"❌ Error reproduciendo beep: {result.get('error', 'Unknown')}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en test de beep: {e}")
        return False

def generate_test_audio():
    """Generar audio de prueba (tono de 440Hz por 2 segundos)"""
    try:
        sample_rate = 44100
        duration = 2.0
        frequency = 440
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Convertir a 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)
        
        return audio_data, sample_rate
    except Exception as e:
        print(f"❌ Error generando audio: {e}")
        return None, None

def test_audio_playback():
    """Test 4: Probar reproducción de audio generado"""
    print("\n4️⃣ Probando reproducción de audio generado...")
    
    # Generar audio de prueba
    audio_data, sample_rate = generate_test_audio()
    if audio_data is None:
        return False
    
    try:
        # Convertir a bytes y luego a base64
        audio_bytes = audio_data.tobytes()
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        print(f"📦 Audio generado: {len(audio_bytes)} bytes")
        
        # Enviar al endpoint
        payload = {
            "audio_data": audio_b64,
            "format": "raw",
            "sample_rate": sample_rate
        }
        
        response = requests.post(
            "http://localhost:8080/audio/play",
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Audio reproducido exitosamente")
                return True
            else:
                print(f"❌ Error reproduciendo audio: {result.get('error', 'Unknown')}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Detalle: {error_detail.get('detail', 'Unknown')}")
            except:
                pass
            return False
            
    except Exception as e:
        print(f"❌ Error en test de reproducción: {e}")
        return False

def test_audio_manager_direct():
    """Test 5: Probar AudioManager directamente"""
    print("\n5️⃣ Probando AudioManager directamente...")
    
    try:
        from core.audio_manager import AudioManager
        
        audio_manager = AudioManager()
        print("✅ AudioManager inicializado")
        
        # Generar audio de prueba
        audio_data, sample_rate = generate_test_audio()
        if audio_data is None:
            return False
        
        # Reproducir directamente
        success = audio_manager.play_audio(audio_data, sample_rate)
        
        if success:
            print("✅ Audio reproducido directamente con AudioManager")
            return True
        else:
            print("❌ Error reproduciendo audio con AudioManager")
            return False
            
    except ImportError as e:
        print(f"❌ No se puede importar AudioManager: {e}")
        return False
    except Exception as e:
        print(f"❌ Error en test directo: {e}")
        return False

def check_logs():
    """Test 6: Verificar logs recientes"""
    print("\n6️⃣ Verificando logs recientes...")
    
    try:
        # Ejecutar docker-compose logs
        result = subprocess.run(
            ["docker-compose", "logs", "--tail=20", "hardware"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        
        if result.returncode == 0:
            logs = result.stdout
            audio_logs = []
            for line in logs.split('\n'):
                if any(keyword in line for keyword in ['🎵', '🔊', 'Audio', 'Playing', 'play_audio', 'test-beep']):
                    audio_logs.append(line)
            
            if audio_logs:
                print("Logs de audio encontrados:")
                for log in audio_logs[-5:]:  # Últimos 5
                    print(f"  {log}")
            else:
                print("No hay logs de audio recientes")
            
            # Verificar errores
            error_logs = []
            for line in logs.split('\n'):
                if any(keyword in line for keyword in ['ERROR', 'Error', '❌']):
                    error_logs.append(line)
            
            if error_logs:
                print("\nErrores encontrados:")
                for log in error_logs[-3:]:  # Últimos 3 errores
                    print(f"  {log}")
            
            return True
        else:
            print(f"❌ Error ejecutando docker-compose logs: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando logs: {e}")
        return False

def test_volume_control():
    """Test 7: Probar control de volumen"""
    print("\n7️⃣ Probando control de volumen...")
    
    try:
        # Obtener volumen actual
        response = requests.get("http://localhost:8080/audio/volume", timeout=5)
        if response.status_code == 200:
            current_volume = response.json()
            print(f"Volumen actual: {current_volume}")
        
        # Cambiar volumen a 50%
        new_volume = {"volume_percent": 50.0}
        response = requests.post(
            "http://localhost:8080/audio/volume",
            json=new_volume,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Volumen cambiado a 50%")
                print(f"   Detalles: {result.get('volume', {})}")
                return True
            else:
                print(f"❌ Error cambiando volumen: {result.get('error', 'Unknown')}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error en test de volumen: {e}")
        return False

def main():
    """Función principal"""
    print_header()
    
    tests = [
        ("Dispositivos de audio", test_devices),
        ("Servidor HTTP", test_http_server),
        ("Beep de prueba", test_beep),
        ("Reproducción de audio", test_audio_playback),
        ("AudioManager directo", test_audio_manager_direct),
        ("Logs del sistema", check_logs),
        ("Control de volumen", test_volume_control)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error ejecutando {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen
    print("\n📊 RESUMEN DE PRUEBAS")
    print("=" * 40)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{len(tests)} pruebas pasaron")
    
    if passed == len(tests):
        print("🎉 ¡Todas las pruebas pasaron! El audio está funcionando correctamente.")
    elif passed > 0:
        print("⚠️  Algunas pruebas fallaron. Revisar logs para más detalles.")
    else:
        print("❌ Todas las pruebas fallaron. Verificar configuración del sistema.")
    
    print("\n💡 Para debugging adicional:")
    print("   - docker-compose logs -f hardware")
    print("   - docker exec -it puertocho-hardware bash")
    print("   - python3 -c 'import sounddevice; sounddevice.query_devices()'")

if __name__ == "__main__":
    main()
