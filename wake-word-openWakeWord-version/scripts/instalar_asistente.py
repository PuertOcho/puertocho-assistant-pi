#!/usr/bin/env python3
"""
🎤 INSTALADOR AUTOMÁTICO - Asistente de Voz Puertocho con openWakeWord
Script que automatiza todo el proceso de configuración e instalación
"""

import os
import sys
import subprocess
import time

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🎤 {title}")
    print(f"{'='*60}")

def print_step(step, title):
    print(f"\n{'='*60}")
    print(f"✅ PASO {step}: {title}")
    print(f"{'='*60}")

def run_script(script_name, description):
    """Ejecutar un script Python y mostrar el resultado"""
    print(f"\n🔄 Ejecutando: {description}")
    print(f"📄 Script: {script_name}")
    print("-" * 50)
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=False, 
                              text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} - COMPLETADO")
            return True
        else:
            print(f"❌ {description} - ERROR (código: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando {script_name}: {e}")
        return False

def run_docker_command(description):
    """Ejecutar comando Docker en segundo plano"""
    print(f"\n🔄 {description}")
    print("-" * 50)
    
    # Comandos para ejecutar en background (detached)
    background_commands = [
        ["docker", "compose", "up", "-d", "--build"],
        ["docker-compose", "up", "-d", "--build"]
    ]
    
    # Comandos para mostrar logs
    log_commands = [
        ["docker", "compose", "logs", "-f", "puertocho-assistant"],
        ["docker-compose", "logs", "-f", "puertocho-assistant"]
    ]
    
    # Ejecutar en background
    success = False
    cmd_used = 0
    
    for i, cmd in enumerate(background_commands):
        try:
            print(f"🔄 Ejecutando en segundo plano: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            success = True
            cmd_used = i
            break
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"⚠️ Error con {' '.join(cmd[:2])}: {e}")
            continue
    
    if not success:
        return False
    
    print("✅ Asistente ejecutándose en segundo plano")
    print("🔗 Contenedor: puertocho-assistant")
    print("\n📋 CONTROLES DISPONIBLES:")
    print("   • Ver logs: docker compose logs -f puertocho-assistant")
    print("   • Detener: docker compose stop")
    print("   • Estado: docker compose ps")
    print("   • Reiniciar: docker compose restart")
    print()
    print("🎮 GESTOR DEL ASISTENTE:")
    print("   python3 ejecutar_asistente.py")
    print()
    
    # Preguntar si quiere ver logs
    choice = input("❓ ¿Quieres ver los logs en tiempo real? (S/n): ").lower().strip()
    
    if choice in ['', 's', 'si', 'sí', 'y', 'yes']:
        print("\n📋 MOSTRANDO LOGS EN TIEMPO REAL")
        print("💡 Para salir de los logs: Ctrl+C (el asistente seguirá funcionando)")
        print("="*60)
        
        try:
            subprocess.run(log_commands[cmd_used])
        except KeyboardInterrupt:
            print("\n\n✅ Logs interrumpidos (asistente sigue funcionando)")
            print("💡 Para ver logs nuevamente: docker compose logs -f puertocho-assistant")
        except Exception as e:
            print(f"⚠️ Error mostrando logs: {e}")
            print("💡 Puedes ver los logs manualmente con: docker compose logs -f puertocho-assistant")
    
    return True

def check_requirements():
    """Verificar que los scripts necesarios existan"""
    print_step("0", "VERIFICANDO ARCHIVOS NECESARIOS")
    
    required_files = [
        "verificar_configuracion.py",
        "docker-compose.yml",
        "app/main.py",
        "app/requirements.txt"
    ]
    
    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - NO ENCONTRADO")
            missing.append(file)
    
    if missing:
        print(f"\n❌ FALTAN ARCHIVOS: {', '.join(missing)}")
        print("💡 Asegúrate de estar en el directorio correcto del proyecto")
        return False
    
    print("\n✅ Todos los archivos necesarios están presentes")
    return True

