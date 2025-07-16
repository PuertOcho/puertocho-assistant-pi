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
from core.hardware_client import HardwareClient
from utils.logging_config import get_logger
from config import Config

logger = get_logger('main')

class PuertoChoApp:
    """Aplicación principal del asistente PuertoCho"""
    
    def __init__(self):
        self.config = Config()
        self.hardware_client: Optional[HardwareClient] = None
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
            
            # Crear y configurar el cliente hardware
            self.hardware_client = HardwareClient(self.config)
            
            # Configurar manejadores de señales
            self.setup_signal_handlers()
            
            # Inicializar el cliente
            await self.hardware_client.initialize()
            
            # Mostrar información de inicio
            logger.info("✅ Cliente hardware inicializado correctamente")
            logger.info(f"🎯 Wake words: {self.hardware_client.get_wake_words()}")
            logger.info(f"🤖 Backend: {self.config.get_backend_endpoint()}")
            logger.info(f"🎵 Audio: {self.config.get_audio_config()}")
            
            # Iniciar el bucle principal
            self.running = True
            await self.hardware_client.run()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error iniciando cliente hardware: {e}")
            return False
    
    def stop(self):
        """Detener el cliente"""
        logger.info("🛑 Deteniendo cliente...")
        self.running = False
        
        if self.hardware_client:
            asyncio.create_task(self.hardware_client.stop())
    
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
    print("🎙️  PuertoCho Hardware Client - Versión Simplificada")
    print("=" * 60)
    
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
