#!/usr/bin/env python3
"""
Button Handler Module for PuertoCho Assistant Hardware Service

Maneja la detección de botones GPIO con debouncing y soporte para pulsaciones cortas y largas.
Notifica eventos al StateManager a través de callbacks.
"""

import time
import threading
from typing import Callable, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass
from utils.logger import HardwareLogger, log_hardware_event

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    # Manejaremos el warning en la clase

from config import config

class ButtonEvent(Enum):
    """Tipos de eventos de botón"""
    SHORT_PRESS = "short_press"
    LONG_PRESS = "long_press"
    PRESS_START = "press_start"
    PRESS_END = "press_end"

@dataclass
class ButtonEventData:
    """Datos del evento de botón"""
    event_type: ButtonEvent
    pin: int
    press_duration: float
    timestamp: float

class ButtonHandler:
    """
    Maneja la detección de botones GPIO con debouncing y soporte para pulsaciones cortas y largas.
    
    Características:
    - Detección de pulsaciones cortas y largas
    - Debouncing para evitar falsas activaciones
    - Soporte para simulación (sin hardware real)
    - Callbacks para notificar eventos al StateManager
    - Logging detallado de eventos
    """
    
    def __init__(self, pin: Optional[int] = None, debounce_time: Optional[float] = None, 
                 long_press_time: Optional[float] = None, simulate: Optional[bool] = None):
        """
        Inicializar ButtonHandler
        
        Args:
            pin: Pin GPIO para el botón (default: config.gpio.button_pin)
            debounce_time: Tiempo de debounce en segundos (default: config.gpio.debounce_time)
            long_press_time: Tiempo para considerar pulsación larga (default: config.gpio.long_press_time)
            simulate: Modo simulación (default: config.app.simulate_hardware)
        """
        # Initialize HardwareLogger
        self.logger = HardwareLogger("button_handler")
        
        self.pin = pin or config.gpio.button_pin
        self.debounce_time = debounce_time or config.gpio.debounce_time
        self.long_press_time = long_press_time or config.gpio.long_press_time
        self.simulate = simulate if simulate is not None else config.simulate_hardware
        
        # Log warning if GPIO not available
        if not GPIO_AVAILABLE:
            self.logger.warning("RPi.GPIO not available, ButtonHandler will run in simulation mode")
        
        # Estado interno
        self._is_running = False
        self._is_pressed = False
        self._press_start_time = None
        self._last_interrupt_time = 0
        self._callbacks: Dict[ButtonEvent, Callable] = {}
        self._button_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Configurar GPIO si está disponible
        if GPIO_AVAILABLE and not self.simulate:
            self._setup_gpio()
        else:
            self.logger.info(f"ButtonHandler iniciado en modo simulación (pin: {self.pin})")
    
    def _setup_gpio(self):
        """Configurar GPIO para el botón"""
        try:
            # Configurar GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Configurar interrupción para ambos flancos
            GPIO.add_event_detect(self.pin, GPIO.BOTH, callback=self._gpio_callback, bouncetime=int(self.debounce_time * 1000))
            
            self.logger.info(f"GPIO configurado correctamente para pin {self.pin}")
            
        except Exception as e:
            self.logger.error(f"Error configurando GPIO: {e}")
            self.simulate = True
            self.logger.info("Cambiando a modo simulación debido a error en GPIO")
    
    def _gpio_callback(self, channel):
        """Callback para interrupciones GPIO"""
        current_time = time.time()
        
        # Debouncing por software adicional
        with self._lock:
            if current_time - self._last_interrupt_time < self.debounce_time:
                return
            self._last_interrupt_time = current_time
        
        # Leer estado del pin
        pin_state = GPIO.input(self.pin)
        
        # El botón está presionado cuando el pin está LOW (pull-up)
        if pin_state == GPIO.LOW:
            self._handle_button_press(current_time)
        else:
            self._handle_button_release(current_time)
    
    def _handle_button_press(self, timestamp: float):
        """Manejar inicio de pulsación"""
        with self._lock:
            if self._is_pressed:
                return  # Ya está presionado
            
            self._is_pressed = True
            self._press_start_time = timestamp
        
        self.logger.debug(f"Botón presionado en pin {self.pin}")
        
        # Notificar evento de inicio de pulsación
        self._notify_event(ButtonEvent.PRESS_START, 0, timestamp)
        
        # Iniciar thread para detectar pulsación larga
        if self._button_thread is None or not self._button_thread.is_alive():
            self._button_thread = threading.Thread(target=self._monitor_long_press, daemon=True)
            self._button_thread.start()
    
    def _handle_button_release(self, timestamp: float):
        """Manejar fin de pulsación"""
        with self._lock:
            if not self._is_pressed:
                return  # No estaba presionado
            
            self._is_pressed = False
            press_duration = timestamp - self._press_start_time if self._press_start_time else 0
        
        self.logger.debug(f"Botón liberado en pin {self.pin}, duración: {press_duration:.2f}s")
        
        # Notificar evento de fin de pulsación
        self._notify_event(ButtonEvent.PRESS_END, press_duration, timestamp)
        
        # Determinar tipo de pulsación
        if press_duration < self.long_press_time:
            self._notify_event(ButtonEvent.SHORT_PRESS, press_duration, timestamp)
        else:
            self._notify_event(ButtonEvent.LONG_PRESS, press_duration, timestamp)
    
    def _monitor_long_press(self):
        """Monitorear pulsación larga en thread separado"""
        time.sleep(self.long_press_time)
        
        with self._lock:
            if self._is_pressed:
                # Todavía está presionado después del tiempo de pulsación larga
                press_duration = time.time() - self._press_start_time if self._press_start_time else 0
                self.logger.debug(f"Pulsación larga detectada en pin {self.pin}, duración: {press_duration:.2f}s")
    
    def _notify_event(self, event_type: ButtonEvent, press_duration: float, timestamp: float):
        """Notificar evento a callbacks registrados"""
        event_data = ButtonEventData(
            event_type=event_type,
            pin=self.pin,
            press_duration=press_duration,
            timestamp=timestamp
        )
        
        # Notificar a callbacks específicos
        if event_type in self._callbacks:
            try:
                self._callbacks[event_type](event_data)
            except Exception as e:
                self.logger.error(f"Error en callback para evento {event_type}: {e}")
        
        # Notificar a callback general si existe
        if ButtonEvent.PRESS_START in self._callbacks and event_type != ButtonEvent.PRESS_START:
            try:
                self._callbacks[ButtonEvent.PRESS_START](event_data)
            except Exception as e:
                self.logger.error(f"Error en callback general para evento {event_type}: {e}")
    
    def register_callback(self, event_type: ButtonEvent, callback: Callable[[ButtonEventData], None]):
        """
        Registrar callback para eventos de botón
        
        Args:
            event_type: Tipo de evento (SHORT_PRESS, LONG_PRESS, etc.)
            callback: Función a llamar cuando ocurra el evento
        """
        self._callbacks[event_type] = callback
        self.logger.debug(f"Callback registrado para evento {event_type.value}")
    
    def unregister_callback(self, event_type: ButtonEvent):
        """
        Desregistrar callback para eventos de botón
        
        Args:
            event_type: Tipo de evento a desregistrar
        """
        if event_type in self._callbacks:
            del self._callbacks[event_type]
            self.logger.debug(f"Callback desregistrado para evento {event_type.value}")
    
    def simulate_button_press(self, duration: float = 0.1):
        """
        Simular pulsación de botón para testing
        
        Args:
            duration: Duración de la pulsación en segundos
        """
        if not self.simulate:
            self.logger.warning("simulate_button_press() solo funciona en modo simulación")
            return
        
        timestamp = time.time()
        
        # Simular inicio de pulsación
        self._handle_button_press(timestamp)
        
        # Esperar duración especificada
        time.sleep(duration)
        
        # Simular fin de pulsación
        self._handle_button_release(timestamp + duration)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtener estado actual del ButtonHandler
        
        Returns:
            Dict con información del estado
        """
        return {
            "pin": self.pin,
            "is_pressed": self._is_pressed,
            "is_running": self._is_running,
            "simulate": self.simulate,
            "debounce_time": self.debounce_time,
            "long_press_time": self.long_press_time,
            "press_start_time": self._press_start_time,
            "callbacks_registered": list(self._callbacks.keys())
        }
    
    def start(self):
        """Iniciar ButtonHandler"""
        if self._is_running:
            self.logger.warning("ButtonHandler ya está ejecutándose")
            return
        
        self._is_running = True
        self.logger.info(f"ButtonHandler iniciado en pin {self.pin} (simulate: {self.simulate})")
    
    def stop(self):
        """Detener ButtonHandler"""
        if not self._is_running:
            return
        
        self._is_running = False
        
        # Limpiar GPIO si está disponible
        if GPIO_AVAILABLE and not self.simulate:
            try:
                GPIO.remove_event_detect(self.pin)
                GPIO.cleanup(self.pin)
                self.logger.info(f"GPIO limpiado para pin {self.pin}")
            except Exception as e:
                self.logger.error(f"Error limpiando GPIO: {e}")
        
        # Limpiar callbacks
        self._callbacks.clear()
        
        self.logger.info("ButtonHandler detenido")
    
    def __del__(self):
        """Destructor para limpiar recursos"""
        self.stop()
