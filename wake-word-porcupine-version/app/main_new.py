"""
Punto de entrada principal del asistente de voz PuertoCho.
"""

import asyncio
import signal
import sys
from pathlib import Path

# Añadir el directorio padre al path para importaciones
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import config
from app.utils.logging_config import setup_logging, setup_print_flush, get_logger
from app.core.assistant import VoiceAssistant

# Configurar logging y print
setup_print_flush()
logger = setup_logging()

# Variable global para el asistente
assistant: VoiceAssistant = None

async def main():
    """Función principal del asistente"""
    global assistant
    
    try:
        # Mostrar información inicial
        print("=" * 60)
        print("🎤 ASISTENTE DE VOZ PUERTOCHO")
        print("=" * 60)
        print(f"📁 Directorio de trabajo: {config.get_project_root()}")
        print(f"🔑 Access Key configurada: {'✅' if config.porcupine_access_key else '❌'}")
        print("=" * 60)
        
        # Crear e inicializar asistente
        logger.info("🚀 Iniciando asistente de voz PuertoCho...")
        assistant = VoiceAssistant()
        
        # Configurar manejo de señales
        def signal_handler(signum, frame):
            logger.info(f"🛑 Señal recibida ({signum}), deteniendo asistente...")
            asyncio.create_task(shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Iniciar asistente
        await assistant.start()
        
    except KeyboardInterrupt:
        logger.info("🛑 Interrupción por teclado")
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        sys.exit(1)
    finally:
        await shutdown()

async def shutdown():
    """Realizar shutdown limpio del asistente"""
    global assistant
    
    if assistant:
        await assistant.stop()
    
    logger.info("👋 Asistente detenido completamente")
    
    # Forzar salida si es necesario
    loop = asyncio.get_event_loop()
    loop.stop()

if __name__ == "__main__":
    try:
        # Ejecutar asistente
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Detenido por el usuario")
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)
