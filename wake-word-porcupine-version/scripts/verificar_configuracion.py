#!/usr/bin/env python3
"""
Script de verificación de configuración para el Asistente Puertocho
Ejecutar antes de lanzar el contenedor Docker
"""

import os
import json
import requests
import re
import subprocess
import sys
from pathlib import Path

# Obtener la ruta del proyecto (directorio padre del script)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Cargar variables de entorno desde .env si existe
try:
    from dotenv import load_dotenv
    env_file = PROJECT_ROOT / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Variables cargadas desde {env_file}")
    else:
        print(f"ℹ️  No se encontró archivo .env en {env_file}")
except ImportError:
    print("ℹ️  python-dotenv no instalado")

def print_header(title):
    print(f"\n{'='*50}")
    print(f"🔍 {title}")
    print(f"{'='*50}")

def print_check(description, status, details=""):
    """Imprimir resultado de verificación con formato"""
    emoji = "✅" if status else "❌"
    print(f"{emoji} {description}")
    if details:
        print(f"   {details}")

def parse_docker_compose_simple(file_path):
    """Parser simple para docker-compose.yml sin dependencias externas"""
    config = {
        "services": {
            "puertocho-assistant": {
                "environment": [],
                "devices": []
            }
        }
    }
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        in_environment = False
        in_devices = False
        
        for line in lines:
            line = line.strip()
            
            # Detectar secciones
            if line == "environment:":
                in_environment = True
                in_devices = False
                continue
            elif line == "devices:":
                in_devices = True
                in_environment = False
                continue
            elif line and not line.startswith("-") and not line.startswith("#"):
                if ":" in line and not line.startswith(" "):
                    in_environment = False
                    in_devices = False
            
            # Procesar variables de entorno
            if in_environment and line.startswith("- "):
                env_var = line[2:].strip().strip('"')
                config["services"]["puertocho-assistant"]["environment"].append(env_var)
            
            # Procesar devices
            elif in_devices and line.startswith("- "):
                device = line[2:].strip().strip('"')
                config["services"]["puertocho-assistant"]["devices"].append(device)
        
        return config
        
    except Exception as e:
        print(f"Error leyendo docker-compose.yml: {e}")
        return None

def check_files():
    """Verificar que todos los archivos necesarios existan"""
    print_header("VERIFICACIÓN DE ARCHIVOS")
    
    required_files = {
        "docker-compose.yml": "Configuración Docker",
        "Dockerfile": "Imagen Docker", 
        "app/main.py": "Código principal",
        "app/commands.json": "Comandos disponibles",
        "app/requirements.txt": "Dependencias Python",
        "app/Puerto-ocho_es_raspberry-pi_v3_0_0.ppn": "Modelo wake word"
    }
    
    all_files_ok = True
    for file_path, description in required_files.items():
        exists = os.path.exists(file_path)
        print_check(f"{description}: {file_path}", exists)
        if not exists:
            all_files_ok = False
    
    return all_files_ok



def check_commands():
    """Verificar archivo de comandos"""
    print_header("VERIFICACIÓN DE COMANDOS")
    
    try:
        with open("app/commands.json", "r") as f:
            commands = json.load(f)
        
        print_check("Archivo commands.json válido", True, f"{len(commands)} comandos encontrados")
        
        # Mostrar comandos
        for cmd, config in commands.items():
            pin = config.get("pin", "?")
            state = config.get("state", "?")
            print(f"   • '{cmd}' → GPIO {pin} = {state}")
        
        return True
        
    except Exception as e:
        print_check("Error en commands.json", False, str(e))
        return False

