#!/usr/bin/env python3
"""
Punto de entrada principal para el asistente de voz PuertoCho.
Versión modular que utiliza los componentes separados.
"""

import asyncio
import os
import sys
import signal
import time
import logging
from typing import Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Importaciones de módulos locales
from core.assistant import VoiceAssistant
from utils.logging_config import get_logger
from config import Config

logger = get_logger('main')

class PuertoChoApp:
    """Aplicación principal del asistente PuertoCho"""
    
    def __init__(self):
        self.config = Config()
        self.assistant: Optional[VoiceAssistant] = None
        self.running = False
        
    def setup_signal_handlers(self):
        """Configurar manejadores de señales para terminación limpia"""
        def signal_handler(signum, frame):
            logger.info(f"Recibida señal {signum}, terminando...")
            self.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def start(self):
        """Iniciar el asistente"""
        logger.info("🚀 Iniciando PuertoCho Assistant")
        
        try:
            # Verificar configuración
            if not self.config.validate():
                logger.error("❌ Configuración inválida")
                return False
            
            # Crear y configurar el asistente
            self.assistant = VoiceAssistant(self.config)
            
            # Configurar manejadores de señales
            self.setup_signal_handlers()
            
            # Inicializar el asistente
            await self.assistant.initialize()
            
            # Mostrar información de inicio
            logger.info("✅ Asistente inicializado correctamente")
            logger.info(f"🎯 Wake words: {self.assistant.get_wake_words()}")
            logger.info(f"🤖 Endpoint: {self.config.get_assistant_endpoint()}")
            logger.info(f"🎵 Audio: {self.config.get_audio_config()}")
            
            # Iniciar el bucle principal
            self.running = True
            await self.assistant.run()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error iniciando asistente: {e}")
            return False
    
    def stop(self):
        """Detener el asistente"""
        logger.info("🛑 Deteniendo asistente...")
        self.running = False
        
        if self.assistant:
            self.assistant.stop()
    
    async def run(self):
        """Ejecutar la aplicación"""
        try:
            await self.start()
        except KeyboardInterrupt:
            logger.info("Interrupción de usuario")
        except Exception as e:
            logger.error(f"Error en aplicación: {e}")
        finally:
            self.stop()
            logger.info("👋 Aplicación terminada")

def main():
    """Función principal"""
    print("🎙️  PuertoCho Voice Assistant - Versión Modular")
    print("=" * 50)
    
    app = PuertoChoApp()
    
    try:
        # Ejecutar aplicación
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("\n👋 Hasta luego!")
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
