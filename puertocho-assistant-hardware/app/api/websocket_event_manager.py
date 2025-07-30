#!/usr/bin/env python3
"""
WebSocket event manager for hardware service
Handles emission of events from hardware and reception of commands from backend.
"""

import asyncio
import time
import os
from typing import Dict, Any, Optional
from dataclasses import asdict

from api.websocket_client import WebSocketClient, MessageType, WebSocketMessage
from config import config
from utils.logger import get_logger

logger = get_logger(__name__)

class WebSocketEventManager:
    """Gestor de eventos WebSocket para comunicación con backend"""
    
    def __init__(self, state_manager=None):
        """
        Inicializar gestor de eventos WebSocket
        
        Args:
            state_manager: Referencia al StateManager principal
        """
        self.state_manager = state_manager
        self.ws_client = WebSocketClient(
            ws_url=config.backend.ws_url,
            reconnect_interval=5.0,
            max_reconnect_attempts=0  # Reconexión infinita
        )
        
        # Configurar handlers
        self._setup_message_handlers()
        self._setup_connection_handlers()
        
        # Estado interno
        self.last_metrics_sent = 0.0
        self.metrics_interval = 30.0  # Enviar métricas cada 30 segundos
        
        logger.info("WebSocket event manager initialized")
    
    def _setup_message_handlers(self):
        """Configurar handlers para mensajes entrantes"""
        # Comando genérico de hardware
        self.ws_client.add_message_handler(
            MessageType.HARDWARE_COMMAND.value,
            self._handle_hardware_command
        )
        
        # Respuestas de ping
        self.ws_client.add_message_handler(
            MessageType.PONG.value,
            self._handle_pong
        )
    
    def _setup_connection_handlers(self):
        """Configurar handlers para eventos de conexión"""
        self.ws_client.add_connection_handler(self._on_connection_changed)
    
    async def start(self):
        """Iniciar el gestor de eventos WebSocket"""
        logger.info("Starting WebSocket event manager...")
        await self.ws_client.start()
        
        # Iniciar tarea de métricas periódicas
        asyncio.create_task(self._metrics_sender())
    
    async def stop(self):
        """Detener el gestor de eventos WebSocket"""
        logger.info("Stopping WebSocket event manager...")
        await self.ws_client.stop()
    
    # =========================================================================
    # EMISIÓN DE EVENTOS DESDE HARDWARE (HW-WS-02)
    # =========================================================================
    
    async def emit_audio_captured(self, audio_file_path: str, metadata: Dict[str, Any]):
        """
        Emitir evento de audio capturado
        
        Args:
            audio_file_path: Ruta del archivo de audio capturado
            metadata: Metadatos del audio (duración, formato, etc.)
        """
        try:
            # Obtener información del archivo
            file_size = os.path.getsize(audio_file_path) if os.path.exists(audio_file_path) else 0
            
            data = {
                "file_path": audio_file_path,
                "file_name": os.path.basename(audio_file_path),
                "file_size": file_size,
                "metadata": metadata,
                "timestamp": time.time(),
                "source": "hardware_service"
            }
            
            await self.ws_client.send_message(MessageType.AUDIO_CAPTURED, data)
            logger.info(f"Audio captured event sent: {audio_file_path}")
            
        except Exception as e:
            logger.error(f"Failed to emit audio captured event: {e}")
    
    async def emit_state_changed(self, old_state: str, new_state: str, context: Optional[Dict[str, Any]] = None):
        """
        Emitir evento de cambio de estado
        
        Args:
            old_state: Estado anterior
            new_state: Nuevo estado
            context: Contexto adicional del cambio
        """
        try:
            data = {
                "old_state": old_state,
                "new_state": new_state,
                "context": context or {},
                "timestamp": time.time(),
                "source": "state_manager"
            }
            
            await self.ws_client.send_message(MessageType.STATE_CHANGED, data)
            logger.debug(f"State change event sent: {old_state} -> {new_state}")
            
        except Exception as e:
            logger.error(f"Failed to emit state changed event: {e}")
    
    async def emit_button_event(self, event_type: str, duration: float = 0.0):
        """
        Emitir evento de botón
        
        Args:
            event_type: Tipo de evento ('short_press', 'long_press')
            duration: Duración de la pulsación
        """
        try:
            data = {
                "event_type": event_type,
                "duration": duration,
                "timestamp": time.time(),
                "source": "button_handler"
            }
            
            await self.ws_client.send_message(MessageType.BUTTON_EVENT, data)
            logger.info(f"Button event sent: {event_type} ({duration:.2f}s)")
            
        except Exception as e:
            logger.error(f"Failed to emit button event: {e}")
    
    async def emit_hardware_metrics(self, metrics: Dict[str, Any]):
        """
        Emitir métricas de hardware
        
        Args:
            metrics: Diccionario con métricas del sistema
        """
        try:
            data = {
                "metrics": metrics,
                "timestamp": time.time(),
                "source": "hardware_service"
            }
            
            await self.ws_client.send_message(MessageType.HARDWARE_METRICS, data)
            logger.debug("Hardware metrics sent")
            
        except Exception as e:
            logger.error(f"Failed to emit hardware metrics: {e}")
    
    # =========================================================================
    # RECEPCIÓN DE COMANDOS DESDE BACKEND (HW-WS-03)
    # =========================================================================
    
    async def _handle_hardware_command(self, message: WebSocketMessage):
        """Manejar comando genérico de hardware"""
        try:
            data = message.data
            command_type = data.get('command_type')
            
            logger.info(f"Received hardware command: {command_type}")
            
            if command_type == 'set_led_pattern':
                await self._handle_led_pattern(data)
            elif command_type == 'set_config':
                await self._handle_config_update(data)
            elif command_type == 'activate_listening':
                await self._handle_activation(data)
            elif command_type == 'calibrate':
                await self._handle_calibration(data)
            else:
                logger.warning(f"Unknown command type: {command_type}")
            
        except Exception as e:
            logger.error(f"Error handling hardware command: {e}")
    
    async def _handle_led_pattern(self, data: Dict[str, Any]):
        """Manejar comando de cambio de patrón LED"""
        try:
            pattern = data.get('pattern')
            color = data.get('color')
            brightness = data.get('brightness')
            
            if self.state_manager and hasattr(self.state_manager, 'led_controller'):
                led_controller = self.state_manager.led_controller
                
                if pattern == 'solid' and color:
                    await led_controller.set_solid_color(tuple(color))
                elif pattern == 'pulse' and color:
                    await led_controller.set_pulse(tuple(color))
                elif pattern == 'off':
                    await led_controller.set_off()
                
                if brightness is not None:
                    led_controller.brightness = max(0, min(255, brightness))
                
                logger.info(f"LED pattern applied: {pattern}")
            
        except Exception as e:
            logger.error(f"Error applying LED pattern: {e}")
    
    async def _handle_config_update(self, data: Dict[str, Any]):
        """Manejar actualización de configuración"""
        try:
            config_section = data.get('section')
            config_values = data.get('values', {})
            
            logger.info(f"Updating config section: {config_section}")
            
            # Aplicar configuración según la sección
            if config_section == 'audio':
                await self._apply_audio_config(config_values)
            elif config_section == 'wake_word':
                await self._apply_wake_word_config(config_values)
            elif config_section == 'vad':
                await self._apply_vad_config(config_values)
            elif config_section == 'led':
                await self._apply_led_config(config_values)
            else:
                logger.warning(f"Unknown config section: {config_section}")
            
        except Exception as e:
            logger.error(f"Error updating config: {e}")
    
    async def _handle_activation(self, data: Dict[str, Any]):
        """Manejar comando de activación"""
        try:
            activation_type = data.get('type', 'manual')
            
            if self.state_manager:
                if activation_type == 'manual':
                    await self.state_manager.handle_button_event('short_press', 0.5)
                elif activation_type == 'wake_word':
                    await self.state_manager.handle_wake_word_detected()
                
                logger.info(f"System activated via {activation_type}")
            
        except Exception as e:
            logger.error(f"Error handling activation: {e}")
    
    async def _handle_calibration(self, data: Dict[str, Any]):
        """Manejar comando de calibración"""
        try:
            calibration_type = data.get('type')
            
            logger.info(f"Starting calibration: {calibration_type}")
            
            if calibration_type == 'wake_word_sensitivity':
                await self._calibrate_wake_word_sensitivity(data.get('parameters', {}))
            elif calibration_type == 'vad_thresholds':
                await self._calibrate_vad_thresholds(data.get('parameters', {}))
            elif calibration_type == 'audio_levels':
                await self._calibrate_audio_levels(data.get('parameters', {}))
            else:
                logger.warning(f"Unknown calibration type: {calibration_type}")
            
        except Exception as e:
            logger.error(f"Error handling calibration: {e}")
        """Manejar comando de sistema genérico"""
        try:
            data = message.data
            command = data.get('command')
            
            logger.info(f"Received system command: {command}")
            
            if command == 'restart':
                await self._restart_system()
            elif command == 'reset_config':
                await self._reset_configuration()
            elif command == 'clear_audio_cache':
                await self._clear_audio_cache()
            else:
                logger.warning(f"Unknown system command: {command}")
            
        except Exception as e:
            logger.error(f"Error handling system command: {e}")
    
    async def _handle_pong(self, message: WebSocketMessage):
        """Manejar respuesta pong"""
        logger.debug("Received pong from backend")
    
    # =========================================================================
    # INTEGRACIÓN CON STATEMANAGER (HW-WS-04)
    # =========================================================================
    
    async def _on_connection_changed(self, connected: bool):
        """Callback para cambios de estado de conexión"""
        if connected:
            logger.info("WebSocket connected to backend")
            # Enviar estado actual al conectar
            if self.state_manager:
                await self.emit_state_changed(
                    "unknown", 
                    self.state_manager.current_state.value,
                    {"event": "connection_established"}
                )
        else:
            logger.warning("WebSocket disconnected from backend")
    
    async def _metrics_sender(self):
        """Enviar métricas periódicamente"""
        while True:
            try:
                current_time = time.time()
                if current_time - self.last_metrics_sent >= self.metrics_interval:
                    metrics = await self._collect_system_metrics()
                    await self.emit_hardware_metrics(metrics)
                    self.last_metrics_sent = current_time
                
                await asyncio.sleep(10.0)  # Verificar cada 10 segundos
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics sender: {e}")
                await asyncio.sleep(5.0)
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Recopilar métricas del sistema"""
        try:
            import psutil
            
            # Métricas básicas del sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = {
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available": memory.available,
                    "disk_percent": disk.percent,
                    "disk_free": disk.free
                },
                "websocket": self.ws_client.get_connection_info(),
                "timestamp": time.time()
            }
            
            # Métricas del StateManager si está disponible
            if self.state_manager:
                metrics["state_manager"] = {
                    "current_state": self.state_manager.current_state.value,
                    "last_transition": getattr(self.state_manager, 'last_transition_time', 0),
                    "total_transitions": getattr(self.state_manager, 'total_transitions', 0)
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {"error": str(e), "timestamp": time.time()}
    
    # =========================================================================
    # CONFIGURACIÓN DINÁMICA
    # =========================================================================
    
    async def _apply_audio_config(self, config_values: Dict[str, Any]):
        """Aplicar configuración de audio"""
        logger.info(f"Applying audio config: {config_values}")
        # Implementar aplicación de configuración de audio
    
    async def _apply_wake_word_config(self, config_values: Dict[str, Any]):
        """Aplicar configuración de wake word"""
        logger.info(f"Applying wake word config: {config_values}")
        # Implementar aplicación de configuración de wake word
    
    async def _apply_vad_config(self, config_values: Dict[str, Any]):
        """Aplicar configuración de VAD"""
        logger.info(f"Applying VAD config: {config_values}")
        # Implementar aplicación de configuración de VAD
    
    async def _apply_led_config(self, config_values: Dict[str, Any]):
        """Aplicar configuración de LED"""
        logger.info(f"Applying LED config: {config_values}")
        # Implementar aplicación de configuración de LED
    
    # =========================================================================
    # CALIBRACIÓN
    # =========================================================================
    
    async def _calibrate_wake_word_sensitivity(self, parameters: Dict[str, Any]):
        """Calibrar sensibilidad de wake word"""
        logger.info(f"Calibrating wake word sensitivity: {parameters}")
        # Implementar calibración de wake word
    
    async def _calibrate_vad_thresholds(self, parameters: Dict[str, Any]):
        """Calibrar umbrales de VAD"""
        logger.info(f"Calibrating VAD thresholds: {parameters}")
        # Implementar calibración de VAD
    
    async def _calibrate_audio_levels(self, parameters: Dict[str, Any]):
        """Calibrar niveles de audio"""
        logger.info(f"Calibrating audio levels: {parameters}")
        # Implementar calibración de audio
    
    # =========================================================================
    # COMANDOS DE SISTEMA
    # =========================================================================
    
    async def _restart_system(self):
        """Reiniciar sistema"""
        logger.info("Restarting system...")
        # Implementar reinicio del sistema
    
    async def _reset_configuration(self):
        """Resetear configuración"""
        logger.info("Resetting configuration...")
        # Implementar reset de configuración
    
    async def _clear_audio_cache(self):
        """Limpiar cache de audio"""
        logger.info("Clearing audio cache...")
        # Implementar limpieza de cache de audio
    
    # =========================================================================
    # MÉTODOS PÚBLICOS
    # =========================================================================
    
    def is_connected(self) -> bool:
        """Verificar si WebSocket está conectado"""
        return self.ws_client.is_connected
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Obtener estado de conexión WebSocket"""
        return self.ws_client.get_connection_info()
    
    async def send_ping(self) -> bool:
        """Enviar ping al backend"""
        try:
            data = {"timestamp": time.time()}
            return await self.ws_client.send_message(MessageType.PING, data)
        except Exception as e:
            logger.error(f"Failed to send ping: {e}")
            return False
