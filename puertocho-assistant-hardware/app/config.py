#!/usr/bin/env python3
"""
Configuration module for PuertoCho Assistant Hardware Service
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

@dataclass
class AudioConfig:
    """Configuración de audio"""
    device_name: str = os.getenv("AUDIO_DEVICE_NAME", "seeed-voicecard")
    sample_rate: int = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
    channels: int = int(os.getenv("AUDIO_CHANNELS", "2"))
    chunk_size: int = int(os.getenv("AUDIO_CHUNK_SIZE", "1024"))
    format: str = os.getenv("AUDIO_FORMAT", "int16")
    buffer_size: int = int(os.getenv("AUDIO_BUFFER_SIZE", "4096"))

@dataclass
class WakeWordConfig:
    """Configuración del wake word"""
    model_path: str = os.getenv("WAKE_WORD_MODEL_PATH", "/app/models/Puerto-ocho_es_raspberry-pi_v3_0_0.ppn")
    sensitivity: float = float(os.getenv("WAKE_WORD_SENSITIVITY", "0.5"))
    access_key: str = os.getenv("PORCUPINE_ACCESS_KEY", "")

@dataclass
class VADConfig:
    """Configuración del Voice Activity Detection"""
    mode: int = int(os.getenv("VAD_MODE", "3"))
    frame_duration: int = int(os.getenv("VAD_FRAME_DURATION", "30"))
    silence_timeout: float = float(os.getenv("VAD_SILENCE_TIMEOUT", "2.0"))
    speech_timeout: float = float(os.getenv("VAD_SPEECH_TIMEOUT", "10.0"))

@dataclass
class GPIOConfig:
    """Configuración de GPIO"""
    button_pin: int = int(os.getenv("BUTTON_PIN", "17"))
    debounce_time: float = float(os.getenv("BUTTON_DEBOUNCE_TIME", "0.2"))
    long_press_time: float = float(os.getenv("BUTTON_LONG_PRESS_TIME", "2.0"))

@dataclass
class LEDConfig:
    """Configuración de LEDs"""
    count: int = int(os.getenv("LED_COUNT", "3"))
    brightness: int = int(os.getenv("LED_BRIGHTNESS", "128"))
    animation_speed: float = float(os.getenv("LED_ANIMATION_SPEED", "0.1"))
    simulate: bool = os.getenv("LED_SIMULATE", "false").lower() == "true"

@dataclass
class NFCConfig:
    """Configuración de NFC"""
    i2c_bus: int = int(os.getenv("NFC_I2C_BUS", "1"))
    i2c_address: int = int(os.getenv("NFC_I2C_ADDRESS", "0x48"), 16)
    timeout: float = float(os.getenv("NFC_TIMEOUT", "5.0"))

@dataclass
class BackendConfig:
    """Configuración del backend"""
    url: str = os.getenv("BACKEND_URL", "http://localhost:8765")
    ws_url: str = os.getenv("BACKEND_WS_URL", "ws://localhost:8765/ws")
    timeout: int = int(os.getenv("BACKEND_TIMEOUT", "30"))

@dataclass
class HardwareConfig:
    """Configuración del servicio de hardware"""
    host: str = os.getenv("HARDWARE_HOST", "0.0.0.0")
    port: int = int(os.getenv("HARDWARE_PORT", "8080"))
    log_level: str = os.getenv("HARDWARE_LOG_LEVEL", "INFO")

@dataclass
class AppConfig:
    """Configuración principal de la aplicación"""
    debug_mode: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    simulate_hardware: bool = os.getenv("SIMULATE_HARDWARE", "false").lower() == "true"
    test_mode: bool = os.getenv("TEST_MODE", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "json")
    log_file: str = os.getenv("LOG_FILE", "/app/logs/hardware.log")
    
    # Configuraciones específicas
    audio: AudioConfig = field(default_factory=AudioConfig)
    wake_word: WakeWordConfig = field(default_factory=WakeWordConfig)
    vad: VADConfig = field(default_factory=VADConfig)
    gpio: GPIOConfig = field(default_factory=GPIOConfig)
    led: LEDConfig = field(default_factory=LEDConfig)
    nfc: NFCConfig = field(default_factory=NFCConfig)
    backend: BackendConfig = field(default_factory=BackendConfig)
    hardware: HardwareConfig = field(default_factory=HardwareConfig)

# Instancia global de configuración
config = AppConfig()

def get_log_level():
    """Obtener nivel de logging"""
    level_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    return level_mapping.get(config.log_level.upper(), logging.INFO)

def validate_config():
    """Validar configuración"""
    errors = []
    
    # Validar wake word
    if not config.wake_word.access_key:
        errors.append("PORCUPINE_ACCESS_KEY is required")
    
    if not os.path.exists(config.wake_word.model_path):
        errors.append(f"Wake word model not found: {config.wake_word.model_path}")
    
    # Validar audio
    if config.audio.sample_rate <= 0:
        errors.append("AUDIO_SAMPLE_RATE must be positive")
    
    if config.audio.channels <= 0:
        errors.append("AUDIO_CHANNELS must be positive")
    
    # Validar GPIO
    if config.gpio.button_pin < 0 or config.gpio.button_pin > 40:
        errors.append("BUTTON_PIN must be between 0 and 40")
    
    # Validar LED
    if config.led.count <= 0:
        errors.append("LED_COUNT must be positive")
    
    if config.led.brightness < 0 or config.led.brightness > 255:
        errors.append("LED_BRIGHTNESS must be between 0 and 255")
    
    if config.led.animation_speed <= 0:
        errors.append("LED_ANIMATION_SPEED must be positive")
    
    if errors:
        raise ValueError(f"Configuration errors: {'; '.join(errors)}")
    
    return True
