#!/usr/bin/env python3
"""
EventBus básico para desacoplar componentes.

Implementa un sistema de eventos centralizado que permite comunicación
entre componentes sin crear dependencias directas.
"""

import logging
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum, auto
import time
import threading
import queue
from utils.logger import logger, log_hardware_event


class EventType(Enum):
    """Tipos de eventos del sistema"""
    # Audio events
    WAKE_WORD_DETECTED = auto()
    VOICE_ACTIVITY_START = auto()
    VOICE_ACTIVITY_END = auto()
    AUDIO_CHUNK_READY = auto()
    
    # State events  
    STATE_CHANGED = auto()
    
    # Hardware events
    BUTTON_PRESSED = auto()
    BUTTON_RELEASED = auto()
    LED_STATE_CHANGED = auto()
    
    # Communication events
    WEBSOCKET_CONNECTED = auto()
    WEBSOCKET_DISCONNECTED = auto()
    MESSAGE_TO_BACKEND = auto()
    MESSAGE_FROM_BACKEND = auto()
    
    # System events
    SYSTEM_ERROR = auto()
    COMPONENT_READY = auto()
    SHUTDOWN_REQUESTED = auto()


@dataclass
class Event:
    """Evento básico del sistema"""
    event_type: EventType
    timestamp: float
    source: str
    data: Dict[str, Any] = None
    event_id: Optional[str] = None


class EventHandler:
    """Interfaz base para manejadores de eventos"""
    
    def handle_event(self, event: Event) -> None:
        """Maneja un evento"""
        pass
    
    def get_handler_name(self) -> str:
        """Retorna el nombre del manejador"""
        return self.__class__.__name__


