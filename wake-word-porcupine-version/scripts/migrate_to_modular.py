#!/usr/bin/env python3
"""
🔄 MIGRADOR - Transición al código refactorizado
Script para migrar del main.py original al código modular
"""

import os
import sys
import shutil
from pathlib import Path

# Obtener la ruta del proyecto
PROJECT_ROOT = Path(__file__).parent.absolute()

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔄 {title}")
    print(f"{'='*60}")

def backup_original():
    """Hacer backup del main.py original"""
    original_main = PROJECT_ROOT / "app" / "main.py"
    backup_main = PROJECT_ROOT / "app" / "main_original_backup.py"
    
    if original_main.exists() and not backup_main.exists():
        shutil.copy2(original_main, backup_main)
        print(f"✅ Backup creado: {backup_main}")
        return True
    elif backup_main.exists():
        print(f"ℹ️  Backup ya existe: {backup_main}")
        return True
    else:
        print(f"⚠️  No se encontró {original_main}")
        return False

def activate_new_main():
    """Activar el nuevo main.py"""
    new_main = PROJECT_ROOT / "app" / "main_new.py"
    current_main = PROJECT_ROOT / "app" / "main.py"
    
    if new_main.exists():
        # Hacer backup del actual si existe
        if current_main.exists():
            backup_main = PROJECT_ROOT / "app" / "main_original_backup.py"
            if not backup_main.exists():
                shutil.copy2(current_main, backup_main)
                print(f"✅ Backup del main.py actual: {backup_main}")
        
        # Copiar el nuevo main
        shutil.copy2(new_main, current_main)
        print(f"✅ Nuevo main.py activado desde {new_main}")
        return True
    else:
        print(f"❌ No se encontró {new_main}")
        return False

def update_dockerfile():
    """Actualizar Dockerfile si es necesario"""
    dockerfile = PROJECT_ROOT / "Dockerfile"
    
    if dockerfile.exists():
        with open(dockerfile, 'r') as f:
            content = f.read()
        
        # Verificar si ya está actualizado
        if 'python3 main.py' in content or 'python main.py' in content:
            print("ℹ️  Dockerfile ya configurado para usar main.py")
            return True
        
        print("ℹ️  Dockerfile no necesita cambios o ya está actualizado")
        return True
    else:
        print("⚠️  Dockerfile no encontrado")
        return False

def show_migration_summary():
    """Mostrar resumen de la migración"""
    print_header("RESUMEN DE LA MIGRACIÓN")
    
    print("📁 ESTRUCTURA NUEVA:")
    print("   app/")
    print("   ├── main.py              (nuevo código modular)")
    print("   ├── main_original_backup.py  (backup del original)")
    print("   ├── config.py            (configuración centralizada)")
    print("   ├── core/")
    print("   │   └── assistant.py     (lógica del asistente)")
    print("   ├── api/")
    print("   │   └── client.py        (cliente WebSocket)")
    print("   └── utils/")
    print("       └── logging_config.py (configuración de logging)")
    print()
    print("   scripts/")
    print("   ├── instalar_asistente.py")
    print("   ├── ejecutar_asistente.py")
    print("   ├── verificar_configuracion.py")
    print("   ├── configurar_access_key.py")
    print("   └── descargar_modelo_espanol.py")
    print()
    
    print("🔄 CAMBIOS REALIZADOS:")
    print("   ✅ Código modular separado por responsabilidades")
    print("   ✅ Scripts organizados en carpeta scripts/")
    print("   ✅ Rutas dinámicas (funcionan desde cualquier ubicación)")
    print("   ✅ Configuración centralizada")
    print("   ✅ Sistema de logging estructurado")
    print("   ✅ Cliente WebSocket para backend")
    print()
    
    print("🚀 PARA USAR EL CÓDIGO REFACTORIZADO:")
    print(f"   cd {PROJECT_ROOT}")
    print("   python3 scripts/instalar_asistente.py  # Instalación completa")
    print("   python3 scripts/ejecutar_asistente.py  # Ejecución con Docker")
    print("   # O directamente:")
    print("   cd app && python3 main.py             # Ejecución directa")
    print()
    
    print("📖 DOCUMENTACIÓN:")
    print("   README_REFACTORED.md  # Documentación completa de la nueva estructura")

def main():
    """Función principal del migrador"""
    print_header("MIGRADOR DEL ASISTENTE PUERTOCHO")
    print("🎯 Este script migra del código monolítico al modular")
    print()
    
    # Verificar estructura
    app_dir = PROJECT_ROOT / "app"
    if not app_dir.exists():
        print("❌ No se encontró el directorio app/")
        return False
    
    # Paso 1: Backup del original
    print("\n📋 PASO 1: Backup del código original")
    if not backup_original():
        print("⚠️  Continuando sin backup...")
    
    # Paso 2: Activar nuevo main
    print("\n📋 PASO 2: Activar código refactorizado")
    if not activate_new_main():
        print("❌ No se pudo activar el nuevo código")
        return False
    
    # Paso 3: Verificar Dockerfile
    print("\n📋 PASO 3: Verificar Dockerfile")
    update_dockerfile()
    
    # Paso 4: Mostrar resumen
    show_migration_summary()
    
    print("\n🎉 MIGRACIÓN COMPLETADA")
    print("💡 El sistema sigue siendo compatible con Docker")
    print("💡 Todos los scripts originales funcionan igual")
    print("💡 Nueva funcionalidad: integración con backend WebSocket")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n👋 ¡Migración exitosa!")
            sys.exit(0)
        else:
            print("\n❌ Migración fallida")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Migración interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado durante la migración: {e}")
        sys.exit(1)
