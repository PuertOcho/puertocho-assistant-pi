#!/usr/bin/env python3
"""
LED Controller for APA102 RGB LEDs
Maneja el control de LEDs RGB para indicar estados del asistente
"""

import asyncio
import time
import threading
import os
import queue
from enum import Enum
from typing import Optional, Tuple, List, Callable, Dict, Any
from dataclasses import dataclass, field
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

class AudioLevelPattern(LEDPattern):
    """Patrón que responde a niveles de audio en tiempo real"""
    def __init__(self, colors: List[LEDColor], duration: float = 0.1):
        super().__init__(colors, duration)
        self.audio_level = 0.0  # 0.0 a 1.0
        self.peak_level = 0.0
        self.decay_factor = 0.95  # Factor de decaimiento para picos
    
    def update_audio_level(self, level: float, peak: float = None):
        """Actualizar nivel de audio"""
        self.audio_level = max(0.0, min(1.0, level))
        if peak is not None:
            self.peak_level = max(self.peak_level * self.decay_factor, peak)
    
    def get_color(self, led_index: int, elapsed_time: float) -> LEDColor:
        if not self.colors:
            return LEDColor(0, 0, 0)
        
        base_color = self.colors[0]
        
        # Calcular número de LEDs que deben estar encendidos basado en el nivel
        num_leds = 3  # Para ReSpeaker 2-Mic Hat
        active_leds = int(self.audio_level * num_leds)
        
        if led_index < active_leds:
            # LED activo basado en nivel
            intensity = 1.0
        elif led_index == int(self.peak_level * num_leds) and self.peak_level > self.audio_level:
            # LED de pico
            intensity = 0.5
        else:
            # LED inactivo
            intensity = 0.0
        
        return LEDColor(
            int(base_color.red * intensity),
            int(base_color.green * intensity), 
            int(base_color.blue * intensity),
            int(base_color.brightness * intensity)
        )

class SpectrumPattern(LEDPattern):
    """Patrón que visualiza espectro de frecuencias"""
    def __init__(self, colors: List[LEDColor], duration: float = 0.1):
        super().__init__(colors, duration)
        self.frequency_bins = [0.0, 0.0, 0.0]  # Una por LED
        self.smoothing_factor = 0.7
    
    def update_spectrum(self, frequencies: List[float]):
        """Actualizar bins de frecuencia"""
        if len(frequencies) >= 3:
            for i in range(3):
                # Smoothing exponencial
                self.frequency_bins[i] = (
                    self.smoothing_factor * self.frequency_bins[i] + 
                    (1 - self.smoothing_factor) * frequencies[i]
                )
    
    def get_color(self, led_index: int, elapsed_time: float) -> LEDColor:
        if not self.colors or led_index >= len(self.frequency_bins):
            return LEDColor(0, 0, 0)
        
        base_color = self.colors[min(led_index, len(self.colors) - 1)]
        intensity = min(1.0, max(0.0, self.frequency_bins[led_index]))
        
        return LEDColor(
            int(base_color.red * intensity),
            int(base_color.green * intensity),
            int(base_color.blue * intensity),
            int(base_color.brightness * intensity)
        )

@dataclass
class AnimationTransition:
    """Configuración para transiciones entre animaciones"""
    from_pattern: Optional[LEDPattern]
    to_pattern: LEDPattern
    duration: float = 0.5
    transition_type: str = "fade"  # "fade", "slide", "instant"
    start_time: float = field(default_factory=time.time)

