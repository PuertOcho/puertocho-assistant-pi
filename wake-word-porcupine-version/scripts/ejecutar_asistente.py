#!/usr/bin/env python3
"""
🎤 EJECUTOR RÁPIDO - Asistente de Voz Puertocho
Script simple para ejecutar el asistente cuando ya está configurado
"""

import os
import sys
import subprocess

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🎤 {title}")
    print(f"{'='*60}")

def show_status():
    """Mostrar estado del asistente"""
    print_header("ESTADO DEL ASISTENTE")
    
    try:
        # Verificar si el contenedor está corriendo
        result = subprocess.run(["docker", "ps", "-q", "-f", "name=puertocho-assistant"], 
                              capture_output=True, text=True)
        
        if result.stdout.strip():
            print("✅ ESTADO: EJECUTÁNDOSE")
            print("🔗 Contenedor: puertocho-assistant")
            print("\n📋 COMANDOS ÚTILES:")
            print("   • Ver logs: docker compose logs -f puertocho-assistant")
            print("   • Detener: docker compose stop")
            print("   • Reiniciar: docker compose restart")
        else:
            print("⭕ ESTADO: DETENIDO")
            print("💡 Ejecuta este script para iniciarlo")
            
    except Exception as e:
        print(f"❓ No se pudo verificar el estado: {e}")

def run_foreground():
    """Ejecutar en primer plano (con logs visibles)"""
    print_header("🚀 EJECUTANDO ASISTENTE (PRIMER PLANO)")
    print("🎯 Wake words: 'Hola Puertocho' u 'Oye Puertocho'")
    print("🔴 LED Rojo (GPIO 27): Escuchando")
    print("🟢 LED Verde (GPIO 17): Listo")
    print("🔘 Botón (GPIO 22): Activación manual")
    print("🤖 Transcripción: Servicio HTTP Local")
    print("\n💡 Para detener: Ctrl+C")
    print("="*60)
    
    try:
        # Intentar con docker compose
        subprocess.run(["docker", "compose", "up", "--build"])
    except Exception as e:
        print(f"⚠️ Error con 'docker compose': {e}")
        try:
            # Fallback a docker-compose
            subprocess.run(["docker-compose", "up", "--build"])
        except Exception as e:
            print(f"❌ Error con 'docker-compose': {e}")
            return False
    return True

