#!/usr/bin/env python3
"""
LED Controller for APA102 RGB LEDs
Maneja el control de LEDs RGB para indicar estados del asistente
"""

import asyncio
import time
import threading
import os
from enum import Enum
from typing import Optional, Tuple, List
from dataclasses import dataclass
import math
from utils.logger import HardwareLogger, log_hardware_event

try:
    from utils.apa102 import APA102
    SPI_AVAILABLE = True
except ImportError:
    # Fallback para desarrollo sin hardware
    APA102 = None
    SPI_AVAILABLE = False

from config import config

class LEDState(Enum):
    """Estados del asistente que se reflejan en los LEDs"""
    IDLE = "idle"           # Disponible (azul pulsante)
    LISTENING = "listening" # Escuchando (verde sólido)
    PROCESSING = "processing" # Procesando (amarillo giratorio)
    SPEAKING = "speaking"   # Hablando (blanco pulsante)
    ERROR = "error"         # Error (rojo parpadeante)
    OFF = "off"             # Apagado

@dataclass
class LEDColor:
    """Representa un color RGB"""
    red: int
    green: int 
    blue: int
    brightness: int = 255
    
    def __post_init__(self):
        # Validar valores
        for value in [self.red, self.green, self.blue, self.brightness]:
            if not 0 <= value <= 255:
                raise ValueError(f"Color values must be between 0 and 255, got {value}")

class LEDPattern:
    """Clase base para patrones de LED"""
    def __init__(self, colors: List[LEDColor], duration: float = 1.0):
        self.colors = colors
        self.duration = duration
        self.start_time = time.time()
    
    def get_color(self, led_index: int, elapsed_time: float) -> LEDColor:
        """Obtener color para un LED específico en un tiempo dado"""
        raise NotImplementedError

class SolidPattern(LEDPattern):
    """Patrón sólido - todos los LEDs del mismo color"""
    def get_color(self, led_index: int, elapsed_time: float) -> LEDColor:
        return self.colors[0] if self.colors else LEDColor(0, 0, 0)

class PulsePattern(LEDPattern):
    """Patrón pulsante - brillo que varía sinusoidalmente"""
    def __init__(self, colors: List[LEDColor], duration: float = 2.0, min_brightness: int = 50):
        super().__init__(colors, duration)
        self.min_brightness = min_brightness
    
    def get_color(self, led_index: int, elapsed_time: float) -> LEDColor:
        if not self.colors:
            return LEDColor(0, 0, 0)
        
        base_color = self.colors[0]
        # Calcular brillo pulsante
        pulse_factor = (math.sin(elapsed_time * 2 * math.pi / self.duration) + 1) / 2
        brightness = int(self.min_brightness + (base_color.brightness - self.min_brightness) * pulse_factor)
        
        return LEDColor(base_color.red, base_color.green, base_color.blue, brightness)

class RotatingPattern(LEDPattern):
    """Patrón giratorio - color que se mueve alrededor del anillo"""
    def __init__(self, colors: List[LEDColor], duration: float = 1.0, width: int = 1):
        super().__init__(colors, duration)
        self.width = width
    
    def get_color(self, led_index: int, elapsed_time: float) -> LEDColor:
        if not self.colors:
            return LEDColor(0, 0, 0)
        
        # Calcular posición del patrón
        num_leds = 3  # Para el ReSpeaker 2-Mic Hat
        progress = (elapsed_time / self.duration) % 1.0
        active_position = progress * num_leds
        
        # Determinar si este LED está activo
        distance = min(
            abs(led_index - active_position),
            abs(led_index - active_position + num_leds),
            abs(led_index - active_position - num_leds)
        )
        
        if distance < self.width:
            return self.colors[0]
        else:
            return LEDColor(0, 0, 0)

class BlinkPattern(LEDPattern):
    """Patrón parpadeante - encendido/apagado"""
    def __init__(self, colors: List[LEDColor], duration: float = 1.0, duty_cycle: float = 0.5):
        super().__init__(colors, duration)
        self.duty_cycle = duty_cycle
    
    def get_color(self, led_index: int, elapsed_time: float) -> LEDColor:
        if not self.colors:
            return LEDColor(0, 0, 0)
        
        cycle_progress = (elapsed_time / self.duration) % 1.0
        if cycle_progress < self.duty_cycle:
            return self.colors[0]
        else:
            return LEDColor(0, 0, 0)

