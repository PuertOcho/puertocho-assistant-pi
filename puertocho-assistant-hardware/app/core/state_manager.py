#!/usr/bin/env python3
"""
StateManager refactorizado - Solo coordinación de estados.

Este StateManager implementa el patrón Observer y actúa como coordinador puro
sin conocimiento específico de implementaciones de componentes.
"""

from enum import Enum, auto
from typing import Optional, Dict, List, Callable, Any
from dataclasses import dataclass
import time
from utils.logger import HardwareLogger, log_hardware_event


class AssistantState(Enum):
    """Estados del asistente"""
    IDLE = auto()
    LISTENING = auto() 
    PROCESSING = auto()
    SPEAKING = auto()
    ERROR = auto()


@dataclass
class StateChangeEvent:
    """Evento de cambio de estado"""
    previous_state: AssistantState
    new_state: AssistantState
    timestamp: float
    context: Dict[str, Any] = None


class ComponentInterface:
    """Interface base para componentes registrados"""
    
    def on_state_changed(self, event: StateChangeEvent) -> None:
        """Callback cuando cambia el estado"""
        pass
    
    def get_component_name(self) -> str:
        """Retorna el nombre del componente"""
        return self.__class__.__name__


class StateManager:
    """
    Gestor de estados refactorizado que actúa como coordinador puro.
    
    Responsabilidades:
    - Gestionar transiciones de estado
    - Notificar cambios a componentes registrados 
    - Mantener historial de estados
    - Proporcionar API para consulta de estado
    
    NO responsable de:
    - Manejo directo de audio
    - Comunicación WebSocket
    - Lógica específica de componentes
    """
    
    def __init__(self):
        self.state = AssistantState.IDLE
        self._previous_state = None
        self._state_history: List[StateChangeEvent] = []
        self._registered_components: Dict[str, ComponentInterface] = {}
        self._state_callbacks: Dict[AssistantState, List[Callable]] = {
            state: [] for state in AssistantState
        }
        self._transition_callbacks: Dict[tuple, List[Callable]] = {}
        
        # Initialize HardwareLogger
        self.logger = HardwareLogger("state_manager")
        
        # Estadísticas
        self._stats = {
            "total_transitions": 0,
            "state_durations": {state.name: 0.0 for state in AssistantState},
            "last_state_change": None,
            "current_state_start": time.time()
        }
        
        self.logger.info("StateManager initialized in pure coordinator mode")
    
    def register_component(self, component: ComponentInterface) -> None:
        """
        Registra un componente para recibir notificaciones de cambio de estado.
        
        Args:
            component: Componente que implementa ComponentInterface
        """
        component_name = component.get_component_name()
        self._registered_components[component_name] = component
        
        self.logger.info(f"Component registered: {component_name}")
        log_hardware_event("component_registered", {
            "component_name": component_name,
            "total_components": len(self._registered_components)
        })
    
    def unregister_component(self, component_name: str) -> None:
        """Desregistra un componente"""
        if component_name in self._registered_components:
            del self._registered_components[component_name]
            self.logger.info(f"Component unregistered: {component_name}")
    
    def register_state_callback(self, state: AssistantState, callback: Callable[[StateChangeEvent], None]) -> None:
        """
        Registra un callback para ejecutar cuando se entra a un estado específico.
        
        Args:
            state: Estado que debe activar el callback
            callback: Función a ejecutar cuando se entra al estado
        """
        self._state_callbacks[state].append(callback)
        self.logger.debug(f"State callback registered for {state.name}")
    
    def register_transition_callback(self, from_state: AssistantState, to_state: AssistantState, 
                                   callback: Callable[[StateChangeEvent], None]) -> None:
        """
        Registra un callback para una transición específica.
        
        Args:
            from_state: Estado origen
            to_state: Estado destino
            callback: Función a ejecutar en la transición
        """
        transition = (from_state, to_state)
        if transition not in self._transition_callbacks:
            self._transition_callbacks[transition] = []
        
        self._transition_callbacks[transition].append(callback)
        self.logger.debug(f"Transition callback registered: {from_state.name} -> {to_state.name}")
    
    def set_state(self, new_state: AssistantState, context: Dict[str, Any] = None) -> bool:
        """
        Cambia el estado del asistente.
        
        Args:
            new_state: Nuevo estado
            context: Contexto adicional para el cambio de estado
            
        Returns:
            True si el cambio fue exitoso, False si fue rechazado
        """
        if self.state == new_state:
            self.logger.debug(f"State unchanged: {new_state.name}")
            return True
        
        # Validar transición (puede ser extendido con reglas de validación)
        if not self._is_valid_transition(self.state, new_state):
            self.logger.warning(f"Invalid transition: {self.state.name} -> {new_state.name}")
            return False
        
        # Actualizar estadísticas
        current_time = time.time()
        state_duration = current_time - self._stats["current_state_start"]
        self._stats["state_durations"][self.state.name] += state_duration
        self._stats["total_transitions"] += 1
        self._stats["last_state_change"] = current_time
        self._stats["current_state_start"] = current_time
        
        # Crear evento
        event = StateChangeEvent(
            previous_state=self.state,
            new_state=new_state,
            timestamp=current_time,
            context=context or {}
        )
        
        # Ejecutar callbacks de transición específica
        transition = (self.state, new_state)
        if transition in self._transition_callbacks:
            for callback in self._transition_callbacks[transition]:
                try:
                    callback(event)
                except Exception as e:
                    self.logger.error(f"Error in transition callback: {e}")
        
        # Cambiar estado
        self._previous_state = self.state
        self.state = new_state
        
        # Añadir al historial
        self._state_history.append(event)
        if len(self._state_history) > 100:  # Mantener solo los últimos 100
            self._state_history.pop(0)
        
        # Log del cambio
        self.logger.info(f"State changed: {event.previous_state.name} -> {event.new_state.name}")
        log_hardware_event("state_changed", {
            "previous_state": event.previous_state.name,
            "new_state": event.new_state.name,
            "transition_time_ms": (current_time - self._stats["current_state_start"]) * 1000,
            "total_transitions": self._stats["total_transitions"]
        })
        
        # Notificar a componentes registrados
        self._notify_components(event)
        
        # Ejecutar callbacks de estado
        for callback in self._state_callbacks[new_state]:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Error in state callback: {e}")
        
        return True
    
    def _is_valid_transition(self, from_state: AssistantState, to_state: AssistantState) -> bool:
        """
        Valida si una transición de estado es permitida.
        Puede ser extendido con reglas de negocio específicas.
        """
        # Por ahora, todas las transiciones son válidas
        # Esto puede ser extendido con reglas específicas del negocio
        return True
    
    def _notify_components(self, event: StateChangeEvent) -> None:
        """Notifica el cambio de estado a todos los componentes registrados"""
        for component_name, component in self._registered_components.items():
            try:
                component.on_state_changed(event)
            except Exception as e:
                self.logger.error(f"Error notifying component {component_name}: {e}")
    
    def get_current_state(self) -> AssistantState:
        """Retorna el estado actual"""
        return self.state
    
    def get_previous_state(self) -> Optional[AssistantState]:
        """Retorna el estado anterior"""
        return self._previous_state
    
    def get_state_history(self, limit: int = 10) -> List[StateChangeEvent]:
        """
        Retorna el historial de cambios de estado.
        
        Args:
            limit: Número máximo de eventos a retornar
            
        Returns:
            Lista de eventos de cambio de estado (más recientes primero)
        """
        return list(reversed(self._state_history[-limit:]))
    
    def get_time_in_current_state(self) -> float:
        """Retorna el tiempo en segundos que lleva en el estado actual"""
        return time.time() - self._stats["current_state_start"]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del StateManager.
        
        Returns:
            Dict con estadísticas de funcionamiento
        """
        current_time = time.time()
        current_state_duration = current_time - self._stats["current_state_start"]
        
        stats = self._stats.copy()
        stats.update({
            "current_state": self.state.name,
            "previous_state": self._previous_state.name if self._previous_state else None,
            "current_state_duration": current_state_duration,
            "registered_components": list(self._registered_components.keys()),
            "component_count": len(self._registered_components),
            "state_callbacks_count": {
                state.name: len(callbacks) for state, callbacks in self._state_callbacks.items()
            },
            "transition_callbacks_count": len(self._transition_callbacks),
            "history_length": len(self._state_history)
        })
        
        return stats
    
    def reset(self) -> None:
        """Resetea el StateManager al estado inicial"""
        self.set_state(AssistantState.IDLE, {"reason": "manual_reset"})
        self.logger.info("StateManager reset to IDLE state")
    
    def is_in_state(self, state: AssistantState) -> bool:
        """Verifica si está en un estado específico"""
        return self.state == state
    
    def is_transitioning_from(self, state: AssistantState) -> bool:
        """Verifica si viene de un estado específico"""
        return self._previous_state == state


# Componentes adaptadores para componentes existentes
class LEDControllerAdapter(ComponentInterface):
    """Adaptador para LEDController existente"""
    
    def __init__(self, led_controller):
        self.led_controller = led_controller
    
    def on_state_changed(self, event: StateChangeEvent) -> None:
        """Mapea estados del asistente a estados de LED"""
        if not self.led_controller:
            return
        
        try:
            from core.led_controller import LEDState
            
            state_mapping = {
                AssistantState.IDLE: LEDState.IDLE,
                AssistantState.LISTENING: LEDState.LISTENING,
                AssistantState.PROCESSING: LEDState.PROCESSING,
                AssistantState.SPEAKING: LEDState.SPEAKING,
                AssistantState.ERROR: LEDState.ERROR
            }
            
            led_state = state_mapping.get(event.new_state, LEDState.IDLE)
            self.led_controller.set_state(led_state)
            
        except Exception as e:
            self.logger.error(f"Error updating LED state: {e}")
    
    def get_component_name(self) -> str:
        return "LEDController"


class VADHandlerAdapter(ComponentInterface):
    """Adaptador para VADHandler existente"""
    
    def __init__(self, vad_handler):
        self.vad_handler = vad_handler
    
    def on_state_changed(self, event: StateChangeEvent) -> None:
        """Resetea VAD cuando entra en estado LISTENING"""
        if not self.vad_handler:
            return
        
        try:
            if event.new_state == AssistantState.LISTENING:
                self.vad_handler.reset()
                self.logger.debug("VAD handler reset for LISTENING state")
        except Exception as e:
            self.logger.error(f"Error resetting VAD handler: {e}")
    
    def get_component_name(self) -> str:
        return "VADHandler"


# Funciones de conveniencia
def create_state_manager_with_adapters(led_controller=None, vad_handler=None) -> StateManager:
    """
    Crea un StateManager y registra adaptadores para componentes existentes.
    
    Args:
        led_controller: Controlador de LEDs existente
        vad_handler: Handler de VAD existente
        
    Returns:
        StateManager configurado con adaptadores
    """
    state_manager = StateManager()
    
    if led_controller:
        led_adapter = LEDControllerAdapter(led_controller)
        state_manager.register_component(led_adapter)
    
    if vad_handler:
        vad_adapter = VADHandlerAdapter(vad_handler)
        state_manager.register_component(vad_adapter)
    
    return state_manager


if __name__ == "__main__":
    # Test básico del StateManager refactorizado
    print("Testing refactored StateManager...")
    
    state_manager = StateManager()
    
    # Test 1: Cambio básico de estado
    success = state_manager.set_state(AssistantState.LISTENING)
    print(f"State change successful: {success}")
    print(f"Current state: {state_manager.get_current_state().name}")
    
    # Test 2: Estadísticas
    stats = state_manager.get_stats()
    print(f"Total transitions: {stats['total_transitions']}")
    
    # Test 3: Historial
    history = state_manager.get_state_history()
    print(f"History length: {len(history)}")
    
    print("StateManager test completed!")