@dataclass
class AnimationCommand:
    """Comando para la cola de animaciones"""
    pattern: LEDPattern
    priority: int = 0
    interrupting: bool = False
    transition: Optional[AnimationTransition] = None

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
        self.current_transition: Optional[AnimationTransition] = None
        self.animation_running = False
        self.animation_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Cola de animaciones y sistema de prioridades
        self.animation_queue = queue.PriorityQueue()
        self.current_priority = 0
        
        # Cache de patrones para optimización
        self.pattern_cache: Dict[str, LEDPattern] = {}
        
        # Callbacks para eventos de audio
        self.audio_callbacks: List[Callable] = []
        
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
        """Bucle principal de animación con soporte para transiciones y cola"""
        self.logger.info("Starting LED animation loop")
        
        while not self.stop_event.is_set():
            try:
                # Procesar cola de animaciones
                self._process_animation_queue()
                
                if self.current_pattern:
                    current_time = time.time()
                    elapsed_time = current_time - self.current_pattern.start_time
                    colors = []
                    
                    # Verificar si hay transición activa
                    if self.current_transition:
                        transition_elapsed = current_time - self.current_transition.start_time
                        transition_progress = min(1.0, transition_elapsed / self.current_transition.duration)
                        
                        if transition_progress >= 1.0:
                            # Transición completada
                            self.current_transition = None
                        else:
                            # Aplicar transición
                            for i in range(self.num_leds):
                                if self.current_transition.from_pattern:
                                    from_color = self.current_transition.from_pattern.get_color(i, elapsed_time)
                                else:
                                    from_color = LEDColor(0, 0, 0)
                                
                                to_color = self.current_transition.to_pattern.get_color(i, elapsed_time)
                                
                                final_color = self._apply_transition(
                                    from_color, to_color, transition_progress, 
                                    self.current_transition.transition_type
                                )
                                colors.append(final_color)
                    
                    # Si no hay transición o está completada, usar patrón normal
                    if not self.current_transition:
                        for i in range(self.num_leds):
                            color = self.current_pattern.get_color(i, elapsed_time)
                            colors.append(color)
                    
                    self._update_all_leds(colors)
                    
                    # Marcar patrón como usado (para cache)
                    if hasattr(self.current_pattern, 'last_used'):
                        self.current_pattern.last_used = current_time
                
                # Optimización periódica (cada 30 segundos aproximadamente)
                if int(time.time()) % 30 == 0:
                    self.optimize_performance()
                
                time.sleep(config.led.animation_speed)  # Usar velocidad de animación de config
                
            except Exception as e:
                self.logger.error(f"Error in animation loop: {e}")
                time.sleep(0.1)  # Breve pausa en caso de error
        
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
    
    def _get_pattern_for_state(self, state: LEDState) -> LEDPattern:
        """Obtener patrón correspondiente a un estado (para uso interno)"""
        if state == LEDState.IDLE:
            return PulsePattern([self.COLORS['blue']], duration=3.0, min_brightness=30)
        elif state == LEDState.LISTENING:
            return SolidPattern([self.COLORS['green']])
        elif state == LEDState.PROCESSING:
            return RotatingPattern([self.COLORS['yellow']], duration=1.5)
        elif state == LEDState.SPEAKING:
            return PulsePattern([self.COLORS['white']], duration=1.0, min_brightness=100)
        elif state == LEDState.ERROR:
            return BlinkPattern([self.COLORS['red']], duration=0.5, duty_cycle=0.5)
        elif state == LEDState.OFF:
            return SolidPattern([self.COLORS['off']])
        else:
            return SolidPattern([self.COLORS['off']])
    
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
    
    # ============= NUEVAS FUNCIONALIDADES - FASE 3 =============
    
    def pulse_with_audio_level(self, audio_level: float, peak_level: float = None, 
                              base_color: LEDColor = None):
        """
        Pulsar LEDs sincronizado con nivel de audio
        
        Args:
            audio_level: Nivel de audio (0.0 a 1.0)
            peak_level: Nivel de pico opcional
            base_color: Color base para la visualización
        """
        if base_color is None:
            base_color = self.COLORS['blue']
        
        # Crear o actualizar patrón de audio
        pattern_key = "audio_level"
        if pattern_key not in self.pattern_cache:
            self.pattern_cache[pattern_key] = AudioLevelPattern([base_color])
        
        audio_pattern = self.pattern_cache[pattern_key]
        audio_pattern.update_audio_level(audio_level, peak_level)
        
        # Aplicar patrón con prioridad media
        self._queue_animation(AnimationCommand(
            pattern=audio_pattern,
            priority=50,
            interrupting=True
        ))
    
    def visualize_spectrum(self, frequency_bins: List[float], colors: List[LEDColor] = None):
        """
        Visualizar espectro de frecuencias en los LEDs
        
        Args:
            frequency_bins: Lista de niveles por bin de frecuencia
            colors: Colores para cada bin (opcional)
        """
        if colors is None:
            colors = [self.COLORS['red'], self.COLORS['green'], self.COLORS['blue']]
        
        pattern_key = "spectrum"
        if pattern_key not in self.pattern_cache:
            self.pattern_cache[pattern_key] = SpectrumPattern(colors)
        
        spectrum_pattern = self.pattern_cache[pattern_key]
        spectrum_pattern.update_spectrum(frequency_bins)
        
        self._queue_animation(AnimationCommand(
            pattern=spectrum_pattern,
            priority=50,
            interrupting=True
        ))
    
    def set_pattern_with_transition(self, pattern: LEDPattern, transition_duration: float = 0.5,
                                   transition_type: str = "fade", priority: int = 0):
        """
        Establecer patrón con transición suave
        
        Args:
            pattern: Nuevo patrón a aplicar
            transition_duration: Duración de la transición en segundos
            transition_type: Tipo de transición ("fade", "slide", "instant")
            priority: Prioridad de la animación
        """
        transition = AnimationTransition(
            from_pattern=self.current_pattern,
            to_pattern=pattern,
            duration=transition_duration,
            transition_type=transition_type
        )
        
        command = AnimationCommand(
            pattern=pattern,
            priority=priority,
            interrupting=True,
            transition=transition
        )
        
        self._queue_animation(command)
        self.logger.debug(f"Pattern queued with {transition_type} transition ({transition_duration}s)")
    
    def queue_animation(self, pattern: LEDPattern, priority: int = 0, interrupting: bool = False):
        """
        Añadir animación a la cola
        
        Args:
            pattern: Patrón a animar
            priority: Prioridad (mayor número = mayor prioridad)
            interrupting: Si True, interrumpe la animación actual
        """
        command = AnimationCommand(
            pattern=pattern,
            priority=priority,
            interrupting=interrupting
        )
        self._queue_animation(command)
    
    def _queue_animation(self, command: AnimationCommand):
        """Añadir comando a la cola de animaciones"""
        if command.interrupting and command.priority >= self.current_priority:
            # Interrumpir animación actual
            self.current_pattern = command.pattern
            self.current_transition = command.transition
            self.current_priority = command.priority
        else:
            # Añadir a cola
            self.animation_queue.put((-command.priority, time.time(), command))
    
    def _process_animation_queue(self):
        """Procesar cola de animaciones"""
        try:
            # Intentar obtener siguiente animación
            _, _, command = self.animation_queue.get_nowait()
            
            if command.priority >= self.current_priority:
                self.current_pattern = command.pattern
                self.current_transition = command.transition
                self.current_priority = command.priority
                
        except queue.Empty:
            pass
    
    def _apply_transition(self, from_color: LEDColor, to_color: LEDColor, 
                         progress: float, transition_type: str) -> LEDColor:
        """
        Aplicar transición entre colores
        
        Args:
            from_color: Color inicial
            to_color: Color final
            progress: Progreso de transición (0.0 a 1.0)
            transition_type: Tipo de transición
            
        Returns:
            Color interpolado
        """
        if transition_type == "instant" or progress >= 1.0:
            return to_color
        
        if transition_type == "fade":
            # Interpolación lineal
            return LEDColor(
                int(from_color.red + (to_color.red - from_color.red) * progress),
                int(from_color.green + (to_color.green - from_color.green) * progress),
                int(from_color.blue + (to_color.blue - from_color.blue) * progress),
                int(from_color.brightness + (to_color.brightness - from_color.brightness) * progress)
            )
        
        elif transition_type == "slide":
            # Transición con curva suave (ease-in-out)
            smooth_progress = 3 * progress**2 - 2 * progress**3
            return LEDColor(
                int(from_color.red + (to_color.red - from_color.red) * smooth_progress),
                int(from_color.green + (to_color.green - from_color.green) * smooth_progress),
                int(from_color.blue + (to_color.blue - from_color.blue) * smooth_progress),
                int(from_color.brightness + (to_color.brightness - from_color.brightness) * smooth_progress)
            )
        
        return to_color
    
    def register_audio_callback(self, callback: Callable[[float, float], None]):
        """
        Registrar callback para eventos de audio
        
        Args:
            callback: Función que recibe (audio_level, peak_level)
        """
        self.audio_callbacks.append(callback)
        self.logger.debug("Audio callback registered")
    
    def unregister_audio_callback(self, callback: Callable):
        """Desregistrar callback de audio"""
        if callback in self.audio_callbacks:
            self.audio_callbacks.remove(callback)
            self.logger.debug("Audio callback unregistered")
    
    def _notify_audio_callbacks(self, audio_level: float, peak_level: float):
        """Notificar callbacks de audio"""
        for callback in self.audio_callbacks:
            try:
                callback(audio_level, peak_level)
            except Exception as e:
                self.logger.error(f"Error in audio callback: {e}")
    
    def get_animation_status(self) -> Dict[str, Any]:
        """Obtener estado actual de las animaciones"""
        return {
            "current_state": self.current_state.value,
            "current_pattern": type(self.current_pattern).__name__ if self.current_pattern else None,
            "current_priority": self.current_priority,
            "animation_running": self.animation_running,
            "queue_size": self.animation_queue.qsize(),
            "has_transition": self.current_transition is not None,
            "cached_patterns": list(self.pattern_cache.keys()),
            "audio_callbacks": len(self.audio_callbacks)
        }
    
    def clear_animation_queue(self):
        """Limpiar cola de animaciones"""
        while not self.animation_queue.empty():
            try:
                self.animation_queue.get_nowait()
            except queue.Empty:
                break
        self.logger.debug("Animation queue cleared")
    
    def optimize_performance(self):
        """Optimizar rendimiento limpiando cache antiguo"""
        # Limpiar patrones en cache que no se han usado recientemente
        current_time = time.time()
        patterns_to_remove = []
        
        for key, pattern in self.pattern_cache.items():
            # Si el patrón no se ha usado en los últimos 30 segundos
            if hasattr(pattern, 'last_used') and current_time - pattern.last_used > 30:
                patterns_to_remove.append(key)
        
        for key in patterns_to_remove:
            del self.pattern_cache[key]
        
        if patterns_to_remove:
            self.logger.debug(f"Removed {len(patterns_to_remove)} unused patterns from cache")
    
    # ============= FIN NUEVAS FUNCIONALIDADES =============
    
    def __enter__(self):
        """Context manager entry"""
        self.start_animation()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
