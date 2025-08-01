#!/usr/bin/env python3
"""
Button Handler Module for PuertoCho Assistant Hardware Service

Maneja la detección de botones GPIO con debouncing y soporte para pulsaciones cortas y largas.
Notifica eventos al StateManager a través de callbacks.
"""

import time
import threading
from typing import Callable, Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, field
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
    DOUBLE_CLICK = "double_click"
    TRIPLE_CLICK = "triple_click"
    STATE_CHANGE = "state_change"

@dataclass
class ButtonEventData:
    """Datos del evento de botón"""
    event_type: ButtonEvent
    pin: int
    press_duration: float
    timestamp: float
    click_count: int = 0
    is_pressed: bool = False

@dataclass
class CallbackRegistration:
    """Registro de callback con prioridad y metadatos"""
    callback: Callable[[ButtonEventData], None]
    priority: int = 0
    name: str = ""
    enabled: bool = True

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
        self._callbacks: Dict[ButtonEvent, List[CallbackRegistration]] = {}
        self._button_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Estado para detección de múltiples clicks
        self._click_count = 0
        self._last_click_time = 0
        self._click_timeout = 0.5  # 500ms para detectar doble/triple click
        self._click_thread: Optional[threading.Thread] = None
        
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
        self._notify_event(ButtonEvent.PRESS_START, 0, timestamp, is_pressed=True)
        
        # Notificar cambio de estado
        self._notify_event(ButtonEvent.STATE_CHANGE, 0, timestamp, is_pressed=True)
        
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
        
        # Notificar cambio de estado
        self._notify_event(ButtonEvent.STATE_CHANGE, press_duration, timestamp, is_pressed=False)
        
        # Detectar tipo de pulsación y múltiples clicks
        if press_duration < self.long_press_time:
            self._handle_click_detection(timestamp, press_duration)
        else:
            self._notify_event(ButtonEvent.LONG_PRESS, press_duration, timestamp)
    
    def _handle_click_detection(self, timestamp: float, press_duration: float):
        """Manejar detección de clicks múltiples"""
        with self._lock:
            # Verificar si es parte de una secuencia de clicks
            if timestamp - self._last_click_time < self._click_timeout:
                self._click_count += 1
            else:
                self._click_count = 1
            
            self._last_click_time = timestamp
        
        # Cancelar thread anterior de timeout si existe
        if self._click_thread and self._click_thread.is_alive():
            # No hay forma directa de cancelar, pero el nuevo thread manejará la lógica
            pass
        
        # Iniciar nuevo thread para manejar timeout de clicks
        self._click_thread = threading.Thread(
            target=self._process_click_sequence, 
            args=(timestamp, press_duration, self._click_count),
            daemon=True
        )
        self._click_thread.start()
    
    def _process_click_sequence(self, timestamp: float, press_duration: float, click_count: int):
        """Procesar secuencia de clicks después del timeout"""
        time.sleep(self._click_timeout)
        
        with self._lock:
            # Verificar si no hubo más clicks durante el timeout
            if self._last_click_time == timestamp and self._click_count == click_count:
                # Determinar tipo de evento basado en número de clicks
                if click_count == 1:
                    self._notify_event(ButtonEvent.SHORT_PRESS, press_duration, timestamp, click_count=1)
                elif click_count == 2:
                    self._notify_event(ButtonEvent.DOUBLE_CLICK, press_duration, timestamp, click_count=2)
                elif click_count == 3:
                    self._notify_event(ButtonEvent.TRIPLE_CLICK, press_duration, timestamp, click_count=3)
                else:
                    # Para más de 3 clicks, notificar como short press con el número
                    self._notify_event(ButtonEvent.SHORT_PRESS, press_duration, timestamp, click_count=click_count)
                
                # Reset contador
                self._click_count = 0
    
    def _monitor_long_press(self):
        """Monitorear pulsación larga en thread separado"""
        time.sleep(self.long_press_time)
        
        with self._lock:
            if self._is_pressed:
                # Todavía está presionado después del tiempo de pulsación larga
                press_duration = time.time() - self._press_start_time if self._press_start_time else 0
                self.logger.debug(f"Pulsación larga detectada en pin {self.pin}, duración: {press_duration:.2f}s")
    
    def _notify_event(self, event_type: ButtonEvent, press_duration: float, timestamp: float, 
                     click_count: int = 0, is_pressed: Optional[bool] = None):
        """Notificar evento a callbacks registrados"""
        event_data = ButtonEventData(
            event_type=event_type,
            pin=self.pin,
            press_duration=press_duration,
            timestamp=timestamp,
            click_count=click_count,
            is_pressed=is_pressed if is_pressed is not None else self._is_pressed
        )
        
        # Notificar a callbacks específicos ordenados por prioridad
        if event_type in self._callbacks:
            sorted_callbacks = sorted(self._callbacks[event_type], key=lambda x: x.priority, reverse=True)
            for registration in sorted_callbacks:
                if registration.enabled:
                    try:
                        registration.callback(event_data)
                    except Exception as e:
                        self.logger.error(f"Error en callback '{registration.name}' para evento {event_type}: {e}")
    
    def register_callback(self, event_type: ButtonEvent, callback: Callable[[ButtonEventData], None], 
                         priority: int = 0, name: str = "") -> str:
        """
        Registrar callback para eventos de botón con soporte para prioridades
        
        Args:
            event_type: Tipo de evento (SHORT_PRESS, LONG_PRESS, etc.)
            callback: Función a llamar cuando ocurra el evento
            priority: Prioridad del callback (mayor número = mayor prioridad)
            name: Nombre descriptivo del callback para debugging
            
        Returns:
            ID único del callback registrado
        """
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        
        # Generar ID único basado en timestamp y tipo de evento
        callback_id = f"{event_type.value}_{len(self._callbacks[event_type])}_{int(time.time() * 1000)}"
        
        registration = CallbackRegistration(
            callback=callback,
            priority=priority,
            name=name or callback_id,
            enabled=True
        )
        
        self._callbacks[event_type].append(registration)
        self.logger.debug(f"Callback '{name}' registrado para evento {event_type.value} con prioridad {priority}")
        
        return callback_id
    
    def register_state_callback(self, callback: Callable[[ButtonEventData], None], 
                               priority: int = 0, name: str = "") -> str:
        """
        Registrar callback para cambios de estado del botón
        
        Args:
            callback: Función a llamar cuando cambie el estado
            priority: Prioridad del callback
            name: Nombre descriptivo del callback
            
        Returns:
            ID único del callback registrado
        """
        return self.register_callback(ButtonEvent.STATE_CHANGE, callback, priority, name)
    
    def unregister_callback(self, event_type: ButtonEvent, callback_name: str = None):
        """
        Desregistrar callback(s) para eventos de botón
        
        Args:
            event_type: Tipo de evento a desregistrar
            callback_name: Nombre específico del callback (opcional, si no se especifica borra todos)
        """
        if event_type not in self._callbacks:
            return
        
        if callback_name:
            # Remover callback específico por nombre
            self._callbacks[event_type] = [
                reg for reg in self._callbacks[event_type] 
                if reg.name != callback_name
            ]
            self.logger.debug(f"Callback '{callback_name}' desregistrado para evento {event_type.value}")
        else:
            # Remover todos los callbacks para este evento
            del self._callbacks[event_type]
            self.logger.debug(f"Todos los callbacks desregistrados para evento {event_type.value}")
    
    def enable_callback(self, event_type: ButtonEvent, callback_name: str):
        """Habilitar callback específico"""
        if event_type in self._callbacks:
            for registration in self._callbacks[event_type]:
                if registration.name == callback_name:
                    registration.enabled = True
                    self.logger.debug(f"Callback '{callback_name}' habilitado para evento {event_type.value}")
                    return
    
    def disable_callback(self, event_type: ButtonEvent, callback_name: str):
        """Deshabilitar callback específico"""
        if event_type in self._callbacks:
            for registration in self._callbacks[event_type]:
                if registration.name == callback_name:
                    registration.enabled = False
                    self.logger.debug(f"Callback '{callback_name}' deshabilitado para evento {event_type.value}")
                    return
    
    def is_pressed(self) -> bool:
        """
        Obtener estado actual del botón
        
        Returns:
            True si el botón está presionado, False en caso contrario
        """
        return self._is_pressed
    
    def get_press_duration(self) -> float:
        """
        Obtener duración de la pulsación actual
        
        Returns:
            Duración en segundos si está presionado, 0 si no está presionado
        """
        if self._is_pressed and self._press_start_time:
            return time.time() - self._press_start_time
        return 0.0
    
    def set_click_timeout(self, timeout: float):
        """
        Configurar timeout para detección de múltiples clicks
        
        Args:
            timeout: Timeout en segundos (por defecto 0.5s)
        """
        self._click_timeout = timeout
        self.logger.debug(f"Timeout de click configurado a {timeout}s")
    
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
    
    def simulate_double_click(self, click_duration: float = 0.1, gap_duration: float = 0.1):
        """
        Simular doble click para testing
        
        Args:
            click_duration: Duración de cada click
            gap_duration: Tiempo entre clicks
        """
        if not self.simulate:
            self.logger.warning("simulate_double_click() solo funciona en modo simulación")
            return
        
        # Primer click
        self.simulate_button_press(click_duration)
        time.sleep(gap_duration)
        
        # Segundo click
        self.simulate_button_press(click_duration)
    
    def simulate_triple_click(self, click_duration: float = 0.1, gap_duration: float = 0.1):
        """
        Simular triple click para testing
        
        Args:
            click_duration: Duración de cada click
            gap_duration: Tiempo entre clicks
        """
        if not self.simulate:
            self.logger.warning("simulate_triple_click() solo funciona en modo simulación")
            return
        
        # Tres clicks consecutivos
        for i in range(3):
            if i > 0:
                time.sleep(gap_duration)
            self.simulate_button_press(click_duration)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtener estado actual del ButtonHandler
        
        Returns:
            Dict con información del estado
        """
        with self._lock:
            callback_info = {}
            for event_type, registrations in self._callbacks.items():
                callback_info[event_type.value] = [
                    {
                        "name": reg.name,
                        "priority": reg.priority,
                        "enabled": reg.enabled
                    }
                    for reg in registrations
                ]
        
        return {
            "pin": self.pin,
            "is_pressed": self._is_pressed,
            "is_running": self._is_running,
            "simulate": self.simulate,
            "debounce_time": self.debounce_time,
            "long_press_time": self.long_press_time,
            "click_timeout": self._click_timeout,
            "press_start_time": self._press_start_time,
            "current_press_duration": self.get_press_duration(),
            "click_count": self._click_count,
            "last_click_time": self._last_click_time,
            "callbacks_registered": callback_info
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
