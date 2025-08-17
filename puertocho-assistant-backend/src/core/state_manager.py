"""
State Manager Gateway for PuertoCho Assistant Backend
====================================================

StateManager que actúa como gateway entre el hardware, frontend y backend remoto.
Replica y sincroniza el estado del hardware, agregando estados del backend y remoto.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from clients.hardware_client import get_hardware_client, HardwareClient


class BackendState(Enum):
    """Estados del backend local"""
    STARTING = "starting"
    READY = "ready"
    CONNECTING_HARDWARE = "connecting_hardware"
    HARDWARE_CONNECTED = "hardware_connected"
    HARDWARE_DISCONNECTED = "hardware_disconnected"
    PROCESSING_AUDIO = "processing_audio"
    SENDING_TO_REMOTE = "sending_to_remote"
    ERROR = "error"


class StateManagerGateway:
    """
    StateManager que actúa como gateway entre hardware, frontend y backend remoto.
    
    Responsabilidades:
    - Replicar estado del hardware en tiempo real
    - Mantener estado del backend local
    - Combinar estados para el frontend
    - Gestionar sincronización entre servicios
    """
    
    def __init__(self, websocket_manager=None):
        self.logger = logging.getLogger("state_manager_gateway")
        
        # Estados
        self.hardware_state: Optional[Dict[str, Any]] = None
        self.backend_state: BackendState = BackendState.STARTING
        self.remote_state: Optional[Dict[str, Any]] = None
        
        # Timestamps
        self.last_hardware_sync: Optional[float] = None
        self.last_hardware_update: Optional[float] = None
        
        # WebSocket manager para notificar frontend
        self.websocket_manager = websocket_manager
        
        # Configuration
        self.hardware_sync_interval: float = 1.0  # Sync cada 1 segundo (reducido para mejor responsividad)
        self.hardware_timeout: float = 30.0       # Timeout de hardware
        
        # Tasks
        self._sync_task: Optional[asyncio.Task] = None
        self._running = False
    
    def set_websocket_manager(self, manager):
        """Inyectar websocket manager"""
        self.websocket_manager = manager
    
    async def start(self):
        """Iniciar el StateManager gateway"""
        self.logger.info("🚀 Starting StateManager Gateway...")
        
        self._running = True
        self.backend_state = BackendState.CONNECTING_HARDWARE
        
        # Notificar frontend del estado inicial
        await self._notify_frontend()
        
        # Iniciar tarea de sincronización con hardware
        self._sync_task = asyncio.create_task(self._hardware_sync_loop())
        
        self.logger.info("✅ StateManager Gateway started")
    
    async def stop(self):
        """Detener el StateManager gateway"""
        self.logger.info("🛑 Stopping StateManager Gateway...")
        
        self._running = False
        
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("✅ StateManager Gateway stopped")
    
    # ===============================================
    # SINCRONIZACIÓN CON HARDWARE
    # ===============================================
    
    async def _hardware_sync_loop(self):
        """Loop principal de sincronización con hardware"""
        self.logger.info("🔄 Starting hardware sync loop...")
        
        while self._running:
            try:
                await self._sync_hardware_state()
                await asyncio.sleep(self.hardware_sync_interval)
                
            except asyncio.CancelledError:
                self.logger.info("🔄 Hardware sync loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"❌ Error in hardware sync loop: {e}")
                await asyncio.sleep(self.hardware_sync_interval)
    
    async def _sync_hardware_state(self):
        """Sincronizar estado con el hardware"""
        try:
            hardware_client = get_hardware_client()
            
            # Obtener estado del hardware
            hardware_state = await hardware_client.get_state()
            
            # Verificar si hubo cambios
            if self._has_hardware_state_changed(hardware_state):
                old_state = self.hardware_state.get("state") if self.hardware_state else "unknown"
                new_state = hardware_state.get("state", "unknown")
                
                self.logger.info(f"🔄 Hardware state change: {old_state} -> {new_state}")
                
                # Actualizar estado
                self.hardware_state = hardware_state
                self.last_hardware_update = datetime.now().timestamp()
                
                # Notificar cambio al frontend
                await self._notify_frontend()
            
            # Actualizar timestamp de sincronización
            self.last_hardware_sync = datetime.now().timestamp()
            
            # Actualizar estado del backend
            if self.backend_state == BackendState.CONNECTING_HARDWARE:
                self.backend_state = BackendState.HARDWARE_CONNECTED
                await self._notify_frontend()
            elif self.backend_state == BackendState.HARDWARE_DISCONNECTED:
                self.backend_state = BackendState.HARDWARE_CONNECTED
                self.logger.info("✅ Hardware reconnected!")
                await self._notify_frontend()
                
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to sync with hardware: {e}")
            
            # Marcar hardware como desconectado
            if self.backend_state != BackendState.HARDWARE_DISCONNECTED:
                self.backend_state = BackendState.HARDWARE_DISCONNECTED
                self.logger.warning("❌ Hardware disconnected")
                await self._notify_frontend()
    
    def _has_hardware_state_changed(self, new_state: Dict[str, Any]) -> bool:
        """Verificar si el estado del hardware ha cambiado"""
        if self.hardware_state is None:
            return True
        
        # Comparar campos importantes
        important_fields = ["state", "listening_duration_seconds"]
        
        for field in important_fields:
            if self.hardware_state.get(field) != new_state.get(field):
                return True
        
        return False
    
    # ===============================================
    # GESTIÓN DE ESTADOS
    # ===============================================
    
    async def set_backend_state(self, new_state: BackendState):
        """Cambiar estado del backend y notificar"""
        if self.backend_state != new_state:
            old_state = self.backend_state.value
            self.backend_state = new_state
            
            self.logger.info(f"🔄 Backend state change: {old_state} -> {new_state.value}")
            await self._notify_frontend()
    
    def get_unified_state(self) -> Dict[str, Any]:
        """Obtener estado unificado del sistema completo"""
        now = datetime.now().timestamp()
        
        # Estado base
        unified_state = {
            "timestamp": datetime.now().isoformat(),
            "backend": {
                "state": self.backend_state.value,
                "last_hardware_sync": self.last_hardware_sync,
                "hardware_connected": self.backend_state not in [
                    BackendState.CONNECTING_HARDWARE,
                    BackendState.HARDWARE_DISCONNECTED
                ]
            }
        }
        
        # Agregar estado del hardware si está disponible
        if self.hardware_state:
            unified_state["hardware"] = self.hardware_state.copy()
            
            # Calcular tiempo desde última actualización
            if self.last_hardware_update:
                unified_state["hardware"]["seconds_since_update"] = now - self.last_hardware_update
        else:
            unified_state["hardware"] = {
                "state": "unknown",
                "available": False
            }
        
        # Agregar estado remoto si está disponible
        if self.remote_state:
            unified_state["remote"] = self.remote_state.copy()
        else:
            unified_state["remote"] = {
                "state": "unknown",
                "available": False
            }
        
        return unified_state
    
    async def handle_hardware_event(self, event: Dict[str, Any]):
        """Procesar eventos del hardware (audio capturado, botón, etc.)"""
        event_type = event.get("type", "unknown")
        
        self.logger.info(f"📡 Hardware event received: {event_type}")
        
        if event_type == "audio_captured":
            await self._handle_audio_captured_event(event)
        elif event_type == "button_press":
            await self._handle_button_press_event(event)
        elif event_type == "state_change":
            await self._handle_state_change_event(event)
        else:
            self.logger.warning(f"Unknown hardware event type: {event_type}")
        
        # Siempre notificar al frontend sobre eventos
        await self._notify_frontend()
    
    async def _handle_audio_captured_event(self, event: Dict[str, Any]):
        """Manejar evento de audio capturado"""
        self.logger.info("🎙️ Audio captured by hardware")
        
        # Cambiar estado del backend
        await self.set_backend_state(BackendState.PROCESSING_AUDIO)
        
        # Aquí se podría iniciar procesamiento del audio
        # Por ahora solo registramos el evento
        
        # TODO: Implementar procesamiento de audio
        # audio_processor = get_audio_processor()
        # await audio_processor.process_hardware_audio(event)
    
    async def _handle_button_press_event(self, event: Dict[str, Any]):
        """Manejar evento de botón presionado"""
        button_type = event.get("button_type", "unknown")
        self.logger.info(f"🔘 Button press: {button_type}")
        
        # Los eventos de botón se propagan al frontend sin cambiar estado
    
    async def _handle_state_change_event(self, event: Dict[str, Any]):
        """Manejar evento de cambio de estado del hardware"""
        new_hardware_state = event.get("state", "unknown")
        self.logger.info(f"🔄 Hardware state change event: {new_hardware_state}")
        
        # Forzar sincronización inmediata
        await self._sync_hardware_state()
    
    # ===============================================
    # COMUNICACIÓN CON FRONTEND
    # ===============================================
    
    async def _notify_frontend(self):
        """Notificar cambios al frontend via WebSocket"""
        if self.websocket_manager:
            unified_state = self.get_unified_state()
            
            await self.websocket_manager.broadcast({
                "type": "unified_state_update",
                "payload": unified_state
            })
    
    # ===============================================
    # MÉTODOS PARA API ENDPOINTS
    # ===============================================
    
    async def send_command_to_hardware(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Enviar comando al hardware"""
        try:
            hardware_client = get_hardware_client()
            command_type = command.get("type")
            
            if command_type == "led_pattern":
                result = await hardware_client.set_led_pattern(**command.get("params", {}))
            elif command_type == "state_change":
                result = await hardware_client.set_state(command.get("state"))
            elif command_type == "button_simulate":
                result = await hardware_client.simulate_button_press(**command.get("params", {}))
            else:
                raise ValueError(f"Unknown command type: {command_type}")
            
            self.logger.info(f"✅ Command sent to hardware: {command_type}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send command to hardware: {e}")
            raise
    
    async def get_hardware_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del hardware"""
        try:
            hardware_client = get_hardware_client()
            return await hardware_client.get_metrics()
        except Exception as e:
            self.logger.warning(f"Could not get hardware metrics: {e}")
            return {"error": str(e), "available": False}
    
    # ===============================================
    # COMPATIBILIDAD CON CÓDIGO ANTERIOR
    # ===============================================
    
    def get_assistant_status(self) -> str:
        """Compatibilidad: obtener estado del asistente"""
        if self.hardware_state:
            return self.hardware_state.get("state", "unknown")
        return "unknown"
    
    def get_hardware_status(self) -> Dict[str, Any]:
        """Compatibilidad: obtener estado del hardware"""
        return self.hardware_state or {}
    
    async def set_assistant_status(self, status: str):
        """Compatibilidad: establecer estado del asistente"""
        try:
            hardware_client = get_hardware_client()
            await hardware_client.set_state(status)
            self.logger.info(f"✅ Assistant status changed to: {status}")
        except Exception as e:
            self.logger.error(f"❌ Failed to set assistant status: {e}")
    
    async def set_hardware_status(self, status: Dict[str, Any]):
        """Compatibilidad: establecer estado del hardware (NO-OP)"""
        # En la nueva arquitectura, el hardware mantiene su propio estado
        # Este método existe solo para compatibilidad
        self.logger.warning("set_hardware_status called - hardware manages its own state")


# Instancia singleton
state_manager_gateway: Optional[StateManagerGateway] = None


def get_state_manager() -> StateManagerGateway:
    """Obtener instancia del state manager"""
    global state_manager_gateway
    if state_manager_gateway is None:
        raise Exception("StateManager not initialized. Call init_state_manager() first.")
    return state_manager_gateway


def init_state_manager(websocket_manager=None) -> StateManagerGateway:
    """Inicializar state manager"""
    global state_manager_gateway
    state_manager_gateway = StateManagerGateway(websocket_manager)
    return state_manager_gateway


async def close_state_manager():
    """Cerrar state manager"""
    global state_manager_gateway
    if state_manager_gateway:
        await state_manager_gateway.stop()
        state_manager_gateway = None
