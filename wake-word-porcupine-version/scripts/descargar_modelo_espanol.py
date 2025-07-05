#!/usr/bin/env python3
"""
Script para descargar el modelo base en español de Porcupine
Ejecutar antes de iniciar el contenedor Docker
"""

import requests
import os

def download_spanish_model():
    """Descargar modelo base en español para Porcupine"""
    spanish_model_path = "app/porcupine_params_es.pv"
    
    if os.path.exists(spanish_model_path):
        print(f"✅ Modelo en español ya existe: {spanish_model_path}")
        return True
        
    try:
        print("📥 Descargando modelo base en español para Porcupine...")
        
        # URLs posibles para el modelo en español
        urls = [
            "https://github.com/Picovoice/porcupine/raw/master/lib/common/porcupine_params_es.pv",
            "https://github.com/Picovoice/porcupine/raw/main/lib/common/porcupine_params_es.pv",
            "https://raw.githubusercontent.com/Picovoice/porcupine/master/lib/common/porcupine_params_es.pv"
        ]
        
        for i, url in enumerate(urls, 1):
            try:
                print(f"🔄 Intentando URL {i}/{len(urls)}: {url}")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # Crear directorio si no existe
                os.makedirs("app", exist_ok=True)
                
                with open(spanish_model_path, 'wb') as f:
                    f.write(response.content)
                
                file_size = len(response.content)
                print(f"✅ Modelo en español descargado exitosamente!")
                print(f"   📁 Archivo: {spanish_model_path}")
                print(f"   📏 Tamaño: {file_size:,} bytes")
                return True
                
            except Exception as e:
                print(f"⚠️ Error con URL {i}: {e}")
                continue
        
        print("❌ No se pudo descargar el modelo en español desde ninguna URL")
        print("💡 El asistente usará keywords genéricos como fallback")
        return False
        
    except Exception as e:
        print(f"❌ Error general descargando modelo: {e}")
        return False

def main():
    print("🌍 Descargador de Modelo en Español - Porcupine")
    print("=" * 50)
    
    success = download_spanish_model()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ¡Listo! El modelo en español está disponible.")
        print("🚀 Ahora puedes ejecutar:")
        print("   docker compose up --build")
        print("\n💡 Tu asistente usará:")
        print("   🎯 Wake words: 'Hola Puertocho' u 'Oye Puertocho'")
    else:
        print("⚠️ No se descargó el modelo, pero el asistente funcionará.")
        print("🚀 Puedes ejecutar de todas formas:")
        print("   docker compose up --build")
        print("\n💡 Tu asistente usará:")
        print("   🎯 Wake words: 'Hey Google' o 'Alexa' (fallback)")
    print("=" * 50)

if __name__ == "__main__":
    main() 