class EventBus:
    """
    Bus de eventos centralizado para comunicación entre componentes.
    
    Características:
    - Publicación/suscripción por tipo de evento
    - Procesamiento asíncrono opcional
    - Filtrado de eventos
    - Estadísticas y monitoreo
    - Thread-safe
    """
    
    def __init__(self, async_processing: bool = True, max_queue_size: int = 1000):
        self._handlers: Dict[EventType, List[Callable[[Event], None]]] = {
            event_type: [] for event_type in EventType
        }
        self._wildcard_handlers: List[Callable[[Event], None]] = []
        self._event_filters: List[Callable[[Event], bool]] = []
        
        # Procesamiento asíncrono
        self._async_processing = async_processing
        self._event_queue = queue.Queue(maxsize=max_queue_size) if async_processing else None
        self._processing_thread = None
        self._shutdown_event = threading.Event()
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Estadísticas
        self._stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_filtered": 0,
            "events_failed": 0,
            "handler_count": 0,
            "event_type_counts": {event_type.name: 0 for event_type in EventType},
            "processing_errors": []
        }
        
        if self._async_processing:
            self._start_processing_thread()
        
        logger.info(f"EventBus initialized (async={async_processing})")
    
    def _start_processing_thread(self) -> None:
        """Inicia el hilo de procesamiento asíncrono"""
        self._processing_thread = threading.Thread(
            target=self._process_events_async,
            name="EventBus-Processor",
            daemon=True
        )
        self._processing_thread.start()
        logger.debug("EventBus async processing thread started")
    
    def _process_events_async(self) -> None:
        """Procesa eventos de forma asíncrona"""
        while not self._shutdown_event.is_set():
            try:
                # Timeout para permitir shutdown
                event = self._event_queue.get(timeout=1.0)
                self._process_event(event)
                self._event_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in async event processing: {e}")
                self._stats["events_failed"] += 1
    
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """
        Suscribe un manejador a un tipo de evento específico.
        
        Args:
            event_type: Tipo de evento a manejar
            handler: Función que procesará el evento
        """
        with self._lock:
            self._handlers[event_type].append(handler)
            self._stats["handler_count"] += 1
        
        logger.debug(f"Handler subscribed to {event_type.name}")
    
    def subscribe_wildcard(self, handler: Callable[[Event], None]) -> None:
        """
        Suscribe un manejador para todos los tipos de eventos.
        
        Args:
            handler: Función que procesará todos los eventos
        """
        with self._lock:
            self._wildcard_handlers.append(handler)
            self._stats["handler_count"] += 1
        
        logger.debug("Wildcard handler subscribed")
    
    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> bool:
        """
        Desuscribe un manejador de un tipo de evento.
        
        Args:
            event_type: Tipo de evento
            handler: Función a desuscribir
            
        Returns:
            True si se encontró y removió el handler
        """
        with self._lock:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
                self._stats["handler_count"] -= 1
                logger.debug(f"Handler unsubscribed from {event_type.name}")
                return True
            return False
    
    def add_filter(self, filter_func: Callable[[Event], bool]) -> None:
        """
        Añade un filtro de eventos. Solo se procesan eventos que pasen el filtro.
        
        Args:
            filter_func: Función que retorna True si el evento debe procesarse
        """
        with self._lock:
            self._event_filters.append(filter_func)
        
        logger.debug("Event filter added")
    
    def publish(self, event_type: EventType, source: str, data: Dict[str, Any] = None) -> None:
        """
        Publica un evento.
        
        Args:
            event_type: Tipo de evento
            source: Componente que genera el evento
            data: Datos del evento
        """
        event = Event(
            event_type=event_type,
            timestamp=time.time(),
            source=source,
            data=data or {},
            event_id=f"{event_type.name}_{int(time.time() * 1000000)}"
        )
        
        with self._lock:
            self._stats["events_published"] += 1
            self._stats["event_type_counts"][event_type.name] += 1
        
        if self._async_processing:
            try:
                self._event_queue.put_nowait(event)
            except queue.Full:
                logger.warning("EventBus queue full, dropping event")
                self._stats["events_failed"] += 1
        else:
            self._process_event(event)
    
    def _process_event(self, event: Event) -> None:
        """Procesa un evento ejecutando todos los manejadores relevantes"""
        
        # Aplicar filtros
        for filter_func in self._event_filters:
            try:
                if not filter_func(event):
                    self._stats["events_filtered"] += 1
                    return
            except Exception as e:
                logger.error(f"Error in event filter: {e}")
        
        handlers_executed = 0
        
        # Ejecutar manejadores específicos del tipo
        for handler in self._handlers[event.event_type]:
            try:
                handler(event)
                handlers_executed += 1
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
                self._stats["events_failed"] += 1
                self._stats["processing_errors"].append({
                    "timestamp": time.time(),
                    "event_type": event.event_type.name,
                    "error": str(e)
                })
        
        # Ejecutar manejadores wildcard
        for handler in self._wildcard_handlers:
            try:
                handler(event)
                handlers_executed += 1
            except Exception as e:
                logger.error(f"Error in wildcard handler: {e}")
                self._stats["events_failed"] += 1
        
        self._stats["events_processed"] += 1
        
        # Log para eventos importantes
        if event.event_type in [EventType.WAKE_WORD_DETECTED, EventType.STATE_CHANGED]:
            logger.debug(f"Event processed: {event.event_type.name} from {event.source}")
            log_hardware_event("event_processed", {
                "event_type": event.event_type.name,
                "source": event.source,
                "handlers_executed": handlers_executed,
                "timestamp": event.timestamp
            })
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del EventBus"""
        with self._lock:
            stats = self._stats.copy()
            stats.update({
                "queue_size": self._event_queue.qsize() if self._event_queue else 0,
                "async_processing": self._async_processing,
                "is_running": not self._shutdown_event.is_set(),
                "recent_errors": self._stats["processing_errors"][-10:]  # Últimos 10 errores
            })
            return stats
    
    def get_handler_count(self, event_type: EventType = None) -> int:
        """
        Retorna el número de manejadores registrados.
        
        Args:
            event_type: Si se especifica, cuenta solo para ese tipo
            
        Returns:
            Número de manejadores
        """
        with self._lock:
            if event_type:
                return len(self._handlers[event_type])
            else:
                return sum(len(handlers) for handlers in self._handlers.values()) + len(self._wildcard_handlers)
    
    def shutdown(self) -> None:
        """Termina el EventBus de forma limpia"""
        logger.info("EventBus shutting down...")
        
        self._shutdown_event.set()
        
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=5.0)
            if self._processing_thread.is_alive():
                logger.warning("EventBus processing thread did not terminate cleanly")
        
        # Procesar eventos pendientes si no es asíncrono
        if self._event_queue and not self._async_processing:
            while not self._event_queue.empty():
                try:
                    event = self._event_queue.get_nowait()
                    self._process_event(event)
                except queue.Empty:
                    break
        
        logger.info("EventBus shutdown complete")


# Decorador para facilitar la suscripción
def event_handler(event_type: EventType):
    """
    Decorador para marcar métodos como manejadores de eventos.
    
    Args:
        event_type: Tipo de evento que maneja el método
    """
    def decorator(func):
        func._event_type = event_type
        func._is_event_handler = True
        return func
    return decorator


class EventMixin:
    """
    Mixin para añadir capacidades de eventos a cualquier clase.
    """
    
    def __init__(self, event_bus: EventBus = None):
        self._event_bus = event_bus
        self._auto_subscribe()
    
    def set_event_bus(self, event_bus: EventBus) -> None:
        """Establece el EventBus y se auto-suscribe"""
        if self._event_bus:
            self._auto_unsubscribe()
        
        self._event_bus = event_bus
        self._auto_subscribe()
    
    def _auto_subscribe(self) -> None:
        """Auto-suscribe métodos marcados con @event_handler"""
        if not self._event_bus:
            return
        
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, '_is_event_handler') and hasattr(attr, '_event_type'):
                self._event_bus.subscribe(attr._event_type, attr)
    
    def _auto_unsubscribe(self) -> None:
        """Desuscribe métodos de eventos"""
        if not self._event_bus:
            return
        
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, '_is_event_handler') and hasattr(attr, '_event_type'):
                self._event_bus.unsubscribe(attr._event_type, attr)
    
    def publish_event(self, event_type: EventType, data: Dict[str, Any] = None) -> None:
        """Publica un evento usando el EventBus"""
        if self._event_bus:
            source = getattr(self, 'component_name', self.__class__.__name__)
            self._event_bus.publish(event_type, source, data)


# Singleton global del EventBus (opcional)
_global_event_bus = None

def get_global_event_bus() -> EventBus:
    """Retorna la instancia global del EventBus"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus(async_processing=True)
    return _global_event_bus


def set_global_event_bus(event_bus: EventBus) -> None:
    """Establece la instancia global del EventBus"""
    global _global_event_bus
    _global_event_bus = event_bus


if __name__ == "__main__":
    # Test básico del EventBus
    print("Testing EventBus...")
    
    event_bus = EventBus(async_processing=False)
    
    # Test handler
    def test_handler(event: Event):
        print(f"Received event: {event.event_type.name} from {event.source}")
    
    # Suscribir y publicar
    event_bus.subscribe(EventType.WAKE_WORD_DETECTED, test_handler)
    event_bus.publish(EventType.WAKE_WORD_DETECTED, "test", {"confidence": 0.95})
    
    # Estadísticas
    stats = event_bus.get_stats()
    print(f"Events published: {stats['events_published']}")
    print(f"Events processed: {stats['events_processed']}")
    
    event_bus.shutdown()
    print("EventBus test completed!")