def run_background():
    """Ejecutar en segundo plano (background)"""
    print_header("🚀 EJECUTANDO ASISTENTE (SEGUNDO PLANO)")
    
    try:
        # Intentar con docker compose
        result = subprocess.run(["docker", "compose", "up", "-d", "--build"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Asistente ejecutándose en segundo plano")
            print("🔗 Contenedor: puertocho-assistant")
            print("\n📋 COMANDOS ÚTILES:")
            print("   • Ver logs: docker compose logs -f puertocho-assistant")
            print("   • Detener: docker compose stop")
            print("   • Estado: docker compose ps")
            return True
        else:
            raise Exception(f"Error código: {result.returncode}")
            
    except Exception as e:
        print(f"⚠️ Error con 'docker compose': {e}")
        try:
            # Fallback a docker-compose
            result = subprocess.run(["docker-compose", "up", "-d", "--build"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Asistente ejecutándose en segundo plano")
                return True
            else:
                raise Exception(f"Error código: {result.returncode}")
                
        except Exception as e:
            print(f"❌ Error con 'docker-compose': {e}")
            return False

def stop_assistant():
    """Detener el asistente"""
    print_header("🛑 DETENIENDO ASISTENTE")
    
    try:
        # Intentar con docker compose
        result = subprocess.run(["docker", "compose", "stop"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Asistente detenido correctamente")
            return True
        else:
            raise Exception(f"Error código: {result.returncode}")
            
    except Exception as e:
        print(f"⚠️ Error con 'docker compose': {e}")
        try:
            # Fallback a docker-compose
            result = subprocess.run(["docker-compose", "stop"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Asistente detenido correctamente")
                return True
            else:
                raise Exception(f"Error código: {result.returncode}")
                
        except Exception as e:
            print(f"❌ Error con 'docker-compose': {e}")
            return False

def show_logs():
    """Mostrar logs del asistente"""
    print_header("📋 LOGS DEL ASISTENTE")
    print("💡 Para salir de los logs: Ctrl+C")
    print("="*60)
    
    try:
        # Intentar con docker compose
        subprocess.run(["docker", "compose", "logs", "-f", "puertocho-assistant"])
    except Exception as e:
        print(f"⚠️ Error con 'docker compose': {e}")
        try:
            # Fallback a docker-compose
            subprocess.run(["docker-compose", "logs", "-f", "puertocho-assistant"])
        except Exception as e:
            print(f"❌ Error con 'docker-compose': {e}")

def show_logs_alternative():
    """Mostrar logs alternativos si el comando estándar no funciona"""
    print_header("📋 LOGS ALTERNATIVOS DEL ASISTENTE")
    print("💡 Intentando métodos alternativos para ver logs...")
    print("="*60)
    
    try:
        # Método 1: Docker logs directo
        print("🔍 Intentando 'docker logs'...")
        result = subprocess.run(["docker", "logs", "-f", "puertocho-assistant"], 
                              capture_output=False, text=True)
    except Exception as e:
        print(f"⚠️ Error con 'docker logs': {e}")
        
        try:
            # Método 2: Verificar si el contenedor existe
            print("🔍 Verificando contenedores...")
            result = subprocess.run(["docker", "ps", "-a", "--filter", "name=puertocho"], 
                                  capture_output=True, text=True)
            print(f"Contenedores encontrados:\n{result.stdout}")
            
            if result.stdout.strip():
                print("🔍 Intentando obtener logs de cualquier contenedor relacionado...")
                subprocess.run(["docker", "logs", "-f", "--tail", "50"] + 
                             [line.split()[0] for line in result.stdout.strip().split('\n')[1:] 
                              if 'puertocho' in line][:1])
            else:
                print("❌ No se encontraron contenedores relacionados con 'puertocho'")
                
        except Exception as e2:
            print(f"❌ Error verificando contenedores: {e2}")

def restart_assistant():
    """Reiniciar el asistente"""
    print_header("🔄 REINICIANDO ASISTENTE")
    
    try:
        # Parar primero
        print("🛑 Deteniendo asistente...")
        subprocess.run(["docker", "compose", "stop"], capture_output=True)
        
        # Reiniciar
        print("🚀 Iniciando asistente...")
        result = subprocess.run(["docker", "compose", "up", "-d", "--build"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Asistente reiniciado correctamente")
            return True
        else:
            print(f"❌ Error reiniciando: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error reiniciando asistente: {e}")
        return False

def show_menu():
    """Mostrar menú de opciones"""
    print_header("ASISTENTE DE VOZ PUERTOCHO - MENÚ PRINCIPAL")
    print("🎤 Selecciona una opción:")
    print()
    print("1️⃣  Ejecutar asistente (primer plano)")
    print("2️⃣  Ejecutar asistente (segundo plano)")
    print("3️⃣  Ver estado del asistente")
    print("4️⃣  Ver logs en tiempo real")
    print("5️⃣  Ver logs (método alternativo)")
    print("6️⃣  Reiniciar asistente")
    print("7️⃣  Detener asistente")
    print("8️⃣  Diagnóstico completo")
    print("9️⃣  Ayuda")
    print("0️⃣  Salir")
    print()

def show_help():
    """Mostrar ayuda"""
    print_header("AYUDA - ASISTENTE DE VOZ PUERTOCHO")
    print("📋 USO DEL SCRIPT:")
    print("   python3 ejecutar_asistente.py [opción]")
    print()
    print("🎯 OPCIONES:")
    print("   run       - Ejecutar en primer plano")
    print("   start     - Ejecutar en segundo plano") 
    print("   stop      - Detener asistente")
    print("   status    - Ver estado")
    print("   logs      - Ver logs en tiempo real")
    print("   logs-alt  - Ver logs (método alternativo)")
    print("   restart   - Reiniciar asistente")
    print("   diagnose  - Diagnóstico completo del sistema")
    print("   --help    - Mostrar esta ayuda")
    print()
    print("🎤 WAKE WORDS:")
    print("   • 'Hola Puertocho' u 'Oye Puertocho' (modelo español)")
    print("   • 'Hey Google' o 'Alexa' (fallback)")
    print()
    print("🔧 COMANDOS DE VOZ:")
    print("   • 'enciende luz verde'")
    print("   • 'apaga luz verde'")
    print("   • 'enciende luz rojo'")
    print("   • 'apaga luz rojo'")
    print()
    print("💡 TIPS:")
    print("   • LED Verde: Listo para escuchar")
    print("   • LED Rojo: Grabando comando")
    print("   • Botón GPIO 22: Activación manual")

def diagnose_system():
    """Diagnóstico completo del sistema"""
    print_header("🔍 DIAGNÓSTICO COMPLETO DEL ASISTENTE")
    
    print("1️⃣ VERIFICANDO DOCKER...")
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker: {result.stdout.strip()}")
        else:
            print("❌ Docker no está instalado o no funciona")
            return
    except:
        print("❌ Docker no está instalado")
        return
    
    print("\n2️⃣ VERIFICANDO DOCKER COMPOSE...")
    try:
        result = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker Compose: {result.stdout.strip()}")
        else:
            # Intentar con docker-compose
            result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Docker Compose (legacy): {result.stdout.strip()}")
            else:
                print("❌ Docker Compose no está disponible")
                return
    except:
        print("❌ Docker Compose no está disponible")
        return
    
    print("\n3️⃣ VERIFICANDO CONTENEDORES...")
    try:
        result = subprocess.run(["docker", "ps", "-a", "--filter", "name=puertocho"], 
                              capture_output=True, text=True)
        print("Contenedores relacionados con puertocho:")
        if result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            print(f"   {lines[0]}")  # Header
            for line in lines[1:]:
                print(f"   {line}")
        else:
            print("   ❌ No se encontraron contenedores")
        
        # Verificar contenedor específico
        result = subprocess.run(["docker", "ps", "-q", "-f", "name=puertocho-assistant"], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            print(f"\n✅ Contenedor puertocho-assistant está EJECUTÁNDOSE")
            container_id = result.stdout.strip()
            
            # Obtener información detallada del contenedor
            result = subprocess.run(["docker", "inspect", container_id], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                import json
                container_info = json.loads(result.stdout)[0]
                state = container_info['State']
                print(f"   Estado: {state['Status']}")
                print(f"   Inicio: {state['StartedAt']}")
                if state['Status'] != 'running':
                    print(f"   Error: {state.get('Error', 'N/A')}")
        else:
            print(f"\n⭕ Contenedor puertocho-assistant está DETENIDO")
            
    except Exception as e:
        print(f"❌ Error verificando contenedores: {e}")
    
    print("\n4️⃣ VERIFICANDO ARCHIVOS DE CONFIGURACIÓN...")
    files_to_check = [
        "docker-compose.yml",
        ".env",
        "app/main.py",
        "app/requirements.txt",
        "Dockerfile"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} no encontrado")
    
    print("\n5️⃣ INTENTANDO OBTENER LOGS...")
    try:
        print("🔍 Intentando docker compose logs...")
        result = subprocess.run(["docker", "compose", "logs", "--tail", "10", "puertocho-assistant"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            print("✅ Logs disponibles con docker compose:")
            for line in result.stdout.strip().split('\n')[-5:]:  # Últimas 5 líneas
                print(f"   {line}")
        else:
            print("⚠️ No hay logs recientes con docker compose")
            
            # Intentar con docker logs directo
            result = subprocess.run(["docker", "ps", "-q", "-f", "name=puertocho-assistant"], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                container_id = result.stdout.strip()
                result = subprocess.run(["docker", "logs", "--tail", "10", container_id], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    print("✅ Logs disponibles con docker logs:")
                    for line in result.stdout.strip().split('\n')[-5:]:
                        print(f"   {line}")
                else:
                    print("⚠️ No hay logs recientes con docker logs")
            else:
                print("⚠️ No hay contenedor ejecutándose para obtener logs")
                
    except subprocess.TimeoutExpired:
        print("⚠️ Timeout obteniendo logs")
    except Exception as e:
        print(f"❌ Error obteniendo logs: {e}")
    
    print("\n6️⃣ RECOMENDACIONES...")
    print("💡 Si no ves logs:")
    print("   • Usa la opción 5 (logs alternativos) del menú")
    print("   • Reinicia el asistente con la opción 6")
    print("   • Ejecuta en primer plano con la opción 1 para ver logs directos")
    print("   • Verifica que las variables de entorno estén configuradas en .env")
    
    print("\n💡 Para resolver problemas comunes:")
    print("   • docker compose down && docker compose up --build")
    print("   • Verificar permisos de GPIO en la Raspberry Pi")
    print("   • Comprobar que el servicio de transcripción esté ejecutándose")

def main():
    """Función principal con menú interactivo"""
    
    # Verificar argumentos de línea de comandos
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['--help', '-h', 'help']:
            show_help()
            return
        elif arg in ['run', 'foreground']:
            run_foreground()
            return
        elif arg in ['start', 'background']:
            run_background()
            return
        elif arg == 'stop':
            stop_assistant()
            return
        elif arg == 'status':
            show_status()
            return
        elif arg == 'logs':
            show_logs()
            return
        elif arg == 'logs-alt':
            show_logs_alternative()
            return
        elif arg == 'restart':
            restart_assistant()
            return
        elif arg == 'diagnose':
            diagnose_system()
            return
        else:
            print(f"❌ Opción desconocida: {arg}")
            print("💡 Usa --help para ver las opciones disponibles")
            return
    
    # Menú interactivo
    while True:
        try:
            show_menu()
            choice = input("🔢 Selecciona una opción (0-9): ").strip()
            
            if choice == '1':
                run_foreground()
                break
            elif choice == '2':
                if run_background():
                    break
            elif choice == '3':
                show_status()
                input("\n⏸️  Presiona ENTER para continuar...")
            elif choice == '4':
                show_logs()
            elif choice == '5':
                show_logs_alternative()
            elif choice == '6':
                restart_assistant()
                input("\n⏸️  Presiona ENTER para continuar...")
            elif choice == '7':
                stop_assistant()
                input("\n⏸️  Presiona ENTER para continuar...")
            elif choice == '8':
                diagnose_system()
                input("\n⏸️  Presiona ENTER para continuar...")
            elif choice == '9':
                show_help()
                input("\n⏸️  Presiona ENTER para continuar...")
            elif choice == '0':
                print("👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción inválida. Por favor selecciona 0-9.")
                input("⏸️  Presiona ENTER para continuar...")
                
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("⏸️  Presiona ENTER para continuar...")

if __name__ == "__main__":
    main() 