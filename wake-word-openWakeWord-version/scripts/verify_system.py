#!/usr/bin/env python3
"""
Script de verificación del sistema para asistente con openWakeWord
Ejecuta checks completos cuando las dependencias están instaladas
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_system_dependencies():
    """Verificar dependencias del sistema"""
    print("🔍 Verificando dependencias del sistema...")
    
    # Verificar librerías del sistema
    system_libs = [
        'libsndfile1',
        'libasound2-dev', 
        'libspeexdsp-dev'
    ]
    
    for lib in system_libs:
        try:
            result = subprocess.run(['dpkg', '-l', lib], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✅ {lib}")
            else:
                print(f"  ❌ {lib} - no instalado")
        except Exception:
            print(f"  ⚠️  {lib} - no se pudo verificar")

def check_python_dependencies():
    """Verificar dependencias de Python"""
    print("\n🐍 Verificando dependencias de Python...")
    
    dependencies = [
        'openwakeword',
        'sounddevice', 
        'numpy',
        'requests',
        'python-dotenv',
        'webrtcvad'
    ]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep.replace('-', '_'))
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  ❌ {dep}")
            missing.append(dep)
    
    if missing:
        print(f"\n💡 Para instalar dependencias faltantes:")
        print(f"   pip install {' '.join(missing)}")
    
    return len(missing) == 0

def check_audio_devices():
    """Verificar dispositivos de audio"""
    print("\n🎵 Verificando dispositivos de audio...")
    
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        print(f"  📱 {len(devices)} dispositivos encontrados")
        
        # Buscar dispositivos de entrada
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        print(f"  🎤 {len(input_devices)} dispositivos de entrada")
        
        if input_devices:
            default = sd.default.device[0]
            if default is not None:
                print(f"  🔊 Dispositivo por defecto: {devices[default]['name']}")
            else:
                print("  ⚠️  No hay dispositivo de entrada por defecto")
                
            # Test rápido de captura
            try:
                test_data = sd.rec(frames=1024, samplerate=16000, channels=1, dtype='int16')
                sd.wait()
                print("  ✅ Captura de audio funcional")
            except Exception as e:
                print(f"  ❌ Error en captura: {e}")
        else:
            print("  ❌ No hay dispositivos de entrada disponibles")
            
    except ImportError:
        print("  ❌ sounddevice no disponible")
    except Exception as e:
        print(f"  ❌ Error verificando audio: {e}")

def check_gpio_access():
    """Verificar acceso a GPIO (si está en RPi)"""
    print("\n🔌 Verificando acceso a GPIO...")
    
    # Verificar si estamos en Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'raspberry pi' in cpuinfo.lower() or 'bcm' in cpuinfo.lower():
                print("  🍓 Raspberry Pi detectado")
                
                # Verificar acceso a /dev/gpiomem
                if os.path.exists('/dev/gpiomem'):
                    print("  ✅ /dev/gpiomem disponible")
                else:
                    print("  ❌ /dev/gpiomem no disponible")
                
                # Test básico de RPi.GPIO
                try:
                    import RPi.GPIO as GPIO
                    GPIO.setmode(GPIO.BCM)
                    print("  ✅ RPi.GPIO funcional")
                    GPIO.cleanup()
                except Exception as e:
                    print(f"  ❌ Error RPi.GPIO: {e}")
            else:
                print("  ℹ️  No es Raspberry Pi - GPIO no disponible")
    except Exception:
        print("  ⚠️  No se pudo determinar plataforma")

def check_openwakeword_models():
    """Verificar modelos de openWakeWord"""
    print("\n🧠 Verificando modelos de openWakeWord...")
    
    try:
        import openwakeword
        from openwakeword.model import Model
        
        # Intentar descargar modelos
        print("  📥 Descargando modelos preentrenados...")
        openwakeword.utils.download_models()
        print("  ✅ Modelos descargados")
        
        # Crear modelo de prueba
        print("  🔄 Inicializando modelo...")
        model = Model(inference_framework='onnx')
        
        available_models = list(model.models.keys()) if hasattr(model, 'models') else []
        print(f"  🎯 {len(available_models)} modelos disponibles: {', '.join(available_models)}")
        
        # Test básico de predicción
        if available_models:
            import numpy as np
            test_audio = np.zeros(1280, dtype=np.int16)  # 80ms @ 16kHz
            prediction = model.predict(test_audio)
            print(f"  ✅ Predicción test: {max(prediction.values()):.3f}")
        
        return True
        
    except ImportError:
        print("  ❌ openwakeword no disponible")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def check_transcription_service():
    """Verificar servicio de transcripción"""
    print("\n🤖 Verificando servicio de transcripción...")
    
    # Leer URL del .env o usar default
    transcription_url = os.getenv('TRANSCRIPTION_SERVICE_URL', 'http://localhost:5000/transcribe')
    print(f"  🔗 URL: {transcription_url}")
    
    try:
        import requests
        
        # Verificar health endpoint
        health_url = transcription_url.replace('/transcribe', '/health')
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            print("  ✅ Servicio disponible (health check)")
        else:
            print(f"  ⚠️  Health check: HTTP {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("  ❌ Servicio no disponible")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def check_project_files():
    """Verificar archivos del proyecto"""
    print("\n📁 Verificando archivos del proyecto...")
    
    required_files = [
        'main.py',
        'requirements.txt', 
        'commands.json',
        '../docker-compose.yml',
        '../Dockerfile',
        '../PROJECT_TRACKER.md'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file}")

def run_functional_test():
    """Ejecutar test funcional básico"""
    print("\n🧪 Ejecutando test funcional...")
    
    try:
        # Ejecutar test simple
        result = subprocess.run([sys.executable, 'test_simple.py'], 
                              capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0:
            print("  ✅ Tests unitarios pasaron")
            # Contar tests ejecutados
            if 'Ran' in result.stdout:
                for line in result.stdout.split('\n'):
                    if 'Ran' in line and 'tests' in line:
                        print(f"  📊 {line.strip()}")
        else:
            print("  ❌ Tests fallaron")
            print(f"  🔍 Error: {result.stderr[:200]}")
            
    except Exception as e:
        print(f"  ❌ Error ejecutando tests: {e}")

def check_docker_setup():
    """Verificar configuración Docker"""
    print("\n🐳 Verificando configuración Docker...")
    
    try:
        # Verificar Docker
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ {result.stdout.strip()}")
        else:
            print("  ❌ Docker no disponible")
            
        # Verificar docker-compose
        result = subprocess.run(['docker', 'compose', 'version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ Docker Compose disponible")
        else:
            print("  ❌ Docker Compose no disponible")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

def main():
    """Función principal"""
    print("🔧 VERIFICACIÓN COMPLETA DEL SISTEMA")
    print("=" * 50)
    
    # Cambiar al directorio app si no estamos ahí
    if not os.path.exists('main.py'):
        if os.path.exists('app/main.py'):
            os.chdir('app')
        else:
            print("❌ No se encontró main.py")
            return False
    
    # Ejecutar todas las verificaciones
    check_system_dependencies()
    python_deps_ok = check_python_dependencies()
    check_project_files()
    
    if python_deps_ok:
        check_audio_devices()
        check_openwakeword_models()
        check_transcription_service()
        run_functional_test()
    else:
        print("\n⚠️  Saltando tests avanzados - instalar dependencias primero")
    
    check_gpio_access()
    check_docker_setup()
    
    print("\n" + "=" * 50)
    if python_deps_ok:
        print("✅ Verificación completa terminada")
        print("🎉 Sistema listo para ejecutar el asistente")
    else:
        print("⚠️  Verificación parcial - instalar dependencias")
        print("💡 Ejecutar: pip install -r requirements.txt")
    
    return python_deps_ok

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 