def check_docker():
    """Verificar que Docker esté disponible"""
    print_header("VERIFICACIÓN DE DOCKER")
    
    try:
        result = subprocess.run(["docker", "--version"], 
                              capture_output=True, text=True, timeout=5)
        docker_available = result.returncode == 0
        print_check("Docker disponible", docker_available, result.stdout.strip())
        
        if docker_available:
            # Probar primero docker compose (nueva sintaxis)
            result = subprocess.run(["docker", "compose", "version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print_check("Docker Compose disponible (nueva sintaxis)", True, result.stdout.strip())
                return True
            
            # Si falla, probar docker-compose (sintaxis antigua)
            result = subprocess.run(["docker-compose", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            compose_available = result.returncode == 0
            print_check("Docker Compose disponible (sintaxis antigua)", compose_available, 
                       result.stdout.strip() if compose_available else "Usa 'docker compose' en su lugar")
            return compose_available
        
        return False
        
    except Exception as e:
        print_check("Error verificando Docker", False, str(e))
        return False

def check_environment_variables():
    """Verificar variables de entorno desde .env o sistema"""
    print_header("VERIFICACIÓN DE VARIABLES DE ENTORNO")
    
    # Variables requeridas
    required_vars = {
        "PORCUPINE_ACCESS_KEY": "Porcupine ACCESS_KEY para wake word",
        "TRANSCRIPTION_SERVICE_URL": "URL del servicio de transcripción"
    }
    
    # Variables opcionales con valores por defecto
    optional_vars = {
        "BUTTON_PIN": "22",
        "LED_IDLE_PIN": "17", 
        "LED_RECORD_PIN": "27"
    }
    
    all_ok = True
    
    # Verificar variables requeridas
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        has_value = value and value != "TU_ACCESS_KEY_AQUI"
        
        if var_name == "PORCUPINE_ACCESS_KEY":
            print_check(f"{description}", has_value, 
                       f"Valor: {value[:20]}..." if has_value else "Necesitas configurar esta variable")
        else:
            print_check(f"{description}", has_value, 
                       f"Valor: {value}" if has_value else "Necesitas configurar esta variable")
        
        if not has_value:
            all_ok = False
    
    # Verificar variables opcionales
    for var_name, default_value in optional_vars.items():
        value = os.getenv(var_name, default_value)
        print_check(f"GPIO {var_name}", True, f"Valor: {value}")
    
    return all_ok

def check_transcription_service():
    """Verificar conectividad con el servicio de transcripción"""
    print_header("VERIFICACIÓN DEL SERVICIO DE TRANSCRIPCIÓN")
    
    transcription_url = os.getenv('TRANSCRIPTION_SERVICE_URL', 'http://localhost:5000/transcribe')
    
    try:
        # Intentar health check primero
        try:
            health_url = transcription_url.replace('/transcribe', '/health')
            response = requests.get(health_url, timeout=5)
            print_check("Servicio disponible (health check)", True, f"Respuesta: {response.status_code}")
            return True
        except:
            pass
        
        # Si no hay health check, crear petición de prueba
        print("🔄 Verificando servicio con petición de prueba...")
        
        # Crear archivo de audio de prueba mínimo
        import wave
        import io
        
        test_audio = b'\x00' * 1000  # Audio silencioso
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(test_audio)
        
        files = {'audio': ('test.wav', buffer.getvalue(), 'audio/wav')}
        response = requests.post(transcription_url, files=files, timeout=10)
        
        if response.status_code == 200:
            try:
                result = response.json()
                if 'transcription' in result:
                    print_check("Servicio de transcripción funcionando", True, f"URL: {transcription_url}")
                    return True
                else:
                    print_check("Servicio responde pero formato incorrecto", False, 
                              "Respuesta debe tener formato: {'transcription': 'texto'}")
                    return False
            except:
                print_check("Servicio responde pero no es JSON válido", False)
                return False
        else:
            print_check("Error en servicio de transcripción", False, f"Status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_check("No se puede conectar al servicio", False, f"URL: {transcription_url}")
        print("💡 Asegúrate de que el servicio esté ejecutándose")
        return False
    except requests.exceptions.Timeout:
        print_check("Timeout conectando al servicio", False, f"URL: {transcription_url}")
        return False
    except Exception as e:
        print_check("Error verificando servicio", False, str(e))
        return False

def main():
    """Función principal de verificación"""
    print("🎤 Verificador de Configuración - Asistente Puertocho")
    print("=" * 60)
    
    checks = [
        ("Archivos", check_files()),
        ("Docker", check_docker()),
        ("Variables de Entorno", check_environment_variables()),
        ("Comandos", check_commands()),
        ("Servicio de Transcripción", check_transcription_service())
    ]
    
    print_header("RESUMEN FINAL")
    
    all_ok = True
    for name, status in checks:
        print_check(f"{name}", status)
        if not status:
            all_ok = False
    
    print(f"\n{'='*50}")
    if all_ok:
        print("🎉 ¡Configuración CORRECTA! Puedes ejecutar:")
        print("   docker compose up --build")
    else:
        print("⚠️  Hay problemas en la configuración.")
        print()
        print("🔧 Para solucionarlo:")
        print("   python3 configurar_access_key.py  # Configurar variables")
        print("   # Asegúrate de que el servicio de transcripción esté ejecutándose")
        print("   # curl -X POST http://localhost:5000/transcribe -F 'audio=@test.wav'")
    print(f"{'='*50}")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main()) 