def create_env_file():
    """Crear archivo .env básico si no existe"""
    if not os.path.exists('.env'):
        print("\n🔧 Creando archivo .env básico...")
        
        env_content = """# Configuración del Asistente de Voz Puertocho con openWakeWord
# Servicio de transcripción HTTP
TRANSCRIPTION_SERVICE_URL=http://localhost:5000/transcribe

# Configuración de GPIO
BUTTON_PIN=22
LED_IDLE_PIN=17
LED_RECORD_PIN=27

# Configuración openWakeWord
OPENWAKEWORD_MODEL_PATHS=alexa,hey_mycroft
OPENWAKEWORD_THRESHOLD=0.5
OPENWAKEWORD_VAD_THRESHOLD=0.0
OPENWAKEWORD_ENABLE_SPEEX_NS=false
OPENWAKEWORD_INFERENCE_FRAMEWORK=onnx

# Configuración de audio
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1
AUDIO_CHUNK_SIZE=1280
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ Archivo .env creado con configuración por defecto")
        return True
    else:
        print("✅ Archivo .env ya existe")
        return True

def install_openwakeword():
    """Instalar openWakeWord y dependencias"""
    print_step("1", "INSTALACIÓN DE OPENWAKEWORD")
    
    try:
        print("🔄 Verificando si openWakeWord está instalado...")
        result = subprocess.run([sys.executable, "-c", "import openwakeword; print('openWakeWord ya está instalado')"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ openWakeWord ya está instalado")
            return True
        else:
            print("📦 Instalando openWakeWord...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", "openwakeword"], 
                                  capture_output=False, text=True)
            
            if result.returncode == 0:
                print("✅ openWakeWord instalado correctamente")
                return True
            else:
                print("❌ Error instalando openWakeWord")
                return False
                
    except Exception as e:
        print(f"❌ Error verificando/instalando openWakeWord: {e}")
        return False

def download_models():
    """Descargar modelos preentrenados de openWakeWord"""
    print_step("2", "DESCARGA DE MODELOS PREENTRENADOS")
    
    try:
        print("📥 Descargando modelos preentrenados de openWakeWord...")
        result = subprocess.run([
            sys.executable, "-c", 
            "import openwakeword; openwakeword.utils.download_models(); print('Modelos descargados correctamente')"
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print("✅ Modelos preentrenados descargados")
            return True
        else:
            print("⚠️ Error descargando modelos (pero el asistente puede funcionar)")
            return True  # No es crítico
            
    except Exception as e:
        print(f"⚠️ Error descargando modelos: {e}")
        print("💡 Los modelos se descargarán automáticamente en el primer uso")
        return True  # No es crítico

def main():
    print_header("INSTALADOR AUTOMÁTICO DEL ASISTENTE DE VOZ PUERTOCHO")
    print("🚀 Este script configurará automáticamente tu asistente de voz con openWakeWord")
    print("⏱️  Tiempo estimado: 2-4 minutos")
    print("📋 Pasos a realizar:")
    print("   1️⃣  Instalar openWakeWord")
    print("   2️⃣  Descargar modelos preentrenados")
    print("   3️⃣  Configurar variables de entorno")
    print("   4️⃣  Verificar configuración")
    print("   5️⃣  Ejecutar asistente en Docker")
    
    print("\n💡 VENTAJAS DE OPENWAKEWORD:")
    print("   • No requiere API keys (funciona offline)")
    print("   • Modelos preentrenados: 'alexa', 'hey mycroft', etc.")
    print("   • Entrenamiento de modelos personalizados")
    print("   • Supresión de ruido y VAD integrados")
    
    print("\n" + "="*60)
    input("🔥 Presiona ENTER para comenzar la instalación...")
    
    # Paso 0: Verificar archivos
    if not check_requirements():
        sys.exit(1)
    
    # Paso 1: Instalar openWakeWord
    if not install_openwakeword():
        print("❌ No se pudo instalar openWakeWord")
        print("💡 Intenta manualmente: pip install openwakeword")
        sys.exit(1)
    
    # Paso 2: Descargar modelos
    download_models()
    
    # Paso 3: Configurar variables de entorno
    print_step("3", "CONFIGURACIÓN DE VARIABLES DE ENTORNO")
    if not create_env_file():
        print("❌ No se pudo crear el archivo .env")
        sys.exit(1)
    
    print("\n💡 CONFIGURACIÓN ACTUAL:")
    print("   🎯 Modelos: alexa, hey_mycroft (puedes cambiarlos en .env)")
    print("   🎚️ Umbral: 0.5 (ajústalo según tu entorno)")
    print("   🔊 VAD: Deshabilitado (habilítalo si hay mucho ruido)")
    print("   🤖 Transcripción: http://localhost:5000/transcribe")
    
    # Paso 4: Verificar configuración
    print_step("4", "VERIFICACIÓN DE CONFIGURACIÓN")
    print("🔍 Verificando que todo esté configurado correctamente...")
    
    verification_ok = run_script("verificar_configuracion.py", "Verificación de configuración")
    
    if not verification_ok:
        print("\n⚠️ ADVERTENCIA: Hay problemas en la configuración")
        print("💡 Puedes continuar, pero el asistente podría no funcionar correctamente")
        
        choice = input("\n❓ ¿Continuar de todas formas? (s/N): ").lower().strip()
        if choice not in ['s', 'si', 'sí', 'y', 'yes']:
            print("🛑 Instalación cancelada")
            print("🔧 Revisa los problemas y ejecuta el script nuevamente")
            sys.exit(1)
    
    # Paso 5: Ejecutar Docker
    print_step("5", "EJECUTANDO ASISTENTE EN DOCKER")
    print("🐳 Construyendo y ejecutando el contenedor Docker en segundo plano...")
    print("⏳ Esto puede tomar unos minutos la primera vez...")
    print("\n🎯 WAKE WORDS DISPONIBLES:")
    print("   • 'Alexa' (modelo alexa)")
    print("   • 'Hey Mycroft' (modelo hey_mycroft)")
    print("   • O entrena tu propio modelo 'Puertocho'")
    
    print("\n💡 VENTAJAS DEL MODO SEGUNDO PLANO:")
    print("   • El asistente sigue funcionando aunque cierres la terminal")
    print("   • Puedes ver logs cuando quieras")
    print("   • Control total desde la misma consola")
    print("   • Fácil detener/reiniciar sin interrumpir otras tareas")
    
    print("\n" + "="*60)
    input("🚀 Presiona ENTER para ejecutar el asistente...")
    
    # Limpiar pantalla para mejor visualización
    os.system('clear' if os.name == 'posix' else 'cls')
    
    print_header("🎤 INICIANDO ASISTENTE DE VOZ PUERTOCHO")
    print("🎯 Wake words: 'Alexa' y 'Hey Mycroft'")
    print("🔴 LED Rojo (GPIO 27): Escuchando")
    print("🟢 LED Verde (GPIO 17): Listo")
    print("🔘 Botón (GPIO 22): Activación manual")
    print("🤖 Transcripción: Servicio HTTP Local")
    print("\n💡 Para detener el asistente: Ctrl+C")
    print("="*60)
    
    success = run_docker_command("Ejecutando contenedor Docker")
    
    if success:
        print("\n🎉 ¡ASISTENTE EJECUTÁNDOSE EN SEGUNDO PLANO!")
        print("🔗 El asistente está funcionando correctamente")
        print()
        print("📋 COMANDOS ÚTILES:")
        print("   python3 ejecutar_asistente.py         # Gestor completo")
        print("   docker compose logs -f                # Ver logs")
        print("   docker compose stop                   # Detener")
        print("   docker compose restart                # Reiniciar")
        print()
        print("🎯 ¡Tu asistente con openWakeWord está listo!")
        print("💡 Puedes entrenar modelos personalizados siguiendo la documentación")
    else:
        print("\n❌ Error ejecutando el contenedor Docker")
        print("🔧 Comandos para intentar manualmente:")
        print("   docker compose up -d --build")
        print("   # o")
        print("   docker-compose up -d --build")
        sys.exit(1)

def show_usage():
    """Mostrar ayuda de uso"""
    print("🎤 Instalador Automático - Asistente de Voz Puertocho con openWakeWord")
    print("=" * 70)
    print("USO:")
    print("  python3 instalar_asistente.py")
    print()
    print("DESCRIPCIÓN:")
    print("  Automatiza todo el proceso de instalación:")
    print("  1. Instalar openWakeWord")
    print("  2. Descargar modelos preentrenados") 
    print("  3. Configurar variables de entorno")
    print("  4. Verificar configuración")
    print("  5. Ejecutar asistente en Docker")
    print()
    print("REQUISITOS:")
    print("  • Docker instalado")
    print("  • Conexión a internet (para descargar modelos)")
    print("  • Servicio de transcripción en http://localhost:5000/transcribe")
    print("  • Hardware conectado (LEDs, botón, micrófono)")
    print()
    print("VENTAJAS DE OPENWAKEWORD:")
    print("  • Sin API keys necesarias")
    print("  • Modelos preentrenados disponibles")
    print("  • Entrenamiento de modelos personalizados")
    print("  • Funciona completamente offline")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        show_usage()
    else:
        try:
            main()
        except KeyboardInterrupt:
            print("\n\n🛑 Instalación interrumpida por el usuario")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Error inesperado: {e}")
            sys.exit(1) 