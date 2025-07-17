#!/usr/bin/env python3
"""
🎙️ PuertoCho Voice Assistant - Hardware Service
Main entry point for the hardware service
"""

import asyncio
import sys
import signal
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import config, validate_config
from utils.logger import logger, log_hardware_event

class HardwareService:
    """Main hardware service class"""
    
    def __init__(self):
        self.running = False
        self.tasks = []
    
    async def start(self):
        """Start the hardware service"""
        try:
            # Validate configuration
            validate_config()
            log_hardware_event("service_starting", {"config_valid": True})
            
            # Initialize components (placeholder for now)
            await self._initialize_components()
            
            # Start main service loop
            self.running = True
            log_hardware_event("service_started", {"status": "ready"})
            
            # Keep service running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Failed to start hardware service: {e}")
            raise
    
    async def stop(self):
        """Stop the hardware service"""
        log_hardware_event("service_stopping")
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        log_hardware_event("service_stopped")
    
    async def _initialize_components(self):
        """Initialize hardware components"""
        log_hardware_event("initializing_components")
        
        # TODO: Initialize audio manager
        # TODO: Initialize LED controller
        # TODO: Initialize button handler
        # TODO: Initialize NFC manager
        # TODO: Initialize wake word detector
        # TODO: Initialize VAD
        # TODO: Initialize HTTP server
        # TODO: Initialize WebSocket client
        
        log_hardware_event("components_initialized")

def setup_signal_handlers(service: HardwareService):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(service.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main function"""
    logger.info("Starting PuertoCho Assistant Hardware Service")
    
    service = HardwareService()
    setup_signal_handlers(service)
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Service failed: {e}")
        sys.exit(1)
    finally:
        await service.stop()

if __name__ == "__main__":
    asyncio.run(main())


