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

from core.led_controller import LEDController, LEDState
from core.state_manager import StateManager, AssistantState
from core.vad_handler import VADHandler

class HardwareService:
    """Main hardware service class"""
    
    def __init__(self):
        self.running = False
        self.tasks = []
        self.main_loop = asyncio.get_event_loop()

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
        
        # Stop components in reverse order
        if hasattr(self, 'audio_manager'):
            self.audio_manager.stop_recording()
            
        if hasattr(self, 'wake_word_detector'):
            self.wake_word_detector.stop()
            
        if hasattr(self, 'led_controller'):
            self.led_controller.set_state(LEDState.OFF)
            self.led_controller.stop_animation()
        
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

        self.led_controller = LEDController()
        self.led_controller.start_animation()
        self.led_controller.set_state(LEDState.IDLE)
        log_hardware_event("led_controller_initialized", {
            "num_leds": self.led_controller.num_leds,
            "brightness": self.led_controller.brightness
        })

        # Initialize VADHandler
        self.vad_handler = VADHandler(
            sample_rate=16000,  # WebRTC VAD requiere 16kHz
            input_sample_rate=config.audio.sample_rate,  # Audio del ReSpeaker (44.1kHz)
            frame_duration=config.vad.frame_duration,
            aggressiveness=config.vad.mode,
            silence_timeout=config.vad.silence_timeout
        )
        log_hardware_event("vad_handler_initialized", {
            "target_sample_rate": 16000,
            "input_sample_rate": config.audio.sample_rate,
            "frame_duration": config.vad.frame_duration,
            "aggressiveness": config.vad.mode,
            "silence_timeout": config.vad.silence_timeout
        })

        # Initialize StateManager with LED and VAD
        self.state_manager = StateManager(
            led_controller=self.led_controller,
            vad_handler=self.vad_handler
        )
        
        # Pasar referencia al event loop para operaciones asíncronas
        self.state_manager._event_loop = asyncio.get_running_loop()

        # Initialize audio manager with configuration
        from core.audio_manager import AudioManager
        self.audio_manager = AudioManager()
        log_hardware_event("audio_manager_initialized", {
            "sample_rate": config.audio.sample_rate,
            "channels": config.audio.channels,
            "device_name": config.audio.device_name
        })

        # Initialize wake word detector
        from core.wake_word_detector import WakeWordDetector
        self.wake_word_detector = WakeWordDetector(on_wake_word=self._on_wake_word_detected)
        self.wake_word_detector.start()
        log_hardware_event("wake_word_detector_initialized", {
            "model_path": config.wake_word.model_path,
            "sensitivity": config.wake_word.sensitivity
        })

        # Start audio recording with main callback
        self.audio_manager.start_recording(self._audio_callback)
        log_hardware_event("audio_recording_started")

        # TODO: Initialize button handler
        # TODO: Initialize NFC manager
        # TODO: Initialize HTTP server
        # TODO: Initialize WebSocket client

        log_hardware_event("components_initialized")
    
    def _audio_callback(self, audio_data, frames, status):
        """Callback para procesar chunks de audio"""
        # Procesar wake word si está en IDLE
        if hasattr(self, 'wake_word_detector') and hasattr(self, 'state_manager'):
            if self.state_manager.state == AssistantState.IDLE:
                self.wake_word_detector.process_audio_chunk(audio_data)
            elif self.state_manager.state == AssistantState.LISTENING:
                # En LISTENING, enrutar audio al VADHandler vía StateManager
                self.state_manager.handle_audio_chunk(audio_data)
        else:
            # Fallback: solo wake word
            if hasattr(self, 'wake_word_detector'):
                self.wake_word_detector.process_audio_chunk(audio_data)
    
    def _on_wake_word_detected(self, event):
        """Callback cuando se detecta wake word"""
        logger.info(f"🔥 Wake word detected on channel {event.channel}!")

        # Cambiar estado a LISTENING usando StateManager
        if hasattr(self, 'state_manager'):
            self.state_manager.set_state(AssistantState.LISTENING)
        else:
            # Fallback: solo LEDs
            if hasattr(self, 'led_controller'):
                self.led_controller.set_state(LEDState.LISTENING)

        log_hardware_event("wake_word_detected", {
            "channel": event.channel,
            "keyword_index": event.keyword_index,
            "timestamp": event.timestamp
        })

        # El StateManager se encargará de volver a IDLE tras fin de voz
    
    async def _return_to_idle_after_delay(self, delay_seconds: float):
        """Vuelve al estado idle después de un delay"""
        await asyncio.sleep(delay_seconds)
        if hasattr(self, 'led_controller'):
            self.led_controller.set_state(LEDState.IDLE)
        logger.info("Returned to idle state")

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


