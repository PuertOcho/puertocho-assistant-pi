#!/usr/bin/env python3
"""
🎤 INSTALADOR AUTOMÁTICO - Asistente de Voz Puertocho
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
        "configurar_access_key.py",
        "descargar_modelo_espanol.py", 
        "verificar_configuracion.py",
        "docker-compose.yml"
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

def check_existing_configuration():
    """Verificar si ya existe configuración válida"""
    env_path = ".env"
    
    if not os.path.exists(env_path):
        return False
    
    try:
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Buscar PORCUPINE_ACCESS_KEY
        porcupine_key = None
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('PORCUPINE_ACCESS_KEY=') and not line.startswith('#'):
                porcupine_key = line.split('=', 1)[1].strip()
                break
        
        # Verificar si es una clave válida
        if porcupine_key and porcupine_key != "TU_ACCESS_KEY_AQUI" and len(porcupine_key) > 20:
            return True
            
    except Exception as e:
        print(f"⚠️ Error verificando configuración: {e}")
    
    return False

def main():
    print_header("INSTALADOR AUTOMÁTICO DEL ASISTENTE DE VOZ PUERTOCHO")
    print("🚀 Este script configurará automáticamente tu asistente de voz")
    print("⏱️  Tiempo estimado: 3-5 minutos")
    print("📋 Pasos a realizar:")
    print("   1️⃣  Configurar API Keys (Porcupine)")
    print("   2️⃣  Descargar modelo en español")
    print("   3️⃣  Verificar configuración")
    print("   4️⃣  Ejecutar asistente en Docker")
    
    print("\n" + "="*60)
    input("🔥 Presiona ENTER para comenzar la instalación...")
    
    # Paso 0: Verificar archivos
    if not check_requirements():
        sys.exit(1)
    
    # Verificar configuración existente
    has_config = check_existing_configuration()
    
    # Paso 1: Configurar API Keys
    print_step("1", "CONFIGURACIÓN DE API KEYS")
    
    if has_config:
        print("✅ Ya tienes configuración en .env")
        choice = input("❓ ¿Quieres reconfigurar las API Keys? (s/N): ").lower().strip()
        
        if choice not in ['s', 'si', 'sí', 'y', 'yes']:
            print("🔄 Saltando configuración de API Keys (usando configuración existente)")
        else:
            print("💡 Necesitarás:")
            print("   🎯 Porcupine ACCESS_KEY: https://console.picovoice.ai/")
            print("   🤖 Servicio de transcripción ejecutándose en http://localhost:5000/transcribe")
            print("\n⚠️  Ten las API Keys listas antes de continuar")
            
            input("\n🔑 Presiona ENTER cuando tengas las API Keys listas...")
            
            if not run_script("configurar_access_key.py", "Configuración de API Keys"):
                print("❌ No se pudieron configurar las API Keys")
                print("💡 Ejecuta manualmente: python3 configurar_access_key.py")
                sys.exit(1)
    else:
        print("💡 Necesitarás:")
        print("   🎯 Porcupine ACCESS_KEY: https://console.picovoice.ai/")
        print("   🤖 Servicio de transcripción ejecutándose en http://localhost:5000/transcribe")
        print("\n⚠️  Ten las API Keys listas antes de continuar")
        
        input("\n🔑 Presiona ENTER cuando tengas las API Keys listas...")
        
        if not run_script("configurar_access_key.py", "Configuración de API Keys"):
            print("❌ No se pudieron configurar las API Keys")
            print("💡 Ejecuta manualmente: python3 configurar_access_key.py")
            sys.exit(1)
    
    # Paso 2: Descargar modelo español
    print_step("2", "DESCARGA DE MODELO EN ESPAÑOL")
    print("🌍 Descargando modelo base en español para Porcupine...")
    
    if not run_script("descargar_modelo_espanol.py", "Descarga del modelo en español"):
        print("⚠️ No se pudo descargar el modelo en español")
        print("💡 El asistente funcionará con keywords genéricos")
    
    # Paso 3: Verificar configuración
    print_step("3", "VERIFICACIÓN DE CONFIGURACIÓN")
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
    
    # Paso 4: Ejecutar Docker
    print_step("4", "EJECUTANDO ASISTENTE EN DOCKER")
    print("🐳 Construyendo y ejecutando el contenedor Docker en segundo plano...")
    print("⏳ Esto puede tomar unos minutos la primera vez...")
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
    print("🎯 Wake words: 'Hola Puertocho' u 'Oye Puertocho'")
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
        print("🎯 ¡Tu asistente 'Hola Puertocho' está listo para usar!")
    else:
        print("\n❌ Error ejecutando el contenedor Docker")
        print("🔧 Comandos para intentar manualmente:")
        print("   docker compose up -d --build")
        print("   # o")
        print("   docker-compose up -d --build")
        sys.exit(1)

def show_usage():
    """Mostrar ayuda de uso"""
    print("🎤 Instalador Automático - Asistente de Voz Puertocho")
    print("=" * 60)
    print("USO:")
    print("  python3 instalar_asistente.py")
    print()
    print("DESCRIPCIÓN:")
    print("  Automatiza todo el proceso de instalación:")
    print("  1. Configurar API Keys (Porcupine)")
    print("  2. Descargar modelo en español") 
    print("  3. Verificar configuración")
    print("  4. Ejecutar asistente en Docker")
    print()
    print("REQUISITOS:")
    print("  • Docker instalado")
    print("  • Porcupine ACCESS_KEY")
    print("  • Servicio de transcripción en http://localhost:5000/transcribe")
    print("  • Hardware conectado (LEDs, botón, micrófono)")

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