class LEDController:
    """Controlador principal para LEDs APA102"""
    
    # Colores predefinidos
    COLORS = {
        'blue': LEDColor(0, 0, 255),
        'green': LEDColor(0, 255, 0),
        'yellow': LEDColor(255, 255, 0),
        'red': LEDColor(255, 0, 0),
        'white': LEDColor(255, 255, 255),
        'purple': LEDColor(128, 0, 128),
        'orange': LEDColor(255, 165, 0),
        'off': LEDColor(0, 0, 0)
    }
    
    def __init__(self, num_leds: int = None, brightness: int = None, simulate: bool = None):
        """
        Inicializar controlador de LEDs
        
        Args:
            num_leds: Número de LEDs en el anillo (usar config si es None)
            brightness: Brillo global 0-255 (usar config si es None)
            simulate: Si True, simula sin hardware real (usar config si es None)
        """
        # Initialize HardwareLogger
        self.logger = HardwareLogger("core.led_controller")
        
        # Usar configuración por defecto si no se especifica
        self.num_leds = num_leds if num_leds is not None else config.led.count
        self.brightness = brightness if brightness is not None else config.led.brightness
        self.simulate = simulate if simulate is not None else config.led.simulate
        
        # Si simulate es False, verificar si hay hardware disponible
        if not self.simulate and not os.path.exists('/dev/spidev0.0'):
            self.logger.warning("SPI device not found, switching to simulation mode")
            self.simulate = True
        
        self.current_state = LEDState.OFF
        self.current_pattern: Optional[LEDPattern] = None
        self.animation_running = False
        self.animation_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Inicializar driver APA102
        if not self.simulate and SPI_AVAILABLE:
            try:
                self.driver = APA102(num_led=self.num_leds)
                self.logger.info(f"Initialized APA102 driver with {self.num_leds} LEDs")
            except Exception as e:
                self.logger.error(f"Failed to initialize APA102 driver: {e}")
                self.simulate = True
                self.driver = None
        else:
            self.driver = None
            self.logger.info("Running in LED simulation mode")
    
    def _apply_brightness(self, color: LEDColor) -> LEDColor:
        """Aplicar brillo global a un color"""
        factor = self.brightness / 255.0
        return LEDColor(
            int(color.red * factor),
            int(color.green * factor),
            int(color.blue * factor),
            color.brightness
        )
    
    def _set_led_color(self, led_index: int, color: LEDColor):
        """Establecer color de un LED específico"""
        if self.simulate:
            # Simular - solo logging
            self.logger.debug(f"LED {led_index}: RGB({color.red}, {color.green}, {color.blue}) Brightness({color.brightness})")
            return
        
        if self.driver:
            try:
                # La librería apa102 no usa brightness por pixel, aplicamos el brightness global
                adjusted_color = self._apply_brightness(color)
                self.driver.set_pixel(led_index, adjusted_color.red, adjusted_color.green, adjusted_color.blue)
            except Exception as e:
                self.logger.error(f"Failed to set LED {led_index}: {e}")
    
    def _update_all_leds(self, colors: List[LEDColor]):
        """Actualizar todos los LEDs"""
        for i in range(self.num_leds):
            color = colors[i] if i < len(colors) else LEDColor(0, 0, 0)
            self._set_led_color(i, color)
        
        if self.driver:
            try:
                self.driver.show()
            except Exception as e:
                self.logger.error(f"Failed to show LEDs: {e}")
    
    def _animation_loop(self):
        """Bucle principal de animación"""
        self.logger.info("Starting LED animation loop")
        
        while not self.stop_event.is_set():
            if self.current_pattern:
                elapsed_time = time.time() - self.current_pattern.start_time
                colors = []
                
                for i in range(self.num_leds):
                    color = self.current_pattern.get_color(i, elapsed_time)
                    colors.append(color)
                
                self._update_all_leds(colors)
            
            time.sleep(config.led.animation_speed)  # Usar velocidad de animación de config
        
        self.logger.info("LED animation loop stopped")
    
    def start_animation(self):
        """Iniciar hilo de animación"""
        if self.animation_running:
            return
        
        self.stop_event.clear()
        self.animation_running = True
        self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.animation_thread.start()
        self.logger.info("LED animation started")
    
    def stop_animation(self):
        """Detener hilo de animación"""
        if not self.animation_running:
            return
        
        self.stop_event.set()
        self.animation_running = False
        
        if self.animation_thread:
            self.animation_thread.join(timeout=1.0)
            self.animation_thread = None
        
        self.logger.info("LED animation stopped")
    
    def set_pattern(self, pattern: LEDPattern):
        """Establecer patrón de LED"""
        self.current_pattern = pattern
        self.current_pattern.start_time = time.time()
        self.logger.info(f"LED pattern set: {type(pattern).__name__}")
    
    def set_state(self, state: LEDState):
        """Establecer estado del asistente"""
        if self.current_state == state:
            return
        
        self.current_state = state
        self.logger.info(f"LED state changed to: {state.value}")
        
        # Configurar patrón según estado
        if state == LEDState.IDLE:
            # Azul pulsante
            pattern = PulsePattern([self.COLORS['blue']], duration=3.0, min_brightness=30)
        elif state == LEDState.LISTENING:
            # Verde sólido
            pattern = SolidPattern([self.COLORS['green']])
        elif state == LEDState.PROCESSING:
            # Amarillo giratorio
            pattern = RotatingPattern([self.COLORS['yellow']], duration=1.5)
        elif state == LEDState.SPEAKING:
            # Blanco pulsante
            pattern = PulsePattern([self.COLORS['white']], duration=1.0, min_brightness=100)
        elif state == LEDState.ERROR:
            # Rojo parpadeante
            pattern = BlinkPattern([self.COLORS['red']], duration=0.5, duty_cycle=0.5)
        elif state == LEDState.OFF:
            # Apagado
            pattern = SolidPattern([self.COLORS['off']])
        else:
            self.logger.warning(f"Unknown LED state: {state}")
            pattern = SolidPattern([self.COLORS['off']])
        
        self.set_pattern(pattern)
    
    def set_custom_color(self, color: LEDColor):
        """Establecer color personalizado sólido"""
        pattern = SolidPattern([color])
        self.set_pattern(pattern)
        self.logger.info(f"Custom color set: RGB({color.red}, {color.green}, {color.blue})")
    
    def set_rainbow_pattern(self, duration: float = 5.0):
        """Establecer patrón arcoíris"""
        # Crear colores del arcoíris
        rainbow_colors = [
            LEDColor(255, 0, 0),    # Rojo
            LEDColor(255, 165, 0),  # Naranja
            LEDColor(255, 255, 0),  # Amarillo
            LEDColor(0, 255, 0),    # Verde
            LEDColor(0, 0, 255),    # Azul
            LEDColor(128, 0, 128),  # Púrpura
        ]
        
        class RainbowPattern(LEDPattern):
            def get_color(self, led_index: int, elapsed_time: float) -> LEDColor:
                progress = (elapsed_time / self.duration) % 1.0
                color_index = (progress * len(rainbow_colors) + led_index) % len(rainbow_colors)
                return rainbow_colors[int(color_index)]
        
        pattern = RainbowPattern(rainbow_colors, duration)
        self.set_pattern(pattern)
        self.logger.info("Rainbow pattern set")
    
    def set_brightness(self, brightness: int):
        """Establecer brillo global"""
        if not 0 <= brightness <= 255:
            raise ValueError("Brightness must be between 0 and 255")
        
        self.brightness = brightness
        self.logger.info(f"LED brightness set to: {brightness}")
    
    def turn_off(self):
        """Apagar todos los LEDs"""
        self.set_state(LEDState.OFF)
    
    def test_pattern(self, duration: float = 5.0):
        """Ejecutar patrón de prueba"""
        self.logger.info("Starting LED test pattern")
        
        # Ciclo de prueba
        states = [
            LEDState.IDLE,
            LEDState.LISTENING,
            LEDState.PROCESSING,
            LEDState.SPEAKING,
            LEDState.ERROR
        ]
        
        for state in states:
            self.set_state(state)
            time.sleep(duration / len(states))
        
        self.set_state(LEDState.OFF)
        self.logger.info("LED test pattern completed")
    
    def cleanup(self):
        """Limpiar recursos"""
        self.logger.info("Cleaning up LED controller")
        self.stop_animation()
        self.turn_off()
        
        if self.driver:
            try:
                # Asegurarse de que los LEDs estén apagados
                for i in range(self.num_leds):
                    self.driver.set_pixel(i, 0, 0, 0)
                self.driver.show()
                self.driver.cleanup()
            except Exception as e:
                self.logger.error(f"Error during LED cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        self.start_animation()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
