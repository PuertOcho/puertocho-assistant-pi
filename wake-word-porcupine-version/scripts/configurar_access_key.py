#!/usr/bin/env python3
"""
Script para configurar Porcupine ACCESS_KEY automáticamente
"""

import os
import re
from pathlib import Path

# Obtener la ruta del proyecto (directorio padre del script)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

def load_existing_env():
    """Cargar configuración existente desde .env si existe"""
    env_vars = {}
    env_path = PROJECT_ROOT / ".env"
    
    if env_path.exists():
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        except Exception as e:
            print(f"⚠️ Error leyendo .env existente: {e}")
    
    return env_vars, env_path

def main():
    print("🔑 Configurador de API Keys - Porcupine")
    print("=" * 40)
    print()
    
    # Verificar configuración existente
    existing_vars, env_path = load_existing_env()
    existing_key = existing_vars.get('PORCUPINE_ACCESS_KEY', '')
    
    # Si ya existe una clave válida, preguntar si quiere mantenerla
    if existing_key and existing_key != "TU_ACCESS_KEY_AQUI" and len(existing_key) > 20:
        print("✅ Ya tienes configuración en .env")
        print(f"🔍 Porcupine ACCESS_KEY actual: {existing_key[:20]}...")
        print()
        
        choice = input("❓ ¿Quieres mantener la configuración actual? (S/n): ").lower().strip()
        
        if choice in ['', 's', 'si', 'sí', 'y', 'yes']:
            print("\n✅ Configuración mantenida")
            print("🎯 Porcupine Access Key: " + existing_key[:20] + "...")
            print()
            print("🚀 Configuración lista para usar:")
            print("   python3 verificar_configuracion.py  # Para verificar todo")
            print("   docker compose up --build           # Para ejecutar el asistente")
            print()
            print("💡 IMPORTANTE: Asegúrate de que el servicio de transcripción esté ejecutándose:")
            print("   curl -X POST http://localhost:5000/transcribe -F 'audio=@test.wav'")
            return
        else:
            print("\n🔄 Procediendo a reconfigurar...")
    
    print("🎯 CONFIGURACIÓN DE PORCUPINE ACCESS KEY")
    print("-" * 45)
    print("📋 Pasos para obtener tu Porcupine ACCESS_KEY:")
    print("1. Ve a: https://console.picovoice.ai/")
    print("2. Inicia sesión o crea una cuenta gratuita")
    print("3. En el dashboard, encontrarás tu AccessKey")
    print("4. Copia el AccessKey completo")
    print()
    
    # Solicitar Porcupine ACCESS_KEY
    while True:
        porcupine_key = input("🎯 Pega tu PORCUPINE_ACCESS_KEY aquí: ").strip()
        
        if not porcupine_key:
            print("❌ PORCUPINE_ACCESS_KEY no puede estar vacío")
            continue
        
        if porcupine_key == "TU_ACCESS_KEY_AQUI":
            print("❌ Debes usar tu ACCESS_KEY real, no el placeholder")
            continue
        
        # Validar formato básico (longitud típica de Porcupine)
        if len(porcupine_key) < 20:
            print("❌ ACCESS_KEY parece muy corto. Verifica que sea correcto.")
            continue
        
        break
    
    # Crear contenido del archivo .env
    try:
        # Preservar otras variables si existen
        env_content_lines = []
        
        # Si hay archivo existente, preservar variables que no vamos a cambiar
        if existing_vars:
            for key, value in existing_vars.items():
                if key != 'PORCUPINE_ACCESS_KEY':  # Esta la vamos a actualizar
                    env_content_lines.append(f"{key}={value}")
        
        # Agregar configuración nueva/actualizada
        env_content = f"""# Configuración del Asistente de Voz Puertocho
# {"Actualizado" if existing_vars else "Generado"} automáticamente por configurar_access_key.py

# REQUERIDO: Porcupine ACCESS_KEY para detección de wake word
PORCUPINE_ACCESS_KEY={porcupine_key}

# Servicio de transcripción HTTP
TRANSCRIPTION_SERVICE_URL={existing_vars.get('TRANSCRIPTION_SERVICE_URL', 'http://localhost:5000/transcribe')}

# Configuración de GPIO
BUTTON_PIN={existing_vars.get('BUTTON_PIN', '22')}
LED_IDLE_PIN={existing_vars.get('LED_IDLE_PIN', '17')}
LED_RECORD_PIN={existing_vars.get('LED_RECORD_PIN', '27')}
"""
        
        with open(env_path, "w") as f:
            f.write(env_content)
        
        print("\n" + "=" * 50)
        print(f"✅ Configuración {'actualizada' if existing_vars else 'guardada'} en {env_path}")
        print("🎯 Porcupine Access Key: " + porcupine_key[:20] + "...")
        print()
        print("🚀 Ahora puedes ejecutar:")
        print("   python3 verificar_configuracion.py  # Para verificar todo")
        print("   docker compose up --build           # Para ejecutar el asistente")
        print()
        print("💡 IMPORTANTE: Asegúrate de que el servicio de transcripción esté ejecutándose:")
        print("   curl -X POST http://localhost:5000/transcribe -F 'audio=@test.wav'")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error creando archivo .env: {e}")

if __name__ == "__main__":
    main() 