#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento del VAD integrado
"""
import sys
import asyncio
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config
from core.vad_handler import VADHandler
from core.state_manager import StateManager, AssistantState
from core.led_controller import LEDController, LEDState
from core.audio_manager import AudioManager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class VADTestService:
    def __init__(self):
        self.running = False
        self.audio_manager = None
        self.vad_handler = None
        self.state_manager = None
        self.led_controller = None
        
    async def start(self):
        """Start the VAD test service"""
        print("🎙️ Starting VAD Integration Test...")
        
        # Initialize components
        self.led_controller = LEDController()
        self.led_controller.start_animation()
        self.led_controller.set_state(LEDState.IDLE)
        print("✅ LED Controller initialized")
        
        self.vad_handler = VADHandler(
            sample_rate=16000,
            input_sample_rate=config.audio.sample_rate,
            frame_duration=config.vad.frame_duration,
            aggressiveness=config.vad.mode,
            silence_timeout=config.vad.silence_timeout
        )
        print("✅ VAD Handler initialized")
        
        self.state_manager = StateManager(
            led_controller=self.led_controller,
            vad_handler=self.vad_handler
        )
        print("✅ State Manager initialized")
        
        self.audio_manager = AudioManager()
        print("✅ Audio Manager initialized")
        
        self.running = True
        
        # Start audio recording
        self.audio_manager.start_recording(self._audio_callback)
        print("🎤 Audio recording started")
        
        # Simulate wake word detection after 3 seconds
        await asyncio.sleep(3)
        print("🔔 Simulating wake word detection...")
        self.state_manager.set_state(AssistantState.LISTENING)
        
        # Keep running
        print("🎯 VAD is now active. Speak into the microphone...")
        print("📝 The system will:")
        print("   - Detect when you start speaking")
        print("   - Capture your audio")
        print("   - Detect when you stop speaking")
        print("   - Save the captured audio")
        print("   - Return to idle state")
        print("⏹️  Press Ctrl+C to stop")
        
        try:
            while self.running:
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping VAD test...")
            await self.stop()
            
    async def stop(self):
        """Stop the test service"""
        self.running = False
        
        if self.audio_manager:
            self.audio_manager.stop_recording()
            
        if self.led_controller:
            self.led_controller.set_state(LEDState.OFF)
            self.led_controller.stop_animation()
            
        print("✅ VAD test stopped")
    
    def _audio_callback(self, audio_data, frames, status):
        """Audio callback that feeds data to the state manager"""
        if status:
            print(f"⚠️ Audio status: {status}")
            
        if self.state_manager:
            self.state_manager.handle_audio_chunk(audio_data)

async def main():
    """Main test function"""
    service = VADTestService()
    await service.start()

if __name__ == "__main__":
    asyncio.run(main())
